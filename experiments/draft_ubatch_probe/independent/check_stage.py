#!/usr/bin/env python3
"""Independent whole-file inverse and byte-pin check; reads the study only."""
import argparse, pathlib, subprocess, json, hashlib, importlib.util, sys
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--study',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False);root=a.study.resolve()
spec=importlib.util.spec_from_file_location('reviewed_stage',root/'stage.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=(root/'frozen-worker.cpp').read_bytes();text=source.decode();rows=[]
for ub in (1,2,4):
 out=m.stage(text,ub);inverse=out
 for old,new in [
  (f'\nstatic constexpr int draft_ubatch={ub};',''),
  ('const fs::path&dir,int layout,int draft_physical=1):model(m)','const fs::path&dir,int layout):model(m)'),
  ('p.n_ubatch=istarget?ub:draft_physical;','p.n_ubatch=ub;'),
  ('dir/"draft",spec.selector,draft_ubatch);','dir/"draft",spec.selector);'),
  ('"rtx_draft_ubatch_probe_v1"','"rtx_scope_transfer_v1"'),
  ('{"draft_producer","NATIVE"},{"draft_ubatch",draft_ubatch}','{"draft_producer","NATIVE"}'),
  ('need(slot.at("draft_ubatch")==draft_ubatch,"draft ubatch slot mismatch");\n            need(plan.at("context").at("draft_ubatch")==draft_ubatch,"draft ubatch plan mismatch");\n            need(identity.at("draft_ubatch")==draft_ubatch,"draft ubatch binding mismatch");\n            ',''),
  ('    if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft ubatch differs");\n','')]:
  assert old in inverse,old;inverse=inverse.replace(old,new)
 assert inverse.encode()==source,'unexpected extra source edits'
 dest=a.output/f'ub{ub}';r=subprocess.run([sys.executable,str(root/'stage.py'),'--worker',str(root/'frozen-worker.cpp'),'--draft-ubatch',str(ub),'--output',str(dest)],capture_output=True,text=True);assert r.returncode==0,r.stderr
 receipt=json.loads((dest/'STAGE.json').read_text());assert receipt['output_sha256']==hashlib.sha256((dest/'worker.cpp').read_bytes()).hexdigest()
 rows.append({'ubatch':ub,'whole_file_inverse_equal':True,'actual_output_hash_matches':True,'worker_sha256':receipt['output_sha256']})
crlf=a.output/'crlf.cpp';crlf.write_bytes(source.replace(b'\n',b'\r\n'));dest=a.output/'must-not-exist'
r=subprocess.run([sys.executable,str(root/'stage.py'),'--worker',str(crlf),'--draft-ubatch','2','--output',str(dest)],capture_output=True,text=True)
assert r.returncode!=0 and not dest.exists(),'CRLF should be rejected before creating output'
for ub in (-1,0,3,8):
 try:m.stage(text,ub)
 except ValueError:pass
 else:raise AssertionError('invalid width accepted')
result={'status':'PASS','arms':rows,'crlf_raw_bytes_rejected':True,'unsupported_widths_rejected':[-1,0,3,8],'stage_sha256':hashlib.sha256((root/'stage.py').read_bytes()).hexdigest()}
(a.output/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
