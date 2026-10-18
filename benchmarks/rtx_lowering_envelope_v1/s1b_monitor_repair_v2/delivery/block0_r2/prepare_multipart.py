"""Bounded CPU transport fragments; original ZIP/raw experiment bytes unchanged."""
import hashlib,json,zipfile
from pathlib import Path
from common import V,load,save,sha
import publication as P

def prepare(f,out,d):
    original=out/'raw/raw-000.zip.part';desc=load(out/'raw/ARCHIVE.json');assert sha(original)==desc['sha256'] and len(desc['parts'])==1
    dst=out/'raw_api';dst.mkdir(exist_ok=False);parts=[]
    with original.open('rb') as stream:
        for i in range(1024):
            b=stream.read(1024**2)
            if not b:break
            p=dst/f'raw-{i:03d}.zip.part';p.write_bytes(b);parts.append(dict(name=p.name,bytes=len(b),sha256=sha(p)))
        else:raise RuntimeError('fragment cap')
    h=hashlib.sha256()
    for row in parts:h.update((dst/row['name']).read_bytes())
    assert h.hexdigest()==desc['sha256'] and sum(r['bytes'] for r in parts)==desc['bytes']
    save(dst/'ARCHIVE.json',desc|dict(parts=parts,transport_fragment_bytes_max=1024**2,original_ZIP_bytes_unchanged=True))
    manifest=load(out/'RAW_MANIFEST.json');save(out/'RESULT_RAW_MANIFEST.json',manifest|dict(archive=load(dst/'ARCHIVE.json'),original_single_part_manifest_sha256=sha(out/'RAW_MANIFEST.json'),members_unchanged=True))
    save(out/'TRANSPORT_LAYOUT.json',dict(active_archive_directory='raw_api',manifest='RESULT_RAW_MANIFEST.json',original_archive_preserved=str(original),archive_sha256=desc['sha256'],original_ZIP_bytes_unchanged=True,reason='large transport request connection/timeout/401;no GPU retry or registration change'))
    # All CPU transfer receipts remain locally. Small records are also sealed as
    # one auxiliary archive. Redundant large HTTP encoding/read scratch is kept
    # locally with exact hashes and reconstructible source,never called science raw.
    members={};omitted=[]
    with zipfile.ZipFile(out/'CPU_TRANSFER_RECORDS.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((out/'cpu_ledger').rglob('*')):
            if not p.is_file() or d in p.parents:continue
            rel=p.relative_to(out).as_posix();row=dict(bytes=p.stat().st_size,sha256=sha(p))
            if p.stat().st_size>1024**2:omitted.append(dict(path=rel,**row,retained_locally=True,redundant_CPU_transport_scratch_not_experimental_raw=True));continue
            members[rel]=row;z.write(p,rel)
        z.writestr('MANIFEST.json',json.dumps(members,separators=(',',':'))+'\n')
    save(out/'CPU_TRANSFER_RECORDS_MANIFEST.json',dict(members=members,large_redundant_transport_scratch_retained_locally=omitted,archive_sha256=sha(out/'CPU_TRANSFER_RECORDS.zip')))
    selected=[]
    for folder in [out,V/'authorizations/clean0_r2',V/'execution_ledger',V/'delivery/cpu_ledger']:
        for p in folder.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p==original or out/'cpu_ledger' in p.parents:continue
            selected.append(p)
    rows=P.stage_exact(f['repository'],selected)
    # Remove only an index entry for the unpublished monolithic transport copy;
    # original file + original local commit + every experimental byte are retained.
    import subprocess
    rel=original.relative_to(Path(f['repository'])).as_posix()
    subprocess.run([f['git']['path'],'-C',f['repository'],'update-index','--force-remove','--',rel],check=True)
    assert original.exists() and sha(original)==desc['sha256']
    save(d/'MULTIPART_PREPARED.json',dict(parts=len(parts),archive_sha256=desc['sha256'],all_original_ZIP_bytes_unchanged=True,scientific_raw_members_unchanged=242,staged_files=rows,GPU_queries=0))
