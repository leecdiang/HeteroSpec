"""Reconstruct the entire hash chain and reconcile each settled native attempt."""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,json,collections
from independent_qualification import read,save,sha,require

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def audit(root,out,allow_open=False,original_root=None,relocated_root=None):
    root=Path(root);ledger=root/'LEDGER.jsonl';previous='0'*64;opened={};settled=[];limits={'credits':0,'seconds':0};reserved=0;notes=[]
    for line in ledger.read_text(encoding='utf-8').splitlines():
        event=json.loads(line);h=event.pop('hash');require(event['prev']==previous and hashlib.sha256(canonical(event)).hexdigest()==h,'ledger hash chain');previous=h
        if event['event']=='EXTEND':limits['credits']+=event['credits'];limits['seconds']+=event['seconds']
        elif event['event']=='START':
            require(not opened,'overlapping unsettled work');opened[event['attempt']]=event;reserved+=event['credits']
        elif event['event']=='END':
            start=opened.pop(event['attempt']);p=Path(event['attempt'])
            if original_root:
                require(relocated_root is not None,'relocation destination');relative=PureWindowsPath(event['attempt']).relative_to(PureWindowsPath(original_root));require('..' not in relative.parts,'confined attempt relocation');p=Path(relocated_root).joinpath(*relative.parts)
            receipt=read(p/'RECEIPT.json');supervisor=read(p/'SUPERVISOR.json')
            require(supervisor['job_accounting']['active_processes']==0 and receipt['cleanup_verified'],'unclean process')
            native=read(p/'native/result.json');completed=len(native.get('records',native.get('requests',[])));operators=len(native.get('rows',[]))
            require(completed==event['completed_model_requests'] and operators==event['operator_calls'] and completed<=start['requests'],'native cumulative accounting');require(receipt['success']==event['success'],'success/failure accounting')
            settled.append({'attempt':event['attempt'],'reserved_model_slots':start['requests'],'completed_model_requests':completed,'operator_graph_calls':operators,'success':event['success'],'host_owned_seconds':event['seconds'],'native_process_seconds':supervisor['charged_seconds'],'supervisor_sha256':sha(p/'SUPERVISOR.json'),'receipt_sha256':sha(p/'RECEIPT.json')})
        else:require(event['event']=='NOTE','event type');notes.append(event)
    require(allow_open or not opened,'unfinished native attempts');require(reserved<=limits['credits'],'renewable credit capacity')
    save(out,{'status':'INDEPENDENT_LEDGER_RECONCILED','hash_chain_head':previous,'ledger_sha256':sha(ledger),'limits':limits,'credits_reserved_including_failed_and_unstarted_slots':reserved,'completed_model_requests':sum(x['completed_model_requests'] for x in settled),'operator_graph_calls':sum(x['operator_graph_calls'] for x in settled),'host_owned_seconds':sum(x['host_owned_seconds'] for x in settled),'native_process_seconds':sum(x['native_process_seconds'] for x in settled),'failed_attempts':sum(not x['success'] for x in settled),'zero_request_attempts':sum(x['completed_model_requests']==0 and x['operator_graph_calls']==0 for x in settled),'attempts':settled,'open':opened,'notes':notes,'scope':'New B570 native work only. Historical externally executed requests and invalid historical alias captures are preserved separately. Operator count is native graph submissions, not inferred shader dispatches; stage/dispatch counts are separately evidenced. Build and transport failures are retained outside the inference ledger.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--allow-open',action='store_true');p.add_argument('--original-root');p.add_argument('--relocated-root');a=p.parse_args();audit(a.root,a.out,a.allow_open,a.original_root,a.relocated_root)
