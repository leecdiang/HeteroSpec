# Claim → evidence and allowed interpretation

| Claim | Fixed source / local reconstruction | Allowed interpretation and limit |
|---|---|---|
| Query/mask view equivalence | Reviewed v4 §3; retained §3 equations/proof | Exact-arithmetic index mapping only; numerical kernels qualified separately. |
| Original CUDA request benefit | PR104 `f997262d6b0accb126a1217c9356745cc8bbf708`; anc/rtx104 | Six-session k3 resident-request PQ/QB reductions 3.06/6.17/2.83%; preserve task regressions and registered intervals. |
| PQ/QB operator correspondence | Same PR104; 72-context records | All tested QK/softmax/AV agree; MQ agrees only in 18 q1 controls. Not model quality or a universal reduction theorem. |
| State composition limits | Reviewed v4 complete S4/S5; state_and_pilot.json | Preserve 80 cells, 32 controls, donor/third/recipient outcomes, nonmonotonicity and 44/112 coverage. |
| RTX replay and padding | PR124 synthesis `9b8cdba784b34a5aa3e8981073223c451bbaaf54` indexing PR120–123 | ON/OFF is an execution-mode intervention. Failed padding has no qualified clean cost; kernel counts do not establish a bottleneck. |
| Complete Q representation cost | PR123 via synthesis; B570 PR128 `cf6c8bf43dc1ee4e9e8529bbe42300844e0165c9` | Each comparator and window explicit. Compact-QH does not establish practical improvement; not equivalence. |
| Scoped GQA repair | PR132 `7e98e288b4137c998604a0809c7e956474967de1` | Six synthetic coordinates pass while prior AV failure remains. Request qualification is separate. |
| B570 service | PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`; closure/b570_blocks.csv | QB/dual-PQ 0.995144 below 2%; QB/R 2.619763. Four exposed inputs, k1, one machine/date and private service policy. |
| Draft CPU policy | PR135 `e44c4df04c895b55ef734ee7b0659189158f95ab` | Ratio 1.003994: no practical benefit. Parameter change does not prove actual worker reduction. |
| Prefill submission closeout | PR143, main `805864b1`; followup_20261026/closeout/b570 | SUBMIT/dual-BASE 0.999161; practical benefit unestablished. Later CPU-draft contract; do not pool with PR134. Helper accounting limitation retained. |
| RTX service | PR137 `9868acfbb2ae2e4b753ad20b680c333d55289dc0`; closure/rtx_blocks.csv | QB/dual-PQ 0.989284 unresolved under 5.208% A/A; two session reversals retained. |
| RTX speculative economics | Same saved arm service times | QB/R 0.582325, 41.8% lower service; dual-PQ/R already 0.588633. Not 41.8% caused by QB, nor a throughput increase of that percentage. |
| Architectural implications | §8 with original strong baselines and later evidence | Software-first. Physical critical path, area, energy, frequency and hardware benefit are not established. |

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

## Major revision (2026-10-25)

The principal narrative now orders numerical qualification, repair-scope economics, QB incremental cost, transfer, and deployment cost. The E2 bootstrap remains primary; `anc/rtx104/e2_sensitivity.json` records t5 and leave-one-session checks. Llama C keeps a positive direction but its t5 interval crosses1.02. Authentic request rows provide absolute costs, separately from any new experiment. `anc/runtime_reproduction/` supplies a bounded CPU/archived-source kit, not native GPU replication. That was the 2026-10-25 cutoff; the completed matched bridge is integrated below.

## Native results integration (2026-10-26)

| Claim | Source | Interpretation |
|---|---|---|
| k3 QB gain survives fresh lifecycle | PR147 `3429e2c4`; exact 936-row TIMING.csv | QB/PQ is 0.937404 resident and 0.946409 fresh; both registered screens pass. Neither k1 cell passes. Six process sessions on one date; Graph mechanism remains unisolated. |
| Transfer requires deployed-reference qualification | PR144 `79f6e6d6`; exact timing/counterexample records | Qwen and Smol qualify 12 new inputs each. Llama PQ/QB agree but diverge from R at output81 of 737-token CodeContests/108; all Llama timing remains NOT_RUN. |
| Smol layout gain is not net draft gain | Same PR144 | QB/PQ 0.930056 passes the screen, but QB/R 1.007007 remains slower. Qwen's layout estimate is below its A/A threshold. |
| Native source-host reproduction | PR147 `3429e2c4` and PR148 `41cb7504` | RTX core/frontend rebuilt with pinned numerical DLLs; B570 rebuilt all five numerical DLLs and 147 shader units. Real stage/request fixtures replay. Fresh-directory checks use the same host; bulk raw access remains separate. |

This update preserves every original measurement file. New compact source records
are exact Git-blob copies. The paper reconstruction runs CPU checks only; native
platform executions are attributed to their original campaigns.

## Post-review revision (2026-10-26)

The main text now proceeds from workload qualification and repair-scope economics to QB incremental cost, complete-service deployment, and transfer. Section 8 specifies an offline selection rule, not an implemented online correctness detector or recovery guarantee. SmolLM2's qualified target-only batching is presented as a positive deployment choice; its draft-cost result, the Llama transfer failure and both k1 practical-screen failures remain explicit.

The native source-build scopes remain distinct: RTX core/frontend rebuild with retained numerical DLLs; B570 numerical-library and shader rebuild. `REPRODUCTION_ACCESS.md` lists exact pinned entry points and the external bytes still required. Complete external native delivery is not claimed. The revision adds FlashAttention/FlashAttention-2 positioning, disambiguates MQ from multi-query attention, corrects the mapping figure to `4/4 fail`, and moves historical service panels to Supplement S8. Measurement inputs and analysis estimators are unchanged. Current validation is recorded in `docs/research/review_revision_20261026/QA_FINAL.json` in the repository.

## Native material delivery closeout (2026-10-27)

PR149 `9149b6f5` and PR150 `9f03bead` close the minimum controlled-access material gaps recorded above. RTX now provides a 12-part source/fixture/full-request archive, relocatable wrappers and exact acquisition for 21 pinned numerical DLLs. B570 publishes a minimal source/stage/request package and all four inputs' complete references as private-repository release assets. Both provide exact model identities and acquisition routes. Source-host fresh-download CPU audits verify preserved bytes, with no new native execution. B570's 175 capture/reference comparisons and 914 reference self-checks have different roles and are reported separately.

The paper's scientific measurements and native rebuild scopes remain unchanged. Authenticated material delivery is established; independent-machine execution and anonymous public access are not claimed. The B570 historical driver version is identified but a fixed installer is not supplied. `REPRODUCTION_ACCESS.md` is the current access index; compact pinned records are in `anc/native_delivery/`. Current validation status is in `docs/research/native_delivery_closeout_20261027/QA_STATUS.json` in the repository.

## P0 evidence and narrative revision (2026-10-27)

The main repair argument now starts with the explicitly named seven-arm campaign.
The historical M3/C3 qualification table is retained in Supplement S2, without
retroactively assigning those implementations to PQ or QB.

`anc/rtx104/e2_draft_profitability.json` reconstructs 216 four-arm cells from the
original 864 local-arm measurements. The equal-task/session draft ratios remain
above parity for Qwen3 and Llama and below parity for SmolLM2 under both PQ and QB
in every session. This is a retrospective exploratory contrast; its pointwise
t5 intervals do not replace the registered PQ/QB intervals. E2 has no GS arm and
does not independently replicate the full GS/local repair interaction.

The original seven-arm response audit is indexed in `anc/seven_arm_work_audit/`.
It distinguishes equal recorded logical work from the physical graph fields
changed by GS. Complete-request time is not partitioned into projection,
attention, feed-forward or prefill shares.

The implementation-selection section now expresses a joint comparison of
qualified repair/layout/draft combinations under a fixed service contract. It
does not assert that sequential choices find a global optimum over untested
implementations. Scope conditions are centralized in the reference contract;
the Llama transfer failure, SmolLM2 draft cost, k1 screen failures and all original
measurements remain. Current revision and independent review records are in
`docs/research/p0_revision_20261027/`.
