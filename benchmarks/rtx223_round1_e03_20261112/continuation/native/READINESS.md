# Native continuation readiness

All 66 cells remain **NOT_RUN**. No CUDA context, model request, GPU kernel, or
operator probe process was executed in this continuation. The only executed
new native fixture is the host C++ launch-accounting test, which has no CUDA
headers, imports, libraries or initialization.

The unchanged first-round limits are 256 model requests, 1,000,000 target/draft
rows, one 10,800-second native GPU window, 4096 kernel launches and 2 GiB of
capture. E02 is a continuation of the same zero-spend E01 family, not a new
allocation. The 4096 launch limit explicitly includes model kernels.

## New source/build work

`capture_operand.hpp` observes one actual `MUL_MAT` with Q8_0 weight, F32 input,
and exactly eight logical rows. The original A wide tensor and B `[K,4,2]`
mapping are accepted only when actual caller width is eight. It captures the
complete weight, floating input and output, plus actual buffer/view/device/
shape/stride data. It never slices a q32 activation. MSVC host-only syntax
compilation passed. The frontend must configure and bind this capture; its
successful output alone would still not certify clean guards, dispatcher
specialization, original Q8_1 bytes or performance.

`backend-source-patch-v2/` instruments the exact pinned original MMVQ source
after `quantize_row_q8_1_cuda`, saving the complete padded Q8_1 buffer. It also
records the actual selected `mul_mat_vec_q_switch_fusion` template parameters,
including case4 columns, K options, grid/block, shared bytes and strides,
immediately before each MMVQ kernel submission. A and B require two and one
dispatch records respectively. These are **before-submission observations**;
they do not prove completed kernels or equality. Full patched MMVQ sm120 TU
compilation passed in `backend-build-v1/BUILD.json`; no DLL was linked, loaded
or substituted. The patch adds diagnostic synchronization and cannot supply a
clean timing price. The old source and DLLs remain unchanged.

`operator-v3/` adds failure-visible accounting to the previously built
standalone operator. A numerical or submission failure retains every launch
attempt, successfully submitted count, and actual partial raw capture sizes.
Unknown file attributes produce a null exact byte count plus a lower bound,
not a false zero. It remains compiled with execution disabled. The candidate
kernel and original arithmetic are unchanged. Its standalone kernel count
does not count model/back-end work.

`host-accounting-v1/RECEIPT.json` records six CPU native adversarial accounting
cases, including failure after the first launch, failed second submission and
cap exhaustion. These tests qualify only accounting logic. They are not any
of the 66 native projection/state qualifications.

## Remaining hard gates

1. Reliable current original-thread and host-wide task evidence must establish
   no overlap. Sandbox-only process listings and GPU-idle snapshots cannot.
2. A qualified all-model-kernel prelaunch cap is still missing. Captured graph
   replay must count internal kernel nodes as well as direct launches. The
   existing 119-launch standalone plan is not permission to exempt model work.
   CUPTI observation could corroborate actual work, but delayed observations
   alone cannot prevent the first overspending launch.
3. The isolated backend capture TU must be linked into separately bound
   numerical modules, and those modules, frontend observer hooks and runtime
   adapter must be qualified against the unchanged original numerical oracle.
4. Then obtain one actual q8 capture, replay the same bytes through actual
   backend A and B, compare original quantized buffers and every output against
   C, and fill the applicable native matrix. Only afterward may the frozen
   small paired operator timing run. Native request/state/owner/fallback and
   complete service gates remain separate.

The exact standalone schedule remains 14 correctness launches, 21 warmup
launches, and 84 paired diagnostic launches: **119 total**, not a measurement.
The cheapest prospective actual q8 operand could come from a newly frozen
eight-token prefix of an existing real prompt, decoded as an actual q8 prefill
in a target-only capture entry. That would reserve one model request/eight
target rows before execution, but its kernel cost is **unknown** until the
whole-backend budget guard is qualified. No request or time is allocated by
this suggestion. It is not the later natural bonus/correction chain.
