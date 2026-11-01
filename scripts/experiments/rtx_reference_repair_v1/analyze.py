"""Read-only reference/observer audit and full-cost analysis; no model execution."""
from __future__ import annotations
import argparse, array, collections, json, math, sys
from pathlib import Path
from common import *
from plans import TIMING


def vector(path,n=151936):
    p=Path(path);need(p.stat().st_size==4*n,'incomplete full vocabulary vector')
    a=array.array('f');a.frombytes(p.read_bytes())
    if sys.byteorder!='little':a.byteswap()
    need(all(math.isfinite(v) for v in a),'nonfinite logit')
    return max(range(n),key=a.__getitem__),sha(p)


def vector_audit(root,r):
    need(not r.get('diagnostic_teacher_forced',False),'teacher trace is not natural qualification')
    root=safe(root,r['folder']);expected={'target/initial.f32':r['ids'][0]}
    if r['draft_enabled']:
        for i,c in enumerate(r['cycles']):
            expected.update({f'draft/proposal-{i}-{j}.f32':v for j,v in enumerate(c['proposals'])})
            expected.update({f'target/verify-{i}-{j}.f32':v for j,v in enumerate(c['decisions'])})
    else:expected.update({f'target/ordinary-{j}.f32':r['ids'][j] for j in range(1,r['length'])})
    present={str(p.relative_to(root)).replace('\\','/') for role in ('target','draft') for p in (root/role).glob('*.f32')}
    need(present==set(expected),'missing or unexpected decision vectors')
    hashes={}
    for name,token in expected.items():
        best,h=vector(root/name);need(best==token,'greedy mismatch: '+name);hashes[name]=h
    for role in ('target','draft'):
        if role=='draft' and not r['draft_enabled']:continue
        p=root/(role+'_final.state');pin=r[role+'_state']
        need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'final state artifact differs')
    return hashes


def transactions(r):
    """Independent committed-prefix reconstruction, including pending/KV bounds."""
    e=endpoint(r);ids=e['ids'];n=len(r['prompt_ids']);done=ids[0] in r['vocabulary_eog'] or len(ids)==1
    need(e['eog']==[v in r['vocabulary_eog'] for v in ids],'EOG token classification')
    if not r['draft_enabled']:
        need(not r['cycles'],'target-only has speculative cycles');return
    out=[ids[0]];base=n
    for i,c in enumerate(r['cycles']):
        need(not done,'cycle after terminal')
        need(c['cycle']==i and c['base']==base and c['seed']==out[-1],'cycle prefix/seed')
        p,d=c['proposals'],c['decisions'];need(len(p)==3 and len(d)==4,'fixed k3 row count')
        accepted=0;rejected=False;kind=None
        for j in range(3):
            token=p[j] if p[j]==d[j] else d[j]
            if p[j]==d[j]:accepted+=1;kind='accepted'
            else:rejected=True;kind='correction'
            out.append(token);done=token in r['vocabulary_eog'] or len(out)==128
            if done or rejected:break
        if accepted==3 and not done:
            out.append(d[3]);kind='bonus';done=out[-1] in r['vocabulary_eog'] or len(out)==128
        keep=base+1+accepted
        need((c['accepted'],c['rejected'],c['commit_kind'],c['keep'],c['done'])==(accepted,rejected,kind,keep,done),'transaction fields')
        need(c['output_length']==len(out) and c['pending_after']==(None if done else out[-1]),'pending ownership')
        for role in ('target_after','draft_after'):need(c[role]['max']==keep-1,'KV trim upper bound')
        base=keep
    need(out==ids and done,'committed token reconstruction')


def placement(r,n_layers=40):
    """Observe the actual assignment; never require it to equal weight placement."""
    if r.get('target_calls')==0 and r.get('length')==1 and r.get('producer')=='RSEED':
        seed=r.get('seed_geometry',[])
        layers={g.get('layer') for g in seed if g.get('op')=='MUL_MAT' and g.get('name','').startswith('kq')
                and g.get('placement_basis')=='ggml_backend_sched_get_tensor_backend'
                and g.get('compute_backend') not in (None,'','UNRESOLVED')}
        need(layers==set(range(n_layers)),'missing reference-seed geometry for initial EOG')
        return {'consumer':'NOT_RUN_INITIAL_EOG','seed_layers':sorted(layers)}
    found={};q4=False
    for g in r.get('geometry',[]):
        if g.get('op')!='MUL_MAT' or not g.get('name','').startswith('kq'):continue
        need(g.get('placement_basis')=='ggml_backend_sched_get_tensor_backend','not scheduler evidence')
        need(g.get('compute_backend') not in (None,'UNRESOLVED',''),'unknown actual backend')
        layer=g.get('layer')
        if layer is not None:found.setdefault(g['phase'],set()).add(layer)
        # Actual Q descriptor is recorded from the node operands; no layer->device guess.
        for src in g.get('sources',[]):
            q=src.get('ne',[])
            if r['observed_scope']=='QB' and len(q)==4 and q[0]==128 and q[1]==1 and q[3]==4 and g['phase']=='VERIFY':q4=True
    need(found,'no QK scheduler evidence')
    phase='VERIFY' if r['draft_enabled'] and r['cycles'] else 'ORDINARY' if r['length']>1 else 'PREFILL'
    need(found.get(phase,set())==set(range(n_layers)),'incomplete actual QK layer coverage')
    if r['observed_scope']=='QB' and r['draft_enabled'] and r['cycles']:need(q4,'no actual q4 verification witness')
    return {k:sorted(v) for k,v in found.items()}


def audit(records,planned,panel,historical=None,require_placement=True,vector_roots=None):
    """records are native JSONs indexed by outer slot_id; every planned cell retained."""
    need(len({s['slot_id'] for s in planned})==len(planned),'duplicate plan slot')
    need(set(records)=={s['slot_id'] for s in planned},'missing/foreign records')
    data={};errors=[];hashes={};references={};checks=[]
    for s in planned:
        r=records[s['slot_id']];x=panel['inputs'][s['source_index']]
        try:
            need(r['prompt_ids']==x['prompt_ids'] and r['prompt_ids_sha256']==x['prompt_ids_sha256'],'prompt binding')
            need(r.get('capture')==(s['observer']=='heavy'),'capture binding')
            need(r['arm']==s['arm'] and r['k']==s['k'] and r['producer']==s['producer'],'arm/producer binding')
            need(r.get('observed_scope')==s['scope'],'layout scope')
            need(not r.get('diagnostic_teacher_forced',False),'diagnostic forcing cannot qualify')
            if s['cohort']=='repair':need(r.get('row_repair_policy')==s['rows'],'row policy drift')
            endpoint(r);transactions(r)
            if s['observer']=='heavy':
                need(vector_roots is not None,'full raw-vector root required')
                hashes[s['slot_id']]=vector_audit(vector_roots[s['slot_id']],r)
                if require_placement and s['cohort']=='repair':placement(r,r.get('context',{}).get('expected_layers',40))
            data[s['source_index'],s['experiment_arm'],s['category']]=r
        except (ValueError,KeyError,OSError,TypeError) as e:errors.append({'slot':s['slot_id'],'error':str(e)})
    for i,x in enumerate(panel['inputs']):
        arms={s['experiment_arm'] for s in planned if s['source_index']==i}
        try:
            reference=historical[x['id']] if historical else endpoint(data[i,'R','off'])
            if historical is None:need(endpoint(data[i,'R','heavy'])==reference,'original R observer/repeat mismatch')
            references[x['id']]=reference
            if 'R' in arms and 'R_NEW' in arms:
                old,new=data[i,'R','heavy'],data[i,'R_NEW','heavy']
                names={s['experiment_arm']:s['slot_id'] for s in planned if s['source_index']==i and s['category']=='heavy'}
                need(names['R'] in hashes and names['R_NEW'] in hashes and hashes[names['R']]==hashes[names['R_NEW']],'new-core R vectors differ from frozen original')
                need(old['target_state']==new['target_state'],'new-core R serialized state differs')
            for a in arms:
                h,o=data[i,a,'heavy'],data[i,a,'off']
                match=endpoint(h)==endpoint(o)==reference
                obs_equal=all(h[k]==o[k] for k in ('cycles','target_final_kv','draft_final_kv'))
                checks.append({'input':x['id'],'arm':a,'reference_equal':match,'observer_equal':obs_equal})
                if not match:errors.append({'input':x['id'],'arm':a,'error':'REFERENCE_COUNTEREXAMPLE'})
                if not obs_equal:errors.append({'input':x['id'],'arm':a,'error':'OBSERVER_STATE_DIFFERENCE'})
        except (ValueError,KeyError,TypeError) as e:errors.append({'input':x['id'],'error':str(e)})
    # A panel of initial-EOG requests cannot establish transfer of multiquery verification.
    if any(s['experiment_arm']=='C_QB' for s in planned):
        witnesses=[r for (i,arm,cat),r in data.items() if arm=='C_QB' and cat=='heavy' and r.get('cycles')]
        if not witnesses:errors.append({'error':'NO_MULTITOKEN_VERIFICATION_OBSERVED'})
    internal=[]
    for i,x in enumerate(panel['inputs']):
        for p in ('M','C'):
            a,b=data.get((i,p+'_PQ','heavy')),data.get((i,p+'_QB','heavy'))
            if a and b:
                by={s['experiment_arm']:s['slot_id'] for s in planned if s['source_index']==i and s['category']=='heavy'}
                internal.append({'input':x['id'],'path':p,'endpoint_equal':endpoint(a)==endpoint(b),
                    'cycles_equal':a['cycles']==b['cycles'],
                    'vectors_equal':hashes.get(by[p+'_PQ'])==hashes.get(by[p+'_QB']) if by[p+'_PQ'] in hashes and by[p+'_QB'] in hashes else None,
                    'target_state_equal':a.get('target_state')==b.get('target_state')})
    return {'status':'PASS' if not errors else 'UNQUALIFIED','errors':errors,'cells':checks,'references':references,
            'paired_internal':internal,'interpretation':'internal equality separate from R qualification; observer controls required',
            'native_runs_added':0}


def analyze(records):
    need(len(records)==576,'complete 4x12x6 warmup/measured panel required');t={}
    for r in records:
        s=r['outer_slot'];key=s['session'],s['source_index'],s['experiment_arm'],s['category']
        need(key not in t,'duplicate cost slot');need(r.get('endpoint_qualified') is True,'unqualified cost record')
        need(not r.get('capture') and not r.get('diagnostic_teacher_forced',False),'instrumented cost')
        t[key]=pos(r['service_seconds'],'request cost')
    expected={(s,i,a,c) for s in range(4) for i in range(12) for a in TIMING for c in ('warmup','measured')}
    need(set(t)==expected,'missing/foreign cost cells');blocks=[]
    for s in range(4):
        for i in range(12):
            v=lambda a:t[s,i,a,'measured'];pq=(v('C_PQ_A')+v('C_PQ_B'))/2
            blocks.append(dict(session=s,input_index=i,layout=v('C_QB')/pq,aa=v('C_PQ_A')/v('C_PQ_B'),
                candidate_R=v('C_QB')/v('R'),target_R=v('M_QB')/v('R'),D_QB=v('M_QB')/v('C_QB'),
                D_PQ=v('M_PQ')/pq,local_target=v('M_QB')/v('M_PQ')))
    means={k:gm(b[k] for b in blocks) for k in blocks[0] if k not in ('session','input_index')}
    noise=max(abs(gm(b['aa'] for b in blocks if b['input_index']==i)-1) for i in range(12))
    sessions=[gm(b['layout'] for b in blocks if b['session']==s) for s in range(4)]
    return dict(status='COMPLETE_FINITE_COST_PANEL',means=means,aa_max_input=noise,session_layout=sessions,
        practical_layout_gain=(1-means['layout'])>max(.02,noise) and all(x<1 for x in sessions),
        blocks=blocks,confidence_interval=None,scope='all request work including reference prefill/import/readback; no universal guarantee or isolated kernel attribution')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('records',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();save(a.out,analyze(read(a.records)['records']),True)
