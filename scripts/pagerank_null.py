"""Null-adjusted PageRank and community flows under the temporal DCM.

Raw PageRank confounds influence with age and degree. The DCM ensemble holds
each paper's citation activity in each year fixed while rewiring who cites
whom, so a paper's null PageRank distribution is what its age and degree
history alone would earn it. The reported quantity is the empirical percentile
of the observed value in that distribution, and the excess ratio. Same for
community-to-community flows: observed arcs against the DCM ensemble rather
than the closed-form configuration expectation.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import igraph as ig
import numpy as np

from citation_communities import load_papers
from dcm_null import directed_edges, dcm_layer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
R = 20

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    src = np.array([idx[a] for a, b, y in de])
    dst = np.array([idx[b] for a, b, y in de])
    yr = np.array([y for a, b, y in de])
    N = len(names)
    layer = yr - yr.min()
    L = int(layer.max()) + 1

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = np.full(N, -1)
    for c in canon["communities"]:
        for b in c["members"]:
            memb[idx[b]] = c["id"]

    def pagerank_of(s, d):
        g = ig.Graph(n=N, edges=list(zip(s.tolist(), d.tolist())), directed=True)
        return np.array(g.pagerank(damping=0.85))

    def flows_of(s, d):
        f = Counter()
        for a, b in zip(memb[s], memb[d]):
            if a != b and a >= 0 and b >= 0:
                f[(int(a), int(b))] += 1
        return f

    pr_obs = pagerank_of(src, dst)
    fl_obs = flows_of(src, dst)
    print(f"{N:,} papers, {len(de):,} arcs, {L} layers; drawing {R} nulls", flush=True)

    rng = np.random.default_rng(20260825)
    below = np.zeros(N); prsum = np.zeros(N); prsq = np.zeros(N)
    fl_null = {k: [] for k in fl_obs}
    for r in range(R):
        ns, nd = src.copy(), dst.copy()
        for n in range(L):
            m = layer == n
            if m.sum() < 2:
                continue
            a, b = dcm_layer(src[m], dst[m], rng)
            ns[m], nd[m] = a, b
        assert int((ns == nd).sum()) == 0
        assert len(ns) == len(set(zip(ns.tolist(), nd.tolist())))
        pr = pagerank_of(ns, nd)
        below += (pr < pr_obs)
        prsum += pr; prsq += pr * pr
        fn = flows_of(ns, nd)
        for k in fl_null:
            fl_null[k].append(fn.get(k, 0))
        print(f"  draw {r+1:>2}/{R} done", flush=True)

    pct = (below + 0.5) / (R + 1)
    mean = prsum / R
    excess = pr_obs / np.where(mean > 0, mean, np.nan)

    years = np.array([papers[n].get("year") or 0 for n in names])
    titles = {n: ((papers[n].get("title") or [""])[0]
                  if isinstance(papers[n].get("title"), list)
                  else papers[n].get("title") or "") for n in names}
    kin = np.array(ig.Graph(n=N, edges=list(zip(src.tolist(), dst.tolist())),
                            directed=True).degree(mode="in"))
    hi = np.argsort(np.where(pct >= (R - 0.5 + 0.5) / (R + 1), excess, -np.inf))[::-1]
    print(f"\npapers above every null draw: {int((below == R).sum()):,} of {N:,}")
    floor_mask = (kin >= 50) & (below == R)
    print(f"with influence floor kin>=50: {int(floor_mask.sum()):,}")
    print("\n=== largest PageRank excess over the DCM (above all draws) ===")
    top = []
    for i in hi[:15]:
        if below[i] < R:
            continue
        top.append(dict(bibcode=names[i], year=int(years[i]), community=int(memb[i]),
                        excess=float(excess[i]), title=titles[names[i]][:90]))
        print(f"  {names[i]}  {years[i]}  C{memb[i]:<3} x{excess[i]:5.2f}  "
              f"{titles[names[i]][:64]}")

    frows = []
    for (s_, t_), o in fl_obs.items():
        nul = np.array(fl_null[(s_, t_)])
        if o < 30:
            continue
        frows.append(dict(src=s_, dst=t_, obs=int(o), null_mean=float(nul.mean()),
                          null_sd=float(nul.std(ddof=1)),
                          pct=float(((nul < o).sum() + 0.5) / (R + 1)),
                          excess=float(o / nul.mean()) if nul.mean() > 0 else None))
    frows.sort(key=lambda x: -(x["excess"] or 0))
    print("\n=== community flows vs DCM ensemble (top excess, obs>=30) ===")
    for f in frows[:10]:
        print(f"  C{f['src']}->C{f['dst']}: {f['obs']:>5} vs {f['null_mean']:8.1f} "
              f"+/- {f['null_sd']:5.1f}  x{f['excess']:.2f}  pct={f['pct']:.3f}")

    np.save(OUT / "pagerank_null_pct.npy", pct)
    np.save(OUT / "pagerank_null_excess.npy", excess)
    fl_order = np.argsort(np.where(floor_mask, excess, -np.inf))[::-1]
    top_infl = [dict(bibcode=names[i], year=int(years[i]), community=int(memb[i]),
                     kin=int(kin[i]), excess=float(excess[i]),
                     title=titles[names[i]][:90])
                for i in fl_order[:15] if floor_mask[i]]
    (OUT / "pagerank_null.json").write_text(json.dumps(dict(
        R=R, n_above_all=int((below == R).sum()),
        n_above_all_kin50=int(floor_mask.sum()),
        top_excess=top, top_excess_influential=top_infl,
        note=("top_excess is ratio-ranked and dominated by low-PageRank papers; "
              "use top_excess_influential for claims"),
        flows=frows), indent=1))
    print(f"\nwrote {OUT/'pagerank_null.json'}")

if __name__ == "__main__":
    main()
