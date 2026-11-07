#!/usr/bin/env python3
"""Validate Phase-6 reading aids without changing frozen scientific values."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from pypdf import PdfReader
import pymupdf


ROOT = Path(__file__).resolve().parents[3]
MS = ROOT / "paper/mlsys2027/manuscript"
EVIDENCE = ROOT / "paper/mlsys2027/evidence"
START = "33aec6fe5c71912889b22e63a2b9295a9b5685e6"


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS:", label)


def read(relative):
    return (MS / relative).read_text(encoding="utf-8")


def old(relative):
    return subprocess.check_output(["git", "show", f"{START}:{relative}"], cwd=ROOT)


def pdf_text(relative):
    reader = PdfReader(MS / relative)
    return reader, "\n".join(page.extract_text() or "" for page in reader.pages)


def main():
    figure2_tex = read("figures/06_translation.tex")
    figure2_source = read("figures/presentation_v083/figure2.tex")
    figure2, figure2_text = pdf_text("figures/presentation_v083/figure2.pdf")
    check(all(phrase in figure2_text for phrase in
              ("Local execution", "Path qualification", "Realized cost",
               "Diagnose blocked path", "Target-partition", "qualified", "blocked")),
          "Figure 2 required evaluation nodes and branches")
    check("independently frozen case studies" in figure2_tex and
          "not causal progression across platforms" in figure2_tex and
          "evaluation order" in figure2_tex,
          "Figure 2 caption rules out cross-platform causal chain")
    check(not re.search(r"\d", figure2_text) and
          not any(name in figure2_text for name in ("B570", "358H", "M4", "RTX")) and
          "mechanism_v05" not in figure2_tex and
          "begin{tikzpicture}" in figure2_source,
          "Figure 2 has no new numeric claim or platform sequence")
    check(len(figure2.pages) == 1 and
          abs(float(figure2.pages[0].mediabox.width) - 486) < .02 and
          "<image" not in read("figures/presentation_v083/figure2.svg"),
          "Figure 2 native vector asset")

    timeline = read("tables/b570_timeline_v083.tex")
    diagnoses = read("sections/05_diagnoses.tex")
    ledger = json.loads((EVIDENCE / "B570_PREDICTION_COMMITMENT_LEDGER_V083.json").read_text())
    counts = ledger["aggregate_checks"]
    check((counts["discovery_H1_exact_pairs"], counts["reserved_prompt_count"],
           counts["repetition_count_per_prompt"], counts["prediction_count"],
           counts["predictor_live_exact_pairs"], counts["reference_live_exact_pairs"]) ==
          (36, 24, 3, 72, 72, 60), "timeline numbers match frozen ledger")
    for phrase in ("12 exposed prompts", "3 repetitions", "36/36", "24 prompts",
                   "72 complete generated-token-ID predictions", "72 live serialized reserved runs",
                   "72/72", "60/72 BLOCKED"):
        check(phrase in timeline, "timeline: " + phrase)
    bands = ("DISCOVERY (outcome-exposed)", "FREEZE BOUNDARY", "RESERVED VALIDATION")
    check(timeline.index(bands[0]) < timeline.index(bands[1]) < timeline.index(bands[2]) and
          timeline.index("predictions fixed before live outcomes") <
          timeline.index("72 live serialized reserved runs") and
          timeline.count(r"\midrule") == 2 and
          r"\input{tables/b570_timeline_v083.tex}" in diagnoses,
          "discovery, freeze, reserved prediction and live order visibly separated")
    check(not re.search(r"\b[0-9a-f]{40}\b|github|/Users/|leecdiang|heterospec\.git",
                        timeline, re.I) and
          "72/72 qualified" not in timeline.lower() and
          "root cause" not in timeline.lower(),
          "timeline anonymity and scientific guardrails")

    table1 = read("tables/01_platforms_v05.tex")
    previous = old("paper/mlsys2027/manuscript/tables/01_platforms_v05.tex").decode()
    tabular = lambda text: text.split(r"\begin{tabular}", 1)[1].split(r"\end{tabular}", 1)[0]
    check(tabular(table1) == tabular(previous), "Table 1 factual cells unchanged")
    check("Independently frozen case studies; not a matched hardware comparison" in table1,
          "Table 1 explicitly excludes matched hardware comparison")

    source = read("figures/presentation_v05/plot.py")
    figure4, figure4_text = pdf_text("figures/presentation_v05/pdf/state.pdf")
    check("Arithmetic-mean timing breakdown" in figure4_text and
          "Replay/reconstruction + proposal" in figure4_text and
          "(inseparable)" in figure4_text and
          "Separate prompt-GM speedup" in figure4_text,
          "Figure 4 in-panel timing and inseparability boundaries")
    check("Arithmetic-mean timing breakdown" in source and
          "Replay/reconstruction + proposal" in source,
          "Figure 4 labels regenerated from plotting source")
    receipt_path = "paper/mlsys2027/manuscript/figures/presentation_v05/qa/state.json"
    current_receipt = json.loads((ROOT / receipt_path).read_text())
    previous_receipt = json.loads(old(receipt_path))
    check(current_receipt["inputs"] == previous_receipt["inputs"] and
          current_receipt["artists"] == previous_receipt["artists"] and
          current_receipt["out_of_bounds_text"] == [] and
          len(figure4.pages) == 1 and
          abs(float(figure4.pages[0].mediabox.width) - 486) < .01,
          "Figure 4 plotted values, ordering and components unchanged")
    for value in ("87.34%", "58.35%", "13.25 s", "27.54 s", "0.734", "0.352"):
        check(value in figure4_text, "Figure 4 rendered frozen value: " + value)

    for relative in ("figures/03_verification.tex",
                     "figures/presentation_v07/plot.py",
                     "figures/presentation_v07/pdf/verification.pdf",
                     "figures/presentation_v07/svg/verification.svg"):
        path = "paper/mlsys2027/manuscript/" + relative
        check((ROOT / path).read_bytes() == old(path), "Figure 3 unchanged: " + relative)
    check(hashlib.sha256((MS / "figures/presentation_v05/pdf/state.pdf").read_bytes()).hexdigest() !=
          hashlib.sha256(old("paper/mlsys2027/manuscript/figures/presentation_v05/pdf/state.pdf")).hexdigest(),
          "Figure 4 presentation asset regenerated")

    main, main_text = pdf_text("output/manuscript-v0.8.3-phase6-preview.pdf")
    appendix, appendix_text = pdf_text("output/appendix-v0.8.3-phase6-preview.pdf")
    check(len(main.pages) == 12 and len(appendix.pages) == 8,
          "Phase-6 previews retain 10-body/2-reference and 8-appendix pages")
    for phrase in ("B570 discovery to reserved validation", "36/36", "72/72", "60/72",
                   "BLOCKED", "Arithmetic-mean timing breakdown",
                   "Replay/reconstruction + proposal", "Independently frozen case studies"):
        check(phrase in main_text, "main preview renders: " + phrase)
    check("Our three contributions are" in main.pages[0].extract_text() and
          "72/72" in main.pages[0].extract_text(), "first-page central story retained")
    forbidden = re.compile(r"github\.com|/Users/|Projects/HeteroSpec|leecdiang|"
                           r"paper/mlsys2027-reviewer-convergence|(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])",
                           re.I)
    check(not forbidden.search(main_text + appendix_text), "anonymous previews have no private provenance")
    for name in ("manuscript", "appendix"):
        current_path = MS / f"output/{name}-v0.8.3-phase6-preview.pdf"
        baseline_path = MS / f"output/{name}-v0.8.3-phase5-preview.pdf"
        current_doc = pymupdf.open(current_path)
        baseline_doc = pymupdf.open(baseline_path)
        current_fonts = {row[0]: row[3].split("+")[-1]
                         for page in current_doc for row in page.get_fonts(full=True)}
        baseline_fonts = {row[3].split("+")[-1]
                          for page in baseline_doc for row in page.get_fonts(full=True)}
        check(all(len(current_doc.extract_font(xref)[3]) > 0 for xref in current_fonts),
              name + " fonts embedded")
        check(set(current_fonts.values()) == baseline_fonts,
              name + " font families unchanged from Phase 5")
    print("PHASE-6 PRESENTATION: PASS")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, KeyError) as error:
        print("PHASE-6 PRESENTATION: FAIL:", error, file=sys.stderr)
        sys.exit(1)
