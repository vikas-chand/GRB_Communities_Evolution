"""The canonical partition, on the same graph every other measurement uses.

One graph is used throughout: the directed citation arcs from ADS reference
lists, collapsed to an undirected multigraph. Collapsing without simplifying
keeps reciprocal pairs as two edges, so that a DCM null draw and the observed
graph have identical edge count and identical undirected degree. Direction is
retained up to that point because the DCM and temporal modularity both need it.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np

from citation_communities import load_papers, STOPWORDS, TOKEN
from dcm_null import directed_edges, undirected

papers = load_papers(Path("data/raw/ads_corpus_v2_core_frozen.jsonl"), "core")
de = directed_edges(papers)
names = sorted({x for a, b, _ in de for x in (a, b)})
idx = {n: i for i, n in enumerate(names)}
src = [idx[a] for a, b, y in de]
dst = [idx[b] for a, b, y in de]
g = undirected(len(names), zip(src, dst))
print(f"canonical graph: {g.vcount():,} nodes, {g.ecount():,} edges "
      f"(multigraph, from {len(de):,} directed arcs)")

best, bq = None, -np.inf
for s in range(42, 47):
    p = la.find_partition(g, la.RBConfigurationVertexPartition,
                          resolution_parameter=1.0, n_iterations=-1, seed=s)
    if p.modularity > bq:
        bq, best = p.modularity, p
print(f"Leiden, best of 5 starts: Q = {bq:.4f}, {len(best)} communities")

all_df = Counter(); n_docs = len(papers)
for d in papers.values():
    for t in set(TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower())):
        all_df[t] += 1

deg, internal = Counter(), Counter()
memb = np.array(best.membership)
for e in g.get_edgelist():
    ca, cb = memb[e[0]], memb[e[1]]
    deg[ca] += 1; deg[cb] += 1
    if ca == cb: internal[ca] += 1

comms = []
for cid in range(len(best)):
    mem = [names[i] for i in np.where(memb == cid)[0]]
    if len(mem) < 30:
        continue
    tf = Counter()
    for b in mem:
        d = papers[b]
        for t in TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()):
            if t not in STOPWORDS and len(t) > 3:
                tf[t] += 1
    tot = sum(tf.values()) or 1
    terms = [t for _, t in sorted(((c/tot*np.log(1+n_docs/(1+all_df[t])), t)
                                   for t, c in tf.items() if c >= 5), reverse=True)[:8]]
    yrs = [papers[b].get("year") for b in mem if papers[b].get("year")]
    comms.append({"id": cid, "size": len(mem), "terms": terms,
                  "median_year": float(np.median(yrs)),
                  "year_p10": float(np.percentile(yrs, 10)),
                  "year_p90": float(np.percentile(yrs, 90)),
                  "f_int": 2*internal[cid]/deg[cid] if deg[cid] else 0.0,
                  "members": mem})
comms.sort(key=lambda c: -c["size"])
print(f"communities >= 30: {len(comms)} covering {sum(c['size'] for c in comms):,} papers\n")
for c in comms:
    print(f"  C{c['id']:<3} n={c['size']:<5} med {c['median_year']:.0f}  "
          f"f_int={c['f_int']:.2f}  {', '.join(c['terms'][:6])}")
Path("data/communities/canonical_partition.json").write_text(json.dumps(
    {"q": bq, "n_nodes": g.vcount(), "n_edges": g.ecount(),
     "n_directed_arcs": len(de), "communities": comms}, indent=1))
print("\nwrote data/communities/canonical_partition.json")
