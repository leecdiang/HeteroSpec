# Common target harness design

Build a small standalone executable against the retained b10839 llama-common static libraries and llama/ggml import libraries used for B570 direct-ID v1. Reuse the exact frozen runtime DLL bytes; record all library, header, executable, and DLL hashes. Source remains in scripts/platform/b570_mechanism_v08. Historical source/build trees are read-only.

Use common argument parsing, common_init_from_params, common sampler acceptance, common tokenizer, and common_prompt_batch_decode from the exact upstream source. Consume explicit prompt token IDs when supplied; otherwise package the dataset-derived prompt using the common tokenizer and archive those IDs. The generated stream is never retokenized. Reference and H1 differ only in n_ubatch (128 versus 1).

Decode each prefill chunk at n_batch=512 using the same batch API as completion. Decode one committed token per autoregressive step. Record the raw target top-1, runner-up, logits and margin before common sampling; record the actual sampled/committed ID separately, runtime EOG flag, position, n_past, decode input IDs, and batch/ubatch/context metadata. Include first EOG in the sequence. Stop at 128 IDs. Fresh process/context for every observation; no prompt cache.

Qualification is an empirical prerequisite: 90/90 complete sequences must reproduce the existing reference at UB128 before using H1. A faithful API design alone is not qualification. A failed qualification ends this study as HARNESS_NOT_QUALIFIED.

H2 is implemented only after qualified H1 fails. Its replay inputs must be generated without observing reserved live serialized outcomes. No archived or newly observed reserved live proposals may enter predictions; if an independent pre-outcome proposal construction cannot be specified, do not claim prospective H2 validation.
