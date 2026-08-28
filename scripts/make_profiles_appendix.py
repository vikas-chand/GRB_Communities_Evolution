"""SUPERSEDED: paper/appendix_profiles.tex is hand-authored (PI close-read
of the dossiers); this generator is retained for the audit trail only and
no longer reproduces the installed appendix. Do not run it to regenerate.

Appendix: one compact scientific profile per community, distilled from the
retrieval-grounded dossiers. Bibcode anchors are stripped for the print
version; the machine-readable dossiers retain every per-claim anchor.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper"

def strip(t):
    t = re.sub(r"\s*\[\d{4}[^\]]*\]", "", t)          # [bibcode; bibcode]
    t = re.sub(r"\s*\(\d{4}[A-Za-z&.]+[^)]*\)", "", t)
    t = t.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
    t = t.replace("γ", "$\\gamma$").replace("~", "$\\sim$")
    # scientific notation via placeholder so the caret escape cannot touch it
    t = re.sub(r"10\^\{?(-?\d+)\}?", r"@@POW\1@@", t)
    t = t.replace("^", "\\textasciicircum{}")
    t = re.sub(r"@@POW(-?\d+)@@", r"$10^{\1}$", t)
    # collapse adjacent math like $\sim$$10^{50}$ into one environment
    t = t.replace("$$", "")
    return re.sub(r"\s+", " ", t).strip()

ABBREV = {"vs", "al", "et", "e.g", "i.e", "cf", "no", "fig", "sgr", "grb", "z"}

def first_words(t, n):
    w = t.split()
    if len(w) <= n:
        return t
    cut = " ".join(w[:n])
    # never leave an unbalanced math environment behind
    if cut.count("$") % 2 == 1:
        cut = cut[:cut.rfind("$")].rstrip()
    best = -1
    for m in re.finditer(r"\.", cut):
        i = m.start()
        tok = cut[:i].rsplit(None, 1)[-1].lower().strip("().,")
        if tok in ABBREV or any(ch.isdigit() for ch in tok):
            continue
        best = i
    if best > 40 and cut[:best + 1].count("$") % 2 == 0:
        return cut[:best + 1]
    return cut + "\\,\\ldots"

def main():
    d = json.loads((ROOT / "dossiers/dossiers.json").read_text())
    out = []
    for x in sorted(d["dossiers"], key=lambda v: v["community_id"]):
        cid = x["community_id"]
        prob = first_words(strip(x["defining_problem"]), 55)
        res = first_words(strip(x["shaping_results"][0]), 40) if x["shaping_results"] else ""
        dis = first_words(strip(x["internal_disagreements"][0]), 45) \
            if x["internal_disagreements"] else ""
        para = (f"\\paragraph{{C{cid}: {strip(x['name'])}.}} {prob}"
                f" A result that shaped it: {res[0].lower()}{res[1:]}"
                + (f" A dispute inside it: {dis[0].lower()}{dis[1:]}" if dis else "")
                + f" ({x['activity'].split('.')[-2].strip() if x['activity'].count('.')>1 else ''})"
                )
        # cleaner: activity as its own short clause only if short
        para = (f"\\paragraph{{C{cid}: {strip(x['name'])}.}} {prob}"
                f" A result that shaped it: {res}"
                + (f" A dispute inside it: {dis}" if dis else ""))
        out.append(para)
    (OUT / "appendix_profiles.tex").write_text("\n\n".join(out) + "\n")
    print(f"wrote appendix_profiles.tex with {len(out)} profiles")

if __name__ == "__main__":
    main()
