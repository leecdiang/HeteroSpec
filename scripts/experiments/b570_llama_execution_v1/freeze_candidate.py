"""Evidence-backed freeze and subsequent, single prospective panel selection."""
from pathlib import Path
import argparse,shutil,sys,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,utc
import host,panel,budget

def freeze(root,epoch,repo):
    root=Path(root);epoch=Path(epoch);repo=Path(repo);need(not Path('C:/hs/b570-llama-exclusive.lock').exists(),'settle all native work before freeze');need(not budget.totals(root/'research/LEDGER.jsonl')['open'],'unsettled ledger')
    source_paths=['scripts/experiments/b570_llama_companion_v1','scripts/experiments/b570_llama_execution_v1']
    subprocess.run(['git','diff','--quiet','HEAD','--',*source_paths],cwd=repo,check=True)
    need(not subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',*source_paths],cwd=repo).strip(),'commit all scientific source before freeze')
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    need(read(root/'FINAL_PREFREEZE_CONTROLS-00.json')['status']=='FINAL_NATIVE_CONTROLS_PASS','final controls')
    need(read(root/'FINAL_CONTROLLED_TRACE-00.json')['status']=='FINAL_CONTROLLED_TRACE_PASS','final trace reconstruction')
    need(read(root/'COMBINED_INDEPENDENT_DEVELOPMENT-00.json')['status']=='INDEPENDENT_COMPLETE_QUALIFICATION_PASS','independent full development')
    need(read(epoch/'BASELINE_AUDIT.json')['all_reference_equal'] and read(epoch/'BASELINE_AUDIT.json')['pure_layout_correspondence'],'whole development matrix')
    need(read(root/'COMBINED_COMMITTED_AUDIT-03.json')['status']=='COMMITTED_REFERENCE_VECTORS_PASS','all committed vectors')
    for name in ('Q8_FACTOR_REVERSAL-00.json','PREFIX_FACTOR_REVERSAL-00.json'):need(read(root/name)['status']=='COMPLETE_FACTOR_REVERSAL_PASS' and read(root/name)['requests']==36,'full factor reversal')
    ablation=root/'combined-no-q8-epoch-03/BASELINE_AUDIT.json';a=read(ablation);need(not a['all_reference_equal'] and a['pure_layout_correspondence'] and all(c['observer_stable'] for c in a['cells']),'Q8 factor ablation must reproduce failure with stable controls')
    proof=read(root/'COMBINED_PROBE_AUDIT-00.json');need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS' and len(proof['results'])==5 and all(row['bitwise_equal'] for item in proof['results'] for row in item['rows']),'final common-state equality')
    qwen=[read(root/f'QWEN_FINAL_AUDIT-0{i}.json') for i in range(4)];need(all(x['status']=='HISTORICAL_REQUEST_REPLAY_PASS' for x in qwen) and sum(x['full_vector_count'] for x in qwen)==914,'unchanged old Qwen auditor')
    exposure=root/'EXPOSURE_AUDIT-00.json';need(read(exposure)['complete'] and not read(exposure)['unresolved_sources'],'cross-platform exposure inventory')
    snapshot=root/'freeze-code-00';need(not snapshot.exists(),'fresh source snapshot');snapshot.mkdir()
    for folder in ('b570_llama_companion_v1','b570_llama_execution_v1'):shutil.copytree(repo/'scripts/experiments'/folder,snapshot/folder,ignore=shutil.ignore_patterns('__pycache__'))
    write(snapshot/'SOURCE_FILES.json',{'utc':utc(),'files':[{'path':p.relative_to(snapshot).as_posix(),'sha256':sha(p)} for p in sorted(snapshot.rglob('*')) if p.is_file()]})
    evidence=[epoch/'BASELINE_AUDIT.json',ablation,snapshot/'SOURCE_FILES.json']+[root/n for n in ['HISTORICAL_RAW_AUDIT-00.json','COMBINED_INDEPENDENT_DEVELOPMENT-00.json','COMBINED_COMMITTED_AUDIT-03.json','COMBINED_GEOMETRY_AUDIT-00.json','FROZEN_REFERENCE_STABILITY-00.json','Q8_FACTOR_REVERSAL-00.json','PREFIX_FACTOR_REVERSAL-00.json','FINAL_PREFREEZE_CONTROLS-00.json','COMBINED_PROBE_AUDIT-00.json','FINAL_PROJECTION_WIDTHS_AUDIT-00.json','AV_EXTENT_AUDIT-00.json','ATTENTION_REPLAY_AUDIT-cycle0-00.json','ATTENTION_REPLAY_AUDIT-cycle8-00.json','COMBINED_BINARY_DIFF-00.json','tests-07.log','prefix-guards-00.log']]+[root/f'QWEN_FINAL_AUDIT-0{i}.json' for i in range(4)]
    review={'disposition':'EVIDENCED_REPAIR','baseline_oracle_stable':True,'observation_controls_pass':True,'ablation_pass':True,'mechanism':'Real B570 producer/dispatch controls isolate q1 F32 versus q4 Q8_1 activation quantization in Q8 projection before RoPE. With that factor repaired, actual cycle8/base765 exhibits the independent scalar768/batched1024 physical-prefix effect: visible V, QK and probabilities agree, and crossed-extent AV replays exchange results, including the actual nc/contiguous Vulkan dispatch change. Explicit scoped F32 Q8 projection and maximal adjacent equal-prefix attention groups restore every committed scalar-reference vector. Independent switches reproduce the two respective failures. Grouping remains batched at width3 plus the required scalar boundary row, with actual Vulkan0 scheduler evidence in all layers.','regression_summary':'Final binary passes 12 historical Qwen requests and all914 saved vectors/old descriptors under the unchanged original auditor. Frozen original Llama R remains bitwise stable across all384 development reference vectors. Repaired q1/q4 probe rows all match, and original observed trajectories are preserved by controls. Real attention replay covers q1..4 at keys768/1024; historical valid q2/q4 key256/512 evidence and old-path regressions are retained. Invalid historical post-consumer alias captures are excluded.','evidence':[{'path':str(p.resolve()),'sha256':sha(p)} for p in evidence],'cross_project_exposure_audit':{'path':str(exposure),'sha256':sha(exposure)},'candidate_build_sha256':sha(root/'candidate-combined-02/BUILD.json'),'original_reference_build_sha256':sha(root/'oracle-01/BUILD.json'),'numerical_policy':{'reference_q8':True,'prefix_extent':True,'target_gpu_layers':999,'draft_gpu_layers':0,'threads':8,'k':3,'cap':128,'n_ctx':1024,'kv_dtype':'F16','flash_attention':False},'confirmation_count':24,'timing_periods':6,'no_performance_claim_before_complete_costs':True,'failures_and_exposures_preserved':True}
    review['evidence'].append({'path':str(root/'FINAL_CONTROLLED_TRACE-00.json'),'sha256':sha(root/'FINAL_CONTROLLED_TRACE-00.json')})
    review['evidence'].append({'path':str(root/'FREEZE_REMOTE_COORDINATION-00.json'),'sha256':sha(root/'FREEZE_REMOTE_COORDINATION-00.json')})
    review['source_commit']=source_commit
    out=root/'FREEZE_REVIEW-00.json';write(out,review);host.review_freeze(epoch,out)
    panel.make(root/'natural-pool-00/POOL.json',exposure,epoch/'FREEZE.json',root/'UNSEEN_PANEL-00.json',24)
    print('FROZEN_AND_THEN_SELECTED_24_UNSEEN',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','epoch','repo'):p.add_argument('--'+k,required=True)
    a=p.parse_args();freeze(a.root,a.epoch,a.repo)
