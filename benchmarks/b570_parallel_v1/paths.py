from pathlib import Path
import json, hashlib, subprocess, sys, os, time
ROOT=Path('I:/HeteroSpec/b570-parallel-20261103')
PR165=Path('I:/HeteroSpec/b570-qwen-transfer-20261103')
OLD=Path('C:/hs/b570-producer-consumer-20261028')
OLD_LIB=Path('C:/hs/b570-native-reproduction-20261026')
KIT=Path('C:/hs/b570-llama-results/scripts/experiments/b570_llama_companion_v1')
HERE=Path(__file__).resolve().parent
SUP=Path('I:/HeteroSpec/b570-llama-20261102/oracle-01/supervisor.py')
LOCK=Path('C:/hs/b570-llama-exclusive.lock')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def hashval(x):return hashlib.sha256(json.dumps(x,separators=(',',':'),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def once(s,a,b):
    if s.count(a)!=1:raise ValueError('source drift '+a[:80])
    return s.replace(a,b,1)
def command(cmd,log):
    with Path(log).open('x',encoding='utf-8') as f:subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,check=True)

