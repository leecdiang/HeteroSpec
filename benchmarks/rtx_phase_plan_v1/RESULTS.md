# RTX resident phase plans: completed native results

SIMPLE is sufficient to implement the admitted resident phases under the original numerical R. LOCAL transfers unchanged and reduces Smol D4 resident service, but Smol target-only M is faster. Qwen has no established incremental LOCAL-D4 advantage over SIMPLE-D4 in this eight-root panel. There is no universal speculative or LOCAL winner.

Design input: PR188 actual head `de96c18ced307b480f360d4d88a85792fc71fd6c`. Result branch: `codex/rtx-phase-plan-results`, PR190. Original R, old D invalidation, prior AUTO null results, B570 and arXiv remain unchanged. No rental, new AUTO/MMA arm or merge.

## Native method and actual qualification

`native/resident_context.hpp` binds actual dense-cache occupancy, physical head, positions, capacity, padding and F16 types to immutable per-call groups. The native graph binding obtains real tensor shapes/strides, Q/K/V head mapping, scalar arithmetic preference and CUDA placement/dispatch. SIMPLE uses maximal compatible whole-graph groups up to32 queries with loop4. LOCAL keeps wide outer projection groups and groups reference-prefix attention locally, using the inherited packed operator. Both receive the same lifecycle, arithmetic and output-owner repairs. No model-name, prompt-ID or registered-coordinate strategy branch is added.

One target/KV owner executes prefill, ordinary decode and verification. Originally requested logits are copied before a later split overwrites native output storage; the selected logical row remains the frontier after trim. Original masks, k3 proposal/sync policy, pending tokens, cap128 and native EOG are retained. Actual clean public sequence-export/import/context-init API counts are zero; reference replay is absent from the supported method. RTX original R was already resident, so zero migration alone is not a new RTX speedup.

The independent original executable/observer bridges pass. Original R stays C1024, physical UB1, output reserve1, NATIVE whole-prompt caller with only its final output requested, F16 K/V, no FA and24 threads. Candidate reserve4 is separate from physical query width32. Later candidate code is not renamed R. Final executable/core/module bindings are checked against the published freeze.

At the retained APPS/train/65 counterexample, actual requirements prescribe SIMPLE1+3 at observed head767; LOCAL uses extents [768,1024,1024,1024] within its four-query call. Requested vectors and active KV/frontiers agree with independent original R. The original failed candidate/result remains a failure. Each final executable passes all48 registered boundary/width cells, including q1/2/3/4/5/8/16/32 and both sides of256/512/768. Wide q>4 diagnostics retain the original last-only output mask, rather than enlarging R reservation.

The common rule and actual candidate bytes were published at `f9c9289a2fc3516558d12ce15c1fa00f06419a94` before new Smol outputs. Qwen has36 layers,32 query heads,8 KV heads and128-dimensional heads; Smol has24 layers,32 query/KV heads and64-dimensional heads. Both use identical clean candidate executables. Subsequent host-only storage/metadata/resumption repairs do not extend the numerical rule or change R.

All six development arms pass full originally requested target-vector comparisons, including unaccepted branches, and complete active KV/frontier comparisons at initial, first speculative commit when present, and terminal boundaries. Rejection after acceptance, all-accept/bonus, unequal cap tails, reused contexts and native EOG are exercised. These are finite observations at declared boundaries, not a theorem or an all-intermediate-state dump. Clean confirmation checks independent R endpoints and producer/frontier/pending/termination traces; it does not export or claim full-vector/KV equality for every clean test slot.

## Source predictions versus observed work

Separate zero-drop CUPTI traces match the pre-output projection-work predictions. Counts below are actual CUDA kernel activities, not host launch-API counts or inferred device time.

| Family | SIMPLE activities | LOCAL activities | SIMPLE−LOCAL MMVQ | SIMPLE−LOCAL quantization |
|---|---:|---:|---:|---:|
| Qwen |45633|40404|5229|0|
| Smol |36599|34289|2640|-165|

Smol retains extra tail work: quantization and other activities each increase by165 in LOCAL, while MMVQ falls by2640. The total activity reduction is2310. Native decode calls, physical-width evidence and cache heads are retained. Separate clean CUDA graph construction/reuse counts and host CUDA launch-API counts are not invented from the inherited observer field; their work remains inside synchronized service. Initial-plan clocks measure CPU grouping, not GPU code generation.

## Fixed development screen and new confirmation

One fixed four-exposed-root timing pass per family supported bounded confirmation. LOCAL/SIMPLE D4 service ratios were0.986272 for Qwen (two adverse roots) and0.962905 for Smol. No development timing was retried for a favorable value. A storage-interrupted Smol SIMPLE-D1 pass keeps its first three completed measurements; charged history recovery supplies only the missing fourth warmup/measurement. Recovery samples are not substituted into the first three slots.

The new panel selects raw source roots before native token admission:16000 source entries,8435 unique unexposed roots after conservative historical identity/text exclusions,32 frozen source candidates per domain/family, then capacity-only admission of four math and four code roots per family. Original native tokenizer/template roundtrips pass12 historical inputs per family. No padding, alignment/opportunity filter or favorable offset is used. Prior PR174/175/177/186/187 and development exposures are excluded by the frozen snapshots.

Source/input/estimand freeze `2112778750da2affda16d6efdf8a4139bcae3f0e` and independent published readback receipt `139d84f00b5442e52cdb76e4d2512e88f95487b3` precede all new test forwards. Six Williams sessions complete exactly576 measurements and576 immediate same-arm warmups, plus16 separately charged original-R free requests. All1152 candidate requests pass endpoint/trace/API checks. No input, failed slot or session is replaced; no extra round is added.

Each arm/root pair provisions both model weights and resident contexts in a fresh worker, then runs an immediate warmup and measurement on those contexts. Setup, priming, integrity checks, record I/O and process cleanup are charged separately. Primary service includes reset, synchronized native phases, planning, requested-output copies, sampling, bookkeeping and request teardown.

## Complete measured resident service

Each table entry sums48 measurements (eight independent roots × six sessions); units are seconds.

| Arm | Qwen | Smol |
|---|---:|---:|
| SIMPLE-M |166.154947|39.129375|
| LOCAL-M |163.823185|37.810487|
| SIMPLE-D1 |139.881112|53.080506|
| LOCAL-D1 |138.007401|51.451107|
| SIMPLE-D4 |120.985659|42.550479|
| LOCAL-D4 |119.908386|40.914665|

Primary fixed contrasts use10000 root-cluster bootstrap draws, keeping all six repetitions and arms together. The intervals below are approximate Bonferroni-adjusted98.333333% intervals for three fixed contrasts within each model family. The independent unit is the root (n=8), not48 repeated slots. Families are analyzed separately.

| Family | Numerator / denominator | Total service ratio | Adjusted interval | Adverse roots |
|---|---|---:|---|---:|
| Qwen | LOCAL-D4 / SIMPLE-D4 |0.991096|[0.979442, 1.005593]|1/8|
| Qwen | LOCAL-D4 / SIMPLE-M |0.721666|[0.570176, 0.833625]|0/8|
| Qwen | LOCAL-D4 / LOCAL-M |0.731938|[0.585783, 0.838898]|0/8|
| Smol | LOCAL-D4 / SIMPLE-D4 |0.961556|[0.954028, 0.973783]|0/8|
| Smol | LOCAL-D4 / SIMPLE-M |1.045625|[0.969502, 1.111415]|4/8|
| Smol | LOCAL-D4 / LOCAL-M |1.082098|[0.994033, 1.160700]|5/8|

Qwen LOCAL-D4 saves1.077273s in aggregate versus SIMPLE-D4 (0.89%); its adjusted interval crosses1, and MATH/algebra/train/191 regresses. SIMPLE-D4 therefore remains a sufficient, competitive organization; a stable incremental LOCAL advantage is not established here. Both fixed D4 paths beat the corresponding measured M totals on this Qwen panel.

Smol LOCAL-D4 saves1.635815s versus SIMPLE-D4 (3.84%), with all eight root totals improving. However LOCAL-M is fastest: LOCAL-D4 costs1.082098 times LOCAL-M, with five adverse roots, and1.045625 times SIMPLE-M, with four adverse roots. The adjusted M intervals overlap1. The D4-to-D4 improvement is not a demonstrated speculative advantage over M.

LOCAL-D4/observed-min-M ratios are0.731938 for Qwen and1.082098 for Smol. Both fixed M contrasts are reported above; their simultaneous interval envelope is [0.585783,0.838898] and [0.994033,1.160700], respectively. This avoids an uncorrected posthoc minimum. All15 paired contrasts, Bonferroni99.666667% descriptive intervals, absolute differences, every adverse root and secondary equal-root geometric sensitivity are in `host_evidence/confirmation/RESULTS.json`. No significance target or learned routing is used.

## Setup, warmup and full host costs

These components are retained alongside resident service. Host wall covers each complete warmup/measurement pair, including model/module integrity checks, model/context setup and process/record overhead. It contains the other components; the columns must not be added again.

### Qwen costs (seconds)

| Arm | Warmup service | Model load | Context pool setup | Full host pair wall |
|---|---:|---:|---:|---:|
| SIMPLE-M |148.518423|194.780469|1.188488|846.531000|
| LOCAL-M |146.262373|194.223400|1.185419|851.451000|
| SIMPLE-D1 |131.137315|194.110801|1.190660|829.688000|
| LOCAL-D1 |129.118739|193.901326|1.185932|826.771000|
| SIMPLE-D4 |113.990787|193.843655|1.187106|798.324000|
| LOCAL-D4 |111.897114|193.954384|1.189083|789.560000|

### Smol costs (seconds)

| Arm | Warmup service | Model load | Context pool setup | Full host pair wall |
|---|---:|---:|---:|---:|
| SIMPLE-M |42.660798|46.628866|0.827973|311.657000|
| LOCAL-M |41.039227|46.655654|0.835253|311.499000|
| SIMPLE-D1 |56.906140|46.575556|0.827181|336.450000|
| LOCAL-D1 |54.967084|46.660100|0.830883|335.951000|
| SIMPLE-D4 |46.912774|46.507068|0.832669|335.452000|
| LOCAL-D4 |45.199230|46.567876|0.828420|336.424000|

Setup dominates many benchmark pairs. Smol LOCAL-D4 full host wall is336.424s versus335.452s for SIMPLE-D4, despite lower resident service. Resident savings do not establish a cold-start end-to-end advantage. The JSON retains calculated native-setup amortization at1/16/128 requests, explicitly distinguished from additional measurements; warmup and full wrapper costs remain separately visible.

## Cumulative resource ledger and retained failures

All723 attempts reserve1902 logical model trajectories, 1803902 decoded rows and0 isolated operator probes under unchanged4096/12000000/1536 ceilings. Confirmed complete work is1865 trajectories/1172163 rows. Including partial native counters, the observed lower bound is1895/1193242; remaining partial work is unknown. Failed reservations are never refunded.

Complete native host-attempt wall is11936.305000s. Recorded request service is2698.424285s, including qualification/warm/recovery work, not just formal measurements. The confirmation coordinator records7018.016s including original R and outside-service validation. These clocks overlap and are not additive. Original-reference teachers, repeated diagnostics, failed work and build/storage clocks remain in unified/engineering costs. Some CPU preparation components were not separately wall-metered: no missing component is zero and no complete total engineering-time claim is made.

Eight native failures remain: the initial scoped dummy-reservation assertion; Smol matrix9/11 reference disk stops; interrupted Smol SIMPLE-D1 development; Qwen exact-matrix6 LOCAL system-volume stop; and three retained matrix11 LOCAL output-volume stops. The common initialization repair precedes Smol. Later bounded metadata reads, verified hardlink/chunk reuse, lossless compression and archive relocation repair storage without changing candidate/R numerical bytes or replacing completed measurements. Final same-version GPU qualification succeeds after repair.

Native output D/E20GiB, C system10GiB, RAM4GiB and GPU128MiB floors remain enforced. The separate bounded F cold archive uses18GiB reserve and is not a native output volume. Every retired raw byte is reconstructible with chunk and complete-file SHA256 checks. Cache deletion was blocked by automatic approval; the deletion was not bypassed.

## Delivery, scope and decision

The reusable artifact is the native requirements → immutable grouping → same-KV execution → owned requested rows interface, with two measured lowerings. Fixed reductions, loop4, packed kernels and same-context execution are inherited ingredients. The contribution is their demonstrated composition with a pre-existing numerical reference across phases and two real structures, not a new arithmetic algorithm, universal transaction system or equivalence proof. See RELATED_WORK.md for Taming, Vosti and LLM-42 scope.

Support is the pinned dense single-sequence append/reset/trim deployment, C1024, uniform F16 K/V, no FA, original masks and the admitted native arithmetic/backend profile, with query groups up to32. Holes, shifted/wrapped/sliding or paged caches, multi-sequence scheduling, different arithmetic/backends and other runtimes require separate support/qualification. Neither matching metadata nor this finite corpus proves arbitrary-input equivalence.

Keep SIMPLE as the sufficient reference-compatible organization; retain LOCAL as a separately selectable optimized lowering with the measured Smol same-arm savings and its strong-M limitation. No model-name/input-position routing or new AUTO is deployed. No further GPU work follows this panel.

RTX workers and the owner lock are absent (`host_evidence/host/GPU_STOP.json`). Reproduction instructions are in REPRODUCE.md. The [authenticated private-repository evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/rtx-resident-phase-v1-evidence-20261106) contains original-path manifests, compiled workers/cores/modules, staged sources/build commands, all raw failures/references, cold states, data/exposure dependencies, ledger and traces. GGUF weights are separately pinned inputs. Publication/readback receipts accompany the final result commit; transport checks do not constitute a new GPU qualification.
