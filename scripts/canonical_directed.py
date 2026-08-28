"""The directed canonical partition, built so the representation switch is one
editorial decision rather than a rebuild.

Citations have direction; the reviewer's recommendation is that the directed
graph become primary, with the simple projection as robustness check and the
reciprocal-weighted multigraph demoted to a sensitivity analysis. This produces
the directed consensus partition at R = 30, characterises it exactly as the
current canonical is characterised, and maps every community onto the current
canonical so the cost of switching is visible before it is paid.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import igraph as ig
import numpy as np
from citation_communities import load_papers, STOPWORDS, TOKEN
from dcm_null import directed_edges
from representation_three import consensus_directed
from consensus import sizes

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/communities"
SEEDS = list(range(42, 72))

def main():
    papers = load_papers(ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl", "core")
    de = directed_edges(papers)
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b, _ in de],
                 directed=True)
    print(f"directed graph: {g.vcount():,} nodes, {g.ecount():,} arcs", flush=True)

    m, rounds, ok = consensus_directed(g, SEEDS)
    if not ok:
        raise RuntimeError(f"directed consensus did not converge in {rounds} rounds")
    m = np.asarray(m)
    q = g.modularity(list(m), directed=True)
    big = [c for c in np.unique(m) if (m == c).sum() >= 30]
    big.sort(key=lambda c: -(m == c).sum())
    print(f"consensus R={len(SEEDS)}: converged in {rounds} rounds, "
          f"Q_dir = {q:.4f}, {len(np.unique(m))} groups, {len(big)} with N >= 30",
          flush=True)

    all_df = Counter(); n_docs = len(papers)
    for d in papers.values():
        for t in set(TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower())):
            all_df[t] += 1
    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    ref = {}
    for c in canon["communities"]:
        for b in c["members"]:
            ref[b] = c["id"]

    comms = []
    for cid in big:
        mem = [names[i] for i in np.where(m == cid)[0]]
        tf = Counter()
        for b in mem:
            d = papers[b]
            for t in TOKEN.findall(f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()):
                if t not in STOPWORDS and len(t) > 3:
                    tf[t] += 1
        tot = sum(tf.values()) or 1
        terms = [t for _, t in sorted(((c / tot * np.log(1 + n_docs / (1 + all_df[t])), t)
                                       for t, c in tf.items() if c >= 5), reverse=True)[:8]]
        src = Counter(ref.get(b, -1) for b in mem)
        top = src.most_common(2)
        comms.append(dict(id=int(cid), size=len(mem), terms=terms,
                          from_canonical=[[int(k), int(v)] for k, v in top],
                          members=mem))
        mapdesc = "; ".join(f"C{k} {v/len(mem):.0%}" for k, v in top)
        print(f"  D{cid:<3} n={len(mem):<5} {', '.join(terms[:4]):<44} <- {mapdesc}",
              flush=True)

    (OUT / "canonical_directed.json").write_text(json.dumps(dict(
        q_directed=float(q), R=len(SEEDS), rounds=rounds,
        n_groups=int(len(np.unique(m))), n_above=len(big),
        communities=comms), indent=1))
    print(f"wrote {OUT/'canonical_directed.json'}")

if __name__ == "__main__":
    main()
