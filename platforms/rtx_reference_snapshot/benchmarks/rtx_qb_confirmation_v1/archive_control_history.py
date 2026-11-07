"""Preserve ancillary control/export failures and exact recovery evidence."""
from pathlib import Path
import shutil
import zipfile
import experiment as e

HERE=Path(__file__).parent;FINAL=HERE/'final_20261015'
WORK=HERE.parents[2]
STAGE=Path('D:/hs104-control-history')
def main():
    STAGE.mkdir(exist_ok=False)
    workspace=Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/work')
    logs=STAGE/'work_logs';logs.mkdir()
    for p in workspace.glob('*.log'):shutil.copyfile(p,logs/p.name)
    for name in ('PR104_CONTINUATION.md','E2_AUTHENTICATED_RAW_READBACK.json','E2_ECONOMICS_COUNTER_RECHECK.json'):
        if (workspace/name).exists():shutil.copyfile(workspace/name,STAGE/name)
    recovery=workspace/'pr104-runtime-recovery-20261015';saved=STAGE/'runtime_recovery';saved.mkdir()
    for p in recovery.iterdir():
        if p.is_file() and (p.suffix in ('.py','.json','.log') or p.name in ('python-before-restoration.exe','python.exe')):
            shutil.copyfile(p,saved/p.name)
    for name,path in [('prior_delivery_failure',Path('D:/hs104c15b/PRIOR_DELIVERY_FAILURE.log')),
                      ('old_export_failure',Path('D:/hs104cp01/export_failures'))]:
        if path.is_dir():shutil.copytree(path,STAGE/name)
        elif path.is_file():shutil.copyfile(path,STAGE/(name+'.log'))
    manifest=dict(schema=1,scope='Ancillary control/export/download/cancellation/restoration logs; not scientific retries',
                  package_tarballs_excluded=True,files=[dict(path=p.relative_to(STAGE).as_posix(),bytes=p.stat().st_size,sha256=e.sha(p))
                                                     for p in sorted(STAGE.rglob('*')) if p.is_file()])
    e.save(STAGE/'RAW_MANIFEST.json',manifest)
    archive=FINAL/'RAW_CONTROL_HISTORY.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(STAGE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(STAGE).as_posix())
    e.save(FINAL/'RAW_ARCHIVE_MANIFEST_CONTROL.json',manifest)
    component=dict(name=archive.name,bytes=archive.stat().st_size,sha256=e.sha(archive))
    delivery=dict(schema=1,scope='All six E2 sessions, all72 E1 coordinates, complete tensor/source evidence and preserved control history',
                  scientific_retries=0,models_and_numerical_DLL_bytes_included=False,
                  E2=dict(path='benchmarks/rtx_qb_confirmation_v1/e2_completed_20261015/RAW_E2_FULL.zip',
                          commit='75e01db7b2b471137b638a0d6c2e5bb61a23838f',bytes=26237013,
                          sha256='ed3a87567b62c2610627783d43db00e187aef865aa7874d806428dd51d4a7227'),
                  E1=e.read(FINAL/'E1_ARCHIVE_ASSEMBLY.json'),CONTROL=component,
                  native_F0s=dict(E2='49b992b2ed1cabd05fad6e234cad2d3418c2b65a',E1='fea46ef7ffa0f553b6aa5c9f1a26f6296f1cd1ca'))
    e.save(FINAL/'RAW_ARCHIVE_MANIFEST.json',delivery)
    print(component)
if __name__=='__main__':main()
