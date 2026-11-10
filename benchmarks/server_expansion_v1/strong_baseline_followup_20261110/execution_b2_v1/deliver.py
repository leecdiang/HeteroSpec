"""Complete B2 text export/replay, preserving private numeric inventories."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from execute import analyze,need,read,save,sha


def archive_module(source):
    sys.path.insert(0,str(source))
    spec=importlib.util.spec_from_file_location('_B2_archive',source/'archive.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def public(value,root):
    value=value.replace(str(root),'${HS_ROOT}').replace(str(Path.home()),'${HOST_HOME}')
    value=re.sub(r'GPU-[0-9a-fA-F-]{16,}','${ALLOCATED_GPU_UUID}',value)
    need(not re.search(r'(?<!\d)(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)',value),'Internal network literal in public text')
    return value


def export(work,root,source,out,archive_source):
    need(read(work/'STATE.json')['status']in ('B2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY','B2_PARTIAL_STOPPED'),'B2 is not terminal')
    need((work/'LOCK_RELEASED.private.json').is_file(),'Own lock has not closed')
    need(not out.exists(),'Fresh export directory required');out.mkdir(parents=True)
    files=[];numeric=[];private=[]
    for name,base in [('data',work),('source',source)]:
        for path in sorted(base.rglob('*')):
            if not path.is_file()or '__pycache__'in path.parts or path.is_symlink():continue
            relative=str(path.relative_to(base));logical=name+'/'+relative
            if path.suffix in ('.bin','.f32','.gguf'):
                numeric.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            # Foreign resource observations stay private; expose only their
            # hashes, event status and independently checked own host records.
            if relative.startswith(('RESOURCE_GUARD','GUARD_BASELINE','HARDWARE_DRIVER_BINDING')):
                private.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            try:text=path.read_text()
            except UnicodeDecodeError:
                private.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            target=out/logical;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(public(text,root))
    save(out/'PRIVATE_RESOURCE_TEXT_INVENTORY.json',private)
    for path in sorted(out.rglob('*')):
        if path.is_file():files.append(dict(path=str(path.relative_to(out)),sha256=sha(path),bytes=path.stat().st_size,
             payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    complete=read(work/'STATE.json')['status'].startswith('B2_COMPLETE')
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE'if complete else'PARTIAL',
                   files=files,withheld_numeric_payloads=numeric,private_literals=[str(root),str(Path.home())])
    save(out.parent/(out.name+'.selection.json'),selection)
    result=archive_module(archive_source).create(out,selection,out.parent/(out.name+'.tar.gz'))
    save(out.parent/(out.name+'.archive.json'),result);return result


def replay(archive,expected,out,archive_source):
    report=archive_module(archive_source).replay(archive,out,expected)
    status=read(out/'data/STATE.json')['status']
    if status.startswith('B2_COMPLETE'):
        plan=read(out/'data/PLAN.json');records=[]
        for worker in plan['workers']:
            record=read(out/'data/checked'/(worker['id']+'.json'))
            need(record['worker']==worker,'B2 exact ordered worker binding')
            job=read(out/'data'/worker['job'])
            need(len(record['operations'])==len(job['diagnostics'])==8,'Eight complete operations per worker')
            for item,operation in zip(job['diagnostics'],record['operations']):
                need(operation['item']==item,'Complete ordered native operation binding')
                native=read(out/'data/runs'/worker['id']/'native'/item['name']/'receipt.json')
                need(operation['receipt']==native,'Raw native receipt differs from checked record')
                need(operation['role']==('warm'if item['name'].startswith('warm-')else'measured'),'Native operation role')
                need(not native['capture'],'No heavy capture in B2 measured worker')
            records.append(record)
        actual=analyze(records,plan);need(actual==read(out/'data/RESULTS.json'),'B2 saved-data statistical replay differs')
        ledger=[json.loads(x)for x in (out/'data/ledger.jsonl').read_text().splitlines()]
        reservations=[x for x in ledger if x['event']=='RESERVE']
        need(len(reservations)==16 and sum(x['requests']for x in reservations)==128 and sum(x['rows']for x in reservations)==33024,'Complete B2 budget')
        need(sum(x['event']=='COMPLETE'for x in ledger)==16,'Every native process completed')
        report.update(statistical_replay='PASSED_COMPLETE_128_OPERATIONS',workers=16,warmups=64,measurements=64)
    else:report.update(statistical_replay='PARTIAL_NO_COMPLETE_PANEL_ESTIMATE')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('export')
    for name in ('work','root','source','out','archive-source'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('replay')
    for name in ('archive','out','archive-source','report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sha256',required=True);a=parser.parse_args()
    if a.mode=='export':print(json.dumps(export(a.work,a.root,a.source,a.out,a.archive_source)))
    else:
        result=replay(a.archive,a.sha256,a.out,a.archive_source);save(a.report,result);print(json.dumps(result))
