"""Fetch evidence from GitHub without local Git objects, restore and audit."""
import json,os,pathlib,subprocess,sys,uuid
from datetime import datetime,timezone
from restore import read,write,sha,restore
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1';DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
def main():
    state=read(OUT/'UPLOAD_STATE.json');assert state['status']=='UPLOADED_PENDING_REMOTE_READBACK'
    content=state['content_commit'];expected=read(OUT/'ARCHIVE.json')
    nonce=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    checkout=pathlib.Path('C:/hs/pf-remote-'+nonce);dest=pathlib.Path('C:/hs/pf-restored-'+nonce)
    assert not checkout.exists() and not dest.exists()
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    log=OUT/'delivery-logs';log.mkdir(exist_ok=True)
    def run(args,label):
        with (log/(label+'.stdout.txt')).open('wb') as out,(log/(label+'.stderr.txt')).open('wb') as err:
            subprocess.run(args,cwd=ROOT,env=env,stdout=out,stderr=err,check=True)
    run(['git','-c','http.sslBackend=openssl','clone','--filter=blob:none','--depth','1','--single-branch','--no-checkout','--branch','codex/b570-prefill-diagnostic-v1','https://github.com/leecdiang/HeteroSpec.git',str(checkout)],'remote-clone-'+nonce)
    seen=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip();assert seen==content
    run(['git','-C',str(checkout),'sparse-checkout','init','--no-cone'],'remote-sparse-init-'+nonce)
    run(['git','-C',str(checkout),'sparse-checkout','set','/artifacts/b570_prefill_diagnostic_v1/','/benchmarks/b570_prefill_diagnostic_v1/','/scripts/platform/b570_prefill_delivery_v1/'],'remote-sparse-set-'+nonce)
    print(json.dumps({'phase':'FETCHING_REMOTE_EVIDENCE','content_commit':content,'checkout':str(checkout)}),flush=True)
    run(['git','-C',str(checkout),'-c','http.sslBackend=openssl','checkout'],'remote-checkout-'+nonce)
    remote_index=checkout/'artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json'
    assert sha(remote_index)==state['archive_index_sha256']==sha(OUT/'ARCHIVE.json')
    seal=read(DOC/'DELIVERY_SEAL.json');assert expected['archive_sha256']==seal['archive_sha256']
    assert sha(checkout/'benchmarks/b570_prefill_diagnostic_v1/DELIVERY_SEAL.json')==sha(DOC/'DELIVERY_SEAL.json')
    remote_parts=remote_index.parent
    for part in expected['parts']:
        assert sha(remote_parts/part['path'])==part['sha256'] and (remote_parts/part['path']).stat().st_size==part['bytes']
    print(json.dumps({'phase':'REMOTE_PARTS_HASHED','parts':len(expected['parts']),'bytes':expected['archive_bytes']}),flush=True)
    receipt=restore(remote_index,dest)
    receipt.update({'status':'UPLOADED_AND_REMOTE_RESTORE_VERIFIED','repository':'leecdiang/HeteroSpec','repository_visibility':'private','branch':'codex/b570-prefill-diagnostic-v1',
      'remote_content_commit':content,'fresh_remote_checkout':str(checkout),'remote_readback_method':'new shallow filtered Git clone from GitHub; no local object cache or alternates; hydrate all archive parts over network',
      'remote_parts_verified':len(expected['parts']),'remote_archive_bytes':expected['archive_bytes'],
      'delivery_seal_sha256':sha(DOC/'DELIVERY_SEAL.json'),'verification_implementation_sha256':sha(pathlib.Path(__file__)),
      'scientific_raw_or_frozen_code_changed':False,'main_tag_merge_release_or_PR51_modified':False})
    write(DOC/'REMOTE_DELIVERY.json',receipt)
    print(json.dumps({'phase':'REMOTE_RESTORE_PASS','receipt':str(DOC/'REMOTE_DELIVERY.json'),'commit':content,'formal_units':360,'raw_checks':receipt['independent_raw_checks']},indent=2),flush=True)
if __name__=='__main__':main()
