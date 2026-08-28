"""Resolution sweep on the corrected corpus.

The old plateau was measured on the contaminated corpus and cannot be carried
over. Best of ten starts per gamma, selected by weighted modularity.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import leidenalg as la
from sklearn.metrics import adjusted_rand_score as ari
from consensus import build, collapse, wq

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
GAMMAS = [0.3, 0.5, 0.7, 1.0, 1.3, 1.7, 2.2, 3.0]

def best(h, gamma):
    # rank candidates by their OWN objective at this gamma; ranking by the
    # gamma=1 modularity would bias every sweep point toward gamma=1 structure
    return max((la.find_partition(h, la.RBConfigurationVertexPartition,
                                  weights=h.es["weight"], resolution_parameter=gamma,
                                  n_iterations=-1, seed=s) for s in range(42, 52)),
               key=lambda p: p.quality())

def main():
    h = collapse(build())
    parts, rows = {}, []
    for g in GAMMAS:
        p = best(h, g)
        m = np.asarray(p.membership)
        parts[g] = m
        n30 = int(sum(1 for c in np.bincount(m) if c >= 30))
        rows.append(dict(gamma=g, q_gamma=float(p.quality()),
                         q_std=wq(h, m, h.es["weight"]), n30=n30,
                         n_total=int(m.max() + 1)))
        print(f"  gamma={g:<5} Q_std={rows[-1]['q_std']:.4f}  {n30:>3} "
              f"communities >=30 ({rows[-1]['n_total']} total)", flush=True)
    print("\nadjacent-gamma agreement:")
    for a, b in zip(GAMMAS, GAMMAS[1:]):
        v = ari(parts[a], parts[b])
        print(f"  {a} vs {b}: ARI {v:.3f}")
        rows[GAMMAS.index(b)]["ari_prev"] = float(v)
    ref = parts[1.0]
    for g in GAMMAS:
        rows[GAMMAS.index(g)]["ari_vs_1"] = float(ari(parts[g], ref))
    (OUT / "gamma_sweep.json").write_text(json.dumps(rows, indent=1))
    print(f"wrote {OUT/'gamma_sweep.json'}")

if __name__ == "__main__":
    main()
