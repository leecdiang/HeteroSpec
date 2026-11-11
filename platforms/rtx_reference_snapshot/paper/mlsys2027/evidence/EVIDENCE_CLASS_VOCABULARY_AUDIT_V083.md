# Evidence-class vocabulary audit — v0.8.3 Phase 3

The active source was searched for `exact`, `equality`, `agreement`, `comparator`, `match`, `text-path`, `direct-ID`, `sequence`, `qualification`, `reference`, `prediction`, and `predictor`. The audit covers `main.tex`, `appendix.tex`, active `sections/`, active `tables/`, Figure 3 source/caption, and generated A4 rows. Older inactive table variants are excluded from the active PDF.

| File | Old phrase or ambiguity | Class | Action | Final phrase |
|---|---|---|---|---|
| `sections/02_framework.tex` | Comparator distinctions spread across text | H/Q/P | Add compact key at first formal distinction | Historical text-path agreement; fresh direct-ID qualification; frozen predictor-to-live complete-ID agreement |
| `tables/01_platforms_v05.tex` | Historical controls called `text-path-qualified` | H | Avoid qualification vocabulary on historical row | Text-path-agreeing controls |
| `sections/03_methodology.tex` | 72 complete predictions could read as qualification | P | Name prediction comparator | Predictor-to-live complete-ID agreement |
| `sections/04_outcomes.tex` | Historical timing and exact-pair wording | H | State timing endpoint once; label M4/RTX pair counts | Recorded text-path agreement / text-path-equal pairs |
| `sections/04_outcomes.tex` | 358H `exact` could be grouped with historical rows | Q | Name captured-ID endpoint | Direct-ID sequence equality, 90/90 each path |
| `sections/05_diagnoses.tex` | Physical proxy adjacent to fresh gate | H/Q | Identify different runs/contexts, then fresh endpoint | Historical target-forward proxy; fresh direct-ID qualification |
| `sections/05_diagnoses.tex` | 72/72 mechanism result adjacent to 60/72 gate | P/Q | Name each comparator separately | Predictor-to-live 72/72; reference-to-live 60/72 BLOCKED |
| `sections/07_runtime_codesign.tex` | Historical M4 and prospective M4 in same section | H/Q | Separate campaign references | Historical M4 text-path; prospective M4 direct-ID sequences |
| `sections/10_conclusion.tex` | B570 72/72 without endpoint label | P | Specify predictor comparison | Predictor-to-live complete-ID agreement |
| `sections/09_limitations.tex` | Historical `equality counts` | H | Name recorded comparator | Historical text-path agreement counts |
| `tables/02_headlines_v05.tex` | `Exact pairs` mixed H/Q evidence | H/Q | Split endpoint and pair columns; label every row | Text-path for M4/RTX/B570; Direct-ID for 358H |
| `tables/04_energy_v05.tex` | B570 `not globally exact` | H | Scope to historical comparator | No workload-global text-path agreement |
| `tables/05_regimes_v05.tex` + generated `05_regimes_v083_rows.tex` | Frozen style table mixed `Exact` labels | H/Q | Generate a row-level endpoint overlay without altering protected source | Text-path on six historical rows; Direct-ID on two 358H rows |
| `tables/06_verification_lookup_v05.tex` | Bare `Exact` status | H | Relabel status and caption | Historical text-path status / Text-path agreement |
| `tables/07_runtime.tex` | `direct-token exact` | Q | Name prospective M4 endpoint | Direct-ID sequence equality |
| `tables/08_direct_id.tex` | Qualification implied by numeric column alone | Q | Add endpoint column and gate caption | Direct-ID pairs / Direct-ID sequences / QUALIFIED or BLOCKED |
| `figures/03_verification.tex` + `presentation_v07/plot.py` | Adjacent panels could imply matched intervention | H/Q | Add visible panel labels and explicit caption boundary | Historical target-forward proxy from different runs/contexts; fresh direct-ID qualification with no matching latency endpoint |
| `appendix.tex` A/B/E/F/I/J | Historical counts, fresh gate, and B570 prediction could blur | H/Q/P | Clarify each in local prose | Text-path agreement; direct-ID qualification; predictor-to-live 72/72 and reference-to-live 60/72 BLOCKED |

## Retained uses of `exact` and related terms

- Frozen macro names such as `\MRepExact` and archived JSON fields are identifiers, not claims about generated-ID evidence. The active PDF labels their historical values as text-path.
- Appendix `exact replay`, `exact candidate`, `exact ties`, and `exact source commit` describe deterministic replay, selection, tie handling, or provenance, not output equality.
- `not proven exact historical upstream identity` concerns source reconstruction, not a decoding comparator.
- The appendix explicitly calls the historical artifact's `exact` field a legacy field label.
- Direct-ID equality in 358H, fresh RTX/B570, and prospective M4 is retained as Q evidence.

## Deferred

CR-03, CR-04, CR-09, CR-10, CR-11, CR-12, CR-14, CR-15, and CR-18 were not revised in this phase. Table 1 hardware scope was not changed.
