"""Conditional fresh natural confirmation for the packed implementation."""
import sys
from host import *
sys.path.insert(0,str(HERE.parents[1]/"tpds_parallel"))
import panel
N=ROOT/"natural01"
OLD=FROZEN/"bin/service.exe"
REF=FROZEN.parent/"oracle01/service.exe"
NEW=ROOT/"new-driver/service.exe"
ARMS=("oldQB","newQB","newWB")
def link_service():
    cmd=read(sorted(FROZEN.glob("link-*.json"))[-1])["argv"]
    cmd=[s.replace(str(FROZEN/"probe.obj"),str(FROZEN/"service.obj")).replace(str(FROZEN/"core"),str(ROOT/"candidate01/core")).replace(str(FROZEN/"bin/probe.exe"),str(NEW)) for s in cmd]
    with (ROOT/"new-driver/service-link.log").open("xb") as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300,check=True)
    put(ROOT/"new-driver/service-build.json",dict(argv=cmd,source=sha(FROZEN/"service.cpp"),object=sha(FROZEN/"service.obj"),core=sha(ROOT/"candidate01/core/src/libllama.a"),result=sha(NEW)))
def freeze():
    N.mkdir()
    prior=read(FROZEN.parent/"formal01/freeze.json")
    for exe in (OLD,REF):assert sha(exe)==prior["inputs"][str(exe)]
    for role in ("target","draft"):assert sha(Path(panel.CFG[role]))==prior["models"][role]["sha256"]
    for dll,h in prior["numerical_modules"].items():
        for exe in (OLD,REF,NEW):assert sha(exe.parent/dll)==h
    order=[[dict(session=s,index=i,arm=ARMS[(j+i+s)%3]) for i in range(4) for j in range(3)] for s in range(3)]
    files=[NEW,OLD,REF,ROOT/"matrix.json",ROOT/"candidate01/source/src/llama-graph.cpp",HERE/"natural.py",HERE/"candidate.py",FROZEN/"service.cpp"]
    put(N/"freeze.json",dict(files={str(p):sha(p) for p in files},order=order,ctx=1536,k=3,cap=128,width=32,pool_sha=read(Path("E:/rtx164/pool06/PROVENANCE.json"))["pool_sha256"],models=prior["models"]))
def select():
    from study import keys
    old=Path("E:/rtx164");r160=Path("E:/rtx160")
    audit=read(old/"exposure-pr163/EXPOSURE_AUDIT-00.json");assert audit["complete"]
    excluded=set(audit["keys"])
    for file in [old/"exposure-pr163/EXPOSURES.json",r160/"exposure04/EXPOSURES.json",FROZEN.parent/"formal01/panel.json"]:
        for x in read(file):excluded.update(keys(x))
    for line in (old/"exposure-pr163/EXPOSURE.jsonl").read_text().splitlines():excluded.update(keys(json.loads(line)))
    for x in read(old/"exposure-pr165/UNSEEN.json").values():
        excluded.update(keys(x))
        for k in ("text","raw_prompt","formatted_prompt"):excluded.add(hashlib.sha256(x[k].strip().encode()).hexdigest())
    for file in [r160/"research/epoch07/HELDOUT.json",*[p for fam in ("qwen8b02","qwen14b02") for p in (old/f"selection01/{fam}.json",r160/f"research/{fam}/DEV.json")]]:
        for x in read(file)["inputs"]:excluded.update(keys(x))
    pool=old/"pool06/POOL.json";assert sha(pool)==read(N/"freeze.json")["pool_sha"]
    data=read(pool)["inputs"];seed=sha(N/"freeze.json");items=[]
    for domain in ("math","code"):
        for lo,hi in [(64,360),(361,900)]:
            options=[x for x in data if x["domain"]==domain and lo<=len(x["prompt_ids"])<=hi and keys(x).isdisjoint(excluded)]
            x=min(options,key=lambda x:hashlib.sha256((seed+x["id"]).encode()).hexdigest())
            items.append(x);excluded.update(keys(x))
    put(N/"inputs.json",items)
def run(exe,labels,role,folder):
    items=read(N/"inputs.json")
    blocks=[]
    for i,arm in labels:
        native={"oldQB":"QB-local","newQB":"QB-local","newWB":"WB-cut"}.get(arm,arm)
        roles=["warm","measured"] if role=="cost" else ["capture"]
        blocks.append(dict(arm=native,slots=[dict(id=f"i{i}/{arm}/{r}",capture=r=="capture",input=items[i]) for r in roles]))
    manifest=folder.with_suffix(".json");put(manifest,dict(ctx=1536,width=32,layers=999,blocks=blocks))
    panel.run(exe,[panel.CFG["target"],panel.CFG["draft"],manifest,folder],folder)
def qualify():
    for file,h in read(N/"freeze.json")["files"].items():assert sha(Path(file))==h
    for name,exe,arms in [("reference",REF,["R","S1"]),("historical",OLD,["oldQB"]),("changed",NEW,["newQB","newWB"])]:
        run(exe,[(i,a) for i in range(4) for a in arms],"heavy",N/name)
    proof=[]
    for i in range(4):
        p=N/f"reference/i{i}/R/capture";r=read(p/"receipt.json");baseline=panel.vectors(p,r)
        s=N/f"reference/i{i}/S1/capture";sr=read(s/"receipt.json")
        def branch(d):return {f.name:sha(f) for f in (d/"target").glob("verify-*.f32")}
        for arm in ("S1",*ARMS):
            loc="reference" if arm=="S1" else "historical" if arm=="oldQB" else "changed"
            d=N/loc/f"i{i}/{arm}/capture";c=read(d/"receipt.json");v=panel.vectors(d,c)
            proof.append(dict(i=i,arm=arm,oracle=baseline,vectors=v,endpoint_equal=c["endpoint"]==r["endpoint"],transactions_equal=c["cycles"]==sr["cycles"],branch=branch(d),scalar_branch=branch(s)))
    put(N/"qualification.json",proof)
    assert all(x["endpoint_equal"] and x["transactions_equal"] and x["oracle"]==x["vectors"] and x["branch"]==x["scalar_branch"] for x in proof)
def cost():
    proof=read(N/"qualification.json");assert all(x["endpoint_equal"] and x["transactions_equal"] and x["oracle"]==x["vectors"] and x["branch"]==x["scalar_branch"] for x in proof)
    for session in read(N/"freeze.json")["order"]:
        for row in session:
            i,s,a=row["index"],row["session"],row["arm"];d=N/f"cost-s{s}-i{i}-{a}"
            run(OLD if a=="oldQB" else NEW,[(i,a)],"cost",d)
            ref=read(N/("historical" if a=="oldQB" else "changed")/f"i{i}/{a}/capture/receipt.json")
            for role in ("warm","measured"):
                c=read(d/f"i{i}/{a}/{role}/receipt.json");assert c["endpoint"]==ref["endpoint"] and c["cycles"]==ref["cycles"]
if __name__=="__main__":
    for name in sys.argv[1:]:globals()[name]()

