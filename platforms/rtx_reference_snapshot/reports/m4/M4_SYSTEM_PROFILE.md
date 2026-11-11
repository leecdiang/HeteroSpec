# M4 System Profile

Captured on 2026-09-07 before the feasibility smoke tests. Machine-unique identifiers are intentionally omitted.

| Field | Observed value |
|---|---|
| Hardware | MacBook Air, model identifier Mac16,13 |
| SoC | Apple M4 |
| CPU | 10 cores: 4 performance + 6 efficiency |
| GPU | 10 cores, Metal 4 |
| Unified memory | 24 GB |
| macOS | 26.6.2, build 25G83 |
| Kernel | Darwin 25.6.0, arm64 |
| Firmware | 18000.161.10 |
| Root filesystem free | 148 GiB at capture |
| Power | AC connected, 45 W adapter, battery charging |
| Low Power Mode | Off on AC and battery profiles |
| Initial swap | 0 MiB allocated / 0 MiB used |
| Initial memory pressure | 48% system-wide memory free |

The system was already connected to AC and Low Power Mode was off; no thermal or power setting was changed. The MacBook Air is fanless, so later benchmark runs must still record thermal state and run order.

Development tools were present: Xcode command-line path under the installed Xcode bundle, Apple clang 21.0.0, Git 2.50.1, Homebrew Python 3.11.15, and the Metal compiler. The isolated environment is `.venv-m4`; the system Python 3.9 was not modified.
