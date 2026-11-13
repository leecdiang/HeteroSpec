#!/usr/bin/env python3
"""Build the author-review documents with CPU tools only.

The fallback repairs missing local TeX filename/format/font-map caches without
changing the system installation. It does not install packages or access a GPU.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

def run(args, *, cwd=None, env=None, log=None):
    if cwd is None:
        cwd = ROOT
    p = subprocess.run(args, cwd=cwd, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if log:
        Path(log).write_text(p.stdout)
    if p.returncode:
        print(p.stdout[-12000:], file=sys.stderr)
        raise RuntimeError(f"Command failed ({p.returncode}): {args[0]}")
    return p.stdout

def tex_environment():
    env = os.environ.copy()
    env.setdefault("SOURCE_DATE_EPOCH", "1794528000")
    env["FORCE_SOURCE_DATE"] = "1"
    if not shutil.which("pdflatex") or not shutil.which("bibtex"):
        raise RuntimeError("Install a complete TeX Live distribution with pdflatex, bibtex, natbib and CAS dependencies.")
    check = subprocess.run(["kpsewhich", "pdflatex.fmt"], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    article = subprocess.run(["kpsewhich", "article.cls"], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check.returncode == 0 and check.stdout.strip() and article.stdout.strip():
        return env, "system TeX installation"
    trees = [p for p in [Path("/etc/texmf"), Path("/usr/share/texmf"),
                         Path("/usr/share/texlive/texmf-dist")] if p.exists()]
    if not trees:
        raise RuntimeError("TeX source trees not found; a complete TeX Live installation is required.")
    cache = BUILD / "tex_cache"
    cache.mkdir(parents=True, exist_ok=True)
    env.update(TEXMF="{" + ",".join(map(str, trees)) + "}",
               TEXMFVAR=str(cache/"var"), TEXMFCONFIG=str(cache/"config"),
               TEXFORMATS=str(cache)+"//:", TEXFONTMAPS=str(cache)+"//:")
    for name in ["var", "config"]:
        (cache/name).mkdir(exist_ok=True)
    if not (cache/"pdflatex.fmt").exists():
        run(["pdftex", "-ini", "-interaction=nonstopmode", "-halt-on-error",
             "-jobname=pdflatex", "-progname=pdflatex", "*pdflatex.ini"],
            cwd=cache, env=env, log=cache/"format.log.txt")
    maps = [
        "/usr/share/texmf/fonts/map/dvips/lm/lm.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/amsfonts/cm.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/amsfonts/cmextra.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/amsfonts/symbols.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/amsfonts/latxfont.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/tetex/ps2pk35.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/psnfss/pazo.map",
        "/usr/share/texlive/texmf-dist/fonts/map/dvips/psnfss/fpls.map",
    ]
    (cache/"pdftex.map").write_text("\n".join(Path(p).read_text() for p in maps if Path(p).exists()))
    return env, "local format and font-map cache (system sources retained)"

def build(target, env):
    args = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
            "-file-line-error", "-output-directory="+str(BUILD), target+".tex"]
    for step in range(1, 4):
        run(args, env=env, log=BUILD/f"{target}.pass{step}.txt")
        if step == 1 and "\\bibdata" in (BUILD/f"{target}.aux").read_text():
            benv = env.copy()
            benv["BIBINPUTS"] = str(ROOT)+os.pathsep+benv.get("BIBINPUTS", "")
            run(["bibtex", target], cwd=BUILD, env=benv, log=BUILD/f"{target}.bibtex.txt")
    log = (BUILD/f"{target}.log").read_text(errors="replace")
    errors = [line for line in log.splitlines() if
              ("undefined" in line.lower() and ("reference" in line.lower() or "citation" in line.lower()))]
    if errors:
        raise RuntimeError("Unresolved references/citations: " + " | ".join(errors))
    info = run(["pdfinfo", str(BUILD/f"{target}.pdf")]) if shutil.which("pdfinfo") else ""
    pages = next((int(line.split(":",1)[1]) for line in info.splitlines() if line.startswith("Pages:")), None)
    shutil.copy2(BUILD/f"{target}.pdf", ROOT/f"{target}.pdf")
    return {"document": target, "pages": pages, "pdf_bytes": (ROOT/f"{target}.pdf").stat().st_size,
            "overfull_warnings": [line for line in log.splitlines() if "Overfull" in line],
            "unresolved_references": errors}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", choices=["main","supplement","highlights","all"], default="all")
    ap.add_argument("--figures", action="store_true", help="Regenerate figures from included public inputs before building.")
    args=ap.parse_args()
    BUILD.mkdir(exist_ok=True)
    if args.figures:
        run([sys.executable, str(ROOT/"scripts/build_figures.py")], log=BUILD/"figures.txt")
    env, mode=tex_environment()
    targets=["main","supplement","highlights"] if args.target=="all" else [args.target]
    result={"tex_mode":mode,"model_calls":0,"gpu_contexts":0,
            "documents":[build(t,env) for t in targets]}
    (BUILD/"build_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    main()
