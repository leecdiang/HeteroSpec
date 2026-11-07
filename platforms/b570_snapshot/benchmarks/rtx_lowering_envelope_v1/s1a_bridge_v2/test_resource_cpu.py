"""Actual OS child-commit rejection and exact helper identity guard, CPU only."""
import sys
from pathlib import Path
from common import V,load,save,env
from lifecycle import Child

def main():
    helper=load(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json'))['console_helper']
    worker=Child(helper);error=None
    try:worker.run([sys.executable,'-B','-c','x=bytearray(256*1024*1024);print(len(x))'],V/'cpu_tests/commit_rejection',10,env(''),64*1024**2)
    except Exception as exc:error=repr(exc)
    assert error and load(V/'cpu_tests/commit_rejection.LIFETIME.json')['exit_code']!=0
    wrong=dict(helper,sha256='0'*64);rejected=False
    try:Child(wrong)
    except AssertionError:rejected=True
    assert rejected
    save(V/'CPU_RESOURCE_TESTS.json',dict(status='PASS',actual_256MiB_allocation_under_64MiB_job_rejected=True,lifetime=load(V/'cpu_tests/commit_rejection.LIFETIME.json'),wrong_console_helper_SHA_rejected_before_launch=True,GPU_queries=0,CUDA_loads=0))
    print('PASS actual Windows Job commit rejection and wrong helper identity rejection')
if __name__=='__main__':main()
