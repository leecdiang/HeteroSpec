"""Lossless content-addressed transport of immutable snapshots; old ZIPs retained."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import zipfile
from common import *
from archive import TAG, REPOSITORY

BASE=Path('D:/rtx151-archives')
LABELS=('main-through-day0','llama-diagnostic')

def prepare(root):
    s.need(not root.exists(),'never replace an existing object archive')
    with exclusive('object-archive-prepare',3600) as deadline:
        root.mkdir(parents=True);objects={};members=[];sources=[]
        for label in LABELS:
            source=BASE/label;manifest=s.read(source/'MEMBERS.json')
            sources.append({'label':label,'members_sha256':sha(source/'MEMBERS.json'),
                            'prior_zip_index_sha256':sha(source/'PARTS.json'),'audited_pin_link':s.read(source/'AUDITED_PIN_LINK.json')})
            for m in manifest['files']:
                members.append({'snapshot':label,**m})
                if m['sha256'] in objects:s.need(objects[m['sha256']]['bytes']==m['bytes'],'hash/size inconsistency')
                else:objects[m['sha256']]={'sha256':m['sha256'],'bytes':m['bytes'],'snapshot':label,'source_path':m['path']}
        save(root/'OBJECT_MEMBERS.json',{'schema':1,'format':'sha256-object-zips-v1','sources':sources,'members':members,'objects':list(objects.values()),
               'restore':'For each member, copy the downloaded object whose SHA256 is member.sha256 to snapshot/member.path; verify length and SHA256. Duplicate member paths reference exactly the same bytes, not an approximation.',
               'old_indices_retained':True})
        groups=[];group=[];size=0
        for obj in sorted(objects.values(),key=lambda o:o['sha256']):
            if group and size+obj['bytes']>256*1024**2:groups.append(group);group=[];size=0
            group.append(obj);size+=obj['bytes']
        if group:groups.append(group)
        parts=[];(root/'parts').mkdir()
        for n,group in enumerate(groups):
            s.need(now()<deadline,'formal-priority deadline reached')
            path=root/'parts'/f'completed-through-day0.objects-{n:03d}.zip'
            with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
                for obj in group:
                    source=BASE/obj['snapshot']/'snapshot'/obj['source_path']
                    s.need(source.stat().st_size==obj['bytes'] and sha(source)==obj['sha256'],'sealed object changed')
                    z.write(source,'objects/'+obj['sha256'])
            s.need(path.stat().st_size<1900*1024**2,'part too large')
            parts.append({**pin(root,path),'objects':[o['sha256'] for o in group]})
            save(root/'PACK_PROGRESS.json',{'completed':parts,'total':len(groups)})
            print(json.dumps({'part':n+1,'total':len(groups),'bytes':path.stat().st_size}),flush=True)
        save(root/'OBJECT_PARTS.json',{'schema':1,'parts':parts,'members_manifest':pin(root,root/'OBJECT_MEMBERS.json'),
               'total_logical_members':len(members),'unique_objects':len(objects),'compressed_bytes':sum(p['bytes'] for p in parts),'status':'PACKAGED_LOCAL_ONLY'})

def transfer(root):
    spec=s.read(root/'OBJECT_PARTS.json');manifest=s.read(s.payload(root,spec['members_manifest']));objects={o['sha256']:o for o in manifest['objects']}
    with exclusive('object-archive-transfer',7200) as deadline:
        receipt_path=root/'READBACK.json'
        receipt=s.read(receipt_path) if receipt_path.exists() else {'status':'IN_PROGRESS','parts':[],'index_assets':[],'verified_objects':[]}
        release=json.loads(subprocess.check_output(['gh','api',f'repos/{REPOSITORY}/releases/tags/{TAG}'],text=True));existing={a['name']:a for a in release['assets']}
        receipt['release_url']=release['html_url'];save(receipt_path,receipt)
        download=root/'fresh-download';download.mkdir(exist_ok=True)
        completed={p['name'] for p in receipt['parts']};verified=set(receipt['verified_objects'])
        for part in spec['parts']:
            name=Path(part['path']).name
            if name in completed:continue
            remaining=int((deadline-now()).total_seconds());s.need(remaining>60,'formal-priority deadline')
            local=s.payload(root,part)
            if name not in existing:
                print(json.dumps({'uploading':name,'bytes':part['bytes']}),flush=True)
                subprocess.run(['gh','release','upload',TAG,str(local),'--repo',REPOSITORY],check=True,timeout=min(1800,remaining))
            dest=download/name
            # A retained unverified download may be validated, never silently overwritten.
            if not dest.exists():
                print(json.dumps({'downloading':name}),flush=True)
                remaining=int((deadline-now()).total_seconds());s.need(remaining>60,'formal-priority deadline')
                subprocess.run(['gh','release','download',TAG,'--repo',REPOSITORY,'--pattern',name,'--dir',str(download)],check=True,timeout=min(1800,remaining))
            s.need(dest.stat().st_size==part['bytes'] and sha(dest)==part['sha256'],'fresh download hash mismatch')
            with zipfile.ZipFile(dest) as z:
                s.need(z.namelist()==['objects/'+h for h in part['objects']],'object inventory differs')
                for h in part['objects']:
                    digest=hashlib.sha256();size=0
                    with z.open('objects/'+h) as f:
                        while block:=f.read(4*1024**2):size+=len(block);digest.update(block)
                    s.need(digest.hexdigest()==h and size==objects[h]['bytes'],'downloaded object mismatch')
                    verified.add(h)
            receipt['parts'].append({'name':name,'sha256':part['sha256'],'bytes':part['bytes'],'verified_utc':now().isoformat(),'objects':len(part['objects'])})
            receipt['verified_objects']=sorted(verified);save(receipt_path,receipt)
            print(json.dumps({'verified_parts':len(receipt['parts']),'total':len(spec['parts'])}),flush=True)
        s.need(verified==set(objects),'some objects were not downloaded/verified')
        for member in manifest['members']:
            s.need(member['sha256'] in verified and member['bytes']==objects[member['sha256']]['bytes'],'logical member not covered by verified downloaded content')
        for name in ('OBJECT_MEMBERS.json','OBJECT_PARTS.json'):
            local=root/name;asset=root/('completed-through-day0.'+name)
            if not asset.exists():shutil.copyfile(local,asset)
            if asset.name not in existing:subprocess.run(['gh','release','upload',TAG,str(asset),'--repo',REPOSITORY],check=True,timeout=120)
            dest=download/asset.name
            if not dest.exists():subprocess.run(['gh','release','download',TAG,'--repo',REPOSITORY,'--pattern',asset.name,'--dir',str(download)],check=True,timeout=120)
            s.need(sha(dest)==sha(local),'downloaded index differs')
            receipt['index_assets'].append({'name':asset.name,'sha256':sha(local),'verified':True})
        receipt.update(status='ALL_DOWNLOADED_OBJECTS_AND_LOGICAL_MEMBERS_VERIFIED',logical_members=len(manifest['members']),unique_objects=len(objects),
                       compressed_bytes=spec['compressed_bytes'],verified_utc=now().isoformat(),
                       verification='Every object is independently rehashed from the freshly downloaded ZIP; all logical paths are mapped to these exact bytes/lengths; both mapping indices are freshly downloaded and hash-verified.')
        save(receipt_path,receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('parts','verified_objects')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','transfer']);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    if a.action=='prepare':prepare(a.root.resolve())
    else:transfer(a.root.resolve())
