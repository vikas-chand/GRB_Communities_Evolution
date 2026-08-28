# Extraction benchmark, pre-annotation round — 2026-08-24

120 items, stratified 6 entity types x 4 eras, judged against their source
abstracts by two machine annotators with opposed lenses (strict literalist,
domain reader), disagreements adjudicated by a third. 95/120 lens-agreement.
This is PRE-annotation: Vikas adjudicates before any number becomes a result.
Machine-judging-machine caveat applies, with one asymmetry worth noting: the
verdicts run AGAINST the extractor, which is the direction correlated bias
would not produce, and the decisive cases were verified by hand.

## The finding

Extraction fidelity splits cleanly by entity type:

| type | clean | drifted | unsupported | wrong type |
|---|---|---|---|---|
| claims         | 90% | 0%  | 5%  | 5%  |
| methods        | 85% | 10% | 0%  | 5%  |
| results        | 85% | 5%  | 10% | 0%  |
| assumptions    | 40% | 20% | 20% | 20% |
| speculations   | 30% | 25% | 35% | 10% |
| open_questions | 15% | 15% | 55% | 15% |

(n = 20 per row; a 55% cell carries a 95% interval of roughly 34-74%.)

The factual layers (claims, methods, results) are extractive and reliable.
The interpretive layers are partly GENERATIVE: the model wrote plausible
questions and speculations rather than extracting stated ones. Hand-verified
examples:

- 1992ApJ...391L..63B: extracted question invokes FRB lensing searches.
  FRBs were discovered in 2007. Training-knowledge injection, anachronistic
  by fifteen years.
- 1995PASP..107.1145F: abstract says "all proposed models must be considered
  speculative"; extraction names neutron stars, black holes and exotic
  objects, none of which appear.
- 2011MNRAS.413.2173G: extracted host-metallicity question; metallicity never
  mentioned.

No era gradient: clean rate is 50-60% in every era, so the failure is a
property of the entity type, not of old abstracts.

Assumptions are a definitional problem rather than a fabrication problem:
the extractor records the implicit assumption a method entails (using a 2D
model entails assuming 2D adequacy). The strict lens calls that drift, the
reader lens calls it supported, and the adjudicator split case by case. The
benchmark instructions must decide whether implicit assumptions are in scope
before precision can be defined for that type.

## Consequences, pending human adjudication

1. Any analysis built on open_questions or speculations inherits a ~50%
   fabrication rate and cannot be interpreted until re-extraction or
   filtering. The 36,551 extracted open questions are textually distinct but
   distinctness is not fidelity.
2. Claims, methods and results layers are usable with disclosed error.
3. Re-extraction of the two generative types needs a prompt that forbids
   inference beyond the text, plus a post-hoc entailment filter.

## Files

- sample_v1.json          120 items with abstracts
- preannotation_v1.json   both lenses + adjudicated finals
- unsupported_ids.json    the 25 items to adjudicate first
