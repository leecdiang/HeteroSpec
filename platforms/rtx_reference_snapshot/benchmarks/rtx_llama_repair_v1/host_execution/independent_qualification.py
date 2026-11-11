"""Independent complete-vector qualification reconstruction; no production auditor."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from independent_cost import endpoint, transaction, read


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--pool',type=Path);p.add_argument('--exposures',type=Path)
    a=p.parse_args();b=a.bundle;panel=read(b/'HELDOUT.json');n=len(panel['inputs']);assert n==24
    selection=read(b.parent/'SELECTION_PROVENANCE.json')
    pool_origin=next(p for p in selection['inputs'] if p.replace('\\','/').endswith('/POOL.json'))
    exposure_origin=next(p for p in selection['inputs'] if p.replace('\\','/').endswith('/EXPOSURES.json'))
    pool_path=a.pool or Path(pool_origin);exposure_path=a.exposures or Path(exposure_origin)
    assert sha(pool_path)==selection['inputs'][pool_origin] and sha(exposure_path)==selection['inputs'][exposure_origin]
    pool=read(pool_path);exposures=read(exposure_path);fields=('id','text_sha256','prompt_ids_sha256')
    canonical=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    assert canonical(pool)==panel['source_pool_sha256'] and canonical(exposures)==panel['exposure_sha256']
    seen={k:{x[k] for x in exposures if x.get(k)} for k in fields};used={k:set() for k in fields};chosen=[]
    assert panel['seed']=='llama-mechanism-transfer-v1'
    for domain in ('code','math'):
        for band,low,high in [('short',128,384),('long',512,768)]:
            eligible=[x for x in pool if x['domain']==domain and low<=len(x['prompt_ids'])<=high and not any(x[k] in seen[k] for k in fields)]
            eligible.sort(key=lambda x:hashlib.sha256((panel['seed']+'|'+x['prompt_ids_sha256']).encode()).digest())
            group=[]
            for x in eligible:
                if any(x[k] in used[k] for k in fields):continue
                group.append(dict(x,stratum=band))
                for k in fields:used[k].add(x[k])
                if len(group)==6:break
            assert len(group)==6;chosen+=group
    assert chosen==panel['inputs']
    assert not a.out.exists();vector_index=a.out.with_suffix('.vectors.jsonl');assert not vector_index.exists()
    old_identity=read(b/'ORIGINAL_BINDING.json')['families']['Llama'];identity=read(b/'BINDING.json')['families']['Llama']
    references={};old_vectors={};groups={};records={};vectors=states=0;committed_comparisons=[];geometry=[]
    with vector_index.open('x',encoding='utf-8') as journal:
        for unit_name,original in [('original_references',True),('qualification',False)]:
            unit=b/'units'/unit_name;slots=read(unit/'SLOTS.json');receipt=read(unit/'RECEIPT.json')
            assert receipt['success'] and receipt['active_processes_after_wait']==0
            assert len(slots)==n*(2 if original else 10)
            for s in slots:
                path=unit/'native'/(s['slot_id']+'.json');r=read(path);folder=path.with_suffix('')
                assert r['slot']==s and r['input_id']==panel['inputs'][s['source_index']]['id']
                assert r['prompt_ids']==panel['inputs'][s['source_index']]['prompt_ids']
                assert r['identity']==(old_identity if original else identity)
                assert all(type(t) is int and 0<=t<128256 for t in r['ids'])
                assert all(r['endpoint'][k]==r[k] for k in ('ids','eog','length','terminal_id','stop_reason'))
                transaction(r);value=endpoint(r);records[str(path)]=sha(path)
                if original:
                    if r['input_id'] in references:assert value==references[r['input_id']]
                    references[r['input_id']]=value
                else:
                    assert value==references[r['input_id']]
                    assert not r['teacher_forced'] and r['llama_diagnostic']['mode']=='off'
                    assert r['context_teardown_completed'] and s['lifecycle']=='fresh'
                    groups.setdefault((r['input_id'],s['arm']),{})[s['observer']]=r
                hashes={}
                if s['observer']=='heavy':
                    expected={'target/initial.f32':r['ids'][0]}
                    if r['draft_enabled']:
                        for c in r['cycles']:
                            expected.update({f'draft/proposal-{c["cycle"]}-{i}.f32':t for i,t in enumerate(c['proposals'])})
                            expected.update({f'target/verify-{c["cycle"]}-{i}.f32':t for i,t in enumerate(c['decisions'])})
                    else:expected.update({f'target/ordinary-{i}.f32':t for i,t in enumerate(r['ids'][1:],1)})
                    actual={f.relative_to(folder).as_posix() for role in ('target','draft') for f in (folder/role).glob('*.f32')}
                    assert actual==set(expected)
                    for name,token in expected.items():
                        f=folder/name;raw=f.read_bytes();assert len(raw)==128256*4
                        values=np.frombuffer(raw,dtype='<f4');assert np.isfinite(values).all() and int(values.argmax())==token
                        digest=hashlib.sha256(raw).hexdigest();hashes[name]=digest;vectors+=1
                        journal.write(json.dumps({'file':str(f),'bytes':len(raw),'argmax':token,'sha256':digest})+'\n')
                    if original:old_vectors[r['input_id']]=hashes
                    else:
                        nodes=r['geometry'] or (r.get('boundary') or {}).get('producer_geometry',[])
                        qk=[node for node in nodes if node['op']=='MUL_MAT' and node['name'].startswith('kq-')]
                        assert {node['layer'] for node in qk}==set(range(32))
                        assert all(node.get('scheduler_backend') is not None and 'buffer_owner_device' in node for node in qk)
                        geometry.append({'slot':s['slot_id'],'layers':32,'scheduler_backends':sorted({node['scheduler_backend'] for node in qk})})
                        if s['arm']=='R':assert hashes==old_vectors[r['input_id']]
                        for role in ('target','draft'):
                            if role=='draft' and not r['draft_enabled']:continue
                            f=folder/(role+'_final.state');meta=r[role+'_state']
                            assert f.stat().st_size==meta['bytes'] and sha(f)==meta['sha256'];states+=1
                        for name,key in [('boundary_source.state','boundary_state_sha256'),('boundary_logits.f32','boundary_logits_sha256')]:
                            if key in (r.get('boundary') or {}):assert sha(folder/name)==r['boundary'][key]
                        committed=['target/initial.f32']
                        if not r['draft_enabled']:committed+=['target/ordinary-%d.f32'%i for i in range(1,len(r['ids']))]
                        else:
                            for c in r['cycles']:
                                rows=list(range(c['accepted']))
                                if c['commit_kind']=='correction':rows.append(c['accepted'])
                                elif c['commit_kind']=='bonus':rows.append(r['k'])
                                committed += [f'target/verify-{c["cycle"]}-{i}.f32' for i in rows]
                        assert len(committed)==len(r['ids'])
                        mismatches=[]
                        for i,name in enumerate(committed):
                            reference='target/initial.f32' if i==0 else 'target/ordinary-%d.f32'%i
                            if hashes[name]!=old_vectors[r['input_id']][reference]:mismatches.append(i)
                        committed_comparisons.append({'slot':s['slot_id'],'rows':len(committed),'different_complete_vectors':mismatches})
                print(unit_name,s['slot_id'],'vectors',vectors,flush=True)
    assert len(groups)==5*n
    for pair in groups.values():
        assert set(pair)=={'off','heavy'}
        assert all(pair['off'][k]==pair['heavy'][k] for k in ('ids','eog','length','terminal_id','stop_reason','cycles','target_final_kv','draft_final_kv'))
    report={'status':'INDEPENDENT_QUALIFICATION_RECONSTRUCTED','original_requests':48,'candidate_requests':240,
      'complete_vectors':vectors,'candidate_final_states':states,'all_endpoints_and_observers_equal_original':True,
      'selection_reconstructed_from_pre_output_pool_and_exposures':True,'geometry':geometry,
      'candidate_R_complete_vectors_equal_original':True,'committed_vector_comparisons':committed_comparisons,
      'committed_vector_scope':'Additional descriptive reconstruction; non-R full-vector equality is not a new qualification gate. Registered endpoint/observer gates and exact R preservation are checked independently.',
      'record_sha256':records,'vector_index_path':str(vector_index),'vector_index_sha256':sha(vector_index),'numpy_version':np.__version__,
      'source_sha256':sha(Path(__file__)),'transaction_source_sha256':sha(Path(__file__).with_name('independent_cost.py'))}
    with a.out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(report['status'],vectors,states,flush=True)


if __name__=='__main__':main()
