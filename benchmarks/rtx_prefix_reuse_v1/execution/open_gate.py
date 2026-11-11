"""Verify immutable peer freeze and exact shared cohort before any held-out launch."""
from formal import *
from datetime import datetime,timezone
b=read(ROOT/'B570_FREEZE_SOURCE_POLICY_FREEZE.json');a=read(ROOT/'SOURCE_POLICY_FREEZE.json')
assert b['status']=='NATIVE_CALIBRATION_SOURCE_POLICY_FROZEN' and b['main_output_exposures']==0
assert study.digest(b['source'])==b['source_sha256']
assert study.digest(b['policy'])==b['policy_sha256']
assert b['policy']==read(ROOT/'B570_FREEZE_policy.json')
assert b['source']==read(ROOT/'B570_FREEZE_CALIBRATION_SOURCE.json')
q=read(ROOT/'B570_FREEZE_CALIBRATION_QUALIFICATION_V3.json');assert len(q)==36 and all(x['passed'] for x in q)
peer=read(ROOT/'B570_FREEZE_COHORT_RECEIPT.json');own=read(ROOT/'COHORT_RECEIPT.json')
fields=('id','root_id','request_token_sha256','cached_token_sha256','effective_head','physical_head','prompt_tokens','append_tokens')
for split,n in [('calibration',12),('test',32)]:
    left={x['id']:x for x in own[split]};right={x['id']:x for x in peer[split]}
    assert len(left)==len(right)==n and left.keys()==right.keys()
    for key in left:
        for field in fields:assert left[key][field]==right[key][field],(key,field)
tok=read(ROOT/'B570_FREEZE_TOKENIZER_AND_CENSUS.json')
assert tok['tokenizer_sha256']==a['native_tokenizer_identity']['tokenizer_sha256']
assert tok['tokenizer']['template_sha256']==a['template_sha256']
c=tok['sensitivity'][0];assert c['capacity']==a['capacity']==4096 and c['cache_granule']==a['cache_granule']==1 and c['padding']==a['padding']==256
assert not list(ROOT.glob('main-*/launch.json'))
put(ROOT/'COMMON_BLIND_GATE.json',dict(utc=datetime.now(timezone.utc).isoformat(),both_source_policy_freezes_verified=True,capacity=4096,shared_cohort_sha256=sha(ROOT/'common-panel.json'),shared_token_rows_sha256=sha(ROOT/'tokenize01/tokens.jsonl'),matched_rows=44,matched_fields=fields,heldout_outputs_at_release=0,rtx=dict(commit='efd92438a08a4e9c37a422731ddd6850d8907f1b',repository_url='https://github.com/leecdiang/HeteroSpec/pull/174',receipt_files={'SOURCE_POLICY_FREEZE.json':sha(ROOT/'SOURCE_POLICY_FREEZE.json'),'COHORT_RECEIPT.json':sha(ROOT/'COHORT_RECEIPT.json')}),b570=dict(commit='6517c79b59ad3d813a35fa087d15751b825dad34',repository_url='https://github.com/leecdiang/HeteroSpec/pull/175',receipt_files={p.name:sha(p) for p in ROOT.glob('B570_FREEZE_*.json')}),receipt_encoding='GitHub fetched UTF-8 content normalized to local LF; hashes authenticate retained bytes, semantic source/policy digests independently checked',lifecycle_scope='Independent file-backed RTX and host-memory B570 deployments; no pooling or pure hardware contrast'))
assert len(gate())==32
print('COMMON_BLIND_GATE_OPEN')
