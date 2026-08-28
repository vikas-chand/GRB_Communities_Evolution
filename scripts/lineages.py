"""Many-to-many community lineages with significance-tested overlap edges.

Replaces single best-Jaccard parent threading, which structurally forbids the
two events that matter most in a growing literature: splits and merges. For
consecutive cumulative snapshots, every community pair (A at t, B at t+1) gets
a hypergeometric overlap test on the papers that already existed at t, with
Benjamini-Hochberg control across each transition. Three quantities per edge:

  r = |A n B_old| / |A|        where did A's members go
  c = |A n B_old| / |B_old|    where did B's old members come from
  g = |B \\ U_t| / |B|          how much of B is new papers (growth, not blame)

Events: continuation (one strong r and c), split (one A, several significant
B), merge (several A, one B), formation (no significant predecessor),
lineage termination (no significant successor). Termination of a partition
identity is not the death of a research programme; activity evidence is a
separate question.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from scipy.stats import hypergeom

from citation_communities import load_papers
from dcm_null import directed_edges, undirected
from consensus import collapse, consensus, wq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
CUTS = [1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2026]
MIN = 30
SEEDS = list(range(42, 52))
ALPHA = 0.05

def snapshot(papers, cut):
    de = [(a, b, y) for a, b, y in directed_edges(papers)
          if (papers[a].get("year") or 0) <= cut and (papers[b].get("year") or 0) <= cut]
    if not de:
        return None, None
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return collapse(g), names

def communities(h, names):
    m, r, ok = consensus(h, SEEDS)
    if not ok:
        raise RuntimeError("snapshot consensus did not converge")
    m = np.asarray(m)
    out = {}
    for c in np.unique(m):
        mem = [names[i] for i in np.where(m == c)[0]]
        if len(mem) >= MIN:
            out[int(c)] = set(mem)
    return out, float(wq(h, m, h.es["weight"]))

def canon_map(comms):
    """label each snapshot community by its best-overlap canonical community"""
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    ref = {c["id"]: set(c["members"]) for c in canon["communities"]
           if c["above_threshold"]}
    out = {}
    for cid, mem in comms.items():
        best = max(ref, key=lambda k: len(mem & ref[k]))
        out[cid] = dict(canonical=int(best),
                        frac=len(mem & ref[best]) / len(mem))
    return out

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    snaps = {}
    for cut in CUTS:
        h, names = snapshot(papers, cut)
        if h is None or h.vcount() < 100:
            print(f"cut {cut}: too small, skipped", flush=True)
            continue
        comms, q = communities(h, names)
        snaps[cut] = dict(nodes=set(names), comms=comms,
                          sizes={int(c): len(m) for c, m in comms.items()},
                          canon=canon_map(comms))
        print(f"cut {cut}: {h.vcount():,} papers, {len(comms)} communities >= {MIN}, "
              f"Q={q:.3f}", flush=True)

    cuts = sorted(snaps)
    transitions = []
    for t0, t1 in zip(cuts, cuts[1:]):
        U = snaps[t0]["nodes"]
        A_, B_ = snaps[t0]["comms"], snaps[t1]["comms"]
        n = len(U)
        # every A x B pair is in the multiplicity family, including zero
        # overlaps (their p is 1); BH is the standard step-up: find the largest
        # rank whose p <= alpha*rank/m and accept every test up to it
        tests = []
        for ai, A in sorted(A_.items()):
            for bi, B in sorted(B_.items()):
                Bold = B & U
                k = len(A & Bold)
                p = float(hypergeom.sf(k - 1, n, len(Bold), len(A)))
                tests.append((p, ai, bi, k, len(A), len(Bold), len(B)))
        tests.sort()
        mtests = len(tests)
        cutoff = 0
        for rank, t in enumerate(tests, 1):
            if t[0] <= ALPHA * rank / mtests:
                cutoff = rank
        edges = [dict(src=ai, dst=bi, overlap=k,
                      r=k / na, c=k / nbo if nbo else 0.0,
                      g=(nb - nbo) / nb, p=p)
                 for (p, ai, bi, k, na, nbo, nb) in tests[:cutoff] if k > 0]
        out_deg = {}
        in_deg = {}
        for e in edges:
            if e["r"] >= 0.10 or e["c"] >= 0.10:
                out_deg[e["src"]] = out_deg.get(e["src"], 0) + 1
                in_deg[e["dst"]] = in_deg.get(e["dst"], 0) + 1
        events = dict(
            splits=[a for a, d in out_deg.items() if d >= 2],
            merges=[b for b, d in in_deg.items() if d >= 2],
            terminations=[a for a in A_ if out_deg.get(a, 0) == 0],
            formations=[b for b in B_ if in_deg.get(b, 0) == 0],
        )
        transitions.append(dict(t0=t0, t1=t1, n_tests=mtests,
                                n_significant=len(edges), edges=edges,
                                events=events))
        print(f"{t0}->{t1}: {mtests} tested, {len(edges)} significant; "
              f"splits {len(events['splits'])}, merges {len(events['merges'])}, "
              f"terminations {len(events['terminations'])}, "
              f"formations {len(events['formations'])}", flush=True)

    (OUT / "lineages.json").write_text(json.dumps(dict(
        cuts=cuts, min_size=MIN, alpha=ALPHA, R=len(SEEDS),
        snapshots={str(c): dict(sizes=snaps[c]["sizes"], canon=snaps[c]["canon"],
                                n_nodes=len(snaps[c]["nodes"]))
                   for c in cuts},
        transitions=transitions), indent=1, default=int))
    print(f"\nwrote {OUT/'lineages.json'}")

if __name__ == "__main__":
    main()
