"""Table of sub-communities, one level below the canonical fourteen.

Same style as the communities table: N, median year, distinctive terms, and a
reading of ours. Terms are TF-IDF within the parent, so each child is described
by what distinguishes it from its siblings.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper"

PARENT = {0: "BATSE-era distance scale", 1: "afterglows",
          2: "compact mergers", 3: "prompt emission",
          4: "high-energy and neutrinos", 5: "collapsars and supernovae",
          6: "host galaxies", 7: "cosmology"}

READING = {
 (0,0): "distance-scale statistics", (0,1): "cyclotron and annihilation lines",
 (0,2): "counterpart searches", (0,3): "magnetars and giant flares",
 (0,4): "pre-BATSE observations", (0,5): "duration classes",
 (0,6): "gravitational lensing of bursts", (0,7): "solar-flare comparisons",
 (0,8): "primordial black holes",
 (1,0): "broadband afterglow modelling", (1,1): "Swift X-ray flares, plateaus",
 (1,2): "reverse shocks, early optical", (1,3): "radio calorimetry, blast waves",
 (1,4): "X-ray line searches", (1,5): "jet geometry, orphan afterglows",
 (1,6): "robotic follow-up networks", (1,7): "late optical light curves",
 (2,0): "GW170817 and merger afterglows", (2,1): "compact-object masses, remnants",
 (2,2): "short-burst hosts, offsets", (2,3): "duration classification revisited",
 (2,4): "magnetar remnants, plateaus", (2,5): "GW counterpart searches",
 (2,6): "fast radio bursts", (2,7): "GW speed, modified gravity",
 (3,0): "pulse structure and lags", (3,1): "photospheric emission",
 (3,2): "prompt polarization", (3,3): "shock microphysics",
 (3,4): "magnetic reconnection models", (3,5): "synchrotron spectra",
 (4,0): "IceCube neutrino searches", (4,1): "Fermi-LAT afterglows",
 (4,2): "EGRET-era GeV emission", (4,3): "TeV afterglows (LHAASO era)",
 (4,4): "ultra-high-energy cosmic rays", (4,5): "TeV afterglow modelling",
 (4,6): "AGILE instrumentation", (4,7): "Cygnus X-3 air-shower era",
 (5,0): "hyperaccretion engines", (5,1): "GRB--SN associations",
 (5,2): "jet-launch simulations", (5,3): "ultra-long bursts, TDE links",
 (5,4): "collapsar GW predictions", (5,5): "shock breakout, llGRBs",
 (5,6): "off-axis and radio SNe", (5,7): "fast X-ray transients (EP era)",
 (6,0): "dust and absorption", (6,1): "high-z bursts, reionization",
 (6,2): "dark bursts, host IDs", (6,3): "host metallicities",
 (6,4): "rates and star formation", (6,5): "progenitor populations",
 (7,0): "spectral-peak correlations", (7,1): "dark-energy constraints",
 (7,2): "Hubble-tension era cosmology", (7,3): "plateau-based standardising",
}

def main():
    sub = json.loads((ROOT / "data/communities/subcommunities.json").read_text())
    rows = []
    for x in sub:
        pid = x["parent"]
        if rows:
            rows[-1] = rows[-1] + "[5pt]"
        rows.append(f" & & \\textbf{{C{pid} {PARENT[pid]}}} "
                    f"({x['parent_size']:,} papers, replicate ARI "
                    f"{x['replicate_ari']:.2f}) & \\\\[1pt]")
        for k, ch in enumerate(x["children"]):
            terms = ", ".join(ch["terms"][:4]).replace("_", "\\_")
            rd = READING[(pid, k)]
            rows.append(f"{ch['size']} & {ch['median_year']:.0f} & "
                        f"{terms} & {rd} \\\\")
    (OUT / "table3_subcommunities.tex").write_text("\n".join(rows) + "\n")
    n = sum(len(x["children"]) for x in sub)
    print(f"wrote table3_subcommunities.tex: {n} children under {len(sub)} parents")

if __name__ == "__main__":
    main()
