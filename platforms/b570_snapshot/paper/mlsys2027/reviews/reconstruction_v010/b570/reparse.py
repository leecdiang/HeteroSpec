"""Independent CPU parser. Uses standard library only; imports no study helper.

Usage: python reparse.py EXTRACTED_RAW_SUBSET FIXED_METADATA OUTPUT_JSON
The raw subset is from Actions run 37178393741, artifact 11293269625.
FIXED_METADATA contains protocol/freeze/manifest and eight source files fetched
from PR53 head 3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4.
"""
import collections
import hashlib
import json
from pathlib import Path
import sys

raw, fixed, output = map(Path, sys.argv[1:])
study = raw / 'artifacts/b570_prefill_diagnostic_v1'
bench = raw / 'benchmarks/b570_prefill_diagnostic_v1'
source = raw / 'scripts/platform/b570_prefill_diagnostic_v1'
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks = collections.Counter()
def check(value, label):
    assert value, label
    checks[label] += 1

protocol = load(fixed/'PROTOCOL.json')
freeze = load(fixed/'FREEZE.json')
for name in ['PROTOCOL.json', 'FREEZE.json', 'ASSET_MANIFEST.json']:
    check((fixed/name).read_bytes() == (bench/name).read_bytes(), 'fixed_head_metadata_identical')
for winpath, digest in freeze['sources'].items():
    name = winpath.split('\\')[-1]
    check(sha(source/name) == digest == sha(fixed/name), 'frozen_source_matches_fixed_head')
check(sha(fixed/'PROTOCOL.json') == freeze['protocol_sha256'], 'frozen_protocol')
check(sha(fixed/'ASSET_MANIFEST.json') == freeze['manifest_sha256'], 'frozen_manifest')

data = {}
graph_rows = []
overshoot = collections.Counter()
endpoint_counts = collections.Counter()
transfer_count = 0
available_hashes = 0
for phase in ['formal', 'g0']:
    results = sorted((study/phase).glob('*/result.json'))
    check(len(results) == (360 if phase == 'formal' else 120), phase+'_denominator')
    for rp in results:
        d = load(rp)
        attempts = list(rp.parent.glob('attempt-*'))
        check(len(attempts)==1, phase+'_single_attempt')
        cp = raw/d['capture']
        c = load(cp)
        check(d['valid'] and d['exit_code']==0, phase+'_valid_exit')
        check(d['protocol_sha256']==sha(fixed/'PROTOCOL.json'), phase+'_protocol')
        start = load(cp.parent/'START.json')
        for k in ['unit_id','attempt_id','variant','formal','task','rep','command','env_overrides','protocol_sha256','start_utc']:
            check(start[k]==d[k], phase+'_attempt_identity')
        for path, digest in d['files'].items():
            p = raw/path
            if p.exists():
                check(sha(p)==digest, phase+'_available_file_hash')
                available_hashes += 1
        ids=c.get('ids',c.get('generated_ids'))
        eog=c['eog']
        check(len(ids)==len(eog), phase+'_raw_alignment')
        stop = next((i+1 for i,x in enumerate(eog[:128]) if x),min(128,len(ids)))
        endpoint = 'EOG' if any(eog[:stop]) else 'CAP128'
        if endpoint=='CAP128': check(stop==128, phase+'_cap_complete')
        check((ids[:stop],eog[:stop],endpoint)==(d['ids'],d['eog'],d['endpoint']), phase+'_endpoint_contract')
        check(len(ids)-stop==d['raw_overshoot'], phase+'_overshoot_retained')
        if 'prompt_ids' in c:
            check(c['prompt_ids'] == load(study/'inputs'/d['task'].replace('/','_')/'prompt_ids.json'), phase+'_prompt_ids')
        else:
            check(phase=='g0' and d['variant']=='N_old', 'legacy_native_prompt_ids_unrecorded')
        cmd=d['command']
        def arg(k): return cmd[cmd.index(k)+1]
        check(arg('--device')=='Vulkan0' and arg('--n-gpu-layers')=='all', phase+'_device_command')
        stderr=(cp.parent/'stderr.txt').read_text()
        check('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in stderr, phase+'_device_log')
        check('offloaded 37/37 layers to GPU' in stderr, phase+'_target_offload')
        if d['variant'].startswith('N'):
            check(arg('--spec-draft-device')=='Vulkan0' and arg('--spec-draft-ngl')=='all' and arg('--spec-draft-n-max')=='2', phase+'_native_fixed_config')
            check(set(d['env_overrides']) <= {'HS_PREFILL_OUTPUT','HS_PREFILL_UB','HS_MECHANISM_INPUT_IDS','HS_MECHANISM_OUTPUT','HS_NO_TRANSFER','HETEROSPEC_DIRECT_ID_PATH'}, phase+'_native_no_future_tape')
        if phase=='formal':
            check(d['formal'], 'formal_flag')
            endpoint_counts[endpoint]+=1
            overshoot[d['variant']]+=d['raw_overshoot']
            transfer=c.get('transfer')
            if d['variant']!='R':
                transfer_count += 1
                check(transfer['source_ub']==(128 if d['variant'] in ['T1','N1'] else 1) and transfer['destination_ub']==1, 'transfer_policy')
                check(transfer['before']==transfer['after']==transfer['source_after']=={'sequence_id':0,'min':0,'max':len(c['prompt_ids'])-1}, 'transfer_positions')
                check(transfer['state_bytes']==transfer['consumed_bytes'] and transfer['kv_equal'] and transfer['source_unchanged'], 'transfer_recorded_equal')
                check(transfer['sampler_chain']==transfer['clone_chain'] and transfer['sampler_history']==transfer['clone_history'] and transfer['seed']==transfer['clone_seed']==123, 'sampler_recorded_clone')
                check(transfer['pending_id']==ids[0] and transfer['pending_eog']==eog[0], 'pending_first_sample')
                kvhashes=[v for k,v in d['files'].items() if k.endswith(('.before.kv','.restored.kv','.source_after.kv'))]
                check(len(kvhashes)==3 and len(set(kvhashes))==1, 'transfer_kv_digest_identity')
            target_prefill=[x for x in c['trace'] if x.get('event')=='decode' and x.get('role')=='target' and x.get('phase')=='prefill']
            lengths=[len(x['input_ids']) for x in target_prefill]
            n=len(c['prompt_ids'])
            wanted=[n-1,1] if d['variant'].startswith('N') else [min(512,n-i) for i in range(0,n,512)]
            check(lengths==wanted, 'preserved_prefill_caller_grouping')
            graph=[g['ne1'] for x in target_prefill for g in x['graphs'] if g['tensor']=='embd']
            cap=128 if d['variant'] in ['R','T1','N1'] else 1
            wanted_graph=[min(cap,ln-i) for ln in lengths for i in range(0,ln,cap)]
            check(graph==wanted_graph, 'observed_prefill_graph_tokens')
            for x in c['trace']:
                if x.get('event')=='decode':
                    check(x['exit_code']==0, 'decode_exit')
                    if x['role']=='draft' or (x['phase']=='continuation' and d['variant']!='R'):
                        check(x['ub_capacity']==1, 'continuation_and_draft_ub1')
            graph_rows.append({'task':d['task'],'variant':d['variant'],'rep':d['rep'],'caller_lengths':lengths,'occupied_graph_tokens':graph})
        data[(phase,d['task'],d['variant'],d['rep'])]=(d,c)

def contract(phase,task,variant,rep):
    d=data[(phase,task,variant,rep)][0]
    return d['ids'],d['eog'],d['endpoint']
comparisons=collections.Counter()
task_rows=[]
for task in protocol['tasks']:
    row={'task':task, 'diagnostic':task in protocol['cases']}
    for a,b,label in [('T0','N0','prediction_before'),('T1','N1','prediction_after'),('N0','R','reference_before'),('N1','R','reference_after'),('N0','N1','output_unchanged')]:
        row[label]=sum(contract('formal',task,a,r)==contract('formal',task,b,r) for r in [1,2,3])
        comparisons[label]+=row[label]
    row['stable']=all(contract('formal',task,v,1)==contract('formal',task,v,2)==contract('formal',task,v,3) for v in protocol['conditions'])
    check(row['stable'], 'task_repeat_stable')
    task_rows.append(row)

historical=load(study/'evaluation/HISTORICAL_EXPECTED.json')
oldpred=load(fixed/'RESERVED_PREDICTIONS.json')
check(sha(fixed/'RESERVED_PREDICTIONS.json')=='0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826', 'original_prediction_authority_hash')
for pred in oldpred['predictions']:
    for variant,field in [('R','reference_ids'),('T0','predicted_ids'),('N0','predicted_ids')]:
        check(contract('formal',pred['task_id'],variant,pred['repetition'])[0]==pred[field], 'original_prediction_authority_ids_equal')
for task in protocol['tasks']:
    for v in ['R','T0','N0']:
        for rep in [1,2,3]:
            h=historical[f'{task}/{v}/{rep}']
            check(contract('formal',task,v,rep)==(h['ids'],h['eog'],h['endpoint']), 'historical_expected_baseline_equal')
for task in protocol['g0_tasks']:
    for rep in [1,2,3]:
        for old,new in [('R_old','R'),('T_old','T_plain'),('N_old','N_plain'),('T_old','T0'),('N_old','N0')]:
            check(contract('g0',task,old,rep)==contract('g0',task,new,rep), 'g0_original_baseline_equal')
        for plain,sham in [('T_plain','T0'),('N_plain','N0')]:
            a=data[('g0',task,plain,rep)][1];b=data[('g0',task,sham,rep)][1]
            check(contract('g0',task,plain,rep)==contract('g0',task,sham,rep), 'sham_complete_output')
            check(a['commits']==b['commits'] and a['trace']==b['trace'], 'sham_scores_decisions_decode_trace')

seal=load(study/'T1_SEAL.json')
check(len(seal['predictions'])==72, 'sealed_denominator')
for pred in seal['predictions'].values():
    d=load(raw/pred['path'])
    check(sha(raw/pred['path'])==pred['sha256'], 'sealed_result_hash')
    check((pred['ids'],pred['eog'],pred['endpoint'])==contract('formal',d['task'],'T1',d['rep']), 'sealed_prediction_array')
check(seal['protocol_sha256']==sha(fixed/'PROTOCOL.json') and seal['freeze_sha256']==sha(fixed/'FREEZE.json') and seal['manifest_sha256']==sha(fixed/'ASSET_MANIFEST.json'), 'sealed_authority_hashes')
lines=(study/'RUN_LEDGER.jsonl').read_bytes().splitlines(keepends=True)
events=[json.loads(l) for l in lines]
idx=next(i for i,e in enumerate(events) if e['event']=='T1_SEALED')
check(hashlib.sha256(b''.join(lines[:idx])).hexdigest()==seal['ledger_sha256_before_seal'], 'ledger_prefix_hash')
check(events[idx]['seal_sha256']==sha(study/'T1_SEAL.json'), 'ledger_seal_hash')
n1=[i for i,e in enumerate(events) if e['event']=='ATTEMPT_START' and e.get('formal') and e.get('variant')=='N1']
t1=[i for i,e in enumerate(events) if e['event']=='ATTEMPT_END' and e.get('formal') and e.get('variant')=='T1']
check(len(n1)==72 and min(n1)>idx, 'all_native_post_seal')
# Completion event schema is captured in the individual result timestamps too.
check(all(data[('formal',task,'T1',r)][0]['end_utc']<seal['created']<data[('formal',task,'N1',r)][0]['start_utc'] for task in protocol['tasks'] for r in [1,2,3]), 'local_prediction_before_native')

result={'status':'PASS','reviewed_head':'3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4','method':'fresh independent standard-library raw reparse; no study helper imported','formal_arrays':360,'g0_arrays':120,'unique_tasks':24,'repetitions':3,'comparisons':dict(comparisons),'reference_transitions':{'recover_tasks':sum(x['reference_before']==0 and x['reference_after']==3 for x in task_rows),'unchanged_agree_tasks':sum(x['reference_before']==3 and x['reference_after']==3 for x in task_rows),'regress_tasks':sum(x['reference_before']==3 and x['reference_after']==0 for x in task_rows)},'task_rows':task_rows,'formal_endpoint_counts':dict(endpoint_counts),'formal_raw_overshoot_total_by_variant':dict(overshoot),'transfer_records':transfer_count,'available_file_hashes_recomputed':available_hashes,'checks':dict(checks),'total_checks':sum(checks.values()),'graph_rows':graph_rows,'limits':['The raw subset omits binary KV/logits dumps: this pass checks their equal recorded digests; earlier full-archive audit authenticated those bytes.','All 24 tasks were previously exposed; repetitions are not independent prompts.','Ledger verifies local order and hashes, not an independently certified absolute pre-live timestamp.','Shared OS is not adversarial isolation; omitted model/runtime/driver bytes and opaque sampler serialization remain outside independent byte authentication.','No functional HumanEval, speed, energy, universal repair, or unique-kernel-cause claim.']}
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['task_rows','graph_rows','checks']},indent=2))
