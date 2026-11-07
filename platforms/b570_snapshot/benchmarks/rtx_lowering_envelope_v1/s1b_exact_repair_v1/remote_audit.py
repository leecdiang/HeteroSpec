"""Authenticated remote download -> fresh restore -> enumerate/hash every member."""
import argparse, datetime, json
from pathlib import Path
from common import V, load, save, sha, env
from lifecycle import Child
import publication as P

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);a=parser.parse_args()
    assert len(a.commit)==40 and all(c in '0123456789abcdef' for c in a.commit)
    old=load(V.parent/'s1b_cost_v1/F0.json');d=V/'cpu_raw/remote_download';d.mkdir(exist_ok=False)
    fresh=Path('D:/hs116-s1b-exact-r1-remote-fresh');assert not fresh.exists()
    rows=[]
    try:
        for i,name in enumerate(['delivery/raw/ARCHIVE_MANIFEST.json','delivery/raw/raw-000.zip.part','CPU_RECORDS.zip']):
            command=[old['gh']['path'],'api','repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/s1b_exact_repair_v1/'+name+'?ref='+a.commit,'-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity']
            prefix=d/str(i);save(prefix.with_suffix('.COMMAND.json'),dict(command=command,CPU_only=True))
            Child(old['console_helper']).run(command,prefix,120,env(''),512*1024**2,log_cap=40*1024**2)
            b=prefix.with_suffix('.stdout').read_bytes()
            if b!=(V/name).read_bytes():raise ValueError('actual authenticated remote bytes differ')
            target=d/Path(name).name
            with target.open('xb') as f:f.write(b)
            rows.append(dict(path=name,bytes=len(b),sha256=P.sha(b)))
        manifest=load(d/'ARCHIVE_MANIFEST.json')
        proof=P.validate_archive(d,manifest,fresh)
        execution=Path('D:/hs116-s1b-cost-v1/census/native/CENSUS.json')
        restored=fresh/'raw/census/native/CENSUS.json'
        assert restored.read_bytes()==execution.read_bytes()
        assert sha(restored)=='d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256'
        save(V/'REMOTE_ARCHIVE_VERIFIED.json',dict(status='VERIFIED',authenticated_remote_bytes=True,commit=a.commit,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),remote_files=rows,manifest_sha256=sha(d/'ARCHIVE_MANIFEST.json'),fresh_root=str(fresh),enumeration=proof,not_a_local_only_restore=True,new_GPU_queries=0,CUDA_loads=0,graph_computes=0))
        save(V/'CENSUS_EXACT_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,commit=a.commit,execution_bound_path=str(execution),execution_bound_sha256=sha(execution),execution_bound_bytes=execution.stat().st_size,remote_member='raw/census/native/CENSUS.json',remote_archive_sha256=manifest['archive_sha256'],manifest_sha256=sha(d/'ARCHIVE_MANIFEST.json'),JSON_normalization_used_for_binding=False))
        print('VERIFIED real remote download/fresh197member restore;exact native Census bytes authenticated')
    except BaseException as error:
        save(d/'FAILED.json',dict(error=repr(error),no_VERIFIED_on_failure=True,no_retry=True))
        raise

if __name__=='__main__':main()
