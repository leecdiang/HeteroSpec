import sys,pathlib,tempfile,copy,json,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import replay_audit as A, test_replay_audit as T
root=pathlib.Path(tempfile.mkdtemp(prefix='audit-adversarial-'))
p,e=T.bundle(root,T.case(0,5));results={}
# Exact accounting of successful payload reads, including duplicate observations.
real=A.blob;seen=[]
def counted(*args):
 b=real(*args);seen.append(len(b));return b
A.blob=counted
r=A.audit(p,e,root,T.ID);A.blob=real
results['byte_accounting']={'reported':r['payload_bytes_read'],'actually_read':sum(seen),'missed':sum(seen)-r['payload_bytes_read'],'calls':len(seen)}
for name,mutate in [
 ('job_observation_wrong_prefix',lambda x:next(iter(next(iter(x['reference_jobs'].values()))['observations'].values())).__setitem__('decoded_tokens',[15])),
 ('job_observation_not_fresh',lambda x:next(iter(next(iter(x['reference_jobs'].values()))['observations'].values())).__setitem__('fresh_context',False)),
 ('job_observation_wrong_positions',lambda x:next(iter(next(iter(x['reference_jobs'].values()))['observations'].values())).__setitem__('positions',[99])),
 ('job_observation_wrong_caller',lambda x:next(iter(next(iter(x['reference_jobs'].values()))['observations'].values())).__setitem__('caller_widths',[64])),
 ('job_observation_wrong_sequence',lambda x:next(iter(next(iter(x['reference_jobs'].values()))['observations'].values())).__setitem__('sequence_id',9)),
 ('reference_all_outputs_disabled',lambda x:[v.__setitem__('logits_masks',[[False]*w for w in v['caller_widths']]) for v in x['reference_queries'].values()]),
 ('candidate_all_outputs_disabled',lambda x:[v.__setitem__('logits_masks',[[False]*4]) for v in x['candidate_rows'].values()]),
]:
 z=copy.deepcopy(e);mutate(z)
 try:results[name]={'accepted':True,'status':A.audit(p,z,root,T.ID)['status']}
 except Exception as ex:results[name]={'accepted':False,'error':str(ex)}
c=T.case();c['cap']=float(c['cap']);c['target_ubatch']=True
try: A.make_plan(c,[1,2,3],T.ID);results['float_cap_bool_ubatch']={'accepted':True}
except Exception as ex:results['float_cap_bool_ubatch']={'accepted':False,'error':str(ex)}
results['auditor_sha256']=hashlib.sha256(pathlib.Path(A.__file__).read_bytes()).hexdigest()
print(json.dumps(results,indent=2))
