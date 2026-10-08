from pathlib import Path
import json,collections,hashlib
R=Path(__file__).parent;groups=collections.defaultdict(set)
for p in (R/'raw').glob('*/RESULT.json'):
 j=json.loads(p.read_text(encoding='utf8'));groups[j['unit_id'].split('/')[0]].add(j['source_commit'])
source=dict(A='2469e42',B='f274874',C_decision='415a503e4a378e596f970695ec2234d40745097b',C_initial_zero_model_preflight='601080b6cf1cf8f661865b30fc80e25cd62f60cf',C_actual_source='3be8db4d6c98c9466dd61414f8ee9b7dc4b3e4d6',D_first_reused_unit='f074dcec03a5d299350447a11bc01a5df497c102',D_namespace_resume='de2dcbf69f011a0d16b03e9d7089a7412d307027',E='84748a3c76e3eda5aaea7132a83a92989ceecbd4')
for stage in ['A','B','C','D','E']:
 n=stage+'_FREEZE.json';p=R/n
 if p.exists():source[n+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(frozen_epochs=source,actual_raw_source_epochs={k:sorted(v) for k,v in groups.items()},actual_source_distribution_not_git_checkout=True,private_history='packaging/GIT_HISTORY.bundle in CAS archive',public_branch='codex/b570-mechanism-pilot-v1',public_scope_only='benchmarks/b570_mechanism_pilot_v1',unchanged_external_PR63='66594b349955e66146702325559c26019ea16485',old_negative_results_retained=True)
(R/'SOURCE_EPOCHS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('Source epochs derived from authentic actual receipts')
