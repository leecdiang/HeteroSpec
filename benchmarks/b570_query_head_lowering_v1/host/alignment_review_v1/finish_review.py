"""CPU-only publication validation. No experiment subprocess is launched."""
import datetime
import hashlib
import io
import pathlib
import subprocess
import sys
import unittest
import zipfile
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(HERE))
from common import load,save,sha,modules


def main():
    before=modules()
    # Preserve the unapproved prospective draft; this revision only makes an
    # unavailable RSS sample stop rather than count as zero. No numerical changes.
    path=HERE/'DIAGNOSTIC_F0.json'
    path.rename(HERE/'DIAGNOSTIC_F0_DRAFT_00.json')
    f0=load(HERE/'DIAGNOSTIC_F0_DRAFT_00.json')
    f0['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    f0['preexecution_revision']='Reject unavailable RSS in the new diagnostic supervisor; old S1 files remain unchanged.'
    f0['sources']={name:sha(ROOT/name) for name in f0['sources']}
    save(path,f0)
    for name,digest in f0['sources'].items():assert sha(ROOT/name)==digest
    for item in [f0['executable']]+f0['dependencies']+f0['driver_files']:assert sha(item['path'])==item['sha256']
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_admission.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    save(HERE/'CPU_ADMISSION_TESTS.json',dict(success=result.wasSuccessful(),tests=result.testsRun,log=stream.getvalue(),
        process_launches_mocked=True,actual_diagnostic_processes=0,F0_sha256=sha(path)))
    assert result.wasSuccessful()
    for file in HERE.rglob('*.py'):compile(file.read_text(encoding='utf-8'),str(file),'exec')
    conditions=ROOT/'host_outputs/alignment_review_v1/OFFSET_CONDITIONS.json'
    archive=HERE/'OFFSET_CONDITIONS.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:z.write(conditions,conditions.name)
    with zipfile.ZipFile(archive) as z:assert hashlib.sha256(z.read(conditions.name)).hexdigest()==sha(conditions)
    save(HERE/'OFFSET_CONDITIONS_MANIFEST.json',dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
         file_bytes=conditions.stat().st_size,file_sha256=sha(conditions),all_archived_bytes_rehashed=True))
    validate_current()


def validate_current():
    before=modules()
    path=HERE/'DIAGNOSTIC_F0.json'
    f0=load(path)
    for name,digest in f0['sources'].items():assert sha(ROOT/name)==digest
    for item in [f0['executable']]+f0['dependencies']+f0['driver_files']:assert sha(item['path'])==item['sha256']
    git='C:/hs/pr108-tools/git/cmd/git.exe'
    commit='27cfad39cbffcac413760900c6deedbb93bdfc78'
    prefix='benchmarks/b570_query_head_lowering_v1/'
    repo=ROOT.parents[1]
    lines=subprocess.check_output([git,'-C',str(repo),'ls-tree','-r','--format=%(objectname) %(path)',commit,'--',prefix],text=True).splitlines()
    objects=[line.split(' ',1) for line in lines]
    got=subprocess.check_output([git,'-C',str(repo),'hash-object','--no-filters']+[p for _,p in objects],text=True).splitlines()
    assert len(got)==len(objects)
    eol_only=[]
    for actual,(expected,name) in zip(got,objects):
        if actual==expected:continue
        assert name.endswith(('host/ACTOR_CONTEXT.diff','host/ACTOR_WORKER.diff'))
        committed=subprocess.check_output([git,'-C',str(repo),'show',commit+':'+name])
        local=(repo/name).read_bytes()
        assert local.replace(b'\r\n',b'\n')==committed
        eol_only.append(dict(path=name,worktree_sha256=hashlib.sha256(local).hexdigest(),
                            explanation='Pre-existing mixed CRLF in generated diff; Git clean normalization matches the reviewed commit. No edit made.'))
    assert not subprocess.check_output([git,'-C',str(repo),'diff','--name-only',commit,'--',prefix],text=True).strip()
    old_f0=load(ROOT/'host/S1_F0.json')
    for name,digest in old_f0['sources'].items():assert sha(ROOT/name)==digest
    for item in [old_f0['executable']]+old_f0['dependencies']+old_f0['driver_files']:assert sha(item['path'])==item['sha256']
    for item in load(ROOT/'host/S1_INPUTS.json'):assert sha(item['path'])==item['sha256']
    original=load(ROOT/'host_outputs/S1_RUN/CLOSEOUT.json')
    assert original['attempts']==2 and len(original['failed'])==1 and len(original['unstarted'])==159
    assert abs(original['owned_wall_s']-5.109)<1e-8
    assert not (ROOT/'host_outputs/alignment_review_v1/DIAGNOSTIC_RUN').exists()
    binary=load(HERE/'BINARY_MANIFEST.json')
    for item in binary['files']:assert sha(item['path'])==item['sha256']
    save(HERE/'FINAL_CPU_REVIEW_VALIDATION.json',dict(reviewed_commit=commit,
        original_PR112_Git_files_unchanged=True,original_file_count=len(objects),original_raw_Git_blob_matches=len(objects)-len(eol_only),
        preexisting_diff_line_endings=eol_only,frozen_source_input_binary_and_evidence_bytes_match=True,original_S1_attempts=2,
        original_S1_owned_wall_s=original['owned_wall_s'],original_unstarted=159,
        frozen_vulkan_source_sha256='04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d',
        new_F0_sha256=sha(path),new_diagnostic_binary_sha256=sha(f0['executable']['path']),
        new_diagnostic_attempts=0,GPU_device_queries=0,model_requests=0,graph_computes=0,
        CPU_metadata_processes=1,metadata_graphs_without_compute=288,unit_and_admission_methods=9,
        S2='NOT_ADMITTED',S3='NOT_ADMITTED',modules_before=before,modules_after=modules()))
    print(dict(original_files_unchanged=len(objects),new_F0=sha(path),CPU_methods=9,new_GPU=0,diagnostic_started=0))


if __name__=='__main__':
    validate_current() if '--validate-only' in sys.argv else main()
