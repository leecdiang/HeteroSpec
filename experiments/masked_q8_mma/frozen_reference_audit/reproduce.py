#!/usr/bin/env python3
"""Inspect an already-downloaded frozen runtime, without loading/executing it.

Python standard library plus NVIDIA cuobjdump. This does not compile any CUDA
source, call CUDA, download model weights, or perform a native experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

ZIP_SHA = '24d647dbf7bedb1003e766363d24cad04d55094290f1b06d6e17a342cb328d12'
DLL_SHA = '8df3d5d6363dab0b221f143992e816d1366be4b076b47ce6b1612a148c0bc09c'
SECTION_SHA = 'c5f1d0057fe2859da82daa8a806e7592d7c5fe74eccf562b651c349dba43c4a6'
Q1 = '_Z13mul_mat_vec_qIL9ggml_type8ELi1ELb0ELb0ELb0EEvPKvS2_PKi31ggml_cuda_mm_fusion_args_devicePfj5uint3jjjS7_jjjS7_jjjj'
Q4 = Q1.replace('ELi1ELb0', 'ELi4ELb0')
QUANT = '_Z13quantize_q8_1PKfPvxxxxxj5uint3'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def extract_section(dll, dest):
    with dll.open('rb') as src:
        src.seek(0x3c)
        pe = struct.unpack('<I', src.read(4))[0]
        src.seek(pe)
        if src.read(4) != b'PE\0\0':
            raise RuntimeError('Not PE')
        src.seek(pe + 6)
        n = struct.unpack('<H', src.read(2))[0]
        src.seek(pe + 20)
        optional_size = struct.unpack('<H', src.read(2))[0]
        src.seek(pe + 24 + optional_size)
        headers = [src.read(40) for _ in range(n)]
        for h in headers:
            if h[:8].rstrip(b'\0') != b'.nv_fatb':
                continue
            virtual_size, _, raw_size, offset = struct.unpack_from('<IIII', h, 8)
            if virtual_size > raw_size:
                raise RuntimeError('Section has unbacked bytes')
            src.seek(offset)
            remaining = virtual_size
            with dest.open('wb') as dst:
                while remaining:
                    b = src.read(min(1024 * 1024, remaining))
                    if not b:
                        raise RuntimeError('Truncated section')
                    dst.write(b)
                    remaining -= len(b)
            return {'file_offset': offset, 'bytes': virtual_size, 'sha256': sha(dest)}
    raise RuntimeError('No .nv_fatb section')

def isolate(module, names, out):
    """Save LF-normalized inspection snippets; not standalone PTX modules."""
    version = target = ''
    cap = None
    depth = 0
    started = False
    results = []
    with module.open() as f:
        for ln, line in enumerate(f, 1):
            if line.startswith('.version'):
                version = line.strip()
            if line.startswith('.target'):
                target = line.strip()
            if cap is None and line.startswith('.entry '):
                name = line.split()[1].split('(')[0]
                if name in names:
                    cap = [version+'\n', target+'\n', '.address_size 64\n', line]
                    start, depth, started = ln, 0, False
                    continue
            if cap is not None:
                cap.append(line)
                started |= '{' in line
                depth += line.count('{') - line.count('}')
                if started and depth == 0:
                    dest = out / (names[name] + '.ptx')
                    dest.write_bytes(''.join(cap).encode('utf-8'))
                    results.append({'file': dest.name, 'source_module': module.name,
                                    'source_start_line': start, 'source_end_line': ln,
                                    'sha256': sha(dest), 'entry': name})
                    cap = None
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runtime_zip', type=Path)
    ap.add_argument('cuobjdump', type=Path)
    ap.add_argument('--output', type=Path, default=Path('reproduced'))
    args = ap.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tool = str(args.cuobjdump.resolve())
    if sha(args.runtime_zip) != ZIP_SHA:
        raise RuntimeError('Runtime ZIP hash does not match PR174')
    members = ['modules/ggml-cuda.dll', 'modules/cudart64_12.dll',
               'candidate/binding.json', 'oracle/binding.json',
               'historical-core-commands/configure-1793705144164009100.json', 'index.json']
    with zipfile.ZipFile(args.runtime_zip) as z:
        index = json.loads(z.read('index.json'))
        for member in members:
            dest = output / member
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as src, dest.open('wb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            if member in index and sha(dest) != index[member]['sha256']:
                raise RuntimeError('Member hash mismatch: '+member)
    dll = output / 'modules/ggml-cuda.dll'
    if sha(dll) != DLL_SHA:
        raise RuntimeError('DLL hash mismatch')
    fatbin = output / 'ggml-cuda.nv_fatb'
    section = extract_section(dll, fatbin)
    if section['sha256'] != SECTION_SHA:
        raise RuntimeError('Section hash mismatch')
    commands = []
    def run(params, log, cwd=output):
        cmd = [tool, *map(str, params)]
        with (output / log).open('w') as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, cwd=cwd)
        (output / (log+'.err')).write_text(r.stderr)
        commands.append({'argv': cmd, 'cwd': str(cwd), 'exit_code': r.returncode})
        if r.returncode:
            raise RuntimeError('cuobjdump failed: '+r.stderr)
    run(['--version'], 'cuobjdump-version.txt')
    run(['-lelf', fatbin], 'elf-list.txt')
    run(['-lptx', fatbin], 'ptx-list.txt')
    modules = output / 'ptx_modules'
    modules.mkdir(exist_ok=True)
    run(['-xptx', 'ggml-cuda.228.sm_90.ptx,ggml-cuda.288.sm_90.ptx', fatbin], 'extract-ptx.txt', modules)
    cubins = output / 'cubin_modules'
    cubins.mkdir(exist_ok=True)
    run(['-xelf', 'ggml-cuda.76.sm_89.cubin', fatbin], 'extract-cubin.txt', cubins)
    run(['-sass', '-fun', Q1+','+Q4, cubins/'ggml-cuda.76.sm_89.cubin'], 'q8_mmvq_q1_q4_original_sm89.sass.txt')
    snippets = output / 'snippets'
    snippets.mkdir(exist_ok=True)
    entries = isolate(modules/'ggml-cuda.228.sm_90.ptx', {Q1:'q8_mmvq_q1.sm90',Q4:'q8_mmvq_q4.sm90'}, snippets)
    entries += isolate(modules/'ggml-cuda.288.sm_90.ptx', {QUANT:'quantize_q8_1.sm90'}, snippets)
    if len(entries) != 3:
        raise RuntimeError('Missing expected entries')
    receipt = {'runtime_zip_sha256': ZIP_SHA, 'dll_sha256': sha(dll),
               'section': section, 'commands': commands, 'snippets': entries,
               'gpu_execution': False, 'source_recompilation': False,
               'note': 'Native sm89 SASS is not the deployed sm120 driver-JIT output.'}
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
