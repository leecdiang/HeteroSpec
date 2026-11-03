"""Gate candidate freeze on observed RTX transfer, retained controls and old vectors."""
import json
import hashlib
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
        for x in expected:
            e=x["extents"]
            assert any((int(row[2]),int(row[3]),int(row[4]),int(row[5]),int(row[6]))==(len(e),e[0],e[-1],int(e[0]!=e[-1]),x["head"]) for row in shapes),x
        assert any(row[5]=="1" for row in shapes) and any(row[5]=="0" for row in shapes)
        assert "RTX164_CACHE_BUILD" in log
        changed=sum("scalar=0 batch=1 selected=0" in l for l in log.splitlines() if l.startswith("RTX164_HEAD "))
        if fam=="qwen14b02":
            assert changed>0 and re.search(r"RTX164_HEAD Kcur_normed-\d+ CUDA0 heads=8 rows=4 scalar=0 batch=1 selected=0",log)
            assert re.search(r"RTX164_HEAD Qcur_normed-\d+ CUDA0 heads=40 rows=4 scalar=1 batch=1 selected=1",log)
        else:assert changed==0
        facts[fam]=dict(source=read(epoch/fam/"RUNTIME_SOURCE.json"),expected=expected,
             observed=sorted(shapes),scalar_override_events=changed,epoch_sha256=digest(epoch/fam/"EPOCH.json"))
    save(ROOT/"FREEZE.json",dict(families=facts,qualification_inputs_per_family=4,
         timing_sessions_per_family=3,arms=["R","M_PQ","M_QB","C_PQ","C_QB"],
         prefill="native",candidate_audit_sha256=digest(epoch/"COMMITTED_VECTOR_AUDIT.json"),
         llama_control_sha256=digest(ROOT/"llama_controls01/AUDIT.json")))


if __name__=="__main__":
    main()
