"""Independently reconstruct greedy transactions; never trust candidate length/history."""
from __future__ import annotations
from common import need,digest

def reconstruct(t:dict)->dict:
    prompt=t['prompt_ids'];cap=t['cap'];vocab=t['vocab']
    need(type(cap) is int and cap>0 and type(vocab) is int and vocab>1,'cap/vocab')
    def token(x):need(type(x) is int and 0<=x<vocab,'token outside vocabulary');return x
    need(isinstance(prompt,list) and prompt,'empty prompt')
    for x in prompt:token(x)
    eog=set(t['eog_ids'])
    for x in eog:token(x)
    emitted=[];done=False;states=[];uses=[];materialized=list(prompt);pending=None
    def commit(x):
        nonlocal done
        token(x);need(not done,'commit after stop');emitted.append(x)
        done=x in eog or len(emitted)==cap
    def state(kind):
        n=len(materialized)-len(prompt)
        need(0<=n<=len(emitted),'invalid committed length')
        need(materialized==prompt+emitted[:n],'committed prefix not derivable from output')
        suffix=emitted[n:];need(len(suffix)<=1,'more than one unmaterialized output')
        states.append({'index':len(states),'prefix':list(materialized),
            'prefix_sha256':digest(materialized),'unmaterialized_suffix':list(suffix),
            'next_pending':None if done else (suffix[0] if suffix else None),
            'terminal':done,'branch':kind,'output_count':len(emitted)})
    initial=token(t['initial']);uses.append({'prefix':list(prompt),'decision':initial,'key':'initial'})
    commit(initial);pending=initial;state('initial')
    for i,s in enumerate(t['steps']):
        need(not done,'extra step after independent stop')
        need(s['base']==len(materialized),'wrong physical/semantic base')
        need(s['seed']==pending,'wrong pending seed')
        if s['kind']=='ordinary':
            materialized.append(pending);decision=token(s['decision'])
            uses.append({'prefix':list(materialized),'decision':decision,'key':f'step{i}/0'})
            commit(decision);pending=decision;state('ordinary');continue
        need(s['kind']=='verify','unknown transaction')
        ps=s['proposals'];ds=s['decisions'];k=t['k']
        need(type(k) is int and k>0 and len(ps)==k and len(ds)==k+1,'verification widths')
        for x in ps+ds:token(x)
        before=list(materialized);batch=[pending]+ps
        for j,d in enumerate(ds):uses.append({'prefix':before+batch[:j+1], 'decision':d,'key':f'step{i}/{j}'})
        accepted=0;branch=''
        for j in range(k):
            if done:break
            if ds[j]==ps[j]:accepted+=1;commit(ps[j]);branch='accepted'
            else:pending=ds[j];commit(pending);branch='correction';break
        if accepted==k and not done:
            pending=ds[k];commit(pending);branch='bonus'
        materialized=before+batch[:1+accepted]
        if 'accepted' in s:need(s['accepted']==accepted,'false accepted count')
        state(branch)
    need(done,'premature termination before cap/native EOG')
    return {'tokens':emitted,'stop_reason':'EOG' if emitted[-1] in eog else 'CAP',
            'states':states,'vector_uses':uses}
