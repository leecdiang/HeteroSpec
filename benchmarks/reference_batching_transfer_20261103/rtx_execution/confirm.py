"""Execute the frozen old oracle, heavy qualification and fixed paired cost panel."""
import importlib.util
import math
import statistics
import sys
from pathlib import Path
from audit_focused import vector_files
from focused import PREVIOUS, OLD, ROOT, digest, read, save

ARMS=("R","M_PQ","M_QB","C_PQ","C_QB")


def mean_ratio(values):
    return math.exp(statistics.mean(math.log(v) for v in values))


def run_family(lib,fam,mode):
    import plan
    diag=ROOT/"diagnostics04"/fam
    parent=ROOT/"confirmation01";parent.mkdir(exist_ok=True)
    b=parent/fam
    cfg=read(diag/"CONFIG.json")
    binding,original=(read(diag/name) for name in ("BINDING.json","ORIGINAL_BINDING.json"))
    panel_path=ROOT/"selection01"/(fam+".json")
    panel=read(panel_path)
    assert panel["freeze_sha256"]==digest(ROOT/"FREEZE.json")
    pins=read(ROOT/"FREEZE.json")["families"][fam]["source"]
    def check(bundle):
        for path,h in pins.items():assert digest(Path(path))==h
        for n,h in read(bundle/"EPOCH.json").items():assert digest(bundle/n)==h
        assert digest(Path(cfg["original_worker"]))==original["families"]["Qwen"]["executable_sha256"]
        return cfg
    lib.check_epoch=check
    def make(i,arm,observer,key,category):
        s=plan.slot(panel,i,arm,"native",observer,key,category)
        s["study_id"]=lib.STUDY
        return s
    if mode=="qualify":
        b.mkdir()
        for n,x in [("CONFIG.json",cfg),("BINDING.json",binding),("ORIGINAL_BINDING.json",original),
                    ("PLAN.json",read(diag/"PLAN.json")),("PANEL.json",panel)]:
            save(b/n,x)
        timing={}
        for session in range(3):
            slots=[]
            for step in range(4):
                i=(step+session)%4
                for k in range(5):
                    arm=ARMS[(k+i+session)%5]
                    for role in ("warmup","measured"):
                        slots.append(make(i,arm,"off",f"s{session}/i{i}/{arm}/{role}",role))
            timing[str(session)]=slots
        save(b/"TIMING_PLAN.json",timing)
        save(b/"EPOCH.json",{p.name:digest(p) for p in b.iterdir() if p.is_file()})
        save(b/"CANDIDATE_FREEZE.json",dict(epoch_sha256=digest(b/"EPOCH.json"),freeze_sha256=digest(ROOT/"FREEZE.json")))
        save(b/"EXPOSURE_BEFORE_LAUNCH.json",dict(inputs=[x["id"] for x in panel["inputs"]],panel_sha256=digest(panel_path)))
        old_fn,_,_,audit=lib.driver(cfg["parent_snapshot"],original)
        def transaction(record):
            assert record["identity"]==original["families"]["Qwen"]
            inventory=read(next((OLD/fam/"units/regression/native").rglob("R/native/heavy.json")))["vocabulary_eog"]
            assert record["eog"]==[token in inventory for token in record["ids"]]
            audit.transaction_check(dict(record,vocabulary_eog=inventory))
        def states(record,folder):
            if fam=="qwen14b02":audit.verify_states(record,folder)
            else:assert not record.get("target_state") and not list(Path(folder).glob("*_final.state"))
        old_fn.__globals__.update(transaction_check=transaction,verify_states=states)
        slots=[make(i,"R","heavy",f"old/i{i}/heavy","qualification") for i in range(4)]
        for s in slots:s["study_id"]="rtx_dense14b_transfer_v1" if fam=="qwen14b02" else "rtx_scope_transfer_v1"
        old_fn(b,"original",panel,slots,original=True)
        candidate,_,_,_=lib.driver(cfg["parent_snapshot"],binding)
        slots=[make(i,arm,obs,f"qual/i{i}/{arm}/{obs}","qualification") for i in range(4) for arm in ARMS
               for obs in (("heavy","off") if i==0 else ("heavy",))]
        candidate(b,"qualification",panel,slots)
        cells=[]
        for i in range(4):
            op=b/"units/original/native/old"/f"i{i}"/"heavy.json";oracle=read(op)
            originals=vector_files(oracle,op.with_suffix(""))
            prefix=b/"units/qualification/native/qual"/f"i{i}"
            rs={}
            for arm in ARMS:
                path=prefix/arm/"heavy.json";record=read(path);rs[arm]=record
                v=vector_files(record,path.with_suffix(""))
                eq=record["endpoint"]==oracle["endpoint"]
                mismatches=[pos for pos,(x,y) in enumerate(zip(v,originals)) if x.read_bytes()!=y.read_bytes()]
                observer=(i!=0 or all(read(prefix/arm/"off.json")[k]==record[k] for k in ("endpoint","cycles")))
                cells.append(dict(input=record["input_id"],arm=arm,endpoint_equal=eq,observer_equal=observer,
                    vector_count=len(v),original_count=len(originals),different_vector_positions=mismatches))
            for scope in ("M","C"):
                a,c=(rs[scope+"_"+layout] for layout in ("PQ","QB"))
                assert a["cycles"]==c["cycles"],(i,scope,"transaction mismatch")
                for role in ("target","draft"):
                    dirs=[prefix/(scope+"_"+layout)/"heavy"/role for layout in ("PQ","QB")]
                    tables=[{p.name:digest(p) for p in folder.glob("*.f32")} for folder in dirs]
                    assert tables[0]==tables[1],(i,scope,role,"conditional row mismatch")
        save(b/"QUALIFICATION.json",cells)
        assert all(c["endpoint_equal"] and c["observer_equal"] and c["vector_count"]==c["original_count"] and not c["different_vector_positions"] for c in cells)
        save(b/"QUALIFICATION_PASS.json",dict(cells=len(cells)))
    else:
        for f in ("qwen8b02","qwen14b02"):assert (parent/f/"QUALIFICATION_PASS.json").is_file()
        candidate,_,_,_=lib.driver(cfg["parent_snapshot"],binding)
        blocks=[]
        for session,slots in read(b/"TIMING_PLAN.json").items():
            rows=candidate(b,"formal"+session,panel,slots)
            for i in range(4):
                oracle=read(b/"units/original/native/old"/f"i{i}"/"heavy.json")
                times={}
                for r in rows:
                    if r["slot"]["source_index"]!=i:continue
                    assert not r["capture"] and r["endpoint"]==oracle["endpoint"]
                    if r["slot"]["category"]=="measured":times[r["arm"]]=r["service_seconds"]
                assert set(times)==set(ARMS)
                blocks.append(times)
        pairs=[("M_QB","M_PQ"),("C_QB","C_PQ"),("M_QB","C_QB")]+[(a,"R") for a in ARMS[1:]]
        by_input={panel["inputs"][i]["id"]:{f"{a}/{c}":sum(blocks[j*4+i][a] for j in range(3))/sum(blocks[j*4+i][c] for j in range(3)) for a,c in pairs} for i in range(4)}
        by_session=[{f"{a}/{c}":mean_ratio([blocks[j*4+i][a]/blocks[j*4+i][c] for i in range(4)]) for a,c in pairs} for j in range(3)]
        save(b/"COST.json",dict(blocks=blocks,input_ratios=by_input,session_ratios=by_session,
            ratios={f"{a}/{c}":mean_ratio([v[f"{a}/{c}"] for v in by_input.values()]) for a,c in pairs}))


if __name__=="__main__":
    source=PREVIOUS/"benchmarks/rtx_llama_repair_v1/host_execution/qwen_regression.py"
    spec=importlib.util.spec_from_file_location("retained_driver",source)
    lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib);lib.initialize(PREVIOUS)
    lib.parent.load("E:/rtx160/parent159")
    for mode in ("qualify","cost"):
        for fam in ("qwen8b02","qwen14b02"):run_family(lib,fam,mode)
