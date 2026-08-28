"""The complete probe lexicons as a released, human-readable document.

Imports the three vocabularies directly from concept_spread.py (so this
listing cannot drift from the code that produced the numbers) and joins
each probe with its match counts and concentration from the saved product.
Emits docs/probe_lexicons.md.
"""
from __future__ import annotations
import json, re
from pathlib import Path

import concept_spread as cs

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/probe_lexicons.md"


def section(title, lex, rows):
    by = {r["probe"]: r for r in rows}
    md = [f"## {title} ({len(lex)} probes)", "",
          "| probe | pattern | case | papers linked | concentration |",
          "|---|---|---|---:|---:|"]
    for name in sorted(lex, key=lambda n: -by.get(n, {}).get("n_linked", 0)):
        pat, flag = lex[name]
        r = by.get(name, {})
        md.append(f"| {name} | `{pat}` | {'i' if flag else 's'} | "
                  f"{r.get('n_linked', 0)} | {r.get('concentration', 0):.2f} |")
    return md + [""]


def main() -> None:
    d = json.loads((ROOT / "data/communities/concept_spread.json").read_text())
    md = ["# Probe lexicons of record",
          "",
          "The three fixed vocabularies swept over every title and abstract of",
          "the frozen core corpus by `scripts/concept_spread.py`: declared",
          "regular-expression patterns (case column: `i` = case-insensitive,",
          "`s` = case-sensitive), with guards excluding the known homonyms",
          "(the Vela pulsar, Chandrasekhar, the Planck mass, the Virgo",
          "cluster, Fermi acceleration in the facility sense). Concentration",
          "is the share of a probe's linked papers in its single largest",
          "community. The statistic is per-probe: adding or removing a probe",
          "changes no other probe's number. This file is generated from the",
          "producer's own dictionaries by `scripts/emit_probe_lexicons.py`.",
          ""]
    md += section("Facilities", cs.FACILITIES, d["facilities"])
    md += section("Analysis methods", cs.METHODS, d["methods"])
    md += section("Theoretical concepts", cs.THEORY, d["theory"])
    OUT.write_text("\n".join(md) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
