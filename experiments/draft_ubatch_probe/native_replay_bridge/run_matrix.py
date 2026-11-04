#!/usr/bin/env python3
"""Sequential small CPU matrix; every subprocess attempt and payload retained."""
import argparse,pathlib,subprocess,json,time,sys
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--library-dir',required=True);p.add_argument('--binary',required=True);p.add_argument('--models',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
cases=[('initial',1,0,0,1),('reject0',5,0,0,2),('reject1',5,1,0,4),('reject2',5,2,0,2),('bonus',5,3,0,4),('accepted',4,3,0,2),('synthetic-stop',9,3,3,1),('native-draft',5,-1,0,4)]
records=[]
for model in ['q8','dense']:
 for name,cap,reject,stop,ub in cases:
  dest=a.output/(model+'-'+name);cmd=[sys.executable,str(R/'run_bridge.py'),'--source',a.source,'--library-dir',a.library_dir,'--binary',a.binary,'--model',str(a.models/(model+'.gguf')),'--output',str(dest),'--cap',str(cap),'--reject',str(reject),'--stop',str(stop),'--draft-ubatch',str(ub)];t=time.monotonic()
  with (a.output/(dest.name+'.log')).open('w') as f:cp=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  rec={'name':dest.name,'returncode':cp.returncode,'wall_seconds':time.monotonic()-t,'command':cmd};records.append(rec);(a.output/'MATRIX.json').write_text(json.dumps(records,indent=2))
  if cp.returncode:sys.exit(cp.returncode)
print(json.dumps({'cases':len(records),'status':'PASS','gpu_qualification_established':False}))
