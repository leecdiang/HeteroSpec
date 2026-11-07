from host import *
CELLS=[(b,q,b-q if not cross else b-3,cross) for b in (256,1024) for q in (8,32) for cross in (False,True)]
ARMS=["S1","QB4","WB4","newQB","newWB"]
def family(arm):return "S1" if arm=="S1" else "WB-cut" if "WB" in arm else "QB-local"
def create():
    freeze=ROOT/"matrix.json"
    plan=[]
    for rep in range(3):
        for i,(b,q,h,cross) in enumerate(CELLS):
            for a in range(5):
                arm=ARMS[(a+i+rep)%5]
                plan.append(dict(block=rep,cell=i,arm=arm,id=f"s{rep}-c{i}-{arm}",pos=h,width=q))
    put(freeze,dict(cells=CELLS,arms=ARMS,plan=plan,fixture="113+(i*173)%2309",oracle_core=sha(ORIG/"core/src/libllama.a")))
def prefixes():
    units=[unit(f"h{pos}","prefix","S1",pos,1) for pos in sorted({x[2] for x in CELLS})]
    launch("prefix01","oracle01",dict(units=units))
def qualify():
    for build_id,arms in [("oracle01",["R"]),("capture01",["S1","QB4","WB4"]),("new-driver",["newQB","newWB"])]:
        units=[unit(f"c{i}-{arm}","qual",family(arm) if arm!="R" else "S1",h,q) for i,(b,q,h,cross) in enumerate(CELLS) for arm in arms]
        launch("qual-"+build_id,build_id,dict(units=units))
    audit=[]
    for i,(b,q,h,cross) in enumerate(CELLS):
        ref=ROOT/"qual-oracle01"/f"c{i}-R"
        for arm in ARMS:
            p=ROOT/("qual-new-driver" if arm.startswith("new") else "qual-capture01")/f"c{i}-{arm}"
            for f in sorted(ref.glob("*.f32")):
                audit.append(dict(cell=i,arm=arm,row=f.name,oracle=sha(f),actual=sha(p/f.name)))
    put(ROOT/"matrix-qual.json",audit);assert all(x["actual"]==x["oracle"] for x in audit)
def cost():
    audit=read(ROOT/"matrix-qual.json");assert all(x["actual"]==x["oracle"] for x in audit)
    for row in read(ROOT/"matrix.json")["plan"]:
        arm=row["arm"];units=[unit(role,"cost",family(arm),row["pos"],row["width"]) for role in ("warm","measured")]
        launch("cost/"+row["id"],"new-driver" if arm.startswith("new") else "capture01",dict(units=units))
if __name__=="__main__":
    import sys
    for stage in sys.argv[1:]:globals()[stage]()

