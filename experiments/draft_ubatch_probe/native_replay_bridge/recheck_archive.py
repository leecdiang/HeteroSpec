#!/usr/bin/env python3
"""Re-audit every extracted case without rerunning native code."""
import argparse,pathlib,json,sys
R=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(R/'offline'));import replay_audit as A
p=argparse.ArgumentParser();p.add_argument('--matrix',type=pathlib.Path,required=True);a=p.parse_args();n=0
for f in sorted(a.matrix.glob('*/plan.json')):
 d=f.parent;load=lambda name:json.loads((d/name).read_text());r=A.audit(load('plan.json'),load('evidence.json'),d/'bundle',load('identity.json'));A.need(r==load('audit.json'),'audit report differs');n+=1
A.need(n==16,'incomplete 16-case archive');print(json.dumps({'offline_cases_rechecked':n,'gpu_qualification_established':False}))
