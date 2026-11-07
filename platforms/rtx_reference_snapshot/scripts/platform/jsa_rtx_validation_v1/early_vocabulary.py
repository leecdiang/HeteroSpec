"""Expose no tasks: check the complete actual native pair vocabulary only."""
from common import *
cfg=read(LOCAL/'CONFIG.json');values={};receipts={}
for role in ['target','draft']:
    m=read(LOCAL/'models'/(role+'_DOWNLOAD.json'));r=subprocess.run([str(LOCAL/'native/vocabulary.exe'),str(Path(cfg['asset'])/'tools/llama-b10839'),m['path']],input=b'',capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert r.returncode==0
    p=LOCAL/'models'/(role+'-early-vocabulary.stdout.jsonl');p.write_bytes(r.stdout);values[role]=json.loads(r.stdout.splitlines()[0]);assert values[role]['forward_calls']==values[role]['context_creations']==0;receipts[role]={'raw_sha256':sha(p),'vocab_count':len(values[role]['tokens']),'eog':values[role]['eog'],'bos':values[role]['bos'],'eos':values[role]['eos'],'add_bos':values[role]['add_bos'],'add_eos':values[role]['add_eos']}
save(PUB/'PRE_DISCOVERY_NATIVE_COMPATIBILITY.json',{'native_pair_vocabulary_byte_structure_equal':values['target']==values['draft'],'models':receipts,'forward_calls':0,'confirmation_selection':'not involved in this check'});print(json.dumps(read(PUB/'PRE_DISCOVERY_NATIVE_COMPATIBILITY.json')),flush=True)
