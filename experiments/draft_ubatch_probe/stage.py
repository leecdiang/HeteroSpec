#!/usr/bin/env python3
"""Exact #151 worker derivative; independent study, never overwrite old bytes."""
import argparse, hashlib, pathlib, json, difflib
PIN='4423bf687de4d652809c3ffad9cd9bf31770c2019c383fb54bd7abd24858b124'
def stage(source, ub):
    if ub not in (1,2,4): raise ValueError('draft ubatch must be 1, 2 or 4')
    if hashlib.sha256(source.encode()).hexdigest()!=PIN: raise ValueError('unexpected worker bytes')
    s=source.replace('using Clock=std::chrono::steady_clock;', f'using Clock=std::chrono::steady_clock;\nstatic constexpr int draft_ubatch={ub};')
    for old,new in [
      ('const fs::path&dir,int layout):model(m)', 'const fs::path&dir,int layout,int draft_physical=1):model(m)'),
      ('p.n_ubatch=ub;', 'p.n_ubatch=istarget?ub:draft_physical;'),
      ('dir/"draft",spec.selector);', 'dir/"draft",spec.selector,draft_ubatch);'),
      ('"rtx_scope_transfer_v1"','"rtx_draft_ubatch_probe_v1"'),
      ('{"draft_producer","NATIVE"}', '{"draft_producer","NATIVE"},{"draft_ubatch",draft_ubatch}'),
      ('need(slot.at("schema")==1', 'need(slot.at("draft_ubatch")==draft_ubatch,"draft ubatch slot mismatch");\n            need(plan.at("context").at("draft_ubatch")==draft_ubatch,"draft ubatch plan mismatch");\n            need(identity.at("draft_ubatch")==draft_ubatch,"draft ubatch binding mismatch");\n            need(slot.at("schema")==1'),
      ('    double setup=since(start);', '    if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft ubatch differs");\n    double setup=since(start);')]:
        if old not in s: raise ValueError('missing stage anchor')
        s=s.replace(old,new)
    return s
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--draft-ubatch',type=int,required=True);a=p.parse_args()
    src=a.worker.read_bytes().decode("utf-8");out=stage(src,a.draft_ubatch)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'worker.cpp').write_bytes(out.encode('utf-8'))
    (a.output/'CHANGE.patch').write_text(''.join(difflib.unified_diff(src.splitlines(True),out.splitlines(True),fromfile='frozen-worker.cpp',tofile='candidate-worker.cpp')))
    (a.output/'STAGE.json').write_text(json.dumps({'study':'rtx_draft_ubatch_probe_v1','draft_ubatch':a.draft_ubatch,'source_sha256':PIN,'output_sha256':hashlib.sha256(out.encode()).hexdigest(),'target_request_algorithm_changed':False,'target_effective_context_params_changed':False,'shared_context_expression_changed':True,'windows_worker_compilation':'NOT_RUN','gpu_execution':'NOT_RUN'},indent=2)+'\n')
