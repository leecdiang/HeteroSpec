# Processed analysis data

These files are generated from local raw runs and telemetry. Missing measurements remain null; they are never retrospectively estimated as observations. Regenerate with the scripts in `scripts/`, and do not edit numerical summary CSV/JSON files manually.

## 358H Phase-3 authority note

The final successful Phase-3 analysis is represented by:

- `358h_phase3_prompt_summary.csv` — final paired observation-level summary produced by `scripts/platform/358h/analyze_phase3_campaign.py`;
- `358h_phase3_rounds.csv` — speculative round traces used for committed-progress `C` and round-mechanism analysis;
- `358h_phase3_decomposition.csv` — request-level arithmetic decomposition summary;
- `358h_phase3_summary.json` — authoritative processed headline/correctness/acceptance/decomposition summary.

`358h_phase3_prompt_level.csv` is **not** a final Phase-3 result. It is a historical header-only scaffold committed during a blocked preflight (`89fb76009d4308218bd0aa572bed0170596b0850`) before the successful formal campaign. It is retained as provenance and must not be used as a paper table/figure source or treated as missing final observations.

When two processed files appear to overlap, follow `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md` and the platform closeout report to determine the authoritative evidence path rather than selecting a file by name alone.
