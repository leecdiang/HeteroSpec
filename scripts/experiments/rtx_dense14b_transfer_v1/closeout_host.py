"""Read-only independent pilot reconstruction; never authorizes more requests."""
import array, collections, hashlib, json, math, re, sys
from pathlib import Path
from common import read, save, file_hash, END_KEYS, UNIQUE_ARMS
from design import slots, load_cycle_validator

def check(ok,why):
    if not ok:raise ValueError(why)

def reconstruct(bundle,repo):
    bundle=Path(bundle);root=bundle/'units/pilot/native';panel=read(bundle/'PILOT.json')
    binding=read(bundle/'BINDING.json');planned=slots(panel,'pilot')
    cycle=load_cycle_validator(repo);records={};vectors={};geometry={};matrix=[];pairs=[];nvec=0
    source_hashes={}
    for s in planned:
        p=root/(s['slot_id']+'.json');r=read(p);item=panel['inputs'][s['source_index']]
        check(r['slot']==s and r['identity']==binding['families']['Qwen'],'slot/identity')
        check(r['prompt_ids']==item['prompt_ids'] and r['prompt_ids_sha256']==item['prompt_ids_sha256'],'input')
        e={k:r[k] for k in END_KEYS};check(e==r['endpoint'],'endpoint envelope')
        check(e['length']==len(e['ids'])==len(e['eog']) and e['terminal_id']==e['ids'][-1],'endpoint length')
        check(e['eog']==[v in r['vocabulary_eog'] for v in e['ids']],'EOG flags')
        check(not any(e['eog'][:-1]),'early EOG')
        check((e['stop_reason']=='EOG' and e['eog'][-1]) or (e['stop_reason']=='CAP' and not e['eog'][-1] and e['length']==128),'stop rule')
        cycle(r,dict(item,prompt_tokens=len(item['prompt_ids'])),{'vocabulary_tokens':151936,'eog':r['vocabulary_eog']})
        key=(s['source_index'],s['arm'],s['observer']);records[key]=r;source_hashes[s['slot_id']]=file_hash(p)
        if s['observer']!='heavy':continue
        expected={'target/initial.f32':r['ids'][0]}
        if r['draft_enabled']:
            for c in r['cycles']:
                for j,t in enumerate(c['proposals']):expected[f'draft/proposal-{c["cycle"]}-{j}.f32']=t
                for j,t in enumerate(c['decisions']):expected[f'target/verify-{c["cycle"]}-{j}.f32']=t
        else:
            for j,t in enumerate(r['ids'][1:],1):expected[f'target/ordinary-{j}.f32']=t
        folder=root/s['slot_id'];actual={p.relative_to(folder).as_posix() for role in ('target','draft') for p in (folder/role).glob('*.f32')}
        check(actual==set(expected),'full vector inventory')
        pins={}
        for name,token in expected.items():
            b=(folder/name).read_bytes();check(len(b)==151936*4,'vocabulary width')
            v=array.array('f');v.frombytes(b)
            if sys.byteorder!='little':v.byteswap()
            check(all(math.isfinite(x) for x in v),'nonfinite logits')
            check(v.index(max(v))==token,'independent full-vector greedy mismatch')
            pins[name]=hashlib.sha256(b).hexdigest();nvec+=1
        vectors[key]=pins
        for role in ('target','draft'):
            if role=='draft' and not r['draft_enabled']:continue
            p=folder/(role+'_final.state');pin=r[role+'_state']
            check(p.stat().st_size==pin['bytes'] and file_hash(p)==pin['sha256'],'complete state pin')
        mapped=collections.defaultdict(dict)
        for g in r['geometry']:
            m=re.fullmatch(r'kq-(\d+)',g['name'])
            if not m or g['op']!='MUL_MAT':continue
            layer=int(m[1]);check(0<=layer<40,'layer index');phase=g['phase']
            check(phase in ('PREFILL','ORDINARY','VERIFY'),'phase')
            check('5070' in g['device'] and g['device_type']==1,'observed pilot QK compute map differs')
            k,q=[x['ne'] for x in g['sources'][:2]]
            check(k[0]==q[0]==128 and k[2]==8 and q[2]==40,'GQA geometry')
            if s['scope']=='PQ':check(q[1]==q[3]==1,'PQ query extent')
            if s['scope']=='QB':check(q[1]==1 and 1<=q[3]<=4 and (phase!='VERIFY' or q[3]==4),'QB query extent')
            mapped[phase][layer]='GPU'
        check(set(mapped['PREFILL'])==set(range(40)),'all40 prefill witnesses')
        if r['cycles']:check(set(mapped['VERIFY'])==set(range(40)),'all40 q4 verification witnesses')
        geometry[s['slot_id']]={phase:dict(layers) for phase,layers in mapped.items()}
        print('Audited',s['slot_id'],len(expected),'full vectors',flush=True)
    for i,item in enumerate(panel['inputs']):
        ref=records[i,'R','heavy']['endpoint'];check(records[i,'R','off']['endpoint']==ref,'R not repeatable')
        for arm in UNIQUE_ARMS:
            h,o=records[i,arm,'heavy'],records[i,arm,'off']
            observer_equal=all(h[k]==o[k] for k in ('endpoint','cycles','target_final_kv','draft_final_kv'))
            check(observer_equal,'observer interference')
            a,b=ref['ids'],h['ids'];diff=next((j for j,(u,v) in enumerate(zip(a,b)) if u!=v),None)
            if diff is None and len(a)!=len(b):diff=min(len(a),len(b))
            matrix.append({'input':item['id'],'arm':arm,'observer_equal':observer_equal,'reference_equal':h['endpoint']==ref,'length':h['length'],'first_different_output_index':diff,'reference_token':a[diff] if diff is not None and diff<len(a) else None,'candidate_token':b[diff] if diff is not None and diff<len(b) else None})
        for path in ('M','C'):
            a,b=records[i,path+'_PQ','heavy'],records[i,path+'_QB','heavy']
            pairs.append({'input':item['id'],'path':path,'endpoint_equal':a['endpoint']==b['endpoint'],
              'logical_work_equal':all(a[k]==b[k] for k in ('cycles','target_calls','draft_calls','target_final_kv','draft_final_kv')),
              'full_logits_equal':vectors[i,path+'_PQ','heavy']==vectors[i,path+'_QB','heavy'],
              'target_state_equal':a['target_state']==b['target_state'],'draft_state_equal':path=='M' or a['draft_state']==b['draft_state']})
    text=(root.parent/'stderr.log').read_text(errors='replace')
    assignments=re.findall(r'load_tensors: layer\s+(\d+) assigned to device (\S+),',text)
    ngl=binding['dense14b']['target_gpu_layers'];expected=[(str(i),'CPU' if i<41-ngl else 'CUDA0') for i in range(41)]
    check(assignments[:41]==expected,'actual target weight placement')
    receipt=read(root.parent/'RECEIPT.json');check(receipt['success'] and receipt['active_processes_after_wait']==0 and receipt['native_completed_events']==40,'process completeness/cleanup')
    ledger=[json.loads(x) for x in (bundle/'LEDGER.jsonl').read_text().splitlines()]
    charged=sum(x.get('reserved_requests',0) for x in ledger if x['event']=='START')
    result={'status':'REFERENCE_COUNTEREXAMPLE' if any(not x['reference_equal'] for x in matrix) else 'ENDPOINTS_PRESERVED_NOT_AUTHORIZATION',
      'original_gate_status':read(bundle/'PILOT_AUDIT.json')['status'],'records':len(records),'full_vectors_checked':nvec,
      'all_vectors_finite_and_greedy_reconstructed':True,'all_state_artifacts_verified':True,'all_transactions_reconstructed':True,
      'all_observer_pairs_equal':True,'all_R_pairs_repeatable':True,'endpoint_matrix':matrix,'paired_internal_diagnostics':pairs,
      'QK_geometry':geometry,'target_weight_assignments':expected,'source_record_hashes':source_hashes,
      'actual_requests':40,'cumulative_charged_requests':charged,'remaining_hard_ceiling':800-charged,'engineering_reserve_used':0,
      'qualification_requests':0,'formal_measured_requests':0,'formal_warmup_requests':0,
      'native_seconds':sum(x.get('seconds',0) for x in ledger if x['event']=='END'),
      'placement_note':'Authenticated scheduler expands supported non-weight ops to GPU; actual QK is all40-layer CUDA despite17 CPU-weight layers. Original weight-to-QK inference was invalid. No CPU-QK coverage claim.',
      'authority':'Read-only closeout only. Original failed gate remains. No further model execution authorized by this report.'}
    save(bundle/'INDEPENDENT_RECOMPUTE.json',result)
    pending=[dict(s,status='NOT_RUN_DEPENDENCY',reason='pilot reference counterexample') for s in slots(read(bundle/'PANEL.json'),'qualification')]
    for session in range(4):pending += [dict(s,status='NOT_RUN_DEPENDENCY',reason='pilot reference counterexample') for s in slots(read(bundle/'PANEL.json'),'formal',session)]
    save(bundle/'UNSTARTED_SLOTS.json',pending)
    return result

if __name__=='__main__':
    r=reconstruct(Path(sys.argv[1]),Path(sys.argv[2]));print(r['status'],r['records'],r['full_vectors_checked'])
