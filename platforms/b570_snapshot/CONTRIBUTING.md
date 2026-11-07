# Contributing

1. Keep `main` runnable and use one branch per platform or purpose: `windows/5070ti-closeout`, `windows/358h`, `macos/m4-mlx`, or `analysis/paper`.
2. Commit code before a formal experiment and record the Git commit SHA in every run.
3. Never commit model weights, caches, virtual environments, credentials, or raw telemetry.
4. Generate summary CSV files with scripts; do not edit them manually and never overwrite a raw run.
5. Re-run the correctness suite after changing correctness-critical speculative decoding code.
6. Keep paths repository-relative or configurable through `HETEROSPEC_*` environment variables.

