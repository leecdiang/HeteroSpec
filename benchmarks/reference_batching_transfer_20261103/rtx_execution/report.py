"""Publish compact results only after both qualifications and all registered blocks pass."""
from pathlib import Path
import json,shutil,subprocess
from focused import ROOT, read, save, digest

DEST=Path(__file__).resolve().parent
FAMILIES=("qwen8b02","qwen14b02")


def main():
    out=DEST/"evidence";out.mkdir()
    freeze=read(ROOT/"FREEZE.json")
    shutil.copy2(ROOT/"FREEZE.json",out/"FREEZE.json")
    shutil.copy2(ROOT/"llama_controls01/AUDIT.json",out/"LLAMA_CONTROLS.json")
    shutil.copy2(ROOT/"diagnostics04/COMMITTED_VECTOR_AUDIT.json",out/"RETAINED_R.json")
    shutil.copy2(ROOT/"diagnostics04/LEDGER.jsonl",out/"LEDGER.jsonl")
    table=[]
    for fam in FAMILIES:
        b=ROOT/"confirmation01"/fam
        q=read(b/"QUALIFICATION.json");cost=read(b/"COST.json")
        assert (b/"QUALIFICATION_PASS.json").is_file() and len(cost["blocks"])==12
        files=["QUALIFICATION.json","QUALIFICATION_PASS.json","TIMING_PLAN.json","COST.json","PANEL.json","CANDIDATE_FREEZE.json","EPOCH.json"]
        folder=out/fam;folder.mkdir()
        for n in files:shutil.copy2(b/n,folder/n)
        times=[]
        for session in range(3):
            u=b/"units"/f"formal{session}"
            assert read(u/"RECEIPT.json")["completed_requests"]==40
            rows=[read(u/"native"/(s["slot_id"]+".json")) for s in read(u/"SLOTS.json")]
            for warm,measured in zip(rows[::2],rows[1::2]):
                assert warm["slot"]["category"]=="warmup" and measured["slot"]["category"]=="measured"
                assert warm["arm"]==measured["arm"] and warm["input_id"]==measured["input_id"]
            times.append(dict(session=session,load=read(u/"native/PROVISIONED.json")["model_load_seconds"],
                              requests=[dict(slot=r["slot"]["slot_id"],arm=r["arm"],input=r["input_id"],seconds=r["service_seconds"]) for r in rows]))
        save(folder/"SERVICE.json",dict(sessions=times,original_reference_supervised_seconds=read(b/"units/original/RECEIPT.json")["seconds"]))
        table.append((fam,len(q),sum(x["vector_count"] for x in q),cost["ratios"]))
    receipts={str(p.relative_to(out)):digest(p) for p in out.rglob("*") if p.is_file()}
    save(out/"INDEX.json",receipts)
    lines=["# RTX shared planner transfer","", "The frozen candidate passed the retained original-R controls and all eight unseen inputs. The fixed cost panel completed 120 measured requests and 120 immediate warmups.","",
           "| Family | Heavy qualification cells | Committed vectors | M_QB/M_PQ | C_QB/C_PQ | M_QB/C_QB | M_QB/R | C_QB/R |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for fam,cells,v,ratios in table:
        lines.append("| "+str(fam)+" | "+str(cells)+" | "+str(v)+" | "+" | ".join(f"{ratios[k]:.6f}" for k in ["M_QB/M_PQ","C_QB/C_PQ","M_QB/C_QB","M_QB/R","C_QB/R"])+" |")
    lines+=["","FREEZE.json records the predicted and observed groups, scalar placement override counts and executed source identities. The 8B all-GPU cohort and partially offloaded 14B cohort are reported separately. The retained audit and Llama control receipts are under evidence/. The per-family SERVICE.json separates loading, reference preparation and every warmup and measured service interval.",
            "", "The first exploratory epoch inherited a stale static-core digest. The final diagnostics bind the actual compiled libraries and executables. Earlier attempts remain under E:/rtx164. No experimental outcome depends on changing the original R.",
            "", "Reproduction order: authenticate PR162 sources, stage CUDA through integrate_llama_cpp.py, build the two pinned cohorts, then run focused.py, audit_focused.py, llama_controls.py, freeze.py, select_panel.py and confirm.py. Prepare pool.py before selection. Saved native raw is under E:/rtx164 on the RTX host."]
    (DEST/"RESULTS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
