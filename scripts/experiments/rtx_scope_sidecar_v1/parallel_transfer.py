"""Four bounded upload streams, serialized downloaded-object verification."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from pathlib import Path
import subprocess
import zipfile
from common import *
from archive import TAG, REPOSITORY

def transfer(root):
    spec=s.read(root/'OBJECT_PARTS.json');manifest=s.read(s.payload(root,spec['members_manifest']))
    objects={o['sha256']:o for o in manifest['objects']}
    with exclusive('object-archive-parallel-transfer',7200) as deadline:
        receipt=s.read(root/'READBACK.json');complete={p['name'] for p in receipt['parts']};verified=set(receipt['verified_objects'])
        release=json.loads(subprocess.check_output(['gh','api',f'repos/{REPOSITORY}/releases/tags/{TAG}'],text=True))
        remote={a['name'] for a in release['assets'] if a['state']=='uploaded'}
        download=root/'fresh-download';download.mkdir(exist_ok=True)
        pending=[p for p in spec['parts'] if Path(p['path']).name not in complete]
        def upload(part):
            local=s.payload(root,part);name=local.name
            if name not in remote:
                remaining=int((deadline-now()).total_seconds());s.need(remaining>60,'formal-priority deadline')
                print(json.dumps({'uploading':name,'bytes':part['bytes']}),flush=True)
                result=subprocess.run(['gh','release','upload',TAG,str(local),'--repo',REPOSITORY],capture_output=True,text=True,timeout=min(1800,remaining))
                s.need(result.returncode==0,'upload failed: '+name+' '+result.stderr)
            return part
        failures=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs={pool.submit(upload,p):p for p in pending}
            for future in as_completed(jobs):
                try:
                    part=future.result();name=Path(part['path']).name;dest=download/name
                    if not dest.exists():
                        remaining=int((deadline-now()).total_seconds());s.need(remaining>60,'formal-priority deadline')
                        print(json.dumps({'downloading':name}),flush=True)
                        subprocess.run(['gh','release','download',TAG,'--repo',REPOSITORY,'--pattern',name,'--dir',str(download)],check=True,timeout=min(1800,remaining))
                    s.need(dest.stat().st_size==part['bytes'] and sha(dest)==part['sha256'],'downloaded archive mismatch')
                    with zipfile.ZipFile(dest) as z:
                        s.need(z.namelist()==['objects/'+h for h in part['objects']],'downloaded inventory mismatch')
                        for h in part['objects']:
                            digest=hashlib.sha256();size=0
                            with z.open('objects/'+h) as f:
                                while block:=f.read(4*1024**2):digest.update(block);size+=len(block)
                            s.need(digest.hexdigest()==h and size==objects[h]['bytes'],'downloaded object mismatch')
                            verified.add(h)
                    receipt['parts'].append({'name':name,'sha256':part['sha256'],'bytes':part['bytes'],'objects':len(part['objects']),'verified_utc':now().isoformat()})
                    receipt['verified_objects']=sorted(verified);save(root/'READBACK.json',receipt)
                    print(json.dumps({'verified_parts':len(receipt['parts']),'total':len(spec['parts'])}),flush=True)
                except Exception as exc:
                    failures.append({'part':jobs[future]['path'],'error':str(exc),'utc':now().isoformat()})
                    save(root/'TRANSFER_FAILURES.json',failures)
                    print(json.dumps(failures[-1]),flush=True)
        s.need(not failures,'transport failures retained; no automatic retry')
        s.need(verified==set(objects),'not all content objects verified')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();transfer(a.root.resolve())
