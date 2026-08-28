"""One recursive level: sub-structure inside each large community.

Only communities of at least 500 papers are recursed, only one level, and a
child is reported only if it is structurally reproducible: two independent
consensus runs on the parent's induced subgraph must agree, and the child must
hold at least 30 papers. Labels are TF-IDF within the parent, so a child is
described by what distinguishes it from its siblings, not from the corpus.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score as ari

from citation_communities import load_papers, STOPWORDS, TOKEN
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, wq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
MINPARENT, MINCHILD = 500, 30

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    h = collapse(g)
    canon = json.loads((OUT / "canonical_consensus.json").read_text())

    out = []
    for c in canon["communities"]:
        if not c["above_threshold"] or c["size"] < MINPARENT:
            continue
        nodes = [h.vs.find(name=b).index for b in c["members"]]
        sub = h.induced_subgraph(nodes)
        sn = sub.vs["name"]
        m1, _, ok1 = consensus(sub, list(range(42, 52)))
        m2, _, ok2 = consensus(sub, list(range(542, 552)))
        rep = float(ari(m1, m2))
        m1 = np.asarray(m1)
        # per-parent document frequency for within-parent TF-IDF
        df = Counter(); nd = len(sn)
        docs = {}
        for b in sn:
            d = papers[b]
            toks = [t for t in TOKEN.findall(
                f"{d.get('title') or ''} {d.get('abstract') or ''}".lower())
                    if t not in STOPWORDS and len(t) > 3]
            docs[b] = toks
            for t in set(toks):
                df[t] += 1
        kids = []
        for k in np.unique(m1):
            mem = [sn[i] for i in np.where(m1 == k)[0]]
            if len(mem) < MINCHILD:
                continue
            tf = Counter()
            for b in mem:
                tf.update(docs[b])
            tot = sum(tf.values()) or 1
            terms = [t for _, t in sorted(
                ((cnt / tot * np.log(1 + nd / (1 + df[t])), t)
                 for t, cnt in tf.items() if cnt >= 5), reverse=True)[:6]]
            yrs = [papers[b].get("year") for b in mem if papers[b].get("year")]
            kids.append(dict(size=len(mem), terms=terms,
                             median_year=float(np.median(yrs)),
                             members=mem))
        kids.sort(key=lambda x: -x["size"])
        out.append(dict(parent=c["id"], parent_size=c["size"],
                        replicate_ari=rep, converged=bool(ok1 and ok2),
                        q=float(wq(sub, m1, sub.es["weight"])),
                        n_children=len(kids), children=kids))
        print(f"C{c['id']} (n={c['size']:,}) replicate ARI {rep:.3f}  "
              f"{len(kids)} children >= {MINCHILD}:", flush=True)
        for k in kids:
            print(f"    {k['size']:>5}  med {k['median_year']:.0f}  "
                  f"{', '.join(k['terms'][:5])}", flush=True)
    (OUT / "subcommunities.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT/'subcommunities.json'}")

if __name__ == "__main__":
    main()
