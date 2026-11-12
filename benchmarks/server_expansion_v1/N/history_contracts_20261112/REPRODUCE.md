# Saved-data reproduction: CPU only

Requirements: Node18+ and Python3.9+ for the inherited strict UTF8 archive helper.
No llama binary, weights, GPU, tokenizer or model context is needed. Use fresh
output paths; scripts refuse existing comparison/check outputs. These commands
reconstruct new CPU predictions, **not the old N0 census execution**.

1. Download this successor directory at the immutable commit recorded by
   PUBLIC_READBACK.json. Fetch HISTORY_TEXT_PACKET.tar.gz and verify against
   PACKET.json's full SHA256 and byte count. PACKET.json also pins the unchanged
   original N0_TEXT_PACKET.tar.gz at PR224 head8be5f9a. Obtain that original packet
   and verify its SHA256
   `7c5768f77ccbcf0521d4508324db3b4f87b6f7ed5d8f896f8a681eb0c2a75f8e`
   and11,059,974 bytes. Its licensed source/tokenizer text is the required input.
   Its separate parquet companion is not required by this successor's saved-ID
   checker; reconstructing the original parquet conversion is a different action.
2. Use the unchanged PR224 packaging/archive.py and support.py, pinned by this
   packet's packaging provenance. Strict replay checks the complete archive hash,
   safe member names/types/uniqueness, exact INDEX coverage and every member's
   bytes/SHA before writing. No native context or numeric revalidation occurs.

```sh
python3 -B packaging/archive.py replay --archive N0_TEXT_PACKET.tar.gz \
  --sha256 7c5768f77ccbcf0521d4508324db3b4f87b6f7ed5d8f896f8a681eb0c2a75f8e \
  --out "$NEW_N0_RESTORE"
python3 -B packaging/archive.py replay --archive HISTORY_TEXT_PACKET.tar.gz \
  --sha256 "$HISTORY_PACKET_SHA256" --out "$NEW_HISTORY_RESTORE"
node "$NEW_HISTORY_RESTORE/test_contracts.js"
node "$NEW_HISTORY_RESTORE/evidence/verify_audit.js"
node "$NEW_HISTORY_RESTORE/independent/independentcheck.js" \
  "$NEW_HISTORY_RESTORE" "$NEW_N0_RESTORE" "$NEW_INDEPENDENT_CHECK"
node "$NEW_HISTORY_RESTORE/compare_contracts.js" \
  "$NEW_N0_RESTORE" "$NEW_COMPARISON_OUTPUT"
```

`NEW_HISTORY_RESTORE/COMPARISON_01/` contains all four original successor output
files. Compare SHA256/bytes of newly generated FREEZE,REPORT,PER_ROOT and
TURN_COMPARISON against those immutable files. No absolute paths enter these
results. The independent checker uses raw message ancestry and saved native
tokenizer IDs with its own geometry and no imports from the experiment. The final
portable checker passes118,207 checks; its prior118,219-check local variant also
snapshotted12 irrelevant local documents, which were removed from the input
contract without removing any semantic/math checks. Earlier private reports remain.

The independent report and per-turn raw replay have exact identities in INDEX.
Native full vectors/KV captures do not exist; a zero withheld-native-payload count
does not mean GPU qualification passed. The audit verifier rechecks delivered
excerpt bytes and recorded build-identity equality; it cannot reconstruct all full
source files or rehash ELF/weight bytes that are not included.

For provenance, upstream fragments are from the pinned source named in
evidence/SOURCE_AUDIT.json, with exact line ranges, full-source hashes and excerpt
hashes. Original OASST1 is `OpenAssistant/oasst1` revision
`fdf72ae0827c1cda404aff25b6603abec9e3399b`, validation-of-ready partition.
licenses/OASST1_CARD.md and OASST1_LICENSE.txt preserve attribution and CC-BY-4.0
license; new predictions are derived from its saved tokens, not private company
conversations. licenses/LLAMA_CPP_LICENSE.txt covers the pinned upstream snippets.
Model and binary hashes are identities only; no model weights or executable is
redistributed. Source/serializer/config updates need new epochs and requalification.
