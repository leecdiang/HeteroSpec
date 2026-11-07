"""Archive all evidence bytes once per SHA256, excluding model/runtime assets."""
import hashlib,json,subprocess,time,zipfile
from pathlib import Path
from run import HERE,OLD,ORIGINAL,read,save,sha

OUT=HERE.parent.parent/'outputs'
PUBLIC=HERE.parent/'continuity-public/benchmarks/rtx_consistency_contract_v1'

def main():
    bundle=HERE/'generated/FROZEN_HISTORY.bundle'
    assert not bundle.exists()
    subprocess.check_call(['git','bundle','create',str(bundle),'--all'],cwd=HERE)
    subprocess.check_call(['git','bundle','verify',str(bundle)],cwd=HERE)
    pairs=[]
    def add(p,name):
        assert p.is_file();pairs.append((p,name))
    for p in HERE.iterdir():
        if p.is_file():add(p,'experiment/'+p.name)
    for directory in ['runs','generated/analysis','generated/source']:
        for p in (HERE/directory).rglob('*'):
            if p.is_file():add(p,'experiment/'+p.relative_to(HERE).as_posix())
    for p in (HERE/'generated').iterdir():
        if p.is_file():add(p,'experiment/generated/'+p.name)
    for name in ['llama-cli.exe','llama-server.exe']:
        add(HERE/'generated/build/bin'/name,'experiment/current-binaries/'+name)
    for p in (OLD/'pinned-source').rglob('*'):
        if p.is_file():add(p,'historical/work/rtx-target-v1/pinned-source/'+p.relative_to(OLD/'pinned-source').as_posix())
    add(OLD/'native-build/bin/llama-cli.exe','historical/work/rtx-target-v1/native-build/bin/llama-cli.exe')
    add(ORIGINAL/'scripts/platform/rtx_trajectory_cost_v4/native.py','historical/scripts/platform/rtx_trajectory_cost_v4/native.py')
    add(OLD/'INPUTS.json','historical/work/rtx-target-v1/INPUTS.json')
    inputs=read(OLD/'INPUTS.json')
    for tid,x in inputs.items():
        if not tid.startswith('HumanEval/'):continue
        prompt=ORIGINAL/x['prompt']
        add(prompt,'historical/'+prompt.resolve().relative_to(ORIGINAL.resolve()).as_posix())
        conditions=['R','N0','N1'] if tid in ['HumanEval/15','HumanEval/25','HumanEval/18','HumanEval/31'] else ['R']
        for condition in conditions:
            for rep in [1,2,3]:
                d=OLD/f"formal/{tid.replace('/','-')}-{condition}-r{rep}"
                add(d/'result.json','historical/work/rtx-target-v1/'+(d/'result.json').relative_to(OLD).as_posix())
                if condition!='R':
                    for p in d.glob('attempt-*/trace.jsonl'):add(p,'historical/work/rtx-target-v1/'+p.relative_to(OLD).as_posix())
    for p in PUBLIC.rglob('*'):
        if p.is_file():add(p,'public/benchmarks/rtx_consistency_contract_v1/'+p.relative_to(PUBLIC).as_posix())
    for p in OUT.iterdir():
        if p.is_file() and p.name.startswith('HeteroSpec_') and p.suffix in ['.md','.csv','.png','.svg']:
            add(p,'outputs/'+p.name)
    names=[n for _,n in pairs];assert len(names)==len(set(names))
    destination=OUT/'HeteroSpec_局部一致性实验_完整记录.zip';assert not destination.exists()
    index=[];seen={};total=0;unique=0;started=time.time()
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        z.write(HERE/'rehydrate.py','rehydrate.py')
        for p,name in pairs:
            h=sha(p);size=p.stat().st_size;index.append({'path':name,'sha256':h,'bytes':size});total+=size
            if h not in seen:z.write(p,'objects/'+h);seen[h]=p;unique+=size
        manifest={'schema':'heterospec-content-addressed-archive-v1','files':index,'logical_bytes':total,
                  'unique_bytes':unique,'unique_objects':len(seen),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
                  'excluded':'Model GGUF weights, released DLLs, build intermediates and unrelated workspaces; identities supplied in provenance.',
                  'restore':'python rehydrate.py ARCHIVE.zip NEW_DESTINATION; every object is hash-checked and different existing files are refused.'}
        z.writestr('INDEX.json',json.dumps(manifest,ensure_ascii=True,indent=2)+'\n')
        z.writestr('README.txt','All original bytes are preserved through SHA256-addressed objects. INDEX.json maps relative paths to bytes.\nUse the included rehydrate.py to restore into a new directory. No source/run file is silently dropped because it is a repeated measurement.\nModels and released runtime DLLs are excluded; use matching pre/post hashes. Frozen Git bundle retains all locally committed experiment versions.\nReferences/captured logits/paid state forks are offline diagnostic evidence, never free online inputs. See outputs report and public README for interpretation limits.\n')
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for h in seen:
            with z.open('objects/'+h) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
        assert json.loads(z.read('INDEX.json'))==manifest
    result={'status':'PASS','archive':str(destination),'sha256':sha(destination),'zip_bytes':destination.stat().st_size,
            'file_paths':len(index),'unique_objects':len(seen),'logical_bytes':total,'unique_bytes':unique,'seconds':time.time()-started,
            'crc_and_all_object_sha256_verified':True,'source_head':manifest['source_head']}
    save(OUT/'HeteroSpec_记录包校验.json',result)
    print(json.dumps(result,ensure_ascii=True),flush=True)

if __name__=='__main__':main()
