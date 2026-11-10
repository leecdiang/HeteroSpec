"""Complete terminal S3 text/numeric inventories and saved-data replay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent/'execution_v1'))
from support import need,read,sha,fresh
from public_text import transform
import archive
from analyze import analyze
from ledger import canonical


def journal(path,prefix_path,approval,inheritance):
    prefix=Path(prefix_path).read_bytes();raw=Path(path).read_bytes()
    need(raw.startswith(prefix)and hashlib.sha256(prefix).hexdigest()==approval['predecessor_prefix_sha256'],'Original global journal prefix')
    old_count=len(prefix.splitlines());prior=hashlib.sha256(canonical(approval['predecessor_approval'])).hexdigest()
    current=hashlib.sha256(canonical(approval)).hexdigest();parent='0'*64;operations={};requests=inheritance['requests'];rows=inheritance['reserved_rows'];phase=0
    for ordinal,line in enumerate(raw.splitlines()):
        value=json.loads(line);digest=value.pop('event_sha256')
        need(value['parent_sha256']==parent and hashlib.sha256(canonical(value)).hexdigest()==digest,'Complete public journal hash chain')
        parent=digest;need(value['approval_sha256']==(prior if ordinal<old_count else current),'Public approval-prefix binding')
        need(value['inheritance_sha256']==inheritance['ledger_sha256'],'Original514 ledger identity')
        op=value['operation_id'];kind=value['kind']
        if kind=='RESERVE':
            need(op not in operations,'Duplicate reserved public operation');requests+=1;rows+=value['reserved_rows'];phase+=int(ordinal>=old_count)
        else:
            allowed={'START':['RESERVE'],'COMPLETE':['START'],'FAILED':['START'],'CANCELLED_NO_LAUNCH':['RESERVE']}
            need(kind in allowed and operations.get(op)in allowed[kind],'Public operation lifecycle')
        operations[op]=kind
    need(requests<=approval['request_ceiling']and rows<=approval['row_ceiling']and phase<=approval['phase_request_ceiling'],'Public cumulative budget')
    return dict(requests=requests,reserved_rows=rows,phase_requests=phase,operations=operations)


def export(configuration,out):
    c=read(configuration);root=Path(c['execution_root']);state=read(root/'STATE.json')
    need(state['status']in ('S3_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY','S3_PARTIAL_STOPPED'),'Only terminal S3 export')
    need((root/'CONTROLLER_CLOSED.private.json').exists(),'Controller has not closed its own guard/locks')
    need(not out.exists(),'Fresh terminal export');out.mkdir(parents=True);numeric=[];private=[]
    for label,base in [('data',root),('source',Path(__file__).resolve().parent.parent)]:
        for path in sorted(base.rglob('*')):
            if not path.is_file()or path.is_symlink()or '__pycache__'in path.parts:continue
            relative=str(path.relative_to(base));logical=label+'/'+relative
            if path.suffix in ('.bin','.f32','.gguf'):
                numeric.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            if relative.startswith(('RESOURCE_GUARD','GUARD_BASELINE')):
                private.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            try:text=path.read_text()
            except UnicodeDecodeError:
                private.append(dict(logical_id=logical,sha256=sha(path),bytes=path.stat().st_size));continue
            target=out/logical;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(transform(text,c['study_root']))
    extras={'FROZEN_MANIFEST.json':Path(c['manifest']),'ROOTS.json':Path(c['roots']),
            'ORIGINAL32B_S1_S2_PREFIX.jsonl':Path(c['inheritance']['approval_prefix_path']),
            'FINAL_GLOBAL_LEDGER.jsonl':root/'FINAL_GLOBAL_LEDGER.jsonl'if(root/'FINAL_GLOBAL_LEDGER.jsonl').exists()else Path(c['ledger'])}
    # A final snapshot is exported even for partial attempts; all failures and
    # reservations remain chargeable. Existing completed source data are kept.
    for name,path in extras.items():
        target=out/'data'/name
        if target.exists():
            need(target.read_text()==transform(path.read_text(),c['study_root']),'Existing final snapshot differs')
        else:target.write_text(transform(path.read_text(),c['study_root']))
    fresh(out/'data/BUDGET_APPROVAL.json',c['budget_approval']);fresh(out/'data/INHERITANCE.json',c['inheritance'])
    # INHERITANCE paths are private configuration, not part of approval hashes.
    path=out/'data/INHERITANCE.json';path.write_text(transform(path.read_text(),c['study_root']))
    fresh(out/'PRIVATE_RESOURCE_TEXT_INVENTORY.json',private)
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='COMPLETE'if state['status'].startswith('S3_COMPLETE')else'PARTIAL',
        files=[],withheld_numeric_payloads=numeric,private_literals=[c['study_root'],str(Path.home())])
    for path in out.rglob('*'):
        if path.is_file():selection['files'].append(dict(path=str(path.relative_to(out)),sha256=sha(path),bytes=path.stat().st_size,
            payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    fresh(out.parent/(out.name+'.selection.json'),selection)
    meta=archive.create(out,selection,out.parent/(out.name+'.tar.gz'));fresh(out.parent/(out.name+'.archive.json'),meta);return meta


def replay(package,expected,out):
    report=archive.replay(package,out,expected,max_payload_bytes=16*1024**3)
    approval=read(out/'data/BUDGET_APPROVAL.json');inheritance=read(out/'data/INHERITANCE.json')
    accounting=journal(out/'data/FINAL_GLOBAL_LEDGER.jsonl',out/'data/ORIGINAL32B_S1_S2_PREFIX.jsonl',approval,inheritance)
    complete=read(out/'data/STATE.json')['status']=='S3_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY'
    if complete:
        rows=read(out/'data/S3_ROWS.json');actual=json.loads(json.dumps(analyze(rows,'S3')))
        need(actual==read(out/'data/S3_ANALYSIS.json'),'Complete288-operation/root-level statistics replay differs')
        plan=read(out/'data/FROZEN_MANIFEST.json');by_id={r['operation_id']:r for r in rows};need(len(by_id)==288,'All288 distinct S3 operation rows')
        for worker in plan['workers']:
            if worker['stage']!='formal':continue
            for ordinal,op in enumerate(worker['operations']):
                row=by_id[op['operation_id']];need(row['worker_id']==worker['worker_id']and row['ordinal']==ordinal,'Exact formal manifest row')
                native=read(out/'data/S3/workers'/worker['worker_id']/'native'/('warm'if ordinal==0 else'measured')/'receipt.json')
                need(native['S3_service']['elapsed_s']==row['elapsed_s']and native['ids']==row['tokens'],'Actual raw native endpoint/complete output binding')
        need(accounting['phase_requests']==423 and all(value=='COMPLETE'for op,value in accounting['operations'].items()if op.startswith('s3-v1-')),'All423 S3 requests charged/completed')
        report.update(statistical_replay='PASSED_COMPLETE_288_FORMAL_AND423_STAGE_OPERATIONS',workers=144,warmups=144,measurements=144)
    else:report.update(statistical_replay='PARTIAL_NO_COMPLETE_PANEL_ESTIMATE')
    report['cumulative_accounting']={k:v for k,v in accounting.items()if k!='operations'}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('export');p.add_argument('--configuration',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('replay')
    for name in ('archive','out','report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sha256',required=True);a=parser.parse_args()
    if a.mode=='export':print(json.dumps(export(a.configuration,a.out)))
    else:
        result=replay(a.archive,a.sha256,a.out);fresh(a.report,result);print(json.dumps(result))
