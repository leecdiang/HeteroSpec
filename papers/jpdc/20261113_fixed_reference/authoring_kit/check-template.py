#!/usr/bin/env python3
"""Check the official ZIP, without model execution or network access."""
from pathlib import Path
import zipfile
p = Path(__file__).with_name('els-cas-templates.zip')
with zipfile.ZipFile(p) as z:
    bad = z.testzip()
    if bad:
        raise SystemExit(f'ZIP CRC failed: {bad}')
    needed = ['README', 'manifest.txt', 'cas-sc.cls', 'cas-dc.cls',
              'cas-common.sty', 'cas-model2-names.bst', 'cas-refs.bib',
              'cas-sc-template.tex', 'cas-dc-template.tex', 'doc/elsdoc-cas.pdf']
    missing = [f for f in needed if 'els-cas-templates/' + f not in z.namelist()]
    if missing:
        raise SystemExit(f'Missing template files: {missing}')
print('PASS: ZIP integrity and required template files; PDF compilation is separate.')
