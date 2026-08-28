"""Figure: the alluvial history of the communities, 1985 to 2026.

Columns are cumulative snapshots; blocks are the communities of at least 30
papers at each cut, coloured by the canonical community their members end up
in; ribbons are the statistically selected lineage edges, with width set by the
overlap. Splits and merges are visible as ribbons that fan; nothing terminates.
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "paper/figures"
PALETTE = {0: "#2b6ca3", 1: "#3f8f5c", 2: "#c1462f", 3: "#7d5ba6", 4: "#d98324",
           5: "#5a5a5a", 6: "#1b9e9e", 7: "#a6761d", 8: "#6a3d9a", 9: "#b2182b",
           10: "#4d9221", 11: "#e7298a", 12: "#666633", 13: "#1f78b4"}
NAME = {0: "BATSE era", 1: "afterglows", 2: "mergers", 3: "prompt", 4: "neutrinos",
        5: "collapsars", 6: "hosts", 7: "cosmology", 8: "LIV", 9: "TGFs",
        10: "fireshell", 11: "dark matter", 12: "bio", 13: "quark stars"}

def main():
    plt.rcParams.update({
        "font.family": "serif", "font.size": 13, "mathtext.fontset": "stix",
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 300,
    })
    d = json.loads((ROOT / "data/communities/lineages.json").read_text())
    cuts = [c for c in d["cuts"] if str(c) in d["snapshots"]]
    snaps = d["snapshots"]
    GAP = 120           # papers of vertical gap between blocks
    W = 0.16            # block half-width in cut-index units

    # vertical layout per cut: stack blocks ordered by canonical label
    pos = {}            # (cut, cid) -> (y0, y1)
    for c in cuts:
        sizes = {int(k): v for k, v in snaps[str(c)]["sizes"].items()}
        canon = {int(k): v["canonical"] for k, v in snaps[str(c)]["canon"].items()}
        order = sorted(sizes, key=lambda k: (canon.get(k, 99), -sizes[k]))
        y = 0
        for cid in order:
            pos[(c, cid)] = (y, y + sizes[cid])
            y += sizes[cid] + GAP

    fig, ax = plt.subplots(figsize=(13.8, 8.2))
    xi = {c: i for i, c in enumerate(cuts)}

    # ribbons first
    for tr in d["transitions"]:
        t0, t1 = tr["t0"], tr["t1"]
        used0, used1 = {}, {}
        for e in sorted(tr["edges"], key=lambda e: -e["overlap"]):
            if e["r"] < 0.10 and e["c"] < 0.10:
                continue
            k0, k1 = (t0, e["src"]), (t1, e["dst"])
            if k0 not in pos or k1 not in pos:
                continue
            h = e["overlap"]
            y0a = pos[k0][0] + used0.get(k0, 0); used0[k0] = used0.get(k0, 0) + h
            y1a = pos[k1][0] + used1.get(k1, 0); used1[k1] = used1.get(k1, 0) + h
            x0, x1 = xi[t0] + W, xi[t1] - W
            col = PALETTE[snaps[str(t1)]["canon"][str(e["dst"])]["canonical"]]
            verts, codes = [], []
            xm = (x0 + x1) / 2
            verts += [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a)]
            codes += [MP.MOVETO, MP.CURVE4, MP.CURVE4, MP.CURVE4]
            verts += [(x1, y1a + h), (xm, y1a + h), (xm, y0a + h), (x0, y0a + h)]
            codes += [MP.LINETO, MP.CURVE4, MP.CURVE4, MP.CURVE4]
            verts += [(x0, y0a)]; codes += [MP.CLOSEPOLY]
            ax.add_patch(PathPatch(MP(verts, codes), facecolor=col, alpha=0.32,
                                   edgecolor="none", zorder=1))

    # blocks on top
    for (c, cid), (y0, y1) in pos.items():
        can = snaps[str(c)]["canon"][str(cid)]["canonical"]
        ax.add_patch(plt.Rectangle((xi[c] - W, y0), 2 * W, y1 - y0,
                                   facecolor=PALETTE[can], edgecolor="white",
                                   linewidth=0.6, zorder=3))
    # label final column
    c = cuts[-1]
    seen, last_y = set(), -10**9
    for cid, sz in sorted(((int(k), v) for k, v in snaps[str(c)]["sizes"].items()),
                          key=lambda t: pos[(c, t[0])][0]):
        can = snaps[str(c)]["canon"][str(cid)]["canonical"]
        y0, y1 = pos[(c, cid)]
        ym = (y0 + y1) / 2
        if sz < 60 or can in seen or ym - last_y < 320:
            continue
        seen.add(can); last_y = ym
        ax.text(xi[c] + W + 0.06, ym, NAME[can], va="center",
                fontsize=11.5, color=PALETTE[can])
    ax.set_xticks(range(len(cuts)))
    ax.set_xticklabels([str(c if c < 2026 else 2026) for c in cuts], fontsize=13)
    ax.set_xlim(-0.5, len(cuts) + 0.6)
    ymax = max(y1 for (_, _), (y0, y1) in zip(pos.keys(), pos.values()))
    ax.set_ylim(-GAP, ymax + GAP)
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("cumulative snapshot (papers published up to and including year)")
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"figE_alluvial.{ext}", bbox_inches="tight",
                    pad_inches=0.04, dpi=300)
    plt.close(fig)
    print(f"wrote {FIG/'figE_alluvial'}.pdf/.png")

if __name__ == "__main__":
    main()
