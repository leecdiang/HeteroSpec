# Direct committed-ID capture on the original CLI

Pinned source: llama.cpp `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` (b10839). The source inspected for this contract comes from the clean Git objects, excluding the old local server debug patches.

`tools/cli/cli.cpp` constructs `cli_context` and calls `run()`. `tools/cli/cli-context.cpp` starts the embedded server for a local model. This is how the original CLI executes; the study does not replace it with a separately designed server experiment.

`tools/server/server-context.cpp:process_token` receives `completion_token_output::tok`. Its ordinary caller sets that integer to the target sampler's selected ID. Its speculative caller iterates the accepted `ids` vector in order, sets `result.tok = ids[i]`, increments `slot.stats.n_gen`, and calls `process_token`. It stops that loop when the function returns false, including at the output cap or EOS. Draft proposals that were not accepted are never passed through this boundary. Prompt tokens are processed elsewhere.

At the end of `process_token`, the original source logs:

```cpp
SLT_DBG(slot, "n_gen = %d, n_remaining = %d, next token: %5d '%s'\n", (int) slot.stats.n_gen, slot.n_remaining(), result.tok, token_str.c_str());
```

`tools/server/server-common.h:SLT_DBG` prefixes this message with the function, slot ID and task ID. The function name is limited to 12 characters, so `process_token` appears as `process_toke`. `common/log.h` defines debug verbosity as 5. The native logger records the integer directly; the adjacent decoded piece is never used to recover or reconstruct the ID.

The runner selects only timestamped debug events from this function with `n_gen`, `n_remaining`, and `next token`. It checks that generated indices are exactly 1..N, the remaining budget is 128 minus each index, there is one slot/request, and N agrees with the final runtime generation count. It rejects missing/duplicate events, negative IDs, unsupported termination, incomplete offload and wrong device binding. A committed terminal EOG ID is part of the compared array even when its displayed piece is empty.

The native plain log is the capture sidecar. `generated_ids.json` is a structured copy of those actual runtime integers. `--output-file` supplies a CLI transcript for an auxiliary integrity check and the R0 original/logged comparison. The scientific comparator reads only complete ordered generated integer arrays; no prompt text stripping, whitespace normalization, tokenization or text reconstruction can override a mismatch.

No runtime source change or build is required. `instrumentation.patch` is a zero-byte patch. Original executable and DLL hashes are frozen. Verbosity 5, a log sidecar and a transcript file are observational command additions. R0 explicitly checks all 21 sanity/regression prompt/condition output transcripts against the same original binaries with verbosity 4.

Protocol v2 reads the log as raw bytes with a lossless Latin-1 view of ASCII fields. Invalid UTF-8 in any individual draft or committed-token fragment cannot invalidate ID extraction. Auxiliary committed pieces are concatenated as original bytes and checked against the CLI transcript bytes; their text is never re-tokenized.
