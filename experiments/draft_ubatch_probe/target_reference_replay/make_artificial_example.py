#!/usr/bin/env python3
"""Generate a deliberately artificial offline byte-evidence demo, never model evidence."""
import argparse,json
from pathlib import Path
import test_replay_audit as T
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
plan,evidence=T.bundle(a.output,T.case(0,5))
for name,data in [('identity.json',T.ID),('trace.json',{'prompt_ids':plan['prompt_ids'],'case':plan['case']}),('evidence.json',evidence)]:
    (a.output/name).write_text(json.dumps(data,indent=2)+'\n')
