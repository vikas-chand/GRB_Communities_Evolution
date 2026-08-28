"""Stable cores, boundary entropy, and the medoid partition.

The consensus partition is reproducible at ARI ~0.9, which means one paper in
ten still moves between runs. Reporting a single crisp membership hides that.
This measures it per paper: 100 independent Leiden runs, each run's communities
matched to the canonical consensus labels by plurality overlap, then for every
paper the distribution over canonical labels across runs.

  stable core   papers assigned to their canonical community in >=90% of runs
  entropy       Shannon entropy of a paper's label distribution (bits)
  medoid        the single run with minimum mean (1 - ARI) to all other runs,
                the honest choice if one concrete partition must be displayed
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from collections import Counter
from sklearn.metrics import adjusted_rand_score as ari
from consensus import build, collapse, leiden

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
NRUNS = 100

def main():
    h = collapse(build())
    names = h.vs["name"]
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    ref = {}
    for c in canon["communities"]:
        for b in c["members"]:
            ref[b] = c["id"]
    refv = np.array([ref[n] for n in names])
    K = refv.max() + 1

    runs = []
    for k in range(NRUNS):
        # seeds disjoint from the canonical ensemble (42-71), so the
        # evaluation runs share nothing with the reference construction
        m = np.asarray(leiden(h, 200 + k, h.es["weight"]).membership)
        runs.append(m)
        if (k + 1) % 20 == 0:
            print(f"  {k+1}/{NRUNS} runs", flush=True)

    # match each run's communities to canonical labels by plurality overlap
    counts = np.zeros((len(names), K + 1), dtype=np.int32)   # last col = unmatched
    for m in runs:
        lab = {}
        for c in np.unique(m):
            idx = np.where(m == c)[0]
            best = Counter(refv[idx]).most_common(1)[0][0]
            lab[c] = best
        assigned = np.array([lab[c] for c in m])
        for i, a in enumerate(assigned):
            counts[i, a] += 1

    share = counts[:, :K] / NRUNS
    # stability is the share of runs assigning the paper its OWN canonical
    # label; for this product it equals the max share for every paper, but the
    # definition is the own-label one
    own = share[np.arange(len(names)), refv]
    top = own
    with np.errstate(divide="ignore", invalid="ignore"):
        pl = np.where(share > 0, share, 1.0)
        ent = -(share * np.log2(pl)).sum(axis=1)
    stable = top >= 0.90

    print(f"\nstable core (>=90% of runs): {stable.sum():,} of {len(names):,} "
          f"papers ({stable.mean():.1%})")
    print(f"entropy: median {np.median(ent):.3f} bits, "
          f"90th pct {np.percentile(ent,90):.3f}, max {ent.max():.3f}\n")
    rows = []
    for c in sorted(canon["communities"], key=lambda x: -x["size"]):
        if not c["above_threshold"]:
            continue
        mk = refv == c["id"]
        rows.append(dict(id=c["id"], size=int(mk.sum()),
                         core_frac=float(stable[mk].mean()),
                         median_entropy=float(np.median(ent[mk]))))
        print(f"  C{c['id']:<3} n={mk.sum():<5} core {stable[mk].mean():5.1%}  "
              f"median entropy {np.median(ent[mk]):.3f}  {', '.join(c['terms'][:3])}")

    # medoid
    A = np.zeros((NRUNS, NRUNS))
    for i in range(NRUNS):
        for j in range(i + 1, NRUNS):
            A[i, j] = A[j, i] = ari(runs[i], runs[j])
    md = int(np.argmax(A.sum(axis=1)))
    print(f"\nmedoid run: seed {42+md}, mean ARI to ensemble "
          f"{A[md].sum()/(NRUNS-1):.3f}, ARI to canonical {ari(runs[md], refv):.3f}")

    np.save(OUT / "boundary_entropy.npy", ent)
    np.save(OUT / "coassign_share.npy", share)
    (OUT / "boundary_entropy.json").write_text(json.dumps(dict(
        nruns=NRUNS, stable_frac=float(stable.mean()),
        median_entropy=float(np.median(ent)),
        medoid_seed=200 + md, medoid_mean_ari=float(A[md].sum() / (NRUNS - 1)),
        medoid_ari_to_canonical=float(ari(runs[md], refv)),
        communities=rows), indent=1))
    print(f"wrote {OUT/'boundary_entropy.json'}")

if __name__ == "__main__":
    main()
