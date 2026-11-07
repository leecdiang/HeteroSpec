"""Reject selected-set, KV-hash and direct-ID corruption in isolated evidence copies."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
def clone(destination):
    paths=['benchmarks/b570_partition_intervention_v1','scripts/platform/b570_partition_intervention_v1',
        'artifacts/b570_partition_intervention_v1/raw','benchmarks/b570_direct_id_v1/protocol_v1.json',
        'benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json']
    for name in paths:
        src=ROOT/name
        files=src.rglob('*') if src.is_dir() else [src]
        for file in files:
            if not file.is_file() or '__pycache__' in file.parts:continue
            dest=destination/file.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);os.link(file,dest)
def replace_json(path,obj):
    # Replace a copied hardlink; never mutate authoritative evidence inode.
    tmp=path.with_suffix('.isolated.tmp');tmp.write_text(json.dumps(obj)+'\n',encoding='utf-8');tmp.replace(path)

def main():
    base=Path('C:/hs/b570-partition-verifier-tests');base.mkdir(parents=True,exist_ok=True)
    results=[]
    for test in ('selected_set','kv_digest','direct_ids'):
        with tempfile.TemporaryDirectory(prefix=test+'-',dir=base) as directory:
            fixture=Path(directory).resolve();assert fixture.is_relative_to(base.resolve())
            clone(fixture)
            if test=='selected_set':
                file=fixture/'benchmarks/b570_partition_intervention_v1/RESERVED_SET.json';obj=json.loads(file.read_text(encoding='utf-8'));obj['task_ids'].reverse();replace_json(file,obj)
                expected='salt selection'
            elif test=='kv_digest':
                file=next((fixture/'artifacts/b570_partition_intervention_v1/raw/r0').glob('*-control/record.json'))
                obj=json.loads(file.read_text(encoding='utf-8'));next(iter(obj['state_objects'].values()))['sha256']='0'*64;replace_json(file,obj);expected='decompressed KV bytes'
            else:
                file=next((fixture/'artifacts/b570_partition_intervention_v1/raw/r0').glob('*-baseline/ids.json'))
                obj=json.loads(file.read_text(encoding='utf-8'));obj['ids'][0]+=1;replace_json(file,obj);expected='frontend primary sidecar'
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/platform/b570_partition_intervention_v1/verify_complete.py'),'--root',str(fixture)],capture_output=True,encoding='utf-8')
            passed=proc.returncode!=0 and expected in proc.stdout
            results.append({'case':test,'rejected':passed,'exit_code':proc.returncode,'expected_failure':expected})
            assert passed,(test,proc.stdout[-2000:],proc.stderr)
            assert fixture.is_relative_to(base.resolve()) # verify cleanup scope
    out=ROOT/'benchmarks/b570_partition_intervention_v1/VALIDATOR_NEGATIVE_TESTS.json'
    out.write_text(json.dumps({'status':'PASS','cases':results,'no_model_inference':True,'authoritative_raw_untouched':True},indent=2)+'\n',encoding='utf-8')
    print('Independent verifier rejects all 3 isolated corruptions.',flush=True)

if __name__=='__main__':main()
