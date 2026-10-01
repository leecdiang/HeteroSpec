"""No GPU/network/runner imports. Authenticate inventory and independently replay evidence."""
import hashlib,importlib.util,json,sys
from pathlib import Path
def main(root):
    root=Path(root);m=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()};assert actual==set(m['files'])|{'MANIFEST.json'},'inventory extra/missing file'
    for name,v in m['files'].items():
        p=root/name
        with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        assert p.stat().st_size==v['bytes'] and h==v['sha256'],'file digest/length '+name
    p=root/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2/verify.py';spec=importlib.util.spec_from_file_location('offline_independent',p);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    phases={}
    for name,kind in [('reference-qualification','reference'),('discovery','discovery'),('pre-live','pre-live'),('live','live')]:
        if (root/name/'records.json').exists():phases[name]=v.check_phase(root/name,kind)
    for name in ['endpoint-probes','endpoint-probes-qualified','engineering-extra','engineering-attempt1','engineering-attempt2']:
        p=root/name
        if not p.exists():continue
        for record in p.rglob('record.json'):
            r=v.read(record)
            if 'negative-fixtures' in record.parts:
                try:v.check_run(record.parent)
                except (ValueError,KeyError,IndexError):continue
                raise ValueError('negative fixture accepted offline: '+str(record))
            if r['status']!='VALID':continue
            if r.get('process_environment_overrides',{}).get('LLAMA_BATCH_DEBUG')!='1':continue
            tape=record.parent.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['condition']=='R_ONLY' else None
            v.check_run(record.parent,tape)
    # In a strict inventory, loading verification must create no bytecode files.
    assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==actual,'verification polluted inventory'
    proofs=[]
    if (root/'frozen-checkpoints').exists():
        for p in sorted((root/'frozen-checkpoints').iterdir()):proofs.append(v.git_membership(p,root/'metadata'))
    scientific=v.complete_comparisons(root) if (root/'live/records.json').exists() else None
    print(json.dumps({'status':'PASS','file_count':len(actual),'phases':phases,'git_membership_proofs':proofs,'complete_scientific_verification':scientific,'GPU_required':False,'network_required':False,'omitted_external_bytes_authenticated':False,'content_head':m['content_head']}))
if __name__=='__main__':main(sys.argv[1])
