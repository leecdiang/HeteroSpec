"""Bind the external author's actual immutable method source files."""
from common import *
revision='143cb7075d96b756edc3ef44e6f752cb4fcc90e2';files=['README.md','python/sglang/srt/llm42/llm42_worker.py','python/sglang/srt/llm42/llm42_info.py'];rows=[]
for name in files:
    url='https://raw.githubusercontent.com/microsoft/llm-42/'+revision+'/'+name
    with urllib.request.urlopen(url,timeout=60) as r:b=r.read()
    p=LOCAL/'method'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append({'path':name,'url':url,'sha256':sha(p),'bytes':len(b)})
save(PUB/'METHOD_SOURCE_RECEIPT.json',{'official_repository':'https://github.com/microsoft/llm-42','revision':revision,'files':rows,'paper':'https://arxiv.org/html/2601.17768v2','mapping':'METHOD_MAPPING.md','actual_adaptation_source_sha256':sha(Path(__file__).parent/'dvr_server.cpp')});print('METHOD SOURCE BOUND',flush=True)
