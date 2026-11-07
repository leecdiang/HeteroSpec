"""CPU-only census of distinct caller schedules. Never launches a model.
Accept PR174 common-census.json, its old common-panel.json, and a separately
verified root-exclusion manifest. Select before new outputs or timing.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
from typing import Any
SEED = 'rtx-rechunk-discrimination-v1-20261104'
ARMS = ('QB', 'WB-cut', 'WB-rechunk')

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def plan(head: int, count: int, arm: str) -> list[list[int]]:
    if type(head) is not int or type(count) is not int or head<0 or count<1 or head+count+128>4096:
        raise ValueError('invalid C4096/cap128 geometry')
    if arm not in ARMS:raise ValueError('unknown fixed arm')
    at=head;end=head+count;out=[]
    while at<end:
        stop=min(at+32,end)
        if arm=='QB':out.append([at,stop-at]);at=stop;continue
        while at<stop:
            cut=min(stop,(at//256+1)*256)
            out.append([at,cut-at]);at=cut
            if arm=='WB-rechunk':break
    return out

def select(census: dict, prior: dict, exclusions: dict) -> dict:
    if (census.get('capacity'),census.get('padding'),census.get('cache_granule'))!=(4096,256,1):
        raise ValueError('keep the frozen exact-token C4096 deployment')
    if len(prior.get('calibration',[]))!=12 or len(prior.get('test',[]))!=32:
        raise ValueError('original 12/32 panel required')
    if not isinstance(exclusions.get('root_ids'),list) or not exclusions.get('evidence'):
        raise ValueError('root exclusion manifest and provenance required')
    blocked=set(exclusions['root_ids'])|{r['root_id'] for r in prior['calibration']+prior['test']}
    if not all(isinstance(x,str) and x for x in blocked):raise ValueError('invalid excluded root')
    rows=census.get('eligible');groups=defaultdict(list);seen=set();different=0
    if not isinstance(rows,list):raise ValueError('common-census eligible rows required')
    for r in rows:
        if any(k in r for k in ('seconds','latency','answer','target_output','score')):
            raise ValueError('outcome field in geometry input')
        if not all(isinstance(r.get(k),str) and r[k] for k in ('id','root_id')):raise ValueError('identity missing')
        if r['id'] in seen:raise ValueError('duplicate path')
        seen.add(r['id'])
        h=r.get('physical_head');n=r.get('append_tokens')
        if h!=r.get('effective_head') or type(h) is not int or h<1:raise ValueError('dense native head missing')
        if r.get('prompt_tokens')!=h+n:raise ValueError('prompt geometry mismatch')
        for k in ('request_token_sha256','cached_token_sha256','source_sha256'):
            v=r.get(k)
            if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v):raise ValueError('invalid source/token hash')
        paths={a:plan(h,n,a) for a in ARMS}
        delta=paths['WB-cut']!=paths['WB-rechunk'];different+=int(delta)
        clean={k:r[k] for k in ('id','root_id','source_sha256','physical_head','append_tokens','prompt_tokens','request_token_sha256','cached_token_sha256')}
        clean.update(plans=paths,rechunk_changes_schedule=delta)
        groups[r['root_id']].append(clean)
    # Select one natural path per root before conditioning on schedule difference.
    representatives=[min(rs,key=lambda r:(digest([SEED,'path',r['id']]),r['id'])) for rs in groups.values()]
    available=[r for r in representatives if r['root_id'] not in blocked]
    eligible=sorted((r for r in available if r['rechunk_changes_schedule']),key=lambda r:(digest([SEED,'root',r['root_id']]),r['root_id']))
    chosen=eligible[:8] if len(eligible)>=4 else []
    return {'status':'READY_FOR_NATIVE_QUALIFICATION' if chosen else 'STOP_NO_GPU',
            'scientific_scope':'conditional structural challenge, never a new population-average estimate',
            'selection_seed':SEED,'census_sha256':digest(census),'prior_panel_sha256':digest(prior),
            'exclusion_sha256':digest(exclusions),'paths_seen':len(rows),'roots_seen':len(groups),
            'paths_with_distinct_rechunk_schedule':different,
            'unexposed_root_representatives':len(available),
            'unexposed_representatives_with_distinct_schedule':len(eligible),
            'representative_rule':'one hash-ranked path/root BEFORE geometry conditioning',
            'selected':chosen,'planned_scientific_requests':20*len(chosen),
            'maximum_all_stage_requests':200 if chosen else 0,
            'native_deployment_and_exclusion_provenance_not_certified_by_this_script':True}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('census',type=Path);p.add_argument('prior_panel',type=Path);p.add_argument('exclusions',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    data=[json.loads(x.read_text(encoding='utf-8')) for x in (a.census,a.prior_panel,a.exclusions)]
    out=select(*data)
    with a.output.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(out['status'], 'selected=',len(out['selected']))
if __name__=='__main__':
    try:main()
    except (ValueError,TypeError,KeyError,OSError) as e:raise SystemExit('REFUSED: '+str(e))
