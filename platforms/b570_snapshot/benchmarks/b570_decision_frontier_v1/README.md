# B570 decision-frontier v1

Independent, exposed-input CPU audit and bounded native observation study. Fixed PR103 result b46415f2725d7c06e093a6cd2b2d261b61925dc6; fixed PR101 26706c9fb4818ec3465e45acea029c4ab88a390f. This study does not modify those artifacts.

The immutable F0 binds source bodies, 56 mixtures and recipient initial logits, 168 fresh-process slots (16/32/40/80), panel-specific prefixes/cuts/token rules and 168 attempts / 21600 owned seconds / 4 GiB output. No warmups, probes, scientific retries, upstream intervention, teacher forcing, or paid latency.

CPU: set FRONTIER_CPU_ROOT to the evidence directory and FRONTIER_FRESH to a fresh PR103 restore, then run test_frontier.py. audit_raw.py independently restores and verifies the commit-pinned final ZIP; state_distance.py computes actual F16 distances; plan_frontier.py resolves full-logit gaps. run_frontier.py executes each frozen stage only after authenticated F0 readback; analyze_frontier.py independently validates original native evidence and computes FP64 contrasts. Use --help for exact arguments.

Historical full-logit availability and complete new-batch analysis are separate. Full FP32 vectors and FP64 vector residuals are preserved in the local private evidence package; remote raw availability remains REMOTE_PENDING. Other-machine recomputation is NOT_PERFORMED.

Native collection stopped at its first counts attempt: a frozen task|state donor registry omitted recipient and imported the wrong KV. No retries or new subset requests. RESULT.md and FRONTIER_ANALYSIS.json explicitly separate 44 available historical four-cell comparisons from the failed new batch. RAW_MANIFEST.json binds the local/private archive; RESTORE_RECEIPT.json records same-host fresh recomputation. independent_logits_check.cjs adds post-stop CPU-only JavaScript checks of full raw vectors/prefixes/Float64 contrasts (audit JSON, analysis JSON, fresh root, output JSON). This does not qualify the failed native control or amend/restart F0.
