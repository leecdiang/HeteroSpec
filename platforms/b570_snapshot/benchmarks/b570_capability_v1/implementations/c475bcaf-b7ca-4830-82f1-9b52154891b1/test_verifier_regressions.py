"""CPU file-fixture tests against actual raw development evidence; all fixtures retained."""
import importlib.util,json,shutil,sys
from pathlib import Path
root=Path(sys.argv[1]);run=root/sys.argv[2];spec=importlib.util.spec_from_file_location('cap_verify',root/'src/rev2/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
base=root/'test_fixtures';base.mkdir(exist_ok=False);results=[]
def check(name,fn,expected):
    try:fn()
    except ValueError as e:
        if expected not in str(e):raise
        results.append(dict(test=name,outcome='REJECTED_FOR_EXPECTED_REASON',reason=str(e)));return
    raise AssertionError('negative fixture incorrectly accepted: '+name)
def altered(case,name,mutate):
    folder=base/name;shutil.copytree(run/case,folder);path=folder/'EVENTS.jsonl';rs=[json.loads(s) for s in path.read_text().splitlines()];mutate(rs);path.write_text(''.join(json.dumps(r)+'\n' for r in rs));return folder
normal=v.verify_case(run/'D0_C1');results.append(dict(test='valid_normal_raw',outcome='PASS',actors=normal['actors']))
def bad_timeout(rs):next(r for r in rs if r['event']=='TIMEOUT_CONTROL')['actor_alive']=False
folder=altered('D0_C2','timeout_not_alive',bad_timeout);check('timeout_not_alive',lambda:v.verify_case(folder),'timeout control')
def late_tree(rs):
    cutoff=next(r['at_ns'] for r in rs if r['event']=='TREE_READY_COMPLETE')
    for r in rs:
        if r['at_ns']>=cutoff:r['at_ns']+=6_000_000_000
        if r.get('exit_observed_ns',-1)>=cutoff:r['exit_observed_ns']+=6_000_000_000
folder=altered('D0_C3','late_tree_ready',late_tree);check('late_tree_ready',lambda:v.verify_case(folder),'complete tree READY')
def late_cleanup(rs):
    root_pid=next(r['pid'] for r in rs if r['event']=='PROCESS_CREATE' and r['role']=='root');cutoff=next(r['at_ns'] for r in rs if r['event']=='EXIT_OBSERVED' and r['pid']==root_pid)
    for r in rs:
        if r['at_ns']>cutoff:r['at_ns']+=6_000_000_000
        if r.get('exit_observed_ns',-1)>cutoff:r['exit_observed_ns']+=6_000_000_000
folder=altered('D0_C3','late_cleanup',late_cleanup);check('late_cleanup',lambda:v.verify_case(folder),'descendant cleanup')
empty=base/'empty_manifest.json';empty.write_text(json.dumps({'files':[]}));check('empty_manifest',lambda:v.audit(root,sys.argv[2],empty.relative_to(root).as_posix()),'empty manifest')
print(json.dumps(dict(status='CPU_VERIFIER_REGRESSIONS_PASS',tests=results),sort_keys=True))
