# Community Structure of the Gamma-Ray Burst Citation Network

This documentation describes, end to end, how the analysis behind the paper
works: what was measured, the mathematics of each measurement, why each
methodological choice was made, and how to reproduce every number.

It is written to be read in order, like a course:

1. **[Data](data.md)** — what the corpus is, how it was retrieved, what its
   two tiers mean, and what can and cannot be redistributed.
2. **[Methods](methods.md)** — the mathematics and the logic, from modularity
   to lineages. This is the long chapter, and the one to read slowly.
3. **[Products](products.md)** — a catalogue of every analysis product in
   `data/communities/`, with the script that makes it and the numbers the
   paper quotes from it.
4. **[Reproduction](reproduction.md)** — environment, run order, runtimes,
   and the determinism guarantees.
5. **[Validation](validation.md)** — the three adversarial audit rounds, the
   extraction-fidelity benchmark, and what each round found and fixed. Read
   this to know exactly how far to trust each claim.

## The question

Gamma-ray burst research is fifty years old and holds more than fifteen
thousand papers. The project asks three questions of that literature, using
only who cites whom:

- **What are its communities?** Which papers belong together, discovered by
  an algorithm that knows nothing about astrophysics.
- **What roles do papers play?** Which works are foundational inside one
  community, which ones bridge communities, which are peripheral.
- **How did the structure evolve?** Which communities formed, split, merged,
  kept growing, or stopped recruiting.

## The headline results

Fourteen communities of at least thirty papers, matching subfields a
practitioner would name, at modularity far above a null model that preserves
each paper's citation activity in each year. One level down, fifty-four
sub-communities that read as research programmes. The role plane separates
connector hubs (the collapsar paper, the mission descriptions) from
provincial hubs (the GW170817 discovery papers). The lineage graph shows a
single BATSE-era heritage until 1995, one great diversification after the
first afterglows, and a quarter century of splits and mergers in which no
lineage was ever lost. One community — dark matter — is an artefact of
indexing rather than a subfield, and three independent tests agree on that.

## How to read the trust level of any number

Every number in the paper comes from a JSON or CSV product in
`data/communities/`, produced by a script in `scripts/`, from a frozen corpus
whose SHA-256 is pinned. Three independent audit rounds (in `audits/`)
reproduced the numbers from cold and adversarially attacked the methods; the
reports list what failed and what was repaired. If you want to know how much
to trust a claim, the chain is: manuscript sentence → product → producer →
corpus, and the audit reports tell you whether that chain has been walked by
someone motivated to break it.
