"""Figures describing the citation graph: what a node is, what an edge is, and
how both are distributed.

Fig A (anatomy)   : tier schematic, degree distribution, edges and papers by year,
                    and the internal/external resolution of reference entries.
Fig B (the graph) : DRL layout of the core-tier giant component, coloured by
                    Leiden community, node area proportional to degree.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import igraph as ig
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle

from citation_communities import build_graph, direct_edges, load_papers

META_N_CORE = __import__("json").loads((Path(__file__).resolve().parent.parent / "data/communities/corpus_meta.json").read_text())["n_core"]
FIG = Path("paper/figures")
CORE = "#2b6ca3"; CITED = "#d98324"; GREY = "#6f6f6f"; ACC = "#c1462f"
PALETTE = ["#2b6ca3", "#3f8f5c", "#c1462f", "#7d5ba6", "#d98324", "#5a5a5a",
           "#1b9e9e", "#a6761d", "#6a3d9a", "#b2182b", "#4d9221"]


def style():
    plt.rcParams.update({
        "font.family": "serif", "font.size": 16, "mathtext.fontset": "stix",
        "axes.labelsize": 18, "axes.linewidth": 1.2, "axes.facecolor": "white",
        "xtick.labelsize": 14, "ytick.labelsize": 14,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "xtick.major.width": 1.2, "ytick.major.width": 1.2,
        "xtick.major.size": 6, "ytick.major.size": 6,
        "xtick.minor.width": 0.8, "ytick.minor.width": 0.8,
        "xtick.minor.size": 3, "ytick.minor.size": 3,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "legend.fontsize": 12, "legend.framealpha": 0.9, "legend.edgecolor": "0.6",
        "legend.fancybox": False, "figure.facecolor": "white",
        "savefig.facecolor": "white", "savefig.dpi": 300,
    })


def save(fig, stem, dpi=300):
    # dpi governs both the PNG and the resolution of any rasterised artist
    # embedded in the PDF, so it must be passed explicitly for both.
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.03,
                    dpi=dpi)
    plt.close(fig)
    print(f"  wrote {FIG/stem}.pdf/.png")


def main():
    style(); FIG.mkdir(parents=True, exist_ok=True)
    allp = load_papers(Path("data/raw/ads_corpus_v2.jsonl"))
    core = {b: d for b, d in allp.items() if d.get("tier") == "core"}
    edges = direct_edges(core)   # panel (d) only: reference-entry distribution

    # One graph throughout: the canonical undirected multigraph, exactly the
    # object every measurement in the paper is computed on. Figure B later takes
    # its induced subgraph over the displayed communities.
    from dcm_null import directed_edges as _de0, undirected as _und0
    _de = _de0(core)
    _cn = sorted({x for a, b, _ in _de for x in (a, b)})
    _ci = {n: i for i, n in enumerate(_cn)}
    g = _und0(len(_cn), ((_ci[a], _ci[b]) for a, b, _ in _de))
    g.vs["name"] = _cn
    print(f"canonical graph: {g.vcount():,} nodes, {g.ecount():,} edges")

    # ---------------- Figure A: anatomy ----------------
    fig = plt.figure(figsize=(15.4, 9.6))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.42)

    # (a) schematic: what a node and an edge are
    ax = fig.add_subplot(gs[0, 0]); ax.set_axis_off()
    ax.set_xlim(-0.3, 10.9); ax.set_ylim(-0.2, 7.2)
    ax.text(-0.25, 7.1, "(a)", fontsize=17, va="top")
    core_pos = [(2.4, 4.5), (4.3, 5.0), (3.4, 3.3), (5.6, 3.9), (1.9, 2.9)]
    cited_pos = [(7.9, 4.8), (8.4, 3.0), (7.2, 1.9)]
    for (x1, y1), (x2, y2) in [(core_pos[0], core_pos[1]), (core_pos[0], core_pos[2]),
                               (core_pos[1], core_pos[3]), (core_pos[2], core_pos[3]),
                               (core_pos[4], core_pos[2]), (core_pos[4], core_pos[0])]:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=13, lw=1.4, color=CORE,
                                     shrinkA=13, shrinkB=13))
    for (x1, y1), (x2, y2) in [(core_pos[1], cited_pos[0]), (core_pos[3], cited_pos[0]),
                               (core_pos[3], cited_pos[1]), (core_pos[2], cited_pos[2]),
                               (core_pos[0], cited_pos[0])]:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=13, lw=1.2, color=GREY,
                                     linestyle=(0, (4, 2)), alpha=0.8,
                                     shrinkA=13, shrinkB=13))
    for x, y in core_pos:
        ax.add_patch(Circle((x, y), 0.34, fc=CORE, ec="black", lw=1.0, zorder=3))
    for x, y in cited_pos:
        ax.add_patch(Circle((x, y), 0.30, fc=CITED, ec="black", lw=1.0, zorder=3))
    ax.text(3.6, 1.55, f"tier 1 · core\n{META_N_CORE:,} papers\nnames a GRB in title,\nabstract or keywords",
            ha="center", va="top", fontsize=11.5, color=CORE)
    ax.text(8.9, 1.55, "tier 2 · cited\n126,108 papers\ncited by core",
            ha="center", va="top", fontsize=11.5, color=CITED)
    ax.text(1.15, 7.1, "node = one paper       edge = one cites the other",
            fontsize=12.5, color="black", va="top")
    ax.text(-0.25, 6.35, "solid  core–core (analysed)\ndashed  core–cited (context)",
            fontsize=11, color=GREY, va="top")

    # (c) degree distribution
    ax = fig.add_subplot(gs[1, 0])
    deg = np.array(g.degree()); deg = deg[deg > 0]
    bins = np.logspace(0, np.log10(deg.max() + 1), 40)
    ax.hist(deg, bins=bins, color=CORE, alpha=0.85, edgecolor="black", linewidth=0.5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("degree (internal citation links)")
    ax.set_ylabel("papers")
    ax.text(-0.16, 1.06, "(c)", transform=ax.transAxes, fontsize=17, va="top")
    ax.text(0.97, 0.93, f"median {np.median(deg):.0f}\nmean {deg.mean():.1f}\n"
                        f"max {deg.max():,}", transform=ax.transAxes,
            ha="right", va="top", fontsize=12.5)

    # (d) papers and edges per year
    ax = fig.add_subplot(gs[1, 1])
    yrs = Counter(d["year"] for d in core.values() if d.get("year"))
    # link formation counted on the canonical arcs, by CITING year: the same
    # 380,362 arcs every measurement uses, not the reference+citation union
    ey = Counter()
    for a, b, y in _de:
        if y:
            ey[y] += 1
    xs = sorted(y for y in yrs if 1965 <= y <= 2026)
    ax.bar(xs, [yrs[y] for y in xs], color=CORE, alpha=0.85, width=0.9,
           label="papers published")
    ax.set_ylim(0, max(yrs[y] for y in xs) * 1.30)
    ax2 = ax.twinx()
    ax2.plot(xs, [ey[y] for y in xs], color=ACC, lw=2.0, label="citation links formed")
    ax2.set_ylabel("citation links formed", color=ACC, fontsize=15, labelpad=4)
    ax2.tick_params(axis="y", colors=ACC, direction="in")
    ax2.minorticks_on()
    ax.set_xlabel("year"); ax.set_ylabel("papers published", color=CORE)

    ax.tick_params(axis="y", colors=CORE)
    ax.text(-0.20, 1.06, "(d)", transform=ax.transAxes, fontsize=17, va="top")
    for yr, lab in ((1973, "discovery"), (1997, "afterglows"), (2017, "GW170817")):
        ax.axvline(yr, color="0.55", ls="--", lw=1.1, zorder=0)
        ax.annotate(lab, (yr - 0.8, ax.get_ylim()[1] * 0.99), rotation=90,
                    fontsize=10.5, ha="right", va="top", color="0.30")

    # (b) how completely reference entries resolve, before and after the
    #     neighbourhood fetch -- the point of the second tier
    ax = fig.add_subplot(gs[0, 1])
    corpus_all = set(allp); core_ids = set(core)
    n_core = n_cited = n_out = 0
    for d in core.values():
        for r in d.get("references") or []:
            if r in core_ids: n_core += 1
            elif r in corpus_all: n_cited += 1
            else: n_out += 1
    tot = n_core + n_cited + n_out
    old = json.loads(Path("data/communities/ref_resolution_old.json").read_text()) \
        if Path("data/communities/ref_resolution_old.json").exists() else None
    # the core-only bar is computed, not typed: with no second tier every
    # reference either resolves core->core or is unresolved
    bars = [("core-only\ncorpus",
             [100*n_core/tot, 0.0, 100*(n_cited+n_out)/tot]),
            ("two-tier\ncorpus",
             [100*n_core/tot, 100*n_cited/tot, 100*n_out/tot])]
    cols = [CORE, CITED, "0.78"]
    labs = ["resolves core \u2192 core", "resolves core \u2192 cited tier", "unresolved"]
    ypos = [1, 0]
    for (name, vals), y in zip(bars, ypos):
        left = 0
        for v, c in zip(vals, cols):
            if v <= 0:
                continue
            ax.barh([y], [v], left=left, color=c, edgecolor="black",
                    linewidth=0.8, height=0.42)
            if v > 7:
                ax.text(left + v/2, y, f"{v:.1f}%", ha="center", va="center",
                        fontsize=12.5, color="white" if c != "0.78" else "black")
            left += v
    ax.set_xlim(0, 100); ax.set_ylim(-0.62, 1.85)
    ax.set_yticks(ypos)
    ax.set_yticklabels([b[0] for b in bars], fontsize=11.5)
    ax.set_xlabel("share of reference entries (%)")
    ax.tick_params(axis="y", which="both", left=False, right=False, pad=2)
    handles = [plt.Rectangle((0,0),1,1, fc=c, ec="black", lw=0.7) for c in cols]
    ax.legend(handles, labs, loc="upper center", ncol=1, fontsize=10.5,
              handlelength=1.2, borderpad=0.35, labelspacing=0.25)
    ax.text(-0.20, 1.06, "(b)", transform=ax.transAxes, fontsize=17, va="top")
    ax.set_title(f"{tot:,} reference entries from core papers", fontsize=13, pad=8)
    save(fig, "figA_graph_anatomy")

    # ---------------- Figure B: the graph itself ----------------
    # A raw force-directed layout of every node is a hairball: it spends its
    # resolution separating high-degree filaments and hides the block structure.
    # Instead we lay the community graph out first, then lay each community out
    # locally and place it at its own position. Distance between blocks is then
    # interpretable (it is the inter-community coupling), and distance within a
    # block still reflects local citation structure.
    import random as _random
    _random.seed(11)            # igraph layouts draw from Python's RNG
    # The consensus partition, not one optimiser run. Groups below the display
    # threshold are kept here and excluded explicitly further down, so the node
    # and edge counts the caption quotes are the ones actually drawn.
    part = json.loads(Path("data/communities/canonical_consensus.json").read_text())
    shown = [c for c in part["communities"] if c["above_threshold"]]
    comm = {b: c["id"] for c in shown for b in c["members"]}
    ids = [c["id"] for c in shown]
    size = {c["id"]: c["size"] for c in shown}
    LABEL = {0: "BATSE era,\nsoft repeaters", 1: "afterglows",
             2: "compact mergers", 3: "prompt emission", 4: "high-energy\nneutrinos",
             5: "collapsars, SNe", 6: "host galaxies",
             7: "correlations,\ncosmology", 8: "Lorentz-invariance\ntests",
             9: "TGFs", 10: "fireshell school", 11: "dark matter",
             12: "biological effects\nat Earth", 13: "quark stars"}
    assert set(LABEL) == set(ids), f"label/community mismatch: {set(ids) ^ set(LABEL)}"


    # the canonical graph: directed arcs collapsed WITHOUT simplifying, the
    # same object every measurement in the paper uses
    g_full = g
    cnames = g_full.vs["name"]
    keep = [i for i, n in enumerate(cnames) if n in comm]
    n_drop = g_full.vcount() - len(keep)
    g = g_full.induced_subgraph(keep)
    names_all = [cnames[i] for i in keep]
    g.vs["name"] = names_all
    cid_all = np.array([comm[n] for n in names_all])
    deg_all = np.array(g.degree())
    print(f"  figure B draws {g.vcount():,} of {g_full.vcount():,} vertices "
          f"and {g.ecount():,} of {g_full.ecount():,} edges "
          f"({n_drop} vertices in groups below the {30}-paper display threshold)")
    assert (cid_all >= 0).all(), "a drawn vertex has no community"

    # inter-community coupling, observed over expected, computed on the SAME
    # multigraph that is drawn below rather than on the panel figure's edge list
    degc, btw = Counter(), Counter()
    for ea, eb in g.get_edgelist():
        ca, cb = cid_all[ea], cid_all[eb]
        degc[ca] += 1; degc[cb] += 1
        if ca != cb:
            btw[(min(ca, cb), max(ca, cb))] += 1
    m2 = sum(degc.values()) / 2
    gi = {c: k for k, c in enumerate(ids)}
    pairs = []
    for (a, b), o in btw.items():
        e = degc[a] * degc[b] / (2 * m2)
        if e > 0:
            pairs.append((a, b, o / e, o))
    cg = ig.Graph(n=len(ids), edges=[(gi[a], gi[b]) for a, b, r, o in pairs])
    cg.es["weight"] = [r for *_, r, o in pairs]
    centres = np.array(cg.layout_fruchterman_reingold(weights=cg.es["weight"], niter=2000))
    centres -= centres.mean(0)
    centres /= np.abs(centres).max()

    pos = np.zeros((g.vcount(), 2))
    for c in ids:
        idxs = np.where(cid_all == c)[0]
        sub = g.induced_subgraph(idxs.tolist())
        loc = np.array(sub.layout_fruchterman_reingold(niter=500))
        loc -= loc.mean(0)
        span = np.abs(loc).max() or 1.0
        radius = 0.052 * np.sqrt(size[c]) / np.sqrt(max(size.values())) * 4.2
        pos[idxs] = centres[gi[c]] * 2.6 + loc / span * radius

    fig, ax = plt.subplots(figsize=(13.6, 8.4))
    el = np.array(g.get_edgelist())
    same = cid_all[el[:, 0]] == cid_all[el[:, 1]]
    rng = np.random.default_rng(0)
    # The link bundles and the node cloud are rasterised: as vector paths they
    # make the PDF several megabytes and force the viewer to re-render hundreds
    # of thousands of segments on every scroll. Text, connectors and axes stay
    # vector, so labels remain sharp and selectable at any zoom.
    n_drawn = 0
    for mask, col, lw, al in ((same, "0.80", 0.05, 0.30),
                              (~same, "0.55", 0.05, 0.16)):
        sub = el[mask]
        take = rng.choice(len(sub), size=min(40000, len(sub)), replace=False)
        n_drawn += len(take)
        seg = pos[sub[take]]
        ax.plot(seg[:, :, 0].T, seg[:, :, 1].T, color=col, lw=lw, alpha=al,
                zorder=1, rasterized=True)
    print(f"  figure B renders {n_drawn:,} of {g.ecount():,} links "
          f"({n_drawn/g.ecount():.0%}, sampled for legibility)")
    # Labels sit on a ring around the drawing, each at its community's own
    # bearing from the centre. Bearings are then spread so no two labels are
    # closer than a minimum angle, which is the only reliable way to keep
    # communities that lie on the same radius from colliding.
    mid = pos.mean(axis=0)
    ang = {}
    for c in ids:
        v = centres[gi[c]] * 2.6 - mid
        ang[c] = np.arctan2(v[1], v[0])
    order = sorted(ids, key=lambda c: ang[c])
    # Even angular spacing in bearing order. Iterative relaxation can oscillate
    # when two communities share a bearing, so we place the labels on exact
    # equal steps and choose the global rotation that stays closest to the
    # communities' true bearings.
    n = len(order)
    step = 2 * np.pi / n
    base = np.array([ang[c] for c in order])
    best, bestcost = 0.0, np.inf
    for shift in np.linspace(0, 2 * np.pi, 720, endpoint=False):
        cand = shift + step * np.arange(n)
        cost = np.abs(np.angle(np.exp(1j * (cand - base)))).sum()
        if cost < bestcost:
            bestcost, best = cost, shift
    theta = best + step * np.arange(n)
    place = {c: theta[k] for k, c in enumerate(order)}

    span = np.abs(pos - mid).max()
    RX, RY = span * 1.46, span * 1.30
    for k, c in enumerate(ids):
        mk = cid_all == c
        col = PALETTE[k % len(PALETTE)]
        ax.scatter(pos[mk, 0], pos[mk, 1], s=1.0 + 0.5 * np.sqrt(deg_all[mk]),
                   color=col, alpha=0.80, linewidths=0, zorder=3, rasterized=True)
        cxy = centres[gi[c]] * 2.6
        r = 0.052 * np.sqrt(size[c]) / np.sqrt(max(size.values())) * 4.2
        t = place[c]
        lx, ly = mid[0] + RX * np.cos(t), mid[1] + RY * np.sin(t)
        # connector runs from the rim of the blob toward the label
        d = np.array([lx, ly]) - cxy
        d = d / (np.linalg.norm(d) or 1.0)
        ax.plot([cxy[0] + d[0] * r, lx - d[0] * 0.30],
                [cxy[1] + d[1] * r, ly - d[1] * 0.30],
                color=col, lw=0.9, alpha=0.60, zorder=2)
        ha = "center" if abs(np.cos(t)) < 0.35 else ("left" if np.cos(t) > 0 else "right")
        ax.text(lx, ly, f"{LABEL[c]}\n{size[c]:,}", ha=ha, va="center",
                fontsize=14, color=col, zorder=5, linespacing=1.15)

    ax.set_xticks([]); ax.set_yticks([]); ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    # limits from the node positions only; labels sit inside the margin
    ax.set_xlim(mid[0] - RX * 1.62, mid[0] + RX * 1.62)
    ax.set_ylim(mid[1] - RY * 1.30, mid[1] + RY * 1.30)
    ax.set_title(f"{g.vcount():,} papers · {g.ecount():,} citation links, "
                 f"{n_drawn:,} drawn · {len(ids)} communities", fontsize=16, pad=8)
    save(fig, "figB_citation_graph")


if __name__ == "__main__":
    main()
