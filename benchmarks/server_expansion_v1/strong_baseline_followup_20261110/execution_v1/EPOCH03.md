S1's original `graphs_reused == 0` service assertion confused two mechanisms.
The `hsc::reused(this)` call is in llama-context's host graph reuse branch. It
does not count CUDA graph replay. The native frontend sets
`GGML_CUDA_DISABLE_GRAPHS=1` before backend/model/context initialization; the
compiled CUDA common header's `is_enabled` checks that exact switch. All native
ELFs, numerical inputs, graph policy, ABI and timing code remain unchanged.

The first G service worker completed normally and retained all12 heavy/clean
receipts and raw state/vector payloads. A post hoc reader correction checks the
actual off-only capability separately, retains the host graph cache counts, and
repeats every saved numerical, physical, lifecycle and service comparison. Its
six complete service pairs passed offline after the correction. This is an
explicit reader correction, not new GPU numerical data or performance evidence.

The continuation reuses714 complete logical requests across208 workers, plus
the four earlier failed slots that remain charged. It revalidates every saved
comparison and then executes the141 still-unstarted operations, including72 S2
operations only after complete S1 and F1 public readback. The same cumulative
journal,871 incremental ceiling and12 remaining failure/closeout slots apply.
No successful native slot is relaunched and no partially started slot is reused.

All reused native/build source bytes and dependency closure are rehashed. CPU
tests and fresh zero-GPU echoes run again. New reader code, complete reuse file
commitments and the full continuation manifest receive a new immutable public
F0 and anonymous full-byte readback before any new model output.
