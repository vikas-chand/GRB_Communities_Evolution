"""The canonical partition, from consensus rather than from one lucky seed.

A single Leiden run on this graph agrees with another single run at ARI ~0.63,
so no one run can be quoted as the partition. This produces the consensus
partition at R = 30, the setting with the highest measured reproducibility, and
characterises it the same way `canonical_partition.py` characterised the
single-run result: class-based TF-IDF terms, year distribution, and the fraction
of citation stubs internal to each community.

Every group is written out, not only those above the display threshold, so that
downstream figures can account for all 13,801 vertices instead of silently
dropping the ones below it.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import numpy as np

from citation_communities import load_papers, STOPWORDS, TOKEN
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, wq

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"
R = 30
SEEDS = list(range(42, 42 + R))
MIN = 30

def main():
    papers = load_papers(CORE, "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    h = collapse(g)
    print(f"canonical graph: {g.vcount():,} nodes, {g.ecount():,} edges "
          f"(multigraph, from {len(de):,} directed arcs)", flush=True)

    memb, rounds, ok = consensus(h, SEEDS)
    if not ok:
        raise RuntimeError(f"consensus did not converge in {rounds} rounds")
    memb = np.asarray(memb)
    q = wq(h, memb, h.es["weight"])
    ngroups = int(len(np.unique(memb)))
    big = [c for c in np.unique(memb) if (memb == c).sum() >= MIN]
    print(f"consensus R={R}: converged in {rounds} rounds, Q = {q:.4f}, "
          f"{ngroups} groups, {len(big)} with N >= {MIN}", flush=True)

    all_df = Counter(); n_docs = len(papers)
    for d in papers.values():
        for t in set(TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower())):
            all_df[t] += 1

    deg, internal = Counter(), Counter()
    for a, b in g.get_edgelist():
        ca, cb = memb[a], memb[b]
        deg[ca] += 1; deg[cb] += 1
        if ca == cb:
            internal[ca] += 1

    comms = []
    for cid in np.unique(memb):
        mem = [names[i] for i in np.where(memb == cid)[0]]
        tf = Counter()
        for b in mem:
            d = papers[b]
            for t in TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()):
                if t not in STOPWORDS and len(t) > 3:
                    tf[t] += 1
        tot = sum(tf.values()) or 1
        terms = [t for _, t in sorted(((c / tot * np.log(1 + n_docs / (1 + all_df[t])), t)
                                       for t, c in tf.items() if c >= 5), reverse=True)[:8]]
        yrs = [papers[b].get("year") for b in mem if papers[b].get("year")]
        comms.append({"id": int(cid), "size": len(mem), "terms": terms,
                      "median_year": float(np.median(yrs)) if yrs else None,
                      "year_p10": float(np.percentile(yrs, 10)) if yrs else None,
                      "year_p90": float(np.percentile(yrs, 90)) if yrs else None,
                      "f_int": 2 * internal[cid] / deg[cid] if deg[cid] else 0.0,
                      "above_threshold": len(mem) >= MIN,
                      "members": mem})
    comms.sort(key=lambda c: -c["size"])
    shown = [c for c in comms if c["above_threshold"]]
    print(f"\ncommunities >= {MIN}: {len(shown)} covering "
          f"{sum(c['size'] for c in shown):,} of {g.vcount():,} papers "
          f"({g.vcount() - sum(c['size'] for c in shown)} below threshold)\n")
    for c in shown:
        print(f"  C{c['id']:<3} n={c['size']:<5} med {c['median_year']:.0f}  "
              f"f_int={c['f_int']:.2f}  {', '.join(c['terms'][:6])}")

    (OUT / "canonical_consensus.json").write_text(json.dumps(
        {"q": q, "R": R, "rounds": rounds, "tau": 0.5, "min_size": MIN,
         "n_nodes": g.vcount(), "n_edges": g.ecount(), "n_directed_arcs": len(de),
         "n_groups": ngroups, "n_above_threshold": len(shown),
         "communities": comms}, indent=1))
    print(f"\nwrote {OUT/'canonical_consensus.json'}")

if __name__ == "__main__":
    main()
