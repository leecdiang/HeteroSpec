# Pre-forward input-source amendment, 2026-10-28

The first static census used the local HumanEval and sanitized MBPP corpora.
With conservative project-wide ID/normalized-text exclusion it yielded zero
eligible short and long candidates. This does **not** establish that every task
was run on the current Qwen implementation: ambiguous and other-platform mentions
were deliberately also excluded. The original census and STOP receipt are kept.
There have been zero new model forwards or GPU qualification requests.

Before selecting a panel, add the original, human-written GSM8K train and test
questions from [openai/grade-school-math](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data),
commit `3101c7d5072418e28b9008a6636bde82a006892c`. This uses neither Socratic
rewrites nor generated example solutions. Dataset answers do not enter prompts,
ranking, eligibility, or experiment analysis. The study concerns numerical
reference preservation, not held-out mathematical accuracy or training novelty.

Candidate IDs are `GSM8K/train/<zero-based-row>` and `GSM8K/test/<zero-based-row>`;
the immutable source file SHA256 and exact question bytes accompany every ID.
Use the unchanged native Qwen wrapper with the literal user prefix
`Solve the following math problem. Give a concise solution and the final answer.`
followed by two newlines and the complete original question. Never truncate,
concatenate or repeat questions. Tokenize with the pinned vocabulary-only native
tool; no model context or forward is used. Run the same conservative accessible
history scan against IDs and normalized question text, with exhaustive source
corpora/zero-forward tokenization inventories treated as availability only.

After that scan, rank the union of eligible candidates by the existing canonical
SHA256 of `{study,id,source}` and take the first four in each unchanged length
band, 64–192 and 256–352. Domain remains descriptive. If fewer than four exist
in either band, stop again before forwards. Do not select using any new output.

The two historical controls, independent strict R, P1/P4T recipes, 32+120=152
primary budget, cap64/cap128, native dependencies, B0 gate, no-retry rule,
clean-receiver scope and exclusion of performance claims are unchanged.

## Static length follow-up, still before any forward

Native tokenization of all 8,792 original GSM8K questions produced **zero**
256–352-token candidates under the exact wrapper. Its interrupted exposure scan
does not produce a qualified panel; its tokenization and STOP receipts remain.
Add the 500 original `problem` fields in
[HuggingFaceH4/MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500/tree/6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be),
revision `6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be`, `test.jsonl` SHA256
`35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132`.
Use `MATH500/` followed by the original `unique_id`, the same math prefix, and
the complete original problem string, including any original Asymptote notation.
Solutions, levels and expected answers are not selection features. This is a
text input preservation experiment, not a claim of mathematical/diagram accuracy.

The final pool is the union of HumanEval, sanitized MBPP, GSM8K and MATH-500.
Exclude duplicate native token sequences before ranking. Apply the unchanged
hash rule and historical-exposure policy to the full union. If this final pool
still cannot fill either band, stop without extending it further in this attempt.
These source amendments respond only to static availability and token lengths;
they use no new model outputs, qualification results or performance observations.

The initial scan also found six copies of two historical 22/23-byte failed ZIP
transfers. Adjacent immutable failure receipts identify transport truncation,
not usable archives. The amended scanner accepts this classification only when
the adjacent receipt says TRANSPORT_FAILED and its exact received/partial byte
count matches; it hashes both the fragment and receipt and retains the paths.
Other unreadable archives still block selection. This does not assert recovery
of missing bytes or access to unavailable other-machine history.
