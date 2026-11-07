"""Incremental immutable snapshots, bounded ZIP parts, upload and fresh readback."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time
import zipfile
from common import *

REPOSITORY='leecdiang/HeteroSpec'
TAG='rtx-scope-transfer-v1-evidence-20261030'

def seal(source, root, label):
    s.need(source.resolve()==MAIN.resolve() or source.name.startswith('rtx151-llama-diagnostic-'),'unexpected source bundle')
    s.need(not root.exists(),'snapshot already exists; never replace an old index')
    with exclusive('archive-seal-'+label,3600) as deadline:
        attempts=s.read(source/'ATTEMPTS.json')
        s.need(attempts and all(a['cleanup_verified'] and a['status']=='COMPLETE' for a in attempts),'only completed clean units may be sealed')
        root.mkdir(parents=True);snapshot=root/'snapshot';snapshot.mkdir()
        candidates=sorted(p for p in source.rglob('*') if p.is_file() and p.name!='HOST.lock')
        s.need(not any(p.suffix=='.tmp' for p in candidates),'uncommitted temporary evidence')
        size=sum(p.stat().st_size for p in candidates)
        check_room(root,size+20*1024**3)
        members=[]
        for n,src in enumerate(candidates):
            s.need(now()<deadline,'formal-priority deadline reached')
            relative=src.relative_to(source);dst=snapshot/relative;dst.parent.mkdir(parents=True,exist_ok=True)
            before=src.stat();digest=hashlib.sha256()
            with src.open('rb') as inp,dst.open('xb') as out:
                while block:=inp.read(4*1024**2):out.write(block);digest.update(block)
            after=src.stat()
            s.need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'source changed while sealing')
            s.need(sha(dst)==digest.hexdigest(),'snapshot copy readback differs')
            members.append({'path':relative.as_posix(),'bytes':dst.stat().st_size,'sha256':digest.hexdigest()})
            dst.chmod(stat.S_IREAD)
            if n%2000==0:print(json.dumps({'sealed':n,'total':len(candidates)}),flush=True)
        save(root/'MEMBERS.json',{'schema':1,'label':label,'created_utc':now().isoformat(),'source':str(source),'files':members,'source_bytes':size,'source_attempts':attempts,'status':'IMMUTABLE_SNAPSHOT_HASH_VERIFIED'})
        print(json.dumps({'status':'SEALED','files':len(members),'bytes':size}),flush=True)

def pack(root):
    manifest=s.read(root/'MEMBERS.json');partsdir=root/'parts'
    s.need(not partsdir.exists(),'parts already exist; retain the original attempt')
    with exclusive('archive-pack',3600) as deadline:
        partsdir.mkdir();groups=[];current=[];size=0
        for member in manifest['files']:
            if current and size+member['bytes']>512*1024**2:groups.append(current);current=[];size=0
            current.append(member);size+=member['bytes']
        if current:groups.append(current)
        parts=[]
        for number,group in enumerate(groups):
            s.need(now()<deadline,'formal-priority deadline reached');check_room(root,20*1024**3)
            name=f"{manifest['label']}.part-{number:03d}.zip";path=partsdir/name
            with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
                for m in group:
                    src=root/'snapshot'/m['path'];s.need(sha(src)==m['sha256'],'sealed member changed')
                    z.write(src,m['path'])
            s.need(path.stat().st_size<1900*1024**2,'release part exceeds bound')
            parts.append({**pin(root,path),'members':[m['path'] for m in group]})
            save(root/'PACK_PROGRESS.json',{'completed_parts':parts,'total_parts':len(groups)})
            print(json.dumps({'part':number+1,'total':len(groups),'bytes':path.stat().st_size}),flush=True)
        index={'schema':1,'status':'PACKAGED_LOCAL','label':manifest['label'],'members_manifest':pin(root,root/'MEMBERS.json'),'parts':parts,
               'release_tag':TAG,'repository':REPOSITORY,'models_and_dlls_included':False,'remote_readback':'NOT_RUN'}
        save(root/'PARTS.json',index)

def transfer(root):
    index=s.read(root/'PARTS.json');manifest=s.read(root/'MEMBERS.json')
    with exclusive('archive-transfer',7200) as deadline:
        receipt_path=root/'REMOTE_READBACK.json'
        receipt=s.read(receipt_path) if receipt_path.exists() else {'label':index['label'],'release_tag':TAG,'status':'IN_PROGRESS','parts':[]}
        view=subprocess.run(['gh','release','view',TAG,'--repo',REPOSITORY,'--json','url'],capture_output=True,text=True)
        if view.returncode:
            notes=root/'RELEASE_NOTES.txt';notes.write_text('Incremental raw evidence for PR151. Completed units only, with exact member hashes and downloaded ZIP readback. The three-date study remains incomplete. No model weights or numerical DLLs are redistributed.\n',encoding='utf-8')
            subprocess.run(['gh','release','create',TAG,'--repo',REPOSITORY,'--target',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'--prerelease','--title','RTX scope transfer v1 incremental raw evidence','--notes-file',str(notes)],check=True,timeout=120)
        url=json.loads(subprocess.check_output(['gh','release','view',TAG,'--repo',REPOSITORY,'--json','url'],text=True))['url'];receipt['release_url']=url
        assets=json.loads(subprocess.check_output(['gh','api',f'repos/{REPOSITORY}/releases/tags/{TAG}'],text=True))['assets']
        byname={x['name']:x for x in assets}
        download=root/'download-readback';download.mkdir(exist_ok=True)
        done={p['name'] for p in receipt['parts'] if p['status']=='DOWNLOADED_MEMBERS_VERIFIED'}
        expected={x['path']:x for x in manifest['files']}
        for part in index['parts']:
            s.need(now()<deadline,'formal-priority deadline reached')
            name=Path(part['path']).name
            if name in done:continue
            local=s.payload(root,part)
            if name not in byname:
                subprocess.run(['gh','release','upload',TAG,str(local),'--repo',REPOSITORY],check=True,timeout=1800)
            dest=download/name
            s.need(not dest.exists(),'readback destination exists without verified receipt; retain and inspect')
            subprocess.run(['gh','release','download',TAG,'--repo',REPOSITORY,'--pattern',name,'--dir',str(download)],check=True,timeout=1800)
            s.need(dest.stat().st_size==part['bytes'] and sha(dest)==part['sha256'],'downloaded archive hash differs')
            with zipfile.ZipFile(dest) as z:
                s.need(z.namelist()==part['members'] and len(z.namelist())==len(set(z.namelist())),'archive member inventory differs')
                for member in part['members']:
                    digest=hashlib.sha256();size=0
                    with z.open(member) as f:
                        while block:=f.read(4*1024**2):digest.update(block);size+=len(block)
                    s.need(size==expected[member]['bytes'] and digest.hexdigest()==expected[member]['sha256'],'downloaded member differs: '+member)
            receipt['parts'].append({'name':name,'sha256':part['sha256'],'bytes':part['bytes'],'members':len(part['members']),'status':'DOWNLOADED_MEMBERS_VERIFIED','verified_utc':now().isoformat()})
            save(receipt_path,receipt);print(json.dumps({'remote_verified':len(receipt['parts']),'total':len(index['parts'])}),flush=True)
        receipt['status']='ALL_PARTS_DOWNLOADED_AND_ALL_MEMBERS_VERIFIED';save(receipt_path,receipt)
        # Publish discoverable indices only after complete downloaded member verification.
        for name in ('MEMBERS.json','PARTS.json','REMOTE_READBACK.json'):
            target=root/(index['label']+'.'+name)
            if not target.exists():shutil.copyfile(root/name,target)
            if target.name not in byname:
                subprocess.run(['gh','release','upload',TAG,str(target),'--repo',REPOSITORY],check=True,timeout=120)
        print(json.dumps({'status':receipt['status'],'release_url':url}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['seal','pack','transfer']);p.add_argument('--source',type=Path);p.add_argument('--root',type=Path,required=True);p.add_argument('--label');a=p.parse_args()
    if a.action=='seal':seal(a.source.resolve(),a.root.resolve(),a.label)
    elif a.action=='pack':pack(a.root.resolve())
    else:transfer(a.root.resolve())
