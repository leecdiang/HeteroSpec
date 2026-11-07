"""The registered Llama 18+36 requests; separate evidence, no retries or repair."""
import argparse
from collections import Counter, defaultdict
import copy
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import subprocess
import sys
import threading
import time
import numpy as np
from common import *

HISTORY=Path('D:/hs144-e5c03228-9eb9-4198-8f14-a7d279d08afa')

def slots():
    rows=s.lines(DESIGN/'DIAGNOSTIC_SLOTS.jsonl')
    s.need(len(rows)==54 and Counter(r['stage'] for r in rows)=={'diagnostic_A1':18,'diagnostic_A2':36},'registered diagnostic schedule differs')
    s.need({r['source_index'] for r in rows}=={8,6,3},'diagnostic panel differs')
    return rows

def prepare(bundle):
    s.need(not bundle.exists(),'fresh diagnostic bundle required')
    with exclusive('diagnostic-prepare',600):
        bundle.mkdir(parents=True)
        before=main_pins()
        model=s.read(DESIGN/'MODEL_PINS.json')['families']['Llama']
        contract=s.read(HISTORY/'MODEL_CONTRACT.json')
        s.need(sha(HISTORY/'MODEL_CONTRACT.json')==s.MODEL_SHA,'model contract differs')
        main=s.read(MAIN/'EXECUTION_IDENTITY.json')
        ident=copy.deepcopy(main['families']['SmolLM2'])
        for key in ('source_variant','source_zip_sha256','models','vocabulary_sha256','template_sha256'):
            ident[key]=model[key]
        plan=s.read(DESIGN/'PLAN.json')
        plan['context']['lifecycle']='fresh'
        plan['context']['model_residency']='both weights loaded once per diagnostic unit; fresh contexts per request'
        plan['service_timer_definition']='diagnostic only: complete fresh-context request; never eligible for performance estimates'
        ident['context']=plan['context']
        local={'executable':str(REPO/'work/native-metadata4-v4/bin/rtx-scope-transfer.exe'),
               **{role:contract['families']['Llama']['models'][role]['path'] for role in ('target','draft')}}
        for role in ('target','draft'):
            p=Path(local[role]);s.need(p.stat().st_size==model['models'][role]['bytes'] and sha(p)==model['models'][role]['sha256'],'Llama model mismatch')
        exe=Path(local['executable'])
        s.need(sha(exe)==ident['executable_sha256'],'existing metadata4 executable mismatch')
        for name,digest in ident['numerical_modules'].items():
            s.need(sha(exe.parent/name)==digest,'DLL mismatch')
        panel=[None]*12
        for item in s.read(DESIGN/'PANEL.json')['llama_diagnostic']:
            panel[item['source_index']]=item
        history_manifest=MAIN/'provenance/PR144_RAW_FILE_MANIFEST.jsonl'
        inventory={r['path'].replace('\\','/'):r for r in s.lines(history_manifest)}
        refs={}; a0=[]; manifest=[]
        for item in (x for x in panel if x):
            idx=item['source_index']; endpoints={}; captures={}
            for arm in ('R','PQ','QB'):
                base=HISTORY/f'runs/E1/Llama/{idx:02d}_{arm}'
                paths=[p for p in base.glob('requests/*/RECORD.json') if s.read(p)['mode']=='heavy']
                s.need(len(paths)==1,'historical heavy request missing/ambiguous')
                record=s.read(paths[0]);output=record['output']
                endpoints[arm]={'ids':output['ids'],'eog':output['eog_flags'],**{k:output[k] for k in ('length','terminal_id','stop_reason')}}
                s.endpoint(endpoints[arm],model)
                captures[arm]={}
                for src in [paths[0],*sorted((base/'capture').glob('*'))]:
                    if not src.is_file():continue
                    rel=src.relative_to(HISTORY).as_posix(); expected=inventory.get(rel)
                    s.need(expected is not None and sha(src)==expected['sha256'] and src.stat().st_size==expected['bytes'],'A0 source pin mismatch: '+rel)
                    dest=bundle/'historical'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
                    p=pin(bundle,dest);manifest.append(p);captures[arm][src.name]=p
            refs[str(idx)]=endpoints
            first=next((i for i,(a,b) in enumerate(zip(endpoints['R']['ids'],endpoints['PQ']['ids'])) if a!=b),None)
            a0.append({'source_index':idx,'input_id':item['id'],'first_endpoint_divergence_zero_based':first,
                       'R_token':endpoints['R']['ids'][first] if first is not None else None,
                       'PQ_token':endpoints['PQ']['ids'][first] if first is not None else None,
                       'PQ_QB_endpoints_equal':endpoints['PQ']==endpoints['QB'],
                       'PQ_QB_full_logit_files_equal':captures['PQ']['logits.f32']['sha256']==captures['QB']['logits.f32']['sha256'],
                       'captures':captures})
        known=next(r for r in a0 if r['source_index']==8)
        s.need(known['first_endpoint_divergence_zero_based']==81 and known['R_token']==16 and known['PQ_token']==15,'known failure reconstruction differs')
        binding={'schema':1,'status':'FROZEN_BEFORE_FIRST_NATIVE_REQUEST','is_synthetic':False,'frozen_utc':now().isoformat(),
                 'study_id':'rtx_scope_transfer_v1','diagnostic_only':True,'families':{'Llama':ident},
                 'registered_slots_sha256':sha(DESIGN/'DIAGNOSTIC_SLOTS.jsonl'),
                 'main_checkpoint':before,'main_source_binding':s.read(MAIN/'FREEZE_COMMIT.json'),
                 'caps':{'requests':54,'A1_seconds':2700,'A2_seconds':3600,'total_owned_seconds':6300,'payload_bytes':24*1024**3,'minimum_free_bytes':20*1024**3,'post_model_load_free_bytes':512*1024**2},
                 'host_python_sha256':sha(sys.executable),'numpy_version':np.__version__,
                 'no_retry':True,'checkpoint_restore':False,'extra_capture':False,'operator_replay':False,'repair_confirmation':False}
        for name,value in [('EXECUTION_IDENTITY.json',binding),('PLAN.json',plan),('PANEL.json',{'inputs':panel}),('REFERENCES.json',refs),('LOCAL_PATHS.json',local),('ATTEMPTS.json',[]),
                           ('A0.json',{'status':'HISTORICAL_RAW_RETRIEVED_AND_ENDPOINTS_RECONSTRUCTED','requests':0,'source_commit':s.PANEL_COMMIT,'cases':a0,'operator_location':None,'earliest_numerical_divergence':'NOT_LOCALIZED; raw files and response traces retained; endpoint divergence does not identify an operator'})]:
            save(bundle/name,value)
        (bundle/'REQUESTS.jsonl').write_bytes(b'')
        save(bundle/'A0_MANIFEST.json',manifest)
        s.need(main_pins()==before,'main evidence changed during preparation')
        for name in ('EXECUTION_IDENTITY.json','PLAN.json','PANEL.json','REFERENCES.json','A0.json','A0_MANIFEST.json'):
            dest=EVIDENCE/'diagnostic'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(bundle/name,dest)
        print(json.dumps({'status':'PREPARED_NOT_EXECUTED','A0':3,'native_requests':0,'bundle':str(bundle)}),flush=True)

def expected_vectors(raw, slot):
    expected={'target/initial.f32':raw['endpoint']['ids'][0]}
    if slot['draft_enabled']:
        for c in raw['cycles']:
            expected.update({f"draft/proposal-{c['cycle']}-{j}.f32":t for j,t in enumerate(c['proposals'])})
            expected.update({f"target/verify-{c['cycle']}-{j}.f32":t for j,t in enumerate(c['decisions'])})
    else:
        expected.update({f'target/ordinary-{j}.f32':t for j,t in enumerate(raw['endpoint']['ids'][1:],1)})
    return expected

def geometry(raw, slot):
    result=[]
    prefix='hs_attn_query_batch-' if slot['scope']=='QB' else 'hs_attention_q-'
    for g in raw['geometry']:
        if g['name'].startswith(prefix):result.append(g)
        elif slot['scope']=='QB' and g['name'].startswith('kq-') and g['op']=='MUL_MAT' and len(g['sources'])==2:
            q=g['sources'][1]
            if q.get('name')=='jsa_llama_query_batch-'+g['name'][3:]:result.append(q)
    return result

def validate_request(bundle, raw_path, slot, binding, vectors=True):
    raw=s.read(raw_path);item=s.read(bundle/'PANEL.json')['inputs'][slot['source_index']]
    model=s.read(DESIGN/'MODEL_PINS.json')['families']['Llama'];plan=s.read(bundle/'PLAN.json')
    s.need(raw['slot']==slot and raw['identity']==binding['families']['Llama'],'native slot/identity mismatch')
    s.need(raw['prompt_ids']==item['prompt_ids'] and raw['prompt_ids_sha256']==slot['prompt_ids_sha256'],'prompt mismatch')
    s.need(raw['lifecycle']=='fresh' and raw['context_teardown_completed'] and raw['context_scope_fixed'],'fresh fixed context contract')
    s.need(raw['producer']==slot['producer'] and raw['draft_producer']=='NATIVE','producer recipe differs')
    s.need(raw['context']=={**plan['context'],'target_ub':slot['target_ub'],'target_outputs':slot['target_outputs']},'context differs')
    s.need(raw['observed_scope']==slot['scope'] and raw['draft_enabled']==slot['draft_enabled'],'scope/draft differs')
    s.endpoint(raw['endpoint'],model)
    row={**slot,**raw};s.validate_cycles(row,item,model)
    prefill=item['prompt_tokens'] if slot['producer']=='P1' else 1
    generation=len(raw['cycles']) if slot['draft_enabled'] else raw['endpoint']['length']-1
    s.need(raw['target_calls']==prefill+generation,'target producer call count differs')
    s.need(raw['draft_calls']==(1+4*len(raw['cycles']) if slot['draft_enabled'] else 0),'draft caller recipe differs')
    pins=[]
    if slot['observer']=='heavy':
        s.need(raw['capture'] and raw['geometry'] and raw['physical_widths'],'heavy observations absent')
        if slot['scope']=='R':s.need(set(raw['physical_widths'])=={1},'strict R physical width differs')
        else:
            gs=geometry(raw,slot)
            s.need({int(g['name'].rsplit('-',1)[1]) for g in gs}==set(range(32)),'Llama 32-layer geometry missing')
            s.need(all(g['ne'][0]==128 and g['ne'][1]==1 and g['ne'][2]==32 and len(g['nb'])==4 and all(v>0 for v in g['nb']) and '5070' in g['device'] for g in gs),'Llama observed shape/stride/device differs')
            if slot['scope']=='PQ':s.need(all(g['ne'][3]==1 for g in gs),'PQ query width differs')
            if slot['scope']=='QB' and raw['cycles']:s.need(any(g['ne'][3]==4 for g in gs),'QB four-row evidence missing')
        expected=expected_vectors(raw,slot);folder=raw_path.with_suffix('')
        files={p.relative_to(folder).as_posix():p for p in folder.rglob('*.f32')}
        s.need(set(files)==set(expected),'decision-vector inventory differs')
        for name,path in files.items():
            s.need(path.stat().st_size==model['vocabulary_tokens']*4,'incomplete full-vocabulary vector')
            if vectors:
                values=np.fromfile(path,dtype='<f4')
                s.need(np.isfinite(values).all() and int(values.argmax())==expected[name],'vector not finite or greedy decision differs')
            pins.append({**pin(bundle,path),'name':name,'dtype':'float32'})
    else:
        s.need(not raw['capture'] and not list(raw_path.with_suffix('').rglob('*.f32')),'unexpected heavy capture')
    reference=s.read(bundle/'REFERENCES.json')[str(slot['source_index'])]['R']
    return {**slot,'status':'COMPLETE','started':True,'diagnostic_only':True,'performance_eligible':False,
            'raw_native_record':pin(bundle,raw_path),'raw_vectors':pins,
            'historical_R_match':raw['endpoint']==reference,
            'request_start_utc':raw['request_start_utc'],'request_end_utc':raw['request_end_utc']}

def run(bundle, unit):
    binding=validate_binding(bundle);registered=slots();planned=[x for x in registered if x['unit_id']==unit]
    s.need(sha(sys.executable)==binding['host_python_sha256'] and np.__version__==binding['numpy_version'],'host auditor runtime differs')
    s.need(planned and unit in ('diagnostic_A1/Llama','diagnostic_A2/Llama'),'unregistered unit')
    attempts=s.read(bundle/'ATTEMPTS.json');s.need(not any(a['unit_id']==unit for a in attempts),'unit already attempted; no retry')
    if unit=='diagnostic_A2/Llama':s.need(len(attempts)==1 and attempts[0]['status']=='COMPLETE','A1 incomplete')
    limit=binding['caps']['A1_seconds' if 'A1' in unit else 'A2_seconds']
    spent=sum((s.utc(a['process_end_utc'])-s.utc(a['process_start_utc'])).total_seconds() for a in attempts)
    s.need(spent+limit<=binding['caps']['total_owned_seconds'],'diagnostic owned-time cap')
    with exclusive(unit,limit) as deadline:
        s.need(main_pins()==binding['main_checkpoint'],'main checkpoint changed')
        gpu,driver,used=host.current_gpu();ident=binding['families']['Llama']
        s.need(gpu==ident['device_id'] and driver==ident['driver'] and socket.gethostname()==ident['host_id'] and int(used)<1024,'GPU identity/admission differs')
        check_room(bundle,binding['caps']['minimum_free_bytes'])
        local=s.read(bundle/'LOCAL_PATHS.json');exe=Path(local['executable'])
        s.need(sha(exe)==ident['executable_sha256'] and sha(exe.parent.parent/'core/src/libllama.a')==ident['core_sha256'] and sha(exe.parent.parent/'BUILD.json')==ident['build_receipt_sha256'],'native build mismatch')
        root=bundle/'attempts'/unit.replace('/','-');root.mkdir(parents=True,exist_ok=False)
        save(root/'SLOTS.json',planned)
        command=[str(exe),str(root/'native'),local['target'],local['draft'],str(bundle/'PANEL.json'),str(root/'SLOTS.json'),'Llama',str(bundle/'EXECUTION_IDENTITY.json'),str(bundle/'PLAN.json')]
        receipt={'unit_id':unit,'attempt_index':0,'status':'STARTED','process_start_utc':now().isoformat(),'argv':command,'cleanup_verified':False}
        attempts.append(receipt);save(bundle/'ATTEMPTS.json',attempts)
        events=queue.Queue();rows=[];process=None;start=time.monotonic()
        existing=sum(p.stat().st_size for p in bundle.rglob('*') if p.is_file())
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
        try:
            with (root/'stdout.log').open('x',encoding='utf-8') as log,(root/'stderr.log').open('xb') as err:
                process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env,creationflags=subprocess.CREATE_NO_WINDOW)
                receipt['pid']=process.pid;save(root/'PROCESS.json',receipt)
                def consume():
                    for line in process.stdout:
                        log.write(line);log.flush()
                        try:events.put(json.loads(line))
                        except ValueError:events.put({'event':'BAD_STDOUT'})
                    events.put({'event':'EOF'})
                reader=threading.Thread(target=consume,daemon=True);reader.start()
                while True:
                    s.need(time.monotonic()-start<limit and now()<deadline,'owned timeout or formal-priority deadline')
                    check_room(bundle,binding['caps']['minimum_free_bytes'])
                    s.need(existing<=binding['caps']['payload_bytes'],'diagnostic payload cap')
                    try:event=events.get(timeout=1)
                    except queue.Empty:continue
                    if event['event']=='EOF':break
                    if event['event']=='POOLS_READY':
                        p=s.read(root/'native/PROVISIONED.json')
                        s.need(p['requests']==[] and p['pid']==process.pid and p['memory_after_provisioning']['free_bytes']>=binding['caps']['post_model_load_free_bytes'],'model-load memory admission failed')
                        process.stdin.write('RUN\n');process.stdin.flush();continue
                    s.need(event['event']=='REQUEST_COMPLETED' and len(rows)<len(planned),'unexpected native event')
                    slot=planned[len(rows)];s.need(event['slot_id']==slot['slot_id'],'native order differs')
                    raw_path=root/'native'/(slot['slot_id']+'.json')
                    row=validate_request(bundle,raw_path,slot,binding)
                    rows.append(row);existing+=row['raw_native_record']['bytes']+sum(p['bytes'] for p in row['raw_vectors'])
                    s.save_lines(root/'REQUESTS.jsonl',rows)
                    print(json.dumps({'completed':len(rows),'unit':unit,'historical_R_match':row['historical_R_match']}),flush=True)
                    process.stdin.write('CONTINUE\n');process.stdin.flush()
                receipt['exit_code']=process.wait(timeout=30);reader.join(timeout=5)
                native=s.read(root/'native/result.json')
                s.need(receipt['exit_code']==0 and native['normal_cleanup_returned'] and len(rows)==len(planned),'native diagnostic incomplete')
                receipt['status']='COMPLETE'
        except BaseException as exc:
            receipt['status']='FAILED_NO_RETRY';receipt['reason']=str(exc)
        finally:
            if process and process.poll() is None:
                try:process.stdin.close();process.wait(timeout=30)
                except (OSError,subprocess.TimeoutExpired):process.kill();process.wait(timeout=30)
            receipt['cleanup_verified']=process is None or process.poll() is not None
            receipt['process_end_utc']=now().isoformat()
            if process:receipt['exit_code']=process.returncode
            active=s.read(root/'native/ACTIVE_SLOT.json') if (root/'native/ACTIVE_SLOT.json').exists() else None
            for slot in planned[len(rows):]:
                rows.append({**slot,'status':'STARTED_UNCOMPLETED' if active and active['slot_id']==slot['slot_id'] else 'NOT_RUN',
                             'started':bool(active and active['slot_id']==slot['slot_id']),'reason':receipt.get('reason'),'diagnostic_only':True,'performance_eligible':False})
            s.save_lines(root/'REQUESTS.jsonl',rows)
            prior=s.lines(bundle/'REQUESTS.jsonl');s.save_lines(bundle/'REQUESTS.jsonl',prior+rows)
            save(root/'PROCESS.json',receipt);save(bundle/'ATTEMPTS.json',attempts)
        s.need(main_pins()==binding['main_checkpoint'],'main stream changed during diagnostic')
        print(json.dumps(receipt),flush=True)
        s.need(receipt['status']=='COMPLETE','diagnostic stopped; no retry')

def audit(bundle):
    binding=validate_binding(bundle)
    with exclusive('diagnostic-audit',900):
        rows=s.lines(bundle/'REQUESTS.jsonl');planned=slots();attempts=s.read(bundle/'ATTEMPTS.json')
        s.need([r['slot_id'] for r in rows]==[r['slot_id'] for r in planned],'full diagnostic denominator incomplete')
        s.need(len(attempts)==2 and all(a['status']=='COMPLETE' and a['cleanup_verified'] for a in attempts),'attempts incomplete')
        groups=defaultdict(dict);checked=[]
        for row,slot in zip(rows,planned):
            raw_path=s.payload(bundle,row['raw_native_record'])
            fresh=validate_request(bundle,raw_path,slot,binding)
            s.need(fresh==row,'diagnostic normalized evidence differs')
            raw=s.read(raw_path);a=next(a for a in attempts if a['unit_id']==slot['unit_id'])
            s.need(s.utc(binding['frozen_utc'])<s.utc(a['process_start_utc'])<=s.utc(raw['request_start_utc'])<s.utc(raw['request_end_utc'])<=s.utc(a['process_end_utc']),'diagnostic timestamp bounds')
            groups[(slot['stage'],slot['source_index'],slot['producer'],slot['observer'])][slot['arm']]=(row,raw)
            checked.append(row)
        comparisons=[];sentinels=[]
        for (stage,index,producer,observer),arms in groups.items():
            pq,qb=arms['C_PQ'],arms['C_QB'];fields=('endpoint','cycles','target_final_kv','draft_final_kv')
            record={'stage':stage,'source_index':index,'producer':producer,'observer':observer,
                    'PQ_QB_equal':{k:pq[1][k]==qb[1][k] for k in fields},
                    'PQ_QB_complete_vector_bytes_equal':({v['name']:(v['bytes'],v['sha256']) for v in pq[0]['raw_vectors']}=={v['name']:(v['bytes'],v['sha256']) for v in qb[0]['raw_vectors']}) if observer=='heavy' else None,
                    'historical_R_match':{arm:r[0]['historical_R_match'] for arm,r in arms.items()}}
            if stage=='diagnostic_A1':
                record['new_R_match']={arm:r[1]['endpoint']==arms['R'][1]['endpoint'] for arm,r in arms.items()}
                record['outcome']=('RUNTIME_REFERENCE_CHANGED' if not arms['R'][0]['historical_R_match'] else
                                   'COUNTEREXAMPLE_REPRODUCED' if not record['new_R_match']['C_PQ'] or not record['new_R_match']['C_QB'] else
                                   'RUNTIME_DEPENDENT_COUNTEREXAMPLE' if index==8 else 'CONTROL_MATCH')
            else:record['interpretation']='BUNDLED_PRODUCER_CONSUMER_RECIPE_ONLY; no imported common state'
            comparisons.append(record)
            if observer=='off':
                heavy=groups[(stage,index,producer,'heavy')]
                sentinels.append({'stage':stage,'source_index':index,'producer':producer,'equal':{arm:all(r[1][k]==heavy[arm][1][k] for k in fields) for arm,r in arms.items()}})
        report={'status':'COMPLETE_DIAGNOSTIC_AUDITED','executed':54,'A1':18,'A2':36,'new_A0_requests':0,'performance_eligible':False,
                'audit_utc':now().isoformat(),'comparisons':comparisons,'observer_pairs':sentinels,'operator_location':None,
                'interpretation':'Observed counterexamples or disappearances are outcomes, not repairs. No additional experiment is authorized.',
                'main_checkpoint_unchanged':main_pins()==binding['main_checkpoint'],'raw_vectors':sum(len(r['raw_vectors']) for r in rows)}
        s.need(report['main_checkpoint_unchanged'],'main evidence changed')
        save(bundle/'AUDIT.json',report)
        print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','audit']);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--unit');a=p.parse_args()
    if a.action=='prepare':prepare(a.bundle.resolve())
    elif a.action=='run':run(a.bundle.resolve(),a.unit)
    else:audit(a.bundle.resolve())
