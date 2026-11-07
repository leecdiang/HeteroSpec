# Reviewer D targeted freshness search

Search date: 2026-09-25 UTC / 2026-09-26 Asia/Shanghai. Primary sources only used for substantive assessment. No comprehensive literature survey claimed. Search covered runtime/adaptive SD, admission/disable decisions, hardware-aware execution, deterministic/verified inference, online policies and draft-state overhead. The initial broad engine occasionally rewrote queries and returned irrelevant gaming-controller sources; those were discarded. A second engine and direct primary-page opens filled the gaps.

## Recommended addition: BanditSpec

- Title: BanditSpec: Adaptive Speculative Decoding via Bandit Algorithms.
- Authors: Yunlong Hou; Fengzhuo Zhang; Cunxiao Du; Xuan Zhang; Jiachun Pan; Tianyu Pang; Chao Du; Vincent Tan; Zhuoran Yang (proceedings form; arXiv uses Vincent Y. F. Tan).
- Venue: Proceedings of the 42nd International Conference on Machine Learning, PMLR 267, pages 24045–24079, 2025.
- Authoritative bibliographic URL: https://proceedings.mlr.press/v267/hou25h.html
- Updated full text inspected: https://arxiv.org/html/2505.15141v2
- Version: v1 2025-05-21; v2 2025-11-20 (typos and affiliations corrected).
- Supported comparison: online adaptive configuration selection is established; BanditSpec's stopping-time regret is a theoretical object and should not be conflated with HeteroSpec's descriptive measured latency ratio.
- Proposed minimal BibTeX:

```bibtex
@inproceedings{banditspec,
 title={{BanditSpec}: Adaptive Speculative Decoding via Bandit Algorithms},
 author={Hou, Yunlong and Zhang, Fengzhuo and Du, Cunxiao and Zhang, Xuan and Pan, Jiachun and Pang, Tianyu and Du, Chao and Tan, Vincent and Yang, Zhuoran},
 booktitle={Proceedings of the 42nd International Conference on Machine Learning},
 volume={267}, pages={24045--24079}, year={2025}, publisher={PMLR},
 url={https://proceedings.mlr.press/v267/hou25h.html}
}
```

## Existing citation requiring clearer comparison: TurboSpec

- Full text inspected: https://arxiv.org/html/2406.14066v3
- Title: TurboSpec: Closed-loop Speculation Control System for Optimizing LLM Serving Goodput.
- Version: v3, 2025-07-27; existing bibliography is version-pinned correctly.
- Supported comparison: its control objective includes disabling speculation, alongside adapting proposal/verification lengths using profiled execution and feedback. Section 4 distinguishes predictive goodput from directly observing a completed step. HeteroSpec may describe its own cumulative realized-cost input without claiming that runtime feedback or admission was absent from prior work.
- No bibliography addition required.

## Conditional freshness lead: MemSpec

- Title: MemSpec: Memory-Aware Runtime for Adaptive Draft Scheduling in Speculative Decoding on Edge Devices.
- Authors: Eunjeong Kim; Yeong Jun Jeon; Myeonggyun Han.
- arXiv: 2608.10362; primary indexed abstract date 2026-08-11.
- URL: https://arxiv.org/abs/2608.10362
- Retrieval limit: both search engines returned the primary arXiv abstract; direct abstract/HTML/PDF opens returned DisabledError. Full text and exact version history were not inspected.
- Narrow supported claim: an edge runtime studies draft-switching/residency overhead and uses prediction-guided scheduling. Do not attribute an exact-output contract, experimental split, complete timing boundary, or source-level distinction to it from the abstract.
- Conditional BibTeX, only if the coordinator accepts abstract-level coverage or retrieves the paper:

```bibtex
@article{memspec,
 title={{MemSpec}: Memory-Aware Runtime for Adaptive Draft Scheduling in Speculative Decoding on Edge Devices},
 author={Kim, Eunjeong and Jeon, Yeong Jun and Han, Myeonggyun},
 journal={arXiv preprint arXiv:2608.10362}, year={2026},
 url={https://arxiv.org/abs/2608.10362}
}
```

## Existing primary works checked

- LLM-42 v2 (2026-01-30): https://arxiv.org/html/2601.17768v2 and https://arxiv.org/abs/2601.17768v2. Current v2 author list is Raja Gond, Aditya K Kamath, Ramachandran Ramjee, Ashish Panwar, matching repository. It uses verification/rollback to enforce deterministic inference. It is not merely a report that numerics can diverge. Keep the existing distinction between this repair approach and HeteroSpec's measurement of excluded paths.
- Speculative Decoding: Performance or Illusion?, MLSys 2026: https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html. Official abstract confirms production-engine evaluation, verification dominance and observed/theoretical gaps. This supports retaining it as the nearest characterization precedent.
- Runtime-Controlled Evaluation of Speculative Decoding Methods: https://www.mdpi.com/2079-9292/15/14/3179. Primary indexed publisher title/metadata confirmed; direct page opening failed in this review. Existing manuscript already cites it for the cost/commit decomposition. No unsupported new source characterization proposed.

## Fresh works considered but not recommended for addition

| Work | Primary source / date | Reason not to expand bibliography |
|---|---|---|
| SPECTRA: Adaptive Execution of Speculative Decoding on a Runtime-Reconfigurable Tiled Architecture | https://arxiv.org/abs/2609.24847 ; v1 2026-09-21; official abstract notes ICCAD 2026 acceptance | Architecture reconfiguration is outside the admitted-path/cost-control contribution. Relevant to a hardware-design survey, unnecessary here. |
| AdaptiveSD: A Stability-Aware, Runtime-Adaptive Speculative Decoding Framework with Multi-Policy Orchestration for CPU-Constrained LLM Inference | https://arxiv.org/abs/2607.03876 ; indexed primary abstract 2026-07-04 | Full text unavailable; elaborate CPU resource controller differs from the narrow experiment. TurboSpec/BanditSpec provide clearer established overlap. |
| ModeSwitch-LLM: A Lightweight Phase-Aware Controller for Cross-Mode LLM Inference on a Single GPU | https://arxiv.org/abs/2605.23057 ; indexed primary abstract 2026-05-21 | Request-boundary mode selection with a quality gate is a different question; no need to broaden to quantization/mode routing. |
| A Sparse Glimpse of the Whole: Train-Free Self-Speculative Decoding | https://arxiv.org/abs/2607.27735 ; indexed primary abstract 2026-07-30 | Long-context self-speculation and entropy control; existing state-reuse and adaptive-control citations cover the required novelty boundary. |

This search did not establish a priority claim for HeteroSpec. Absence of a closer retrieved paper is not evidence of being first.
