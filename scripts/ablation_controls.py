"""Ablations against a matched random-deletion control, not against a reseed.

The previous design compared each ablation's ARI to the spread of reseeding on
the unablated graph. Those are different random quantities: one compares two
partitions of two different graphs, the other two partitions of one graph. A
cut can only be said to matter if it perturbs the partition more than deleting
the same papers at random would.

The control has to be degree-matched, not uniform. The classes under test are
not degree-typical. Papers with no reference list have low out-degree by
construction, and 98 of the 159 homonym papers are not in the graph at all.
Uniform deletion of the same count would remove better-connected papers and
perturb more, which would make every real cut look benign.

For each cut we bin the removed papers by undirected degree in the baseline
graph, draw control sets from the complement matching those per-bin counts,
repartition by the same consensus procedure, and compare.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi

from citation_communities import load_papers
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, sizes, wq
from ablations import GRB, HOMONYM, ASTRO

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"
SEEDS = list(range(42, 62))          # R = 20
K = 3                                # control replicates per cut
BINS = [0, 1, 2, 3, 5, 9, 17, 33, 10**9]
MIN = 30

def build(papers, drop=frozenset()):
    de = [(a, b, y) for a, b, y in directed_edges(papers) if a not in drop and b not in drop]
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return collapse(g)

def agreement(n0, m0, nn, m):
    i0 = {n: k for k, n in enumerate(n0)}
    i1 = {n: k for k, n in enumerate(nn)}
    shared = sorted(set(n0) & set(nn))
    a = [m0[i0[n]] for n in shared]
    b = [m[i1[n]] for n in shared]
    return ari(a, b), nmi(a, b), len(shared)

def degree_bin(d):
    for i in range(len(BINS) - 1):
        if BINS[i] <= d < BINS[i + 1]:
            return i
    return len(BINS) - 2

def matched_control(all_bibs, deg, removed, rng):
    """draw a set the same size as `removed`, matching its degree histogram"""
    want = {}
    for b in removed:
        want[degree_bin(deg.get(b, 0))] = want.get(degree_bin(deg.get(b, 0)), 0) + 1
    pool = {}
    for b in all_bibs:
        if b in removed:
            continue
        pool.setdefault(degree_bin(deg.get(b, 0)), []).append(b)
    out = []
    for k, n in want.items():
        cand = pool.get(k, [])
        if len(cand) < n:                      # bin too small, borrow from neighbours
            extra = [b for j in sorted(pool, key=lambda j: abs(j - k))
                     for b in pool[j] if b not in cand]
            cand = cand + extra
        out.extend(rng.choice(np.array(cand, dtype=object), size=n, replace=False).tolist())
    return set(out)

def main():
    papers = load_papers(CORE, "core")
    h0 = build(papers)
    m0, r0, ok0 = consensus(h0, SEEDS)
    if not ok0:
        raise RuntimeError("baseline consensus did not converge")
    n0 = h0.vs["name"]
    q0 = wq(h0, m0, h0.es["weight"])
    deg = dict(zip(n0, h0.strength(weights=h0.es["weight"])))
    nbig0 = len(sizes(m0, MIN))
    print(f"baseline: {h0.vcount():,} papers  Q={q0:.4f}  {nbig0} communities >= {MIN} "
          f"of {len(np.unique(m0))} total  (converged in {r0} rounds)\n", flush=True)

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    cuts = {
        "no reference list": {b for b, d in papers.items() if not (d.get("references") or [])},
        "not refereed": {b for b, d in papers.items()
                         if "REFEREED" not in (d.get("property") or [])},
        "keyword-only": {b for b, d in papers.items() if not GRB.search(text(d))},
        "homonym": {b for b, d in papers.items()
                    if HOMONYM.search(text(d)) and not ASTRO.search(text(d))},
    }
    cuts["keyword-only + homonym"] = cuts["keyword-only"] | cuts["homonym"]

    all_bibs = list(papers)
    rows = []
    for lab, drop in cuts.items():
        h = build(papers, drop)
        m, r, ok = consensus(h, SEEDS)
        if not ok:
            raise RuntimeError(f"{lab}: consensus did not converge")
        a, v, nsh = agreement(n0, m0, h.vs["name"], m)
        q = wq(h, m, h.es["weight"])
        ingraph = sum(1 for b in drop if b in deg)
        dV = h0.vcount() - h.vcount()

        ctrl = []
        for k in range(K):
            rng = np.random.default_rng(20260822 + 1000 * len(rows) + k)
            cs = matched_control(all_bibs, deg, drop, rng)
            hc = build(papers, cs)
            mc, rc, okc = consensus(hc, SEEDS)
            if not okc:
                raise RuntimeError(f"{lab}: control {k} did not converge")
            ca, cv, _ = agreement(n0, m0, hc.vs["name"], mc)
            ctrl.append(ca)
            print(f"     control {k+1}/{K}: ARI={ca:.3f}", flush=True)
        cm, cs_ = float(np.mean(ctrl)), float(np.std(ctrl))
        z = (a - cm) / cs_ if cs_ > 0 else float("nan")
        verdict = ("indistinguishable from random deletion"
                   if abs(a - cm) <= 2 * cs_ else
                   ("perturbs MORE than random deletion" if a < cm
                    else "perturbs LESS than random deletion"))
        rows.append(dict(label=lab, removed=len(drop), in_graph=ingraph, delta_V=dV,
                         q=q, communities=len(sizes(m, MIN)), ari=a, nmi=v, shared=nsh,
                         control_ari=ctrl, control_mean=cm, control_sd=cs_, z=z,
                         verdict=verdict))
        print(f"\n{lab:<24} removed {len(drop):>5} ({ingraph} in graph, dV={dV})  "
              f"Q={q:.4f}  ARI={a:.3f}", flush=True)
        print(f"{'':<24} matched control ARI {cm:.3f} +/- {cs_:.3f}  z={z:+.1f}  "
              f"-> {verdict}\n", flush=True)

    (OUT / "ablation_controls.json").write_text(json.dumps(
        dict(baseline=dict(q=q0, nodes=h0.vcount(), communities=nbig0,
                           total_groups=int(len(np.unique(m0))),
                           covered=int(sum(sizes(m0, MIN)))),
             R=len(SEEDS), K=K, rows=rows), indent=1))
    print(f"wrote {OUT/'ablation_controls.json'}", flush=True)

if __name__ == "__main__":
    main()
