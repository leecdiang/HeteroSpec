"""CPU-only payloads for stage seal, complete coordinates, archive and restore."""
import argparse,json,zipfile
from pathlib import Path
from common import V,load,save,sha
import audit,identity
import archive
def analyze(root,frozen=V):
    f=load(Path(frozen)/'F0.json');p=load(Path(frozen)/'PLAN.json');expected={(r['descriptor_id'],r['layout']):r for r in load(Path(frozen)/'CPU_EXPECTED.json')};rows=[];qualified=[];failure=None
    identity.V=Path(frozen)
    for slot in p['clean_slots']+p['trace_slots']:
        d=Path(root)/slot['kind']/f'{slot["index"]:03d}';state='NOT_ADMITTED_PROFILE_UNAVAILABLE' if slot['kind']=='trace' else 'NOT_STARTED_PROTOCOL_STOP' if list(Path(root).glob('*_MINIMUM_STOP.json')) else 'NOT_STARTED_NOT_AUTHORIZED'
        if (d/'BEFORE_START.json').exists():
            if not (d/'COMPLETED.json').exists():
                state='STARTED_FAILED_OR_INCOMPLETE' if (d/'native.PROCESS.json').exists() else 'NATIVE_START_UNCONFIRMED';failure=failure or state
            elif failure:state='STARTED_AFTER_CONTROL_FAILURE_INVALID'
            else:
                try:r=audit.inspect(slot,d,f,p,expected[slot['descriptor'],slot['layout']],Path(root));qualified.append(r);state='COMPLETED_QUALIFIED'
                except Exception as exc:failure=repr(exc);state='CONTROL_FAILED'
        elif (d/'FAILED.json').exists():state='RESERVED_FAILED_BEFORE_NATIVE';failure=failure or state
        rows.append(dict(id=slot['id'],descriptor=slot['descriptor'],family=slot['family'],phase=slot['phase'],q=slot['q'],layout=slot['layout'],block=slot['block'],status=state))
    clean=[r for r in qualified if r['block'] is not None]
    return dict(run_id=p['run_id'],slots=rows,hosts=qualified,control_failure=failure,clean_statistics=audit.aggregate(clean,p),trace_status='PROFILE_UNAVAILABLE',original_S1B_complete=False,hardware_causality='UNKNOWN')
def main():
    p=argparse.ArgumentParser();p.add_argument('--action',required=True);p.add_argument('--root',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--frozen',type=Path,default=V);p.add_argument('--archive',type=Path);a=p.parse_args();f=load(a.frozen/'F0.json')
    if a.action=='analyze':save(a.out,analyze(a.root,a.frozen))
    elif a.action=='package':archive.package(a.root,a.out,a.frozen)
    elif a.action=='restore':save(a.out.parent/'RESTORE.json',archive.restore(a.archive,load(a.archive/'ARCHIVE.json'),a.out,f['budget']['limits']['raw_bytes']+32*1024**2))
    elif a.action=='seal-census':
        assert load(a.root/'CENSUS_ENDED.json')['status']=='COMPLETE';n=a.root/'census/native';r=load(n/'CENSUS.json');host=f['hosts']['clean'];identity.process_identity(a.root/'census','native',dict(f,executable=host['path']),240);identity.process_identity(a.root/'census','readiness',f);identity.verify_modules(n,r,dict(f,executable=host['path'],executable_sha256=host['sha256']),load(a.root/'census/MODULE_FILES.json'))
        expected={(r['descriptor_id'],r['layout']):r for r in load(a.frozen/'CPU_EXPECTED.json')};decision=audit.census(r,load(a.frozen/'PLAN.json'),expected);assert decision==load(a.root/'CENSUS_DECISION.json');a.out.mkdir(exist_ok=False)
        save(a.out/'CENSUS.json',r);save(a.out/'DECISION.json',decision)
        with zipfile.ZipFile(a.out/'RECEIPTS.zip','x',zipfile.ZIP_DEFLATED) as z:
            for file in a.root.rglob('*'):
                if file.is_file() and 'cas' not in file.relative_to(a.root).parts:z.write(file,file.relative_to(a.root).as_posix())
        save(a.out/'MANIFEST.json',dict(F0_sha256=sha(a.frozen/'F0.json'),census_sha256=sha(a.out/'CENSUS.json'),decision_sha256=sha(a.out/'DECISION.json')))
    else:raise AssertionError('unsupported CPU payload')
if __name__=='__main__':main()
