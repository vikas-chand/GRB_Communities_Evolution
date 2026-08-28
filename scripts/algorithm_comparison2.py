"""Cross-algorithm agreement on the frozen canonical graph, seeded, saved.

Replaces algorithm_comparison.py, which ran on a different node universe
(reference-plus-citation union), left Infomap unseeded, and saved nothing.
Here every algorithm runs on the canonical collapsed weighted graph, igraph's
RNG is seeded through Python's random module, memberships are saved, and
agreement with the canonical consensus is reported as ARI and NMI plus a
symmetric per-paper agreement under a one-to-one greedy label match.
"""
from __future__ import annotations
import json
import random as pyrandom
from pathlib import Path

import igraph as ig
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi

from consensus import build, collapse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

def one_to_one_agreement(a, b):
    """greedy one-to-one community matching, symmetric per-paper agreement"""
    from collections import Counter
    pairs = Counter(zip(a.tolist(), b.tolist()))
    used_a, used_b, matched = set(), set(), 0
    for (ca, cb), n in pairs.most_common():
        if ca in used_a or cb in used_b:
            continue
        used_a.add(ca); used_b.add(cb); matched += n
    return matched / len(a)

def main():
    ig.set_random_number_generator(pyrandom)
    g = build()
    h = collapse(g)
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    name_ix = {n: i for i, n in enumerate(h.vs["name"])}
    ref = np.full(h.vcount(), -1)
    for c in canon["communities"]:
        for b in c["members"]:
            ref[name_ix[b]] = c["id"]
    print(f"graph: {h.vcount():,} nodes, {h.ecount():,} weighted edges", flush=True)

    runs = {}
    pyrandom.seed(42)
    runs["louvain"] = np.asarray(
        h.community_multilevel(weights=h.es["weight"]).membership)
    pyrandom.seed(42)
    runs["infomap"] = np.asarray(
        h.community_infomap(edge_weights=h.es["weight"]).membership)
    pyrandom.seed(42)
    runs["leading_eigenvector"] = np.asarray(
        h.community_leading_eigenvector(weights=h.es["weight"]).membership)

    def purity_into(fine, coarse, min_size=1):
        """share of papers whose fine block's majority coarse label matches
        their own coarse label: how far `fine` nests inside `coarse`"""
        from collections import Counter
        lab = {}
        for c in np.unique(fine):
            mask = fine == c
            if mask.sum() < min_size:
                continue
            lab[c] = Counter(coarse[mask]).most_common(1)[0][0]
        ok = sum(1 for i in range(len(fine))
                 if fine[i] in lab and lab[fine[i]] == coarse[i])
        return ok / len(fine)

    out = {}
    for k, m in runs.items():
        out[k] = dict(ari=float(ari(ref, m)), nmi=float(nmi(ref, m)),
                      one_to_one=float(one_to_one_agreement(ref, m)),
                      nesting_purity=float(purity_into(m, ref)),
                      nesting_purity_30=float(purity_into(m, ref, 30)),
                      n_communities_30=int(sum(1 for c in np.bincount(m) if c >= 30)),
                      membership=[int(x) for x in m])
        print(f"  {k:<20} ARI {out[k]['ari']:.3f}  NMI {out[k]['nmi']:.3f}  "
              f"one-to-one {out[k]['one_to_one']:.3f}  "
              f"nesting purity {out[k]['nesting_purity']:.3f}  "
              f"{out[k]['n_communities_30']} communities >=30", flush=True)
    (OUT / "algorithm_comparison2.json").write_text(json.dumps(
        dict(seed=42, graph="canonical collapsed weighted, 13801 nodes",
             results={k: {x: v for x, v in d.items() if x != "membership"}
                      for k, d in out.items()},
             memberships={k: d["membership"] for k, d in out.items()}), indent=1))
    print(f"wrote {OUT/'algorithm_comparison2.json'}")

if __name__ == "__main__":
    main()
