# M4 runtime-control preflight and recovered contract

Status: **Formal measurement and post-measurement provenance audit complete.** R0 timing remains non-formal. See `FORMAL_REPORT.md` and `FORMAL_ANALYSIS.json` for results and the recorded freeze-hash defect.

## Repository and machine

- Audited `main` base: `b80bdbc67f6e19829245ad732390cd6aef941675` (the handoff SHA; fetched and fast-forwarded on 2026-09-24).
- Study branch: `runtime/m4-profitability-control-v0.1`.
- Local machine: MacBook Air `Mac16,13`, Apple M4, 10 cores, 24 GB RAM; macOS 27.0 build 26A428. At preflight it was on 65 W AC power, charging, and Low Power Mode was off.
- Python: system 3.9.6; M4 environment 3.11.15.
- Installed llama.cpp: version 0.4.0, build 10809, source commit `5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, AppleClang 21.0.0.21000101.
- Target: `Qwen3-8B-Q8_0.gguf`, SHA-256 `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`.
- Draft: `Qwen3-0.6B-Q8_0.gguf`, SHA-256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
- Both local GGUF hashes match `artifacts/m4_humaneval_code_conditioned/manifest.json`.

## Historical authority

- `benchmarks/m4_code_conditioned_30q/preregistration.json`: HumanEval prompt IDs, exact condition flags, cap, and repetitions.
- `benchmarks/m4_confirmatory_24q/selection.json` and `benchmarks/root_cause_12q/selection.json`: prior Spec-Bench IDs.
- `scripts/m4_humaneval_code_conditioned.py` and `scripts/m4_llama_metal_12q.py`: actual CLI invocation, timing extraction, output extraction, and comparator.
- `artifacts/m4_humaneval_code_conditioned/results.json` and `work/m4/llama_confirmatory_24q.json`: authoritative historical run records.
- `artifacts/m4_humaneval_code_conditioned/manifest.json`: archived hashes and original software environment.
- llama.cpp commit `5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, especially `common/speculative.cpp`, `tools/cli/cli-context.cpp`, and `tools/server/server-context.cpp`: backend mechanism.

## Recovered execution semantics

The HumanEval runner passed each formatted task as a file to `llama-cli --single-turn --simple-io --no-display-prompt`. The CLI sends that file content as one **user** message to its embedded server's `/v1/chat/completions` endpoint. Chat formatting is Qwen's installed GGUF template with `{"enable_thinking":false}`. There is no separate historical tokenizer/config file: tokenization and template metadata come from the GGUF, so the model hashes are the configuration anchor.

Both models use Metal `MTL0`, all GPU layers, target greedy sampling (`--temp 0 --top-k 0 --top-p 1 --min-p 0 --seed 123`), batch size one, and `draft-simple` with `--spec-draft-n-max 2 --spec-draft-n-min 0`. Draft simple samples its own top candidate with a top-10 draft sampler, checks vocabulary compatibility, and supplies up to two proposed tokens to the server. The server verifies the proposal with target logits; `common_sampler_sample_and_accept_n` yields accepted tokens plus one target token (correction on rejection or bonus on full acceptance). The server removes uncommitted target KV positions; when its memory backend requires it, it restores a checkpoint and replays. The draft implementation discards speculative suffix state before subsequent rounds. These details are taken from the pinned llama.cpp sources, not inferred from speed summaries.

HumanEval uses a 128 generated-token cap; the older representative Spec-Bench campaign uses a 64-token cap. Generation stops on the server's end-of-generation token, the cap, or its normal chat stop handling. The old primary latency is the server's `eval time` (`server_slot_stats::t_gen_ms`), which excludes model load and prompt evaluation. The new guard must account for every synchronous policy action within this post-prefill generation window. Three repetitions per prompt and randomized condition order were used historically; the new schedule requires its own independent freeze.

**Comparator limitation:** the old Python runner parsed CLI text and called `llama-tokenize` on that text. Its saved `tokens` are **not direct generated token IDs** and, for HumanEval, the parsed text includes the prompt. For example, the first stored baseline has 214 re-tokenized IDs while llama.cpp reports 116 generated tokens. The historical 90/90 and 72/72 claims are preserved as reported text-path equality evidence, but they cannot by themselves establish the stricter direct token-ID contract required here. The new runner must request or instrument direct generated IDs and pass fresh exactness qualification before any performance claim.

## Leakage preflight

`WORKLOAD_INVENTORY.json` scans tracked M4 raw records, summaries, preregistrations, and the local ignored `work/m4` directory. It conservatively excludes 36 of 480 Spec-Bench questions and 30 of 164 HumanEval tasks. Remaining untouched candidates: 444 Spec-Bench and 134 HumanEval. This suffices for a prospective calibration, qualification, and held-out split selected solely by fixed ID hashes. A final independent audit of any other local run directories is required before freezing the split.

## R0 feasibility evidence

The pinned `draft-simple` common library is linked by `scripts/platform/m4_runtime/runtime_runner.cpp`. The runner emits direct generated token IDs, the per-round draft and verifier trace, realized cost, one-way fallback, and control costs. A context-capability probe in llama.cpp clears the KV state; R0 found and fixed an initial misuse by moving that probe before prompt prefill. The corrected runner matched a fresh llama-server direct-ID reference for a previously exposed HumanEval prompt under target-only, fixed k=2, and guard with and without fallback. At the 128-token cap, all conditions matched the target-only 122-ID EOS output. R0 traces include full acceptance, rejection of each of two proposed positions, correction, bonus, early fallback at round 2, late fallback at round 8, cap, EOS, repeat/reset, and nonzero measured guard and transition work. These checks are in ignored `runs/m4/runtime_profitability_control_20260924/r0/` and validated by `validate_r0_traces.py`.

The prompt-token file `PROMPT_TOKENS.json` was generated through pinned llama-server `/apply-template` and `/tokenize` with thinking disabled. It contains 116 outcome-blind prospective tasks; the longest formatted input is 1,500 tokens, below the 2,048-token runtime context after the 128-token output cap. R0 uses only historically exposed HumanEval/89. The qualification and held-out outcomes were unseen before their reserved stages began.

## Completed study and provenance exception

The completed attempt `unattended-20260924t125921z` recorded 240 baseline, 1,080 candidate, 144 qualification, and 540 formal observations. Calibration froze `E8_M000`; qualification passed 48/48 direct-ID pairs for each speculative condition. The formal run began from clean commit `202109717754bc62f889d19b5fbb141bfc3cc529` and produced 180/180 direct-ID pairs for each speculative condition, with no mismatches. The prompt-level geometric mean target/guard speedup is 1.3114 (95% prompt bootstrap interval 1.2487–1.3787). Energy is not claimed.

The original pipeline stopped at analysis because the frozen `frozen()` function returned the build-manifest path after a loop variable shadowed the calibration-freeze path. Qualification and formal-start records therefore contain the build-manifest SHA-256 where the freeze SHA-256 was intended. Raw observations and original markers were retained without modification. The versioned recovery analyzer independently verified the actual freeze file against the clean formal-start commit, rechecked source/model/calibration/policy hashes and complete attempts, and used the original frozen analysis formulas. The report discloses this metadata exception; the original pipeline status remains `STOPPED` for auditability.
