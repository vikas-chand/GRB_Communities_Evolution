"""Dynamic configuration model (DCM) null for the GRB citation network.

Ren, Mariani, Zhang & Medo (2018), PRE 97, 052311. The static configuration
model preserves in- and out-degree but ignores time, so it produces citations
running forward in time. The DCM additionally preserves each node's degree
*trajectory*: the timeline is cut into L layers of equal duration, and within
layer n the model preserves every node's in- and out-degree increments
dk_in[i,n], dk_out[i,n], randomising only which citing paper reached which
cited paper inside that layer.

Two deliberate departures from the published procedure, both because this
project has already been bitten once:

  * The paper matches stubs at random and then DISCARDS the resulting
    self-loops and multi-edges. Discarding breaks exact degree preservation,
    which is the defect that invalidated our first null. We instead repair them
    with within-layer double-edge swaps, which preserve dk_in and dk_out
    exactly, and we assert the degree trajectory afterwards.

  * We keep the real ADS citation direction rather than inferring it from
    publication year. Direction is only collapsed at the very end, so that the
    null graph is built exactly the way the observed graph is.

The observed graph is rebuilt here by the same route (directed -> collapse,
without simplification) so the comparison is like-for-like. Reciprocal pairs
therefore survive as parallel edges in both the observed and the null graph.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np

from citation_communities import load_papers


def directed_edges(papers: dict) -> list[tuple[str, str, int]]:
    """(citing, cited, year_of_citing) using the real ADS reference direction."""
    out = []
    for b, d in papers.items():
        y = d.get("year")
        if not y:
            continue
        for r in d.get("references") or []:
            if r in papers and r != b:
                out.append((b, r, int(y)))
    return sorted(set(out))


def undirected(n: int, pairs) -> ig.Graph:
    """Collapse direction WITHOUT simplifying.

    Simplifying merges reciprocal pairs (i->j and j->i) into one edge. The
    observed graph has 1,529 such pairs and a null draw only ~170, so
    simplifying leaves the two graphs with different edge counts (+0.36%) and
    different undirected degrees on 14% of nodes -- the same defect class that
    invalidated the project's first null. Keeping the multigraph makes
    m = 380,362 and the undirected degree sequence identical by construction.
    """
    return ig.Graph(n=n, edges=[(int(a), int(b)) for a, b in pairs], directed=False)


def _dcm_layer_once(src, dst, rng, max_repair=400):
    """Randomise one layer, preserving each node's in/out stub counts exactly.

    Stub matching first, then double-edge swaps to remove self-loops and
    duplicates. A swap exchanges the targets of two edges, so out-degree and
    in-degree of every node are invariant by construction.
    """
    from collections import Counter

    s = src.copy()
    d = dst.copy()
    rng.shuffle(d)                       # random out-stub / in-stub matching
    m = len(s)
    if m < 2:
        return s, d
    # A Counter of held directed keys, maintained incrementally. An earlier
    # version used a set with an asymmetric discard, which left 149 phantom and
    # 135 missing entries per draw -- rejecting valid swaps and accepting
    # invalid ones. The outer rescan absorbed it, but it was wrong.
    held = Counter(zip(s.tolist(), d.tolist()))
    for _ in range(max_repair):
        bad = [k for k in range(m)
               if s[k] == d[k] or held[(int(s[k]), int(d[k]))] > 1]
        if not bad:
            break
        for k in bad:
            for _try in range(200):
                j = int(rng.integers(0, m))
                if j == k:
                    continue
                sk, dk, sj, dj = int(s[k]), int(d[k]), int(s[j]), int(d[j])
                if sk == dj or sj == dk:
                    continue                       # would make a self-loop
                if held[(sk, dj)] or held[(sj, dk)]:
                    continue                       # would make a duplicate
                held[(sk, dk)] -= 1
                held[(sj, dj)] -= 1
                d[k], d[j] = d[j], d[k]
                held[(sk, dj)] += 1
                held[(sj, dk)] += 1
                break
    return s, d


def best_q(g, resolution, seeds):
    return max(la.find_partition(g, la.RBConfigurationVertexPartition,
                                 resolution_parameter=resolution,
                                 n_iterations=-1, seed=int(s)).modularity
               for s in seeds)


def dcm_layer(src, dst, rng, max_repair=400, attempts=25):
    """Randomise one layer, retrying the whole layer if repair cannot finish.

    Small or highly constrained layers can reach a state where no single
    double-edge swap removes the last duplicate. Rather than abort the draw --
    or, worse, accept a defective layer -- we reshuffle that layer and try
    again. Each attempt is an independent stub matching, so retrying does not
    bias the ensemble; it only rejects matchings that cannot be repaired.
    """
    for _ in range(attempts):
        s, d = _dcm_layer_once(src, dst, rng, max_repair)
        if int((s == d).sum()) == 0 and len(s) == len(set(zip(s.tolist(), d.tolist()))):
            return s, d
    raise RuntimeError(
        f"layer of {len(src)} edges could not be repaired in {attempts} attempts")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path,
                    default=Path("data/raw/ads_corpus_v2_core_frozen.jsonl"))
    ap.add_argument("--tier", default="core")
    ap.add_argument("--layer-years", type=int, default=1)
    ap.add_argument("--realisations", type=int, default=20)
    ap.add_argument("--opt-seeds", type=int, default=5)
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    papers = load_papers(args.raw, args.tier)
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    src = np.array([idx[a] for a, b, y in de])
    dst = np.array([idx[b] for a, b, y in de])
    yr = np.array([y for a, b, y in de])
    seeds = list(range(42, 42 + args.opt_seeds))

    y_of = {idx[n]: (papers[n].get("year") or 0) for n in names}

    def fwd_count(a, b, ymap):
        """citations running forward in nominal years -- a metadata-error rate"""
        return int(sum(1 for u, v in zip(a.tolist(), b.tolist())
                       if ymap[u] < ymap[v]))

    g_obs = undirected(len(names), zip(src, dst))
    deg_obs = np.array(g_obs.degree())
    recip_obs = len(src) - len({frozenset((int(a), int(b)))
                                for a, b in zip(src.tolist(), dst.tolist())})
    fwd_obs = fwd_count(src, dst, y_of)
    q_obs = best_q(g_obs, args.resolution, seeds)
    print(f"observed (directed {len(de):,} refs -> undirected multigraph): "
          f"{g_obs.vcount():,} nodes, {g_obs.ecount():,} edges, Q = {q_obs:.4f}")

    lo, hi = yr.min(), yr.max()
    layer = (yr - lo) // args.layer_years
    L = int(layer.max()) + 1
    print(f"layers: {L} of {args.layer_years} yr ({lo}-{hi}), "
          f"median layer size {int(np.median(np.bincount(layer))):,} edges")
    print(f"observed: reciprocal pairs {recip_obs:,}, "
          f"forward-in-time {fwd_obs/len(src):.3%}\n")

    # reference degree trajectory, to assert against
    def trajectory(s, d, lay):
        t = defaultdict(int)
        for a, b, n in zip(s, d, lay):
            t[("o", int(a), int(n))] += 1
            t[("i", int(b), int(n))] += 1
        return t
    traj_obs = trajectory(src, dst, layer)

    rng = np.random.default_rng(42)
    qs = []
    for r in range(args.realisations):
        ns, nd = src.copy(), dst.copy()
        for n in range(L):
            m = layer == n
            if m.sum() < 2:
                continue
            a, b = dcm_layer(src[m], dst[m], rng)
            ns[m], nd[m] = a, b
        # Assertions that can fail. The trajectory check alone is nearly
        # vacuous: a draw with 3.1% defective edges still passes it, because it
        # only detects edge DELETION. These three detect what actually goes
        # wrong.
        assert trajectory(ns, nd, layer) == traj_obs, "degree trajectory not preserved"
        assert int((ns == nd).sum()) == 0, "residual self-loops"
        assert len(ns) == len(set(zip(ns.tolist(), nd.tolist()))), \
            "residual duplicate directed edges"
        g_null = undirected(len(names), zip(ns, nd))
        assert np.array_equal(np.array(g_null.degree()), deg_obs), \
            "undirected degree not preserved on the graph Q is measured on"
        recip = len(ns) - len({frozenset((int(a), int(b)))
                               for a, b in zip(ns.tolist(), nd.tolist())})
        fwd = fwd_count(ns, nd, y_of)
        q = best_q(g_null, args.resolution, seeds)
        qs.append(q)
        print(f"  draw {r+1:>2}/{args.realisations}: Q={q:.4f}  "
              f"edges {g_null.ecount():,} (obs {g_obs.ecount():,})  "
              f"reciprocal {recip:,} (obs {recip_obs:,})  "
              f"forward-in-time {fwd/len(ns):.3%} (obs {fwd_obs/len(ns):.3%})",
              flush=True)

    qs = np.array(qs)
    b = int((qs >= q_obs).sum())
    print(f"\nDCM null (dT={args.layer_years} yr): Q = {qs.mean():.4f} "
          f"+/- {qs.std(ddof=1):.4f} (range {qs.min():.4f}-{qs.max():.4f})")
    print(f"observed: Q = {q_obs:.4f}   Delta Q = {q_obs - qs.mean():.4f}")
    print(f"empirical one-sided p = ({b}+1)/({args.realisations}+1) = "
          f"{(b+1)/(args.realisations+1):.4f}")
    out = args.out or Path(f"data/communities/dcm_null_dT{args.layer_years}.json")
    out.write_text(json.dumps({
        "layer_years": args.layer_years, "L": L, "q_observed": q_obs,
        "q_null": qs.tolist(), "q_null_mean": float(qs.mean()),
        "q_null_std": float(qs.std(ddof=1)),
        "delta_q": float(q_obs - qs.mean()),
        "p_empirical": (b + 1) / (args.realisations + 1),
        "R": args.realisations, "opt_seeds": seeds,
        "n_directed_edges": len(de), "n_undirected_obs": g_obs.ecount(),
    }, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
