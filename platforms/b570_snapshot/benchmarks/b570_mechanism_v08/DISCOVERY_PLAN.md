# B570 qualification mechanism study v0.8 — discovery freeze

Starting main: `31e756f3311cee4226bd1be57ee6febadd032aa4`.
The complete user-supplied protocol is preserved in STUDY_PROTOCOL.txt.

Before any inference, commit this plan, exposure inventory, deterministic reserved selection, and harness design. Reserved prompts are forbidden until a selected hypothesis and exact predictor have been committed and pushed. Dataset text may be packaged without inference.

Use exactly 12 exposed discovery tasks: HumanEval/89, /101, /104, /162 (residual mismatches); /3, /10, /68, /70 (serialization-repaired); /19, /20, /28, /32 (stable exact). Three repetitions for qualification and discovery. Discovery is exploratory and cannot establish transfer.

First qualify HARNESS_REF_UB128 against all 90 archived TARGET_REFERENCE sequences over the 30 historical tasks. Any incomplete execution, placement error, or sequence mismatch stops scientific work as HARNESS_NOT_QUALIFIED. Do not repair the harness after a failed scientific qualification and restart to rescue the result.

If qualified, evaluate H1 using the same common harness, target-only, UB1, on these 12 tasks × 3 repetitions. Require 36/36 complete direct-ID matches to archived serialized outcomes, including all four residual divergence fingerprints and reference-equal controls. If H1 passes, select H1 without constructing H2.

Only if H1 fails, evaluate H2: fixed-proposal target verification replay at UB1 with no live draft during replay. Obtain discovery-only observational proposal logs if absent; require unchanged committed sequences versus archive. Require 36/36 complete replay-to-serialized matches. If H2 fails, stop as MECHANISM_NOT_ISOLATED. No third hypothesis or parameter sweep.

Selected predictor must be frozen and pushed before reserved inference. Reserved validation uses 24 frozen tasks × 3 repetitions: target reference and predictor first (144 executions). Require within-condition repeat stability; otherwise preserve data and stop operationally ambiguous before outcomes. Commit and push all 72 predictions and their file digest before 72 live serialized outcomes. Never edit predictions after outcomes start. Primary validation requires 72/72 exact complete sequences; any smaller count is MECHANISM_PREDICTION_NOT_FULLY_VALIDATED. Continue mismatches; no selective rerun or tuning. Secondary endpoints are descriptive classification and first divergence. No confidence intervals are declared.

All modes use b10839/0cae43063cf15170e91a2ff4d034da0ecef4a1b2, Qwen3-8B Q8_0, B570 Vulkan0 37/37 offload, context 1024, batch 512, FA off, greedy seed 123, first 128 committed IDs or inclusive first EOG. Serialized uses Qwen3-0.6B Q8_0 Vulkan0 29/29 and k=2 with UB1. Reference uses UB128. Preserve raw output IDs, logits top two and margins, commands, partitions, stdout/stderr, hashes, environment, and chronology.

Do not change historical evidence or manuscript/reviews. No performance or energy experiments. No automatic merge. Independent hardware-free checker and content-addressed evidence bundle required for closeout.
