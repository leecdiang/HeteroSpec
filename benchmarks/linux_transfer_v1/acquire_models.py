"""Fetch exact public model objects; reject same-name quantizations with other hashes.

Run in a separate, pinned transfer-tool environment. This never initializes CUDA.
"""
import argparse, hashlib, json, time
from pathlib import Path
from huggingface_hub import hf_hub_download

MODELS={
 'Qwen-target':('Qwen/Qwen3-8B-GGUF','7c41481f57cb95916b40956ab2f0b139b296d974','Qwen3-8B-Q8_0.gguf',8709518112,'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'),
 'Qwen-draft':('Qwen/Qwen3-0.6B-GGUF','23749fefcc72300e3a2ad315e1317431b06b590a','Qwen3-0.6B-Q8_0.gguf',639446688,'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'),
 'Smol-target':('bartowski/SmolLM2-1.7B-Instruct-GGUF','1f03464768bfcc0319fc50da8ff5fb20b6417ba2','SmolLM2-1.7B-Instruct-Q8_0.gguf',1820414944,'0c6e8955788b1253f418c354a4bdc4cf507b8cfe49c48bb10c7c58ae713cfa2a'),
 'Smol-draft':('lmstudio-community/SmolLM2-135M-Instruct-GGUF','04f7f8a05a8e4bc208e88d11e8c9122be36c2f9b','SmolLM2-135M-Instruct-Q8_0.gguf',144811072,'40f7094960b6ede829145d102ca79451b364b27d9d8694d4406e002024cff357')}

def main():
 p=argparse.ArgumentParser();p.add_argument('key',choices=MODELS);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 repo,revision,name,size,expected=MODELS[a.key];a.out.mkdir(parents=True,exist_ok=True)
 start=time.monotonic();path=Path(hf_hub_download(repo,name,revision=revision,local_dir=a.out,token=False))
 if path.stat().st_size!=size:raise RuntimeError('model size differs from frozen input')
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 if h.hexdigest()!=expected:raise RuntimeError('model SHA256 differs from protocol')
 record={'key':a.key,'repo':repo,'revision':revision,'file':name,'bytes':size,'sha256':expected,'verified':True,'download_and_hash_s':time.monotonic()-start}
 receipt=a.out/(a.key+'-VERIFIED.json')
 if receipt.exists():
  existing=json.loads(receipt.read_text())
  if any(existing[k]!=record[k] for k in ('repo','revision','file','bytes','sha256','verified')):raise RuntimeError('acquisition receipt changed')
  print('Reverified existing exact model object',a.key,flush=True);return
 with receipt.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps(record),flush=True)

if __name__=='__main__':main()
