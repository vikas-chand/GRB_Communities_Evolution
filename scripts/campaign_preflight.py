"""Input-bundle preflight for campaign replay.

Verifies, without touching the frozen driver, that the repository's runtime
inputs are the unified-campaign bundle: the 1970-floor corpus, the v3
canonical consensus, and the 125 v3 base control sets. Fails loudly on any
mismatch. Run before any campaign replay or extension.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECT = {
    "data/raw/ads_corpus_v2_core_frozen.jsonl":
        "16b1e0306802843f4c0dfff678fb44f76b4d223ee69d955e45c91c67275eaddc",
    "data/communities/canonical_consensus.json":
        "9f3911f092bf651950ceec863f0e33a89f47b94d915c04f49766411a5f8ffd7c",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    for rel, want in EXPECT.items():
        got = sha(ROOT / rel)
        assert got == want, f"{rel}: {got[:16]} != expected {want[:16]}"
    base = ROOT / "data/communities/control_sets"
    camp = ROOT / "data/communities/campaign/control_sets"
    n = 0
    for i in range(5):
        for k in range(25):
            b = base / f"cut{i}_k{k}.json"
            c = camp / f"j0_cut{i}_k{k}.json"
            assert b.exists(), f"missing base control {b.name}"
            assert b.read_bytes() == c.read_bytes(), \
                f"base control {b.name} != campaign j0 copy"
            n += 1
    print(f"preflight OK: corpus + canonical hashes match; "
          f"{n} base control sets equal the campaign j=0 ledger")


if __name__ == "__main__":
    main()
