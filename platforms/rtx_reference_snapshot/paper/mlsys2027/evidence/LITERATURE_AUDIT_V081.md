# Literature audit v0.8.1

Accessed 2026-09-29. Primary-source audit; not an exhaustive search. Four mandatory papers were inspected through their full-text methods, evaluation, limitations and metadata (HTML/PDF). A broader 2025–2026 search covered consumer speculation, verification cost, CPU/GPU/NPU execution, deterministic inference, batch-shape divergence, state/KV reuse and adaptive control. Search snippets were discovery aids, not citation authorities.

## Mandatory additions

### Lossless but Not Free: An Empirical Anatomy of Speculative Decoding on Consumer Hardware
- Author: Param Chordiya. Year: 2026. Status: arXiv preprint 2607.17283v1; submitted July 19, 2026. Primary: https://arxiv.org/abs/2607.17283 ; full text https://arxiv.org/html/2607.17283v1 .
- Verified: Apple-silicon laptop; five backend pairs; two positive and three decelerating main configurations; best sweep speedup 1.61× (main best 1.57×). Quantized Metal small-batch verification lacks effective parallel execution (§6.5). Distribution checks and exact greedy agreement are reported; real-model greedy leg uses fp32 CPU (§6.1), not blanket exactness of Metal timing configurations. The same section already reports target-only batch-shape logit/argmax changes. Correctness gating itself is prior art.
- ADD (`lossless`). Exact paragraphs: Introduction opening; Related Work “Performance and cost accounting.” Removes novelty from slowdown, absent parallelism, draft/target latency gap, and the bare observation of numerical path dependence. Our distinction is the prospective cross-runtime qualification evidence and frozen reserved B570 output prediction.

### Compiler-Assisted Speculative Sampling for Accelerated LLM Inference on Heterogeneous Edge Devices
- Authors: Alejandro Ruiz y Mesa; Guilherme Korol; Moritz Riesterer; João Paulo Cardoso de Lima; Jeronimo Castrillon. Year: 2026.
- Status: 8th AccML workshop at HiPEAC 2026; official workshop PDF https://accml.dcs.gla.ac.uk/papers/2026/8th_AccML_paper_8.pdf . arXiv https://arxiv.org/abs/2602.08060 is v2, February 10, 2026 (v1 February 8). Author institution publication record confirms workshop status: https://cfaed.tu-dresden.de/publications?pubId=3873 . The institution export misspells Riesterer as Riesteter; the paper and arXiv supply Riesterer. Full de Lima spelling follows arXiv; workshop header abbreviates it. No workshop DOI verified; none invented.
- Verified: analytical profitability/mapping model, compiler partitioning, CPU/GPU validation on Cortex-A55/Mali-G310, up to 1.68×; short translation sequences, greedy sampling, no KV cache (§IV). This is performance/mapping prediction, not frozen complete output-trajectory prediction.
- ADD (`compilerassisted`), using published workshop metadata rather than a preprint label. Exact paragraphs: Introduction contribution statement; Related Work “Heterogeneous execution.”

### Lever: Speculative LLM Inference on Smartphones
- Authors: Tuowei Wang; Fengzu Li; Yanfan Sun; Wei Gao; Ju Ren. Year: 2026. Status: arXiv preprint 2605.16786v1, May 16, 2026; no final proceedings version verified. Primary: https://arxiv.org/abs/2605.16786 ; full text https://arxiv.org/html/2605.16786v1 .
- Verified: DRAM draft, flash-backed target, joint tree construction/pruning/execution design, mobile CPU/NPU mapping; reported 2.93× over Flash-AR and 1.50× over Chain-SD (§5.2). These are paper-reported geometric-mean decode speedups, not directly comparable to our post-prefill campaign estimators.
- ADD (`lever`). Exact paragraphs: Introduction contribution statement; Related Work “Heterogeneous execution.” Positive co-design evidence bounds the interpretation of the implementation-specific 358H interface measurement.

### HeteroSpec: Leveraging Contextual Heterogeneity for Efficient Speculative Decoding
- Authors: Siran Liu; Yang Ye; Qianchao Zhu; Zane Cao; Yongchao He. Year: 2026. Status: ACL long paper, pages 12930–12947, July 2026, Association for Computational Linguistics. Primary: https://aclanthology.org/2026.acl-long.589/ ; DOI 10.18653/v1/2026.acl-long.589. Official PDF inspected; proceedings author Zane Cao takes precedence over the older preprint's Zheng Cao.
- Verified: entropy-based context/verification-complexity estimation, stratification, adaptive depth/pruning and execution adaptation. This is adaptive resource allocation, rather than our output-contract qualification diagnostic.
- ADD (`aclheterospec`). Exact paragraphs: Introduction contribution statement; Related Work “Adaptive and contextual speculation.” The public manuscript does not propose HeteroSpec as its own method name. The only new public occurrences identify cited prior work; no same-name warning or ownership claim is appropriate.

## Broader candidates assessed without adding

### Cassandra: Enabling Reasoning LLMs at Edge via Self-Speculative Decoding
- Authors: Soongyu Choi; Yuntae Kim; Muyoung Son; Joo-Young Kim. Year: 2026. Status: arXiv preprint 2605.26558. Primary: https://arxiv.org/abs/2605.26558 .
- Relevant: low-batch consumer inference and algorithm/hardware co-design with weight/KV selection. DO NOT ADD: a different self-draft/compression mechanism, without a new boundary beyond the selected consumer and co-design citations. Exact paragraph considered: Related Work “Heterogeneous execution”; no edit made for this candidate.

### AHASD: Asynchronous Heterogeneous Architecture for LLM Adaptive Drafting Speculative Decoding on Mobile Devices
- Authors (arXiv display order): Ma Zirui; Fan Zhihua; Li Wenxing; Wu Haibin; Zhang Fulin; Ye Xiaochun; Li Wenming. Year: 2026. Status: accepted DAC 2026; arXiv v3 April 30, 2026, related proceedings DOI 10.1145/3770743.3803965. Primary: https://arxiv.org/abs/2604.25326 .
- Relevant: task-level mobile NPU/PIM scheduling and adaptive drafting. DO NOT ADD: custom architecture comparison does not alter the qualification or measured OpenVINO state-interface interpretation already sharpened by Lever. Exact paragraphs considered: Related Work “Heterogeneous execution” and “Adaptive and contextual speculation”; no edit made for this candidate.

### SSV: Sparse Speculative Verification for Efficient LLM Inference
- Authors: Zhibin Wang; Ziyu Zhong; Nuo Shen; Yuhang Zhou; Rong Gu; Sheng Zhong. Year: 2026. Status: arXiv preprint 2605.19893v2, May 20, 2026. Primary: https://arxiv.org/abs/2605.19893 .
- Relevant: verification-shape cost, sparse-attention KV reuse and profile-guided orchestration on H100. DO NOT ADD: sparse verification is outside the measured dense greedy stacks and adds no distinct comparator expectation. Exact paragraphs considered: Related Work “Performance and cost accounting” and “State and memory reuse”; no edit made for this candidate. Search results returned an older title, SpecSA; the current primary record supplies SSV.

### MarginGate: Sparse Margin-Triggered Verification for Batch-Invariant LLM Inference
- Authors: Kexin Chu; Yang Zhou; Wei Zhang. Year: 2026. Status: arXiv preprint 2605.30218v1, May 28, 2026. Primary: https://arxiv.org/abs/2605.30218 .
- Relevant: margin-triggered verification/repair for batch-invariant deterministic inference. DO NOT ADD: deterministic repair is already credited to LLM-42; this paper reinforces that numerical divergence/repair is prior art but does not replace our frozen diagnostic-output prediction comparator. Exact paragraph considered: Related Work “Correctness and numerical reproducibility”; no edit made for this candidate. This candidate appeared during existing-citation status verification.

## Existing citations retained

Dovetail, DuoDecoding, Mirror-SD, TurboSpec, BanditSpec, BatchCorrect, numerical nondeterminism, LLM-42 and compressed draft memory remain in their affected Related Work paragraphs. Current arXiv records for Dovetail, DuoDecoding, BatchCorrect, LLM-42, numerical nondeterminism, TurboSpec and compressed draft memory were checked; existing full-author entries remain. No claim of literature exhaustiveness or cross-paper speedup ranking is made. The bibliography contains 19 entries after exactly four additions.

Status follow-up: no final ACL Anthology records were found for BatchCorrect or compressed draft memory; retain their honest preprint labels and acceptance notes. The LLM-42 author institution lists SOSP 2026 (https://www.microsoft.com/en-us/research/publication/llm-42-enabling-determinism-in-llm-inference-with-verified-speculation/), but links the preprint and supplies no verified final proceedings DOI/pages. Retain the explicit v2 preprint citation, whose four authors match that institutional record; do not silently combine later arXiv author changes with the v2 bibliographic identity. No final publisher record was verified to replace it.
