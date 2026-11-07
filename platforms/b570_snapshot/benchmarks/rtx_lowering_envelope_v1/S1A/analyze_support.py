"""CPU-only reconstruction from complete S1A raw; never starts a native host."""
import argparse, collections, hashlib, importlib.util, json
from pathlib import Path

def load(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reconstruct(root):
    spec = importlib.util.spec_from_file_location('sealed_audit', root/'code/audit.py')
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    actual = load(root/'support/CENSUS.json'); expected = load(root/'expected/SUPPORT_REGISTRY_S0.json')
    decision = audit.census(expected, actual)
    assert decision == load(root/'support/PREOUTPUT_SELECTION.json')
    f0 = load(root/'registration/S1_F0.json')
    approval = load(root/'registration/S1A_AUTHOR_APPROVAL.json')
    assert sha(root/'registration/S1_F0.json') == approval['approved_F0_sha256']
    assert hashlib.sha256(approval['author_message'].encode()).hexdigest() == approval['author_message_sha256']
    assert approval['stage'] == 'S1A_SUPPORT_ONLY'
    start = load(root/'support/BEFORE_START.json'); global_start = load(root/'ledger/S1_CENSUS_STARTED.json')
    assert start == global_start and start['graph_cap'] == 0 and start['operator_host_attempts'] == 1
    assert start['F0_sha256'] == approval['approved_F0_sha256']
    life = load(root/'support/LIFETIME.json'); pid = load(root/'support/PROCESS.json')
    assert life['pid'] == pid['pid'] and life['exit_code'] == 0 and life['failure'] is None and life['graphs'] == 0
    assert life['seconds'] <= 240
    admission = load(root/'support/HOST_ADMISSION.json'); policy = f0['admission_policy']
    assert (admission['gpu'], admission['driver'], admission['total_MiB']) == (policy['gpu'], policy['driver'], policy['total_MiB'])
    assert admission['AC'] == 1 and admission['util'] <= 5 and admission['temp'] <= 55 and admission['total_MiB']-admission['used_MiB'] >= 512
    modules = load(root/'MODULE_AUDIT.json')
    assert [m['path'] for m in modules['modules']] == actual['modules']
    assert set(modules['matched_pinned_numerical_DLLs']) >= {'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}
    for m in modules['modules']:
        if m['pinned_numerical_name']:
            name = m['pinned_numerical_name']
            assert m['sha256'] == f0['numerical_DLLs'][name]
            assert Path(m['path']).parent == Path(f0['runtime_directory'])
    by_layout = {}; unsupported = []; operations = collections.defaultdict(collections.Counter)
    family_layout = collections.defaultdict(lambda: collections.Counter())
    for row in actual['records']:
        layout = row['layout']; stats = by_layout.setdefault(layout, collections.Counter())
        stats['graphs'] += 1; stats['fully_supported_graphs'] += int(row['full_support'])
        assert row['actual_placement'] is None
        family = row['descriptor_id'].split('_')[0]
        family_layout[(family,layout)]['graphs'] += 1
        family_layout[(family,layout)]['fully_supported_graphs'] += int(row['full_support'])
        for n in row['nodes']:
            stats['node_queries'] += 1; stats['supported_node_queries'] += int(n['CUDA_support'])
            stats['executable_node_queries'] += int(not n['metadata_only'])
            operations[layout][n['op']] += 1
            assert n['placement'] is None
            if not n['CUDA_support']:
                unsupported.append(dict(descriptor_id=row['descriptor_id'],layout=layout,stage_outputs=row['stage_outputs'],node=n))
    return dict(status='PASS',selection=decision,by_layout=by_layout,
                by_family_layout=[dict(family=f,layout=l,**dict(c)) for (f,l),c in sorted(family_layout.items())],
                operator_query_counts=dict(operations),unsupported_nodes=unsupported,
                support_API_queries=sum(x['node_queries'] for x in by_layout.values()),
                actual_support_hosts=1,native_pid=life['pid'],native_owned_seconds=life['seconds'],explicit_readiness_queries=1,
                graph_computes=0,model_requests=0,warmups=0,failed_scientific_or_control_attempts=0,
                placement='NOT_EXECUTED',numeric_qualification='NOT_EXECUTED',full_request_qualification='NOT_EXECUTED',cost='NOT_MEASURED',
                profiling='PROFILE_UNAVAILABLE_PLACEMENT_ONLY',remaining_host_upper_bound=1008,
                remaining_graph_compute_upper_bound=2808,remaining_warmup_upper_bound=288,
                caveat='Backend support is a predicate, not allocation, executed placement, numerical equality, endpoint qualification or speed. No continuous GPU monitoring; no new GPU query in this reconstruction.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=reconstruct(Path(a.raw))
    with Path(a.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','selection','by_layout','support_API_queries','native_owned_seconds')}))
if __name__=='__main__': main()
