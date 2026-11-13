"""Bind the panel only after a remotely frozen primary implementation and exposure audit."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import runner as r
from execute_panel import schedule

HERE=Path(__file__).resolve().parent
WORK=r.WORK

def digest(data):return hashlib.sha256(data).hexdigest()
def pin(path):return {'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':r.sha(path)}

def primary_freeze():
    builds={item['variant']:item for item in r.read(WORK/'amended-native-v2/BUILDS.json')}
    body={'status':'PRIMARY_IMPLEMENTATION_FROZEN_BEFORE_HELD_OUT_SELECTION',
          'builds':builds,'historical_model_contract_sha256':r.sha(Path('D:/hs-qb-confirmation-v02/MODEL_CONTRACT.json')),
          'code':[pin(HERE/name) for name in ['runner.py','execute_panel.py','audit_raw.py','prepare_panel.py','jsa_observer_v2.h','CAUSAL_TRACE_RULES.md']],
          'observer_correction_sha256':r.sha(HERE/'OBSERVER_METADATA_CORRECTION.json'),
          'native_numeric_changes':'NONE; only heavy-mode observational metadata changed after calibration',
          'held_out_selection_performed':False,'held_out_model_requests':0,
          'primary_timer':'Inherited inclusive resident nonstreaming HTTP request; native normalize before timer stop',
          'ordering':'Four-arm balanced rotation; optional admitted FAST inserted at fixed (session+input_index)%5 position',
          'automatic_retry':False,'all_other_PR140_constraints':'UNCHANGED'}
    r.save(HERE/'PRIMARY_IMPLEMENTATION_FREEZE.json',body)


def select(commit,audit_path):
    path='benchmarks/rtx_jsa_closeout_v1/revision_a/PRIMARY_IMPLEMENTATION_FREEZE.json'
    remote=subprocess.check_output(['gh','api','repos/leecdiang/HeteroSpec/contents/'+path+'?ref='+commit,'-H','Accept: application/vnd.github.raw+json'],cwd=r.REPO)
    r.require(remote==(HERE/'PRIMARY_IMPLEMENTATION_FREEZE.json').read_bytes(),'primary freeze remote differs')
    primary=r.read(HERE/'PRIMARY_IMPLEMENTATION_FREEZE.json')
    for file in primary['code']:r.require(pin(Path(file['path']))==file,'primary implementation drift')
    audit=r.read(audit_path)
    r.require(audit['status']=='PASS','complete exposure audit required')
    r.require(not audit.get('unresolved_archive_objects') and not audit.get('unresolved_text_objects'),'unresolved history objects block selection')
    exclusions=set(audit['excluded_ids'])
    old=WORK/'s0-static-census';old_tasks={task['id']:task for task in r.read(old/'NATURAL_TASKS.json')}
    prep=r.read(HERE/'PREP_REGISTRATION.json');new=r.read(Path(prep['output'])/'NATIVE_INPUTS.json')
    inventory={family:[] for family in ['Qwen','SmolLM2','Llama']}
    for family in inventory:
        for line in (old/(family+'-target.stdout.jsonl')).read_bytes().splitlines()[1:]:
            row=json.loads(line);task=old_tasks[row['task_id']]
            snapshot='e49bbfe381c9c0e564b937f1c4e163a2273c65cc' if task['domain']=='MBPP' else '3101c7d5072418e28b9008a6636bde82a006892c'
            inventory[family].append({**task,'prompt_ids':row['prompt_ids'],'snapshot':snapshot,'domain_group':'code' if task['domain']=='MBPP' else 'math'})
        inventory[family].extend({**row,'domain_group':'code'} for row in new if row['family']==('Qwen3' if family=='Qwen' else family))
    panel={};counts={};selection_rows=[]
    normalize=__import__('exposure_v2').normalize
    for family,candidates in inventory.items():
        duplicate=collections.Counter(normalize(t['description']) for t in candidates)
        eligible=[t for t in candidates if t['id'] not in exclusions and duplicate[normalize(t['description'])]==1]
        for task in eligible:task['selection_hash']=digest(('heterospec-jsa-closeout-20261021\0'+task['snapshot']+'\0'+task['id']).encode())
        chosen=[];counts[family]={}
        for label,lo,hi in [('short',64,192),('medium',256,448),('long',640,832)]:
            pool=sorted((t for t in eligible if lo<=len(t['prompt_ids'])<=hi),key=lambda t:(t['selection_hash'],t['id']))
            by={domain:[t for t in pool if t['domain_group']==domain] for domain in ['code','math']}
            counts[family][label]={'total':len(pool),'code':len(by['code']),'math':len(by['math'])}
            r.require(len(pool)>=4,'unfilled natural stratum after exposure exclusions')
            selected=sorted(by['code'][:2]+by['math'][:2],key=lambda t:t['selection_hash']) if all(len(by[d])>=2 for d in by) else pool[:4]
            r.require(len(selected)==4,'fixed four-input stratum')
            for task in selected:
                item={**task,'cap':128,'stratum':label,'prompt_token_count':len(task['prompt_ids'])}
                r.require(item['prompt_token_count']+128+3<=1024,'allocation/mask-domain headroom')
                chosen.append(item);selection_rows.append({'family':family,'input_index':len(chosen)-1,'id':item['id'],'stratum':label,'tokens':len(item['prompt_ids']),'domain_group':item['domain_group'],'selection_hash':item['selection_hash']})
        r.require(len({task['id'] for task in chosen})==12,'duplicate selected task')
        panel[family]=chosen
    manifest={'status':'HELD_OUT_PANEL_SEALED_BEFORE_E1','primary_freeze_commit':commit,'primary_freeze_sha256':r.sha(HERE/'PRIMARY_IMPLEMENTATION_FREEZE.json'),
              'exposure_audit_sha256':r.sha(audit_path),'eligible_counts':counts,'panel':panel,'selection_rows':selection_rows,
              'independent_task_count':len({row['id'] for row in selection_rows}),
              'cross_family_reuse':{ident:[row['family'] for row in selection_rows if row['id']==ident] for ident in sorted({row['id'] for row in selection_rows})},
              'new_model_outputs_used_for_selection':False}
    r.save(HERE/'INPUT_MANIFEST.json',manifest)
    config=r.read(HERE/'F0A_CALIBRATION.json');config['status']='FROZEN_E1_E2_MATRIX';config['builds']=primary['builds'];config['panel']=panel
    cal=r.read(Path(config['run_root'])/'CALIBRATION_SUMMARY.json');config['eligible_primary']=cal['eligible_primary'];config['eligible_fast']=cal['eligible_fast']
    old_pins=[file for file in config['files'] if 'amended-native' not in file['path']]
    files={file['path']:file for file in old_pins}
    for variant,build in config['builds'].items():
        root=WORK/'amended-native-v2'/variant
        paths=[p for p in (root/'source').rglob('*') if p.is_file()]+[Path(build['server'])]+[Path(build['server']).parent/name for name in build['numerical_DLL_sha256']]
        paths += [root/'SOURCE_HASHES.json',root/'PARENT_SOURCE_HASHES.json',root/'NATIVE_BUILD.json']
        for item in paths:files[str(item.resolve())]=pin(item)
    for item in [HERE/'INPUT_MANIFEST.json',HERE/'PRIMARY_IMPLEMENTATION_FREEZE.json',audit_path,HERE/'CAUSAL_TRACE_RULES.md',HERE/'OBSERVER_METADATA_CORRECTION.json']+list(HERE.glob('*.py')):
        files[str(item.resolve())]=pin(item)
    config['files']=list(files.values());config['held_out_execution_authorized_by_this_file']=True
    config['primary_implementation_freeze_commit']=commit;config['input_manifest_sha256']=r.sha(HERE/'INPUT_MANIFEST.json')
    config['schedule']=schedule(config);config['schedule_sha256']=digest(json.dumps(config['schedule'],sort_keys=True,separators=(',',':')).encode())
    r.save(HERE/'F0B_EXECUTION.json',config)
    print('Panel sealed',json.dumps(counts),'independent tasks',manifest['independent_task_count'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze-primary','select']);parser.add_argument('--primary-commit');parser.add_argument('--audit',type=Path);args=parser.parse_args()
    if args.action=='freeze-primary':primary_freeze()
    else:select(args.primary_commit,args.audit)
