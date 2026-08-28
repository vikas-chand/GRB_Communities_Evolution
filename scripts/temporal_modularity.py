"""Temporal-modularity community detection (Medo, Zeng, Zhang & Mariani 2019,
New J. Phys. 21, 093066) on the GRB citation network.

Static modularity compares the observed graph against a null that ignores time,
so it can split a genuine subject community into age cohorts. Temporal
modularity replaces that null with the dynamic configuration model:

    Q_T = (1/m) sum_ij [ A_ij - sum_l dk^out_{i,l} dk^in_{j,l} / m_l ] d(c_i,c_j)

Because every edge belongs to exactly one temporal layer, A_ij = sum_l A^(l)_ij,
and Q_T is identically the layer-weighted sum of per-layer directed
modularities with a single shared membership:

    Q_T = sum_l (m_l/m) Q_l

We verified that identity to machine precision (2e-17) on a toy network, which
means leidenalg's multiplex interface optimises exactly Q_T when the layer
weights are m_l/m. Medo et al. used an adapted Louvain; this uses Leiden's
refinement instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari
from sklearn.metrics import normalized_mutual_info_score as nmi

from citation_communities import load_papers
from dcm_null import directed_edges


def build_layers(src, dst, lay, n_nodes, L):
    graphs, weights = [], []
    m = len(src)
    for l in range(L):
        sel = lay == l
        graphs.append(ig.Graph(n=n_nodes,
                               edges=list(zip(src[sel].tolist(), dst[sel].tolist())),
                               directed=True))
        weights.append(int(sel.sum()) / m)
    return graphs, weights


def time_span(memb, order, min_size):
    """Size-weighted community time span (Medo et al. Eq. A2).

    For each community, the span between the 80th and 20th percentile of its
    members' appearance rank, weighted by community size. A partition that
    groups papers by era rather than by subject has a smaller span.
    """
    memb = np.asarray(memb)
    tot = wsum = 0.0
    for c in np.unique(memb):
        idx = np.where(memb == c)[0]
        if len(idx) < min_size:
            continue
        r = np.sort(order[idx])
        span = np.percentile(r, 80) - np.percentile(r, 20)
        wsum += len(idx) * span
        tot += len(idx)
    return wsum / tot if tot else float("nan")


def q_temporal(graphs, weights, memb):
    return sum(w * g.modularity(memb, directed=True)
               for g, w in zip(graphs, weights) if g.ecount())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path,
                    default=Path("data/raw/ads_corpus_v2_core_frozen.jsonl"))
    ap.add_argument("--tier", default="core")
    ap.add_argument("--layer-years", type=int, nargs="+", default=[1, 2, 5, 10])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--min-size", type=int, default=30)
    args = ap.parse_args()

    papers = load_papers(args.raw, args.tier)
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    src = np.array([idx[a] for a, b, y in de])
    dst = np.array([idx[b] for a, b, y in de])
    yr = np.array([y for a, b, y in de])
    N = len(names)
    print(f"{N:,} papers, {len(de):,} directed citation links\n")

    # Static comparator = directed L=1 modularity on the SAME arcs. Medo et al.
    # compare temporal modularity against the L=1 limit of the same objective on
    # the same graph; comparing against an undirected simplified graph would
    # change direction, reciprocal multiplicity and the null term at once, so
    # the resulting NMI would not isolate the temporal null.
    gs = ig.Graph(n=N, edges=list(zip(src.tolist(), dst.tolist())), directed=True)
    static = max((la.find_partition(gs, la.ModularityVertexPartition,
                                    n_iterations=-1, seed=s)
                  for s in range(42, 42 + args.seeds)),
                 key=lambda p: gs.modularity(p.membership, directed=True))
    sm = np.array(static.membership)
    ns = int(sum(1 for c in np.bincount(sm) if c >= args.min_size))
    q_static = gs.modularity(sm, directed=True)
    print(f"static directed L=1 : Q = {q_static:.4f}, "
          f"{ns} communities >= {args.min_size}\n")

    # appearance rank of each paper, for the time-span diagnostic
    y_node = np.array([papers[n].get("year") or 0 for n in names])
    appear = np.argsort(np.argsort(y_node)).astype(float)
    om_s = time_span(sm, appear, args.min_size)
    print(f"static community time span (Eq. A2): {om_s:.1f} ranks\n")

    rows = []
    for dt in args.layer_years:
        lay = (yr - yr.min()) // dt
        L = int(lay.max()) + 1
        graphs, weights = build_layers(src, dst, lay, N, L)
        best, bq = None, -np.inf
        for s in range(42, 42 + args.seeds):
            memb, _ = la.find_partition_multiplex(
                graphs, la.ModularityVertexPartition,
                layer_weights=weights, n_iterations=-1, seed=s)
            q = q_temporal(graphs, weights, memb)
            if q > bq:
                bq, best = q, np.array(memb)
        nc = int(sum(1 for c in np.bincount(best) if c >= args.min_size))
        om_t = time_span(best, appear, args.min_size)
        rows.append({"layer_years": dt, "L": L, "q_temporal": float(bq),
                     "omega_temporal": float(om_t),
                     "omega_static": float(om_s),
                     "omega_ratio": float(om_t / om_s),
                     "n_communities": nc,
                     "nmi_vs_static": float(nmi(best, sm)),
                     "ari_vs_static": float(ari(best, sm)),
                     "q_static_of_temporal_partition": float(gs.modularity(best, directed=True))})
        print(f"dT={dt:>3} yr (L={L:>3}): Q_T = {bq:.4f}   "
              f"{nc:>3} communities >= {args.min_size}   "
              f"NMI = {rows[-1]['nmi_vs_static']:.3f}  "
              f"ARI = {rows[-1]['ari_vs_static']:.3f}  "
              f"span ratio = {rows[-1]['omega_ratio']:.3f}")

    out = Path("data/communities/temporal_modularity.json")
    out.write_text(json.dumps({"static_q": q_static,
                               "static_communities": ns, "sweep": rows}, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
