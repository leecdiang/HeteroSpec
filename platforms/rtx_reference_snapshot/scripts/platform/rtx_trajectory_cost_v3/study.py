"""Unified V3 entry. PREPARE_ONLY is default; formal stages require exact F0 review."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now,ledger
import engine,native_runner,guards,configuration,freeze,analysis
def read(name):return json.loads((STUDY/name).read_text(encoding='utf-8'))
def commit(message):
    subprocess.run(['git','add','scripts/platform/rtx_trajectory_cost_v3','benchmarks/rtx_trajectory_cost_v3','artifacts/rtx_trajectory_sufficiency_v3','artifacts/rtx_matched_qualification_cost_v2'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True)
def _assets(phase):
    import identity
    dest=ROOT/'work'/('ASSET_OBSERVATION_'+phase+'.json');identity.main(dest);actual=json.loads(dest.read_text());expected=read('ASSET_IDENTITY.json')
    for group in ['assets','runtime','frontends','driver_modules','timer_binaries']:
        for n,v in expected[group].items():
            if n not in actual[group] or actual[group][n]['sha256']!=v['sha256'] or actual[group][n]['bytes']!=v['bytes']:raise RuntimeError('IDENTITY_CHANGED: '+group+'/'+n)
    env=configuration.host(ROOT/'work'/('HOST_OBSERVATION_'+phase+'.json'));frozen=read('ENVIRONMENT.json')
    if env['GHelper_config_sha256']!=frozen['GHelper_config_sha256'] or env['os']!=frozen['os'] or env['gpu']['values'][:3]!=frozen['gpu']['values'][:3]:raise RuntimeError('HOST_CONFIGURATION_CHANGED')
    return dest

def assets(phase):
    try:return _assets(phase)
    except Exception as e:
        f=STUDY/'JOINT_BLOCKED.json'
        if not f.exists():save(f,{'status':'PROVENANCE_INVALID','phase':phase,'utc':now(),'reason':repr(e),'both_formal_studies_stopped':True,'same_study_repair_forbidden':True})
        raise
def authorize_review(args):
    if args.authorization!='EXECUTE_FROZEN' or not args.reviewed_sha or len(args.reviewed_sha)!=40:raise RuntimeError('Provide EXECUTE_FROZEN and reviewed full F0 SHA')
    r=guards.receipt('F0');guards.check_manifest('F0_MANIFEST.json')
    if args.reviewed_sha!=r['commit']:raise RuntimeError('REVIEWED_SHA_NOT_F0')
    if (STUDY/'AUTHORIZATION.json').exists():
        if read('AUTHORIZATION.json')['reviewed_source_sha']!=args.reviewed_sha:raise RuntimeError('review cannot be moved to different freeze')
    else:save(STUDY/'AUTHORIZATION.json',{'instruction':args.authorization,'reviewed_source_sha':args.reviewed_sha,'recorded_utc':now(),'basis':'explicit operator-supplied reviewed SHA and EXECUTE_FROZEN invocation; no authorization inferred from generic continue'})
def phase(name,phase,plan,timed=False):
    os.environ['HS_PHASE']=phase;os.environ['HS_RUN_NAMESPACE']=name;os.environ['HS_GRAPH_OBSERVER']='1'
    out=ROOT/'work'/name;out.mkdir(exist_ok=False);r={'phase':phase,'started_utc':now(),'execution_head':engine.source_head(),'planned_runs':len(plan),'runs':[],'status':'STARTED'};save(out/'records.json',r)
    for t,rep,c,w in plan:ledger({'event':'condition_planned','phase':phase,'task_id':t,'repetition':rep,'condition':c,'status':'PLANNED'})
    try:
        for t,rep,c,w in plan:
            if timed:time.sleep(2)
            if w in native_runner.WIRE:
                x=native_runner.execute(t,rep,w,out/'runs',c,timed=timed)
            else:
                tape=out/'runs'/f'{t.replace("/","-")}-r{rep}-H2_P_R/tape.jsonl' if w=='R_ONLY' else None
                x=engine.execute(t,rep,w,out/'runs',tape_path=tape)
            entry={**x,'canonical_condition':c,'path':(out/'runs'/x['run_id']).relative_to(ROOT).as_posix()};r['runs'].append(entry);save(out/'records.json',r)
            print(name,len(r['runs']),x['run_id'],x['status'],flush=True)
            if x['status']!='VALID':raise RuntimeError(x.get('error','invalid run'))
        r['status']='COMPLETE'
    except Exception as e:
        r.update(status='INCOMPLETE_OPERATIONAL_FAILURE',error=repr(e));raise
    finally:
        r['ended_utc']=now();r['not_reached']=len(plan)-len(r['runs']);save(out/'records.json',r)
        try:assets(phase+'_AFTER')
        except Exception as e:
            r.update(status='PROVENANCE_INVALID',error=repr(e));save(out/'records.json',r);raise
    return r
def pre_live(args):
    authorize_review(args);p=read('JOINT_PROTOCOL.json')
    if p['mode']!='A24_B24':raise RuntimeError('A_RESERVED_POOL_BLOCKED; A forwards remain zero')
    if (STUDY/'A_TERMINAL.json').exists():raise RuntimeError('A_TERMINAL_IRREVERSIBLE')
    assets('F1');guards.check_manifest('F0_MANIFEST.json')
    # Re-tokenize frozen formatted bytes using vocab-only loader; no context/decode.
    inp=read('INPUT_CONTRACT.json');tasks=p['A']['task_ids'];cmd=[str(ROOT/'work/h2-bin/T.exe'),str(engine.BIN),str(engine.TARGET)]
    q=b''.join((json.dumps({'task_id':t,'formatted_prompt':inp['inputs'][t]['formatted_utf8']})+'\n').encode() for t in tasks)
    tok=subprocess.run(cmd,input=q,capture_output=True,timeout=300);rows=[json.loads(x) for x in tok.stdout.splitlines()]
    if tok.returncode or [x['task_id'] for x in rows]!=tasks or any(x['forward_calls'] or x['prompt_ids']!=inp['reserved_tokens'][x['task_id']]['prompt_ids'] for x in rows):raise RuntimeError('F1 input re-tokenization differs')
    save(STUDY/'F1_INPUT_RECHECK.json',{'utc':now(),'status':'PASS','forward_calls':0,'task_ids':tasks,'stdout_sha256':engine.digest(tok.stdout),'formatted_inputs_bound_to_F0':True})
    paths=list(read('F0_MANIFEST.json')['files'])+[str((STUDY/'AUTHORIZATION.json').relative_to(ROOT)).replace('\\','/'),'benchmarks/rtx_trajectory_cost_v3/F1_INPUT_RECHECK.json']
    freeze.manifest('F1',paths);commit('RTX V3 F1 reviewed source and reserved input freeze');freeze.receipt('F1')
    plan=[(t,r,c,w) for t in tasks for r in [1,2,3] for c,w in zip(configuration.A[:4],configuration.AW[:4])]
    try:
        result=phase('A-pre-live','A_PRE_LIVE',plan)
        import verify_A
        checked=verify_A.pre_live(ROOT);qualification={k:v for k,v in checked.items() if k!='rows'};save(STUDY/'PRE_LIVE_QUALIFICATION.json',qualification)
        if qualification['status']!='PRE_LIVE_QUALIFIED':raise RuntimeError(qualification['status'])
    except Exception as e:
        status=read('PRE_LIVE_QUALIFICATION.json')['status'] if (STUDY/'PRE_LIVE_QUALIFICATION.json').exists() else 'INCOMPLETE_OPERATIONAL_FAILURE'
        save(STUDY/'A_TERMINAL.json',{'status':status,'utc':now(),'reason':repr(e),'same_cohort_A_resume_forbidden':True});raise
def seal_predictions():
    import verify_A,package
    q=verify_A.pre_live(ROOT)
    if q['status']!='PRE_LIVE_QUALIFIED':raise RuntimeError('F2 cannot seal failed pre-live qualification')
    p=read('JOINT_PROTOCOL.json');m=json.loads((ROOT/'work/A-pre-live/records.json').read_text());look={(x['task_id'],x['repetition'],x['canonical_condition']):x for x in m['runs']};rows=[]
    for t in p['A']['task_ids']:
        for r in [1,2,3]:
            h=look[t,r,'A_H2_P_R'];row={'task_id':t,'repetition':r,'input_sha256':h['input_sha256'],'tape_sha256':h['tape_sha256'],'conditions':{c:{k:look[t,r,c][k] for k in ['run_id','generated_ids','array_sha256','termination']} for c in configuration.A[:4]}}
            row['reference_differences']={c:analysis.diff(look[t,r,configuration.A[0]]['generated_ids'],look[t,r,c]['generated_ids']) for c in configuration.A[1:4]};rows.append(row)
    dest=STUDY/'A_trajectory/RESERVED_PREDICTIONS.json'
    if dest.exists():raise RuntimeError('sealed predictions cannot be overwritten')
    save(dest,{'study_id':p['A']['study_id'],'sealed_utc':now(),'rows':rows,'arrays_complete':True,'pre_live_runs':288})
    package.make('pre-live','A');freeze.manifest('F2');commit('RTX V3 F2 complete pre-live arrays and proposal tapes');freeze.receipt('F2')
def live():
    p=read('JOINT_PROTOCOL.json');guards.authorize(p['A']['task_ids'][0],'RTX_BATCHED_K2','A_LIVE');assets('A_LIVE');guards.check_manifest('F2_MANIFEST.json')
    try:
        m=phase('A-live','A_LIVE',[(t,r,configuration.A[4],'RTX_BATCHED_K2') for t in p['A']['task_ids'] for r in [1,2,3]])
        pre=json.loads((ROOT/'work/A-pre-live/records.json').read_text())['runs'];report=analysis.A_report(pre+m['runs'],p['A']);save(STUDY/'A_trajectory/REPORT.json',report)
        import verify_A
        v=verify_A.full(ROOT)
        for k in ['status','comparisons','reference_divergent_prompts','repeat_stability','candidates']:
            if v[k]!=report[k]:raise RuntimeError('independent A report mismatch '+k)
        save(STUDY/'A_trajectory/INDEPENDENT_VALIDATION.json',{'status':'PASS','result':v,'independent':True})
    except Exception as e:
        save(STUDY/'A_TERMINAL.json',{'status':'INCOMPLETE_OPERATIONAL_FAILURE','utc':now(),'reason':repr(e),'same_cohort_A_resume_forbidden':True,'reached_stage':'A_LIVE'});raise
def thermal():
    samples=[];start=time.monotonic();time.sleep(120)
    while time.monotonic()-start<=600:
        s=native_runner.telemetry();samples.append(s);save(STUDY/'B_THERMAL_ENTRY.json',{'status':'WAITING','samples':samples,'elapsed_seconds':time.monotonic()-start})
        if len(samples)>=3:
            last=samples[-3:];temps=[float(x['values'][3]) for x in last];utils=[float(x['values'][6]) for x in last]
            if max(utils)<=5 and max(temps)<=55 and max(temps)-min(temps)<=2:
                save(STUDY/'B_THERMAL_ENTRY.json',{'status':'PASS','samples':samples,'elapsed_seconds':time.monotonic()-start,'minimum_idle_seconds':120});return
        time.sleep(10)
    save(STUDY/'B_THERMAL_ENTRY.json',{'status':'BLOCKED','samples':samples,'elapsed_seconds':time.monotonic()-start,'minimum_idle_seconds':120,'reason':'fixed thermal entry thresholds not reached within 600 seconds'})
    raise RuntimeError('B_THERMAL_ENTRY_BLOCKED')
def B_formal(args):
    authorize_review(args);p=read('JOINT_PROTOCOL.json')
    if p['mode']=='A24_B24' and not (STUDY/'A_TERMINAL.json').exists():
        guards.receipt('F2')
        if not read('A_trajectory/REPORT.json').get('execution_complete'):raise RuntimeError('A must complete or be irreversibly terminated before B')
    assets('B_START');thermal();freeze.manifest('B_START');commit('RTX V3 B-start stack and thermal recheck');freeze.receipt('B_START')
    by=dict(zip(configuration.B,configuration.BW));schedule=read('B_matched_cost/schedule.json');plan=[(b['task_id'],b['repetition'],c,by[c]) for b in schedule for c in b['order']]
    result=phase('B-formal','B_FORMAL',plan,True);report=analysis.B_report(result['runs'],p['B']);save(STUDY/'B_matched_cost/REPORT.json',report)
    import verify_B
    save(STUDY/'B_matched_cost/INDEPENDENT_VALIDATION.json',verify_B.full(ROOT))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','seal-protocol','A-pre-live','seal-predictions','A-live','B-formal','verify','archive']);ap.add_argument('--authorization');ap.add_argument('--reviewed-sha');ap.add_argument('--source-tar',type=Path);a=ap.parse_args()
    if a.mode=='prepare':
        if (STUDY/'F0_MANIFEST.json').exists():raise RuntimeError('F0 already frozen; prepare cannot overwrite it')
        import audit,build,input_contract,identity,engineering,engineering_extra,negative
        import bootstrap
        bootstrap.prepare_dependencies(a.source_tar)
        audit.main();configuration.main()
        if not (ROOT/'work/h2-bin/P.exe').exists():build.main()
        if not (ROOT/'work/timer-build/bin/llama-cli.exe').exists():
            if not a.source_tar:raise RuntimeError('--source-tar required for isolated timer build')
            subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('build_timer.py')),'--source-tar',str(a.source_tar)],check=True)
        input_contract.main();identity.main(STUDY/'ASSET_IDENTITY.json');engineering.main('engineering-attempt1');engineering_extra.main();negative.main()
        import finalize
        finalize.main()
    elif a.mode=='seal-protocol':
        import verify_joint,package,closeout
        verify_joint.preparation(ROOT);package.make('engineering','A');package.make('engineering','B');closeout.index();freeze.manifest('F0');commit('RTX V3 protocol/engineering freeze; reserved not executed');print(json.dumps(freeze.receipt('F0')))
    elif a.mode=='A-pre-live':pre_live(a)
    elif a.mode=='seal-predictions':seal_predictions()
    elif a.mode=='A-live':live()
    elif a.mode=='B-formal':B_formal(a)
    elif a.mode=='verify':
        import verify_joint;print(json.dumps(verify_joint.all_reached(ROOT)))
    else:
        import package,closeout;closeout.reached();package.make('complete','A');package.make('complete','B');closeout.index()
if __name__=='__main__':main()
