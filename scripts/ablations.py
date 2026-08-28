"""Attack the stated limitations rather than declaring them.

Each limitation names a set of papers whose presence might be driving the
partition. For each, we remove that set, rebuild the graph, repartition, and
measure what changed against the baseline on the papers common to both. A
limitation that survives this is bounded; one that does not is a defect.

  homonym      papers entering through GRB as a non-astronomical acronym
  keyword-only papers with no GRB string in their own title or abstract
  no-refs      papers with no ADS reference list, whose linkability is
               correlated with how much attention they later received
  refereed     the refereed subset, as a document-type sensitivity test

Reported per ablation: papers and edges removed, Q, community count, ARI and NMI
against the baseline on shared papers, and whether each baseline community
survives (defined as >=50% of its members landing together in one new one).
"""
from __future__ import annotations
import json, re
from pathlib import Path
import igraph as ig, leidenalg as la, numpy as np
from sklearn.metrics import adjusted_rand_score as ari, normalized_mutual_info_score as nmi
from citation_communities import load_papers
from dcm_null import directed_edges, undirected

CORE = Path("data/raw/ads_corpus_v2_core_frozen.jsonl")
GRB = re.compile(r'gamma[\s\-‐-―]?ray burst|γ[\s\-]?ray burst|\bGRB|\bXRF\b', re.I)
# conservative homonym screen: GRB appears, but in a non-astronomical context
HOMONYM = re.compile(r'\briver basin|\bbasin\b.{0,40}\b(runoff|catchment|hydrolog|water)|'
                     r'\bGrb-?2\b|\breceptor\b|\bkinase\b|\bprotein\b|\bgene\b|'
                     r'\bGr\.?B\b.{0,30}steel|\bsteel\b|\bthunderstorm', re.I)
ASTRO = re.compile(r'burst|afterglow|redshift|luminosit|photon|spectr|galax|'
                   r'neutron star|black hole|supernova|jet\b|fluence', re.I)

def partition(g, seeds=range(42, 47)):
    return max((la.find_partition(g, la.RBConfigurationVertexPartition,
                                  resolution_parameter=1.0, n_iterations=-1, seed=s)
                for s in seeds), key=lambda p: p.modularity)

def build(papers, drop=frozenset()):
    de = [(a, b, y) for a, b, y in directed_edges(papers) if a not in drop and b not in drop]
    names = sorted({x for a, b, _ in de for x in (a, b)})
    idx = {n: i for i, n in enumerate(names)}
    g = undirected(len(names), ((idx[a], idx[b]) for a, b, _ in de))
    g.vs["name"] = names
    return g

def survival(base_names, base_memb, new_names, new_memb, min_size=30):
    """what fraction of each baseline community lands together afterwards"""
    nm = {n: c for n, c in zip(new_names, new_memb)}
    out = []
    for c in np.unique(base_memb):
        mem = [n for n, m in zip(base_names, base_memb) if m == c]
        if len(mem) < min_size:
            continue
        dest = [nm[n] for n in mem if n in nm]
        if not dest:
            out.append((c, len(mem), 0.0)); continue
        _, cnt = np.unique(dest, return_counts=True)
        out.append((c, len(mem), cnt.max() / len(mem)))
    return out

def main():
    papers = load_papers(CORE, "core")
    g0 = build(papers)
    p0 = partition(g0)
    n0 = g0.vs["name"]; m0 = np.array(p0.membership)
    big0 = sum(1 for c in np.bincount(m0) if c >= 30)
    print(f"baseline: {g0.vcount():,} papers, {g0.ecount():,} edges, "
          f"Q={p0.modularity:.4f}, {big0} communities >=30\n")

    def text(d):
        return f"{d.get('title') or ''} {d.get('abstract') or ''}"
    homonym = {b for b, d in papers.items()
               if HOMONYM.search(text(d)) and not ASTRO.search(text(d))}
    kwonly  = {b for b, d in papers.items() if not GRB.search(text(d))}
    norefs  = {b for b, d in papers.items() if not (d.get("references") or [])}
    unref   = {b for b, d in papers.items()
               if "REFEREED" not in (d.get("property") or [])}

    rows = []
    for label, drop in [("homonym screen", homonym), ("keyword-only", kwonly),
                        ("no reference list", norefs), ("non-refereed", unref),
                        ("keyword-only + homonym", kwonly | homonym)]:
        g = build(papers, drop)
        p = partition(g)
        nn = g.vs["name"]; mm = np.array(p.membership)
        shared = sorted(set(n0) & set(nn))
        i0 = {n: k for k, n in enumerate(n0)}; i1 = {n: k for k, n in enumerate(nn)}
        a = ari([m0[i0[n]] for n in shared], [mm[i1[n]] for n in shared])
        v = nmi([m0[i0[n]] for n in shared], [mm[i1[n]] for n in shared])
        surv = survival(n0, m0, nn, mm)
        worst = min(surv, key=lambda t: t[2])
        big = sum(1 for c in np.bincount(mm) if c >= 30)
        rows.append(dict(label=label, dropped=len(drop), nodes=g.vcount(),
                         edges=g.ecount(), q=p.modularity, communities=big,
                         ari=a, nmi=v,
                         min_survival=worst[2], min_survival_size=int(worst[1]),
                         all_survive_50=bool(all(t[2] >= 0.5 for t in surv))))
        print(f"{label:<24} drop {len(drop):>5}  {g.vcount():>6,} nodes  "
              f"Q={p.modularity:.4f}  {big:>2} comm  ARI={a:.3f}  NMI={v:.3f}  "
              f"weakest community retains {worst[2]:.0%}")
    Path("data/communities/ablations.json").write_text(json.dumps(
        {"baseline": {"q": p0.modularity, "nodes": g0.vcount(),
                      "edges": g0.ecount(), "communities": big0},
         "ablations": rows}, indent=1))
    print("\nwrote data/communities/ablations.json")

if __name__ == "__main__":
    main()
