"""Do the communities survive a change of graph representation?

Three representations of the same citation evidence:
  A  directed        -- arcs as ADS records them, directed modularity
  B  simple          -- direction collapsed, each dyad one edge
  C  multigraph      -- direction collapsed, a reciprocal dyad kept as two edges

C is what the paper uses. Its weight-2 treatment of a reciprocal pair asserts
that mutual citation carries twice the community evidence of a one-way citation,
which is inherited from the projection rather than argued. The 1,529 reciprocal
pairs are almost all contemporaneous (94.8% within one year), so the assertion is
not obviously wrong, but the partition should not depend on it.

Each representation is partitioned by the same consensus procedure so the
comparison is not confounded by optimiser noise.
"""
from __future__ import annotations
import json
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi

from citation_communities import load_papers
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, sizes, wq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
SEEDS = list(range(42, 62))

def consensus_directed(g, seeds, tau=0.5, max_rounds=8):
    """co-association consensus using the directed objective"""
    edges = np.asarray(g.get_edgelist())
    w = np.ones(g.ecount())
    prev = None
    for r in range(1, max_rounds + 1):
        parts = [np.asarray(la.find_partition(
            g, la.ModularityVertexPartition, weights=list(w),
            n_iterations=2, seed=s).membership) for s in seeds]
        agree = np.mean([p[edges[:, 0]] == p[edges[:, 1]] for p in parts], axis=0)
        wc = np.where(agree >= tau, agree, 0.0)
        if not wc.any():
            return prev, r, False
        # candidates are selected by their own weighted quality, exactly as
        # the undirected helper selects by weighted modularity; the returned
        # fixed point gets one fully optimised pass, also as in the undirected
        # helper
        m = np.asarray(max((la.find_partition(
            g, la.ModularityVertexPartition, weights=list(wc),
            n_iterations=2, seed=s) for s in seeds),
            key=lambda p: p.quality()).membership)
        if prev is not None and ari(prev, m) > 0.9999:
            final = max((la.find_partition(
                g, la.ModularityVertexPartition, weights=list(wc),
                n_iterations=-1, seed=s) for s in seeds),
                key=lambda p: p.quality())
            return np.asarray(final.membership), r, True
        prev, w = m, wc
    return prev, max_rounds, False

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    src = [idx[a] for a, b, _ in de]; dst = [idx[b] for a, b, _ in de]

    gA = ig.Graph(n=len(names), edges=list(zip(src, dst)), directed=True)
    gC = undirected(len(names), zip(src, dst))
    gB = gC.copy(); gB.simplify()
    hC = collapse(gC)
    print(f"A directed   : {gA.vcount():,} nodes, {gA.ecount():,} arcs")
    print(f"B simple     : {gB.vcount():,} nodes, {gB.ecount():,} edges")
    print(f"C multigraph : {gC.vcount():,} nodes, {gC.ecount():,} edges "
          f"({gC.ecount()-gB.ecount():,} from reciprocal dyads)\n", flush=True)

    res = {}
    mA, rA, okA = consensus_directed(gA, SEEDS)
    res["A_directed"] = dict(q=gA.modularity(list(mA), directed=True),
                             n=len(sizes(mA)), converged=bool(okA), rounds=rA)
    print(f"A directed   : Q={res['A_directed']['q']:.4f}  "
          f"{res['A_directed']['n']} communities >=30  (converged={okA})", flush=True)

    hB = gB.copy(); hB.es["weight"] = 1.0
    mB, rB, okB = consensus(hB, SEEDS)
    res["B_simple"] = dict(q=wq(hB, mB, hB.es["weight"]), n=len(sizes(mB)),
                           converged=bool(okB), rounds=rB)
    print(f"B simple     : Q={res['B_simple']['q']:.4f}  "
          f"{res['B_simple']['n']} communities >=30  (converged={okB})", flush=True)

    mC, rC, okC = consensus(hC, SEEDS)
    res["C_multigraph"] = dict(q=wq(hC, mC, hC.es["weight"]), n=len(sizes(mC)),
                               converged=bool(okC), rounds=rC)
    print(f"C multigraph : Q={res['C_multigraph']['q']:.4f}  "
          f"{res['C_multigraph']['n']} communities >=30  (converged={okC})\n", flush=True)

    pairs = {"A vs B": (mA, mB), "A vs C": (mA, mC), "B vs C": (mB, mC)}
    res["agreement"] = {}
    for k, (x, y) in pairs.items():
        res["agreement"][k] = dict(ari=float(ari(x, y)), nmi=float(nmi(x, y)))
        print(f"{k}: ARI {ari(x,y):.3f}   NMI {nmi(x,y):.3f}")
    print("\nreference band: see stability_sweep.json R=20 for the reseed floor")
    (OUT / "representation_three.json").write_text(json.dumps(res, indent=1))
    print(f"wrote {OUT/'representation_three.json'}")

if __name__ == "__main__":
    main()
