# What must exist before the strict physical-kernel budget can admit a worker

The missing item is not another self-authored receipt. Every obligation below
must be tied to the actual executable, complete dependency closure, device,
driver/runtime/library versions and the same policy for A/B/C, draft and
reference. A zero-work claim also needs evidence. Until then the empty native
registry is the correct result.

| Lifecycle area | Required physical coverage | Minimal concrete implementation or evidence |
| --- | --- | --- |
| Worker and DLL bootstrap | CRT/TLS constructors, dependency DllMain, CUDA fatbinary registration and lazy initialization before the first ordinary API call | A CUDA-free preflight outside the numeric process; reviewed dependency/initializer closure; no numeric process or normal LoadLibrary until initialization is itself bounded or interceptable |
| CUDA context and memory setup | Context init, allocation, managed memory, zeroing, copies, pinning, stream/event setup and deferred initialization on the actual deployment | A qualified finite physical-work envelope plus a mechanism that can reject before any uncovered operation; no assumption that allocation/copy is always zero-kernel or DMA-only |
| Target and draft models/KV | Both models, both cache lifecycles, target/draft prefill, warmup and all deferred first-use work | Descriptor- and build-specific closed route inventory, including initialization; per-request/row plan must include every model role |
| cuBLAS/CUB/other opaque libraries | Lazy handles, workspaces, tuning, library-launched kernels and any internal fallback | Either replace with owned qualified kernels or obtain and enforce a trusted finite envelope for every reachable opaque route. A single API counter is insufficient |
| Direct and ordinary wrapped kernels | All actual dispatches, branches, multithreaded submissions and one shared family reservation | e03 source guard remains useful but needs qualified native integration; prove aliases and alternate routes cannot bypass it |
| Graphs and replay | Instantiation/upload/update work, every kernel/memory/library node, each replay, nested work and dynamic launch/loop behavior | Keep graphs OFF in the present profile. A future static graph needs a complete immutable graph fingerprint and finite node expansion per replay; reject mutation, dynamic/device launch and unbounded WHILE/conditional work |
| Capture/reconciliation/failure paths | Capture copies, correction/trim cleanup and every error/exit path | Pre-reserve the qualified cleanup envelope before bootstrap. Include process/driver cleanup after fail-stop; if its physical work cannot be bounded, the strict original profile remains unadmitted |
| Actual evidence | Complete physical observations with source/process/device identity and explicit dropped/omitted-record handling | Post-run CUPTI/Nsight-style evidence can audit an already admitted deployment; it cannot create a pre-execution bound or universal veto by itself |

The concrete CPU implementation here is a controller scaffold for conditional
proofs, conservative reservation and deny-before-entry behavior. It does not
provide the missing vendor/driver-level coverage or physical launch veto.
The original 4,096 budget must not be silently reinterpreted as only explicit
application launches after initialization. If the required coverage cannot
be obtained under the existing access, that different resource contract or
an exploratory bootstrap allowance would require explicit new authorization.
Neither is assumed or started here.

Root checked these primary references for this work:

- [CUPTI 12.9 documentation](https://docs.nvidia.com/cupti/12.9/main/main.html): activity collection uses asynchronous buffers and can lose records; API callbacks observe runtime/driver calls. This is not a documented universally cancellable physical-kernel admission API.
- [CUDA 12.9.1 Programming Guide: CUDA Graphs](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-c-programming-guide/index.html#cuda-graphs): graph construction/instantiation and execution are different, and a graph may execute repeatedly. Dynamic/conditional/device launch needs additional finite closure or rejection.

No CUPTI/Nsight library, CUDA context or normal numeric DLL has been loaded
for this CPU work.
