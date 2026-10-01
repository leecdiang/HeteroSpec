# Current manuscript — v0.8.5 evidence integration

This is the current author-review draft, built from merged main
`98e8470f2559f78335de8d3473997d21b4bb55b8`. It adds sealed B570 live-fork,
RTX independent proposal/replay, and directly qualified matched latency
studies to the existing argument. The main PDF has 10 body + 2 reference
pages; the separate appendix has 10 pages; the hardware-only proof has
8 body + 2 reference pages. That proof removes the runtime section only,
retains full-manuscript summaries, and is not a submission manuscript.

## Build and current QA

Prerequisites: Python 3.11+ with `pypdf`, `numpy` and `pymupdf`; pdfLaTeX,
BibTeX and latexmk; Poppler for page rendering. Use an activated environment
containing these dependencies. The recorded environment is in
`../evidence/CLEAN_ZIP_REBUILD_V085_QA.json`; no new TeX/plugin is needed on
the authoring host. All commands below were exercised in this revision.

From this manuscript directory:

```sh
python3 scripts/build_v085.py
make check
```

The build creates a new QA directory, follows current TeX dependencies,
packages the self-contained anonymous source ZIP, builds main/appendix
from two independently extracted copies, and builds the internal proof.
It verifies manifests, compares every page's text, and runs PDF/log/font/
reference/anonymity gates. It copies the inspected PDF bytes to `output/`.
`make all` invokes the same current build; it does not invoke old asset
or macro generation. `make check` runs current scientific, numerical,
protected-byte, counterexample and PDF checks. Visual review remains a
separate manual step; a build alone is never a visual PASS.

The five outputs are `manuscript-v0.8.5.pdf`, `appendix-v0.8.5.pdf`,
`hardware-only-v0.8.5.pdf`, `overleaf-evidence-integration-v0.8.5.zip` and
`anonymous-evidence-index-v0.8.5.zip`. The source ZIP needs only TeX:
extract into a new directory and run `latexmk -pdf main.tex` and
`latexmk -pdf appendix.tex`. The evidence ZIP has its own standard-library
`python3 -B verify.py` entry. Its INDEX identifies the separate complete
anonymous RTX H2 tar.gz by exact filename, length and SHA256.

## Full retained-archive replay

From the repository root, using the same Python environment:

```sh
python3 paper/mlsys2027/scripts/replay_archives_v085.py --work tmp/qa-v085/new-archives
python3 paper/mlsys2027/scripts/project_evidence_v085.py --work tmp/qa-v085/new-archives
python3 paper/mlsys2027/scripts/build_evidence_ledger_v085.py
python3 paper/mlsys2027/scripts/package_anonymous_evidence_v085.py --work tmp/qa-v085/new-archives
```

Choose a nonexistent work directory. This reconstructs all 49 B570 parts,
all RTX H2 parts, complete and anonymous H2, the earlier RTX two arms,
old B570 H1 and old direct-ID archives, and M4 primary/secondary evidence.
It performs CPU/file verification only. Frozen B570 Windows path basenames
need the disclosed portable adapter on POSIX; the unadapted failure is
retained and no scientific assertion is skipped. Recreate projections and
anonymous exports after changing the archive receipt so its content anchor
remains current, then run current QA.

The exact old v0.8.4 sequence ZIP is absent from this checkout; no old file
was replaced. Its original sealed 72 arrays remain available and the new
index exports element-identical values. 358H runtime raw traces are absent;
compact pinned diagnostics are not a raw replay. Omitted weights/binaries
are not authenticated by these offline checks.

## Review boundaries and historical material

Prediction equality does not imply reference qualification. B570 immediate
fork decisions are unchanged despite scores and later trajectories changing;
the alternate continues at UB128. RTX H1 failed discovery with no reserved
execution. V2 H2 is independent orchestration sharing numerical routines;
its reference remains blocked. Newly qualified RTX serialization is slower
in an instrumented CLI interval. M4 Guard remains slower than fixed Always
on a post-study paired secondary endpoint; 358H replay/proposal is inseparable
and its runtime intervention has no formal performance result.

See `../HANDOVER_CURRENT.md`, `../evidence/EVIDENCE_INTEGRATION_AUDIT_V085.md`
and `../reviews/integration_v085/`. Earlier versioned scripts, reviews,
receipts and outputs are history and must not serve as current default
build/QA targets. The official title, Figure 3, old numeric macros, vendor
style and original scientific archives stay unchanged. The next step is
an author-initiated independent submission-level review of these exact
artifacts and their Draft PR, followed by a separate author upload decision.
