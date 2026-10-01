"""Content-addressed evidence packaging and clean full offline reconstruction."""
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import now,digest,source_head
ART=ROOT/'artifacts/rtx_independent_proposal_replay_v2'
def make(mode):
    ART.mkdir(exist_ok=True);stage=ROOT/'work'/('package-'+mode);stage.mkdir(exist_ok=False)
    shutil.copytree(STUDY,stage/'metadata')
    source=stage/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2';source.mkdir(parents=True)
    for p in Path(__file__).parent.glob('*'):
        if p.is_file():shutil.copyfile(p,source/p.name)
    phases=['pre-live','frozen-checkpoints'] if mode=='pre-live' else ['reference-qualification','endpoint-probes','endpoint-probes-qualified','engineering-extra','discovery','pre-live','live','engineering-attempt1','engineering-attempt2','audit-attempts','build-attempts','frozen-checkpoints']
    for name in phases:
        p=ROOT/'work'/name
        if p.exists():shutil.copytree(p,stage/name,ignore=shutil.ignore_patterns('*.exe','*.dll','*.pdb','__pycache__'))
    for name in ['exposure_catalog.json','audit-attempt1.log','audit-attempt2.log','qualification.stdout.log','qualification.stderr.log','engineering-extra.stdout.log','engineering-extra.stderr.log','build-P.log','build-R.log','tokenizer-only.stdout.jsonl','tokenizer-only.stderr.log','tokenizer-build.log','endpoint-probe-attempt1-receipt.json']:
        p=ROOT/'work'/name
        if p.exists() and mode!='pre-live':shutil.copyfile(p,stage/name)
    if mode!='pre-live':
        upstream=stage/'pinned_upstream';upstream.mkdir()
        names=['LICENSE','include/llama.h','ggml/include/ggml.h','ggml/include/ggml-backend.h','ggml/include/ggml-cpu.h','ggml/include/ggml-opt.h','vendor/nlohmann/json.hpp','tools/server/server-context.cpp','tools/cli/cli.cpp','tools/cli/cli-context.cpp','common/common.cpp','common/common.h','common/speculative.cpp','common/sampling.cpp','common/chat.cpp','src/llama-batch.cpp','src/llama-context.cpp']
        for name in names:
            p=ROOT/'work/pinned-source'/name
            if p.exists():dest=upstream/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    entries={p.relative_to(stage).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(stage.rglob('*')) if p.is_file()}
    manifest={'schema':'RTX_H2_V2.complete_inventory','mode':mode,'content_head':source_head(),'created_utc':now(),'files':entries,'omitted':['model weights','downloaded dataset','runtime/frontend/compiler/driver binaries','credentials','bytecode/build caches'],'external_byte_authentication':'External identities were rehashed on original host; omitted bytes cannot be authenticated offline.'};save(stage/'MANIFEST.json',manifest)
    temporary=ROOT/'work'/('evidence-'+mode+'.tar.gz')
    with tarfile.open(temporary,'w:gz',compresslevel=6) as tar:
        for p in sorted(stage.rglob('*')):
            if p.is_file():tar.add(p,arcname=p.relative_to(stage).as_posix(),recursive=False)
    h=digest(temporary.read_bytes());dest=ART/(mode+'-'+h+'.tar.gz');shutil.copyfile(temporary,dest)
    record={'mode':mode,'path':dest.relative_to(ROOT).as_posix(),'sha256':h,'bytes':dest.stat().st_size,'file_count':len(entries)+1,'content_head':source_head(),'manifest_sha256':digest((stage/'MANIFEST.json').read_bytes())};save(STUDY/(mode.upper().replace('-','_')+'_ARCHIVE.json'),record)
    return dest
def offline(archive):
    # Never reuse the packaging directory as a reconstruction proof.
    dest=ROOT/'work'/('clean-reconstruction-'+digest(Path(archive).read_bytes())[:12]);dest.mkdir(exist_ok=False)
    with tarfile.open(archive) as t:t.extractall(dest,filter='data')
    cmd=[str(Path('D:/HeteroSpec-PC/python311/python.exe')),'-B',str(Path(__file__).with_name('offline.py')),str(dest)]
    p=subprocess.run(cmd,capture_output=True);(dest.parent/(dest.name+'.stdout.log')).write_bytes(p.stdout);(dest.parent/(dest.name+'.stderr.log')).write_bytes(p.stderr)
    if p.returncode:raise RuntimeError('clean offline reconstruction failed '+p.stderr.decode('utf-8',errors='replace'))
    result=json.loads(p.stdout);mode=Path(archive).name.split('-')[0].upper();save(STUDY/(mode+'_OFFLINE_RECONSTRUCTION.json'),result|{'archive_sha256':digest(Path(archive).read_bytes()),'fresh_directory':True,'bytecode_disabled':True,'utc':now()});return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['engineering','pre-live','complete']);p.add_argument('--verify',action='store_true');a=p.parse_args();archive=make(a.mode);print(archive)
    if a.verify:print(json.dumps(offline(archive)))
