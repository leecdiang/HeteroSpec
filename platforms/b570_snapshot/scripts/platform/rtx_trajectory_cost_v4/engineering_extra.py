"""Declared observer switches, real EOG/cap endpoints, and state branch fixtures."""
import argparse,ctypes,json,os,time
from pathlib import Path
from prepare import ROOT,STUDY,save,now,ledger
import engine
import native_runner as native
import verify_common as verify
def main(wait=False):
    base=ROOT/'work/engineering-attempt1/records.json'
    if wait:
        while True:
            r=verify.read(base)
            if r['status']=='BASE_PASS':break
            if r['status']!='STARTED':raise RuntimeError('base engineering blocked, extras not started')
            time.sleep(15)
    report_base=verify.read(base);verify.require(report_base['status']=='BASE_PASS','base qualification not complete')
    os.environ['HS_PHASE']='ENGINEERING';os.environ['HS_RUN_NAMESPACE']='engineering-extra'
    out=ROOT/'work/engineering-extra';out.mkdir(exist_ok=False);report={'started_utc':now(),'status':'STARTED','runs':[],'observer_pairs':[],'endpoint_probes':[],'fixtures':[]}
    def add(r,parent,tape=None,off=False):
        report['runs'].append({'path':(parent/r['run_id']).relative_to(ROOT).as_posix(),**r});save(out/'records.json',report)
        print(len(report['runs']),r['run_id'],r['status'],flush=True);verify.require(r['status']=='VALID','extra execution failed '+str(r.get('error')))
        return verify.check_run(parent/r['run_id'],tape,STUDY,observer_off=off)
    try:
        originals={'REFERENCE_UB1':'E_ORIGINAL_REFERENCE_UB1','TARGET_ONLY_UB2':'E_ORIGINAL_TARGET_ONLY_UB2','RTX_BATCHED_K2':'E_ORIGINAL_BATCHED_K2','RTX_SERIALIZED_K2':'E_ORIGINAL_SERIALIZED_K2'}
        timers={'REFERENCE_UB1':'E_TIMER_REFERENCE_UB1','RTX_BATCHED_K2':'E_TIMER_BATCHED_K2','RTX_SERIALIZED_K2':'E_TIMER_SERIALIZED_K2'}
        for task in ['HumanEval/3','HumanEval/106']:
            for timed,mapping in [(False,originals),(True,timers)]:
                for w,label in mapping.items():
                    r=native.execute(task,1,w,out/'observer-off',label+'_OBSERVER_OFF',timed=timed,debug='0');v=add(r,out/'observer-off')
                    b=next(x for x in report_base['runs'] if x['task_id']==task and x['repetition']==1 and x['condition']==label)
                    verify.require(v['ids']==b['generated_ids'],'native observer on/off changed IDs');report['observer_pairs'].append({'task_id':task,'on_run_id':b['run_id'],'off_run_id':r['run_id'],'exact':True,'kind':'TIMER' if timed else 'ORIGINAL'})
            os.environ['HS_GRAPH_OBSERVER']='0';tape=None
            for c in ['H2_P_R','R_ONLY','R_REFERENCE_UB1']:
                r=engine.execute(task,1,c,out/'graph-observer-off',tape_path=tape);v=add(r,out/'graph-observer-off',tape if c=='R_ONLY' else None,True)
                if c=='H2_P_R':tape=out/'graph-observer-off'/r['run_id']/'tape.jsonl'
                b=next(x for x in report_base['runs'] if x['task_id']==task and x['repetition']==1 and x['condition']==c)
                verify.require(v['ids']==b['generated_ids'],'metadata observer on/off changed IDs');report['observer_pairs'].append({'task_id':task,'on_run_id':b['run_id'],'off_run_id':r['run_id'],'exact':True,'kind':'REPLAY'})
            os.environ['HS_GRAPH_OBSERVER']='1';save(out/'records.json',report)
        probes=[('SYNTH_EOG','Reply with only OK.','EOS'),('SYNTH_CAP','Write a detailed 2000-word story about a lighthouse keeper discovering a lost island. Begin the story immediately and include descriptions and dialogue.','limit')]
        save(out/'ENDPOINT_PLAN.json',{'declared_utc':now(),'probes':probes,'engineering_only':True,'source':'Same fixed synthetic prompts as retained V2 qualified endpoints; integer enumeration is known to terminate early and is not used as cap coverage'})
        for task,text,term in probes:
            for timed,mapping in [(False,originals),(True,timers)]:
                for w,label in mapping.items():
                    r=native.execute(task,1,w,out/'endpoints',label+'_ENDPOINT',timed=timed,text=text);v=add(r,out/'endpoints');verify.require(v['termination']==term,'synthetic endpoint not triggered')
                    report['endpoint_probes'].append({'run_id':r['run_id'],'task_id':task,'length':len(v['ids']),'termination':term,'timed':timed})
            tape=None
            for c in ['H2_P_R','R_ONLY','R_REFERENCE_UB1']:
                r=engine.execute(task,1,c,out/'endpoints',text=text,tape_path=tape);v=add(r,out/'endpoints',tape if c=='R_ONLY' else None)
                if c=='H2_P_R':tape=out/'endpoints'/r['run_id']/'tape.jsonl'
                verify.require(v['termination']==term,'synthetic replay endpoint not triggered');report['endpoint_probes'].append({'run_id':r['run_id'],'task_id':task,'length':len(v['ids']),'termination':term,'timed':False})
        # These explicit branch witnesses use an already-exposed reference only.
        # They are constructed fixtures, never independent predictions.
        engine.set_context('HumanEval/3',1,'R_BRANCH_FIXTURES')
        fx=out/'constructed-R';fx.mkdir();log=(fx/'events.jsonl').open('wb');w=engine.Worker('R',2,fx,log)
        try:
            initial=w.call({'op':'init','formatted_prompt':engine.format_prompt(engine.prompts()['HumanEval/3'])});prefix=initial['committed_ids'].copy();pos=len(initial['prompt_ids'])
            ref=next(x['generated_ids'] for x in report_base['runs'] if x['task_id']=='HumanEval/3' and x['repetition']==1 and x['condition']=='E_ORIGINAL_REFERENCE_UB1');cases=[]
            for j,(name,length,wrong) in enumerate([('zero_proposal',0,None),('one_accept_bonus',1,None),('accept_then_correction',2,1),('first_rejection',2,0),('all_accept_bonus',2,None)]):
                props=ref[len(prefix):len(prefix)+length].copy()
                if wrong is not None:props[wrong]=0
                q={'op':'verify','round':j,'position':pos,'pending':prefix[-1],'proposal_ids':props};v=w.call(q);cases.append({'name':name,'request':q,'response':v});prefix+=v['committed_ids'];pos=v['next_position']
            verify.require([x['response']['accepted_proposals'] for x in cases]==[0,1,1,0,2],'constructed branch acceptance')
            verify.require(all(x['response']['suffix_delete_start']==x['response']['next_position'] for x in cases),'constructed rollback')
            report['fixtures'].append({'kind':'R_branches','cases':cases,'natural':False,'independent_prediction':False,'source':'new exposed HumanEval/3 reference'});save(fx/'FIXTURES.json',report['fixtures'][-1])
        finally:w.close();log.close()
        engine.set_context('HumanEval/3',1,'P_WIDTH_FIXTURES');px=out/'constructed-P';px.mkdir();log=(px/'events.jsonl').open('wb');rw=engine.Worker('R',2,px,log);pw=engine.Worker('P',2,px,log)
        try:
            ri=rw.call({'op':'init','formatted_prompt':engine.format_prompt(engine.prompts()['HumanEval/3'])});pw.call({'op':'init','formatted_prompt':engine.format_prompt(engine.prompts()['HumanEval/3'])});pos=len(ri['prompt_ids']);pending=ri['committed_ids'][-1];widths=[]
            for j,width in enumerate([0,1,2]):
                pp=pw.call({'op':'propose','position':pos,'pending':pending,'max_proposals':width});verify.require(len(pp['proposal_ids'])==width,'actual P requested width');v=rw.call({'op':'verify','round':j,'position':pos,'pending':pending,'proposal_ids':pp['proposal_ids']});pw.call({'op':'update','position':pos,'verified_batch':[pending]+pp['proposal_ids'],'retain_count':v['retain_count']});pos=v['next_position'];pending=v['committed_ids'][-1];widths.append({'requested':width,'response':pp,'R_response':v})
            report['fixtures'].append({'kind':'P_widths','widths':widths,'natural':False,'complete_scientific_conditions':0});save(px/'FIXTURES.json',report['fixtures'][-1])
        finally:pw.close();rw.close();log.close()
        qpc=ctypes.windll.kernel32.QueryPerformanceCounter;costs=[]
        for _ in range(10000):
            s=time.perf_counter_ns();q=ctypes.c_longlong();qpc(ctypes.byref(q));time.perf_counter_ns();qpc(ctypes.byref(q));time.perf_counter_ns();costs.append(time.perf_counter_ns()-s)
        shortest=min(r['timer']['milliseconds'] for r in report_base['runs']+report['runs'] if r.get('timer'));p99=sorted(costs)[9900]/1000
        hook={'samples':10000,'p99_microseconds':p99,'shortest_qualified_engineering_interval_ms':shortest,'p99_threshold_us':10,'fraction_threshold':.01,'clock_calls_only':True,'PASS':p99<=10 and p99/1000<shortest*.01};save(out/'CLOCK_PROBE.json',{'costs_ns':costs,**hook});verify.require(hook['PASS'],'clock hook threshold')
        report.update(status='PASS',hook_probe=hook,constructed_contexts=3,constructed_R_branch_cases=5,constructed_P_width_cases=3)
    except Exception as e:report.update(status='ENGINEERING_EXTRA_BLOCKED',error=repr(e));raise
    finally:
        report['ended_utc']=now();save(out/'records.json',report);save(STUDY/'ENGINEERING_EXTRA_REPORT.json',{k:v for k,v in report.items() if k!='runs'}|{'actual_complete_runs':sum(x['status']=='VALID' for x in report['runs']),'actual_attempted_runs':len(report['runs']),'raw_records_path':out.relative_to(ROOT).as_posix()})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--wait-for-base',action='store_true');a=p.parse_args();main(a.wait_for_base)
