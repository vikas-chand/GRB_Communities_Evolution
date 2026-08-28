"""Dark-matter community survival, on the repaired V-matched sampler.

Replaces the legacy run, which used the old degree-only three-control sampler
at R = 20. Here the baseline is the same R = 10 consensus as the ablation
table, the dark-matter group is the baseline community with best overlap with
canonical C11, and K = 5 controls per test come from the effective-vertex
matched sampler.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from citation_communities import load_papers
from consensus import consensus, wq
from ablations import GRB
from ablation_controls2 import build, matched_control, papers
SEEDS = list(range(42, 62))   # R = 20: the resolution at which the dark-matter group exists

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
K = 5

def survival(n0, m0, nn, m, targets):
    nm = {n: c for n, c in zip(nn, m)}
    out = {}
    for c in targets:
        mem = [n0[i] for i in np.where(m0 == c)[0]]
        dest = [nm[n] for n in mem if n in nm]
        out[int(c)] = float(np.bincount(dest).max() / len(mem)) if dest else 0.0
    return out

def main():
    h0 = build()
    n0 = h0.vs["name"]
    m0, _, ok = consensus(h0, SEEDS)
    assert ok
    m0 = np.asarray(m0)
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    c11 = set(next(c["members"] for c in canon["communities"] if c["id"] == 11))
    ix = {n: i for i, n in enumerate(n0)}
    ov = {}
    for c in np.unique(m0):
        mem = {n0[i] for i in np.where(m0 == c)[0]}
        if len(mem) >= 30:
            ov[int(c)] = len(mem & c11) / len(c11)
    dm = max(ov, key=ov.get)
    dm_size = int((m0 == dm).sum())
    big = [int(c) for c in np.unique(m0) if (m0 == c).sum() >= 30]
    print(f"baseline R={len(SEEDS)}: dark-matter group = C{dm} (n={dm_size}, "
          f"overlap {ov[dm]:.0%} of canonical C11)", flush=True)

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    cut = {b for b, d in papers().items() if not GRB.search(text(d))}
    vertices = set(n0)
    deg = dict(zip(n0, h0.strength(weights=h0.es["weight"])))
    cut_v = cut & vertices

    def run(drop, tag):
        h = build(frozenset(drop))
        m, _, okc = consensus(h, SEEDS)
        assert okc, tag
        s = survival(n0, m0, h.vs["name"], np.asarray(m), big)
        print(f"  {tag:<18} dark-matter retains {s[dm]:5.1%}   "
              f"weakest other {min(v for c, v in s.items() if c != dm):5.1%}",
              flush=True)
        return s

    real = run(cut, "keyword-only cut")
    ctrl = []
    for k in range(K):
        rng = np.random.default_rng(20260825 + 5000 + k)
        cs = matched_control(deg, cut_v, rng, pool_restrict=vertices)
        assert len(cs) == len(cut_v)
        ctrl.append(run(cs, f"matched control {k+1}"))

    (OUT / "darkmatter_control2.json").write_text(json.dumps(dict(
        R=len(SEEDS), K=K, dm_group=int(dm), dm_size=dm_size,
        dm_overlap_c11=ov[dm], real=real,
        controls=ctrl), indent=1))
    print(f"wrote {OUT/'darkmatter_control2.json'}")

if __name__ == "__main__":
    main()
