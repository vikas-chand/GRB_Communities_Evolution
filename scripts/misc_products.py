"""Producers for numbers the manuscript quotes but no product emitted:
the five observed-graph optimiser starts and their spread, the fixed-membership
multigraph/simple modularity difference, the density ratio against Ren et
al.'s network, and the literal stub-discard fraction their method would lose
here.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import leidenalg as la

from citation_communities import load_papers
from dcm_null import directed_edges, undirected
from consensus import build, collapse, wq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    src = np.array([idx[a] for a, b, y in de])
    dst = np.array([idx[b] for a, b, y in de])
    yr = np.array([y for a, b, y in de])
    g = undirected(len(names), zip(src, dst))

    qs = {}
    for s in range(42, 47):
        p = la.find_partition(g, la.RBConfigurationVertexPartition,
                              resolution_parameter=1.0, n_iterations=-1, seed=s)
        qs[s] = float(p.modularity)
    spread = max(qs.values()) - min(qs.values())
    print(f"observed-start Q: {qs}  spread {spread:.8f}", flush=True)

    h = collapse(build())
    probe = la.find_partition(h, la.RBConfigurationVertexPartition,
                              weights=h.es["weight"], resolution_parameter=1.0,
                              n_iterations=-1, seed=45).membership
    q_multi = g.modularity(list(probe))
    q_simple = h.modularity(list(probe))          # unweighted = simple graph
    print(f"fixed membership: multigraph {q_multi:.7f}  simple {q_simple:.7f}  "
          f"diff {q_multi - q_simple:.7f}", flush=True)

    # density ratio vs Ren et al. 2018 (arXiv APS network: 449,673 nodes,
    # 4,710,547 arcs; mean degree 2m/n = 20.95); ours 2*380,362/13,801
    ren_density = 2 * 4710547 / 449673
    ours = 2 * len(de) / len(names)
    ratio = (ours / len(names)) / (ren_density / 449673)
    print(f"edge-density ratio vs Ren et al.: {ratio:.3f}", flush=True)

    # literal stub matching per year layer, seed 42: discarded fraction
    rng = np.random.default_rng(42)
    lost = 0
    lo = yr.min()
    for n in range(int(yr.max() - lo) + 1):
        m = yr - lo == n
        if m.sum() < 2:
            continue
        s_, d_ = src[m], rng.permutation(dst[m])
        bad = int((s_ == d_).sum())
        seen, dup = set(), 0
        for a, b in zip(s_.tolist(), d_.tolist()):
            if (a, b) in seen:
                dup += 1
            seen.add((a, b))
        lost += bad + dup
    frac = lost / len(de)
    print(f"literal stub-match discard (one seeded draw): {lost:,} arcs "
          f"({frac:.3%})", flush=True)

    (OUT / "misc_products.json").write_text(json.dumps(dict(
        observed_start_Q={str(k): v for k, v in qs.items()},
        observed_start_spread=spread,
        fixed_membership=dict(multigraph=q_multi, simple=q_simple,
                              diff=q_multi - q_simple, seed=45),
        density_ratio_vs_ren=ratio,
        literal_discard=dict(seed=42, lost=int(lost), frac=frac)), indent=1))
    print(f"wrote {OUT/'misc_products.json'}")

if __name__ == "__main__":
    main()
