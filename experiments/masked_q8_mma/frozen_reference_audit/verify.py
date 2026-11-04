#!/usr/bin/env python3
"""Verify committed text evidence, and optionally a fresh extraction."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reproduced', type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root/'MANIFEST.json').read_text())
    count = 0
    for name, expected in manifest['files'].items():
        p = root/name
        if p.stat().st_size != expected['bytes'] or digest(p) != expected['sha256']:
            raise RuntimeError('Committed file mismatch: '+name)
        count += 1
    if args.reproduced:
        r = args.reproduced.resolve()
        identity = json.loads((root/'IDENTITY.json').read_text())
        for rel, expected in [('modules/ggml-cuda.dll',identity['cuda_dll']),
                              ('ggml-cuda.nv_fatb',identity['fatbin'])]:
            if digest(r/rel) != expected['sha256']:
                raise RuntimeError('Reproduced binary mismatch: '+rel)
        for name in ['q8_mmvq_q1.sm90.ptx','q8_mmvq_q4.sm90.ptx','quantize_q8_1.sm90.ptx']:
            if (r/'snippets'/name).read_bytes() != (root/'ptx'/name).read_bytes():
                raise RuntimeError('PTX snippet differs: '+name)
        if (r/'q8_mmvq_q1_q4_original_sm89.sass.txt').read_bytes() != (root/'sass/q8_mmvq_q1_q4.original_sm89.sass').read_bytes():
            raise RuntimeError('SASS text differs; check disassembler version before interpreting')
        receipt = json.loads((r/'receipt.json').read_text())
        if receipt['gpu_execution'] or receipt['source_recompilation']:
            raise RuntimeError('Invalid inspection-only receipt')
        if any(c['exit_code'] for c in receipt['commands']):
            raise RuntimeError('Extraction command failed')
        print('Fresh extraction matches committed PTX/SASS evidence.')
    print(f'Verified {count} committed text files.')

if __name__ == '__main__':
    main()
