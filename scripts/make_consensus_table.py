"""Table of the consensus communities, and the numbers the text quotes about them.

Readings in the last column are ours. The dagger marking literature that is not
about gamma-ray bursts is not a judgement call: it is applied where fewer than
half the members mention a burst anywhere in their title or abstract.
"""
from __future__ import annotations
import json, re
from pathlib import Path

import numpy as np

from citation_communities import load_papers

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper"
GRB = re.compile(r'gamma[\s\-]?ray burst|\bGRB', re.I)

READING = {
    0: "BATSE-era distance scale", 1: "afterglows",
    2: "compact mergers, short GRBs", 3: "prompt emission, radiation physics",
    4: "high-energy neutrinos", 5: "collapsars, GRB--SNe",
    6: "host galaxies", 7: "luminosity correlations, cosmology",
    8: "Lorentz-invariance tests", 9: "terrestrial $\\gamma$-ray flashes",
    10: "fireshell / BdHN school", 11: "dark matter",
    12: "biological effects at Earth", 13: "quark/strange-star models",
}

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    part = json.loads((ROOT / "data/communities/canonical_consensus.json").read_text())
    shown = [c for c in part["communities"] if c["above_threshold"]]
    assert set(READING) == {c["id"] for c in shown}, "reading/community mismatch"

    rows, fints, mentions = [], [], []
    for c in sorted(shown, key=lambda c: -c["size"]):
        cid = c["id"]
        hits = sum(1 for b in c["members"]
                   if GRB.search(f"{papers[b].get('title') or ''} "
                                 f"{papers[b].get('abstract') or ''}"))
        frac = hits / c["size"]
        mark = "$^{\\dagger}$" if frac < 0.5 else ""
        terms = ", ".join(c["terms"][:5]).replace("_", "\\_")
        rows.append(f"C{cid} & {c['size']} & {c['median_year']:.0f} & "
                    f"{c['year_p10']:.0f}--{c['year_p90']:.0f} & "
                    f"{c['f_int']:.2f} & {frac:.2f} & {terms} & "
                    f"{READING[cid]}{mark} \\\\")
        fints.append(c["f_int"]); mentions.append(frac)
        print(f"  C{cid:<3} n={c['size']:<5} f_int={c['f_int']:.2f}  "
              f"GRB mention {frac:.0%}  {READING[cid]}{'  <- dagger' if mark else ''}")

    (OUT / "table1_communities.tex").write_text("\n".join(rows) + "\n")
    print(f"\nf_int spans {min(fints):.2f}--{max(fints):.2f}")
    print(f"GRB-mention fraction spans {min(mentions):.0%}--{max(mentions):.0%}")
    print(f"communities below 50% mention: "
          f"{sum(1 for m in mentions if m < 0.5)} of {len(mentions)}")
    print(f"\nwrote {OUT/'table1_communities.tex'}")

if __name__ == "__main__":
    main()
