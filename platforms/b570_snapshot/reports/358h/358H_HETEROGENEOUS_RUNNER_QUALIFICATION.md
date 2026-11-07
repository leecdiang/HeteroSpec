# 358H heterogeneous runner qualification

## Result

**PASS.** The custom heterogeneous runner is qualified for the already-frozen Phase-3 protocol. No formal HumanEval Phase-3 data were generated.

## Architecture

- Target: pinned llama.cpp b10839 (`0cae43063cf15170e91a2ff4d034da0ecef4a1b2`) loaded through its C API by Python `ctypes`; Qwen3-8B Q8_0; explicit Vulkan0; persistent target KV with suffix removal after rejection.
- CPU draft: frozen Qwen3-0.6B OpenVINO symmetric INT4 IR on explicit CPU.
- NPU draft: the byte-identical IR on explicit NPU with the already-qualified cache.
- Draft state: complete committed-prefix replay for every proposal on both devices. Replay is inside `draft_time` and must remain inside future end-to-end timing.
- Algorithm: greedy k=2, ordered matching prefix, first-mismatch target correction, target bonus after complete acceptance, 128-token cap for future formal runs.

## Pinned source semantics

The mapping in `358H_RUNNER_SEMANTICS_MAPPING.md` was derived from the exact pinned `examples/speculative-simple/speculative-simple.cpp` and `common/speculative.cpp`, not from memory.

The native llama.cpp reference trace and the custom historical-GGUF adapter produced the same eight target tokens. Both native and custom traces used the same draft rounds `[0, 5692]` and `[264, 4285]`, accepted both tokens in each round, and applied the same target bonus behavior. The initial and output-boundary target-only tokens also agree.

## State and accounting qualification

Forced target-adapter tests passed for:

- zero draft tokens accepted;
- only d1 accepted;
- d1 and d2 accepted plus target bonus;
- rejection on consecutive rounds;
- reset and exact repeat.

Every call asserted target KV maximum position against prompt plus committed history. There was no state drift. Proposed tokens, accepted draft tokens, correction/bonus tokens and committed progress C reconcile in every round.

## CPU bridge

- Two independent reset/replay executions: token-exact with paired target-only baseline.
- Proposals and acceptance trace repeated exactly.
- `EXECUTION_DEVICES=[CPU]`.
- Target log: 37/37 layers and 36/36 KV layers on Vulkan0.

## NPU bridge

- Two independent reset/replay executions: token-exact with paired target-only baseline.
- Proposals and acceptance trace repeated exactly and matched CPU on the qualification prompt.
- `EXECUTION_DEVICES=[NPU]`, backed by the frozen cache-binding record and cache SHA256.
- No empty-KV failure because the qualified GenAI static-profile path reconstructs from a non-empty committed prefix.
- No CPU fallback.
- Target log: 37/37 layers and 36/36 KV layers on Vulkan0.

## Instrumentation

The runner records total end-to-end decode time, OpenVINO replay/draft time, target verification time, derived orchestration residual, every proposal, accepted prefix length, correction or bonus, per-round C, target state position, draft logical state length and exact output IDs. Qualification timings are `NON_FORMAL / INVALID_FOR_CLAIMS`.

## Frozen hashes

- Runner: `1d11e42d008f981ee6a91ac7bfeb478f11c060d51e79b9e060fe04ece70153e8`
- Forced-state tests: `628e454cc6362634d75620791de01775f6bcdc7ba6fb721a08d3ff62ae155b96`
- Semantics mapping: `14a20fcacf6f5aab111300ac6936c3c9378423cc04e077118c90c3dfa8569f0b`

`formal_phase3_data_seen_before_runner_freeze = false`

Formal HumanEval was not started.

