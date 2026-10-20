# HeteroSpec v4 reconstruction candidate

This is a review-only manuscript reconstruction based on public arXiv v3 (arXiv:2610.03228v3, 15 October 2026), updated with RTX closure PR137 and B570 PR131–135. It is not submitted to arXiv.

## Scientific disposition
- Retain phase-scoped query-to-batch (QB) as the core method.
- Preserve v3's original RTX three-family request results and 72-context numerical replay with their original scope.
- Add new RTX and B570 request results as distinct finite-panel experiments; do not pool cross-platform measurements.
- Report the RTX layout point estimate as unresolved under A/A instability, not as a confirmed 1.07% speedup.
- Report that speculation repays draft cost on the new RTX panel (QB/R=0.5823), but not on the new B570 panel (QB/R=2.6198). Runtime policies and cost windows differ, so do not rank devices by absolute time.
- Keep architecture discussion empirical and software-first. No new accelerator or physical bottleneck has been established.

## Source and validation status
The public v3 HTML was consulted directly for article structure and scientific claims. The exact arXiv source archive could not be retrieved through the available repository connector. This candidate is a reconstruction, not a byte-for-byte edit of the deposited source. The older manuscript_v0150 source was not treated as scientific source of truth because it predates public v3; its bibliography and general TeX conventions were reused selectively.

The Windows report and 2.27 GB archive supplied in the handoff were not directly accessible here. PR137's compact report, estimator, result tables and manifests were reviewed from GitHub. The complete raw archive remains locally held; compact-record readback is not external authentication of the raw archive.

No PDF compilation or visual inspection is claimed. Before release, build with the repository TeX toolchain, inspect every page and figure, run citation/reported-value checks, and compare against the public v3 article. No installed Humanizer skill was available; a manual clarity pass is included but is not represented as execution of that skill.
