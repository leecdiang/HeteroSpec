# CPU saved-data reproduction

Use fresh output directories and the immutable packet identities in PACKET.json.
Python3.9+ runs the unchanged strict archive helper; Node18+ runs pure CPU checks.
No model, tokenizer, GPU or native invocation is needed for saved-data replay.

Restore three packets: this N1A_CPU_TEXT_PACKET, the unchanged PR225
HISTORY_TEXT_PACKET (SHA256 adddad50aadc98e2e0100a35e3a57a16449ef90e80198bd88663a30dc99eae65,
1232228 bytes), and PR224 N0_TEXT_PACKET (SHA256
7c5768f77ccbcf0521d4508324db3b4f87b6f7ed5d8f896f8a681eb0c2a75f8e,
11059974 bytes). Strict archive replay verifies the whole transport hash, safe
regular/unique members, exact INDEX coverage and all member bytes before writing.
The old parquet companion is not needed by these saved-token checks.

```sh
python3 -B packaging/archive.py replay --archive N1A_CPU_TEXT_PACKET.tar.gz \
  --sha256 "$N1A_PACKET_SHA" --out "$N1A_RESTORE"
python3 -B packaging/archive.py replay --archive HISTORY_TEXT_PACKET.tar.gz \
  --sha256 adddad50aadc98e2e0100a35e3a57a16449ef90e80198bd88663a30dc99eae65 \
  --out "$PR225_RESTORE"
python3 -B packaging/archive.py replay --archive N0_TEXT_PACKET.tar.gz \
  --sha256 7c5768f77ccbcf0521d4508324db3b4f87b6f7ed5d8f896f8a681eb0c2a75f8e \
  --out "$N0_RESTORE"
node "$N1A_RESTORE/test_contracts.js"
node "$N1A_RESTORE/independent/test_token_contracts.js"
node --test "$N1A_RESTORE"/plan/test_*.js
node "$N1A_RESTORE/independent/independentcheck.js" \
  "$PR225_RESTORE" "$N0_RESTORE" "$NEW_INDEPENDENT_CHECK"
node "$N1A_RESTORE/compare_contracts.js" "$N0_RESTORE" "$NEW_COMPARISON"
node "$N1A_RESTORE/freeze_episodes.js" \
  "$N0_RESTORE" "$PR225_RESTORE/COMPARISON_01" "$NEW_EPISODES"
node "$N1A_RESTORE/producer/verify_producer.js" "$N1A_RESTORE/producer_evidence"
node "$N1A_RESTORE/plan/manifest.js" validate \
  "$N1A_RESTORE/N1A_PROPOSAL_NOT_ADMITTED.json"
```

Compare all four regenerated comparison artifacts with
PR225_RESTORE/COMPARISON_01 byte-for-byte, and all four episode files with the
delivered episodes/. The new checker uses its sibling independent helpers; do
not substitute the frozen old checker. Independent review scripts bind their
explicit input files/plan directory; their CLI headers and review evidence specify
the arguments. The final review03 supersedes earlier coarse-row/missing-coverage
wording; all intermediate private reports remain retained.

producer_evidence/ contains all four real CPU input/output/receipt versions and
public-safe logs; RAW_EVIDENCE_INDEX distinguishes raw identities and redacted
private-stat/path fields. verify_producer checks saved outputs/hashes/fixtures,
not a new invocation of upstream parser/tokenizer. Empty UTF8 fallback bytes are
preserved as hex before the actual safe JSON replacement; no invalid text is
silently repaired by packaging. There are no native logits/KV captures to restore.

For an **optional separate CPU rebuild**, producer/README and build_cpu_bridge.py
pin the exact upstream source set, model/vocabulary hash, compiler/flags and actual
manual recipe. Use at most2 compile jobs, fresh directories and CPU-only backends.
The build helper itself reads no model. Re-executing producer_bridge requires the
exact GGUF as a vocabulary-only object and the frozen fixture inputs; it must not
create llama_context, load model tensors or run forward. Its explicit vocabulary
execution costs differ from this saved-data replay. The model and ELF are not
distributed; the convenience CMake helper target was prepared, not separately
rebuilt. No source or dependency may be silently upgraded to make a test pass.

Raw-state replay tools operate on supplied actual files only and never start a
model. A matching byte comparison or261-check supplied-record coverage report
does not prove native provenance or execution. `--require-admission` always
rejects in this preparation. NativeR/writer/adapter, resource/window approval and
finite GPU allowance remain separate gates. No N1a/N1b/N2 GPU step is authorized
by a successful CPU command.

Attribution: exact OASST1 validation-of-ready revision
fdf72ae0827c1cda404aff25b6603abec9e3399b and CC-BY-4.0 card/license are in licenses/;
upstream code excerpts carry the pinned ggml/llama.cpp MIT notice. The raw source
corpus and model identities are inherited unchanged. No company conversation,
credential, GPU UUID or unrelated user/job information belongs in the public packet.
