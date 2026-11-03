"""Build an output-free Qwen pool from retained sources and both tokenizer controls."""
from pathlib import Path
import hashlib
import json
from jinja2 import Environment
from tokenizers import Tokenizer
import pyarrow.parquet as pq


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    root=Path("E:/rtx164/pool06")
    root.mkdir()
    data=Path("D:/rtx155/preparation")
    tokenizer_path=Path("D:/HeteroSpec-PC/models/qwen3-14b/tokenizer.json")
    receipt=json.loads((data/"TOKENIZATION.json").read_bytes())
    assert sha(tokenizer_path.read_bytes())==receipt["tokenizer_sha256"]
    tok=Tokenizer.from_file(str(tokenizer_path))
    contract=json.loads(Path("D:/hs144-e5c03228-9eb9-4198-8f14-a7d279d08afa/MODEL_CONTRACT.json").read_bytes())["families"]["Qwen"]
    assert sha(contract["template"].encode())==receipt["template_sha256"]
    template=Environment().from_string(contract["template"])
    def tokenize(raw):
        rendered=template.render(messages=[{"role":"user","content":raw}],add_generation_prompt=True,enable_thinking=False)
        return rendered,tok.encode(rendered,add_special_tokens=True).ids
    historical=json.loads(Path("D:/hs-qb-confirmation-v02/PLAN.json").read_bytes())["panel"]["Qwen"]
    for x in historical:
        rendered,ids=tokenize(x["raw_prompt"])
        assert rendered==x["formatted_prompt"] and ids==x["prompt_ids"]
    rows=[]
    for i,line in enumerate((data/"apps-first1000.jsonl").read_text(encoding="utf-8").splitlines()):
        x=json.loads(line); rows.append(("code","APPS/test/"+str(x.get("problem_id",i)),x["question"],"21e74ddf8de1a21436da12e3e653065c5213e9d1"))
    for p in sorted((data/"math").rglob("test-*.parquet")):
        for i,x in enumerate(pq.read_table(p).to_pylist()):
            rows.append(("math",f"MATH/{p.parent.name}/test/{i}",x["problem"],"21a5633873b6a120296cce3e2df9d5550074f4a3"))
    train=Path("E:/rtx164/math-train")
    for item in json.loads((train/"SOURCE.json").read_bytes()):
        path=train/item["path"]
        assert sha(path.read_bytes())==item["sha256"]
        for i,x in enumerate(pq.read_table(path).to_pylist()):
            rows.append(("math",f"MATH/{path.parent.name}/train/{i}",x["problem"],"21a5633873b6a120296cce3e2df9d5550074f4a3"))
    apps=Path("E:/rtx164/apps-new")
    receipt_apps=json.loads((apps/"SOURCE.json").read_bytes())
    assert sha((apps/"rows.jsonl").read_bytes())==receipt_apps["sha256"]
    for i,line in enumerate((apps/"rows.jsonl").read_text(encoding="utf-8").splitlines(),receipt_apps["first"]):
        x=json.loads(line)
        rows.append(("code","APPS/test/"+str(x.get("problem_id",i)),x["question"],"21e74ddf8de1a21436da12e3e653065c5213e9d1"))
    train_apps=Path("E:/rtx164/apps-train")
    source=json.loads((train_apps/"SOURCE.json").read_bytes())
    assert sha((train_apps/"rows.jsonl").read_bytes())==source["sha256"]
    for i,line in enumerate((train_apps/"rows.jsonl").read_text(encoding="utf-8").splitlines()):
        x=json.loads(line)
        rows.append(("code","APPS/train/"+str(x.get("problem_id",i)),x["question"],"21e74ddf8de1a21436da12e3e653065c5213e9d1"))
    import sys
    sys.path.insert(0,'../pr160/scripts/experiments/rtx_dense14b_transfer_v1')
    from common import prompt_hash
    inputs=[]
    for domain,ident,text,rev in rows:
        prefix="Complete the following Python programming task. Return only the completed Python code, without Markdown fences." if domain=="code" else "Solve the following mathematics problem. Give your reasoning and final answer."
        raw=prefix+"\n\n"+text
        rendered,ids=tokenize(raw)
        if not 64<=len(ids)<=896:continue
        inputs.append(dict(id=ident,domain=domain,source_revision=rev,description=text,raw_prompt=raw,
             formatted_prompt=rendered,prompt_ids=ids,prompt_ids_sha256=prompt_hash(ids),text_sha256=sha(text.strip().encode()),
             formatted_prompt_sha256=sha(rendered.encode()),raw_prompt_sha256=sha(raw.encode()),cap=128))
    (root/"POOL.json").write_text(json.dumps({"inputs":inputs},ensure_ascii=False),encoding="utf-8")
    (root/"PROVENANCE.json").write_text(json.dumps(dict(pool_sha256=sha((root/"POOL.json").read_bytes()),
         tokenization_receipt=receipt,historical_roundtrips=len(historical),model_forwards=0,selected_inputs=0)),encoding="utf-8")


if __name__=="__main__":
    main()

