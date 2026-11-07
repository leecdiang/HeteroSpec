# Sources and retrieval scope

Checked 2026-11-04. User-authorized private repository content was accessed through the connected GitHub tool. No unpublished evidence was sent to external literature-search queries.

- PR171 source/result: https://github.com/leecdiang/HeteroSpec/tree/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution
- PR169 source/result: https://github.com/leecdiang/HeteroSpec/tree/8ca17478c292275b3515a91b51d0e791a8fae256/benchmarks/b570_parallel_v1
- Actual B570 caller implementation: `worker.cpp` (`natural`, `chunk`, `partition`); actual physical planner: `wb_plan.py` (`hs_parallel_groups`). These support the proposed rechunk comparator. The new comparator has NOT been natively built/tested here.
- OASST1 dataset card and revision: https://huggingface.co/datasets/OpenAssistant/oasst1/blob/56e16363c12104182b8ad8173591b4d1e31c1faa/README.md . Apache-2.0; parent/message/root fields support tree reconstruction. The card was inspected; a full native-tokenized cohort has NOT been downloaded or selected in this authoring task.
- vLLM v0.25.0 design documentation: https://docs.vllm.ai/en/v0.25.0/design/prefix_caching/ . Explicitly caches full blocks; supports distinguishing logical LCP from actual reusable prefix. This does not assert a universal block size, same numerical reference, or reproduction of vLLM performance.

The proposal's workload, estimates, thresholds, allocation and new algorithms are prospective design choices by the authoring assistant, not facts measured by these sources. SGLang/LLM-42 are not claimed to have been ported in this study.
