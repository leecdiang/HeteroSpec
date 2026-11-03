"""Gate candidate freeze on observed RTX transfer, retained controls and old vectors."""
import json
from itertools import groupby
import re
from pathlib import Path
from focused import ROOT, digest, read, save


def main():
    epoch=ROOT/"diagnostics04"
    audit=read(epoch/"COMMITTED_VECTOR_AUDIT.json")
    assert audit and all(x["endpoint_equal"] and not x["different_positions"] for x in audit)
    assert all(x["endpoint_equal"] and x["committed_tokens"] for x in read(ROOT/"llama_controls01/AUDIT.json"))
    facts={}
    for fam in ("qwen8b02","qwen14b02"):
        unit=epoch/fam/"units/focused"
        assert read(unit/"RECEIPT.json")["success"]
        log=(unit/"stderr.log").read_text(encoding="utf-8",errors="replace")
        expected=read(epoch/fam/"PREDICTIONS.json")["boundaries"]
        shapes=set(re.findall(r"RTX164_ATTN layer=0 heads=(\d+) kv_heads=(\d+) rows=(\d+) first=(\d+) last=(\d+) split=(\d+) position=(\d+)",log))
        observed=[]
        slots=read(unit/"SLOTS.json")
        layers=read(epoch/fam/"BINDING.json")["repair_model"]["layers"]
        for x in expected:
            extents=x["extents"]
            wanted=[(extent,len(list(run))) for extent,run in groupby(extents)]
            for arm in ("C_PQ","C_QB"):
                slot,=[s for s in slots if s["arm"]==arm and s["input_id"]==x["input"]]
                record=read(unit/"native"/(slot["slot_id"]+".json"))
                nodes=[n for n in record["geometry"] if n["phase"]=="VERIFY" and n["caller_first_position"]==x["head"] and
                       n["op"]=="MUL_MAT" and n["name"]=="kq-"+str(n["layer"])]
                assert {n["layer"] for n in nodes}==set(range(layers)),(fam,x,arm)
                for layer in range(layers):
                    got=sorted((n["ne"][0],n["ne"][1]*n["ne"][3]) for n in nodes if n["layer"]==layer)
                    # PQ emits one query per QK node. The heavy observer coalesces
                    # identical shapes, so PQ witnesses extents, not multiplicities.
                    expected_qk=wanted if arm=="C_QB" else [(extent,1) for extent,width in wanted]
                    assert got==expected_qk,(fam,x,arm,layer,got,expected_qk)
                observed.append(dict(input=x["input"],head=x["head"],arm=arm,planned_groups=wanted,observed_qk_extent_width=got,
                                     layers_checked=layers,backends=sorted({n["scheduler_backend"] for n in nodes})))
        assert any(row[5]=="1" for row in shapes) and any(row[5]=="0" for row in shapes)
        assert "RTX164_CACHE_BUILD" in log
        changed=sum("scalar=0 batch=1 selected=0" in l for l in log.splitlines() if l.startswith("RTX164_HEAD "))
        if fam=="qwen14b02":
            assert changed>0 and re.search(r"RTX164_HEAD Kcur_normed-\d+ CUDA0 heads=8 rows=4 scalar=0 batch=1 selected=0",log)
            assert re.search(r"RTX164_HEAD Qcur_normed-\d+ CUDA0 heads=40 rows=4 scalar=1 batch=1 selected=1",log)
        else:assert changed==0
        facts[fam]=dict(source=read(epoch/fam/"RUNTIME_SOURCE.json"),expected=expected,
             observed=observed,graph_build_shapes=sorted(shapes),scalar_override_events=changed,epoch_sha256=digest(epoch/fam/"EPOCH.json"))
    save(ROOT/"FREEZE.json",dict(families=facts,qualification_inputs_per_family=4,
         timing_sessions_per_family=3,arms=["R","M_PQ","M_QB","C_PQ","C_QB"],
         prefill="native",candidate_audit_sha256=digest(epoch/"COMMITTED_VECTOR_AUDIT.json"),
         llama_control_sha256=digest(ROOT/"llama_controls01/AUDIT.json")))


if __name__=="__main__":
    main()
