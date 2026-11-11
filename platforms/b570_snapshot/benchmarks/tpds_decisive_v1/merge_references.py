"""Merge independent scalar path captures; reject unstable shared prefixes."""
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
from common import *

def merge(paths:list[Path],out:Path):
    need(paths and not out.exists(),'fresh nonempty reference bank')
    data=[read(p) for p in paths];base=data[0]['binding'];out.mkdir(parents=True)
    prefixes={};pids=set()
    def store(root,spec):
        p=check_blob(root,spec);raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();dest=out/'cas'/h[:2]/h
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(raw)
        else:need(dest.read_bytes()==raw,'content-address collision')
        return {'path':dest.relative_to(out).as_posix(),'bytes':len(raw),'sha256':h}
    for path,obj in zip(paths,data):
        need(obj['role']=='forced_reference_path' and obj['execution']=='NATIVE' and obj['completed'] is True,'not independent native reference capture')
        need(obj['binding']==base and obj['reference_bridge_passed'] is True and obj['fallback_count']==0,'reference family drift')
        need(obj['invocation_id'] not in pids,'duplicate reference process record');pids.add(obj['invocation_id'])
        for x in obj['prefixes']:
            key=digest(x['prefix']);entry={'prefix':x['prefix'],'active_layout_sha256':hexsha(x['active_layout_sha256']),
                'frontier':store(path.parent,x['frontier']),'active_kv':store(path.parent,x['active_kv'])}
            if key in prefixes:need(prefixes[key]==entry,'scalar reference differs at a shared prefix across independent histories')
            else:prefixes[key]=entry
    result={'role':'forced_reference','execution':'NATIVE','completed':True,'binding':base,'reference_bridge_passed':True,
       'fallback_count':0,'invocation_id':digest(sorted(pids)),'source_invocations':sorted(pids),
       'prefixes':[prefixes[k] for k in sorted(prefixes)],'origin':'host captures, not independently attested by this merger'}
    write_new(out/'capture.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();merge(a.inputs,a.out)
