# Validation: how these numbers were attacked

Nothing in this project is asked to be trusted on the author's word. Three
adversarial audit rounds — an independent model (GPT-5.6) instructed to
*reproduce every number from cold and try to break every method* — plus an
extraction-fidelity benchmark and an external label check. The full briefs
and unedited reports are in `audits/`. This page is the honest summary.

## The audit protocol

Each round: the state is frozen (SHA-256 of every producer, product, corpus,
and the manuscript), a written brief lists every claim with its producer, and
the auditor recomputes from the frozen inputs in an isolated tree — cold
reruns where affordable, arithmetic reconstruction elsewhere — then attacks
the *methods*: wrong nulls, invalid comparisons, circular definitions,
unlabelled pipelines. Findings are then verified by us at the primitive
before any fix. The auditor has been right about real bugs and wrong about
others; both happened, and the reports record which.

## What each round found (and what that says about the result)

**Round 1 — consensus and ablations** (`CODEX_consensus_20260822.md`,
verdict: do not sign off). Found: a silent library trap (igraph's
`VertexClustering.modularity` ignores edge weights) that had both reported
and *selected* partitions by the wrong objective; an invalid comparison
(cross-graph ablation ARIs judged against a same-graph reseed floor); a
figure drawing 13,648 vertices while claiming 13,801; the canonical
partition attributed to the wrong seed. All repaired; the sampler comparison
was redesigned around matched random deletions; a regression test now pins
the modularity identity.

**Round 2 — the number manifest** (`CODEX_roles_20260823.md`, do not sign
off). Reproduced dozens of products byte-identically, then found: the
matched-control sampler could silently shrink control sets and was
hash-order nondeterministic; 2,812 legacy arXiv identifiers truncated by a
parsing bug (its offline reconstruction of the corrected enrichments matched
ours to rounding — two independent implementations agreeing on the *fix*);
the community-flow conclusion inverted under the proper time-aware baseline;
an unseeded algorithm comparison whose "88.8% agreement" became NMI 0.69 at
finer resolution when seeded on the frozen graph; and a list of manuscript
numbers with no producer, all since produced or removed.

**Round 3 — evolution and print** (`CODEX_evolution_20260824.md`, do not
sign off). Found: the repaired sampler still mismatched the *effective*
deletion for reference-list cuts (controls removed 1,168 graph vertices where
the cut removes 339) — redesigned to match on effective vertices; a census
computed from rounded CSV values; mixed denominators in the instrument
paragraph plus regex false positives (Fermi acceleration, the Virgo
cluster); an appendix generator emitting broken TeX; and — the subtlest —
eight places where a prose-register pass had preserved every numeral while
shifting a claim's *meaning*. All repaired; the build now passes a hard QA
gate (zero TeX errors, no unresolved references, verified in the PDF text).

The pattern across rounds is the project's honest self-portrait: **numbers
that reproduce, reproduce exactly; defects concentrate in the newest layer;
and guards only protect what they measure.** The numeral guard could not
catch meaning drift; the compile-log grep could not catch what only the PDF
shows. Each round added the guard the previous failure implied.

## The extraction benchmark

Machine-extracted statements (claims, methods, results, assumptions,
speculations, open questions) were tested against their source abstracts on
a 120-item stratified sample, doubly annotated under opposed lenses with
adjudication (`data/benchmark/`). Factual layers extract at 85–90% fidelity;
speculations and open questions are ~50% fabricated — including a
training-data anachronism (a 1992 paper given an "open question" about fast
radio bursts, fifteen years before FRBs were discovered). Consequence
enforced throughout: the community dossiers may cite only the validated
layers, and no analysis in the paper rests on the fabrication-prone ones.
The machine pre-annotation awaits human adjudication and is labelled as such.

## External checks

- **arXiv primary categories** (author-assigned, independent of the graph
  and of our labels): ten of fourteen community readings show strong,
  directionally consistent enrichment; the four core high-energy communities
  sit at the corpus rate of astro-ph.HE, which cannot resolve burst physics
  internally.
- **Cross-algorithm**: Louvain 84.3% one-to-one; Infomap, sharing no
  objective with modularity, NMI 0.69 with 91% nesting purity into our
  partition.
- **Cross-representation**: directed, simple, and multigraph partitions of
  the same evidence agree at or above the level either agrees with itself
  under reseeding.

## What remains open, stated plainly

The ascertainment process (how the literature became observable — ADS
coverage, reference-list availability over time) is bounded by the
matched-deletion experiments but not modelled; a masking experiment is the
designed next instrument. The subject-vs-era question in temporal modularity
awaits a subject-displacement test. Reciprocity is measured (1,529
contemporaneous pairs) but not preserved by the null. And review capacity
being unbounded, the freeze recorded in `audits/DECISION_LOG.md` marks where
validation deliberately stopped and use of the map began.

## The realization campaign (2026-08-25/26)

An unplanned two-paper corpus change re-randomised every seeded stream and
flipped two single-draw conclusions, so the fragile layer was re-measured
under five predeclared seed schedules on the frozen corpus
(`notes/CODEX_MULTISEED_20260825.md` fixes the design; two audit rounds and
a closure sign-off lock the numbers). Results: no removal class occupies
the matched-control tail in every schedule (the paper draws no
cut-specific conclusion); the fixed dark-matter set loses 90.9% of its
members to the keyword cut in every schedule while matched controls retain
at least 94.3%; consensus reproducibility is quoted as ten pairwise ARIs
per ensemble size (median 0.929 at R=30); Louvain agreement as five
schedule values (median 76.7%). One control nonconvergence is recorded as
an outcome. Products under `data/communities/campaign/`.
