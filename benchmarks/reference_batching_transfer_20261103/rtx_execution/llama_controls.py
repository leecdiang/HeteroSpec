"""Run the retained Llama boundary and ordinary control under the same candidate."""
import sys
from pathlib import Path
from focused import ROOT, PREVIOUS, OLD, digest, read, save

sys.path.insert(0,str(PREVIOUS/"scripts/experiments/rtx_llama_repair_v1"))
import host
import parent


def main():
    base=OLD/"epoch07"
    out=ROOT/"llama_controls01"
    out.mkdir()
    build=ROOT/"active03/config06"
    cfg=read(base/"CONFIG.json")
    cfg.update(worker=str(build/"bin/rtx-scope-transfer.exe"),research_root=str(ROOT/"diagnostics04"),
               request_limit=1200,development_limit=480)
    cfg["resources"].update(total_native_seconds=86400,worker_timeout_seconds=7200)
    binding=read(base/"BINDING.json")
    binding["families"]["Llama"].update(build_receipt_sha256=digest(build/"BUILD.json"),executable_sha256=digest(Path(cfg["worker"])),
        core_sha256=digest(build/"core/src/libllama.a"),worker_source_sha256=digest(build/"worker.cpp"))
    panel=read(base/"units/development/PANEL.json")
    slots=[s for s in read(base/"units/development/SLOTS.json") if s["input_id"] in
           ("CodeContests/valid/108","GSM8K/test/496") and s["arm"]=="C_QB" and s["observer"]=="heavy"]
    assert len(slots)==2
    for n,j in [("CONFIG.json",cfg),("BINDING.json",binding),("PLAN.json",read(base/"PLAN.json")),
                ("ORIGINAL_BINDING.json",read(base/"ORIGINAL_BINDING.json")),
                ("PREDICTIONS.json",{"CodeContests/valid/108":"cycle 8 at head 765: extents 768,768,768,1024",
                 "GSM8K/test/496":"ordinary control, compare all original endpoint tokens"})]:
        save(out/n,j)
    _,runner,audit=parent.load(cfg["parent_snapshot"])
    fn,_,_=host.derive_driver(runner,audit,binding)
    fn.__globals__["check_epoch"]=lambda _:cfg
    fn(out,"admission",panel,slots[:1],admit=True)
    results=fn(out,"retained",panel,slots)
    comparisons=[]
    for s,r in zip(slots,results):
        old=read(base/"units/development/native"/(s["slot_id"]+".json"))
        assert r["prompt_ids"]==old["prompt_ids"]
        old_folder=base/"units/development/native"/s["slot_id"]
        new_folder=out/"units/retained/native"/s["slot_id"]
        previous={f.relative_to(old_folder).as_posix():digest(f) for role in ("target","draft") for f in (old_folder/role).glob("*.f32")}
        current={f.relative_to(new_folder).as_posix():digest(f) for role in ("target","draft") for f in (new_folder/role).glob("*.f32")}
        comparisons.append(dict(id=r["input_id"],all_vectors_equal=previous==current,vector_count=len(current),endpoint_equal=r["endpoint"]==old["endpoint"],
          committed_tokens=r["ids"]==old["ids"]))
    save(out/"AUDIT.json",comparisons)
    assert all(x["all_vectors_equal"] and x["endpoint_equal"] and x["committed_tokens"] for x in comparisons)


if __name__=="__main__":
    main()
