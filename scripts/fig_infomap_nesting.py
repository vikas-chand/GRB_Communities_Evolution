"""Appendix figure: how Infomap's finer partition nests inside the map.

One horizontal bar per canonical community (length = membership); coloured
segments are the Infomap blocks of at least thirty papers nested inside it,
grey is the remainder in smaller fragments. Right margin: block count and,
for the eight sub-community parents, the NMI against our sub-communities.
All values load from products.
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / "data/communities"
FIG = ROOT / "paper/figures"

NAME = {0: "BATSE era", 1: "afterglows", 2: "mergers", 3: "prompt",
        4: "high energy", 5: "collapsars", 6: "hosts", 7: "cosmology",
        8: "LIV", 9: "TGFs", 10: "fireshell", 11: "dark matter",
        12: "bio", 13: "quark stars"}
BLUE, LIGHT, GREY = "#3b6ea5", "#9db8d6", "#d0d0d0"


def main() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 14, "mathtext.fontset": "stix",
        "xtick.direction": "in", "ytick.direction": "in",
        "savefig.dpi": 300, "savefig.facecolor": "white",
        "figure.facecolor": "white"})
    sub = json.loads((COM / "infomap_subdivision.json").read_text())
    canon = json.loads((COM / "canonical_consensus.json").read_text())
    sizes = {c["id"]: len(c["members"]) for c in canon["communities"]
             if c["id"] <= 13 and len(c["members"]) >= 30}
    agree = {r["parent"]: r["nmi"] for r in sub["parent_agreement"]}

    order = sorted(sizes, key=lambda c: -sizes[c])
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    for row, cid in enumerate(order):
        y = len(order) - 1 - row
        x = 0.0
        blocks = sub["subdivision"][f"C{cid}"]
        for k, (_, n) in enumerate(blocks):
            ax.barh(y, n, left=x, height=0.72,
                    color=BLUE if k % 2 == 0 else LIGHT,
                    edgecolor="white", linewidth=0.6)
            x += n
        rest = sizes[cid] - x
        if rest > 0:
            ax.barh(y, rest, left=x, height=0.72, color=GREY,
                    edgecolor="white", linewidth=0.6)
        nb = len(blocks)
        note = f"{nb} block" + ("s" if nb != 1 else "")
        if cid in agree:
            note += f", NMI {agree[cid]:.2f}"
        ax.text(sizes[cid] + 30, y, note, va="center", fontsize=11.5,
                color="0.25")
    ax.set_yticks([len(order) - 1 - r for r in range(len(order))])
    ax.set_yticklabels([f"C{c} {NAME[c]}" for c in order], fontsize=12.5)
    ax.set_xlabel("papers")
    ax.set_xlim(0, max(sizes.values()) * 1.32)
    ax.tick_params(top=True, right=False, which="both")
    ax.spines[["right", "top"]].set_visible(True)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"figF_infomap_nesting.{ext}",
                    bbox_inches="tight", pad_inches=0.03)
    print("wrote", FIG / "figF_infomap_nesting.pdf/.png")


if __name__ == "__main__":
    main()
