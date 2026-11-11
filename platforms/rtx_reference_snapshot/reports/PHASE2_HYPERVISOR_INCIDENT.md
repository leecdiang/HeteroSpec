# Phase 2 Hypervisor Crash Incident

## Status

Phase 2 target-only attempt started on 2026-09-05 and was aborted by a system bugcheck after 20 of 30 run artifacts had been written. None of those artifacts are accepted as formal Phase 2 evidence because the in-process NVML buffer was lost and the Intel trace was not cleanly finalized.

## Bugcheck evidence

- Code: `HYPERVISOR_ERROR (0x20001)`
- Parameters: `0x28, 0x1, 0x29b92701, 0xfc810000`
- WinDbg meaning for parameter 1: internal error in the I/O MMU module
- Failure bucket: `0x20001_28_1_intelppm!HvRequestIdle`
- Stack path: `HvcallInitiateHypercall -> HvlRequestProcessorHalt -> intelppm!HvRequestIdle -> intelppm!PepIdleExecute -> PpmIdleExecuteTransition -> PoIdle -> KiIdleLoop`
- Stack pointer: NMI
- Hyper-V present: yes
- VBS running: yes
- WHEA errors near the crash: none found
- NVIDIA driver was loaded but was not named as the failing module

## Relevant concurrent kernel collectors

The dump module list contains Intel telemetry drivers `sepdrv5.sys`, `sepdal.sys`, and `socwatchdrv.sys`. The crash occurred during a long Unified Telemetry capture using EMON, SocWatch, Level Zero, XPU-OS, and ITT. This establishes correlation, not definitive causation.

## Working diagnosis

The original Intel-collector hypothesis has been falsified as a necessary cause by later reproductions. The stable facts are a long, near-capacity CUDA workload, Hyper-V/VBS I/O remapping, and the same internal I/O-MMU hypervisor failure during a processor idle path. The Qwen CUDA workload passed only the short smoke gate; long 8192-token runs are unsafe on the current platform stack.

## Safety decision

Do not repeat the same long combined collector session. First stop residual Intel collector drivers. The next diagnostic run, if authorized, should be a short 8192-token target workload with NVML only. Intel Package Power should then be reintroduced in short, isolated sessions with the minimum collector set. No BIOS virtualization, VBS, affinity, voltage, clock, or power-limit changes are authorized at this point.

## Second reproduction (NVML only)

The isolated 8192-token diagnostic reproduced the exact same bugcheck without Unified Telemetry collectors loaded in the crash dump:

- Parameters again: `0x28, 0x1, 0x29b92701, 0xfc810000`
- Failure bucket: `0x20001_28_1_nt!KiIdleLoop`
- OS kernel: `10.0.26100.9168`
- No SEP, SEP-DAL, or SocWatch module was present in the second dump
- Pre-crash NVML: GPU utilization 100%, 45–55 W, 57–59 C, approximately 12,170 MiB VRAM used

This falsifies Unified Telemetry as a necessary trigger. The leading hypothesis is near-capacity CUDA memory pressure causing Windows/NVIDIA system-memory fallback and heavy DMA remapping through VBS/IOMMU. A newly published independent AI-workload report shows the same first three parameters, same I/O MMU interpretation, and the same `HvRequestIdle` family of failure, with crashes eliminated by setting NVIDIA's per-application CUDA system-memory fallback policy to Prefer No Sysmem Fallback. This is supporting external evidence, not proof for this machine.

The machine is on Windows 11 25H2 build 26200.9168. Microsoft lists a newer Release Preview build 26200.9267. BIOS G615LR.338 is the current ASUS-listed release at the time of investigation.

## Third reproduction (no sysmem fallback)

On 2026-09-05, NVIDIA App was configured specifically for `.venv-target\Scripts\python.exe`:

- `CUDA - Sysmem Fallback Policy`: `Prefer No Sysmem Fallback`
- Global NVIDIA settings: unchanged
- Intel services `sepdrv5`, `sepdal`, and `socwatchdrv`: stopped before launch
- NVIDIA Overlay: closed
- Workload: one controlled 8192-token / 128-output diagnostic; no Intel telemetry

The system nevertheless reproduced the exact bugcheck for a third time:

- Event time: `2026-09-05 18:33:12 +08:00`
- Dump: `C:\Windows\Minidump\090526-15250-01.dmp`
- Code: `HYPERVISOR_ERROR (0x20001)`
- Parameters: `0x28, 0x1, 0x29b92701, 0xfc810000`
- Pre-crash NVML: approximately `12,175.9 MiB` VRAM, `100%` GPU utilization, roughly `47-53 W`, `67-69 C`

This falsifies Windows CUDA system-memory fallback as a sufficient explanation or mitigation on this machine. The third dump could not be opened non-elevated (`Win32 error 5`), but Windows Error Reporting independently recorded the identical code and all four parameters. No further intentional reproduction is justified.

## Current disposition

Phase 2 is blocked by a reproducible platform-level stability defect under the 8192-token near-VRAM-capacity workload. Do not resume the full matrix on the current configuration. Preserve the per-program no-fallback policy, dumps, event evidence, and streamed NVML traces. Future work must first reduce the workload's peak VRAM below the observed near-capacity regime and validate it with a substantially smaller, bounded canary; changing VBS, virtualization, BIOS tuning, clocks, voltage, affinity, or power limits is outside the authorized experiment scope.

## Bounded recovery canary

A reduced canary completed successfully at `2026-09-05 18:37:57 +08:00`:

- Context/output: `4096 / 32`
- Repetitions/warmups: `1 / 0`
- Intel telemetry drivers: stopped
- NVIDIA system-memory fallback: disabled for the target Python executable
- Result: valid, 32 output tokens, no crash
- Completion: `6401.7 ms`
- PyTorch peak allocated: `11.212 GiB`
- NVML peak used: approximately `12,190.1 MiB`
- Run ID: `p2diag-RTX-c4096-o32-r1-de9143bb`

This establishes only that the reduced canary can complete. It does **not** clear the platform for formal Phase 2: even this run approached the physical VRAM ceiling, so a direct 6144/8192 escalation is unsafe. The runner now explicitly requests PyTorch SDPA and supports configurable diagnostic warmup count plus a pre-run VRAM-headroom guard. A fresh comparison is required before any larger context is attempted.

## Fourth reproduction (GPU memory at default clock)

At the user's request, the original `8192 / 128`, three-warmup diagnostic was repeated after GPU tuning was restored to default. Immediately before launch, NVML reported the memory clock and maximum memory clock both at `14001 MHz`; the prior `14301 MHz` reading was no longer present. Intel telemetry services were stopped, NVIDIA Overlay was closed, and per-program system-memory fallback remained disabled.

The system crashed again:

- Event time: `2026-09-05 18:48:55 +08:00`
- Dump: `C:\Windows\Minidump\090526-15562-01.dmp`
- Code: `HYPERVISOR_ERROR (0x20001)`
- Parameters: `0x13, 0x0, 0x29b92701, 0xffffe80001acfdf0`
- Pre-crash NVML: approximately `12170.1 MiB` used, `100%` GPU utilization, roughly `46-52 W`, `63-64 C`

The first two bugcheck parameters differ from the earlier three reproductions, but the bugcheck family remains `HYPERVISOR_ERROR`. This controlled result excludes the `+300 MHz` memory overclock as a necessary cause. Overclocking may have reduced margin, but restoring default clocks did not resolve the platform failure. No further 8192-token reproductions should be attempted.

## Attention-backend mitigation

PyTorch's Windows wheel reports that Flash Attention was not compiled in. A forced Flash-SDPA 512-token canary therefore failed safely with `RuntimeError: No available kernel`; no fallback result was accepted. Forced cuDNN Attention was supported and produced a large, repeatable reduction in peak memory:

- 4096/32 automatic backend: `11.212 GiB` PyTorch peak, about `12190 MiB` NVML peak
- 4096/32 cuDNN backend: `6.660 GiB` PyTorch peak, about `7488 MiB` NVML peak
- 6144/32 cuDNN: valid, about `8046 MiB` NVML peak
- 8192/32 cuDNN: valid, about `8540 MiB` NVML peak
- 8192/128 cuDNN, zero warmups: valid, about `8550 MiB` NVML peak
- 8192/128 cuDNN, one warmup: valid
- 8192/128 cuDNN, three warmups: valid, about `8550 MiB` NVML peak

The one-warmup and three-warmup 8192/128 measured runs produced the identical output-token SHA-256 `c7508c8461630d8a9e0ac0a7288c419a3da39e18fddabc14d701a9c84c021044`. The final three-warmup session completed without a crash, with 70 NVML samples, 57.4 W average power, 140.8 W sampled maximum, and 83 C maximum temperature.

The evidence now identifies the practical trigger as the high-memory attention path selected under the prior automatic configuration, which drove VRAM to approximately 12.17 GiB and exposed the Hyper-V/VBS/IOMMU platform failure. Explicit cuDNN Attention is the required mitigation for this Windows target configuration. The runner now refuses automatic SDPA for contexts of 4096 tokens or longer.

## Fifth reproduction during Phase 4 FP32/eager pilot

The failure boundary reproduced unintentionally during the official Spec-Bench pilot after the target runtime had been changed to NF4 weights with FP32 compute and eager attention to obtain exact token equality between single-token baseline decoding and batched speculative verification.

- Bugcheck event: `2026-09-06 00:40:29 +08:00`
- Unexpected shutdown recorded for: `2026-09-06 00:24:02 +08:00`
- Code: `HYPERVISOR_ERROR (0x20001)`
- Parameters: `0x28, 0x1, 0x29b92701, 0xfc810000`
- WER report ID: `89cc5ab3-e589-4b10-8a25-9a98b357e5a8`
- Minidump: `C:\Windows\Minidump\090626-15687-01.dmp` (10,173,836 bytes)
- Full dump: `C:\Windows\MEMORY.DMP` (50,872,160,197 bytes)
- Last active run ID: `p4-q93-t1-SPEC-k8-fa1fffce`
- Workload: official question 93, second turn, CPU draft, k=8, RTX target
- Last NVML samples: approximately 12,168-12,170 MiB used, up to 100% GPU utilization
- Segment maximum: 12,212.1 MiB, 88 C
- NVML errors: 0
- Formal pilot progress preserved: 11/60 complete questions

The exact first three bugcheck parameters match the first three reproductions, and the immediate pre-failure memory level matches the earlier approximately 12,170 MiB plateau. This converts the former correlation into a strong reproducible operational boundary across two different attention/runtime configurations: the common factor is near-capacity RTX VRAM use, not the particular automatic SDPA implementation.

The pre-run 1 GiB headroom check was insufficient because it measured memory before generation. The FP32/eager workload could grow by several GiB during a long multi-turn configuration and cross the known failure boundary after the check. The formal pilot must not be resumed with FP32/eager at the 512-token output cap.

The new dump files exist, but non-elevated WinDbg access is denied with Win32 error 5. Windows Error Reporting and the streamed NVML trace are sufficient to identify the repeated signature; dump access can be revisited from an elevated terminal without intentionally reproducing the crash.

## Phase 4 bounded recovery after cache-lifetime fix

The speculative verifier now releases the candidate KV cache and its logits before a canonical precision-guard recomputation. The formal output cap is reduced from 512 to 128 tokens per turn, and the old partial pilot will not be resumed or combined with the replacement session.

Two bounded FP32/eager checks passed without entering the known failure region:

- Context 1456, output 128, k=8: exact token match, PyTorch peak 9.460 GiB.
- Official question 93 (the prior trigger), two turns, B0 and k=8: exact match; NVML peak 9904.1 MB and maximum PyTorch allocation 8.811 GiB.

These checks provide several GiB of observed separation from the approximately 12,170 MiB failure plateau. They do not prove that the underlying Windows/driver/hypervisor defect is fixed; the mitigation is workload containment.

## Persistent G-Helper clock offsets

Before starting the formal cuDNN target matrix, NVML again reported `14301 MHz` memory versus `14001 MHz` maximum. The run was immediately aborted and no artifact was accepted. NVIDIA App automatic tuning was visually confirmed off with a displayed `+0 MHz` GPU adjustment. Read-only inspection of `%USERPROFILE%\AppData\Roaming\GHelper\config.json` found persistent offsets in both stored profiles:

- `gpu_core_0: 100`, `gpu_memory_0: 300`
- `gpu_core_1: 100`, `gpu_memory_1: 300`
- `gpu_auto: 0`

No setting was changed because the experiment constraints prohibit unapproved clock modification. Formal RTX measurements remain paused until G-Helper reports zero core and memory offsets and NVML confirms the setting persists.

## Evidence paths

- `logs/crash-hypervisor-20260905/windbg-minidump.txt`
- `logs/crash-hypervisor-20260905/relevant-events.txt`
- `C:\Windows\Minidump\090526-15796-01.dmp`
- `C:\Windows\MEMORY.DMP`

