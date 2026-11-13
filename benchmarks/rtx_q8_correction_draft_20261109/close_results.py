"""Post-GPU cost/ledger/archive closure; no inference entry point."""
from pathlib import Path
import collections,gzip,hashlib,importlib.util,json,os,shutil,sqlite3,sys,time,zipfile
from common import HERE,REPO,RUNTIME,ORIGINAL,AUDIT,OLD,read,put,sha,inherit

DEST=REPO.parent/'q8rtx213-supplement-evidence-20261109'

def collect():
    assert read(RUNTIME/'COMPLETE_QUALIFICATION.json')['passed'];inherit()
    c=sqlite3.connect((RUNTIME/'ledger.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;attempts=[dict(x) for x in c.execute('SELECT * FROM attempts ORDER BY started')];c.close()
    assert len(attempts)==16 and sum(a['requests'] for a in attempts)==37 and sum(a['rows'] for a in attempts)==18543
    plan=read(HERE/'EXECUTION_PLAN.json');details=[];minima={};maxima={};anomalies=[];arm=[];native_requests=0;native_rows=0
    for a,j in zip(attempts,plan['jobs']):
        assert a['id']==j['id'];folder=RUNTIME/'runs'/j['id'];host=read(folder/'HOST.json');meta=read(folder/'native/result.json');assert meta['status']=='COMPLETE' and host['code']==0
        native_requests+=meta['trajectories'];native_rows+=meta['token_rows']
        row=dict(reservation=a,host=host,native_requests=meta['trajectories'],native_rows=meta['token_rows'],model_load_s=meta.get('model_load_s'),pool_setup_s=meta.get('pool_setup_s'))
        if a['status']=='FAILED':
            assert j['id']==plan['jobs'][0]['id'] and read(folder/'RECOVERED_NATIVE_COMPLETE.json')['passed_offline_recheck']
            row['preserved_supervisor_failure']=read(folder/'SUPERVISOR_FAILURE.json');row['recovered_native_completion']=read(folder/'RECOVERED_NATIVE_COMPLETE.json')
        else:assert a['status']=='COMPLETE'
        if j['role']=='candidate':
            r=read(folder/'native/boundary-natural-heavy/receipt.json');check=read(RUNTIME/'checks'/(j['id']+'.json'));row['heavy_request_cost']=r['service_seconds']
            row['phases']=dict(target=r['target_phases'],draft=r['draft_phases'],planning=r['planning_s'],owned_copy=r['output_copy_s'],setup=r['setup_seconds'],teardown=r['teardown_seconds'])
            arm.append(dict(job=j['id'],k=r['k'],cycles=len(r['cycles']),boundary_cycles=len(check['boundary_cycles']),boundary_rejections=sum(x['rejected'] for x in check['boundary_cycles']),
                full_vector_comparisons=len(check['all_full_vectors']),active_KV_comparisons=len(check['all_committed_target_states']),
                draft_vectors=len(check['all_draft_proposal_vectors']),target_physical_rows=sum(int(w)*n for w,n in r['target_physical_width_hist'].items()),draft_physical_rows=sum(int(w)*n for w,n in r['draft_physical_width_hist'].items()),
                heavy_service_cost_s=r['service_seconds'],passed=True))
        samples=folder/'resources.jsonl';count=0
        for line in samples.read_text().splitlines():
            s=json.loads(line);count+=1
            for key in ('gpu_free','ram_free','C_free','D_free'):minima[key]=min(minima.get(key,s[key]),s[key])
            for key in ('temperature_C','clock_MHz','power_W'):
                try:v=float(s[key])
                except (ValueError,TypeError):continue
                maxima[key]=max(maxima.get(key,v),v)
                if key=='clock_MHz' and v>10000:anomalies.append(dict(job=j['id'],utc=s['utc'],raw_clock_MHz=v,interpretation='Reported anomaly retained; no actual operating frequency inferred'))
        row['resource_samples']=count;details.append(row)
    assert native_requests==37
    ledger=dict(inherited_requests=2679,inherited_reserved_rows=2854298,new_requests=37,new_reserved_rows=18543,new_actual_requests=native_requests,new_actual_rows=native_rows,
        cumulative_requests=2716,cumulative_reserved_rows=2872841,qualification_requests=500,qualification_limit=512,remaining_qualification_requests=12,
        new_tranche_requests=1812,new_tranche_limit=2048,cumulative_request_limit=3072,cumulative_row_limit=4000000,
        source_ledger=str(RUNTIME/'ledger.sqlite'),source_ledger_sha256=sha(RUNTIME/'ledger.sqlite'),attempts=attempts,
        failed_status_preserved=True,refunds=0,native_reruns=0,original_ledgers_byte_unchanged=True,
        latest_RTX_ledger_chain=[read(HERE/'LEDGER_SNAPSHOT.json')['legacy'],read(HERE/'LEDGER_SNAPSHOT.json')['epoch'],dict(path=str(RUNTIME/'ledger.sqlite'),sha256=sha(RUNTIME/'ledger.sqlite'),requests=37,rows=18543)])
    cost=dict(attempts=details,sampled_minimum_bytes=minima,raw_sampled_maxima=maxima,telemetry_anomalies=anomalies,profiling_requests=0,new_primers=0,
        host_wrapper_seconds_sum=sum(d['host']['wrapper_seconds'] for d in details),initial_engineering_wall_total=None,
        scope='Heavy qualification costs, never appended to original clean performance. Inclusive load/pool/phases/worker/wrapper clocks overlap and cannot be added. Native synchronized host phase clocks are not kernel times. Resources sampled, not guaranteed peaks.',
        postprocessor_failure_count=1,native_nonzero_exit_count=0,first4_requests_reused_without_refund_or_rerun=True)
    put(HERE/'results/CUMULATIVE_LEDGER.json',ledger);put(HERE/'results/COMPLETE_COSTS.json',cost);put(HERE/'results/ARM_QUALIFICATION.json',dict(passed=True,arms=arm,complete=read(RUNTIME/'COMPLETE_QUALIFICATION.json')))
    print(json.dumps(dict(requests=native_requests,actual_rows=native_rows,reserved_rows=18543,arms=len(arm),cumulative_requests=2716,cumulative_reserved_rows=2872841)),flush=True)

def archive():
    assert read(HERE/'results/ARM_QUALIFICATION.json')['passed'];started=time.monotonic();DEST.mkdir(exist_ok=False);files={}
    def add(name,p):
        p=Path(p).resolve();assert p.is_file() and p.suffix.lower() not in ('.gguf','.key','.pem')
        if name in files:assert sha(files[name])==sha(p)
        else:files[name]=p
    for p in RUNTIME.rglob('*'):
        if p.is_file() and 'temp' not in p.relative_to(RUNTIME).parts:add('runtime/'+p.relative_to(RUNTIME).as_posix(),p)
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:add('scripts/'+p.relative_to(HERE).as_posix(),p)
    add('dependencies/audit/core.py',AUDIT/'core.py')
    old_index=REPO.parent/'q8rtx211-evidence-20261109/ARCHIVE_INDEX.json';add('dependencies/parent-archive/ARCHIVE_INDEX.json',old_index)
    add('dependencies/parent-SOURCE_BINDINGS.json',ORIGINAL/'SOURCE_BINDINGS.json');add('dependencies/parent-DRIVER_MODULE_PINS.json',ORIGINAL/'DRIVER_MODULE_PINS.json')
    aliases={}
    for j in read(HERE/'EXECUTION_PLAN.json')['jobs']:
        for p in [Path(j['exe'])]+[Path(j['exe']).parent/n for n in read(j['build'])['modules']]:
            h=sha(p);name='dependencies/runtime/'+h+'/'+p.name;add(name,p);aliases[str(p)]=name
    archive=DEST/'supplement-complete.cas.zip';index=[];blobs={};public=[];textpath=DEST/'scientific-records.json.gz'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z,textpath.open('xb') as raw:
        with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=1) as g:
            g.write(b'{"schema":"heterospec.rtx213.supplement-text.v1","records":[');first=True
            for name,p in sorted(files.items()):
                size=p.stat().st_size;h=sha(p);blob='blobs/'+h
                assert shutil.disk_usage(DEST).free>=10*1024**3+size+1024**3
                if h not in blobs:z.write(p,blob);blobs[h]=dict(bytes=size,blob=blob)
                index.append(dict(path=name,sha256=h,bytes=size,blob=blob))
                if p.suffix.lower() in ('.exe','.dll','.bin','.f32','.sqlite','.zip','.gz'):continue
                try:text=p.read_bytes().decode('utf8')
                except UnicodeDecodeError:continue
                if '\x00' in text:continue
                if not first:g.write(b',')
                first=False;g.write(json.dumps(dict(path=name,text=text),ensure_ascii=True,separators=(',',':')).encode());public.append(dict(path=name,sha256=h,bytes=size))
            g.write(b']}')
    put(DEST/'ARCHIVE_INDEX.json',dict(files=index,unique_blobs=blobs,aliases=aliases,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,weights_included=False,source_files_preserved=True))
    restore=DEST/'readback';restore.mkdir();blobdir=restore/'.blobs';blobdir.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={x['blob'] for x in blobs.values()}
        for h,m in blobs.items():
            dest=blobdir/h;dig=hashlib.sha256();count=0
            with z.open(m['blob']) as source,dest.open('xb') as target:
                while b:=source.read(4*1024**2):
                    assert shutil.disk_usage(DEST).free>=10*1024**3+len(b)+64*1024**2;target.write(b);dig.update(b);count+=len(b)
            assert dig.hexdigest()==h and count==m['bytes']
    for x in index:
        p=restore/x['path'];assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True);os.link(blobdir/x['sha256'],p)
        assert os.path.samefile(p,blobdir/x['sha256']) and p.stat().st_size==x['bytes']
    put(HERE/'results/ARCHIVE_READBACK.json',dict(passed=True,archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,index=str(DEST/'ARCHIVE_INDEX.json'),index_sha256=sha(DEST/'ARCHIVE_INDEX.json'),restored_root=str(restore),
        logical_files=len(index),logical_bytes=sum(x['bytes'] for x in index),unique_blobs=len(blobs),all_unique_blob_bytes_reread=True,all_logical_paths_restored=True,wall_seconds=time.monotonic()-started))
    packet=HERE/'results/public_archive';packet.mkdir();parts=[]
    with textpath.open('rb') as source:
        while b:=source.read(512*1024):
            p=packet/f'scientific-records.json.gz.part-{len(parts):04d}';p.write_bytes(b);parts.append(dict(name=p.name,bytes=len(b),sha256=sha(p)))
    put(packet/'PARTS.json',dict(joined_sha256=sha(textpath),joined_bytes=textpath.stat().st_size,parts=parts));put(packet/'TEXT_INDEX.json',dict(files=public))
    public_paths={x['path'] for x in public};put(packet/'BINARY_INDEX.json',dict(files=[x for x in index if x['path'] not in public_paths],weights_included=False))
    print(json.dumps(dict(logical_files=len(index),archive_GiB=archive.stat().st_size/1024**3,public_parts=len(parts),wall_seconds=time.monotonic()-started)),flush=True)

def recompute():
    proof=read(HERE/'results/ARCHIVE_READBACK.json');assert proof['passed'];root=Path(proof['restored_root']);started=time.monotonic()
    def module(name,p):
        spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
    prior=sys.modules.get('common');common=module('common',root/'scripts/common.py');common.HERE=root/'scripts';common.RUNTIME=root/'runtime'
    core=module('supplement_archived_independent_core',root/'dependencies/audit/core.py');core.ARCHIVE=root/'dependencies/parent-archive';common.reader_class=lambda:core.Reader
    gate=module('supplement_archived_gate',root/'scripts/check_output.py');check=gate.Check();check.bank_ready(publish=False)
    for j in check.plan['jobs'][8:]:
        actual=check.candidate(j,publish=False);expected=read(root/'runtime/checks'/(j['id']+'.json'))
        for key in ('passed','job','old_trace_equal','full_endpoint_equal','boundary_cycles','target_physical_hist','receipt_sha256'):assert actual[key]==expected[key]
        assert [(x['sha256'],x['prefix']) for x in actual['all_full_vectors']]==[(x['sha256'],x['prefix']) for x in expected['all_full_vectors']]
        assert [(x['active_sha256'],x['positions']) for x in actual['all_committed_target_states']]==[(x['active_sha256'],x['positions']) for x in expected['all_committed_target_states']]
        assert [(x['sha256'],x['token']) for x in actual['all_draft_proposal_vectors']]==[(x['sha256'],x['token']) for x in expected['all_draft_proposal_vectors']]
    assert dict(check.counts)==read(root/'runtime/COMPLETE_QUALIFICATION.json')['counts']
    if prior is not None:sys.modules['common']=prior
    put(HERE/'results/ARCHIVED_NUMERICAL_RECHECK.json',dict(passed=True,source='Fully restored/rehashed archive; archived validator and independent reader; no inference',
        R_vectors=257,R_state_prefixes=40,counts=dict(check.counts),all_full_vector_hashes_and_active_KV_hashes_exact=True,
        all_frozen_traces_and_boundary_proofs_exact=True,new_GPU_requests=0,wall_seconds=time.monotonic()-started))
    print('Archived full-vector/KV/trace checks exactly reproduced without GPU',flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['collect','archive','recompute']);a=p.parse_args();{'collect':collect,'archive':archive,'recompute':recompute}[a.phase]()
