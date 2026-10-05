"""Qualification controls; complete outputs compared to fixed historical evidence."""
import time
from prepare import *
from execution import unit, Worker

VARIANTS=['R_original','H_original','N_original','R_instrumented','H_plain','N_plain','H_sham','N_sham']

def selected_attempt(base):
    row=read(base/'result.json');prefixes={Path(p).parts[0] for p in row['files']};assert len(prefixes)==1
    return base/next(iter(prefixes))

def normalize_h(d):
    rows=[]
    for p in sorted(selected_attempt(d).glob('[PR]-wire.jsonl')):
        for line in p.read_text(encoding='utf-8').splitlines():
            x=json.loads(line)
            if x['event'] in ['startup','close','request_sent']:continue
            def clean(v):
                if isinstance(v,dict):return {k:clean(w) for k,w in v.items() if k not in ['logits_sha256','logits_bytes','transfer']}
                if isinstance(v,list):return [clean(w) for w in v]
                return v
            rows.append({'role':p.name[0],'event':x['event'],'request':x['request'],'response':clean(x['response'])})
    return rows

def normalize_native(d):
    rows=[]
    for p in selected_attempt(d).glob('trace.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():
            x=json.loads(line)
            if x['event'] in ['transfer','first_pending']:continue
            x.pop('sequence')
            if x['event']=='sample' and x['role']=='draft':
                # The pinned draft frontend overwrites the distribution draw with
                # sorted candidate0. Keep the draw in raw; compare actual proposals
                # in verify_decision and their logits/decode witnesses instead.
                x.pop('selected_id');x.pop('selected_score')
            rows.append(x)
    return rows

def run_g0():
    expected=read(DOC/'HISTORICAL_EXPECTED.json');checks=[];paths=[]
    for t in G0TASKS:
        for rep in range(1,4):
            rows={}
            for v in VARIANTS:
                c='R' if v.startswith('R') else 'H0' if v.startswith('H') else 'N0'
                if False and rep==1 and v in ['R_original','N_original']:
                    early=read(DOC/'EARLY_G0.json')['runs'];x=next(x for x in early if x['task']==t and x['condition']==c)
                    row={'ids':x['generated_ids'],'endpoint':x['termination'],'valid':x['status']=='VALID','reused_early_qualification':True,'path':str(next((OUT/'early-g0'/(t.replace('/','-')+'-'+c+'-r1')).glob('*')).relative_to(ROOT)).replace('\\','/')}
                else:
                    namespace=('g0-' if v.startswith('H') else 'g0-threads24-')+v
                    row=unit(t,c,rep,namespace,instrument=v in ['R_instrumented','N_plain','N_sham'],transfer=2 if v.endswith('sham') else 0,old=v=='H_original')
                    row['path']=str((OUT/namespace/(t.replace('/','-')+'-'+c+'-r'+str(rep))).relative_to(ROOT)).replace('\\','/')
                e=expected[f'{t}/{c}/{rep}'];equal=row['ids']==e['ids'] and row['endpoint']==e['endpoint']
                paths.append({'task':t,'rep':rep,'variant':v,'path':row['path'],'historical_equal':equal})
                save(DOC/'G0_THREADS24_PROGRESS.json',{'status':'QUALIFYING','arrays_completed':len(paths),'planned':120,'records':paths,'pair_checks':checks})
                if not equal:raise RuntimeError(f'historical baseline mismatch {t} {v} r{rep}')
                rows[v]=row
            assert normalize_h(ROOT/rows['H_plain']['path'])==normalize_h(ROOT/rows['H_sham']['path']),('H sham witness mismatch',t,rep)
            assert normalize_native(ROOT/rows['N_plain']['path'])==normalize_native(ROOT/rows['N_sham']['path']),('N sham witness mismatch',t,rep)
            checks.append({'task':t,'rep':rep,'arrays':8,'H_plain_sham':True,'N_plain_sham':True})
    save(DOC/'G0_THREADS24.json',{'status':'PASS','arrays':120,'plain_sham_pairs':30,'checks':checks,'records':paths,'native_threads':24,'H_arrays_reused_from_identical_H_qualification':45,'additional_native_arrays':75,'native_draw_control':'raw overwritten draft distribution draw retained; actual sorted proposals, target samples/scores, decodes/positions and decisions compared','utc':utc()})

def engineering():
    rows=[]
    for tid in read(DOC/'COHORT.json')['engineering']:
        t='MBPP/'+str(tid)
        for c in ['R','H0','H1','N0','N1']:
            row=unit(t,c,1,'engineering',instrument=c.startswith('N'),transfer=1 if c in ['H1','N1'] else 2 if c in ['H0','N0'] else 0)
            rows.append({'task':t,'condition':c,'valid':row['valid'],'seconds':row['elapsed_seconds'],'length':len(row['ids']),'endpoint':row['endpoint']})
            save(DOC/'ENGINEERING.json',{'status':'RUNNING','records':rows,'formal_units':0})
    times=[r['seconds'] for r in rows];estimate=645*max(times)*1.5+1200
    save(DOC/'ENGINEERING.json',{'status':'PASS','records':rows,'arrays':30,'per_unit_timeout_seconds':300,'estimated_formal_plus_hash_seconds':estimate,'basis':'1.5 x slowest complete engineering unit x645 plus1200s hashing; wall time is operational only','utc':utc()})

if __name__=='__main__':run_g0()
