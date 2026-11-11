# PR87 B570 Llama memory follow-up: bounded closeout

The primary Q6 study completed550 native generation requests and12 zero-forward probes. The secondary Q8 study stopped after10 zero-forward probes because both all-weight-GPU target/draft loads had negative signed dedicated budget at draft weights, before draft context creation. There were no formal requests, scientific retries, F0B selection, manuscript edits or merges. Completion refers to the bounded engineering/evidence closeout; GPU feasibility and performance qualification remain unestablished.

## Primary Q6 result

All12 declared candidates ran the same12 exposed tasks twice, using exactly the same Q6 target file as ordinary and matched controls. Six native batched candidates diverged in whole generated IDs; six repaired candidates matched every whole native endpoint in their engineering panels. The unrepair diagnostic naturally triggered eight first differences across two repeats. UB128 reference was stable, UB32 changed a whole output and was excluded, and UB512 was the fastest whole-equivalent ordinary configuration. Matched controls were also whole-output equivalent.

The unique diagnostic first-ranked candidate was Q4_K_M / vulkan_batched_repair / k_max1. Its two instrumented engineering R_prod/C geometric ratios were0.7074518733 and0.7041989338, corresponding to approximately1.42 times the ordinary request cost. Its56 cap/capture comparisons, four warmups and four longest-input checks passed; the longest prompt had768 native IDs. An additional36 paid requests checked all four draft/mode combinations at k_max3 with caps1/2/3/4, actual native termination, full KV/state byte checks at phase binding, and reset/verification/rollback traces. These synthetic checks do not override the native modes' scientific-task divergences or select another candidate.

All performance numbers are exposed engineering diagnostics, with memory sampling/compute observations enabled. No confirmation confidence intervals or qualified speedup ratios are reported. No positive-gain admission rule was applied: the negative candidate received its unique full boundary check.

## Secondary Q8 result

With explicit GPU placement of every weight tensor, target Q8 plus draft Q4 failed the fixed128MiB budget at DRAFT_WEIGHTS: budget minus usage was-208109622 and-253526054 bytes in the two declared modes. These were pre-context budget guards, not generation OOMs. Six candidate entries are memory-blocked; zero secondary generation requests were made. Neither reducing k nor lowering a positive threshold repairs an already-negative observed budget. The earlier PR86 fixed512MiB outcomes are preserved.

## Residency and measurement limits

Actual per-tensor maps confirm Vulkan0 backend buffers for every weight tensor in qualifying logical-placement probes/workers; KV buffers and sampled compute nodes also map to Vulkan0. Earlier default-layer probes left CPU_Mapped input embeddings and remain nonqualifying. This study used an explicit tensor-buffer override after discovering that distinction. Logical buffer placement, VK_EXT_memory_budget and a PDH process sample do not prove physical allocation residency or absence of paging. WPR GPU tracing was rejected by Windows with0xc5585011. Physical residency remains UNKNOWN, all qualified ratios are null, and confirmation was not admitted. No accuracy, energy, root-cause or hardware-wide claim follows.

Memory records retain native PID, UTC, B570 PCI8086:E20C and both raw heaps. The guard uses only signed budget minus usage of the mapped device-local heap0; no system/shared heap is added. Periodic samples and before/after-decode samples bound observed peaks and retain sampling gaps; they do not establish a continuous physical-residency proof. Native weight placement and compute observations are deliberately separate from this missing proof.

Whole request timing begins before request JSON preparation and ends after the complete native IDs/stop response has been parsed and endpoint-checked. Proposal, verification, rollback and synchronization are inside the resident request. Hashing/persistence and the pre-request memory CHECK are outside, consistently. Model loads, warmups, search and owned-process lifetimes are charged and retained separately. Private instrumentation can affect these engineering timings.

## Provenance and restoration

PR87 design head is ab9dc1f935618931c3779f46a95f3b056b707457. Actual Git restoration of all405 F0A files at8c3a690acc3c8206662366bbe223387a31d50d05 preceded every new token forward. The rebuilt private llama module extends the inherited phase-binding guard to UB32/128/512 and adds read-only weight/compute observations. The four GGML modules retain inherited bytes; this is not an assertion that the newly built llama module equals the previous binary. Upstream numeric source SHA and checkpoint conversion remain NOT_CERTIFIED where no complete certification exists; full local source and binary bytes are bound.

All four full GGUF assets and128256-row native vocabulary tables are independently checked. Frozen ASSET_CHECKS retains original static design fields such as PENDING/false; its actual_sha256/actual byte-verification fields and independent full-file rehash are the executed evidence. Native tokenizer outputs, exact rendered prompts and IDs are retained. F0A policy design state is preserved as the original plan, while DECISION.json records executed state.

The ID history audit and opaque pool reservation are retained. Because no F0B/cohort was admitted, the full exact-description/history audit for a fresh24-task confirmation cohort was not finalized and no unseen-generalization claim is made. All engineering inputs were declared exposed. Historical results and manuscript worktrees were not edited.

CAS_INDEX.json identifies the complete deduplicated recovery archive and Git parts. Four exact GGUF files remain external hash-bound dependencies. The archive includes all raw native endpoints, traces, sampled memory, paid ledger, failed/nonqualifying probes, source/version/binary bytes, vocabulary, preparation failures and independent verifier. LOCAL_RESTORE.json and REMOTE_RESTORE.json record actual fresh restorations and identical CPU rederivation. Draft PR88 is the canonical result delivery; scientific status remains ENGINEERING_CLOSED_FORMAL_NOT_ADMITTED. A new frozen extension is needed before any further GPU campaign under these missing gates.
