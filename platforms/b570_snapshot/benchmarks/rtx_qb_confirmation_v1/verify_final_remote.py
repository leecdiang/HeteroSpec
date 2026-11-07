"""Authenticated E1 part readback + fresh complete E2/E1 CPU reconstruction."""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile
import experiment as e

HERE=Path(__file__).parent;FINAL=HERE/'final_20261015'
ROOT=Path('D:/hs104-authenticated-final-restore')

def extract(archive,dest):
    dest.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        e.require(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()),'archive traversal')
        z.extractall(dest)
    manifest=e.read(dest/'RAW_MANIFEST.json')
    for item in manifest['files']:
        p=dest/item['path'];e.require(p.stat().st_size==item['bytes'] and e.sha(p)==item['sha256'],'restored member differs')
    return len(manifest['files'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-commit',required=True);a=p.parse_args()
    ROOT.mkdir(exist_ok=False);assembly=e.read(FINAL/'E1_ARCHIVE_ASSEMBLY.json');downloads=[]
    for item in assembly['parts']:
        target=ROOT/item['name'];route=f"repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_qb_confirmation_v1/final_20261015/{item['name']}?ref={a.data_commit}"
        with target.open('xb') as f:r=subprocess.run(['gh','api',route,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],stdout=f,stderr=subprocess.PIPE)
        (ROOT/(item['name']+'.stderr.log')).write_bytes(r.stderr)
        e.require(r.returncode==0 and target.stat().st_size==item['bytes'] and e.sha(target)==item['sha256'],'authenticated E1 archive part differs')
        downloads.append(dict(name=item['name'],sha256=e.sha(target),bytes=target.stat().st_size))
    archive=ROOT/'E1_FULL.zip'
    with archive.open('xb') as f:
        for item in assembly['parts']:
            with (ROOT/item['name']).open('rb') as source:
                while body:=source.read(1048576):f.write(body)
    e.require(e.sha(archive)==assembly['full_archive_sha256'],'assembled remote E1 archive differs')
    control=e.read(FINAL/'RAW_ARCHIVE_MANIFEST.json')['CONTROL'];control_file=ROOT/control['name']
    route=f"repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_qb_confirmation_v1/final_20261015/{control['name']}?ref={a.data_commit}"
    with control_file.open('xb') as f:r=subprocess.run(['gh','api',route,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],stdout=f,stderr=subprocess.PIPE)
    (ROOT/'CONTROL_DOWNLOAD.stderr.log').write_bytes(r.stderr)
    e.require(r.returncode==0 and e.sha(control_file)==control['sha256'] and control_file.stat().st_size==control['bytes'],'authenticated control history differs')
    # The E2 archive was already independently authenticated at its full data commit.
    e2remote=Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/work/REMOTE_RAW_E2_FULL.zip')
    e.require(e.sha(e2remote)=='ed3a87567b62c2610627783d43db00e187aef865aa7874d806428dd51d4a7227','authenticated complete E2 archive changed')
    n2=extract(e2remote,ROOT/'E2');n1=extract(archive,ROOT/'E1');nc=extract(control_file,ROOT/'CONTROL')
    code=ROOT/'E1/analysis_scripts';out=ROOT/'CPU_RECALCULATED'
    command=[sys.executable,'-B',str(code/'final_analysis.py'),'--e2',str(ROOT/'E2/data'),'--e1',str(ROOT/'E1/data'),'--out',str(out)]
    r=subprocess.run(command,cwd=code,capture_output=True)
    (ROOT/'CPU.stdout.log').write_bytes(r.stdout);(ROOT/'CPU.stderr.log').write_bytes(r.stderr)
    e.require(r.returncode==0,'fresh complete CPU reconstruction failed')
    comparisons=[]
    for p in sorted((ROOT/'E1/live_analysis').iterdir()):
        e.require(p.read_bytes()==(out/p.name).read_bytes(),'fresh analysis differs: '+p.name)
        comparisons.append(dict(name=p.name,sha256=e.sha(p),bitwise_equal=True))
    receipt=dict(status='PASS',data_commit=a.data_commit,complete_E2_remote_commit='75e01db7b2b471137b638a0d6c2e5bb61a23838f',
                 authenticated_remote_archive_parts=downloads,E2_members_checked=n2,E1_members_checked=n1,
                 CONTROL_members_checked=nc,CONTROL_archive_sha256=e.sha(control_file),
                 E1_full_archive_sha256=e.sha(archive),fresh_directory=True,separate_interpreter=True,
                 restoration_directory=str(ROOT),
                 analysis_bitwise_equal=True,comparisons=comparisons,external_auditor=False,new_native_starts=0)
    e.save(FINAL/'AUTHENTICATED_COMBINED_RESTORE.json',receipt)
    print(receipt)
if __name__=='__main__':main()
