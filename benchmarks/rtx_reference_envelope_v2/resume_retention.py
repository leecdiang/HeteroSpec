"""CPU-only retention repair;resume ONLY never-started original T1 coordinates.

Native binary,math,inputs,order,calls and clock boundaries are unchanged.
Block4 is excluded from cost aggregates prospectively due the acquisition pause.
No completed GPU coordinate is repeated;no replacement block is collected.
"""
import datetime,itertools,json,os,random,time
from pathlib import Path
from common import V,load,save,sha
from run import root,guard,telemetry,quiet,runtime_locks,invoke,dedup,git,now
def audit_native(folder):
    j=load(folder/'JOB.json');r=load(folder/'native/RECORD.json');assert r['status']=='QUALIFIED';assert r['input_after_equal'] and r['host_input_unchanged'];assert len(r['calls'])==38
    ref=Path(j['context']['references'][j['layout']]['path']).read_bytes()
    for c in r['calls']:assert (folder/'native'/f'ordinary_{c["index"]}.bin').read_bytes()==ref and c['compute_status']==c['sync_status']==0
    for role in ['Q','K','V','mask']:
        b=(Path(j['context']['root'])/j['context']['metadata'][role]['file']).read_bytes()
        for phase in ['before','after']:assert (folder/'native'/f'input_{role}_{phase}.bin').read_bytes()==b
    assert not load(folder/'host.JOB_EVENTS.json')['errors'];assert load(folder/'host.LIFETIME.json')['exit_code']==0
    return r
def prepare():
    raw=root();freeze=load(raw/'T1_FREEZE.json');assert not (raw/'WORKER.lock').exists();missing=[p for p in (raw/'attempts').iterdir() if not (p/'ENDED.json').exists()];assert len(missing)==1
    folder=missing[0];r=audit_native(folder);save(raw/'T1_RETENTION_ERROR.json',dict(recorded_utc=now(),failure='NTFS maximum hardlinks;WinError1142',attempt=folder.name,GPU_record_status=r['status'],all38outputs_exact=True,native_binary_unchanged=sha(V/'build/native.exe')==freeze['files']['native.exe'],GPU_calls_repeated=0,original_failure_preserved=True))
    save(raw/'T1_BLOCK_4_INVALIDATION.json',dict(reason='post-exit CPU retention failure interrupted acquisition;exclude entire block from timing aggregate before inspecting costs',numerical_results_retained=True,GPU_retry=False,already_completed_native_attempt=folder.name))
    # Exercise actual Windows hardlink ceiling and byte-preserving fallback.
    test=raw/'CPU_HARDLINK_LIMIT';test.mkdir();data=b'cpu_retention_regression'
    for i in range(1100):(test/f'{i:04d}.bin').write_bytes(data)
    dedup(test);assert all(p.read_bytes()==data for p in test.glob('*.bin'))
    save(V/'CPU_RETENTION_TEST.json',dict(status='PASS',actual_Windows_occurrences=1100,all_exact=True,NTFS_cap_fallback='retain ordinary files unchanged',GPU_calls=0))
    dedup(folder/'native');start=load(folder/'START.json');j=load(folder/'JOB.json');life=load(folder/'host.LIFETIME.json')
    ended=dict(start,end_utc=now(),wall_seconds=None,native_lifetime_seconds=life['seconds'],exit=0,error='post-exit dedup failed;CPU reverified all bytes,original native execution retained',native_status='QUALIFIED',actual_calls=38,eligible=True,CPU_reconstructed_postprocessing=True);save(folder/'ENDED.json',ended)
    with (raw/'ATTEMPTS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(ended,separators=(',',':'))+'\n')
    save(raw/'T1_RETENTION_AMENDMENT.json',dict(old_run_py_sha256=freeze['files']['run.py'],new_run_py_sha256=sha(V/'run.py'),native_sha256=sha(V/'build/native.exe'),change='post-exit hardlink1142 fallback+exact CPU amendment pin',scientific_bytes_timers_and_order_unchanged=True,no_GPU_reexecution=True,block4_timing_excluded=True,old_freeze_preserved=True))
def resume():
    raw=root();spec=load(raw/'RUN_SPEC.json');assert not git('status','--porcelain','--untracked-files=no','--','benchmarks/rtx_reference_envelope_v2');freeze=load(raw/'T1_FREEZE.json');begin=datetime.datetime.fromisoformat(freeze['UTC']).timestamp();assert time.time()-begin<7200
    save(raw/'T1_RETENTION_RESUME_STARTED.json',dict(utc=now(),git=git('rev-parse','HEAD'),CPU_amendment_sha256=sha(raw/'T1_RETENTION_AMENDMENT.json'),original_T1_started=freeze['UTC'],budget_not_reset=True));lock=raw/'WORKER.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        handles=runtime_locks(spec);orders=list(itertools.permutations(['PQ','QB','QH_C']))
        for block in range(6):
            if (raw/f'T1_BLOCK_{block}_ENDED.json').exists():continue
            quiet(spec,str(block)+'/retention-resume')
            if not (raw/f'T1_BLOCK_{block}_STARTED.json').exists():save(raw/f'T1_BLOCK_{block}_STARTED.json',dict(UTC=now(),pid=os.getpid()))
            contexts=spec['contexts'].copy();random.Random(20261018+block).shuffle(contexts)
            existing={(j['context']['id'],j['layout']) for p in (raw/'attempts').glob('*/JOB.json') if (j:=load(p))['stage']=='T1' and j['block']==block}
            for d in contexts:
                for layout in orders[(block+next(i for i,c in enumerate(spec['contexts']) if c['id']==d['id']))%6]:
                    if (d['id'],layout) in existing:continue
                    assert time.time()-begin<7200;guard(spec);r=invoke(spec,'T1',d,layout,'persistent_inputs',8,30,block);assert r['eligible'],'new output/control failure'
                print('T1 resume',block,d['id'],flush=True)
            post=telemetry(spec,f'T1/{block}/post-retention');valid=post.get('quiet',False) and block!=4
            save(raw/f'T1_BLOCK_{block}_ENDED.json',dict(status='COMPLETE' if valid else 'NUMERICALLY_COMPLETE_TIMING_INVALIDATED',environment_qualified=valid,physical_post_environment_quiet=post.get('quiet',False),hosts=72,calls=2736,failed_cells=[],UTC=now(),reason='retention interruption' if block==4 else None))
        save(raw/'T1_ENDED.json',dict(status='NUMERICALLY_COMPLETE_5_TIMING_BLOCKS',hosts=432,calls=16416,seconds=time.time()-begin,block4_excluded_for_CPU_retention_pause=True,all_original_coordinates_once=True))
    finally:lock.unlink()
if __name__=='__main__':
    import sys
    {'prepare':prepare,'resume':resume}[sys.argv[1]]()
