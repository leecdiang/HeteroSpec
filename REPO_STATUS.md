# Repository status — v0.8.6 manuscript; RTX V4 evidence merged

Updated 2026-10-02. [Current handover](paper/mlsys2027/HANDOVER_CURRENT.md) is the first-read control file.

## Repository and manuscript identity

- Main contains the unchanged v0.8.6 delivery via PR #46, manuscript integration anchor `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`.
- [PR #48](https://github.com/leecdiang/HeteroSpec/pull/48) preserves terminal V3 history at merge `7f365f4fa87aedcebc2ae4cae5d8071b8223132d`; [PR #49](https://github.com/leecdiang/HeteroSpec/pull/49) integrates complete V4 evidence at `4500d140d78f77d0e314044acab1ae8e68dec42f`. Both merge to main.
- v0.8.6 content/delivery remains `494a5ca4fe62534b032b37d01652c3f88e0d16e1`; TeX source `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`. TeX, PDFs/ZIPs, macros, Figure 3, official styles and old scientific records are unchanged. No v0.8.7 manuscript has been produced by the evidence merge.
- The author-freeze tag remains at `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. Resolve the moving remote main HEAD separately from these fixed integration anchors.

## Closed RTX A+B results

V3 is incomplete: 72 valid A pre-live conditions and one capture failure, zero A live, 54 valid B conditions and one failure. Its full-study accuracy/speedup/CI remain unavailable, not zero or success. V4 uses all 19 remaining exposure-audited tasks after conservative exclusion of 145 tasks, including seven exposed by V3; three repetitions are not independent prompts.

V4 A: 285 conditions. Target-only UB2/live 51/57; H2/live and R_ONLY/live each 57/57; UB1 reference/live 51/57, two reference-divergent prompts. This distinguishes predefined candidates on the finite cohort, without proving history necessity or a unique numerical cause.

V4 B: 171 fresh matched observations. Batched 51/57 BLOCKED, speedup/CI null. Serialized 57/57 QUALIFIED, reference/candidate 0.677351 [0.661653, 0.691812], 0/19 prompts faster. This is instrumented post-prefill request latency, not production throughput or energy. The old 0.646 cohort remains a separate study.

All nine V4 capsules were independently retrieved/reconstructed and their frozen offline verifiers executed in [CPU audit run 37015269566](https://github.com/leecdiang/HeteroSpec/actions/runs/37015269566); all 228 native A-live/B-formal arrays and the B raw QPC-to-statistic chain were separately recomputed. [Evidence closeout](paper/mlsys2027/evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) defines the scope. No new model inference was performed. The original amended host-policy history is preserved; the author instructed not to treat fan adjustment as an obstacle.

## Next work and guardrails

RTX A+B is CLOSED. Next: integrate the new bounded evidence into a new manuscript version, rebuild exact artifacts and conduct independent submission-level review. The old PREPARE_ONLY prompt is historical, not a current run instruction. Existing B570/358H/M4 campaigns remain closed; dense B570 scans, new backends, 358H persistence and M4 variants remain deferred/not authorized. No result-driven candidate or cohort search.

The paper still centers B570's draft-free prospective 72/72 prediction; predicted blocked paths are not lossless replacements. M4 Guard loses to fixed speculation. 358H's zero-draft/residual bounds are conditional on fixed progress/target work. Remaining evidence-access limits include unavailable 358H runtime traces and exact old v0.8.4 ZIP. Offline archives do not authenticate omitted external assets or trusted absolute chronology.

Use [the v0.8.6 artifact manifest](paper/mlsys2027/evidence/FINAL_ARTIFACT_MANIFEST_V086.json) and [build instructions](paper/mlsys2027/manuscript/README.md). Public release, author/licensing metadata, arXiv and conference submission are separate decisions.
