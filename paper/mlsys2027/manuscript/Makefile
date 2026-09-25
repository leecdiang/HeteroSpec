STYLE := $(CURDIR)/vendor/official/mlsys2025style
export TEXINPUTS := $(STYLE)//:
export BSTINPUTS := $(STYLE)//:
PYTHON ?= python3
.PHONY: all assets check clean hardware-only overleaf
all: assets
	mkdir -p build output
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build appendix.tex
	cp build/main.pdf output/manuscript-v0.4.pdf
	cp build/appendix.pdf output/appendix-v0.4.pdf
assets:
	$(PYTHON) scripts/build_assets.py
	$(PYTHON) scripts/runtime_values.py
check:
	$(PYTHON) scripts/validate_evidence.py
	$(PYTHON) scripts/validate_narrative.py
	$(PYTHON) scripts/validate_runtime.py
	$(PYTHON) scripts/validate_figures.py
	$(PYTHON) scripts/qa_pdf.py
hardware-only: assets
	mkdir -p build/hardware-only
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build/hardware-only -jobname=hardware-only '\def\HardwareOnly{1}\input{main.tex}'
	BIBINPUTS=$(CURDIR): bibtex build/hardware-only/hardware-only
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build/hardware-only -jobname=hardware-only '\def\HardwareOnly{1}\input{main.tex}'
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build/hardware-only -jobname=hardware-only '\def\HardwareOnly{1}\input{main.tex}'
clean:
	latexmk -C -outdir=build main.tex appendix.tex

overleaf:
	$(PYTHON) scripts/package_overleaf.py
