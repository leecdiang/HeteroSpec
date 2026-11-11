#!/usr/bin/env python3
"""Standard-library recomputation of the V4 reviewer projection; no models."""
import collections, hashlib, json, math, random, statistics

A_CONDITIONS = ('A_REFERENCE_UB1', 'A_TARGET_ONLY_UB2', 'A_H2_P_R', 'A_R_ONLY', 'A_NATIVE_BATCHED_LIVE')
B_CONDITIONS = ('B_TARGET_REFERENCE_UB1', 'B_BATCHED_K2_UB2', 'B_SERIALIZED_K2_UB1')
EXPECTED_TASKS = [143,31,25,81,15,141,142,18,136,99,148,140,87,76,26,49,40,109,66]

def digest_ids(ids):
    return hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest()

def quantile(values, q):
    a = sorted(values); p = (len(a)-1)*q; i = int(p); j = math.ceil(p)
    return a[i] + (a[j]-a[i])*(p-i)

def first_difference(a, b):
    for i in range(max(len(a), len(b))):
        if i >= len(a) or i >= len(b) or a[i] != b[i]:
            return {'index': i, 'left_id': a[i] if i < len(a) else None, 'right_id': b[i] if i < len(b) else None}
    return None

def validate(data):
    tasks = data['tasks']; assert tasks == ['HumanEval/'+str(i) for i in EXPECTED_TASKS]
    sel = data['selection']; excluded = sel['excluded']; eligible = sel['eligible']
    universe = {'HumanEval/'+str(i) for i in range(164)}
    assert len(excluded) == len(set(excluded)) == 145 and len(eligible) == 19
    assert set(eligible) == set(tasks) and set(excluded).isdisjoint(eligible)
    assert set(excluded) | set(eligible) == universe
    assert set(sel['v3_newly_exposed']) == {'HumanEval/'+str(i) for i in (2,16,59,86,157,158,161)}
    assert set(sel['v3_newly_exposed']).issubset(excluded)
    assert tasks == sorted(eligible, key=lambda t: hashlib.sha256((sel['salt']+t).encode()).hexdigest())
    assert data['formal_counts'] == {'A_pre_live':228, 'A_live':57, 'B':171, 'total':456, 'independent_prompts':19}
    eog = set(data['eog_ids']); assert eog == {128247,151643,151645,151662,151663,151664}
    def endpoint(row):
        ids = row['ids']; assert ids and len(ids) <= 128 and all(type(x) is int and x >= 0 for x in ids)
        assert digest_ids(ids) == row['ids_sha256']
        assert not any(x in eog for x in ids[:-1])
        assert row['termination'] in ('EOS','limit')
        assert (row['termination'] == 'EOS' and ids[-1] in eog) or (row['termination'] == 'limit' and len(ids) == 128)
        return ids
    rows = data['A']; assert len(rows) == 57
    pairs = {(r['task_id'],r['repetition']) for r in rows}; expected_pairs = {(t,k) for t in tasks for k in (1,2,3)}
    assert pairs == expected_pairs and len(pairs) == len(rows)
    a_by = {(r['task_id'],r['repetition']):r['conditions'] for r in rows}
    endpoints = collections.defaultdict(collections.Counter)
    for r in rows:
        assert set(r['conditions']) == set(A_CONDITIONS)
        for c,v in r['conditions'].items(): endpoint(v); endpoints[c][v['termination']] += 1
    for t in tasks:
        for c in A_CONDITIONS: assert all(a_by[t,k][c]['ids'] == a_by[t,1][c]['ids'] for k in (2,3))
    a_results = {}
    for label,left,right,n in [('UB2_live',A_CONDITIONS[1],A_CONDITIONS[4],51),('H2_live',A_CONDITIONS[2],A_CONDITIONS[4],57),('R_ONLY_live',A_CONDITIONS[3],A_CONDITIONS[4],57),('reference_live',A_CONDITIONS[0],A_CONDITIONS[4],51),('H2_R_ONLY',A_CONDITIONS[2],A_CONDITIONS[3],57)]:
        diffs = [{'task_id':t,'repetition':k,'first_divergence':first_difference(a_by[t,k][left]['ids'],a_by[t,k][right]['ids'])} for t in tasks for k in (1,2,3)]
        count = sum(x['first_divergence'] is None for x in diffs); assert count == n
        failed = sorted({x['task_id'] for x in diffs if x['first_divergence'] is not None})
        a_results[label] = {'pairs':count,'total':57,'failed_tasks':failed,'first_divergences':[x for x in diffs if x['first_divergence'] is not None]}
    assert a_results['UB2_live']['failed_tasks'] == ['HumanEval/15','HumanEval/25']
    assert a_results['reference_live']['failed_tasks'] == ['HumanEval/15','HumanEval/18']
    b = data['B']; assert len(b) == 171
    b_by = {(r['task_id'],r['repetition'],r['condition']):r for r in b}
    assert len(b_by) == len(b) and set(b_by) == {(t,k,c) for t,k in expected_pairs for c in B_CONDITIONS}
    for r in b:
        ids = endpoint(r); timer = r['timer']; ticks = timer['qpc_delta']; freq = timer['frequency']
        assert type(ticks) is int and ticks > 0 and type(freq) is int and freq > 0
        ms = ticks*1000/freq; secondary = timer['steady_delta_ns']/1e6
        assert ms == timer['milliseconds'] and secondary == timer['secondary_milliseconds']
        assert abs(ms-secondary) <= max(.020, .001*ms)
        assert timer['count'] == len(ids) and timer['terminal_id'] == ids[-1]
    for t in tasks:
        for c in B_CONDITIONS: assert all(b_by[t,k,c]['ids'] == b_by[t,1,c]['ids'] for k in (2,3))
    schedule = data['schedule']; assert len(schedule) == 57
    positions = {c:collections.Counter() for c in B_CONDITIONS}; reached=set()
    for block in schedule:
        t=block['task_id']; k=block['repetition']; reached.add((t,k)); order=block['order']
        assert len(order) == len(set(order)) == 3 and set(order) == set(B_CONDITIONS)
        for i,c in enumerate(order): positions[c][i]+=1
    assert reached == expected_pairs and all(dict(v)=={0:19,1:19,2:19} for v in positions.values())
    medians = {t:{c:statistics.median(b_by[t,k,c]['timer']['milliseconds'] for k in (1,2,3)) for c in B_CONDITIONS} for t in tasks}
    result = {}
    for c,n in [(B_CONDITIONS[1],51),(B_CONDITIONS[2],57)]:
        count=sum(b_by[t,k,B_CONDITIONS[0]]['ids']==b_by[t,k,c]['ids'] for t,k in expected_pairs); assert count == n
        reported=data['reported_B'][c]
        if count<57:
            assert reported['status']=='BLOCKED' and all(reported[x] is None for x in ('speedup','CI','prompt_ratios'))
            result[c]={'pairs':count,'status':'BLOCKED','speedup':None,'CI':None};continue
        logs=[math.log(medians[t][B_CONDITIONS[0]]/medians[t][c]) for t in tasks]
        gm=math.exp(math.fsum(logs)/len(tasks)); rng=random.Random(2026100204)
        boot=[math.exp(math.fsum(logs[rng.randrange(19)] for _ in tasks)/19) for _ in range(10000)]
        ci=[quantile(boot,p) for p in (.025,.975)]
        assert reported['status']=='QUALIFIED' and abs(gm-reported['speedup'])<1e-14
        assert all(abs(x-y)<1e-14 for x,y in zip(ci,reported['CI']))
        assert sum(medians[t][B_CONDITIONS[0]]/medians[t][c]>1 for t in tasks)==0
        result[c]={'pairs':count,'status':'QUALIFIED','speedup':gm,'CI':ci,'faster_prompts':0}
    return {'A':a_results,'A_endpoint_counts':{k:dict(v) for k,v in endpoints.items()},'B':result,'B_prompt_medians_ms':medians,'independent_prompts':19,'formal_conditions':456}
