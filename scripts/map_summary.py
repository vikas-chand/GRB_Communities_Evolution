"""Print the map: the fourteen communities with size, span, and reading."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / "data/communities"


def main() -> None:
    canon = json.loads((COM / "canonical_consensus.json").read_text())
    census = json.loads((COM / "role_census.json").read_text())["displayed_stable"]
    comms = sorted((c for c in canon["communities"] if c["id"] <= 13), key=lambda c: -len(c["members"]))
    print(f"THE GRB CITATION MAP — {sum(len(c['members']) for c in comms):,} papers in 14 communities  (Q = {canon['q']:.4f})")
    for c in comms:
        print(f"  C{c['id']:<3}{len(c['members']):>6}  {', '.join(c['terms'][:4])}")
    print(f"roles (stable cores): {census['two_class_connector']} connector hubs · "
          f"{census['two_class_provincial']} provincial hubs · {census['peripheral']:,} peripheral")


if __name__ == "__main__":
    main()
