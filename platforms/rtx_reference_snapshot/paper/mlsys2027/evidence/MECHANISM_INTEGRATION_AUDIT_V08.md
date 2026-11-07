# B570 mechanism integration audit — manuscript v0.8

Base: `00da1d00bd24328826b04db10b481c56fbba4f3e` (merged PR #34). This audit maps new manuscript claims to the closed `benchmarks/b570_mechanism_v08/` study and `artifacts/b570_mechanism_v08/` archive. No new inference, performance, or energy experiment was conducted for paper integration.

## Directly measured / recorded

| Claim | Canonical evidence | Scope |
|---|---|---|
| Harness 90/90 reference reproduction | `HARNESS_QUALIFICATION.json` and report | Target-only reference setup |
| H1 discovery 36/36 | `DISCOVERY_ANALYSIS.json`, `HYPOTHESIS_FREEZE.md` | 12 previously exposed tasks, three repetitions; exploratory |
| Reserved set 24, 72 frozen predictions | `exposure_inventory.json`, `RESERVED_VALIDATION_SET.json`, `PREDICTION_FREEZE.md`, `RESERVED_PREDICTIONS.json` | No known B570 exposure in audited retained scope |
| Predictor-to-live 72/72 complete sequences | `VALIDATION_ANALYSIS.json`, `VALIDATION_REPORT.md` | One model pair, B570 stack, greedy k=2, HumanEval |
| 24/24 classifications; 12/12 divergent-pair indices, four prompts | `VALIDATION_ANALYSIS.json` | Descriptive secondary checks |
| Predicted and actual 60/72 reference equality, BLOCKED | `VALIDATION_ANALYSIS.json` | Reserved qualification; distinct from v0.7 78/90 |
| Chronology and independent validator | `HYPOTHESIS_FREEZE.md`, `PREDICTION_FREEZE.md`, `INDEPENDENT_VALIDATION.json`, `POST_RUN_INPUT_AUDIT.json` | Hypothesis before reserved inference; 72 predictions before live outcomes; 5,681 checks PASS |

The prediction file's recorded SHA-256 is `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`; its commit is `c99aaf2082ffff46741bef6f69dd96b4654d4c08`. The hypothesis freeze is `313069ce5ac10d4d31849f515c912cad29ac7360`. The study's `CLOSEOUT_REPORT.json` and archive manifest retain the full chronological and source identities.

## Controlled inference

Target-only greedy execution at `n_ubatch=1` is **sufficient to reproduce the tested B570 serialized speculative output trajectory** without live drafting. The evidence localizes a sufficient numerical execution path to target partition under the frozen configuration. It does not determine the unique physical cause of each numerical difference.

## Not claimed

- The target partition is the unique root cause, or a particular kernel is responsible.
- Vulkan or Intel B570 is generally defective or nondeterministic.
- The B570 H1 mechanism explains historical CUDA/RTX divergence.
- UB1 is a universal correctness rule or the predictor a production certificate.
- The new qualification retrospectively certifies historical timing or yields a speed/energy effect.

The main paper uses the existing two-panel Figure 3 at publication scale. Section 5 reports the H1 chronology and primary/secondary endpoints in prose; the appendix retains task IDs and exact divergence tokens. This avoids shrinking Figure 3 or confusing historical physical cost with the fresh predictive study.
