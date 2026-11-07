Review materials for manuscript v0.15.3
Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding
Prepared 13 October 2026. Local author staging; no repository deposit or reviewer link has been published.

What the two packages contain

JSA_v0153_review_core.zip contains the article and supplement, editable figure sources, reported values, the claim-to-evidence map, fixed-commit source reports, exposed experiment scripts, and checks that run without a GPU. The original GitHub repository is private. Files actually included in this ZIP can be read offline; the GitHub URLs identify provenance and are not reviewer access links.

JSA_v0153_native_source.zip contains the CUDA study's patched native source extracted from its SOURCE_RUNTIME_V02 capsule, its upstream license notices, and a file-level extraction manifest. It does not include model weights or archived executables/DLLs. It is a source-inspection package. Rebuilding it on a different runtime does not by itself reproduce the study's numerical contract.

The author has authorized unpublished Zenodo drafts for read-only review. Author-owned code uses MIT; author-owned experimental data and figures use CC BY 4.0. See LICENSE_SCOPE.txt and licenses/. Upstream licenses remain in effect for their respective components. Draft URLs are confidential access tokens, not registered DOIs.

Start here

1. Read paper/main.pdf and paper/supplement.pdf.
2. Read paper/CLAIM_EVIDENCE.md. Source IDs resolve in paper/provenance/SOURCE_MANIFEST.json; the local campaign folders are listed below.
3. From the root of the extracted review-core package, run:

   python3 verify_review_package.py
   python3 run_report_checks.py

The first command verifies the packaged file hashes. The second runs report and figure checks in a temporary copy, leaving the delivered files unchanged. It requires Python 3.10 or later and the standard library, with no network, GPU, model, GitHub account, or TeX installation. Expected checks cover 186 reported-value conditions, 2,032 supplementary-figure conditions, and equality of the report extract to the included PR98 results. These are report-level checks, not a new audit of native timings or a hardware rerun.

For editable manuscript rebuilding, the separate author/source package contains the full TeX build requirements. The review-core package includes figure sources for inspection but is not the Editorial Manager source upload.

Evidence folders

- evidence/rtx98/: query layout, phase/reuse obligations, fixed-input operator replay, qualified repair costs, session and task comparisons; scripts/platform/... contains the study controllers and audit scripts.
- evidence/rtx91/ and evidence/rtx94/: three-family confirmation and its separately attributed CPU audit.
- evidence/b57092/ and evidence/b57093/: inherited production-path qualification and the later 240/240 complete-output pairing audit.
- evidence/b57097/: the physical-work witness and failed observer/receiver controls.
- evidence/b57099/: external prefill-partition intervention.
- evidence/b570101/: projection frontier, partition classes, eight failed scale controls, validated KV receiver, initial-logit negative control and limitations.
- evidence/historical/: the destinations of the 28 earlier experiment groups. The review-core package does not duplicate every earlier experiment archive.

SOURCE_ACCESS_INVENTORY.json records each selected campaign's commit, original path, Git blob identity, byte size and retrieval status. A file marked not_fetched or failed_retry_required is not included. verified_raw_part_separate_local_store identifies parts restored in the separate raw staging directory, not files inside the lightweight core ZIP. Raw archive parts and raw subdirectories are inventoried separately from the report/source files. NATIVE_SOURCE_EXTRACTION.json links the native-source package to the original capsule SHA256. MODEL_ACCESS.json records model identity and acquisition status; model weights are obtained from their publishers under their respective terms.

Full raw audit and hardware execution

RAW_ARCHIVE_ACCESS.json lists the six primary archives and all 638 ordered parts, with per-part and full-archive SHA256 values. The six archives total 1,646,803,532 bytes before extraction. All six archives have now been restored locally and every indexed logical file rehashed; see RAW_RESTORE_VERIFICATION.json and RAW_SCIENTIFIC_AUDIT.json for the CPU rederivation and its limits. These large ZIPs remain separate from the core package. Once the named parts have been obtained, verify and assemble one archive with:

   python3 assemble_raw_archive.py --archive b570101 --parts-dir /path/to/parts --output /path/to/new-archive.bin

The helper verifies each part and the concatenated archive, refuses to replace an existing output, and does not extract or execute the contents. Use the campaign-specific restoration verifier for logical-file reconstruction and scientific checks afterwards.

A complete raw audit additionally needs the identified archive parts, the campaign's restore/audit program, and the expected archive hashes. Raw audit should preserve failed controls, rejected qualifications and campaign-specific endpoint contracts. It must not pool historical and final panels. PR101's 675,012,404-byte final archive is not included in the review-core package.

Hardware reproduction also needs the exact numerical runtime, matching model bytes, and the recorded host environment. The original Windows CUDA/Vulkan drivers and library identities are recorded in the campaign files. The study scripts contain original host paths and should be reviewed and adapted in an isolated workspace before use. No study controller, binary, model download, installation or GPU run is executed by the two offline commands above.

Known limits retained from the manuscript

The CUDA correspondence is sampled and finite. The target-only Qwen3/Llama session reversals and all task regressions remain. SmolLM2's cheaper repair does not make speculation profitable. The B570 experiments are a boundary study, not a Vulkan QB implementation; eight failed scale shams and the P1A/P1B driver-freeze gap remain explicit. Kernel-schedule causality and component-time attribution are not established.
