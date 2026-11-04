#!/usr/bin/env python3
"""Create two deliberately invalid native fixtures without changing the source."""
import argparse, pathlib, json, hashlib
p=argparse.ArgumentParser();p.add_argument('--fixture',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
s=a.fixture.read_bytes().decode('utf-8');a.output.mkdir(parents=True,exist_ok=False)
patterns={
 'early_stop':('done=int(output.size())==cap||int(output.size())==stop_index;','done=true; /* deliberately invalid early stop */'),
 'discard_committed_state':(' Ctx state_oracle(m,1);',' target.trim(prompt.size());history=prompt;base=int(prompt.size()); /* deliberately invalid committed-state loss, after frontier checks */\n Ctx state_oracle(m,1);')}
manifest={'fixture_sha256':hashlib.sha256(s.encode()).hexdigest(),'mutants':{}}
for name,(old,new) in patterns.items():
 if s.count(old)!=1:raise ValueError('unexpected fixture anchor: '+name)
 b=s.replace(old,new).encode();(a.output/(name+'.cpp')).write_bytes(b);manifest['mutants'][name]=hashlib.sha256(b).hexdigest()
(a.output/'MUTANTS.json').write_text(json.dumps(manifest,indent=2)+'\n')
