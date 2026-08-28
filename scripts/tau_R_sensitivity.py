"""Sensitivity of the consensus partition to tau, and convergence in R.

tau is the co-association threshold below which an edge is dropped between
rounds; it was set at 0.5 without a stated reason. R convergence asks whether
doubling the ensemble from 30 to 60 runs still moves the fixed point.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari
from consensus import build, collapse, consensus, sizes

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"

def canon_membership(names):
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    ref = {}
    for c in canon["communities"]:
        for b in c["members"]:
            ref[b] = c["id"]
    return np.array([ref[n] for n in names])

def main():
    h = collapse(build())
    refv = canon_membership(h.vs["name"])
    out = {"tau": [], "R": []}
    print("=== tau sensitivity, R = 15 ===", flush=True)
    for tau in (0.4, 0.5, 0.6, 0.7):
        m, r, ok = consensus(h, list(range(42, 57)), tau=tau)
        v = ari(refv, m)
        n30 = len(sizes(m))
        out["tau"].append(dict(tau=tau, ari_vs_canonical=float(v), n30=n30,
                               converged=bool(ok), rounds=r))
        print(f"  tau={tau}: ARI vs canonical {v:.3f}  {n30} communities >=30 "
              f"(converged={ok} in {r})", flush=True)
    print("\n=== R convergence ===", flush=True)
    m60, r60, ok60 = consensus(h, list(range(42, 102)))
    v = ari(refv, m60)
    out["R"].append(dict(R=60, ari_vs_R30_canonical=float(v),
                         n30=len(sizes(m60)), converged=bool(ok60), rounds=r60,
                         note="seeds nested with canonical R=30"))
    print(f"  R=60 vs canonical R=30: ARI {v:.3f}  {len(sizes(m60))} communities "
          f"(converged={ok60} in {r60})", flush=True)
    (OUT / "tau_R_sensitivity.json").write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT/'tau_R_sensitivity.json'}")

if __name__ == "__main__":
    main()
