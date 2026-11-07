"""Prospective leaf-only reconciliation; never reassign an exposed root to test."""
from calibrate import *
import gzip
def main():
    with gzip.open(ROOT/'oasst.messages.jsonl.gz','rt',encoding='utf8') as f:raw=[json.loads(s) for s in f]
    parents={r.get('parent_id') for r in raw};rows=[json.loads(s) for s in (ROOT/'tokenize01/tokens.jsonl').read_text(encoding='utf8').splitlines()];leaf=[r for r in rows if r['id'] not in parents];assert len(leaf)==6423
    by={}
    for r in leaf:
        assert len(r['request_ids'])+128<=4096
        by.setdefault(r['root_id'],[]).append(r)
    roots=sorted(by,key=lambda root:(study.digest([study.CFG['selection_seed'],'root',root]),root))
    chosen=[min(by[root],key=lambda r:(study.digest([study.CFG['selection_seed'],'path',r['id']]),r['id'])) for root in roots[:44]]
    peer=read(ROOT/'B570_COHORT_RECEIPT.json');old=read(ROOT/'provisional-cohort.json')
    assert not {r['root_id'] for r in old['calibration']}&{r['root_id'] for r in chosen[12:]}
    for a,b in zip(chosen,peer['calibration']+peer['test']):
        assert (a['id'],a['root_id'])==(b['id'],b['root_id'])
        assert study.digest(a['request_ids'])==b['request_token_sha256'] and study.digest(a['cached_ids'])==b['cached_token_sha256']
    index={r['id']:i for i,r in enumerate(old['calibration'])};maps=[]
    for i,r in enumerate(chosen[:12]):
        previous=index.get(r['id']);maps.append(dict(index=i,previous_index=previous,original_reference=str(ROOT/f'cal-r-{previous:02}') if previous is not None else None))
    put(ROOT/'common-cohort.json',dict(status='SHARED_LEAF_IDS_AND_TOKEN_HASHES_AUTHENTICATED_NO_TEST_OUTPUT',calibration=chosen[:12],test=chosen[12:],reference_reuse=maps))
    put(ROOT/'COHORT_RECEIPT.json',dict(status='COMMON_COHORT_RECONCILED_BEFORE_HELDOUT',peer_commit='eb1420cd74b64f21dab282a589e1a66ffa574706',leaf_paths=len(leaf),roots=len(by),calibration=peer['calibration'],test=peer['test'],old_calibration_overlap_with_test=[],native_request_and_cached_token_hashes_match=44,reference_reuse=maps,selection='independently hash-ranked actual user leaves; no geometry/output selection'))
    print('common panel matched',len(chosen),'exact reference reuse',sum(x['previous_index'] is not None for x in maps))
if __name__=='__main__':main()
