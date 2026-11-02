"""Llama-specific endpoint/raw audit and complete paired cost; no GPU execution."""
from __future__ import annotations
import array, math, sys
from pathlib import Path
from lr_common import *
from schedule import LABELS

def full_vector(path):
    p=Path(path);need(p.stat().st_size==VOCAB*4,'full Llama vector length')
    v=array.array('f');v.frombytes(p.read_bytes())
    if sys.byteorder!='little':v.byteswap()
    need(all(math.isfinite(x) for x in v),'nonfinite full vector')
    return max(range(VOCAB),key=lambda i:v[i]),file_hash(p)

def verify_vectors(r,folder):
    expected={'target/initial.f32':r['ids'][0]}
    if r['draft_enabled']:
        for c in r['cycles']:
            for i,t in enumerate(c['proposals']):expected[f'draft/proposal-{c["cycle"]}-{i}.f32']=t
            for i,t in enumerate(c['decisions']):expected[f'target/verify-{c["cycle"]}-{i}.f32']=t
    else:expected.update({f'target/ordinary-{i}.f32':t for i,t in enumerate(r['ids'][1:],1)})
    folder=Path(folder);files={p.relative_to(folder).as_posix():p for role in ('target','draft') for p in (folder/role).glob('*.f32')}
    need(set(files)==set(expected),'missing/extra decision vectors')
    hashes={}
    for name,t in expected.items():
        actual,h=full_vector(files[name]);need(actual==t,'greedy argmax differs '+name);hashes[name]=h
    return hashes

def transaction(r):
    e=endpoint(r);need(all(r[k]==e[k] for k in END_KEYS),'nested endpoint differs')
    p=r['prompt_tokens'];ids=r['ids']
    if 'vocabulary_eog' in r:
        eos=set(r['vocabulary_eog']);need(r['eog']==[t in eos for t in ids],'native EOG inventory differs')
    else:eos={t for t,f in zip(ids,r['eog']) if f} # historical R reports stop flags, not a new vocabulary oracle
    if not r['draft_enabled']:
        need(not r['cycles'],'ordinary path has speculative cycles')
        need(r['target_final_kv']['max']==p+len(ids)-2,'ordinary pending-token bound');return
    outputs=[ids[0]];base=p;done=r['eog'][0]
    for i,c in enumerate(r['cycles']):
        need(not done and c['cycle']==i and c['base']==base and c['seed']==outputs[-1],'cycle order/seed')
        need(len(c['proposals'])==r['k'] and len(c['decisions'])==r['k']+1,'proposal/verify widths')
        accepted=0;rejected=False;kind=None
        for j,t in enumerate(c['proposals']):
            if c['decisions'][j]==t:outputs.append(t);accepted+=1;kind='accepted'
            else:outputs.append(c['decisions'][j]);rejected=True;kind='correction'
            done=outputs[-1] in eos or len(outputs)==128
            if done or rejected:break
        if accepted==r['k'] and not done:outputs.append(c['decisions'][-1]);kind='bonus';done=outputs[-1] in eos or len(outputs)==128
        keep=base+1+accepted
        need((accepted,rejected,kind,len(outputs),done,keep)==(c['accepted'],c['rejected'],c['commit_kind'],c['output_length'],c['done'],c['keep']),'accept/reject/bonus reconstruction')
        need(c['pending_after']==(None if done else outputs[-1]),'pending ownership')
        need(c['target_after']['max']==keep-1 and c['draft_after']['max']==keep-1,'reconciliation bounds');base=keep
    need(outputs==ids and done,'complete transaction mismatch')
    need(r['target_final_kv']['max']==base-1 and r['draft_final_kv']['max']==base-1,'final KV bounds')

def check_record(r,s,item,folder,identity,parent_audit=None,original=False):
    need(r['slot']==s and r['input_id']==item['id'] and r['prompt_ids']==item['prompt_ids'],'slot/input identity')
    need(r['prompt_ids_sha256']==item['prompt_ids_sha256'],'prompt digest')
    need(r['identity']==identity and r['family']=='Llama','native execution identity')
    need(r['k']==s['k'] and r['draft_enabled']==s['draft_enabled'],'actual draft policy')
    transaction(r)
    diagnostic=s['category']=='diagnostic';mode=s.get('llama_diag',{}).get('mode','off')
    if not original:
        need(r.get('teacher_forced') is False,'teacher-forced output cannot qualify')
        need(r['repair_prefill']==s['repair']['prefill'],'producer policy drift')
        need(r['llama_diagnostic']['mode']==mode,'diagnostic mode drift')
        need(r['qualification_eligible']==(mode=='off'),'diagnostic eligibility incorrect')
        if mode!='off':need(diagnostic and s['observer']=='heavy' and r['llama_diagnostic']['seen'],'invalid probe evidence')
        if s['repair']['trace']['mode']!='off':need(diagnostic,'traced output used as qualification')
        if s['repair']['prefill']!='native':
            b=r['boundary'];need(b['positions_equal'] and not b['pending_token_consumed'] and b['pending_token']==r['ids'][0],'producer transfer semantics')
            if s['observer']=='heavy':need(b['receiver_readback_checked'] and b['serialized_bytes_equal'],'state import control')
    if s['observer']=='heavy':
        verify_vectors(r,folder)
        if not original:
            need(parent_audit is not None,'missing state/geometry auditor')
            parent_audit.verify_states(r,folder)
            parent_audit.geometry_check(r['geometry'] or (r.get('boundary') or {}).get('producer_geometry',[]),32)
    if s['category'] in ('warmup','measured'):
        need(mode=='off' and s['repair']['trace']['mode']=='off' and not r['capture'],'instrumented timing')
        need(type(r['service_seconds']) in (float,int) and math.isfinite(r['service_seconds']) and r['service_seconds']>0,'bad time')
    return endpoint(r)

def matrix(records,slots,refs):
    need(len(records)==len(slots),'incomplete matrix');by={}
    for r in records:
        s=r['slot'];k=s['slot_id'];need(k not in by,'duplicate slot');by[k]=r
    need(set(by)=={s['slot_id'] for s in slots},'foreign/missing slot')
    groups={}
    for s in slots:
        k=(s['input_id'],s['arm'],s['repair']['prefill'])
        groups.setdefault(k,{})[s['observer']]=by[s['slot_id']]
    cells=[]
    for (i,a,p),v in groups.items():
        need(set(v)=={'heavy','off'},'incomplete observer pair')
        stable=endpoint(v['heavy'])==endpoint(v['off']) and all(v['heavy'][k]==v['off'][k] for k in ('cycles','target_final_kv','draft_final_kv'))
        same=endpoint(v['heavy'])==refs[i] and endpoint(v['off'])==refs[i]
        cells.append({'input_id':i,'arm':a,'producer':p,'observer_equal':stable,'reference_equal':same})
    return {'status':'MATRIX_RECONSTRUCTED','cells':cells,'all_observer_equal':all(x['observer_equal'] for x in cells),
      'all_reference_equal':all(x['reference_equal'] for x in cells)}

def performance(records,refs,n,sessions=6):
    want={(s,i,a,k) for s in range(sessions) for i in range(n) for a in LABELS for k in ('warmup','measured')};times={}
    for r in records:
        s=r['slot'];key=(s['session'],s['source_index'],s['experiment_arm'],s['category'])
        need(key not in times,'duplicate timing slot');need(endpoint(r)==refs[r['input_id']],'timing reference failure')
        need(not r['capture'] and not r['teacher_forced'] and r['observer_mode']=='off' and r['llama_diagnostic']['mode']=='off','diagnostic contamination')
        v=r['service_seconds'];need(type(v) in (float,int) and math.isfinite(v) and v>0,'bad time');times[key]=v
    need(set(times)==want,'incomplete/foreign timing Cartesian panel')
    blocks=[]
    for s in range(sessions):
        for i in range(n):
            f=lambda a:times[s,i,a,'measured'];pq=(f('C_PQ_A')+f('C_PQ_B'))/2
            blocks.append({'session':s,'input':i,'layout':f('C_QB')/pq,'AA':f('C_PQ_A')/f('C_PQ_B'),
              'D_QB':f('M_QB')/f('C_QB'),'D_PQ':f('M_PQ')/pq,'CQB_R':f('C_QB')/f('R'),
              'MQB_R':f('M_QB')/f('R'),'MPQ_R':f('M_PQ')/f('R'),'CPQ_R':pq/f('R'),
              'service_seconds':{a:f(a) for a in LABELS}})
    means={k:gm(b[k] for b in blocks) for k in ('layout','AA','D_QB','D_PQ','CQB_R','MQB_R','MPQ_R','CPQ_R')}
    aa=[gm(b['AA'] for b in blocks if b['input']==i) for i in range(n)]
    noise=max(max(x,1/x)-1 for x in aa) # prospectively symmetric A/A rule
    sess=[gm(b['layout'] for b in blocks if b['session']==s) for s in range(sessions)]
    return {'status':'COMPLETE_PAIRED_PANEL','means':means,'AA_max_symmetric_input':noise,'sessions':sess,
      'practical_layout_gain':1-means['layout']>max(.02,noise) and all(x<1 for x in sess),
      'blocks':blocks,'confidence_interval':None,'scope':'six loaded sessions; inputs are sampling units, not individual calls; no population claim'}
