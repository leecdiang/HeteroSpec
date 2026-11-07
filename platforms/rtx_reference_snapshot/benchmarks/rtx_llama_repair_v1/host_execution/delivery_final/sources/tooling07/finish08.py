"""Gated raw and metadata download verification; no model work or publication."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)


def main():
    p=argparse.ArgumentParser()
    for name in ('archive','upload','root'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('tag','snapshot','result-pr'):p.add_argument('--'+name,required=True)
    p.add_argument('--upload-source',type=Path,required=True);p.add_argument('--pack-operation',default='PACK01');p.add_argument('--upload-operation',default='UPLOAD06');a=p.parse_args()
    ops=Path('D:/rtx160/operations');parent=Path('E:/rtx160/parent159');adapt=Path(__file__).parent;code=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160/benchmarks/rtx_llama_repair_v1/host_execution')
    repo=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160');env=dict(os.environ,GODEBUG='http2client=0',PYTHONUTF8='1')
    def run(name,script,args):
        subprocess.run([sys.executable,'-B',str(ops/'run_logged.py'),name,sys.executable,'-B',str(script),*map(str,args)],cwd=repo,env=env,check=True)
    def gh(name,args):
        command=['gh',*map(str,args)];start=time.monotonic()
        with (ops/(name+'.log')).open('xb') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=repo)
            try:exit_code=process.wait(timeout=600)
            except subprocess.TimeoutExpired:process.kill();process.wait();exit_code=-1
        save(ops/(name+'.json'),{'argv':command,'pid':process.pid,'exit_code':exit_code,'seconds':time.monotonic()-start})
        assert exit_code==0,name+' failed; receipt and partial retained'
    policy=read(a.root/'TRANSPORT_RESOURCE_POLICY02.json')
    remaining=(datetime.datetime.fromisoformat(policy['overall_deadline_utc'])-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    assert 0<remaining<=86400
    deadline=time.monotonic()+remaining
    for name in (a.pack_operation,a.upload_operation):
        receipt=ops/(name+'.json')
        while not receipt.exists():
            assert time.monotonic()<deadline,'finite transport gate wait expired';time.sleep(5)
        assert read(receipt)['exit_code']==0,name+' gate failed'
    remote=a.root/'remote03';delivery=a.root/'delivery01';metadata_remote=a.root/'delivery_remote01'
    run('REMOTE_VERIFY03',adapt/'verify_remaining.py',[a.archive,remote,a.tag])
    run('DELIVERY_METADATA06',adapt/'metadata08.py',['--archive',a.archive,'--upload',a.upload,'--remote',remote,
      '--out',delivery,'--upload-source',a.upload_source,'--operations',ops,'--parent',parent,'--snapshot',a.snapshot,'--result-pr',a.result_pr,'--pack-operation',a.pack_operation])
    assets=[delivery/x['name'] for x in read(delivery/'DELIVERY_ASSETS.json')['assets']]+[delivery/'DELIVERY_ASSETS.json']
    gh('DELIVERY_METADATA_UPLOAD06',['release','upload',a.tag,'--repo','leecdiang/HeteroSpec',*assets])
    run('DELIVERY_METADATA_VERIFY06',code/'verify_delivery_metadata.py',[delivery,metadata_remote,a.tag])
    receipt=metadata_remote/'DELIVERY_METADATA_READBACK.json'
    assert read(receipt)['status']=='DELIVERY_METADATA_FRESH_REMOTE_READBACK_PASS'
    gh('DELIVERY_RECEIPT_UPLOAD06',['release','upload',a.tag,'--repo','leecdiang/HeteroSpec',receipt])
    fresh=a.root/'receipt_remote01';fresh.mkdir(exist_ok=False)
    gh('DELIVERY_RECEIPT_VERIFY06',['release','download',a.tag,'--repo','leecdiang/HeteroSpec','--dir',fresh,'--pattern',receipt.name])
    downloaded=fresh/receipt.name
    assert downloaded.stat().st_size==receipt.stat().st_size and sha(downloaded)==sha(receipt)
    save(fresh/'RECEIPT_ASSET_READBACK.json',{'status':'RECEIPT_ASSET_FRESH_REMOTE_READBACK_PASS',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tag':a.tag,'name':receipt.name,
      'bytes':downloaded.stat().st_size,'sha256':sha(downloaded),'native_requests_added':0,'release_published':False})
    print('ALL_TRANSPORT_GATES_PASS_RELEASE_STILL_DRAFT',flush=True)


if __name__=='__main__':main()
