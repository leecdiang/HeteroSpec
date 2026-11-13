from pathlib import Path
import json,subprocess,sys,time
import argparse
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r=a.root;w=a.work;src=Path(__file__).parent
def run(label,args):
 with(w/(label+'.stdout.log')).open('xb')as so,(w/(label+'.stderr.log')).open('xb')as se:
  p=subprocess.run([sys.executable,'-B',*args],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
 (w/(label+'.TERMINAL.json')).write_text(json.dumps(dict(returncode=p.returncode,epoch=time.time(),native_requests_started=0))+'\n')
 return p.returncode
if run('archive-13',[str(src/'archive.py'),'--root',str(r),'--work',str(w)])==0:
 run('delivery-03',[str(src/'delivery_audit.py'),'--root',str(r),'--work',str(w),'--epoch','09','--qualification-epoch','08','--closure-epoch','09','--request-ceiling','640','--export',str(w/'export-13'),'--out',str(w/'delivery-03')])
