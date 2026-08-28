# End-to-end notebooks

Seven notebooks reproduce every product, table, and figure of
"The Structure and Evolution of Gamma-Ray Burst Research" in dependency
order, running the scripts of record in `scripts/` via `%run`.

## Environment and kernel

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install python-igraph leidenalg infomap numpy scipy scikit-learn matplotlib jupyterlab ipykernel
python -m ipykernel install --user --name grb-venv --display-name "Python (grb-venv)"
jupyter lab            # from the repository root
```

Every notebook's first cell locates the repository root (bounded search),
changes into it, and asserts that the running kernel has python-igraph.

## Data

The frozen ADS corpus (`data/raw/*.jsonl`) is **not** in the repository —
ADS terms do not permit bulk redistribution of abstracts. The repository
ships instead:

- `data/graph/core_arcs.tsv.gz` and `core_nodes.tsv.gz` — the 380,361
  core-to-core citation arcs among 13,800 papers, with bibcode, year, first
  author, title, and doctype for every node;
- `data/raw/core_bibcodes.tsv.gz`, `cited_bibcodes.tsv.gz` — the corpus
  manifests, and `arxiv_primary_categories.tsv.gz`;
- every analysis product under `data/communities/` (including the locked
  five-schedule campaign) and `data/communities/arxiv_meta.jsonl`.

With these, every stage that starts from the graph or from saved products
runs. Stages that read abstracts (TF-IDF labelling, the concept sweep,
graph-figure titles) need a corpus; each notebook detects its absence
(`HAVE_CORPUS`) and falls back to the shipped product. To refetch, set
`ADS_API_TOKEN` (the variable `scripts/fetch_corpus.py` reads) and run
Stage 0 with `RUN_FETCH = True`; the result is a new corpus, not the frozen
one.

## Stages

| Notebook | Stage | Behind `RUN_LONG` |
|---|---|---|
| `00_corpus` | frozen-bundle preflight, optional refetch, corpus metadata | — |
| `01_partition` | citation graph, consensus partition (R = 30), the consensus table | consensus runs, sensitivity sweeps |
| `02_validation` | DCM null (`--realisations 50`), seeded algorithm comparison, representation checks, five-schedule campaign, arXiv label check | null draws, campaign, consensus-level representation |
| `03_interior` | 57 sub-communities, the sub-community table, Infomap subdivision and role stability | sub-community consensus |
| `04_roles` | stable cores → roles → full-precision role product and strict census → the roles table | stable cores (100 runs), betweenness, PageRank null |
| `05_evolution` | temporal modularity, evolution, lineages, life cycles, concept spread, probe lexicons | temporal, evolution, lineages |
| `06_figures` | all figures plus the repository-only pipeline diagram | — |

`RUN_LONG = False` (default) verifies the saved products and rebuilds every
cheap product, table, and figure; `RUN_LONG = True` re-derives the expensive
ones (the campaign takes hours). All stochastic stages are seeded; the
campaign seed schedules are fixed in `scripts/campaign_reseed.py`.

## Superseded scripts kept for the audit trail

`ablations.py`, `ablations2.py`, `ablation_controls.py`,
`algorithm_comparison.py`, `darkmatter_control.py`, `darkmatter_control2.py`,
`modularity_null_v2.py`, `canonical_partition.py`,
`make_profiles_appendix.py` (Appendix D is hand-authored),
`fig_subcommunities.py` (figure produced, not included).
