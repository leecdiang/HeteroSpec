#!/usr/bin/env python3
"""Export the editable TikZ figures as cropped vector PDFs at manuscript size."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


from figure_catalog import FIGURES


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "output" / "figures")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    latex = shutil.which("pdflatex")
    if not latex:
        raise SystemExit("pdfLaTeX is required; see the manuscript README for TeX dependencies.")

    # Match the manuscript class, type sizes and text width. Cropping preserves
    # the vector artwork at its original scale.
    with tempfile.TemporaryDirectory(prefix="heterospec-figures-") as temporary:
        scratch = Path(temporary)
        for number, stem, _ in FIGURES:
            wrapper = scratch / f"{stem}.tex"
            wrapper.write_text(
                r"\documentclass[final,5p,times,twocolumn]{elsarticle}" "\n"
                r"\input{preamble}" "\n"
                r"\usepackage[active,tightpage]{preview}" "\n"
                r"\PreviewEnvironment{tikzpicture}" "\n"
                r"\setlength\PreviewBorder{4pt}" "\n"
                r"\begin{document}" "\n"
                r"\begin{minipage}{\textwidth}" "\n"
                rf"\input{{figures/{stem}.tex}}" "\n"
                r"\end{minipage}" "\n"
                r"\end{document}" "\n",
                encoding="utf-8",
            )
            command = [
                latex, "-interaction=nonstopmode", "-halt-on-error",
                f"-output-directory={scratch}", str(wrapper),
            ]
            for _ in range(2):
                result = subprocess.run(
                    command, cwd=root, text=True, capture_output=True, timeout=120,
                )
                if result.returncode:
                    raise RuntimeError(f"Figure {stem} failed:\n{result.stdout[-5000:]}")
            log = (scratch / f"{stem}.log").read_text(errors="replace")
            if "Overfull \\hbox" in log or "Overfull \\vbox" in log:
                raise RuntimeError(f"Figure {stem} has a layout overflow; inspect its source.")
            destination = output / f"Figure_{number}_{stem}.pdf"
            shutil.copy2(scratch / f"{stem}.pdf", destination)
            print(f"Exported {destination}")


if __name__ == "__main__":
    main()
