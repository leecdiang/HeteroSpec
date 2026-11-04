#!/usr/bin/env python3
import argparse,pathlib,json,subprocess,hashlib,sys
p=argparse.ArgumentParser();p.add_argument('--controller',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);existing=a.output/'existing';existing.mkdir();before=b'{"status":"RECORDED_EVIDENCE_MATCH","sentinel":"prior immutable success"}\n';(existing/'receipt.json').write_bytes(before)
results=[]
for name,dest in [('existing_output',existing),('fresh_preflight_failure',a.output/'fresh')]:
 cmd=[sys.executable,str(a.controller.resolve()),'--source','/nonexistent/source','--library-dir','/nonexistent/lib','--binary','/nonexistent/binary','--model','/nonexistent/model','--output',str(dest)];cp=subprocess.run(cmd,capture_output=True,text=True);(a.output/(name+'.stdout')).write_text(cp.stdout);(a.output/(name+'.stderr')).write_text(cp.stderr)
 rec={'case':name,'returncode':cp.returncode}
 if name=='existing_output':rec['prior_receipt_unchanged']=(dest/'receipt.json').read_bytes()==before;rec['after']=(dest/'receipt.json').read_text()
 else:
  rec['failed_receipt_exists']=(dest/'receipt.json').is_file();rec['failure_status']=json.loads((dest/'receipt.json').read_text()).get('status') if rec['failed_receipt_exists'] else None
 results.append(rec)
x={'controller_sha256':hashlib.sha256(a.controller.read_bytes()).hexdigest(),'results':results,'pass':results[0]['prior_receipt_unchanged'] and results[1]['failure_status']=='FAILED' and all(x['returncode']!=0 for x in results)};(a.output/'RESULT.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x,indent=2))

if not x["pass"]:raise SystemExit(1)
