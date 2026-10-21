"""Offline evidence calculations. Source-bound host raw reconstruction is still required."""
import math
import struct
from pathlib import Path
from core import need, hash_ok, sha
from plan import ARMS, operator_cells, validate_plan


def choose_from_capabilities(census, binding_sha256):
    """Fixed pre-output rule; never consumes numerical results or elapsed times."""
    need(set(census)=={'binding_sha256','observations'},'capability-only schema')
    need(hash_ok(binding_sha256) and census['binding_sha256']==binding_sha256,'unbound backend census')
    expected={(sha(c),m) for c in operator_cells() for m in ('MQ','PQ','QH_C','QH_D','REPEAT4')}
    rows={}
    for row in census['observations']:
        need(set(row)=={'cell_sha256','mode','compute_nodes','raw_sha256'},'capability row fields')
        key=row['cell_sha256'],row['mode']; need(key in expected and key not in rows,'duplicate/unplanned capability')
        need(hash_ok(row['raw_sha256']) and row['compute_nodes'],'missing source/node list')
        names=set(); ok=True
        for n in row['compute_nodes']:
            need(set(n)=={'id','op','supports_op'},'node capability fields')
            need(n['id'] not in names and n['op'],'duplicate/empty node');names.add(n['id'])
            need(type(n['supports_op']) is bool,'one necessary predicate or unknown is not full supports_op')
            ok &= n['supports_op']
        rows[key]=ok
    need(set(rows)==expected,'incomplete capability grid')
    if not all(rows[sha(c),m] for c in operator_cells() for m in ('MQ','PQ')):
        return 'STOP_REFERENCE_BACKEND_NOT_ADMITTED'
    for m in ('QH_C','QH_D'):
        if all(rows[sha(c),m] for c in operator_cells()):return m
    return 'STOP_NO_SUPPORTED_CANDIDATE'


def compare_f32(left, right):
    """Same-input CPU file comparison. No tolerance chosen from results."""
    a=Path(left).read_bytes();b=Path(right).read_bytes()
    need(len(a)==len(b) and len(a)>0 and len(a)%4==0 and len(a)<=64*1024**2,'full-vector size contract')
    maxabs=0.;maxulp=0;nonfinite=0;different=0
    def order(x,bits):
        magnitude=bits & 0x7fffffff
        return 0x80000000-magnitude if bits>>31 else 0x80000000+magnitude
    for offset in range(0,len(a),4):
        aa=a[offset:offset+4];bb=b[offset:offset+4];different+=aa!=bb
        x=struct.unpack('<f',aa)[0];y=struct.unpack('<f',bb)[0]
        if not math.isfinite(x) or not math.isfinite(y):nonfinite+=1;continue
        maxabs=max(maxabs,abs(x-y))
        u=struct.unpack('<I',aa)[0];v=struct.unpack('<I',bb)[0]
        maxulp=max(maxulp,abs(order(x,u)-order(y,v)))
    return dict(elements=len(a)//4,bitwise_equal=a==b,bit_mismatches=different,
                max_abs_finite=maxabs,max_ulp_finite=maxulp,nonfinite_pairs=nonfinite,
                scope='file arithmetic only; input/placement qualification separate')


def endpoint(e):
    need(set(e)=={'ids','eog','cap','stop'},'full endpoint fields')
    ids=e['ids']; flags=e['eog']
    need(e['cap']==128 and type(ids) is list and 0<len(ids)<=128,'registered window')
    need(all(type(i) is int and 0<=i<128256 for i in ids),'native token IDs')
    need(type(flags) is list and all(type(f) is bool for f in flags),'flags')
    need(flags==[i in (128001,128008,128009) for i in ids] and not any(flags[:-1]),'EOG contract')
    need(e['stop']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128),'stop/cap')
    return e


def time_gate(s):
    if type(s) is not list or len(s)!=3:return False
    s=sorted(s,key=lambda x:x['id'])
    if [x['id'] for x in s]!=[0,1,2]:return False
    if not all(type(x[k]) in (float,int) and math.isfinite(x[k]) for x in s for k in ('start','end')):return False
    return all(x['end']>=x['start'] for x in s) and s[1]['start']>=s[0]['end']+3600 and s[2]['start']>=max(s[0]['start']+86400,s[1]['end'])


def summarize(plan, records, sessions, allow_synthetic=False):
    """Normalized full panel only. Does not claim independent raw semantic auditing."""
    validate_plan(plan)
    need(plan['phase']=='confirm','confirmation plan')
    expected={x['id']:x for x in plan['slots']};seen={};values={};invalid=[];failed=[];groups={}
    need(len(expected)==1008,'plan inventory')
    for r in records:
        need(r['slot'] in expected and r['slot'] not in seen,'unknown/duplicate slot')
        s=expected[r['slot']];seen[r['slot']]=r
        if r['status']!='COMPLETED':failed.append(r['slot']);continue
        try:
            need(allow_synthetic or r['origin']=='NATIVE','synthetic cannot become native evidence')
            need(r['request_sha256']==sha(s),'actual request-plan mismatch')
            need(hash_ok(r['raw_audit_sha256']),'missing raw audit link')
            need(r['channel']=='counts' and r['warmup'] is s['warmup'],'observer channel')
            need(r['runtime_role']==('original' if s['arm']=='R' else 'candidate'),'reference runtime mismatch')
            need(r['process_group']==s['process_group'] and r['fresh_state'] is True,'ownership/reset')
            t=r['wall_ms'];need(type(t) in (int,float) and math.isfinite(t) and t>0,'invalid cost')
            endpoint(r['endpoint'])
            groups.setdefault(s['process_group'],[]).append((s,r))
            if not s['warmup']:values[s['session'],s['task'],s['arm']]=r
        except (ValueError,KeyError,TypeError) as e:invalid.append(dict(slot=r['slot'],error=str(e)))
    missing=sorted(set(expected)-set(seen)); linkage=[];drift=set()
    for gid,pair in groups.items():
        if len(pair)!=2:linkage.append(gid);continue
        (sa,ra),(sb,rb)=sorted(pair,key=lambda x:not x[0]['warmup'])
        if sa['warmup'] is not True or sb['warmup'] is not False or ra['lifecycle_id']!=rb['lifecycle_id']:linkage.append(gid)
        if ra['endpoint']!=rb['endpoint']:drift.add(sa['arm'])
    complete=not(missing or failed or invalid or linkage) and time_gate(sessions)
    tasks=sorted({s['task'] for s in plan['slots']});refs={};refbad=[]
    for t in tasks:
        v=[values[k,t,'R']['endpoint'] for k in range(3) if (k,t,'R') in values]
        if len(v)==3 and all(x==v[0] for x in v) and 'R' not in drift:refs[t]=v[0]
        else:refbad.append(t)
    answers={}
    for arm in ARMS:
        bad=[]; logs=[];totalr=0.;totalc=0;rows=[]
        for k in range(3):
            ll=[]
            for t in tasks:
                r=values.get((k,t,'R'));c=values.get((k,t,arm))
                if not r or not c or t not in refs:bad.append((k,t,'MISSING_REFERENCE_OR_RECORD'));continue
                if c['endpoint']!=refs[t]:bad.append((k,t,'ENDPOINT_COUNTEREXAMPLE'));continue
                rr=r['wall_ms']/c['wall_ms'];ll.append(math.log(rr));totalr+=r['wall_ms'];totalc+=c['wall_ms']
                rows.append(dict(session=k,task=t,ratio=rr))
            logs.append(sum(ll)/len(ll) if len(ll)==24 else None)
        ok=complete and not bad and not refbad and arm not in drift
        answers[arm]=dict(qualified=ok,failures=bad,per_session_logs=logs,task_ratios=rows,
            ratio=math.exp(sum(logs)/3) if ok else None,total_cost_ratio=totalr/totalc if ok else None,
            regression_coordinates=sum(x['ratio']<1 for x in rows),interval=None)
    meta={s['task']:(s['domain'],s['length_bin']) for s in plan['slots']}
    for arm,a in answers.items():
        a['observed_matching_pairs']=len(a['task_ratios']);a['planned_pairs']=72
        a['strata']={}
        for domain in ('code','math'):
            for b in (0,1,2):
                rr=[x['ratio'] for x in a['task_ratios'] if meta[x['task']]==(domain,b)]
                a['strata'][f'{domain}/bin{b}']=dict(planned_pairs=12,matching_pairs=len(rr),
                    ratio=math.exp(sum(map(math.log,rr))/12) if a['qualified'] and len(rr)==12 else None,
                    regression_coordinates=sum(v<1 for v in rr))
    pairs={}
    for left,right in (('C_R_PQ','C_R_QH'),('C_B_PQ','C_B_QH'),('M_R','C_R_QH'),('M_B','C_B_QH'),('C_B_QH','C_R_QH')):
        ok=answers[left]['qualified'] and answers[right]['qualified'];ratios=[]
        if ok:
            for k in range(3):
                for t in tasks:ratios.append(values[k,t,left]['wall_ms']/values[k,t,right]['wall_ms'])
        pairs[left+'/'+right]=dict(qualified=ok,ratio=math.exp(sum(map(math.log,ratios))/len(ratios)) if ok else None,
                                      regression_coordinates=sum(v<1 for v in ratios))
    return dict(complete=complete,missing=missing,failed=failed,invalid=invalid,process_link_errors=linkage,
                reference_instability=refbad,within_process_drift=sorted(drift),arms=answers,pairs=pairs,
                scope='SYNTHETIC_TEST_ONLY' if allow_synthetic else 'NORMALIZED_RECORDS_REQUIRE_INDEPENDENT_RAW_AUDIT',
                generalization='24 texts; one model; three sessions on two date blocks; no request-level CI')
