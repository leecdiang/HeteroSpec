#!/usr/bin/env python3
"""Check final table/figure transcription, PDF text bounds, fonts and references."""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pdfplumber
from figure_catalog import FIGURES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdffonts", default=shutil.which("pdffonts"))
    args = parser.parse_args()
    if not args.pdffonts:
        raise SystemExit("Install Poppler or supply --pdffonts /path/to/pdffonts.")
    root = Path(__file__).resolve().parents[1]
    rows = list(csv.DictReader((root / "data/rtx_repair_cost.csv").open()))
    values = {(r["family"], r["comparison"]): r for r in rows}
    main_text = (root / "sections/05_evaluation.tex").read_text()
    cost_table = main_text.split(r"\label{tab:cost}")[1].split(r"\end{table*}")[0]
    comparisons = ["M_PQ/M_QB", "C_PQ/C_QB", "M_GS/M_QB", "C_GS/C_QB",
                   "M_QB/C_QB", "R/M_QB", "R/C_QB"]
    for family in ("Qwen3", "SmolLM2", "Llama"):
        line = next(line for line in cost_table.splitlines() if line.startswith(family + " &"))
        cells = re.findall(r"([0-9]+\.[0-9]+) \((\d+)\)", line)
        assert len(cells) == len(comparisons)
        for pair, (ratio, regressions) in zip(comparisons, cells):
            row = values[family, pair]
            assert ratio == f"{float(row['ratio']):.3f}"
            assert int(regressions) == int(row["regressed_tasks"])
    supplement_text = (root / "supplement/04_cost.tex").read_text()
    supplement_table = supplement_text.split(r"\label{tab:allrepair}")[1].split(r"\end{table*}")[0]
    table_rows = [line for line in supplement_table.splitlines() if line.startswith("$")]
    assert len(table_rows) == len(comparisons)
    for pair, line in zip(comparisons, table_rows):
        cells = re.findall(r"([0-9]+\.[0-9]+) & (\d+)/12", line)
        assert len(cells) == 3
        for family, (ratio, regressions) in zip(("Qwen3", "SmolLM2", "Llama"), cells):
            row = values[family, pair]
            assert ratio == f"{float(row['ratio']):.6f}"
            assert int(regressions) == int(row["regressed_tasks"])
    figure = (root / "figures/cost.tex").read_text()
    plotted = re.findall(r"\((\.?\d+(?:\.\d+)?),([123])\)\s*\[([\d.]+)\]", figure)
    assert len(plotted) == 9
    families = {"1": "Llama", "2": "SmolLM2", "3": "Qwen3"}
    for index, (ratio, y, label) in enumerate(plotted):
        pair = ("C_PQ/C_QB", "C_GS/C_QB", "M_QB/C_QB")[index // 3]
        assert abs(float(ratio) - float(values[families[y], pair]["ratio"])) < 1e-9
        assert label == f"{float(ratio):.3f}"
    report = {
        "version": "0.15.3", "date": "2026-10-14",
        "scope": "Final manuscript/figure transcription and PDF checks; no GPU or full raw-archive audit.",
        "main_cost_cells_checked": 21, "supplement_cost_cells_checked": 21, "cost_figure_points_checked": 9,
        "documents": {},
    }
    files = [root / "output/main.pdf", root / "output/supplement.pdf"]
    files.extend(root / "output/figures" / f"Figure_{number}_{stem}.pdf"
                 for number, stem, _ in FIGURES)
    assert len(files) == 9
    for path in files:
        font_output = subprocess.check_output([args.pdffonts, str(path)], text=True)
        font_lines = font_output.splitlines()[2:]
        assert font_lines, path
        assert all(re.search(r"\s+yes\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
                   for line in font_lines), f"Unembedded font: {path}"
        with pdfplumber.open(path) as pdf:
            pages = []
            for number, page in enumerate(pdf.pages, 1):
                words = page.extract_words()
                outside = [w for w in words if w["x0"] < -1 or w["top"] < -1
                           or w["x1"] > page.width + 1 or w["bottom"] > page.height + 1]
                text = page.extract_text() or ""
                assert words and not outside, (path, number, outside)
                assert "??" not in text and "\ufffd" not in text, (path, number)
                pages.append({"page": number, "out_of_page_words": 0, "words": len(words)})
            report["documents"][path.relative_to(root).as_posix()] = {
                "pages": len(pdf.pages), "fonts_embedded": True, "page_checks": pages,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
    report["status"] = "PASS_AUTOMATED_CHECKS_VISUAL_REVIEW_RECORDED_SEPARATELY"
    (root / "provenance/FINAL_QA_V0153.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Checked 42 main/supplement cost cells, 9 main cost-figure points, 9 PDFs, embedded fonts and page text bounds.")


if __name__ == "__main__":
    main()
