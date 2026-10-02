PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONUTF8 := 1
.PHONY: all check overleaf hardware-only
all:
	$(PYTHON) scripts/build_v087.py
check:
	$(PYTHON) ../scripts/validate_integration_v087.py
	$(PYTHON) scripts/qa_pdf_v087.py
overleaf:
	$(PYTHON) scripts/package_overleaf_v087.py
hardware-only: all
