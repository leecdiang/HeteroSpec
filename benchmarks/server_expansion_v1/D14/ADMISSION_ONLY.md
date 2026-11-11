# Bounded C1024 admission after M1

This entrypoint performs PR198 stage2 only. It cannot establish numerical
equivalence, forward-workspace headroom, speed, or eligibility for a formal panel.
M2, C4096, candidate outputs and14B timing are not launched.

The predecessor is the qualified Linux successor592abdfe9267fd97ecbde18cd0ee9a1bfc319e20
and completed M1 is PR204. Admission links read-only numerical archives from that
predecessor's full CUDA reference build, compiling a new allocation observer.
This observer is not an independent14B numerical reference. An independent
R_14B_C1024 must be frozen before any later candidate forwards.

The actual native checks require one GPU, all target/draft weight buffers and
every layer's F16 K/V buffers on that GPU, no host-backed buffers, actual C1024
capacity, an empty active prefix, full native pair vocabulary/EOG equality and
the fixed output/batch/FA fields. The original1GiB GPU,4GiB RAM and20GiB disk
reserves remain enforced by a separate admission-only supervisor. Allocation
includes context-construction buffers but does not execute a model graph.

Use the exact target/draft identities in models.json. The official Qwen
ModelScope distribution in transport_modelscope.json has independently matching
file size and whole-file SHA256; it changes transport, not the pinned model.
Signed redirect headers and host inventory stay private. All failed transports,
partial files, build epochs and attempted admissions are retained.

```sh
python D14/build_admission.py --baseline /path/to/qualified/run-01 \
  --runtime /path/to/qualified/runtime --out /fresh/admission-build \
  --supervisor /fresh/admission-supervisor
python D14/run_admission.py --baseline /path/to/qualified/run-01 \
  --supervisor /fresh/admission-supervisor --build /fresh/admission-build \
  --work /fresh/admission --target /verified/Qwen3-14B-Q8_0.gguf \
  --draft /verified/Qwen3-0.6B-Q8_0.gguf
```

Alternatively await_admission.py freezes source/build identities before waiting
for a verified acquisition receipt and invokes that same bounded admission once.
A failed attempt is not replayed automatically. The environment uses the existing
explicit allocation; a source or download receipt never grants GPU permission.

Report actual load/context allocation, the full supervisor window, sampled free
memory and total-minus-free separately. Total-minus-free includes driver-reserved
memory; it is not per-process usage or NVML memory.used. A zero-forward admission
pass must be labeled separately from numerical qualification and timing.
