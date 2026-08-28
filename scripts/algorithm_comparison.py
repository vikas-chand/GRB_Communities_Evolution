"""Does the partition depend on which algorithm found it?

Leiden and Louvain both maximise modularity, so agreement between them tests the
optimiser rather than the objective. Infomap optimises something different --
the description length of a random walk -- and leading-eigenvector is the
spectral method Chen & Redner (2010) used, so those are the informative
comparisons. Velden et al. (2017) partitioned astrophysics with Infomap, making
it the closest published precedent for this graph.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import igraph as ig
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari
from sklearn.metrics import normalized_mutual_info_score as nmi

from citation_communities import build_graph, direct_edges, load_papers, partition


def sizes(mem, min_size=30):
    _, c = np.unique(mem, return_counts=True)
    return int((c >= min_size).sum()), sorted(c[c >= min_size], reverse=True)[:5]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/raw/ads_corpus_v2.jsonl"))
    ap.add_argument("--tier", default="core")
    args = ap.parse_args()

    papers = load_papers(args.raw, args.tier)
    g = build_graph(direct_edges(papers), weighted=False)
    print(f"graph: {g.vcount():,} nodes, {g.ecount():,} edges\n")

    runs = {}
    t = time.time()
    runs["Leiden (RB, gamma=1)"] = np.array(partition(g, 1.0).membership)
    print(f"  Leiden               {time.time()-t:>6.1f}s")
    t = time.time()
    runs["Louvain"] = np.array(g.community_multilevel().membership)
    print(f"  Louvain              {time.time()-t:>6.1f}s")
    t = time.time()
    runs["leading eigenvector"] = np.array(
        g.community_leading_eigenvector(clusters=20).membership)
    print(f"  leading eigenvector  {time.time()-t:>6.1f}s")
    t = time.time()
    runs["Infomap"] = np.array(g.community_infomap().membership)
    print(f"  Infomap              {time.time()-t:>6.1f}s")

    print(f"\n{'algorithm':<24} {'communities>=30':>16} {'Q':>8}  largest")
    for k, m in runs.items():
        n, top = sizes(m)
        q = g.modularity(m)
        print(f"  {k:<22} {n:>16} {q:>8.4f}  {top}")

    keys = list(runs)
    print(f"\npairwise agreement (NMI above diagonal, ARI below):")
    print(f"{'':<24}" + "".join(f"{k[:11]:>13}" for k in keys))
    for i, a in enumerate(keys):
        row = ""
        for j, b in enumerate(keys):
            if i == j:
                row += f"{'-':>13}"
            elif j > i:
                row += f"{nmi(runs[a], runs[b]):>13.3f}"
            else:
                row += f"{ari(runs[a], runs[b]):>13.3f}"
        print(f"  {a:<22}{row}")

    ref = runs["Leiden (RB, gamma=1)"]
    print(f"\nnode-level agreement with Leiden (best-match community, "
          f"as Chen & Redner report):")
    for k, m in runs.items():
        if k.startswith("Leiden"):
            continue
        agree = 0
        for c in np.unique(m):
            mask = m == c
            if mask.sum():
                agree += np.bincount(ref[mask]).max()
        print(f"  {k:<22} {agree/len(ref):>6.1%}")


if __name__ == "__main__":
    main()
