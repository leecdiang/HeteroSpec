"""Recompute numerical gates, executed widths and paired ratios from delivered receipts."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import geometric_mean
HERE=Path(__file__).resolve().parent
E=HERE/"evidence"
def read(name):
    content=(E/name).read_bytes()
    return json.loads(gzip.decompress(content) if name.endswith(".gz") else content)
def check(condition,detail):
    if not condition:raise ValueError(detail)
def main():
    mech=read("mechanism.json")
    raw=read("mechanism-raw.json.gz")
    hashes={r["cell"]:r["vectors"] for r in raw}
    passed=0
    for r in mech:
        folder=f"probes/{r['attempt']}/{r['base']}-{r['width']}-"
        if r["exit"]:continue
        a=hashes[folder+r["arm"]];b=hashes[folder+"oracle"]
        differences=[i for i in range(r["width"]) if a[f"{i}.f32"]!=b[f"{i}.f32"]]
        check(differences==r["mismatch_rows"],folder)
        if r["attempt"] not in ("first","tilefix") and r["arm"]!="native":
            check(not differences and r["predicted_calls"]==r["actual_calls"],folder)
            if r["predicted_attention_tiles"]:
                observed=[s[2] for s in r["actual_layer0_qk"]]
                check(observed==r["predicted_attention_tiles"],(folder,r["arm"],observed))
                passed+=1
    oracle={(o["ctx"],o["input"]):o for o in read("oracles.json.gz")}
    captures=read("qualification-raw.json.gz")
    by={(r["ctx"],r["input"],r["arm"]):r for r in captures}
    qual=read("qualification.json")
    committed=0
    for x in qual:
        key=(x["ctx"],x["input"]);o=oracle[key];cell=by[(*key,x["arm"])]
        r=cell["receipt"];h=cell["hashes"]
        v=[h["target/initial.f32"]]
        if r["draft_enabled"]:
            for c in r["cycles"]:
                n=c["output_length"]-len(v)
                v.extend(h[f"target/verify-{c['cycle']}-{j}.f32"] for j in range(n))
        else:v.extend(h[f"target/ordinary-{j}.f32"] for j in range(1,len(r["ids"])))
        bad=[i for i in range(max(len(v),len(o["vectors"]))) if v[i:i+1]!=o["vectors"][i:i+1]]
        check(bad==x["different"],key)
        check((r["ids"]==o["ids"])==x["endpoint"],key)
        if x["arm"] in ("S1","PQ-ext","QB-local","WB-cut","R"):
            check(not bad and x["endpoint"],key);committed+=len(v)
            if r["draft_enabled"]:
                s=by[(*key,"S1")]
                for k in set(h)|set(s["hashes"]):
                    if k.startswith("target/verify-"):check(h.get(k)==s["hashes"].get(k),k)
                check(r["cycles"]==s["receipt"]["cycles"],key)
    timing=read("timing-raw.json.gz");blocks={}
    for row in timing:
        r=row["receipt"];key=(row["ctx"],row["input"],row["session"],row["arm"])
        check(not r["capture"] and r["endpoint"]==by[(key[0],key[1],key[3])]["receipt"]["endpoint"],key)
        blocks.setdefault(key,{})[row["role"]]=r["service_seconds"]
    check(len(blocks)==64 and all(set(v)=={"warm","timed"} for v in blocks.values()),"incomplete blocks")
    cost=read("cost.json")
    for arm,ratio in cost["ratios"].items():
        values=[v["timed"]/blocks[(ctx,inp,s,"QB-local")]["timed"] for (ctx,inp,s,a),v in blocks.items() if a==arm]
        check(math.isclose(geometric_mean(values),ratio,rel_tol=1e-12),arm)
    print(f"{passed} traced policy cells; {committed} exact committed vectors across qualified R and four methods; {len(blocks)} complete paired blocks.")
if __name__=="__main__":main()

