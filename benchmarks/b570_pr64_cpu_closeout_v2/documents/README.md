# B570 PR64 CPU closeout v2

Start with REPORT.zh-CN.md; later manuscript work starts with PAPER_HANDOFF.md and CLAIM_EVIDENCE_MATRIX.csv. Evidence repair qualifies finite endpoints but shows no deployment gain over ordinary R. E remains119/120; B570 GPU next action STOP. RTX scalar-reference raw costs are explicitly deferred. No models, KV or fullfloat bulk are bundled here.

## CPU reproduction

Python3.12.10 + NumPy2.5.3, Matplotlib3.11.2 were used (recorded in RUNTIME.json). Only code/ scripts are needed; none launches a model executable or imports the old runner. Bind an existing read-only PR64 restore and original immutable archive; setup verifies the archive and reads only its INDEX, with no bulk restore:

```powershell
python code/setup.py --root C:/hs/cpu-recheck --archive ORIGINAL_CAS.zip --restore EXISTING_PR64_RESTORE
$env:HS_CPU_ROOT='C:/hs/cpu-recheck'
python code/evidence.py   # once, new CPU directory only
python code/resume.py
```

The D32 MBPP historical reference access follows the prior-core path in original STAGE0.json. On another host, restore/use that same immutable PR63 archive separately and supply a **new private configuration override**, never edit the old STAGE0/raw: `prior_core_restore` and `prior_core_archive` may be set in the new CONFIG.json. The PR63 archive index/hash and selected receipts still must match their frozen identity. D24HE uses the CAS-bound three-repeat HISTORICAL_EXPECTED endpoint exports, not invented full raw.

The Python units regenerate counts, qualification, all cross scores/KV checks, absolute costs, task/round ratios, source work formulas and exact figure data. `resume.py` hashes input bytes once and skips a unit only if its code, reader and owned output hashes match. Failed units remain in LEDGER; no model work is resumed.

The publication handoff uses fixed public PR sources and a privately cached primary-source reading. `handoff.py` regenerates bindings/claim CSV/decision from those sources; fetch each exact head/path listed in SOURCE_BINDINGS using read-only Git before running it on another machine. Cache layouts are `private/fixed_sources/PR/PATH` and `private/rtx_public/PR/PATH`; metadata catalog is `dependencies/FIXED_SOURCE_READINGS.json`. `documents/` provides the delivered prose/visual-QA drafts for a clean reconstruction (copy into output/ after raw-stage generation), then:

```powershell
python code/handoff.py
python code/verify.py
python code/seal.py
```

Visual QA must be repeated after changed figures: render PDFs with Poppler, inspect both outputs, and update the new study's FIGURE_VISUAL_QA hashes. An old PASS is invalid for changed bytes. The verifier rejects changed source/raw, missing/duplicate denominators, inverted ratios, suffix/raw conflation and unqualified costs. Five synthetic negative fixtures are included in verify.py.

CPU_ARCHIVE records a deterministic content-addressed package of this new CPU evidence and code; the original2GB CAS is only an external dependency. Remote delivery uses a new Draft PR; a fresh branch fetch verifies Git blobs, hashes and additive diff. No paper rewrite or merge is part of this workflow.
