#!/usr/bin/env python3
"""Reproduce published timing estimands from included public inputs (CPU only)."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',type=Path,default=ROOT/'build'/'statistics',
                help='New output directory; existing result files are not overwritten.')
args=ap.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
jobs=[('recompute_panels.py',ROOT/'data/closeout','panels.json'),
      ('recompute_transfer.py',ROOT/'data/closeout/pr203','transfer.json'),
      ('recompute_service.py',ROOT/'data/closeout/service','service.json')]
for script,data,out in jobs:
    target=args.out/out
    if target.exists():raise SystemExit(f'Refusing to overwrite existing result: {target.name}')
    p=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--data',str(data),'--out',str(target)],
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if p.returncode:
        print(p.stdout);raise SystemExit(p.returncode)
    result=json.loads(target.read_text())
    print(script+': '+result['status'])
print('All reconstruction stages passed; no model/native/GPU execution.')
