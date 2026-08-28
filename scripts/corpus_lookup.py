"""Look up the paper record for a bibcode, or search it, from the command line.

Built so that an agent auditing a historical claim reads what the corpus
actually holds instead of reciting the claim from memory. Every field returned
comes from the ADS record or the extraction of that paper's abstract.

  corpus_lookup.py get 1997Natur.387..783C
  corpus_lookup.py search "kilonova" --year 1998-2005 --limit 20
  corpus_lookup.py cited-by 1993ApJ...405..273W --limit 15
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
EXTR = ROOT / "data/extractions/all_extractions.jsonl"
IDX = ROOT / "data/extractions/.bibcode_offsets.json"

def build_index() -> dict[str, int]:
    if IDX.exists():
        return json.loads(IDX.read_text())
    off, pos = {}, 0
    with EXTR.open("rb") as fh:
        for ln in fh:
            try:
                b = json.loads(ln).get("bibcode")
                if b:
                    off[b] = pos
            except Exception:
                pass
            pos += len(ln)
    IDX.write_text(json.dumps(off))
    return off

def extraction(bib: str, idx: dict[str, int]):
    if bib not in idx:
        return None
    with EXTR.open("rb") as fh:
        fh.seek(idx[bib])
        return json.loads(fh.readline())

def load_core():
    rec = {}
    with CORE.open() as fh:
        for ln in fh:
            try:
                d = json.loads(ln)
                rec[d["bibcode"]] = d
            except Exception:
                pass
    return rec

def show(bib, core, idx, full=True):
    d = core.get(bib)
    if not d:
        print(f"{bib}: not in core corpus"); return
    print(f"=== {bib} ===")
    print(f"title : {d.get('title')}")
    print(f"pub   : {d.get('pub')} {d.get('year')}   citations: {d.get('citation_count')}")
    if full and d.get("abstract"):
        print(f"\nabstract:\n{d['abstract']}\n")
    e = extraction(bib, idx)
    if not e:
        print("(no extraction on file)"); return
    for k in ("claims", "assumptions", "results", "methods", "speculations",
              "limitations", "open_questions", "parameter_constraints",
              "population_claims"):
        v = e.get(k) or []
        if not v:
            continue
        print(f"{k} ({len(v)}):")
        for item in v[:12]:
            t = item if isinstance(item, str) else (
                item.get("text") or item.get("statement") or json.dumps(item))
            print(f"  - {t}")
        print()

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get");    g.add_argument("bibcode", nargs="+")
    g.add_argument("--brief", action="store_true")
    s = sub.add_parser("search"); s.add_argument("query")
    s.add_argument("--year"); s.add_argument("--limit", type=int, default=25)
    s.add_argument("--field", default="both", choices=["title", "abstract", "both"])
    c = sub.add_parser("cited-by"); c.add_argument("bibcode")
    c.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()

    core, idx = load_core(), build_index()
    if a.cmd == "get":
        for b in a.bibcode:
            show(b, core, idx, full=not a.brief)
    elif a.cmd == "search":
        pat = re.compile(a.query, re.I)
        lo, hi = (-9999, 9999)
        if a.year:
            p = a.year.split("-"); lo = int(p[0]); hi = int(p[-1])
        hits = []
        for b, d in core.items():
            y = d.get("year") or 0
            if not (lo <= y <= hi):
                continue
            hay = (d.get("title") or "") if a.field == "title" else (
                  (d.get("abstract") or "") if a.field == "abstract" else
                  f"{d.get('title') or ''} {d.get('abstract') or ''}")
            if pat.search(hay):
                hits.append((d.get("citation_count") or 0, y, b, d.get("title")))
        hits.sort(reverse=True)
        print(f"{len(hits)} matches, top {min(a.limit, len(hits))} by citations:\n")
        for cc, y, b, t in hits[:a.limit]:
            print(f"  {b}  {y}  cited {cc:>5}  {t}")
    elif a.cmd == "cited-by":
        n = 0
        for b, d in core.items():
            if a.bibcode in (d.get("references") or []):
                print(f"  {b}  {d.get('year')}  {d.get('title')}")
                n += 1
                if n >= a.limit:
                    break
        if not n:
            print("no citing papers found in the core tier")

if __name__ == "__main__":
    main()
