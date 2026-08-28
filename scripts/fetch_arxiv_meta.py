"""Fetch arXiv metadata for every core paper that has an arXiv identifier.

The primary category is the point of this. It is assigned by the authors on
submission, so it is independent of the citation graph we partitioned and of the
title/abstract terms we labelled the communities with. That makes it usable as an
external check on whether a community means what we say it means.

Batched through the arXiv API at its documented rate, cached to disk, resumable.
"""
from __future__ import annotations
import json, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS = ROOT / "data/communities/arxiv_ids.json"
OUT = ROOT / "data/communities/arxiv_meta.jsonl"
API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
BATCH = 100
PAUSE = 3.0          # arXiv asks for one request per three seconds
UA = "AstroGraph/1.0 (community-label validation; vikas.chand.physics@gmail.com)"

def parse(xml: str) -> list[dict]:
    root = ET.fromstring(xml)
    out = []
    for e in root.findall("a:entry", NS):
        # the id is a URL like http://arxiv.org/abs/astro-ph/9204003v1 or
        # http://arxiv.org/abs/1234.5678v2; splitting on the LAST slash destroys
        # the archive prefix of every legacy id, so split on /abs/ instead
        url = e.findtext("a:id", "", NS) or ""
        aid = url.split("/abs/", 1)[-1] if "/abs/" in url else url.rsplit("/", 1)[-1]
        if not aid:
            continue
        prim = e.find("arxiv:primary_category", NS)
        out.append({
            "arxiv": aid.rsplit("v", 1)[0] if aid[-1:].isdigit() and "v" in aid[max(0,len(aid)-4):] else aid,
            "primary": prim.get("term") if prim is not None else None,
            "categories": [c.get("term") for c in e.findall("a:category", NS)],
            "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
            "abstract": " ".join((e.findtext("a:summary", "", NS) or "").split()),
            "published": e.findtext("a:published", "", NS),
        })
    return out

def main():
    ids = json.loads(IDS.read_text())
    want = sorted(set(ids.values()))
    done = set()
    if OUT.exists():
        for ln in OUT.read_text().splitlines():
            if ln.strip():
                done.add(json.loads(ln)["arxiv"])
    todo = [a for a in want if a not in done]
    print(f"{len(want):,} distinct arXiv ids, {len(done):,} cached, {len(todo):,} to fetch",
          flush=True)

    with OUT.open("a") as fh:
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            url = f"{API}?" + urllib.parse.urlencode(
                {"id_list": ",".join(chunk), "max_results": len(chunk)})
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": UA})
                    xml = urllib.request.urlopen(req, timeout=90).read().decode()
                    rows = parse(xml)
                    break
                except Exception as exc:
                    if attempt == 3:
                        print(f"  batch {i//BATCH}: giving up ({exc})", flush=True)
                        rows = []
                    else:
                        time.sleep(5 * (attempt + 1))
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            fh.flush()
            got = sum(1 for r in rows if r.get("primary"))
            print(f"  batch {i//BATCH + 1}/{(len(todo)+BATCH-1)//BATCH}: "
                  f"{got}/{len(chunk)} with a primary category", flush=True)
            time.sleep(PAUSE)
    print("done", flush=True)

if __name__ == "__main__":
    main()
