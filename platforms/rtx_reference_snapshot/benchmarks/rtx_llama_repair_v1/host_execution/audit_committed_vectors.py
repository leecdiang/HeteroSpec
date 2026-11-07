"""Compare actual committed decision rows with pinned historical R vectors."""
import argparse
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for name in ('repo','epoch','history','raw','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.repo/'scripts/experiments/rtx_llama_repair_v1'))
    import history
    from lr_common import read,file_hash,save,need
    manifest=a.history/'REQUESTS.original.jsonl'
    need(file_hash(manifest)==history.MANIFEST_SHA,'historical request manifest')
    originals={}
    for line in manifest.read_text().splitlines():
        r=json.loads(line)
        if (r['stage'],r['arm'],r['observer'])==('diagnostic_A1','R','heavy'):
            pin=r['raw_native_record'];path=a.raw/pin['path'];need(file_hash(path)==pin['sha256'],'historical R record');originals[r['input_id']]=path
    rows=[]
    for slot in read(a.epoch/'units/development/SLOTS.json'):
        if slot['observer']!='heavy':continue
        original=originals[slot['input_id']];current=a.epoch/'units/development/native'/(slot['slot_id']+'.json')
        old,new=read(original),read(current)
        comparison=history.compare_records(old,new,original.with_suffix(''),current.with_suffix(''))
        rows.append({'slot':slot['slot_id'],'input_id':slot['input_id'],**comparison,
                     'old_record_sha256':file_hash(original),'new_record_sha256':file_hash(current)})
    need(len(rows)==18,'full development heavy matrix')
    passed=all(r['endpoint_equal'] and r['earliest_saved_decision_vector_difference_on_common_prefix'] is None for r in rows)
    result={'status':'ALL_COMMITTED_VECTORS_MATCH_OLD_R' if passed else 'COMMITTED_VECTOR_DIFFERENCE',
            'all_equal':passed,'rows':rows,'scope':'Actual committed rows only; rejected suffix rows are not relabeled as natural R.'}
    save(a.out,result,exclusive=True);print(result['status'])


if __name__=='__main__':main()
