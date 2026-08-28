"""Paper roles on the citation map: degree, PageRank, betweenness,
participation, within-community z, clustering, coreness, components,
and the community-level flow matrix.

Everything is computed on the directed graph where direction matters and on
the simple undirected projection where it does not. Age is handled by cohort
percentiles: a 1997 paper is ranked among 1997 papers. Participation is
computed over a 25-run partition ensemble as well as the canonical consensus,
because a connector whose status vanishes under reseeding is not a connector.

High PageRank means structurally influential, not evidentially validated.
"""
from __future__ import annotations
import gzip, json, re, time
from collections import Counter, defaultdict
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np

from citation_communities import load_papers
from dcm_null import directed_edges

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
REVIEW = re.compile(r'\breview\b|\bcatalog(?:ue)?\b|\bcompilation\b|a (?:decade|quarter century) of|'
                    r'\bprogress and problems\b|\bstatus report\b', re.I)

def cohort_pct(values, years):
    """percentile of each value within its publication-year cohort"""
    out = np.zeros(len(values))
    by = defaultdict(list)
    for i, y in enumerate(years):
        by[y].append(i)
    for y, idx in by.items():
        v = values[idx]
        order = v.argsort().argsort()
        out[idx] = (order + 0.5) / len(idx)
    return out

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    arcs = [(idx[a], idx[b]) for a, b, _ in de]
    gd = ig.Graph(n=len(names), edges=arcs, directed=True)   # newer -> older
    gu = gd.as_undirected(mode="collapse")                   # simple projection
    N = gd.vcount()
    years = np.array([papers[n].get("year") or 0 for n in names])
    titles = {n: ((papers[n].get("title") or [""])[0]
                  if isinstance(papers[n].get("title"), list)
                  else papers[n].get("title") or "") for n in names}
    print(f"directed {N:,} nodes {gd.ecount():,} arcs | simple {gu.ecount():,} edges",
          flush=True)

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = np.full(N, -1)
    reading = {}
    for c in canon["communities"]:
        for b in c["members"]:
            memb[idx[b]] = c["id"]
        reading[c["id"]] = ", ".join(c["terms"][:3])
    core_share = np.load(OUT / "coassign_share.npy")
    stable = core_share.max(axis=1) >= 0.90

    t0 = time.time()
    kin = np.array(gd.degree(mode="in"))     # citations received within core
    kout = np.array(gd.degree(mode="out"))   # references made within core
    pr = np.array(gd.pagerank(damping=0.85))
    pr_pct = cohort_pct(pr, years)
    kin_pct = cohort_pct(kin.astype(float), years)
    print(f"degree + pagerank         {time.time()-t0:6.1f}s", flush=True)

    t0 = time.time()
    bwd = np.array(gd.betweenness(directed=True))
    print(f"betweenness directed      {time.time()-t0:6.1f}s", flush=True)
    t0 = time.time()
    bwu = np.array(gu.betweenness(directed=False))
    print(f"betweenness undirected    {time.time()-t0:6.1f}s", flush=True)

    # review/catalogue pruning sensitivity (title proxy; every doctype is 'article')
    rev = np.array([bool(REVIEW.search(titles[n])) for n in names])
    keep = np.where(~rev)[0]
    gu_p = gu.induced_subgraph(keep.tolist())
    bwu_p_sub = np.array(gu_p.betweenness(directed=False))
    bwu_p = np.full(N, np.nan)
    bwu_p[keep] = bwu_p_sub
    print(f"pruned {rev.sum()} review/catalogue-titled papers; "
          f"top-50 undirected-betweenness overlap with full graph: "
          f"{len(set(np.argsort(bwu)[-50:]) & set(np.argsort(np.nan_to_num(bwu_p))[-50:]))}/50",
          flush=True)

    # participation coefficient: canonical + 25-run ensemble
    t0 = time.time()
    nbrs = [np.array(gu.neighbors(i)) for i in range(N)]
    def participation(mv):
        out = np.zeros(N)
        for i in range(N):
            nb = nbrs[i]
            if nb.size == 0:
                continue
            _, cnt = np.unique(mv[nb], return_counts=True)
            out[i] = 1.0 - ((cnt / nb.size) ** 2).sum()
        return out
    P_canon = participation(memb)
    from consensus import build, collapse, leiden
    h = collapse(build())
    Ps = []
    for s in range(300, 325):
        mv = np.asarray(leiden(h, s, h.es["weight"]).membership)
        Ps.append(participation(mv))
    Ps = np.array(Ps)
    P_mean, P_sd = Ps.mean(axis=0), Ps.std(axis=0)
    print(f"participation (canon+25)  {time.time()-t0:6.1f}s", flush=True)

    # within-community degree z, canonical
    kin_int = np.zeros(N)
    for a, b in gu.get_edgelist():
        if memb[a] == memb[b]:
            kin_int[a] += 1; kin_int[b] += 1
    z = np.zeros(N)
    for c in np.unique(memb):
        mk = memb == c
        mu, sd = kin_int[mk].mean(), kin_int[mk].std()
        z[mk] = (kin_int[mk] - mu) / (sd or 1.0)

    clus = np.array(gu.transitivity_local_undirected(mode="zero"))
    corev = np.array(gu.coreness())

    wcc = gu.connected_components()
    scc = gd.connected_components(mode="strong")
    scc_sizes = sorted((len(c) for c in scc), reverse=True)
    print(f"\ncomponents: giant WCC {max(len(c) for c in wcc):,}/{N:,} "
          f"({len(wcc)} components); SCCs of size>1: "
          f"{sum(1 for s in scc_sizes if s>1)} (largest {scc_sizes[0]})", flush=True)

    # community-level directed flow, observed over configuration expectation
    m = gd.ecount()
    KO = {c: kout[memb == c].sum() for c in np.unique(memb)}
    KI = {c: kin[memb == c].sum() for c in np.unique(memb)}
    obs = Counter()
    for a, b in arcs:
        obs[(int(memb[a]), int(memb[b]))] += 1
    flows = []
    for (s_, t_), o in obs.items():
        if s_ < 0 or t_ < 0 or s_ == t_ or o < 30:
            continue
        e = KO[s_] * KI[t_] / m
        flows.append(dict(src=s_, dst=t_, obs=int(o), exp=float(e),
                          log2_oe=float(np.log2(o / e))))
    flows.sort(key=lambda f: -f["log2_oe"])

    # role plane, Guimera-Amaral thresholds, restricted to stable-core papers
    hub = z >= 2.5
    conn = P_canon >= 0.62
    def toplist(score, k=15, mask=None, fmt=lambda i: ""):
        order = np.argsort(np.where(mask, score, -np.inf) if mask is not None else score)
        return [dict(bibcode=names[i], year=int(years[i]),
                     community=int(memb[i]), title=titles[names[i]][:90], **{"v": float(score[i])},
                     extra=fmt(i)) for i in order[-k:][::-1]]

    summary = dict(
        n=N, arcs=m, review_titled=int(rev.sum()),
        giant_wcc=int(max(len(c) for c in wcc)),
        n_scc_nontrivial=int(sum(1 for s in scc_sizes if s > 1)),
        top_pagerank=toplist(pr),
        top_pagerank_recent=toplist(np.where(years >= 2015, pr_pct, -1), 15),
        top_betweenness_dir=toplist(bwd),
        top_betweenness_und=toplist(bwu),
        top_betweenness_und_pruned=toplist(np.nan_to_num(bwu_p)),
        connector_hubs=toplist(np.where(hub & conn & stable, P_canon, -np.inf), 15,
                               fmt=lambda i: f"z={z[i]:.1f}"),
        provincial_hubs=toplist(np.where(hub & ~conn & stable, z, -np.inf), 15,
                                fmt=lambda i: f"P={P_canon[i]:.2f}"),
        stable_connectors=toplist(np.where(stable & (P_mean - 2*P_sd > 0.5),
                                           P_mean, -np.inf), 15,
                                  fmt=lambda i: f"P={P_mean[i]:.2f}+/-{P_sd[i]:.2f}"),
        flows_top=flows[:20], flows_bottom=flows[-10:],
        role_counts=dict(connector_hub=int((hub & conn).sum()),
                         provincial_hub=int((hub & ~conn).sum()),
                         connector_nonhub=int((~hub & conn).sum()),
                         peripheral=int((~hub & ~conn).sum())),
        role_counts_stable=dict(
            population=int((stable & (memb <= 13) & (memb >= 0)).sum()),
            connector_hub=int((hub & conn & stable & (memb <= 13)).sum()),
            provincial_hub=int((hub & ~conn & stable & (memb <= 13)).sum()),
            connector_nonhub=int((~hub & conn & stable & (memb <= 13)).sum()),
            peripheral=int((~hub & ~conn & stable & (memb <= 13)).sum()),
            absent_communities=[int(c) for c in range(14)
                                if not (stable & (memb == c)).any()]),
    )
    (OUT / "paper_roles.json").write_text(json.dumps(summary, indent=1))

    with gzip.open(OUT / "paper_roles_table.csv.gz", "wt") as fh:
        fh.write("bibcode,year,community,stable,kin,kout,kin_pct,pagerank,pr_pct,"
                 "betw_dir,betw_und,participation,P_mean,P_sd,z_within,clustering,"
                 "coreness,review_titled\n")
        for i in range(N):
            fh.write(f"{names[i]},{years[i]},{memb[i]},{int(stable[i])},{kin[i]},"
                     f"{kout[i]},{kin_pct[i]:.3f},{pr[i]:.3e},{pr_pct[i]:.3f},"
                     f"{bwd[i]:.1f},{bwu[i]:.1f},{P_canon[i]:.3f},{P_mean[i]:.3f},"
                     f"{P_sd[i]:.3f},{z[i]:.2f},{clus[i]:.3f},{corev[i]},{int(rev[i])}\n")
    print(f"\nwrote {OUT/'paper_roles.json'} and paper_roles_table.csv.gz", flush=True)

    print("\n=== top 10 PageRank (all-time) ===")
    for r in summary["top_pagerank"][:10]:
        print(f"  {r['bibcode']}  {r['year']}  C{r['community']:<3} {r['title'][:70]}")
    print("\n=== top 10 connector hubs (z>=2.5, P>=0.62, stable core) ===")
    for r in summary["connector_hubs"][:10]:
        if r["v"] == float("-inf"): continue
        print(f"  {r['bibcode']}  {r['year']}  C{r['community']:<3} P={r['v']:.2f} "
              f"{r['extra']}  {r['title'][:56]}")
    print("\n=== strongest excess community flows (log2 obs/exp) ===")
    for f in flows[:10]:
        print(f"  C{f['src']}->C{f['dst']}: {f['obs']:>5} vs {f['exp']:7.1f} "
              f"(2^{f['log2_oe']:+.2f})  [{reading[f['src']][:22]} -> {reading[f['dst']][:22]}]")

if __name__ == "__main__":
    main()
