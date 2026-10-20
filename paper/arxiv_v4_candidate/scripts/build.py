#!/usr/bin/env python3
"""Build the review-only manuscript. Requires local LaTeX/BibTeX installation."""
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"

def run(args, cwd, log, env):
    with log.open("w", encoding="utf-8") as stream:
        p = subprocess.run(args, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if p.returncode:
        raise SystemExit(f"Command failed: {args}; inspect {log}")

def main():
    latex = shutil.which("pdflatex")
    bibtex = shutil.which("bibtex")
    if not latex or not bibtex:
        raise SystemExit("Install pdflatex, bibtex, elsarticle, TikZ/PGFPlots and required packages.")
    OUT.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["BIBINPUTS"] = str(ROOT) + os.pathsep + env.get("BIBINPUTS", "")
    env["BSTINPUTS"] = str(ROOT) + os.pathsep + env.get("BSTINPUTS", "")
    cmd = [latex, "-interaction=nonstopmode", "-halt-on-error", "-output-directory=output", "main.tex"]
    run(cmd, ROOT, OUT / "pass1.log", env)
    run([bibtex, "main"], OUT, OUT / "bibtex.log", env)
    run(cmd, ROOT, OUT / "pass2.log", env)
    run(cmd, ROOT, OUT / "pass3.log", env)
    pdf = OUT / "main.pdf"
    if not pdf.exists() or pdf.stat().st_size < 10000:
        raise SystemExit("PDF missing or unexpectedly small.")
    log = (OUT / "main.log").read_text(errors="replace")
    warnings = [line for line in log.splitlines() if "Overfull \\\\hbox" in line or "Overfull \\\\vbox" in line or "undefined" in line.lower()]
    if warnings:
        raise SystemExit("Review warnings before acceptance:\\n" + "\\n".join(warnings))
    print(f"Built {pdf} ({pdf.stat().st_size} bytes). Visual page review is still required.")

if __name__ == "__main__":
    main()
