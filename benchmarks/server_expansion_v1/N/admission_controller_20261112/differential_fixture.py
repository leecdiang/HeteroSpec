"""Retained artificial raw-byte cases for Python/frozen-Node differential replay.

No model/tokenizer/runtime/native calls. These files are mock input, never a
complete qualification panel or actual producer output.
"""
import argparse,json,pathlib,struct
from stage_verify import RawChecker,digest
from test_stage_verify import Files,H

def export(out):
 out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=False);summary=[]
 def case(name,scope,make):
  root=out/name;root.mkdir();f=Files('runTest');f.root=root;f.r=RawChecker(root);c=make(f);c.update(id='CPU_SYNTHETIC_DIFFERENTIAL/'+name,scope=scope,bindings={})
  manifest={'schema':'hs.N1a.raw-comparisons.v1','comparisons':[c]};(root/'COMPARISONS.json').write_text(json.dumps(manifest,indent=2)+'\n');result=f.r.compare(c);(root/'PYTHON_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');summary.append({'case':name,'status':result['status'],'manifest':name+'/COMPARISONS.json'})
 def aligned(f,kind='equal'):
  a,ad=f.snapshot('a');b,bd=f.snapshot('b',op='control/REPEAT_RESIDENT_R/example/0')
  if kind in ('signed_zero','nonfinite'):
   targets=[a,b] if kind=='nonfinite' else [b]
   for s in targets:
    t=s['tensors']['vectors'];p=f.root/t['file'];raw=bytearray(p.read_bytes());raw[-4:]=struct.pack('<I',0x7f800000 if kind=='nonfinite' else 0x80000000);p.write_bytes(raw);t['sha256']=digest(raw)
   ad['sha256']=f.json('a.json',a)['sha256'];bd['sha256']=f.json('b.json',b)['sha256']
  if kind=='state':b['generated_ids']=[151643];b['logical_ids']=b['materialized_ids']+[151643];b['pending']['id']=151643;bd['sha256']=f.json('b.json',b)['sha256']
  if kind=='invalid_eog':b['stop_reason']='CAP';bd['sha256']=f.json('b.json',b)['sha256']
  return {'left':ad,'right':bd}
 for name,kind in [('aligned_equal','equal'),('signed_zero_last_vocab','signed_zero'),('equal_nonfinite_last_vocab','nonfinite'),('pending_state_difference','state'),('invalid_EOG_CAP_precedence','invalid_eog')]:case(name,'ALIGNED_STATE',lambda f,k=kind:aligned(f,k))
 def cold(f):
  a,ad=f.snapshot('resident',phase='POST_RECONCILE');b,bd=f.snapshot('cold',phase='POST_RECONCILE',op='control/COLD_CANONICAL_ORACLE/example/0');b.update(path_kind='COLD_ORACLE',execution_mode='SCRIPTED_CONTROL_ORACLE',frontier={'valid':True,'owned':True,'position':0},requested_vector_positions=[0],owned_vector_ids=['CPU-COLD-FRONTIER'])
  b['tensors']['vectors']=f.tensor('cold-frontier.bin','F32LE',[1,151936],['requested_row','vocabulary']);bd['sha256']=f.json('cold.json',b)['sha256'];return {'left':ad,'right':bd}
 case('cold_invalid_resident_frontier_exception','ALIGNED_STATE',cold)
 def retained(f,bad=False):
  a,ad=f.snapshot('previous',q=[3,4,5],event=1);b,bd=f.snapshot('next',phase='POST_RECONCILE',q=[3,9],head=1,op='control/RESIDENT_R/example/1',event=6)
  for kind in ('active_k','active_v'):
   old=bytearray((f.root/a['tensors'][kind]['file']).read_bytes());new=bytearray((f.root/b['tensors'][kind]['file']).read_bytes())
   for layer in range(36):
    for head in range(8):old[(layer*8+head)*3*256:(layer*8+head)*3*256+2]=b'\0\x3c';new[(layer*8+head)*256:(layer*8+head)*256+2]=b'\0\x3c'
   if bad and kind=='active_v':new[-2:]=b'\0\x3c'
   for s,raw in [(a,old),(b,new)]:t=s['tensors'][kind];(f.root/t['file']).write_bytes(raw);t['sha256']=digest(raw)
  ad['sha256']=f.json('previous.json',a)['sha256'];bd['sha256']=f.json('next.json',b)['sha256']
  rr={'schema':'hs.N1a.reconcile-receipt.v1','run_id':a['run_id'],'context_id':a['context_id'],'source_operation_id':a['operation_id'],'operation_id':b['operation_id'],'previous_snapshot_sha256':ad['sha256'],'current_snapshot_sha256':bd['sha256'],'fallback_reason':None,'mode':'LCP_TRIM_REPLAY','actual_head_before':3,'actual_keep':1,'actual_model_rows_before_append':0,'old_frontier_invalidated':True,'old_pending_id':151645,'pending_disposition':'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX'}
  return {'previous':ad,'current':bd,'transition_receipt':f.json('RECONCILE.json',rr)}
 case('retained_old_head_stride_equal','PREFIX_RETENTION',retained);case('retained_last_layer_V_difference','PREFIX_RETENTION',lambda f:retained(f,True))
 def owned(f,bad=False):
  s,sd=f.snapshot('source');nextop='control/RESIDENT_R/example/1';origin={'snapshot':sd,'requested_row_index':0,'vector_position':0,'ownership_id':s['owned_vector_ids'][0],'next_operation_id':nextop};events=[]
  for name,phase,ordinal in [('before','BEFORE_NEXT_MUTATION',2),('after','AFTER_NEXT_MUTATION',5)]:
   data=bytearray(151936*4)
   if bad:data[-4:]=struct.pack('<f',1)
   t=f.tensor(name+'.bin','F32LE',[1,151936],['requested_row','vocabulary'],data);e={'schema':'hs.N1a.owned-vector-event.v1','phase':phase,'run_id':s['run_id'],'context_id':s['context_id'],'source_operation_id':s['operation_id'],'next_operation_id':nextop,'source_snapshot_sha256':sd['sha256'],'source_requested_row_index':0,'source_vector_position':0,'ownership_id':origin['ownership_id'],'caller_owned':True,'capture_writer_sha256':H,'event_ordinal':ordinal,'tensor':t};events.append(f.json(name+'.json',e))
  m={'schema':'hs.N1a.mutation-receipt.v1','run_id':s['run_id'],'context_id':s['context_id'],'operation_id':nextop,'source_operation_id':s['operation_id'],'begin_event_ordinal':3,'end_event_ordinal':4,'actual_decode_calls':1,'actual_model_rows':1,'status':'COMPLETE'};return {'origin':origin,'before_event':events[0],'after_event':events[1],'mutation_receipt':f.json('MUTATION.json',m)}
 case('owned_source_and_before_after_equal','OWNED_VECTOR_STABILITY',owned);case('owned_equal_copies_differ_from_source','OWNED_VECTOR_STABILITY',lambda f:owned(f,True))
 def reset(f,bad=False):
  s,d=f.snapshot('reset',phase='RESET')
  if bad:(f.root/s['tensors']['active_k']['file']).write_bytes(b'\0\0')
  return {'capture':d}
 case('reset_empty_files','RESET_EMPTY_CHECK',reset);case('reset_nonempty_raw_rejected','RESET_EMPTY_CHECK',lambda f:reset(f,True))
 result={'schema':'hs.N1controller.synthetic-differential-inputs.v1','scope':'ARTIFICIAL_PROVIDED_BYTES_NOT_NATIVE_EVIDENCE','cases':summary,'model_forwards':0,'native_ELF':0};(out/'INDEX.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(export(a.out)))
