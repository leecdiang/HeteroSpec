from common95 import *
from runner95 import condition
import shutil
parent=LOCAL/'parent-restored/repository/benchmarks/rtx_evidence_closeout_v1'
for name in ['MODEL_CONTRACT.json','COUNTER_SEMANTICS.md','HOST_ADMISSION.json']:
    shutil.copyfile(parent/name,PUB/name)
oldinputs=read(parent/'CONFIRMATION_INPUTS.json');oldrows=read(parent/'FORMAL_RECORDS.json')
families=['Qwen','SmolLM2','Llama'];arms=['R','M_QB','C_QB','M_PQ','C_PQ','M_GS','C_GS'];selection={};panel={}
for family in families:
    tasks=oldinputs['families'][family];rows={(r['condition'],r['task']):r for r in oldrows if r['family']==family and r['session']==0 and r['round']==0}
    def sig(r):return [r['output'][k] for k in ['ids','eog_flags','length','terminal_id','stop_reason']]
    divergent=[t['id'] for t in tasks if sig(rows['R',t['id']])!=sig(rows['M0',t['id']])]
    agreeing=[t['id'] for t in tasks if t['id'] not in divergent]
    def choose(ids):
        result=[]
        for domain in ['MBPP','GSM8K']:
            candidates=sorted(t for t in ids if t.startswith(domain+'/'))
            if candidates:result.append(candidates[0])
        for t in sorted(ids):
            if len(result)==2:break
            if t not in result:result.append(t)
        assert len(result)==2;return result
    selected=choose(divergent)+choose(agreeing)
    selection[family]=dict(divergent=choose(divergent),agreeing=choose(agreeing),constraint='Prefer one each domain; if absent choose sorted remaining IDs',tasks=[t for tid in selected for t in tasks if t['id']==tid])
    ids=[tid for domain in ['MBPP','GSM8K'] for tid in sorted(t['id'] for t in tasks if t['id'].startswith(domain+'/'))[:6]]
    panel[family]=[t for tid in ids for t in tasks if t['id']==tid]
    assert len(panel[family])==12 and all(t['cap']==128 and t['prompt_token_count']<=768 for t in panel[family])
maxR={f:max(r['wall_ms']/1000 for r in oldrows if r['family']==f and r['condition']=='R') for f in families}
estimate=2*sum(maxR.values())*(672+112)+84*60+216*5
assert estimate<43200,'prospective all-family resource gate failed'
save(PUB/'P0_PLAN.json',dict(design_head=DESIGN_HEAD,parent_head=PARENT_HEAD,families=families,arms=[condition(a) for a in arms],P1_selection=selection,P2_panel=panel,selection_rule='PR91 exposed task IDs only; six lexicographically smallest IDs in each domain; no length/speed/new-output consultation',max_snapshot_contexts=24,snapshot_rule='First multiquery layer0 prefill and first multiquery layer0 target continuation per selected diagnostic input',operator_repetitions=3,max_operator_starts=216,diagnostic_full_request_cap=512,formal_request_cap=2016,formal_warmup_cap=84,owned_GPU_seconds_cap=43200,prospective_owned_reserve_seconds=estimate,old_R_max_seconds=maxR,reserve_rule='2x oldR maximum per family for672formal+112diagnostic,84loads at60s and216replays at5s; projection not component attribution',resource_gate='All three families admitted prospectively from model bytes and prior timers; no post-cost family pruning',reuse_controls=dict(cases={f:selection[f]['tasks'][0]['id'] for f in families},mask=1,arm='C_QB',capture=False,purpose='Native cached graph flag mismatch must reject reuse; exposed diagnostic control only'),warmups=read(parent/'ENGINEERING_INPUTS.json')['warmups'],parent_readonly=True))
save(PUB/'EXECUTION_DEPENDENCIES.json',dict(python=sys.version,executable_sha256=sha(PYTHON),reused_authenticated_parent_code={p.name:sha(p) for p in (LOCAL/'parent-restored/repository/scripts/platform/rtx_evidence_closeout_v1').glob('*.py')},reuse_scope='Resident HTTP timer, complete native output checks and workload conservation; new ledger,12h caps, native patches and study plan are separate',new_forward_count=0))
status('P0_SELECTION_AND_BUDGET_FIXED',families=families,reserved_GPU_seconds=estimate,new_forwards=0)
