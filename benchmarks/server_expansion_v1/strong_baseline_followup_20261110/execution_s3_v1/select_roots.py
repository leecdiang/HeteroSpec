"""Close input-only exposure keys and choose six deterministic roots per domain."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata
from exposure_audit import keys,token_hash


def need(x,message):
    if not x:raise ValueError(message)


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')


def select(pool_path,local_audit_path,remote_index_path,reconciliation_path,out):
    need(not out.exists(),'Fresh roots freeze only');out.mkdir(parents=True)
    pool=read(pool_path);local=read(local_audit_path);index=read(remote_index_path);closed=read(reconciliation_path)
    need(not local['unresolved_sources']and pool['no_generated_outputs_seen']is True,'No unresolved local source or generated selection outputs')
    need(closed['status']=='ALL_RECOVERABLE_PROJECT_INPUTS_CLOSED'and not closed['unresolved_sources'],
         'Complete later-head input reconciliation required; do not relabel a pending audit blind')
    need(closed['local_exposure_sha256']==sha(local_audit_path)and closed['pool_sha256']==sha(pool_path),'Closed input snapshot binding')
    registered={x['path']:x for x in closed['remote_artifacts']};new_keys=set();ids=set();sources=[]
    def visit(value):
        if isinstance(value,dict):
            if isinstance(value.get('prompt_ids'),list):
                tokens=value['prompt_ids'];need(all(type(x)is int for x in tokens),'Complete integer prior prompt');new_keys.add(token_hash(tokens))
            for name in ('id','root','reference_id'):
                if isinstance(value.get(name),str):ids.add(value[name]);new_keys.update(keys(value[name]))
            for name in ('description','raw_prompt','formatted_prompt','text','question','prompt'):
                if isinstance(value.get(name),str):new_keys.update(keys(value[name]))
            for x in value.values():visit(x)
        elif isinstance(value,list):
            for x in value:visit(x)
    for item in index:
        path=Path(remote_index_path).parent/item['local_file']
        need(sha(path)==item['sha256']and path.stat().st_size==item['bytes'],'Complete fixed remote input artifact bytes')
        need(item['path']in registered and registered[item['path']]['commit']==item['commit']and registered[item['path']]['sha256']==item['sha256'],'Unreconciled remote artifact')
        visit(read(path));sources.append(item)
    need(len(sources)==len(registered),'Missing registered remote input artifact')
    local_by_id={x['id']:x for x in local['table']};table=[];eligible=[]
    for item in pool['inputs']:
        prior=local_by_id[item['id']]
        variants=keys(item['id'])|keys(item['description'])|keys(item['raw_prompt'])|keys(item['formatted_prompt'])|{item['prompt_ids_sha256']}
        overlap=sorted(new_keys&variants)
        row=dict(prior,remote_historical_hash_matches=overlap,candidate_for_final_selection=prior['candidate_for_final_selection']and not overlap)
        table.append(row)
        if row['candidate_for_final_selection']:eligible.append(item)
    selected=[];seen_ids=set();seen_text=set();seen_tokens=set()
    for domain in ('code','math'):
        group=[]
        for item in sorted((x for x in eligible if x['domain']==domain),key=lambda x:(x['rank'],x['id'])):
            expected=hashlib.sha256(('heterospec-q32-strong-v1:'+item['id']).encode()).hexdigest()
            need(item['rank']==expected and item['length_eligible']and 1<=item['prompt_tokens']<=192 and item['cap']==128,'Fixed input-only selection formula')
            if item['id']in seen_ids or item['normalized_description_sha256']in seen_text or item['prompt_ids_sha256']in seen_tokens:continue
            seen_ids.add(item['id']);seen_text.add(item['normalized_description_sha256']);seen_tokens.add(item['prompt_ids_sha256']);group.append(item)
            if len(group)==6:break
        need(len(group)==6,'Insufficient genuinely unexposed eligible roots; do not replace universe after outputs')
        selected.extend(group)
    result=dict(schema='hs.strong.S3.roots.v1',inputs=[dict(x,slot=i)for i,x in enumerate(selected)],
         selection='SHA256(heterospec-q32-strong-v1:+canonical_id); first6 unique per domain',
         pool_sha256=sha(pool_path),local_exposure_sha256=sha(local_audit_path),remote_index_sha256=sha(remote_index_path),
         reconciliation_sha256=sha(reconciliation_path),cap=128,prompt_ceiling=192,answers_used=False,
         generated_outputs_seen=False,training_unseen_claim=False,
         scope='Previously unused in the closed recoverable project input history; not a claim about model training or semantic similarity beyond recorded text/ID/token variants')
    save(out/'ROOTS.json',result);save(out/'EXPOSURE_TABLE.json',dict(table=table,remote_artifacts=sources,
         remote_prior_IDs=sorted(ids),unresolved_sources=[],roots_selected_before_any_new_model_output=True))
    print(json.dumps(dict(status='TWELVE_INPUT_ONLY_ROOTS_SELECTED_NOT_GPU_QUALIFIED',roots=[x['id']for x in selected])))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('pool','local-audit','remote-index','reconciliation','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();select(a.pool,a.local_audit,a.remote_index,a.reconciliation,a.out)
