"""Endpoint/boundary qualification and paired cost reconstruction; raw hashes are retained."""
from __future__ import annotations
import array
import math
import re
from pathlib import Path
import sys
from common import *
from plan import ARMS,TIMING_ARMS

def full_vector(path,n=151936):
    p=Path(path);need(p.stat().st_size==4*n,'full-vector length differs')
    a=array.array('f');a.frombytes(p.read_bytes())
    if sys.byteorder!='little':a.byteswap()
    need(all(math.isfinite(v) for v in a),'nonfinite full logit')
    return max(range(n),key=lambda i:a[i]),file_hash(p)

def verify_greedy(r,folder):
    """Audit every saved decision vector, including discarded rows. Returns hashes."""
    folder=Path(folder);hashes={};best={}
    for role in ('target','draft'):
        for p in sorted((folder/role).glob('*.f32')):
            token,h=full_vector(p);rel=p.relative_to(folder).as_posix();best[rel]=token;hashes[rel]=h
    need('target/initial.f32' in best,'missing initial decision vector')
    need(best['target/initial.f32']==r['ids'][0],'initial argmax differs')
    if not r['draft_enabled']:
        for i,tok in enumerate(r['ids'][1:],1):need(best[f'target/ordinary-{i}.f32']==tok,'ordinary argmax differs')
    else:
        for c in r['cycles']:
            for i,t in enumerate(c['proposals']):need(best[f'draft/proposal-{c["cycle"]}-{i}.f32']==t,'proposal differs')
            for i,t in enumerate(c['decisions']):need(best[f'target/verify-{c["cycle"]}-{i}.f32']==t,'verification differs')
    return hashes

def verify_states(r,folder):
    folder=Path(folder)
    for role in ('target','draft'):
        if role=='draft' and not r['draft_enabled']:continue
        meta=r[role+'_state'];p=folder/(role+'_final.state')
        need(p.stat().st_size==meta['bytes'] and file_hash(p)==meta['sha256'],'state artifact changed: '+role)
    b=r.get('boundary') or {}
    for name,key in [('boundary_source.state','boundary_state_sha256'),('boundary_logits.f32','boundary_logits_sha256')]:
        if key in b:need(file_hash(folder/name)==b[key],'boundary artifact changed')


def transaction_check(r):
    """Reconstruct commits/trim positions from actual cycle records."""
    end=endpoint(r);need({k:r[k] for k in END_KEYS}==end,'top-level/nested endpoint disagreement')
    ids=[r['ids'][0]];base=r['prompt_tokens']
    need(r['eog']==[i in set(r['vocabulary_eog']) for i in r['ids']],'native vocabulary EOG differs')
    if not r['draft_enabled']:
        need(not r['cycles'],'ordinary path has speculative cycles')
        need(r['target_final_kv']['max']==r['prompt_tokens']+len(r['ids'])-2,'ordinary pending-token KV bound')
        return
    eog=set(r['vocabulary_eog']);done=ids[-1] in eog
    for number,c in enumerate(r['cycles']):
        need(not done and c['cycle']==number and c['base']==base,'transaction order')
        need(c['seed']==ids[-1] and len(c['proposals'])==r['k'] and len(c['decisions'])==r['k']+1,'transaction rows')
        accepted=0;kind=None;rejected=False
        for j,t in enumerate(c['proposals']):
            if c['decisions'][j]==t:ids.append(t);accepted+=1;kind='accepted'
            else:ids.append(c['decisions'][j]);kind='correction';rejected=True
            done=ids[-1] in eog or len(ids)==128
            if rejected or done:break
        if accepted==r['k'] and not done:
            ids.append(c['decisions'][-1]);kind='bonus';done=ids[-1] in eog or len(ids)==128
        keep=base+1+accepted
        need(c['accepted']==accepted and c['rejected']==rejected and c['commit_kind']==kind,'accept/reject mismatch')
        need(c['keep']==keep and c['output_length']==len(ids) and c['done']==done,'commit/trim mismatch')
        need(c['pending_after']==(None if done else ids[-1]),'pending token mismatch')
        for role in ('target_after','draft_after'):need(c[role]['max']==keep-1,'trim bounds')
        base=keep
    need(ids==r['ids'] and done,'full speculative reconstruction differs')
    expected_max=(r['cycles'][-1]['keep']-1) if r['cycles'] else r['prompt_tokens']-1
    need(r['target_final_kv']['max']==expected_max and r['draft_final_kv']['max']==expected_max,'final committed KV bound differs')

def geometry_check(nodes,expected_layers=40):
    """Require actual scheduler-assigned QK nodes on every target layer.
    View/buffer ownership and merely configured offload counts are not substitutes.
    Name-map adaptations require a source-reviewed successor, never an ignored failure.
    """
    need(bool(nodes),'no target geometry was observed')
    qk=[]
    for node in nodes:
        need(node.get('scheduler_backend') is not None,'missing actual scheduler assignment')
        need('buffer_owner_device' in node,'buffer/scheduler distinction missing')
        name=node.get('name','').lower()
        if node.get('op')=='MUL_MAT' and re.match(r'^(?:kq(?!v)|hs_.*(?:qk|kq)).*-\d+$',name):
            need(type(node.get('layer')) is int,'QK layer identity missing')
            qk.append(node)
    need({n['layer'] for n in qk}==set(range(expected_layers)),'incomplete scheduler QK coverage; inspect exact graph name mapping')
    return {'layers':expected_layers,'backend_names':sorted({n['scheduler_backend'] for n in qk}),
            'scope':'scheduler node assignment; no kernel occupancy or per-kernel device execution proof'}

def record_check(r,s,item,vector_root=None):
    need(r['slot']==s and r['input_id']==item['id'],'record/slot/input mismatch')
    need(r['prompt_ids_sha256']==item['prompt_ids_sha256'] and r['prompt_ids']==item['prompt_ids'],'prompt bytes differ')
    need(r['repair_prefill']==s['repair']['prefill'],'producer policy differs')
    probe=s['repair'].get('probe',False)
    need(r['teacher_forced']==probe and r['qualification_eligible']==(not probe),'diagnostic leak')
    need(r['observer_mode']==s['repair']['trace']['mode'],'observer mode differs')
    if probe:
        need(not r['draft_enabled'],'probe must not run speculation')
        prefix=s['repair']['teacher_tokens'];need(r['probe_prefix']==prefix and r['ids'][:len(prefix)]==prefix,'teacher prefix differs')
        endpoint(r,len(prefix)+1)
    else:transaction_check(r)
    if s['repair']['prefill']!='native':
        b=r['boundary'];need(b['positions_equal'] and not b['pending_token_consumed'],'boundary handoff semantics')
        need(b['pending_token']==r['ids'][0] or probe,'imported initial-logit token differs')
        if s['observer']=='heavy':need(b['receiver_readback_checked'] and b['serialized_bytes_equal'],'unverified imported state')
    if s['observer']=='heavy':
        # A natural first-token EOG may execute only the canonical producer.
        # Its placement is recorded separately; never claim an unexecuted consumer geometry.
        geometry_check(r['geometry'] or (r.get('boundary') or {}).get('producer_geometry',[]))
        if vector_root is not None:
            verify_states(r,vector_root)
            if not probe:verify_greedy(r,vector_root)
    if s['category'] in ('measured','warmup'):
        need(not probe and r['observer_mode']=='off' and not r['capture'],'instrumented timing rejected')
        positive(r['service_seconds'])
    return endpoint(r,len(s['repair'].get('teacher_tokens',[]))+1 if probe else 128)

def matrix(records, panel, required, strict_refs):
    by={};errors=[];pairs=[]
    for r in records:
        s=r['slot'];key=(s['source_index'],s['arm'],s['repair']['prefill'],s['observer'])
        need(key not in by,'duplicate matrix coordinate');by[key]=r
    need(len(records)==len(required),'incomplete matrix')
    for s in required:
        key=(s['source_index'],s['arm'],s['repair']['prefill'],s['observer']);need(key in by,'missing registered slot')
    for i,x in enumerate(panel['inputs']):
        refs=strict_refs[x['id']]
        for arm,producer in sorted({(s['arm'],s['repair']['prefill']) for s in required if s['source_index']==i}):
            a=by[i,arm,producer,'off'];b=by[i,arm,producer,'heavy']
            stable=endpoint(a)==endpoint(b) and all(a[k]==b[k] for k in ('cycles','target_final_kv','draft_final_kv'))
            same=endpoint(a)==refs and endpoint(b)==refs
            pairs.append({'input':x['id'],'arm':arm,'producer':producer,'observer_equal':stable,'reference_equal':same})
            if not stable:errors.append({'input':x['id'],'arm':arm,'producer':producer,'type':'OBSERVER_CONTAMINATION'})
    return {'status':'MATRIX_RECONSTRUCTED','cells':pairs,'observer_errors':errors,
      'all_reference_equal':all(x['reference_equal'] for x in pairs),
      'scope':'Serialized state round trips and saved decision vectors are audited separately; matrix alone is not a universal guarantee.'}

def performance(records,qualified_refs):
    need(len(records)==576,'complete 576-row timing/warmup matrix required')
    t={}
    for r in records:
        s=r['slot'];key=(s['session'],s['source_index'],s['experiment_arm'],s['category'])
        need(key not in t,'duplicate timing coordinate')
        need(s['category'] in ('measured','warmup') and not r['teacher_forced'] and not r['capture'] and r['observer_mode']=='off','diagnostic timing contamination')
        need(endpoint(r)==qualified_refs[r['input_id']],'timed request violates frozen reference')
        t[key]=positive(r['service_seconds'])
    want={(s,i,a,k) for s in range(4) for i in range(12) for a in TIMING_ARMS for k in ('warmup','measured')}
    need(set(t)==want,'incomplete/foreign timing cells')
    blocks=[]
    for s in range(4):
        for i in range(12):
            f=lambda a:t[s,i,a,'measured'];pq=(f('C_PQ_A')+f('C_PQ_B'))/2
            blocks.append({'session':s,'input':i,'layout':f('C_QB')/pq,'AA':f('C_PQ_A')/f('C_PQ_B'),
                'D_QB':f('M_QB')/f('C_QB'),'D_PQ':f('M_PQ')/pq,'CQB_R':f('C_QB')/f('R'),
                'MQB_R':f('M_QB')/f('R')})
    g=lambda k:gm(b[k] for b in blocks)
    noise=max(abs(gm(b['AA'] for b in blocks if b['input']==i)-1) for i in range(12))
    sessions=[gm(b['layout'] for b in blocks if b['session']==s) for s in range(4)]
    return {'status':'COMPLETE_PAIRED_PANEL','means':{k:g(k) for k in ('layout','D_QB','D_PQ','CQB_R','MQB_R','AA')},
      'AA_max_input':noise,'sessions':sessions,'practical_layout_gain':1-g('layout')>max(.02,noise) and all(v<1 for v in sessions),
      'blocks':blocks,'confidence_interval':None,'scope':'Paid repair + complete service; no diagnostic or warmup timing promoted.'}
