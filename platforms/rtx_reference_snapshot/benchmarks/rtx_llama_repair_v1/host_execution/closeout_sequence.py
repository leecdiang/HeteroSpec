"""After complete science, snapshot and verify draft evidence delivery; no merge."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
CODE=REPO/'benchmarks/rtx_llama_repair_v1/host_execution'
OPS=Path('D:/rtx160/operations')
ROOT=Path('E:/rtx160');TRANSPORT=ROOT/'transport01';ARCHIVE=Path('F:/rtx160/archive01')
TAG='rtx-llama-repair-v1-evidence-20261102'
PR='https://github.com/leecdiang/HeteroSpec/pull/162'
ENV=dict(os.environ,PYTHONUTF8='1',GODEBUG='http2client=0')


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def logged(name,script,args):
    return [sys.executable,'-B',str(OPS/'run_logged.py'),name,sys.executable,'-B',str(script),*map(str,args)]
def run(name,script,args):subprocess.run(logged(name,script,args),cwd=REPO,env=ENV,check=True)
def command(name,args,timeout=600):
    start=time.monotonic();p=subprocess.run(list(map(str,args)),cwd=REPO,env=ENV,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    save(TRANSPORT/(name+'.json'),{'argv':list(map(str,args)),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.monotonic()-start})
    assert p.returncode==0,name+' failed; retain receipts and use a fresh explicit successor'
    return p.stdout.strip()


def main():
    done=OPS/'POST_CONFIRMATION04.json';deadline=time.monotonic()+86400
    while not done.exists():
        assert time.monotonic()<deadline,'finite science wait expired';time.sleep(10)
    assert read(done)['exit_code']==0,'science gate failed; no archive or release created'
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    assert not ARCHIVE.exists();TRANSPORT.mkdir(exist_ok=False)
    run('FINALIZE_SCIENCE01',CODE/'finalize_science.py',[])
    assert command('BRANCH',['git','branch','--show-current'])=='codex/pr160-llama-repair'
    command('DIFF_CHECK',['git','diff','--check'])
    command('STAGE',['git','add','--','benchmarks/rtx_llama_repair_v1/host_execution','scripts/experiments/rtx_llama_repair_v1'])
    command('COMMIT',['git','-c','user.name=leecdiang','-c','user.email=162876606+leecdiang@users.noreply.github.com','commit','-m','Record complete Llama qualification, paired costs and independent audits'])
    snapshot=command('SNAPSHOT',['git','rev-parse','HEAD'])
    command('PUSH',['git','-c','http.version=HTTP/1.1','push','origin','codex/pr160-llama-repair'])
    # A duplicate tag, authentication failure or existing release is a hard error;
    # no clobber or adoption of unaccounted remote assets is allowed.
    existing=subprocess.run(['gh','api',f'repos/leecdiang/HeteroSpec/releases/tags/{TAG}'],cwd=REPO,env=ENV,capture_output=True,text=True,encoding='utf-8',timeout=120)
    save(TRANSPORT/'RELEASE_ABSENCE.json',{'exit_code':existing.returncode,'stdout':existing.stdout,'stderr':existing.stderr})
    assert existing.returncode!=0 and 'HTTP 404' in existing.stderr,'release tag not unambiguously absent'
    notes=TRANSPORT/'DRAFT_NOTES.md'
    notes.write_text('Independent results: '+PR+'\n\nScientific execution and independent reconstruction are complete. Raw upload and fresh every-member readback are in progress. This release remains a draft until all delivery gates pass. No merge or manuscript edit.\n',encoding='utf-8')
    command('RELEASE_CREATE',['gh','release','create',TAG,'--repo','leecdiang/HeteroSpec','--target',snapshot,'--draft','--title','Llama RTX prefix-extent repair: PR162 evidence','--notes-file',notes])
    release=json.loads(command('RELEASE_METADATA',['gh','api',f'repos/leecdiang/HeteroSpec/releases/tags/{TAG}']))
    assert release['draft'] and release['tag_name']==TAG and release['target_commitish']==snapshot and not release['assets']
    save(TRANSPORT/'CONFIG.json',{'tag':TAG,'release_id':release['id'],'snapshot':snapshot,'result_pr':PR,'archive':str(ARCHIVE),'upload':str(TRANSPORT/'upload01')})
    prior=TRANSPORT/'empty_prior';prior.mkdir();(prior/'UPLOADED_PARTS.jsonl').write_text('')
    packing=subprocess.Popen(logged('PACK01',CODE/'pack_evidence.py',['--out',ARCHIVE,'--repo',REPO]),cwd=REPO,env=ENV)
    uploading=subprocess.Popen(logged('UPLOAD01',ROOT/'parent159/diagnostics/parallel_upload.py',[ARCHIVE,TRANSPORT/'upload01',prior,TAG,release['id']]),cwd=REPO,env=ENV)
    # Both tools have finite transport contracts. The next-shard barrier only
    # exposes shards already closed and locally read back by the packer.
    codes=[packing.wait(),uploading.wait()]
    assert codes==[0,0],f'packing/upload failed {codes}; retain all partial evidence'
    run('DELIVERY_FINISH01',CODE/'finish_transport.py',['--archive',ARCHIVE,'--upload',TRANSPORT/'upload01','--root',TRANSPORT,'--tag',TAG,'--snapshot',snapshot,'--result-pr',PR])
    save(TRANSPORT/'CLOSEOUT_READY.json',{'status':'ALL_SCIENCE_AND_DRAFT_DELIVERY_GATES_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release_published':False,'result_pr':PR,'snapshot':snapshot,'tag':TAG,'release_id':release['id']})
    print('ALL_SCIENCE_AND_DRAFT_DELIVERY_GATES_PASS',flush=True)


if __name__=='__main__':main()
