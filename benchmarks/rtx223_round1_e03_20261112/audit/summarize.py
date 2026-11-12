"""Summarize retained audit evidence, without invoking an inference runtime."""
from pathlib import Path
import hashlib,json,os

HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/name).read_bytes())

def main():
    disk=read('DISK_IDENTITIES.json'); ledger=read('LEGACY_LEDGER_AUDIT.json'); host=read('HOST_AUDIT.json')
    models=[x for x in disk['inventory'] if 'model' in x]
    mismatch=[f['path'] for x in disk['inventory'] for f in x.get('disk_files',[]) if f.get('matches') is not True]
    for model in models:
        if model['model']['matches'] is not True:mismatch.append(model['model']['path'])
    old=HERE.parent.parent
    cap=json.loads((old/'q8rtx213-supplement-runtime-20261109/runs/rtx213-s1-LOCAL-packed-k7/JOB_NATIVE.json').read_bytes())['capability_request']
    result=dict(schema='heterospec.round1.environment-audit.v1',
        evidence_scope='STATIC_DISK_AND_HISTORICAL_RECEIPTS_ONLY',
        model_hash_mismatches=mismatch,
        vocabulary_match=models[0]['model']['gguf']['vocabulary_canonical_json_sha256']==models[1]['model']['gguf']['vocabulary_canonical_json_sha256'],
        vocab_size=models[0]['model']['gguf']['vocabulary_count'],
        previous_qualified_target_context=cap['target_context'],previous_qualified_draft_context=cap['draft_context'],
        previous_target_placement=cap['target_placement'],previous_draft_placement=cap['draft_placement'],
        previous_greedy=cap['greedy'],previous_output_policy=cap['target_output_policy'],
        previous_proposal_mode=cap['proposal_mode'],previous_producer='NATIVE',
        previous_residency='matched',current_new_runtime_policy=None,
        graph_policy=dict(current_environment={k:os.getenv(k) for k in ('CUDA_VISIBLE_DEVICES','CUDA_DEVICE_ORDER','GGML_CUDA_DISABLE_GRAPHS','LLAMA_GRAPH_REUSE_DISABLE')},
            historical_host_core_CMake_GGML_CUDA=False,historical_CMake_GGML_CUDA_GRAPHS=True,
            warning='These host core CMake caches have GGML_CUDA=OFF and do not establish how the imported ggml-cuda.dll was compiled. No new loaded CUDA graph receipt is available.',
            source_behavior='llama-context.cpp reads LLAMA_GRAPH_REUSE_DISABLE; CUDA backend has compile-time USE_CUDA_GRAPH guarded paths.'),
        inherited_ledger_totals=ledger['published_totals'],
        inherited_ledgers_all_main_pins_match=all(x['after']['matches'] for x in ledger['ledgers']),
        inherited_ledgers_unchanged=all(x['old_main_byte_unchanged'] for x in ledger['ledgers']),
        original_thread_check=dict(status='UNVERIFIED',method='codex_app/list_threads limit50',error='MCP -32000 Codex app tool request failed',
            consequence='No exclusive resource window or duplicate-work clearance can be inferred.'),
        shared_gpu_lock_exists=host['old_shared_lock']['exists'],
        new_epoch_GPU_model_requests=0,new_epoch_kernel_launches=0,
        GPU_mechanism_decision='INCONCLUSIVE_PENDING_THREAD_AND_NATIVE_QUALIFICATION')
    with (HERE/'SUMMARY.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ('model_hash_mismatches','vocabulary_match','vocab_size','inherited_ledger_totals','inherited_ledgers_all_main_pins_match','GPU_mechanism_decision')}))

if __name__=='__main__':main()
