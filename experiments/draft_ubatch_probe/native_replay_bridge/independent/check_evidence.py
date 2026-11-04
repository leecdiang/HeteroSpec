#!/usr/bin/env python3
"""Mutate real native evidence only. Never runs inference or modifies input files."""
import argparse,pathlib,json,hashlib,importlib.util,copy,sys
p=argparse.ArgumentParser();p.add_argument('--auditor',type=pathlib.Path,required=True);p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
s=importlib.util.spec_from_file_location('audit',a.auditor);A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
load=lambda n:json.loads((a.run/n).read_text());plan=load('plan.json');identity=load('identity.json');baseline=load('evidence.json');root=a.output/'bundle';root.mkdir()
for f in (a.run/'bundle').iterdir(): (root/f.name).write_bytes(f.read_bytes())
base=A.audit(plan,baseline,root,identity);cases=[]
firstrow=next(iter(baseline['candidate_rows']));tailrow=list(baseline['candidate_rows'])[-1];firstcommit=next(iter(baseline['candidate_commits']));lastcommit=list(baseline['candidate_commits'])[-1];firstjob=next(iter(baseline['reference_jobs']));firstq=next(iter(baseline['reference_queries']))
def payload(ref,op):
 b=op(bytearray((root/ref['path']).read_bytes()));h=hashlib.sha256(b).hexdigest();(root/(h+'.bin')).write_bytes(b);return {'path':h+'.bin','bytes':len(b),'sha256':h}
def flip(b): b[0]^=1;return b
def swap_halves(b):return b[512:1024]+b[:512]+b[1024:]
def swap_endian(b):return b''.join(b[i:i+2][::-1] for i in range(0,len(b),2))
def add(name,fn):cases.append((name,fn))
def replace(e,where,key,fn):where[key]=payload(where[key],fn)
for name,field,key,op in [('candidate_KV_bit',firstcommit,'kv',flip),('candidate_KV_KVswap',firstcommit,'kv',swap_halves),('candidate_KV_endian',firstcommit,'kv',swap_endian),('candidate_KV_missing_token',firstcommit,'kv',lambda b:b[:-2048]),('frontier_bit',lastcommit,'frontier_logits',flip)]:
 add(name,lambda e,field=field,key=key,op=op:replace(e,e['candidate_commits'][field],key,op))
add('initial_vector_bit',lambda e:replace(e,e['candidate_rows'][firstrow],'logits',flip));add('rejected_tail_vector_bit',lambda e:replace(e,e['candidate_rows'][tailrow],'logits',flip))
add('free_vector_bit',lambda e:e['free_scalar_run']['logits'].__setitem__(-1,payload(e['free_scalar_run']['logits'][-1],flip)))
add('reference_vector_bit',lambda e:replace(e,e['reference_queries'][firstq],'logits',flip))
add('pending_wrong',lambda e:e['candidate_commits'][firstcommit].update(pending_for_next_loop=127))
add('unmaterialized_missing',lambda e:e['candidate_commits'][firstcommit].update(unmaterialized_output=[]))
add('frontier_wrong_use',lambda e:e['candidate_commits'][lastcommit].update(frontier_logits_use=firstrow))
add('position_shift',lambda e:e['candidate_commits'][firstcommit]['positions'].__setitem__(0,1))
add('next_position_float',lambda e:e['candidate_commits'][firstcommit].update(next_position=float(e['candidate_commits'][firstcommit]['next_position'])))
add('candidate_mask_wrong',lambda e:e['candidate_rows'][firstrow]['producer']['logits_mask'].__setitem__(0,True))
add('candidate_row_wrong',lambda e:e['candidate_rows'][tailrow]['producer'].update(captured_batch_row=0))
add('candidate_scalar_schedule_wrong',lambda e:e['candidate_rows'][firstrow]['producer'].update(physical_ubatches=[7]))
add('reference_mask_wrong',lambda e:e['reference_jobs'][firstjob]['execution']['logits_masks'][0].__setitem__(0,True))
add('reference_start_dirty',lambda e:e['reference_jobs'][firstjob].update(start_empty=False))
add('missing_reference_job',lambda e:e['reference_jobs'].pop(firstjob))
add('missing_query',lambda e:e['reference_queries'].pop(firstq))
add('missing_rejected_tail',lambda e:e['candidate_rows'].pop(tailrow))
add('free_forced',lambda e:e['free_scalar_run'].update(forced_tokens_used=True))
add('free_endpoint_wrong',lambda e:e['free_scalar_run']['output'].__setitem__(-1,(e['free_scalar_run']['output'][-1]+1)%128))
add('free_caller_recipe_wrong',lambda e:e['free_scalar_run'].update(caller_widths=[1]*len(e['free_scalar_run']['decoded_tokens'])))
results=[]
for name,fn in cases:
 e=copy.deepcopy(baseline);fn(e)
 try:A.audit(plan,e,root,identity);result={'name':name,'rejected':False}
 except A.EvidenceError as ex:result={'name':name,'rejected':True,'reason':str(ex)}
 results.append(result)
x={'auditor_sha256':hashlib.sha256(a.auditor.read_bytes()).hexdigest(),'baseline_report':base,'evidence_sha256':hashlib.sha256((a.run/'evidence.json').read_bytes()).hexdigest(),'cases':results,'rejected':sum(x['rejected'] for x in results),'accepted_mutants':[x['name'] for x in results if not x['rejected']]};(a.output/'RESULT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x,indent=2))

if x["accepted_mutants"]:raise SystemExit(1)
