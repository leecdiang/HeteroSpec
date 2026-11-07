"""Check every original failing PR159 recipe with the frozen RTX application."""
import importlib.util
from pathlib import Path
from audit_focused import vector_files
from focused import PREVIOUS, ROOT, OLD, digest, read, save


def first_difference(left, right):
    return next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),
                min(len(left),len(right)) if len(left)!=len(right) else None)


def main():
    epoch=Path("D:/rtx158/research/epoch01")
    historical=read(epoch/"development01_AUDIT.json")
    assert digest(epoch/"EPOCH.json")==historical["epoch_sha256"]
    bundle=ROOT/"diagnostics04/qwen14b02"
    cfg=read(bundle/"CONFIG.json")
    panel=read(epoch/"DEV.json")
    old=epoch/"units/development01"
    source_slots=read(old/"SLOTS.json")
    failing={(cell["input"],cell["arm"],cell["producer"]) for cell in historical["cells"]
             if cell["input"] in ("GSM8K/test/111","GSM8K/test/120") and not cell["reference_equal"]}
    assert len(failing)==12
    source=PREVIOUS/"benchmarks/rtx_llama_repair_v1/host_execution/qwen_regression.py"
    spec=importlib.util.spec_from_file_location("retained_driver",source)
    lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib);lib.initialize(PREVIOUS)
    binding=read(bundle/"BINDING.json")
    def check(b):
        for n,h in read(b/"EPOCH.json").items():assert digest(b/n)==h
        for n,h in read(ROOT/"FREEZE.json")["families"]["qwen14b02"]["source"].items():assert digest(Path(n))==h
        return cfg
    lib.check_epoch=check
    previous_slots=read(bundle/"units/focused/SLOTS.json")
    reused={(s["input_id"],s["arm"],s["repair"]["prefill"]):s for s in previous_slots}
    requested=[]
    jobs=[]
    for s in source_slots:
        key=s["input_id"],s["arm"],s["repair"]["prefill"]
        if key not in failing or s["observer"]!="heavy":continue
        old_path=old/"native"/(s["slot_id"]+".json")
        assert digest(old_path)==historical["source_record_sha256"][s["slot_id"]]
        oracle_path=OLD/"qwen14b02/units/original_control05/native/original-control"/f"i{s['source_index']:02d}"/"heavy.json"
        oracle=read(oracle_path)
        failed=read(old_path)
        assert failed["input_id"]==oracle["input_id"] and failed["prompt_ids"]==oracle["prompt_ids"]
        assert oracle["endpoint"]==read(epoch/"DEV_REFERENCES.json")[s["input_id"]]
        assert failed["endpoint"]!=oracle["endpoint"]
        if key in reused:
            unit="focused";slot=reused[key]
        else:
            unit="pr159_recipes";slot=dict(s,study_id=lib.STUDY);jobs.append(slot)
        requested.append((key,old_path,oracle_path,unit,slot))
    assert len(requested)==12 and len(jobs)==10
    save(ROOT/"PR159_RECIPE_PREDICTION.json",dict(freeze_sha256=digest(ROOT/"FREEZE.json"),historical_audit_sha256=digest(epoch/"development01_AUDIT.json"),
         scope="Supplement after the fixed panel. Two exact cells already ran before freeze. Ten original failing producer/arm recipes are run here.",
         placement="Host-weight K scale on a four-row verify: 8 scalar rows and 32 batch rows imply scalar preference false, batch true, selected false. Q scale has 40 and 160 rows, both true.",expected="Each recipe preserves the original endpoint and every complete committed target vector under the same frozen structural rules.",cells=[list(key) for key,*_ in requested]))
    fn,_,driver_source,_=lib.driver(cfg["parent_snapshot"],binding)
    anchor="env['CUDA_VISIBLE_DEVICES']"
    assert driver_source.count(anchor)==1
    driver_source=driver_source.replace(anchor,"env['HS_RTX164_TRACE']='1'\n        "+anchor)
    env=dict(fn.__globals__)
    exec(compile(driver_source,"pr159_retained_recipe_supervisor","exec"),env)
    env["run_unit"](bundle,"pr159_recipes",panel,jobs)
    results=[]
    for key,old_path,oracle_path,unit,slot in requested:
        path=bundle/"units"/unit/"native"/(slot["slot_id"]+".json")
        actual,oracle,old_record=read(path),read(oracle_path),read(old_path)
        assert actual["prompt_ids"]==oracle["prompt_ids"]
        a,b=(vector_files(r,f.with_suffix("")) for r,f in ((actual,path),(oracle,oracle_path)))
        mismatches=[i for i,(left,right) in enumerate(zip(a,b)) if left.read_bytes()!=right.read_bytes()]
        results.append(dict(input=key[0],arm=key[1],producer=key[2],unit=unit,old_record_sha256=digest(old_path),
            original_record_sha256=digest(oracle_path),candidate_record_sha256=digest(path),
            historical_first_token_difference=first_difference(old_record["ids"],oracle["ids"]),
            endpoint_equal=actual["endpoint"]==oracle["endpoint"],vector_count=len(a),original_count=len(b),
            different_committed_positions=mismatches))
    save(ROOT/"PR159_RECIPE_AUDIT.json",results)
    assert all(c["endpoint_equal"] and c["vector_count"]==c["original_count"] and not c["different_committed_positions"] for c in results)


if __name__=="__main__":
    main()
