#!/usr/bin/env python3
"""Compare maximal-path captures with one independently spawned fresh R per query."""
import argparse,sys,pathlib,hashlib,json,subprocess,importlib.util,os
p=argparse.ArgumentParser();p.add_argument('--parser',type=pathlib.Path,required=True);p.add_argument('--binary',type=pathlib.Path,required=True);p.add_argument('--run',type=pathlib.Path,required=True);p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
s=importlib.util.spec_from_file_location('state',a.parser);P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
plan=json.loads((a.run/'plan.json').read_text());ev=json.loads((a.run/'evidence.json').read_text());records=[]
for i,q in enumerate(plan['queries']):
 cfg={'prompt_ids':plan['prompt_ids'],'jobs':[{'job_id':q['query_id'],'tokens':q['tokens'],'queries':[{'query_id':q['query_id'],'length':len(q['tokens']),'state_required':q['state_required']}]}]};dest=a.output/str(i);dest.mkdir();inp=dest/'input.json';inp.write_text(json.dumps(cfg,indent=2)+'\n');env=os.environ.copy()
 for k in list(env):
  if k.startswith(('HS_','GGML_','LLAMA_')) or k in ('LD_PRELOAD','LD_LIBRARY_PATH'):env.pop(k)
 cp=subprocess.run([str(a.binary.resolve()),'reference',str(a.model.resolve()),str(inp),str(dest/'capture')],env=env,capture_output=True,text=True);(dest/'stdout').write_text(cp.stdout);(dest/'stderr').write_text(cp.stderr)
 if cp.returncode:raise RuntimeError('fresh native query failed '+str(i))
 cap=json.loads((dest/'capture'/'capture.json').read_text());ob=cap['jobs'][q['query_id']]['observations'][q['query_id']];old=ev['reference_queries'][q['query_id']];blob=lambda ref:(a.run/'bundle'/ref['path']).read_bytes();new=lambda ref:(dest/'capture'/ref['path']).read_bytes();v_match=new(ob['logits'])==blob(old['logits']);kv_match=None
 if q['state_required']:canonical,_=P.parse(new(ob['serialized_sequence']),q['tokens']);kv_match=canonical==blob(old['kv'])
 widths=[len(plan['prompt_ids'])]+[1]*(len(q['tokens'])-len(plan['prompt_ids']));calls=cap['execution'];decoded=[]
 for e in calls:
  if e['base']!=len(decoded) or e['caller_width']!=len(e['tokens']) or e['physical_ubatch_capacity']!=1:raise RuntimeError('actual call mismatch')
  if e['logits_mask']!=[False]*(len(e['tokens'])-1)+[True]:raise RuntimeError('mask mismatch')
  decoded+=e['tokens']
 if decoded!=q['tokens'] or [x['caller_width'] for x in calls]!=widths:raise RuntimeError('prefix recipe mismatch')
 records.append({'query_id':q['query_id'],'prefix_length':len(q['tokens']),'pid':cap['pid'],'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest(),'vector_equal':v_match,'state_required':q['state_required'],'active_kv_equal':kv_match})
 if not v_match or kv_match is False:raise RuntimeError('fresh per-query differs')
x={'scope':'Real CPU captures, maximal-path observations versus separate-process fresh context for every query; not all-value or historical resident-R proof','binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'source_evidence_sha256':hashlib.sha256((a.run/'evidence.json').read_bytes()).hexdigest(),'queries':len(records),'state_queries':sum(x['state_required'] for x in records),'fresh_processes':len(set(x['pid'] for x in records)),'results':records,'status':'MATCH'};(a.output/'RESULT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items() if k!='results'},indent=2))
