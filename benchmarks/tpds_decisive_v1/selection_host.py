"""Output-free native tokenization and prospective disjoint lane panels."""
from build_host import *
from build_v2 import compile_one
from common import digest
from design import select
import re,hashlib
def main():
    out=ROOT/'selection-v3';out.mkdir();build=out/'tokenizer';build.mkdir()
    src=Path('E:/rtx160/tokenizer01/build/vocab_only.cpp').read_text().replace('128256','151936').replace('original Llama vocabulary','original Qwen vocabulary')
    (build/'tokenizer.cpp').write_text(src,encoding='utf8');compile_one(build,'tokenizer.cpp')
    pool=Path('E:/rtx164/pool06/POOL.json');rows=json.loads(pool.read_bytes())['inputs']
    with (out/'input.jsonl').open('x',encoding='utf8') as f:
        for r in rows:f.write(json.dumps(dict(id=r['id'],formatted_prompt=r['formatted_prompt']),ensure_ascii=False)+'\n')
    start=time.monotonic();cmd=[str(build/'bin/worker.exe'),'D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf',str(out/'input.jsonl'),str(out/'tokens.jsonl')]
    with (out/'tokenizer.log').open('xb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    put(out/'TOKENIZER_RUN.json',dict(argv=cmd,code=r.returncode,seconds=time.monotonic()-start,model_forward_requests=0,n_gpu_layers=0,vocab_only=True));r.check_returncode()
    finish(out,pool,rows)

def finish(out,pool,rows):
    native={x['id']:x['prompt_ids'] for x in map(json.loads,(out/'tokens.jsonl').read_text().splitlines())}
    assert len(native)==len(rows);assert all(native[r['id']]==r['prompt_ids'] for r in rows),'saved/native tokenizer disagreement'
    legacy=Path('E:/rtx164/exposure-pr163/EXPOSURE_AUDIT-00.json');audit=json.loads(legacy.read_bytes());assert audit['complete'];blocked=set(audit['keys']);pins={str(legacy):sha(legacy)}
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('id','input_id','root_id','task_id','message_id') and isinstance(v,str):blocked.add(v)
                if k in ('text','description','raw_prompt','formatted_prompt','prompt') and isinstance(v,str):blocked.add(hashlib.sha256(v.strip().encode()).hexdigest())
                if k in ('prompt_ids','tokens','input_ids') and isinstance(v,list):blocked.add(digest(v))
                visit(v)
        elif isinstance(x,list):
            for y in x:visit(y)
    paths=[]
    for base in [Path('E:/rtx164'),Path('E:/rtx170')]:
        paths += [p for p in base.rglob('*.json') if p.name in ('PANEL.json','panel.json','input.json','inputs.json','SELECTED.json','SELECTION.json','UNSEEN.json','EXPOSURES.json','DEV.json','HELDOUT.json') and not any(x in p.parts for x in ('source','core','build','reproduce03'))]
    paths += [OLD.parent/'admission-Qwen-v4/PANEL.json']
    paths += [Path(x) for x in ('E:/rtx160/exposure04/EXPOSURES.json','E:/tpds167/formal01/panel.json','E:/rtx160/research/epoch07/HELDOUT.json','E:/rtx164/selection01/qwen8b02.json','E:/rtx164/selection01/qwen14b02.json','E:/rtx160/research/qwen8b02/DEV.json','E:/rtx160/research/qwen14b02/DEV.json')]
    for p in sorted(set(paths)):
        pins[str(p)]=sha(p);visit(json.loads(p.read_bytes()))
    for p in Path('E:/rtx164').rglob('EXPOSURE.jsonl'):
        pins[str(p)]=sha(p)
        for line in p.read_text().splitlines():visit(json.loads(line))
    excluded=[];eligible=[]
    for r in rows:
        keys={r['id'],digest(r['prompt_ids'])}|{r[k] for k in ('text_sha256','formatted_prompt_sha256','raw_prompt_sha256')}
        if keys&blocked:excluded.append(r['id']);continue
        n=len(r['prompt_ids'])
        if n+132>1024:continue
        eligible.append(dict(root_id=r['id'],id=r['id'],tokens=n,native_tokenized=True,admitted=True,domain=r['domain'],source_revision=r['source_revision'],token_sha256=digest(r['prompt_ids'])))
    put(out/'EXCLUSIONS.json',dict(source_pins=pins,excluded_roots=excluded,eligible_roots=len(eligible),saved_pool_sha256=sha(pool),rule='match historical identity/text/token keys and conservatively exclude every retained planned panel; D panel allocated before disjoint O panel without outputs'))
    d=select(eligible,set(),12,4);used={r['root_id'] for r in d['development']+d['test']};o=select(eligible,used,12,4)
    for lane,panel in [('D',d),('O',o)]:
        panel['development_policy']='Four already exposed PR151 inputs used for engineering; the four prospective development reservations remain unexecuted and excluded from confirmation.'
        put(out/(lane+'-panel.json'),panel);ids={x['id'] for x in panel['test']};put(out/(lane+'-inputs.json'),[r for r in rows if r['id'] in ids])
    print('native tokenizer matched',len(rows),'saved rows; eligible',len(eligible),'disjoint test roots 12+12; no new model outputs')
if __name__=='__main__':main()
