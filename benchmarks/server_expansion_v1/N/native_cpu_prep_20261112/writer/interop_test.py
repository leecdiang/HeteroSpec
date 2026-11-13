"""Test only: unchanged PR226 comparator accepts our numerical descriptors.
Synthetic receipt must remain ineligible as a native snapshot.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from raw_writer import CaptureWriter, OwnedTensor

parser=argparse.ArgumentParser()
parser.add_argument('comparator',type=Path)
COMPARATOR=parser.parse_args().comparator.resolve()
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    pairs=[]
    for name in ['left','right']:
        with CaptureWriter(root,name,run_id='r',operation_id=name,context_id='c',source_sha256='a'*64,executable_sha256='b'*64) as w:
            d=w.tensor('active_k',OwnedTensor(b'\x00\x3c\x00\x80','F16LE',[1,2],['row','dim']))
            w.commit();pairs.append(d)
    script="""
const fs=require('fs'), c=require(process.argv[1]), spec=JSON.parse(process.argv[3]);
const result=c.compareTensor(process.argv[2],spec[0],spec[1]);
if(result.status!=='PASS'||result.bytes_compared!==4)throw Error('transport mismatch');
const receipt=JSON.parse(fs.readFileSync(process.argv[2]+'/left/COMPLETE.json'));
let rejected=false;try{c.validateSnapshot(receipt);}catch(e){rejected=true;}
if(!rejected)throw Error('synthetic receipt accepted as native');
console.log(JSON.stringify({tensor_interop:result.status,bytes_compared:result.bytes_compared,synthetic_rejected_as_native:rejected,model_forwards:0,gpu_contexts:0}));
"""
    p=subprocess.run(['node','-e',script,str(COMPARATOR),str(root),json.dumps(pairs)],check=True,text=True,capture_output=True)
    print(p.stdout,end='')
