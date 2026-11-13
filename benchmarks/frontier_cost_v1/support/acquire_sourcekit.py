"""Acquire the pinned public source ZIP and extract unchanged loop4 + frontend.

Only public source is fetched. No model, native binary, GPU job or remote command
is involved. Every extracted member is checked against the manifest inside the
whole-file-hashed ZIP. Existing destinations and partial downloads are retained.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import stat
import urllib.request
import zipfile

URL = "https://github.com/leecdiang/HeteroSpec/releases/download/tpds-phase1-rtx-review-v2-evidence-20261107/rtx-phase1-source.zip"
EXPECTED_BYTES = 39003959
EXPECTED_SHA = "57cbfbfe43ae1c4b4ed5ba3f5261412daa2b5c14b712e76d868da55f4f8a4101"
MANIFEST_SHA = "8d37214bb699565c535b52d3fd4439786f3e45c2d40a1aaff6db948c27366a1f"
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "sourcekit")
    parser.add_argument("--archive", type=Path, help="Existing exact ZIP; no download when supplied")
    args = parser.parse_args()
    out = args.out
    if out.exists() or out.is_symlink():
        raise ValueError("fresh extraction destination required")
    out.mkdir(parents=True)
    archive = args.archive
    if archive is None:
        archive = out / "rtx-phase1-source.zip"
        with urllib.request.urlopen(URL, timeout=60) as source, archive.open("xb") as destination:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                destination.write(chunk)
    archive_bytes = archive.read_bytes()
    if len(archive_bytes) != EXPECTED_BYTES or sha(archive_bytes) != EXPECTED_SHA:
        raise ValueError("source ZIP identity differs; retained but not extracted")
    checked = []
    with zipfile.ZipFile(archive) as source:
        manifest_bytes = source.read("SOURCE_ASSET_MANIFEST.json")
        if sha(manifest_bytes) != MANIFEST_SHA:
            raise ValueError("manifest identity differs")
        manifest = json.loads(manifest_bytes)["files"]
        members = source.infolist()
        names = set()
        for member in members:
            name = PurePosixPath(member.filename)
            if name.is_absolute() or ".." in name.parts or "\\" in member.filename or any(":" in part for part in name.parts):
                raise ValueError("unsafe archive path")
            if member.filename in names or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("duplicate or symlink member")
            names.add(member.filename)
            if member.is_dir() or not member.filename.startswith(("native/cores/loop4/", "native/frontend/")):
                continue
            payload = source.read(member)
            expected = manifest.get(member.filename)
            if expected != {"bytes": len(payload), "sha256": sha(payload)}:
                raise ValueError("member identity differs: " + member.filename)
            destination = out / member.filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(payload)
            checked.append(member.filename)
        expected_names = {name for name in manifest if name.startswith(("native/cores/loop4/", "native/frontend/"))}
        if set(checked) != expected_names:
            raise ValueError("source membership incomplete")
        with (out / "SOURCE_ASSET_MANIFEST.json").open("xb") as stream:
            stream.write(manifest_bytes)
    report = dict(schema="heterospec.native-tail.source-acquisition.v1", url=URL,
                  source_archive_sha256=EXPECTED_SHA, source_archive_bytes=EXPECTED_BYTES,
                  manifest_sha256=MANIFEST_SHA, checked_members=len(checked),
                  loop4_members=sum(name.startswith("native/cores/loop4/") for name in checked),
                  numerical_source_edits=False, numerical_reference_qualification="NOT_RUN",
                  status="SOURCE_HASH_VERIFIED")
    (out / "ACQUISITION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
