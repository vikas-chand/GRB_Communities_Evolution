"""Corrected degree-preserving, time-respecting rewired null.

Replaces modularity_null.py, whose null was invalid. Three defects, all found by
audit and reproduced here before fixing:

  1. Duplicate rejection tested ordered (newer, older) pairs against an
     undirected graph, so a proposed (u,v) was accepted when (v,u) already
     existed. 20,432 edges (5.4%) join same-year papers and can flip
     orientation, so parallel edges were created.
  2. `simplify()` then deleted them -- ~450 edges per draw, changing the degree
     of ~620 vertices by up to 15. The null therefore did NOT preserve degree,
     which is the one property it exists to preserve.
  3. `direct_edges()` returns a set converted to a list without sorting, so the
     numpy seed acted on a Python-hash-dependent ordering and the saved
     sequence did not reproduce from cold.

Fixes: canonical undirected keys throughout, both proposals checked against the
edge set and against each other, no post-hoc simplification, and an assertion
that every draw is simple and degree-identical to the observed graph. Edges are
sorted before use so a given seed reproduces across processes.

Optimiser variation is treated as part of the measurement rather than ignored:
each graph -- observed and null alike -- is partitioned with the same multi-start
rule, and we report the spread. We report an empirical Monte Carlo p-value
alongside Delta-Q rather than a z-score, since with R draws the smallest
attainable one-sided p is 1/(R+1) and a large z presumes a calibrated tail that
has not been demonstrated.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np

from citation_communities import build_graph, direct_edges, load_papers


def canonical_edges(papers, sort=True):
    """Deterministic, sorted, canonical undirected edge list."""
    e = [tuple(sorted(p)) for p in direct_edges(papers)]
    return sorted(e) if sort else e


def best_partition(g, resolution, seeds):
    """Same multi-start rule for observed and null graphs."""
    qs = []
    for s in seeds:
        p = la.find_partition(g, la.RBConfigurationVertexPartition,
                              resolution_parameter=resolution,
                              n_iterations=-1, seed=int(s))
        qs.append(p.modularity)
    return float(np.max(qs)), qs


def rewire(newer, older, year, n_swaps, rng):
    """Degree-preserving double-edge swaps that keep citations pointing back in
    time and never create a parallel edge in either orientation."""
    m = len(newer)
    present = {frozenset((int(a), int(b))) for a, b in zip(newer, older)}
    kept = 0
    for _ in range(n_swaps):
        i, j = rng.integers(0, m, 2)
        if i == j:
            continue
        a, b, c, d = int(newer[i]), int(older[i]), int(newer[j]), int(older[j])
        if a == d or c == b:
            continue                                  # self-loop
        if year[a] < year[d] or year[c] < year[b]:
            continue                                  # citation would run forwards
        e1, e2 = frozenset((a, d)), frozenset((c, b))
        if e1 == e2 or e1 in present or e2 in present:
            continue                                  # parallel edge, either orientation
        present.discard(frozenset((a, b)))
        present.discard(frozenset((c, d)))
        present.add(e1)
        present.add(e2)
        older[i], older[j] = d, b
        kept += 1
    return kept


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path,
                    default=Path("data/raw/ads_corpus_v2_core_frozen.jsonl"))
    ap.add_argument("--tier", default="core")
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--realisations", type=int, default=50)
    ap.add_argument("--swaps-per-edge", type=int, default=10)
    ap.add_argument("--opt-seeds", type=int, default=5)
    ap.add_argument("--out", type=Path,
                    default=Path("data/communities/modularity_null_v2.json"))
    args = ap.parse_args()

    papers = load_papers(args.raw, args.tier)
    edges = canonical_edges(papers)
    g = build_graph([tuple(e) for e in edges], weighted=False)
    opt_seeds = list(range(42, 42 + args.opt_seeds))
    q_obs, q_obs_all = best_partition(g, args.resolution, opt_seeds)
    print(f"observed: {g.vcount():,} nodes, {g.ecount():,} edges, simple={not g.has_multiple()}")
    print(f"  Q over {len(opt_seeds)} optimiser starts: "
          f"{min(q_obs_all):.4f}-{max(q_obs_all):.4f}, best {q_obs:.4f}\n")

    names = g.vs["name"]; idx = {n: i for i, n in enumerate(names)}
    yr = np.array([papers[n].get("year") or 0 for n in names])
    arr = np.array([(idx[a], idx[b]) for a, b in edges if a in idx and b in idx])
    flip = yr[arr[:, 0]] < yr[arr[:, 1]]
    newer = np.where(flip, arr[:, 1], arr[:, 0])
    older = np.where(flip, arr[:, 0], arr[:, 1])
    deg_obs = np.array(g.degree())

    qs, spreads = [], []
    rng = np.random.default_rng(42)
    for r in range(args.realisations):
        nw, ol = newer.copy(), older.copy()
        kept = rewire(nw, ol, yr, args.swaps_per_edge * len(nw), rng)
        gr = ig.Graph(n=g.vcount(), edges=list(zip(nw.tolist(), ol.tolist())))
        # the null is only a null if these hold; fail loudly, never repair
        assert not gr.has_multiple(), "parallel edge created"
        assert gr.ecount() == g.ecount(), f"edge count {gr.ecount()} != {g.ecount()}"
        assert np.array_equal(np.array(gr.degree()), deg_obs), "degree not preserved"
        q, allq = best_partition(gr, args.resolution, opt_seeds)
        qs.append(q); spreads.append(max(allq) - min(allq))
        print(f"  draw {r+1:>3}/{args.realisations}: Q={q:.4f} "
              f"(optimiser spread {spreads[-1]:.4f}, {kept:,} swaps)", flush=True)

    qs = np.array(qs)
    b = int((qs >= q_obs).sum())
    p = (b + 1) / (args.realisations + 1)
    print(f"\nnull  Q = {qs.mean():.4f} +/- {qs.std(ddof=1):.4f}  "
          f"(range {qs.min():.4f}-{qs.max():.4f}, R={args.realisations})")
    print(f"obs   Q = {q_obs:.4f}")
    print(f"Delta Q = {q_obs - qs.mean():.4f}")
    print(f"empirical one-sided p = ({b}+1)/({args.realisations}+1) = {p:.4f}")
    print(f"mean optimiser spread within a graph = {np.mean(spreads):.4f}  "
          f"(null SD = {qs.std(ddof=1):.4f})")
    args.out.write_text(json.dumps({
        "q_observed": q_obs, "q_observed_starts": q_obs_all,
        "q_null": qs.tolist(), "q_null_mean": float(qs.mean()),
        "q_null_std": float(qs.std(ddof=1)), "delta_q": float(q_obs - qs.mean()),
        "R": args.realisations, "exceedances": b, "p_empirical": p,
        "mean_optimiser_spread": float(np.mean(spreads)),
        "opt_seeds": opt_seeds, "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        "corpus": str(args.raw), "tier": args.tier, "resolution": args.resolution,
    }, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
