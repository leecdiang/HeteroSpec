"""Never invoke without separate author approval. Not run during the CPU review."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(HERE/'generated'));sys.path.insert(0,str(ROOT))
from common import load,save,sha,modules
from diagnostic_child import child
import core,evidence


def expected_assertion(index,folder,request):
    raw=[json.loads(line) for line in (folder/'raw.jsonl').read_text().splitlines()]
    layout=next(x for x in raw if x['event']=='PHYSICAL_LAYOUT')
    a=layout['minStorageBufferOffsetAlignment'];ts=layout['tensors']
    life=load(folder/'LIFECYCLE.json');stderr=(folder/'stderr.log').read_text(encoding='utf-8')
    core.need(raw[0]['event']=='HOST_START' and raw[0]['pid']==life['pid'] and raw[0]['request']==request,'raw process/request mismatch')
    core.need(life['request_sha256']==sha(folder/'REQUEST.wire') and life['raw_sha256']==sha(folder/'raw.jsonl'),'raw byte hash mismatch')
    core.need(all(t['device_matches'] and t['buffer_relative_offset']+t['bytes']<=t['buffer_bytes'] for t in ts),'physical bounds/device gate')
    core.need(any(x['event']=='DEVICE' and 'B570' in x['description'] for x in raw),'device identity')
    core.need(life['graph_start_events']==1,'exactly one owned graph call')
    core.need(life['stop'] is None and life['returncode']==3221226505,'unexpected exit/watchdog')
    core.need(raw[-1]['event']=='GRAPH_START' and life['graph_return_events']==0,'unexpected partial execution')
    if index==0:
        q=next(x for x in ts if x['ctx_id']==1)
        core.need(a>0 and q['buffer_relative_offset']%a!=0,'Q offset does not explain expected negative')
        core.need('GGML_ASSERT(allow_misalign || misalign_bytes == 0) failed' in stderr,'wrong q1 assertion')
    else:
        masks=[x for x in ts if x['op']=='VIEW' and x['ne']==[63,1,1,1] and x['view_offset']==252]
        core.need(len(masks)==1 and masks[0]['buffer_relative_offset']%a!=0,'PQ mask offset does not explain negative')
        core.need('GGML_ASSERT(!src1 || get_misalign_bytes(ctx, src1) == 0) failed' in stderr,'wrong PQ-mask assertion')
    return dict(classification='EXPECTED_NEGATIVE_LAYOUT_ASSERTION',actual_alignment=a,
                exact_dynamic_callsite_confirmed=False,reason='physical offset and source branch consistent; no native stack captured')


def main():
    p=argparse.ArgumentParser();p.add_argument('--author-approved-f0-sha',required=True);args=p.parse_args()
    before=modules();digest=sha(HERE/'DIAGNOSTIC_F0.json');core.need(args.author_approved_f0_sha==digest,'exact new F0 author approval required')
    f0=load(HERE/'DIAGNOSTIC_F0.json')
    for name,h in f0['sources'].items():core.need(sha(ROOT/name)==h,'source changed '+name)
    for x in [f0['executable']]+f0['dependencies']+f0['driver_files']:core.need(sha(x['path'])==x['sha256'],'runtime changed')
    environment={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
    core.need(environment==f0['environment'],'environment changed')
    core.need(sha(HERE/'DIAGNOSTIC_PLAN.json')==f0['plan_sha256'],'plan changed')
    slots=load(HERE/'DIAGNOSTIC_PLAN.json')['slots'];core.need(len(slots)==7,'wrong diagnostic budget')
    for s in slots:core.need(sha(s['input'])==s['input_sha256'],'input changed')
    run=ROOT/'host_outputs/alignment_review_v1/DIAGNOSTIC_RUN';run.mkdir(exist_ok=False)
    outcomes=[];owned=0.;error=None;outputs={}
    ledger=(run/'LEDGER.jsonl').open('x',encoding='utf-8')
    def record(event,**data):
        ledger.write(json.dumps(dict(event=event,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**data))+'\n');ledger.flush()
    try:
        for s in slots:
            folder=run/s['id']
            request={k:s[k] for k in ('study','cell','input','mode','q_offset_bytes','relocate_pq_mask')}
            request.update(F0_sha256=digest,kind='graph',output_dir=str(folder/'vectors'))
            record('ATTEMPT',slot=s['id'],index=s['index'],request=request)
            try:
                raw,life=child(request,folder,f0,owned)
                result=dict(classification='COMPLETE_NUMERICAL_GRAPH',owned_wall_s=life['owned_wall_s'])
                layout=next(x for x in raw if x['event']=='PHYSICAL_LAYOUT')
                core.need(layout['minStorageBufferOffsetAlignment']>0,'missing actual alignment')
                core.need(all(t['device_matches'] and t['buffer_relative_offset']+t['bytes']<=t['buffer_bytes'] for t in layout['tensors']),'physical bounds/device gate')
                key=core.sha(s['cell']);path=folder/'vectors/final.f32'
                for other in outputs.get(key,[]):
                    metrics=evidence.compare_f32(path,other)
                    record('FULL_VECTOR_DIFFERENCE_RETAINED',slot=s['id'],metrics=metrics)
                    if s['cell']['geometry']['q']==1:core.need(metrics['bitwise_equal'],'q1 common arithmetic changed under storage relocation')
                outputs.setdefault(key,[]).append(path)
            except Exception:
                if s['index'] not in (0,2):raise
                # Runtime hashes, wire and planned numerical modules must still be admitted.
                life=load(folder/'LIFECYCLE.json');core.need(bool(life['actual_runtime_modules']),'runtime gate did not complete')
                result=expected_assertion(s['index'],folder,request)
            outcomes.append(dict(slot=s['id'],index=s['index'],**result));record('OUTCOME',**outcomes[-1])
            owned=sum(load(p)['owned_wall_s'] for p in run.glob('*/LIFECYCLE.json'))
    except Exception as e:error=str(e);record('STOP',error=error)
    finally:
        owned=sum(load(p)['owned_wall_s'] for p in run.glob('*/LIFECYCLE.json'))
        started=[p.name for p in run.iterdir() if p.is_dir()]
        record('CLOSE',owned_wall_s=owned);ledger.close()
        save(run/'CLOSEOUT.json',dict(status='STOPPED' if error else 'DIAGNOSTIC_COMPLETE_PENDING_ANALYSIS',error=error,
             outcomes=outcomes,attempts=len(started),started=started,unstarted=[s['id'] for s in slots if s['id'] not in started],
             owned_wall_s=owned,retries=0,warmups=0,model_requests=0,automatic_S2_S3=False,modules_before=before,modules_after=modules()))
    if error:raise SystemExit(error)


if __name__=='__main__':main()
