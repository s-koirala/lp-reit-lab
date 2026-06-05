# Audit Trail — research_market-scoping_2026-06-05.md

| Field | Value |
|---|---|
| Artifact | `docs/research_notes/research_market-scoping_2026-06-05.md` |
| Pattern | audit-remediate-loop (parallel-specialist ensemble), 3-round cap |
| Round | 1 (exited after round 1 — no critical, both majors remediated, residual minors dispositioned) |
| Auditors | literature-check, quant-auditor, format-auditor (run in parallel) |
| Date | 2026-06-05 |

## Disposition summary
3 major + several minor findings. All majors remediated in round 1. Substantive
minors remediated; cosmetic minors and release-gate items logged as residual.

| ID | Auditor | Severity | Issue (abridged) | Disposition |
|---|---|---|---|---|
| LIT-1 | literature-check | major | §3 FHAA-1988 link pointed to the HUD/DOJ Reasonable-Accommodations Joint Statement, not the statute (claim true, citation wrong) | **Fixed** — repointed to Pub. L. 100-430 / H.R.1158 (congress.gov) |
| QNT-F1-1 | quant-auditor | major | "HC3 robust SEs, clustered by submarket" conflates two mutually-exclusive estimators | **Fixed** — changed to cluster-robust SEs (CR3 / wild-cluster bootstrap, Cameron-Gelbach-Miller 2008); added VIF/condition-index collinearity screen |
| QNT-F1-2 | quant-auditor | major | "Conley-HAC keeps OLS estimates" only valid for SEM; under a SAR lag OLS is biased/inconsistent | **Fixed** — sequence robust LM-lag vs LM-error (Anselin-Bera-Florax-Yoon 1996) first; Conley only if SEM dominates; SAR/SDM required if lag dominates |
| QNT-F1-3 | quant-auditor | minor | "3-stage WLS" loosely attributed to BMN | **Fixed** — disambiguated BMN (OLS base) vs Case-Shiller (3-stage WLS) vs Calhoun/FHFA (geometric weighting) |
| QNT-F1-4 | quant-auditor | minor | Assumption-verification protocol not enumerated (collinearity, renovation filter, clustered Cox) | **Fixed** — added VIF screen, building-permit-join renovation filter (`ydr8-5enu`), PIN-clustered Cox SEs |
| QNT-F1-5 / FMT | quant-auditor / format | minor | rate↔exit-cap correlation 0.6–0.8 hard-coded (magic number) | **Fixed** — relabeled as placeholder to be estimated empirically (UST vs transaction-cap), reported with CI |
| QNT-F1-6 | quant-auditor | minor | Cross-refs to `docs/audits/` and ADR-0002 not yet existing | **Fixed/Resolving** — this trail created; ADR-0002 written in Phase E; status line updated |
| QNT-F1-7 / FMT | quant-auditor / format | minor | Break-even occupancy labeling ambiguous / unqualified | **Fixed** — labeled as ratio = (OpEx + DS)/GPR, property-specific screen |
| FMT-cap | format-auditor | minor | Cap-rate-spread 2–4% lacked inline cite | **Fixed** — Wall Street Prep cited inline |
| FMT-links | format-auditor | minor | §6 DOI linking inconsistent (some linked, some not) | **Accepted/Residual** — literature-check verified all cites canonical; full bibliography (pages/ISBNs/DOIs) to be mirrored into CITATION.cff via /cite-add |
| FMT-cff | format-auditor | minor (release gate) | CITATION.cff retains `<<TODO>>` body fields | **Residual** — intentional template; must be filled before any tagged Zenodo release (release gate, not this round) |
| LIT-2 | literature-check | minor | Inline book cites lack page spans / ISBNs | **Residual** — to be closed when CITATION.cff is populated |

## Residual risk
- This is a **scoping** memo; the implementing code operationalizes the
  verification protocols (SE-estimator choice, SAR/SEM decision sequence,
  renovation filter, clustered Cox, empirical rate↔cap correlation). Method
  fidelity is confirmable only once those models are fit on real data
  (out of scope for v0, which is deterministic finance on synthetic data).
- CITATION.cff placeholder fields are a **release gate** — fill before tagging.
- All current-market figures (§5) remain provisional pending programmatic re-pull.

## Verification (round-1 exit check)
No critical findings; both majors and all substantive minors remediated in-round.
Remaining items are cosmetic or release-gated. Loop exits at round 1 per the
exit rule (only minor/residual remain).
