"""Conservatively exclude the complete pinned APPS/test and MATH/test RTX pools."""
from pathlib import Path
import json,sys,hashlib,concurrent.futures
from download_natural_pool import get
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def run(root,out):
    root=Path(root);out=Path(out);need(not out.exists(),'fresh exclusion');out.mkdir(parents=True);inventory=[]
    for repo,rev in [('codeparrot/apps','21e74ddf8de1a21436da12e3e653065c5213e9d1'),('EleutherAI/hendrycks_math','21a5633873b6a120296cce3e2df9d5550074f4a3')]:
        with get('https://huggingface.co/api/datasets/'+repo+'/tree/'+rev+'?recursive=true') as r:tree=json.load(r)
        write(out/(repo.split('/')[-1]+'-TREE.json'),tree)
        for item in tree:
            name=item['path']
            if item['type']!='file' or not(name=='test.jsonl' or Path(name).name.startswith('test-') and name.endswith('.parquet')):continue
            inventory.append({'repo':repo,'revision':rev,'repo_path':name,'path':str((out/repo.split('/')[-1]/name).resolve()),'bytes':item['size'],'lfs_sha256':item.get('lfs',{}).get('oid'),'url':'https://huggingface.co/datasets/'+repo+'/resolve/'+rev+'/'+name})
    def download(f):
        dest=Path(f['path']);dest.parent.mkdir(parents=True,exist_ok=True)
        with get(f['url']) as r,dest.open('xb') as o:
            while b:=r.read(4*1024**2):o.write(b)
        need(dest.stat().st_size==f['bytes'],'full source length');f['sha256']=sha(dest)
        if f['lfs_sha256']:need(f['sha256']==f['lfs_sha256'],'pinned LFS identity')
        print('VERIFIED',f['repo'],f['repo_path'],flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(download,inventory))
    write(out/'SOURCES.json',inventory);sys.path.insert(0,str(root/'pool-pydeps'));import pyarrow.parquet as pq
    keys=set();counts={}
    for f in inventory:
        code=f['repo']=='codeparrot/apps';p=Path(f['path']);rows=map(json.loads,p.read_text(encoding='utf-8').splitlines()) if code else pq.read_table(p,columns=['problem']).to_pylist();count=0
        for i,x in enumerate(rows):
            text=x['question' if code else 'problem'];keys.add(hashlib.sha256(text.strip().encode()).hexdigest());keys.add('APPS/test/'+str(x.get('problem_id',i)) if code else f'MATH/{p.parent.name}/test/{i}');count+=1
        counts[f['repo_path']]=count
    write(out/'EXCLUSION.json',{'keys':sorted(keys),'counts':counts,'scope':'Conservative exclusion of entire pinned APPS test and MATH test, a superset of ongoing RTX162 first1000 APPS / MATH test pool. These are exclusions, not asserted actual output exposures.','source_sha256':sha(out/'SOURCES.json'),'rtx_pool_author_sha256':sha(root/'rtx162-readonly/prepare_pool.py'),'model_forwards':0})

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
