"""Community detection on the AstroGraph paper citation network.

Builds paper-level graphs directly from data/raw/ads_papers.jsonl (no Neo4j
needed) and partitions them with Leiden. Three graph flavours are supported,
because they answer different questions:

  direct    A--B if A cites B. Carries the field's time arrow.
  coupling  A--B weighted by shared references (bibliographic coupling).
            Links contemporaries who cannot cite each other yet.
  cocite    A--B weighted by how many later papers cite both (co-citation).
            Links older papers that the field reads together.

Communities are characterised post hoc: size, year profile, most-cited and
most-central members, and distinctive terms via class-based TF-IDF (each
community pooled into one document, scored against the rest of the corpus).
Nothing about GRB physics is supplied to the algorithm.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import igraph as ig
import leidenalg as la
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

RAW = Path("data/raw/ads_papers.jsonl")
OUT = Path("data/communities")

# Terms that are in essentially every paper of this corpus carry no signal for
# telling communities apart, so they are removed before the TF-IDF pass.
# MathML/HTML fragments that leak in from ADS abstracts of some publishers.
MARKUP_STOPWORDS = {
    "mrow", "math", "inline-formula", "msub", "msup", "mfrac", "mtext", "mstyle",
    "mspace", "mrow-", "tex-math", "mml", "xmlns", "mathvariant", "displaystyle",
    "annotation", "semantics", "mtable", "mtd", "mtr", "mover", "munder",
}

DOMAIN_STOPWORDS = {
    "grb", "grbs", "gamma", "ray", "rays", "burst", "bursts", "gamma-ray",
    "gamma-rays", "emission", "observed", "observations", "observation",
    "results", "data", "using", "used", "use", "new", "show", "shows", "shown",
    "study", "studies", "present", "presented", "find", "found", "we", "our",
    "also", "may", "can", "however", "thus", "based", "obtained", "analysis",
    "paper", "et", "al", "one", "two", "three", "time", "times", "high", "low",
    "large", "small", "different", "possible", "consistent", "suggest",
    "suggests", "indicate", "indicates", "model", "models", "source", "sources",
}

# Assembled once at import: generic English + markup + domain-ubiquitous terms.
STOPWORDS = frozenset(ENGLISH_STOP_WORDS) | MARKUP_STOPWORDS | DOMAIN_STOPWORDS


# The v2 corpus stores ADS's native field names and types (singular
# `reference`/`citation`/`author`, `title` as a list, `year` as a string).
# Normalising here means every downstream script works on either corpus.
_V2_RENAME = {"reference": "references", "citation": "citations",
              "author": "authors", "keyword": "keywords",
              "identifier": "identifiers"}


def _normalise(d: dict) -> dict:
    for src, dst in _V2_RENAME.items():
        if src in d and dst not in d:
            d[dst] = d.pop(src)
    t = d.get("title")
    if isinstance(t, list):
        d["title"] = t[0] if t else ""
    y = d.get("year")
    if isinstance(y, str):
        d["year"] = int(y) if y.isdigit() else None
    return d


def load_papers(path: Path | None = None, tier: str | None = None) -> dict[str, dict]:
    """Load a corpus JSONL. `tier` restricts to 'core' or 'cited' if present."""
    papers: dict[str, dict] = {}
    with (path or RAW).open() as f:
        for line in f:
            d = _normalise(json.loads(line))
            if tier and d.get("tier") not in (None, tier):
                continue
            papers[d["bibcode"]] = d
    return papers


def direct_edges(papers: dict[str, dict]) -> list[tuple[str, str]]:
    """Undirected edge set from the union of `references` and `citations`."""
    corpus = set(papers)
    edges: set[frozenset[str]] = set()
    for b, d in papers.items():
        for r in d.get("references") or []:
            if r in corpus and r != b:
                edges.add(frozenset((b, r)))
        for c in d.get("citations") or []:
            if c in corpus and c != b:
                edges.add(frozenset((b, c)))
    return [tuple(e) for e in edges]


def coupling_edges(
    papers: dict[str, dict], min_shared: int = 3, hub_cap: int = 400
) -> list[tuple[str, str, int]]:
    """Bibliographic coupling: A--B weighted by shared references.

    References cited by more than `hub_cap` corpus papers are dropped — a
    review or a founding paper that everyone cites couples the whole field
    together and washes out the community structure.
    """
    ref_to_papers: dict[str, list[str]] = defaultdict(list)
    for b, d in papers.items():
        for r in set(d.get("references") or []):
            ref_to_papers[r].append(b)

    pair_counts: Counter[tuple[str, str]] = Counter()
    for r, cited_by in ref_to_papers.items():
        if len(cited_by) < 2 or len(cited_by) > hub_cap:
            continue
        cited_by = sorted(cited_by)
        for i in range(len(cited_by)):
            for j in range(i + 1, len(cited_by)):
                pair_counts[(cited_by[i], cited_by[j])] += 1
    return [(a, b, w) for (a, b), w in pair_counts.items() if w >= min_shared]


def cocite_edges(
    papers: dict[str, dict], min_shared: int = 3, hub_cap: int = 400
) -> list[tuple[str, str, int]]:
    """Co-citation: A--B weighted by the number of corpus papers citing both."""
    pair_counts: Counter[tuple[str, str]] = Counter()
    corpus = set(papers)
    for d in papers.values():
        refs = sorted(r for r in set(d.get("references") or []) if r in corpus)
        if len(refs) < 2 or len(refs) > hub_cap:
            continue
        for i in range(len(refs)):
            for j in range(i + 1, len(refs)):
                pair_counts[(refs[i], refs[j])] += 1
    return [(a, b, w) for (a, b), w in pair_counts.items() if w >= min_shared]


def build_graph(edges, weighted: bool) -> ig.Graph:
    if weighted:
        names = sorted({n for e in edges for n in e[:2]})
        idx = {n: i for i, n in enumerate(names)}
        g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b, _ in edges])
        g.es["weight"] = [w for _, _, w in edges]
    else:
        names = sorted({n for e in edges for n in e})
        idx = {n: i for i, n in enumerate(names)}
        g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b in edges])
    g.vs["name"] = names
    g.simplify(combine_edges="sum" if weighted else "first")
    return g


def partition(g: ig.Graph, resolution: float, seed: int = 42):
    weights = g.es["weight"] if "weight" in g.es.attributes() else None
    return la.find_partition(
        g,
        la.RBConfigurationVertexPartition,
        resolution_parameter=resolution,
        weights=weights,
        n_iterations=-1,
        seed=seed,
    )


TOKEN = re.compile(r"[a-z][a-z\-]{2,}")


def distinctive_terms(
    members: list[str], papers: dict[str, dict], all_df: Counter, n_docs: int, top: int = 12
) -> list[str]:
    """Class-based TF-IDF: term frequency inside the community, damped by how
    common the term is across the whole corpus."""
    tf: Counter[str] = Counter()
    for b in members:
        d = papers[b]
        text = f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()
        for t in TOKEN.findall(text):
            if t not in STOPWORDS and len(t) > 3:
                tf[t] += 1
    total = sum(tf.values()) or 1
    scored = []
    for t, c in tf.items():
        if c < 5:
            continue
        idf = np.log(1 + n_docs / (1 + all_df[t]))
        scored.append((c / total * idf, t))
    scored.sort(reverse=True)
    return [t for _, t in scored[:top]]


def characterise(part, g: ig.Graph, papers: dict[str, dict], min_size: int) -> list[dict]:
    weights = g.es["weight"] if "weight" in g.es.attributes() else None
    pagerank = g.pagerank(weights=weights)
    name = g.vs["name"]

    all_df: Counter[str] = Counter()
    for d in papers.values():
        text = f"{d.get('title') or ''} {d.get('abstract') or ''}".lower()
        for t in set(TOKEN.findall(text)):
            all_df[t] += 1
    n_docs = len(papers)

    comms = []
    for cid, idxs in enumerate(part):
        if len(idxs) < min_size:
            continue
        members = [name[i] for i in idxs]
        years = [papers[b].get("year") for b in members if papers[b].get("year")]
        by_pr = sorted(idxs, key=lambda i: pagerank[i], reverse=True)[:5]
        by_cit = sorted(
            members, key=lambda b: papers[b].get("citation_count") or 0, reverse=True
        )[:5]
        comms.append(
            {
                "id": cid,
                "size": len(members),
                "median_year": float(np.median(years)) if years else None,
                "year_p10": float(np.percentile(years, 10)) if years else None,
                "year_p90": float(np.percentile(years, 90)) if years else None,
                "terms": distinctive_terms(members, papers, all_df, n_docs),
                "top_pagerank": [
                    {
                        "bibcode": name[i],
                        "title": (papers[name[i]].get("title") or "")[:110],
                        "year": papers[name[i]].get("year"),
                    }
                    for i in by_pr
                ],
                "top_cited": [
                    {
                        "bibcode": b,
                        "title": (papers[b].get("title") or "")[:110],
                        "year": papers[b].get("year"),
                        "citations": papers[b].get("citation_count"),
                    }
                    for b in by_cit
                ],
                "members": members,
            }
        )
    comms.sort(key=lambda c: c["size"], reverse=True)
    return comms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", choices=["direct", "coupling", "cocite"], default="direct")
    ap.add_argument("--resolution", type=float, default=1.0)
    ap.add_argument("--min-size", type=int, default=30)
    ap.add_argument("--sweep", action="store_true", help="resolution sweep only")
    ap.add_argument("--raw", type=Path, default=RAW,
                    help="corpus JSONL (e.g. the two-tier filtered file)")
    ap.add_argument("--tag", default="", help="suffix for the output filename")
    ap.add_argument("--tier", default=None, choices=["core", "cited"],
                    help="restrict to one corpus tier")
    args = ap.parse_args()

    papers = load_papers(args.raw, args.tier)
    if args.graph == "direct":
        edges, weighted = direct_edges(papers), False
    elif args.graph == "coupling":
        edges, weighted = coupling_edges(papers), True
    else:
        edges, weighted = cocite_edges(papers), True

    g = build_graph(edges, weighted)
    comps = g.connected_components()
    giant = max(comps.sizes())
    print(f"graph={args.graph}  nodes={g.vcount():,}  edges={g.ecount():,}")
    print(f"components={len(comps)}  giant={giant:,} ({giant/g.vcount():.1%})")

    if args.sweep:
        for res in (0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0):
            p = partition(g, res)
            sizes = sorted((s for s in p.sizes() if s >= args.min_size), reverse=True)
            print(
                f"  res={res:<4} communities={len(p):<5} "
                f">={args.min_size}: {len(sizes):<3} Q={p.modularity:.3f}  "
                f"largest={sizes[:6]}"
            )
        return

    p = partition(g, args.resolution)
    print(f"resolution={args.resolution}  communities={len(p)}  Q={p.modularity:.4f}")
    comms = characterise(p, g, papers, args.min_size)
    covered = sum(c["size"] for c in comms)
    print(f"communities >= {args.min_size} papers: {len(comms)} covering {covered:,} papers "
          f"({covered/g.vcount():.1%} of graph)\n")

    out = OUT / f"{args.graph}_res{args.resolution}{args.tag}.json"
    out.write_text(json.dumps({"graph": args.graph, "resolution": args.resolution,
                               "modularity": p.modularity, "communities": comms}, indent=1))
    for c in comms:
        print(f"C{c['id']:<3} n={c['size']:<5} yr {c['year_p10']:.0f}-{c['year_p90']:.0f} "
              f"(med {c['median_year']:.0f})")
        print(f"     terms: {', '.join(c['terms'])}")
        print(f"     top:   {c['top_pagerank'][0]['title']} ({c['top_pagerank'][0]['year']})")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
