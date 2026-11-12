# Counter proof boundary references

The effective implementation is the pinned local CUDA12.9 source/header/build identity. External documentation explains the execution model; it does not certify this DLL's coverage or observed work.

- [CUDA12.9.1 Programming Guide](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-c-programming-guide/index.html#cuda-graphs): graph creation/instantiation and graph execution are separate. Replaying an executable graph can repeat its nodes; creation-site counts cannot stand in for executed kernel counts. This study therefore denies graph replay in the prospective narrow profile rather than charging one graph call as one kernel.
- [CUDA12.9.1 Runtime API, Library Management](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-runtime-api/group__CUDART__LIBRARY.html): runtime library/code lifecycle is separate from calling an exported application metadata function. A host-only metadata function does not prove that normal Windows DLL loading invokes no CUDA registration/initialization.

The local coverage inventory separately identifies raw CUDA launches, ordinary/PDL/cooperative wrappers, cuBLAS, CUB, graph and runtime-memory paths. Its static counts are a source inventory, not a dynamic count, minimum request cost or proof of physical-kernel enforcement. Unknown library/runtime work keeps native admission closed.
