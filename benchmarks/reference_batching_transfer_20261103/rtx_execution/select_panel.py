"""Choose the registered eight inputs after the successful candidate freeze."""
from focused import ROOT, OLD, digest, read, save
import hashlib
import json

FIELDS=("id","text_sha256","prompt_ids_sha256","formatted_prompt_sha256","raw_prompt_sha256")


def keys(record):
    return {record[k] for k in FIELDS if record.get(k)}


def main():
    freeze=read(ROOT/"FREEZE.json")
    source=ROOT/"exposure-pr163"
    audit=read(source/"EXPOSURE_AUDIT-00.json")
    assert audit["complete"] and not audit["unresolved_sources"]
    excluded=set(audit["keys"])
    for item in read(source/"EXPOSURES.json")+read(ROOT.parent/"rtx160/exposure04/EXPOSURES.json"):
        excluded.update(keys(item))
    for path in (source/"EXPOSURE.jsonl",OLD/"epoch07/HELDOUT.json"):
        rows=[json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.suffix==".jsonl" else read(path)["inputs"]
        for row in rows:excluded.update(keys(row))
    for fam in ("qwen8b02","qwen14b02"):
        for row in read(OLD/fam/"DEV.json")["inputs"]:excluded.update(keys(row))
    other=read(ROOT/"exposure-pr165/UNSEEN.json")
    assert len(other)==8
    for row in other.values():
        excluded.update(keys(row))
        for field in ("text","raw_prompt","formatted_prompt"):
            excluded.add(hashlib.sha256(row[field].strip().encode()).hexdigest())
    pool=ROOT/"pool06/POOL.json"
    assert digest(pool)==read(pool.parent/"PROVENANCE.json")["pool_sha256"]
    available=[x for x in read(pool)["inputs"] if len(x["prompt_ids"])<=892 and keys(x).isdisjoint(excluded)]
    out=ROOT/"selection01";out.mkdir()
    seed=digest(ROOT/"FREEZE.json")
    for fam in freeze["families"]:
        selected=[]
        for near in (True,False):
            for domain in ("code","math"):
                candidates=[]
                for x in available:
                    d=len(x["prompt_ids"])%256
                    eligible=(d in (253,254,255,0,1)) if near else min(d,256-d)>=32
                    if eligible and keys(x).isdisjoint(excluded):candidates.append(x)
                preferred=[x for x in candidates if x["domain"]==domain]
                options=preferred or candidates
                if near:
                    before=[x for x in options if len(x["prompt_ids"])%256>=253]
                    options=before or options
                x=min(options,key=lambda row:hashlib.sha256((seed+fam+str(near)+domain+row["id"]).encode()).digest())
                selected.append(dict(x,stratum="boundary-near" if near else "ordinary"))
                excluded.update(keys(x))
        save(out/(fam+".json"),dict(inputs=selected,freeze_sha256=seed,pool_sha256=digest(pool)))
    save(out/"SELECTION.json",dict(seed=seed,eligible=len(available),source_audit_sha256=digest(source/"EXPOSURE_AUDIT-00.json"),model_forwards=0))


if __name__=="__main__":
    main()
