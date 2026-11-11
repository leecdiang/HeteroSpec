"""Recover fixed native sources and verify existing immutable assets; CPU only."""
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import zipfile
from common import BASE, DESIGN, JOURNALS, need, load, write_new, sha, utc

GIT='C:/hs/pr108-tools/git/cmd/git.exe'
REPO=DESIGN.parents[1]
GEOM=Path('C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1')
QH=Path('C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1')

def git(*args):
    p=subprocess.run([GIT,*args],cwd=REPO,capture_output=True,timeout=60)
    need(p.returncode==0,'fixed git object unavailable '+str(args))
    return p.stdout

def fixed(commit,path,actual=None):
    data=git('show',commit+':'+path)
    if actual is not None:need(Path(actual).read_bytes()==data,'local asset does not match fixed git bytes '+path)
    return data

def main():
    lock=load(DESIGN/'SOURCE_LOCK.json');records=[]
    for row in lock['sources']:
        need(git('cat-file','-t',row['commit']).strip()==b'commit','fixed source commit absent')
    runtime=json_bytes=fixed(lock['sources'][0]['commit'],'benchmarks/b570_geometry_state_codesign_v1/p0/RUNTIME.json',GEOM/'p0/RUNTIME.json')
    import json
    runtime=json.loads(runtime)
    checked=[]
    for row in list(runtime['models'].values())+runtime['driver_files']+runtime['import_libraries']:
        need(Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256'],'asset drift '+row['path'])
        checked.append(row)
    for role in runtime['roles'].values():
        for row in role['modules']+role['files']:
            need(Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256'],'runtime drift '+row['path'])
            checked.append(row)
    target=BASE/'sources/actor';target.mkdir(exist_ok=False)
    data=fixed(lock['sources'][2]['commit'],'benchmarks/b570_query_head_lowering_v1/host/ACTOR_SOURCE_FIXED.zip',QH/'host/ACTOR_SOURCE_FIXED.zip')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            need(not Path(name).is_absolute() and '..' not in Path(name).parts,'archive traversal')
            p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
            records.append(dict(path=str(p),source_member=name,sha256=sha(p),bytes=p.stat().st_size))
    original=BASE/'sources/original';original.mkdir(exist_ok=False)
    for row in runtime['roles']['old']['modules']+runtime['roles']['old']['files']:
        dest=original/row['name'];shutil.copyfile(row['path'],dest)
        need(sha(dest)==row['sha256'],'original runtime copy identity')
    # One immutable copy of the numerical DLLs for the new actor/replay build.
    numerical=BASE/'sources/numerical';numerical.mkdir(exist_ok=False)
    for row in runtime['roles']['old']['modules']:
        if row['name'].startswith('ggml'):
            shutil.copyfile(row['path'],numerical/row['name'])
    inputs=fixed(lock['sources'][0]['commit'],'benchmarks/b570_geometry_state_codesign_v1/p0/SENTINEL_PANEL.json',GEOM/'p0/SENTINEL_PANEL.json')
    write_new(JOURNALS/'SENTINELS.json',json.loads(inputs))
    qh=fixed(lock['sources'][2]['commit'],'benchmarks/b570_query_head_lowering_v1/native/query_head.h',QH/'native/query_head.h')
    need((target/'source/query_head.h').read_bytes()==qh,'actor source QH implementation differs from fixed candidate')
    reviews=list(Path('C:/Users/DIANG/.codex/sessions/2026/10/16').glob('*01a142cf-fac7-7a22-b7b8-f49a5305610a.jsonl'))
    need(len(reviews)==1,'actual independent design review log')
    shutil.copyfile(reviews[0],JOURNALS/'DESIGN_REVIEW_ROLLOUT.jsonl')
    write_new(JOURNALS/'ASSET_RECOVERY.json',dict(recorded_utc=utc(),source_lock_sha256=sha(DESIGN/'SOURCE_LOCK.json'),
        design_commit='67ef96e1f393231464f7e38ec6c344b784c4b1a4',assets=checked,actor_sources=records,
        actor_archive_sha256=hashlib.sha256(data).hexdigest(),
        model_copy_bytes=0,original_runtime_copy_byte_identical=True,
        pinned_source='C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/pr97/dependencies/pinned-source',
        pinned_import_libraries=runtime['import_libraries'],driver_version=runtime['driver_version'],
        native_process_starts=0,GPU_queries=0,model_requests=0))
    print('Recovered',len(records),'fixed actor files; verified',len(checked),'runtime/model/driver assets; GPU/model starts=0')

if __name__=='__main__':main()
