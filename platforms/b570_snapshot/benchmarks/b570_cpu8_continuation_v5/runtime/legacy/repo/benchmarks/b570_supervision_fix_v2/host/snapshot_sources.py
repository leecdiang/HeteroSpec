"""Keep source-only restoration import trees separate from compiled build evidence."""
import hashlib
import json
from pathlib import Path


def source_members(design, snapshot, source_only=False):
    design=Path(design);snapshot=Path(snapshot)
    paths=[p for p in (design/'host').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    dll=design/'host/LauncherCapture.dll'
    if source_only and dll in paths:
        if dll.is_symlink():raise ValueError('compiled artifact alias')
        data=dll.read_bytes();compiled=snapshot/'compiled';compiled.mkdir(exist_ok=False)
        retained=compiled/'LauncherCapture.dll'
        with retained.open('xb') as f:f.write(data)
        receipt=compiled/'BUILD_ARTIFACT.json'
        record=dict(original_path=str(dll),retained_path=str(retained),bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                    source_path=str(design/'host/LauncherCapture.cs'),
                    source_sha256=hashlib.sha256((design/'host/LauncherCapture.cs').read_bytes()).hexdigest(),
                    scope='Retained compiled bytes and source identity; not a claim of verified compiler behavior')
        with receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,sort_keys=True);f.write('\n')
        paths.remove(dll);paths.extend((retained,receipt))
    return paths
