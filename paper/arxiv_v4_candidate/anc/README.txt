Ancillary data and review records
================================
check.py preserves the original numerical/state checks and adds check_closure.py.
check_rtx104.py reconstructs the original six-session estimates and bootstrap.
check_portability.py retains the original necessary-condition CPU checks.
closure/ contains exact saved RTX/B570 CSV blocks, reported values, generated
figures/tables and their derived summary. RTX ratios are recomputed from saved
arm service times; the B570 table contains paired ratios rather than complete
native timing records. Neither operation independently replays full raw logits.

review/ records the uploaded v3 identity, section/label/reference preservation,
build and page inspection, academic-English edits and successful mutation tests.
check_result.json is the current 484-check result. The original 357-check result
is retained as review/V3_BASELINE_CHECKS.json. editorial_archive/ retains the
unchanged earlier development history; it is not current measurement evidence.

Do not combine old resident-request and new fresh-context-service ratios, treat
technical repetitions as independent inputs, or infer a GPU bottleneck from
host phase timings. All complete raw archives and native runtime identities
remain governed by their fixed experimental records.
