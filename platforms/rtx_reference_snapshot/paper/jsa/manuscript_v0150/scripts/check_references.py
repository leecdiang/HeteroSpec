#!/usr/bin/env python3
"""Check citation coverage and compiled PDF links against the audited bibliography.

This is an offline transcription check, not a new literature or metadata search.
"""
from pathlib import Path
import hashlib
import json
import re

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def included_text(path: Path) -> str:
    text = path.read_text()
    return text + "\n" + "\n".join(
        included_text(ROOT / (name if name.endswith(".tex") else name + ".tex"))
        for name in re.findall(r"\\input\{([^}]+)\}", text)
    )


def main() -> None:
    source = (ROOT / "references.bib").read_text()
    blocks = re.split(r"(?=@\w+\{)", source)
    entries = {}
    for block in blocks:
        match = re.match(r"@\w+\{([^,]+),", block)
        if match:
            key = match.group(1)
            assert key not in entries, f"Duplicate bibliography key: {key}"
            entries[key] = block
    audit = json.loads((ROOT / "provenance/REFERENCE_AUDIT_V0153.json").read_text())
    assert len(entries) == audit["final_bib_entries"] == 30
    assert hashlib.sha256(source.encode()).hexdigest() == audit["bibliography_sha256"]
    report = {"version": "0.15.3", "bibliography_entries": len(entries), "documents": {}}
    used = set()
    for document in ("main", "supplement"):
        text = included_text(ROOT / f"{document}.tex")
        cited = {key.strip() for group in re.findall(r"\\cite\{([^}]+)\}", text)
                 for key in group.split(",")}
        used |= cited
        assert cited <= entries.keys(), cited - entries.keys()
        bbl = (ROOT / "output" / f"{document}.bbl").read_text()
        printed = re.findall(r"\\bibitem\{([^}]+)\}", bbl)
        assert len(printed) == len(set(printed)) and set(printed) == cited
        pdf = PdfReader(ROOT / "output" / f"{document}.pdf")
        uris = set()
        for page in pdf.pages:
            for ref in page.get("/Annots", []):
                action = ref.get_object().get("/A", {})
                if action.get("/URI"):
                    uris.add(str(action["/URI"]))
        checked = 0
        for key in cited:
            block = entries[key]
            urls = re.findall(r"url=\{([^}]+)\}", block)
            for url in urls:
                assert url.replace(r"\#", "#") in uris, (document, key, url)
                checked += 1
            for doi in re.findall(r"doi=\{([^}]+)\}", block):
                assert "https://doi.org/" + doi in uris, (document, key, doi)
                checked += 1
            if "lastchecked=" in block:
                assert r"\url{" + urls[0] + "}" in bbl, (document, key)
        report["documents"][document] = {"printed_references": len(cited),
                                         "verified_url_and_doi_links": checked}
    report["uncited_library_entries"] = sorted(entries.keys() - used)
    assert report["uncited_library_entries"] == audit["uncited_library_entries"] == ["qwen3"]
    report["status"] = "PASS_OFFLINE_CITATION_COVERAGE_AND_PDF_LINKS"
    report["limit"] = "Primary-source verification is recorded separately in REFERENCE_AUDIT_V0153.json."
    (ROOT / "provenance/REFERENCE_CHECKS_V0153.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
