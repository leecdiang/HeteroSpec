# Endpoint interpretation before reserved inference

The engineering frontend, build identity, checkpoint rule and R0 pass/fail gate remain at commit 237d34a. The added `characterize.py` runs only on independently validated evidence and is frozen before reserved inference. No additional model execution or checkpoint selection is introduced.

For every sampled fixed-proposal batch, report all three raw score records, top-1 differences, actual immediate committed/acceptance decision differences at a still-common prefix, and full continuation ID divergence separately. Count executions and unique prompts for each endpoint, excluding all engineering R0 observations.

If immediate decisions split, report TARGET_PARTITION_INTERVENTION_EFFECT_ON_TESTED_STATES, bounded to those measured states. If scores or downstream trajectories differ while the sampled block has no immediate decision split, report SCORE_OR_DOWNSTREAM_EFFECT_WITHOUT_IMMEDIATE_DECISION_EFFECT_AT_SAMPLED_CHECKPOINTS. Use NO_EFFECT_DETECTED_ON_TESTED_STATES only when the complete score, immediate-decision and continuation comparisons are unchanged. A continuation split alone cannot be described as a decision split at the sampled checkpoint. Correlated event counts are not independent prompts.
