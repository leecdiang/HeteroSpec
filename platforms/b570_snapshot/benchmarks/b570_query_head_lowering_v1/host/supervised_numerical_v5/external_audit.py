"""CPU-only post-controller log audit and publication; never runs a graph."""
import argparse
import os
import pathlib
import shutil
import time
import zipfile
from legacy import HERE,OUT,EXTERNAL_LOG_ROOT,load,save,sha,need,modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--cpu-case');p.add_argument('--approved-f0-sha');p.add_argument('--launcher-begin-ns',type=int,required=True);a=p.parse_args()
    before=modules();begin=time.monotonic_ns()
    if a.cpu_case:
        case=load(a.cpu_case);need(case['purpose']=='CPU_LAUNCH_TEST','CPU audit purpose')
        external=pathlib.Path(case['external_log_root']);dest=pathlib.Path(case['protected_roots'][0])/'results/POST_CLOSE_CAPTURE';seconds=case['launcher_seconds']
    else:
        need(a.approved_f0_sha==sha(HERE/'F0.json'),'post-close exact F0')
        f0=load(HERE/'F0.json');external=EXTERNAL_LOG_ROOT;dest=HERE/'results/launcher';seconds=900
        for row in f0['bound_files']:need(sha(row['path'])==row['sha256'],'post-close binding drift')
    closed=load(external/'CLOSED.json');need(closed['readers_completed']==2 and closed['error'] is None,'capture incomplete; no qualification')
    expected={'CONTROLLER.stdout.log','CONTROLLER.stderr.log','INITIAL.json','LAUNCH_EVENTS.jsonl','CLOSED.json'}
    need({p.name for p in external.iterdir()}==expected,'unknown external file')
    need(sum(p.stat().st_size for p in external.iterdir())<=16*1024**2,'external16MiB budget')
    for row in closed['files']:
        p=external/row['name'];need(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'closing log hash/size')
    need(len(closed['files'])==4 and {r['name'] for r in closed['files']}==expected-{'CLOSED.json'},'complete closing manifest')
    dest.mkdir(parents=True,exist_ok=False);entries=[]
    for p in sorted(external.iterdir()):
        target=dest/p.name
        with target.open('xb') as f:f.write(p.read_bytes())
        need(sha(target)==sha(p),'post-exit sealed copy');entries.append(dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)))
    with zipfile.ZipFile(dest/'EXTERNAL_LOGS.zip','x',zipfile.ZIP_DEFLATED) as z:
        for row in entries:z.write(dest/row['name'],row['name'])
    with zipfile.ZipFile(dest/'EXTERNAL_LOGS.zip') as z:
        import hashlib
        for row in entries:need(hashlib.sha256(z.read(row['name'])).hexdigest()==row['sha256'],'external archive authentication')
    save(dest/'EXTERNAL_MANIFEST.json',dict(files=entries,archive_sha256=sha(dest/'EXTERNAL_LOGS.zip'),external_path=str(external),external_budget=16*1024**2,external_plus_export_reserved=32*1024**2,controller_returncode=closed['controller_exit_code'],controller_status=closed['status']))
    elapsed=time.monotonic_ns()-a.launcher_begin_ns
    save(dest/'LAUNCHER_FINISHED.json',dict(CPU_audit_pid=os.getpid(),controller_PID=closed['controller_pid'],controller_has_exited_before_this_tool=True,
        engineering_through_log_audit_ns=elapsed,within_registered_seconds=elapsed<=seconds*10**9,post_close_CPU_audit_seconds=(time.monotonic_ns()-begin)/1e9,
        modules_before=before,modules_after=modules(),graphs=0,device_queries=0,CPU_test=bool(a.cpu_case)))
    need(elapsed<=seconds*10**9,'whole launcher/controller/audit engineering budget')

if __name__=='__main__':main()
