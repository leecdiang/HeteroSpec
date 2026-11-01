"""Prospective panel, native slot generation, endpoint/state audit, paired costs."""
from __future__ import annotations
import argparse, collections, hashlib, importlib.util, json, math, re, struct
from pathlib import Path
from common import *
SEED='dense14b-transfer-20261101-v1'
STRATA={('code','short'):(128,384),('math','short'):(128,384),
        ('code','long'):(512,768),('math','long'):(512,768)}

def input_check(x):
    need(isinstance(x.get('id'),str) and x['id'],'input id')
    ids=x.get('prompt_ids');need(isinstance(ids,list) and ids,'prompt IDs missing')
    need(all(type(v) is int and 0<=v<151936 for v in ids),'prompt ID range')
    need(len(ids)+132<=1024 and x.get('cap')==128,'prompt/cap exceeds frozen context')
    need(x.get('prompt_ids_sha256')==prompt_hash(ids),'rendered prompt hash differs')
    for field in ('source_revision','text_sha256','tokenization_receipt_sha256'):
        need(isinstance(x.get(field),str) and x[field], 'missing '+field)
    return x

def select_panel(candidates, exposure):
    need(exposure.get('coverage_review_complete') is True,'historical exposure scan incomplete')
    excluded_ids=set(exposure['input_ids']);excluded_text=set(exposure['text_sha256'])
    excluded_tokens=set(exposure['prompt_ids_sha256']); groups=collections.defaultdict(list)
    seen_id=set();seen_text=set();seen_tokens=set()
    # Sorting precedes de-duplication: deterministic even if the input file is reordered.
    for x in sorted(candidates,key=lambda x:digest([SEED,x.get('id')])):
        input_check(x);k=(x.get('domain'),x.get('stratum'));need(k in STRATA,'domain/length stratum')
        lo,hi=STRATA[k];need(lo<=len(x['prompt_ids'])<=hi,'incorrect token-length label')
        i,h,t=x['id'],x['text_sha256'],x['prompt_ids_sha256']
        if i in excluded_ids or h in excluded_text or t in excluded_tokens:continue
        if i in seen_id or h in seen_text or t in seen_tokens:continue
        seen_id.add(i);seen_text.add(h);seen_tokens.add(t);groups[k].append(x)
    need(all(len(groups[k])>=3 for k in STRATA),'insufficient unexposed natural inputs in a stratum')
    return {'study_id':STUDY,'seed':SEED,'inputs':[x for k in STRATA for x in groups[k][:3]],
            'exposure_manifest_sha256':digest(exposure),'natural_inputs_only':True}

def spec(arm):
    a='C_PQ' if arm in ('C_PQ_A','C_PQ_B') else arm
    need(a in UNIQUE_ARMS,'unknown arm')
    scope='R' if a=='R' else a.split('_')[1]
    return {'arm':a,'experiment_arm':arm,'scope':scope,'layout_selector':1 if scope in ('PQ','R') else 0,
            'scoped_target':a!='R','target_ub':1 if a=='R' else 4,
            'target_outputs':1 if a=='R' else 4,'draft_enabled':a.startswith('C_'),
            'k':3 if a.startswith('C_') else 0}

def slots(panel, stage, session=0):
    items=panel['inputs'];need(stage in ('pilot','qualification','formal'),'stage')
    need(len(items)==(4 if stage=='pilot' else 12),'panel size')
    rows=[]
    order=list(range(len(items)));order=order[session%len(order):]+order[:session%len(order)]
    for i in order:
        x=input_check(items[i]); arms=ARMS if stage=='formal' else UNIQUE_ARMS
        shift=(i+session)%len(arms); ordered=arms[shift:]+arms[:shift]
        for a in ordered:
            for kind in (('warmup','measured') if stage=='formal' else ('heavy','off')):
                unit=stage+(f'/s{session}' if stage=='formal' else '')
                sid=f'{unit}/i{i:02d}/{a}/{kind}'
                rows.append({'schema':1,'study_id':STUDY,'family':'Qwen',
                    'model_id':'Qwen3-14B-Q8_0','slot_id':sid,'unit_id':unit,'source_index':i,
                    'input_id':x['id'],'prompt_ids_sha256':x['prompt_ids_sha256'],
                    'stage':stage,'session':session,'category':kind,
                    'observer':kind if kind=='heavy' else 'off','producer':'NATIVE',
                    'lifecycle':'resident',**spec(a)})
    return rows

def phases_map(record, ngl):
    """Requires actual QK operation placement at every target layer, no device guesses."""
    observed={}
    for g in record.get('geometry',[]):
        m=re.fullmatch(r'kq-(\d+)',g.get('name',''))
        if not m or g.get('op')!='MUL_MAT':continue
        layer=int(m[1]);need(0<=layer<40,'unexpected target layer')
        phase=g.get('phase');need(phase in ('PREFILL','ORDINARY','VERIFY'),'unknown geometry phase')
        dev=g.get('device','');need(dev and dev!='UNALLOCATED','unobserved device')
        gpu='5070' in dev; is_cpu=g.get('device_type')==0
        need(gpu or is_cpu,'unregistered compute device')
        need(gpu==(layer>=40-ngl),'unexpected attention placement; inspect actual scheduler before freeze')
        # All core matrix products keep the native QK source order.
        src=g.get('sources',[]);need(len(src)>=2,'missing Q/K operand descriptors')
        q=src[1]['ne'];k=src[0]['ne']
        need(len(q)==4 and q[0]==128 and q[2]==40,'wrong Q dimension/head count')
        need(len(k)==4 and k[0]==128 and k[2]==8,'wrong K head mapping')
        if record['observed_scope']=='QB':
            need(q[1]==1 and 1<=q[3]<=4,'QB lifted-query extent')
            if phase=='VERIFY':need(q[3]==4,'QB verification is not actual q4')
        elif record['observed_scope']=='PQ':need(q[1]==1 and q[3]==1,'PQ per-query extent')
        observed.setdefault(phase,{})[layer]='GPU' if gpu else 'CPU'
    need(set(observed.get('PREFILL',{}))==set(range(40)),'prefill placement coverage incomplete')
    if record['cycles']:need(set(observed.get('VERIFY',{}))==set(range(40)),'verification placement incomplete')
    return observed

def vector_index(root, record):
    folder=confined(root,record['slot']['slot_id']);n=151936;out={}
    for role in ('target','draft'):
        base=folder/role
        if not base.is_dir():continue
        for p in sorted(base.glob('*.f32')):
            need(p.stat().st_size==n*4,'not a complete vocabulary vector')
            b=p.read_bytes();v=struct.unpack('<'+str(n)+'f',b)
            need(all(math.isfinite(a) for a in v),'nonfinite full logits')
            expected=None;name=p.stem
            if name=='initial':expected=record['ids'][0]
            elif name.startswith('ordinary-'):expected=record['ids'][int(name.split('-')[1])]
            elif name.startswith('proposal-'):
                _,cy,row=name.split('-');expected=record['cycles'][int(cy)]['proposals'][int(row)]
            elif name.startswith('verify-'):
                _,cy,row=name.split('-');expected=record['cycles'][int(cy)]['decisions'][int(row)]
            need(expected is not None,'unknown logits role')
            need(max(range(n),key=v.__getitem__)==expected,'full-logit greedy decision differs')
            out[f'{role}/{p.name}']=hashlib.sha256(b).hexdigest()
    expected={'target/initial.f32'}
    if record['draft_enabled']:
        for i in range(len(record['cycles'])):
            expected|={f'draft/proposal-{i}-{j}.f32' for j in range(3)}
            expected|={f'target/verify-{i}-{j}.f32' for j in range(4)}
    else:expected|={f'target/ordinary-{j}.f32' for j in range(1,record['length'])}
    need(set(out)==expected,'missing or extra decision logits')
    for role in ('target','draft'):
        if role=='draft' and not record['draft_enabled']:continue
        p=folder/(role+'_final.state'); pin=record.get(role+'_state',{})
        need(p.is_file() and p.stat().st_size==pin.get('bytes') and file_hash(p)==pin.get('sha256'), 'state artifact differs')
    return out

def load_cycle_validator(repo):
    import tempfile
    # Use the existing independently checked transaction-conservation function.
    raw=upstream_bytes(repo,'study.py')
    ns={'__file__':str(Path(repo)/NATIVE_DIR/'study.py'),'__name__':'dense14b_inherited_auditor'}
    exec(compile(raw,ns['__file__'],'exec'),ns)
    return ns['validate_cycles']

def record_check(r, slot, item, binding, cycle_validator):
    need(r.get('slot')==slot,'record/slot mismatch')
    need(r.get('identity')==binding['families']['Qwen'],'native identity drift')
    need(r.get('prompt_ids')==item['prompt_ids'] and r.get('prompt_ids_sha256')==item['prompt_ids_sha256'],'native prompt drift')
    need(r.get('capture')==(slot['observer']=='heavy'),'capture drift')
    for k in ('arm','k','draft_enabled'):need(r.get(k)==slot[k], 'native '+k+' differs')
    need(r.get('observed_scope')==slot['scope'] and r.get('lifecycle')=='resident','scope/lifecycle drift')
    e=endpoint(r)
    need(e['eog']==[i in r['vocabulary_eog'] for i in e['ids']],'EOG classification mismatch')
    cycle_validator(r,dict(item,prompt_tokens=len(item['prompt_ids'])),
                    {'vocabulary_tokens':151936,'eog':r['vocabulary_eog']})
    positive(r.get('service_seconds'),'complete service time')
    return e

def qualification(root,panel,planned,binding,cycle_validator):
    root=Path(root);rows={};vectors={};placements={};errors=[];refs={};pair_results=[]
    for s in planned:
        try:
            r=read(confined(root,s['slot_id']+'.json'));item=panel['inputs'][s['source_index']]
            record_check(r,s,item,binding,cycle_validator)
            key=(s['source_index'],s['experiment_arm'],s['category']);need(key not in rows,'duplicate qualification slot')
            rows[key]=r
            if s['observer']=='heavy':
                vectors[key]=vector_index(root,r);placements[key]=phases_map(r,binding['dense14b']['target_gpu_layers'])
        except (ValueError,KeyError,OSError,TypeError) as exc:errors.append({'slot':s['slot_id'],'error':str(exc)})
    for i,item in enumerate(panel['inputs']):
        try:
            R=endpoint(rows[i,'R','heavy']);need(endpoint(rows[i,'R','off'])==R,'reference not repeatable')
            refs[item['id']]=R
            for arm in UNIQUE_ARMS:
                a,b=rows[i,arm,'heavy'],rows[i,arm,'off']
                need(endpoint(a)==endpoint(b)==R,'reference/observer failure: '+arm)
                for k in ('cycles','target_final_kv','draft_final_kv'):
                    need(a[k]==b[k],'observer changes state/trace: '+arm)
            for path in ('M','C'):
                a,b=rows[i,path+'_PQ','heavy'],rows[i,path+'_QB','heavy']
                need(placements[i,path+'_PQ','heavy']==placements[i,path+'_QB','heavy'],'PQ/QB actual placement differs')
                keys=('cycles','target_calls','draft_calls','target_final_kv','draft_final_kv')
                pair_results.append({'input_id':item['id'],'path':path,
                    'logical_work_equal':all(a[k]==b[k] for k in keys),
                    'full_logits_equal':vectors[i,path+'_PQ','heavy']==vectors[i,path+'_QB','heavy'],
                    'target_state_equal':a['target_state']==b['target_state'],
                    'draft_state_equal':path=='M' or a['draft_state']==b['draft_state']})
        except (ValueError,KeyError,TypeError) as exc:errors.append({'input':item['id'],'error':str(exc)})
    witness=any(r.get('cycles') for (i,a,c),r in rows.items() if a=='C_QB' and c=='heavy')
    if not witness:errors.append({'error':'no real multiquery speculative verification witness'})
    return {'status':'PASS' if not errors else 'UNQUALIFIED','errors':errors,
            'records':len(rows),'expected_records':len(planned),'references':refs,'paired_diagnostics':pair_results,
            'qualification_kind':'complete shared-reference endpoints; internal PQ/QB correspondence reported separately',
            'source_record_hashes':{s['slot_id']:file_hash(confined(root,s['slot_id']+'.json')) for s in planned if confined(root,s['slot_id']+'.json').is_file()}}

def analyze(records):
    need(len(records)==576,'full timing/warmup matrix required')
    t={}
    for r in records:
        s=r['slot'];key=(s['session'],s['source_index'],s['experiment_arm'],s['category'])
        need(key not in t,'duplicate timing cell');positive(r['service_seconds'],'service time');t[key]=r['service_seconds']
    expected={(s,i,a,k) for s in range(4) for i in range(12) for a in ARMS for k in ('warmup','measured')}
    need(set(t)==expected,'missing/foreign timing cell')
    blocks=[]
    for s in range(4):
        for i in range(12):
            v=lambda a:t[s,i,a,'measured'];pq=(v('C_PQ_A')+v('C_PQ_B'))/2
            blocks.append({'session':s,'input_index':i,'C_QB_over_dual_C_PQ':v('C_QB')/pq,
                 'M_QB_over_M_PQ':v('M_QB')/v('M_PQ'),'D_QB':v('M_QB')/v('C_QB'),
                 'D_PQ':v('M_PQ')/pq,'C_QB_over_R':v('C_QB')/v('R'),
                 'M_QB_over_R':v('M_QB')/v('R'),'AA':v('C_PQ_A')/v('C_PQ_B')})
    metric=lambda k:geomean(b[k] for b in blocks)
    aa=max(abs(geomean(b['AA'] for b in blocks if b['input_index']==i)-1) for i in range(12))
    sessions=[geomean(b['C_QB_over_dual_C_PQ'] for b in blocks if b['session']==s) for s in range(4)]
    ratio=metric('C_QB_over_dual_C_PQ')
    return {'status':'COMPLETE_PAIRED_PANEL','primary_ratio':ratio,'latency_reduction':1-ratio,
        'aa_max_input':aa,'session_ratios':sessions,'practical_screen_pass':1-ratio>max(.02,aa) and all(v<1 for v in sessions),
        'means':{k:metric(k) for k in blocks[0] if k not in ('session','input_index')},
        'blocks':blocks,'confidence_interval':None,
        'scope':'One 14B mixed-placement deployment; not a pure parameter-size effect or population inference.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidates',type=Path,required=True)
    ap.add_argument('--exposure',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();save(a.out,select_panel(read(a.candidates)['inputs'],read(a.exposure)),exclusive=True)
