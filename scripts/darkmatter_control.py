"""Is the dark-matter community's collapse specific to the keyword papers?

The global ARI test says the keyword-only cut perturbs the partition no more
than deleting the same papers at random. That is a whole-partition statement and
cannot settle a claim about one community. A small community might be fragile to
losing any 838 vertices, in which case its collapse says nothing about indexing.

So we repeat the cut against the same degree-matched control sets used in
`ablation_controls.py`, and compare per-community survival rather than ARI. The
control seeds are reproduced exactly.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from citation_communities import load_papers
from consensus import consensus, sizes, wq
from ablations import GRB
from ablation_controls import build, matched_control, SEEDS, MIN

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"

def survival(n0, m0, nn, m, big):
    nm = {n: c for n, c in zip(nn, m)}
    out = {}
    for c in big:
        mem = [n0[i] for i in np.where(m0 == c)[0]]
        dest = [nm[n] for n in mem if n in nm]
        out[int(c)] = (float(np.bincount(dest).max() / len(mem)) if dest else 0.0, len(mem))
    return out

def main():
    papers = load_papers(CORE, "core")
    h0 = build(papers)
    m0, _, ok = consensus(h0, SEEDS)
    if not ok:
        raise RuntimeError("baseline consensus did not converge")
    n0 = h0.vs["name"]
    deg = dict(zip(n0, h0.strength(weights=h0.es["weight"])))
    big = [c for c in np.unique(m0) if (m0 == c).sum() >= MIN]
    big.sort(key=lambda c: -(m0 == c).sum())
    print(f"baseline: {h0.vcount():,} papers  Q={wq(h0,m0,h0.es['weight']):.4f}  "
          f"{len(big)} communities >= {MIN}\n", flush=True)

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    cut = {b for b, d in papers.items() if not GRB.search(text(d))}

    def run(drop, tag):
        h = build(papers, drop)
        m, _, okc = consensus(h, SEEDS)
        if not okc:
            raise RuntimeError(f"{tag}: consensus did not converge")
        s = survival(n0, m0, h.vs["name"], m, big)
        worst = min(s.items(), key=lambda kv: kv[1][0])
        nbroken = sum(1 for f, _ in s.values() if f < 0.5)
        print(f"{tag:<22} weakest C{worst[0]} (n={worst[1][1]}) retains {worst[1][0]:.0%}   "
              f"communities below 50%: {nbroken}", flush=True)
        return s, worst, nbroken

    real, rworst, rbroken = run(cut, "keyword-only cut")
    dm = sorted(big, key=lambda c: abs((m0 == c).sum() - 99))[0]   # the 99-paper group
    print(f"   dark-matter group is C{dm} (n={(m0==dm).sum()}), "
          f"retains {real[int(dm)][0]:.0%}\n", flush=True)

    ctrls = []
    all_bibs = list(papers)
    for k in range(3):
        rng = np.random.default_rng(20260822 + 2000 + k)     # same sets as the ARI run
        cs = matched_control(all_bibs, deg, cut, rng)
        s, w, nb = run(cs, f"matched control {k+1}")
        print(f"   its C{dm} retains {s[int(dm)][0]:.0%}\n", flush=True)
        ctrls.append(dict(weakest_id=int(w[0]), weakest_frac=float(w[1][0]),
                          n_below_50=int(nb), dm_frac=float(s[int(dm)][0])))

    dm_ctrl = [c["dm_frac"] for c in ctrls]
    worst_ctrl = [c["weakest_frac"] for c in ctrls]
    print("=" * 66)
    print(f"dark-matter survival, real cut : {real[int(dm)][0]:.0%}")
    print(f"dark-matter survival, controls : "
          f"{', '.join(f'{x:.0%}' for x in dm_ctrl)}  (mean {np.mean(dm_ctrl):.0%})")
    print(f"weakest-community survival, real cut : {rworst[1][0]:.0%} (C{rworst[0]})")
    print(f"weakest-community survival, controls : "
          f"{', '.join(f'{x:.0%}' for x in worst_ctrl)}")
    specific = real[int(dm)][0] < min(dm_ctrl) - 0.10
    print(f"\n=> the collapse IS specific to the keyword papers: {specific}")
    (OUT / "darkmatter_control.json").write_text(json.dumps(dict(
        dm_community=int(dm), dm_size=int((m0 == dm).sum()),
        real_dm=float(real[int(dm)][0]), real_weakest=float(rworst[1][0]),
        real_n_below_50=int(rbroken), controls=ctrls, specific=bool(specific)), indent=1))
    print(f"wrote {OUT/'darkmatter_control.json'}")

if __name__ == "__main__":
    main()
