# Final clean-room fixes — v0.8.2

## Trigger

The PDF-only clean-room review classified the manuscript **READY AFTER MINOR TEXTUAL REVISION** and required **no new experiment**. Its four original review files are preserved byte-for-byte under `reviews/final_clean_room_v081/`.

## Fix 1

Before: “all 72 serialized output sequences”

After: “all 72 complete generated-token-ID sequences on the reserved set”

Reason: Prevent a text-level-output interpretation and make the strongest endpoint explicit in the abstract. The frozen-before-reserved chronology and residual divergences remain in the same sentence.

## Fix 2

Added: “These prospective qualification studies are separate from the historical timing campaigns and do not retrospectively certify those timings under the direct-ID contract.”

Reason: Keep historical timing and fresh qualification evidence unmistakably separate on first-page reading, immediately before the RTX/B570 results.

The first build exceeded the ten-page body limit. Nearby introductory prose, the M4 comparator summary and the repeated practitioner sequence were lightly compressed while preserving their citations, numerical endpoints, comparator and scope boundaries. This restored ten body pages without changing margins, fonts, sizes, template spacing, scientific endpoints or section headings.

## Scientific status

No new experiment or inference; no numerical result changed; no claim broadened; no closed evidence changed. Title, three-contribution structure, Figure 3, Related Work, Guard interpretation, B570/358H scope, and canonical Limitations remain unchanged. Version labels and build outputs advance to v0.8.2 without overwriting v0.8.1.
