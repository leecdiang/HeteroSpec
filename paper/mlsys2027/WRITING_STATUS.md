# MLSys 2027 writing status

Status date: 2026-09-18.

Legend:
- READY — evidence is sufficiently closed to draft now.
- PROVISIONAL — draftable, but wording/numbers depend on pending 358H merge/closeout.
- HOLD — do not freeze until pending evidence closes.

| Section | Status | Notes |
|---|---|---|
| Introduction | READY | Frame around correctness-constrained profitability, not "heterogeneous always helps". |
| Background: speculative decoding | READY | Algorithmic explanation is stable. |
| Cost / break-even model | READY | Use tracked verification-amortization framework. |
| Correctness contract | READY | Token-ID equality, generated tokens only. |
| Methodology: M4 | READY | Closed platform. |
| Methodology: RTX 5070 Ti Laptop | READY | Closed platform; preserve Laptop designation. |
| Methodology: B570 | READY | Closed platform. |
| Methodology: 358H | PROVISIONAL | Environment + Phase-1/2/runner design can be drafted from experiment branch; Phase 3 still pending. |
| M4 results | READY | Include representative negative + code-conditioned positive. |
| RTX results | READY | Include raw-vs-exact verification distinction. |
| B570 results | READY | Keep diagnostic/correctness-admissible distinction. |
| 358H results | HOLD | Formal Phase 3 not started at audited branch head. |
| Cross-platform final table | HOLD | Wait for 358H. |
| Discussion | PROVISIONAL | Main mechanism is stable; 358H may strengthen or redirect system-overhead argument. |
| Related work | READY | Requires literature pass but does not depend on 358H outcome. |
| Limitations | READY/PROVISIONAL | Existing limitations are stable; add final 358H limitations later. |
| Abstract | HOLD | Write after headline result ordering is final. |
| Conclusion | HOLD | Wait for Phase 3. |
| Appendix | PROVISIONAL | Can be assembled incrementally. |

## Internal evidence discipline

For every table/figure intended for the paper, maintain:
- source report / analysis file;
- source commit;
- exact aggregation script;
- whether the result is primary, secondary, diagnostic, or post-hoc descriptive;
- correctness status;
- energy sensor boundary if applicable.

Do not copy a number from chat history into the manuscript without checking the tracked source.
