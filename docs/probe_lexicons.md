# Probe lexicons of record

The three fixed vocabularies swept over every title and abstract of
the frozen core corpus by `scripts/concept_spread.py`: declared
regular-expression patterns (case column: `i` = case-insensitive,
`s` = case-sensitive), with guards excluding the known homonyms
(the Vela pulsar, Chandrasekhar, the Planck mass, the Virgo
cluster, Fermi acceleration in the facility sense). Concentration
is the share of a probe's linked papers in its single largest
community. The statistic is per-probe: adding or removing a probe
changes no other probe's number. This file is generated from the
producer's own dictionaries by `scripts/emit_probe_lexicons.py`.

## Facilities (124 probes)

| probe | pattern | case | papers linked | concentration |
|---|---|---|---:|---:|
| Swift | `\bSwift\b` | i | 1897 | 0.30 |
| Fermi | `\bFermi\b(?![ -]?(?:Dirac|acceleration|accelerated|energy|energies|gas|surface|momentum|level|sea|motion|coordinates|liquid|golden))` | i | 1306 | 0.26 |
| BATSE | `\bBATSE\b` | i | 815 | 0.53 |
| Fermi-GBM | `\bGBM\b` | s | 529 | 0.28 |
| LIGO/Virgo | `\bLIGO\b|\bVirgo\b(?!\s+[Cc]luster)` | s | 475 | 0.77 |
| Fermi-LAT | `\bLAT\b` | s | 296 | 0.63 |
| IceCube | `IceCube` | i | 243 | 0.83 |
| CGRO | `\bCGRO\b|Compton Gamma[- ]Ray Observatory` | s | 229 | 0.53 |
| BeppoSAX | `BeppoSAX|Beppo-SAX` | i | 210 | 0.43 |
| INTEGRAL | `\bINTEGRAL\b` | s | 203 | 0.20 |
| HST | `\bHST\b|Hubble Space Telescope` | s | 194 | 0.37 |
| VLT | `\bVLT\b` | s | 179 | 0.63 |
| Chandra | `\bChandra\b(?!sekhar)` | s | 156 | 0.29 |
| Konus | `\bKonus\b` | i | 151 | 0.48 |
| VLA | `\bVLA\b|Very Large Array` | s | 144 | 0.37 |
| XMM-Newton | `\bXMM\b` | s | 133 | 0.35 |
| HETE | `\bHETE\b` | s | 125 | 0.29 |
| Planck | `\bPlanck\b(?!\s+(mass|scale|constant|time|length|energy|units|era|epoch|density))` | s | 120 | 0.28 |
| SVOM | `\bSVOM\b|ECLAIRs` | s | 97 | 0.27 |
| EGRET | `\bEGRET\b` | s | 92 | 0.51 |
| Einstein Probe | `Einstein Probe` | i | 90 | 0.49 |
| MAGIC | `\bMAGIC\b` | s | 90 | 0.69 |
| IPN | `\bIPN\b|interplanetary network` | s | 83 | 0.65 |
| Keck | `\bKeck\b` | i | 79 | 0.46 |
| LHAASO | `\bLHAASO\b` | i | 72 | 0.78 |
| GROND | `\bGROND\b` | s | 71 | 0.48 |
| Telescope Array | `Telescope Array` | s | 69 | 0.56 |
| AGILE | `\bAGILE\b` | s | 68 | 0.72 |
| KAGRA | `\bKAGRA\b` | s | 67 | 0.84 |
| SDSS | `\bSDSS\b` | s | 64 | 0.41 |
| GECAM | `\bGECAM\b` | s | 59 | 0.73 |
| CTA | `\bCTA\b` | s | 57 | 0.56 |
| Rubin/LSST | `\bLSST\b|Rubin Observatory` | s | 55 | 0.62 |
| Granat/PHEBUS | `Granat|PHEBUS` | i | 54 | 0.87 |
| Ulysses | `\bUlysses\b` | i | 53 | 0.77 |
| POLAR | `\bPOLAR\b` | s | 53 | 0.96 |
| Einstein Telescope | `Einstein Telescope` | s | 53 | 0.77 |
| Vela | `\bVela\b(?!\s+(pulsar|SNR|supernova|X-1|Jr|region|glitch))` | s | 50 | 0.76 |
| Ginga | `\bGinga\b` | i | 50 | 0.82 |
| COMPTEL | `\bCOMPTEL\b` | s | 50 | 0.70 |
| Gemini | `\bGemini\b` | i | 50 | 0.34 |
| ALMA | `\bALMA\b` | s | 49 | 0.41 |
| JWST | `\bJWST\b` | s | 48 | 0.50 |
| Insight-HXMT | `\bHXMT\b|Insight[- ]HXMT` | s | 47 | 0.45 |
| Spitzer | `\bSpitzer\b` | s | 45 | 0.76 |
| H.E.S.S. | `H\.E\.S\.S\.` | s | 44 | 0.59 |
| Palomar | `\bPalomar\b` | i | 44 | 0.41 |
| Pierre Auger | `Pierre Auger|\bAuger Observatory\b` | s | 43 | 0.77 |
| PVO | `\bPVO\b|Pioneer Venus` | s | 41 | 0.98 |
| ROSAT | `\bROSAT\b` | s | 41 | 0.63 |
| ATCA | `\bATCA\b|Australia Telescope Compact` | s | 41 | 0.32 |
| MAXI | `\bMAXI\b` | s | 40 | 0.35 |
| RHESSI | `\bRHESSI\b` | s | 40 | 0.42 |
| Subaru | `\bSubaru\b` | i | 40 | 0.45 |
| ROTSE | `\bROTSE\b` | s | 40 | 0.70 |
| Suzaku | `\bSuzaku\b` | i | 38 | 0.34 |
| MASTER | `\bMASTER\b` | s | 38 | 0.84 |
| AstroSat/CZTI | `AstroSat|CZTI` | i | 37 | 0.78 |
| SKA | `\bSKA\b` | s | 36 | 0.25 |
| ANTARES | `\bANTARES\b` | s | 33 | 0.79 |
| Magellan | `\bMagellan\b` | i | 33 | 0.39 |
| SMM | `\bSMM\b` | s | 28 | 0.82 |
| Milagro | `\bMilagro\b` | i | 28 | 0.93 |
| TAROT | `\bTAROT\b` | s | 27 | 0.85 |
| Liverpool Telescope | `Liverpool Telescope` | i | 27 | 0.56 |
| VERITAS | `\bVERITAS\b` | s | 26 | 0.69 |
| KM3NeT | `KM3NeT` | i | 26 | 0.73 |
| TNG | `\bTNG\b` | s | 26 | 0.31 |
| RXTE | `\bRXTE\b` | s | 25 | 0.48 |
| HAWC | `\bHAWC\b` | s | 24 | 0.79 |
| ASCA | `\bASCA\b` | s | 23 | 0.56 |
| AMANDA | `\bAMANDA\b` | s | 23 | 0.91 |
| LISA | `\bLISA\b` | s | 22 | 0.46 |
| ZTF | `\bZTF\b` | s | 22 | 0.55 |
| Pan-STARRS | `Pan-STARRS` | i | 22 | 0.32 |
| REM | `\bREM\b` | s | 22 | 0.82 |
| LOFAR | `\bLOFAR\b` | s | 20 | 0.35 |
| Herschel | `\bHerschel\b` | s | 20 | 0.75 |
| BOOTES | `\bBOOTES\b` | s | 19 | 0.68 |
| Whipple | `\bWhipple\b` | i | 18 | 0.33 |
| CHIME | `\bCHIME\b` | s | 18 | 0.78 |
| GTC | `\bGTC\b` | s | 18 | 0.33 |
| NuSTAR | `NuSTAR` | i | 17 | 0.41 |
| WSRT | `\bWSRT\b|Westerbork` | s | 17 | 0.59 |
| WHT | `\bWHT\b|William Herschel Telescope` | s | 17 | 0.53 |
| MeerKAT | `MeerKAT` | i | 16 | 0.38 |
| ARGO-YBJ | `ARGO[- ]YBJ` | s | 15 | 0.87 |
| GMRT | `\bu?GMRT\b` | s | 13 | 0.39 |
| DECam/DES | `\bDECam\b|\bDES\b` | s | 13 | 0.39 |
| TESS | `\bTESS\b` | s | 13 | 0.46 |
| ASKAP | `\bASKAP\b` | s | 12 | 0.50 |
| Gaia | `\bGaia\b` | s | 12 | 0.42 |
| NICER | `\bNICER\b` | s | 11 | 0.46 |
| MMT | `\bMMT\b` | s | 11 | 0.46 |
| OSSE | `\bOSSE\b` | s | 10 | 0.40 |
| eROSITA | `eROSITA` | i | 10 | 0.30 |
| Baikal | `\bBaikal\b` | i | 10 | 0.70 |
| LBT | `\bLBT\b` | s | 10 | 0.30 |
| RAPTOR | `\bRAPTOR\b` | s | 10 | 0.70 |
| Super-K | `Super[- ]Kamiokande|\bSuper-K\b` | s | 8 | 0.50 |
| Arecibo | `\bArecibo\b` | i | 8 | 0.75 |
| NOEMA/PdB | `\bNOEMA\b|Plateau de Bure` | s | 8 | 0.62 |
| 2MASS | `\b2MASS\b` | s | 8 | 0.25 |
| Kepler | `\bKepler\b(?!'s| SN| supernova)` | s | 8 | 0.38 |
| VLBA | `\bVLBA\b` | s | 7 | 0.43 |
| MERLIN | `\bMERLIN\b` | s | 7 | 0.43 |
| WISE | `\bWISE\b` | s | 7 | 0.57 |
| EVN | `\bEVN\b` | s | 6 | 0.50 |
| Effelsberg | `Effelsberg` | i | 6 | 0.67 |
| FAST (radio) | `\bFAST\b` | s | 6 | 0.50 |
| AMI | `\bAMI\b` | s | 6 | 0.67 |
| KAIT | `\bKAIT\b` | s | 6 | 1.00 |
| Parkes | `\bParkes\b` | i | 5 | 0.80 |
| CFHT | `\bCFHT\b` | s | 5 | 1.00 |
| ATLAS (survey) | `\bATLAS\b` | s | 5 | 0.60 |
| GOTO | `\bGOTO\b` | s | 5 | 0.60 |
| GEO600 | `GEO ?600` | s | 4 | 0.50 |
| UKIRT | `\bUKIRT\b` | s | 4 | 0.50 |
| IXPE | `\bIXPE\b` | s | 3 | 1.00 |
| Euclid | `\bEuclid\b` | s | 3 | 0.33 |
| OVRO | `\bOVRO\b` | s | 2 | 0.50 |
| Tibet AS | `Tibet AS` | s | 1 | 1.00 |
| Ryle | `\bRyle\b` | s | 1 | 1.00 |
| Hitomi | `\bHitomi\b` | i | 0 | 0.00 |

## Analysis methods (33 probes)

| probe | pattern | case | papers linked | concentration |
|---|---|---|---:|---:|
| hydrodynamic simulation | `hydrodynamic|hydrodynamical` | i | 765 | 0.28 |
| Monte Carlo | `Monte Carlo` | s | 476 | 0.20 |
| (GR)MHD simulation | `\bGRMHD\b|magnetohydrodynamic` | i | 306 | 0.36 |
| Bayesian inference | `\bBayesian\b` | s | 200 | 0.24 |
| polarimetry | `polarimetr` | i | 177 | 0.57 |
| time-resolved spectroscopy | `time-resolved spectr` | i | 175 | 0.62 |
| spectral lag | `spectral lag` | i | 155 | 0.42 |
| Band function | `Band function|Band model|Band spectrum` | s | 141 | 0.67 |
| particle-in-cell | `particle-in-cell|\bPIC\b` | s | 129 | 0.88 |
| power spectrum/Fourier | `power spectr|power[- ]density spectr|\bFourier\b` | i | 121 | 0.35 |
| MCMC | `\bMCMC\b|Markov [Cc]hain Monte Carlo` | s | 117 | 0.49 |
| population synthesis | `population synthesis` | i | 113 | 0.50 |
| machine learning | `machine[- ]learning|machine learning|deep[- ]?learning` | i | 99 | 0.37 |
| radiative transfer | `radiative transfer` | i | 89 | 0.34 |
| XSPEC/spectral fitting | `\bXSPEC\b|spectral fit` | i | 85 | 0.33 |
| photometric redshift | `photometric redshift|photo-z` | i | 68 | 0.53 |
| variability timescale | `minimum variability|variability timescale` | i | 61 | 0.34 |
| cross-correlation | `cross-correlation` | i | 60 | 0.25 |
| maximum likelihood | `maximum[- ]likelihood` | i | 54 | 0.30 |
| KS test | `Kolmogorov` | s | 52 | 0.25 |
| VLBI | `\bVLBI\b` | s | 50 | 0.34 |
| neural networks | `neural network|convolutional|autoencoder|\bCNN\b|\bLSTM\b` | i | 46 | 0.26 |
| Gaussian process | `Gaussian process` | s | 32 | 0.66 |
| wavelet | `\bwavelet` | i | 29 | 0.52 |
| stacking | `\bstacking\b|stacked analysis` | i | 29 | 0.66 |
| logN-logS | `log ?N[- ]log ?S` | i | 28 | 0.64 |
| matched filter | `matched[- ]filter` | i | 24 | 0.38 |
| V/Vmax | `V/V ?_?\{?max` | s | 23 | 0.96 |
| N-body | `\bN-body\b` | s | 17 | 0.71 |
| PCA | `principal component|\bPCA\b` | s | 16 | 0.38 |
| random forest/SVM | `random forest|support vector` | i | 15 | 0.33 |
| bootstrap | `\bbootstrap` | i | 10 | 0.60 |
| template fitting | `template fit` | i | 1 | 1.00 |

## Theoretical concepts (43 probes)

| probe | pattern | case | papers linked | concentration |
|---|---|---|---:|---:|
| synchrotron | `synchrotron` | i | 1267 | 0.33 |
| Lorentz factor | `Lorentz factor` | i | 938 | 0.35 |
| fireball | `\bfireball` | i | 774 | 0.42 |
| magnetar engine | `\bmagnetar` | i | 666 | 0.38 |
| kilonova | `kilonova|macronova` | i | 466 | 0.91 |
| accretion disk/torus | `accretion dis[ck]|accretion torus|hyperaccret` | i | 458 | 0.47 |
| photosphere | `photospher` | i | 437 | 0.61 |
| internal shocks | `internal shock` | i | 400 | 0.46 |
| plateau | `\bplateau` | i | 396 | 0.33 |
| inverse Compton/SSC | `inverse Compton|self-Compton|\bSSC\b` | s | 387 | 0.47 |
| collapsar | `\bcollapsar` | i | 382 | 0.50 |
| NS equation of state | `equation of state` | i | 334 | 0.56 |
| reverse shock | `reverse shock` | i | 327 | 0.64 |
| external shock | `external shock` | i | 317 | 0.40 |
| turbulence | `turbulen` | i | 274 | 0.54 |
| structured jet | `structured jet|jet structure` | i | 268 | 0.39 |
| jet break | `jet break` | i | 265 | 0.53 |
| precursor | `\bprecursor` | i | 232 | 0.30 |
| X-ray flares | `X-ray flare` | i | 229 | 0.48 |
| magnetic reconnection | `reconnection` | i | 203 | 0.64 |
| r-process | `r-process|rapid neutron capture` | i | 203 | 0.76 |
| nucleosynthesis | `nucleosynthesis` | i | 202 | 0.41 |
| compactness/pair production | `compactness|pair production` | i | 195 | 0.35 |
| Poynting flux | `Poynting` | s | 195 | 0.49 |
| hadronic/photopion | `photohadronic|photopion|photomeson|\bhadronic\b` | i | 186 | 0.69 |
| Lorentz invariance | `Lorentz invariance|Lorentz violation` | i | 184 | 0.78 |
| cocoon | `\bcocoon` | i | 176 | 0.45 |
| tidal disruption | `tidal disruption` | i | 168 | 0.43 |
| extended emission | `extended emission` | i | 167 | 0.60 |
| Blandford-Znajek | `Blandford` | s | 157 | 0.53 |
| standard candle | `standard candle` | i | 142 | 0.56 |
| gravitational lensing | `gravitational lens|gravitationally lensed` | i | 133 | 0.56 |
| quantum gravity | `quantum gravity` | i | 126 | 0.80 |
| shock breakout | `shock breakout` | i | 106 | 0.60 |
| quark/strange star | `strange quark|quark star|strange star` | i | 104 | 0.49 |
| fallback | `\bfallback` | i | 98 | 0.44 |
| Hubble constant | `Hubble constant|\bH_?0\b tension` | s | 93 | 0.56 |
| baryon loading | `baryon load` | i | 86 | 0.28 |
| Fermi acceleration | `Fermi[- ]accelerat|diffusive shock accelerat|first-order Fermi` | i | 82 | 0.54 |
| axions | `\baxion` | i | 71 | 0.58 |
| orphan afterglow | `orphan afterglow` | i | 63 | 0.59 |
| choked jet | `choked jet` | i | 35 | 0.40 |
| ICMART | `ICMART` | s | 16 | 0.69 |

