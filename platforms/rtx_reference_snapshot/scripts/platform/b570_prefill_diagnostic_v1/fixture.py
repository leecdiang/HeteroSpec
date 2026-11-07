"""No-GPU gate, atomic persistence and detached-process fixtures."""
import importlib.util,json,pathlib,tempfile,hashlib,sys,time,os
HERE=pathlib.Path(__file__).parent
def gates():
    spec=importlib.util.spec_from_file_location('controller',HERE/'controller.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    receipt={}
    with tempfile.TemporaryDirectory(prefix='prefill-fixture-',dir='C:/hs') as td:
        c.ROOT=pathlib.Path(td);c.OUT=c.ROOT/'out';c.DOC=c.ROOT/'doc';c.OUT.mkdir();c.DOC.mkdir()
        c.save(c.DOC/'BASELINE_GATE.json',{'status':'PASS'});c.save(c.DOC/'PROTOCOL.json',{});c.save(c.DOC/'ASSET_MANIFEST.json',{})
        def reject(name,fn):
            try:fn()
            except (Exception,AssertionError):receipt[name]=True
            else:raise AssertionError(name+' not rejected')
        reject('missing_seal_rejected',c.verify_seal)
        reject('bad_endpoint_rejected',lambda:c.endpoint([1,2],[False,False]))
        predictions={}
        for t in c.TASKS:
            for r in range(1,4):
                unit=f'{c.STUDY}/v1/{t}/T1/{r}';p=c.OUT/(t.replace('/','_')+str(r)+'.json');c.save(p,{'unit_id':unit,'valid':True,'files':{}})
                predictions[unit]={'path':c.rel(p),'sha256':c.sha(p)}
        c.save(c.OUT/'T1_SEAL.json',{'protocol_sha256':c.sha(c.DOC/'PROTOCOL.json'),'manifest_sha256':c.sha(c.DOC/'ASSET_MANIFEST.json'),'predictions':predictions})
        c.event('T1_SEALED',seal_sha256=c.sha(c.OUT/'T1_SEAL.json'));c.verify_seal();receipt['valid_seal_accepted']=True
        c.save(c.DOC/'PROTOCOL.json',{'drift':True});reject('protocol_hash_drift_rejected',c.verify_seal);c.save(c.DOC/'PROTOCOL.json',{})
        c.acquire();reject('duplicate_active_controller_rejected',c.acquire)
        p=c.ROOT/next(iter(predictions.values()))['path'];p.write_text('{}');reject('result_hash_drift_rejected',c.verify_seal)
        # Restore the file exactly, then move an N1 event before the seal event.
        unit=next(iter(predictions));c.save(p,{'unit_id':unit,'valid':True,'files':{}})
        events=c.ledger();early={'event':'ATTEMPT_START','variant':'N1','utc':c.utc()}
        (c.OUT/'RUN_LEDGER.jsonl').write_text('\n'.join(json.dumps(x) for x in [early]+events)+'\n')
        reject('early_N1_rejected',c.verify_seal)
        c.save(c.OUT/'atomic.json',{'complete':True});assert not (c.OUT/'atomic.json.tmp').exists();receipt['atomic_commit_pass']=True
        c.save(c.OUT/'partial.json.tmp',{'unfinished':True});assert not (c.OUT/'partial.json').exists();receipt['partial_not_completed']=True
    return receipt
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':
        dest=pathlib.Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
        (dest/'started.json').write_text(json.dumps({'pid':os.getpid(),'utc':time.time()}))
        for i in range(3):time.sleep(4);(dest/'progress.json').write_text(json.dumps({'i':i,'pid':os.getpid()}))
        tmp=dest/'complete.json.tmp'
        with tmp.open('w') as f:json.dump({'pid':os.getpid(),'complete':True},f);f.flush();os.fsync(f.fileno())
        os.replace(tmp,dest/'complete.json')
    else:print(json.dumps(gates(),indent=2))
