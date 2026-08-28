"""Predeclared multi-realization campaign on the frozen 1970-floor corpus.

Design fixed by notes/CODEX_MULTISEED_20260825.md before any new result was
inspected. Five outer realizations j = 0..4; j = 0 is the existing v3
execution (Leiden block start 42) recomputed with its original seeds and
control sets; j = 1..4 use block starts 10042/20042/30042/40042. Nested
consensus blocks: first 10 seeds -> R=10, first 20 -> R=20, all 30 -> R=30.
Control streams: numpy default_rng(20260825 + 1_000_000*j + 10_000*cut_i + k)
for the K=25 ablation controls and (20260825 + 1_000_000*j + 5_000 + k) for
the K=5 dark-matter controls; for j = 0 these reduce to the published v3
streams, and redrawn sets are asserted equal to the stored ones. The
dark-matter estimand is the fixed bibcode set D (the published v3 canonical
dark-matter community), frozen in data/communities/campaign/D_darkmatter.json;
per realization we record the best-matching block's size/capture/purity at
R=10/20/30 and, under the keyword cut and each control at R=20, the fixed-D
retention, conditional cohesion, and their product S_D. Louvain runs once per
realization (seeded with the block start) against the fixed published
canonical membership. Stop after the five realizations regardless of outcome.
"""
from __future__ import annotations
import argparse
import json
import random as pyrandom
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import os
from pathlib import Path

import igraph as ig
import numpy as np

from ablations import GRB, HOMONYM, ASTRO
from ablation_controls2 import (agreement, build, matched_control, papers)
from algorithm_comparison2 import one_to_one_agreement
from consensus import consensus, wq
from sklearn.metrics import adjusted_rand_score as ari

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
CAMP = OUT / "campaign"
K_ABL, K_DM = 25, 5
BLOCK = {0: 42, 1: 10042, 2: 20042, 3: 30042, 4: 40042}


def seeds_for(j, r):
    return list(range(BLOCK[j], BLOCK[j] + r))


def one_partition(drop, seeds, allow_nonconverged=False):
    h = build(frozenset(drop))
    m, _, ok = consensus(h, seeds)
    if not ok:
        if allow_nonconverged:
            return None, None
        raise RuntimeError("consensus did not converge")
    return h.vs["name"], np.asarray(m)


def d_block_metrics(names, memb, D):
    """Best-matching block for the fixed set D: size, capture, purity."""
    lab = {n: c for n, c in zip(names, memb)}
    inter = Counter(lab[n] for n in D if n in lab)
    if not inter:
        return dict(size=0, capture=0.0, purity=0.0)
    c, hit = inter.most_common(1)[0]
    size = int(sum(1 for v in lab.values() if v == c))
    return dict(size=size, capture=hit / len(D), purity=hit / size)


def d_retention(names, memb, D):
    """Fixed-D retention after a deletion: retained fraction, conditional
    cohesion among survivors, and their product S_D."""
    lab = {n: c for n, c in zip(names, memb)}
    retained = [n for n in D if n in lab]
    rf = len(retained) / len(D)
    if not retained:
        return dict(retained_frac=0.0, cohesion=None, s_d=0.0)
    top = Counter(lab[n] for n in retained).most_common(1)[0][1]
    return dict(retained_frac=rf, cohesion=top / len(retained),
                s_d=top / len(D))


def control_worker(args):
    j, cut_i, k, drop_list, excl, seeds = args
    rng = np.random.default_rng(20260825 + 1_000_000 * j + 10_000 * cut_i + k)
    h0 = build()
    vertices = set(h0.vs["name"])
    deg = dict(zip(h0.vs["name"], h0.strength(weights=h0.es["weight"])))
    drop_v = set(drop_list) & vertices
    cs = matched_control(deg, drop_v, rng, exclude_covariate=excl,
                         pool_restrict=vertices)
    assert len(cs) == len(drop_v) and cs <= vertices
    if j == 0:
        stored = OUT / f"control_sets/cut{cut_i}_k{k}.json"
        if stored.exists():
            assert sorted(cs) == json.loads(stored.read_text()), \
                f"j=0 control set mismatch cut{cut_i} k{k}"
    (CAMP / f"control_sets/j{j}_cut{cut_i}_k{k}.json").write_text(
        json.dumps(sorted(cs)))
    # nonconvergence at the declared max rounds is an OUTCOME, not an error
    # (protocol: CODEX_MULTISEED_20260825): record it, never replace it
    nn, m = one_partition(cs, seeds, allow_nonconverged=True)
    return cut_i, k, nn, m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--j", type=int, required=True, choices=range(5))
    args = ap.parse_args()
    j = args.j
    CAMP.mkdir(exist_ok=True)
    (CAMP / "control_sets").mkdir(exist_ok=True)
    D = set(json.loads((CAMP / "D_darkmatter.json").read_text()))
    canon = json.loads((OUT / "canonical_consensus.json").read_text())

    s10, s20, s30 = seeds_for(j, 10), seeds_for(j, 20), seeds_for(j, 30)
    import hashlib
    res = dict(j=j, block=BLOCK[j], seeds_r30=s30,
               driver_sha256=hashlib.sha256(
                   Path(__file__).read_bytes()).hexdigest(),
               workers=int(os.environ.get("CAMPAIGN_WORKERS", "6")))

    # --- R=30 consensus membership (fixed graph) + D metrics
    n30, m30 = one_partition([], s30)
    (CAMP / f"membership_r30_j{j}.json").write_text(json.dumps(
        {n: int(c) for n, c in zip(n30, m30)}))
    res["r30_n_communities"] = int(sum(1 for c in np.bincount(m30) if c >= 30))
    res["d_r30"] = d_block_metrics(n30, m30, D)
    print(f"[j={j}] R=30 done: {res['r30_n_communities']} communities, "
          f"D block {res['d_r30']}", flush=True)

    # --- ablations at R=10
    n10, m10 = one_partition([], s10)
    (CAMP / f"membership_r10_j{j}.json").write_text(json.dumps(
        {n: int(c) for n, c in zip(n10, m10)}))
    res["d_r10"] = d_block_metrics(n10, m10, D)

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    cuts = {
        "no reference list": {b for b, d in papers().items()
                              if not (d.get("references") or [])},
        "not refereed": {b for b, d in papers().items()
                         if "REFEREED" not in (d.get("property") or [])},
        "keyword-only": {b for b, d in papers().items()
                         if not GRB.search(text(d))},
        "homonym": {b for b, d in papers().items()
                    if HOMONYM.search(text(d)) and not ASTRO.search(text(d))},
    }
    cuts["keyword-only + homonym"] = cuts["keyword-only"] | cuts["homonym"]
    names = list(cuts)
    excl_of = {"not refereed": "refereed"}

    real = {}
    for lab in names:
        nn, m = one_partition(cuts[lab], s10)
        real[lab] = agreement(n10, m10, nn, m)
        print(f"[j={j}] real cut {lab:<24} ARI={real[lab]:.3f}", flush=True)

    jobs = [(j, i, k, sorted(cuts[names[i]]), excl_of.get(names[i]), s10)
            for i in range(len(names)) for k in range(K_ABL)]
    ctrl = {lab: [] for lab in names}
    done = 0
    nonconv = {lab: 0 for lab in names}
    with ProcessPoolExecutor(max_workers=int(os.environ.get("CAMPAIGN_WORKERS", "6"))) as ex:
        for cut_i, k, nn, m in ex.map(control_worker, jobs):
            if nn is None:
                nonconv[names[cut_i]] += 1
                print(f"[j={j}]   NONCONVERGED control cut{cut_i} k{k}",
                      flush=True)
            else:
                ctrl[names[cut_i]].append(agreement(n10, m10, nn, m))
            done += 1
            if done % 25 == 0:
                print(f"[j={j}]   controls {done}/{len(jobs)}", flush=True)
    rows = []
    for lab in names:
        c = np.array(ctrl[lab]); a = real[lab]
        rows.append(dict(
            label=lab, ari=float(a), control_mean=float(c.mean()),
            control_sd=float(c.std(ddof=1)),
            delta_ari=float(a - c.mean()),
            z=float((a - c.mean()) / c.std(ddof=1)),
            pct_rank=float((c < a).mean()),
            n_nonconverged=nonconv[lab],
            controls=[float(x) for x in c]))
    res["ablation_rows"] = rows

    # --- dark matter at R=20: fixed-D retention under cut and controls
    n20, m20 = one_partition([], s20)
    (CAMP / f"membership_r20_j{j}.json").write_text(json.dumps(
        {n: int(c) for n, c in zip(n20, m20)}))
    res["d_r20"] = d_block_metrics(n20, m20, D)
    h0 = build()
    vertices = set(h0.vs["name"])
    deg = dict(zip(h0.vs["name"], h0.strength(weights=h0.es["weight"])))
    cut = cuts["keyword-only"]
    cut_v = cut & vertices
    nn, m = one_partition(cut, s20)
    res["dm_cut"] = d_retention(nn, m, D)
    print(f"[j={j}] keyword cut fixed-D: {res['dm_cut']}", flush=True)
    dm_ctrl = []
    for k in range(K_DM):
        rng = np.random.default_rng(20260825 + 1_000_000 * j + 5_000 + k)
        cs = matched_control(deg, cut_v, rng, pool_restrict=vertices)
        assert len(cs) == len(cut_v)
        (CAMP / f"control_sets/j{j}_dm_k{k}.json").write_text(
            json.dumps(sorted(cs)))
        nn, m = one_partition(cs, s20)
        dm_ctrl.append(d_retention(nn, m, D))
        print(f"[j={j}]   dm control {k+1}: {dm_ctrl[-1]}", flush=True)
    res["dm_controls"] = dm_ctrl

    # --- Louvain vs fixed published canonical
    ig.set_random_number_generator(pyrandom)
    h = build()
    name_ix = {n: i for i, n in enumerate(h.vs["name"])}
    ref = np.full(h.vcount(), -1)
    for c in canon["communities"]:
        for b in c["members"]:
            if b in name_ix:
                ref[name_ix[b]] = c["id"]
    pyrandom.seed(BLOCK[j])
    lou = np.asarray(h.community_multilevel(weights=h.es["weight"]).membership)
    res["louvain"] = dict(ari=float(ari(ref, lou)),
                          one_to_one=float(one_to_one_agreement(ref, lou)))
    print(f"[j={j}] louvain {res['louvain']}", flush=True)

    (CAMP / f"real{j}.json").write_text(json.dumps(res, indent=1))
    print(f"[j={j}] wrote {CAMP / f'real{j}.json'}", flush=True)


if __name__ == "__main__":
    main()
