"""Detached data-only audit after terminal export; no native/GPU admission."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--epoch',choices=['07','08','09'],required=True);p.add_argument('--qualification-epoch');p.add_argument('--closure-epoch');p.add_argument('--request-ceiling',type=int,choices=[512,640],default=512);p.add_argument('--export',required=True);p.add_argument('--out',required=True);a=p.parse_args();w=a.work;export=w/a.export
 def save(name,x):(w/name).write_text(json.dumps(x,indent=2)+'\n')
 while not(export/'EXPORT_COMPLETE.json').exists():
  launched=w/f'PIPELINE_LAUNCH_{a.epoch}.private.json'
  if launched.exists():
   processes=json.loads(launched.read_text())['processes'];arc=processes['archive-'+a.epoch];proc=Path(f"/proc/{arc['pid']}");alive=False
   if proc.exists():
    try:
     text=(proc/'stat').read_text();fields=text[text.rfind(')')+2:].split();alive=fields[0]!='Z'and fields[19]==arc['start_ticks']
    except FileNotFoundError:pass
   if not alive:
    save('DELIVERY_AUDIT_NOT_STARTED-'+a.epoch+'.json',dict(epoch=time.time(),reason='Terminal exporter exited without complete artifact; preserve its stderr and partial export; zero native requests started',export=a.export));return
  if time.time()>1794268200:
   save('DELIVERY_AUDIT_NOT_STARTED-'+a.epoch+'.json',dict(epoch=time.time(),reason='Data-only delivery boundary exceeded',zero_native_requests=True));return
  time.sleep(5)
 with(w/('delivery-'+a.epoch+'.stdout.log')).open('xb')as so,(w/('delivery-'+a.epoch+'.stderr.log')).open('xb')as se:
  extra=['--request-ceiling',str(a.request_ceiling)]+(['--qualification-epoch',a.qualification_epoch]if a.qualification_epoch else[])+(['--closure-epoch',a.closure_epoch]if a.closure_epoch else[])
  result=subprocess.run([sys.executable,'-B',str(Path(__file__).parent/'delivery_audit.py'),'--root',str(a.root),'--work',str(w),'--epoch',a.epoch,'--export',str(export),'--out',str(w/a.out),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
 save('DELIVERY_AUDIT_TERMINAL-'+a.epoch+'.json',dict(epoch=time.time(),returncode=result.returncode,out=a.out,zero_native_requests=True,public_upload_and_remote_readback='Pending connected publication'))
if __name__=='__main__':main()
