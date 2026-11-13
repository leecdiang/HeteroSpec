"""Admit the exact scalar continuations needed by all four diagnostic origins."""
from pathlib import Path
import hashlib,json,sys
from admission import ROOT,put,sha
from execute import BASE,WORK,execute
from lifecycle_gate import read,spec,MANIFEST as NATURAL

MANIFEST='JOB_MANIFEST_DIAGNOSTIC_OPERANDS.json'

def freeze():
    base=read(ROOT/NATURAL);models={k:v for k,v in base['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots'];jobs=[];origins=[]
    for i,x in enumerate(roots):
        # The observed original cache padding is256; retain the first full extent
        # holding this immutable prompt, including the long704-token failure root.
        edge=((len(x['prompt_ids'])+255)//256)*256
        needed=edge+4-len(x['prompt_ids'])
        item=dict(index=i,id=x['id'],prompt_tokens=len(x['prompt_ids']),expected_extent=edge,within_head=edge-8,cross_head=edge-4,needed_scalar_tokens=needed)
        old=Path('D:/rtx188/runs/Qwen-old-free/native')/f'r{i}-heavy/receipt.json'
        r=read(old);assert r['prompt_ids']==x['prompt_ids']
        if len(r['ids'])>=needed:
            item.update(source='BOUND_ORIGINAL_WINDOWS_R',receipt=str(old),receipt_sha256=sha(old))
        else:
            assert r['stop_reason']=='CAP','Existing EOG prevents the frozen origin from reaching required extent'
            input=dict(x,cap=needed)
            job=spec(f'diagnostic-operands-v2-R-r{i}','R',dict(models,lowering='SIMPLE',inputs=[dict(name='free',capture=False,input=input)]),1,len(x['prompt_ids'])+needed-1)
            jobs.append(job);item.update(source='NEW_INDEPENDENT_WINDOWS_R',job=job['id'],previous_receipt=str(old),previous_receipt_sha256=sha(old))
        origins.append(item)
    put(ROOT/MANIFEST,dict(base,status='FROZEN_FOUR_ORIGIN_SCALAR_CONTINUATION_ADMISSION',jobs=jobs,origins=origins,requests=len(jobs),rows=sum(x['rows'] for x in jobs),
        selection='Original four exposed Windows development roots in immutable order; no replacement if any scalar continuation ends too early. Within/cross are before/after each origin actual native extent;256 for short roots,768 for the long root.',
        stop='If any origin lacks eight authorized exact scalar continuation tokens at either head, report the missing fixture and stop the diagnostic/panel, without repetitions or synthetic/replacement inputs.'))
    print('Frozen scalar operand construction',len(jobs),'new R requests',sum(j['rows'] for j in jobs),'rows',flush=True)

def main():
    if sys.argv[1]=='freeze':freeze();return
    manifest=read(ROOT/MANIFEST);roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots'];actual={}
    old_binding=read('D:/rtx188/runs/Qwen-old-free/binding.json');current_binding=read(BASE/'R-Qwen/BUILD.json')
    assert old_binding['exe']==current_binding['exe'] and old_binding['modules']==current_binding['modules']
    for item in manifest['origins']:
        r=read(WORK/'runs/lifecycle-v2-loop4-SIMPLE-k3/native'/('r'+str(item['index'])+'-heavy')/'receipt.json')
        prefill=[e for e in r['executions'] if e['phase']=='PREFILL'];assert prefill[-1]['actual_attention_extent']==item['expected_extent'],'Frozen native extent differs'
    for job in manifest['jobs']:
        native=execute(job,MANIFEST);actual[job['id']]=native/'free/receipt.json'
    fixtures=[];shortages=[]
    for item in manifest['origins']:
        p=actual[item['job']] if item['source']=='NEW_INDEPENDENT_WINDOWS_R' else Path(item['receipt'])
        r=read(p);x=roots[item['index']]
        if item['source']=='NEW_INDEPENDENT_WINDOWS_R':
            prior=read(item['previous_receipt']);assert r['ids'][:len(prior['ids'])]==prior['ids'],'Original scalar continuation is unstable'
        if len(r['ids'])<item['needed_scalar_tokens']:
            shortages.append(dict(item,actual_scalar_tokens=len(r['ids']),stop=r['stop_reason'],receipt=str(p),receipt_sha256=sha(p)));continue
        tape=x['prompt_ids']+r['ids']
        for relation in ('within','cross'):
            head=item[relation+'_head'];assert head>=len(x['prompt_ids']) and len(tape)>=head+8
            fixtures.append(dict(origin=x['id'],index=item['index'],geometry=relation,prefix_ids=tape[:head],append_ids=tape[head:head+8],extent=item['expected_extent'],
                independent_R_receipt=str(p),independent_R_receipt_sha256=sha(p)))
    result=dict(status='READY_FOR_FULL_VECTOR_KV_QUALIFICATION' if not shortages else 'BLOCKED_FROZEN_SCALAR_CONTINUATION_TOO_SHORT',
        fixtures=fixtures,shortages=shortages,root_replacements=0,clean_timing_requests=0,manifest_sha256=sha(ROOT/MANIFEST))
    put(ROOT/'DIAGNOSTIC_OPERANDS.json',result)
    print(result['status'],json.dumps(shortages),flush=True)
    assert not shortages,'Frozen four-origin equal-work fixture cannot be constructed; no smaller or substituted panel admitted'

if __name__=='__main__':main()
