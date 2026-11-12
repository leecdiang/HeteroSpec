"""Synthetic serialized R-prefix for consumer integration tests, NEVER native data.

All tensor values are artificial zero bytes. No producer, sampling, tokenizer,
model, context, placement or forward occurs. Deliberately fake source bindings
are usable only by the pure-file verifier tests, not production admission.
"""
import json,pathlib
from stage_verify import digest,ROLES,EOG

FAKE='c'*64
def build_synthetic_prefix(verifier,root,last_role=ROLES[0],append=False):
 root=pathlib.Path(root);root.mkdir(exist_ok=append);proposal=verifier.proposal
 template=json.loads((verifier.repo/'benchmarks/server_expansion_v1/N/native_chain_successor_20261112/NATIVE_JOB_TEMPLATE.json').read_text())
 identity={k:FAKE for k in ('contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256')};identity.update(model_sha256=proposal['freezes']['model_sha256'],template_sha256=proposal['freezes']['template_sha256'])
 manifest={'run_id':'CPU_SYNTHETIC_FILES_NOT_NATIVE','worker_bindings':{},'stage_check_ids':{role:[c['id'] for c in verifier.stage_checks(role)[1]] for role in ROLES}}
 allowed=set(ROLES[:ROLES.index(last_role)+1])
 for role in allowed:
  for cohort in ('NATURAL','CONTROL'):manifest['worker_bindings'][role+'/'+cohort]={'source_sha256':FAKE,'executable_sha256':FAKE,'writer_sha256':FAKE,'identity':identity}
 def put(name,v):
  b=(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n').encode()
  with (root/name).open('xb') as f:f.write(b)
  return {'file':name,'sha256':digest(b)}
 def record(key,v):return put(digest(key.encode())[:32]+'.json',v)
 def tensor(folder,name,dtype,shape,axes):
  n=2 if dtype=='F16LE' else 4
  for d in shape:n*=d
  data=b'\0'*n;rel=folder+'/'+name+'.bin';(root/rel).write_bytes(data)
  return {'name':name,'file':rel,'dtype':dtype,'shape':shape,'axes':axes,'bytes':n,'sha256':digest(data),'canonical_numeric':True}
 def commit(key,phase,s,context,charged=None):
  folder=digest((key+'/'+phase).encode())[:24]+'-'+phase;(root/folder).mkdir();s=dict(s)
  if s['schema']=='hs.N1a.raw-state.v1':
   h=s['head'];s['tensors']={k:tensor(folder,k,'F16LE',[36,8,h,128],['layer','kv_head','position','dimension']) for k in ('active_k','active_v')};s['tensors']['vectors']=tensor(folder,'vectors','F32LE',[len(s['requested_vector_positions']),151936],['requested_row','vocabulary']);tensors=list(s['tensors'].values())
  else:s['tensor']=tensor(folder,'owned','F32LE',[1,151936],['requested_row','vocabulary']);tensors=[s['tensor']]
  d=put(folder+'/SNAPSHOT.json',s);transport={'schema':'hs.N1chain.raw-transport.v1','run_id':manifest['run_id'],'operation_id':charged or s['operation_id'],'context_id':context,'source_sha256':FAKE,'executable_sha256':FAKE,'capture_writer_sha256':FAKE,'snapshot_sha256':d['sha256'],'native_qualified':False,'tensors':tensors};put(folder+'/COMPLETE.json',transport);put(folder+'/TRANSPORT.pending',transport)
  if s['schema']=='hs.N1a.raw-state.v1':d.update(operation_id=s['operation_id'],phase=phase,run_id=manifest['run_id'],executable_sha256=FAKE)
  return s,d
 def state(op,phase,q,keep,context,control,ordinal,generated=None):
  reset=phase=='RESET';terminal=phase=='TERMINAL';appended=phase=='POST_APPEND';g=generated or [];h=0 if reset else keep if phase=='POST_RECONCILE' else len(q);canonical=[] if reset else q;m=canonical[:h];cold=op.split('/')[1]==ROLES[2];frontier=appended or terminal or cold and phase=='POST_RECONCILE' and h>0;positions=[len(q)-1] if terminal else [h-1] if frontier else []
  s={'schema':'hs.N1a.raw-state.v1','phase':phase,'path_kind':'COLD_ORACLE' if cold else 'RESIDENT','cohort':'SCRIPTED_CONTROL' if control else 'NATURAL','execution_mode':('SCRIPTED_CONTROL_ORACLE' if cold else 'SCRIPTED_STATE_CONTROL') if control else ('CANONICAL_INPUT_ORACLE_REPLAY' if cold else 'FREE_SEQUENTIAL'),'generation_cap':1 if control else 128,'run_id':manifest['run_id'],'operation_id':op,'context_id':context,'identity':identity,'provenance':{'executable_sha256':FAKE,'capture_writer_sha256':FAKE},'canonical_ids':canonical,'materialized_ids':m,'logical_ids':m+g if terminal else m,'generated_ids':g if terminal else [],'head':h,'pending':{'id':g[-1],'position':h} if terminal else None,'frontier':{'valid':frontier,'owned':frontier,'position':h-1 if frontier else None},'requested_vector_positions':positions,'owned_vector_ids':[digest((op+'/owned/'+str(x)).encode()) for x in positions],'event_ordinal':ordinal}
  if terminal:s['stop_reason']='EOG' if g[-1] in EOG else 'CAP'
  return commit(op,phase,s,context)
 parser={'format_name':'peg-native','generation_prompt':'<|im_start|>assistant\n<think>\n\n</think>\n\n','additional_stops':[],'preserved_tokens':['<think>','</think>','<tool_call>','</tool_call>'],'parser_serialized':'{"CPU_SYNTHETIC_NOT_ACTUAL_PARSER":true}','profile':{'use_jinja':True,'enable_thinking':False,'reasoning_format':'deepseek','stream':False,'explicit_stop_strings':[],'tools':[],'add_generation_prompt':True,'parse_special':True,'add_special':False}};parser['generation_prompt_hex']=parser['generation_prompt'].encode().hex()
 jobs=[j for j in template['jobs'] if (j['role']==last_role if append else j['role'] in allowed)]
 for job in jobs:
  control=job['worker_id'].endswith('/CONTROL');cold=job['role']==ROLES[2];context='CPU_SYNTHETIC_CONTEXT_'+job['role']+'_'+('CONTROL' if control else 'NATURAL')
  for episode in job['episodes']:
   previous=None;prior_history=[]
   for turn,op in enumerate(episode['operations']):
    oid=op['id'];q=op['canonical_ids'] if control else op['expected_canonical_ids'] if not turn else previous[0]['canonical_ids']+previous[0]['generated_ids']+[42]
    generated=op['forced_terminal_ids'] if control else [151645];keep=0;mode=None;fallback=None
    if turn:
     old,old_d=previous;lcp=0
     while lcp<min(len(old['logical_ids']),len(q)) and old['logical_ids'][lcp]==q[lcp]:lcp+=1
     keep=min(lcp,old['head']);replay=keep==len(q);keep-=int(replay);mode='LAST_TOKEN_REPLAY' if replay else 'DIRECT_APPEND' if lcp==len(old['logical_ids']) and keep==old['head'] else 'LCP_TRIM_REPLAY'
     fault=op.get('caller_fault')
     if cold and control and ('trim_unsupported_rebuild' in oid or 'trim_pre_mutation_failure_rebuild' in oid):fault='UNSUPPORTED_BEFORE_CALL' if 'trim_unsupported_rebuild' in oid else 'FAILED_BEFORE_MUTATION'
     if fault:keep=0;mode='COMMON_FULL_REBUILD';fallback='TRIM_CAPABILITY_UNSUPPORTED' if fault=='UNSUPPORTED_BEFORE_CALL' else 'CALLER_INJECTED_TRIM_FAILURE_BEFORE_NATIVE_MUTATION'
     event={'schema':'hs.N1a.owned-vector-event.v1','phase':'BEFORE_NEXT_MUTATION','run_id':manifest['run_id'],'context_id':context,'source_operation_id':old['operation_id'],'next_operation_id':oid,'source_snapshot_sha256':old_d['sha256'],'source_requested_row_index':0,'source_vector_position':old['requested_vector_positions'][-1],'ownership_id':old['owned_vector_ids'][-1],'caller_owned':True,'capture_writer_sha256':FAKE,'event_ordinal':4}
     _,before=commit(old['operation_id']+'/'+oid,event['phase'],event,context,old['operation_id'])
    if not control and not cold:
     user=op['user'];wire='' if not turn else json.dumps({'choices':[{'message':{'role':'assistant','content':''},'finish_reason':'stop'}]},separators=(',',':'));history=[user] if not turn else prior_history+[{'role':'assistant','content':''},user]
     record(oid+'/PRODUCER',{'schema':'hs.N1chain.actual-producer.v1','operation_id':oid,'run_id':manifest['run_id'],'context_id':context,'role':job['role'],'mode':'ACTUAL_FREE_SEQUENTIAL_PRODUCER','identity':identity,'source_sha256':FAKE,'canonical_ids':q,'prompt_utf8':'CPU_SYNTHETIC_NOT_RENDERER_OUTPUT','history_json':json.dumps(history,ensure_ascii=False,separators=(',',':')),'runtime_parser_state_json':json.dumps(parser,separators=(',',':')),'wire_response_json':wire,'parser_input_hex':'','previous_actual_generated_ids':previous[0]['generated_ids'] if turn else [],'previous_stop_reason':previous[0]['stop_reason'] if turn else '','previous_cap':128 if turn else None,'next_user':user,'native_qualified':False});prior_history=history
    reconciled,rd=state(oid,'POST_RECONCILE',q,keep,context,control,6 if turn else 1);state(oid,'POST_APPEND',q,len(q),context,control,7 if turn else 2)
    if turn:
     pending='DISCARD_OLD_PENDING_WITH_RESET' if mode=='COMMON_FULL_REBUILD' else 'REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION' if lcp>old['head'] else 'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX'
     if not cold:record(oid+'/RECONCILE',{'schema':'hs.N1a.reconcile-receipt.v1','run_id':manifest['run_id'],'context_id':context,'source_operation_id':old['operation_id'],'operation_id':oid,'previous_snapshot_sha256':old_d['sha256'],'current_snapshot_sha256':rd['sha256'],'fallback_reason':fallback,'mode':mode,'actual_head_before':old['head'],'actual_keep':keep,'actual_model_rows_before_append':0,'old_frontier_invalidated':True,'old_pending_id':old['pending']['id'],'pending_disposition':pending})
     mutation=record(oid+'/MUTATION',{'schema':'hs.N1a.mutation-receipt.v1','run_id':manifest['run_id'],'context_id':context,'operation_id':oid,'source_operation_id':old['operation_id'],'begin_event_ordinal':5,'end_event_ordinal':8,'actual_decode_calls':1,'actual_model_rows':1,'status':'COMPLETE'})
     event=dict(event,phase='AFTER_NEXT_MUTATION',event_ordinal=9);_,after=commit(old['operation_id']+'/'+oid,event['phase'],event,context,oid)
     record(oid+'/OWNERSHIP_CHECK',{'schema':'hs.N1chain.owned-required-binding.v1','scope':'OWNED_VECTOR_STABILITY','origin':{'snapshot':old_d,'requested_row_index':0,'vector_position':old['requested_vector_positions'][-1],'ownership_id':old['owned_vector_ids'][-1],'next_operation_id':oid},'before_event':before,'after_event':after,'mutation_receipt':mutation})
    previous=state(oid,'TERMINAL',q,len(q),context,control,10 if turn else 3,generated)
   state(episode['operations'][-1]['id'],'RESET',[],0,context,control,11)
 return manifest

def build_synthetic_R(verifier,root):return build_synthetic_prefix(verifier,root,ROLES[0])
