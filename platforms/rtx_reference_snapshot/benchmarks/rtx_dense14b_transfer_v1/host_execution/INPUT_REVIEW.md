# Prospective natural-input review, 2026-11-01

No14B generation has occurred at this review. Candidate pool: first1000 test
records of codeparrot/apps at21e74ddf8de1a21436da12e3e653065c5213e9d1 and all
seven test partitions of EleutherAI/hendrycks_math at
21a5633873b6a120296cce3e2df9d5550074f4a3. Exact source downloads, hashes and
row identifiers are retained in D:/rtx155/preparation. Both dataset cards identify
MIT licensing. No solution fields are included in any prompt.

Full source problem statements are rendered with the inherited Qwen template,
thinking disabled, and a fixed domain instruction. Actual natural text is not
padded, truncated, concatenated with other tasks or replaced after observing
outputs. Source-text hashes normalize only surrounding whitespace; prompts retain
the source text itself. Length eligibility yields code283 short/337 long and
math656 short/16 long candidates. The registered deterministic SHA ordering
selects three per cell after the exposure exclusions.

The selected twelve statements were read in full. They are natural benchmark
tasks, with the following limitations retained rather than edited away:
APPS/test/858 refers to a previous subtask, APPS/test/931 contains an original
image placeholder plus a text explanation of mirroring, and the selected MATH
items contain their original Asymptote diagram source. Thus mathematical prompt
length includes diagram code. This study tests deployment reference preservation,
not answer correctness or pure prose-only reasoning. These characteristics must
be disclosed in the result and do not justify output-driven substitution.

Exposure scan inspected402 unique Git input/plan/contract/manifest blobs across
available branch/tag heads and17329 successfully parsed retained manifests,
collecting10381 IDs,831 text hashes and556 token-array hashes. Twenty-one parser
refusals were inspected byte-for-byte:20 explicit CPU-only fixture sentinels and
one one-byte newline remote placeholder. Their original failure list and exact
contents/hashes remain in the review receipt. No real input manifest was waived.
All selected input IDs, normalized source-text hashes and token hashes are
disjoint from that inventory and from the four already-exposed pilot inputs.
This is project exposure exclusion, not a claim about pretraining contamination.

The14B tokenizer reproduces all12 old Qwen formatted strings and token arrays
exactly. Its rendered template hash equals both the historical contract and the
actual14B GGUF template hash57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361.
No native inference is used in input preparation.
