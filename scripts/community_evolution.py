"""Temporal evolution of the GRB citation network's community structure.

At each cut year Y the graph is induced on papers published in or before Y,
using only citations among those papers — the field as it could have been seen
at the time, with no knowledge of the future. Leiden is re-run independently
per snapshot, then communities are threaded across snapshots by membership
overlap (Jaccard against the previous snapshot's communities).

A community with no predecessor above `--birth-threshold` is reported as new.
This is descriptive, not causal: Leiden's partition of a growing graph can
split or merge for reasons other than a change in the science, so treat splits
as hypotheses to check against the term profiles, not as established events.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import igraph as ig
import numpy as np

from citation_communities import (
    STOPWORDS,
    TOKEN,
    build_graph,
    direct_edges,
    load_papers,
    partition,
)


def snapshot_terms(members, papers, all_df, n_docs, top=8):
    from collections import Counter

    tf: Counter[str] = Counter()
    for b in members:
        d = papers[b]
        text = f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()
        for t in TOKEN.findall(text):
            if t not in STOPWORDS and len(t) > 3:
                tf[t] += 1
    total = sum(tf.values()) or 1
    scored = [
        (c / total * np.log(1 + n_docs / (1 + all_df[t])), t)
        for t, c in tf.items()
        if c >= 4
    ]
    scored.sort(reverse=True)
    return [t for _, t in scored[:top]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuts", type=int, nargs="+",
                    default=[1997, 2000, 2005, 2010, 2015, 2020, 2026])
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--min-size", type=int, default=40)
    ap.add_argument("--birth-threshold", type=float, default=0.15)
    ap.add_argument("--raw", type=Path, default=None)
    ap.add_argument("--tier", default=None, choices=["core", "cited"])
    ap.add_argument("--with-cited", type=int, default=0, metavar="N",
                    help="admit cited-tier papers cited by >=N core papers "
                         "PUBLISHED BY THE CUT YEAR (0 = core only)")
    ap.add_argument("--out", type=Path,
                    default=Path("data/communities/evolution.json"))
    args = ap.parse_args()

    papers = load_papers(args.raw, None if args.with_cited else args.tier)
    all_edges = direct_edges(papers)
    year = {b: (d.get("year") or 9999) for b, d in papers.items()}

    # Which cited-tier papers may enter a snapshot at year Y?
    #
    # A cited-tier paper is in the corpus at all because MODERN core papers
    # cite it, so admitting it to an early snapshot on that basis would leak
    # the future. Recomputing its citation count from only those core papers
    # published by Y removes that leak: a paper enters the 1990 graph only if
    # the field had already leaned on it by 1990.
    #
    # Residual caveat, stated rather than fixed: the candidate POOL was
    # downloaded using an all-time citation threshold, so work that mattered
    # in 1980 but ended up below that threshold is absent from the data
    # entirely. Only an unthresholded tier-2 fetch removes that.
    core_ids = {b for b, d in papers.items() if d.get("tier") == "core"}
    cited_by_core_year: dict[str, list[int]] = {}
    if args.with_cited:
        for b in core_ids:
            y = year[b]
            for r in papers[b].get("references") or []:
                if r in papers and r not in core_ids:
                    cited_by_core_year.setdefault(r, []).append(y)

    def eligible(cut: int) -> set[str]:
        """Papers admissible to the snapshot at `cut`, leak-free."""
        keep = {b for b in core_ids if year[b] <= cut}
        if args.with_cited:
            for r, years in cited_by_core_year.items():
                if year.get(r, 9999) <= cut and \
                        sum(1 for y in years if y <= cut) >= args.with_cited:
                    keep.add(r)
        return keep

    from collections import Counter

    # Document frequency MUST be computed inside the cut, not over the whole
    # corpus. Using corpus-wide DF to score a 1997 snapshot lets post-cut
    # documents decide which terms look distinctive then: DF("afterglow") is
    # 3,062/18,620 corpus-wide against 21/1,764 at the 1997 cut. Audited at
    # 38% of snapshot communities changing their top-8 terms when this is
    # fixed, so the terms in every published snapshot table depend on it.
    def df_upto(cut: int) -> tuple[Counter, int]:
        df: Counter[str] = Counter()
        n = 0
        for b, d in papers.items():
            if (d.get("year") or 9999) > cut:
                continue
            n += 1
            text = f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()
            for t in set(TOKEN.findall(text)):
                df[t] += 1
        return df, n

    prev: list[dict] = []
    history = []
    for cut in args.cuts:
        cut_df, cut_n = df_upto(cut)
        ok = eligible(cut)
        edges = [(a, b) for a, b in all_edges if a in ok and b in ok]
        if not edges:
            continue
        g = build_graph(edges, weighted=False)
        p = partition(g, args.resolution)
        names = g.vs["name"]

        comms = []
        for idxs in p:
            if len(idxs) < args.min_size:
                continue
            members = {names[i] for i in idxs}
            comms.append({"members": members, "size": len(members)})
        comms.sort(key=lambda c: -c["size"])

        # thread each community back to its best-overlapping predecessor
        for c in comms:
            best, best_j = None, 0.0
            for k, pc in enumerate(prev):
                inter = len(c["members"] & pc["members"])
                if not inter:
                    continue
                j = inter / len(c["members"] | pc["members"])
                if j > best_j:
                    best, best_j = k, j
            c["parent"], c["jaccard"] = best, best_j
            c["terms"] = snapshot_terms(c["members"], papers, cut_df, cut_n)

        print(f"\n=== cut {cut}  papers={g.vcount():,} edges={g.ecount():,} "
              f"communities>={args.min_size}: {len(comms)}  Q={p.modularity:.3f} ===")
        for i, c in enumerate(comms):
            if not prev:
                tag = "     "
            elif c["jaccard"] < args.birth_threshold:
                tag = " NEW "
            else:
                tag = f" <-{c['parent']:<2} "
            print(f"  [{i:<2}]{tag}n={c['size']:<5} J={c['jaccard']:.2f}  "
                  f"{', '.join(c['terms'])}")

        if prev:
            survived = {c["parent"] for c in comms if c["jaccard"] >= args.birth_threshold}
            for k, pc in enumerate(prev):
                if k not in survived:
                    print(f"  [--] GONE prev[{k}] n={pc['size']} "
                          f"({', '.join(pc['terms'][:5])}) — absorbed or dispersed")

        history.append({"cut": cut, "n_papers": g.vcount(), "n_edges": g.ecount(),
                        "modularity": p.modularity,
                        "communities": [{"size": c["size"], "terms": c["terms"],
                                         "parent": c["parent"], "jaccard": c["jaccard"]}
                                        for c in comms]})
        prev = comms

    out = args.out
    out.write_text(json.dumps(history, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
