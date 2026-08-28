"""Corpus and query metadata as a named product.

Counts are computed from the shipped manifests; the query parameters and the
partitioning objective's resolution are the frozen definitions of the
measurement, recorded here so that no figure or table carries a typed-in
constant.
"""
from __future__ import annotations
import gzip, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    def count(name: str) -> int:
        with gzip.open(ROOT / "data/raw" / name, "rt") as f:
            return sum(1 for line in f if line.strip()) - 1  # header

    meta = dict(
        query_year_min=1970, query_year_max=2026,
        gamma=1.0,
        n_core=count("core_bibcodes.tsv.gz"),
        n_cited=count("cited_bibcodes.tsv.gz"),
    )
    out = ROOT / "data/communities/corpus_meta.json"
    out.write_text(json.dumps(meta, indent=1))
    print("wrote", out, meta)


if __name__ == "__main__":
    main()
