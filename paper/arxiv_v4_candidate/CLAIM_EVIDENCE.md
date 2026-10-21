# Claim → evidence and allowed interpretation

| Claim | Fixed source / local reconstruction | Allowed interpretation and limit |
|---|---|---|
| Query/mask view equivalence | Uploaded v3 §3; unchanged §3 equations/proof | Exact-arithmetic index mapping only; numerical kernels qualified separately. |
| Original CUDA request benefit | PR104 `f997262d6b0accb126a1217c9356745cc8bbf708`; anc/rtx104 | Six-session k3 resident-request PQ/QB reductions 3.06/6.17/2.83%; preserve task regressions and registered intervals. |
| PQ/QB operator correspondence | Same PR104; 72-context records | All tested QK/softmax/AV agree; MQ agrees only in 18 q1 controls. Not model quality or a universal reduction theorem. |
| State composition limits | Uploaded v3 complete S4/S5; state_and_pilot.json | Preserve 80 cells, 32 controls, donor/third/recipient outcomes, nonmonotonicity and 44/112 coverage. |
| RTX replay and padding | PR124 synthesis `9b8cdba784b34a5aa3e8981073223c451bbaaf54` indexing PR120–123 | ON/OFF is an execution-mode intervention. Failed padding has no qualified clean cost; kernel counts do not establish a bottleneck. |
| Complete Q representation cost | PR123 via synthesis; B570 PR128 `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9` | Each comparator and window explicit. Compact-QH does not establish practical improvement; not equivalence. |
| Scoped GQA repair | PR132 `7e98e288b4137c998604a0809c7e956474967de1` | Six synthetic coordinates pass while prior AV failure remains. Request qualification is separate. |
| B570 service | PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`; closure/b570_blocks.csv | QB/dual-PQ 0.995144 below 2%; QB/R 2.619763. Four exposed inputs, k1, one machine/date and private service policy. |
| Draft CPU policy | PR135 `e44c4df04c895b55ef734ee7b0659189158f95ab` | Ratio 1.003994: no practical benefit. Parameter change does not prove actual worker reduction. |
| Prefill submission follow-up | Same PR135, b570_draft_prefill_submission_v1/attempt2/QUALIFICATION_RECHECK.json | Four inputs/346 vectors qualified, one API call with physical q1. No complete timing result in reviewed tree; no software ceiling. |
| RTX service | PR137 `9868acfbb2ae2e4b753ad20b680c333d55289dc0`; closure/rtx_blocks.csv | QB/dual-PQ 0.989284 unresolved under 5.208% A/A; two session reversals retained. |
| RTX speculative economics | Same saved arm service times | QB/R 0.582325, 41.8% lower service; dual-PQ/R already 0.588633. Not 41.8% caused by QB, nor a throughput increase of that percentage. |
| Architectural implications | §9 with original strong baselines and later evidence | Software-first. Physical critical path, area, energy, frequency and hardware benefit are not established. |

The two service panels are separate within-platform studies, not a GPU-brand
comparison. RTX ratios are independently reconstructed from saved arm times;
B570 ratios are reconstructed from its saved paired-ratio table. Full raw logits
remain separately held. The paper contains no new native execution, no imputed
missing vector, no pooled cross-platform effect, and no synthetic confidence
interval for the four-input service panels.

## Explicit repair--draft contrast (2026-10-21)

The seven-arm table already supports the draft-parity crossover under local repair.
`anc/repair_interaction.json` and `scripts/generate_repair_interaction.py` make
that existing result explicit: `Gamma = (C_GS/C_QB)/(M_GS/M_QB)`. The ratios are
1.6115444934, 1.0706599083 and 1.5415718508 for Qwen3, SmolLM2 and Llama.
Both PQ and QB cross draft parity for Qwen3/Llama; SmolLM2 remains below parity.
This is retrospective common-panel arithmetic, not a new experiment, independent
confirmation, uncertainty estimate or operator-time attribution. The target-only
R/M_QB comparisons are also retained from the same original table.

All original scientific result inputs remain unchanged. New TeX table locations
under `tables/` remove compilation dependencies on ancillary-file handling.
