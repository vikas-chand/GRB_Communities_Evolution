"""Fetch the GRB corpus from NASA ADS as two labelled tiers.

Tier 1 (core) is the exact-phrase seed. The original corpus used
``q="gamma-ray burst"``, whose default phrase handling does not require the
phrase to be present -- ``abs:"gamma-ray burst" title:"SS Cygni"`` returns 11
dwarf-nova papers while ``=abs:"gamma-ray burst" title:"SS Cygni"`` returns
none. All four surface forms are needed because the ``=`` operator disables
stemming, and the plural alone contributes ~3,700 papers the others miss.

Tier 2 (cited) is the papers Tier 1 cites, fetched by bibcode. Foundational
work such as Blandford & McKee (1976) or Li & Paczynski (1998) never names a
GRB in its abstract yet underpins the field, and only this tier recovers it.

Writes JSON Lines with a ``tier`` field. Resumable: re-running skips bibcodes
already present in the output file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

API = "https://api.adsabs.harvard.edu/v1/search/query"
FIELDS = ["bibcode", "title", "abstract", "author", "year", "citation_count",
          "reference", "citation", "keyword", "doctype", "identifier", "pub",
          "volume", "page", "doi", "aff", "property"]

CORE_QUERY = ('(=abs:"gamma-ray burst" OR =abs:"gamma-ray bursts" '
              'OR =abs:GRB OR =abs:GRBs)')


def token(token_file: Path | None = None) -> str:
    """ADS token, in order: $ADS_API_TOKEN, --token-file, then ./.env.

    The project's own .env token returns 401 as of 2026-08-20; pass
    --token-file to point at a working one rather than copying secrets
    between project directories.
    """
    if os.environ.get("ADS_API_TOKEN"):
        return os.environ["ADS_API_TOKEN"].strip()
    for path in [p for p in (token_file, Path(".env")) if p and p.exists()]:
        for line in path.read_text().splitlines():
            for key in ("ADS_API_TOKEN=", "ADS_DEV_KEY="):
                if line.startswith(key):
                    tok = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if tok:
                        return tok
    sys.exit("no ADS token found (set $ADS_API_TOKEN or pass --token-file)")


def get(tok: str, q: str, rows: int, start: int = 0, fields=None) -> dict:
    url = API + "?" + urllib.parse.urlencode(
        {"q": q, "fl": ",".join(fields or FIELDS), "rows": rows,
         "start": start, "sort": "bibcode asc"})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                remaining = r.headers.get("x-ratelimit-remaining")
                return json.load(r) | {"_remaining": remaining}
        except Exception as e:
            wait = 4 * (attempt + 1)
            print(f"    retry {attempt+1}/5 after {wait}s ({e})", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"gave up on: {q[:80]}")


def already(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen = set()
    with path.open() as f:
        for line in f:
            try:
                seen.add(json.loads(line)["bibcode"])
            except Exception:
                pass
    return seen


def year_shards(counts: dict[int, int], n: int) -> list[tuple[int, int]]:
    """Split the year axis into n contiguous blocks of roughly equal paper count.

    Year blocks are used rather than result offsets because offset paging is
    only safe if every collaborator gets an identical, stable sort from ADS;
    a year range is self-describing and verifiable after the fact.
    """
    years = sorted(counts)
    total = sum(counts.values())
    target = total / n
    shards, lo, run = [], years[0], 0
    for y in years:
        run += counts[y]
        if run >= target and len(shards) < n - 1:
            shards.append((lo, y))
            lo, run = y + 1, 0
    shards.append((lo, years[-1]))
    return shards


def fetch_core(tok: str, out: Path, years: str, rows: int) -> None:
    q = f"{CORE_QUERY} AND year:{years} AND doctype:article"
    total = get(tok, q, 1, fields=["bibcode"])["response"]["numFound"]
    seen = already(out)
    print(f"tier 1 core: {total:,} papers in ADS; {len(seen):,} already on disk")
    start, wrote = 0, 0
    with out.open("a") as f:
        while start < total:
            d = get(tok, q, rows, start)
            docs = d["response"]["docs"]
            if not docs:
                break
            for doc in docs:
                if doc["bibcode"] in seen:
                    continue
                doc["tier"] = "core"
                f.write(json.dumps(doc) + "\n")
                seen.add(doc["bibcode"])
                wrote += 1
            f.flush()
            start += rows
            print(f"  {min(start,total):>6,}/{total:,}  written {wrote:,}"
                  f"  quota left {d.get('_remaining')}", flush=True)
    print(f"tier 1 done: {wrote:,} new records -> {out}")


def write_targets(core_file: Path, targets_file: Path, min_cites: int) -> None:
    """Freeze the tier-2 bibcode list so every collaborator shards the same set."""
    core, counts = set(), Counter()
    rows = []
    with core_file.open() as f:
        for line in f:
            d = json.loads(line)
            if d.get("tier") == "core":
                core.add(d["bibcode"])
                rows.append(d)
    for d in rows:
        for r in d.get("reference") or []:
            if r not in core:
                counts[r] += 1
    keep = sorted(b for b, n in counts.items() if n >= min_cites)
    targets_file.write_text("\n".join(f"{b}\t{counts[b]}" for b in keep) + "\n")
    print(f"{len(counts):,} distinct cited papers outside core; "
          f"{len(keep):,} at >= {min_cites} -> {targets_file}")


def merge(out: Path) -> None:
    """Concatenate shard files, dropping duplicate bibcodes (last wins)."""
    merged, seen = [], set()
    for shard in sorted(out.parent.glob("*shard*.jsonl")) + [out]:
        if not shard.exists():
            continue
        n = 0
        with shard.open() as f:
            for line in f:
                d = json.loads(line)
                if d["bibcode"] in seen:
                    continue
                seen.add(d["bibcode"])
                merged.append(line)
                n += 1
        print(f"  {shard.name:<28} +{n:,} new")
    final = out.parent / "ads_corpus_merged.jsonl"
    final.write_text("".join(merged))
    print(f"merged {len(merged):,} unique records -> {final}")


def fetch_cited(tok: str, out: Path, min_cites: int, batch: int,
                targets_file: Path | None = None,
                shard: int | None = None, of: int | None = None) -> None:
    if targets_file and targets_file.exists():
        targets = [l.split("\t")[0] for l in
                   targets_file.read_text().splitlines() if l.strip()]
        counts = {l.split("\t")[0]: int(l.split("\t")[1]) for l in
                  targets_file.read_text().splitlines() if "\t" in l}
    else:
        core, counts = set(), Counter()
        rows = []
        with out.open() as f:
            for line in f:
                d = json.loads(line)
                if d.get("tier") == "core":
                    core.add(d["bibcode"]); rows.append(d)
        for d in rows:
            for r in d.get("reference") or []:
                if r not in core:
                    counts[r] += 1
        targets = sorted(b for b, n in counts.items() if n >= min_cites)
    if shard is not None and of:
        # md5 rather than hash(): Python salts str hashing per process, so
        # hash() would give different splits on different machines.
        import hashlib
        targets = [b for b in targets
                   if int(hashlib.md5(b.encode()).hexdigest(), 16) % of == shard]
        print(f"shard {shard}/{of}: {len(targets):,} bibcodes")
    seen = already(out)
    targets = [b for b in targets if b not in seen]
    print(f"tier 2: {len(counts):,} distinct cited papers outside core; "
          f"{len(targets):,} at >= {min_cites} core citations still to fetch")
    wrote = 0
    with out.open("a") as f:
        for i in range(0, len(targets), batch):
            chunk = targets[i:i + batch]
            q = "bibcode:(" + " OR ".join(chunk) + ")"
            d = get(tok, q, len(chunk))
            for doc in d["response"]["docs"]:
                doc["tier"] = "cited"
                doc["core_citations"] = int(counts.get(doc["bibcode"], 0))
                f.write(json.dumps(doc) + "\n")
                wrote += 1
            f.flush()
            print(f"  {min(i+batch,len(targets)):>6,}/{len(targets):,}"
                  f"  written {wrote:,}  quota left {d.get('_remaining')}", flush=True)
    print(f"tier 2 done: {wrote:,} new records -> {out}")


def plan(tok: str, years: str, n: int) -> None:
    """Print a shard table collaborators can run without further coordination."""
    lo, hi = (int(x) for x in years.split("-"))
    counts = {}
    for y in range(lo, hi + 1):
        q = f"{CORE_QUERY} AND year:{y} AND doctype:article"
        c = get(tok, q, 1, fields=["bibcode"])["response"]["numFound"]
        if c:
            counts[y] = c
    shards = year_shards(counts, n)
    total = sum(counts.values())
    print(f"tier 1: {total:,} papers over {len(counts)} years -> {n} shards\n")
    print(f"{'shard':<6} {'years':<14} {'papers':>8} {'~requests':>10}  command")
    for i, (a, b) in enumerate(shards):
        k = sum(v for y, v in counts.items() if a <= y <= b)
        print(f"  {i:<4} {f'{a}-{b}':<14} {k:>8,} {-(-k//200):>10}  "
              f"python scripts/fetch_corpus.py --stage core --years {a}-{b} "
              f"--out data/raw/core_shard{i}.jsonl")
    print(f"\ntier 2 shards use --shard i --of {n} on the target list "
          f"(hash split; run after merging tier 1).")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["core", "cited", "probe", "plan", "targets", "merge"],
                    default="probe")
    ap.add_argument("--out", type=Path, default=Path("data/raw/ads_corpus_v2.jsonl"))
    ap.add_argument("--years", default="1900-2026")
    ap.add_argument("--rows", type=int, default=200)
    ap.add_argument("--min-cites", type=int, default=5)
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--token-file", type=Path, default=None)
    ap.add_argument("--shard", type=int, default=None, help="this shard index")
    ap.add_argument("--of", type=int, default=None, help="total shards")
    ap.add_argument("--targets", type=Path, default=Path("data/raw/tier2_targets.txt"))
    args = ap.parse_args()
    tok = token(args.token_file)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if args.stage == "probe":
        q = f"{CORE_QUERY} AND year:{args.years} AND doctype:article"
        d = get(tok, q, 3)
        print(f"query   : {q}")
        print(f"numFound: {d['response']['numFound']:,}")
        print(f"quota   : {d.get('_remaining')} requests left today\n")
        for doc in d["response"]["docs"]:
            print(f"  {doc['bibcode']}  {doc.get('year')}  "
                  f"refs={len(doc.get('reference') or []):<4} "
                  f"cites={len(doc.get('citation') or []):<5} "
                  f"{(doc.get('title') or ['?'])[0][:58]}")
        size = len(json.dumps(d["response"]["docs"][0]))
        print(f"\n~{size/1024:.1f} KB per record → "
              f"~{size*15652/1024/1024:.0f} MB for tier 1")
    elif args.stage == "plan":
        plan(tok, args.years, args.of or 5)
    elif args.stage == "targets":
        write_targets(args.out, args.targets, args.min_cites)
    elif args.stage == "merge":
        merge(args.out)
    elif args.stage == "core":
        fetch_core(tok, args.out, args.years, args.rows)
    else:
        fetch_cited(tok, args.out, args.min_cites, args.batch,
                    args.targets, args.shard, args.of)


if __name__ == "__main__":
    main()
