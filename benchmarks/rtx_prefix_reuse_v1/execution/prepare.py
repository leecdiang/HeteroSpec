"""Output-blind descriptors and provisional cohort, never claims unobserved physical heads."""
from host import *
sys.path.insert(0,str(HERE.parents[1]/'tpds_prefix_reuse_v1'))
import study
def main():
    audit=read('E:/rtx164/exposure-pr163/EXPOSURE_AUDIT-00.json');assert audit['complete'];keys=set(audit['keys']);files={}
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','task_id','root_id','message_id') and isinstance(v,str):keys.add(v)
                if k in ('text','raw_prompt','formatted_prompt','prompt') and isinstance(v,str):keys.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('prompt_ids','tokens','input_ids') and isinstance(v,list):keys.add(study.digest(v))
                visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    for base in ('E:/rtx160','E:/rtx164','E:/tpds167','E:/rtx170'):
        for p in Path(base).rglob('*.json'):
            if p.stat().st_size>30*1024**2:continue
            if p.name.lower() in ('panel.json','inputs.json','unseen.json','heldout.json','dev.json','exposures.json') or p.name.startswith('EXPOSURE_AUDIT'):
                files[str(p)]=sha(p);visit(read(p))
        for p in Path(base).rglob('EXPOSURE.jsonl'):
            files[str(p)]=sha(p)
            for line in p.read_text(encoding='utf8').splitlines():visit(json.loads(line))
    put(ROOT/'exposure-audit.json',dict(prior_complete_audit=sha('E:/rtx164/exposure-pr163/EXPOSURE_AUDIT-00.json'),files=files,key_count=len(keys),scope='known original-host archives; counterpart must attest newer B570 exposures before shared cohort freeze'))
    rows=[json.loads(s) for s in (ROOT/'tokenize01/tokens.jsonl').read_text(encoding='utf8').splitlines()];eligible=[];excluded=[];census=[]
    for r in rows:
        h=study.lcp(r['cached_ids'],r['request_ids']);n=len(r['request_ids']); probes=set(r['message_ids'])|{r['root_id'],r['id'],study.digest(r['request_ids']),study.digest(r['cached_ids'])}
        probes|={hashlib.sha256(t.strip().encode()).hexdigest() for t in [r['cached_text'],r['request_text'],*[m['content'] for m in r['messages']]]}
        reason='historical_exposure' if probes&keys else 'capacity' if n+128>4096 else 'no_reuse_or_append' if h==0 or h==n else None
        if reason:excluded.append(dict(id=r['id'],reason=reason,prompt_tokens=n));continue
        scenarios={}
        for g in (1,16,32,64):
            head=h//g*g;plans={a:study.plan(head,n-head,a) for a in study.FIXED};scenarios[str(g)]={a:len(p) for a,p in plans.items()};scenarios[str(g)]['crossed_qb_calls']=sum(len(p['attention_groups'])>1 for p in plans['QB'])
        z=dict(id=r['id'],root_id=r['root_id'],logical_lcp=h,effective_head=h,prompt_tokens=n,physical_head=None,physical_status='predicted_dense_restore; must be checked natively before qualification',scenarios=scenarios)
        census.append(z);eligible.append(r)
    by={}
    for r in eligible:by.setdefault(r['root_id'],[]).append(r)
    roots=sorted(by,key=lambda x:(study.digest([study.CFG['selection_seed'],'root',x]),x));assert len(roots)>=44
    chosen=[min(by[root],key=lambda r:(study.digest([study.CFG['selection_seed'],'path',r['id']]),r['id'])) for root in roots[:44]]
    put(ROOT/'provisional-cohort.json',dict(status='OUTPUT_BLIND_SELECTION_NOT_SHARED_FREEZE',capacity=4096,calibration=chosen[:12],test=chosen[12:]))
    put(ROOT/'descriptor-census.json',dict(rows=census,excluded=excluded,eligible_roots=len(by),physical_observations='development controls only; full-pool heads are predictions, not observations',summary={str(g):dict(crossed_requests=sum(r['scenarios'][str(g)]['crossed_qb_calls']>0 for r in census),requests=len(census)) for g in (1,16,32,64)}))
    print(len(census),len(by),len(excluded))
if __name__=='__main__':main()
