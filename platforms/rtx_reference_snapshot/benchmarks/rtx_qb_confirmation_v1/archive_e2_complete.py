"""Fresh complete E2 raw archive and separate-interpreter CPU restoration."""
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import experiment as e
import export_e2_checkpoint as export

LIVE=Path('D:/hs-qb-confirmation-v02');HERE=Path(__file__).parent
STAGE=Path('D:/hs104-e2-complete-archive');RESTORE=Path('D:/hs104-e2-complete-restore')
def main():
    e.require(not (LIVE/'EXECUTION.lock').exists() and (LIVE/'SESSION-5-COMPLETE.json').exists(),'E2 must have ended')
    STAGE.mkdir(exist_ok=False);data=STAGE/'data';data.mkdir()
    for name in ('blocks','cooldown','ledger','runs','monitor','transport_recovery_20261014','exact_restoration_20261015','resumption_20261015'):
        if (LIVE/name).exists():shutil.copytree(LIVE/name,data/name)
    for p in LIVE.iterdir():
        if p.is_file() and p.suffix in ('.json','.log','.md'):shutil.copyfile(p,data/p.name)
    binaries=data/'native/build/bin';binaries.mkdir(parents=True)
    for name in ('llama-server.exe','llama-server-pq-metadata4.exe'):shutil.copyfile(LIVE/'native/build/bin'/name,binaries/name)
    code=STAGE/'analysis_scripts';code.mkdir()
    for name in ('experiment.py','export_e2_checkpoint.py','archive_e2_complete.py'):shutil.copyfile(HERE/name,code/name)
    for name in ('execution_20261014','recovery_20261015','registration'):
        shutil.copytree(HERE/name,code/name)
    # Original stopped-state/cancellation records remain history, not current gates.
    history=STAGE/'prior_terminal_seal';history.mkdir()
    for p in (HERE/'terminal_20261015').iterdir():
        if p.is_file() and p.suffix in ('.json','.csv','.md'):shutil.copyfile(p,history/p.name)
    expected=export.checkpoint_analysis(LIVE);e.save(STAGE/'EXPECTED_ANALYSIS.json',expected)
    manifest=dict(schema=1,scope='Complete six-session E2 raw plus preserved historical stop/recovery evidence',
                  models_and_numerical_DLL_bytes_included=False,files=[])
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():manifest['files'].append(dict(path=p.relative_to(STAGE).as_posix(),bytes=p.stat().st_size,sha256=e.sha(p)))
    e.save(STAGE/'RAW_MANIFEST.json',manifest)
    archive=HERE/'e2_completed_20261015/RAW_E2_FULL.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(STAGE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(STAGE).as_posix())
    RESTORE.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        e.require(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()),'archive traversal')
        z.extractall(RESTORE)
    for item in manifest['files']:
        p=RESTORE/item['path'];e.require(p.stat().st_size==item['bytes'] and e.sha(p)==item['sha256'],'restored E2 member differs')
    cmd=[sys.executable,'-B','-c',
         'from pathlib import Path;import experiment as e;import export_e2_checkpoint as x;'
         'e.save(Path("RECALCULATED.json"),x.checkpoint_analysis(Path("../data").resolve(),"D:/hs-qb-confirmation-v02"))']
    r=subprocess.run(cmd,cwd=RESTORE/'analysis_scripts',capture_output=True)
    (STAGE/'RESTORE_CPU.stdout.log').write_bytes(r.stdout);(STAGE/'RESTORE_CPU.stderr.log').write_bytes(r.stderr)
    e.require(r.returncode==0,'separate restored E2 CPU interpreter failed')
    e.require((RESTORE/'analysis_scripts/RECALCULATED.json').read_bytes()==e.encoded(expected),'six-session restored analysis differs')
    receipt=dict(status='PASS',complete_sessions=6,archive_sha256=e.sha(archive),archive_bytes=archive.stat().st_size,
                 members_checked=len(manifest['files']),fresh_directory=True,separate_interpreter=True,analysis_bitwise_equal=True,
                 original_scientific_fields_unchanged=True,metadata_scope='legacy code-bundle flag omitted by original export helper; no estimate/input excluded',
                 external_auditor=False,includes_models_or_numerical_DLL_bytes=False)
    e.save(HERE/'e2_completed_20261015/RAW_ARCHIVE_MANIFEST.json',manifest)
    e.save(HERE/'e2_completed_20261015/ARCHIVE_RESTORE.json',receipt)
    print(receipt)
if __name__=='__main__':main()
