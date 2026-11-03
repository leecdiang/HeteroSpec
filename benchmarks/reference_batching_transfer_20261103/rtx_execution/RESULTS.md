# RTX transfer execution

PR164 head `2cfcc1efb14381423cfec406521bdbbbf7f04777`. The pinned PR162 raw index `ba4999f8d8a526aa209a181ab7a0d96dd5a7cc5bd9c4e9e048e12d5dc1089f86` identifies both final source trees. All 3,535 archived source members in each cohort were checked against the final index before staging. The historical SOURCE_MEMBERS file alone describes an earlier stage and differed at the scheduler file.

The CUDA entry point stages the shared planner, checks the rotary graph consumer and RMS head-scale producer, asks the actual backend for scalar and batch offload preferences, and includes the head placement decisions in graph reuse. Native diagnostics emit RTX164_HEAD, RTX164_ATTN and RTX164_CACHE_BUILD records when enabled. The Qwen and metadata4 workers were compiled in separate output trees using the pinned compiler commands and original numerical DLL cohorts.

Development is in progress. The first diagnostic epoch is exploratory: its binding inherited the old static-core digest even though its executable digest identifies the freshly compiled worker. Its results remain separate. The successor records the actual static-core digest and source files. The ordinary CUDA staging command reproduces the sources compiled for that successor byte-for-byte. Qualification, timing and final mechanism adjudication remain pending.
