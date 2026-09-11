# B570 backend-control preregistration v2 deviation note

The first B570 attempt is retained but reclassified **INVALID / CONFIGURATION-BLOCKED**. Its frozen `n_batch=128` caused llama.cpp to assert `n_tokens_all <= cparams.n_batch` on a selected prompt. Separately, the b10839 baseline and speculative applications exposed inconsistent 127/129 output-boundary counts in the old wrapper. The assertion is a capacity error and the count difference is an I/O/CLI-boundary ambiguity; neither is evidence of a Vulkan numerical mismatch.

Before any replacement inference, the exact frozen tokenizer measured the six unchanged formatted prompts at 137, 407, 130, 153, 116, and 177 tokens for HumanEval/106, /129, /3, /10, /19, and /20 respectively. `n_batch=512` is the smallest power of two covering the longest input. Because 407+128=535 also exceeds the old context 512, v2 fixes `n_ctx=1024`, the smallest power of two covering the input-plus-output contract. Both changes are capacity corrections selected without performance results.

The replacement contract compares only normalized generated token IDs, excludes prompt/prefix tokens, stops at EOS when earlier, and otherwise compares at most the first 128 generated tokens. Raw CLI total-token counts are not equality evidence. Ambiguous boundary/count reconciliation is a configuration error, not a mismatch. Synthetic normalization tests pass; no HumanEval output was used to debug v2.

No B570 V2 cell or HumanEval30 performance result existed when v2 was frozen. Correctness remains the first gate, and no replacement formal run is authorized by this note.
