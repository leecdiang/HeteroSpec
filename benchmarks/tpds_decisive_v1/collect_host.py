"""Publish compact receipts and complete reserved/observed native costs."""
from build_host import *
from native_adapter import RUNS
import sqlite3,datetime,os
HERE=Path(__file__).resolve().parent;DEST=HERE/'host_evidence'
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2),encoding='utf8');os.replace(tmp,p)
def main():
    copies={}
    for p in ROOT.glob('*.json'):
        if p.name.startswith('EVIDENCE_DEDUP-'):continue
        copies['host/'+p.name]=p
    for p in Path('D:/rtx184-qualification').glob('*/QUALIFICATION.json'):copies['qualification/'+p.parent.name+'.json']=p
    for p in RUNS.glob('priming-v3-*/PRIMING_QUALIFICATION.json'):copies['priming/'+p.parent.name+'.json']=p
    for p in (ROOT/'selection-v3').glob('*.json'):copies['selection/'+p.name]=p
    for root in (ROOT/'draft-v3',ROOT/'forced-v2',Path('D:/rtx184-operator')):
        for name in ('BUILD.json','CORE_BUILD.json','BUILD_CORE.json','RUNTIME_BUILD.json','RUNTIME_BINDING.json'):
            for p in root.rglob(name):copies['build/'+p.parent.name+'/'+name]=p
    for name,p in copies.items():write(DEST/name,json.loads(p.read_bytes()))
    db=sqlite3.connect(ROOT/'ledger.sqlite');db.row_factory=sqlite3.Row;attempts=[dict(r) for r in db.execute('select * from attempts order by started')];db.close()
    services=[];native=[]
    for attempt in attempts:
        base=RUNS/attempt['id']
        if not base.exists():base=ROOT/attempt['id']
        record=dict(attempt=attempt['id'],status=attempt['status'],reserved={k:attempt[k] for k in ('requests','token_rows','operators')})
        exit=base/'exit.json'
        if exit.exists():record['host_exit']=json.loads(exit.read_bytes())
        receipt=base/'session-result.json'
        if receipt.exists():
            result=json.loads(receipt.read_bytes());record['actual_work']=result['actual_work'];services += [dict(x,attempt=attempt['id']) for x in result['records']] if 'records' in result else []
        for file in ('result.json','PROVISIONED.json'):
            p=base/'native'/file
            if p.exists():
                data=json.loads(p.read_bytes());record[file]={k:v for k,v in data.items() if ('seconds' in k or 'memory' in k or k in ('status','requests','token_rows','error')) and k!='requests'}
                if isinstance(data.get('requests'),list):record['completed_native_records']=len(data['requests'])
        if (base/'failure.json').exists():record['failure']=json.loads((base/'failure.json').read_bytes())
        native.append(record)
    summary=dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempts=attempts,native=native,reserved_total={k:sum(x[k] for x in attempts) for k in ('requests','token_rows','operators')},host_process_seconds=sum(x.get('host_exit',{}).get('seconds',0) for x in native),service_seconds=sum(x['service_s'] for x in services),services=services,interpretation='Reservations never refunded. Service/model/provision components are nested within host process wall and must not be added to it. Running/failed attempts remain explicit; missing actual-work fields are not zeros.')
    write(DEST/'UNIFIED_COSTS.json',summary)
    write(DEST/'RECEIPT_INDEX.json',dict(files={k:dict(source=str(v),sha256=sha(v)) for k,v in copies.items()},raw_archive_root='C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence',raw_restore='python archive_host.py restore <manifest stem>; restore requires its chunks directory; no GPU'))
    print('collected',len(copies),'receipts;',len(attempts),'ledger entries')
if __name__=='__main__':main()
