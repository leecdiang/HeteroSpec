"""Fixed exposed 12x3 engineering; failures and attempts persist, no reserved inference."""
import argparse,json,os,shutil,time
from pathlib import Path
from prepare import ROOT,STUDY,ENGINEERING,save,sha,now,ledger
import engine
import native_runner as native
import verify_common as verify

def main(attempt,resume_io=False):
    os.environ['HS_PHASE']='ENGINEERING';os.environ['HS_GRAPH_OBSERVER']='1'
    out=ROOT/'work'/attempt
    if resume_io:
        verify.require(not (STUDY/'F0_MANIFEST.json').exists(),'engineering recovery forbidden after F0')
        previous=verify.read(out/'records.json');verify.require(previous['status']=='ENGINEERING_BLOCKED' and 'PermissionError' in previous['error'] and all(r['status']=='VALID' for r in previous['runs']),'only a metadata replace failure with valid prefix may be recovered')
        recovery=out/'io-recovery';recovery.mkdir(exist_ok=False);shutil.copyfile(out/'records.json',recovery/'BLOCKED_RECORDS.json');shutil.copyfile(STUDY/'ENGINEERING_BASE_REPORT.json',recovery/'BLOCKED_BASE_REPORT.json');shutil.copyfile(ROOT/'work/ENGINEERING_STDOUT.log',recovery/'BLOCKED_STDOUT.log')
        p=verify.read(out/'ENGINEERING_PROTOCOL.json');expected=[(t,r,c) for t in ENGINEERING for r in [1,2,3] for c in p['engineering']['base_order']]
        verify.require([(r['task_id'],r['repetition'],r['condition']) for r in previous['runs']]==expected[:len(previous['runs'])],'recovery is not exact fixed prefix')
        for r in previous['runs']:
            d=ROOT/r['path'];tape=d.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['condition']=='R_ONLY' else None
            verify.require(verify.check_run(d,tape,STUDY)['ids']==r['generated_ids'],'recovery raw prefix invalid')
        report=previous;report.update(status='STARTED',io_recovery={'utc':now(),'retained_valid_prefix':len(previous['runs']),'no_model_retry':True,'cause':'atomic metadata replacement PermissionError; only unstarted scheduled items run'},blocks=[])
        loaded=out/'io-recovery/source_snapshot';loaded.mkdir()
        for f in Path(__file__).parent.iterdir():
            if f.suffix in ['.py','.cpp']:shutil.copyfile(f,loaded/f.name)
        cached={r['run_id']:r for r in report['runs']};save(out/'records.json',report)
    else:out.mkdir(exist_ok=False);cached={}
    if not resume_io:
        sources=out/'source_snapshot';sources.mkdir()
        for p in Path(__file__).parent.iterdir():
            if p.suffix in ['.py','.cpp']:shutil.copyfile(p,sources/p.name)
        save(out/'ENGINEERING_PROTOCOL.json',json.loads((STUDY/'JOINT_PROTOCOL.json').read_text()))
        report={'started_utc':now(),'phase':'ENGINEERING','attempt':attempt,'planned_base_runs':360,'runs':[],'blocks':[],'source_snapshot_sha256':{p.name:sha(p) for p in sources.iterdir()},'status':'STARTED','reserved_model_forwards':0}
        save(out/'records.json',report)
    def add(r,d,tape=None):
        path=d/r['run_id'];report['runs'].append({'path':path.relative_to(ROOT).as_posix(),**r});save(out/'records.json',report)
        print(len(report['runs']),r['run_id'],r['status'],flush=True)
        verify.require(r['status']=='VALID','engineering execution failed: '+str(r.get('error')))
        return verify.check_run(path,tape,STUDY)
    try:
        for task in ENGINEERING:
            for rep in [1,2,3]:
                runs=out/'runs';block={'task_id':task,'repetition':rep,'run_ids':{}}
                def n(w,label,timed=False):
                    rid=f'{task.replace("/","-")}-r{rep}-{label}'
                    if rid in cached:
                        r=cached[rid];block['run_ids'][label]=rid;return verify.check_run(ROOT/r['path'],metadata=STUDY)
                    r=native.execute(task,rep,w,runs,label,timed=timed);v=add(r,runs);block['run_ids'][label]=r['run_id'];return v
                def e(c,tape=None):
                    rid=f'{task.replace("/","-")}-r{rep}-{c}'
                    if rid in cached:
                        r=cached[rid];block['run_ids'][c]=rid;return verify.check_run(ROOT/r['path'],tape,STUDY)
                    os.environ['HS_RUN_NAMESPACE']=attempt
                    r=engine.execute(task,rep,c,runs,tape_path=tape);v=add(r,runs,tape);block['run_ids'][c]=r['run_id'];return v
                ref=n('REFERENCE_UB1','E_ORIGINAL_REFERENCE_UB1');rref=e('R_REFERENCE_UB1')
                verify.require(ref['ids']==rref['ids'] and ref['prompt_ids']==rref['prompt_ids'],'fresh reference harness differs')
                ub2=n('TARGET_ONLY_UB2','E_ORIGINAL_TARGET_ONLY_UB2');h=e('H2_P_R');tape=runs/h['run_id']/'tape.jsonl';ro=e('R_ONLY',tape)
                verify.require(h['ids']==ro['ids'],'fresh independent R_ONLY differs')
                bat=n('RTX_BATCHED_K2','E_ORIGINAL_BATCHED_K2');ser=n('RTX_SERIALIZED_K2','E_ORIGINAL_SERIALIZED_K2')
                tr=n('REFERENCE_UB1','E_TIMER_REFERENCE_UB1',True);tb=n('RTX_BATCHED_K2','E_TIMER_BATCHED_K2',True);ts=n('RTX_SERIALIZED_K2','E_TIMER_SERIALIZED_K2',True)
                verify.require(ref['ids']==tr['ids'] and bat['ids']==tb['ids'] and ser['ids']==ts['ids'],'timer changed original committed IDs')
                block.update(reference_exact=True,replay_exact=True,timer_exact={'reference':True,'batched':True,'serialized':True},observations={'UB2_live':verify.difference(ub2['ids'],bat['ids']),'H2_live':verify.difference(h['ids'],bat['ids'])})
                report['blocks'].append(block);save(out/'records.json',report)
        report['status']='BASE_PASS'
    except Exception as exc:
        report.update(status='ENGINEERING_BLOCKED',error=repr(exc));raise
    finally:
        report['ended_utc']=now();save(out/'records.json',report);save(STUDY/'ENGINEERING_BASE_REPORT.json',{k:v for k,v in report.items() if k!='runs'}|{'actual_complete_runs':sum(r['status']=='VALID' for r in report['runs']),'actual_attempted_runs':len(report['runs']),'raw_records_path':out.relative_to(ROOT).as_posix()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',default='engineering-attempt1');p.add_argument('--resume-metadata-failure',action='store_true');a=p.parse_args();main(a.attempt,a.resume_metadata_failure)
