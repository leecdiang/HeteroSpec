"""Zero-forward native vocabulary contract; no model contexts or generation."""
from common import *
cfg=read(LOCAL/'CONFIG.json');r=subprocess.run([str(LOCAL/'native/vocabulary.exe'),str(Path(cfg['asset'])/'tools/llama-b10839'),cfg['models']['target']['path']],input=b'',capture_output=True,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert r.returncode==0
(LOCAL/'models/S-vocabulary.stdout.jsonl').write_bytes(r.stdout);(LOCAL/'models/S-vocabulary.stderr.log').write_bytes(r.stderr)
v=json.loads(r.stdout.splitlines()[0]);assert v['forward_calls']==v['context_creations']==0
save(PUB/'S_TOKEN_CONTRACT.json',{k:v[k] for k in ['eog','bos','eos','add_bos','add_eos','suppress','vocab_only','forward_calls','context_creations']})
print('S actual native EOG:',v['eog'],flush=True)
