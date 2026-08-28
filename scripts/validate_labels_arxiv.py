"""Check community labels against arXiv primary categories.

The primary category is chosen by the authors at submission. It knows nothing
about our citation graph or the title/abstract terms we labelled with, so
agreement between the two is external evidence that a community means what we
say it means.

Reported per community: the category mix, and the enrichment of each category
over its corpus-wide share. A label that is right should sit on a category the
community is enriched in.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import normalized_mutual_info_score as nmi

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / "data/communities"

READING = {
    0: "BATSE-era distance scale", 1: "afterglows", 2: "compact mergers, short GRBs",
    3: "prompt emission, radiation physics", 4: "high-energy neutrinos",
    5: "collapsars, GRB-SNe", 6: "host galaxies",
    7: "luminosity correlations, cosmology", 8: "Lorentz-invariance tests",
    9: "terrestrial gamma-ray flashes", 10: "fireshell / BdHN school",
    11: "dark matter", 12: "biological effects at Earth", 13: "quark/strange-star models",
}

def main():
    ids = json.loads((COM / "arxiv_ids.json").read_text())
    meta = {}
    with (COM / "arxiv_meta.jsonl").open() as fh:
        for ln in fh:
            r = json.loads(ln)
            if r.get("primary"):
                meta[r["arxiv"]] = r["primary"]
    canon = json.loads((COM / "canonical_consensus.json").read_text())
    shown = [c for c in canon["communities"] if c["above_threshold"]]

    cat_of = {b: meta[a] for b, a in ids.items() if a in meta}
    print(f"{len(cat_of):,} core papers carry an arXiv primary category\n")

    overall = Counter(cat_of.values())
    tot = sum(overall.values())
    print("corpus-wide top categories:")
    for c, n in overall.most_common(6):
        print(f"  {c:<18} {n:>6,}  {n/tot:5.1%}")

    labels, cats, rows = [], [], []
    print("\nper community, categories enriched over their corpus share:\n")
    for c in shown:
        cid = c["id"]
        mem = [cat_of[b] for b in c["members"] if b in cat_of]
        if not mem:
            continue
        labels += [cid] * len(mem); cats += mem
        cnt = Counter(mem); n = len(mem)
        enr = sorted(((v / n) / (overall[k] / tot), k, v)
                     for k, v in cnt.items() if v >= max(3, 0.02 * n))
        top = [f"{k} {v/n:.0%} (x{e:.1f})" for e, k, v in reversed(enr[-3:])]
        rows.append(dict(id=cid, reading=READING[cid], n_with_cat=n,
                         coverage=n / c["size"],
                         top=[{"cat": k, "share": v / n, "enrichment": e}
                              for e, k, v in reversed(enr[-3:])]))
        print(f"  C{cid:<3} {READING[cid]:<36} [{n:>4}/{c['size']:<4} {n/c['size']:3.0%}]")
        print(f"        {' | '.join(top)}")

    score = nmi(labels, cats)
    print(f"\nNMI between our partition and arXiv primary category: {score:.3f}")
    print(f"  (over {len(labels):,} papers, {len(set(cats))} distinct categories)")
    (COM / "label_validation_arxiv.json").write_text(json.dumps(
        dict(nmi=float(score), n_papers=len(labels),
             n_categories=len(set(cats)), communities=rows), indent=1))
    print(f"\nwrote {COM/'label_validation_arxiv.json'}")

if __name__ == "__main__":
    main()
