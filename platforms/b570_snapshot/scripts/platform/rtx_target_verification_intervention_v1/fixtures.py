"""Executed negative, lock, atomic completion and recovery fixtures."""
import tempfile, shutil
import execution as ex
import integrity as g
from prepare import *

def main(gpu=True):
    receipt={'utc':utc(),'synthetic_guard_inputs':True};tests={}
    def reject(name,fn):
        try:fn()
        except Exception as e:tests[name]={'pass':True,'error_type':type(e).__name__}
        else:raise AssertionError(name+' accepted')
    with tempfile.TemporaryDirectory(prefix='rtx-guards-',dir=OUT) as td:
        root=Path(td);doc=root/'doc';out=root/'out';doc.mkdir();out.mkdir()
        source=root/'source.py';source.write_text('fixed')
        cohort=doc/'COHORT.json';save(cohort,{'fixed':[1]});protocol=doc/'PROTOCOL.json';save(protocol,{'fixed':True})
        asset=root/'asset.bin';asset.write_bytes(b'fixed');st=asset.stat()
        save(doc/'ASSET_ENVIRONMENT.json',{'files':{'fixture':{'path':str(asset),'sha256':sha(asset),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}}})
        paths=[source,cohort,protocol];freeze={'files':{str(p.relative_to(root)).replace('\\','/'):sha(p) for p in paths},'critical_files':[],'metadata':{str(p.relative_to(root)).replace('\\','/'):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in paths}}
        save(doc/'FREEZE.json',freeze)
        queue=[{'id':f'fixture/{c}/{i}','condition':c} for c in ['R','H0','H1','N0','N1'] for i in range(129)];save(doc/'QUEUE.json',queue)
        preds={}
        for q in queue:
            if q['condition'] not in ['R','H0','H1']:continue
            p=root/'results'/(q['id'].replace('/','-')+'.json')
            save(p,{'valid':True,'unit_id':q['id'],'files':{},'ids':[151645],'endpoint':'EOS'})
            if q['condition'] in ['H0','H1']:preds[q['id']]={'result':str(p.relative_to(root)).replace('\\','/'),'sha256':sha(p),'ids':[151645],'endpoint':'EOS'}
            g.event('UNIT_VALID',root=out,condition=q['condition'],unit_id=q['id'])
        save(out/'STATUS.json',{'stage':'N0'});save(out/'SEAL_MODE.json',{'mode':'LOCAL_SEAL_ONLY'})
        def guard():return g.native_guard('N0',root,doc,out)
        launches=[]
        def guarded_launch():guard();launches.append('started')
        reject('missing_seal_native_not_started',guarded_launch);assert not launches
        save(out/'PREDICTION_SEAL.json',{'freeze_sha256':sha(doc/'FREEZE.json'),'predictions':preds})
        g.event('PREDICTION_SEALED',root=out,seal_sha256=sha(out/'PREDICTION_SEAL.json'))
        guard();tests['valid_seal_accepted']={'pass':True}
        original=(out/'PREDICTION_SEAL.json').read_bytes();save(out/'PREDICTION_SEAL.json',{'bad':True});reject('bad_seal_digest_native_not_started',guarded_launch);(out/'PREDICTION_SEAL.json').write_bytes(original)
        p=root/next(iter(preds.values()))['result'];b=p.read_bytes();p.write_bytes(b'{}');reject('tampered_prediction_native_not_started',guarded_launch);p.write_bytes(b)
        for name,p in [('source',source),('protocol',protocol),('cohort',cohort),('asset',asset)]:
            b=p.read_bytes();stat=p.stat();p.write_bytes(b'drift');reject(name+'_drift_native_not_started',guarded_launch);p.write_bytes(b);os.utime(p,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        assert not launches
        g.lock(out);reject('second_active_controller_rejected',lambda:g.lock(out))
        stale=read(out/'LOCK.json');stale['creation_identity']='0';save(out/'LOCK.json',stale);g.lock(out);tests['same_pid_wrong_creation_not_active']={'pass':True}
        oldout=ex.OUT;ex.OUT=out
        try:
            base=out/'cached'/'MBPP-1-H0-r1';base.mkdir(parents=True);raw=base/'raw.txt';raw.write_bytes(b'original')
            result={'valid':True,'files':{'raw.txt':sha(raw)}};save(base/'result.json',result);h=sha(base/'result.json')
            ex.unit('MBPP/1','H0',1,'cached');assert sha(base/'result.json')==h and raw.read_bytes()==b'original';tests['resume_complete_original_bytes_retained']={'pass':True}
            partial=out/'partial';partial.mkdir();attempt=partial/'attempt-01-fixture';attempt.mkdir();(attempt/'raw.txt').write_bytes(b'incomplete')
            new=ex.attempt_directory(partial);(new/'raw.txt').write_bytes(b'complete');assert (attempt/'raw.txt').read_bytes()==b'incomplete' and new.name.startswith('attempt-02');tests['resume_partial_original_attempt_retained_rerun']={'pass':True}
            save(out/'result.json.tmp',{'valid':True});assert not (out/'result.json').exists();tests['unfinished_output_not_valid']={'pass':True}
        finally:ex.OUT=oldout
        ids=[1]*127+[151645];idx=list(range(1,129))
        x=g.committed(idx,ids,['limit','EOS'],128);assert x['endpoint']=='EOS' and x['stop_markers']==['limit','EOS'];tests['token128_simultaneous_eog_cap_preserved']={'pass':True}
        for name,indices,stops,count in [('missing',idx[:-1],['limit','EOS'],128),('duplicate',idx[:-1]+[127],['limit','EOS'],128),('reordered',idx[:2][::-1]+idx[2:],['limit','EOS'],128),('reversed_stop',idx,['EOS','limit'],128),('missing_stop',idx,['limit'],128),('wrong_count',idx,['limit','EOS'],127)]:reject(name+'_committed_rejected',lambda i=indices,s=stops,n=count:g.committed(i,ids,s,n))
        reject('early_eog_rejected',lambda:g.committed(idx,[151645]+[1]*127,['limit'],128))
        reject('short_non_eog_rejected',lambda:g.committed([1],[1],['EOS'],1))
    detached=read(OUT/'detached-fixture/COMPLETE.json');launch=read(OUT/'detached-launch.json');assert detached['complete'] and detached['pid']==launch['pid'] and detached['utc']>launch['launch_return_utc']
    tests['launch_tool_return_survival']={'pass':True,'launch':launch,'completion':detached,'scope':'tool returned before completion; not logout/reboot/app forced termination proof'}
    if gpu:
        text=(ROOT/read(OUT/'INPUTS.json')['HumanEval/15']['prompt']).read_text(encoding='utf-8')
        for name in ['wrong_pending','wrong_position','proposal_width','future_answer_field']:
            d=OUT/'gpu-fixtures'/name;d.mkdir(parents=True,exist_ok=False);w=ex.Worker('R',2,d,False,0)
            try:
                ri=w.call({'op':'init','formatted_prompt':formatted(text)});q={'op':'verify','round':0,'position':len(ri['prompt_ids']),'pending':ri['committed_ids'][0],'proposal_ids':[1,2]}
                if name=='wrong_pending':q['pending']+=1
                if name=='wrong_position':q['position']-=1
                if name=='proposal_width':q['proposal_ids']=[1,2,3]
                if name=='future_answer_field':q['future_native_ids']=[1]
                reject(name+'_worker_rejected',lambda:w.call(q))
            finally:w.close()
    receipt.update(status='PASS',tests=tests,test_count=len(tests));save(DOC/'FIXTURE_RECEIPT.json',receipt);print(json.dumps({'status':'PASS','tests':len(tests)}),flush=True)

if __name__=='__main__':main()
