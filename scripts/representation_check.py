"""Does the graph representation change the answer?

The canonical analysis partitions the literal undirected multigraph, in which a
reciprocal citation pair is two parallel edges. The consensus work partitions a
collapsed simple graph carrying those multiplicities as edge weights, because
co-association has to be indexed by a unique edge.

For a fixed membership the two objectives are identical, and this asserts that.
That is not sufficient for a stochastic optimiser, whose search trajectory can
differ, so we also measure how far the two representations move the partition at
matched seed, and compare that against the seed noise on either one.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import leidenalg as la
from sklearn.metrics import adjusted_rand_score as ari

from consensus import build, collapse, wq

OUT = Path(__file__).resolve().parent.parent / "data/communities"
SEEDS = range(42, 52)

def main():
    g = build(); h = collapse(g)
    print(f"multigraph {g.vcount():,} nodes {g.ecount():,} edges", flush=True)
    print(f"collapsed  {h.vcount():,} nodes {h.ecount():,} edges "
          f"(weights sum {int(sum(h.es['weight'])):,})\n", flush=True)

    # 1. fixed-membership equivalence, asserted
    probe = la.find_partition(h, la.RBConfigurationVertexPartition, weights=h.es["weight"],
                              resolution_parameter=1.0, n_iterations=2, seed=1).membership
    a, b = wq(h, probe, h.es["weight"]), g.modularity(list(probe))
    assert abs(a - b) < 1e-12, f"objectives differ for a fixed membership: {a} vs {b}"
    print(f"fixed-membership equivalence: {a:.12f} == {b:.12f}  PASS\n", flush=True)

    # 2. how far apart do the two representations land at matched seed?
    mg, mh, cross = [], [], []
    for s in SEEDS:
        pg = la.find_partition(g, la.RBConfigurationVertexPartition,
                               resolution_parameter=1.0, n_iterations=-1, seed=s)
        ph = la.find_partition(h, la.RBConfigurationVertexPartition, weights=h.es["weight"],
                               resolution_parameter=1.0, n_iterations=-1, seed=s)
        mg.append(np.asarray(pg.membership)); mh.append(np.asarray(ph.membership))
        cross.append(ari(pg.membership, ph.membership))
        print(f"  seed {s}: Q_multi={g.modularity(pg.membership):.5f}  "
              f"Q_collapsed={wq(h, ph.membership, h.es['weight']):.5f}  "
              f"cross-ARI={cross[-1]:.3f}", flush=True)

    def pairwise(ms):
        return [ari(ms[i], ms[j]) for i in range(len(ms)) for j in range(i+1, len(ms))]
    wg, wh = pairwise(mg), pairwise(mh)
    print(f"\ncross-representation ARI, matched seed : {np.mean(cross):.3f} "
          f"+/- {np.std(cross):.3f}  (n={len(cross)})")
    print(f"within multigraph, reseed              : {np.mean(wg):.3f} +/- {np.std(wg):.3f}")
    print(f"within collapsed,  reseed              : {np.mean(wh):.3f} +/- {np.std(wh):.3f}")
    verdict = ("representation moves the partition LESS than reseeding does"
               if np.mean(cross) > max(np.mean(wg), np.mean(wh))
               else "representation matters as much as or more than the seed")
    print(f"\n=> {verdict}")
    (OUT / "representation_check.json").write_text(json.dumps(dict(
        cross_mean=float(np.mean(cross)), cross_sd=float(np.std(cross)),
        multigraph_reseed_mean=float(np.mean(wg)), multigraph_reseed_sd=float(np.std(wg)),
        collapsed_reseed_mean=float(np.mean(wh)), collapsed_reseed_sd=float(np.std(wh)),
        seeds=list(SEEDS), verdict=verdict), indent=1))
    print(f"wrote {OUT/'representation_check.json'}")

if __name__ == "__main__":
    main()
