"""Strict raw-byte checks of the pre-bound reference bank and8 heavy requests."""
from pathlib import Path
import collections
from common import HERE,RUNTIME,read,put,sha,canonical,reader_class

class Check:
    def __init__(self):
        self.reader=reader_class()();self.coverage=read(HERE/'REFERENCE_COVERAGE.json');self.plan=read(HERE/'EXECUTION_PLAN.json');self.bank={};self.statebank={};self.counts=collections.Counter()
    def bank_ready(self,publish=True):
        meta=read(RUNTIME/'runs'/self.plan['jobs'][0]['id']/'native/result.json');self.eog=set(meta['eog_ids']);assert meta['vocab']==151936
        for m in self.coverage['vector_map']:
            key=tuple(m['prefix_ids']);p=RUNTIME/'runs'/m['job']/'native'/m['vector_relative'];self.bank[key]=p;self.reader.vector(p)
        for m in self.coverage['state_map']:
            key=tuple(m['prefix_ids']);p=RUNTIME/'runs'/m['job']/'native'/m['state_relative'];self.statebank[key]=p;self.reader.state(p,len(key))
        assert len(self.bank)==257 and len(self.statebank)==40
        expected=self.coverage['old_trace_bindings'][0]['old_clean_endpoint']['ids'];prompt=self.plan['root']['prompt_ids'];greedy=0
        for i,token in enumerate(expected):
            prefix=tuple(prompt+expected[:i])
            if prefix in self.bank:assert self.reader.vector(self.bank[prefix])['greedy']==token;greedy+=1
        assert greedy==len(expected),'All original greedy endpoint decisions require pre-bound R vectors'
        proof=dict(passed=True,full_R_vectors=257,active_R_states=40,greedy_endpoint_decisions=greedy,
            expected_endpoint_checked_from_independent_R_vectors=True,reference_expected_floats_from_candidate=False,
            numerical_tolerance='All-byte SHA256 equality; active dense F16 only; finite full151936-F32 outputs',raw_files=self.reader.seen)
        if publish:put(RUNTIME/'REFERENCE_BANK_COMPLETE.json',proof)
        return proof
    def vector(self,p,prefix):
        ref=self.bank[tuple(prefix)];a=self.reader.vector(p);b=self.reader.vector(ref)
        assert a['sha256']==b['sha256'],('FULL_VECTOR_MISMATCH',str(p),str(ref));self.counts['full_vector_comparisons']+=1
        return dict(actual=str(p),reference=str(ref),sha256=a['sha256'],prefix=len(prefix)),a['greedy']
    def state(self,p,prefix):
        ref=self.statebank[tuple(prefix)];a=self.reader.state(p,len(prefix));b=self.reader.state(ref,len(prefix))
        assert a['active_sha256']==b['active_sha256'],('ACTIVE_KV_MISMATCH',str(p),str(ref));self.counts['active_KV_comparisons']+=1
        return dict(actual=str(p),reference=str(ref),active_sha256=a['active_sha256'],positions=len(prefix),active_bytes=a['active_bytes'])
    def candidate(self,j,publish=True):
        binding=next(x for x in self.coverage['old_trace_bindings'] if x['job']==j['id']);p=RUNTIME/'runs'/j['id']/'native/boundary-natural-heavy';r=read(p/'receipt.json');x=j['job']['inputs'][0]['input'];k=j['job']['k']
        assert r['capture'] and r['target_output_reserve']==8 and r['draft_ubatch']==4 and r['proposal_mode']=='live'
        assert r['endpoint']==binding['old_clean_endpoint'] and r['cycles']==binding['expected_cycles'],'FROZEN_TRACE_CHANGED: stop without expanding reference inputs'
        assert r['executions']==binding['expected_executions']
        assert r['target_physical_width_hist']==binding['expected_target_hist'] and r['draft_physical_width_hist']==binding['expected_draft_hist']
        prefix=x['prompt_ids'].copy();vectors=[];states=[];proposals=[];out=[];pending=r['ids'][0]
        v,g=self.vector(p/'target/initial.f32',prefix);vectors.append(v);assert g==pending;out.append(pending);done=pending in self.eog or len(out)==x['cap']
        def snapshot(label):
            states.append(self.state(p/'target/state'/label/'sequence.bin',prefix));v,_=self.vector(p/'target/state'/label/'frontier.f32',prefix);vectors.append(v)
        snapshot('initial')
        boundary=[];physical=iter(e for e in r['executions'] if e['phase']=='VERIFY')
        for ci,c in enumerate(r['cycles']):
            assert not done and c['cycle']==ci and c['base']==len(prefix) and c['seed']==pending
            before=dict(min=0,max=len(prefix)-1);assert c['target_before']==c['draft_before']==before
            verify=[pending]+c['proposals'];decisions=[]
            for row in range(k+1):v,g=self.vector(p/'target'/f'verify-{ci}-{row}.f32',prefix+verify[:row+1]);vectors.append(v);decisions.append(g)
            assert decisions==c['decisions']
            for i,token in enumerate(c['proposals']):
                f=p/'draft'/f'proposal-{ci}-{i}.f32';a=self.reader.vector(f);assert a['greedy']==token;proposals.append(dict(path=str(f),sha256=a['sha256'],token=token))
            accepted=0;rejected=False;kind=None
            for token,decision in zip(c['proposals'],decisions):
                if done:break
                if token==decision:accepted+=1;emitted=token;kind='accepted'
                else:pending=decision;emitted=decision;rejected=True;kind='correction'
                out.append(emitted);done=emitted in self.eog or len(out)==x['cap']
                if rejected:break
            if accepted==k and not done:pending=decisions[k];out.append(pending);kind='bonus';done=pending in self.eog or len(out)==x['cap']
            prefix+=verify[:accepted+1];assert c['accepted']==accepted and c['rejected']==rejected and c['commit_kind']==kind
            assert c['keep']==len(prefix) and c['pending_after']==(None if done else pending) and c['done']==done and c['output_length']==len(out)
            assert c['target_after']==c['draft_after']==dict(min=0,max=len(prefix)-1)
            snapshot('commit-'+str(ci));n=0;masks=[];extents=[];groups=[]
            while n<k+1:
                e=next(physical);assert e['position']==c['base']+n;n+=e['width'];masks+=e['requested_rows'];extents+=e['expected_extents'];groups.append(e)
            assert n==k+1 and sorted(masks)==list(range(k+1))
            if j['job']['lowering']=='LOCAL':assert len(groups)==1 and groups[0]['width']==k+1
            if len(set(extents))>1:boundary.append(dict(cycle=ci,base=c['base'],accepted=accepted,rejected=rejected,keep=len(prefix),extents=extents))
        assert next(physical,None) is None and done and out==r['ids']
        assert r['eog']==[t in self.eog for t in out] and r['target_final_kv']==r['draft_final_kv']==dict(min=0,max=len(prefix)-1)
        snapshot('terminal')
        hist=dict(collections.Counter(str(e['width']) for e in r['executions']));assert hist==r['target_physical_width_hist']
        total=len(x['prompt_ids'])+(k+1)*len(r['cycles']);assert sum(int(w)*n for w,n in hist.items())==sum(int(w)*n for w,n in r['draft_physical_width_hist'].items())==total
        expected=[c for c in self.coverage['target_boundary_cycles'] if c['job']==j['id']];assert len(boundary)==len(expected) and any(c['rejected'] for c in boundary)
        graph=[g for g in r['geometry'] if g['phase']=='VERIFY' and g['op']=='MUL_MAT'];assert graph
        packed=[g for g in graph if g['name'].startswith('frontier_packed_')]
        if k==3:assert not packed
        if k==7 and '-packed-' in j['id']:assert packed and all(g['ne'][1:3]==[4,2] for g in packed)
        if k==7 and '-loop4-' in j['id']:assert any(g['name'].startswith('hs_backend_loop4_') for g in graph)
        self.counts['candidate_requests']+=1
        proof=dict(passed=True,job=j['id'],old_trace_equal=True,full_endpoint_equal=True,all_full_vectors=vectors,all_committed_target_states=states,
            all_draft_proposal_vectors=proposals,boundary_cycles=boundary,target_physical_hist=hist,
            service_seconds_cost_only=r['service_seconds'],receipt_sha256=sha(p/'receipt.json'),new_performance_measurement=False,
            scope='New heavy finite bridge for pre-exposed frozen trace; old clean KV not recovered; original performance statistics unchanged.')
        if publish:put(RUNTIME/'checks'/(j['id']+'.json'),proof)
        return proof
