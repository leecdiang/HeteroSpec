"""Separate content-addressed author packages, parts and fresh offline reconstruction."""
import argparse,gzip,json,shutil,subprocess,sys,tarfile,os
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now
def longpath(p):
    p=Path(p).absolute()
    return Path('\\\\?\\'+str(p)) if os.name=='nt' and not str(p).startswith('\\\\?\\') else p
ROOT=longpath(ROOT);STUDY=longpath(STUDY)
ART={'A':ROOT/'artifacts/rtx_trajectory_sufficiency_v4','B':ROOT/'artifacts/rtx_matched_qualification_cost_v3'}
def inventory(stage,mode,arm,anonymous=False):
    files={p.relative_to(stage).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(stage.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
    save(stage/'MANIFEST.json',{'schema':'RTX_V4.portable_inventory','mode':mode,'arm':arm,'anonymous':anonymous,'files':files,'omitted':['weights','downloaded dataset','runtime/frontends/compiler/driver binaries','credentials','bytecode/build caches'],'offline_scope':'retained arrays/tapes/timers and content digests; omitted external bytes cannot be authenticated'})
def publish(stage,mode,arm,anonymous=False):
    stage=longpath(stage);seen={};links=[]
    for p in sorted(stage.rglob('*')):
        if not p.is_file() or p.is_symlink() or not p.stat().st_size:continue
        key=(p.stat().st_size,sha(p))
        if key not in seen:seen[key]=p;continue
        target=seen[key];temporary=p.with_name(p.name+'.storage-link-tmp')
        if temporary.exists():raise RuntimeError('unexpected storage temporary member')
        os.link(target,temporary);os.replace(temporary,p)
        if sha(p)!=key[1]:raise RuntimeError('lossless storage hash changed')
        links.append({'member':p.relative_to(stage).as_posix(),'same_bytes_as':target.relative_to(stage).as_posix(),'bytes':key[0],'sha256':key[1]})
    save(stage/'STORAGE_ENCODING.json',{'schema':'RTX_V4.lossless_tar_storage','links':links,'logical_member_bytes_changed':0,'internal_hardlinks_only':True,'operator_scope':'filesystem storage only; frozen numerical algorithms, raw evidence and acceptance rules unchanged'})
    art=ART[arm];art.mkdir(parents=True,exist_ok=True);(art/'.gitattributes').write_text('*.part -text\n*.gz -text\n',encoding='utf-8',newline='\n')
    inventory(stage,mode,arm,anonymous);tmp=ROOT/'work'/('package-'+arm+'-'+mode+('-anonymous' if anonymous else '')+'.tar.gz')
    with tmp.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as compressed,tarfile.open(fileobj=compressed,mode='w') as tar:
        for p in sorted(stage.rglob('*')):
            if p.is_file():
                info=tar.gettarinfo(str(p),arcname=p.relative_to(stage).as_posix());info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                with p.open('rb') as f:tar.addfile(info,f)
    h=sha(tmp);name=mode+('-anonymous' if anonymous else '')+'-'+h;parts=[];size=48*1024*1024
    with tmp.open('rb') as f:
        i=0
        while b:=f.read(size):
            i+=1;q=art/(name+f'.part{i:03d}');q.write_bytes(b);parts.append({'ordinal':i,'name':q.name,'path':q.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':sha(q)})
    index={'schema':'RTX_V4.multipart','arm':arm,'mode':mode,'anonymous':anonymous,'sha256':h,'bytes':tmp.stat().st_size,'parts':parts,'file_count':len(json.loads((stage/'MANIFEST.json').read_text())['files'])+1,'manifest_sha256':sha(stage/'MANIFEST.json')};indexpath=art/(name+'.parts.json');save(indexpath,index)
    reconstructed=ROOT/'work'/('clean-'+arm+'-'+h[:16]);result=reconstruct(indexpath,reconstructed)
    save(STUDY/(arm+'_'+mode.upper().replace('-','_')+('_ANONYMOUS' if anonymous else '')+'_ARCHIVE.json'),{'path':indexpath.relative_to(ROOT).as_posix(),**index,'offline_reconstruction':result,'actual_created_utc':now()});return indexpath
def make(mode,arm):
    stage=ROOT/'work'/('package-stage-'+arm+'-'+mode);stage.mkdir(exist_ok=False)
    shutil.copytree(STUDY,stage/'metadata',ignore=shutil.ignore_patterns('*_ARCHIVE.json','*_OFFLINE*.json','PROTOCOL_REVIEW_PACKET.md'))
    source=stage/'frozen_source/scripts/platform/rtx_trajectory_cost_v4';source.mkdir(parents=True)
    for p in Path(__file__).parent.iterdir():
        if p.suffix in ['.py','.cpp']:shutil.copyfile(p,source/p.name)
    folders=['engineering-attempt1','engineering-extra','capture-repair','capture-regression','negative-fixtures','failure-path-fixtures','audit-attempts','build-attempts','preparation-attempts','preparation-initial','frozen-checkpoints','formal-operator']
    if mode in ['pre-live','complete'] and arm=='A':folders+=['A-pre-live']
    if mode=='complete':folders+=['A-live'] if arm=='A' else ['B-formal']
    for name in folders:
        p=ROOT/'work'/name
        if p.exists():shutil.copytree(p,stage/'work'/name,ignore=shutil.ignore_patterns('*.exe','*.dll','*.pdb','__pycache__','*.tmp'))
    for p in (ROOT/'work').iterdir():
        if p.is_file() and (p.suffix.lower() in ['.log','.json','.jsonl']):q=stage/'work'/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
    upstream=stage/'pinned_upstream'
    for name in ['LICENSE','include/llama.h','ggml/include/ggml.h','ggml/include/ggml-backend.h','vendor/nlohmann/json.hpp','tools/server/server-context.cpp','tools/cli/cli.cpp','tools/cli/cli-context.cpp','common/common.cpp','common/common.h','common/speculative.cpp','common/sampling.cpp','common/chat.cpp','src/llama-batch.cpp','src/llama-context.cpp','src/llama-memory.h']:
        p=ROOT/'work/pinned-source'/name
        if p.exists():q=upstream/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    index=publish(stage,mode,arm)
    if mode!='pre-live':
        import anonymous
        anonymous.make(stage,mode,arm)
    return index
def reconstruct(index,output):
    index=longpath(Path(index).resolve());output=longpath(Path(output).resolve());m=json.loads(index.read_text());output.mkdir(parents=True,exist_ok=False);merged=output/'complete.tar.gz'
    with merged.open('xb') as dest:
        for i,row in enumerate(m['parts'],1):
            if row['ordinal']!=i or Path(row['name']).name!=row['name']:raise RuntimeError('part order/name')
            p=index.parent/row['name']
            if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise RuntimeError('part bytes differ')
            with p.open('rb') as src:shutil.copyfileobj(src,dest,1024*1024)
    if merged.stat().st_size!=m['bytes'] or sha(merged)!=m['sha256']:raise RuntimeError('merged archive hash')
    extracted=output/'evidence';extracted.mkdir()
    # Decode once so tar hardlink materialization never repeatedly seeks gzip.
    # Scratch transport is outside the evidence inventory; compressed bytes and
    # every extracted logical member remain independently authenticated.
    plain=output/'complete.transport.tar'
    with gzip.open(merged,'rb') as inp,plain.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
    with tarfile.open(plain,'r:') as tar:tar.extractall(extracted,filter='data')
    cmd=[sys.executable,'-B',str(extracted/'frozen_source/scripts/platform/rtx_trajectory_cost_v4/offline.py'),str(extracted)];r=subprocess.run(cmd,capture_output=True)
    (output/'offline.stdout.log').write_bytes(r.stdout);(output/'offline.stderr.log').write_bytes(r.stderr)
    if r.returncode:raise RuntimeError('fresh offline reconstruction failed: '+r.stderr.decode(errors='replace'))
    result={'status':'PASS','archive_sha256':m['sha256'],'verified_parts':len(m['parts']),'fresh_directory':True,'bytecode_disabled':True,'independent_offline_result':json.loads(r.stdout)};save(output/'RECONSTRUCTION.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['engineering','pre-live','complete','reconstruct']);p.add_argument('--arm',choices=['A','B']);p.add_argument('--index',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();print(reconstruct(a.index,a.output) if a.mode=='reconstruct' else make(a.mode,a.arm))
