"""Deliver only this stopped RTX experiment; never execute a model.

Uses the already exercised bounded-part transport, not its historical collector.
All compiler-bound files are retained even when under a general compiler cache.
"""
from host_rtx import *
import deliver_host as transport
import io,zipfile,zlib

TAG='tpds-phase1-rtx-review-v2-evidence-20261107'
OUT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase192-delivery')
transport.TAG=TAG;transport.OUT=OUT;transport.ROOT=ROOT
CLEAN=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase192-clean-v1')

def source_asset():
    path=OUT/'rtx-phase1-source.zip'; entries={}
    for p in (ROOT/'native-v2').rglob('*'):
        if p.is_file() and '.git' not in p.parts and p.suffix.lower() not in {'.key','.pem','.gguf','.exe','.dll','.bin'}:
            entries['native/'+p.relative_to(ROOT/'native-v2').as_posix()]=p
    sdk=Path('E:/rtx170/profiler/sdk/nvidia')
    for role in ('cuda_nvcc','cuda_runtime','cuda_cupti'):
        for p in (sdk/role).rglob('*'):
            if p.is_file() and ('include' in p.relative_to(sdk/role).parts or 'license' in p.name.lower()):entries['deps/nvidia/'+p.relative_to(sdk).as_posix()]=p
    for name in ('portable_rtx.py','materialize_runtime.py','MODEL_ASSETS.json','REPRODUCE_RTX.md','RESULT.md','SOURCE_AND_BUILD.json'):
        entries[name]=HERE/name
    entries['samples/R1-Qwen-JOB.json']=ROOT/'runs/Qwen-v2-matrix-R/job.json'
    entries['samples/R1-Smol-JOB.json']=ROOT/'runs/Smol-v2-matrix-R/job.json'
    entries['samples/R2-INPUTS.json']=ROOT/'R2/NATIVE_INPUTS.json'
    assert all(p.exists() for p in entries.values())
    manifest={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in entries.items()}
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for n,p in sorted(entries.items()):z.write(p,n)
        z.writestr('SOURCE_ASSET_MANIFEST.json',json.dumps(dict(files=manifest,models_included=False,compilation_requires_no_historical_KV=True),indent=2))
    return transport.upload(path)

def runtime_asset():
    path=OUT/'rtx-phase1-runtime.zip';roles={};blobs={}
    for role,folder,exes in [
        ('candidate',ROOT/'runtime-v2-loop4/bin',False),
        ('qualified-loop4',ROOT/'runtime-v2-loop4/bin',True),
        ('qualified-packed',ROOT/'runtime-v2-packed/bin',True),
        ('R-Qwen',ROOT/'R-Qwen/bin',True),('R-Smol',ROOT/'R-Smol/bin',True)]:
        roles[role]={}
        for p in sorted(folder.iterdir()):
            if p.suffix.lower()=='.dll' or (exes and p.suffix.lower()=='.exe'):
                h=sha(p);roles[role][p.name]=h;blobs.setdefault(h,p)
    manifest=dict(schema='phase1.runtime-assets.v1',roles=roles,blobs={h:dict(bytes=p.stat().st_size,sha256=h) for h,p in blobs.items()},models_included=False,reference_modules_not_replaced_by_candidate_modules=True)
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for h,p in sorted(blobs.items()):z.write(p,'blobs/'+h)
        z.writestr('RUNTIME_MANIFEST.json',json.dumps(manifest,indent=2))
    put(ROOT/'RUNTIME_ASSET_MANIFEST.json',manifest)
    return transport.upload(path)

def files():
    seen=set()
    for root in (ROOT,CLEAN,HERE):
        for p in sorted(root.rglob('*')):
            if not p.is_file() or any(x in p.relative_to(root).parts for x in ('.git','__pycache__','compiler-cache','host_evidence')):continue
            if p.suffix.lower() in {'.gguf','.pem','.key'} or p.name.startswith('ARTIFACT_'):continue
            if str(p.resolve()).casefold() not in seen:seen.add(str(p.resolve()).casefold());yield p
    # Full explicit dependency closure, including integrated toolchain/CRT inputs.
    for recipe in ('loop4','packed'):
        for r in read(ROOT/'freezes'/recipe/'BUILD_INPUTS.json')['files'].values():
            p=Path(r['path']);assert p.is_file(),p
            key=str(p.resolve()).casefold()
            if p.suffix.lower() in {'.gguf','.pem','.key'}:raise RuntimeError('unexpected compiler dependency')
            if key not in seen:seen.add(key);yield p
    # Immutable source/exposure inputs that selected the independent R2 roots.
    selection=read(ROOT/'R2/SOURCE_SELECTION.json')
    for kind in ('source_pins','exposure_pins'):
        for name,h in selection.get(kind,{}).items():
            p=Path(name);assert sha(p)==h
            key=str(p.resolve()).casefold()
            if key not in seen:seen.add(key);yield p

def raw_asset():
    writer=transport.PartsWriter();seen=set();index={};inodes={}
    with zipfile.ZipFile(writer,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for number,p in enumerate(files()):
            stat=p.stat();identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
            if identity in inodes:row=dict(inodes[identity],path=str(p.resolve()))
            else:
                full=hashlib.sha256();chunks=[];size=0
                with p.open('rb') as f:
                    while raw:=f.read(1024*1024):
                        full.update(raw);size+=len(raw);h=hashlib.sha256(raw).hexdigest();chunks.append(h)
                        if h not in seen:z.writestr('chunks/'+h[:2]+'/'+h,zlib.compress(raw,1));seen.add(h)
                row=dict(path=str(p.resolve()),sha256=full.hexdigest(),bytes=size,chunks=chunks,mtime_ns=stat.st_mtime_ns);inodes[identity]=row
            index[str(p.resolve()).casefold()]=row
            if number%2500==0:print('raw files retained',number,'unique chunks',len(seen),flush=True)
        manifest=dict(schema=1,chunk_size=1024*1024,compression='zlib',files=sorted(index.values(),key=lambda r:r['path'].casefold()),models_included=False,original_path_identifiers_only=True,historical_original_R_dependency='PR190/186 remains explicit; consumed historical payloads are in reference-payloads, not historical timings pooled into these panels.')
        z.writestr('FILES.json',json.dumps(manifest,separators=(',',':')),compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
    writer.finish_part();writer.flush_uploads()
    receipt=dict(schema=1,parts=writer.parts,total_bytes=writer.position,unique_chunks=len(seen),logical_files=len(index),logical_bytes=sum(r['bytes'] for r in index.values()),release='https://github.com/leecdiang/HeteroSpec/releases/tag/'+TAG,all_remote_digests_verified=True)
    put(OUT/'raw-evidence.zip.parts.json',receipt);asset=transport.upload(OUT/'raw-evidence.zip.parts.json')
    return dict(**receipt,index_asset=asset)

def main():
    assert (ROOT/'GPU_STOP.json').exists() and not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    OUT.mkdir(exist_ok=False);start=time.monotonic()
    small=dict(source=source_asset(),runtime=runtime_asset())
    put(ROOT/'ARTIFACT_SMALL_ASSETS.json',small)
    raw=raw_asset()
    for name in ('restore_delivered_host.py',):
        p=PARENT/name;transport.upload(p)
    for name in ('RESULT.md','REPRODUCE_RTX.md','MODEL_ASSETS.json'):
        transport.upload(HERE/name)
    put(ROOT/'ARTIFACT_DELIVERY.json',dict(**raw,small_assets=small,wall_s=time.monotonic()-start))
    print('All new RTX artifacts delivered, server size/SHA256 checked',flush=True)

if __name__=='__main__':main()
