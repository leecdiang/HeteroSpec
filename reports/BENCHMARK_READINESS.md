# Formal Benchmark Readiness

## Decision

**READY FOR A RESTARTED PHASE 4 SPECBENCH PILOT WITH A 128-TOKEN SAFETY CAP.**

The original 512-token pilot is permanently paused after a repeatable near-capacity-VRAM `HYPERVISOR_ERROR`. A fresh 60-question pilot may be started with a 128-token per-turn cap. The 420-question holdout remains sealed until the pilot selects and freezes `k` according to the experiment plan.

## Final correctness gate

The original BF16/cuDNN target runtime was shape-sensitive on natural chat prompts: candidate-block verification and single-token greedy decoding diverged at a near-tied logit. A margin-only guard delayed but did not eliminate the effect because batched KV states can carry small numerical differences forward.

The qualified correctness runtime is therefore:

- Target weights: unchanged Qwen3-8B bitsandbytes NF4 with double quantization
- Target compute dtype: FP32
- Target attention: eager
- Draft: Qwen3-0.6B symmetric INT4 OpenVINO on explicit CPU
- Decoding: greedy, shared target-tokenizer IDs, Qwen chat template with thinking disabled

With this runtime, the required 20-prompt Gate C passed:

- Natural prompts: 20
- Coverage: English, Chinese, German translation, summarization, QA, arithmetic, code, JSON, punctuation, mixed text, creative and safety prompts
- Candidate size: k=4
- Maximum output: 64 tokens with EOS-aware stopping
- Exact token equality: 20/20
- Peak CUDA allocation: 8.323 GiB

Because the target runtime changed, earlier BF16/cuDNN target timing is retained as diagnostic history but is not used as the formal paired baseline. Every formal pilot question runs a new FP32/eager B0 baseline in the same randomized block as its speculative configurations.

## Benchmark dry run

- Prompts: 6
- Configurations per prompt: B0 plus k=1,2,4,6,8
- Runs: 36/36
- Complete paired blocks: 6/6
- Speculative outputs exactly matching B0: 30/30
- Unique block orders: 6/6
- Randomization seed: 20260903
- NVML rows: 100
- NVML errors: 0
- Peak NVML power: 118.8 W
- Peak temperature: 83 °C
- Peak NVML VRAM: 9088.1 MB
- Maximum memory clock: 14001 MHz

Dry-run geometric speedups were 0.65, 0.59, 0.49, 0.41, and 0.33 for k=1,2,4,6,8 respectively. These six custom prompts are not the Spec-Bench pilot and cannot select `k`; they are an advance warning that this heterogeneous implementation may yield a scientifically useful negative result.

## Official dataset and split

- Source: official `hemingkx/Spec-Bench` repository
- Frozen repository commit: `fd2c1cd7d2201ef71db4c5f4e455008f017967bf`
- Questions: 480
- Dataset SHA-256: `7DD26882F31ADA100C2AA7447019B5349BDDC55697021ACBC5643FDC8740AA21`
- Split seed: 20260903
- Pilot: 60 questions, 10 from each of six official task groups
- Holdout: 420 questions, 70 from each task group
- Pilot/holdout overlap: none
- Pilot split SHA-256: `52ACDB33AB70A0875934157DBD770765FE07B409E1C432693294C4A0F8036AC6`
- Holdout split SHA-256: `6FE4B6E4C73A9BE215DF3B13C263AC4C3174D75C92391621A97192918AF20CA6`

The 60-question pilot contains 70 user turns. Before generated history is included, the largest tokenized input is 1456 tokens and the 95th percentile is 791. The formal harness preserves natural context lengths and includes a 1024 MiB pre-run VRAM headroom abort guard.

## Official-harness canary

The maintained Phase 4 harness successfully ran one official pilot question through all six randomized configurations with a shortened 16-token cap:

- Question records: 1/1
- Configurations: 6/6
- Correctness: PASS
- Native multi-turn history support: enabled
- NVML 1 Hz logging: enabled
- Per-turn run IDs and hashes: enabled

## Launch artifact

Formal pilot harness:

`scripts\phase4_specbench_pilot.py`

The amended formal launch uses `--limit 60 --max-new-tokens 128` and a new output file; the crash-tainted 512-token session is not resumed. It will generate paired B0/k=1/2/4/6/8 observations, preserve per-turn records, stop on the first correctness mismatch or VRAM guard failure, and write a 1 Hz NVML trace.

## Safety amendment and prior-failure canary

The 512-token output cap allowed a multi-turn speculative configuration to grow to approximately 12.17 GiB VRAM and reproduce `HYPERVISOR_ERROR (0x20001)`. After releasing the candidate KV cache before any canonical precision-guard recomputation, two bounded checks passed:

- Synthetic worst observed initial input: context 1456, output 128, k=8, exact match, PyTorch peak 9.460 GiB.
- Prior crash question 93: both turns, B0 versus k=8, exact match; PyTorch k=8 peaks 8.511/8.811 GiB and NVML peak 9904.1 MB.

This is a safety-driven protocol amendment, not a performance optimization. It changes the maximum response length and therefore the old 11/60 partial results are retained only as incident evidence, not merged into the restarted pilot.

A subsequent three-question canary exercised all six configurations (18 paired blocks) without failure. All speculative outputs matched B0 exactly; peak PyTorch allocation was 8.498 GiB, peak NVML usage was 9420.1 MB, and the maximum sampled temperature was 85 C. The replacement 60-question pilot was then launched as a new session on 2026-09-06.

## Evidence

- Gate C: `logs\phase3-gate-c-20prompts-fp32-eager-20260905.json`
- Dry run: `logs\phase4-benchmark-dry-run-20260905.json`
- Dry-run telemetry: `telemetry\phase4_dry_run_nvml_20260905T232317.csv`
- Official canary: `logs\phase4-specbench-official-canary-20260905.json`
- Prior-failure canary: `logs\phase4-q93-cap128-canary-20260906.json`
- Three-question all-configuration canary: `logs\phase4-specbench-cap128-batch3-canary-20260906.json`
- Restarted formal pilot: `logs\phase4-specbench-pilot-cap128-formal-20260906.json`
- Pilot IDs: `env\specbench_pilot_ids.json`
- Holdout IDs: `env\specbench_holdout_ids.json`
