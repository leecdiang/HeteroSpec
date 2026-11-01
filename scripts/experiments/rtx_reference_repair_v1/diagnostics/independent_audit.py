"""Read-only raw audit using struct decoding and the authenticated old transaction checker.

No imports of the candidate audit/runner; no model execution. Run after native work.
"""
import argparse,ast,hashlib,json,math,pathlib,statistics,struct,subprocess

def need(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def endpoint(r):
    e=r['endpoint'];need(all(r[k]==e[k] for k in ('ids','eog','length','terminal_id','stop_reason')),'endpoint duplication')
    need(1<=len(e['ids'])<=128 and e['length']==len(e['ids']) and e['terminal_id']==e['ids'][-1],'endpoint length/terminal')
    flags=[x in r['vocabulary_eog'] for x in e['ids']]
    need(flags==e['eog'] and not any(flags[:-1]),'EOG sequence')
    need(e['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(e['ids'])==128),'stopping contract')
    return e
def vector(p,n):
    data=p.read_bytes();need(len(data)==n*4,'full vocabulary: '+str(p));best=-math.inf;token=None
    for i,(v,) in enumerate(struct.iter_unpack('<f',data)):
        need(math.isfinite(v),'nonfinite vector: '+str(p))
        if v>best:best=v;token=i
    return token,hashlib.sha256(data).hexdigest()
def main(root,repo,out):
    root=pathlib.Path(root);repo=pathlib.Path(repo);out=pathlib.Path(out);need(not out.exists(),'fresh audit output')
    blob='f25daa3cfed6fd8e9f11d5859cc6d2c9308b1036';source=subprocess.check_output(['git','-C',str(repo),'cat-file','blob',blob])
    need(hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()==blob,'old checker source identity')
    tree=ast.parse(source);fn=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_cycles'];need(len(fn)==1,'old checker anchor')
    env={'need':need};exec(compile(ast.Module(body=fn,type_ignores=[]),'authenticated_old_transaction_checker','exec'),env)
    manifest=[];units=[];allrows={};vector_count=state_count=0;reference_mismatches=[];observer_pairs=0;path_pairs=[]
    for schedule in sorted(root.glob('*/units/*/SLOTS.json')):
        unit=schedule.parent;epoch=unit.parent.parent;receipt=read(unit/'RECEIPT.json');slots=read(schedule);rows=[];panel=read(unit/'PANEL.json')
        identity=read(epoch/('ORIGINAL_BINDING.json' if unit.name=='original_reference' else 'BINDING.json'))
        references=read(epoch/'DEV_REFERENCES.json') if (epoch/'DEV_REFERENCES.json').exists() and unit.name not in ('original_reference','heldout','formal_s0','formal_s1','formal_s2','formal_s3') else {}
        need(receipt['active_processes_after_wait']==0 and not receipt['lock_retained'],'unsettled process')
        for slot in slots:
            p=unit/'native'/(slot['slot_id']+'.json')
            if not p.exists():continue
            r=read(p);e=endpoint(r);need(r['slot']==slot,'slot identity');item=panel['inputs'][slot['source_index']]
            need(r['identity']==identity['families'][r['family']],'executable/model identity')
            need(r['prompt_ids']==item['prompt_ids'] and r['input_id']==item['id'],'input identity')
            if item['id'] in references and e!=references[item['id']]:reference_mismatches.append(p.relative_to(root).as_posix())
            need(not r['teacher_forced'] and r['qualification_eligible'],'unexpected forced diagnostic')
            n=151936 if r['family']=='Qwen' else 128256
            env['validate_cycles'](r,{'prompt_tokens':len(item['prompt_ids']),'cap':128},{'eog':r['vocabulary_eog'],'vocabulary_tokens':n})
            if not r['draft_enabled']:need(r['target_final_kv']=={'min':0,'max':len(item['prompt_ids'])+len(e['ids'])-2},'ordinary pending KV')
            folder=p.with_suffix('');vhash={};shash={};best={}
            if slot['observer']=='heavy':
                for role in ('target','draft'):
                    for v in sorted((folder/role).glob('*.f32')):
                        key=v.relative_to(folder).as_posix();best[key],vhash[key]=vector(v,n);vector_count+=1
                need(best['target/initial.f32']==e['ids'][0],'initial decision')
                if r['draft_enabled']:
                    for c in r['cycles']:
                        for label,role,tokens in [('proposal','draft',c['proposals']),('verify','target',c['decisions'])]:
                            for i,t in enumerate(tokens):need(best[f'{role}/{label}-{c["cycle"]}-{i}.f32']==t,'saved decision')
                else:
                    for i,t in enumerate(e['ids'][1:],1):need(best[f'target/ordinary-{i}.f32']==t,'ordinary decision')
                for role in ('target','draft'):
                    if role=='draft' and not r['draft_enabled']:continue
                    name=role+'_final.state';meta=r[role+'_state'];f=folder/name;shash[name]=sha(f);state_count+=1
                    need(f.stat().st_size==meta['bytes'] and shash[name]==meta['sha256'],'saved state')
                b=r.get('boundary') or {}
                for name,key in [('boundary_source.state','boundary_state_sha256'),('boundary_logits.f32','boundary_logits_sha256')]:
                    if key in b:shash[name]=sha(folder/name);need(shash[name]==b[key],'boundary artifact')
                if r.get('repair_prefill','native')!='native':need(b['positions_equal'] and b['receiver_readback_checked'] and b['serialized_bytes_equal'] and not b['pending_token_consumed'],'native boundary assertions')
            manifest.append({'path':p.relative_to(root).as_posix(),'sha256':sha(p),'vectors':vhash,'states':shash});rows.append(r)
        if receipt['success'] and receipt['completed_requests']:need(len(rows)==len(slots)==receipt['completed_requests'],'complete stage')
        units.append({'path':unit.relative_to(root).as_posix(),'receipt_sha256':sha(unit/'RECEIPT.json'),'success':receipt['success'],'records':len(rows),'reserved_slots':len(slots)})
        allrows[unit.relative_to(root).as_posix()]=rows
        if unit.name.startswith('development') or unit.name in ('regression01','heldout','original_reference'):
            pairs={}
            for r in rows:
                s=r['slot'];key=(s['source_index'],s['arm'],s.get('repair',{}).get('prefill','native'));pairs.setdefault(key,{})[s['observer']]=r
            for pair in pairs.values():
                if set(pair)=={'off','heavy'}:
                    a,b=pair['off'],pair['heavy'];need(endpoint(a)==endpoint(b) and all(a[k]==b[k] for k in ('cycles','target_final_kv','draft_final_kv')),'observer altered natural result');observer_pairs+=1
            for (i,arm,prefill),pair in pairs.items():
                if not arm.endswith('_PQ') or 'heavy' not in pair:continue
                q=pairs.get((i,arm[:-3]+'_QB',prefill),{}).get('heavy')
                if q is None:continue
                a=pair['heavy'];af=unit/'native'/a['slot']['slot_id'];bf=unit/'native'/q['slot']['slot_id'];files=lambda f:{p.relative_to(f).as_posix():sha(p) for role in ('target','draft') for p in (f/role).glob('*.f32')}
                path_pairs.append({'unit':unit.relative_to(root).as_posix(),'input':i,'arm_class':arm[:-3],'prefill':prefill,'endpoint_equal':endpoint(a)==endpoint(q),'transaction_equal':all(a[k]==q[k] for k in ('cycles','target_final_kv','draft_final_kv')),'vectors_equal':files(af)==files(bf),'final_state_hashes_equal':all(a.get(role+'_state')==q.get(role+'_state') for role in ('target','draft'))})
        print('AUDITED',unit.relative_to(root),len(rows),flush=True)
    ledger=[json.loads(l) for l in (root/'LEDGER.jsonl').read_text().splitlines() if l];starts=[r for r in ledger if r['event']=='START'];ends=[r for r in ledger if r['event']=='END']
    need(len(starts)==len(ends),'unsettled ledger');reserved=sum(r['reserved_requests'] for r in starts);dev=sum(r['reserved_requests'] for r in starts if r['stage']=='development')
    need(reserved<=1200 and dev<=480,'shared budget')
    confirmation={};cost=None;ep=root/'epoch03'
    if (ep/'ORIGINAL_HELDOUT_REFERENCES.json').exists():
        refs=read(ep/'ORIGINAL_HELDOUT_REFERENCES.json')['references'];old=allrows['epoch03/units/original_reference']
        need(len(old)==24 and all(endpoint(r)==refs[r['input_id']] for r in old),'original oracle stability')
        candidates=allrows.get('epoch03/units/heldout',[]);fail=[r['slot']['slot_id'] for r in candidates if endpoint(r)!=refs[r['input_id']]]
        confirmation={'original_records':len(old),'candidate_records':len(candidates),'failed_slots':fail}
        timed=[r for key,rows in allrows.items() if key.startswith('epoch03/units/formal_s') for r in rows]
        if timed:
            need(len(timed)==576 and not fail and len(candidates)==120,'qualification/timing completeness');table={}
            for r in timed:
                s=r['slot'];need(endpoint(r)==refs[r['input_id']] and not r['capture'] and r['observer_mode']=='off','clean timed reference')
                key=(s['session'],s['source_index'],s['experiment_arm'],s['category']);need(key not in table,'timing duplicate');t=r['service_seconds'];need(math.isfinite(t) and t>0,'positive service');table[key]=t
            labels=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB');need(set(table)=={(s,i,a,k) for s in range(4) for i in range(12) for a in labels for k in ('warmup','measured')},'complete timing Cartesian set')
            blocks=[]
            for s in range(4):
                for i in range(12):
                    t={a:table[s,i,a,'measured'] for a in labels};pq=statistics.mean([t['C_PQ_A'],t['C_PQ_B']]);blocks.append(dict(session=s,input=i,layout=t['C_QB']/pq,AA=t['C_PQ_A']/t['C_PQ_B'],D_QB=t['M_QB']/t['C_QB'],D_PQ=t['M_PQ']/pq,CQB_R=t['C_QB']/t['R'],MQB_R=t['M_QB']/t['R']))
            geo=lambda xs:math.exp(statistics.fmean(map(math.log,xs)));means={k:geo(b[k] for b in blocks) for k in ('layout','AA','D_QB','D_PQ','CQB_R','MQB_R')};noise=max(abs(geo(b['AA'] for b in blocks if b['input']==i)-1) for i in range(12));sessions=[geo(b['layout'] for b in blocks if b['session']==s) for s in range(4)]
            cost={'means':means,'AA_max_input':noise,'sessions':sessions,'practical_layout_gain':1-means['layout']>max(.02,noise) and all(x<1 for x in sessions),'blocks':blocks}
            primary=read(ep/'FINAL_COST.json');need(all(math.isclose(v,primary['means'][k],rel_tol=1e-12) for k,v in means.items()) and primary['practical_layout_gain']==cost['practical_layout_gain'],'cost implementations disagree')
    result={'status':'INDEPENDENT_RAW_AUDIT_COMPLETE','checker':'struct.iter_unpack finite/first-argmax; authenticated old validate_cycles AST; independent state hashes and fmean-log cost','old_checker_blob':blob,'self_sha256':sha(__file__),'units':units,'records':len(manifest),'full_vectors':vector_count,'final_states':state_count,'observer_pairs':observer_pairs,'reference_mismatches':reference_mismatches,'PQ_QB_pairs':path_pairs,'charged_requests':reserved,'charged_development':dev,'remaining_total':1200-reserved,'remaining_development':480-dev,'native_process_seconds':sum(r['seconds'] for r in ends),'confirmation':confirmation,'cost':cost,'record_manifest':manifest,'limits':'Same-host independent implementation, not external replication. Boundary immediate receiver equality uses native assertions; retained final/source bytes are rehashed. Scientific mismatches remain outcomes, not audit errors.'}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('COMPLETE',len(manifest),reserved,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('repo');p.add_argument('out');a=p.parse_args();main(a.root,a.repo,a.out)
