"""Re-execute immutable Qwen R and independently compare complete R vectors."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import qwen_regression as q


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--bundle',type=Path,required=True)
    a=p.parse_args();q.initialize(a.repo);b=a.bundle;c=q.check_epoch(b)
    panel=q.read(b/'DEV.json');binding=q.read(b/'ORIGINAL_BINDING.json')
    slots=[]
    for s in q.read(b/'SLOTS.json'):
        if s['arm']=='R' and s['repair']['prefill']=='native':
            old=copy.deepcopy(s);old['study_id']='rtx_scope_transfer_v1'
            old['slot_id']='original-control/i%02d/%s'%(s['source_index'],s['observer'])
            slots.append(old)
    fn,_,_,_=q.driver(c['parent_snapshot'],binding)
    rows=fn(b,'original_control',panel,slots,original=True)
    cells=[]
    for r,s in zip(rows,slots):
        candidates=[t for t in q.read(b/'SLOTS.json') if t['arm']=='R' and t['source_index']==s['source_index'] and t['observer']==s['observer']]
        for t in candidates:
            rp=b/'units/regression/native'/(t['slot_id']+'.json');n=q.read(rp)
            fields=('ids','eog','length','terminal_id','stop_reason')
            assert {k:r[k] for k in fields}=={k:n[k] for k in fields}
            vectors=[]
            if s['observer']=='heavy':
                of=b/'units/original_control/native'/s['slot_id'];nf=rp.with_suffix('')
                names={'target/initial.f32'}|{'target/ordinary-%d.f32'%i for i in range(1,len(r['ids']))}
                for folder in (of,nf):
                    assert {f.relative_to(folder).as_posix() for f in folder.glob('target/*.f32')}==names
                for name in sorted(names):
                    oh=digest(of/name);nh=digest(nf/name);assert oh==nh,(s['input_id'],name)
                    vectors.append({'path':name,'sha256':oh})
            cells.append({'input_id':s['input_id'],'candidate_slot':t['slot_id'],'original_slot':s['slot_id'],
                          'endpoint_equal':True,'complete_vectors':vectors,'candidate_record_sha256':digest(rp)})
    q.save(b/'ORIGINAL_R_CONTROL.json',{'status':'ORIGINAL_R_PRESERVED','profile':c['profile'],
      'original_worker_sha256':q.file_hash(c['original_worker']),'source_sha256':digest(Path(__file__)),
      'receipt_sha256':digest(b/'units/original_control/RECEIPT.json'),'cells':cells},exclusive=True)
    print(c['profile'],'ORIGINAL_R_PRESERVED',len(cells),flush=True)


if __name__=='__main__':main()
