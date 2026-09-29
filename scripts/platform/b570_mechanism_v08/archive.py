"""Portable content-addressed evidence packaging; excludes model weights."""
import gzip, hashlib, io, json, shutil, subprocess, tarfile
from datetime import datetime, timezone
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
PROTOCOL=REPO/'benchmarks/b570_mechanism_v08'
ARTIFACT=REPO/'artifacts/b570_mechanism_v08'
START='31e756f3311cee4226bd1be57ee6febadd032aa4'

def sha(path):return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def proof(destination):
    directory=destination/'provenance/git_objects';directory.mkdir(parents=True,exist_ok=True)
    commits=git('rev-list','--reverse',START+'..HEAD').decode().splitlines()
    commits=[START]+commits;result={'starting_main':START,'head_before_archive':git('rev-parse','HEAD').decode().strip(),'commits':{}}
    relevant=['benchmarks/b570_mechanism_v08/DISCOVERY_PLAN.md','benchmarks/b570_mechanism_v08/exposure_inventory.json','benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json','benchmarks/b570_mechanism_v08/hypothesis_freeze.json','benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json','scripts/platform/b570_mechanism_v08/study.py','scripts/platform/b570_mechanism_v08/harness.cpp']
    def object_bytes(kind,oid):
        data=git('cat-file',kind,oid)
        if hashlib.sha1((kind+' '+str(len(data))+'\0').encode()+data).hexdigest()!=oid:raise RuntimeError('Git object identity mismatch')
        (directory/oid).write_bytes(data);return data
    for commit in commits:
        data=object_bytes('commit',commit)
        lines=data.decode('utf-8').splitlines();tree=lines[0].split()[1];parents=[x.split()[1] for x in lines if x.startswith('parent ')]
        record={'tree':tree,'parents':parents,'files':{}};object_bytes('tree',tree)
        for rel in relevant:
            found=git('ls-tree',commit,'--',rel).decode().strip()
            if not found:continue
            mode,kind,oid=found.split('\t')[0].split();object_bytes('blob',oid)
            record['files'][rel]={'blob':oid,'sha256':sha(directory/oid)}
            parts=rel.split('/')
            for i in range(1,len(parts)):
                subtree=git('rev-parse',commit+':'+ '/'.join(parts[:i])).decode().strip();object_bytes('tree',subtree)
        result['commits'][commit]=record
    save(destination/'provenance/git_checkpoints.json',result)

def main():
    if not (PROTOCOL/'CLOSEOUT.md').exists():raise RuntimeError('Closeout required before evidence packaging')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination=REPO/'work/b570_mechanism_v08'/('bundle-'+stamp)
    destination.mkdir(parents=True,exist_ok=False)
    def copy(source,rel):
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for prefix in ['benchmarks/b570_mechanism_v08','scripts/platform/b570_mechanism_v08','artifacts/b570_mechanism_v08/raw']:
        for source in (REPO/prefix).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:copy(source,source.relative_to(REPO))
    for rel in ['benchmarks/b570_direct_id_v1/protocol_v1.json','benchmarks/b570_direct_id_v1/instrumentation.patch','scripts/platform/b570_direct_id_v1/common.py','datasets/humaneval/HumanEval.jsonl.gz']:
        copy(REPO/rel,rel)
    copy(REPO/'work/b570_direct_id_v1/formal-v1-20260929-local/executions.json','provenance/historical_executions.json')
    copy(REPO/'work/b570_direct_id_v1/upstream-0cae43063.zip','source/upstream-0cae43063.zip')
    for source in Path('C:/hs/b570-mechanism-v08-build/Release').glob('*'):
        if source.suffix.lower() in ('.exe','.dll'):copy(source,'runtime/'+source.name)
    for source in Path('C:/hs/b570-direct-id-v1-build/bin/Release').glob('*'):
        if source.suffix.lower() in ('.exe','.dll'):copy(source,'runtime/serialized/'+source.name)
    proof(destination)
    copy(PROTOCOL/'INDEPENDENT_VALIDATION.json','provenance/local_independent_validation.json')
    readme='''# B570 mechanism v0.8 portable evidence

Run with Python 3.12+ (no GPU, Vulkan, model weights, or Python dependencies required):

    python scripts/platform/b570_mechanism_v08/verify.py --root .

Inventory validation:

    python scripts/platform/b570_mechanism_v08/verify_archive.py .

Included bytes: protocol, exposure inventory, deterministic reserved selection, pinned upstream source archive, harness and runners, runtime executable/DLLs, historical direct-ID execution records, all new raw captures/logs/commands, freeze manifests, analyses, independent validation, and Git checkpoint objects.

External assets: model weights are omitted. Their recorded target/draft SHA-256 identities are compared with frozen historical protocol. Static/import libraries and local exposure-audit source files are represented by recorded digests, not verified bytes in this bundle. NO_KNOWN_B570_EXPOSURE refers to the available audited records; it makes no assertion about deleted or unavailable records.

The archive SHA-256 must be checked against the separately delivered ARCHIVE.json before extraction. This inventory verifies every included file. The independent verifier recomputes task selection, generated-ID endpoints, sequence comparisons, coverage, placement and chronology applicable to the reached phases. A failed qualification has no hypothesis/prediction/outcome checkpoint to validate.
'''
    (destination/'README.md').write_text(readme,encoding='utf-8')
    inventory={str(p.relative_to(destination)).replace('\\','/'):sha(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    save(destination/'SHA256_INVENTORY.json',{'schema':'heterospec.b570.mechanism.bundle.v08','files':inventory,'model_weights_included':False})
    check=subprocess.run(['python',str(destination/'scripts/platform/b570_mechanism_v08/verify.py'),'--root',str(destination),'--output',str(PROTOCOL/'PORTABLE_VALIDATION.json')],cwd=REPO)
    if check.returncode:raise RuntimeError('Hardware-free bundle validation failed')
    temporary=ARTIFACT/'bundle.pending.tar.gz'
    with temporary.open('wb') as file:
        with gzip.GzipFile(filename='',mode='wb',fileobj=file,mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w') as tar:
                for path in sorted(destination.rglob('*')):
                    if not path.is_file():continue
                    info=tar.gettarinfo(str(path),arcname=str(path.relative_to(destination)).replace('\\','/'))
                    info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
                    with path.open('rb') as data:tar.addfile(info,data)
    digest=sha(temporary);final=ARTIFACT/(digest+'.tar.gz');temporary.replace(final)
    save(ARTIFACT/'ARCHIVE.json',{'schema':'heterospec.b570.mechanism.archive.v08','sha256':digest,'filename':final.name,'bytes':final.stat().st_size,'files':len(inventory)+1,'head_before_archive':git('rev-parse','HEAD').decode().strip(),'hardware_free_verifier':'scripts/platform/b570_mechanism_v08/verify.py','model_weights_included':False,'portable_verifier_status':'PASS'})
    print(json.dumps({'archive':str(final),'sha256':digest,'bytes':final.stat().st_size}))

if __name__=='__main__':main()
