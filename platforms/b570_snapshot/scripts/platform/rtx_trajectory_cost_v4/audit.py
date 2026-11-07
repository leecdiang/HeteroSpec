"""Pre-forward incremental exposure audit: retain full V3 inventory and scan real raw records."""
import hashlib,json
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,now
PREVIOUS=ROOT.with_name('HeteroSpec-v3')
PM=PREVIOUS/'benchmarks/rtx_trajectory_cost_v3'
SALT='RTX_TRAJECTORY_SUFFICIENCY_V4|reserved|20261002|'
def main():
    from engine import prompts
    prior=json.loads((PM/'EXPOSURE_AUDIT.json').read_text(encoding='utf-8'))
    previous_set=json.loads((PM/'RESERVED_SET.json').read_text(encoding='utf-8'))
    assert prior['status']=='PASS' and not prior['errors'] and len(prior['eligible_pool'])==26
    originals=json.loads((PM/'F0_MANIFEST.json').read_text(encoding='utf-8'))['files']
    assert sha(PM/'EXPOSURE_AUDIT.json')==originals['benchmarks/rtx_trajectory_cost_v3/EXPOSURE_AUDIT.json']['sha256']
    errors=[];catalog=[];exclusions={t:list(v) for t,v in prior['exclusion_reasons'].items()};exposed=set();workspace=ROOT.parents[1]
    for p in sorted(workspace.glob('work/**/record.json')):
        if p.is_relative_to(ROOT):continue
        try:r=json.loads(p.read_text(encoding='utf-8'))
        except (UnicodeError,json.JSONDecodeError,OSError) as e:errors.append({'path':str(p),'error':repr(e)});continue
        task=r.get('task_id')
        if not isinstance(task,str) or not task.startswith('HumanEval/'):continue
        if not r.get('command') and not (p.parent/'events.jsonl').exists():continue
        evidence={'path':p.relative_to(workspace).as_posix(),'sha256':sha(p),'task_id':task,'status':r.get('status'),'run_id':r.get('run_id'),'phase':r.get('phase'),'process_returncode':r.get('process_returncode'),'record_created_before_V4':True}
        catalog.append(evidence);exposed.add(task)
        exclusions.setdefault(task,[]).append({'path':evidence['path'],'reason':'Actual prior raw process record; conservatively exclude also failed/in-flight records','sha256':evidence['sha256']})
    tasks=prompts();eligible=sorted(t for t in tasks if t not in exclusions)
    keys={t:hashlib.sha256((SALT+t).encode()).hexdigest() for t in eligible};selected=sorted(eligible,key=lambda t:(keys[t],t))
    assert not errors,errors
    assert len(eligible)==19,(len(eligible),eligible)
    new_exposed=sorted(set(previous_set['eligible_pool'])&exposed)
    assert set(new_exposed)=={f'HumanEval/{i}' for i in [2,161,86,157,16,158,59]},new_exposed
    prior_catalog=ROOT/'work/PREVIOUS_exposure_catalog.json';assert sha(prior_catalog)==prior['catalog_sha256']
    save(ROOT/'work/exposure_catalog.json',{'previous_full_catalog_path':'work/PREVIOUS_exposure_catalog.json','previous_full_catalog_sha256':sha(prior_catalog),'previous_catalog_entries':prior['catalog_entries'],'incremental_raw_records':catalog,'errors':errors,'newly_exposed_eligible_tasks':new_exposed})
    save(STUDY/'EXPOSURE_AUDIT.json',{'utc':now(),'status':'PASS','errors':errors,'exclusion_reasons':exclusions,'eligible_pool':eligible,'auditor_sha256':sha(Path(__file__)),'catalog_sha256':sha(ROOT/'work/exposure_catalog.json'),'catalog_entries':prior['catalog_entries']+len(catalog),'previous_full_audit_sha256':sha(PM/'EXPOSURE_AUDIT.json'),'previous_full_catalog_sha256':sha(prior_catalog),'previous_full_catalog_entries':prior['catalog_entries'],'incremental_records':len(catalog),'previous_published_HEAD':'9ce203265c867bc847b13cb440c2339d54a50e6f','prior_excluded':138,'newly_exposed':new_exposed,'all_remaining_untouched_selected':True,'new_inference_executed':False,'scope_limit':prior['scope_limit'],'historical_missing_archives_limit':'Prior conservative exclusions and missing-archive limitations remain unchanged.'})
    save(STUDY/'RESERVED_SET.json',{'status':'PASS','salt':SALT,'universe':sorted(tasks),'eligible_pool':eligible,'selection_keys':keys,'selected_task_ids':selected,'input_hashes':{t:hashlib.sha256(tasks[t].encode()).hexdigest() for t in selected},'model_forward_count':0,'tokenizer_forward_count':0,'cohort_amendment':'Use all 19 remaining untouched tasks; do not resume the failed V3 24-task study.'})
    save(STUDY/'EXPOSURE_AUDIT_LINEAGE.json',{'prior_audit':prior,'prior_reserved_set':previous_set,'prior_F0_manifest_sha256':sha(PM/'F0_MANIFEST.json'),'prior_final_publication':'9ce203265c867bc847b13cb440c2339d54a50e6f','prior_F0':'a48381567f7f40330a589e33d285650c9e91f209','new_raw_evidence_catalog_sha256':sha(ROOT/'work/exposure_catalog.json')})
    print(json.dumps({'status':'PASS','eligible':len(eligible),'excluded':164-len(eligible),'newly_exposed':new_exposed,'selected':selected,'incremental_records':len(catalog)}),flush=True)
if __name__=='__main__':main()
