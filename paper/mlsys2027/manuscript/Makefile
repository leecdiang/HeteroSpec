PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONUTF8 := 1
.PHONY: all check archives overleaf hardware-only
# Current build: three fresh PDFs plus the portable v0.8.5 source ZIP.
all:
	$(PYTHON) scripts/build_v085.py
check:
	$(PYTHON) ../scripts/validate_evidence_integration_v085.py
	$(PYTHON) scripts/qa_pdf_v085.py
overleaf:
	$(PYTHON) scripts/package_overleaf_v085.py
hardware-only: all
archives:
	$(PYTHON) ../scripts/replay_archives_v085.py
