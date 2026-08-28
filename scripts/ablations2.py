"""Ablations measured against a consensus partition, with per-community detail.

The first ablation pass compared single Leiden runs, so its ARI mixed two
effects: the corpus change, and the algorithm's own run-to-run spread. Fixing
the baseline to a consensus fixed point removes the second, and what is left is
attributable to the papers that were removed.

Every ablated graph is partitioned by the same consensus procedure as the
baseline, so the two sides of each comparison are produced identically.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import igraph as ig
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi

from citation_communities import load_papers, STOPWORDS, TOKEN
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, sizes, wq
from ablations import GRB, HOMONYM, ASTRO

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"
SEEDS = list(range(42, 62))          # 20 seeds per consensus
MIN = 30

def build(papers, drop=frozenset()):
    de = [(a, b, y) for a, b, y in directed_edges(papers) if a not in drop and b not in drop]
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return collapse(g)

def label(mem, papers, all_df, n_docs, k=4):
    tf = Counter()
    for b in mem:
        d = papers[b]
        for t in TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()):
            if t not in STOPWORDS and len(t) > 3:
                tf[t] += 1
    tot = sum(tf.values()) or 1
    return [t for _, t in sorted(((c / tot * np.log(1 + n_docs / (1 + all_df[t])), t)
                                  for t, c in tf.items() if c >= 5), reverse=True)[:k]]

def main():
    papers = load_papers(CORE, "core")
    n_docs = len(papers)
    all_df = Counter()
    for d in papers.values():
        for t in set(TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower())):
            all_df[t] += 1

    h0 = build(papers)
    m0, r0, ok0 = consensus(h0, SEEDS)
    n0 = h0.vs["name"]
    q0 = wq(h0, m0, h0.es["weight"])
    big = [c for c in np.unique(m0) if (m0 == c).sum() >= MIN]
    big.sort(key=lambda c: -(m0 == c).sum())
    print(f"consensus baseline: {h0.vcount():,} papers, Q={q0:.4f}, "
          f"{len(big)} communities >={MIN} (converged={ok0} in {r0} rounds)\n")
    labels = {}
    for c in big:
        mem = [n0[i] for i in np.where(m0 == c)[0]]
        labels[int(c)] = label(mem, papers, all_df, n_docs)
        print(f"  C{c:<3} n={len(mem):<5} {', '.join(labels[int(c)])}")

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    homonym = {b for b, d in papers.items()
               if HOMONYM.search(text(d)) and not ASTRO.search(text(d))}
    kwonly = {b for b, d in papers.items() if not GRB.search(text(d))}
    norefs = {b for b, d in papers.items() if not (d.get("references") or [])}
    unref = {b for b, d in papers.items() if "REFEREED" not in (d.get("property") or [])}

    i0 = {n: k for k, n in enumerate(n0)}
    rows = []
    for lab, drop in [("homonym screen", homonym), ("keyword-only", kwonly),
                      ("no reference list", norefs), ("non-refereed", unref),
                      ("keyword-only + homonym", kwonly | homonym)]:
        h = build(papers, drop)
        m, r, ok = consensus(h, SEEDS)
        nn = h.vs["name"]
        i1 = {n: k for k, n in enumerate(nn)}
        shared = sorted(set(n0) & set(nn))
        a = ari([m0[i0[n]] for n in shared], [m[i1[n]] for n in shared])
        v = nmi([m0[i0[n]] for n in shared], [m[i1[n]] for n in shared])
        nm = {n: c for n, c in zip(nn, m)}
        surv = {}
        for c in big:
            mem = [n0[i] for i in np.where(m0 == c)[0]]
            dest = [nm[n] for n in mem if n in nm]
            surv[int(c)] = (float(np.bincount(dest).max() / len(mem)) if dest else 0.0,
                            len(mem))
        nbig = sum(1 for x in np.bincount(m) if x >= MIN)
        q = wq(h, m, h.es["weight"])
        rows.append(dict(label=lab, dropped=len(drop), nodes=h.vcount(), q=q,
                         communities=nbig, ari=a, nmi=v, rounds=r, converged=bool(ok),
                         survival={str(k): v2 for k, v2 in surv.items()}))
        print(f"\n{lab:<24} drop {len(drop):>5}  {h.vcount():>6,} papers  "
              f"Q={q:.4f}  {nbig:>2} comm  ARI={a:.3f}  NMI={v:.3f}")
        for c in big:
            f, n = surv[int(c)]
            flag = "  <-- breaks" if f < 0.5 else ""
            print(f"     C{c:<3} n={n:<5} retains {f:5.0%}  "
                  f"{', '.join(labels[int(c)][:3])}{flag}")

    (OUT / "ablations_consensus.json").write_text(json.dumps(
        dict(baseline=dict(q=q0, nodes=h0.vcount(), communities=len(big),
                           labels={str(k): v for k, v in labels.items()},
                           sizes={str(int(c)): int((m0 == c).sum()) for c in big}),
             ablations=rows), indent=1))
    print(f"\nwrote {OUT/'ablations_consensus.json'}")

if __name__ == "__main__":
    main()
