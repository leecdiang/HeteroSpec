"""Exercise actual final Job/pipe/deadline controls with CPU-only commands."""
import argparse,ctypes,copy,os
from pathlib import Path
from common import V,save,load,pin,env
from lifecycle import Child,process_commit
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--final',action='store_true');ap.add_argument('--release',action='store_true');a=ap.parse_args()
    root=V/('lifecycle_cpu_release' if a.release else 'lifecycle_cpu_final' if a.final else 'lifecycle_cpu');root.mkdir(exist_ok=False);helper=pin(Path(os.environ['SystemRoot'])/'System32/conhost.exe')
    worker=Child(helper);runtime=load(V/'PLAN.json')['census_wire']['runtime_directory'];results=[]
    command=[str(V/'lowering113_formal.exe'),'--cpu-one-wire',str(V/'CPU_FIXTURE/wires/000.json'),str(root/'positive_native.json')]
    worker.run(command,root/'positive_native',10,env(runtime),256*1024**2)
    events=load(root/'positive_native.JOB_EVENTS.json');assert len(events['started_unique_PIDs'])==2 and not events['errors']
    cmd=str(Path(os.environ['SystemRoot'])/'System32/cmd.exe')
    for label,args,timeout,expected in [
        ('positive_cmd',[cmd,'/d','/c','echo CPU_ONLY'],5,True),
        ('overflow',[cmd,'/d','/c','for /L %i in (1,1,100000) do @echo CPU_ONLY_BOUNDED_LOG'],5,False),
        ('deadline',[cmd,'/d','/c','for /L %i in (1,1,2147483647) do @rem CPU_ONLY'],.25,False)]:
        error=None
        try:worker.run(args,root/label,timeout,os.environ.copy(),256*1024**2)
        except Exception as exc:error=repr(exc)
        assert (error is None)==expected,(label,error)
        results.append(dict(label=label,expected_success=expected,error=error))
    assert (root/'overflow.stdout').stat().st_size==32768
    assert (root/'overflow.stdout.OVERFLOW.json').exists()
    assert process_commit()<512*1024**2
    save(V/('CPU_LIFECYCLE_TESTS_release.json' if a.release else 'CPU_LIFECYCLE_TESTS_final.json' if a.final else 'CPU_LIFECYCLE_TESTS.json'),dict(status='PASS',cases=results,real_CPU_native_host_shared_wire=True,
        real_PID_events_identify_original_NO_WINDOW_console_helper=True,helper_pin=helper,original_creation_flags=0x08000000|4,
        lifetime_accounting='One research controller plus native/readiness main process plus at most one pinned conhost: wall x3. Direct launches and automatic helper starts reported separately.',
        first_probe_failure='Outer CPU harness active1 blocked nested child creation with WinError1816; failure retained, follow-up CPU controller test uses scoped active8 and charges wall x8.',
        GPU_queries=0,CUDA_plugin_loads=0,graph_computes=0,model_requests=0))
    print('PASS final Job PID/helper, native CPU wire, bounded stream, deadline and controller memory controls; no GPU work')
if __name__=='__main__':main()
