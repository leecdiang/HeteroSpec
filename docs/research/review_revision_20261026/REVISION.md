# Post-review manuscript revision — 2026-10-26

The manuscript now separates three decisions that the previous narrative blurred: reference qualification, whether drafting pays, and the incremental choice between PQ and QB. The revision follows peer-review, scientific-critical-thinking and academic-paper-reviewer findings, with a separate anti-defensive-writing pass. It adds no GPU measurements and changes no scientific inputs.

## Resolved review points

| Review issue | Revision |
|---|---|
| Validated scope versus deployed use | Section 2 distinguishes backend admission, the validated workload and intended use. Section 8 gives an offline selection rule; the evaluated runtime is not presented as an online correctness detector or recovery mechanism. |
| Main narrative and causal attribution | Main order is qualification → repair-scope economics → QB incremental cost → complete-service deployment → input/backend transfer. PQ's role in crossing draft parity is explicit. |
| Positive deployment choice for SmolLM2 | Target-only batching is stated directly as the favorable qualified choice on the original panel. The unseen-input QB/R ratio above one remains. |
| Deployment evidence hierarchy | The matched Qwen3 k/lifecycle bridge leads the deployment section. Earlier four-input service studies remain as scoped k1 controls; their figure moves intact to Supplement S8. |
| Transfer counterevidence | Llama's CodeContests/108 reference failure and its NOT_RUN timing remain explicit; mapping and state evidence are grouped with transfer. |
| Native rebuild scope | RTX core/frontend reconstruction with pinned numerical DLLs is distinguished from B570's numerical-library and shader rebuild. Same-host fresh-directory replay is identified accurately. |
| External artifact access | REPRODUCTION_ACCESS.md indexes immutable commits and archives, then identifies the remaining RTX DLL/path-relocation and B570 full-request-reference delivery needs. NATIVE_DELIVERY_PROMPT.md specifies packaging existing bytes without new timing. |
| Literature positioning | FlashAttention and FlashAttention-2 are compared directly by their optimization objective; MQ is distinguished from multi-query attention. All 35 prior references remain; bibliography now has 37. |
| Reporting corrections | Mapping figure reads `4/4 fail`; source generator is synchronized. Supplement navigation uses section references through S10. Matched-study intervals identify the nominal family-coverage adjustment. |
| Defensive prose | Repeated disclaimers and imagined objections are removed. Necessary conditions remain where they change interpretation; negative results are retained and stated directly. |

## Validation

- 523 reported-data checks passed.
- 53 analysis and mutation tests passed.
- 12 CPU runtime-contract tests passed; eight archival runtime source identities verified.
- 22 compact follow-up source files remain exact pinned copies.
- PDF compiled successfully: 26 pages, 37 cited bibliography entries, no overfull boxes, missing glyphs, unresolved citations or references.
- All 26 rendered pages inspected; final typography corrections re-inspected on pages 11–12.
- Final independent AI-assisted claim audit: PASS. This is an internal manuscript audit, not external peer review.
- No new native execution, model run or timing campaign in this editorial revision.

See QA_FINAL.json for the final PDF identity and DATA_PRESERVATION.json for the byte-preservation audit.

## Remaining delivery work

The paper can proceed to author review with its current evidence. Completing external native reproduction requires packaging and exposing existing material on the source platforms: RTX's exact numerical DLL acquisition path and relocatable commands, plus B570's full request-reference bytes. The required handoff is included. Additional performance experiments are not required for the present claims.

This revision updates PR145 only. It does not merge the PR or submit the manuscript.
