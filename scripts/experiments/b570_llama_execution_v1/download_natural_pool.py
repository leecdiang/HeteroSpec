"""Fetch immutable public natural-task snapshots, without model execution."""
from pathlib import Path
import argparse,json,sys,urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import write,sha,need,utc

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HeteroSpec-reproduction/1.0'}),timeout=120)

def run(out):
    out=Path(out);need(not out.exists(),'fresh source snapshot');out.mkdir(parents=True);inventory=[]
    for repo,split in [('deepmind/code_contests','test'),('EleutherAI/hendrycks_math','train')]:
        with get('https://huggingface.co/api/datasets/'+repo) as response:meta=json.load(response)
        revision=meta['sha'];write(out/(repo.split('/')[-1]+'-METADATA.json'),meta)
        with get('https://huggingface.co/api/datasets/'+repo+'/tree/'+revision+'?recursive=true') as response:tree=json.load(response)
        write(out/(repo.split('/')[-1]+'-TREE.json'),tree)
        selected=[x for x in tree if x.get('type')=='file' and Path(x['path']).name.startswith(split+'-') and x['path'].endswith('.parquet')]
        need(selected,'pinned split files missing')
        for item in selected:
            dest=out/repo.split('/')[-1]/item['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            url='https://huggingface.co/datasets/'+repo+'/resolve/'+revision+'/'+item['path']
            with get(url) as response,dest.open('xb') as f:
                while data:=response.read(4*1024*1024):f.write(data)
            need(dest.stat().st_size==item['size'],'dataset size mismatch');h=sha(dest)
            if item.get('lfs'):need(h==item['lfs']['oid'],'dataset LFS digest mismatch')
            inventory.append({'repo':repo,'split':split,'revision':revision,'path':str(dest.resolve()),'repo_path':item['path'],'url':url,'bytes':dest.stat().st_size,'sha256':h})
            print(repo,item['path'],dest.stat().st_size,flush=True)
    write(out/'SOURCES.json',{'utc':utc(),'files':inventory,'model_forwards':0,'selected_panel':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(p.parse_args().out)
