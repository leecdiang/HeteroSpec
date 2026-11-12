# Independent CUDA route inventory

`CUDA_ROUTE_INVENTORY.json` binds 69 original source files by SHA-256 and lists lexical launch/library/runtime call sites after comments and string literals are blanked. It records 168 raw CUDA launch expressions and 84 `ggml_cuda_kernel_launch` occurrences. These are source occurrences, not dynamic launch counts, physical GPU activity, or a proof of the 4096 ceiling.

The additional concrete route found in this review is `softmax.cu:363`, `cudaLaunchCooperativeKernel`. It must be guarded or denied separately from raw launch syntax and the generic wrapper. Its branch requires cooperative support, a large column/row ratio, no mask/sinks, scale 1 and zero max bias. Branch availability is not evidence it ran in the admitted profile.

`common.cuh:1677` uses `cudaLaunchKernelEx`. `ggml-cuda.cu:4521` contains `cudaLaunchHostFunc` inside `#if 0`; that is a host callback, not one GPU kernel. The inventory also retains CUDA graph APIs, cuBLAS, CUB `DeviceScan`, NCCL and runtime memory operations so a narrow profile can explicitly reject or account for them.

The lexer does not preprocess conditional compilation, resolve templates or analyze included toolkit/library implementation. Function definitions/declarations may count as occurrences. CUB `BlockScan` inside an already owned kernel differs from host `DeviceScan` algorithms. Runtime memory API names do not establish whether or how many physical kernels execute internally. No model, CUDA API, native backend or GPU program was invoked.
