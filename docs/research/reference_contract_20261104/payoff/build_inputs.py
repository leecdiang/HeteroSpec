#!/usr/bin/env python3
"""Rebuild exact compact field projections from authenticated original downloads.
Usage: python build_inputs.py ../data
The files in original_dir must have names and hashes in sources.json.
No network or model requests. data.json contains only fields analyze_payoff uses.
"""
import gzip,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
D=Path(sys.argv[1])
manifest=json.loads((P/'sources.json').read_text())
original={}
for name,meta in manifest['original_sources'].items():
 b=(D/name).read_bytes();assert hashlib.sha256(b).hexdigest()==meta['sha256'],name
 if name.endswith('.hpp'):original[name]=b.decode()
 else:original[name]=json.loads(gzip.decompress(b) if name.endswith('.gz') else b)
bundle={}
name='171_service-cost.json.gz'
bundle[name]=[{**{k:r[k] for k in ('session','index','arm')},'measured':{**{k:r['measured'][k] for k in ('service_seconds','prefill_wall_seconds','continuation_wall_seconds','prompt_tokens')},'cycles':[{'caller_rows':c['caller_rows']} for c in r['measured']['cycles']]}} for r in original[name]]
name='171_operands.json.gz'
bundle[name]=[{'model':o['model'],'descriptor':{'weight':{k:o['descriptor']['weight'][k] for k in ('name','ne')}},'routes':[{k:r[k] for k in ('route','q','scalar_equal','submit_s','sync_s','plan_s')} for r in o['routes'] if r['q']in(8,16,32) and r['route']in('tile','packed')]} for o in original[name] if o['model']=='8B']
name='171_operator-activities.json.gz'
bundle[name]={k:[{f:e[f] for f in ('kind','name','start','end')} for e in v if e['kind']=='kernel'] for k,v in original[name].items() if k.split('/')[-1]in(f'{q}-{a}' for q in (8,16,32) for a in ('tile','packed'))}
name='174_DETAILS.json';bundle[name]={k:original[name][k] for k in ('phase_summaries','break_even')}
name='174_common-panel.json';bundle[name]={'test':[{k:r[k] for k in ('effective_head','append_tokens','crossed_qb_calls')} for r in original[name]['test']]}
name='177_ANALYSIS.json';bundle[name]={'records':original[name]['records']}
name='177_coverage.json';bundle[name]={k:original[name][k] for k in ('paths_seen','roots_seen','paths_with_distinct_rechunk_schedule','unexposed_root_representatives','unexposed_representatives_with_distinct_schedule')}
for name in ('179_native_checkpoint.hpp','179_latest_native_checkpoint.hpp'):bundle[name]=original[name]
body=json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'
assert hashlib.sha256(body.encode()).hexdigest()==manifest['bundle_sha256'],'projection differs'
(P/'data.json').write_text(body)
print('PASS: all originals authenticated; exact compact field projection reproduced.')
