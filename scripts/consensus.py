"""Seed noise floor, and a consensus partition that removes it.

Two things live here.

  floor      Leiden is stochastic. Two runs on the *identical* graph already
             disagree. Measuring that disagreement gives the band against which
             every perturbation test has to be read: a corpus ablation that
             moves the partition less than a reseed does has not moved it.

  consensus  Lancichinetti & Fortunato (2012, Sci. Rep. 2, 336). Run Leiden R
             times, weight each edge by the fraction of runs whose endpoints
             shared a community, drop edges below tau, repartition, repeat until
             two successive rounds agree exactly. The fixed point does not
             depend on any single seed.

The consensus graph is built only on edges already present, so it stays sparse;
pairs that were never adjacent cannot be joined by consensus alone.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import igraph as ig, leidenalg as la, numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi
from citation_communities import load_papers
from dcm_null import directed_edges, undirected

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT  = ROOT / "data/communities"

def leiden(g, seed, weights=None, n_iter=-1):
    return la.find_partition(g, la.RBConfigurationVertexPartition, weights=weights,
                             resolution_parameter=1.0, n_iterations=n_iter, seed=seed)

def wq(g, memb, weights=None):
    """Weighted modularity. igraph's VertexClustering.modularity and leidenalg's
    .modularity property both ignore edge weights, so on the collapsed graph they
    return the simple-graph value. The weighted value is what equals modularity
    on the literal multigraph, which is the estimand this project reports."""
    return g.modularity(list(memb), weights=weights)

def best_of(g, seeds, weights=None, n_iter=-1):
    return max((leiden(g, s, weights, n_iter) for s in seeds),
               key=lambda p: wq(g, p.membership, weights))

def build():
    papers = load_papers(CORE, "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return g

def collapse(g):
    """multigraph -> simple graph with multiplicity as weight (same modularity)"""
    h = g.copy()
    h.es["weight"] = 1.0
    h.simplify(combine_edges={"weight": "sum"})
    return h

def consensus(h, seeds, tau=0.5, max_rounds=8):
    """returns (membership, rounds_used, converged)"""
    base = np.asarray(h.es["weight"], float)
    w = base.copy()
    prev = None
    edges = np.asarray(h.get_edgelist())
    for r in range(1, max_rounds + 1):
        parts = [np.asarray(leiden(h, s, list(w), n_iter=2).membership) for s in seeds]
        agree = np.mean([p[edges[:, 0]] == p[edges[:, 1]] for p in parts], axis=0)
        # the round's own answer: partition the co-association weighting
        wc = base * np.where(agree >= tau, agree, 0.0)
        if not wc.any():
            return prev, r, False
        memb = np.asarray(best_of(h, seeds, list(wc), n_iter=2).membership)
        if prev is not None and ari(prev, memb) > 0.9999:
            return np.asarray(best_of(h, seeds, list(wc)).membership), r, True
        prev, w = memb, wc
    return prev, max_rounds, False

def sizes(m, floor=30):
    return sorted((c for c in np.bincount(m) if c >= floor), reverse=True)

def main():
    g = build()
    h = collapse(g)
    print(f"graph: {h.vcount():,} papers, {h.ecount():,} distinct pairs, "
          f"{int(sum(h.es['weight'])):,} citations\n")

    blocks = [range(b, b + 5) for b in (42, 142, 242, 342, 442)]

    print("=== seed noise floor: best-of-5 Leiden, identical graph ===")
    runs = []
    for b in blocks:
        p = best_of(h, b, h.es["weight"])
        m = np.asarray(p.membership)
        runs.append(m)
        print(f"  seeds {b.start:>3}-{b.start+4:<3} Q={wq(h, m, h.es['weight']):.4f}  "
              f"{len(sizes(m))} communities >=30  largest={sizes(m)[:4]}", flush=True)
    pa = [ari(runs[i], runs[j]) for i in range(len(runs)) for j in range(i+1, len(runs))]
    pn = [nmi(runs[i], runs[j]) for i in range(len(runs)) for j in range(i+1, len(runs))]
    print(f"  pairwise ARI {np.mean(pa):.3f} +/- {np.std(pa):.3f}  "
          f"(range {min(pa):.3f}-{max(pa):.3f})")
    print(f"  pairwise NMI {np.mean(pn):.3f} +/- {np.std(pn):.3f}\n")

    print("=== consensus over 15 seeds, tau=0.5 ===", flush=True)
    cons = []
    for b in [range(42, 57), range(542, 557), range(1042, 1057)]:
        m, r, ok = consensus(h, list(b), tau=0.5)
        q = wq(h, m, h.es["weight"])
        cons.append(m)
        print(f"  seeds {b.start:>4}+  converged={ok} in {r} rounds  "
              f"Q={q:.4f}  {len(sizes(m))} communities >=30  largest={sizes(m)[:4]}", flush=True)
    ca = [ari(cons[i], cons[j]) for i in range(len(cons)) for j in range(i+1, len(cons))]
    cn = [nmi(cons[i], cons[j]) for i in range(len(cons)) for j in range(i+1, len(cons))]
    print(f"  pairwise ARI {np.mean(ca):.3f} +/- {np.std(ca):.3f}  "
          f"(range {min(ca):.3f}-{max(ca):.3f})")
    print(f"  pairwise NMI {np.mean(cn):.3f} +/- {np.std(cn):.3f}")

    out = dict(nodes=h.vcount(), pairs=h.ecount(),
               floor=dict(ari_mean=float(np.mean(pa)), ari_sd=float(np.std(pa)),
                          ari_min=float(min(pa)), ari_max=float(max(pa)),
                          nmi_mean=float(np.mean(pn)), nmi_sd=float(np.std(pn))),
               consensus=dict(ari_mean=float(np.mean(ca)), ari_sd=float(np.std(ca)),
                              ari_min=float(min(ca)), ari_max=float(max(ca)),
                              nmi_mean=float(np.mean(cn)), nmi_sd=float(np.std(cn)),
                              n_communities=len(sizes(cons[0])),
                              sizes=[int(x) for x in sizes(cons[0])]))
    Path(OUT / "consensus.json").write_text(json.dumps(out, indent=1))
    np.save(OUT / "consensus_membership.npy", cons[0])
    Path(OUT / "consensus_names.json").write_text(json.dumps(h.vs["name"]))
    print(f"\nwrote {OUT/'consensus.json'}")

if __name__ == "__main__":
    main()
