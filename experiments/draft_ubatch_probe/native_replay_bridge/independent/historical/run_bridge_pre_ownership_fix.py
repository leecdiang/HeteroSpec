#!/usr/bin/env python3
"""Bounded actual CPU capture/replay bridge. Never launches a GPU experiment."""
import argparse,hashlib,json,pathlib,subprocess,time,sys,os,shutil,struct
from parse_state import parse,BYTES_PER_TOKEN
sys.path.insert(0,str(pathlib.Path(__file__).parent/'offline'))
import replay_audit as A
ROOT=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def run(args):
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bundle=out/'bundle';bundle.mkdir();(out/'cpuinfo.txt').write_bytes(pathlib.Path('/proc/cpuinfo').read_bytes())
 model=args.model.resolve();lib=args.library_dir.resolve();source=args.source.resolve();binary=args.binary.resolve()
 build=json.loads((binary.parent/'build.json').read_text());A.need(build['status']=='PASS' and build['binary_sha256']==sha(binary),'binary build receipt mismatch')
 for name,h in build['sources'].items():A.need(sha(ROOT/name)==h,'compiled source changed '+name)
 expected_model=json.loads((ROOT/'MODEL_PINS.json').read_text());A.need(sha(model) in expected_model.values(),'unregistered synthetic model')
 source_pins=json.loads((ROOT/'SOURCE_PINS.json').read_text())
 for name,h in source_pins.items():A.need(sha(source/name)==h,'source mismatch '+name)
 expected_libs=json.loads((ROOT/'LIBRARY_PINS.json').read_text());A.need({p.name:sha(p) for p in lib.glob('*.so')}==expected_libs,'unregistered CPU libraries')
 libraries={str(p.resolve()):sha(p) for p in lib.glob('*.so')}
 A.need(len(libraries)==4 and libraries==build['libraries'],'unexpected native library set or build linkage drift')
 identity_base={'model':sha(model),'binary':sha(binary),'libraries':libraries,'source':source_pins,'context':{'requested_n_ctx':128,'n_batch':128,'n_ubatch':1,'n_outputs_max':4,'n_outputs_max_per_seq':4,'threads':1,'kv':'F16','flash':'disabled','seq':0},'backend':'CPU','prompt_producer':'whole_prompt_last_only','continuation':'singleton_last_only','scope':'fresh CPU synthetic family; NOT PR151 resident-reset R'}
 receipt={'status':'STARTED','processes':[],'identity_base':identity_base,'gpu_qualification_established':False,'implementation_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'run_bridge.py',ROOT/'parse_state.py',ROOT/'offline/replay_audit.py']},'host':{'machine':os.uname().machine,'kernel':os.uname().release,'cpuinfo_sha256':sha(out/'cpuinfo.txt'),'byteorder':sys.byteorder,'python':sys.version},'build_receipt_sha256':sha(binary.parent/'build.json'),'experiment_kind':'NATIVE_DRAFT_PROPOSALS' if args.reject==-1 else 'ORACLE_CONTROLLED_PROTOCOL_PROBE'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
 def launch(mode,config):
  config_path=out/(mode+'-input.json');dump(config_path,config);dest=out/mode;record={'mode':mode,'input_sha256':sha(config_path),'status':'STARTED'};receipt['processes'].append(record);(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
  env=os.environ.copy()
  for k in list(env):
   if k.startswith(('HS_','GGML_','LLAMA_')) or k in ('LD_PRELOAD','LD_LIBRARY_PATH'):env.pop(k)
  t=time.monotonic()
  with (out/(mode+'.stdout')).open('w') as so,(out/(mode+'.stderr')).open('w') as se:
   cp=subprocess.run([str(binary),mode,str(model),str(config_path),str(dest)],stdout=so,stderr=se,env=env)
  record.update(returncode=cp.returncode,wall_seconds=time.monotonic()-t,status='COMPLETED' if cp.returncode==0 else 'FAILED');(out/'receipt.json').write_text(json.dumps(receipt,indent=2));A.need(cp.returncode==0,'native process failed: '+mode)
  result=json.loads((dest/'capture.json').read_text());paths=set(result['loaded_mapping_paths']);record['loaded_regular_file_sha256']={p:sha(pathlib.Path(p)) for p in sorted(paths) if pathlib.Path(p).is_file()}
  for p,h in libraries.items():A.need(p in paths and sha(pathlib.Path(p))==h,'loaded numerical library binding differs')
  numerical={p for p in paths if pathlib.Path(p).name.startswith(('libggml','libllama'))};A.need(numerical==set(libraries),'unexpected numerical module')
  A.need(result['status']=='COMPLETED','incomplete native capture');record['native_metrics']=result['metrics'];record['pid']=result['pid'];return result,dest
 candidate,cd=launch('candidate',{'prompt_ids':[1,2,3,4,5,6,7],'cap':args.cap,'forced_reject_index':args.reject,'draft_ubatch':args.draft_ubatch,'stop_after_output_index':args.stop})
 identity_base['observed_loaded_modules']=receipt['processes'][0]['loaded_regular_file_sha256']
 prompt=[1,2,3,4,5,6,7];nv=candidate['vocab'];eog=candidate['eog_ids']
 actual={(e['actual_n_ctx'],e['actual_n_ctx_seq'],e['actual_n_batch']) for e in candidate['execution']};A.need(len(actual)==1,'context geometry changes');ctx,ctxseq,nb=next(iter(actual));identity_base['context'].update(actual_n_ctx=ctx,actual_n_ctx_seq=ctxseq,actual_n_batch=nb)
 identity={'reference_deployment_sha256':A.digest(dict(identity_base,lifecycle='fresh reference process, fresh context per maximal path')),'candidate_deployment_sha256':A.digest(dict(identity_base,lifecycle='fresh candidate process and contexts',draft_ubatch=args.draft_ubatch)),'target_model_sha256':sha(model),'tokenizer_sha256':A.digest(candidate['tokenizer']),'vocab':nv,'n_ctx':ctx,'candidate_target_ubatch':1,'candidate_prefill_recipe':'whole_prompt_last_only','reference_recipe':'historical_prefill_then_scalar','binding_complete':True,'eog_ids':eog,'kv_bytes_per_token':BYTES_PER_TOKEN,'state_format':'tiny-llama-seq0-f16-active-v1','scope':'NATIVE_CPU_SYNTHETIC_FRESH_REFERENCE_ONLY_NOT_HISTORICAL_R','logical_token_budget':128,'token_namespace_status':'SYNTHETIC_IDS_NO_REAL_TOKENIZER_OR_NATURAL_EOG','binding_status':'RECORDED_LOCAL_TOOLCHAIN_IDENTITY_NOT_CRYPTOGRAPHIC_ATTESTATION'}
 plan=A.make_plan(candidate['case'],prompt,identity);dump(out/'identity.json',identity);dump(out/'plan.json',plan);dump(out/'trace.json',{'prompt_ids':prompt,'case':candidate['case']})
 qmap={q['query_id']:q for q in plan['queries']}
 jobs=[{'job_id':j['job_id'],'tokens':j['tokens'],'queries':[{'query_id':qid,'length':len(qmap[qid]['tokens']),'state_required':qmap[qid]['state_required']} for qid in j['query_ids']]} for j in plan['fresh_replay_jobs']]
 reference,rd=launch('reference',{'prompt_ids':prompt,'jobs':jobs})
 # This process receives no candidate trace, decisions, endpoint or forced jobs.
 free,fd=launch('free',{'prompt_ids':prompt,'cap':args.cap,'stop_after_output_index':args.stop})
 A.need(all(x['loaded_regular_file_sha256']==identity_base['observed_loaded_modules'] for x in receipt['processes']),'loaded module set differs across roles')
 A.need(len({x['pid'] for x in receipt['processes']})==3,'roles did not use distinct processes')
 for r in [reference,free]:
  A.need(all((e['actual_n_ctx'],e['actual_n_ctx_seq'],e['actual_n_batch'])==(ctx,ctxseq,nb) for e in r['execution']),'role context geometry differs')
  A.need(r['tokenizer']==candidate['tokenizer'] and r['eog_ids']==eog,'model/tokenizer differs across roles')
 raw_retained=[];parses=[]
 def put(b):
  h=hashlib.sha256(b).hexdigest();p=bundle/(h+'.bin')
  if p.exists():A.need(p.read_bytes()==b,'hash collision')
  else:p.write_bytes(b)
  return {'path':p.name,'sha256':h,'bytes':len(b)}
 def payload(root,ref):
  p=(root/ref['path']).resolve();A.need(p.is_relative_to(root.resolve()),'native payload path escape');b=p.read_bytes();A.need(len(b)==ref['bytes'],'native size mismatch');return b
 def vec(root,ref):return put(payload(root,ref))
 def state(root,ref,tokens):
  raw=payload(root,ref);raw_ref=put(raw);canonical,meta=parse(raw,tokens);parses.append(dict(meta,raw=raw_ref,tokens=tokens));raw_retained.append(raw_ref);return put(canonical)
 def observed_execution(events,tokens):
  decoded=[];widths=[];masks=[]
  for e in events:
   A.need(e['base']==len(decoded),'native call position discontinuity');A.need(e['physical_ubatch_capacity']==1,'reference capacity not scalar');decoded+=e['tokens'];widths.append(e['caller_width']);masks.append(e['logits_mask'])
  A.need(decoded==tokens,'native executed token prefix differs')
  return {'mode':'forced_prefix','fresh_context':True,'start_empty':True,'decoded_tokens':decoded,'positions':list(range(len(decoded))),'sequence_id':0,'caller_widths':widths,'physical_ubatches':[1]*len(decoded),'logits_masks':masks}
 evidence={'candidate_identity':identity['candidate_deployment_sha256'],'reference_identity':identity['reference_deployment_sha256'],'state_format':identity['state_format'],'candidate_rows':{},'candidate_commits':{},'reference_queries':{},'reference_jobs':{}}
 for use in plan['uses']:
  ob=candidate['rows'][use['use_id']];q=qmap[use['query_id']];A.need(ob['tokens']==q['tokens'],'native row prefix differs')
  producer=A.candidate_metadata(ob['call_tokens'],ob['base'],ob['row'],'prefill' if use['use_id']=='initial' else 'verify-'+use['use_id'].split('-')[1],identity)
  events=[e for e in candidate['execution'] if e['role'].startswith('candidate_target_')];event=events[0 if use['use_id']=='initial' else int(use['use_id'].split('-')[1])+1]
  A.need(event['tokens']==producer['tokens'] and event['base']==ob['base'] and event['logits_mask']==producer['logits_mask'] and event['physical_ubatch_capacity']==1,'candidate call capture differs')
  evidence['candidate_rows'][use['use_id']]={'query_id':use['query_id'],'producer':producer,'logits':vec(cd,ob['logits'])}
 for job in plan['fresh_replay_jobs']:
  ob=reference['jobs'][job['job_id']];events=reference['execution'][ob['execution_start']:ob['execution_end']];execution=observed_execution(events,job['tokens']);observations={}
  for qid,o in ob['observations'].items():
   n=len(o['tokens']);prefix_events=[];count=0
   for e in events:
    if count+e['caller_width']>n:break
    prefix_events.append(e);count+=e['caller_width']
   meta=observed_execution(prefix_events,o['tokens']);r=dict(meta,logits=vec(rd,o['logits']))
   if qmap[qid]['state_required']:r['kv']=state(rd,o['serialized_sequence'],o['tokens'])
   observations[qid]=r;evidence['reference_queries'][qid]=r
  evidence['reference_jobs'][job['job_id']]={'start_empty':True,'status':'COMPLETED','tokens':ob['tokens'],'execution':execution,'observations':observations}
 for commit in plan['commits']:
  ob=candidate['commits'][commit['commit_id']];A.need(ob['tokens']==commit['tokens'] and ob['kv_min']==0 and ob['kv_max']==len(ob['tokens'])-1,'native commit prefix/positions differ')
  c={key:ob[key] for key in ['next_position','sequence_id','unmaterialized_output','pending_for_next_loop','done']};c.update(query_id=commit['query_id'],positions=list(range(len(ob['tokens']))),frontier_logits_use=commit['frontier_logits_use'],kv=state(cd,ob['serialized_sequence'],ob['tokens']),frontier_logits=vec(cd,ob['frontier_logits']));evidence['candidate_commits'][commit['commit_id']]=c
 ob=free['free'];execution=observed_execution(free['execution'],ob['decoded_tokens']);contract={'cap':args.cap,'eog_ids':eog,'synthetic_stop_after':args.stop};reason='EOG' if ob['output'][-1] in eog else ('CAP' if len(ob['output'])==args.cap else 'SYNTHETIC_STOP')
 evidence['free_scalar_run']=dict(execution,mode='autonomous_scalar',forced_tokens_used=False,prompt_ids=prompt,cap=args.cap,prefixes=ob['prefixes'],output=ob['output'],eog_flags=ob['eog_flags'],logits=[vec(fd,x) for x in ob['logits']],stop_contract=contract,stop_reason=reason)
 dump(out/'state-extraction.json',parses);dump(out/'evidence.json',evidence)
 t=time.monotonic();report=A.audit(plan,evidence,bundle,identity);receipt['offline_audit_wall_seconds']=time.monotonic()-t;dump(out/'audit.json',report)
 receipt.update(status='RECORDED_EVIDENCE_MATCH',unique_bundle_payload_bytes=sum(p.stat().st_size for p in bundle.iterdir()),raw_native_payload_bytes=sum(r['native_metrics']['raw_payload_bytes_written'] for r in receipt['processes']),forced_jobs=len(jobs),state_observations=len(parses),qualification=False)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--library-dir',type=pathlib.Path,required=True);p.add_argument('--binary',type=pathlib.Path,required=True);p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--cap',type=int,default=5);p.add_argument('--reject',type=int,default=-1);p.add_argument('--draft-ubatch',type=int,default=2);p.add_argument('--stop',type=int,default=0);a=p.parse_args()
 try:run(a)
 except Exception as exc:
  receipt=a.output/'receipt.json'
  if receipt.exists():
   previous=json.loads(receipt.read_text());previous.update(status='FAILED',failure=type(exc).__name__+': '+str(exc));receipt.write_text(json.dumps(previous,indent=2)+'\n')
  raise
