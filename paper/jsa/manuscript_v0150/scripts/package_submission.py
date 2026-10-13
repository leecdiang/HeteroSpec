#!/usr/bin/env python3
"""Build and verify a flat LaTeX source archive for author review before upload."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
from figure_catalog import FIGURES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def brace_argument(text: str, start: int) -> tuple[str, int]:
    """Read balanced LaTeX braces, including nested math and formatting macros."""
    assert text[start] == "{"
    depth = 1
    end = start + 1
    while end < len(text) and depth:
        if text[end] in "{}" and text[end - 1] != "\\":
            depth += 1 if text[end] == "{" else -1
        end += 1
    if depth:
        raise ValueError("Unclosed caption")
    return text[start + 1:end - 1], end


def run(command: list[str], cwd: Path, log: Path) -> None:
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(command, cwd=cwd, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, timeout=120)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    highlights = (ROOT / "Highlights.txt").read_text().splitlines()
    assert 3 <= len(highlights) <= 5
    assert all(0 < len(line) <= 85 for line in highlights)
    caption_files = []
    for document, folder, filename in (
        ("main", "sections", "Figure_captions.tex"),
        ("supplement", "supplement", "Supplement_figure_captions.tex"),
    ):
        captions = []
        for path in sorted((ROOT / folder).glob("*.tex")):
            for match in re.finditer(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", path.read_text(), re.S):
                block = match.group()
                start = block.index(r"\caption{") + len(r"\caption")
                captions.append(brace_argument(block, start)[0])
        identifiers = [number for number, _, doc in FIGURES if doc == document]
        assert len(captions) == len(identifiers), document
        caption_text = "\n\n".join(f"Figure {number}. {caption}"
                                   for number, caption in zip(identifiers, captions)) + "\n"
        (ROOT / filename).write_text(
            "% Editable figure captions; inline mathematics uses LaTeX notation.\n" + caption_text)
        caption_files.append(filename)
    sources = sorted([*ROOT.glob("*.tex"), *ROOT.glob("sections/*.tex"),
                      *ROOT.glob("supplement/*.tex"), *ROOT.glob("figures/*.tex"),
                      ROOT / "references.bib", ROOT / "psql-num.bst"])
    names = {p.relative_to(ROOT).as_posix(): p.relative_to(ROOT).as_posix().replace("/", "_")
             for p in sources}
    assert len(set(names.values())) == len(names)
    assert all(len(name) <= 80 for name in names.values())
    source_zip = OUTPUT / "JSA_v0153_flat_sources.zip"
    latex, bibtex = shutil.which("pdflatex"), shutil.which("bibtex")
    if not latex or not bibtex:
        raise SystemExit("pdfLaTeX and BibTeX are required to verify the flat package.")
    with tempfile.TemporaryDirectory(prefix="heterospec-submission-") as temporary:
        flat = Path(temporary)
        for path in sources:
            text = path.read_text()
            def flatten(match: re.Match) -> str:
                target = match.group(1)
                key = target if target.endswith(".tex") else target + ".tex"
                if key not in names:
                    raise ValueError(f"Unpackaged input: {path}: {target}")
                return r"\input{" + names[key] + "}"
            text = re.sub(r"\\input\{([^}]+)\}", flatten, text)
            (flat / names[path.relative_to(ROOT).as_posix()]).write_text(text)
        for filename in ("Highlights.txt", *caption_files):
            shutil.copy2(ROOT / filename, flat / filename)
        members = sorted(p.name for p in flat.iterdir())
        with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in members:
                archive.write(flat / name, name)
        # Verify the delivered archive after extraction, not only the staging tree.
        rebuild = flat / "extracted"
        rebuild.mkdir()
        with zipfile.ZipFile(source_zip) as archive:
            assert all("/" not in name for name in archive.namelist())
            archive.extractall(rebuild)
        for stem in ("main", "supplement"):
            command = [latex, "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"]
            run(command, rebuild, rebuild / f"{stem}.pass1.txt")
            run([bibtex, stem], rebuild, rebuild / f"{stem}.bibtex.txt")
            for pass_number in (2, 3):
                run(command, rebuild, rebuild / f"{stem}.pass{pass_number}.txt")
            log = (rebuild / f"{stem}.log").read_text(errors="replace")
            bad = [r"Overfull \\hbox", r"Overfull \\vbox", r"There were undefined",
                   r"LaTeX Warning: (?:Reference|Citation) .* undefined"]
            assert not any(re.search(pattern, log) for pattern in bad), stem
            shutil.copy2(rebuild / f"{stem}.log", OUTPUT / f"flat_{stem}.log")
    package = OUTPUT / "JSA_v0153_author_package.zip"
    files = sorted(p for p in ROOT.rglob("*") if p.is_file()
                   and "output" not in p.relative_to(ROOT).parts
                   and "__pycache__" not in p.relative_to(ROOT).parts
                   and p.suffix not in {".pyc", ".spl"})
    files += [OUTPUT / "main.pdf", OUTPUT / "supplement.pdf", source_zip]
    files += [OUTPUT / "figures" / f"Figure_{number}_{name}.pdf" for number, name, _ in FIGURES]
    assert all(p.exists() for p in files)
    manifest = {
        "version": "0.15.3", "date": "2026-10-13",
        "base_pr": 102, "base_head": "e22c3565366094baa2980594b42223e57565455f",
        "status": "AUTHOR_REVIEW_REQUIRED_NOT_SUBMITTED",
        "flat_source_rebuild": "PASS: both documents, extracted ZIP in clean temporary directory",
        "highlight_character_counts": list(map(len, highlights)),
        "files": {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
    }
    manifest_path = OUTPUT / "FINAL_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files + [manifest_path]:
            archive.write(path, path.relative_to(ROOT))
    with zipfile.ZipFile(source_zip) as archive:
        assert all("/" not in name for name in archive.namelist())
    print(f"Verified flat compilation and {len(files)} author-package files.")
    print(source_zip)
    print(package)


if __name__ == "__main__":
    main()
