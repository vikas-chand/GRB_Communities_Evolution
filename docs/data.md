# Data

## The corpus

Retrieved from NASA ADS with the exact-phrase query

    (=abs:"gamma-ray burst" OR =abs:"gamma-ray bursts"
     OR =abs:GRB OR =abs:GRBs)
    year:1970-2026 doctype:article

Every element is load-bearing. The `=` operator forces the phrase to be
present (ADS's default handling does not) and disables stemming, which is why
all four surface forms are needed: the plural finds papers the singular
misses, and the bare token admits the multi-messenger literature that writes
"GRB 170817A" without ever spelling the phrase out. The 1970 floor predates the Klebesadel et al. (1973) discovery paper; an
earlier 1965 floor admitted only two keyword-accident records (analysed in
the first corpus freeze, hash 9bf0903d..., retained for the audit trail).

**Core tier**: 15,650 article records (14,346 flagged refereed by ADS).
**Cited tier**: 126,108 records — every paper cited by at least one core
paper. The second tier exists because papers that name a burst leave half the
field's reference structure dangling: with it, reference resolution inside
the corpus rises from 50% to 100%. The citation *graph* that is partitioned
uses core-to-core arcs only; the cited tier is context and future work.

## What ships in this repository and what does not

ADS terms do not permit bulk redistribution of abstracts, so the frozen
corpus files (`ads_corpus_v2.jsonl`, `ads_corpus_v2_core_frozen.jsonl`) are
**not** in the repository. What ships instead:

- `data/raw/core_bibcodes.tsv.gz` — all 15,650 core bibcodes with years;
- `data/raw/cited_bibcodes.tsv.gz` — all 126,108 cited-tier bibcodes;
- `data/raw/arxiv_primary_categories.tsv.gz` — arXiv id and primary category
  for the 9,816 core papers with arXiv identifiers (the full metadata cache
  is likewise not redistributed);
- `scripts/fetch_corpus.py` — rebuilds the frozen corpus from ADS given an
  API token (`ADS_API_TOKEN`), shardable across collaborators.

The frozen core corpus this analysis used has SHA-256
`16b1e0306802843f4c0dfff678fb44f76b4d223ee69d955e45c91c67275eaddc`. A rebuild
today will differ slightly (ADS grows and corrects records); the manifests
define the exact membership this paper analysed.

## Provenance caveats you should know

- The ADS `abs:` field spans title, abstract, **and keywords**. The keyword
  channel is not stationary in time (NASA STI indexing of astronomy stopped
  in the mid-1990s), and the matched-deletion analysis shows it is the one
  corpus channel that does structural work: it alone holds the dark-matter
  community together.
- 1,850 core papers never enter the citation graph; 72% of those lack an ADS
  reference list — a metadata artefact, not a scientific one. The 128 papers
  outside the giant component are the opposite: recent, well-documented, and
  disconnected because their references point outside the core.
- Reciprocal citation is real and contemporaneous here: 1,529 mutual pairs,
  94.8% within one year, essentially no errata/comment artefacts.

## The extraction benchmark

`data/benchmark/` holds a 120-item stratified sample (6 entity types × 4
eras) testing how faithfully machine-extracted statements reflect their
source abstracts, doubly annotated under opposed lenses with adjudication.
Headline: claims/methods/results extract at 85–90% fidelity; speculations and
open questions are ~50% fabricated and are excluded from every evidentiary
use in this project (the community dossiers cite only the validated layers).
