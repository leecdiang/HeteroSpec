"""Public F0 text preparation and anonymous full-byte readback, CPU only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
import urllib.parse
import urllib.request
from support import fresh,need,read,safe_relative,sha
from host import utc,verify_public_readback

PREFIX='benchmarks/server_expansion_v1/strong_baseline_followup_20261110'


def public_text(text,root):
    # Exact path prefixes only. Never replace bare usernames inside identifiers.
    text=text.replace(str(root),'${HS_ROOT}').replace(str(Path.home()),'${HOST_HOME}')
    need(not re.search(r'GPU-[0-9a-fA-F-]{36}',text),'Private allocation UUID in public text')
    need(not re.search(r'\b(?:192\.168|10\.\d+|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+\b',text),'Private network address in public text')
    need(str(Path.home())not in text,'Unmapped private host path')
    return text


def prepare(root,source,cpu,out):
    need(not out.exists(),'Fresh public staging');out.mkdir(parents=True)
    status=read(cpu/'STATE.json');need(status['status']=='CPU_IMPLEMENTATIONS_BUILT_F0_S1_NOT_ADMITTED','CPU pipeline has not passed')
    for p in sorted(source.rglob('*')):
        if not p.is_file()or '__pycache__'in p.parts:continue
        rel=p.relative_to(source);safe_relative(rel.as_posix());raw=p.read_text()
        # Executable source must be byte-identical, not rewritten for privacy.
        need(public_text(raw,root)==raw,'Source contains a private path; fix source before F0')
        q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
    artifacts={
        'F0_DATA/MANIFEST.json':cpu/'prospective/MANIFEST.json',
        'F0_DATA/BUDGET_SUMMARY.json':cpu/'prospective/BUDGET_SUMMARY.json',
        'F0_DATA/DESCRIPTOR_INVENTORY.json':cpu/'prospective/DESCRIPTOR_INVENTORY.json',
        'F0_DATA/COMPILED_CLOSURE.public.json':cpu/'COMPILED_CLOSURE.private.json',
        'F0_DATA/CPU_STATE.json':cpu/'STATE.json',
        'F0_DATA/HISTORICAL_READER_FIXTURE.json':cpu/'HISTORICAL_READER_FIXTURE.json',
        'F0_DATA/CPU_NATIVE_ECHO.json':cpu/'CPU_ECHO.json',
        'F0_DATA/BACKEND_BUILD.public.json':cpu/'backend/BUILD.json',
        'F0_DATA/PRISTINE_GOLD_BUILD.public.json':cpu/'gold/BUILD.json',
        'F0_DATA/MODEL_BUILD.public.json':cpu/'model/BUILD.json',
        'F0_DATA/STATE_PROFILE.json':root/'q32-q4-full-20261109-01/STATE_PROFILE.json',
    }
    for label in ('design-normal','design-optimized','execution-normal','execution-optimized'):
        for stream in ('stdout','stderr'):artifacts['F0_DATA/'+label+'.'+stream+'.log']=cpu/(label+'.'+stream+'.log')
    for name in ('mmvq.cu.diff','ggml-cuda.cu.diff'):artifacts['F0_DATA/'+name]=cpu/'backend'/name
    for name in ('llama-graph.cpp.diff','entry.cpp.diff','geometry_observer.hpp.diff','worker.cpp.diff'):artifacts['F0_DATA/'+name]=cpu/'model'/name
    for name in ('COMPILED_ARTIFACT_REUSE.private.json','GRAPH_POLICY_READER_CORRECTION.json','FRESH_REUSED_NATIVE_ECHO.json'):
        if (cpu/name).is_file():artifacts['F0_DATA/'+name.replace('.private','.public')]=cpu/name
    transforms=[]
    for rel,p in artifacts.items():
        text=p.read_text();value=public_text(text,root);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(value)
        transforms.append(dict(public_path=rel,private_raw_sha256=sha(p),public_sha256=sha(q),
                               transform='exact private path prefixes only'if value!=text else'none'))
    fresh(out/'F0_DATA/TRANSFORM_COMMITMENTS.json',transforms)
    fresh(out/'F0_DATA/REGISTRATION.json',dict(schema='hs.strong.F0.v1',registered_utc=utc(),
          scope='S1 and fixed 72-operation S2; no new-epoch GPU output exists; any declared prior R reuse and failures remain retained',
          S3='User conditionally authorized; requires its own complete new-input/source/budget freeze before any S3 output',
          B2='User authorized as second priority; separate 8B ledger and complete admission required',
          model_native_requests_started=0,numeric_GPU_qualification='NOT_RUN',
          previous_epoch_requests=read(cpu/'prospective/MANIFEST.json')['budget'].get('prior_epoch_consumed_requests',0),
          historical_reader_fixture='CPU saved-byte parser test only, not current numerical qualification',
          raw_numeric_payloads='Retained privately; public hashes do not enable independent numeric replay'))
    files=[dict(path=p.relative_to(out).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
           for p in sorted(out.rglob('*'))if p.is_file()]
    fresh(out/'F0_INDEX.json',dict(schema='hs.strong.public-freeze-index.v1',prefix=PREFIX,files=files))


def verify(directory,commit,cache,output,index_name='F0_INDEX.json'):
    started=time.monotonic()
    need(re.fullmatch('[0-9a-f]{40}',commit),'Immutable commit SHA')
    need(not cache.exists(),'Fresh anonymous readback directory');cache.mkdir(parents=True)
    index=read(directory/index_name);need(index['prefix']==PREFIX,'Freeze repository prefix')
    records=index['files']+[dict(path=index_name,sha256=sha(directory/index_name),bytes=(directory/index_name).stat().st_size)]
    result=[]
    for e in records:
        rel=safe_relative(e['path']);public_path=PREFIX+'/'+rel.as_posix()
        url='https://raw.githubusercontent.com/leecdiang/HeteroSpec/'+commit+'/'+urllib.parse.quote(public_path,safe='/')
        with urllib.request.urlopen(url,timeout=60)as response:value=response.read()
        need(hashlib.sha256(value).hexdigest()==e['sha256']and len(value)==e['bytes'],'Anonymous full-file readback mismatch')
        p=cache/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
        result.append(dict(public_path=public_path,url=url,source_file=str(directory/rel),downloaded_file=str(p),
                           sha256=e['sha256'],bytes=e['bytes']))
    proof=dict(status='COMPLETE_FILE_BYTES_MATCHED',commit=commit,files=result,checked_utc=utc(),anonymous=True,
               download_elapsed_s=time.monotonic()-started,index_name=index_name)
    verify_public_readback(proof);fresh(output,proof)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('prepare');a.add_argument('--root',type=Path,required=True);a.add_argument('--source',type=Path,required=True)
    a.add_argument('--cpu',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    b=sub.add_parser('verify');b.add_argument('--directory',type=Path,required=True);b.add_argument('--commit',required=True)
    b.add_argument('--cache',type=Path,required=True);b.add_argument('--out',type=Path,required=True)
    b.add_argument('--index-name',choices=['F0_INDEX.json','F1_INDEX.json'],default='F0_INDEX.json')
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.root,a.source,a.cpu,a.out)
    else:verify(a.directory,a.commit,a.cache,a.out,a.index_name)


if __name__=='__main__':main()
