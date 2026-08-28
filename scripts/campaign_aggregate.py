"""Aggregate the five campaign realizations per the predeclared contract.

Publishes every realization-level value with median and observed range —
never mean +/- SD from five points. Pairwise consensus ARIs are labelled
non-independent. Runs only when all five real{j}.json exist.
"""
from __future__ import annotations
import json
import statistics as st
from itertools import combinations
from pathlib import Path

from sklearn.metrics import adjusted_rand_score as ari

ROOT = Path(__file__).resolve().parent.parent
CAMP = ROOT / "data/communities/campaign"


def med_range(xs):
    return dict(values=[round(x, 4) for x in xs], median=round(st.median(xs), 4),
                range=[round(min(xs), 4), round(max(xs), 4)])


def main() -> None:
    reals = []
    for j in range(5):
        f = CAMP / f"real{j}.json"
        assert f.exists(), f"missing realization {j}"
        reals.append(json.loads(f.read_text()))

    out = dict(n_realizations=5, blocks=[r["block"] for r in reals])

    # ablations: per cut, five (delta_ari, rank) pairs; m/5 in the 0.04 tail
    cuts = [r["label"] for r in reals[0]["ablation_rows"]]
    abl = {}
    for lab in cuts:
        rows = [next(x for x in r["ablation_rows"] if x["label"] == lab)
                for r in reals]
        abl[lab] = dict(
            delta_ari=med_range([x["delta_ari"] for x in rows]),
            pct_rank=med_range([x["pct_rank"] for x in rows]),
            m_tail=sum(1 for x in rows
                       if x["delta_ari"] < 0 and x["pct_rank"] <= 0.04),
            n_nonconverged=[x.get("n_nonconverged", 0) for x in rows])
    out["ablations"] = abl

    # consensus reproducibility: pairwise ARIs among the five memberships
    for R in (30, 20, 10):
        membs = []
        for j in range(5):
            m = json.loads((CAMP / f"membership_r{R}_j{j}.json").read_text())
            membs.append(m)
        shared = set(membs[0])
        for m in membs[1:]:
            shared &= set(m)
        shared = sorted(shared)
        raw = [ari([a[n] for n in shared], [b[n] for n in shared])
               for a, b in combinations(membs, 2)]
        out[f"pairwise_ari_r{R}"] = dict(
            values=[round(x, 4) for x in raw],
            median=round(st.median(raw), 4),
            range=[round(min(raw), 4), round(max(raw), 4)],
            note="pairwise scores share partitions; descriptive, not "
                 "independent uncertainty replicates")

    # fixed-D structure at each R; retention under keyword cut vs controls
    for R in (10, 20, 30):
        cells = [r[f"d_r{R}"] for r in reals]
        out[f"D_r{R}"] = dict(
            cells=cells,
            size=med_range([c["size"] for c in cells]),
            capture=med_range([c["capture"] for c in cells]),
            purity=med_range([c["purity"] for c in cells]))
    cut = [r["dm_cut"] for r in reals]
    out["dm_cut_retention"] = dict(
        cells=cut,
        retained_frac=med_range([c["retained_frac"] for c in cut]),
        cohesion=med_range([c["cohesion"] for c in cut]),
        s_d=med_range([c["s_d"] for c in cut]))
    out["dm_control_retention"] = [r["dm_controls"] for r in reals]
    out["dm_control_s_d_min"] = round(min(
        c["s_d"] for r in reals for c in r["dm_controls"]), 4)
    # per-schedule ablation detail retained alongside the compact stats
    out["ablation_detail"] = {
        lab: [dict(ari=x["ari"], control_mean=x["control_mean"],
                   control_sd=x["control_sd"], z=x["z"],
                   n_nonconverged=x.get("n_nonconverged", 0))
              for x in (next(y for y in r["ablation_rows"]
                             if y["label"] == lab) for r in reals)]
        for lab in cuts}

    # louvain
    out["louvain_ari"] = med_range([r["louvain"]["ari"] for r in reals])
    out["louvain_one_to_one"] = med_range(
        [r["louvain"]["one_to_one"] for r in reals])
    out["r30_n_communities"] = [r["r30_n_communities"] for r in reals]

    (CAMP / "campaign_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:2000])
    print("...\nwrote", CAMP / "campaign_summary.json")


if __name__ == "__main__":
    main()
