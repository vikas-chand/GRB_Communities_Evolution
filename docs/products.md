# Product catalogue

Every number the paper quotes lives in one of these files, each written by
the named script. All are JSON unless noted. "Key numbers" are the
manuscript-quoted values as of the release commit.

## The partition

| Product | Producer | Key numbers |
|---|---|---|
| `canonical_consensus.json` | `canonical_consensus.py` | The canonical partition: consensus R=30, τ=0.5, Q=0.4636, 66 groups, 14 with N≥30 covering 13,645/13,800; per-community members, TF-IDF terms, years, f_int |
| `canonical_directed.json` | `canonical_directed.py` | Directed consensus R=30, Q_dir=0.4628; 12/14 canonical communities reproduced at ≥93%; separates the Cygnus X-3 air-shower block |
| `canonical_partition.json` | `canonical_partition.py` | *Superseded*: the single best-of-five run (seed 45) the consensus replaced |
| `subcommunities.json` | `subcommunities.py` | 57 children under the 8 parents ≥500 papers; two independent R=10 consensuses per parent (replicate ARI 0.72–1.00) |

## Stability and robustness

| Product | Producer | Key numbers |
|---|---|---|
| `stability_sweep.json` | `stability_sweep.py` | Single-run ARI 0.669±0.083 (campaign pairwise medians 0.783/0.909/0.929 live in `campaign/campaign_summary.json`) |
| `consensus.json` | `consensus.py` | Best-of-five floor 0.743±0.055; three consensus replicates at R=15 |
| `tau_R_sensitivity.json` | `tau_R_sensitivity.py` | τ∈{0.4..0.7} sensitivity; R=60 vs R=30 ARI 0.971 |
| `boundary_entropy.json` (+`coassign_share.npy`, not shipped: 6.7 MB) | `boundary_entropy.py` | Stable cores 7,562 (54.8%), per-community core fractions, medoid |
| `representation_check.json` | `representation_check.py` | Matched-seed multigraph↔weighted ARI 0.875 vs reseed 0.648/0.669 |
| `representation_three.json` | `representation_three.py` | Directed/simple/multigraph three-way at R=20: A–B 0.854, A–C 0.830, B–C 0.895 |
| `ablation_controls2.json` (+`control_sets/`) | `ablation_controls2.py` | Table 1: five corpus cuts vs 25 effective-vertex-matched deletions each, R=10 |
| `darkmatter_control2.json` | `darkmatter_control2.py` | Dark-matter survival under the keyword cut vs matched controls, R=10 |
| `ablations.json`, `ablations_consensus.json`, `ablation_controls.json`, `darkmatter_control.json` | — | *Superseded* earlier designs, kept for the audit trail |
| `gamma_sweep.json` | `gamma_sweep.py` | Resolution sweep γ∈0.3–3.0: count 12→40, membership vs reseed noise |
| `algorithm_comparison2.json` | `algorithm_comparison2.py` | Campaign Louvain (one-to-one median 76.7%, range 75.8–81.9%) and Infomap (NMI 0.69, 43 communities, nesting purity 0.889) |
| `infomap_subdivision.json` | `infomap_subdivision.py` | Infomap blocks (≥30) nested per canonical community (44 total; five smallest stay single blocks); per-parent NMI/ARI vs our sub-communities (0.62/0.59/0.52/0.49 where Infomap subdivides) |
| `table5_roles.tex` + `docs/roles_table.md` | `make_roles_table.py` | The named-papers table: abridged five-per-category for the manuscript; extended top-25 rankings, exporters/importers, and per-community founders for the repository |
| `infomap_roles_check.json` | `infomap_roles_check.py` | Partition dependence of role coordinates: Spearman 0.887 (P) / 0.859 (z) canonical vs Infomap over 13,800 papers; headline hubs keep their classes |
| `misc_products.json` | `misc_products.py` | Five observed-start Q values and observed-start SD 0.0016; fixed-membership multigraph−simple diff 0.0009; density ratio 86; literal stub-discard 3.1% |

## Nulls

| Product | Producer | Key numbers |
|---|---|---|
| `dcm_null_dT1.json`, `dcm_null_dT2.json` | `dcm_null.py` | Q₅=0.4651 vs Q_null=0.2652±0.0006 (ΔT=1 yr) and 0.2631 (ΔT=2); ΔQ=0.1999; p=1/51 |
| `temporal_modularity.json` | `temporal_modularity.py` | Q_T by layer width; span ratios 1.20–1.28; NMI vs directed L=1 static |
| `pagerank_null.json` | `pagerank_null.py` | Per-paper DCM PageRank percentiles (1,832 above all draws; 319 with kin≥50); community flows vs the ensemble (102/111 below all draws; TGF→BATSE ×2.13) |

## Roles and structure

| Product | Producer | Key numbers |
|---|---|---|
| `paper_roles.json` + `paper_roles_table.csv.gz` | `paper_roles.py`, `roles_extend.py` | The master per-paper table: kin/kout with cohort percentiles, PageRank (global/cohort/within-community), betweenness (directed/undirected/review-pruned), participation (+P_in/P_out, ensemble mean±sd), z, clustering, coreness, stability flags; role censuses |
| `roles_extended.json` | `roles_extend.py` | Exporters/importers by directional participation; per-community founders by local PageRank |
| `instrument_spread.json` | `instrument_spread.py` | Facility spread over communities, linked and all-hit denominators; polarimetry-child POLAR/CZTI counts |
| `concept_spread.json` | `concept_spread.py` | Systematic sweep: 124 facility, 33 method, 43 theory probes (fixed lexicons); per-probe concentration; class summaries (median 0.525/0.355/0.496); per-community max single-facility share |
| `campaign/real{0..4}.json`, `campaign/campaign_summary.json` | `campaign_reseed.py`, `campaign_aggregate.py` | Five predeclared seed schedules over the fragile layer: ablation delta-ARI/rank distributions, fixed-D dark-matter retention, pairwise consensus ARIs, Louvain values; full control ledger under `campaign/control_sets/` |
| `concept_roles.json` | `concept_roles.py` | Median participation per concept (MCMC 0.198 vs spectral lag 0.681, baseline 0.38 over 7,690 stable papers); per-community concept enrichment; elite class composition with all ten bibcodes; asserts roles-table/consensus agreement |
| `corpus_meta.json` | `corpus_meta.py` | Query definition and manifest-derived corpus counts; Figure A interpolates n_core from this product |
| `label_validation_arxiv.json` | `validate_labels_arxiv.py` | arXiv primary-category enrichments per community; NMI 0.132 over 9,719 papers |

## Evolution

| Product | Producer | Key numbers |
|---|---|---|
| `lineages.json` | `lineages.py` | Snapshot partitions (R=10) at 5-yr cuts with sizes and canonical maps; hypergeometric+BH lineage edges; splits/merges/formations/terminations per transition (terminations: one 51-paper 1995 block) |
| `community_lifecycles.json` | `community_lifecycles.py` | New papers/yr and annual citation share per community; supernode PageRank/betweenness/assortativity (−0.26) |
| `evolution.json`, `evolution_v2.json`, `modularity_null*.json`, `direct_res*.json` | — | *Superseded* early-era products, audit trail |

## Dossiers and benchmark

| Product | Producer | Notes |
|---|---|---|
| `dossiers/dossiers.json` + `dossiers/C??.md` | agent workflow (see `audits/`) | Fourteen retrieval-grounded community dossiers; every statement anchored to bibcodes; 51 documented internal disagreements |
| `data/benchmark/sample_v1.json`, `preannotation_v1.json`, `REPORT.md` | agent workflow | The 120-item extraction-fidelity benchmark and its verdicts |

## Figures

`fig_graph_anatomy.py` (corpus anatomy + the community map),
`fig_pipeline.py` (the analysis flowchart; loads all numbers from products),
`fig_role_plane.py` (the z–P plane, 24 labelled works),
`fig_alluvial.py` (the lineage history),
`fig_infomap_nesting.py` (Infomap nesting, Appendix). `fig_subcommunities.py` is retained but unused (the
sub-communities are presented as Table 2). Figures read their quantitative values from products at build time;
query-definition constants live in corpus_meta.json.
