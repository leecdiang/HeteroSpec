# RTX implementation amendments

These are scoped adaptations of the forwarded PR121 protocol. No historical run,
DLL, arithmetic, reference tolerance or fixed geometry was changed.

- Native collector is new. H0 is **legacy-style**, retaining PR120's per-call
  STARTED JSON, ordinary allocation/readback and output-file writes with the same
  QPC boundary. The final per-call summary JSON array is constructed after replay
  for both methods, so this is not a bit-identical old observer binary. The delta
  was declared in IMPLEMENTATION.json before GPU qualification. H0 anchor data
  belong only to this newly qualified cohort, never pooled with PR120 timings.
- H1 preallocates every output occurrence and fixed native tick/status slots.
  Readback and byte/finite checking remain per call. This does not claim an
  observer-free measurement. Output-array allocation is separately timed; fixed
  bookkeeping allocation is included in complete host wall even when unpartitioned.
- CPU-only exporter additionally reports actual session IDs in host summaries.
  Its repaired transport/schema does not change any numerical eligibility rule,
  input/output byte, QPC boundary or GPU call. The original pilot export is retained.
- Factor helper, registered before confirmation, shows both value-mode/cycle
  directions and alternate-QB/A/A sensitivity. Its extra 2%+A/A edge screen is
  exploratory and descriptive; no calibrated multiple-comparison claim.
- Optional six-feature ridge rule source was added during B0 acquisition before
  inspecting its costs. It will fit once after complete B0 and freeze coefficients,
  every optional prediction and measured CPU feature/lookup cost BEFORE opening
  any holdout input/reference output. It is not claimed preregistered before B0.
  No retuning on holdout; its charged phase-sum is not a deployed selector.
- Offline build receipt naming collision, wrong git working-directory freeze
  refusal and a CPU test's ambiguous fixture selection are retained. Final CPU
  tests select the reference/candidate stages explicitly. None caused a GPU retry.
- CAS uses verified hardlinks with unchanged ordinary-file fallback at the NTFS
  ceiling. Complete occurrence bytes remain recoverable. Raw telemetry stays local
  under CONTRIBUTING; exact local fresh restore is not remote raw authentication
  or external independent review.

- Input-inclusive native data condition on already formatted snapshots. A separate
  CPU-only followup (at most128 processes,1warmup+64preparations each) measures
  optimized C++ Q copy/permutation, fullKV copies and actual mask construction
  from a common logicalQ source. It will run only outside GPU timing. Its mean
  can replace the preformatted CPU-copy component in a separately labeled phase
  sum; it is not integrated GPU wall time and does not overwrite the original
  view. Fixed target buffers/cold allocation and all byte checks are explicit.
- Final CPU audit strengthens identity reconstruction: all consumed source,
  frozen input/reference bytes, serial query/mask/fullKV derivation and serial
  concatenation are checked. Successful outputs cannot override a lifecycle error.
  These are postcollection verification checks, not changed numerical tolerance.

- Compact execution artifacts are exported with per-file `-text` attributes so
  Git preserves their original exact bytes, including CRLF. The live UUID freeze,
  method/prediction and all runtime files remain unchanged. Earlier Git-normalized
  representations remain in history; EXACT_ARTIFACTS.json names the actual byte
  hashes. Ordinary code remains conventional LF Git text; exact consumed source
  bytes are separately retained under raw/SOURCE and verified by the CPU audit.
