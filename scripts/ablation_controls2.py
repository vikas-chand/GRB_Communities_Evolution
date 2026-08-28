"""Matched-control ablations, second pass: many controls, stratified matching.

The first pass used three control draws per cut, so its z-values rested on a
standard deviation estimated from three numbers, and its matching used degree
alone. This pass draws 25 controls per cut and matches jointly on degree bin,
publication era, and refereed status, so a cut dominated by 1980s conference
papers is compared against papers of the same vintage and kind, not merely the
same connectivity.

Consensus at R = 10 throughout (cut and controls alike). Controls are matched
on the EFFECTIVE deletion: removing a paper that is not a vertex of the
citation graph changes nothing, so the control must mimic only the in-graph
part of the cut. Each control therefore removes exactly V papers, all graph
vertices, matched to the cut's V in-graph removed papers jointly on degree
bin, publication era, and refereed status; the covariate defining a cut is
never matched on itself. Candidates are allocated globally without
replacement; deficient strata coarsen by a declared rule; all strata and
candidate lists are sorted before every seeded draw. Every control set is
stored, and the effective vertex deletion is asserted equal between cut and
control.
"""
from __future__ import annotations
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score as ari

from citation_communities import load_papers
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, wq
from ablations import GRB, HOMONYM, ASTRO

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"
SEEDS = list(range(42, 52))          # R = 10
K = 25
DEG_BINS = [0, 1, 2, 3, 5, 9, 17, 33, 10**9]
ERA_BINS = [0, 1992, 2000, 2009, 2017, 9999]

_papers = None
def papers():
    global _papers
    if _papers is None:
        _papers = load_papers(CORE, "core")
    return _papers

def build(drop=frozenset()):
    de = [(a, b, y) for a, b, y in directed_edges(papers()) if a not in drop and b not in drop]
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return collapse(g)

def stratum(b, deg):
    d = papers()[b]
    db = next(i for i in range(len(DEG_BINS) - 1)
              if DEG_BINS[i] <= deg.get(b, 0) < DEG_BINS[i + 1])
    y = d.get("year") or 0
    eb = next(i for i in range(len(ERA_BINS) - 1)
              if ERA_BINS[i] <= y < ERA_BINS[i + 1])
    ref = "REFEREED" in (d.get("property") or [])
    return (db, eb, ref)

def matched_control(deg, removed, rng, exclude_covariate=None,
                    pool_restrict=None):
    """Draw a control set the same size as `removed`, matched on the strata,
    globally without replacement, deterministic given the rng."""
    def strat(b):
        st = stratum(b, deg)
        if exclude_covariate == "refereed":
            return (st[0], st[1])
        return st
    want = Counter(strat(b) for b in sorted(removed))
    pool = {}
    for b in sorted(pool_restrict if pool_restrict is not None else papers()):
        if b in removed:
            continue
        pool.setdefault(strat(b), []).append(b)
    taken = set()
    out = []
    def coarse(st):
        # declared coarsening ladder: exact -> drop refereed -> drop era -> drop degree
        keys = [k for k in sorted(pool) if k == st]
        if exclude_covariate != "refereed":
            keys += [k for k in sorted(pool) if k != st and k[:2] == st[:2]]
        keys += [k for k in sorted(pool) if k[:1] == st[:1] and k not in keys]
        keys += [k for k in sorted(pool) if k not in keys]
        return keys
    for st in sorted(want):
        n = want[st]
        for key in coarse(st):
            cand = [b for b in pool[key] if b not in taken]
            if not cand:
                continue
            take = min(n, len(cand))
            pick = rng.choice(np.array(cand, dtype=object), size=take,
                              replace=False).tolist()
            out.extend(pick); taken.update(pick)
            n -= take
            if n == 0:
                break
        assert n == 0, f"stratum {st}: could not fill {n} slots"
    assert len(out) == len(set(out)) == len(removed), \
        f"control size {len(set(out))} != removed {len(removed)}"
    return set(out)

def one_partition(drop):
    h = build(frozenset(drop))
    m, r, ok = consensus(h, SEEDS)
    if not ok:
        raise RuntimeError("consensus did not converge")
    return h.vs["name"], np.asarray(m)

def agreement(n0, m0, nn, m):
    i0 = {n: k for k, n in enumerate(n0)}; i1 = {n: k for k, n in enumerate(nn)}
    shared = sorted(set(n0) & set(nn))
    return ari([m0[i0[n]] for n in shared], [m[i1[n]] for n in shared])

def control_job(args):
    cut_i, k, drop_list, excl = args
    rng = np.random.default_rng(20260825 + 10000 * cut_i + k)
    h0 = build()
    vertices = set(h0.vs["name"])
    deg = dict(zip(h0.vs["name"], h0.strength(weights=h0.es["weight"])))
    drop_v = set(drop_list) & vertices          # the effective deletion
    # pool restricted to graph vertices, so every control paper is a vertex
    cs = matched_control(deg, drop_v, rng, exclude_covariate=excl,
                         pool_restrict=vertices)
    assert len(cs) == len(drop_v) and cs <= vertices, "control not V-matched"
    (OUT / f"control_sets/cut{cut_i}_k{k}.json").write_text(json.dumps(sorted(cs)))
    return cut_i, k, one_partition(cs)

def main():
    n0, m0 = one_partition([])
    h0 = build()
    q0 = wq(h0, m0, h0.es["weight"])
    print(f"baseline (R=10): {len(n0):,} papers, Q={q0:.4f}, "
          f"{sum(1 for c in np.bincount(m0) if c>=30)} communities >= 30\n", flush=True)

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    cuts = {
        "no reference list": {b for b, d in papers().items() if not (d.get("references") or [])},
        "not refereed": {b for b, d in papers().items()
                         if "REFEREED" not in (d.get("property") or [])},
        "keyword-only": {b for b, d in papers().items() if not GRB.search(text(d))},
        "homonym": {b for b, d in papers().items()
                    if HOMONYM.search(text(d)) and not ASTRO.search(text(d))},
    }
    cuts["keyword-only + homonym"] = cuts["keyword-only"] | cuts["homonym"]
    names = list(cuts)

    real = {}
    for lab in names:
        nn, m = one_partition(cuts[lab])
        real[lab] = agreement(n0, m0, nn, m)
        print(f"real cut {lab:<24} ARI={real[lab]:.3f}", flush=True)

    (OUT / "control_sets").mkdir(exist_ok=True)
    excl_of = {"not refereed": "refereed"}
    jobs = [(i, k, sorted(cuts[names[i]]), excl_of.get(names[i]))
            for i in range(len(names)) for k in range(K)]
    ctrl = {lab: [] for lab in names}
    done = 0
    with ProcessPoolExecutor(max_workers=6) as ex:
        for cut_i, k, (nn, m) in ex.map(control_job, jobs):
            ctrl[names[cut_i]].append(agreement(n0, m0, nn, m))
            done += 1
            if done % 10 == 0:
                print(f"  controls {done}/{len(jobs)}", flush=True)

    rows = []
    print(f"\n{'cut':<26}{'ARI':>7}{'ctrl mean':>11}{'ctrl sd':>9}{'z':>7}{'pct rank':>10}")
    for lab in names:
        c = np.array(ctrl[lab]); a = real[lab]
        z = (a - c.mean()) / c.std(ddof=1)
        pct = float((c < a).mean())
        rows.append(dict(label=lab, removed=len(cuts[lab]), ari=float(a),
                         control_mean=float(c.mean()), control_sd=float(c.std(ddof=1)),
                         z=float(z), pct_rank=pct, K=K,
                         controls=[float(x) for x in c]))
        print(f"{lab:<26}{a:>7.3f}{c.mean():>11.3f}{c.std(ddof=1):>9.3f}"
              f"{z:>+7.1f}{pct:>10.2f}", flush=True)
    (OUT / "ablation_controls2.json").write_text(json.dumps(
        dict(R=len(SEEDS), K=K, baseline_q=float(q0),
             strata="degree-bin x era x refereed", rows=rows), indent=1))
    print(f"\nwrote {OUT/'ablation_controls2.json'}")

if __name__ == "__main__":
    main()
