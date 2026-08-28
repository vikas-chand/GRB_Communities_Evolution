"""Partition dependence of the role coordinates.

PageRank, betweenness, and null-adjusted influence are graph properties and
do not depend on the partition. Participation P and within-community degree
z do. This check recomputes P and z under the seeded Infomap partition and
correlates them with the canonical values over all linked papers, and
reports the headline papers, answering whether role classifications are an
artefact of the partition choice.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from ablation_controls2 import build

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

HEADLINE = {
    "1993ApJ...405..273W": "Woosley 1993 (collapsar)",
    "2017PhRvL.119p1101A": "GW170817 GW detection",
    "1991ApJ...373..277K": "Krolik & Pier 1991",
}


def roles_under(h, memb):
    """P and z for every vertex under an integer membership vector."""
    n = h.vcount()
    memb = np.asarray(memb)
    ncom = memb.max() + 1
    kic = np.zeros((n, ncom))
    w = np.asarray(h.es["weight"], dtype=float)
    for e, wt in zip(h.es, w):
        a, b = e.tuple
        kic[a, memb[b]] += wt
        kic[b, memb[a]] += wt
    k = kic.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = 1.0 - ((kic / k[:, None]) ** 2).sum(axis=1)
    P[k == 0] = np.nan
    kin = np.array([kic[i, memb[i]] for i in range(n)])
    z = np.zeros(n)
    for c in range(ncom):
        m = memb == c
        if m.sum() < 2:
            z[m] = 0.0
            continue
        mu, sd = kin[m].mean(), kin[m].std()
        z[m] = (kin[m] - mu) / sd if sd > 0 else 0.0
    return P, z


def main() -> None:
    h = build()
    names = h.vs["name"]
    ix = {b: i for i, b in enumerate(names)}

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    cmemb = np.zeros(h.vcount(), dtype=int)
    lab = {}
    for j, c in enumerate(canon["communities"]):
        for b in c["members"]:
            if b in ix:
                cmemb[ix[b]] = j
    algo = json.loads((OUT / "algorithm_comparison2.json").read_text())
    imemb = np.asarray(algo["memberships"]["infomap"])

    Pc, zc = roles_under(h, cmemb)
    Pi, zi = roles_under(h, imemb)
    ok = ~np.isnan(Pc) & ~np.isnan(Pi)
    rP = float(spearmanr(Pc[ok], Pi[ok]).statistic)
    rz = float(spearmanr(zc[ok], zi[ok]).statistic)

    heads = {}
    for b, labl in HEADLINE.items():
        i = ix[b]
        heads[b] = dict(label=labl,
                        P_canonical=round(float(Pc[i]), 3),
                        P_infomap=round(float(Pi[i]), 3),
                        z_canonical=round(float(zc[i]), 2),
                        z_infomap=round(float(zi[i]), 2))

    product = dict(note="P and z depend on the partition; PageRank, "
                        "betweenness, and null-adjusted influence do not.",
                   spearman_P=round(rP, 3), spearman_z=round(rz, 3),
                   n_papers=int(ok.sum()), headline=heads)
    (OUT / "infomap_roles_check.json").write_text(json.dumps(product,
                                                             indent=1))
    print(json.dumps(product, indent=1))


if __name__ == "__main__":
    main()
