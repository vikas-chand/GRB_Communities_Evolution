"""Main-text figure: the 57 named sub-communities of the eight parents.

Small multiples, one panel per parent: children as horizontal bars (length
= membership), labelled by the curated readings of Table C1. Panel headers
carry the parent name, the consensus replicate ARI, and the NMI of the
independent Infomap subdivision where it applies. All quantities load from
products; readings import from the table producer.
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec

from make_subcommunity_table import PARENT, READING

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / "data/communities"
FIG = ROOT / "paper/figures"
BLUE = "#3b6ea5"


def main() -> None:
    plt.rcParams.update({
        "font.family": "serif", "font.size": 12, "mathtext.fontset": "stix",
        "xtick.direction": "in", "ytick.direction": "in",
        "savefig.dpi": 300, "savefig.facecolor": "white",
        "figure.facecolor": "white"})
    sub = json.loads((COM / "subcommunities.json").read_text())
    nmi = {r["parent"]: r["nmi"]
           for r in json.loads((COM / "infomap_subdivision.json").read_text())
           ["parent_agreement"]}

    order = sorted(range(len(sub)),
                   key=lambda i: sub[i].get("parent", sub[i].get("id")))
    left = order[0::2]
    right = order[1::2]
    fig = plt.figure(figsize=(12.8, 10.6))
    outer = gridspec.GridSpec(1, 2, wspace=0.52, left=0.215, right=0.985,
                              top=0.975, bottom=0.045)
    for col, idxs in enumerate((left, right)):
        heights = [len(sub[i]["children"]) + 1.15 for i in idxs]
        inner = gridspec.GridSpecFromSubplotSpec(
            len(idxs), 1, subplot_spec=outer[col],
            height_ratios=heights, hspace=0.55)
        for row, i in enumerate(idxs):
            p = sub[i]
            pid = p.get("parent", p.get("id"))
            ch = p["children"]
            ax = fig.add_subplot(inner[row])
            ys = range(len(ch) - 1, -1, -1)
            ax.barh(list(ys), [c["size"] for c in ch], height=0.7,
                    color=BLUE, edgecolor="white", linewidth=0.5)
            for y, c in zip(ys, ch):
                ax.text(c["size"] + 12, y, f"{c['size']}", va="center",
                        fontsize=9, color="0.35")
            ax.set_yticks(list(ys))
            ax.set_yticklabels([READING[(pid, k)] for k in range(len(ch))],
                               fontsize=10.2)
            head = (f"C{pid} {PARENT[pid]}   "
                    f"(replicate ARI {p['replicate_ari']:.2f}"
                    + (f", Infomap NMI {nmi[pid]:.2f}" if pid in nmi else "")
                    + ")")
            ax.set_title(head, fontsize=11, loc="left", pad=3)
            ax.set_xlim(0, max(c["size"] for c in ch) * 1.22)
            ax.tick_params(labelbottom=(row == len(idxs) - 1), labelsize=9)
            ax.spines[["right", "top"]].set_visible(False)
    fig.text(0.6, 0.006, "papers", ha="center", fontsize=12)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"figG_subcommunities.{ext}",
                    bbox_inches="tight", pad_inches=0.03)
    print("wrote", FIG / "figG_subcommunities.pdf/.png")


if __name__ == "__main__":
    main()
