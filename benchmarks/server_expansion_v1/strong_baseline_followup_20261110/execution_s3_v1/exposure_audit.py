"""Input-only incremental history audit. Remote-head closure is a separate gate."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hashed(text):return hashlib.sha256(text.encode()).hexdigest()
def keys(text):return {hashed(x)for x in (text,text.strip(),' '.join(unicodedata.normalize('NFKC',text).split()))}
def token_hash(ids):return hashed(json.dumps(ids,separators=(',',':')))
def need(value,message):
    if not value:raise RuntimeError(message)


def audit(root,pool_path,out):
    need(not out.exists(),'Fresh audit report; never overwrite historical review')
    old=root/'f-confirmation-bundle-01/confirmation_v1';review=read(old/'EXPOSURE_REVIEW.json')
    need(review['complete']is True and not review['unresolved_sources'],'Inherited project-history review unresolved')
    compressed=old/'EXCLUSION_UNIVERSE.sha256.txt.gz';need(sha(compressed)==review['compressed_sha256'],'Inherited exclusion transport changed')
    raw=gzip.decompress(compressed.read_bytes());need(hashlib.sha256(raw).hexdigest()==review['uncompressed_sha256'],'Inherited exclusion content changed')
    historical=set(raw.decode('ascii').splitlines());need(len(historical)==review['hashed_exclusion_key_count'],'Inherited exclusion count')
    for x in historical:need(re.fullmatch('[0-9a-f]{64}',x),'Canonical exclusion hash')
    paths=set();inventory=[];unresolved=[];identities=set();new_keys=set()
    # Jobs and registered selected cohorts, never source-data availability pools.
    patterns=('*/jobs/**/*.json','*/*/jobs/**/*.json','*/panel-*/*.json','*/inputs-*/COHORT.json',
              'strong-baseline-followup-20261110/sb217-s0-*/execution/S1/workers/*/JOB.json')
    for pattern in patterns:paths.update(p for p in root.glob(pattern)if p.is_file())
    need(paths,'No actual local input/job manifests recovered')
    def visit(node):
        found=0
        if isinstance(node,dict):
            if isinstance(node.get('prompt_ids'),list)and all(type(x)is int for x in node['prompt_ids']):
                new_keys.add(token_hash(node['prompt_ids']));found+=1
                for name in ('id','root','reference_id'):
                    if isinstance(node.get(name),str):identities.add(node[name]);new_keys.update(keys(node[name]))
                for name in ('description','raw_prompt','formatted_prompt','text','question','prompt'):
                    if isinstance(node.get(name),str):new_keys.update(keys(node[name]))
            for value in node.values():found+=visit(value)
        elif isinstance(node,list):
            for value in node:found+=visit(value)
        return found
    for path in sorted(paths):
        if path.is_relative_to(out.parent)or '/sb217-s3-'in str(path):continue
        try:
            need(path.stat().st_size<=16*1024**2,'Oversized input manifest requires explicit review')
            value=read(path);count=visit(value)
            inventory.append(dict(path=str(path.relative_to(root)),sha256=sha(path),bytes=path.stat().st_size,
                                  input_objects=count,scope='Historical registered job/cohort; conservative inclusion even if not executed'))
        except Exception as e:unresolved.append(dict(path=str(path.relative_to(root)),reason=str(e)))
    # F's selected statements retain raw descriptions, while ordinary native jobs
    # generally contain token IDs only. Both are needed for cross-template reuse.
    selected=root/'f-run-01/inputs-formal-03/COHORT.json';cohort=read(selected)
    for item in cohort['inputs']:identities.add(item['id']);new_keys.update(keys(item['id']))
    for item in cohort['statements']:
        for name in ('description','raw_prompt','formatted_prompt'):
            if isinstance(item.get(name),str):new_keys.update(keys(item[name]))
    pool=read(pool_path)['inputs'];table=[];combined=historical|new_keys
    for item in pool:
        variants=keys(item['id'])|keys(item['description'])|keys(item['raw_prompt'])|keys(item['formatted_prompt'])|{item['prompt_ids_sha256']}
        overlaps=sorted(variants&combined)
        table.append(dict(id=item['id'],domain=item['domain'],rank=item['rank'],prompt_tokens=item['prompt_tokens'],
                          length_eligible=item['length_eligible'],historical_hash_matches=overlaps,
                          candidate_for_final_selection=item['length_eligible']and not overlaps,
                          normalized_description_sha256=item['normalized_description_sha256'],
                          prompt_ids_sha256=item['prompt_ids_sha256']))
    report=dict(status='LOCAL_INCREMENTAL_INPUT_AUDIT_REMOTE_HEAD_RECONCILIATION_PENDING',
         inherited_review_sha256=sha(old/'EXPOSURE_REVIEW.json'),inherited_exclusion_sha256=sha(compressed),
         inherited_source_commit=review['source_snapshot_commit'],inherited_review_scope=review['scope'],
         inherited_hashes=len(historical),incremental_hashes=len(new_keys),local_manifest_inventory=inventory,
         selected_F_cohort_sha256=sha(selected),historical_canonical_IDs=sorted(identities),
         unresolved_sources=unresolved,table=table,tokenized_pool_sha256=sha(pool_path),
         eligible_counts={d:sum(x['domain']==d and x['candidate_for_final_selection']for x in table)for d in ('code','math')},
         roots_selected=False,model_outputs_seen=False,training_unseen_claim=False,
         final_gate='Reconcile all later PR heads/input artifacts and close scope explicitly before final deterministic roots/F2. Do not call pending audit blind.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],manifests=len(inventory),unresolved=len(unresolved),eligible_counts=report['eligible_counts'])))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','pool','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit(a.root,a.pool,a.out)
