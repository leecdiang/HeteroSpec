# Draft CPU policy: one-factor software intervention

Parent scientific candidate: PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`.

PR134 reports draft prefill9.229470s and draft decode/prefill12.366798s per QB request, despite a much smaller draft model. The phase data locate expensive work but do not identify a GPU bottleneck.

## Relevant source chain

- PR134 `formal.cpp`, Context constructor: `n_threads=8`, `n_threads_batch=8` for both target and draft. Draft prefill is token-by-token, physical ubatch1.
- Frozen `src/llama-context.cpp`, `graph_compute`: selects `cparams.n_threads` for a single-token microbatch and forwards it through backend `set_n_threads`.
- Frozen `ggml/src/ggml-cpu/ggml-cpu.cpp`, `ggml_backend_cpu_graph_compute`: passes the configured thread count into `ggml_graph_plan`.
- Frozen `ggml/src/ggml-cpu/ggml-cpu.c`, `ggml_graph_compute`: when compiled with OpenMP and `n_threads>1`, uses an OpenMP parallel region; otherwise uses a single worker.
- Frozen build `CMakeCache.txt`: `GGML_OPENMP:BOOL=ON`, `GGML_OPENMP_ENABLED:INTERNAL=ON`.

Although absent explicit threadpool binding creates a disposable ggml threadpool object, that does not establish per-call OS thread creation in this OpenMP build. No persistent-threadpool candidate is executed. The controlled intervention is draft context CPU thread parameters8 ->1 only.

Target remains8. Same compiled backend/model graph DLLs, CPU instruction implementation, GPU kernels, model weights, KV types, q1 prefill, QB verification, output reservations, sampler and state protocol. The count1 is the draft CPU computation policy, not a total native-process/driver-thread cap.

## Admission and inference

Every candidate target/draft logits vector must match the original PR134 QB file byte for byte, including rejected verification rows. Complete output and state traces must match. Only then measure BASE_A/BASE_B/DRAFT1/R complete service under balanced orders.

A cost reduction under this one-factor intervention supports CPU backend parallelism policy as a contributor under this environment. It would not prove a unique OpenMP implementation defect, physical GPU bottleneck, or that all models/backends should use one CPU thread. No requested inference relies on template pool allocations as a proxy for OS thread counts.
