"""Recover the four already-exposed direct-ID inputs without native tokenization."""
from pathlib import Path
from protocol import *
ROOT=Path(__file__).resolve().parent
old=ROOT/'_host/pr97'
inputs=read_json(old/'INPUTS.json')['cases'];conf=read_json(old/'baseline/CONFIRMATION_INPUTS.json')
panel=[]
for id in SENTINELS:
 c=next(c for c in conf['families']['Llama'] if c['id']==id)
 old_case=next((v for v in inputs if v['id']==id),None)
 if old_case:require(c['prompt_ids']==old_case['prompt_ids'],'historical direct IDs disagree')
 panel.append(dict(id=id,domain='math',prompt_ids=c['prompt_ids'],tokenizer_sha256=conf['tokenizer_binary_sha256'],template_sha256=conf['target_template_sha256'],source_sha256=file_sha(old/'baseline/CONFIRMATION_INPUTS.json')))
write_new(ROOT/'p0/SENTINEL_PANEL.json',panel)
plan=build_plan(panel,'pilot');validate_plan(plan);write_new(ROOT/'p0/PLAN_P1.json',plan)
write_new(ROOT/'p0/INPUT_BINDINGS.json',dict(inputs_sha256=file_sha(old/'INPUTS.json'),confirmation_inputs_sha256=file_sha(old/'baseline/CONFIRMATION_INPUTS.json'),tokenizer_binding_sha256=file_sha(old/'baseline/pr92_restore/TOKENIZER_BINDING.json'),tokenizer_identity_scope='Frozen original tokenizer binary; full vocab table remains in restored archive',template_identity_scope='Exact inherited target_template_sha256; preserve double BOS',exposure='ALL_FOUR_SENTINELS_PREVIOUSLY_EXPOSED',sizes={c['id']:len(c['prompt_ids']) for c in panel}))
print('80 slots; 8 R / 4 shadow counts / 4 shadow diagnostic / 32 candidate counts / 32 candidate diagnostic; native starts 0')
