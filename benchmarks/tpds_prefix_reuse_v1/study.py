"""Offline planning and report-level analysis; NEVER launches a native process.

Input tokenization, physical allocator observations, immutable references and full
raw-vector qualification must be provided by the original GPU hosts. A successful
call to this module is not a certificate for those external observations.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
from typing import Any

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / 'study.json').read_text(encoding='utf-8'))
ARMS = tuple(CFG['arms'])
FIXED = ARMS[:3]
WILLIAMS = ((0,1,3,2),(1,2,0,3),(2,3,1,0),(3,0,2,1))
HEX = re.compile(r'^[0-9a-f]{64}$')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(value: Any) -> str:
    """Canonical JSON SHA256, independent of whitespace, with NaN forbidden."""
    body = json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(body).hexdigest()


def integer(x: Any, name: str, lo: int = 0, hi: int = 1_000_000) -> int:
    require(type(x) is int and lo <= x <= hi, f'{name}: bounded integer required')
    return x


def sha(x: Any, name: str) -> str:
    require(isinstance(x, str) and bool(HEX.fullmatch(x)), f'{name}: SHA256 required')
    return x


def lcp(a: list[int], b: list[int]) -> int:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def groups(head: int, rows: int, padding: int = 256,
           capacity: int = 4096) -> list[int]:
    """Dense append lengths by scalar physical extent; not a GPU planner."""
    integer(head, 'head'); integer(rows, 'rows', 1)
    integer(padding, 'padding', 1); integer(capacity, 'capacity', 1)
    require(head + rows <= capacity, 'append exceeds capacity')
    ext = [min(capacity, padding * ((head+i)//padding+1)) for i in range(rows)]
    runs: list[int] = []
    for i, value in enumerate(ext):
        if i == 0 or value != ext[i-1]: runs.append(1)
        else: runs[-1] += 1
    return runs


def plan(head: int, count: int, arm: str, *, width: int = 32,
         padding: int = 256, capacity: int = 4096) -> list[dict[str, Any]]:
    integer(count, 'count', 1); integer(width, 'width', 1, 32)
    require(arm in FIXED, 'fixed policy required')
    integer(head, 'head'); require(head+count <= capacity, 'capacity overflow')
    calls: list[dict[str, Any]] = []
    at = head
    end = head+count
    while at < end:
        n = min(width, end-at)
        sub = groups(at, n, padding, capacity)
        if arm == 'QB':
            calls.append({'head':at, 'width':n, 'attention_groups':sub})
            at += n
        elif arm == 'WB-cut':
            for w in sub:
                calls.append({'head':at, 'width':w, 'attention_groups':[w]})
                at += w
        else:
            # Consume only the first physical run, then recompute a full-width
            # caller from the new head. Do not finish the old chunk remainder.
            w = sub[0]
            calls.append({'head':at, 'width':w, 'attention_groups':[w]})
            at += w
    require(sum(x['width'] for x in calls) == count, 'work not conserved')
    return calls


def inspect_manifest(m: dict[str, Any]) -> dict[str, Any]:
    require(m.get('schema_version') == 1, 'unsupported input schema')
    require(m.get('native_tokenization') is True, 'native tokenization not declared')
    require(m.get('corpus_revision') == CFG['corpus_revision'], 'wrong corpus revision')
    for k in ('tokenizer_sha256','template_sha256','exposure_audit_sha256'):
        sha(m.get(k), k)
    require(isinstance(m.get('deployment_id'),str) and m['deployment_id'], 'deployment missing')
    C=integer(m.get('capacity'), 'capacity', 1)
    P=integer(m.get('padding'), 'padding', 1)
    G=integer(m.get('cache_granule'), 'cache granule', 1)
    require(m.get('qmax') == 32 and m.get('output_cap') == 128, 'unregistered qmax/cap')
    policy=m.get('reuse_policy')
    require(policy in ('floor_lcp','exact_lcp'), 'unreviewed cache reuse policy')
    require(policy != 'exact_lcp' or G == 1, 'exact_lcp requires granule1')
    require(isinstance(m.get('rows'),list) and len(m['rows']) <= 1_000_000, 'rows missing/too large')
    eligible=[]; rejected=[]; seen=set()
    for r in m['rows']:
        require(isinstance(r,dict), 'input row is not an object')
        for k in ('id','root_id'):
            require(isinstance(r.get(k),str) and r[k], f'{k}: identity missing')
        require(r['id'] not in seen, 'duplicate input id'); seen.add(r['id'])
        require(not any(k in r for k in ('latency','seconds','answer','target_output','score')), 'outcome field in selection input')
        sha(r.get('source_sha256'), 'source hash')
        require(type(r.get('history_exposed')) is bool, 'exposure state missing')
        if r['history_exposed']:
            rejected.append({'id':r['id'],'reason':'historical exposure'}); continue
        for k in ('cached_ids','request_ids'):
            require(isinstance(r.get(k),list) and 0<len(r[k])<=100_000, f'{k}: bounded token list required')
            for t in r[k]: integer(t, 'token', 0, 2**31-1)
        common=lcp(r['cached_ids'],r['request_ids'])
        H=common if policy=='exact_lcp' else common//G*G
        require(r.get('effective_head') == H, 'effective head differs from declared cache policy')
        require(type(r.get('effective_head')) is int, 'effective head type')
        require(r.get('native_dense_verified') is True and type(r.get('physical_head')) is int
                and r['physical_head']==H, 'native dense physical-head evidence missing')
        L=len(r['request_ids'])
        reason = ('no reusable prefix' if H==0 else 'no appended work' if L<=H
                  else 'prompt plus cap exceeds capacity' if L+128>C else None)
        if reason:
            rejected.append({'id':r['id'],'reason':reason}); continue
        plans={a:plan(H,L-H,a,padding=P,capacity=C) for a in FIXED}
        qb=plans['QB']; extra=len(plans['WB-cut'])-len(qb)
        crossed=sum(len(x['attention_groups'])>1 for x in qb)
        density=extra/len(qb)
        z={k:r[k] for k in ('id','root_id','source_sha256')}
        z.update(logical_lcp=common,effective_head=H,physical_head=H,
                 prompt_tokens=L,append_tokens=L-H,
                 request_token_sha256=digest(r['request_ids']),
                 cached_token_sha256=digest(r['cached_ids']),
                 calls={a:len(v) for a,v in plans.items()},crossed_qb_calls=crossed,
                 wb_extra_call_density=density,
                 selection_bin='zero' if extra==0 else 'low' if density<=.125 else 'high')
        eligible.append(z)
    total_calls=sum(r['calls']['QB'] for r in eligible)
    return {'status':'DESCRIPTOR_CENSUS_ONLY','manifest_sha256':digest(m),
            'deployment_id':m['deployment_id'],'capacity':C,'padding':P,'cache_granule':G,
            'reuse_policy':policy,'rows_seen':len(m['rows']),'eligible':eligible,'rejected':rejected,
            'eligible_roots':len({r['root_id'] for r in eligible}),
            'crossed_requests':sum(r['crossed_qb_calls']>0 for r in eligible),
            'qb_calls':total_calls,
            'crossed_call_fraction':sum(r['crossed_qb_calls'] for r in eligible)/total_calls if total_calls else None,
            'warning':'Host declarations are checked for consistency, not independently certified as native observations.'}


def select(m: dict[str, Any]) -> dict[str, Any]:
    census=inspect_manifest(m); by=defaultdict(list)
    for r in census['eligible']: by[r['root_id']].append(r)
    seed=CFG['selection_seed']
    roots=sorted(by,key=lambda root:(digest([seed,'root',root]),root))
    ncal=CFG['calibration_roots'];ntest=CFG['test_roots']
    require(len(roots)>=ncal+ntest, 'insufficient eligible disjoint roots; do not silently shrink panel')
    chosen=[]
    for root in roots[:ncal+ntest]:
        chosen.append(min(by[root],key=lambda r:(digest([seed,'path',r['id']]),r['id'])))
    return {'schema_version':1,'status':'SELECTED_WITHOUT_MODEL_OUTPUT',
            'manifest_sha256':census['manifest_sha256'],'deployment_id':m['deployment_id'],
            'configuration':{k:m[k] for k in ('capacity','padding','cache_granule','reuse_policy','qmax','output_cap','tokenizer_sha256','template_sha256')},
            'calibration':chosen[:ncal],'test':chosen[ncal:],
            'census_summary':{k:v for k,v in census.items() if k not in ('eligible','rejected')},
            'rejections':census['rejected']}


def check_panel(p: dict[str, Any]) -> None:
    require(p.get('schema_version')==1, 'panel schema')
    sha(p.get('manifest_sha256'),'manifest')
    require(isinstance(p.get('deployment_id'),str) and p['deployment_id'], 'panel deployment')
    require(len(p.get('test',[]))==32 and len(p.get('calibration',[]))==12, 'panel sizes')
    rows=p['test']+p['calibration']
    require(len({r['id'] for r in rows})==44, 'duplicate selected id')
    require(len({r['root_id'] for r in rows})==44, 'root leakage/duplication')


def schedule(p: dict[str, Any]) -> dict[str, Any]:
    check_panel(p); rows=[]
    for sess in range(4):
        ordered=sorted(enumerate(p['test']),key=lambda x:digest([CFG['selection_seed'],'order',sess,x[1]['root_id']]))
        for block,(idx,r) in enumerate(ordered):
            for pos,a in enumerate(WILLIAMS[(sess+idx)%4]):
                for kind in ('warmup','measure'):
                    rows.append({'id':r['id'],'root_id':r['root_id'],'session':sess,
                                 'block':block,'position':pos,'arm':ARMS[a],'kind':kind})
    return {'schema_version':1,'stage':'main','panel_sha256':digest(p),
            'deployment_id':p['deployment_id'],'records':rows}


def quantile(xs: list[float], p: float) -> float:
    require(bool(xs) and 0<=p<=1, 'invalid quantile')
    ys=sorted(xs);z=(len(ys)-1)*p;i=int(z);f=z-i
    return ys[i]*(1-f)+ys[min(i+1,len(ys)-1)]*f


def analyze(r: dict[str, Any], panel: dict[str, Any], *, draws: int | None = None) -> dict[str, Any]:
    check_panel(panel)
    require(r.get('schema_version')==1 and r.get('stage')=='main','result schema/stage')
    require(r.get('deployment_id')==panel['deployment_id'],'deployment drift')
    require(r.get('panel_sha256')==digest(panel),'panel binding mismatch')
    for k in ('source_freeze_sha256','oracle_sha256','selector_sha256'):sha(r.get(k),k)
    planned=schedule(panel)['records']
    keys=lambda x:(x['id'],x['session'],x['arm'],x['kind'])
    expected={keys(x):x for x in planned}; found={}
    rows=r.get('records');require(isinstance(rows,list),'records missing')
    for x in rows:
        k=keys(x);require(k in expected and k not in found,'extra or duplicate slot')
        require(x.get('root_id')==expected[k]['root_id'],'root identity mismatch')
        integer(x.get('session'),'session',0,3)
        t=x.get('seconds')
        require(type(t) in (int,float) and math.isfinite(t) and t>0,'elapsed time is missing/nonpositive/nonfinite')
        require(x.get('qualified') is True,'unqualified slot: whole-panel qualified estimate withheld')
        for h in ('source_freeze_sha256','oracle_sha256'):
            require(x.get(h)==r[h],f'{h} drift')
        sha(x.get('actual_output_sha256'),'actual output');sha(x.get('expected_output_sha256'),'reference output')
        require(x['actual_output_sha256']==x['expected_output_sha256'],'endpoint hash mismatch')
        found[k]=x
    require(set(found)==set(expected),'incomplete panel: qualified aggregate withheld')
    for z in panel['test']:
        rid=z['id']; hashes={found[(rid,s,a,k)]['expected_output_sha256'] for s in range(4) for a in ARMS for k in ('warmup','measure')}
        require(len(hashes)==1,'reference output differs across arms/sessions for one input')
    n=len(panel['test']); byarm={a:[] for a in FIXED}; root_rows=[];session_effects={a:[] for a in FIXED}
    for z in panel['test']:
        rid=z['id'];v={}
        for a in FIXED:
            logs=[math.log(found[(rid,s,a,'measure')]['seconds']/found[(rid,s,'AUTO','measure')]['seconds']) for s in range(4)]
            v[a]=statistics.mean(logs);byarm[a].append(v[a])
        root_rows.append({'id':rid,'root_id':z['root_id'],'baseline_over_AUTO':{a:math.exp(v[a]) for a in FIXED}})
    for a in FIXED:
        for s in range(4):
            session_effects[a].append(math.exp(statistics.mean(math.log(found[(z['id'],s,a,'measure')]['seconds']/found[(z['id'],s,'AUTO','measure')]['seconds']) for z in panel['test'])))
    draws=CFG['bootstrap_draws'] if draws is None else integer(draws,'draws',100,1000000)
    rng=random.Random(CFG['bootstrap_seed']);boot={a:[] for a in FIXED}
    for _ in range(draws):
        indices=[rng.randrange(n) for _ in range(n)]
        for a in FIXED:boot[a].append(math.exp(sum(byarm[a][i] for i in indices)/n))
    alpha=CFG['family_alpha']/CFG['primary_comparisons']; contrasts=[]
    for a in FIXED:
        point=math.exp(statistics.mean(byarm[a]));ci=[quantile(boot[a],alpha/2),quantile(boot[a],1-alpha/2)]
        contrasts.append({'baseline':a,'baseline_over_AUTO':point,
                          'time_reduction_pct':100*(1-1/point),
                          'family95_bonferroni_interval':ci,
                          'secondary_unadjusted95_interval':[quantile(boot[a],.025),quantile(boot[a],.975)],
                          'session_ratios':session_effects[a],
                          'roots_favoring_AUTO':sum(v>0 for v in byarm[a]),
                          'worst_root_ratio':math.exp(min(byarm[a]))})
    point_vs_best=min(c['baseline_over_AUTO'] for c in contrasts)
    # The three complete contrasts share the same weights, so min baseline/AUTO
    # corresponds to the fastest fixed policy under this declared estimand.
    screen=all(c['family95_bonferroni_interval'][0]>1 for c in contrasts) and (1-1/point_vs_best)>=CFG['practical_time_reduction']
    descriptive={a:{} for a in ARMS}
    for a in ARMS:
        ts=[x['seconds'] for x in rows if x['arm']==a and x['kind']=='measure']
        descriptive[a]={'geometric_service_seconds':math.exp(statistics.mean(map(math.log,ts))),
                        'median_seconds':statistics.median(ts),'descriptive_p95_seconds':quantile(ts,.95)}
    return {'status':'COMPLETE_NORMALIZED_PANEL','scope':'Report-level consistency/statistics only; native raw-vector audit remains external.',
            'panel_sha256':digest(panel),'measured_requests':512,'warmups':512,'independent_roots':32,
            'bootstrap_draws':draws,'resampling_unit':'root with all four matched sessions and arms',
            'contrasts':contrasts,'root_results':root_rows,'descriptive_service':descriptive,
            'engineering_screen_pass':screen,'no_equivalence_test':True,
            'retained_all_slots':len(rows),'cross_platform_pooling':False}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['census','select','schedule','analyze'])
    parser.add_argument('input',type=Path);parser.add_argument('panel',nargs='?',type=Path)
    a=parser.parse_args(); obj=json.loads(a.input.read_text(encoding='utf-8'))
    if a.action=='analyze':
        require(a.panel is not None,'analyze requires a panel JSON')
        out=analyze(obj,json.loads(a.panel.read_text(encoding='utf-8')))
    else:out={'census':inspect_manifest,'select':select,'schedule':schedule}[a.action](obj)
    print(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False))

if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        raise SystemExit(f'REFUSED: {exc}')
