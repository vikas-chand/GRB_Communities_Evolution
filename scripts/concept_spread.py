"""How facilities, analysis methods, and theoretical concepts distribute over
the communities.

Three conversation-independent lexicons are swept over the frozen core corpus
(title + abstract): every GRB-relevant facility class, the standard analysis
and simulation methods, and the field's theoretical frameworks. For each probe
the summary number is its concentration, the share of its linked papers in its
single largest community. The probe sets are fixed in this file, not curated
against the results; collision guards exclude the known homonyms (Vela pulsar,
Chandrasekhar, Planck mass, Virgo cluster, Fermi acceleration in the facility
sense — which reappears deliberately as a theory probe).
"""
from __future__ import annotations
import json, re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data/raw/ads_corpus_v2_core_frozen.jsonl"
OUT = ROOT / "data/communities"

I = re.I

FACILITIES = {
 "Vela": (r"\bVela\b(?!\s+(pulsar|SNR|supernova|X-1|Jr|region|glitch))", 0),
 "Konus": (r"\bKonus\b", I), "IPN": (r"\bIPN\b|interplanetary network", 0),
 "Ginga": (r"\bGinga\b", I), "Granat/PHEBUS": (r"Granat|PHEBUS", I),
 "SMM": (r"\bSMM\b", 0), "PVO": (r"\bPVO\b|Pioneer Venus", 0),
 "CGRO": (r"\bCGRO\b|Compton Gamma[- ]Ray Observatory", 0),
 "BATSE": (r"\bBATSE\b", I), "EGRET": (r"\bEGRET\b", 0),
 "COMPTEL": (r"\bCOMPTEL\b", 0), "OSSE": (r"\bOSSE\b", 0),
 "BeppoSAX": (r"BeppoSAX|Beppo-SAX", I), "HETE": (r"\bHETE\b", 0),
 "Ulysses": (r"\bUlysses\b", I), "RXTE": (r"\bRXTE\b", 0),
 "ASCA": (r"\bASCA\b", 0), "ROSAT": (r"\bROSAT\b", 0),
 "INTEGRAL": (r"\bINTEGRAL\b", 0), "Swift": (r"\bSwift\b", I),
 "Fermi": (r"\bFermi\b(?![ -]?(?:Dirac|acceleration|accelerated|energy|"
           r"energies|gas|surface|momentum|level|sea|motion|coordinates|"
           r"liquid|golden))", I),
 "Fermi-GBM": (r"\bGBM\b", 0), "Fermi-LAT": (r"\bLAT\b", 0),
 "AGILE": (r"\bAGILE\b", 0), "Suzaku": (r"\bSuzaku\b", I),
 "Chandra": (r"\bChandra\b(?!sekhar)", 0), "XMM-Newton": (r"\bXMM\b", 0),
 "NuSTAR": (r"NuSTAR", I), "MAXI": (r"\bMAXI\b", 0),
 "RHESSI": (r"\bRHESSI\b", 0), "NICER": (r"\bNICER\b", 0),
 "Insight-HXMT": (r"\bHXMT\b|Insight[- ]HXMT", 0), "GECAM": (r"\bGECAM\b", 0),
 "SVOM": (r"\bSVOM\b|ECLAIRs", 0), "Einstein Probe": (r"Einstein Probe", I),
 "eROSITA": (r"eROSITA", I), "IXPE": (r"\bIXPE\b", 0),
 "POLAR": (r"\bPOLAR\b", 0), "AstroSat/CZTI": (r"AstroSat|CZTI", I),
 "Hitomi": (r"\bHitomi\b", I),
 "MAGIC": (r"\bMAGIC\b", 0), "H.E.S.S.": (r"H\.E\.S\.S\.", 0),
 "VERITAS": (r"\bVERITAS\b", 0), "Whipple": (r"\bWhipple\b", I),
 "Milagro": (r"\bMilagro\b", I), "HAWC": (r"\bHAWC\b", 0),
 "LHAASO": (r"\bLHAASO\b", I), "CTA": (r"\bCTA\b", 0),
 "ARGO-YBJ": (r"ARGO[- ]YBJ", 0), "Tibet AS": (r"Tibet AS", 0),
 "IceCube": (r"IceCube", I), "AMANDA": (r"\bAMANDA\b", 0),
 "ANTARES": (r"\bANTARES\b", 0), "KM3NeT": (r"KM3NeT", I),
 "Super-K": (r"Super[- ]Kamiokande|\bSuper-K\b", 0),
 "Baikal": (r"\bBaikal\b", I),
 "Pierre Auger": (r"Pierre Auger|\bAuger Observatory\b", 0),
 "Telescope Array": (r"Telescope Array", 0),
 "LIGO/Virgo": (r"\bLIGO\b|\bVirgo\b(?!\s+[Cc]luster)", 0),
 "KAGRA": (r"\bKAGRA\b", 0), "GEO600": (r"GEO ?600", 0),
 "LISA": (r"\bLISA\b", 0), "Einstein Telescope": (r"Einstein Telescope", 0),
 "VLA": (r"\bVLA\b|Very Large Array", 0), "VLBA": (r"\bVLBA\b", 0),
 "EVN": (r"\bEVN\b", 0), "ALMA": (r"\bALMA\b", 0),
 "ATCA": (r"\bATCA\b|Australia Telescope Compact", 0),
 "GMRT": (r"\bu?GMRT\b", 0), "MeerKAT": (r"MeerKAT", I),
 "ASKAP": (r"\bASKAP\b", 0), "LOFAR": (r"\bLOFAR\b", 0),
 "MERLIN": (r"\bMERLIN\b", 0), "WSRT": (r"\bWSRT\b|Westerbork", 0),
 "Effelsberg": (r"Effelsberg", I), "Parkes": (r"\bParkes\b", I),
 "Arecibo": (r"\bArecibo\b", I), "CHIME": (r"\bCHIME\b", 0),
 "FAST (radio)": (r"\bFAST\b", 0), "SKA": (r"\bSKA\b", 0),
 "NOEMA/PdB": (r"\bNOEMA\b|Plateau de Bure", 0), "OVRO": (r"\bOVRO\b", 0),
 "AMI": (r"\bAMI\b", 0), "Ryle": (r"\bRyle\b", 0),
 "HST": (r"\bHST\b|Hubble Space Telescope", 0), "JWST": (r"\bJWST\b", 0),
 "VLT": (r"\bVLT\b", 0), "Keck": (r"\bKeck\b", I),
 "Gemini": (r"\bGemini\b", I), "Subaru": (r"\bSubaru\b", I),
 "GTC": (r"\bGTC\b", 0), "Magellan": (r"\bMagellan\b", I),
 "MMT": (r"\bMMT\b", 0), "LBT": (r"\bLBT\b", 0),
 "WHT": (r"\bWHT\b|William Herschel Telescope", 0),
 "TNG": (r"\bTNG\b", 0), "CFHT": (r"\bCFHT\b", 0),
 "UKIRT": (r"\bUKIRT\b", 0), "Palomar": (r"\bPalomar\b", I),
 "ZTF": (r"\bZTF\b", 0), "Pan-STARRS": (r"Pan-STARRS", I),
 "ATLAS (survey)": (r"\bATLAS\b", 0), "DECam/DES": (r"\bDECam\b|\bDES\b", 0),
 "Rubin/LSST": (r"\bLSST\b|Rubin Observatory", 0),
 "SDSS": (r"\bSDSS\b", 0), "2MASS": (r"\b2MASS\b", 0),
 "GROND": (r"\bGROND\b", 0), "ROTSE": (r"\bROTSE\b", 0),
 "RAPTOR": (r"\bRAPTOR\b", 0), "MASTER": (r"\bMASTER\b", 0),
 "BOOTES": (r"\bBOOTES\b", 0), "TAROT": (r"\bTAROT\b", 0),
 "KAIT": (r"\bKAIT\b", 0), "REM": (r"\bREM\b", 0),
 "Liverpool Telescope": (r"Liverpool Telescope", I),
 "GOTO": (r"\bGOTO\b", 0), "Spitzer": (r"\bSpitzer\b", 0),
 "WISE": (r"\bWISE\b", 0), "Herschel": (r"\bHerschel\b", 0),
 "Gaia": (r"\bGaia\b", 0),
 "Kepler": (r"\bKepler\b(?!'s| SN| supernova)", 0),
 "TESS": (r"\bTESS\b", 0), "Euclid": (r"\bEuclid\b", 0),
 "Planck": (r"\bPlanck\b(?!\s+(mass|scale|constant|time|length|energy|"
            r"units|era|epoch|density))", 0),
}

METHODS = {
 "Bayesian inference": (r"\bBayesian\b", 0),
 "MCMC": (r"\bMCMC\b|Markov [Cc]hain Monte Carlo", 0),
 "Monte Carlo": (r"Monte Carlo", 0),
 "machine learning": (r"machine[- ]learning|machine learning|deep[- ]?learning", I),
 "neural networks": (r"neural network|convolutional|autoencoder|\bCNN\b|\bLSTM\b", I),
 "random forest/SVM": (r"random forest|support vector", I),
 "Gaussian process": (r"Gaussian process", 0),
 "PCA": (r"principal component|\bPCA\b", 0),
 "wavelet": (r"\bwavelet", I),
 "power spectrum/Fourier": (r"power spectr|power[- ]density spectr|\bFourier\b", I),
 "cross-correlation": (r"cross-correlation", I),
 "maximum likelihood": (r"maximum[- ]likelihood", I),
 "KS test": (r"Kolmogorov", 0),
 "bootstrap": (r"\bbootstrap", I),
 "V/Vmax": (r"V/V ?_?\{?max", 0),
 "logN-logS": (r"log ?N[- ]log ?S", I),
 "Band function": (r"Band function|Band model|Band spectrum", 0),
 "XSPEC/spectral fitting": (r"\bXSPEC\b|spectral fit", I),
 "time-resolved spectroscopy": (r"time-resolved spectr", I),
 "photometric redshift": (r"photometric redshift|photo-z", I),
 "stacking": (r"\bstacking\b|stacked analysis", I),
 "matched filter": (r"matched[- ]filter", I),
 "template fitting": (r"template fit", I),
 "population synthesis": (r"population synthesis", I),
 "hydrodynamic simulation": (r"hydrodynamic|hydrodynamical", I),
 "(GR)MHD simulation": (r"\bGRMHD\b|magnetohydrodynamic", I),
 "particle-in-cell": (r"particle-in-cell|\bPIC\b", 0),
 "N-body": (r"\bN-body\b", 0),
 "radiative transfer": (r"radiative transfer", I),
 "VLBI": (r"\bVLBI\b", 0),
 "polarimetry": (r"polarimetr", I),
 "spectral lag": (r"spectral lag", I),
 "variability timescale": (r"minimum variability|variability timescale", I),
}

THEORY = {
 "fireball": (r"\bfireball", I),
 "internal shocks": (r"internal shock", I),
 "external shock": (r"external shock", I),
 "reverse shock": (r"reverse shock", I),
 "synchrotron": (r"synchrotron", I),
 "inverse Compton/SSC": (r"inverse Compton|self-Compton|\bSSC\b", 0),
 "photosphere": (r"photospher", I),
 "compactness/pair production": (r"compactness|pair production", I),
 "Lorentz factor": (r"Lorentz factor", I),
 "jet break": (r"jet break", I),
 "structured jet": (r"structured jet|jet structure", I),
 "cocoon": (r"\bcocoon", I),
 "choked jet": (r"choked jet", I),
 "orphan afterglow": (r"orphan afterglow", I),
 "shock breakout": (r"shock breakout", I),
 "X-ray flares": (r"X-ray flare", I),
 "plateau": (r"\bplateau", I),
 "precursor": (r"\bprecursor", I),
 "extended emission": (r"extended emission", I),
 "magnetar engine": (r"\bmagnetar", I),
 "collapsar": (r"\bcollapsar", I),
 "accretion disk/torus": (r"accretion dis[ck]|accretion torus|hyperaccret", I),
 "fallback": (r"\bfallback", I),
 "Blandford-Znajek": (r"Blandford", 0),
 "Poynting flux": (r"Poynting", 0),
 "baryon loading": (r"baryon load", I),
 "magnetic reconnection": (r"reconnection", I),
 "ICMART": (r"ICMART", 0),
 "turbulence": (r"turbulen", I),
 "Fermi acceleration": (r"Fermi[- ]accelerat|diffusive shock accelerat|"
                        r"first-order Fermi", I),
 "hadronic/photopion": (r"photohadronic|photopion|photomeson|\bhadronic\b", I),
 "kilonova": (r"kilonova|macronova", I),
 "r-process": (r"r-process|rapid neutron capture", I),
 "nucleosynthesis": (r"nucleosynthesis", I),
 "NS equation of state": (r"equation of state", I),
 "quark/strange star": (r"strange quark|quark star|strange star", I),
 "gravitational lensing": (r"gravitational lens|gravitationally lensed", I),
 "standard candle": (r"standard candle", I),
 "Hubble constant": (r"Hubble constant|\bH_?0\b tension", 0),
 "Lorentz invariance": (r"Lorentz invariance|Lorentz violation", I),
 "quantum gravity": (r"quantum gravity", I),
 "axions": (r"\baxion", I),
 "tidal disruption": (r"tidal disruption", I),
}


def main() -> None:
    texts = {}
    with CORPUS.open() as f:
        for line in f:
            d = json.loads(line)
            ti = d.get("title")
            ti = " ".join(ti) if isinstance(ti, list) else (ti or "")
            texts[d["bibcode"]] = f"{ti} {d.get('abstract') or ''}"

    canon = json.loads((OUT / "canonical_consensus.json").read_text())
    memb = {}
    for c in canon["communities"]:
        for b in c["members"]:
            memb[b] = c["id"]

    def sweep(lex):
        rows = []
        for name, (pat, fl) in lex.items():
            rx = re.compile(pat, fl)
            hits = [b for b, t in texts.items() if rx.search(t)]
            linked = [memb[b] for b in hits
                      if b in memb and 0 <= memb[b] <= 13]
            cnt = Counter(linked)
            top = cnt.most_common(4)
            conc = top[0][1] / len(linked) if linked else 0.0
            rows.append(dict(probe=name, n_hits=len(hits),
                             n_linked=len(linked),
                             concentration=round(conc, 3),
                             top=[[int(c), int(n)] for c, n in top]))
        rows.sort(key=lambda r: -r["n_linked"])
        return rows

    comm_n = Counter(c for c in memb.values() if 0 <= c <= 13)
    dominance = {}
    for name, (pat, fl) in FACILITIES.items():
        rx = re.compile(pat, fl)
        cnt = Counter(memb[b] for b, t in texts.items()
                      if rx.search(t) and b in memb and 0 <= memb[b] <= 13)
        for c, n in cnt.items():
            share = n / comm_n[c]
            if share > dominance.get(c, (0.0, ""))[0]:
                dominance[c] = (share, name)
    product = {"facilities": sweep(FACILITIES), "methods": sweep(METHODS),
               "theory": sweep(THEORY),
               "community_facility_dominance": {
                   f"C{c}": dict(facility=nm, share=round(sh, 3))
                   for c, (sh, nm) in sorted(dominance.items())}}
    for cls in ["facilities", "methods", "theory"]:
        rows = product[cls]
        big = [r for r in rows if r["n_linked"] >= 30]
        concs = sorted(r["concentration"] for r in big)
        med = round(statistics.median(concs), 3) if concs else 0
        product[f"{cls}_summary"] = dict(
            n_probes=len(rows), n_over_30=len(big), median_concentration=med,
            max_concentration=max(concs) if concs else 0)
        print(f"{cls}: {len(big)} probes with >=30 linked papers, "
              f"median concentration {med:.2f}, max {max(concs) if concs else 0:.2f}")
    (OUT / "concept_spread.json").write_text(json.dumps(product, indent=1))
    print("wrote", OUT / "concept_spread.json")


if __name__ == "__main__":
    main()
