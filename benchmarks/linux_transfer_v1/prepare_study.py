"""Prepare fixed development jobs before candidate outputs, without loading models."""
from pathlib import Path
import argparse, copy
from common import need, read, save, sha
HERE=Path(__file__).resolve().parent

def prepare(work,stage,repo):
 work=Path(work).resolve();stage=Path(stage).resolve();repo=Path(repo).resolve();out=work/'inputs-01'
 need(not out.exists(),'Retain input epochs');out.mkdir()
 pins=read(HERE/'pins.json');schedule={};models={}
 for family,files in [('Qwen',('Qwen3-8B-Q8_0.gguf','Qwen3-0.6B-Q8_0.gguf')),('Smol',('SmolLM2-1.7B-Instruct-Q8_0.gguf','SmolLM2-135M-Instruct-Q8_0.gguf'))]:
  models[family]={'family':family,'target_model':str(work.parent/'models-final'/files[0]),'target_sha256':pins['models'][family]['target'],
                  'draft_model':str(work.parent/'models-final'/files[1]),'draft_sha256':pins['models'][family]['draft'],'n_ctx':1024,'threads':2}
  original=read(stage/'authenticated-kit/samples'/('R1-'+family+'-JOB.json'))
  cases=copy.deepcopy(original['cases'])
  tape=max((sum((x['ids'] for x in c['forced']),[]) for c in cases),key=len)
  need(len(tape)>=799,'Retained boundary witness truncated')
  extra=[('q1-inside',766,1,False),('q1-boundary',767,1,False),('q4-tail',796,3,False),('q8-tail',792,7,False),('q32-tail',780,19,False),('q4-all-requested',767,4,True)]
  for name,head,width,all_rows in extra:
   end=head+width;cases.append({'name':name,'forced':[{'ids':tape[:head],'phase':'PREFILL','all':False},{'ids':tape[head:end],'phase':'VERIFY','all':all_rows}],
     'observe_positions':[head]+(list(range(head+1,end+1)) if all_rows else [end]),'state_positions':[end]})
  roots_path=repo/'benchmarks/rtx_phase_plan_v1/host_evidence/host'/(family+'-EXPOSED-ROOTS.json')
  roots=read(roots_path)['inputs'];need(len(roots)==4,'Known exposed development family')
  save(out/(family+'-DEVELOPMENT.json'),{'inputs':roots,'source_file_sha256':sha(roots_path),'status':'PREVIOUSLY_EXPOSED_DEVELOPMENT'})
  save(out/(family+'-GEOMETRY.json'),{'cases':cases,'source_sample_sha256':sha(stage/'authenticated-kit/samples'/('R1-'+family+'-JOB.json')),
       'scope':'q1/4/8/32, retained inside/crossing witness, tails, all requested q4 vectors; states only at committed call ends'})
  base={k:v for k,v in models[family].items() if not k.startswith('draft')}
  base.update(residency='target_only',draft=False)
  for repeat in (1,2):
   save(out/f'{family}-R-repeat-{repeat}.json',dict(base,cases=[cases[3],cases[-1]]))
   save(out/f'{family}-R-free-repeat-{repeat}.json',dict(base,inputs=[{'name':f'dev-{i}','input':row,'capture':True} for i,row in enumerate(roots[:2])]))
  save(out/(family+'-R-matrix.json'),dict(base,cases=cases))
  schedule[family]={'matrix_cases':len(cases),'development_roots':[r['id'] for r in roots],
      'before_candidate_outputs':['R-repeat-1','R-repeat-2','R-free-repeat-1','R-free-repeat-2'],
      'qualification':'four target-only cut/projection combinations and both D4 controls; independent forced-prefix vectors and all captured committed states',
      'no_model_name_or_position_exceptions':True}
 save(out/'MODELS.json',models)
 save(out/'PRIMERS.json',{'inputs':read(out/'Qwen-DEVELOPMENT.json')['inputs'][:2],'policy':'Two original exposed GSM development roots, disjoint from all16 fixed transfer roots'})
 save(out/'CONTRACT_BEFORE_OUTPUTS.json',{'schema':'linux-transfer.native-contract.v1','reference':'pristine upstream 0cae43063cf15170e91a2ff4d034da0ecef4a1b2',
      'context':1024,'family_pins':pins['models'],'threads':2,'historical_candidate_threads_observed_in_kit':24,
      'reference_ubatch':1,'reference_output_reservation':1,'candidate_target_ubatch':32,'candidate_target_output_reservation':4,
      'candidate_reservation_difference_requires_full_vector_and_state_qualification':True,'prompt_producer':'whole prompt caller, last-only output',
      'KV':'F16 K/V, dense seq0','flash_attention':False,'sampling':'greedy, native EOG or requested cap, final pending token unmaterialized',
      'D4':'draft physical prefill UB4, k3','static_linking':'all llama/base/CPU/CUDA modules freshly source-built; driver/toolkit libraries observed',
      'clean':'no heavy observer, reference replay, KV migration, state export/import or context creation inside service',
      'CUDA_graph_reuse':'preserve installed pinned source defaults for every role','panel':'all16 previously exposed PR195 deployment-transfer roots; no new blind-sample claim',
      'maximum_requests':2048,'maximum_reserved_rows':4000000,'study_schedule':schedule,'candidate_outputs_seen':0})
 print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('work','stage','repo'):p.add_argument('--'+k,required=True)
 a=p.parse_args();prepare(a.work,a.stage,a.repo)
