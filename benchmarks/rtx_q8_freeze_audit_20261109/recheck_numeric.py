"""Re-evaluate raw vectors, serialized active KV and transactions independently."""
from pathlib import Path
import collections,json,time,traceback
from core import WORK,RECORDS,Reader,R_SHA,read,put,ledger,digest,OUT

class Audit:
    def __init__(self):
        self.reader=Reader();self.refs={};self.ends={};self.checks=[];self.failures=[];self.coverage=collections.Counter();self.branches=collections.defaultdict(lambda:collections.defaultdict(set));self.eog=None
        self.attempts=ledger();self.jobs={a['id']:read(WORK/'runs'/a['id']/'JOB.json') for a in self.attempts}
    def add_reference(self,prefix,vector,state=None):
        prefix=tuple(prefix);entry=self.refs.setdefault(prefix,dict(vectors=[],states=[]))
        v=self.reader.vector(vector)
        if entry['vectors']:assert v['sha256']==self.reader.vector(entry['vectors'][0])['sha256'],'Independent R vector instability'
        entry['vectors'].append(str(vector))
        if state:
            s=self.reader.state(state,len(prefix))
            if entry['states']:assert s['active_sha256']==self.reader.state(entry['states'][0],len(prefix))['active_sha256'],'Independent R state instability'
            entry['states'].append(str(state))
    def build_references(self):
        for a in self.attempts:
            j=self.jobs[a['id']]
            if j['exe_sha256']!=R_SHA:continue
            native=WORK/'runs'/a['id']/'native';meta=read(native/'result.json');assert meta['status']=='COMPLETE'
            if self.eog is None:self.eog=set(meta['eog_ids'])
            else:assert self.eog==set(meta['eog_ids'])
            assert meta['vocab']==151936
            for case in j['job'].get('cases',[]):
                tape=sum((c['ids'] for c in case['forced']),[])
                for n in case['observe_positions']:
                    path=native/case['name']/'captures'/str(n)
                    self.add_reference(tape[:n],path/'frontier.f32',path/'sequence.bin' if n in case['state_positions'] else None)
            for item in j['job'].get('inputs',[]):
                path=native/item['name'];r=read(path/'receipt.json');x=item['input'];ids=r['ids'];key=x['id']
                assert r['prompt_ids']==x['prompt_ids'] and r['endpoint']['ids']==ids
                if key in self.ends:
                    old=self.ends[key]['ids'];assert old[:min(len(old),len(ids))]==ids[:min(len(old),len(ids))],'Scalar endpoint instability'
                    if len(old)>len(ids):continue
                self.ends[key]=r['endpoint']
                if item['capture']:
                    for i in range(len(ids)):
                        label='initial' if i==0 else 'ordinary-'+str(i)
                        prefix=x['prompt_ids']+ids[:i];state=None
                        if i==0:state=path/'target/state/initial/sequence.bin'
                        if i==len(ids)-1:state=path/'target/state/terminal/sequence.bin'
                        self.add_reference(prefix,path/'target'/(label+'.f32'),state)
            self.coverage['independent_R_workers']+=1
        print('REFERENCE_BANK',len(self.refs),'prefixes',len(self.ends),'autonomous roots',flush=True)
    def vector(self,actual,prefix,label):
        e=self.refs[tuple(prefix)];ref=e['vectors'][0];av=self.reader.vector(actual);rv=self.reader.vector(ref)
        assert av['sha256']==rv['sha256'],('Full-vector bitwise mismatch',actual,ref)
        self.coverage['full_vector_comparisons']+=1
        return dict(label=label,actual=str(actual),reference=ref,sha256=av['sha256'],prefix=len(prefix)),av['greedy']
    def state(self,actual,prefix,label):
        e=self.refs[tuple(prefix)];assert e['states'],('No independently captured reference state',label,len(prefix))
        ref=e['states'][0];av=self.reader.state(actual,len(prefix));rv=self.reader.state(ref,len(prefix))
        assert av['active_sha256']==rv['active_sha256'],('Active F16 KV bitwise mismatch',actual,ref)
        self.coverage['active_KV_comparisons']+=1
        return dict(label=label,actual=str(actual),reference=ref,active_sha256=av['active_sha256'],positions=len(prefix),bytes=av['active_bytes'])
    def endpoint(self,x):
        r=self.ends[x['id']];ids=r['ids'][:x['cap']];eog=[v in self.eog for v in ids]
        assert len(ids)==x['cap'] or eog[-1],'Reference shorter than required cap without EOG'
        return dict(ids=ids,eog=eog,length=len(ids),terminal_id=ids[-1],stop_reason='EOG' if eog[-1] else 'CAP')
    def transaction(self,j,item):
        path=WORK/'runs'/j['id']/'native'/item['name'];r=read(path/'receipt.json');x=item['input'];k=j['job']['k'];prompt=x['prompt_ids'];capture=item['capture'];replay=j['job'].get('proposal_mode')=='replay'
        assert r['endpoint']==self.endpoint(x) and r['prompt_ids']==prompt and r['k']==k
        assert r['target_output_reserve']==8 and r['draft_ubatch']==4
        vectors=[];states=[];prefix=list(prompt);pending=r['ids'][0];out=[pending];done=pending in self.eog or len(out)==x['cap']
        if capture:
            v,g=self.vector(path/'target/initial.f32',prefix,'initial');vectors.append(v);assert g==pending
        def capture_state(label):
            states.append(self.state(path/'target/state'/label/'sequence.bin',prefix,label))
            v,_=self.vector(path/'target/state'/label/'frontier.f32',prefix,label+'/frontier');vectors.append(v)
        if capture:capture_state('initial')
        for ci,c in enumerate(r['cycles']):
            assert not done and c['cycle']==ci and c['base']==len(prefix) and c['seed']==pending
            before=dict(min=0,max=len(prefix)-1);assert c['target_before']==before
            assert c['draft_before']==(dict(min=-1,max=-1) if replay else before)
            proposals=c['proposals'];decisions=c['decisions'];assert len(proposals)==k and len(decisions)==k+1
            assert all(0<=t<151936 for t in proposals+decisions)
            verify=[pending]+proposals
            if capture:
                for row in range(k+1):
                    v,g=self.vector(path/'target'/f'verify-{ci}-{row}.f32',prefix+verify[:row+1],f'verify-{ci}-{row}');vectors.append(v);assert g==decisions[row]
            accepted=0;rejected=False;kind=None
            for proposal,decision in zip(proposals,decisions):
                if done:break
                if proposal==decision:accepted+=1;token=proposal;kind='accepted'
                else:token=decision;pending=decision;rejected=True;kind='correction'
                out.append(token);done=token in self.eog or len(out)==x['cap']
                if rejected:break
            if accepted==k and not done:
                pending=decisions[k];out.append(pending);done=pending in self.eog or len(out)==x['cap'];kind='bonus'
            prefix+=verify[:accepted+1]
            assert c['accepted']==accepted and c['rejected']==rejected and c['commit_kind']==kind
            assert c['keep']==len(prefix) and c['output_length']==len(out) and c['done']==done
            assert c['pending_after']==(None if done else pending)
            bounds=dict(min=0,max=len(prefix)-1);assert c['target_after']==bounds and c['draft_after']==(dict(min=-1,max=-1) if replay else bounds)
            if capture:capture_state('commit-'+str(ci))
            arm=(j['job']['lowering'],k,'packed' if '-packed' in j['id'] else 'loop4')
            self.branches[arm]['rejection_ranks'].update([accepted] if rejected else [])
            self.branches[arm]['kinds'].add(kind);self.branches[arm]['stops'].add(r['stop_reason'])
        assert done and out==r['ids'] and r['eog']==[v in self.eog for v in out]
        assert r['target_final_kv']==dict(min=0,max=len(prefix)-1)
        assert r['draft_final_kv']==(dict(min=-1,max=-1) if replay else r['target_final_kv'])
        hist=dict(collections.Counter(str(e['width']) for e in r['executions']));assert hist==r['target_physical_width_hist']
        total=len(prompt)+(k+1)*len(r['cycles']);assert sum(int(w)*n for w,n in hist.items())==total
        assert sum(int(w)*n for w,n in r['draft_physical_width_hist'].items())==(0 if replay else total)
        verify_ex=iter([e for e in r['executions'] if e['phase']=='VERIFY'])
        for c in r['cycles']:
            consumed=0;wanted=[];groups=[]
            while consumed<k+1:
                e=next(verify_ex);assert e['position']==c['base']+consumed
                wanted+=e['requested_rows'];consumed+=e['width'];groups.append(e)
            assert consumed==k+1 and sorted(wanted)==list(range(k+1))
            if j['job']['lowering']=='LOCAL':assert len(groups)==1 and groups[0]['width']==k+1
        assert next(verify_ex,None) is None
        if not capture:assert all(v==0 for v in r['observed_API_calls_within_service'].values())
        if len(r['cycles'])>=2:assert r['graphs_reused']>0
        if item['name'].startswith('reject-'):assert len(r['cycles'])==1 and r['cycles'][0]['accepted']==int(item['name'].split('-')[1]) and r['cycles'][0]['rejected']
        if item['name'].startswith('cap-'):assert len(out)==x['cap'] and r['cycles'][0]['commit_kind']=='accepted'
        if item['name']=='bonus':assert len(r['cycles'])==1 and r['cycles'][0]['commit_kind']=='bonus'
        if item['name']=='cap1':assert not r['cycles']
        if item['name'] in ('bonus-resume','correction-resume'):assert len(r['cycles'])>=2 and r['cycles'][0]['commit_kind']==('bonus' if item['name']=='bonus-resume' else 'correction')
        self.coverage['heavy_transactions' if capture else 'clean_transactions']+=1
        return dict(job=j['id'],name=item['name'],capture=capture,endpoint=True,cycles=len(r['cycles']),stop=r['stop_reason'],vectors=vectors,states=states)
    def geometry(self,j):
        native=WORK/'runs'/j['id']/'native';meta=read(native/'result.json');allcases=[]
        for i,case in enumerate(j['job']['cases']):
            tape=sum((c['ids'] for c in case['forced']),[]);vectors=[];states=[]
            for n in case['observe_positions']:
                p=native/case['name']/'captures'/str(n)
                v,_=self.vector(p/'frontier.f32',tape[:n],str(n));vectors.append(v)
                if n in case['state_positions']:states.append(self.state(p/'sequence.bin',tape[:n],str(n)))
            r=meta['cases'][i]
            if j['id'].startswith('geometry-v2'):
                hist=dict(collections.Counter(str(e['width']) for e in r['executions']));assert hist==r['target_physical_width_hist'] and not r['draft_physical_width_hist']
                q=j['job']['k']+1;v=[e for e in r['executions'] if e['phase']=='VERIFY'];assert sum(e['width'] for e in v)==q
                assert sorted(x for e in v for x in e['requested_rows'])==list(range(q))
                if j['job']['lowering']=='LOCAL':assert len(v)==1 and v[0]['width']==q
                if case['name'].startswith('edge') and j['job']['lowering']=='SIMPLE':assert [e['width'] for e in v]==[1,q-1]
                graph=[g for g in r['geometry'] if g['phase']=='VERIFY' and g['op']=='MUL_MAT'];assert graph
                packed=[g for g in graph if g['name'].startswith('frontier_packed_')]
                if q==4:assert not packed
                if q==8 and 'packed' in j['id'] and any(e['width']==8 for e in v):assert packed and all(g['ne'][1:3]==[4,2] for g in packed)
                if q==8 and 'loop4' in j['id'] and any(e['width']==8 for e in v):assert any(g['name'].startswith('hs_backend_loop4_') for g in graph)
            allcases.append(dict(name=case['name'],vectors=vectors,states=states));self.coverage['geometry_cases']+=1
        return dict(job=j['id'],geometry=allcases)
    def same_work(self,j,p):
        path=WORK/'runs'/j['id']/'native'/p['name'];r=read(path/'receipt.json');prefix=p['prefix_ids'];tokens=p['append_ids'];head=len(prefix);vectors=[];states=[]
        assert r['append_ids']==tokens and r['position']==head and len(tokens)==8
        v,_=self.vector(path/'initial-frontier.f32',prefix,'initial');vectors.append(v)
        for i in range(8):
            v,_=self.vector(path/f'row-{i}.f32',prefix+tokens[:i+1],str(i));vectors.append(v)
        states.append(self.state(path/'initial-sequence.bin',prefix,'initial'));states.append(self.state(path/'final-sequence.bin',prefix+tokens,'final'))
        width=8 if p['execution']=='q8' else 4
        assert r['target_physical_width_hist']=={str(width):8//width} and not r['draft_physical_width_hist']
        assert r['outputs_survive_next_decode_and_plan_clear'] and r['timer_exports']==r['timer_imports']==r['timer_context_creates']==0
        assert sorted(e['position']-head+i for e in r['executions'] for i in e['requested_rows'])==list(range(8))
        expected=[p['extent']]*8 if p['geometry']=='within' else [p['extent']]*4+[p['extent']+256]*4
        assert sum((e['expected_extents'] for e in r['executions']),[])==expected and r['prefix_executions'][-1]['actual_attention_extent']==p['extent']
        self.coverage['same_work_heavy' if p['capture'] else 'same_work_clean']+=1
        return dict(job=j['id'],name=p['name'],vectors=vectors,states=states)
    def run(self):
        start=time.monotonic();self.build_references()
        for a in self.attempts:
            j=self.jobs[a['id']]
            if j['exe_sha256']==R_SHA:continue
            try:
                if a['status']=='EXPECTED_REJECT':
                    n=WORK/'runs'/a['id'];failure=read(n/'native/failure.json');assert j['expect_error'] in failure['error'];assert a['code']==2
                    self.checks.append(dict(job=j['id'],negative_error_verified=failure['error'],new_execution=False));self.coverage['negative_raw_error_records']+=1;continue
                if 'cases' in j['job']:self.checks.append(self.geometry(j))
                for item in j['job'].get('inputs',[]):self.checks.append(self.transaction(j,item))
                for p in j['job'].get('same_work',[]):self.checks.append(self.same_work(j,p))
                if 'proposal_tape_requests' in j['job']:self.coverage['producer_hash_records_only']+=len(j['job']['proposal_tape_requests'])
            except Exception as e:
                self.failures.append(dict(job=j['id'],error=repr(e),traceback=traceback.format_exc()));print('AUDIT_EXCEPTION',j['id'],repr(e),flush=True)
            if a['stage']!='live' or j.get('position')==7:print('OFFLINE_WORKER',j['id'],flush=True)
        put('NUMERIC_RECHECK.json',dict(passed=not self.failures,reader='New independent byte/hash/F16-layout reader and transaction reconstruction; no original gate implementation imported',
            coverage=dict(self.coverage),failures=self.failures,branches={str(k):{n:sorted(v) for n,v in d.items()} for k,d in self.branches.items()},checks=self.checks,
            reference_prefixes=len(self.refs),raw_files_read=len(self.reader.seen),bytes_read=self.reader.bytes,wall_seconds=time.monotonic()-start,new_GPU_requests=0,
            limitations=['Clean live has no full-vector/KV capture: endpoint/trace/width/API checks only; heavy-qualified bridge is checked separately.',
            'Producer full vectors are not exported: producer side recorded hashes require source/record trust; no independent producer-vector byte reread claimed.',
            'Negative rejection records re-evaluated offline; native guards were not executed again.']))
        put('RAW_FILES_READ.json',self.reader.seen)
        print(json.dumps(dict(passed=not self.failures,coverage=dict(self.coverage),failures=len(self.failures),wall_seconds=time.monotonic()-start)),flush=True)

if __name__=='__main__':Audit().run()
