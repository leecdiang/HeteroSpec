"""Replace only this study's idle zero-GPU archive waiter, never a native task."""
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();w=a.work
 while not(w/'PIPELINE_LAUNCH_05.private.json').exists():time.sleep(2)
 x=read(w/'PIPELINE_LAUNCH_05.private.json')['processes']['archive-05'];p=Path(f"/proc/{x['pid']}");raw=(p/'stat').read_text();assert raw[raw.rfind(')')+2:].split()[19]==x['start_ticks'];assert b'q32-q4-full-source-07/archive.py'in(p/'cmdline').read_bytes();assert not(w/'export-06').exists(),'Do not interrupt an active archive'
 os.kill(x['pid'],signal.SIGTERM)
 with(w/'archive-final.stdout.log').open('xb')as so,(w/'archive-final.stderr.log').open('xb')as se:child=subprocess.Popen(['taskset','-c','34,35','nice','-n','10',sys.executable,'-B',str(Path(__file__).parent/'archive.py'),'--root',str(a.root),'--work',str(w)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
 raw=Path(f'/proc/{child.pid}/stat').read_text();save(w/'FINAL_ARCHIVE_LAUNCH.private.json',dict(pid=child.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],epoch=time.time(),source_sha256=sha(Path(__file__).parent/'archive.py'),retired_idle_own_archive=x['pid'],native_tasks_signalled=False,scope='Zero-GPU privacy-only successor waits for all native controllers and observer closure; original source/export directories preserved'))
 print('Q32_FINAL_ARCHIVE_WAITER_INSTALLED',child.pid,flush=True)
if __name__=='__main__':main()
