# ledger.html — number verification, 2026-09-28

Rule: every number on the page re-read from the original evidence file, not from memory notes.
Counts on the page: 31 claims = 20 ledger entries (excl. the method entry) + 11 front-page case files;
held 5 (JADES, geodipole, Masuda, Imatra, LMArena) · overstated 19 (GRB, BAO, H0, Planet Y, 152 GeV,
AGN stacking, coral, DataCite, CWA 18150 + 10 case files) · open 7 (FRB, Fermi 43 GeV, Svensmark,
antibody, Kela, EU AI Act, rongorongo).

| Page claim | Evidence | Status |
|---|---|---|
| GRB QPO 89 / 40 / 4.9 % | ~/grb-qpo-audit/RESULTS.md test G table + fullsel_10000.txt (0.89/0.40/0.049) | OK |
| FRB power 5–7 %, LS p 0.013/0.024 | ~/frb-period-audit/results/round2_out.txt | OK |
| BAO Δχ² 28.5; 46.22 vs 47.54; 33/35 | ~/void-bao-audit/RESULTS.md | OK |
| H0 2.3σ/0σ; doi 10.5281/zenodo.23002508 | ~/h0trend-audit/RESULTS.md; Zenodo API conceptdoi of 23002509 | OK |
| Planet Y 2.62/2.39σ; p 0.20; P 0.03 | ~/planet-y-audit/RESULTS.md | OK |
| 152 GeV 5.4→~4.4σ; ~13 trials | ~/lhc152-audit/RESULTS.md | OK |
| JADES 3.39σ→3.05σ | ~/jades-spin-audit/RESULTS.md | OK |
| Geodipole r 0.72; N_eff 15; p 0.002–0.005 | ~/geodipole-o2-audit/RESULTS.md | OK |
| AGN stacking 1.45σ; N 2004 | ~/stacking-null-audit/RESULTS.md | OK |
| Fermi 43 GeV ρ² 3.7σ | ~/fermi43-audit RESULTS/paper | OK |
| Coral p 0.33/0.42; annual ±0.3 | ~/coral-typhoon-audit/RESULTS.md | OK |
| Masuda N_eff≈80; p≈0.003 | ~/masuda-audit | OK |
| Svensmark +2σ pre-FD excess | ~/svensmark-audit | OK |
| Antibody p 0.005 / 0.56 | ~/lead-research/sable (0.005, 0.557) | OK |
| DataCite 166,283; +543; 600/600 | ~/audits/nrct_era_offset/body.txt | OK |
| CWA 18150 sample size 0, CI 0 | ~/drone-audit/FINDINGS.md | OK |
| Imatra 20.5 % = export level | tools/outreach/ostolasku_audit.py run of 22.9. (62,798 rows) | OK |
| AI Act doi 10.5281/zenodo.22966931 | Zenodo API: conceptdoi of 22966932 | OK (concept) |
| SWE-bench doi 10.5281/zenodo.22541065 | Zenodo API: concept search hit 22839458 | OK (concept) |
| Rongorongo 22825533 + code 22834627 | Zenodo API: both records exist (version DOIs, as submitted to JDMDH) | OK |
| Method doi 10.5281/zenodo.22162050 | Zenodo API: conceptdoi of 22258583 | OK (concept) |
| Proto-Elamite 1,738 / 680 / 468 | ~/script-audit/proto-elamite/RESULTS.md | OK |

Fixed during verification: the hero counters (26/7/12/7 were from memory; recounted from the page → 31/5/19/7).

## Publication pass, 2026-09-28 (user: "julkaise ledger ja etusivu")
- Kela entry HELD (commented out) until 2026-10-06: the 21.9. letter to Kela promised no publication of the
  result before that date. Counters 31/5/19/7 → 30/5/19/6 on ledger.html and index.html; restore on 6.10.
  RESTORED 2026-10-05 (pushed on/after 6.10.). Found on restoring: check_ledger.py counted the commented-out
  entry, so from the Atlas commit (28.9. evening) the live counters read 31/6/19/6 while 30 entries / 5 open
  were visible. The restore makes the counters true without changing them; index.html 30/5/19/6 → 31/6/19/6;
  check_ledger.py now strips comments before counting (sidecar key "benefit series" = [1,0,0,1]).
- Planet Y: the "eleven new objects go against it (P = 0.03)" clause was withdrawn in ~/planet-y-audit/RESULTS.md
  (resonance filter); replaced with a note that it was withdrawn. Tag corrected to MNRAS Letters 543, L27 (2025),
  title to the warp (not "clustering").
- Correspondence: the FRB, BAO and coral lines described the content of private replies; reduced to
  "in correspondence" (no permission recorded). Coral: added the results that held in stage 2
  (~/coral-typhoon-audit/RESULTS.md: ENSO/PDO p 0.002/0.012, multidecadal power p 0.024).
- Lede: "with the test fixed in writing before it runs" overclaimed; the internal ledger found git-verified
  preregistration for only part of the lanes → "Where I could ...". AI use disclosed (policy change 28.9.).
- noindex and draft banner removed.

## Added 2026-09-28 (second pass): the separation-threshold replication
| Page claim | Evidence | Status |
|---|---|---|
| 653 boards; 55.1% of 2.2M below-1x pairs; 90.8% of 7.3M above; 58 inverted; shuffled 50% | ~/shakeup-atlas-audit/results_main.json + results_main.txt; deposit 10.5281/zenodo.23017379 | OK |
Counters 30/5/19/6 -> 31/6/19/6.
