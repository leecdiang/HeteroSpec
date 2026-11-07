# Intel Arc B570 Environment Qualification

Qualification timestamp: 2026-09-11 23:08–23:46 +08:00  
Host: Windows 11 25H2 qualification host  
Scope: environment and remote-session qualification only; no formal benchmark was run.

## 1. Hardware

| Item | Observation |
|---|---|
| CPU | 13th Gen Intel Core i5-13400 |
| CPU topology | 10 cores / 16 logical processors |
| RAM | 32 GiB installed (2 x 16 GiB), configured at DDR4-3200 |
| Motherboard | Micro-Star International B760M BOMBER WIFI DDR4 (MS-7D90), version 1.0 |
| Discrete GPU | Intel Arc B570 Graphics, PCI device `VEN_8086&DEV_E20C`, status OK |
| B570 VRAM | 10,737,418,240 bytes (10 GiB); dxdiag reports 10,074 MiB dedicated |
| Integrated GPU | Intel UHD Graphics 730, PCI device `VEN_8086&DEV_4682`, status OK and Vulkan-visible |
| PCIe | B570 is at PCI bus 3, device 0, function 0. Windows exposed numeric link properties but not a trustworthy decoded generation/width, so negotiated PCIe generation/width is **not qualified**. |

The physical display is attached to the B570: 2560 x 1440, 32-bit, 180 Hz. UHD 730 has no current display mode. A ToDesk Virtual Display Adapter is also installed and enabled.

## 2. OS / driver

| Item | Observation |
|---|---|
| OS | Microsoft Windows 11 Pro, version 25H2, build 26200.9445, 64-bit |
| Power plan | High performance (`8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`) |
| HAGS | Enabled for B570 (dxdiag: Stable/Enabled); always off for UHD 730 |
| Game Mode | No explicit Game Mode registry override was present. Game DVR is enabled (`GameDVR_Enabled=1`); Game Mode effective state remains unqualified. |
| VBS / memory integrity | VBS status 0 / not enabled; security services configured/running `{0}`. Memory-integrity policy path was absent. |
| Pagefile | Automatically managed; `C:\pagefile.sys`, 2,048 MiB currently allocated, 0 MiB in use at observation time |
| Display topology | One active physical monitor; B570 drives 2560 x 1440 at 180 Hz. UHD 730 is enabled but headless. ToDesk virtual adapter present. |

GPU/runtime software:

- B570 driver: 32.0.101.8993 (Vulkan driver 101.8993).
- UHD 730 driver: 32.0.101.7088 (Vulkan driver 101.7088).
- DirectX 12 is available.
- Vulkan loader/instance 1.4.350 is installed. `vulkaninfo --summary` successfully enumerated B570 first as a discrete GPU (Vulkan API 1.4.356, conformance 1.4.0.0), then UHD 730 as an integrated GPU.
- A non-fatal Vulkan loader warning reported an unavailable layer manifest lookup; Steam and GamePP layers were present. These overlays/layers should be disabled or excluded for formal runs.
- oneAPI/SYCL was not found (`sycl-ls` absent, no oneAPI installation/environment detected).
- OpenVINO was not found. It was not installed because Vulkan passed qualification.
- The qualification stage installed Visual Studio Build Tools 2022, CMake 4.4.3, Ninja 1.13.2, and Vulkan SDK 1.4.357.0, then built the pinned llama.cpp Vulkan runtime described in section 7.

## 3. GPU backend candidates

1. **Selected candidate: llama.cpp Vulkan on Arc B570.** The system Vulkan stack directly recognizes the B570 and UHD 730, and B570 is enumerated first. This is the least invasive and currently best-supported candidate.
2. **SYCL/oneAPI: not currently available.** Do not install it merely for comparison unless Vulkan fails a later load/offload smoke test.
3. **OpenVINO GPU: not currently available.** Keep as a secondary fallback only; it is not justified while Vulkan has not yet been tested with llama.cpp.

Vulkan is now the qualified backend: the pinned llama.cpp binary and both frozen models passed the minimal execution gates in sections 7–9.

## 4. ToDesk interference observations

Windows performance counters were sampled at 1 Hz for 30 seconds per state. B570 maps to adapter LUID `0x001582c2`, confirmed by its dedicated-memory usage and active display. LUID `0x000108c5` is inferred to be UHD 730 from its Intel media-engine set and shared-only memory; LUID `0x00010861` is inferred to be the ToDesk virtual adapter from its shared-only memory and 3D-only contexts.

### State A — connected, visually static, 30 s

| Metric | Average | Maximum |
|---|---:|---:|
| CPU total | 23.43% | 39.07% |
| B570 ToDesk Video Decode (PID 13408) | 6.24% | 6.57% |
| B570 ToDesk 3D (PID 13408) | 0.92% | 0.95% |
| B570 DWM 3D | 1.27% | 1.42% |
| B570 System Copy | 0.05% | 0.52% |
| B570 dedicated VRAM | 1,750.5 MiB | 1,776.0 MiB |
| B570 shared memory | 195.7 MiB | 203.3 MiB |
| UHD 730 engines | 0% observed | 0% observed |
| ToDesk main-process CPU (PID 10464, normalized to 16 logical CPUs) | 0.26% | n/a |

Other B570 3D averages included Wallpaper Engine UI (`ui32`) 0.85%, ChatGPT 0.64%, and `0dcloud` 0.23%.

### State B — connected, repeated window scrolling/desktop refresh, 30 s

| Metric | Average | Maximum |
|---|---:|---:|
| CPU total | 25.14% | 35.56% |
| B570 ToDesk Video Decode (PID 13408) | 6.25% | 6.41% |
| B570 ToDesk 3D (PID 13408) | 0.94% | 0.99% |
| B570 DWM 3D | 10.38% | 10.77% |
| B570 System Copy | 0.02% | 0.05% |
| B570 dedicated VRAM | 1,812.6 MiB | 1,818.7 MiB |
| B570 shared memory | 171.1 MiB | 200.9 MiB |
| UHD 730 engines | 0% observed | 0% observed |
| ToDesk main-process CPU (PID 10464, normalized to 16 logical CPUs) | 0.21% | n/a |

State B also showed B570 3D from Wallpaper Engine UI 0.92%, ChatGPT 0.58%, and `0dcloud` 0.48%.

### State C — disconnected

Not performed. There was no independently verified automatic reconnection path for this active session, so forcing a disconnect would have risked losing control. A/B already supply sufficient evidence for the formal-run policy.

### Clocks and board power

Windows' built-in GPU counters did not expose reliable B570 board power or clocks. Task Manager showed B570 at approximately 54–55 C during inspection, but this is not a power measurement. An attempted read-only GPU-Z sensor-log launch did not emit a log under the current privilege boundary; therefore clocks and board power are **not measured**, and no claim about their idle uplift is made. Formal energy work remains blocked until a verified logger is available and calibrated.

## 5. ToDesk GPU engine mapping

- ToDesk processes observed: PID 5068, 10464, and 13408; installed application path for PID 10464 was `C:\ToDesk\ToDesk.exe`.
- PID 13408 continuously used the B570 Video Decode engine at about 6.2% and B570 3D at about 0.9%.
- PID 10464 created contexts on the B570 for Video Decode, Video Processing, Compute, Copy, GSC, and unnamed engines, plus 3D contexts on the inferred ToDesk virtual adapter. Most of those contexts were at 0% during point samples.
- A dedicated `Video Encode` counter was not exposed/active in these samples. Consequently, ToDesk hardware acceleration is proven on the B570 via the media/decode and 3D engines, but the host encode stage cannot be truthfully assigned to a specific Video Encode engine from this capture.
- ToDesk therefore is not isolated to UHD 730. The B570 is directly involved in the remote session.

## 6. Background-load risks

Formal runs must remove or quiesce these observed risks:

- ToDesk (B570 media/3D plus measurable CPU work).
- Desktop Window Manager, whose B570 3D load rose from 1.27% to 10.38% under refresh.
- Wallpaper Engine (`ui32` / `wallpaper64`).
- ChatGPT/Codex UI, Task Manager, Edge, Intel Graphics Software overlay, `0dcloud`, Steam overlays/layers, PowerToys, SearchIndexer, Logitech services, MSI LED service, and Game DVR.
- The diagnostic GPU-Z process from the first phase could not be terminated without elevation. The host was cleanly rebooted; GPU-Z was absent afterward, and no extra benchmark or monitoring GUI remained active.

The 23–25% average total CPU usage during both windows is itself a material timing risk, even though ToDesk's directly measured main-process share was only about 0.2–0.3% of the full machine.

## 7. Selected runtime/backend

**Selected: llama.cpp Vulkan, pinned to build b10839 / commit `0cae43063`, with Arc B570 explicitly selected as `Vulkan0`.** SYCL/oneAPI and OpenVINO remain uninstalled secondary options; Vulkan passed both model and speculative initialization gates, so adding those runtimes is not justified.

The exact source archive resolves to full commit `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`. Because the archive has no `.git` directory, build metadata was explicitly frozen with `LLAMA_BUILD_NUMBER=10839` and `LLAMA_BUILD_COMMIT=0cae43063`. The runtime reports `0.4.0-dev (build 10839, commit 0cae43063)` and MSVC 19.44.35228.0 for x64.

Build environment and command:

- Visual Studio Build Tools 2022 17.14.40; MSVC toolset 14.44.35207.
- CMake 4.4.3.
- Ninja 1.13.2 is installed but was not used; the Visual Studio 17 2022 x64 generator was used.
- Vulkan SDK 1.4.357.0; `glslc` shaderc v2026.3. Installed Vulkan loader/instance remains 1.4.350.
- Source: `C:\hs\llama-b10839`; build: `C:\hs\b`; binaries: `C:\hs\b\bin\Release`.

```powershell
cmake -S C:\hs\llama-b10839 -B C:\hs\b -G "Visual Studio 17 2022" -A x64 -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_NUMBER=10839 -DLLAMA_BUILD_COMMIT=0cae43063 -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_TESTS=OFF
cmake --build C:\hs\b --config Release --target llama-app --parallel 16
```

`llama-completion --list-devices` enumerates:

- `Vulkan0: Intel(R) Arc(TM) B570 Graphics (10074 MiB, 9305 MiB free)`
- `Vulkan1: Intel(R) UHD Graphics 730 (16237 MiB, 15469 MiB free)`

All later commands must retain `--device Vulkan0`; speculative commands must also retain `--spec-draft-device Vulkan0`. Enumeration order alone is not an acceptable device-selection control.

## 8. Model and repository state

- Repository path: `C:\Users\DIANG\Documents\ChatGPT\HeteroSpec`
- Remote: `https://github.com/leecdiang/HeteroSpec.git`
- Branch: `windows/b570-backend-control`; `main` was not modified.
- Local base and `origin/main`: `3bbe878f621d2c0ec5eeaef767575ab6fd23c2e0`.
- Models are stored under ignored `models\gguf`; model files were not modified.

The downloaded files match the repository's frozen manifests byte-for-byte:

| Role | Exact filename | Bytes | SHA256 | Result |
|---|---|---:|---|---|
| target | `Qwen3-8B-Q8_0.gguf` | 8,709,518,112 | `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6` | PASS |
| draft | `Qwen3-0.6B-Q8_0.gguf` | 639,446,688 | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` | PASS |

Sources were the official Qwen Hugging Face GGUF repositories, obtained through the HF mirror only because direct `huggingface.co` connectivity failed. The recorded upstream repository revisions were `7c41481f57cb95916b40956ab2f0b139b296d974` (target) and `23749fefcc72300e3a2ad315e1317431b06b590a` (draft).

## 9. Smoke-test result

**PASS.** These were minimal qualification-only runs: one short greedy prompt per model and a short speculative initialization/decode at `k=2`; no benchmark corpus, timing study, power measurement, or tuning search was run.

| Gate | Evidence | Result |
|---|---|---|
| Target load/decode | Explicit `Vulkan0`; 37/37 layers offloaded; 7,669.77 MiB Vulkan model buffer; 12-token response; exit 0 | PASS |
| Draft load/decode | Explicit `Vulkan0`; 29/29 layers offloaded; 604.15 MiB Vulkan model buffer; 12-token response; exit 0 | PASS |
| Speculative initialization | Target and draft both explicitly on `Vulkan0`; `n_draft=2`; 8 drafted tokens observed; exit 0 | PASS |
| CPU fallback exclusion | Every model layer, KV buffer, and compute buffer was assigned to Vulkan0; no model-layer fallback or driver/allocation error appeared | PASS |
| System-memory safety | Pagefile use remained 85 MiB in the sampled combined run; no OOM, reset, or Vulkan error | PASS |

The logs also show CPU-mapped buffers (target 630.59 MiB; draft 157.65 MiB) for host-visible/supporting tensors, including an embedding tensor that could not use the preferred Vulkan-host buffer. This is **not model-layer compute fallback**: the runtime independently reports full 37/37 and 29/29 layer offload, with KV and compute buffers on Vulkan0.

Capacity is the main residual risk. During the combined speculative smoke, Windows sampled B570 dedicated memory rising from 1,193.6 MiB to 9,587.3 MiB, leaving about 486.7 MiB of the reported 10,074 MiB. The short `c=256` gate passed, but formal commands must use a frozen context/batch configuration and fail closed if allocation behavior differs; this qualification does not establish headroom for arbitrary larger contexts.

## 10. Remote-session policy

- `remote_setup_safe: yes` — setup, download/build work, debugging, and environment inspection may use ToDesk.
- `remote_correctness_safe: yes` — short correctness and initialization checks may use ToDesk, provided their result is not interpreted as timing or energy evidence.
- `remote_timing_safe: no` — ToDesk directly occupies B570 media/3D engines; desktop refresh raised DWM B570 3D to about 10.4%, and total CPU background load was substantial.
- `remote_power_safe: no` — B570 is directly active for the remote session, and board-power/clock uplift could not be isolated or measured with the available telemetry.

All authoritative timing, verification-amortization, and energy runs must execute with ToDesk disconnected. A run collected while ToDesk is connected is diagnostic only.

## 11. Recommended unattended benchmark procedure

The reusable wrapper is `scripts/platform/b570/run_unattended.ps1`. It accepts an executable and argument array, creates a unique timestamped directory, refuses overwrite, records a JSON manifest and timestamped event log, streams stdout/stderr to separate files, preserves the child exit code, and writes distinct started/completed/failed markers. A qualification-only self-test with PowerShell as the harmless child returned exit 0 and preserved both stdout and stderr. It did not invoke a model or benchmark.

Use the wrapper directly from a non-interactive Windows Task Scheduler task:

1. Reboot or close GPU-Z and all listed overlays/background applications; confirm the intended power plan and fixed experiment configuration.
2. From ToDesk, verify the frozen model hashes, runtime version, exact command line, environment, and output root. Put immutable experiment-specific provenance beside the wrapper's manifest; never overwrite a prior run directory.
3. Schedule the wrapper for at least 60 seconds in the future under the local experiment account, using “run whether user is logged on or not.” The task must not depend on an interactive desktop and must propagate the wrapper/child exit code.
4. Use `-DelaySeconds 60 -PreIdleSeconds 60 -PostIdleSeconds 30` (or longer frozen values). The wrapper writes its manifest before waiting, then records each state transition with an ISO-8601 timestamp.
5. Disconnect ToDesk before the settling interval ends. Do not reconnect during the measured window.
6. The wrapper redirects stdout and stderr to separate files from process start and streams both while the child runs, preserving diagnostics on a non-zero child exit.
7. After the experiment exits, it records the exit code, waits the requested post-run interval, and writes `completed.marker` or `failed.marker`.
8. Reconnect only after the expected end time plus post-run settling. Treat a missing completion marker, non-zero exit code, ToDesk process activity in the measurement window, or unexpected B570 engine consumer as a failed/non-authoritative run.

No formal benchmark was started as part of this qualification.

## 12. GO / NO-GO for formal experiment

**GO.** The pinned llama.cpp Vulkan runtime builds and runs on Arc B570, both frozen Q8_0 models match the repository hashes, target and draft fully offload to the explicitly selected B570, the short greedy and `k=2` speculative smoke gates pass, and the unattended launcher is qualified with a harmless self-test.

This GO means the environment is ready for later formal B570 backend-control work, subject to two mandatory controls: (1) authoritative timing/verification/power windows run unattended with ToDesk disconnected, and (2) the formal configuration is frozen within demonstrated VRAM capacity. Energy collection additionally requires a separately validated board-power/clock logger before energy results can be considered authoritative; that instrumentation qualification was outside this backend-readiness smoke stage.
