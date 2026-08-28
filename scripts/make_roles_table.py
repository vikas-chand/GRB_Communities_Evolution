"""The named-papers table: abridged for the manuscript, full for the repo.

Emits paper/table5_roles.tex (five categories, five rows each, every value
from products) and docs/roles_table.md (the extended rankings: top 25 per
category plus exporters, importers, and per-community founders). The tex
paper column cites via CITEKEY (natbib keys backed by ADS-exported
bibitems in the manuscript); the md keeps raw bibcodes. Author strings
for the md come from the frozen corpus.
"""
from __future__ import annotations
import csv, gzip, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / "data/communities"
CORPUS = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"

# natbib keys in paper/grb_communities.tex, all from ADS aastex exports
CITEKEY = {
    "1973ApJ...182L..85K": "klebesadel1973",
    "1986ApJ...308L..43P": "paczynski1986",
    "1986ApJ...308L..47G": "goodman1986",
    "1992Natur.355..143M": "meegan1992",
    "1997Natur.386..686V": "vanparadijs1997",
    "2024Natur.626..737L": "levan2024",
    "2025A&A...701A.134M": "malesani2025",
    "2023ApJ...952L..42L": "lesage2023",
    "2018Natur.561..355M": "mooley2018",
    "2022Natur.612..223R": "rastinejad2022",
    "1993ApJ...405..273W": "woosley1993",
    "2006ARA&A..44..507W": "woosleybloom2006",
    "2005SSRv..120..143B": "barthelmy2005",
    "2004ApJ...611.1005G": "gehrels2004",
    "2002A&A...390...81A": "amati2002",
    "2017PhRvL.119p1101A": "abbott2017gw",
    "2017ApJ...848L..13A": "abbott2017grb",
    "2017ApJ...848L..12A": "abbott2017mma",
    "2014ARA&A..52...43B": "berger2014",
    "1990ARA&A..28..401H": "higdon1990",
    "1993ApJ...413..281B": "band1993",
    "1993ApJ...413L.101K": "kouveliotou1993",
    "2004RvMP...76.1143P": "piran2004",
}

NAME = {0: "BATSE era", 1: "afterglows", 2: "mergers", 3: "prompt",
        4: "high energy", 5: "collapsars", 6: "hosts", 7: "cosmology",
        8: "LIV", 9: "TGFs", 10: "fireshell", 11: "dark matter",
        12: "bio", 13: "quark stars"}


def short_cite(meta):
    au = meta.get("author") or ["?"]
    first = au[0].split(",")[0]
    first = re.sub(r"[{}\\]", "", first)
    tail = " et al." if len(au) > 2 else (" \\& " + re.sub(r"[{}\\]", "", au[1].split(",")[0]) if len(au) == 2 else "")
    return f"{first}{tail} ({meta.get('year')})"


def main() -> None:
    meta = {}
    with CORPUS.open() as f:
        for line in f:
            d = json.loads(line)
            meta[d["bibcode"]] = d
    rows = []
    with gzip.open(COM / "paper_roles_table.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    bycode = {r["bibcode"]: r for r in rows}
    pr = json.loads((COM / "paper_roles.json").read_text())
    rex = json.loads((COM / "roles_extended.json").read_text())

    # Selection and formatting of hub rows use the FULL-PRECISION product
    # (roles_fullprecision.py); the master CSV is display-rounded and must
    # never be re-thresholded or re-rounded.
    fp = {}
    with gzip.open(COM / "paper_roles_fullprec.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            fp[r["bibcode"]] = r
    stable = [r for r in fp.values() if r["stable"] == "1"
              and 0 <= int(r["community"]) <= 13]
    conn = sorted((r for r in stable if float(r["z_within"]) >= 2.5
                   and float(r["participation"]) >= 0.62),
                  key=lambda r: -float(r["participation"]))
    prov = sorted((r for r in stable if float(r["z_within"]) >= 2.5
                   and float(r["participation"]) < 0.62),
                  key=lambda r: -float(r["z_within"]))

    def cell(b, metric):
        r = bycode.get(b, {})
        c = NAME.get(int(r["community"]), "--") if r.get("community") else "--"
        key = CITEKEY[b]
        return f"\\citet{{{key}}} & {c} & {metric} \\\\"

    K = 5
    sections = []
    sections.append(("Founding influence (global PageRank)", [
        cell(x["bibcode"], f"rank {i+1}")
        for i, x in enumerate(pr["top_pagerank"][:K])]))
    sections.append(("Modern landmarks (2015 on, cohort-percentile PageRank)", [
        cell(x["bibcode"], f"rank {i+1}")
        for i, x in enumerate(pr["top_pagerank_recent"][:K])]))
    def hubcell(r):
        return cell(r["bibcode"], f"$z={float(r['z_within']):.1f}$, "
                                  f"$P={float(r['participation']):.2f}$")

    sections.append(("Connector hubs ($z \\geq 2.5$, highest $P$)",
                     [hubcell(r) for r in conn[:K]]))
    sections.append(("Provincial hubs ($z \\geq 2.5$, $P < 0.62$)",
                     [hubcell(r) for r in prov[:K]]))
    sections.append(("Bridges (betweenness, review-pruned)", [
        cell(x["bibcode"], f"rank {i+1}")
        for i, x in enumerate(pr["top_betweenness_und_pruned"][:K])]))

    tex = []
    for si, (title, lines) in enumerate(sections):
        pad = "" if si == 0 else "[3pt]\n"
        tex.append(pad + f"\\textbf{{{title}}} & & \\\\[1pt]")
        tex.extend(lines)
    (ROOT / "paper/table5_roles.tex").write_text("\n".join(tex) + "\n")

    # ---- full version for the repository ----
    md = ["# The map's named papers — extended rankings",
          "",
          "Abridged in the manuscript in preparation; every value from the released",
          "products (`paper_roles.json`, `roles_extended.json`,",
          "`paper_roles_table.csv.gz`, which carries all 22 metrics for all",
          "13,800 papers; hub selection and the z/P values shown come from the",
          "full-precision `paper_roles_fullprec.csv.gz`).", ""]

    def mdsec(title, entries):
        md.extend([f"## {title}", "",
                   "| paper | bibcode | community | metric |",
                   "|---|---|---|---|"])
        for b, metric in entries:
            m = meta.get(b, {})
            r = bycode.get(b, {})
            c = NAME.get(int(r["community"]), "--") if r.get("community") else "--"
            t = (m.get("title") or "?")
            t = (t if isinstance(t, str) else t[0])[:60]
            md.append(f"| {short_cite(m).replace('\\&','&')} — {t} | {b} | {c} | {metric} |")
        md.append("")

    mdsec("Founding influence (global PageRank, top 15)",
          [(x["bibcode"], f"rank {i+1}") for i, x in enumerate(pr["top_pagerank"][:25])])
    mdsec("Modern landmarks (2015 on, cohort-percentile PageRank, top 15)",
          [(x["bibcode"], f"rank {i+1}") for i, x in enumerate(pr["top_pagerank_recent"][:25])])
    mdsec(f"Connector hubs — the complete threshold population "
          f"($z \\geq 2.5$, $P \\geq 0.62$; n={len(conn)})",
          [(r["bibcode"], f"z={float(r['z_within']):.1f}, P={float(r['participation']):.2f}")
           for r in conn])
    mdsec(f"Provincial hubs — the complete threshold population "
          f"($z \\geq 2.5$, $P < 0.62$; n={len(prov)})",
          [(r["bibcode"], f"z={float(r['z_within']):.1f}, P={float(r['participation']):.2f}")
           for r in prov])
    mdsec("Bridges (review-pruned betweenness, top 15)",
          [(x["bibcode"], f"rank {i+1}") for i, x in enumerate(pr["top_betweenness_und_pruned"][:25])])
    mdsec("Exporters (highest $P_{in}$ minus $P_{out}$ asymmetry)",
          [(x["bibcode"], f"asym {x['v']:.2f}") for x in rex["tops"]["export_asym"][:15]])
    mdsec("Importers",
          [(x["bibcode"], f"asym {x['v']:.2f}") for x in rex["tops"]["import_asym"][:15]])
    pn = json.loads((COM / "pagerank_null.json").read_text())
    mdsec("Null-adjusted influence (largest excesses among the 319 papers "
          "above all 20 DCM draws with $k_{in} \\geq 50$; the product "
          "stores the top 15 — the full set is recomputable from "
          "pagerank_null.py)",
          [(x["bibcode"], f"excess {x['excess']:.2f}")
           for x in pn["top_excess_influential"]])
    def ga_census(pool):
        out = dict(R5=0, R6=0, R7=0)
        for r in pool:
            try:
                z_ = float(r["z_within"]); P_ = float(r["participation"])
            except (TypeError, ValueError):
                continue
            if z_ < 2.5:
                continue
            out["R5" if P_ <= 0.30 else ("R6" if P_ <= 0.75 else "R7")] += 1
        return out
    ca, cs = ga_census(rows), ga_census(stable)
    md.extend(["## Strict Guimer\u00e0\u2013Amaral seven-role hub census", "",
               "The paper uses a two-class hub split at P = 0.62 (disclosed as",
               "a coarsening in the Methods). Under the original hub classes",
               "(provincial P <= 0.30 < connector <= 0.75 < kinless):", "",
               "| population | R5 provincial | R6 connector | R7 kinless |",
               "|---|---|---|---|",
               f"| all linked | {ca['R5']} | {ca['R6']} | {ca['R7']} |",
               f"| stable cores | {cs['R5']} | {cs['R6']} | {cs['R7']} |", ""])
    md.append("## Community founders (highest within-community PageRank)")
    md.append("")
    md.append("| community | founder | bibcode |")
    md.append("|---|---|---|")
    for c, lst in sorted(rex["community_founders"].items(),
                         key=lambda kv: int(kv[0])):
        if int(c) > 13:
            continue
        b = (lst[0] if isinstance(lst, list) else lst)["bibcode"]
        m = meta.get(b, {})
        md.append(f"| C{c} {NAME.get(int(c),'')} | "
                  f"{short_cite(m).replace('\\&','&')} | {b} |")
    (ROOT / "docs/roles_table.md").write_text("\n".join(md) + "\n")
    print("wrote paper/table5_roles.tex and docs/roles_table.md")


if __name__ == "__main__":
    main()
