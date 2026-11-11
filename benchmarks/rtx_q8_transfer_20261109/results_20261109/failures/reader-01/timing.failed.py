"""Prospective160-request diagnosis and complete1152-request eight-arm panel."""
from pathlib import Path
import collections,copy,datetime,hashlib,json,sqlite3,sys,time
from admission import HERE,ROOT,put,sha
from execute import WORK,BASE,execute
from lifecycle_gate import read,spec,candidate
from same_work_gate import check_probe
from normalize import trace_from_row

ARMS=[('W-loop4-k3','loop4','SIMPLE',3),('W-loop4-k7','loop4','SIMPLE',7),('W-packed-k3','packed','SIMPLE',3),('W-packed-k7','packed','SIMPLE',7),
      ('LOCAL-loop4-k3','loop4','LOCAL',3),('LOCAL-loop4-k7','loop4','LOCAL',7),('LOCAL-packed-k3','packed','LOCAL',3),('LOCAL-packed-k7','packed','LOCAL',7)]

def prerequisites():
    for name in ['NATURAL_COMPLETE','EXTRA_COMPLETE','TAPES_COMPLETE','GEOMETRY_V2_COMPLETE','SAME_WORK_QUALIFICATION_COMPLETE']:
        assert read(ROOT/(name+'.json'))['passed'],name
    assert read(ROOT/'cohort/EXPOSURE_COMPLETE.json')['passed']

def totals():
    db=sqlite3.connect((WORK/'ledger.sqlite').as_uri()+'?mode=ro',uri=True)
    rows=db.execute('SELECT COALESCE(SUM(requests),0),COALESCE(SUM(rows),0) FROM attempts').fetchone();db.close();return rows

def freeze():
    prerequisites();base=read(ROOT/'JOB_MANIFEST_LIFECYCLE.json');models={k:v for k,v in base['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    fixtures=read(ROOT/'DIAGNOSTIC_OPERANDS.json')['fixtures'];jobs=[]
    for repeat in range(4):
        cores=['loop4','packed'] if repeat%2==0 else ['packed','loop4']
        for core in cores:
            probes=[]
            if repeat==0:
                for f in fixtures:
                    for mode in ('q4pair','q8'):probes.append(dict(f,name=f"primer-o{f['index']}-{f['geometry']}-{mode}",execution=mode,capture=False,kind='primer',repeat=None))
            modes=['q4pair','q8'] if repeat in (0,3) else ['q8','q4pair']
            for geometry in (['within','cross'] if repeat%2==0 else ['cross','within']):
                for f in [x for x in fixtures if x['geometry']==geometry]:
                    for mode in modes:probes.append(dict(f,name=f"test-r{repeat}-o{f['index']}-{geometry}-{mode}",execution=mode,capture=False,kind='measurement',repeat=repeat))
            payload=candidate(core,'LOCAL',7,models);payload['same_work']=probes
            j=spec(f'diagnostic-clean-r{repeat}-{core}',core,payload,len(probes),sum(len(p['prefix_ids'])+8 for p in probes));j.update(stage='diagnostic',projection=core,repeat=repeat);jobs.append(j)
    assert sum(j['requests'] for j in jobs)==160
    put(ROOT/'JOB_MANIFEST_DIAGNOSTIC_CLEAN.json',dict(base,status='FROZEN160_CLEAN_DIAGNOSTIC',jobs=jobs,requests=160,measured=128,primers=32,
        worker_lifecycle='Eight serial workers; each projection receives all16 cell primers before its first measurements. Projection and geometry order reverse in complementary rounds;AB,BA,BA,AB within paired cells. Reload/setup retained outside primary operation clock.',
        operation='Includes all8 full owned output materializations; prefix/save/restore/output-file/state-export remain outside both primary timers, separately retained.'))
    roots=read(ROOT/'cohort/COHORT_FREEZE.json')['inputs'];primers=[dict(x,cap=96) for x in read(ROOT/'QUALIFICATION_TASKS.json')['roots'][:2]]
    assert len(roots)==16 and len({x['id'] for x in roots})==16
    first=[0,1,7,2,6,3,5,4];schedule=[[(x+s)%8 for x in first] for s in range(8)];live=[]
    for session,order in enumerate(schedule):
        perm=sorted(roots,key=lambda r:hashlib.sha256(f"20261109|session{session}|{r['id']}".encode()).hexdigest())
        for position,arm in enumerate(order):
            label,core,cut,k=ARMS[arm]
            inputs=[dict(name='primer-'+str(i),input=x,capture=False) for i,x in enumerate(primers)]
            inputs += [dict(name='test-'+str(i),input=x,capture=False) for i,x in enumerate(perm)]
            payload=candidate(core,cut,k,models);payload['inputs']=inputs
            # Audited common conservative bound includes both prefills, every
            # actual target/draft cycle and original extra work near cap.
            bound=sum(2*len(e['input']['prompt_ids'])+16*e['input']['cap'] for e in inputs)
            j=spec(f'live-s{session}-p{position}-a{arm}',core,payload,18,bound);j.update(stage='live',session=session,position=position,arm=arm,arm_label=label,root_order=[x['id'] for x in perm]);live.append(j)
    assert len(live)==64 and sum(j['requests'] for j in live)==1152
    assert all(sorted(row[p] for row in schedule)==list(range(8)) for p in range(8))
    neighbors=collections.Counter((a,b) for row in schedule for a,b in zip(row,row[1:]));assert len(neighbors)==56 and set(neighbors.values())=={1}
    put(ROOT/'JOB_MANIFEST_LIVE.json',dict(base,status='FROZEN_COMPLETE64_WORKER_PANEL',jobs=live,requests=1152,measurements=1024,primers=128,schedule=schedule,
        root_clusters=16,cap=96,selection_seed=20261109,bootstrap_seed=20261109,bootstrap_draws=10000,bootstrap_rng='numpy.PCG64',percentile_method='linear',interval_percent=98.75,
        primary_contrasts='Four fixed cut/projection service k7/k3 ratios of sums; positive percentage slower; root-cluster paired resampling of all arms/sessions.',
        secondary_family='Separate four contrasts: packed/loop4 at k7 for each cut;LOCAL/W at k7 for each projection.',
        no_old_target_only_timing_control=True,no_arm_or_root_replacement=True,profile_requests=0))
    req,rows=totals();all_req=sum(j['requests'] for j in jobs+live);all_rows=sum(j['rows'] for j in jobs+live)
    assert 904+req+all_req+192+32<=3072 and req+all_req+192+32<=2048
    assert 557528+rows+all_rows<=4000000
    clean=[];startups=[]
    for p in (WORK/'runs').glob('lifecycle-v2-*/native/r*-clean/receipt.json'):
        r=read(p);clean.append(r['service_seconds']/max(1,len(r['ids'])))
    for p in (WORK/'runs').glob('lifecycle-v2-*/HOST.json'):startups.append(read(p)['wall_seconds'])
    max_per_token=max(clean);estimate=64*(18*96*max_per_token*2+max(startups))
    put(ROOT/'TIMING_ADMISSION.json',dict(passed=True,as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),requests_already_reserved=req,rows_already_reserved=rows,
        exact_upcoming_requests=all_req,exact_upcoming_rows=all_rows,cumulative_bound_requests=904+req+all_req,cumulative_bound_rows=557528+rows+all_rows,
        untouched_profile_reservation=32,untouched_closure_reservation=192,available_end='UNLIMITED_USER_AUTHORIZED',timezone='Asia/Shanghai',worker_timeout_seconds=900,
        observed_qualification_max_clean_seconds_per_emitted_token=max_per_token,conservative_wall_estimate_seconds=estimate,
        wall_method='Observed maximum natural clean service per emitted token, doubled, times18*96 per worker plus worst observed qualification wrapper allowance. Conditional planning estimate, not a runtime guarantee or64*900 prediction.',archive_margin_seconds=1800,
        source_epoch='Windows frontend-v2 common reserve8',formal_GPU_serial=True,other_research_build_download_archive_work_during_clean=False))
    print('Frozen C160 and D1152; cumulative bound',904+req+all_req,557528+rows+all_rows,flush=True)

def diagnostic():
    prerequisites();manifest=read(ROOT/'JOB_MANIFEST_DIAGNOSTIC_CLEAN.json');records=[]
    for job in manifest['jobs']:
        native=execute(job,'JOB_MANIFEST_DIAGNOSTIC_CLEAN.json')
        for p in job['job']['same_work']:
            proof=check_probe(native,p,job['projection']);r=read(native/p['name']/'receipt.json')
            records.append(dict(job=job['id'],projection=job['projection'],probe=p,receipt=r,proof=proof))
        put(ROOT/'diagnostic_completed'/(job['id']+'.json'),dict(passed=True,requests=job['requests']))
    assert sum(x['probe']['kind']=='measurement' for x in records)==128 and len(records)==160
    put(ROOT/'SAME_WORK_CLEAN_RECORDS.json',dict(records=records,qualified=True,not_live_speedup=True))

def live():
    prerequisites();assert read(ROOT/'SAME_WORK_CLEAN_RECORDS.json')['qualified']
    manifest=read(ROOT/'JOB_MANIFEST_LIVE.json');oracle=WORK/'runs/extra-v2-formal-independent-R/native';expected={}
    roots=read(ROOT/'cohort/COHORT_FREEZE.json')['inputs']
    for i,x in enumerate(roots):expected[x['id']]=read(oracle/f'formal-{i}/receipt.json')['endpoint']
    records=[]
    for job in manifest['jobs']:
        native=execute(job,'JOB_MANIFEST_LIVE.json');meta=read(native/'result.json');assert meta['total_observed_API_calls']['context_creates']==2
        for item in job['job']['inputs']:
            r=read(native/item['name']/'receipt.json');assert all(v==0 for v in r['observed_API_calls_within_service'].values())
            assert not r['capture'] and r['k']==job['job']['k'] and r['draft_ubatch']==4 and r['target_output_reserve']==8 and r['proposal_mode']=='live'
            bound_row=dict(r,study_cap=item['input']['cap']);_,derived=trace_from_row(bound_row,item['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
            for cycle,state in zip(r['cycles'],derived['states'][1:]):
                bounds=dict(min=0,max=len(state['prefix'])-1)
                assert cycle['target_after']==cycle['draft_after']==bounds
                assert cycle['keep']==len(state['prefix']) and cycle['pending_after']==state['next_pending'] and cycle['done']==state['terminal']
                assert cycle['commit_kind']==state['branch'] and cycle['output_length']==state['output_count'] and cycle['rejected']==(state['branch']=='correction')
            hist=dict(collections.Counter(str(e['width']) for e in r['executions']));assert hist==r['target_physical_width_hist']
            k=job['job']['k'];assert sum(int(w)*v for w,v in hist.items())==len(item['input']['prompt_ids'])+(k+1)*len(r['cycles'])
            assert sum(int(w)*v for w,v in r['draft_physical_width_hist'].items())==len(item['input']['prompt_ids'])+(k+1)*len(r['cycles'])
            verify=[e for e in r['executions'] if e['phase']=='VERIFY'];offset=0
            for cycle in r['cycles']:
                consumed=0;wanted=[];groups=[]
                while consumed<k+1:
                    e=verify[offset];offset+=1;assert e['position']==cycle['base']+consumed
                    wanted += [consumed+i for i in e['requested_rows']];groups.append(e);consumed+=e['width']
                assert consumed==k+1 and sorted(wanted)==list(range(k+1))
                if job['job']['lowering']=='LOCAL':assert len(groups)==1 and groups[0]['width']==k+1
            assert offset==len(verify)
            if len(r['cycles'])>=2:assert r['graphs_reused']>0
            if item['name'].startswith('test-'):assert r['endpoint']==expected[item['input']['id']]
            records.append(dict(worker=job['id'],session=job['session'],position=job['position'],arm=job['arm'],arm_label=job['arm_label'],root=item['input']['id'],domain=item['input'].get('domain','exposed_primer'),
                kind='measurement' if item['name'].startswith('test-') else 'primer',receipt=r,receipt_sha256=sha(native/item['name']/'receipt.json')))
        put(ROOT/'live_completed'/(job['id']+'.json'),dict(passed=True,requests=18,all_test_endpoints_equal=True))
        print('LIVE_WORKERS_COMPLETE',len(records)//18,'/64',flush=True)
    assert len(records)==1152 and sum(x['kind']=='measurement' for x in records)==1024
    put(ROOT/'LIVE_RECORDS.json',dict(passed=True,records=records,complete_workers=64,complete_measurements=1024,primers=128))

if __name__=='__main__':
    {'freeze':freeze,'diagnostic':diagnostic,'live':live}[sys.argv[1]]()
