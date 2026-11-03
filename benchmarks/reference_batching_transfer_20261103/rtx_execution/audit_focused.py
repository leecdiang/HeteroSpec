"""Compare complete committed target-vector bytes against the retained immutable R."""
import json
import hashlib
from pathlib import Path
import sys


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def vector_files(record, folder):
    output = [folder/"target/initial.f32"]
    if record["draft_enabled"]:
        for cycle in record["cycles"]:
            width = cycle["output_length"] - len(output)
            assert 0 <= width <= len(cycle["decisions"])
            output.extend(folder/"target"/f"verify-{cycle['cycle']}-{i}.f32" for i in range(width))
    else:
        output.extend(folder/"target"/f"ordinary-{i}.f32" for i in range(1,len(record["ids"])))
    assert len(output)==len(record["ids"])
    return output


def main(epoch):
    reports=[]
    for fam,control in [("qwen8b02","original_control03"),("qwen14b02","original_control05")]:
        unit=epoch/fam/"units/focused"
        assert load(unit/"RECEIPT.json")["success"]
        old=Path("E:/rtx160/research")/fam/"units"/control/"native"
        for slot in load(unit/"SLOTS.json"):
            candidate=unit/"native"/(slot["slot_id"]+".json")
            reference=old/"original-control"/f"i{slot['source_index']:02d}"/"heavy.json"
            r,o=load(candidate),load(reference)
            assert r["input_id"]==o["input_id"] and r["prompt_ids"]==o["prompt_ids"]
            endpoints=all(r[k]==o[k] for k in ("ids","eog","length","terminal_id","stop_reason"))
            a=vector_files(r,candidate.with_suffix(""))
            b=vector_files(o,reference.with_suffix(""))
            differences=[i for i,(x,y) in enumerate(zip(a,b)) if x.read_bytes()!=y.read_bytes()]
            reports.append(dict(family=fam,slot=slot["slot_id"],input=r["input_id"],endpoint_equal=endpoints,
                                compared=min(len(a),len(b)),different_positions=differences))
    with (epoch/"COMMITTED_VECTOR_AUDIT.json").open("x",encoding="utf-8") as f:
        json.dump(reports,f,indent=2)
    print(len(reports),"requests;",sum(not r["endpoint_equal"] for r in reports),"endpoint failures;",
          sum(len(r["different_positions"]) for r in reports),"different committed vectors")


if __name__=="__main__":
    main(Path(sys.argv[1]))
