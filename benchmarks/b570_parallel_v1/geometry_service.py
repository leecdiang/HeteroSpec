"""Four intact alternate-geometry controls; these are exposed mechanism inputs."""
from experiment import *
def run_controls(role):
    sequences('smol')
    inputs=[json.loads(s) for s in (ROOT/'smol-tokenized.jsonl').read_text(encoding='utf-8').splitlines()]
    rows=[];ref=[]
    for a in ['R',*ARMS]:
        slots=[dict(kind='natural',arm='S1' if a=='R' else a,ub=1 if a=='R' else 32,cap=128,ids=r['prompt_ids'],heavy=True) for r in inputs]
        rr=slots_run(f'smol-intact-{role}-{a}','reference-B' if a=='R' else role,'smol',4096,slots)
        if a=='R':ref=rr;continue
        for prompt,r,original in zip(inputs,rr,ref):
            rows.append(dict(id=prompt['id'],arm=a,reference=original['vectors'] if original else None,
                 vectors=r['vectors'] if r else None,equal=bool(original and r and original['vectors']==r['vectors'] and original['greedy']==r['greedy'])))
    put_once(ROOT/f'SMOL_INTACT-{role}.json',rows)
if __name__=='__main__':run_controls(sys.argv[1])

