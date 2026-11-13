# Revision 3: targeted mechanism and editorial revision

Review baseline: `c08b68b2c68a4b3a86f850eda368430fc8efeb3f` in Draft PR #243. The head was unchanged when this revision began and at the pre-publication check. The title, research line, section order, official CAS files, existing figures and performance estimands are retained.

## Changes applied

| Request | Applied change | Location |
|---|---|---|
| Explain why arithmetic paths must be preserved | Added the captured-operand width counterexample and the distinction between inner arithmetic and outer grouping. Native widths 2/4 match scalar for all 16 descriptors; widths 8/16/32 do not; grouped-four wide executions restore agreement. The dispatch account is limited to the eight profiled 8B descriptors. | Method; Supplement A.5, Table A.1 |
| Show that projection repair and endpoint equality are insufficient | Added the historical Vulkan projection/attention intervention. Corrected the shorthand 99 to 99/128 per speculative layout on the long input, or 198 records in the full 1,920-row audit. Combined repair removes the differences. Attention-off counts are explicitly derived from recorded complete trajectory reversal. | Results; Supplement A.5, Table A.2 |
| Make producer-state dependence concrete | Added the complete eight-input, 48-cell producer/consumer matrix, grouped into three outcome classes against fixed R. Both KV and initial logits change; no KV-only attribution is made. | Supplement A.6, Table A.3 |
| Distinguish experimental contracts | Kept historical RTX, historical Vulkan Llama and historical B570 clean-receiver contracts separate. Scoped the pre-existing physical-microbatch-128 statement to the controlled SmolLM2 append experiment, with its original outer-512 prompt calls. | Supplement A.1 and experiment setup; source index |
| Connect existing performance observations | Connected S3 prefill savings, the at-most-four-row Q8 k=3 verifier, and local opportunity/cost dependence. The application result now explicitly refers to the three A5000 Q8 panels. | Results; Discussion; Conclusion |
| Remove defensive repetition | Replaced “small but measurable” with the exact 1.51% result; explained the opportunity remaining after shared activation quantization; removed unmeasured maintenance/ROI speculation and duplicated caveats. Modern U's result is stated directly, while its different contract and unrun full backend remain clear. Earlier oracle history stays in the supplement. | Results; Discussion; Conclusion; captions |
| Keep the article focused | Replaced redundant explanation rather than introducing another research line. Added three editable mechanism tables instead of new performance plots. Removed repeated development-scenario and cost summaries. | Main remains 13 pages; supplement is 14 pages |

## Sources and interpretation

- Arithmetic width: [frozen report, 371223b](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md). Read the full report and checked all 16 operand descriptors and all 64 retained profiling entries against the original public records. Native width 4 and width 8 share the activation-quantizer entry point but use different reduction organizations. The width-16/32 stream-K fixup occurs in seven of eight profiled classes. The finite complete-output digest comparisons are not a replay of a whole scalar decoder.
- Projection/attention: [frozen report, 10a7056](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/benchmarks/b570_llama_companion_v1/host_execution/RESULTS.md). Read the full report, both complete 1,920-row committed-vector audits, endpoint controls and the reversal record. The audit includes R among its five arms. The attention intervention changes extent, contiguity and dispatch together.
- Producer/consumer: [frozen report, 022babf](https://github.com/leecdiang/HeteroSpec/blob/022babfabb3d1b6f4f2a2830dca04b2654d193f9/benchmarks/b570_producer_consumer_boundary_v1/RESULT.md). Read the protocol, full matrix and state-effects table. All eight inputs and both producers are represented, including the adverse GSM8K result. This historical boundary-zero k=1 contract is distinct from the later C4096 natural multi-turn study.
- Controlled append producer: [frozen report, 62f2e33](https://github.com/leecdiang/HeteroSpec/blob/62f2e3345b25b59268cc2b3c131fd5ed8c7d5f88/platforms/b570_snapshot/benchmarks/tpds_phase1_v1/RESULT.md). The original report and host implementation bind outer calls of up to 512 and physical microbatch 128 for the SmolLM2 append study.

Historical 23-to-2 kernel counts and weak-control service percentages were not brought into the performance argument. The former combines quantization, launches and concatenation changes; neither is the S3 strong-control increment. No recorded comparison is promoted to cross-device or all-input equivalence.

## Independent review and actual verification

Separate reviewers examined arithmetic-path evidence, Vulkan/producer evidence and language. Their findings were cross-checked against the original records by the integrating editor. The integrated-source review found no unresolved scientific contradiction; the 99-vector denominator and the Vulkan producer scope were corrected explicitly. Individual review notes record their own reading scope and must not be mistaken for native reruns or final visual review.

The integrating editor compiled the manuscript, supplement and highlights; rendered and inspected all 13 main and 14 supplement pages; and inspected all three author-note pages and the highlights. Three new tables were checked at final size. Long source filenames and a reference spill page were corrected without altering official margins or fonts. A standard float-only supplement page retains ordinary elastic spacing; no content is cropped or overlapped. The known CAS title-box warning has no visible overflow; the supplement has no overfull warning.

The flat editable source package was separately compiled. Its page text and Poppler-rendered pages match the working-tree PDFs for manuscript, supplement and highlights. All 52 frozen scientific inputs and all 37 existing figure assets are byte-identical to revision 2. New CPU work counts existing public historical records and generates three LaTeX table macros. Existing performance estimates, bootstrap results and plots were not regenerated or changed in this targeted revision.

## Remaining author decisions and scope

Confirm the scientific interpretation of the three historical cases, permissions for the included public record projections, final author/affiliation information, CRediT, funding, interests, acknowledgments, actual historical AI use and final data-deposit/access terms. See `author_notes/DECLARATIONS_TO_CONFIRM.md`. The original private/restricted or pruned native material was not retrieved or replayed; no blanket data-availability promise is made.

The bibliography and policy checks from earlier revisions are preserved; this round does not claim a new full literature or journal-policy search. The complete modern default backend remains unrun. No new model call, native-inference or GPU experiment, merge, release, arXiv update or submission was performed. The stopping point is author review.
