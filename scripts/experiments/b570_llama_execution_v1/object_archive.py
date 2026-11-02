"""Lossless content-addressed raw archive with explicit provenance exclusions."""
from pathlib import Path
import argparse,collections,hashlib,json,zipfile

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def excluded(relative):
    parts=relative.parts;name=relative.name.lower()
    if relative.suffix.lower()=='.gguf':return 'Pinned model weights are separate inputs; model identities and exact paths retained.'
    if parts[0]=='historical-restored':return 'Already published, fully restored historical object release; source manifest and independent restoration audit retained.'
    if parts[0]=='historical-download' and '.attempt-' not in name:return 'Duplicate downloaded historical release transport, pinned and audited separately.'
    if parts[:2]==('rtx159-readonly','download') and '.attempt-' not in name:return 'Duplicate authenticated RTX159 transport; published index, readback and extracted metadata retained.'
    if parts[0]=='pool-pydeps':return 'Reinstallable public preparation dependencies; exact pip report retained.'
    if '__pycache__' in parts:return 'Python bytecode cache.'
    if 'build' in parts:
        if relative.suffix.lower() in ('.dll','.exe','.log','.json','.cmd') or name=='cmakecache.txt':return None
        return 'Regenerable build intermediate; exact source, commands, configuration, logs and runtime binaries retained.'
    return None
def verify_part(root,part):
    p=Path(root)/part['name'];need(p.stat().st_size==part['bytes'] and sha(p)==part['sha256'],'archive SHA/size')
    with zipfile.ZipFile(p) as z:
        need(sorted(z.namelist())==sorted('objects/'+o['sha256'] for o in part['objects']),'unique archive inventory')
        for o in part['objects']:
            h=hashlib.sha256();size=0
            with z.open('objects/'+o['sha256']) as f:
                while b:=f.read(4*1024**2):h.update(b);size+=len(b)
            need(size==o['bytes'] and h.hexdigest()==o['sha256'],'decompressed object SHA/size')
def pack(root,out,limit=512*1024**2):
    root=Path(root).resolve();out=Path(out).resolve();need(root.is_dir() and not out.exists() and not out.is_relative_to(root),'fresh separate delivery root');out.mkdir(parents=True)
    files=[];objects={};omitted=collections.Counter();omitted_bytes=collections.Counter()
    for index,p in enumerate(sorted(root.rglob('*'))):
        if not p.is_file():continue
        need(not p.is_symlink(),'raw symlink');rel=p.relative_to(root);reason=excluded(rel);stat=p.stat()
        if reason:omitted[reason]+=1;omitted_bytes[reason]+=stat.st_size;continue
        h=sha(p);need(p.stat().st_size==stat.st_size and p.stat().st_mtime_ns==stat.st_mtime_ns,'file changed while hashing')
        files.append({'path':rel.as_posix(),'bytes':stat.st_size,'sha256':h});objects.setdefault(h,{'path':p,'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns})
        if len(files)%5000==0:print('HASHED',len(files),'objects',len(objects),flush=True)
    write(out/'MEMBERS.json',{'root_label':'b570-llama-native-evidence','files':files,'exclusions':[{'reason':r,'files':omitted[r],'bytes':omitted_bytes[r]} for r in sorted(omitted)],'models_included':False,'native_runtime_binaries_included':True})
    parts=[];group=[];size=0
    def flush():
        nonlocal group,size
        if not group:return
        p=out/f'raw-objects-{len(parts):04d}.zip';items=[]
        with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
            for h in group:
                o=objects[h];f=o['path'];need(f.stat().st_size==o['bytes'] and f.stat().st_mtime_ns==o['mtime_ns'],'source changed before packing');z.write(f,'objects/'+h);items.append({'sha256':h,'bytes':o['bytes']})
        part={'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'objects':items};verify_part(out,part);parts.append(part);print('PACKED_AND_READBACK',p.name,len(items),flush=True);group=[];size=0
    for h,o in sorted(objects.items()):
        if group and size+o['bytes']>limit:flush()
        group.append(h);size+=o['bytes']
    flush();write(out/'INDEX.json',{'status':'LOCAL_ALL_OBJECTS_READBACK_PASS','logical_files':len(files),'logical_bytes':sum(f['bytes'] for f in files),'unique_objects':len(objects),'unique_bytes':sum(x['bytes'] for x in objects.values()),'members_manifest':{'name':'MEMBERS.json','bytes':(out/'MEMBERS.json').stat().st_size,'sha256':sha(out/'MEMBERS.json')},'parts':parts,'remote_readback_complete':False})
def verify(root):
    root=Path(root);index=read(root/'INDEX.json');m=index['members_manifest'];need(sha(root/m['name'])==m['sha256'],'member manifest identity');members=read(root/m['name'])['files'];objects={}
    for part in index['parts']:
        verify_part(root,part)
        for o in part['objects']:need(o['sha256'] not in objects,'duplicate stored object');objects[o['sha256']]=o['bytes']
    paths=set()
    for f in members:
        p=Path(f['path']);need(not p.is_absolute() and '..' not in p.parts and f['path'] not in paths,'safe unique logical member');paths.add(f['path']);need(objects[f['sha256']]==f['bytes'],'complete logical mapping')
    need(len(paths)==index['logical_files'] and len(objects)==index['unique_objects'],'declared inventory');return {'status':'ALL_LOGICAL_MEMBERS_VERIFIED','files':len(paths),'objects':len(objects),'parts':len(index['parts']),'index_sha256':sha(root/'INDEX.json')}
def restore(root,out,prefixes=(),tails=()):
    root=Path(root);out=Path(out);need(not out.exists(),'fresh reconstruction root');verify(root);index=read(root/'INDEX.json');members=read(root/'MEMBERS.json')['files'];by_hash=collections.defaultdict(list)
    if prefixes or tails:members=[f for f in members if any(f['path']==prefix or f['path'].startswith(prefix.rstrip('/')+'/') for prefix in prefixes) or any(f['path'].endswith(tail) for tail in tails)]
    need(members,'nonempty selected reconstruction')
    for f in members:by_hash[f['sha256']].append(f)
    out.mkdir(parents=True)
    for part in index['parts']:
        with zipfile.ZipFile(root/part['name']) as z:
            for o in part['objects']:
                if o['sha256'] not in by_hash:continue
                for f in by_hash[o['sha256']]:
                    p=out/f['path'];need(p.resolve().is_relative_to(out.resolve()),'confined restore');p.parent.mkdir(parents=True,exist_ok=True)
                    with z.open('objects/'+o['sha256']) as src,p.open('xb') as dest:
                        while b:=src.read(4*1024**2):dest.write(b)
                    need(sha(p)==f['sha256'],'restored file mismatch')
    write(out/'RESTORE_RECEIPT.json',{'status':'EXACT_SELECTED_RECONSTRUCTION_PASS' if prefixes or tails else 'EXACT_LOGICAL_RECONSTRUCTION_PASS','selected_prefixes':list(prefixes),'selected_tails':list(tails),'files':len(members),'all_archive_objects_verified':True,'index_sha256':sha(root/'INDEX.json')})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['pack','verify','restore']);p.add_argument('--root',required=True);p.add_argument('--out');p.add_argument('--prefix',action='append',default=[]);p.add_argument('--tail',action='append',default=[]);p.add_argument('--limit',type=int,default=512*1024**2);a=p.parse_args()
    if a.command=='pack':pack(a.root,a.out,a.limit)
    elif a.command=='restore':restore(a.root,a.out,a.prefix,a.tail)
    else:print(verify(a.root))
