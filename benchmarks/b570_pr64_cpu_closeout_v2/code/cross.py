from evidence import *
import struct,numpy as np

def kv(name):
    data=read(name);cursor=0
    def scalar(fmt):
        nonlocal cursor
        fmt='<'+fmt;v=struct.unpack_from(fmt,data,cursor);cursor+=struct.calcsize(fmt);return v[0] if len(v)==1 else v
    n=scalar('I');arch=data[cursor:cursor+n];cursor+=n
    assert arch==b'qwen3' and scalar('I')==1
    cells=scalar('I');pos=[]
    for _ in range(cells):
        p,owners=scalar('iI');assert owners==1 and scalar('i')==0;pos.append(p)
    trans,layers=scalar('II');assert trans==1 and layers in (28,36)
    tensors=[]
    for _ in range(layers):
        dtype,width=scalar('iQ');assert dtype==1
        n=width*cells;assert cursor+n<=len(data);tensors.append(np.frombuffer(data,dtype='<f2',count=n//2,offset=cursor));cursor+=n
    for _ in range(layers):
        dtype,width,embed=scalar('iII');assert dtype==1 and width==2
        n=width*embed*cells;assert cursor+n<=len(data);tensors.append(np.frombuffer(data,dtype='<f2',count=n//2,offset=cursor));cursor+=n
    assert cursor==len(data) and sorted(pos)==list(range(max(pos)+1))
    return dict(sha256=digest(data),positions=pos,layers=layers,tensors=tensors,bytes=len(data))

def preserve(d):
    assert d['before']==d['after']
    for p,h in d['before'].items():assert digest(read(p))==h,p

def main():
    begin('cross'); manifest=load('B_MANIFEST.json');hist=load('HISTORICAL_PARENTS.json');eog=load('dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids'];cases=[];kvrows=[];scores=[];shams=[]
    for ci,c in enumerate(manifest['cases']):
        assert c['status']=='ALIGNED'
        common=load(c['batch_source']);assert common['batch_target']==c['batch'] and common['ids']==c['common_prefix']
        assert c['primary_row']==min(c['retained_divergence']-c['committed_length'],len(c['batch'])-1)
        assert all(x['pos']==c['logical_position']+i and x['seq']==[0] and x['logits'] for i,x in enumerate(c['batch']))
        donor_kv=[]
        for di,d in enumerate(c['donors']):
            cp=load(d['checkpoint']);assert digest(read(d['checkpoint']))==d['checkpoint_sha256']
            parent=load(d['parent_raw']);assert cp['ids']==parent['ids'][:c['committed_length']]==c['common_prefix']
            assert cp['n_predict']==len(cp['ids']) and cp['pending']==-1 and not cp['has_eos']
            s=cp['effective_sampling']; assert s['temp']==0 and s['penalty_repeat']==1 and s['penalty_freq']==s['penalty_present']==s['dry_multiplier']==0 and s['grammar_empty'] and not s['grammar_lazy'] and not s['reasoning_control'] and s['reasoning_budget_tokens']==-1 and not s['backend_sampling'] and s['mirostat']==0
            assert cp['target_sampler']['accepted_history']==[[i,True] for i in cp['ids']]
            assert cp['draft_sampler']['accepted_history']==[[i,True] for i in cp['ids']+cp['draft_tokens'][1:]]
            for role in ['target','draft']:
                s=cp[role+'_sampler'];assert all(s[a]==s[b] for a,b in [('chain','clone_chain'),('history_string','clone_history'),('seed','clone_seed')])
                p=d['checkpoint'][:-5]+'.'+role+'.kv';k=kv(p);assert digest(read(p.replace('.kv','.source_after.kv')))==k['sha256']
                positions=cp[role+'_position'];assert min(k['positions'])==positions['min'] and max(k['positions'])==positions['max']
                kvrows.append(dict(case=ci,donor=di,role=role,sha256=k['sha256'],bytes=k['bytes'],cells=len(k['positions']),min_position=min(k['positions']),max_position=max(k['positions']),layers=k['layers'],ownership='all sequence 0',fully_consumed=True))
                if role=='target':donor_kv.append(k)
            u=f'B_SHAM/{ci}/{di}/{c["task"]}';r=check_receipt('raw/'+digest(u.encode())[:20]+'/RESULT.json');a=load(next(p for p in r['files'] if p.endswith('/capture.json')))
            assert a['ids']==parent['ids'] and a['eog']==parent['eog']
            rr=load(next(p for p in r['files'] if p.endswith('.resume.json'))); assert rr['target_roundtrip'] and rr['draft_roundtrip'] and rr['no_prefill_recompute']
            preserve(load(f'derived/SHAM_SOURCE-{ci}-{di}.json'))
            shams.append(dict(unit_id=u,full_raw_equal=True,target_roundtrip=True,draft_roundtrip=True,no_prefill_recompute=True,source_preserved=True))
        tensors=zip(donor_kv[0]['tensors'],donor_kv[1]['tensors']); different=sum(int(np.count_nonzero(a.view('<u2')!=b.view('<u2'))) for a,b in tensors)
        arrays={}; cells=[]
        for di,d in enumerate(c['donors']):
            for ri,recipe in enumerate(c['recipes']):
                r=check_receipt(f'aux/B_CROSS_{ci}_{di}_{ri}/RESULT.json');p=next(p for p in r['files'] if p.endswith('/cross.json'));j=load(p)
                assert j['batch']==c['batch'] and j['recipe']==recipe and j['n_vocab']==151936
                before=kv(p+'.before.kv'); after=kv(p+'.after.kv')
                assert before['sha256']==donor_kv[di]['sha256'] and j['consumed_bytes']==before['bytes'] and j['restore_equal']
                assert sorted(after['positions'])==list(range(c['batch'][-1]['pos']+1))
                preserve(load(next(p for p in r['files'] if p.endswith('/SOURCE_UNCHANGED.json'))))
                a=np.frombuffer(read(p+'.logits.f32'),dtype='<f4').reshape(len(c['batch']),151936);assert np.isfinite(a).all();arrays[di,ri]=a
                bad=load(c['donors'][0 if c['task']=='MBPP/72' else 1]['parent_raw'])['ids'];ref=hist[c['task']+'/R_reference']['endpoint']['ids']
                for i,x in enumerate(a):
                    top=np.argsort(-x,kind='stable')[:2];one,two=map(int,top)
                    assert one==j['rows'][i]['top1']==j['row_decision_ids'][i] and two==j['rows'][i]['top2']
                    assert float(x[one])==j['rows'][i]['top1_score'] and float(x[two])==j['rows'][i]['top2_score']
                    idx=c['committed_length']+i;refid=ref[idx] if idx<len(ref) else None;alt=bad[idx] if idx<len(bad) else None
                    scores.append(dict(case=ci,task=c['task'],round=c['round'],donor=di,recipe=ri,row=i,focus=i==c['primary_row'],output_index=idx,top1=one,top2=two,top1_score=float(x[one]),top2_score=float(x[two]),margin=float(x[one]-x[two]),reference_id=refid,reference_score=float(x[refid]) if refid is not None else 'unknown',alternative_id=alt,alternative_score=float(x[alt]) if alt is not None else 'unknown',eog_scores=json.dumps({str(t):float(x[t]) for t in eog},sort_keys=True)))
                cells.append(dict(unit_id=r['unit_id'],before_sha256=before['sha256'],after_sha256=after['sha256'],full_vocabulary_rows=a.shape[0],forward_ms=j['forward_ms'],host_seconds=r['host_seconds']))
        rows=[]
        for i in range(len(c['batch'])):
            mat=[[int(np.argmax(arrays[d,p][i])) for p in [0,1]] for d in [0,1]]
            path=any(mat[d][0]!=mat[d][1] for d in [0,1]);state=any(mat[0][p]!=mat[1][p] for p in [0,1])
            kind='INTERACTION' if state and path else 'STATE_EFFECT' if state else 'CURRENT_PATH_EFFECT' if path else 'NO_DETECTED_EFFECT'
            rows.append(dict(row=i,output_index=c['committed_length']+i,decisions=mat,classification=kind))
        fp={k:v.astype('float64') for k,v in arrays.items()};nonadd=float(np.max(np.abs(fp[1,1]-fp[1,0]-fp[0,1]+fp[0,0])))
        focus=rows[c['primary_row']];same=c['recipes'][0]==c['recipes'][1]
        # Labels differ for duplicate recipes: compare actual numerical recipe fields.
        same=all(c['recipes'][0][k]==c['recipes'][1][k] for k in ['ub','outputs_max','outputs_max_per_seq'])
        assert (focus['classification']=='STATE_EFFECT' and same) if c['task']=='MBPP/72' else (focus['classification']=='INTERACTION' and not same)
        cases.append(dict(case=ci,task=c['task'],round=c['round'],committed_length=c['committed_length'],retained_divergence=c['retained_divergence'],focus_row=c['primary_row'],focus=focus,all_rows=rows,current_columns_identical=same,recipes=c['recipes'],donor_labels=[d['label'] for d in c['donors']],different_target_F16_elements=different,max_absolute_score_nonadditivity=nonadd,cells=cells))
    assert len(cases)==6 and len(shams)==12
    table('CAUSAL_ALL_ROW_SCORES.csv',scores);table('KV_RECHECK.csv',kvrows)
    write('CAUSAL_RECHECK.json',dict(status='PASS',cases=cases,full_own_path_shams=shams,auxiliary_cells=24,kv_parsed_donor_states=24,opaque_sampler_bytes='UNAVAILABLE',RNG_cursor='UNAVAILABLE; supported effective greedy only',scope='Local target numeric state x whole current recipe; score nonadditivity is distinct from argmax class and full candidate endpoint qualification. No unique operator cause or counterfactual repaired trajectory inferred.'))
    finish('cross');print([(c['task'],c['round'],c['focus']['classification'],c['focus']['decisions'],c['different_target_F16_elements']) for c in cases])
if __name__=='__main__':main()
