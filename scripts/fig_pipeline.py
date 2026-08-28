"""Figure C: the measurement pipeline, corpus to findings.

What is built, what is optimised, and what each result is tested against. Every
number is read from the products rather than typed here, so the figure cannot
drift from the analysis.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "paper/figures"
COM = ROOT / "data/communities"

CORPUS = "#2b6ca3"; GRAPH = "#3f8f5c"; PART = "#7d5ba6"
TEST = "#d98324"; OUT = "#c1462f"; GREY = "#7a7a7a"

TITLE_H = 0.034          # vertical room for a box title
LINE_H = 0.0285          # per body line
PAD = 0.022              # top and bottom padding inside a box

def style():
    plt.rcParams.update({
        "font.family": "serif", "font.size": 13, "mathtext.fontset": "stix",
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "savefig.dpi": 300,
    })

def load():
    j = lambda n: json.loads((COM / n).read_text())
    return (j("canonical_consensus.json"), j("stability_sweep.json"),
            j("ablation_controls2.json"), j("representation_check.json"),
            j("dcm_null_dT1.json"),
            j("algorithm_comparison2.json"), j("corpus_meta.json"),
            j("temporal_modularity.json"),
            j("campaign/campaign_summary.json"))

class Box:
    """A titled box: colour band for the title, pale body, self-sized."""
    def __init__(self, ax, cx, top, w, title, lines, colour, fs=12.0):
        band = TITLE_H + PAD * 0.9
        h = band + LINE_H * len(lines) + 1.6 * PAD
        y0, y1 = top - h, top
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, y0), w, h,
            boxstyle="round,pad=0,rounding_size=0.014",
            linewidth=0, edgecolor="none", facecolor=colour, alpha=0.06,
            zorder=2))
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, y1 - band), w, band,
            boxstyle="round,pad=0,rounding_size=0.014",
            linewidth=0, edgecolor="none", facecolor=colour, alpha=0.16,
            zorder=3))
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, y0), w, h,
            boxstyle="round,pad=0,rounding_size=0.014",
            linewidth=1.4, edgecolor=colour, facecolor="none", zorder=4))
        ax.text(cx, y1 - band / 2, title, ha="center", va="center",
                fontsize=fs + 1.6, color=colour, zorder=5, weight="bold")
        for k, ln in enumerate(lines):
            ax.text(cx, y1 - band - 0.55 * PAD - LINE_H * k, ln, ha="center",
                    va="top", fontsize=fs, color="0.18", zorder=5)
        self.cx, self.top, self.bot, self.w = cx, y1, y0, w
        self.left, self.right = cx - w / 2, cx + w / 2

def arrow(ax, a, b, colour=GREY, lw=1.6, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=15,
                                 linewidth=lw, color=colour, linestyle=ls,
                                 shrinkA=1, shrinkB=1, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))

def main():
    style()
    canon, sweep, ctrl, rep, dcm, algo, meta, tmod, camp = load()
    # stability_sweep.json is used ONLY for the single-run reseed ARI
    single = sweep["single_run"]
    kw = [r for r in ctrl["rows"] if r["label"] == "keyword-only"][0]
    zother = max(abs(r["z"]) for r in ctrl["rows"]
                 if "keyword" not in r["label"])
    nab = len(ctrl["rows"])
    q5 = dcm["q_observed"]
    lou = algo["results"]["louvain"]; inf = algo["results"]["infomap"]

    fig, ax = plt.subplots(figsize=(13.6, 12.8))
    ax.set_xlim(-0.02, 1.02); ax.set_axis_off()

    corpus = Box(ax, 0.5, 0.995, 0.60,
        f"ADS corpus, {meta['query_year_min']}--{meta['query_year_max']} query", [
        f"core tier {meta['n_core']:,} papers, exact-phrase query",
        f"cited tier {meta['n_cited']:,} papers they reference"], CORPUS)

    graph = Box(ax, 0.5, corpus.bot - 0.060, 0.66, "citation graph", [
        f"{canon['n_directed_arcs']:,} directed arcs from ADS reference lists",
        "direction collapsed, reciprocal pairs kept as parallel edges",
        f"{canon['n_nodes']:,} nodes, {canon['n_edges']:,} edges (multigraph)"], GRAPH)

    ptop = graph.bot - 0.090
    cons = Box(ax, 0.5, ptop, 0.54,
        f"consensus over $R = {canon['R']}$ runs", [
        f"Leiden, Reichardt and Bornholdt, $\\gamma = {meta['gamma']:.0f}$",
        f"single runs agree only at ARI {single['ari_mean']:.3f} $\\pm$ {single['ari_sd']:.3f}",
        f"co-association on existing edges, $\\tau = {canon['tau']}$:",
        f"{camp['n_realizations']} constructions agree at ARI "
        f"{camp['pairwise_ari_r30']['median']:.4f} "
        f"({camp['pairwise_ari_r30']['range'][0]:.4f}--{camp['pairwise_ari_r30']['range'][1]:.4f})",
        f"{canon['n_above_threshold']} communities of $\\geq${canon['min_size']}, "
        f"membership $Q = {canon['q']:.4f}$"], PART)
    ax.text(cons.right - 0.015, cons.bot - 0.020, "canonical partition",
            ha="right", va="top", fontsize=10.6, color=PART)

    ttop = cons.bot - 0.130
    tests = [
        Box(ax, 0.125, ttop, 0.24, "significance", [
            f"DCM null, {dcm['R']} draws,",
            f"best-of-{len(dcm['opt_seeds'])} $Q$ both sides:",
            f"$Q_{{{len(dcm['opt_seeds'])}}} = {q5:.4f}$ vs {dcm['q_null_mean']:.4f}",
            f"$\\Delta Q = {q5 - dcm['q_null_mean']:.4f}$, "
            f"$p = 1/{round(1/dcm['p_empirical'])}$"], TEST, fs=11.2),
        Box(ax, 0.375, ttop, 0.24, "other algorithms", [
            "seeded, frozen graph:",
            f"Louvain {camp['louvain_one_to_one']['median']*100:.1f}% one-to-one",
            f"({camp['louvain_one_to_one']['range'][0]*100:.1f}--{camp['louvain_one_to_one']['range'][1]*100:.1f}%, "
            f"{camp['n_realizations']} schedules)",
            f"Infomap NMI {inf['nmi']:.2f}, finer",
            f"({inf['n_communities_30']} communities)"], TEST, fs=11.2),
        Box(ax, 0.625, ttop, 0.24,
            f"corpus cuts ($R={ctrl['R']}$)", [
            f"{nab} cuts, {camp['n_realizations']} seed schedules,",
            f"{ctrl['K']} matched deletions each:",
            "no cut in the control tail",
            f"in every schedule (max {max(c['m_tail'] for c in camp['ablations'].values())}/{camp['n_realizations']})"], TEST, fs=11.2),
        Box(ax, 0.873, ttop, 0.24, "representation", [
            "multigraph against weighted,",
            f"{len(rep['seeds'])} matched seeds: ARI {rep['cross_mean']:.3f}",
            f"against {rep['multigraph_reseed_mean']:.3f} on reseed,",
            "so it matters less than seed"], TEST, fs=11.2),
    ]

    btop = min(t.bot for t in tests) - 0.115
    span_lo = min(r["omega_ratio"] for r in tmod["sweep"]) - 1
    span_hi = max(r["omega_ratio"] for r in tmod["sweep"]) - 1
    temporal = Box(ax, 0.225, btop, 0.40, "temporal modularity", [
        "the same graph, layered by time",
        "multiplex $Q_T$, layers of $\\Delta T$ years",
        f"its communities span {span_lo:.0%} to {span_hi:.0%} more,",
        "so the static partition is time-confined"], PART, fs=11.2)
    findings = Box(ax, 0.725, btop, 0.46, "findings", [
        f"{canon['n_above_threshold']} macrocommunities; the fixed dark-matter",
        f"set loses {1 - camp['dm_cut_retention']['retained_frac']['median']:.0%} of its members to the keyword",
        f"cut in all {camp['n_realizations']} schedules (co-location "
        f"{camp['dm_cut_retention']['s_d']['range'][0]:.4f}--{camp['dm_cut_retention']['s_d']['range'][1]:.4f});",
        f"controls retain and co-locate $\\geq$ {camp['dm_control_s_d_min']:.4f}:",
        "an indexing artefact"], OUT, fs=11.2)

    arrow(ax, (0.5, corpus.bot), (0.5, graph.top), CORPUS, lw=2.4)
    arrow(ax, (0.5, graph.bot), (cons.cx, cons.top), PART, lw=2.2)
    # the four checks live in one container, mirroring the manuscript's
    # "Validation of the community map" grouping
    gpad = 0.014
    g_left = tests[0].left - gpad
    g_right = tests[3].right + gpad
    g_top = ttop + 0.052
    g_bot = min(t.bot for t in tests) - gpad
    ax.add_patch(FancyBboxPatch(
        (g_left, g_bot), g_right - g_left, g_top - g_bot,
        boxstyle="round,pad=0,rounding_size=0.018",
        linewidth=1.3, edgecolor=TEST, facecolor=TEST, alpha=0.045, zorder=0))
    ax.add_patch(FancyBboxPatch(
        (g_left, g_bot), g_right - g_left, g_top - g_bot,
        boxstyle="round,pad=0,rounding_size=0.018",
        linewidth=1.3, edgecolor=TEST, facecolor="none", zorder=1))
    g_cx = (g_left + g_right) / 2
    ax.text(g_cx, g_top - 0.010, "validation of the community map",
            ha="center", va="top", fontsize=13.2, color=TEST,
            style="italic", zorder=5)
    arrow(ax, (cons.cx, cons.bot), (g_cx, g_top), TEST, lw=1.6)
    # the findings rest on the validation group as a whole
    arrow(ax, ((tests[2].cx + tests[3].cx) / 2, g_bot),
          (findings.cx, findings.top), OUT, lw=1.5)
    ymid = (temporal.top + temporal.bot) / 2
    arrow(ax, (temporal.right, ymid), (findings.left, ymid), OUT)

    floor = min(temporal.bot, findings.bot)
    ax.text(0.5, floor - 0.030, "arrows run from what is built to what is measured "
            "on it; the boxed group gathers " + {2: "two", 3: "three", 4: "four", 5: "five"}[len(tests)] + " independent checks on the canonical "
            "partition", ha="center", va="top", fontsize=9.8, color="0.35",
            style="italic")
    ax.set_ylim(floor - 0.075, 1.03)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"figC_pipeline.{ext}", bbox_inches="tight",
                    pad_inches=0.04, dpi=300)
    plt.close(fig)
    print(f"  wrote {FIG/'figC_pipeline'}.pdf/.png")

if __name__ == "__main__":
    main()
