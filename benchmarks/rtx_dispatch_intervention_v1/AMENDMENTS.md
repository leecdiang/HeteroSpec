# CPU implementation changes

- New entry and UUID; parent runtime/graph arithmetic unchanged. Inputs are new
  physical artifacts. Full logical coordinate bytes copied with actual tensor
  strides, finite-zero KV extension, negative-infinity mask extension. The native
  entry validates logical/physical fields against actual metadata.
- Route A shared core and persistent independent CUDA inputs retained. H1 keeps
  complete ordinary bytes from every call; files/JSON are emitted after the loop.
- Qualification continues across planned padded arms on exact-reference failure;
  these are retained negative scientific outcomes, not retried. Clean slots for
  ineligible arms remain UNSTARTED. A native crash or uncertain cleanup stops.
- Six separately budgeted alternating-input ON capability hosts (2+6 calls), one
  per T0 shape/layout/storage value0 signature. They switch all four inputs and
  check both fresh references; they do not run the integrated producer operation.
  Qualification/timing T0 hosts do run copy/transpose and upload inside the timer.
- Profile plan: twelve B0 value0 qualification attempts, six T0 value0 first
  qualification attempts, six alternating capability attempts: at most24.
  Capability adds6 hosts/48calls to default344/11400; maximum planned350/11448.
  Any failed qualification uses fewer calls; no replacement or optional diagnostics.
- B0 packing/reallocation/upload are separate setup evidence, not included free in
  an application cost claim. T0 primary is a single contiguous native QPC interval.
- Existing pinned CUPTI tool files/headers referenced by exact hash, not upgraded.
- Source-link uncertainty preserved. Candidate source files retained separately.
- Two CPU preparation errors retained: missing ignored import library at new
  sparse checkout; then missing NVCC-header path. Both fixed before any GPU call.
- Statistical screen is prospective and implements BOTH controls, both values,
  both sessions, all8 blocks, stratified block intervals and matched A/A scale.
