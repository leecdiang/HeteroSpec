# Import the authenticated editable manuscript

The author archive is `HeteroSpec_Final_20261111_Author.zip`, SHA256 `e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b`. It is available to the user in the conversation, but the connected GitHub write API does not consume local sandbox filesystem paths. Thus, the initial PR is a **reviewable draft snapshot**, not a falsely claimed complete source upload.

In a trusted local clone on this PR branch, with that exact ZIP downloaded beside the checkout:

```bash
sha256sum HeteroSpec_Final_20261111_Author.zip
python3 - <<'PY'
from pathlib import Path, PurePosixPath
import hashlib, zipfile, stat
p=Path("HeteroSpec_Final_20261111_Author.zip")
expected="e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b"
if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
    raise SystemExit("AUTHOR ARCHIVE HASH MISMATCH")
target=Path("papers/reference_compatible/20261111_final/source")
if target.exists(): raise SystemExit("Source folder already exists; no overwrite")
with zipfile.ZipFile(p) as z:
    for item in z.infolist():
        name=PurePosixPath(item.filename)
        if name.is_absolute() or ".." in name.parts or "\\" in item.filename:
            raise SystemExit("Unsafe member path")
        if stat.S_ISLNK(item.external_attr >> 16):
            raise SystemExit("Refuse archive symlink")
    z.extractall(target)
if not (target/"paper"/"main.tex").is_file(): raise SystemExit("Missing LaTeX entrypoint")
print("Imported authenticated manuscript source; now rebuild and review")
PY
```

Retain original numerical data and statistical definitions. In the new source folder run the tests/build commands given by `REPRO_COMMANDS.md`, then independently compile the corresponding arXiv entrypoint with BibTeX. Keep source/figures/datasets in Git; generated auxiliary caches and private GPU captures do not belong in this PR.

Before marking ready for review, compare committed tree hashes, validate figure files in the compiled 10-page main / 14-page combined version, and add a source-import receipt documenting whether the PDF output agrees with the pinned version. **Do not automatically merge or publish.**
