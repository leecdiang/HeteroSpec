"""Offline full-vector/state comparison against independent original-R bytes."""
from develop import *
import zlib
from normalize import trace_from_row

class HistoricalChunks:
    def __init__(self):
        self.store=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence');self.rows={};self.verified=set()
        for p in self.store.glob('*.json'):
            j=json.loads(p.read_bytes())
            for row in j.get('files',[]):self.rows[row['sha256']]=row
    def read(self,container,spec):
        p=container/spec['path']
        if p.exists():data=p.read_bytes()
        else:
            row=self.rows[spec['sha256']];parts=[]
            for h in row['chunks']:
                raw=zlib.decompress((self.store/'chunks'/h[:2]/h).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;parts.append(raw)
            data=b''.join(parts)
        assert len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256']
        return data

class Bank:
    def __init__(self,family,ix,free):
        self.family=family;self.ix=ix;self.free=free;self.entries={};self.old=None
        self.meta=json.loads((free.parent/'result.json').read_bytes());self.p=profile(self.meta,family)
        r=json.loads((free/'receipt.json').read_bytes());r['study_cap']=roots(family)[ix]['cap']
        _,d=trace_from_row(r,r['prompt_ids'],self.meta['vocab'],self.meta['eog_ids'],'rtx')
        for use in d['vector_uses']:
            key=use['key'];name='initial' if key=='initial' else 'ordinary-'+str(int(key[4:].split('/')[0])+1)
            self.entries[tuple(use['prefix'])]=dict(frontier_file=str(free/'target'/(name+'.f32')))
        for key,state in [('initial',d['states'][0]),('terminal',d['states'][-1])]:self.entries[tuple(state['prefix'])]['sequence_file']=str(free/'target/state'/key/'sequence.bin')
        self.endpoint=r['endpoint']
        if family=='Qwen' and ix<3:
            for arm in ('D1','D2','D4','M'):
                suffix='' if ix==0 else '-root'+str(ix);container=Path('D:/rtx184-qualification')/(arm+suffix)/'bank';path=container/'capture.json';j=json.loads(path.read_bytes());assert j['binding']['target_model_sha256']==MODELS[family]['target_sha256']
                for row in j['prefixes']:
                    prefix=tuple(row['prefix']);entry=self.entries.setdefault(prefix,{})
                    entry['historical']=(container,row)
        for p in sorted((ROOT/'runs').glob(f'{family}-teacher-r{ix}-*')):
            if (p/'COMPLETE.json').exists():self.add_teacher(p)

    def add_teacher(self,out):
        job=json.loads((out/'job.json').read_bytes())
        for one in job['cases']:
            tape=sum((x['ids'] for x in one['forced']),[])
            for n in one['observe_positions']:
                prefix=tuple(tape[:n]);directory=out/'native'/one['name']/'captures'/str(n);entry=self.entries.setdefault(prefix,{})
                if entry:assert (directory/'frontier.f32').read_bytes()==self.vector(prefix),'unstable independent R frontier at a duplicate prefix'
                if n in one['state_positions'] and self.has_state(prefix):assert parse((directory/'sequence.bin').read_bytes(),list(range(n)),self.p)[0]==self.state(prefix),'unstable independent R state at a duplicate prefix'
                entry['frontier_file']=str(directory/'frontier.f32')
                if n in one['state_positions']:entry['sequence_file']=str(directory/'sequence.bin')

    def vector(self,prefix):
        entry=self.entries[tuple(prefix)]
        if 'frontier_file' in entry:return Path(entry['frontier_file']).read_bytes()
        if self.old is None:self.old=HistoricalChunks()
        container,row=entry['historical'];return self.old.read(container,row['frontier'])

    def state(self,prefix):
        entry=self.entries[tuple(prefix)]
        if 'sequence_file' in entry:return parse(Path(entry['sequence_file']).read_bytes(),list(range(len(prefix))),self.p)[0]
        if self.old is None:self.old=HistoricalChunks()
        container,row=entry['historical'];return self.old.read(container,row['active_kv'])

    def has_state(self,prefix):
        e=self.entries.get(tuple(prefix),{});return 'sequence_file' in e or 'historical' in e

    def fill(self,r,d):
        missing={tuple(u['prefix']) for u in d['vector_uses'] if tuple(u['prefix']) not in self.entries}
        states=[d['states'][0],d['states'][-1]]+([d['states'][1]] if r['cycles'] else [])
        missing_states={tuple(x['prefix']) for x in states if not self.has_state(x['prefix'])}
        if not missing and not missing_states:return []
        prompt=r['prompt_ids'];cases=[];covered=set()
        for i,cycle in enumerate(r['cycles']):
            batch=[cycle['seed']]+cycle['proposals'];uses=[u['prefix'] for u in d['vector_uses'] if u['key'].startswith('step'+str(i)+'/')]
            full=uses[-1];wanted=[len(x) for x in uses if tuple(x) in missing]
            wanted_states=[len(x) for x in missing_states if list(x)==full[:len(x)] and len(x)>len(prompt)]
            wanted=sorted(set(wanted+wanted_states))
            if not wanted:continue
            suffix=full[len(prompt):];name='path'+str(i)
            cases.append(dict(name=name,forced=[dict(ids=prompt,phase='PREFILL',all=False),dict(ids=suffix,phase='FORCED',all=False)],observe_positions=wanted,state_positions=wanted_states));covered.update(tuple(full[:n]) for n in wanted)
        assert missing|missing_states<=covered,'teacher paths do not cover required prefixes'
        outputs=[]
        for start in range(0,len(cases),12):
            group=cases[start:start+12];fingerprint=hashlib.sha256(json.dumps(group,sort_keys=True).encode()).hexdigest()[:16]
            label=f'{self.family}-teacher-r{self.ix}-{fingerprint}';rows=sum(sum(len(c['ids']) for c in one['forced']) for one in group)
            out=finished(label,VERSIONS['R-'+self.family],self.family,dict(lowering='SIMPLE',cases=group),dict(requests=len(group),token_rows=rows,operators=0));self.add_teacher(out);outputs.append(str(out));dedup()
        return outputs

def qualify(family,arm):
    out=ROOT/'runs'/(family+'-'+arm+'-development');free_root=ROOT/'runs'/(family+'-old-free')/'native';rows=[]
    for ix,input in enumerate(roots(family)):
        base=out/'native'/f'r{ix}-heavy';r=json.loads((base/'receipt.json').read_bytes());clean=json.loads((out/'native'/f'r{ix}-clean/receipt.json').read_bytes());bank=Bank(family,ix,free_root/f'r{ix}-heavy')
        r['study_cap']=input['cap'];_,d=trace_from_row(r,r['prompt_ids'],bank.meta['vocab'],bank.meta['eog_ids'],'rtx')
        teacher=bank.fill(r,d);vectors=[]
        for use in d['vector_uses']:
            key=use['key']
            if key=='initial':name='initial'
            elif r['draft_enabled']:name='verify-'+key[4:].replace('/','-')
            else:name='ordinary-'+str(int(key[4:].split('/')[0])+1)
            raw=(base/'target'/(name+'.f32')).read_bytes();reference=bank.vector(use['prefix'])
            vectors.append(dict(key=key,position=len(use['prefix']),equal=raw==reference,sha256=hashlib.sha256(raw).hexdigest(),reference_sha256=hashlib.sha256(reference).hexdigest()))
        states=[]
        selected=[('initial',d['states'][0]),('terminal',d['states'][-1])]
        if r['cycles']:selected.insert(1,('commit-0',d['states'][1]))
        for key,s in selected:
            prefix=s['prefix'];directory=base/'target/state'/key;actual,_=parse((directory/'sequence.bin').read_bytes(),list(range(len(prefix))),bank.p);reference=bank.state(prefix)
            states.append(dict(key=key,position=len(prefix),active_KV_equal=actual==reference,frontier_equal=(directory/'frontier.f32').read_bytes()==bank.vector(prefix),unmaterialized_suffix=s['unmaterialized_suffix'],next_pending=s['next_pending'],terminal=s['terminal']))
        api=clean['observed_API_calls_within_service'];zero_online=all(v==0 for v in api.values())
        row=dict(root=input['id'],endpoint_equal=r['endpoint']==bank.endpoint,heavy_clean_endpoint_equal=r['endpoint']==clean['endpoint'],independent_trace_valid=True,full_requested_vectors=vectors,selected_committed_states=states,online_API_calls=api,zero_online_transition_state_work=zero_online,additional_original_R_teacher_jobs=teacher,historical_GPU_bank_reused=family=='Qwen')
        row['passed']=row['endpoint_equal'] and row['heavy_clean_endpoint_equal'] and zero_online and all(x['equal'] for x in vectors) and all(x['active_KV_equal'] and x['frontier_equal'] for x in states);rows.append(row)
    result=dict(family=family,arm=arm,roots=rows,passed=all(x['passed'] for x in rows),state_observation_scope=['initial','first speculative commit when present','terminal'],all_original_requested_vectors_including_unaccepted_paths=True,reference_processes_separate=True,finite_scope_only=True)
    path=ROOT/(family+'-'+arm+'-QUALIFICATION.json')
    if path.exists():assert json.loads(path.read_bytes())==result
    else:put(path,result)
    print(family,arm,'qualification',result['passed'],flush=True);assert result['passed'],'retained numerical/lifecycle failure'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family');p.add_argument('arm');a=p.parse_args();qualify(a.family,a.arm)
