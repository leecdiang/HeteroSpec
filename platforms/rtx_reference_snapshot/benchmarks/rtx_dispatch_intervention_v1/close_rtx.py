"""CPU-only local packaging, fresh restore and new-interpreter re-audit."""
import argparse,hashlib,json,os,re,shutil,subprocess,time,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha
from prepare_rtx import root
def allocation(paths):
    unique={};logical=count=0
    for folder in paths:
        if not Path(folder).exists():continue
        for p in Path(folder).rglob('*'):
            if p.is_file():
                st=p.stat();logical+=st.st_size;count+=1;unique[st.st_dev,st.st_ino]=((st.st_size+4095)//4096)*4096+4096
    return dict(files=count,logical_bytes=logical,conservative_unique_allocation_bytes=sum(unique.values()),unique_files=len(unique))
def snapshot():
    r=root();dest=r/'source_runtime';dest.mkdir();s=load(r/'RUN_SPEC.json')
    for p in V.iterdir():
        if p.is_file() and p.suffix in ['.py','.h','.cpp','.txt','.md','.json']:shutil.copyfile(p,dest/p.name)
    for name in ['collector.exe','address_cpu.exe','libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(V/'build'/name,dest/name)
    for source in [Path(s['ggml_include']),Path(s['vendor_include'])]:
        for p in source.rglob('*'):
            if p.is_file() and p.suffix in ['.h','.hpp']:
                target=dest/'external_headers'/source.name/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    assert {n:sha(Path(s['runtime_directory'])/n) for n in s['numerical_DLLs']}==s['numerical_DLLs']
def package():
    r=root();dest=Path(str(r)+'-archive');dest.mkdir();index={};blobs={};files=[]
    for p in sorted(r.rglob('*')):
        if not p.is_file():continue
        assert not p.is_symlink();rel=p.relative_to(r).as_posix();h=sha(p);binary=p.suffix=='.bin';index[rel]=dict(bytes=p.stat().st_size,sha256=h,storage='blob' if binary else 'file')
        if binary:blobs.setdefault(h,p)
        else:files.append((rel,p))
    save(dest/'MEMBERS.json',index);start=time.monotonic()
    with zipfile.ZipFile(dest/'raw.zip','x',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        z.write(dest/'MEMBERS.json','MEMBERS.json')
        for rel,p in files:assert sha(p)==index[rel]['sha256'];z.write(p,'files/'+rel)
        for h,p in blobs.items():assert sha(p)==h;z.write(p,'blobs/'+h)
    usage=allocation([r,dest]);assert usage['conservative_unique_allocation_bytes']<8*1024**3-512*1024**2
    save(dest/'ARCHIVE.json',dict(status='SEALED_LOCAL',archive_path=str(dest/'raw.zip'),archive_sha256=sha(dest/'raw.zip'),archive_bytes=(dest/'raw.zip').stat().st_size,manifest_sha256=sha(dest/'MEMBERS.json'),members=len(index),logical_member_bytes=sum(v['bytes'] for v in index.values()),unique_binary_blobs=len(blobs),raw_location=str(r),retention='RAW_LOCAL_ONLY',seconds=time.monotonic()-start,storage=usage,GPU_calls=0))
    print('archive',len(index),sha(dest/'raw.zip'),flush=True)
def restore():
    r=root();arc=Path(str(r)+'-archive');info=load(arc/'ARCHIVE.json');assert sha(arc/'raw.zip')==info['archive_sha256'];fresh=Path(str(r)+'-fresh');fresh.mkdir();start=time.monotonic()
    with zipfile.ZipFile(arc/'raw.zip') as z:
        index=json.loads(z.read('MEMBERS.json'));assert index==load(arc/'MEMBERS.json');binary=fresh/'binary_cas';binary.mkdir();restored=fresh/'raw';restored.mkdir()
        for h in sorted({v['sha256'] for v in index.values() if v['storage']=='blob'}):
            data=z.read('blobs/'+h);assert hashlib.sha256(data).hexdigest()==h;(binary/(h+'.bin')).write_bytes(data)
        for rel,row in index.items():
            path=PurePosixPath(rel);assert not path.is_absolute() and '..' not in path.parts and '\\' not in rel and ':' not in rel;dest=restored/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if row['storage']=='blob':
                source=binary/(row['sha256']+'.bin')
                try:os.link(source,dest)
                except OSError as exc:
                    if getattr(exc,'winerror',None)!=1142:raise
                    shutil.copyfile(source,dest)
            else:dest.write_bytes(z.read('files/'+rel))
            assert dest.stat().st_size==row['bytes'] and sha(dest)==row['sha256']
    usage=allocation([r,arc,fresh]);assert usage['conservative_unique_allocation_bytes']<8*1024**3
    save(fresh/'RESTORE.json',dict(status='ALL_MEMBERS_EXACT',members=len(index),archive_sha256=info['archive_sha256'],manifest_sha256=info['manifest_sha256'],same_host=True,external_review=False,seconds=time.monotonic()-start,storage=usage));print('restored',len(index),flush=True)
def replay():
    r=root();fresh=Path(str(r)+'-fresh');arc=Path(str(r)+'-archive');s=load(r/'RUN_SPEC.json');environ=os.environ.copy();environ['HETEROSPEC_RUN_ROOT']=str(fresh/'raw');source=fresh/'raw/source_runtime';start=time.monotonic()
    cmd=[s['python'],'-B',str(source/'audit_final_rtx.py'),'--out',str(fresh/'analysis')];p=subprocess.run(cmd,env=environ,capture_output=True,timeout=900)
    save(fresh/'CPU_REPLAY.json',dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-start,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));assert p.returncode==0,'fresh new-interpreter CPU audit failure'
    equality={}
    for file in (r/'analysis').iterdir():
        if file.is_file():assert file.read_bytes()==(fresh/'analysis'/file.name).read_bytes(),file.name;equality[file.name]=sha(file)
    extra=[]
    for label,cmd in [('trace',[str(source/'trace_summary.py'),'--out',str(fresh/'trace_analysis')]),('identity',[str(source/'identity_audit.py'),'--out',str(fresh/'IDENTITY_AUDIT.json')]),('archival',[str(source/'verify_archival.py'),'--out',str(fresh/'ARCHIVAL_AUDIT.json')])]:
        began=time.monotonic();q=subprocess.run([s['python'],'-B',*cmd],env=environ,capture_output=True,timeout=900);save(fresh/(label+'_REPLAY.json'),dict(command=cmd,exit=q.returncode,seconds=time.monotonic()-began,stdout=q.stdout.decode(errors='replace'),stderr=q.stderr.decode(errors='replace')));assert q.returncode==0,label
        if label=='trace':
            for file in (r/'trace_analysis').iterdir():assert file.read_bytes()==(fresh/'trace_analysis'/file.name).read_bytes();equality['trace/'+file.name]=sha(file)
        else:assert load(r/(label.upper()+'_AUDIT.json'))==load(fresh/(label.upper()+'_AUDIT.json'));equality[label]=sha(r/(label.upper()+'_AUDIT.json'))
    save(arc/'FRESH_RECOMPUTE.json',dict(status='PASS',all_member_bytes_exact=True,new_interpreter=True,same_host=True,external_review=False,scientific_files_byte_equal=equality,remote_raw_uploaded=False,CPU_seconds=time.monotonic()-start,GPU_calls=0));print('fresh CPU recomputation PASS',flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['snapshot','package','restore','replay']);a=ap.parse_args();globals()[a.action]()
