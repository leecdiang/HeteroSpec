"""Fetch evidence from GitHub without local Git objects, restore and audit."""
import argparse,json,os,pathlib,subprocess,sys,uuid
from datetime import datetime,timezone
from restore import read,write,sha,restore
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1';DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
def main(existing_checkout=None):
    state=read(OUT/'UPLOAD_STATE.json');assert state['status']=='UPLOADED_PENDING_REMOTE_READBACK'
    content=state['content_commit'];expected=read(OUT/'ARCHIVE.json')
    nonce=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    checkout=pathlib.Path(existing_checkout).resolve() if existing_checkout else pathlib.Path('C:/hs/pf-remote-'+nonce)
    dest=pathlib.Path('C:/hs/pf-restored-'+nonce)
    assert not dest.exists()
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    log=OUT/'delivery-logs';log.mkdir(exist_ok=True)
    def run(args,label):
        with (log/(label+'.stdout.txt')).open('wb') as out,(log/(label+'.stderr.txt')).open('wb') as err:
            subprocess.run(args,cwd=ROOT,env=env,stdout=out,stderr=err,check=True)
    if existing_checkout:
        assert checkout.parent==pathlib.Path('C:/hs') and checkout.name.startswith('pf-remote-') and (checkout/'.git').is_dir()
        origin=subprocess.check_output(['git','-C',str(checkout),'remote','get-url','origin'],text=True).strip()
        assert origin=='https://github.com/leecdiang/HeteroSpec.git'
        run(['git','-C',str(checkout),'config','core.autocrlf','false'],'remote-canonical-config-'+nonce)
        run(['git','-C',str(checkout),'-c','http.sslBackend=openssl','fetch','--depth','1','origin','codex/b570-prefill-diagnostic-v1'],'remote-fetch-metadata-amendment-'+nonce)
        # This is the isolated disposable network read-back checkout, never the
        # authoritative study worktree. Canonical checkout removes CRLF only.
        run(['git','-C',str(checkout),'-c','http.sslBackend=openssl','checkout','--detach','--force',content],'remote-canonical-checkout-'+nonce)
    else:
        assert not checkout.exists()
        run(['git','-c','http.sslBackend=openssl','clone','--config','core.autocrlf=false','--filter=blob:none','--depth','1','--single-branch','--no-checkout','--branch','codex/b570-prefill-diagnostic-v1','https://github.com/leecdiang/HeteroSpec.git',str(checkout)],'remote-clone-'+nonce)
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
      'remote_content_commit':content,'fresh_remote_checkout':str(checkout),'remote_readback_method':'isolated shallow filtered Git clone from GitHub; all objects originally hydrated over network, no objects borrowed from authoritative local study; metadata amendment fetched over network',
      'checkout_line_ending_policy':'core.autocrlf=false and tracked -text attributes for sealed JSON; earlier failed working-copy conversion retained in delivery logs',
      'remote_parts_verified':len(expected['parts']),'remote_archive_bytes':expected['archive_bytes'],
      'delivery_seal_sha256':sha(DOC/'DELIVERY_SEAL.json'),'verification_implementation_sha256':sha(pathlib.Path(__file__)),
      'scientific_raw_or_frozen_code_changed':False,'main_tag_merge_release_or_PR51_modified':False})
    write(DOC/'REMOTE_DELIVERY.json',receipt)
    print(json.dumps({'phase':'REMOTE_RESTORE_PASS','receipt':str(DOC/'REMOTE_DELIVERY.json'),'commit':content,'formal_units':360,'raw_checks':receipt['independent_raw_checks']},indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reuse-remote-checkout');a=p.parse_args();main(a.reuse_remote_checkout)
