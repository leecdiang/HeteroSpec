# RTX draft-ubatch protocol: reviewed design, not a runnable GPU study

**Status: NOT_READY_FOR_GPU / PREPARED_NOT_RUN.** Start with [PROTOCOL.md](PROTOCOL.md), the [short executor handoff](SHORT_PROMPT_CN.md), and [publication scope](PUBLICATION_SCOPE.md). This directory publishes an existing reviewed design and arithmetic-only checks. It does not provide a launch-ready GPU runner or authorize device access, model inference, merge or deployment.

[BENCHMARK_PLAN.json](BENCHMARK_PLAN.json) intentionally leaves actual device paths, old-R/adapter bridge, primary family, history recipe, peak resources and conservative storage admission unbound. Missing bindings mean BLOCKED. Short pilot caps must not change the old R contract or silently replace resident R with a fresh reference.

The plan first freezes identity without GPU execution, then requires a separately authorized/budgeted old-R native/observer/resource bridge. Only afterward can finite target-strict qualification and a 5-heavy/10-provisional-light single-input screen proceed. A larger confirmation is optional and separately gated. Both genuine target-only baselines retain the same cache opportunities; default cache hits must not be disabled to manufacture gains.

The four reviewed primary artifacts retain their exact original bytes. Their statements about scratch-only work, the then-unpublished native bridge, and historical local paths describe the earlier design/review snapshot. [PUBLICATION_SCOPE.md](PUBLICATION_SCOPE.md) supplies the later publication state and verified fixed-head source mappings. [SOURCE_SCOPE.json](SOURCE_SCOPE.json) is that historical snapshot, not a claim about the latest branch. [Independent review](independent_review/REVIEW_CN.md) and [reviewed file pins](independent_review/reviewed-files.json) describe design review only.

The published native CPU bridge remains a tiny synthetic diagnostic. Its full generated capture archive is LOCAL_ONLY_NOT_UPLOADED; links to its source/summary do not make that archive downloadable or establish GPU/old-R qualification. See [ARTIFACT_LINKS.json](ARTIFACT_LINKS.json) for verified available files and explicit unavailable/local-only categories.

Optional arithmetic checker, Python standard library only:

```sh
python -O check_design.py --output /tmp/fresh-rtx-cost-check.json
```

Choose a new output filename. The result is always DRAFT_ARITHMETIC_CHECKED_NOT_READY_FOR_GPU. The checker cannot launch a model and checks only setup counts and nominal byte/token scenarios, not device feasibility, exactness or runtime readiness. The 8/12 GiB storage ceilings are hard limits, not a claim that the current native bridge fits the proposed studies. Admission remains BLOCKED without a conservative bound from an implemented capture strategy.
