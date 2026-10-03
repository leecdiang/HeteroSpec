PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONUTF8 := 1
.PHONY: all check overleaf hardware-only
all:
	$(PYTHON) scripts/build_v089.py
check:
	$(PYTHON) ../scripts/validate_closeout_v089.py
	$(PYTHON) scripts/qa_pdf_v089.py
overleaf:
	$(PYTHON) scripts/package_overleaf_v089.py
hardware-only: all
