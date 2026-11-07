# Primary-source boundaries (checked 2026-10-05)

- [Pinned llama.cpp speculative documentation](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/docs/speculative.md) already supports model-free ngram drafting and mixing it with a draft model. The tested native cascade is an existing strong baseline.
- [Prompt lookup decoding, original repository](https://github.com/apoorvumang/prompt-lookup-decoding) proposes replacing the draft model with prompt string matching and describes input-grounded workloads. The field-edit gain is consistent with that known workload, not evidence of an invented proposer.
- [Thinking Machines: Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) and [batch_invariant_ops](https://github.com/thinking-machines-lab/batch_invariant_ops) establish batch-sensitive numeric reductions and provide batch-invariant operations. Their existence prevents claiming that fixing batch-sensitive kernels is a new concept.
- [LLM-42 v2](https://arxiv.org/abs/2601.17768v2) uses a fast path plus fixed-shape verification/rollback. A paid full replay or shape-consistent verifier alone cannot distinguish HeteroSpec.
- [SpecDec++ v3, COLM2025](https://arxiv.org/abs/2405.19715v3) learns an acceptance head and adapts candidate lengths. Merely changing k dynamically is not new.
- [Learning to Draft](https://arxiv.org/abs/2603.01639) jointly optimizes drafting and verification policies for cycle throughput. Direct latency/throughput optimization is also occupied.

Inference from our new data: global serialization loses acceleration on the exposed panel, while multiple batched proposal schedules fail the expanded panel's exact-output gate. This motivates a limited repair prototype. It does not identify a specific kernel, prove shape invariance, establish an online selective guard, or complete a novelty audit for all quantized CUDA implementations.
