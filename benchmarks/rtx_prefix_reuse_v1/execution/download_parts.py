"""Fetch release parts into a fresh directory, then authenticate every byte."""
from host import *
from concurrent.futures import ThreadPoolExecutor,as_completed
import parts

def main(name,out):
    out.mkdir(exist_ok=False)
    def download(filename):
        attempts=[]
        for attempt in range(3):
            started=time.monotonic()
            try:
                r=subprocess.run(['gh','release','download','rtx-prefix-reuse-v1-20261104','--repo','leecdiang/HeteroSpec','--pattern',filename,'--dir',str(out),'--clobber'],capture_output=True,text=True,timeout=600)
                record=dict(attempt=attempt,seconds=time.monotonic()-started,code=r.returncode,stderr=r.stderr)
            except subprocess.TimeoutExpired:
                record=dict(attempt=attempt,seconds=time.monotonic()-started,error='600s transfer timeout')
            attempts.append(record)
            if record.get('code')==0:break
        put(out/(filename+'.download.json'),attempts)
        assert attempts[-1].get('code')==0,filename
        print('downloaded',filename,flush=True)
    download(name+'.parts.json');manifest=read(out/(name+'.parts.json'))
    with ThreadPoolExecutor(max_workers=3) as pool:
        for f in as_completed([pool.submit(download,p['name']) for p in manifest['parts']]):f.result()
    parts.join(out/(name+'.parts.json'),out/name)
    if name.startswith('calibration'):
        import calibration_archive
        verification=calibration_archive.verify(out/name)
    else:
        import archive
        verification=archive.verify(out/name)
    put(ROOT/(name+'.RESTORED_DOWNLOAD.json'),dict(download_directory=str(out),source='GitHub release rtx-prefix-reuse-v1-20261104',sha256=sha(out/name),verification=verification,third_party_native_replication=False))
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]))
