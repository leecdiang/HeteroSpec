"""Real CPU regressions only. Never selects any --gpu-* native mode."""
import copy, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
from common import V, load, save, sha, env, pin, wire
from exact_binding import admit
import publication as P
from lifecycle import Child

def main():
    out=V/'cpu_raw'/'legacy_regression_qpc';out.mkdir(exist_ok=False);cases=[]
    def case(name, fn, good=True):
        error=None
        try:fn()
        except Exception as e:error=repr(e)
        cases.append(dict(case=name,expected_accept=good,accepted=error is None,error=error))
        save(V/'CPU_QPC_TEST_PROGRESS.json',dict(cases=cases)) if not (V/'CPU_QPC_TEST_PROGRESS.json').exists() else (V/'CPU_QPC_TEST_PROGRESS.json').write_text(json.dumps(dict(cases=cases)),encoding='utf-8')
        if (error is None)!=good:raise AssertionError(name+':'+str(error))
    raw=b'{"supported":true}\r\n';artifact=out/'CENSUS.json';artifact.write_bytes(raw);decision=out/'DECISION.json';decision.write_bytes(b'{"admitted":true}\n')
    f0=out/'F0.json';f=dict(run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',execution_bound_census=pin(artifact),execution_bound_decision=pin(decision));save(f0,f)
    a=dict(run_id='pr116-s1b-cost-v1',execution_id='pr116-s1b-exact-r2',F0_sha256=sha(f0),census_sha256=sha(artifact),decision_sha256=sha(decision))
    case('exact_matching_bytes',lambda:admit(f,a,f0))
    def change(data):
        artifact.write_bytes(data)
        try:admit(f,a,f0)
        finally:artifact.write_bytes(raw)
    case('LF_vs_CRLF',lambda:change(raw.replace(b'\r\n',b'\n')),False)
    case('one_byte_mutation',lambda:change(raw.replace(b'true',b'True')),False)
    def missing():
        artifact.rename(out/'saved')
        try:admit(f,a,f0)
        finally:(out/'saved').rename(artifact)
    case('missing_Census',missing,False)
    case('truncated_Census',lambda:change(raw[:-3]),False)
    case('wrong_Census_hash',lambda:admit(f,a|dict(census_sha256='0'*64),f0),False)
    case('semantic_equal_whitespace_rejected',lambda:change(b'{ "supported" : true }\r\n'),False)
    copied=out/'copied.json';shutil.copyfile(artifact,copied);f2=f|dict(execution_bound_census=pin(copied));f2p=out/'F02.json';save(f2p,f2)
    case('authorized_byte_copy',lambda:admit(f2,a|dict(F0_sha256=sha(f2p)),f2p))
    case('F0_hash_mismatch',lambda:admit(f,a|dict(F0_sha256='0'*64),f0),False)
    case('caller_F0_body_mismatch',lambda:admit(f|dict(registration_id='forged'),a,f0),False)
    case('registration_mismatch',lambda:admit(f,a|dict(execution_id='other'),f0),False)
    case('wrong_Decision_hash',lambda:admit(f,a|dict(decision_sha256='0'*64),f0),False)
    # Actual Git ignore/index/tree boundaries in an isolated CPU fixture repo.
    repo=out/'git';repo.mkdir();subprocess.run(['git','init','-q'],cwd=repo,check=True)
    for k,val in [('user.name','CPU Fixture'),('user.email','cpu-fixture@invalid')]:subprocess.run(['git','config',k,val],cwd=repo,check=True)
    (repo/'.gitignore').write_text('raw/\n',encoding='utf-8');(repo/'.git/info/exclude').write_text('raw/nested/*\n',encoding='utf-8');p=repo/'raw/nested/data.json';p.parent.mkdir(parents=True);p.write_bytes(b'CPU_RAW_UNCHANGED')
    case('actual_archive_ignore_detected',lambda:subprocess.run(['git','check-ignore','-q',str(p.relative_to(repo))],cwd=repo,check=True))
    rows=P.stage_exact(repo,[p]);case('force_stage_exact_ignored_archive',lambda:subprocess.check_output(['git','show',':raw/nested/data.json'],cwd=repo)==b'CPU_RAW_UNCHANGED' or (_ for _ in ()).throw(ValueError('staged bytes')))
    subprocess.run(['git','commit','-q','-m','CPU exact archive fixture'],cwd=repo,check=True)
    case('actual_commit_tree_contains_exact_ignored_bytes',lambda:P.tree_exact(repo,'HEAD',rows))
    case('wrong_commit_member_hash',lambda:P.tree_exact(repo,'HEAD',[rows[0]|dict(sha256='0'*64)]),False)
    case('missing_archive_stage_rejected',lambda:P.stage_exact(repo,[repo/'missing']),False)
    # Real lossless packaging, fresh enumerate and corrupt/missing negatives.
    source=out/'source.zip';data=b'COMPLETE_CPU_RAW\r\n';m={'raw/CENSUS.json':dict(bytes=len(data),sha256=P.sha(data))}
    with zipfile.ZipFile(source,'x') as z:z.writestr('raw/CENSUS.json',data);z.writestr('MANIFEST.json',json.dumps(m))
    manifest=P.package_existing(source,out/'parts');case('archive_member_completeness',lambda:P.validate_archive(out/'parts',manifest))
    case('fresh_restore_enumerate_hash_all',lambda:P.validate_archive(out/'parts',manifest,out/'fresh'))
    case('fresh_existing_root_rejected',lambda:P.validate_archive(out/'parts',manifest,out/'fresh'),False)
    bad=copy.deepcopy(manifest);bad['members']['raw/CENSUS.json']['sha256']='0'*64
    case('manifest_hash_mismatch',lambda:P.validate_archive(out/'parts',bad,out/'bad'),False)
    assert not (out/'bad').exists();case('failed_restore_leaves_no_verified_root',lambda:not (out/'bad').exists() or (_ for _ in ()).throw(ValueError('partial verified root')))
    part=out/'parts/raw-000.zip.part';original=part.read_bytes()
    def bad_archive(data):
        part.write_bytes(data)
        try:P.validate_archive(out/'parts',manifest)
        finally:part.write_bytes(original)
    case('truncated_archive_rejected',lambda:bad_archive(original[:-1]),False)
    case('one_byte_archive_mutation',lambda:bad_archive(bytes([original[0]^1])+original[1:]),False)
    case('missing_declared_member',lambda:P.validate_archive(out/'parts',manifest|dict(member_count=2)),False)
    old=load(V.parent/'s1b_cost_v1/F0.json');helper=old['console_helper']
    fixture=out/'native';fixture.mkdir();nativef=dict(CPU_fixture_only=True,run_id=load(V/'PLAN.json')['run_id'],stage='S1B_COST_V1',hosts={l:dict(sha256=sha(V/f's1b_{l}.exe')) for l in ('clean','trace')},plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=old['runtime_directory'],numerical_DLLs=old['numerical_DLLs']);save(fixture/'F0.json',nativef)
    paths=[]
    for slot in load(V/'PLAN.json')['clean_slots'][:72]:
        p=fixture/f'{slot["index"]:03d}.json';save(p,wire(slot,fixture/'F0.json'));paths.append(str(p))
    save(fixture/'WIRES.json',dict(wires=paths));save(fixture/'LOOP.json',{})
    def native(label,role,mode,job,result):
        Child(helper).run([str(V/f's1b_{role}.exe'),mode,str(job),str(result)],out/label,60,env(old['runtime_directory']),512*1024**2)
    case('actual72_CPU_graph_serializer',lambda:native('graphs','clean','--cpu-graphs',fixture/'WIRES.json',V/'CPU_QPC_GRAPHS.json'))
    for role in ['clean','trace']:case('production_loop_CPU_'+role,lambda role=role:native('loop_'+role,role,'--cpu-loop',fixture/'LOOP.json',V/f'CPU_QPC_LOOP_{role}.json'))
    base=load(paths[0])
    for label,key,val in [('wrong_run','run_id','old'),('wrong_F0','approved_stage_F0','0'*64),('extra_warmup','warmups',2),('extra_call','graph_computes',10),('wrong_layout','layout','MQ'),('wrong_reference','ordinary_reference',{}),('wrong_output','native_output','other')]:
        p=fixture/(label+'.json');save(p,base|{key:val});case('native_'+label,lambda p=p,label=label:native(label,'clean','--cpu-wire',p,out/(label+'.out')),False)
    for script,report in [('test_readiness_cpu_qpc.py','CPU_QPC_READINESS_TESTS.json'),('test_bounded_cpu_qpc.py','CPU_QPC_BOUNDED_TESTS.json'),('test_audit_cpu_qpc.py','CPU_QPC_AUDIT_TESTS.json')]:
        case(script,lambda script=script:subprocess.run([sys.executable,'-B',str(V/script)],check=True))
    # Production native/source bits have not changed; no compilation is necessary.
    prior=V.parent/'s1b_cost_v1';case('native_binary_unchanged',lambda:None if sha(V/'s1b_clean.exe')==sha(prior/'s1b_clean.exe') else (_ for _ in ()).throw(ValueError('binary')))
    graph=load(V/'CPU_QPC_GRAPHS.json');assert graph['graphs']==72 and graph['new_CUDA_loads']==graph['new_GPU_queries']==graph['graph_computes']==0
    oldgraphs=load(prior/'CPU_GRAPHS_FINAL2.json');assert graph['records']==oldgraphs['records']
    case('all72_graphs_exactly_unchanged',lambda:None)
    expanded=[]
    for p in ['CPU_QPC_LOOP_clean.json','CPU_QPC_LOOP_trace.json']:expanded.extend(dict(suite=p,case=x['case'],status='PASS') for x in load(V/p)['cases'])
    rr=load(V/'CPU_QPC_READINESS_TESTS.json');expanded.extend(dict(suite='readiness',case=x if isinstance(x,str) else x['label'],status='PASS') for x in rr['positive']+rr['negative'])
    expanded.extend(dict(suite='bounded',case=x,status='PASS') for x in load(V/'CPU_QPC_BOUNDED_TESTS.json')['checks'])
    expanded.extend(dict(suite='raw_audit',case=x['case'],status='PASS') for x in load(V/'CPU_QPC_AUDIT_TESTS.json')['negative'])
    save(V/'CPU_QPC_TESTS.json',dict(status='PASS',top_level_cases=cases,expanded_subcases=expanded,test_total=len(cases)+len(expanded),passed=len(cases)+len(expanded),failed=0,CPU_graphs=72,actual_AV_words=graph['actual_PR116_AV_to_ordinary_words_checked'],GPU_queries=0,CUDA_loads=0,graph_computes=0,model_requests=0))
    print('PASS CPU repair regression',len(cases)+len(expanded),'assertion cases;72actual CPU graphs;GPU0')

if __name__=='__main__':main()
