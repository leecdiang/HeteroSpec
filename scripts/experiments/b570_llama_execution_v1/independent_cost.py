"""Standalone schedule, endpoint and cost reconstruction of every timing pair."""
from pathlib import Path
import argparse,hashlib,json,math
from independent_qualification import read,save,sha,require,endpoint,transactions

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def gm(x):return math.exp(math.fsum(math.log(v) for v in x)/len(x))
def audit(epoch,panel,out):
    epoch=Path(epoch);inputs=read(panel);refs=read(epoch/'QUALIFIED_REFERENCES.json');labels=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB');values={};pairs=[];warmups=0
    for session in range(6):
        ordered=sorted(range(len(inputs)),key=lambda i:digest(['b570-llama-v1',session,inputs[i]['id']]))
        expected=[]
        for i in ordered:
            shift=(int(digest(inputs[i]['id'])[:8],16)+session)%6
            for j in (0,1,5,2,4,3):expected.append((i,labels[(j+shift)%6]))
        for pair,(i,label) in enumerate(expected):
            unit=epoch/'units'/f's{session}-pair{pair:03d}';slots=read(unit/'SLOTS.json');supervisor=read(unit/'SUPERVISOR.json');receipt=read(unit/'RECEIPT.json');native=read(unit/'native/result.json')
            require(receipt['success'] and receipt['completed_model_requests']==2 and supervisor['status']=='complete' and supervisor['job_accounting']['active_processes']==0 and native['normal_cleanup_returned'] and len(native['records'])==2,'complete process pair')
            service=[]
            for index,stage in enumerate(('warmup','measured')):
                s=slots[index];ident=f'timing/s{session}/i{i}/{label}/{stage}';arm='C_PQ' if label.startswith('C_PQ') else label
                require(s['id']==ident and s['input']==inputs[i] and s['label']==label and s['arm']==arm and s['session']==session and s['stage']==stage and s['observer']=='off','independent Williams schedule')
                p=unit/'native'/(ident+'.json');r=read(p);require(r['slot']==s and not r['diagnostic'] and r['performance_eligible'],'clean service clock');require(endpoint(r)==refs[inputs[i]['id']],'reference endpoint');transactions(r)
                t=r['service_seconds'];require(math.isfinite(t) and t>0,'positive clean time');service.append(t)
                if stage=='measured':
                    key=(session,inputs[i]['id'],label);require(key not in values,'duplicate measurement');values[key]=t
                else:warmups+=1
            process=supervisor['charged_seconds'];require(process+0.1>=sum(service),'process/service accounting')
            pairs.append({'session':session,'input_id':inputs[i]['id'],'label':label,'warmup_seconds':service[0],'measured_seconds':service[1],'process_seconds':process,'process_nonrequest_seconds':process-sum(service),'host_owned_seconds':receipt['owned_seconds'],'job_user_seconds':supervisor['job_accounting']['user']/1e7,'job_kernel_seconds':supervisor['job_accounting']['kernel']/1e7,'supervisor_sha256':sha(unit/'SUPERVISOR.json')})
    require(len(values)==warmups==len(inputs)*36,'complete timing totals');blocks=[]
    for session in range(6):
        for x in inputs:
            t={label:values[session,x['id'],label] for label in labels};pq=(t['C_PQ_A']+t['C_PQ_B'])/2
            blocks.append({'session':session,'input_id':x['id'],'seconds':t,'layout':t['C_QB']/pq,'AA':t['C_PQ_A']/t['C_PQ_B'],'D_QB':t['M_QB']/t['C_QB'],'D_PQ':t['M_PQ']/pq,'CQB_R':t['C_QB']/t['R'],'MQB_R':t['M_QB']/t['R']})
    means={k:gm([b[k] for b in blocks]) for k in ('layout','AA','D_QB','D_PQ','CQB_R','MQB_R')};aa=[gm([b['AA'] for b in blocks if b['input_id']==x['id']]) for x in inputs];threshold=max(.02,max(max(x,1/x)-1 for x in aa));sessions=[gm([b['layout'] for b in blocks if b['session']==s]) for s in range(6)]
    report={'blocks':blocks,'means':means,'AA_threshold':threshold,'session_layout':sessions,'practical_layout_screen':1-means['layout']>threshold and all(x<1 for x in sessions),'QB_slower_blocks':sum(b['layout']>1 for b in blocks),'no_population_independence_claim':True}
    primary=read(epoch/'COST.json')
    for key in ('means','AA_threshold','session_layout','practical_layout_screen','QB_slower_blocks'):require(primary[key]==report[key],'independent cost differs from primary audit')
    save(out,{'status':'INDEPENDENT_ALL_COSTS_PASS','warmups':warmups,'measurements':len(values),'process_pairs':len(pairs),'totals':{k:math.fsum(p[k] for p in pairs) for k in ('warmup_seconds','measured_seconds','process_seconds','process_nonrequest_seconds','host_owned_seconds','job_user_seconds','job_kernel_seconds')},'report':report,'pairs':pairs,'panel_sha256':sha(panel),'primary_cost_sha256':sha(epoch/'COST.json'),'clock_scope':'Clean service includes fresh context construction, prefill, draft and verification, KV reconciliation, synchronization and context teardown. Process nonrequest remainder includes model loading/unloading and surrounding native work; it is not mislabeled a separately measured model-load phase.','all_failures_preserved_in_shared_ledger':True})
    print('INDEPENDENT_ALL_COSTS_PASS',len(values),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epoch',required=True);p.add_argument('--panel',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.epoch,a.panel,a.out)
