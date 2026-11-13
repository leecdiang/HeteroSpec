# Completed experiment merges — 11 November 2026

The author asked to integrate experiments that were finished but whose pull requests remained Open. This audit fixes the reviewed original heads and records actual outcomes.

## Outcome

- Open PRs before: **71**. Open PRs after: **17**.
- **20 PRs are now merged:** 12 completed result/audit PRs and 8 associated dependencies.
- **34 older PRs were closed after verifying their original heads were already in baseline main.** Those are status reconciliation, not new content merges.
- Baseline: `cfc9edf4582bb3c02885c9171a2ab2635bf19588`.
- Completed-experiment merge tip: `f36c11f5b16b1568d3bce7b914d4167a1c98b6fe`.
- Recovery branch: `audit/pre-experiment-merges-20261111-cfc9edf4`.
- Full original/current heads and dispositions: [RESULT.json](RESULT.json).

## Completed result and audit PRs

| PR | Result | Merge commit |
|---|---|---|
| [#144](https://github.com/leecdiang/HeteroSpec/pull/144) | RTX PR140 closeout: SmolLM2 layout gain, Qwen noise limit, Llama counterexample | `f36c11f5` |
| [#203](https://github.com/leecdiang/HeteroSpec/pull/203) | Linux Ampere results: frozen R qualification and complete six-arm deployment transfer | `16dbdd64` |
| [#204](https://github.com/leecdiang/HeteroSpec/pull/204) | Linux/A5000 M1: packing gains with a small LOCAL increment | `11825f68` |
| [#205](https://github.com/leecdiang/HeteroSpec/pull/205) | Llama Linux/A5000: complete confirmation, cold costs and reproducible results | `0902ebd6` |
| [#206](https://github.com/leecdiang/HeteroSpec/pull/206) | Linux/A5000 14B: complete six-arm transfer results and full costs | `5e1fe266` |
| [#208](https://github.com/leecdiang/HeteroSpec/pull/208) | Linux/A5000 14B D4 factorial: balanced attribution and complete costs | `a5ac12e2` |
| [#209](https://github.com/leecdiang/HeteroSpec/pull/209) | Linux/A5000: qualify real q8; complete M2 pilot and 32B Q4 admission | `1b6a71bb` |
| [#212](https://github.com/leecdiang/HeteroSpec/pull/212) | PR210 Stage A: zero-GPU cost and ownership audit; retain fixture admission gap | `043beff4` |
| [#213](https://github.com/leecdiang/HeteroSpec/pull/213) | RTX: qualify true q8; complete eight-arm panel with k7 13.6–14.6% slower | `6be105f3` |
| [#214](https://github.com/leecdiang/HeteroSpec/pull/214) | PR210 B/C results: true-q8 eligibility and first-use cost; no numerical optimization | `fc8ad824` |
| [#215](https://github.com/leecdiang/HeteroSpec/pull/215) | RTX: qualify natural extent-crossing rollback in37 bounded requests | `5b40f5b4` |
| [#216](https://github.com/leecdiang/HeteroSpec/pull/216) | 32B mixed-Q4 Linux: complete six-arm results, public archive and independent replay | `8eac578e` |

Associated merged dependencies: **#140, #142, #196, #197, #198, #201, #210, #211**. PR142 is the retained S0 engineering closeout; integration does not recast it as a successful model experiment.

Already-integrated PRs closed with explanatory audit notes: **#147, #148, #149, #150, #151, #152, #155, #156, #158, #159, #160, #161, #165, #166, #168, #169, #170, #171, #172, #173, #174, #175, #176, #177, #184, #185, #186, #187, #188, #189, #190, #191, #192, #193**.

## Preservation checks

All original scientific heads remain in history. Ordinary merge commits were used, with no force push or branch deletion.

- **833/833** file references across PR203/204/205/206/208 matched their fixed original blobs. This count includes shared references across PRs; there are 646 unique preserved target paths. The old shared analyzer is retained at [legacy_shared/experiment.py](legacy_shared/experiment.py).
- **1,263/1,263** unique files from the q8/q32 followups, their protocols and the intervening freeze audit matched their original blobs.
- **270/270** files from the historical PR140/142/144 closeout matched their original blob, type and mode.
- All 29 baseline root entries remain. Twenty-six retain identical SHA/type/mode, including `paper`, `platforms`, `src`, `scripts` and `tests`.
- All 88 original benchmark subtrees and all 222 original documentation blobs remain identical. New experiments add new paths.
- The 2,317 original bytes of `.gitattributes` are an exact prefix of its 2,514-byte result: only the 197-byte RTX closeout comment and two byte-preservation rules were appended.

The shared-helper conflict was resolved by retaining PR204's current validation and preserving the older analyzer byte-for-byte. Original replay SHA guards were not weakened. Use the immutable original scientific checkout for historical replay, as explained in [README.md](README.md).

## Remaining Open PRs

These were retained because they are unexecuted plans/candidates, active studies, historical paper work or a manuscript with a failing final QA gate.

| PR | Reason |
|---|---|
| [#157](https://github.com/leecdiang/HeteroSpec/pull/157) | Unexecuted historical repair candidate; later qualified implementations occupy related paths. |
| [#164](https://github.com/leecdiang/HeteroSpec/pull/164) | Historical manuscript and runtime candidate; current runtime/test versions have evolved. |
| [#167](https://github.com/leecdiang/HeteroSpec/pull/167) | Historical review and future experiment planning, without its own completed experiment. |
| [#178](https://github.com/leecdiang/HeteroSpec/pull/178) | Research roadmap, without an executed result panel. |
| [#179](https://github.com/leecdiang/HeteroSpec/pull/179) | Native-contract and recovery prototype; complete GPU qualification remains unfinished. |
| [#180](https://github.com/leecdiang/HeteroSpec/pull/180) | Old backend-loop implementation/compilation study; its GPU numerical and performance qualification is not complete. |
| [#181](https://github.com/leecdiang/HeteroSpec/pull/181) | MMA/DP4A compilation and CPU diagnostics; GPU reference equivalence has not been established. |
| [#182](https://github.com/leecdiang/HeteroSpec/pull/182) | CPU scheduler diagnostic; armed execution still vetoes the unqualified fast path. |
| [#183](https://github.com/leecdiang/HeteroSpec/pull/183) | CPU bridge/protocol remains NOT_READY_FOR_GPU; historical-reference bridge and delivery are incomplete. |
| [#199](https://github.com/leecdiang/HeteroSpec/pull/199) | Independent Q4 design; native/GPU execution has not started in this branch. |
| [#200](https://github.com/leecdiang/HeteroSpec/pull/200) | Natural conversation/append study design; native/GPU execution has not started. |
| [#202](https://github.com/leecdiang/HeteroSpec/pull/202) | CPU/second-GPU placement design; adapter and performance work are unexecuted. |
| [#207](https://github.com/leecdiang/HeteroSpec/pull/207) | Publication figure-strategy research, without a completed experiment or final figure deliverable. |
| [#217](https://github.com/leecdiang/HeteroSpec/pull/217) | Design dependency for the still-active PR218 S3 study. |
| [#218](https://github.com/leecdiang/HeteroSpec/pull/218) | S1/S2/B2 are delivered, but current public S3 records contain qualification/start rather than final results. |
| [#219](https://github.com/leecdiang/HeteroSpec/pull/219) | Eight-GPU research and CPU preflight only; native adapter and distributed reference are not implemented. |
| [#220](https://github.com/leecdiang/HeteroSpec/pull/220) | Working manuscript; source verification and LaTeX compilation pass, but latest PDF content/font QA fails. |

## Review limits

Relevant existing CPU regression suites, public statistical records and source/Git identities were checked. No new GPU experiment ran; private raw captures were not independently regenerated or fully downloaded. An absent GitHub status/check is not a CI pass. Negative results, failures, incomplete cells, exposure limits, freeze deviations and original baseline definitions remain intact. The latest manuscript PR220 and active S3 PR218 were not modified.
