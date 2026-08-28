"""Redistributable graph layer for the public repository.

ADS terms do not permit bulk redistribution of abstracts, so the frozen
corpus stays local. What can be released is our derived product: the
core-to-core citation arcs the analysis is built on, plus minimal
bibliographic metadata (bibcode, year, first author, title, doctype, tier)
sufficient to identify every node. With these two files every notebook stage
that starts from the graph can be reproduced; only TF-IDF labelling and the
concept sweep, which read abstracts, require a refetched corpus.
"""
from __future__ import annotations
import gzip, json
from pathlib import Path

from citation_communities import load_papers
from dcm_null import directed_edges

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/graph"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    nodes = sorted({x for a, b, _ in de for x in (a, b)})
    with gzip.open(OUT / "core_arcs.tsv.gz", "wt") as f:
        f.write("citing\tcited\n")
        for a, b, _ in sorted(de):
            f.write(f"{a}\t{b}\n")
    with gzip.open(OUT / "core_nodes.tsv.gz", "wt") as f:
        f.write("bibcode\tyear\tfirst_author\ttitle\tdoctype\n")
        for b in nodes:
            d = papers[b]
            t = d.get("title"); t = (t[0] if isinstance(t, list) and t else (t or "")).replace("\t", " ").replace("\n", " ")
            au = d.get("author") or [""]
            f.write(f"{b}\t{d.get('year','')}\t{au[0]}\t{t}\t{d.get('doctype','')}\n")
    manifest = dict(n_nodes=len(nodes), n_arcs=len(de),
                    note="core-to-core citation arcs of the frozen 1970-2026 corpus; abstracts withheld per ADS terms")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(manifest)


if __name__ == "__main__":
    main()
