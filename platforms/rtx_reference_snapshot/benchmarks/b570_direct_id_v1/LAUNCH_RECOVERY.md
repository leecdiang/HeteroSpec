# Direct-ID v1 launch recovery (before formal data)

The 2026-09-28 scheduled launch at frozen HEAD
`089723dd4ebbfc6bbb1cd9afcc68c6ed8a96c7bf` failed during environment
metadata decoding, before the formal output directory was created.
Completed formal executions: **0**. No generated-ID correctness result,
performance observation, or selective rerun exists from that launch.

The failed controller logs and task definition are retained under
`work/b570_direct_id_v1/`. A model-free scheduled-context diagnostic on
2026-09-29 reproduced `UnicodeDecodeError` while the frozen runner decoded
PowerShell's CP936 environment metadata as UTF-8. Merely launching the
diagnostic from PowerShell 7 did not remove the console-codepage issue.
This is an infrastructure bootstrap failure, not evidence about Vulkan
numerics, speculation, or model correctness.

The user explicitly authorized direct local execution on 2026-09-29.
Recovery uses the already verified local UTF-8 subprocess/pipe context and invokes
the **unchanged** frozen `study.py run` entry point with a fresh formal root.
The launcher ownership differs from the original unattended Task Scheduler
deployment, but the full 270-run schedule, all commands, sampling settings,
models, dataset, instrumentation binaries, direct-ID contract, and frozen
source files remain byte-identical. The active console code page was still
936 when read before launch; no system locale or code-page setting was
changed. The successful local read of the frozen environment routine
establishes the usable pipe context, not a global Windows UTF-8 locale.
Frozen protocol v1 is not overwritten.
No semantic repair, parameter search, or repeated formal observation occurs.

The first launch is excluded from scientific inference and will be included
as infrastructure provenance in the new portable evidence archive.
The local run is the first formal data-producing attempt. After completion,
independent validation, content-addressed archiving and Git publication are
performed without reopening historical B570 materials or editing manuscript
evidence. No energy collector or extra hardware telemetry is started.
