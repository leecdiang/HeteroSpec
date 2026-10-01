PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONUTF8 := 1
.PHONY: all check overleaf hardware-only
all:
	$(PYTHON) scripts/build_v086.py
check:
	$(PYTHON) ../scripts/validate_convergence_v086.py
	$(PYTHON) scripts/qa_pdf_v086.py
overleaf:
	$(PYTHON) scripts/package_overleaf_v086.py
hardware-only: all
