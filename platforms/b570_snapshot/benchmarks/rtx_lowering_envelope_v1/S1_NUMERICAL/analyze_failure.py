"""CPU audit of a terminal numerical start, preserving every planned slot."""
import argparse,base64,collections,hashlib,json,struct
from pathlib import Path

def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def analyze(root):
    plan=load(root/'provenance/S1_PLAN.json');approval=load(root/'registration/S1_NUMERICAL_AUTHOR_APPROVAL.json')
    f0=load(root/'registration/S1_F0.json');selected=load(root/'support/PREOUTPUT_SELECTION.json')
    slots=[s for s in plan['slots'] if s['kind']=='numeric'];assert len(slots)==720
    assert approval['stage']=='S1B_EXACT_SLOTS' and approval['slot_ids']==[s['id'] for s in slots]
    assert approval['approved_F0_sha256']==sha(root/'registration/S1_F0.json')
    assert hashlib.sha256(approval['author_message'].encode()).hexdigest()==approval['author_message_sha256']
    assert selected['selected_QH']=='QH_C'
    auth=load(root/'support/AUTHENTICATED_SELECTION.json')
    assert auth['authenticated_commit']==approval['selected_census_commit'] and auth['selection_sha256']==sha(root/'support/PREOUTPUT_SELECTION.json')
    expected_dirs={hashlib.sha256(s['id'].encode()).hexdigest()[:24] for s in slots}
    actual_dirs={p.name for p in (root/'slots').iterdir() if p.is_dir()};assert actual_dirs<=expected_dirs
    statuses=[];started=failed=completed=graph_started=graph_completed=0;seconds=0;admissions=0
    for s in slots:
        directory=root/'slots'/hashlib.sha256(s['id'].encode()).hexdigest()[:24]
        row=dict(slot=s['id'],descriptor=s['descriptor'],layout=s['layout'],repeat=s['repeat'],status='NOT_STARTED_PROTOCOL_STOP',pid=None,exit_code=None,graph_starts=0,completed_graphs=None,numerical_outputs=None)
        if directory.exists():
            before=load(directory/'BEFORE_START.json');job=load(directory/'ADMITTED_JOB.json');process=load(directory/'PROCESS.json');life=load(directory/'LIFETIME.json')
            assert before['slot']==s['id'] and before['reserved_graphs']==1 and before['warmups']==0
            assert before['wire_job_sha256']==sha(directory/'ADMITTED_JOB.json')
            assert all(job[k]==v for k,v in s.items()) and job['approved_stage_F0']==approval['approved_F0_sha256']
            admission=load(directory/'HOST_ADMISSION.json');admissions+=1
            assert admission['AC']==1 and admission['util']<=5 and admission['temp']<=55
            assert (admission['gpu'],admission['driver'],admission['total_MiB'])==(f0['admission_policy']['gpu'],f0['admission_policy']['driver'],f0['admission_policy']['total_MiB'])
            assert admission['total_MiB']-admission['used_MiB']>=512
            markers=sorted((directory/'native').glob('GRAPH_STARTED_*.json'));graph_started+=len(markers)
            assert [load(p) for p in markers]==[dict(index=0,warmup=False)]
            started+=1;seconds+=life['seconds']
            assert (directory/'FAILED.json').exists() and not (directory/'COMPLETED.json').exists()
            assert load(directory/'FAILED.json')['started_no_retry'] is True
            assert life['exit_code']==0xc0000094
            assert not (directory/'native/RECORD.json').exists() and not list(directory.rglob('*.bin'))
            row.update(status='STARTED_FAILED_NATIVE_EXCEPTION',pid=process['pid'],exit_code=hex(life['exit_code']),graph_starts=len(markers),completed_graphs=0)
            failed+=1
        statuses.append(row)
    assert started==failed==1 and completed==graph_completed==0 and graph_started==1
    assert statuses[0]['status']=='STARTED_FAILED_NATIVE_EXCEPTION' and all(s['status']=='NOT_STARTED_PROTOCOL_STOP' for s in statuses[1:])
    controller=load(root/'control/CONTROLLER_ENDED.json');assert controller['exit_code']==1
    capsule=load(root/'diagnostics/EXCEPTION_CAPSULE.json');crash=load(root/'diagnostics/OFFLINE_CRASH.json')
    exception=base64.b64decode(capsule['exception_stream_b64']);context=base64.b64decode(capsule['thread_context_b64'])
    thread,=struct.unpack_from('<I',exception,0);code,=struct.unpack_from('<I',exception,8);address,=struct.unpack_from('<Q',exception,24)
    rcx,=struct.unpack_from('<Q',context,128);rip,=struct.unpack_from('<Q',context,248)
    assert code==0xc0000094 and rcx==0 and rip==address
    assert capsule['source_dump_sha256']==crash['dump']['sha256']
    module=capsule['fault_module'];relative=address-module['base'];assert relative==0x1cf7
    code_bytes=base64.b64decode(capsule['code_context_b64']);fault_offset=relative-capsule['code_context_start_RVA']
    assert code_bytes[fault_offset:fault_offset+3]==b'\x48\xf7\xf9','x64 IDIV RCX'
    assert code_bytes.hex()==crash['instruction_context']['disk_hex']==crash['instruction_context']['dump_hex']
    k=code_bytes.index(b'\x48\x8b\x0d');disp=struct.unpack_from('<i',code_bytes,k+3)[0]
    assert capsule['code_context_start_RVA']+k+7+disp==capsule['frequency_global_RVA']==0xc0358
    frequency,=struct.unpack('<q',base64.b64decode(capsule['frequency_bytes_b64']));assert frequency==0
    nearest=[e for e in crash['nearest_preceding_export_symbols'] if int(e['RVA'],16)<=relative][-1]
    assert nearest==dict(RVA='0x1cc0',name='ggml_time_us')
    assert crash['fault_module_disk_sha256']==f0['numerical_DLLs']['ggml-base.dll']
    source=(root/'source/native113.cpp').read_text(encoding='utf-8')
    assert 'ggml_time_init(' not in source
    assert 'ggml_init(' in source
    link=(root/'source/build.ninja').read_text(encoding='utf-8')
    assert 'ggml/src/ggml-base.a' in link
    census_life=load(root/'support/LIFETIME.json')
    return dict(status='PROTOCOL_STOP_NATIVE_INFRASTRUCTURE_FAILURE',planned_numeric_slots=720,numeric_hosts_started=started,numeric_hosts_completed=completed,
                numeric_hosts_failed=failed,not_started_due_to_protocol_stop=719,missing_unexplained_slots=0,scientific_retries=0,
                numeric_graph_starts=graph_started,confirmed_completed_graphs=graph_completed,graph_budget_charge=1,warmups=0,model_requests=0,
                readiness_queries_this_substage=admissions,native_owned_seconds_this_substage=seconds,controller_wall_seconds_this_substage=controller['elapsed_seconds'],
                S1_total_host_starts=2,S1_total_graph_start_charge=1,S1_total_native_owned_seconds=census_life['seconds']+seconds,
                exception=dict(code=hex(code),module=module['path'],RVA=hex(relative),function='ggml_time_us+0x37',instruction='IDIV RCX',RCX=0,timer_frequency_global_RVA=hex(capsule['frequency_global_RVA']),timer_frequency=frequency,thread_id=thread),
                diagnosis='Pinned ggml-base DLL Windows timer frequency is zero at first graph compute. Host links a separate static ggml-base and initializes its context. Dual-core timer state is the source/linkage explanation; no repaired binary has been built or tested.',
                placements='Pre-compute placement guards were traversed by source control flow, but no successful full native RECORD exists; executed operator/stream placement and actual kernel counts remain unqualified.',
                module_identity='Post-exit disk SHA and bounded fault-code bytes match F0. Complete crash module metadata retained; no successful native runtime SHA receipt or continuous residency claim.',
                numerical_qualification='NOT_OBSERVED_NO_STAGE_BYTES',full_request_qualification='NOT_EXECUTED',cost='NOT_QUALIFIED',selected_QH='QH_C_UNCHANGED_NOT_EXECUTED',
                next_gate='Current numerical execution is terminal; no scientific retry or resuming remaining slots under this F0. Any independent engineering revision/protocol amendment needs prospective scope, freeze and author authorization.',
                slots=statuses)

def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=analyze(Path(a.raw))
    with Path(a.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='slots'}))
if __name__=='__main__':main()
