#!/usr/bin/env python3
"""Render the active A4 row overlay from the frozen style table without new data."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "paper/mlsys2027/figures/style_v04/tables/appendix_table.tex"
OUTPUT = ROOT / "paper/mlsys2027/manuscript/tables/05_regimes_v083_rows.tex"

REPLACEMENTS = [
    (r"p{1.38in}p{1.29in}p{.79in}p{.35in}X", r"p{1.38in}p{1.25in}p{.95in}p{.35in}X"),
    ("Case & Qualification & Outcome & Class & Case annotation", "Case & Evidence endpoint / gate & Outcome & Class & Case annotation"),
    ("Qualified; 72/72 exact", "Text-path 72/72"),
    ("M4 HumanEval30 & Qualified; 90/90 exact", "M4 HumanEval30 & Text-path 90/90"),
    ("Blocked; gate failed", "Text-path; BLOCKED"),
    (r"Qualified;\newline 90/90 each exact", "Text-path 90/90 each"),
    ("Inadmissible; 45/90 exact", "Text-path 45/90"),
    ("Inadmissible; 60/90 exact", "Text-path 60/90"),
]


def main():
    original = SOURCE.read_text()
    rendered = original
    for old, new in REPLACEMENTS:
        if rendered.count(old) != 1:
            raise RuntimeError(f"Expected one frozen table phrase: {old}")
        rendered = rendered.replace(old, new)
    old_358h = "Qualified; 90/90 exact"
    if rendered.count(old_358h) != 2:
        raise RuntimeError("Expected two frozen 358H rows")
    rendered = rendered.replace(old_358h, "Direct-ID 90/90")
    data_rows = lambda value: value.split(r"\midrule", 1)[1].split(r"\bottomrule", 1)[0]
    numbers = lambda value: re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?(?:/\d+)?", data_rows(value))
    if numbers(original) != numbers(rendered):
        raise RuntimeError("A numerical value changed while rendering the endpoint overlay")
    if re.search(r"\bexact\b", rendered, re.I):
        raise RuntimeError("A bare exact label remains")
    OUTPUT.write_text("% AUTO-GENERATED FROM FROZEN STYLE TABLE; OUTPUT ENDPOINT LABELS ONLY.\n" + rendered)
    print("PASS: A4 row overlay; all numeric tokens and row order preserved")


if __name__ == "__main__":
    main()
