"""How Infomap's finer partition subdivides the canonical communities.

Uses the saved seeded Infomap membership (algorithm_comparison2.json) as an
independent-objective probe of the map's interior: for each canonical
community, the Infomap blocks of at least 30 members nested inside it; and
for each of the eight sub-community parents, the agreement between Infomap's
blocks and our consensus sub-communities on shared papers.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import (adjusted_rand_score as ari,
                             normalized_mutual_info_score as nmi)

from ablation_controls2 import build

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"


def main() -> None:
    h = build()
    names = h.vs["name"]
    d = json.loads((OUT / "algorithm_comparison2.json").read_text())
    info = np.asarray(d["memberships"]["infomap"])
    assert len(info) == len(names)
    im = dict(zip(names, info))

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    cm = {b: c["id"] for c in canon["communities"]
          if c["id"] <= 13 and len(c["members"]) >= 30 for b in c["members"]}

    div = {}
    for cid in range(14):
        mem = [b for b, c in cm.items() if c == cid]
        cnt = Counter(im[b] for b in mem if b in im)
        div[cid] = [(int(blk), int(n)) for blk, n in cnt.most_common()
                    if n >= 30]

    sub = json.loads((OUT / "subcommunities.json").read_text())
    rows = []
    for p in sub:
        pid = p.get("parent", p.get("id"))
        ours = {}
        for k, ch in enumerate(p["children"]):
            for b in ch["members"]:
                ours[b] = k
        shared = [b for b in ours if b in im]
        a = [ours[b] for b in shared]
        b_ = [im[x] for x in shared]
        rows.append(dict(parent=pid, n_children=len(p["children"]),
                         n_infomap=len(div[pid]), n_shared=len(shared),
                         nmi=round(float(nmi(a, b_)), 3),
                         ari=round(float(ari(a, b_)), 3)))

    product = dict(
        subdivision={f"C{c}": [[b, n] for b, n in v] for c, v in div.items()},
        parent_agreement=rows,
        n_blocks_nested=int(sum(len(v) for v in div.values())))
    (OUT / "infomap_subdivision.json").write_text(json.dumps(product,
                                                             indent=1))
    print("wrote", OUT / "infomap_subdivision.json")


if __name__ == "__main__":
    main()
