Ancillary reported-data and consistency package

These files support the article's numerical tables, contrasts and scientific
history. They do not contain all model weights, runtime binaries or raw tensors.

check.py verifies the original complete result matrices, original copied source
identities, six-session estimates/intervals, service blocks and generated figures.
check_repair_interaction.py verifies the retrospective repair--draft contrast from
unchanged six-decimal ratios. Its rounding enclosures are not confidence intervals.
The complete test entry point is documented in the source-root README.txt.

TeX compilation uses tables/ and figures/ outside this ancillary directory.
Report-only scripts operate on the complete downloaded source package. No code
here calls a model, GPU, network service or an external language model.

Historical failed comparisons, incomplete vector coverage and unstarted work
remain in the supplement, source_manifest.json and historical_disposition.csv.
Old editorial QA is retained in the repository's author working copy, but is not
part of the arXiv upload. Current checks describe reported-data reconstruction;
they do not establish unseen-input correctness or an external raw-data replication.

The 2026-10-26 integration adds followup_20261026/: exact compact records for
PR143/144/147/148, their Git/SHA256 identities, and generated summaries.
scripts/generate_native_followup.py reconstructs all later service ratios, the
registered20,000-resample bridge intervals and saved Llama token counterexample.
The original historical measurements remain unchanged. New-input/native
qualification is supported by the pinned platform records, not by running this
CPU checker.
