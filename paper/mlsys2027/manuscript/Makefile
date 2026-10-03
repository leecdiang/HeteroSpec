PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONUTF8 := 1
.PHONY: all check overleaf hardware-only
all:
	$(PYTHON) scripts/build_v088.py
check:
	$(PYTHON) ../scripts/validate_revision_v088.py
	$(PYTHON) scripts/qa_pdf_v088.py
overleaf:
	$(PYTHON) scripts/package_overleaf_v088.py
hardware-only: all
