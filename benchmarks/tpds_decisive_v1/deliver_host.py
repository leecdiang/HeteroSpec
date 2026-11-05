"""Stream a deduplicated portable evidence ZIP to bounded release parts.

Run only after RTX work stops. No model weights, unrelated workspaces or secrets
are collected. Server-reported asset SHA256/size must match each uploaded part.
"""
from build_host import *
import io,os,zlib,zipfile
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='leecdiang/HeteroSpec'
TAG='rtx-decisive-v1-evidence-20261105'
OUT=Path('D:/rtx184-delivery')
STORES=[Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence'),Path('F:/rtx184-O-evidence')]

def gh(*args):return subprocess.check_output([GH,*args],text=True)

def upload(path):
    for attempt in range(3):
        result=subprocess.run([GH,'release','upload',TAG,str(path),'--repo',REPO])
        if result.returncode==0:break
        release=json.loads(gh('api','repos/'+REPO+'/releases/tags/'+TAG))
        if any(a['name']==path.name for a in release['assets']):break
        if attempt==2:raise RuntimeError('asset upload failed; staging bytes retained')
        time.sleep(5)
    release=json.loads(gh('api','repos/'+REPO+'/releases/tags/'+TAG))
    asset=next(a for a in release['assets'] if a['name']==path.name)
    h=sha(path)
    if asset['size']!=path.stat().st_size or asset.get('digest')!='sha256:'+h:raise RuntimeError('remote asset digest/size mismatch')
    return dict(name=path.name,bytes=path.stat().st_size,sha256=h,url=asset['browser_download_url'],asset_id=asset['id'])

class PartsWriter(io.RawIOBase):
    def __init__(self):self.position=0;self.current=None;self.size=0;self.parts=[];self.limit=256*1024**2
    def writable(self):return True
    def seekable(self):return False
    def tell(self):return self.position
    def flush(self):
        if self.current:self.current.flush()
    def finish_part(self):
        if not self.current:return
        p=Path(self.current.name);self.current.close();self.current=None
        record=upload(p);self.parts.append(record)
        (OUT/'upload-progress.json').write_text(json.dumps(self.parts,indent=2))
        print('uploaded, server SHA256 verified',p.name,record['bytes'],flush=True)
        # Only the staging copy is retired; original evidence chunks remain.
        if p.resolve().parent!=OUT.resolve():raise RuntimeError('unexpected staging path')
        p.unlink();self.size=0
    def write(self,data):
        n=len(data);view=memoryview(data)
        while view:
            if self.current is None:
                if shutil.disk_usage(OUT).free<21*1024**3:raise RuntimeError('delivery disk reserve')
                self.current=(OUT/('raw-evidence.zip.part%03d'%len(self.parts))).open('xb')
            take=min(len(view),self.limit-self.size);self.current.write(view[:take]);view=view[take:];self.position+=take;self.size+=take
            if self.size==self.limit:self.finish_part()
        return n

def files():
    roots=[ROOT,Path(__file__).resolve().parent,Path('D:/rtx184-runs'),Path('D:/rtx184-qualification'),Path('D:/rtx184-operator'),OLD,Path('E:/rtx164/active03/qwen_config01'),Path('E:/tpds167/build01/source'),Path('E:/tpds167/oracle01'),Path('E:/rtx170/witness-8B/native'),Path('E:/rtx170/witness-0.6B/native'),Path('D:/rtx184-tools/downloads'),Path('E:/rtx164/pool06'),Path('E:/rtx164/exposure-pr163')]
    extensions={'.json','.jsonl','.log','.txt','.bin','.f32','.state','.cpp','.c','.h','.hpp','.cu','.cuh','.inc','.cmake','.py','.md','.exe','.dll','.a','.lib','.sqlite','.patch','.def','.rc','.in','.s','.sh','.bat','.ps1'}
    for root in roots:
        for p in sorted(root.rglob('*')):
            if not p.is_file() or any(x in p.parts for x in ('.git','__pycache__')):continue
            if p.name.startswith(('EVIDENCE_DEDUP-','ARTIFACT_DELIVERY','upload-progress')):continue
            if p.suffix.lower() in extensions or 'cas' in p.parts or p.name in ('CMakeLists.txt','LICENSE','COPYING'):yield p
    for name,h in json.loads((ROOT/'selection-v3/EXCLUSIONS.json').read_bytes())['source_pins'].items():
        p=Path(name)
        if sha(p)!=h:raise RuntimeError('exposure source drift')
        yield p
    for p in (OLD.parent/'admission-Qwen-v4').glob('*.json'):yield p
    yield Path('E:/tpds167/formal01/freeze.json')
    for p in Path('D:/rtx184-tools').glob('*.json'):yield p

def main():
    began=time.monotonic()
    if Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists():raise RuntimeError('GPU work still active')
    OUT.mkdir(exist_ok=False);writer=PartsWriter();index={};seen=set();inodes={}
    with zipfile.ZipFile(writer,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
        def write(name,data,compressed=False):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED
            archive.writestr(info,data,compresslevel=1 if compressed else None)
        def chunk(h,data):
            if h in seen:return
            if hashlib.sha256(zlib.decompress(data)).hexdigest()!=h:raise RuntimeError('archive chunk corrupted')
            write('chunks/'+h[:2]+'/'+h,data);seen.add(h)
        for store in STORES:
            for manifest in sorted(store.glob('*.json')):
                m=json.loads(manifest.read_bytes())
                write('archive-manifests/'+store.name+'/'+manifest.name,manifest.read_bytes())
                if 'files' not in m:continue
                for row in m['files']:
                    name=str(Path(row['path'])).casefold()
                    if name in index and index[name]!=row:raise RuntimeError('archive path version conflict')
                    index[name]=row
                    for h in row['chunks']:
                        if h not in seen:chunk(h,(store/'chunks'/h[:2]/h).read_bytes())
        for p in files():
            stat=p.stat();identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns);name=str(p.resolve()).casefold()
            if identity in inodes:row=dict(inodes[identity],path=str(p.resolve()))
            else:
                full=hashlib.sha256();parts=[];size=0
                with p.open('rb') as f:
                    while raw:=f.read(1024*1024):
                        full.update(raw);size+=len(raw);h=hashlib.sha256(raw).hexdigest();parts.append(h)
                        if h not in seen:chunk(h,zlib.compress(raw,1))
                row=dict(path=str(p.resolve()),sha256=full.hexdigest(),bytes=size,chunks=parts,mtime_ns=stat.st_mtime_ns);inodes[identity]=row
            if name in index and (index[name]['sha256'],index[name]['bytes'])!=(row['sha256'],row['bytes']):raise RuntimeError('live/archived path differs')
            index[name]=row
        manifest=dict(schema=1,chunk_size=1024*1024,compression='zlib',files=sorted(index.values(),key=lambda r:r['path'].casefold()),models_included=False,model_identity='Model SHA256 pins and original-host paths are in job/build/freeze receipts.',original_path_identifiers_only=True)
        write('FILES.json',json.dumps(manifest,separators=(',',':')).encode(),True)
    writer.finish_part()
    receipt=dict(schema=1,format='concatenated ZIP parts; PartsReader avoids concatenation',parts=writer.parts,total_bytes=writer.position,unique_chunks=len(seen),logical_files=len(index),logical_bytes=sum(r['bytes'] for r in index.values()),release='https://github.com/'+REPO+'/releases/tag/'+TAG,all_remote_digests_verified=True,delivery_wall_before_index_upload_s=time.monotonic()-began)
    put(OUT/'raw-evidence.zip.parts.json',receipt);remote=upload(OUT/'raw-evidence.zip.parts.json');put(ROOT/'ARTIFACT_DELIVERY.json',dict(receipt,index_asset=remote))
    print('evidence delivery complete',len(index),'files',len(writer.parts),'parts',flush=True)

if __name__=='__main__':main()
