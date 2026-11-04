"""Reproducible CPU-only checks; no model downloads or GPU calls."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
def main(output):
    compiler=shutil.which('g++')
    if not compiler:raise SystemExit('g++ is required; native protocol checks NOT_RUN')
    records=[]
    def run(cmd):
        r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        records.append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode:raise RuntimeError(r.stderr)
        return r.stdout
    with tempfile.TemporaryDirectory(prefix='hs-contract-') as d:
        flags=['-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-pthread','-I',str(ROOT/'src/reference_batching')]
        lib=str(Path(d)/'libhscontract.so');exe=str(Path(d)/'contract-test')
        run([compiler,*flags,'-fPIC','-shared',str(ROOT/'src/reference_batching/packing_gate.cpp'),'-o',lib])
        run([compiler,*flags,str(ROOT/'tests/reference_contract/test_execution.cpp'),'-L'+d,'-lhscontract','-Wl,-rpath,'+d,'-o',exe])
        run([exe])
        sanitized=str(Path(d)/'sanitized-test')
        run([compiler,*flags,'-fsanitize=undefined','-fno-sanitize-recover=all',
             str(ROOT/'tests/reference_contract/test_execution.cpp'),
             str(ROOT/'src/reference_batching/packing_gate.cpp'),'-o',sanitized])
        run([sanitized])
        run([sys.executable,'-m','unittest','discover','-s','tests/reference_contract','-p','test_*.py','-v'])
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
           for folder in ('src/reference_batching','tests/reference_contract','scripts/reference_contract')
           for p in sorted((ROOT/folder).glob('*')) if p.is_file()}
    files['src/query_layout/state_lineage.py']=hashlib.sha256((ROOT/'src/query_layout/state_lineage.py').read_bytes()).hexdigest()
    result={'status':'CPU_PROTOCOL_AND_SOURCE_FIXTURE_TESTS_PASS','platform':platform.platform(),
            'python':platform.python_version(),'compiler':subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],
            'gpu_executions':0,'full_llama_build':'NOT_RUN','windows_dll':'NOT_RUN',
            'actual_pr171_source_staging':'NOT_RUN','new_numerical_equivalence':'NOT_ESTABLISHED',
            'records':records,'source_sha256':files}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','source_sha256')},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output)
