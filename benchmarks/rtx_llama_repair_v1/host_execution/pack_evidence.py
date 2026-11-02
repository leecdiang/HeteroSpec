"""Explicit multi-root adaptation of the pinned parent's every-member ZIP packer.

Include failed epochs, original historical raw, full source and explicitly named
runtime binaries. Never include model weights, compiler caches or credentials.
Run only after native work and all scientific audits have finished.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import zipfile


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--repo',type=Path,required=True)
    a=p.parse_args();assert not a.out.exists();assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    assert Path('E:/rtx160/research/epoch07/INDEPENDENT_COST.json').exists()
    assert Path('E:/rtx160/research/epoch07/INDEPENDENT_QUALIFICATION.json').exists()
    assert Path('E:/rtx160/research/LEDGER_AUDIT.json').exists()
    a.out.mkdir(parents=True);started=time.monotonic();files={};runtime=[]
    def add(path,name,kind='evidence'):
        assert path.is_file() and not path.is_symlink()
        assert not name.startswith('/') and '..' not in Path(name).parts and name not in files
        assert path.suffix.lower() not in ('.gguf','.pem') and path.name not in ('.env','credentials.json')
        if path.suffix.lower()=='.key':
            # This source-capsule member is an upstream Keynote presentation.
            assert name.endswith('/source/docs/development/llama-star/idea-arch.key')
        if path.suffix.lower() in ('.exe','.dll'):assert kind=='runtime';runtime.append(name)
        files[name]=path
    def tree(root,prefix):
        assert root.is_dir(),root
        for f in sorted(root.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                add(f,prefix+'/'+f.relative_to(root).as_posix())
    root=Path('E:/rtx160')
    for folder in ('research','parent159','preparation01','exposure01','exposure02','exposure03','exposure04','protocol_before_hostfix01'):
        tree(root/folder,folder)
    add(root/'host_schema_config07.json','host_schema_config07.json')
    tree(Path('D:/rtx160/research/history01'),'historical-reconstruction')
    tree(Path('D:/rtx151-llama-diagnostic-v2'),'original-PR151-raw')
    for label,path in [('PR156_LEDGER.jsonl','D:/rtx155/epoch01/LEDGER.jsonl'),
                       ('PR159_LEDGER.jsonl','D:/rtx158/research/LEDGER.jsonl'),
                       ('PR159_INDEPENDENT_AUDIT.json','D:/rtx158/research/INDEPENDENT_AUDIT01.json')]:
        add(Path(path),'historical-ledgers/'+label)
    # Transport receipts are necessarily produced after this immutable archive;
    # deliver them in a separately indexed and freshly downloaded metadata asset.
    operations=Path('D:/rtx160/operations')
    for f in sorted(operations.rglob('*')):
        if f.is_file() and not f.name.startswith(('PACK','ARCHIVE','UPLOAD','REMOTE','DELIVERY','PUBLISH','TRANSPORT')):
            add(f,'operations/'+f.relative_to(operations).as_posix())
    tree(a.repo/'scripts/experiments/rtx_llama_repair_v1','protocol-source')
    tree(a.repo/'benchmarks/rtx_llama_repair_v1','execution-source')
    for name in ('ENGINEERING_POLICY.md','README.md','HOST_PROMPT.md'):
        add(a.repo/'benchmarks/rtx_reference_repair_v1'/name,'inherited-protocol/'+name)
    for config in sorted(p for p in root.glob('*config*') if p.is_dir()):
        tree(config/'stage',config.name+'/stage');tree(config/'build/source',config.name+'/source')
        for f in sorted(config.glob('*.json')):add(f,config.name+'/'+f.name)
        for f in sorted((config/'build').iterdir()):
            if f.is_file() and f.suffix not in ('.obj','.lib','.pdb'):add(f,config.name+'/build/'+f.name)
        for name in ('compile_commands.json','CMakeCache.txt','build.ninja','ar.cmd','ranlib.cmd'):
            f=config/'build/core'/name
            if f.exists():add(f,config.name+'/compiler/'+name)
        for f in (config/'build/bin').glob('*.exe'):add(f,config.name+'/runtime/'+f.name,'runtime')
    for helper in ('operator01','tokenizer01'):
        for f in sorted((root/helper).rglob('*')):
            if not f.is_file() or f.suffix in ('.dll','.obj','.lib','.pdb'):continue
            if f.suffix=='.exe':add(f,helper+'/'+f.relative_to(root/helper).as_posix(),'runtime')
            else:add(f,helper+'/'+f.relative_to(root/helper).as_posix())
    for cohort,folder in [('metadata4',Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-metadata4-v4/bin')),
                          ('original',Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4/bin')),
                          ('dense14b',Path('D:/rtx155/build01/bin'))]:
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in ('.exe','.dll'):add(f,'original-runtime/'+cohort+'/'+f.name,'runtime')
        for name in ('BUILD.json','SOURCE_MEMBERS.json','worker.cpp','arm_spec.h'):
            add(folder.parent/name,'original-runtime/'+cohort+'/'+name)
        tree(folder.parent/'source','original-runtime/'+cohort+'/source')
        for name in ('configure.log','core.log','link.log','worker.log'):
            add(folder.parent/name,'original-runtime/'+cohort+'/'+name)
    for name in ('SOURCE_RUNTIME.zip','SOURCE_RUNTIME_V02.zip'):
        add(Path('D:/hsc95')/name,'original-source-capsules/'+name)
    add(root/'PR160_PROTOCOL_BASE02.zip','original-source-capsules/PR160_PROTOCOL_BASE.zip')
    add(root/'PR160_PROTOCOL_SOURCE_RECEIPT.json','original-source-capsules/PROTOCOL_SOURCE_RECEIPT.json')
    add(root/'PR160_PROTOCOL_BASE.zip','engineering-failures/PR160_PROTOCOL_BASE.failed01.zip')
    total=sum(f.stat().st_size for f in files.values())
    assert shutil.disk_usage(a.out).free>total+20*1024**3,'uncompressed worst-case archive disk reserve'
    groups=[];group=[];size=0;limit=512*1024**2
    for name,f in sorted(files.items()):
        if group and size+f.stat().st_size>limit:groups.append(group);group=[];size=0
        group.append((name,f));size+=f.stat().st_size
    if group:groups.append(group)
    entries=[];parts=[]
    for index,group in enumerate(groups):
        path=a.out/('evidence-%03d.zip'%index);current=[]
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
            for name,f in group:
                before=f.stat();digest=sha(f);z.write(f,name)
                assert f.stat().st_size==before.st_size and f.stat().st_mtime_ns==before.st_mtime_ns,'source changed during archival'
                current.append({'path':name,'part':path.name,'bytes':before.st_size,'sha256':digest})
        with zipfile.ZipFile(path) as z:
            assert z.namelist()==[e['path'] for e in current]
            for e in current:
                h=hashlib.sha256();count=0
                with z.open(e['path']) as f:
                    for block in iter(lambda:f.read(1024**2),b''):h.update(block);count+=len(block)
                assert count==e['bytes'] and h.hexdigest()==e['sha256']
        entries+=current;parts.append({'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path)})
        print('ARCHIVED_AND_READ_BACK',index+1,len(groups),len(current),flush=True)
    report={'status':'LOCAL_ARCHIVE_READBACK_PASS','files':entries,'parts':parts,'remote_uploaded':False,
      'external_reader_verified':False,'explicit_runtime_members':runtime,'seconds':time.monotonic()-started,
      'parent_archive_sha256':sha(root/'parent159/archive.py'),'script_sha256':sha(Path(__file__)),
      'source_map':{name:str(f) for name,f in files.items()},
      'scope':'Complete new research, every failed attempt and operation receipt, authenticated PR151 raw, full staged and patched sources, explicit original/new runtime binaries, tokenizer/pool/exposure provenance. Model weights and compiler caches excluded; original model identities remain pinned.'}
    with (a.out/'RAW_ACCESS.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print('LOCAL_ARCHIVE_READBACK_PASS',len(entries),len(parts),flush=True)


if __name__=='__main__':main()
