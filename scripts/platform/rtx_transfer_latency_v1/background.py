"""File-backed sequential campaign execution, survives app/session changes."""
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
    logs=ROOT/'work/campaign';logs.mkdir(exist_ok=False)
    status=logs/'status.json'
    with (logs/'stdout.log').open('wb') as out,(logs/'stderr.log').open('wb') as err:
        status.write_text(json.dumps({'status':'RUNNING','started_utc':datetime.now(timezone.utc).isoformat()}))
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('study.py')),'campaign'],cwd=ROOT,
                              stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        status.write_text(json.dumps({'status':'EXECUTION_ENDED','process_returncode':result.returncode,
                                     'ended_utc':datetime.now(timezone.utc).isoformat()}))
    return result.returncode
if __name__=='__main__':raise SystemExit(main())
