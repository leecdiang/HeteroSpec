## GPU14 shared-core engineering regression passed

The original numerical host stopped on its first MQ graph with integer division
by zero in the uninitialized DLL timer. Its static core differed from the CUDA
plugin's DLL core. The old execution permanently remains **1 started/failed,
719 unstarted, 0 confirmed completed**; original F0, inputs, binaries, archive,
failure evidence and costs are preserved.

The bounded repair uses route A: the new host imports the original, byte-identical
ggml-base.dll and ggml.dll through import stubs. Exact path/hash/export-owner/IAT
checks and process-lifetime initialization precede CUDA loading. No numerical DLL,
precision, layout, reduction, model or execution configuration was replaced. The
prior real-DLL CPU tests and retained engineering failures are in repair_timer_v1.

The author explicitly approved reviewed9aefd4c and GPU14 F0
`65a6a60b726572305e29f73e2d852936af9e4c87d9740cba5f95f97f738bd290`.
The frozen controller/checker/host executed once under a new run_id and budget:

- **14 started, 14 fully qualified completed, 0 failed, 0 unstarted.**
  14 fresh native hosts, 14 explicit readiness processes, 1 controller:29 starts.
  166 node support queries; zero models, warmups, extra hosts or retries.
- All6 Qwen/SmolLM2/Llama layer0/prefill/q1 MQ controls reproduce the original
  stages bitwise, preserve full inputs, restore own AV and repeat bitwise before q2.
- Fixed Qwen layer0/prefill/q2 MQ reproduces original MQ; PQ and QB reproduce
  their historical outputs. **QH_C=PQ=QB bitwise** in QK, softmax, AV and ordinary
  output in both fresh repeats. These differ finitely from MQ, first at QK;
  original numerical rules retained these differences without tuning or switching.
- All14 actual CUDA paths share the verified initialized core. All41 CUDA plugin
  core IAT entries per host resolve to that module's true exports. All166 supports
  and116 nonmetadata placements pass. Actual graph identities and full before/after
  input bytes match frozen references. All7,808 pins/21 numerical DLLs remain unchanged.
- Conservative owned bound70.5494022/1800s; controller35.2747007/900s. These are
  engineering lifetimes with observation/I/O, **not timing or acceleration evidence**.

Full result, pairwise bitwise/error/ULP tables, all14 raw slots/inputs/stages/module
identities, source/host/checker and manifest are in
`benchmarks/rtx_lowering_envelope_v1/GPU14_EXECUTION/`.
Raw ZIP23,264,913B,575members, SHA256
`f1dc041ad50400b3c11c874d5a94db9fba960d17ec20361df21a2871d8c3102f`.
Closure receipts authenticate remote bytes and reconstruct all14 original frozen
audits plus byte-identical analysis JSON/CSV in a fresh directory, CPU only.

This permits preparing a **formal numerical-v2 review**, not starting it. A new
run_id/F0, support-impact review, budget and further explicit approval remain
required. Wider coordinates, general equivalence, complete actor/requests and
target-mask3/k3 transactions remain unqualified. Kernel/reduction-tree identity
is UNKNOWN. S1 timing/profile, formal720v2 and S2/S3 remain unadmitted. No QH speed
or hardware-benefit claim. Keep Draft; PR104/110, B570, papers, main, releases and
automations are untouched. No next GPU stage or old-slot resumption.
