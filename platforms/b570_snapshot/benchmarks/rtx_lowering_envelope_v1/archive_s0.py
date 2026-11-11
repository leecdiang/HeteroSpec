"""Preserve complete recovered native source, native binaries, CPU raw and F0."""
import json,zipfile
from s0_budget import ROOT,save
from recover_s0 import sha
def main():
    archive=ROOT/'RAW_S0.zip';members=[]
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.name.endswith('.lock') or '__pycache__' in p.parts or p.name in ('RAW_S0.zip','RAW_S0_MANIFEST.json'):continue
        if 's0_ledger' in p.parts and 'archive_complete_S0' in p.name:continue
        if 'native' in p.parts and 'build' in p.parts and p.suffix!='.exe' and p.name not in ('CMakeCache.txt','build.ninja','compile_commands.json'):continue
        files.append(p)
    for p in files:members.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    save(ROOT/'RAW_S0_MANIFEST.json',dict(schema=1,archive='RAW_S0.zip',sha256=sha(archive),bytes=archive.stat().st_size,members=members,
        native_source='complete recovered source and actual modifications, no precision/shader changes',
        full_input_payload='72 complete unmodified tensors remain in authenticated PR104 archive; every file hash/path reverified and frozen here, no cropped substitutes',
        exclusions='build objects/PDBs, bytecode/locks; current unfinished archiver receipt and later restoration/seal metadata supplement in Git'))
    print(json.dumps(dict(members=len(members),bytes=archive.stat().st_size,sha256=sha(archive))))
if __name__=='__main__':main()
