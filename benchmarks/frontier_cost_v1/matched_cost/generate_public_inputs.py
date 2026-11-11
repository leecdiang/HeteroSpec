"""Select two declared boundary histories from the frozen public PR213 trace."""
from pathlib import Path
import argparse
import hashlib
import json

RAW_SHA = '53d76c43d4b2fa378855b90f76d9bcb60e509d4086fddd630e3c0f51f6197487'
TARGET_SHA = '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('fresh output required')
    data=a.records.read_bytes()
    if hashlib.sha256(data).hexdigest()!=RAW_SHA:raise ValueError('public trace SHA mismatch')
    records=json.loads(data)['records'];cases=[]
    for base in (248,255):
        candidates=[]
        for r in records:
            if r['kind']!='measurement' or r['session']!=0 or r['arm_label']!='LOCAL-loop4-k7':continue
            for c in r['receipt']['cycles']:
                if c['base']==base:candidates.append((r['root'],c['cycle'],r,c))
        _,_,record,cycle=min(candidates,key=lambda x:x[:2]);receipt=record['receipt']
        prompt=receipt['prompt_ids'];seed_index=base-len(prompt)
        if seed_index<0 or receipt['ids'][seed_index]!=cycle['seed']:raise ValueError('prefix/seed identity mismatch')
        history=prompt+receipt['ids'][:seed_index]
        rows=[cycle['seed']]+cycle['proposals']
        if len(history)!=base or len(rows)!=8:raise ValueError('declared q8 input mismatch')
        cases.append({'name':f'public-p{base}','history':history,'rows':rows,
                      'continuation':cycle['decisions'][0],
                      'origin':{'root':record['root'],'cycle':cycle['cycle'],'session':0,
                                'arm_label':record['arm_label'],'receipt_sha256':record['receipt_sha256']}})
    out={'schema':'heterospec.matched-local-inputs.v1',
         'purpose':'Exposed matched-history operation inputs, not live SD, held-out confirmation, or historical GPU R captures',
         'source':{'repository':'leecdiang/HeteroSpec','commit':'ba5b4c8e01d50d4bfaab1ac3908f798347be063a',
                   'LIVE_RECORDS_sha256':RAW_SHA,
                   'selection':'For base 248 and 255, first lexicographic (root,cycle) among session0 LOCAL-loop4-k7 measured cycles; no timing selection'},
         'model_binding':{'kind':'original_Qwen3_8B_target_required','expected_sha256':TARGET_SHA,
                          'model':'Qwen3-8B-Q8_0.gguf','expected_vocab':151936,
                          'identity_source_member':'records/JOB_MANIFEST_LIVE.json',
                          'identity_source_member_sha256':'067ebcface1d5c4ac8ca816892c07f1d81551ed41c97fd09d11c07061f631401',
                          'tokenizer_metadata_receipt_sha256':'6a5d5b777059e82fb664b418fb59cd2526d1cf65f4b7846892745c84a5124912',
                          'tokenizer_identity':'The full original GGUF SHA binds its embedded tokenizer; metadata receipt SHA is not a standalone vocabulary digest. No retokenization or remapping.'},
         'q_values':list(range(1,9)),'repeats':2,'threads':2,'cases':cases}
    with a.output.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({'output':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),
                      'cases':[{'name':c['name'],'origin':c['origin']} for c in cases]},indent=2))


if __name__=='__main__':main()
