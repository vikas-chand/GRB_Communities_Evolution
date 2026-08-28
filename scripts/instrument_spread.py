"""How each major facility's literature distributes over the communities.

No instrument forms a community: every facility's papers spread across the
topical partition, which is why mission papers surface as connector hubs. The
one useful summary number per facility is its concentration, the share of its
papers in its single largest community.
"""
from __future__ import annotations
import json, re
from collections import Counter
from pathlib import Path

from citation_communities import load_papers

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

PROBES = {
    # Fermi: exclude conceptual physics uses (Fermi acceleration, Fermi-Dirac...)
    "Fermi": (r"\bFermi\b(?![ -]?(?:Dirac|acceleration|accelerated|energy|energies|"
              r"gas|surface|momentum|level|sea|motion|coordinates|liquid|golden))", re.I),
    "Fermi-GBM": (r"\bGBM\b", 0), "Fermi-LAT": (r"\bLAT\b", 0),
    "Swift": (r"\bSwift\b", re.I),
    "BeppoSAX": (r"BeppoSAX|Beppo-SAX", re.I), "BATSE": (r"\bBATSE\b", re.I),
    "Einstein Probe": (r"Einstein Probe", re.I),
    "VLA": (r"\bVLA\b|Very Large Array", 0), "ALMA": (r"\bALMA\b", 0),
    "VLT": (r"\bVLT\b", 0), "JWST": (r"\bJWST\b", 0),
    "HST": (r"\bHST\b|Hubble Space Telescope", 0),
    "IceCube": (r"IceCube", re.I), "LHAASO": (r"LHAASO", re.I),
    "MAGIC/HESS/CTA": (r"\bMAGIC\b|\bH\.E\.S\.S\.|\bCTA\b", 0),
    # Virgo the detector, not the cluster
    "LIGO/Virgo": (r"\bLIGO\b|\bVirgo\b(?!\s+[Cc]luster)", 0),
    "AstroSat/CZTI": (r"AstroSat|CZTI", re.I), "POLAR": (r"\bPOLAR\b", 0),
}


def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb, reading = {}, {}
    for c in canon["communities"]:
        for b in c["members"]:
            memb[b] = c["id"]
        reading[c["id"]] = ", ".join(c["terms"][:2])
    def txt(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    rows = []
    for name, (pat, flags) in PROBES.items():
        rx = re.compile(pat, flags)
        hits = [b for b, d in papers.items() if rx.search(txt(d))]
        linked = [memb[b] for b in hits if b in memb and memb[b] >= 0
                  and memb[b] <= 13]
        cnt = Counter(linked)
        top = cnt.most_common(4)
        conc = top[0][1] / len(linked) if linked else 0.0
        conc_all = top[0][1] / len(hits) if hits and top else 0.0
        rows.append(dict(facility=name, n_papers=len(hits), n_linked=len(linked),
                         concentration_linked=round(conc, 3),
                         concentration_all=round(conc_all, 3),
                         top=[[int(c), int(n)] for c, n in top]))
        spread = ", ".join(f"C{c} {n}" for c, n in top)
        print(f"  {name:<16} {len(hits):>5} hits / {len(linked):>5} linked  "
              f"top-share {conc:4.0%} (linked) {conc_all:4.0%} (all)   {spread}")
    sub = json.loads((OUT / "subcommunities.json").read_text())
    c3 = next(x for x in sub if x["parent"] == 3)
    child = next(k for k in c3["children"] if "polarization" in k["terms"])
    mem = set(child["members"])
    rx_p = re.compile(r"\bPOLAR\b")
    rx_a = re.compile(r"AstroSat|CZTI", re.I)
    pol = dict(child_size=len(mem),
               polar_corpus=sum(1 for b, d in papers.items() if rx_p.search(txt(d))),
               polar_in_child=sum(1 for b in mem if rx_p.search(txt(papers[b]))),
               czti_corpus=sum(1 for b, d in papers.items() if rx_a.search(txt(d))),
               czti_in_child=sum(1 for b in mem if rx_a.search(txt(papers[b]))))
    print(f"  polarimetry child: POLAR {pol['polar_in_child']}/{pol['polar_corpus']}, "
          f"AstroSat/CZTI {pol['czti_in_child']}/{pol['czti_corpus']} (case-insensitive)")
    (OUT / "instrument_spread.json").write_text(json.dumps(
        dict(readings={str(k): v for k, v in reading.items()}, rows=rows,
             polarimetry_child=pol), indent=1))
    print(f"\nwrote {OUT/'instrument_spread.json'}")

if __name__ == "__main__":
    main()
