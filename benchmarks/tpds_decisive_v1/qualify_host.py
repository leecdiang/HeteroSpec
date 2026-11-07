"""Token-only independent references and actual-byte candidate qualification."""
from native_adapter import *
from normalize import trace_from_row,normalize
from common import digest,write_new,shared_blob
from active_kv import parse
from qualify import qualify
import re,sys
QUAL=Path('D:/rtx184-qualification')
def blob(root,data):
    h=__import__('hashlib').sha256(data).hexdigest();p=root/'cas'/h[:2]/h;p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():shared_blob(p,data)
    else:assert p.read_bytes()==data
    return dict(path=p.relative_to(root).as_posix(),bytes=len(data),sha256=h)
def main(arm,source_index=0):
    suffix='' if source_index==0 else '-root'+str(source_index)
    case=QUAL/(arm+suffix);case.mkdir(parents=True)
    native=RUNS/('development-v3-'+arm+suffix)/'native';free=ROOT/'bridge-observer-r-01/native/r0' if source_index==0 else RUNS/('observer-r'+suffix)/'native/r0'
    row=json.loads((native/'heavy.json').read_bytes());rfree=json.loads(free.with_suffix('.json').read_bytes());prompt=row['prompt_ids']
    eog=sorted(set(int(x) for x in re.findall(r'print_info: EOG token\s*=\s*(\d+)',(ROOT/'bridge-old-r-01/stderr.log').read_text())))
    derived=[]
    for r in [row,rfree]:r['study_cap']=128;r['study_fallback_count']=0;r['study_reference_received_forced_tape']=False;derived.append(trace_from_row(r,prompt,151936,eog,'rtx')[1])
    assert derived[0]['tokens']==derived[1]['tokens'],'candidate autonomous mismatch'
    producer=dict(caller_lengths=[len(prompt)],last_output_flags=[True])
    profile=json.loads((ROOT/'QWEN_PROFILE.json').read_bytes())
    binding=dict(reference_identity_sha256=sha(OLD/'bin/rtx-scope-transfer.exe'),target_model_sha256=profile['target_model_sha256'],producer_sha256=digest(producer),lifecycle_sha256=digest(dict(original='PR151',capacity=1024,pools=4,resident_reset=True,priming='heavy then off in own process')),input_sha256=digest(prompt),cap=128,vocab=151936,eog_ids=eog,active_kv_bytes_per_token=147456,reference_bridge_passed=True)
    write_new(case/'binding.json',binding);write_new(case/'prompt.json',dict(prompt_ids=prompt));write_new(case/'profile.json',profile)
    for kind,r,root,role in [('candidate',row,native/'heavy/target','candidate'),('free',rfree,free/'target','free_reference')]:
        write_new(case/(kind+'-row.json'),r);normalize('rtx',case/(kind+'-row.json'),root,case/'prompt.json',case/'binding.json',case/'profile.json',role,kind+'-'+arm,case/kind)
    prefixes={tuple(x['prefix']) for d in derived for key in ('states','vector_uses') for x in d[key]};ordered=sorted(prefixes,key=lambda p:(-len(p),p));maximal=[]
    for p in ordered:
        if not any(q[:len(p)]==p for q in maximal):maximal.append(p)
    assigned=set();paths=[]
    for p in maximal:
        positions=[n for n in range(len(prompt),len(p)+1) if p[:n] in prefixes and p[:n] not in assigned]
        positions=sorted(set(positions+[len(prompt)]));assigned.update(p[:n] for n in positions)
        paths.append(dict(suffix=list(p[len(prompt):]),positions=positions))
    assert assigned==prefixes
    exe=ROOT/'forced-v2/bin/worker.exe';native_binding=json.loads((ROOT/'bridge-old-r-01/BINDING.json').read_bytes());native_binding['families']['Qwen']['executable_sha256']=sha(exe)
    job=dict(attempt_id='forced-v2-'+arm+suffix,exe=str(exe),binding=native_binding,forced=dict(no_candidate_payload=True,prompt_ids=prompt,producer=producer,paths=paths),reservation=dict(requests=len(paths),token_rows=sum(len(prompt)+len(p['suffix']) for p in paths),operators=0),timeout_s=1800)
    write_new(case/'forced-job.json',job);print(arm,'independent paths',len(paths),'rows',job['reservation']['token_rows'],flush=True)
    output=execute(job);result=json.loads((output/'native/result.json').read_bytes());bank=case/'bank';bank.mkdir();entries={};duplicate=0
    for path in result['paths']:
        full=prompt+path['suffix']
        for cap in path['captures']:
            count=cap['position'];rawdir=output/'native'/cap['directory'];canonical,scope=parse((rawdir/'sequence.bin').read_bytes(),list(range(count)),profile)
            entry=dict(prefix=full[:count],active_layout_sha256=scope['active_layout_sha256'],frontier=blob(bank,(rawdir/'frontier.f32').read_bytes()),active_kv=blob(bank,canonical));key=digest(entry['prefix'])
            if key in entries:assert entries[key]==entry,'independent history stability mismatch';duplicate+=1
            entries[key]=entry
    capture=dict(role='forced_reference',execution='NATIVE',completed=True,binding={k:v for k,v in binding.items() if k not in ('eog_ids','reference_bridge_passed')},reference_bridge_passed=True,fallback_count=0,invocation_id='forced-v2-'+arm,prefixes=list(entries.values()))
    write_new(bank/'capture.json',capture)
    proof=qualify(case/'candidate/capture.json',case/'free/capture.json',bank/'capture.json')
    off=json.loads((native/'off.json').read_bytes());assert off['endpoint']==row['endpoint']
    last=derived[0]['states'][-1];ref=entries[digest(last['prefix'])];clean=native/'off/target/state/final-clean';can,scope=parse((clean/'sequence.bin').read_bytes(),list(range(len(last['prefix']))),profile)
    assert __import__('hashlib').sha256(can).hexdigest()==ref['active_kv']['sha256'];assert sha(clean/'frontier.f32')==ref['frontier']['sha256']
    proof.update(clean_final_state_and_frontier_match=True,stable_duplicate_prefixes=duplicate,forced_requests=len(paths),scope='One exposed root only; additional development roots and full panel not yet qualified')
    write_new(case/'QUALIFICATION.json',proof);print(arm,'native full-state qualification passed on exposed root',flush=True)
if __name__=='__main__':main(sys.argv[1])
