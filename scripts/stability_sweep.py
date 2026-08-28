"""Does consensus converge on one partition, or is the ambiguity intrinsic?

Consensus over R seeds raises reproducibility. If the gain keeps rising with R
the residual disagreement is a sampling artefact and can be bought off with
compute. If it plateaus, the graph genuinely admits more than one good
partition and no amount of averaging will fix it. That distinction decides
whether the instability is a defect to be removed or a property to be reported.

Also measures the single-run floor, which is what the manuscript's stated
figure should be compared against.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi
from consensus import build, collapse, leiden, consensus, sizes

OUT = Path(__file__).resolve().parent.parent / "data/communities"

def pairwise(ms, f):
    return [f(ms[i], ms[j]) for i in range(len(ms)) for j in range(i + 1, len(ms))]

def main():
    h = collapse(build())
    print(f"graph: {h.vcount():,} papers, {h.ecount():,} distinct pairs\n", flush=True)
    w = h.es["weight"]
    res = {}

    print("=== single Leiden run, no best-of, identical graph ===", flush=True)
    singles = [np.asarray(leiden(h, s, w).membership) for s in range(42, 52)]
    a = pairwise(singles, ari); n = pairwise(singles, nmi)
    print(f"  10 seeds, 45 pairs: ARI {np.mean(a):.3f} +/- {np.std(a):.3f} "
          f"(range {min(a):.3f}-{max(a):.3f})", flush=True)
    print(f"                      NMI {np.mean(n):.3f} +/- {np.std(n):.3f}\n", flush=True)
    res["single_run"] = dict(ari_mean=float(np.mean(a)), ari_sd=float(np.std(a)),
                             ari_min=float(min(a)), ari_max=float(max(a)),
                             nmi_mean=float(np.mean(n)), nmi_sd=float(np.std(n)))

    print("=== consensus reproducibility vs number of seeds ===", flush=True)
    res["sweep"] = []
    for R in (5, 10, 20, 30):
        t = time.time()
        ms, ks = [], []
        for start in (42, 542, 1042):
            m, r, ok = consensus(h, list(range(start, start + R)))
            ms.append(m); ks.append(len(sizes(m)))
        a = pairwise(ms, ari); n = pairwise(ms, nmi)
        print(f"  R={R:>2}  ARI {np.mean(a):.3f} +/- {np.std(a):.3f} "
              f"(range {min(a):.3f}-{max(a):.3f})   NMI {np.mean(n):.3f}   "
              f"communities {ks}   [{time.time()-t:.0f}s]", flush=True)
        res["sweep"].append(dict(R=R, ari_mean=float(np.mean(a)), ari_sd=float(np.std(a)),
                                 ari_min=float(min(a)), ari_max=float(max(a)),
                                 nmi_mean=float(np.mean(n)), communities=ks))
    (OUT / "stability_sweep.json").write_text(json.dumps(res, indent=1))
    print(f"\nwrote {OUT/'stability_sweep.json'}", flush=True)

if __name__ == "__main__":
    main()
