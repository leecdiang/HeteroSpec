from pathlib import Path
import argparse,subprocess,sys,json,time
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
def run(label,argv):
 with(w/(label+'.stdout.log')).open('xb')as so,(w/(label+'.stderr.log')).open('xb')as se:x=subprocess.run([sys.executable,'-B',*argv],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
 (w/(label+'.TERMINAL.json')).write_text(json.dumps(dict(returncode=x.returncode,epoch=time.time(),native_requests_started=0))+'\n');return x.returncode
if run('delivery-04',[str(src/'delivery_audit.py'),'--root',str(r),'--work',str(w),'--epoch','09','--qualification-epoch','08','--closure-epoch','09','--request-ceiling','640','--export',str(w/'export-13'),'--out',str(w/'delivery-04')])==0:
 run('public-stage02',[str(src/'stage_public.py'),'--work',str(w),'--out',str(r/'q32-delivery-public-stage-02')])
