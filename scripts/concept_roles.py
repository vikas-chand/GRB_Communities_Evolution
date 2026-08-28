"""Role-weighted concept analysis over the communities.

Combines the fixed lexicons of concept_spread.py with the per-paper role
table: (1) the median participation of each method/theory concept's stable
papers, (2) each community's concept enrichment relative to the corpus rate,
and (3) the facility/method/theory composition of each community's top ten
papers by within-community PageRank. Pure stdlib; reads the frozen corpus,
paper_roles_table.csv.gz, and the canonical consensus, whose memberships
must agree exactly with the roles table or the run fails loudly.
"""
from __future__ import annotations
import csv, gzip, json, re
import statistics as st
from collections import Counter
from pathlib import Path

import concept_spread as cs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"


def main() -> None:
    texts = {}
    with cs.CORPUS.open() as f:
        for line in f:
            d = json.loads(line)
            ti = d.get("title")
            ti = " ".join(ti) if isinstance(ti, list) else (ti or "")
            texts[d["bibcode"]] = f"{ti} {d.get('abstract') or ''}"

    rows = []
    with gzip.open(OUT / "paper_roles_table.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    ALL = {}
    for cls, lex in [("facility", cs.FACILITIES), ("method", cs.METHODS),
                     ("theory", cs.THEORY)]:
        for name, (pat, fl) in lex.items():
            ALL[(cls, name)] = re.compile(pat, fl)

    roles_memb_all = {r["bibcode"]: int(r["community"])
                      for r in rows if r["community"]}
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    canon_memb_all = {b: c["id"] for c in canon["communities"]
                      for b in c["members"]}
    if canon_memb_all != roles_memb_all:
        n_diff = len(set(canon_memb_all.items())
                     ^ set(roles_memb_all.items()))
        raise SystemExit("roles table disagrees with canonical consensus: "
                         f"{n_diff} differing entries")
    memb = {b: c for b, c in roles_memb_all.items() if 0 <= c <= 13}
    comm_n = Counter(memb.values())
    hit_by_comm = {k: Counter() for k in ALL}
    hit_total = Counter()
    for b, c in memb.items():
        t = texts.get(b, "")
        for k, rx in ALL.items():
            if rx.search(t):
                hit_by_comm[k][c] += 1
                hit_total[k] += 1
    n_linked = len(memb)

    roleprof = []
    for (cls, name), rx in ALL.items():
        if cls == "facility":
            continue
        rs = [r for r in rows if r["stable"] == "1" and r["participation"]
              and rx.search(texts.get(r["bibcode"], ""))]
        if len(rs) < 30:
            continue
        roleprof.append(dict(
            cls=cls, probe=name, n_stable=len(rs),
            median_P=round(st.median(float(r["participation"])
                                     for r in rs), 3)))
    roleprof.sort(key=lambda d: -d["median_P"])

    composition = {}
    for c in range(14):
        enr = []
        for k, cnt in hit_by_comm.items():
            if cnt[c] < 20:
                continue
            ratio = (cnt[c] / comm_n[c]) / (hit_total[k] / n_linked)
            enr.append(dict(cls=k[0], probe=k[1], n=cnt[c],
                            ratio=round(ratio, 1)))
        enr.sort(key=lambda d: -d["ratio"])
        composition[f"C{c}"] = enr[:8]

    elite = {}
    for c in range(14):
        top = sorted((r for r in rows
                      if memb.get(r["bibcode"]) == c and r["pr_local"]),
                     key=lambda r: -float(r["pr_local"]))[:10]
        share = Counter()
        for r in top:
            t = texts.get(r["bibcode"], "")
            seen = set()
            for (cls, name), rx in ALL.items():
                if cls not in seen and rx.search(t):
                    share[cls] += 1
                    seen.add(cls)
        elite[f"C{c}"] = dict(facility=share["facility"],
                              method=share["method"],
                              theory=share["theory"],
                              top_bibcodes=[r["bibcode"] for r in top])

    allP = [float(r["participation"]) for r in rows
            if r["stable"] == "1" and r["participation"]]
    product = dict(baseline_median_P=round(st.median(allP), 3),
                   baseline_n=len(allP),
                   concept_role_profiles=roleprof,
                   community_concept_enrichment=composition,
                   elite_composition=elite)
    (OUT / "concept_roles.json").write_text(json.dumps(product, indent=1))
    print("wrote", OUT / "concept_roles.json")


if __name__ == "__main__":
    main()
