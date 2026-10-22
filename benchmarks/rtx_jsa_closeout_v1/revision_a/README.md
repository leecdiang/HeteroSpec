# RTX PR140 amended study — closed

Read [RESULT.md](RESULT.md) for the final mixed disposition and [PAPER_ADDENDUM.md](PAPER_ADDENDUM.md) for manuscript-ready scope. Full raw access is indexed by [RAW_ACCESS.json](RAW_ACCESS.json).

- Qwen: all 12 inputs qualified; 3.2219% incremental layout reduction is below the 4.7781% A/A threshold, hence noise-limited.
- SmolLM2: all 12 inputs qualified; 6.9944% incremental layout reduction passes the screen; QB remains 0.7007% slower than R overall.
- Llama: PQ/QB agree with each other but fail deployed R on a 737-token natural input; no Llama timing or subset speedup.
- FAST: all three families have observed reference counterexamples; no qualified FAST timing.

The execution commit is `87570e6ac4c3f5060b5086969dfc5214e7b17da2`. All 7,729 file pins were rechecked after execution. The 1,776-request/888-worker ceiling contains 1,018 completed requests/509 started workers and 758/379 explicit NOT_RUN slots. There are no native retries or follow-on experiments.

Earlier files such as AMENDMENT.md, registrations and implementation freezes retain their **prospective status at the time written**; their historical wording is not the current study state. F0A calibration and its append-offset metadata failure remain intact. F0B and the sealed input panel are immutable. Existing PR140/PR142 records and old UUID charges are preserved.

`results/` contains the independent raw reconstruction, all input/block/slot/worker tables, exact cost estimates, counterexamples, per-layer observed geometry, charge order, resource/cleanup summaries and raw file hashes. `finalize.py`, `audit_raw.py` and `verify_complete_capture.py` are the frozen CPU verifier. `derive_results.py`, `package_evidence.py` and `upload_evidence.py` perform post-execution reporting and evidence transport. They do not launch model workers.

Remote evidence delivery completed on 2026-10-22: all **15 original ZIP shards and both indexes** are present on the authenticated [draft release](https://github.com/leecdiang/HeteroSpec/releases/tag/untagged-fbbb45e649bd0ef298b5). [Upload receipts](results/UPLOAD_RECEIPTS.json) match every full server SHA256 and byte count; [access probes](results/REMOTE_ACCESS_PROBES_V2.json) compare the full small archive index and the first/last 64 KiB of every other asset to the local originals. These bounded reads do not claim full remote ZIP readback or remote re-extraction. [Completion](results/REMOTE_COMPLETION.json) preserves the unchanged scientific pins and prior partial/failed transport receipts. No experiment was rerun.
