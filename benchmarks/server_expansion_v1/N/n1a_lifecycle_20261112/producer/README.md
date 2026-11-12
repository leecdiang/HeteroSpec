# CPU producer component bridge: bounded scope, no model generation

Executed real pinned upstream vocabulary/tokenizer, parser, server task-state,
final-response, safe-JSON and chat-renderer functions. No llama_context, model
forward, GPU context, placement or resident N runtime was created. The output IDs
are supplied-history or explicit synthetic controls, never a free-generated R.

The final helper loads the exact Qwen3-8B-Q8_0 with vocab_only=true and
n_gpu_layers=0, checks the actual GGUF template bytes, and passes that real
vocabulary-only model pointer to common_chat_templates_init(model, ""). Thus BOS,
EOS, template metadata and source inference are not replaced by blank/null
initialization. The CPU-only linked ELF has no GPU dependency; model tensors are
skipped. The full8,709,518,112-byte model was separately read for SHA-256 once,
which is a file-integrity cost and must not be called tensor loading or forward.

## Actual contract exercised

The planned component profile is fixed before fixtures: nonstream basic-role
text, actual upstream common/jinja renderer, use_jinja=true, thinking=false,
reasoning_format=deepseek, no tools/media, explicit stop strings empty. Actual
runtime output reports PEG-native, additional_stops=[], and preserved think/tool
markers. The full returned generation_prompt includes the assistant header and
empty-think stub and initializes the real parser. The original Python Jinja2
canonical strings remain unchanged.

The CPU flow is:

provided/synthetic token IDs → actual vocabulary token pieces with real
preserved-token policy → actual task_result_state + final response update →
actual OAI-chat final-message/fallback formatter → actual safe_json_to_str →
JSON client message fields → next full canonical renderer → actual tokenizer.

This is a new nonstream component adapter using supported server APIs, not a
claim that the N service is already deployed. The modern CLI's actual stream=true
loop was not executed; its assistant content/reasoning history field policy is
used by the prepared consumer. No full HTTP service, sampling chain or model
state was instantiated. Parsed tool/media output remains explicitly unsupported.

## Results and preserved versions

All1,645 newly rendered canonical strings match the saved N0 Jinja2 prompt bytes.
Those corpus prompts were not retokenized and N0 was not rerun. Four frozen
natural episodes' supplied assistant token IDs plus synthetic EOG pass the
component bridge and reproduce their supplied canonical next prompt. This is
provided-history compatibility, not free-generation or native-head evidence.

The final23 synthetic boundary controls contain12 positive passes and11 expected
rejections. They include all six actual EOG IDs, EOG at cap1, valid cap1/cap128,
empty-think output, special-token text handling, invalid IDs and incompatible
stops. The deliberately invalid UTF8 cap case preserves raw byte F0 as hex:
actual parser state stays empty, the actual final-response fallback retains F0,
and actual safe JSON transport produces U+FFFD; the next actual tokenizer emits
replacement token5691. No replacement/drop rule was invented in this adapter.

Earlier evidence is retained: epoch02's23-control panel was11 passes,11 expected
rejections and1 wrapper block from strict JSON serialization. That was not an
observed server failure. Epoch04 exercised task parsing/safe JSON but omitted the
actual final-message fallback; its raw output is retained as an incomplete
engineering version. Final epoch06 adds the actual formatter. Compiler/link
failures from unsupported wrapper ABI assumptions and missing server helper
objects are retained; upstream source, old baselines and N0 were not edited.

Stop semantics were source audited rather than model executed. n_gen increments
before process_token; UTF8 continuation is set before the finite-budget check,
which still stops at n_predict. EOG then overrides the limit reason at a shared
boundary. This supports strict EOG/cap under the stated profile, sufficient
capacity and no text/time/indent stop. Full sampler/finite-argmax, context-capacity,
placement and resident lifecycle equivalence remain native admission gates.

Total CPU work across all retained versions:4 native-tool invocations and4
vocabulary-only model objects;324 tokenizer,1,615 token-piece,47 parser and1,773
renderer calls. Zero model contexts, tensor loads, forwards, GPU requests and
placements. See CPU_ACCOUNTING.json for build/hash/tool times. These counts include
intermediate work and expected failures, not just final successes.

## Evidence and reproduction

SOURCE_BINDING.json binds948 complete cached source files, selected exact source
fragments, historical build attempts, the final helper source/ELF hashes and
actual command flags. Full-file hashes differ from fragment hashes. source_excerpts/
contains exact byte fragments with one-based inclusive positions and pinned
source links. The model and ELF are not distributed. Paths in public logs are
redacted with placeholders; original private logs and hashes remain retained.

RAW_EVIDENCE_INDEX.json describes the public-safe evidence bundle, including all
four raw CPU input/output versions, receipts and redacted build/runtime logs. The
parent archive supplies its final public location. Verify saved evidence with:

    node producer/verify_producer.js EXPORTED_EVIDENCE_DIRECTORY

This performs no new tokenization or native invocation. The actual direct CMake
library build and g++ object/link recipe was executed. build_cpu_bridge.py
prepares the same operations in a fresh directory and verifies the bound source
files. The convenience CMakeLists.txt also includes the three actual server
translation units and section garbage collection; this alternative helper target
was prepared but not independently rebuilt. Neither builder runs a model.

The CPU pass does not qualify a sequential C4096 R, native append/trim/reset,
complete vectors, active KV/frontier, pending ownership or numerical equivalence.
It does not authorize N1/N2 GPU execution or establish a performance opportunity.

