"""Directional participation and within-community PageRank.

P_out spreads over the communities a paper CITES: how broadly it imports.
P_in spreads over the communities that CITE it: how broadly it exports.
A paper can import from everywhere and export to one field, or the reverse,
and the undirected coefficient cannot see the difference.

Within-community PageRank ranks a paper against its own community only, so a
paper foundational to quark-star models is visible even though the community
is 76 papers in a corpus of 13,801.
"""
from __future__ import annotations
import gzip, json
from pathlib import Path

import igraph as ig
import numpy as np

from citation_communities import load_papers
from dcm_null import directed_edges

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

def part_of(neigh_comms):
    if len(neigh_comms) == 0:
        return np.nan
    _, cnt = np.unique(neigh_comms, return_counts=True)
    return 1.0 - ((cnt / len(neigh_comms)) ** 2).sum()

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b, _ in de], directed=True)
    N = g.vcount()
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = np.full(N, -1)
    for c in canon["communities"]:
        for b in c["members"]:
            memb[idx[b]] = c["id"]

    Pout = np.full(N, np.nan); Pin = np.full(N, np.nan)
    for i in range(N):
        Pout[i] = part_of(memb[np.array(g.neighbors(i, mode="out"), dtype=int)]
                          if g.degree(i, mode="out") else np.array([], dtype=int))
        Pin[i] = part_of(memb[np.array(g.neighbors(i, mode="in"), dtype=int)]
                         if g.degree(i, mode="in") else np.array([], dtype=int))

    pr_local = np.full(N, np.nan); pr_local_rank = np.full(N, np.nan)
    for c in np.unique(memb):
        if c < 0:
            continue
        nodes = np.where(memb == c)[0]
        sub = g.induced_subgraph(nodes.tolist())
        pr = np.array(sub.pagerank(damping=0.85))
        pr_local[nodes] = pr
        pr_local_rank[nodes] = pr.argsort().argsort() / max(len(nodes) - 1, 1)

    # merge into the master table
    import csv, io
    with gzip.open(OUT / "paper_roles_table.csv.gz", "rt") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == N
    pos = {r["bibcode"]: r for r in rows}
    with gzip.open(OUT / "paper_roles_table.csv.gz", "wt") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) +
                           ["P_out", "P_in", "pr_local", "pr_local_rank"])
        w.writeheader()
        for i, n in enumerate(names):
            r = pos[n]
            r.update(P_out=f"{Pout[i]:.3f}", P_in=f"{Pin[i]:.3f}",
                     pr_local=f"{pr_local[i]:.3e}", pr_local_rank=f"{pr_local_rank[i]:.3f}")
            w.writerow(r)

    kin = np.array(g.degree(mode="in")); kout = np.array(g.degree(mode="out"))
    years = np.array([papers[n].get("year") or 0 for n in names])
    titles = {n: ((papers[n].get("title") or [""])[0]
                  if isinstance(papers[n].get("title"), list)
                  else papers[n].get("title") or "") for n in names}
    core_share = np.load(OUT / "coassign_share.npy")
    stable = core_share.max(axis=1) >= 0.90

    def show(label, score, mask, k=10):
        print(f"\n=== {label} ===")
        out = []
        for i in np.argsort(np.where(mask, score, -np.inf))[::-1][:k]:
            if not mask[i]:
                break
            out.append(dict(bibcode=names[i], year=int(years[i]),
                            community=int(memb[i]), v=float(score[i]),
                            title=titles[names[i]][:88]))
            print(f"  {names[i]}  {years[i]}  C{memb[i]:<3} {score[i]:.2f}  "
                  f"kin={kin[i]:<5} {titles[names[i]][:56]}")
        return out

    tops = {}
    tops["exporters"] = show("broadest exporters: P_in, cited from everywhere (kin>=100, stable)",
                             Pin, stable & (kin >= 100))
    tops["importers"] = show("broadest importers: P_out, cite everywhere (kout>=40, stable)",
                             Pout, stable & (kout >= 40))
    asym = Pin - Pout
    tops["export_asym"] = show("exporters beyond their imports: P_in - P_out (kin>=100, kout>=20, stable)",
                               asym, stable & (kin >= 100) & (kout >= 20))
    tops["import_asym"] = show("importers beyond their exports: P_out - P_in (kin>=50, kout>=40, stable)",
                               -asym, stable & (kin >= 50) & (kout >= 40))
    top_local = {}
    for c in sorted(set(memb[memb >= 0])):
        nodes = np.where(memb == c)[0]
        i = nodes[np.argmax(pr_local[nodes])]
        top_local[int(c)] = dict(bibcode=names[i], year=int(years[i]),
                                 title=titles[names[i]][:88])
    print("\n=== the founding paper of each community, by within-community PageRank ===")
    for c, r in top_local.items():
        print(f"  C{c:<3} {r['bibcode']}  {r['year']}  {r['title'][:64]}")

    (OUT / "roles_extended.json").write_text(json.dumps(
        dict(tops=tops, community_founders=top_local), indent=1))
    print(f"\nwrote roles_extended.json and updated paper_roles_table.csv.gz")

if __name__ == "__main__":
    main()
