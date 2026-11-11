"""Sealed-report arithmetic, not native/raw tensor replay. Python 3.11+; no network."""
from __future__ import annotations
import csv,hashlib,json,math,random,statistics,re
from collections import defaultdict,Counter
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PINS={'E2_SESSION_CONTRASTS.csv':'a723987e174f16e33d13e9f257360b66115176ff',
      'E1_CONTEXTS.csv':'23e499a9a1abcc12eab3ef608abbe4a3e7d11376',
      'E2_SESSION_TABLE.csv':'8c2664a683402ad6b8cc32ac15cc8228adefa446'}

def rows(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def quantile(xs,p):
    xs=sorted(xs);k=(len(xs)-1)*p;lo=int(k);hi=min(lo+1,len(xs)-1)
    return xs[lo]*(hi-k)+xs[hi]*(k-lo) if hi!=lo else xs[lo]
def estimate(logs):
    if len(logs)!=6 or not all(math.isfinite(x) for x in logs):raise ValueError('six finite logs required')
    rng=random.Random(20261014)
    boot=[statistics.fmean(rng.choices(logs,k=6)) for _ in range(10000)]
    return math.exp(statistics.fmean(logs)),math.exp(quantile(boot,.025)),math.exp(quantile(boot,.975))

def verify(check,root=ROOT):
    d=root/'anc/rtx104'
    for f,pin in PINS.items():check('PR104 exact Git blob: '+f,blob((d/f).read_bytes())==pin)
    raw=rows(d/'E2_SESSION_CONTRASTS.csv');groups=defaultdict(list)
    check('E2 36 unique family/path/session cells',len(raw)==len({(r['family'],r['path'],r['session']) for r in raw})==36)
    check('E2 12 qualified tasks in every session cell',all(r['qualified_task_count']=='12' for r in raw))
    for r in raw:groups[(r['family'],r['path'])].append((int(r['session']),float(r['log_latency_contrast'])))
    check('E2 exact six comparison groups',set(groups)=={(f,p) for f in ('Qwen','SmolLM2','Llama') for p in ('M','C')})
    reported={(r['family'],r['path']):r for r in rows(d/'e2_summary.csv')}
    tasks=rows(d/'task_ratios.csv');estimates={};reg=Counter()
    check('E2 72 unique task aggregates',len(tasks)==len({(r['family'],r['path'],r['task']) for r in tasks})==72)
    # This file contains selected reported columns, not an inferred request-level dataset.
    task_values=defaultdict(list)
    for r in tasks:
        x=float(r['ratio']);check('Positive finite E2 task '+r['family']+'/'+r['path']+'/'+r['task'],math.isfinite(x) and x>0)
        key=(r['family'],r['path']);task_values[key].append(x);reg[key]+=x<1
    for key,rs in groups.items():
        rs=sorted(rs);check('E2 all six sessions '+str(key),[s for s,x in rs]==list(range(6)))
        logs=[x for s,x in rs];point,lo,hi=estimate(logs);estimates['/'.join(key)]=dict(ratio=point,lower=lo,upper=hi)
        r=reported[key]
        check('E2 reproduced point and registered bootstrap '+str(key),all(abs(a-float(r[k]))<1e-12 for a,k in zip((point,lo,hi),('ratio','lower','upper'))))
        check('E2 task and session aggregate identity '+str(key),len(task_values[key])==12 and abs(math.exp(statistics.fmean(map(math.log,task_values[key])))-point)<1e-12)
        check('E2 task regressions '+str(key),reg[key]==int(r['regressions']))
    check('E2 nine regressed task aggregates retained',sum(reg.values())==9)
    check('E2 all observed session contrasts positive',all(float(r['log_latency_contrast'])>0 for r in raw))
    check('E2 all speculative lower intervals exceed1.02',all(v['lower']>1.02 for k,v in estimates.items() if k.endswith('/C')))
    check('E2 Qwen M uncertainty crosses practical threshold',estimates['Qwen/M']['lower']<1.02<estimates['Qwen/M']['upper'])
    check('E2 Llama M point below practical threshold',estimates['Llama/M']['ratio']<1.02)
    clock=rows(d/'E2_SESSION_TABLE.csv');starts=[datetime.fromisoformat(r['start_utc']) for r in clock];ends=[datetime.fromisoformat(r['complete_utc']) for r in clock]
    check('E2 all clock sessions present',[int(r['session']) for r in clock]==list(range(6)))
    span=(starts[-1]-starts[0]).total_seconds();gaps=[(starts[i]-ends[i-1]).total_seconds() for i in range(1,6)]
    check('E2 span and inter-session gaps',span>=86400 and min(gaps)>=3600)
    check('E2 324 workers and1620 requests',sum(int(r['native_workers']) for r in clock)==324 and sum(int(r['native_requests']) for r in clock)==1620)
    contexts=rows(d/'E1_CONTEXTS.csv')
    check('E1 72 observed admitted coordinates',len(contexts)==72 and all(r['status']=='PASS' and r['operator_failures']=='0' for r in contexts))
    fields=('capture_on_off_equal','own_path_QK','own_path_softmax','own_path_AV','repeatability_MQ','repeatability_PQ','repeatability_QB')
    check('E1 every required context control retained',all(r[k]=='True' for r in contexts for k in fields))
    layers={'Qwen':{0,18,35},'SmolLM2':{0,12,23},'Llama':{0,16,31}}
    expected={(f,l,p,q) for f,ls in layers.items() for l in ls for p in ('prefill','continuation') for q in (1,2,3,4)}
    check('E1 complete layer/phase/query grid',{(r['family'],int(r['layer']),r['phase'],int(r['q'])) for r in contexts}==expected)
    check('E1 all tensor key extents256 with padding',all(r['key_extent']=='256' for r in contexts))
    starts_visible={'Qwen':106,'SmolLM2':127,'Llama':124};maxima={}
    for f in layers:
        fr=[r for r in contexts if r['family']==f]
        for r in fr:
            q=int(r['q']);begin=1 if r['phase']=='prefill' else starts_visible[f]
            check('E1 exact visible-key vector '+r['index'],json.loads(r['visible_mask_keys'])==list(range(begin,begin+q)))
        maxima[f]=max(max(json.loads(r['visible_mask_keys'])) for r in fr)
    check('E1 visible maxima109/130/127, not256',maxima=={'Qwen':109,'SmolLM2':130,'Llama':127})
    check('E1 eighteen single-query controls',sum(r['q']=='1' for r in contexts)==18)
    report=json.loads((d/'summary.json').read_text())
    check('Sealed result source commit',report['commit']=='f997262d6b0accb126a1217c9356745cc8bbf708')
    E1=report['E1'];E2=report['E2']
    check('E1 216 requests,72 warmups,432 operator starts',E1['requests']==216 and E1['warmups']==72 and E1['operator_starts']==432)
    check('E1 pair-stage reported equality counts',all(E1['PQ_QB_equal'][s]==72 and E1['MQ_PQ_equal'][s]==18 and E1['MQ_QB_equal'][s]==18 for s in ('QK','softmax','AV')))
    check('E1 head/context exposure remains finite',E1['distinct_text_ids']==1 and E1['single_selected_exposed_prompt_per_family'] is True and E1['visible_key_max']==maxima)
    check('E2 workload equality is counters not traces',E2['workload_equal_pairs']==E2['all_pairs']==216)
    check('E2 full request arithmetic',E2['warmups']+E2['comparisons']+E2['references']==E2['requests']==1620)
    # Narrative and tables carry distinct report-level evidence, with no pending replacement.
    main=(root/'sections/05_evaluation.tex').read_text();supp=(root/'supplement/03_rtx_replication.tex').read_text()
    check('Completed results replace interim prose','All 72 contexts' in main and '1,620 requests' in main and '54 contexts' in main)
    for v in estimates.values():
        check('Printed E2 point '+str(v['ratio']),f"{v['ratio']:.6f}" in supp)
        check('Printed E2 interval '+str(v['ratio']),all(f'{v[k]:.6f}' in supp for k in ('lower','upper')))
    fig=(root/'figures/sessions.tex').read_text()
    ordered=[(f,p) for f in ('Qwen','SmolLM2','Llama') for p in ('M','C')]
    for key,y in zip(ordered,(6,5,4,3,2,1)):
        point=estimates['/'.join(key)]
        expected_points=[f'({math.exp(x):.9f},{y+.2:g})' for s,x in sorted(groups[key])]
        check('E2 all plotted session points '+str(key),all(v in fig for v in expected_points))
        check('E2 plotted estimate and asymmetric interval '+str(key),f"({point['ratio']:.12f},{y})" in fig and all(f"axis cs:{point[k]:.12f},{y}" in fig for k in ('lower','upper')))
    nf=(root/'figures/numeric.tex').read_text()
    check('E1 updated figure separates common controls',all(x in nf for x in ('18 / 72','72 / 72','18 single-query controls; 54 multi-query contexts')) and '24 / 24' not in nf)
    # Printed table follows the complete fixed task grid; no faster-task-only table.
    for task in sorted({x['task'] for x in tasks}):
        values=[]
        for f,p in ordered:
            values.append(float(next(x['ratio'] for x in tasks if (x['family'],x['path'],x['task'])==(f,p,task))))
        label=task.replace('GSM8K/test/','GSM8K ').replace('MBPP/','MBPP ')
        lines=[l for l in supp.splitlines() if l.startswith(label+'&')]
        check('E2 all six printed task ratios '+task,len(lines)==1 and [float(x) for x in re.findall(r'[01]\.\d{6}',lines[0])]==[round(x,6) for x in values])
    return dict(status='PASS',point_intervals=estimates,span_hours=span/3600,min_gap_seconds=min(gaps),
                observed_visible_maxima=maxima,scope='Original report tables and registered bootstrap arithmetic, not original request/raw-vector reconstruction.')

if __name__=='__main__':
    checks=[]
    def check(name,ok):
        if not ok:raise ValueError(name)
        checks.append(name)
    result=verify(check);print(json.dumps(dict(checks=len(checks),**result),indent=2))
