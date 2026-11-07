"""Saved-data-only exposure audit and schedule census; no native process."""
import hashlib,json,sys
from pathlib import Path
from collections import defaultdict,Counter
import coverage
HERE=Path(__file__).resolve().parent
OLD=Path('E:/rtx172');ROOT=Path('F:/rtx176')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2,ensure_ascii=False)
def main():
    ROOT.mkdir(exist_ok=False)
    rows=[json.loads(s) for s in (OLD/'tokenize01/tokens.jsonl').read_text(encoding='utf8').splitlines()]
    byhash=defaultdict(list)
    for r in rows:byhash[coverage.digest(r['request_ids'])].append(r)
    blocked=set();jobs=[];synthetic=[];reserved=0
    for p in sorted(OLD.glob('*/launch.json')):
        launch=read(p);reserved+=launch['requests']
        if not launch['requests']:continue
        manifest=read(p.parent/'input.json');units=[]
        for u in manifest['units']:
            h=coverage.digest(u['tokens']);matched=byhash.get(h,[])
            if matched:
                roots=sorted({r['root_id'] for r in matched});blocked.update(roots)
                units.append(dict(id=u['id'],token_sha256=h,root_ids=roots,receipt_exists=(p.parent/u['id']/'receipt.json').exists()))
            else:
                assert u['tokens']==[113+(i*173)%2309 for i in range(len(u['tokens']))],(p,u['id'],'unmapped input')
                synthetic.append(dict(job=p.parent.name,id=u['id'],token_sha256=h,tokens=len(u['tokens']),reason='exact inherited deterministic synthetic diagnostic formula; no natural root'))
        jobs.append(dict(job=p.parent.name,launch_sha256=sha(p),input_sha256=sha(p.parent/'input.json'),reserved=launch['requests'],units=units))
    assert reserved==2026
    prior=read(OLD/'common-panel.json');blocked.update(r['root_id'] for r in prior['calibration']+prior['test'])
    # Authenticate and reapply the saved older exposure inventory, including text.
    audit=read(OLD/'exposure-audit.json');old_audit=Path('E:/rtx164/exposure-pr163/EXPOSURE_AUDIT-00.json')
    assert sha(old_audit)==audit['prior_complete_audit'];legacy=read(old_audit);assert legacy['complete'];keys=set(legacy['keys']);files=[]
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','task_id','root_id','message_id') and isinstance(v,str):keys.add(v)
                if k in ('text','raw_prompt','formatted_prompt','prompt') and isinstance(v,str):keys.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('prompt_ids','tokens','input_ids') and isinstance(v,list):keys.add(coverage.digest(v))
                visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    for name,h in audit['files'].items():
        p=Path(name);assert sha(p)==h,name
        if p.suffix=='.jsonl':
            for line in p.read_text(encoding='utf8').splitlines():visit(json.loads(line))
        else:visit(read(p))
        files.append(dict(path=name,sha256=h))
    legacy_roots=set()
    for r in rows:
        probes=set(r['message_ids'])|{r['id'],r['root_id'],coverage.digest(r['request_ids']),coverage.digest(r['cached_ids'])}
        probes|={hashlib.sha256(t.strip().encode()).hexdigest() for t in [r['cached_text'],r['request_text'],*[m['content'] for m in r['messages']]]}
        if probes&keys:legacy_roots.add(r['root_id'])
    blocked.update(legacy_roots)
    exclusions=dict(root_ids=sorted(blocked),evidence=dict(prior_panel_sha256=sha(OLD/'common-panel.json'),prior_exposure_audit_sha256=sha(OLD/'exposure-audit.json'),token_rows_sha256=sha(OLD/'tokenize01/tokens.jsonl'),saved_job_inputs=jobs,synthetic_inputs=synthetic,legacy_files=files,legacy_matched_roots=sorted(legacy_roots),scope='All reserved job units are conservatively exposed, including uncompleted slots; all44 common-panel roots excluded. Saved older ID/text/token exposure inventory reapplied. No model or tokenizer invoked.'))
    put(ROOT/'exclusions.json',exclusions)
    census=read(OLD/'common-census.json');out=coverage.select(census,prior,exclusions);put(ROOT/'coverage.json',out)
    full=[]
    for r in census['eligible']:
        plans={a:coverage.plan(r['physical_head'],r['append_tokens'],a) for a in coverage.ARMS}
        metrics={a:dict(calls=len(v),full32=sum(w==32 for _,w in v),partial_tiles=sum(w<32 for _,w in v),unused32_slots=sum(32-w for _,w in v)) for a,v in plans.items()}
        full.append(dict(id=r['id'],root_id=r['root_id'],plans=plans,metrics=metrics,schedules_differ=plans['WB-cut']!=plans['WB-rechunk'],call_counts_differ=len(plans['WB-cut'])!=len(plans['WB-rechunk'])))
    summary=dict(paths=len(full),roots=len({r['root_id'] for r in full}),different_schedule_paths=sum(r['schedules_differ'] for r in full),roots_with_any_distinct_path=len({r['root_id'] for r in full if r['schedules_differ']}),different_call_count_paths=sum(r['call_counts_differ'] for r in full),roots_with_any_call_count_difference=len({r['root_id'] for r in full if r['call_counts_differ']}),tile_metrics={a:{k:sum(r['metrics'][a][k] for r in full) for k in ('calls','full32','partial_tiles','unused32_slots')} for a in coverage.ARMS},note='Tile metrics describe caller widths, not observed kernel occupancy or GPU padding work.')
    put(ROOT/'full-schedules.json',dict(summary=summary,rows=full))
    chosen={r['id'] for r in out['selected']};selected=[r for r in rows if r['id'] in chosen];assert len(selected)==len(chosen)
    byid={r['id']:r for r in selected};put(ROOT/'selected-inputs.json',[byid[r['id']] for r in out['selected']])
    print(json.dumps(dict(status=out['status'],blocked_roots=len(blocked),unexposed=out['unexposed_root_representatives'],distinguishing=out['unexposed_representatives_with_distinct_schedule'],selected=len(chosen),summary=summary),indent=2))
if __name__=='__main__':main()
