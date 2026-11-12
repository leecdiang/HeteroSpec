# Budget evidence boundaries

These primary sources support the API/observation distinction, not a claim of complete physical-kernel enforcement on this host. No CUPTI/runtime API was initialized in e04.

- NVIDIA CUPTI12.9 usage: https://docs.nvidia.com/cupti/12.9/main/main.html . Activity records are buffered asynchronously and may be dropped; runtime/driver callbacks observe API events. Post-execution activity totals do not by themselves veto the next physical launch. The documentation does not establish the complete cancellable lifecycle policy required by this study.
- CUDA12.9.1 programming guide, CUDA graphs: https://docs.nvidia.com/cuda/archive/12.9.1/cuda-c-programming-guide/index.html#cuda-graphs . A graph submission can represent multiple kernel nodes and conditional/device-side activity. A finite proof must expand and bind all allowed nodes/iterations or reject the graph. The existing prospective native profile disables graphs; CPU graph proofs are not qualification of graph execution.
- CUDA12.9.1 runtime execution control: https://docs.nvidia.com/cuda/archive/12.9.1/cuda-runtime-api/group__CUDART__EXECUTION.html . Kernel launches and host callbacks are distinct operations; API entry counts do not define total device-side activity or internal library kernels.

The inference for e04 is conservative: lacking an independently qualified bound/enforcement route for initialization, numerical DLL load, libraries, transfer-side work and teardown, production admission must refuse before numerical DLL initialization. This is a blocked executable policy, not proof that a useful model request can run within4096.
