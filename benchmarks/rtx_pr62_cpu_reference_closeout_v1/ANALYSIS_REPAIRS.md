# Retained CPU implementation repairs

The first independent parser invocation rejected its own additional assumption that response.tokens_cached must be zero. Read-only inspection of all384 records found timings.cache_n=0, while tokens_cached ranges53–175. Frozen server-context.cpp:2126 assigns the latter from the final slot.prompt.n_tokens(); it is not the cache-hit field. The parser now checks the original timings.cache_n contract and separately retains valid final-slot occupancy. No old input/output/cost was changed, no records were excluded, and no model ran. This is an implementation correction, not an outcome-dependent qualification change.

Other preparation events: schema reader found NumPy absent in system Python; bundled Python lacked Matplotlib. Analysis libraries were installed only into a new work/rtx-cpu-python-deps directory. See protocol amendment for the historical bootstrap seed clarification before comparison reads.

The first independent verifier completed its raw/cost checks but its string-based import guard matched the guard's own forbidden text. Replaced that source scan with AST import inspection. Data, aggregation and negative fixtures were unchanged; no model was run.

The first public whitelist copy stopped on its own source's example path patterns before sealing, figures or publication. The privacy check now applies to data/reports, and an explicitly checked partial new staging directory can resume. No commit/PR had been published. Study-local Git attributes preserve exact bytes (including CSV CRLF) rather than normalizing archived CPU exports. The earlier unsealed staging warnings and failed copy are retained here; no old records or results changed.
