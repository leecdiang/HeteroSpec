#!/usr/bin/env python3
"""Verify PR220 assets and rebuilt PDFs in a clean GitHub checkout."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
EXPECTED_PACKAGE_MANIFEST_SHA256 = "bdebb1810cdb64641d121f6a5dec6a0dd65d19ebef3e95b70fce104170e5db1e"
EXPECTED_ARCHIVE_MEMBERS = 130
EXPECTED_MANIFEST_FILES = 129
EXPECTED_PAGES = {"main.pdf": 14, "journal.pdf": 10}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checkout_identity() -> tuple[str, str]:
    commit = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True
    ).strip()
    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or ""
    return commit, branch


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def source_check(out: Path) -> dict:
    package_manifest = ROOT / "author_archive_root" / "PACKAGE_MANIFEST.json"
    if not package_manifest.is_file() or package_manifest.is_symlink():
        raise RuntimeError("Pinned PACKAGE_MANIFEST.json is missing or is a symlink")
    manifest_bytes = package_manifest.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    if manifest_sha != EXPECTED_PACKAGE_MANIFEST_SHA256:
        raise RuntimeError(f"PACKAGE_MANIFEST SHA256 mismatch: {manifest_sha}")
    manifest = json.loads(manifest_bytes)
    if len(manifest) != EXPECTED_MANIFEST_FILES:
        raise RuntimeError(f"Expected {EXPECTED_MANIFEST_FILES} manifest entries, found {len(manifest)}")

    verified, total_bytes = [], len(manifest_bytes)
    for name, info in sorted(manifest.items()):
        rel = PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or "\\" in name:
            raise RuntimeError(f"Unsafe manifest path: {name!r}")
        if name.startswith(("paper/", "validation/", "visual_review/")):
            dest = ROOT.joinpath(*rel.parts)
        else:
            dest = ROOT / "author_archive_root" / Path(*rel.parts)
        if not dest.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError(f"Manifest path escapes source root: {name}")
        if not dest.is_file() or dest.is_symlink():
            raise RuntimeError(f"Missing/non-regular source asset: {dest}")
        data = dest.read_bytes()
        actual_sha = sha256_bytes(data)
        if len(data) != int(info["bytes"]) or actual_sha != str(info["sha256"]):
            raise RuntimeError(
                f"Asset mismatch {name}: bytes {len(data)}/{info['bytes']}, "
                f"sha256 {actual_sha}/{info['sha256']}"
            )
        total_bytes += len(data)
        verified.append(name)

    if len(verified) + 1 != EXPECTED_ARCHIVE_MEMBERS:
        raise RuntimeError("Archive member accounting mismatch")
    commit, branch = checkout_identity()
    result = {
        "status": "PASS",
        "source": "fresh GitHub checkout",
        "commit_sha": commit,
        "branch": branch,
        "source_archive_reference": {"filename": "HeteroSpec_Final_20261111_Author.zip", "sha256": "e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b", "zip_present_in_checkout": False},
        "verification_method": "Pinned PACKAGE_MANIFEST SHA256 plus per-file SHA256 for every extracted author asset",
        "package_manifest_sha256": manifest_sha,
        "archive_members_verified": len(verified) + 1,
        "manifest_entries_verified": len(verified),
        "total_asset_bytes": total_bytes,
        "assets": verified,
    }
    write_json(out, result)
    return result


def pdfinfo(path: Path) -> tuple[int, str]:
    output = run(["pdfinfo", str(path)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not read page count for {path}")
    return int(match.group(1)), output


def pdf_text(path: Path, out: Path) -> str:
    run(["pdftotext", "-layout", str(path), str(out)])
    return out.read_text(encoding="utf-8", errors="replace")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def font_report(path: Path) -> dict:
    output = run(["pdffonts", str(path)])
    lines = [line for line in output.splitlines()[2:] if line.strip()]
    embedded, type3 = [], 0
    for line in lines:
        parts = line.split()
        if len(parts) >= 8:
            embedded.append(parts[-5] == "yes")
        if "Type 3" in line:
            type3 += 1
    return {
        "font_count": len(lines),
        "all_embedded": bool(lines) and all(embedded),
        "type3_count": type3,
        "raw": output,
    }


def render_pdf(path: Path, directory: Path, stem: str) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    run(["pdftoppm", "-png", "-r", "100", str(path), str(directory / stem)])
    return sorted(directory.glob(stem + "-*.png"))


def compare_pixels(reference: Path, generated: Path, scratch: Path) -> dict:
    from PIL import Image, ImageChops, ImageStat

    ref_pages = render_pdf(reference, scratch / (reference.stem + "-ref"), "page")
    out_pages = render_pdf(generated, scratch / (generated.stem + "-out"), "page")
    if len(ref_pages) != len(out_pages):
        return {"reference_pages": len(ref_pages), "generated_pages": len(out_pages),
                "same_dimensions": False, "pixel_identical": False,
                "mean_absolute_channel_difference": None, "changed_pixel_fraction": None}
    means, changed, total = [], 0, 0
    dimensions_ok, exact = True, True
    for ref_path, out_path in zip(ref_pages, out_pages):
        with Image.open(ref_path) as a0, Image.open(out_path) as b0:
            a, b = a0.convert("RGB"), b0.convert("RGB")
            if a.size != b.size:
                dimensions_ok = exact = False
                continue
            diff = ImageChops.difference(a, b)
            means.append(sum(ImageStat.Stat(diff).mean) / 3.0)
            histogram = diff.convert("L").histogram()
            pixels = a.size[0] * a.size[1]
            changed += pixels - histogram[0]
            total += pixels
            if diff.getbbox() is not None:
                exact = False
    return {
        "reference_pages": len(ref_pages),
        "generated_pages": len(out_pages),
        "same_dimensions": dimensions_ok,
        "pixel_identical": exact and dimensions_ok and len(means) == len(ref_pages),
        "mean_absolute_channel_difference": (sum(means) / len(means)) if means else None,
        "changed_pixel_fraction": (changed / total) if total else None,
        "raster_dpi": 100,
    }


def pdf_check(baseline_dir: Path, out: Path) -> dict:
    paper = ROOT / "paper"
    reports, failures = {}, []
    with tempfile.TemporaryDirectory(prefix="pr220-pdf-check-") as td:
        scratch = Path(td)
        for name, expected_pages in EXPECTED_PAGES.items():
            generated, reference = paper / name, baseline_dir / name
            if not generated.is_file() or not reference.is_file():
                failures.append(f"missing generated/reference {name}")
                continue
            pages, info = pdfinfo(generated)
            ref_pages, ref_info = pdfinfo(reference)
            text = pdf_text(generated, scratch / (name + ".txt"))
            ref_text = pdf_text(reference, scratch / ("reference-" + name + ".txt"))
            fonts = font_report(generated)
            report = {
                "generated_sha256": sha256_file(generated),
                "reference_sha256": sha256_file(reference),
                "byte_identical": sha256_file(generated) == sha256_file(reference),
                "pages": pages,
                "reference_pages": ref_pages,
                "expected_pages": expected_pages,
                "page_count_pass": pages == expected_pages and ref_pages == expected_pages,
                "text_exact": text == ref_text,
                "text_whitespace_normalized": normalize_text(text) == normalize_text(ref_text),
                "text_characters": len(text),
                "fonts": {k: v for k, v in fonts.items() if k != "raw"},
                "pixel_comparison": compare_pixels(reference, generated, scratch / "raster"),
                "pdfinfo": info,
                "reference_pdfinfo": ref_info,
                "pdffonts": fonts["raw"],
            }
            reports[name] = report
            if not report["page_count_pass"]:
                failures.append(f"{name}: unexpected page count")
            if not report["text_whitespace_normalized"]:
                failures.append(f"{name}: extracted content differs after whitespace normalization")
            if not fonts["all_embedded"] or fonts["type3_count"] != 0:
                failures.append(f"{name}: font embedding/Type3 check failed")

    commit, branch = checkout_identity()
    result = {
        "status": "PASS" if not failures else "FAIL",
        "source": "fresh GitHub checkout",
        "commit_sha": commit,
        "branch": branch,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "pdfs": reports,
        "failures": failures,
        "interpretation": (
            "PDF binary hashes are reported separately from extracted text, page counts, "
            "embedded fonts and 100-dpi raster comparisons. Serialization/metadata "
            "differences do not by themselves imply changed paper content."
        ),
    }
    write_json(out, result)
    if failures:
        raise RuntimeError("; ".join(failures))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets-only", action="store_true")
    ap.add_argument("--pdf-check", action="store_true")
    ap.add_argument("--baseline-dir", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.assets_only:
        result = source_check(args.out)
    elif args.pdf_check:
        if args.baseline_dir is None:
            ap.error("--baseline-dir is required with --pdf-check")
        result = pdf_check(args.baseline_dir, args.out)
    else:
        ap.error("choose --assets-only or --pdf-check")
    print(json.dumps({k: v for k, v in result.items() if k not in ("assets", "pdfs")}, indent=2))


if __name__ == "__main__":
    main()
