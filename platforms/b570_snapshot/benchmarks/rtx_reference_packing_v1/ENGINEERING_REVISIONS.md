# Recorded implementation revisions

Initial untested six-file prototype is retained in engineering/INITIAL_UNTESTED_SOURCE.zip. It had no input preparation, tests, formal cells or CPU_F0.

Revision1, before any formal comparison: verify FILL payload/use counts, mandatory owner/epoch, canonical operation IDs and final buffer drain; charge shared bank fill/read ports, reserve finite context writeback ports, add output store ports/latency/credits, and reserve64B global control/credit/latch storage in the same buffer. Rebind prospective native operand selection to completed PR104 E1 instead of the previously blocked historical fallback. Add meaningful independent numeric/trace/resource negatives and budget enforcement. These repairs follow code review/protocol requirements, not model outcomes. Formal panel remains unstarted. At most one further recorded engineering revision is available if tests expose defects; no result-driven architectural expansion.
