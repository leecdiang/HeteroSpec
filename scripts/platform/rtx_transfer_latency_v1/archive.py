"""Package each arm independently; revalidate an extracted copy offline."""
import argparse, gzip, json, shutil, subprocess, sys, tarfile
from pathlib import Path
import native as n
ROOT=n.ROOT;STUDY=n.STUDY;SOURCE=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def package(arm):
    raw=ROOT/('artifacts/rtx_predictive_transfer_v1' if arm=='prediction' else 'artifacts/rtx_matched_latency_v1')
    work=ROOT/'work'/('package-'+arm);work.mkdir(exist_ok=False)
    m=work/'metadata';m.mkdir();(m/arm).mkdir()
    for p in STUDY.iterdir():
        if p.is_file():shutil.copyfile(p,m/p.name)
    for p in (STUDY/arm).glob('*'):
        if p.is_file():shutil.copyfile(p,m/arm/p.name)
    if (STUDY/'chronology').exists():shutil.copytree(STUDY/'chronology',m/'chronology')
    frozen=read(STUDY/'runtime_freeze.json')
    for path,h in frozen['files'].items():
        dst=work/'frozen_source'/path;dst.parent.mkdir(parents=True,exist_ok=True)
        # Frozen file bytes, independent of later outcome-only commits.
        data=subprocess.check_output(['git','show',frozen['source_commit']+':'+path],cwd=ROOT)
        dst.write_bytes(data);assert n.sha(dst)==h,path
    for p in SOURCE.glob('verify*.py'):shutil.copyfile(p,work/p.name)
    shutil.copytree(ROOT/'work/joint-r0',work/'joint-r0')
    if (ROOT/'work/joint-r0-attempt1').exists():shutil.copytree(ROOT/'work/joint-r0-attempt1',work/'joint-r0-attempt1')
    for name in ('harness-preformal-interrupted','campaign-preformal-interrupted'):
        if (ROOT/'work'/name).exists():shutil.copytree(ROOT/'work'/name,work/name)
    for name in ('protocol-before-cap-amendment.json','R0-before-cap-amendment.json'):
        if (ROOT/'work'/name).exists():shutil.copyfile(ROOT/'work'/name,work/name)
    for p in (ROOT/'work').glob('timer-build*.log'):shutil.copyfile(p,work/p.name)
    if arm=='prediction':
        shutil.copyfile(ROOT/'work/exposure_inventory.json',work/'exposure_inventory.json')
        old=read(ROOT/'work/old-reference/formal_records.json');old['runs']=[r for r in old['runs'] if r['condition']=='TARGET_REFERENCE']
        n.save(work/'old_reference.json',old)
        phases=['harness_qualification','discovery_H1','reserved_prediction','reserved_live']
    else:phases=['formal']
    for name in phases:
        if (raw/name).exists():shutil.copytree(raw/name,work/name)
    validation=subprocess.check_output([sys.executable,str(SOURCE/f'verify_{arm}.py'),str(work),'--asset-root','D:/HeteroSpec-PC'],cwd=ROOT,text=True)
    result=json.loads(validation);n.save(work/'INDEPENDENT_VALIDATION.json',result);n.save(STUDY/arm/'INDEPENDENT_VALIDATION.json',result)
    n.save(work/'SHA256_MANIFEST.json',{'files':{p.relative_to(work).as_posix():n.sha(p) for p in work.rglob('*') if p.is_file()}})
    tarpath=ROOT/'work'/f'{arm}-evidence.tar.gz'
    with tarfile.open(tarpath,'w:gz',compresslevel=6) as t:
        for p in sorted(work.rglob('*')):
            if p.is_file():t.add(p,arcname=p.relative_to(work).as_posix())
    digest=n.sha(tarpath);dest=raw/f'{arm}-{digest}.tar.gz';shutil.copyfile(tarpath,dest)
    extracted=ROOT/'work'/('extracted-'+arm);extracted.mkdir(exist_ok=False)
    with tarfile.open(dest) as t:
        for member in t.getmembers():
            target=(extracted/member.name).resolve()
            if not member.isfile() or not target.is_relative_to(extracted.resolve()):raise ValueError('unsafe evidence archive entry')
        t.extractall(extracted,filter='data')
    offline=subprocess.check_output([sys.executable,str(extracted/f'verify_{arm}.py'),str(extracted)],cwd=ROOT,text=True)
    offline_result=json.loads(offline);assert offline_result['status']=='PASS'
    n.save(STUDY/arm/'OFFLINE_VALIDATION.json',offline_result)
    n.save(raw/'archive_manifest.json',{'arm':arm,'created_utc':n.now(),'file':dest.name,'sha256':digest,'bytes':dest.stat().st_size,
         'source_freeze_commit':frozen['source_commit'],'omitted':'weights, dataset download, binaries, build products, caches, credentials',
         'offline_validation':offline_result,'local_external_assets_rehashed':True})
    print(arm,dest.name,dest.stat().st_size,'offline PASS',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('arm',choices=['prediction','latency']);a=p.parse_args();package(a.arm)
