"""Real freeze_check negative gates in disposable task-local copies; no child launch."""
import sys,json,shutil,importlib.util,os
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'src/rev2'))
from win import Journal,now,dump_new,sha
group=ROOT/'development/freeze-r1';group.mkdir(exist_ok=False)
mapping={'PROTOCOL.md':'CPU8_INTEGRATION.md','B570_PROMPT.md':'B570_PROMPT.md','REVIEW_BINDING.json':'REVIEW_BINDING.json','review/REPORT.json':'review/review-2.json','review/STATUS.json':'review/review-2-status.json'}
results=[]
for idx,mode in enumerate(['source_and_manifest','before_child_manifest','source_only','missing_pin']):
    folder=group/mode;folder.mkdir();log=Journal(folder/'EVENTS.jsonl');log.emit('CASE_BEGIN',case=mode,pid=os.getpid())
    sacrifice=folder/'sacrifice';(sacrifice/'src/rev2').mkdir(parents=True);(sacrifice/'acquisition/review').mkdir(parents=True)
    for p in (ROOT/'src/rev2').glob('*.py'):shutil.copyfile(p,sacrifice/'src/rev2'/p.name)
    for dst,src in mapping.items():shutil.copyfile(ROOT/'acquisition/repair'/src,sacrifice/'acquisition'/dst)
    (sacrifice/'CONFIG.json').write_text('{}\n')
    # freeze_check requires the exact real Python identity at initial baseline.
    # The sacrificial copy must reproduce that input BEFORE its F0 is hashed.
    (sacrifice/'preflight').mkdir()
    shutil.copyfile(ROOT/'preflight/TOOLS.json',sacrifice/'preflight/TOOLS.json')
    files={p.relative_to(sacrifice).as_posix():sha(p) for p in sacrifice.rglob('*') if p.is_file()}
    f=dict(source_relative='src/rev2',files=files,python=sys.executable,python_sha256=sha(sys.executable))
    fp=sacrifice/'CAPABILITY_FREEZE.json';fp.write_text(json.dumps(f,sort_keys=True)+'\n');initial=sha(fp)
    spec=importlib.util.spec_from_file_location('sacrificial_win_'+str(idx),sacrifice/'src/rev2/win.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
    if mode not in ['before_child_manifest','missing_pin']:w.freeze_check(sacrifice,initial);log.emit('INITIAL_BASELINE_ACCEPTED',freeze_sha256=initial)
    if mode in ['source_and_manifest','source_only']:
        p=sacrifice/'src/rev2/actor.py';p.write_bytes(p.read_bytes()+b'\n# sacrificial mutation\n')
        if mode=='source_and_manifest':f['files']['src/rev2/actor.py']=sha(p);fp.write_text(json.dumps(f,sort_keys=True)+'\n')
    elif mode=='before_child_manifest':f['replaced']=True;fp.write_text(json.dumps(f,sort_keys=True)+'\n')
    log.emit('ACTUAL_MUTATION',mode=mode,initial_sha256=initial,current_sha256=sha(fp))
    try:w.freeze_check(sacrifice,None if mode=='missing_pin' else initial)
    except (ValueError,RuntimeError) as e:
        expected='required' if mode=='missing_pin' else 'initial freeze digest mismatch' if mode=='before_child_manifest' else 'SOURCE_DRIFT' if mode=='source_only' else 'FREEZE_REPLACED'
        assert expected in str(e),(expected,str(e));log.emit('EXPECTED_DETECTOR',reason=str(e),expected=expected);results.append(dict(case=mode,status='PASS',reason=str(e)))
    else:raise AssertionError('actual freeze guard accepted '+mode)
    log.emit('CASE_CLOSED',case=mode,status='PASS');log.end()
dump_new(group/'RESULT.json',dict(status='NATIVE_FREEZE_GATES_PASS',cases=results,actor_starts=0));print(json.dumps(results,sort_keys=True))
