"""Freeze and execute the complete six-arm panel after actual native qualification."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, math, sys, types
from common import need, read, save, sha
from host import run
from jobs import panel
from freeze import confirmation
from analysis import analyze
from native_checks import legacy_readers
from qualify_native import endpoint, Study

def prepare(w,repo):
 inputs=w/'inputs-01';models=read(inputs/'MODELS.json')['Qwen'];save(w/'panel-models-01.json',models)
 source=w/'stage-04/authenticated-kit/samples/R2-INPUTS.json';dest=w/'panel-01'
 panel(source,inputs/'PRIMERS.json',w/'panel-models-01.json',dest)
 plan=read(dest/'PLAN.json');roots=set(plan['roots']);prior=[]
 ledger=w/'ledger.jsonl'
 if ledger.exists():
  for line in ledger.read_text().splitlines():
   row=json.loads(line)
   if row.get('event')!='RESERVE':continue
   launch=Path(row['out'])/'launch.json'
   prior.append({'phase':row['phase'],'job_sha256':row['job_sha256'],'requests':row['requests'],'rows':row['rows']})
   # Every native run in this version retains its exact job through the
   # coordinator. The fixed R2 roots have not been submitted by any prior phase.
  need(not any(x['phase']=='confirmation' for x in prior),'Prospective panel prepared after timing outputs')
 # Development root identity is predeclared and disjoint from the transfer panel.
 for family in ('Qwen','Smol'):
  dev=read(inputs/(family+'-DEVELOPMENT.json'))['inputs'];need(not roots & {x['id'] for x in dev},'Development/test root overlap')
 save(dest/'PROSPECTIVE_ORDER.json',{'fixed_transfer_root_outputs_seen':0,'prior_native_reservations':prior,
     'prior_ledger_sha256':sha(ledger) if ledger.exists() else None,'plan_sha256':sha(dest/'PLAN.json'),
     'scope':'Previously exposed deployment-transfer roots; development outputs are separate from the fixed panel roots'})
 print(dest,flush=True)

def saved_cost_reader(repo):
 root=repo/'benchmarks/tpds_phase1_v1'
 for name in ('design','receipts'):
  module=types.ModuleType('_linux_saved_'+name);module.__file__=str(root/(name+'.py'))
  text=Path(module.__file__).read_text().replace('from design import','from _linux_saved_design import')
  sys.modules[module.__name__]=module;exec(compile(text,module.__file__,'exec'),module.__dict__)
 return sys.modules['_linux_saved_receipts'].saved_costs

def costs(w,repo,plan,records):
 workers={x['id']:x for x in plan['workers']};datasets={x:{'families':{'Qwen':{'roots':plan['roots'] if x=='measurement' else workers[records[0]['id']]['primers'],'arms':{}}}} for x in ('measurement','primer')}
 for record in records:
  worker=workers[record['id']]
  for i,call in enumerate(record['requests']):
   r=read(Path(call['native_receipt']));kind='primer' if i<2 else 'measurement'
   rows=datasets[kind]['families']['Qwen']['arms'].setdefault(worker['arm'],{'rows':[]})['rows']
   row={'root':call['root'],'session':worker['session'],'status':'COMPLETE','service_s':r['service_seconds'],'planning_s':r.get('planning_s'),
        'output_copy_s':r.get('output_copy_s'),'reset_s':r.get('setup_seconds'),'teardown_s':r.get('teardown_seconds'),'other_service_s':None,
        'target_phases':r.get('target_phases'),'draft_phases':r.get('draft_phases'),'phase_measurement_status':{'target_phases':{},'draft_phases':{}}}
   executed={'target_phases':{'PREFILL':True,'ORDINARY':not r['draft_enabled'] and len(r['ids'])>1,'VERIFY':r['draft_enabled'] and bool(r['cycles'])},
             'draft_phases':{'PREFILL':r['draft_enabled'],'DRAFT_SYNC':r['draft_enabled'] and bool(r['cycles']),'PROPOSE':r['draft_enabled'] and bool(r['cycles'])}}
   for role,phases in executed.items():
    for phase,ran in phases.items():
     if not ran:row['phase_measurement_status'][role][phase]='NOT_EXECUTED'
     elif phase in (row[role] or {}):row['phase_measurement_status'][role][phase]='MEASURED'
   rows.append(row)
 reader=saved_cost_reader(repo)
 for kind,data in datasets.items():
  p=w/'panel-01'/(kind.upper()+'-COST-INPUTS.json');save(p,data);save(p.with_name(kind.upper()+'-COST-COVERAGE.json'),reader(p,expected_sessions=4))

def execute(w,repo,qualification):
 dest=w/'panel-01';plan=read(dest/'PLAN.json');need(read(qualification/'NATIVE_CHECKS_COMPLETE.json')['passed'],'Native qualification required')
 freeze=dest/'CONFIRMATION_FREEZE.json';cfg=read(w/'config-reference-frozen-01.json')
 confirmation(Path(cfg['reference_freeze']),qualification/'REGISTRY.json',dest/'PLAN.json',freeze)
 cfg.update(freeze=str(freeze),freeze_sha256=sha(freeze));config=w/'config-confirmation-01.json';save(config,cfg)
 lookup={x['id']:x for x in read(w/'stage-04/authenticated-kit/samples/R2-INPUTS.json')['inputs']+read(w/'inputs-01/PRIMERS.json')['inputs']}
 order=plan['workers'][0]['primers']+plan['workers'][0]['roots'];need(len(order)==len(set(order))==18,'Fixed free-reference population')
 model=read(w/'inputs-01/MODELS.json')['Qwen'];model.pop('draft_model');model.pop('draft_sha256')
 reference_job=dict(model,residency='target_only',draft=False,inputs=[{'name':f'reference-{i}','input':lookup[key],'capture':False} for i,key in enumerate(order)])
 ref_job=dest/'REFERENCE-JOB.json';save(ref_job,reference_job);ref=dest/'reference-01';run(config,w/'build-R-01/BUILD.json',ref_job,ref,'reference')
 expected={key:read(ref/'native'/f'reference-{i}'/'receipt.json') for i,key in enumerate(order)}
 reference_id='Linux-R-'+sha(Path(cfg['reference_freeze']));trace,_=legacy_readers(repo);records=[];slots={x['id']:'NOT_RUN' for x in plan['workers']}
 try:
  for worker in plan['workers']:
   name=worker['id'];out=dest/'runs'/name;job=dest/worker['job'];slots[name]='STARTED'
   run(config,w/f'build-{worker["core"]}-01/BUILD.json',job,out,'confirmation')
   payload=read(job);meta=read(out/'native/result.json');draft=payload['draft']
   need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'Actual worker residency/model count')
   calls=[]
   for wanted,entry in zip(worker['primers']+worker['roots'],payload['inputs']):
    path=out/'native'/entry['name']/'receipt.json';r=read(path);need(endpoint(r)==endpoint(expected[wanted]),'Independent frozen R endpoint mismatch')
    r['study_cap']=entry['input']['cap'];_,decoded=trace(r,entry['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
    need(all(v==0 for v in r['observed_API_calls_within_service'].values()),'Heavy/state work in clean service')
    # This method checks actual native row counters and physical append tables;
    # it does not depend on Study's orchestration state.
    physical=Study.physical(r,entry['input'],draft)
    need(r['target_final_kv']=={'min':0,'max':len(decoded['states'][-1]['prefix'])-1},'Actual terminal pending frontier')
    calls.append({'root':wanted,'service_s':r['service_seconds'],'reference_id':reference_id,'reference_compatible':True,'trace_valid':True,
        'native_receipt':str(path),'native_receipt_sha256':sha(path),'reference_receipt_sha256':sha(ref/'native'/f'reference-{order.index(wanted)}'/'receipt.json'),
        'physical':physical,'ids':r['ids'],'eog':r['eog'],'terminal_kind':r['stop_reason']})
   clocks=read(out/'CLOCKS.json');host=read(out/'HOST.json');clocks.update(worker_wall_s=host['worker_wall_s'],wrapper_wall_s=host['wrapper_wall_s'],
       model_load_s=meta['model_load_s'],pool_setup_s=meta['pool_setup_s'])
   telemetry=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];need(telemetry,'Actual memory sampling missing')
   clocks['peak_observed_device_bytes']=max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in telemetry)
   clocks['memory_scope']='Selected-device global used bytes, 2s sampled lower bound on true peak; not a per-process high-water mark'
   checked={'id':name,'job_sha256':worker['job_sha256'],'status':'COMPLETE','native_checks_passed':True,'requests':calls,'actual_host_clocks':clocks,
      'launch_sha256':sha(out/'launch.json'),'loaded_modules_sha256':sha(out/'LOADED_MODULES.json'),'actual_processes':1,'model_loads':1}
   save(out/'CHECKED.json',checked);records.append(checked);slots[name]='COMPLETE';print('COMPLETE_WORKER',len(records),24,name,flush=True)
  save(dest/'CHECKED.json',records);save(dest/'RESULTS.json',analyze(plan,records));costs(w,repo,plan,records)
 finally:
  for key in slots:
   if slots[key]=='STARTED':slots[key]='FAILED_RETAINED'
  save(dest/'ALL_SLOT_STATUS.json',{'slots':slots,'complete_workers':len(records),'expected_workers':24,'expected_measurements':384,'expected_primers':48,
      'no_selective_retries':True,'all_controls_retained':True,'inference_open':len(records)==24})

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--work',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--qualification',type=Path)
 a=p.parse_args();w=a.work.resolve();repo=a.repo.resolve()
 if a.action=='prepare':prepare(w,repo)
 else:need(a.qualification is not None,'Actual qualification directory');execute(w,repo,a.qualification.resolve())
