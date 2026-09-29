#!/usr/bin/env python3
"""Package the frozen collaboration draft; relocate dependencies without editing assets."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

HERE = Path(__file__).resolve().parents[1]
files = {}
visited = set()


def collect(source, destination):
    source = source.resolve()
    if source in visited:
        return
    visited.add(source)
    content = source.read_bytes()
    if source.suffix == '.tex':
        text = content.decode()
        pattern = r'\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}'
        for match in list(re.finditer(pattern, text)):
            path = match.group(1)
            dependency = HERE / path
            if not dependency.suffix:
                dependency = dependency.with_suffix('.tex')
            # All repository TeX inputs resolve from the manuscript build root.
            if path.startswith('../figures/'):
                target = 'publication/' + Path(path).name
                text = text.replace('{' + path + '}', '{' + target + '}')
            else:
                target = path
            collect(dependency, target)
        content = text.encode()
    if destination in files:
        assert files[destination] == content, ('package name collision', destination)
    files[destination] = content


for name in ('main.tex', 'appendix.tex'):
    collect(HERE / name, name)
files['references.bib'] = (HERE / 'references.bib').read_bytes()
for source in (HERE / 'vendor/official/mlsys2025style').iterdir():
    if source.suffix in ('.sty', '.bst'):
        files[source.name] = source.read_bytes()
files['README.txt'] = b'''B570 MECHANISM INTEGRATION FOR AUTHOR REVIEW -- v0.8

Upload this ZIP as a new Overleaf project. Use pdfLaTeX and TeX Live 2025.
Select main.tex for the full manuscript (measured runtime study included).
Select appendix.tex to compile the separate appendix, then restore main.tex.
Locally: latexmk -pdf main.tex; latexmk -pdf appendix.tex.

Hardware evidence is closed. The synthesis is retrospective; campaign primary
outcomes were frozen independently. Separate runtime studies retain the blocked
358H qualification and prospective M4 result. The B570 target-only UB1 predictor was frozen before reserved inference; it
predicted 72/72 complete serialized sequences. The direct Guard/Always-Spec
contrast is post-study secondary analysis of frozen observations. No new
measurements were collected. This is not a final submission.

Only dependency paths are relocated. Figure PDF bytes, the inventory table,
official style, scientific values, bibliography, and manuscript prose are kept.
This source bundle is for author collaboration, not an anonymous artifact release.
No shared Overleaf project or collaborator invitation is created by packaging.
'''
manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
files['SHA256SUMS.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
out = HERE / 'output/overleaf-mechanism-integration-v0.8.zip'
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(files.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 9, 25, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, data)
print(f'Packaged {len(files)} files: {out}')

