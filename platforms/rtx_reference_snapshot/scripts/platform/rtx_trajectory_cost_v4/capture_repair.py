"""Thirty fresh exposed-task model runs qualify fixed simultaneous cap/EOG capture."""
import os,json,shutil,sys
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now
import native_runner as native,engine,verify_common as verify
def main(resume=False):
    out=ROOT/'work/capture-repair';cached={}
    if not resume:out.mkdir(exist_ok=False)
    sources=out/('verification-recovery/source_snapshot' if resume else 'source_snapshot');sources.mkdir(parents=True,exist_ok=False)
    for p in Path(__file__).parent.iterdir():
        if p.suffix in ['.py','.cpp']:shutil.copy2(p,sources/p.name)
    os.environ.update(HS_PHASE='ENGINEERING',HS_GRAPH_OBSERVER='1',HS_RUN_NAMESPACE='capture-repair')
    report={'phase':'ENGINEERING','scope':'Exposed HumanEval/59; not a prospective A observation','started_utc':now(),'status':'STARTED','planned_runs':30,'runs':[],'source_snapshot':{p.name:sha(p) for p in sources.iterdir()}}
    if resume:
        previous=verify.read(out/'records.json');verify.require(previous['status']=='ENGINEERING_BLOCKED' and len(previous['runs'])==5 and all(r['status']=='VALID' for r in previous['runs']) and 'NoneType' in previous['error'],'only this verifier-argument failure may continue')
        shutil.copy2(out/'records.json',out/'verification-recovery/FAILED_RECORDS.json');shutil.copy2(ROOT/'work/CAPTURE_REPAIR_STDOUT.log',out/'verification-recovery/FAILED_STDOUT.log')
        for r in previous['runs']:
            d=ROOT/r['path'];tape=d.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['condition']=='R_ONLY' else None
            verify.require(verify.check_run(d,tape,STUDY)['ids']==r['generated_ids'],'valid prefix raw verification');cached[r['run_id']]=r
        report=previous;report.update(status='STARTED',verification_recovery={'utc':now(),'retained_valid_prefix':5,'no_model_retry':True,'cause':'R_ONLY verifier tape argument omitted; original model input/tape and all five raw VALID records remain unchanged.'})
    save(out/'records.json',report)
    def add(r,tape=None):
        d=out/'runs'/r['run_id'];report['runs'].append({'path':d.relative_to(ROOT).as_posix(),**r});save(out/'records.json',report)
        print(len(report['runs']),r['run_id'],r['status'],flush=True)
        verify.require(r['status']=='VALID','capture repair qualification failure '+str(r.get('error')))
        return verify.check_run(d,tape,STUDY)
    try:
        for rep in [1,2,3]:
            task='HumanEval/59';runs=out/'runs'
            def known(c,tape=None):
                rid=f'HumanEval-59-r{rep}-{c}'
                return verify.check_run(ROOT/cached[rid]['path'],tape,STUDY) if rid in cached else None
            def n(w,c,timed=False):return known(c) or add(native.execute(task,rep,w,runs,c,timed=timed))
            def e(c,tape=None):return known(c,tape) or add(engine.execute(task,rep,c,runs,tape_path=tape),tape)
            ref=n('REFERENCE_UB1','E_ORIGINAL_REFERENCE_UB1');rr=e('R_REFERENCE_UB1')
            verify.require(ref['ids']==rr['ids'],'fresh UB1 reference mismatch')
            ub2=n('TARGET_ONLY_UB2','E_ORIGINAL_TARGET_ONLY_UB2');h=e('H2_P_R');tape=runs/h['run_id']/'tape.jsonl';ro=e('R_ONLY',tape)
            verify.require(h['ids']==ro['ids'],'fresh per-round replay mismatch')
            bat=n('RTX_BATCHED_K2','E_ORIGINAL_BATCHED_K2');ser=n('RTX_SERIALIZED_K2','E_ORIGINAL_SERIALIZED_K2')
            tr=n('REFERENCE_UB1','E_TIMER_REFERENCE_UB1',True);tb=n('RTX_BATCHED_K2','E_TIMER_BATCHED_K2',True);ts=n('RTX_SERIALIZED_K2','E_TIMER_SERIALIZED_K2',True)
            verify.require(ref['ids']==tr['ids'] and bat['ids']==tb['ids'] and ser['ids']==ts['ids'],'native timer ID equivalence changed')
            for r in [ref,ser,tr,ts]:verify.require(len(r['ids'])==128 and r['termination']=='EOS' and r['record']['native_stop_observations']==['limit','EOS'],'simultaneous EOG/cap coverage absent')
        report['status']='PASS'
    except Exception as e:report.update(status='ENGINEERING_BLOCKED',error=repr(e));raise
    finally:report['ended_utc']=now();save(out/'records.json',report)
    from verify_capture_repair import check
    save(STUDY/'CAPTURE_REPAIR_QUALIFICATION.json',check(ROOT,STUDY))
if __name__=='__main__':main('--resume-verification-failure' in sys.argv)
