# Reproduction

## Environment

Python 3.12 with the pinned graph stack:

    pip install -r requirements.txt

The analysis was produced with python-igraph 1.0.0, leidenalg 0.12.0,
NumPy 2.4.3, SciPy 1.17.1, scikit-learn 1.8.0 on macOS. Determinism holds on
this stack; igraph/leidenalg are pinned because their internal RNGs are not
guaranteed stable across versions.

Everything runs from the repository root with

    export PYTHONPATH=scripts

because the scripts import each other by bare module name.

## Step 0 — rebuild the corpus

The frozen corpus is not redistributed (ADS terms; see [Data](data.md)).
Rebuild it:

    export ADS_API_TOKEN=...     # your ADS token
    python scripts/fetch_corpus.py probe
    python scripts/fetch_corpus.py plan
    python scripts/fetch_corpus.py core
    python scripts/fetch_corpus.py targets
    python scripts/fetch_corpus.py cited
    python scripts/fetch_corpus.py merge

writes `data/raw/ads_corpus_v2.jsonl`; the core-tier freeze used by every
script is the core-tier subset. Verify membership against
`data/raw/core_bibcodes.tsv.gz` — ADS evolves, and the manifests define the
analysed set. The arXiv metadata cache regenerates with
`python scripts/fetch_arxiv_meta.py` (rate-limited, ~10 min).

## Run order and cost

Wall-clock on a 16-core laptop; every script prints its own progress.

| Stage | Command | Time |
|---|---|---|
| Canonical partition | `canonical_consensus.py` | ~6 min |
| Stability | `stability_sweep.py`, `consensus.py`, `tau_R_sensitivity.py`, `boundary_entropy.py` | ~1.5 h total |
| Nulls | `dcm_null.py` (ΔT=1, ΔT=2), `temporal_modularity.py` | ~1.5 h |
| Representations | `representation_check.py`, `representation_three.py`, `canonical_directed.py` | ~1 h |
| Corpus robustness | `ablation_controls2.py`, `darkmatter_control2.py` | ~1 h |
| Roles | `paper_roles.py`, `roles_extend.py`, `pagerank_null.py` | ~20 min |
| Evolution | `lineages.py`, `community_lifecycles.py` | ~10 min |
| Structure extras | `subcommunities.py`, `gamma_sweep.py`, `instrument_spread.py`, `algorithm_comparison2.py`, `validate_labels_arxiv.py`, `misc_products.py`, `concept_spread.py`, `concept_roles.py`, `corpus_meta.py` | ~45 min |
| Tables, figures, paper | `make_consensus_table.py`, `make_subcommunity_table.py`, `fig_*.py`, then `pdflatex` ×3 in `paper/` | ~10 min |

The single test file guards the identity the whole pipeline leans on:

    python -m pytest tests/test_weighted_modularity.py

(weighted modularity on the collapsed graph equals modularity on the literal
multigraph — the invariant whose silent violation an audit once caught).

## Determinism

Every stochastic step takes explicit seeds, written in the scripts; there is
no unseeded randomness (`Date.now`-style entropy, hash-order iteration, and
unseeded library RNGs were all eliminated — some of them the hard way, see
[Validation](validation.md)). Cold reruns on the pinned stack reproduce
products byte-identically; three independent audit rounds confirmed this on
dozens of products.

## Superseded producers

`ablations.py`, `ablations2.py`, `ablation_controls.py`,
`darkmatter_control.py`, `canonical_partition.py`, `modularity_null_v2.py`,
`algorithm_comparison.py`, `community_evolution.py`, and
`make_profiles_appendix.py` are earlier designs kept
because the audit reports reference them by hash. Do not quote their outputs;
the [product catalogue](products.md) marks their replacements. The
installed `paper/appendix_profiles.tex` is hand-authored and
authoritative; do not regenerate it from the superseded generator.
