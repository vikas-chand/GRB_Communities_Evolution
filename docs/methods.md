# Methods: the mathematics and the logic

This chapter walks through every method in the order the analysis uses them.
Each section gives the quantity, the formula, what it means in words, why
this choice over the alternatives, and where it lives in the code.

---

## 1. The graph

Papers are nodes. A directed arc runs from a citing paper to a cited paper,
taken from ADS reference lists: 380,362 arcs among 13,801 papers of the
15,652-paper core (the rest cite and are cited by nothing inside the core).

For partitioning, direction is collapsed. The subtlety is what to do with the
1,529 **reciprocal pairs** — pairs of papers that cite each other, almost
always published within a year of one another. We keep both arcs as two
parallel edges (a *multigraph*) rather than merging them into one. The reason
is null-model bookkeeping: the null model rewires directed arcs and then
collapses them the same way, so observed and null graphs have identical edge
counts and identical degree sequences. If you simplified one and not the
other, you would be comparing graphs of different sizes.

*Is that choice innocent?* Not entirely — it asserts that mutual citation is
twice the community evidence of one-way citation. Section 9 describes the
test: partitions of the directed, simple, and multigraph representations
agree with each other about as well as one representation agrees with itself
under reseeding, so the choice moves boundary memberships but not the
structure. Code: `citation_communities.py`, `dcm_null.py` (`undirected()`
collapses without simplifying).

---

## 2. Modularity and the Reichardt–Bornholdt objective

Community detection here maximises **modularity**:

    Q = (1/2m) * sum_ij [ A_ij − k_i k_j / (2m) ] δ(c_i, c_j)

In words: for every pair of papers in the same community, count the edge
between them (A_ij) minus the number of edges *expected* between them if the
graph were rewired at random keeping every paper's degree (k_i k_j / 2m).
Q is high when communities contain far more internal edges than degree alone
predicts.

The **Reichardt–Bornholdt configuration objective** generalises this with a
resolution parameter γ multiplying the expectation term. At γ = 1 it *is*
modularity. Larger γ penalises the null term more, so optimal communities get
smaller; smaller γ merges them. We use γ = 1 as the convention and report a
γ sweep (`gamma_sweep.py`): membership within γ ∈ 0.7–2.2 changes about as
much as reseeding does, but the community *count* rises steadily with γ —
so "fourteen communities" is the γ = 1 answer, not a constant of nature. That
honesty matters: modularity has a known resolution limit, and no single γ is
privileged.

**The optimiser** is Leiden (Traag et al. 2019), an improvement on Louvain
that guarantees well-connected communities. It is stochastic: two runs with
different seeds give different partitions.

---

## 3. Why consensus, and how co-association works

The central methodological fact of this project: **one Leiden run is not
reproducible enough to quote.** Ten runs on the identical graph agree
pairwise at ARI 0.634 ± 0.089. Any statement like "paper X is in community Y"
based on one run would change if you reran with a different seed.

**ARI** (adjusted Rand index) measures partition agreement: the fraction of
paper *pairs* on which two partitions agree (same community in both, or
different in both), adjusted so random labelling scores 0 and identity scores
1. **NMI** (normalised mutual information) measures shared information
between partitions. We quote both because ARI is pair-based and sensitive to
large communities, NMI information-based.

**Consensus clustering** (edge-restricted variant of Lancichinetti &
Fortunato 2012) fixes the reproducibility problem:

1. Partition R times with different seeds.
2. For every *existing* edge, compute the fraction of runs in which its two
   endpoints shared a community (the co-association weight).
3. Discard edges with weight below τ = 0.5, keep the rest with their weights.
4. Repartition the reweighted graph. Repeat from step 2 until the partition
   stops changing (it does, within five rounds).

Intuition: an edge inside a real community is inside it in nearly every run,
so its weight stays high; an edge that straddles an ambiguous boundary keeps
getting cut, loses weight, and eventually disappears from the objective. The
fixed point is a partition no single seed determines.

The "edge-restricted" caveat: classic consensus builds the full N×N
co-association matrix, which can join two papers that were never adjacent.
Restricting to existing edges keeps the graph sparse but cannot create such
joins. That is a named limitation, not a hidden one.

Measured effect (all in `stability_sweep.json`): agreement between
independent consensus partitions is 0.825 / 0.825 / 0.849 / 0.898 at
R = 5 / 10 / 20 / 30, against 0.634 for single runs. τ between 0.4 and 0.5
reproduces the canonical partition; τ ≥ 0.6 fragments it. Doubling R = 30 to
R = 60 changes the result by ARI 0.976 — converged. The canonical partition
is consensus at R = 30 (`canonical_consensus.py`): Q = 0.4641, 64 groups, 14
with ≥ 30 papers covering 13,638 of 13,801.

What consensus buys beyond stability: it *resolves structure single runs
merge*. The largest single-run community (2,610 papers) splits almost exactly
in half into prompt emission and high-energy neutrinos; a mixed group
separates into dark matter, biological effects, and terrestrial flashes.

---

## 4. Stable cores and boundary entropy

Even the consensus partition has soft edges. To quantify them
(`boundary_entropy.py`): run 100 independent single partitions with seeds
disjoint from the consensus construction, map each run's communities onto the
canonical labels by plurality overlap, and for each paper record the share of
runs assigning it its own canonical label.

- **Stable core**: papers assigned their canonical community in ≥ 90% of
  runs — 6,820 papers (49.4%).
- **Boundary entropy**: the Shannon entropy of a paper's label distribution
  across runs; high entropy means the paper genuinely sits between
  communities.

The distribution is bimodal and that is a finding: mergers are 90% stable,
the fireshell school 95%, while seven communities have essentially *no*
stable core — they are exactly the ones consensus resolves but single runs
merge into larger neighbours (neutrinos into prompt emission, for example).
Membership-sensitive claims in the paper are restricted to stable-core
papers.

---

## 5. The dynamic configuration model (the null that knows time)

An observed Q means nothing alone: even random graphs have Q well above zero.
The question is always *Q compared to what*.

The **static configuration model** — rewire keeping every node's total
degree — is wrong for citation networks, because it ignores *when* citations
happened. It happily generates arcs from a 1980 paper to a 2020 paper; on
this network the static expectation is that 24.9% of arcs would run forward
in time, against 0.444% observed (metadata quirks). A null that permits
impossible citations is too easy to beat.

The **dynamic configuration model** (Ren et al. 2018) preserves each node's
degree *trajectory*: divide the timeline into layers of ΔT = 1 yr, and within
each layer preserve every paper's in-degree and out-degree increments,
randomising only *which* citing paper reached *which* cited paper inside that
layer. The null therefore reproduces the entire year-by-year citation matrix;
what it destroys is only the *identity* of citation partners given the
opportunity structure.

One adaptation: Ren et al. match stubs randomly and discard collisions
(self-loops, duplicate arcs), which loses ~10⁻⁴ of their sparse network but
~3% of ours (86× denser). We instead repair collisions with within-layer
double-edge swaps, which preserve the degree increments by construction.
Every draw asserts: full degree trajectory preserved, no self-loops, no
duplicate arcs, undirected degree sequence identical to observed.

The test statistic is registered *before* consensus enters: the best
modularity from five Leiden starts, computed identically for the observed
graph (Q₅ = 0.4655) and every null draw. Fifty draws give
Q_null = 0.2653 ± 0.0005, so ΔQ = 0.2002, and no draw approaches the
observed value: empirical one-sided p = 1/51, the floor at this R. We report
ΔQ and empirical p rather than a z-score because the optimiser spread on a
fixed graph (0.0069) is an order of magnitude larger than the null
draw-to-draw spread (0.0005) — the null SD is not a meaningful error bar.
Code: `dcm_null.py`; products `dcm_null_dT1.json`, `dcm_null_dT2.json`,
`misc_products.json`.

---

## 6. Temporal modularity

Static modularity judges a citation against expectations formed from a
paper's whole lifetime; but papers of the same era shared the same available
literature and can cluster for that reason alone. Medo et al. (2019) put the
growing-network null *inside* the objective:

    Q_T = (1/m) * sum_ij [ A_ij − sum_n Δk_out(i,n) Δk_in(j,n) / m_n ] δ(c_i,c_j)

The expectation term is now built layer by layer from the degree increments —
the same bookkeeping as the DCM, but as an objective rather than an ensemble.
An identity worth knowing (we verified it to machine precision):
Q_T = Σ_n (m_n/m) Q_n — temporal modularity is the layer-weighted sum of
per-layer modularities under one shared membership, which is exactly what
leidenalg's multiplex interface optimises.

Result: temporal communities span 26–33% more publication time than static
ones at every layer width tested. The careful reading (and the only one the
statistic supports): the static partition is more time-confined. Whether that
confinement follows era rather than subject would need a subject-displacement
test we have not run. Code: `temporal_modularity.py`.

---

## 7. Paper roles: participation, within-community degree, PageRank

Communities say who belongs together; roles say what each paper does there.

**Participation coefficient** (Guimerà & Amaral 2005):

    P_i = 1 − sum_s (k_is / k_i)²

where k_is is paper i's links into community s. P = 0 means every link stays
home; P → 1 means links spread evenly over many communities. Because it is a
sum over *this partition's* communities, it needs no label matching, so it
can be averaged over an optimiser ensemble — a connector whose status
vanishes under reseeding is not reported as one. The **directional split**
is scientifically the sharpest tool: P_out over the communities a paper
*cites* (import breadth) versus P_in over the communities that *cite it*
(export breadth). Krolik & Pier (1991) is the canonical example: P_in = 0.79,
P_out = 0.13 — consumed everywhere, sourced at home.

**Within-community degree** z_i standardises a paper's internal degree
against its own community's mean and SD. The (z, P) plane with the classic
thresholds (z ≥ 2.5, P ≥ 0.62) separates provincial hubs, connector hubs,
boundary brokers, and peripheral papers. GW170817's discovery papers are the
strongest provincial hubs in the corpus — enormous z, low P: the
multi-messenger literature talks overwhelmingly to itself.

**PageRank** asks whether a paper is cited by papers that are themselves
structurally important (damping 0.85, directed graph). Three variants, three
questions: raw PageRank (historical influence — returns the founding canon);
**cohort percentile** within the publication year (influence for its age —
returns GW170817, GRB 221009A, GRB 190114C); **DCM-null-adjusted** — a
paper's observed PageRank against its distribution over 20 null draws, which
asks who is more influential than their age-and-degree history alone earns
(returns the mission instrument papers and Goodman 1986). High PageRank means
structurally influential, never evidentially validated.

**Betweenness** counts shortest paths through a paper. We compute it directed
and undirected, and again with the 194 review/catalogue-titled papers
removed: the top-fifty ranking changes by one entry, so bridges here are not
review artefacts. Code: `paper_roles.py`, `roles_extend.py`,
`pagerank_null.py`.

---

## 8. Community flows against opportunity

Collapse communities to supernodes and ask which pairs cite each other more
than opportunity predicts. Raw counts are meaningless (big communities cite
everyone); the honest baseline is the same DCM ensemble as the significance
test: observed arcs between communities versus their distribution over 20
time-respecting draws.

The result inverts the naive picture: **100 of 110 displayed flows lie below
every null draw.** Communities suppress cross-traffic — that is what strong
modularity *means*, made concrete. The exceptions are readable history: the
terrestrial-flash community cites the BATSE-era literature (which discovered
its phenomenon) at 2.85× the null; prompt↔neutrino traffic is mildly but
significantly suppressed, consistent with those being genuinely distinct
fields that a single optimiser run wrongly merges.

---

## 9. Robustness: the matched-deletion logic

Two threats: the optimiser (handled by consensus) and the corpus (a
bibliographic query admits work you did not intend). The corpus test has a
subtle trap that took two audit rounds to get right:

- You cannot judge a cut by how far it moves the partition — deleting *any*
  800 papers moves it.
- You cannot compare a cut's ARI to a reseed floor — those are different
  random quantities (two graphs vs one graph).
- The right comparison: remove the suspect class, and separately remove
  **matched random controls** — sets of the same *effective* size (papers
  that are actually graph vertices; deleting a non-vertex is a no-op),
  matched jointly on degree, publication era, and refereed status, never on
  the covariate that defines the cut itself.

With 25 such controls per cut, no class (reference-list-missing, unrefereed,
homonym) moves the partition beyond its controls; the keyword-only channel is
the single directional signal, and at the community level it dissolves
exactly one community — the 94-paper dark-matter group, which also has the
highest self-containment and is the only community where under half the
members mention a burst. Three tests, one artefact. Code:
`ablation_controls2.py`, `darkmatter_control2.py`.

**Self-containment** f_int — the fraction of a community's citation stubs
that terminate inside it — is the cheap unsupervised contamination detector
this project recommends for any literature corpus: off-topic clusters ride
near 1.0 because nothing outside them cites in.

---

## 10. Lineages: splits, merges, and the test behind the alluvial

Cumulative snapshots at five-year cuts, each partitioned by the same
consensus procedure (R = 10). For consecutive snapshots, every community pair
(A at t, B at t+1) gets a **hypergeometric overlap test**: with n papers
existing at time t, of which |B_old| end up in B, the probability that a
random |A|-subset contains at least the observed overlap. Benjamini–Hochberg
step-up over the full family of pairs controls the false discovery rate at
0.05; surviving edges with overlap share ≥ 10% become lineage links.

Events are then read off the link structure: a community with two or more
significant successors *split*; two or more significant predecessors
*merged*; no significant successor would be a *lineage termination* — and
that never happens, at any transition, which is the alluvial figure's
deepest message. Growth (new papers) is bookkept separately from overlap so a
community is never penalised for recruiting.

Persistence is not activity, so life cycles are measured separately
(`community_lifecycles.py`): papers joining per year and the community's
share of each year's citations. Mergers: 132 new papers/yr. Dark matter:
0.4/yr — a fossil: intact lineage, cited, not recruiting.

---

## 11. Labels and their external check

Communities are labelled *after* detection, from class-based TF-IDF over
titles and abstracts (a term scores by frequency in the community weighted
against its document frequency corpus-wide), plus reading central members.
Nothing about physics enters the partition.

The external check uses arXiv primary categories — chosen by authors, so
independent of both the graph and our terms. Ten of fourteen communities show
strong, directionally consistent enrichment (quark stars in nucl-th at 78×
the corpus rate; biological effects in astro-ph.EP at 112×). The four core
high-energy communities cannot be separated by this channel because
astro-ph.HE has no finer resolution — a stated limit, not a failure. Code:
`validate_labels_arxiv.py`.

---

## 12. What the whole design is defending against

Every methodological choice above answers one of four failure modes:

1. **Optimiser noise read as structure** → consensus, stable cores, matched
   optimisation budgets, reseed floors.
2. **Time read as topic** → the DCM, temporal modularity, cohort
   percentiles, era-matched controls.
3. **The corpus creating its own signal** → matched deletions,
   self-containment, the keyword-channel quarantine, the two-tier design.
4. **The analyst fooling themselves** → registered statistics separated from
   membership, every number produced by a script from a frozen corpus, and
   three adversarial audits (see [Validation](validation.md)).
