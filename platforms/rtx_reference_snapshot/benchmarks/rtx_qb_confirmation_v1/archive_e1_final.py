"""Seal E1 raw without model/DLL copies; retain complete source and CPU checks.

Run only after owned native tasks end. Does not execute a model or operator.
Archive parts are capped at48MiB for the existing private GitHub Draft PR.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import experiment as e

LIVE=Path('D:/hs104-e1-v1');E2=Path('D:/hs-qb-confirmation-v02');HERE=Path(__file__).parent
STAGE=Path('D:/hs104-e1-final-archive');FINAL=HERE/'final_20261015'
PART=48*1024*1024

def main():
    e.require(not (LIVE/'EXECUTION.lock').exists(),'native E1 still active')
    e.require((LIVE/'RUN_COMPLETE.json').exists() or (LIVE/'RUN_FAILED.json').exists(),'E1 terminal receipt missing')
    STAGE.mkdir(exist_ok=False);FINAL.mkdir(exist_ok=False)
    # Original runtime adapter/model inputs are immutable; CPU reconstruction is
    # performed from actual bytes before any packaging result is declared.
    out=STAGE/'live_analysis'
    command=[sys.executable,'-B',str(HERE/'final_analysis.py'),'--e2',str(E2),'--e1',str(LIVE),'--out',str(out)]
    r=subprocess.run(command,capture_output=True)
    (STAGE/'LIVE_CPU.stdout.log').write_bytes(r.stdout);(STAGE/'LIVE_CPU.stderr.log').write_bytes(r.stderr)
    e.require(r.returncode==0,'live full CPU reconstruction failed; all inputs/logs retained')
    data=STAGE/'data';data.mkdir()
    for p in LIVE.iterdir():
        if p.name=='native':continue
        if p.is_dir():shutil.copytree(p,data/p.name)
        elif p.is_file():shutil.copyfile(p,data/p.name)
    shutil.copytree(LIVE/'native/source',data/'native/source')
    build=LIVE/'native/build';saved=data/'native/build';saved.mkdir(parents=True,exist_ok=True)
    for p in build.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(build)
        keep=(p.name in ('CMakeCache.txt','build.ninja','compile_commands.json') or p.suffix in ('.h','.hpp','.cmake','.rsp'))
        if keep:
            target=saved/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    binaries=saved/'bin';binaries.mkdir(exist_ok=True)
    for name in ('llama-server.exe','querylayout-replay.exe'):shutil.copyfile(build/'bin'/name,binaries/name)
    code=STAGE/'analysis_scripts';code.mkdir()
    for name in ('experiment.py','export_e2_checkpoint.py','final_analysis.py','archive_e1_final.py'):
        shutil.copyfile(HERE/name,code/name)
    for name in ('e1_integration_v1','analysis_helpers'):
        shutil.copytree(HERE/name,code/name)
    (code/'registration').mkdir();shutil.copyfile(HERE/'registration/E1_F0.json',code/'registration/E1_F0.json')
    manifest=dict(schema=1,scope='Full executed E1 matrix, including all failures/missing, actual tensor bytes and private native source',
                  model_weights_and_numerical_DLL_bytes_included=False,files=[])
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():manifest['files'].append(dict(path=p.relative_to(STAGE).as_posix(),bytes=p.stat().st_size,sha256=e.sha(p)))
    e.save(STAGE/'RAW_MANIFEST.json',manifest)
    archive=STAGE.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(STAGE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(STAGE).as_posix())
    parts=[]
    with archive.open('rb') as f:
        index=0
        while True:
            body=f.read(PART)
            if not body:break
            name=f'RAW_E1_FULL.zip.part{index:03d}'
            with (FINAL/name).open('xb') as output:output.write(body)
            parts.append(dict(name=name,bytes=len(body),sha256=e.digest(body)));index+=1
    assembly=dict(schema=1,full_archive_sha256=e.sha(archive),full_archive_bytes=archive.stat().st_size,
                  part_order='Concatenate the listed bytes in this exact list order; do not interpret each part as a ZIP',parts=parts)
    e.save(FINAL/'E1_ARCHIVE_ASSEMBLY.json',assembly);e.save(FINAL/'RAW_ARCHIVE_MANIFEST_E1.json',manifest)
    for p in out.iterdir():shutil.copyfile(p,FINAL/p.name)
    print('E1 archive complete',assembly,flush=True)
if __name__=='__main__':main()
