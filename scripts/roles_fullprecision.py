"""Full-precision within-community z and participation for every linked paper.

The master role table stores z to two decimals and P to three, so any
thresholding or reformatting from it can flip half-way cases. This producer
recomputes exactly the canonical quantities of paper_roles.py (simple
projection participation; population z of within-community degree) at full
precision and emits them, plus the strict Guimera-Amaral census computed from
those values, so that no manuscript number is derived from a rounded one.
"""
from __future__ import annotations
import gzip, json
from pathlib import Path

import igraph as ig
import numpy as np

from citation_communities import load_papers
from dcm_null import directed_edges

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"


def main() -> None:
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    N = len(names)
    gd = ig.Graph(n=N, edges=[(idx[a], idx[b]) for a, b, _ in de], directed=True)
    gu = gd.as_undirected(mode="collapse")

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = np.full(N, -1)
    for c in canon["communities"]:
        for b in c["members"]:
            memb[idx[b]] = c["id"]
    stable = np.load(OUT / "coassign_share.npy").max(axis=1) >= 0.90

    P = np.zeros(N)
    for i in range(N):
        nb = np.array(gu.neighbors(i))
        if nb.size:
            _, cnt = np.unique(memb[nb], return_counts=True)
            P[i] = 1.0 - ((cnt / nb.size) ** 2).sum()
    kin_int = np.zeros(N)
    for a, b in gu.get_edgelist():
        if memb[a] == memb[b]:
            kin_int[a] += 1; kin_int[b] += 1
    z = np.zeros(N)
    for c in np.unique(memb):
        mk = memb == c
        mu, sd = kin_int[mk].mean(), kin_int[mk].std()
        z[mk] = (kin_int[mk] - mu) / (sd or 1.0)

    with gzip.open(OUT / "paper_roles_fullprec.csv.gz", "wt") as f:
        f.write("bibcode,community,stable,z_within,participation\n")
        for i, n in enumerate(names):
            f.write(f"{n},{memb[i]},{int(stable[i])},{float(z[i])!r},{float(P[i])!r}\n")

    def census(mask):
        hub = z >= 2.5
        return dict(R5_provincial=int((mask & hub & (P < 0.30)).sum()),
                    R6_connector=int((mask & hub & (P >= 0.30) & (P < 0.75)).sum()),
                    R7_kinless=int((mask & hub & (P >= 0.75)).sum()),
                    two_class_connector=int((mask & hub & (P >= 0.62)).sum()),
                    two_class_provincial=int((mask & hub & (P < 0.62)).sum()),
                    peripheral=int((mask & ~hub).sum()))
    disp = memb <= 13
    product = dict(
        note="strict Guimera-Amaral R5/R6/R7 at z>=2.5 with P<0.30 / 0.30-0.75 / >=0.75; two-class split at P=0.62; full precision",
        displayed_stable=census(stable & disp), all_stable=census(stable),
        displayed_linked=census(disp), all_linked=census(np.ones(N, bool)))
    (OUT / "role_census.json").write_text(json.dumps(product, indent=1))
    print(json.dumps(product, indent=1))


if __name__ == "__main__":
    main()
