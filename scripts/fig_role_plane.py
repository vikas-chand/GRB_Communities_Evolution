"""Figure: the role plane. Within-community degree z against participation P,
stable-core papers only, coloured by community, with the papers a GRB reader
would ask about labelled. Guimera-Amaral thresholds at z = 2.5 and P = 0.62.
"""
from __future__ import annotations
import csv, gzip, json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "paper/figures"
PALETTE = ["#2b6ca3", "#3f8f5c", "#c1462f", "#7d5ba6", "#d98324", "#5a5a5a",
           "#1b9e9e", "#a6761d", "#6a3d9a", "#b2182b", "#4d9221", "#e7298a",
           "#666633", "#1f78b4"]

LABELS = {
    "1993ApJ...405..273W": ("Woosley 1993 (collapsar)", (12, -14)),
    "2004ApJ...611.1005G": ("Swift mission", (14, -8)),
    "2006ARA&A..44..507W": ("Woosley & Bloom 2006", (-30, 20)),
    "2002A&A...390...81A": ("Amati+ 2002", (16, -4)),
    "1973ApJ...182L..85K": ("Klebesadel+ 1973", (-40, 26)),
    "1998ApJ...497L..17S": ("Sari, Piran & Narayan 1998", (-215, -4)),
    "2017PhRvL.119p1101A": ("GW170817", (-88, 10)),
    "1992Natur.355..143M": ("Meegan+ 1992 (isotropy)", (-165, 2)),
    "1981Natur.290..378M": ("Mazets+ 1981 (lines)", (10, -18)),
    "2010MNRAS.406.2650M": ("Metzger+ 2010 (kilonova)", (8, -14)),
    "1990ARA&A..28..401H": ("Higdon & Lingenfelter 1990", (10, 10)),
}


def main():
    plt.rcParams.update({
        "font.family": "serif", "font.size": 14, "mathtext.fontset": "stix",
        "axes.labelsize": 17, "axes.linewidth": 1.2,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 300,
    })
    with gzip.open(ROOT / "data/communities/paper_roles_table.csv.gz", "rt") as fh:
        # stable-core papers of the fourteen real communities only; the frozen
        # sub-threshold contamination groups are trivially "stable" and excluded
        rows = [r for r in csv.DictReader(fh)
                if r["stable"] == "1" and 0 <= int(r["community"]) <= 13]
    P = np.array([float(r["participation"]) for r in rows])
    z = np.array([float(r["z_within"]) for r in rows])
    c = np.array([int(r["community"]) for r in rows])
    bib = [r["bibcode"] for r in rows]
    reading = {0: "BATSE era", 1: "afterglows", 2: "mergers", 3: "prompt emission",
               4: "neutrinos", 5: "collapsars", 6: "hosts", 7: "cosmology",
               8: "LIV tests", 9: "TGFs", 10: "fireshell", 11: "dark matter",
               12: "bio effects", 13: "quark stars"}

    fig, ax = plt.subplots(figsize=(12.6, 7.2))
    for k in sorted(set(c)):
        mk = c == k
        ax.scatter(P[mk], z[mk], s=7, color=PALETTE[k % len(PALETTE)],
                   alpha=0.55, linewidths=0, rasterized=True,
                   label=reading.get(k, f"community {k}"))
    ax.axhline(2.5, color="0.4", lw=1.0, ls=(0, (5, 3)))
    ax.axvline(0.62, color="0.4", lw=1.0, ls=(0, (5, 3)))
    ax.text(0.015, 0.97, "provincial hubs", transform=ax.transAxes,
            fontsize=13, color="0.35", va="top")
    ax.text(0.985, 0.97, "connector hubs", transform=ax.transAxes,
            fontsize=13, color="0.35", va="top", ha="right")
    ax.text(0.985, 0.04, "boundary brokers", transform=ax.transAxes,
            fontsize=13, color="0.35", ha="right")
    ax.text(0.015, 0.04, "peripheral", transform=ax.transAxes,
            fontsize=13, color="0.35")

    pos = {b: i for i, b in enumerate(bib)}
    for b, (lab, off) in LABELS.items():
        if b not in pos:
            continue
        i = pos[b]
        ax.annotate(lab, (P[i], z[i]), xytext=off, textcoords="offset points",
                    fontsize=10.3, color="0.1",
                    arrowprops=dict(arrowstyle="-", lw=0.7, color="0.3"))
        ax.scatter([P[i]], [z[i]], s=26, facecolor="none", edgecolor="black",
                   linewidths=0.9, zorder=5)
    ax.set_xlabel("participation coefficient $P$")
    ax.set_ylabel("within-community degree $z$")
    ax.set_xlim(-0.02, 1.0)
    ax.legend(fontsize=11, ncol=1, framealpha=0.9, edgecolor="0.6",
              markerscale=2.6, loc="center left", bbox_to_anchor=(1.01, 0.5),
              handletextpad=0.3, borderpad=0.5)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"figD_role_plane.{ext}", bbox_inches="tight",
                    pad_inches=0.03, dpi=300)
    plt.close(fig)
    print(f"wrote {FIG/'figD_role_plane'}.pdf/.png  ({len(rows):,} stable-core papers)")

if __name__ == "__main__":
    main()
