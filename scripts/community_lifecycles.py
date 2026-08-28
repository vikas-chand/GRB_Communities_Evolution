"""Community life cycles and the supernode graph's own centralities.

Per community and year: new papers joining, and the share of the corpus's
citations made that year which point into the community (recent-citation
share). Together these are the activity evidence any claim about a programme
slowing or closing must cite. Plus PageRank, betweenness and assortativity of
the fourteen-node community graph itself.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

import igraph as ig
import numpy as np

from citation_communities import load_papers
from dcm_null import directed_edges

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = {}
    for c in canon["communities"]:
        if c["above_threshold"]:
            for b in c["members"]:
                memb[b] = c["id"]
    de = directed_edges(papers)

    # per-community, per-year: new members and incoming-citation share
    joins = defaultdict(Counter)      # cid -> year -> new papers
    cites_in = defaultdict(Counter)   # cid -> citing-year -> arcs received
    total_by_year = Counter()
    for b, cid in memb.items():
        y = papers[b].get("year") or 0
        joins[cid][y] += 1
    for a, b, y in de:
        total_by_year[y] += 1
        if b in memb:
            cites_in[memb[b]][y] += 1

    years = list(range(1973, 2027))
    out = {}
    print(f"{'community':<12}{'peak join yr':>13}{'last5 joins/yr':>16}{'peak share yr':>15}{'last5 share':>13}")
    for c in sorted(joins):
        jr = [joins[c].get(y, 0) for y in years]
        sh = [cites_in[c].get(y, 0) / total_by_year[y] if total_by_year[y] else 0
              for y in years]
        last5j = sum(jr[-6:-1]) / 5
        last5s = float(np.mean(sh[-6:-1]))
        py, ps = years[int(np.argmax(jr))], years[int(np.argmax(sh))]
        out[str(c)] = dict(years=years, new_papers=jr,
                           incoming_citation_share=[round(x, 5) for x in sh],
                           peak_join_year=py, peak_share_year=ps,
                           joins_per_yr_last5=last5j, share_last5=round(last5s, 4))
        print(f"C{c:<11}{py:>13}{last5j:>16.1f}{ps:>15}{last5s:>13.4f}")

    # supernode graph
    ids = sorted({v for v in memb.values()})
    gi = {c: k for k, c in enumerate(ids)}
    w = Counter()
    for a, b, _ in de:
        ca, cb = memb.get(a), memb.get(b)
        if ca is not None and cb is not None and ca != cb:
            w[(gi[ca], gi[cb])] += 1
    sg = ig.Graph(n=len(ids), edges=list(w), directed=True)
    sg.es["weight"] = [w[e] for e in w]
    pr = sg.pagerank(weights=sg.es["weight"])
    bw = sg.betweenness(directed=True, weights=[1 / x for x in sg.es["weight"]])
    deg_ass = sg.assortativity_degree(directed=True)
    print("\nsupernode graph (14 nodes):")
    order = np.argsort(pr)[::-1]
    for k in order[:5]:
        print(f"  C{ids[k]:<3} supernode PageRank {pr[k]:.3f}  betweenness {bw[k]:.1f}")
    print(f"  degree assortativity: {deg_ass:.3f}")
    (OUT / "community_lifecycles.json").write_text(json.dumps(dict(
        lifecycles=out,
        supernode=dict(ids=ids, pagerank=[float(x) for x in pr],
                       betweenness=[float(x) for x in bw],
                       assortativity=float(deg_ass))), indent=1))
    print(f"\nwrote {OUT/'community_lifecycles.json'}")

if __name__ == "__main__":
    main()
