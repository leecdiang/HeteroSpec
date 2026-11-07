#!/usr/bin/env python3
"""File/CPU-only audit of sealed H2 code and existing negative witnesses."""
from pathlib import Path
import importlib.util,json,hashlib,sys
import argparse
a=argparse.ArgumentParser();a.add_argument('--work',type=Path,required=True);args=a.parse_args()
w=Path(__file__).resolve().parents[3];e=w/'paper/mlsys2027/evidence';r=args.work.resolve()/'rtx-h2/evidence';src=r/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2';sys.path.insert(0,str(src));import verify
sha=lambda p:hashlib.file_digest(open(p,'rb'),'sha256').hexdigest();neg=[]
for p in sorted((r/'engineering-extra/negative-fixtures').iterdir()):
 try:verify.check_run(p)
 except (ValueError,KeyError,IndexError) as ex:neg.append({'case':p.name,'status':'RERUN_PASS','rejected':True,'reason':str(ex),'record_sha256':sha(p/'record.json')})
 else:raise AssertionError('negative witness accepted '+p.name)
try:verify.provenance({'commit':'abc','remote_ref':'abc','remote_ack_utc':'2026-10-01T10:00:00Z'},'2026-10-01T09:59:59Z')
except ValueError as ex:neg.append({'case':'premature_live','status':'RERUN_PASS','rejected':True,'reason':str(ex),'scope':'original verifier negative ordering fixture; file/CPU only'})
else:raise AssertionError('premature live accepted')
p=r/'pre-live/runs/HumanEval-17-r1-H2_P_R';events=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()];tapes=[json.loads(x) for x in (p/'tape.jsonl').read_text().splitlines()];ids=json.loads((p/'generated_ids.json').read_text());examples=[]
for name,pred in [('rejection',lambda x:x['response']['accepted_proposals']<len(x['request']['proposal_ids'])),('bonus',lambda x:x['response']['accepted_proposals']==len(x['request']['proposal_ids']) and len(x['response']['samples'])>len(x['request']['proposal_ids']))]:
 x=next(x for x in events if x['role']=='R' and x['event']=='verify' and pred(x));q=x['request'];v=x['response'];t=tapes[q['round']];assert ids[t['prefix_count']:t['prefix_count']+len(v['committed_ids'])]==v['committed_ids'];examples.append({'case':name,'request':q,'prefix_count':t['prefix_count'],'prefix_sha256':t['prefix_sha256'],'sample_ids':[s['selected_id'] for s in v['samples']],'accepted':v['accepted_proposals'],'committed':v['committed_ids'],'retain_count':v['retain_count'],'next_position':v['next_position'],'final_array_slice':ids[t['prefix_count']:t['prefix_count']+len(v['committed_ids'])]})
report={'status':'RERUN_PASS','scope':'Source/file/CPU inspection of existing witnesses; no models executed','source_objects':{str(x.relative_to(r)):{'sha256':sha(x),'bytes':x.stat().st_size} for x in [src/'worker.cpp',src/'engine.py',src/'verify.py',r/'engineering-extra/records.json',p/'events.jsonl',p/'tape.jsonl',p/'generated_ids.json']},'R_verify_allowlist':['op','round','position','pending','proposal_ids'],'R_init_allowlist':['op','formatted_prompt'],'assertions':'round, position and pending compare to R local state; tape task/rep/prefix count/hash and prior hash chain are checked before local decode; one line consumed per completed step; mismatches/truncation/extra suffix/fields fail','computed_decisions':'target logits sampled locally; accept matching proposals, correction on first rejection, bonus after complete acceptance, rollback invalid suffix','negative_witnesses':neg,'examples':examples,'independence':'Application/process/model loading/API; shared llama.cpp/GGML/CUDA numerical code; not adversarial OS isolation','necessity_limit':'No target-only UB2 competitor on same V2 reserved cohort; no necessity inference'};(e/'H2_INPUT_AUDIT_V086.json').write_text(json.dumps(report,indent=2)+'\n');print('H2 audit: six original negative witnesses reject; rejection/bonus slices match final array')
