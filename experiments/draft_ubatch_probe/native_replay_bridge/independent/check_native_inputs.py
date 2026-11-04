#!/usr/bin/env python3
import argparse,json,pathlib,subprocess,copy,hashlib
p=argparse.ArgumentParser();p.add_argument('--binary',type=pathlib.Path,required=True);p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--expect-accepted',action='append',default=[]);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
base={'prompt_ids':list(range(1,8)),'cap':1,'forced_reject_index':-1,'draft_ubatch':2,'stop_after_output_index':0}
ref={'prompt_ids':list(range(1,8)),'jobs':[{'job_id':'j','tokens':list(range(1,8)),'queries':[{'query_id':'q','length':7,'state_required':True}]}]}
free={'prompt_ids':list(range(1,8)),'cap':1,'stop_after_output_index':0}
cases=[]
def add(name,mode,cfg):cases.append((name,mode,cfg))
for key,value in [('draft_ubatch',3),('draft_ubatch',2.0),('cap',True),('cap',0),('cap',10),('cap',1.0),('forced_reject_index',4),('forced_reject_index',-2),('forced_reject_index',18446744073709551615),('stop_after_output_index',2),('extra',1)]:
 c=copy.deepcopy(base);c[key]=value;add(key+'_'+str(value),'candidate',c)
for v in [[],[1]*6,[1]*8,[1]*6+[128],[1]*6+[-1],[1]*6+[True],[1]*6+[1.0]]:
 c=copy.deepcopy(base);c['prompt_ids']=v;add('prompt_'+str(len(cases)),'candidate',c)
for k,v in [('jobs',ref['jobs']),('endpoint',[1]),('forced_reject_index',-1),('cap',0)]:
 c=copy.deepcopy(free);c[k]=v;add('free_'+k,'free',c)
for name,change in [('duplicate_job',lambda c:c['jobs'].append(copy.deepcopy(c['jobs'][0]))),('duplicate_query',lambda c:c['jobs'][0]['queries'].append(copy.deepcopy(c['jobs'][0]['queries'][0]))),('length_below',lambda c:c['jobs'][0]['queries'][0].update(length=6)),('length_above',lambda c:c['jobs'][0]['queries'][0].update(length=8)),('length_float',lambda c:c['jobs'][0]['queries'][0].update(length=7.0)),('state_number',lambda c:c['jobs'][0]['queries'][0].update(state_required=1)),('empty_queries',lambda c:c['jobs'][0].update(queries=[])),('job_extra',lambda c:c['jobs'][0].update(extra=1)),('query_extra',lambda c:c['jobs'][0]['queries'][0].update(extra=1))]:
 c=copy.deepcopy(ref);change(c);add(name,'reference',c)
results=[]
for i,(name,mode,c) in enumerate(cases):
 d=a.output/str(i);d.mkdir();inp=d/'input.json';inp.write_text(json.dumps(c));cp=subprocess.run([str(a.binary.resolve()),mode,str(a.model.resolve()),str(inp),str(d/'capture')],capture_output=True,text=True);(d/'stdout').write_text(cp.stdout);(d/'stderr').write_text(cp.stderr);results.append({'case':name,'returncode':cp.returncode,'rejected':cp.returncode!=0,'output_created':(d/'capture').exists(),'stderr_tail':cp.stderr[-200:]})
x={'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'cases':results,'rejected':sum(x['rejected'] for x in results),'accepted_malformed':[x['case'] for x in results if not x['rejected']]};(a.output/'RESULT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x,indent=2))

if set(x["accepted_malformed"])!=set(a.expect_accepted):raise SystemExit(1)
