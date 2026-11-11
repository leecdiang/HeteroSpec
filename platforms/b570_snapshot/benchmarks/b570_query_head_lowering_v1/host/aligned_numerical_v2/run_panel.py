"""Only GPU entry point; exact new F0 approval is mandatory before any launch."""
import argparse
import datetime
import itertools
import os
import pathlib
import struct
import subprocess
import sys
from panel_common import HERE,ROOT,RUN,RUN_ID,MODES,LIMITS,need,load,save,sha,digest,serialize,modules
from controller import launch,output_usage,events
from native_audit import audit_raw
from analyzer import analyze_files,compare

def admission(approved):
    path=HERE/'F0.json';need(approved==sha(path),'explicit author approval of exact new F0 required')
    f0=load(path);need(f0['run_id']==RUN_ID and f0['limits']==LIMITS,'fixed panel identity and ceilings')
    need(sha(HERE/'EXECUTION_BINDING.json')==f0['execution_binding_sha256'],'execution binding identity')
    for name,h in f0['sources'].items():need(sha(ROOT/name)==h,'source drift '+name)
    for x in [f0['executable'],f0['python']]+f0['dependencies']+f0['driver_files']:
        need(sha(x['path'])==x['sha256'],'runtime/driver drift '+x['path'])
    env={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
    need(env==f0['environment'],'backend environment drift')
    for name,h in f0['artifacts'].items():need(sha(HERE/name)==h,'frozen plan/wire/reference artifact drift '+name)
    for x in f0['history_files']:need(sha(ROOT/x['path'])==x['sha256'],'historical evidence drift')
    build=load(HERE/'BUILD_INPUTS.json')
    for x in build['files']+build['frozen_backend_sources']:need(sha(x['path'])==x['sha256'],'frozen build/source identity drift')
    inputs=load(HERE/'INPUTS.json');plan=load(HERE/'PLAN.json');wires=load(HERE/'WIRES.json')
    need(len(plan['slots'])==161 and len(wires)==161 and len(inputs)==16,'fixed complete inventories')
    for x in inputs:need(sha(x['path'])==x['sha256'],'logical input drift')
    for s,w in zip(plan['slots'],wires):
        b=serialize(s,inputs,f0['execution_binding_sha256'])
        need(w['slot_id']==s['id'] and (HERE/w['path']).read_bytes()==b and sha(HERE/w['path'])==w['sha256'],'exact serializer/wire drift')
    need(not RUN.exists(),'existing run or attempt record; never resume/retry')
    return f0,inputs,plan,wires

def load_reference(input_id):
    record=load(HERE/'REFERENCE_MANIFEST.json')['inputs'][input_id];result={}
    for stage,entry in record['stages'].items():
        b=(HERE/entry['path']).read_bytes();need(sha(HERE/entry['path'])==entry['sha256'],'reference bytes drift')
        result[stage]=[x[0] for x in struct.iter_unpack('<d',b)]
    return result

def preflight_processes():
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
        'Get-Process | Select-Object Id,ProcessName,Path | ConvertTo-Json -Depth 2 -Compress'],capture_output=True,text=True,timeout=20)
    need(p.returncode==0,'OS process inventory unavailable')
    import json
    rows=json.loads(p.stdout)
    names=('python','llama','b570','qh-vulkan','aligned-host','alignment-diagnostic','ollama','llmster','lmstudio','comfy','blender','furmark','occt','vulkaninfo','benchmark')
    conflicts=[r for r in rows if r['Id']!=os.getpid() and any(n in r['ProcessName'].lower() for n in names)]
    need(not conflicts,'potential conflicting compute/benchmark process; no GPU launch')
    return dict(OS_processes=rows,conflicts=conflicts,scope='OS inventory only, no device query or GPU utilization probe')

def main():
    p=argparse.ArgumentParser();p.add_argument('--author-approved-f0-sha',required=True);a=p.parse_args()
    before=modules();f0,inputs,plan,wires=admission(a.author_approved_f0_sha)
    processes=preflight_processes();RUN.mkdir(parents=True,exist_ok=False);save(RUN/'PREFLIGHT.json',processes)
    save(RUN/'AUTHORIZATION.json',dict(approved_F0_sha256=a.author_approved_f0_sha,execution_binding_sha256=f0['execution_binding_sha256'],
         mechanism='Exact SHA CLI entry; human confirmation must precede invoking this entry',run_id=RUN_ID))
    expected=load(HERE/'EXPECTED_GRAPHS.json');input_by_id={x['id']:x for x in inputs}
    ledger=(RUN/'LEDGER.jsonl').open('x',encoding='utf-8');started=[];audited=[];owned=0.;error=None
    normalized={};identities={};references={};common={};census_complete=False
    def record(event,**data):
        import json
        ledger.write(json.dumps(dict(event=event,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**data),allow_nan=False)+'\n');ledger.flush()
    try:
        for slot,w in zip(plan['slots'],wires):
            need(census_complete or slot['kind']=='census','census before numerical work')
            if slot.get('q',1)>1:need(len([s for s in audited if s['index'] in range(1,41)])==40,'all40 q1 controls before q>1')
            wire_bytes=serialize(slot,inputs,f0['execution_binding_sha256'])
            need((HERE/w['path']).read_bytes()==wire_bytes and sha(HERE/w['path'])==w['sha256'],'wire changed before attempt')
            need(sha(f0['executable']['path'])==f0['executable']['sha256'],'host changed')
            if slot['kind']=='graph':need(sha(input_by_id[slot['input_id']]['path'])==input_by_id[slot['input_id']]['sha256'],'input changed before attempt')
            actual,reserve=output_usage();need(actual+reserve<=LIMITS['output_bytes'] and owned<LIMITS['owned_seconds'],'pre-attempt remaining budget')
            request=__import__('json').loads(wire_bytes);started.append(slot['id']);record('ATTEMPT',slot=slot,wire_sha256=w['sha256'])
            raw,life=launch(slot,request,wire_bytes,f0,owned);owned+=life['owned_wall_s']
            native=audit_raw(raw,request,life['pid'],expected);folder=RUN/slot['id'];save(folder/'NATIVE_AUDIT.json',native)
            if slot['kind']=='census':
                save(RUN/'CENSUS.json',native);census_complete=True
                record('CENSUS_ADMITTED',fixed_primary_candidate='QH_C',full_graphs=80)
            else:
                item=input_by_id[slot['input_id']];data=pathlib.Path(item['path']).read_bytes()
                need(sha(item['path'])==item['sha256'],'input changed after native return')
                if item['id'] not in references:references[item['id']]=load_reference(item['id'])
                analysis,vectors=analyze_files(request,native['graph'],folder,data,references[item['id']])
                analysis['physical_costs']={k:v for k,v in native.items() if k.startswith('PQ_extra')}
                save(folder/'ANALYSIS.json',analysis)
                ident=(life['pid'],life['creation_FILETIME']);key=(slot['input_id'],slot['mode'])
                if slot['repeat']==1:
                    need(key in normalized and ident!=identities[key],'independent new process repetition')
                    relation=compare(vectors,normalized[key]);record('INDEPENDENT_REPEAT',slot=slot['id'],relation=relation)
                    need(relation['all_stages_bitwise_equal'],'same implementation independent repetition differs')
                else:normalized[key]=vectors;identities[key]=ident
                if slot['q']==1:
                    if slot['input_id'] not in common:common[slot['input_id']]=vectors
                    relation=compare(vectors,common[slot['input_id']]);record('Q1_COMMON_PATH',slot=slot['id'],relation=relation)
                    need(relation['all_stages_bitwise_equal'],'q1 common path mismatch')
                # Freeze all ten pair comparisons at each repeat, without using
                # their numerical values to select a representation or tolerance.
                for other in MODES:
                    otherkey=(slot['input_id'],other,slot['repeat'])
                    if otherkey in normalized:
                        record('FINITE_CROSS_REPRESENTATION',left=slot['id'],other_mode=other,repeat=slot['repeat'],relation=compare(vectors,normalized[otherkey]))
                normalized[slot['input_id'],slot['mode'],slot['repeat']]=vectors
            audited.append(dict(id=slot['id'],index=slot['index'],kind=slot['kind']));record('AUDIT_COMPLETE',slot=slot['id'],owned_wall_s=life['owned_wall_s'])
        for name,h in f0['sources'].items():need(sha(ROOT/name)==h,'source drift at close')
    except Exception as e:error=str(e);record('STOP',error=error)
    finally:
        owned=sum(load(p)['owned_wall_s'] for p in RUN.glob('*/LIFECYCLE.json'))
        actual,reserve=output_usage();record('CLOSE',owned_wall_s=owned)
        ledger.close();audit_ids={x['id'] for x in audited}
        save(RUN/'CLOSEOUT.json',dict(status='PANEL_COMPLETE_PENDING_INDEPENDENT_RECONSTRUCTION' if error is None and len(audited)==161 else 'STOPPED_INCOMPLETE',
            error=error,attempts=len(started),started=started,audited=audited,failed_or_invalid=[s for s in started if s not in audit_ids],
            unstarted=[s['id'] for s in plan['slots'] if s['id'] not in started],owned_wall_s=owned,
            output_bytes_before_closeout=actual,archive_reserve_bytes=reserve,primary_candidate='QH_C',model_requests=0,retries=0,warmups=0,
            automatic_S2_S3=False,modules_before=before,modules_after=modules()))
    if error:raise SystemExit(error)

if __name__=='__main__':main()
