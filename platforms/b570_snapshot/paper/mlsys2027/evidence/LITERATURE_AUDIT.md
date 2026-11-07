# Primary-literature audit — 2026-09-20

Citations are inspected primary publications/preprints, not search-result snippets. Full author lists are retained in references.bib and the official bibliography output. Reported external performance numbers are not imported into our empirical results. The authors must review the draft before submission; this is manuscript v0.1, not a submission-ready claim of authorship.

| Key | Inspected primary source | Relevant material / bounded use |
|---|---|---|
| leviathan2023 | https://proceedings.mlr.press/v202/leviathan23a.html | Official ICML publication/abstract and BibTeX; speculative draft/verify foundation; no firstness claim. |
| illusion | https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html | Official MLSys 2026 publication abstract and downloaded official BibTeX; verification dominance/workload variation and systematic vLLM study. Pages 1719–1741 verified from publisher BibTeX. Full PDF browser fetch exceeded tool size; no full-text-only claim is made. |
| specllm | https://mdpi-res.com/d_attachment/electronics/electronics-15-03179/article_deploy/electronics-15-03179.pdf | Actual publisher PDF downloaded and text inspected (abstract, introduction and cost/commit framing); S=τ/c, controlled policies and conditional execution cost. Publisher HTML returned 403/429, successfully resolved via publisher PDF. DOI 10.3390/electronics15143179; four authors verified on PDF title page. |
| dovetail | https://arxiv.org/html/2412.18934v2 | §3.1 GPU draft/CPU target; official author metadata. v1 is 2024, inspected v2 is 2025; bibliography explicitly pins v2. |
| duodecoding | https://arxiv.org/html/2503.00784v1 | CPU draft/GPU target, concurrent execution and hardware-aware budgeting; all four authors verified. |
| mirror | https://arxiv.org/html/2510.13161v2 | GPU/NPU mapping in method and appendix; all six authors verified. Cited as preprint, not as an independently replicated hardware result. |
| batchcorrect | https://arxiv.org/html/2510.22876v4 | Output-equivalence diagnostic; synchronization invariants and residual numerical differences. Current title differs from terminal handoff's historical title. |
| llm42 | https://arxiv.org/html/2601.17768v2 | Verify/rollback under fixed-shape execution for determinism; not a claim that this is our new idea. |
| numerics | https://arxiv.org/html/2506.09501v2 | System configuration and finite-precision non-associativity; all ten authors verified. Current title differs from historical title. |
| distance | https://arxiv.org/html/2606.25091v2 | Abstract and paper framing of closed-form latency conditions for edge/cloud speculation; no claim of a new break-even equation. |
| compactmemory | https://arxiv.org/html/2608.30252v1 | Draft-side compressed KV memory and incremental compression/update; distinct from our full-prefix replay measurement. |

## Title/version drift resolved explicitly

- `2510.22876`: handoff's **Batch Speculative Decoding Done Right** is now **Correctness Forensics for Batch Speculative Decoding: Diagnosing the Ragged Tensor Problem**, v4 (2026-08-31). The manuscript cites current v4 and mentions the former title. The novelty boundary remains valid.
- `2506.09501`: handoff's **Give Me FP32 or Give Me Death?** is now **Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference**, v2 (2025-10-24). Current title and full author list are used. No scientific claim was strengthened by choosing a different version.
- Forthcoming EMNLP status follows the arXiv author-supplied comments; references remain explicitly arXiv preprints. No invented final proceedings pagination.

No unresolved bibliographic identity gap remains for the cited mechanisms. This is targeted positioning, not an exhaustive systematic literature review. Author review of positioning remains necessary.

Downloaded SpecLLM publisher PDF SHA-256: `171fbe942a13d5b316affee4adff9fa2097c862995a8263ccc0956b82f712e4d`. Full copyrighted papers are not vendored into the repository.

Dataset citations added: HumanEval official arXiv 2107.03374v2 author/abstract page (all 58 authors retained), and the official ACL publication https://aclanthology.org/2024.findings-acl.456/ (all nine authors, pages 7655–7671), which introduces Spec-Bench. Dataset citations identify provenance; HumanEval functional evaluation is explicitly not performed here.
