"""Publish compact results only after both qualifications and all registered blocks pass."""
from pathlib import Path
import shutil
from focused import ROOT, read, save, digest

DEST=Path(__file__).resolve().parent
FAMILIES=("qwen8b02","qwen14b02")


def main():
    for fam in FAMILIES:assert (ROOT/"confirmation01"/fam/"COST.json").is_file()
    from retained_recipes import main as check_original_recipes
    check_original_recipes()
    out=DEST/"evidence";out.mkdir()
    shutil.copy2(ROOT/"PR159_RECIPE_AUDIT.json",out/"PR159_RECIPE_AUDIT.json")
    shutil.copy2(ROOT/"PR159_RECIPE_PREDICTION.json",out/"PR159_RECIPE_PREDICTION.json")
    freeze=read(ROOT/"FREEZE.json")
    shutil.copy2(ROOT/"FREEZE.json",out/"FREEZE.json")
    shutil.copy2(ROOT/"llama_controls01/AUDIT.json",out/"LLAMA_CONTROLS.json")
    shutil.copy2(ROOT/"diagnostics04/COMMITTED_VECTOR_AUDIT.json",out/"RETAINED_R.json")
    shutil.copy2(ROOT/"diagnostics04/LEDGER.jsonl",out/"LEDGER.jsonl")
    for cohort in ("qwen_config01","config06"):
        shutil.copy2(ROOT/"active03"/cohort/"BUILD.json",out/(cohort+"_BUILD.json"))
    table=[]
    preparation=[]
    for fam in FAMILIES:
        b=ROOT/"confirmation01"/fam
        q=read(b/"QUALIFICATION.json");cost=read(b/"COST.json")
        assert (b/"QUALIFICATION_PASS.json").is_file() and len(cost["blocks"])==12
        files=["QUALIFICATION.json","QUALIFICATION_PASS.json","TIMING_PLAN.json","COST.json","PANEL.json","CANDIDATE_FREEZE.json","EPOCH.json"]
        folder=out/fam;folder.mkdir()
        for n in files:shutil.copy2(b/n,folder/n)
        times=[]
        for session in range(3):
            u=b/"units"/cost["units"][str(session)]
            assert read(u/"RECEIPT.json")["completed_requests"]==40
            rows=[read(u/"native"/(s["slot_id"]+".json")) for s in read(u/"SLOTS.json")]
            for warm,measured in zip(rows[::2],rows[1::2]):
                assert warm["slot"]["category"]=="warmup" and measured["slot"]["category"]=="measured"
                assert warm["arm"]==measured["arm"] and warm["input_id"]==measured["input_id"]
            times.append(dict(session=session,load=read(u/"native/PROVISIONED.json")["model_load_seconds"],
                              requests=[dict(slot=r["slot"]["slot_id"],arm=r["arm"],input=r["input_id"],seconds=r["service_seconds"]) for r in rows]))
        reference_seconds=read(b/"units/original/RECEIPT.json")["seconds"]
        qualification_seconds=read(b/"units/qualification/RECEIPT.json")["seconds"]
        warm=sum(r["seconds"] for session in times for r in session["requests"] if r["slot"].endswith("/warmup"))
        measured=sum(r["seconds"] for session in times for r in session["requests"] if r["slot"].endswith("/measured"))
        load=sum(session["load"] for session in times)
        save(folder/"SERVICE.json",dict(sessions=times,original_reference_supervised_seconds=reference_seconds,
              qualification_supervised_seconds=qualification_seconds,formal_model_loading_seconds=load,
              warmup_service_seconds=warm,measured_service_seconds=measured))
        preparation.append((fam,reference_seconds,qualification_seconds,load,warm,measured))
        panel=read(b/"PANEL.json")["inputs"]
        reversals={}
        for contrast,aggregate in cost["ratios"].items():
            numerator,denominator=contrast.split("/")
            reversals[contrast]=[]
            for ix,block in enumerate(cost["blocks"]):
                ratio=block[numerator]/block[denominator]
                if (ratio-1)*(aggregate-1)<0:
                    reversals[contrast].append(dict(session=ix//4,input=panel[ix%4]["id"],ratio=ratio))
        save(folder/"BLOCK_REVERSALS.json",reversals)
        shutil.copy2(b/"ORIGINAL_BINDING.json",folder/"ORIGINAL_BINDING.json")
        table.append((fam,len(q),sum(x["vector_count"] for x in q),cost["ratios"]))
    failed=ROOT/"confirmation01/qwen8b02/units/formal0"
    save(out/"TIMING_PREPARATION_FAILURE.json",dict(receipt=read(failed/"RECEIPT.json"),
        events=[__import__("json").loads(l) for l in (failed/"EVENTS.jsonl").read_text(encoding="utf-8").splitlines()],
        reference_index_repair="Derived from the already validated original-R endpoints. No measured request existed in this attempt. The unchanged order was executed in the successor unit."))
    receipts={str(p.relative_to(out)):digest(p) for p in out.rglob("*") if p.is_file()}
    save(out/"INDEX.json",receipts)
    lines=["# RTX shared planner transfer","", "The frozen candidate passed the retained original-R controls and all eight unseen inputs. The fixed cost panel completed 120 measured requests and 120 immediate warmups.","",
           "| Family | Heavy qualification cells | Committed vectors | M_QB/M_PQ | C_QB/C_PQ | M_QB/C_QB | M_PQ/R | M_QB/R | C_PQ/R | C_QB/R |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for fam,cells,v,ratios in table:
        lines.append("| "+str(fam)+" | "+str(cells)+" | "+str(v)+" | "+" | ".join(f"{ratios[k]:.6f}" for k in ["M_QB/M_PQ","C_QB/C_PQ","M_QB/C_QB","M_PQ/R","M_QB/R","C_PQ/R","C_QB/R"])+" |")
    lines.extend(["","| Family | Original R preparation (s) | Qualification (s) | Formal model loading (s) | Warmup service (s) | Measured service (s) |",
                  "|---|---:|---:|---:|---:|---:|"])
    for fam,*values in preparation:
        lines.append("| "+fam+" | "+" | ".join(f"{v:.3f}" for v in values)+" |")
    lines.extend(["","The supervisor stopped the first 8B timing attempt after one unpaired warmup because its reference-index file was missing. That warmup and its receipt remain charged separately. Zero measured requests occurred in the failed attempt. The published panel uses the original registered order and includes every matched block.","","The old executable supplied each qualification reference. The timed R arm uses the candidate runtime's ordinary path after its complete committed vectors match that reference. Per-session ratios, input ratios, every service interval and the blocks on the opposite side of one from each aggregate are recorded under evidence/."])
    lines.extend(["","| Family | Input and start position | Layout | Planned (extent, width) | Observed QK (extent, width) | Layers |",
                  "|---|---|---|---|---|---:|"])
    for fam in FAMILIES:
        for cell in freeze["families"][fam]["observed"]:
            lines.append(f"| {fam} | {cell['input']} at {cell['head']} | {cell['arm']} | {cell['planned_groups']} | {cell['observed_qk_extent_width']} | {cell['layers_checked']} |")
    lines.append("")
    for fam in FAMILIES:
        lines.append(f"{fam} recorded {freeze['families'][fam]['scalar_override_events']} host-weight placement queries where scalar and batch preferences differed and the scalar preference was selected.")
        lines.append("")
    lines.extend(["","PR159 recorded twelve failing input/arm/producer combinations across GSM8K/test/111 and GSM8K/test/120. Two identical recipes were covered before freeze. A review of the historical failure ledger found ten missing recipes; these were tested after the fixed panel, using the same frozen binary. PR159_RECIPE_AUDIT.json records the historical first differing token, the exact old and new record identities and the complete committed-vector comparison for each recipe."])
    lines.extend(["","| PR159 input | Arm | Producer | Historical first token difference (zero-based) | Frozen endpoint | Different committed vectors |",
        "|---|---|---|---:|---|---:|"])
    for c in read(ROOT/"PR159_RECIPE_AUDIT.json"):
        lines.append(f"| {c['input']} | {c['arm']} | {c['producer']} | {c['historical_first_token_difference']} | {c['endpoint_equal']} | {len(c['different_committed_positions'])}/{c['vector_count']} |")
    lines+=["","FREEZE.json records the predicted and observed groups, scalar placement override counts and executed source identities. The 8B all-GPU cohort and partially offloaded 14B cohort are reported separately. The retained audit and Llama control receipts are under evidence/. The per-family SERVICE.json separates loading, reference preparation and every warmup and measured service interval.",
            "", "The first exploratory epoch inherited a stale static-core digest. The final diagnostics bind the actual compiled libraries and executables. Earlier attempts remain under E:/rtx164. No experimental outcome depends on changing the original R.",
            "", "Reproduction order: authenticate PR162 sources, stage CUDA through integrate_llama_cpp.py, build the two pinned cohorts, then run focused.py, audit_focused.py, llama_controls.py, freeze.py, select_panel.py and confirm.py. Prepare pool.py before selection. Saved native raw is under E:/rtx164 on the RTX host."]
    (DEST/"RESULTS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
