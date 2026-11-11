"""Freeze before looking at the natural panel; run each registered block once."""
from panel import *
import sys

F=ROOT/"formal01"
FIELDS=("id","text_sha256","prompt_ids_sha256","formatted_prompt_sha256","raw_prompt_sha256")
def keys(x):return {x[k] for k in FIELDS if x.get(k)}
def select(seed):
    prior=Path("E:/rtx164")
    pool=prior/"pool06/POOL.json"
    assert sha(pool)==read(pool.parent/"PROVENANCE.json")["pool_sha256"]
    audit=read(prior/"exposure-pr163/EXPOSURE_AUDIT-00.json");assert audit["complete"] and not audit["unresolved_sources"]
    excluded=set(audit["keys"])
    for p in [prior/"exposure-pr163/EXPOSURES.json",Path("E:/rtx160/exposure04/EXPOSURES.json")]:
        for x in read(p):excluded.update(keys(x))
    for l in (prior/"exposure-pr163/EXPOSURE.jsonl").read_text().splitlines():excluded.update(keys(json.loads(l)))
    for x in read(prior/"exposure-pr165/UNSEEN.json").values():
        excluded.update(keys(x))
        for k in ("text","raw_prompt","formatted_prompt"):excluded.add(hashlib.sha256(x[k].strip().encode()).hexdigest())
    paths=[Path("E:/rtx160/research/epoch07/HELDOUT.json")]
    for family in ("qwen8b02","qwen14b02"):
        paths+=[prior/f"selection01/{family}.json",Path("E:/rtx160/research")/family/"DEV.json"]
    for path in paths:
        for x in read(path)["inputs"]:excluded.update(keys(x))
    rows=read(pool)["inputs"]
    selected=[]
    for domain,near in [("math",True),("code",False)]:
        candidates=[x for x in rows if x["domain"]==domain and keys(x).isdisjoint(excluded) and 64<=len(x["prompt_ids"])<=892 and
                     (len(x["prompt_ids"])%256 in (253,254,255) if near else min(len(x["prompt_ids"])%256,256-len(x["prompt_ids"])%256)>=32)]
        choice=min(candidates,key=lambda x:hashlib.sha256((seed+x["id"]).encode()).hexdigest())
        selected.append(choice);excluded.update(keys(choice))
    return selected

def freeze():
    F.mkdir()
    binding=read(OLD/"ORIGINAL_BINDING.json")["families"]["Qwen"]
    assert sha(Path(CFG["original_worker"]))==binding["executable_sha256"]
    for role in ("target","draft"):assert sha(Path(CFG[role]))==binding["models"][role]["sha256"]
    for n,h in binding["numerical_modules"].items():
        for folder in [OUT/"bin",ROOT/"oracle01",Path(CFG["original_worker"]).parent]:assert sha(folder/n)==h
    paths=[OUT/"bin/service.exe",ROOT/"oracle01/service.exe",ROOT/"oracle01/probe.exe",OUT/"bin/probe.exe",BASE/"core/src/libllama.a",OUT/"core/src/libllama.a",OUT/"service.cpp",
        *[p for p in HERE.iterdir() if p.suffix in (".cpp",".py",".inc")],HERE/"PROTOCOL.md"]
    put(F/"freeze.json",dict(inputs={str(p):sha(p) for p in paths},numerical_modules=binding["numerical_modules"],models=binding["models"],
        original_ctx1024_worker=binding["executable_sha256"],panel=dict(contexts=[1024,1536],arms=ARMS,sessions=[0,1],width=32,cap=128,k=3)))
    put(F/"panel.json",select(sha(F/"freeze.json")))

def formal():
    frozen=read(F/"freeze.json")
    for file,h in frozen["inputs"].items():assert sha(Path(file))==h,file
    items=read(F/"panel.json")
    for ctx in [1024,1536]:
        o=F/f"oracle-{ctx}"
        if ctx==1024:original(o,items)
        else:service(o,items,ctx,["R"],"heavy",True)
        c=F/f"qual-{ctx}"
        service(c,items,ctx,ARMS,"heavy")
        assert compare(c,items,o,legacy=ctx==1024),"reference gate failed; retain all evidence"
    for session in [0,1]:
        for ctx in ([1024,1536] if session==0 else [1536,1024]):
            d=F/f"cost-{ctx}-s{session}"
            service(d,items,ctx,ARMS,"cost",session=session)
            for i in range(len(items)):
                for arm in ARMS:
                    q=read(F/f"qual-{ctx}/i{i}/{arm}/capture/receipt.json")
                    for role in ("warm","timed"):
                        r=read(d/f"i{i}/{arm}/{role}/receipt.json")
                        assert all(r[k]==q[k] for k in ["endpoint","cycles","prompt_ids"])
            put(d/"complete.json",dict(blocks=len(ARMS)*len(items),warm=len(ARMS)*len(items),measured=len(ARMS)*len(items)))
if __name__=="__main__":
    if sys.argv[1]=="freeze":freeze()
    elif sys.argv[1]=="run":formal()

