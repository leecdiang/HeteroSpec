#!/usr/bin/env python3
"""Run the frozen formal v2 pipeline with durable file-backed output."""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--asset-root',type=Path,default=Path('D:/HeteroSpec-PC'))
    args=parser.parse_args()
    log_dir=args.output.parent/'rtx-v2-background'
    log_dir.mkdir(parents=True,exist_ok=True)
    status_path=log_dir/'status.json'
    def status(state,stage,code=None):
        value={'status':state,'stage':stage,'process_returncode':code,'updated_utc':datetime.now(timezone.utc).isoformat(),'formal_output':str(args.output)}
        temporary=status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
        temporary.replace(status_path)
    with (log_dir/'stdout.log').open('w',encoding='utf-8',buffering=1) as stdout, (log_dir/'stderr.log').open('w',encoding='utf-8',buffering=1) as stderr:
        commands=[
            ('formal_execution',[sys.executable,str(ROOT/'scripts/rtx_direct_id_v2.py'),'run','--output',str(args.output)]),
            ('formal_analysis',[sys.executable,str(ROOT/'scripts/rtx_direct_id_v2.py'),'analyze','--output',str(args.output)]),
            ('independent_validation',[sys.executable,str(ROOT/'scripts/verify_rtx_direct_id_v2.py'),str(args.output),'--asset-root',str(args.asset_root),'--output',str(args.output/'independent_validation.json')]),
        ]
        for stage,command in commands:
            status('RUNNING',stage)
            result=subprocess.run(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
            if result.returncode:
                status('STOPPED_FAILURE',stage,result.returncode)
                return result.returncode
        status('COMPLETE','independent_validation',0)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
