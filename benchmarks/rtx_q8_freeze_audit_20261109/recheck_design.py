"""Independent input reconstruction, chronology and paired-root statistics."""
from pathlib import Path
import collections,datetime,hashlib,json,math,sys,time
import numpy as np
from core import HERE,OUT,REPO,ORIGINAL,RECORDS,WORK,ARCHIVE,PIN,R_SHA,read,put,git,digest,stamp,ledger

PREFIX='benchmarks/rtx_q8_transfer_20261109/'
def pinfile(p,ref=PIN):return git('show',ref+':'+PREFIX+p)
def first_commit(p):
    rows=git('log','--reverse','--format=%H %aI','--',PREFIX+p).decode().splitlines();return rows[0].split(' ',1)
def features(x):
    found=set()
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str):
                if k in ('id','root','input_id','root_id','task_id','message_id','text_sha256','content_sha256','raw_prompt_sha256','formatted_prompt_sha256'):found.add(v)
                if k in ('text','description','raw_prompt','formatted_prompt','prompt'):found.add(digest(v.strip().encode()))
            if k in ('keys','root_ids','roots','excluded_roots','additional_authenticated_roots') and isinstance(v,list):found.update(t for t in v if isinstance(t,str))
            found.update(features(v))
    elif isinstance(x,list):
        for v in x:found.update(features(v))
    return found

def cohort():
    source=read(RECORDS/'cohort/SOURCE_SELECTION_BEFORE_TOKENIZATION.json');admission=read(RECORDS/'cohort/COHORT_ADMISSION.json');frozen=read(RECORDS/'cohort/COHORT_FREEZE.json')['inputs'];pins=[]
    for group in ('source_pins','exposure_pins'):
        for p,h in source[group].items():
            actual=digest(Path(p).read_bytes());assert actual==h,('Changed raw source/exposure',p);pins.append(dict(path=p,sha256=h))
    sys.path.insert(0,'D:/rtx188/host-dependencies/packages');import pyarrow.parquet as pq
    rows=[]
    for p in [Path('D:/rtx155/preparation/apps-first1000.jsonl'),Path('E:/rtx164/apps-new/rows.jsonl'),Path('E:/rtx164/apps-train/rows.jsonl')]:
        split='train' if p.parent.name=='apps-train' else 'test';first=read(p.parent/'SOURCE.json')['first'] if p.parent.name=='apps-new' else 0
        for i,line in enumerate(p.read_text(encoding='utf8').splitlines(),first):
            x=json.loads(line);rows.append(dict(id=f"APPS/{split}/{x.get('problem_id',i)}",domain='code',description=x['question']))
    for name in sorted(p for p in source['source_pins'] if p.endswith('.parquet')):
        p=Path(name);split='test' if p.name.startswith('test-') else 'train'
        for i,x in enumerate(pq.read_table(p).to_pylist()):rows.append(dict(id=f'MATH/{p.parent.name}/{split}/{i}',domain='math',description=x['problem']))
    assert len(rows)==source['source_entries'] and len({r['id'] for r in rows})==len(rows)
    blocked=set()
    for name in source['exposure_pins']:blocked.update(features(read(name)))
    unique={}
    for r in sorted(rows,key=lambda r:r['id']):
        lead='Complete the following Python programming task. Return only the completed Python code, without Markdown fences.' if r['domain']=='code' else 'Solve the following mathematics problem. Give your reasoning and final answer.'
        r['raw_prompt']=lead+'\n\n'+r['description'];r['text_sha256']=digest(r['description'].strip().encode());r['raw_prompt_sha256']=digest(r['raw_prompt'].encode())
        if {r['id'],r['text_sha256'],r['raw_prompt_sha256']} & blocked:continue
        unique.setdefault(r['text_sha256'],r)
    ordered=sorted(unique.values(),key=lambda r:(r['domain'],digest(('20261109|'+r['domain']+'|'+r['id']).encode()),r['id']))
    assert [r['id'] for r in ordered]==source['ranked_ids']
    tokenfile=RECORDS/'cohort/tokens.jsonl';tokens={r['id']:r['prompt_ids'] for r in map(json.loads,tokenfile.read_text(encoding='utf8').splitlines())}
    chosen=[]
    for domain in ('code','math'):chosen += [r for r in ordered if r['domain']==domain and 1<=len(tokens[r['id']])<=192][:8]
    assert [r['id'] for r in chosen]==[r['id'] for r in frozen]==[r['id'] for r in admission['selected']]
    for actual,expected in zip(chosen,frozen):
        for k in ('id','domain','description','raw_prompt','text_sha256','raw_prompt_sha256'):assert actual[k]==expected[k]
        assert tokens[actual['id']]==expected['prompt_ids'] and expected['cap']==96
        assert digest(expected['formatted_prompt'].encode())==expected['formatted_prompt_sha256']
    # Re-read all39 immutable PR62 JSONs, rather than a sparse checkout or pass flag.
    names=git('ls-tree','-r','--name-only','8dfa60a2492e0639a0774f7bac842273485ca26a','benchmarks/rtx_closeout_bcd').decode().splitlines();names=[n for n in names if n.endswith('.json')];assert len(names)==39
    exposed=set()
    for name in names:exposed.update(features(json.loads(git('show','8dfa60a2492e0639a0774f7bac842273485ca26a:'+name))))
    assert not any({r['id'],r['text_sha256'],r['raw_prompt_sha256'],r['formatted_prompt_sha256']}&exposed for r in frozen)
    history=[]
    for p in ('cohort/SOURCE_SELECTION_BEFORE_TOKENIZATION.json','cohort/COHORT_ADMISSION.json','cohort/COHORT_FREEZE.json','select_inputs.py','analyze_results.py','JOB_MANIFEST_LIVE.json','results_20261109/JOB_MANIFEST_LIVE.json'):
        path=p if p.endswith('.py') else 'results_20261109/'+p if not p.startswith('results_') else p
        try:c,t=first_commit(path);history.append(dict(path=path,first_commit=c,commit_time=t))
        except (IndexError,Exception):continue
    earliest=first_commit('results_20261109/cohort/COHORT_ADMISSION.json')[0]
    assert json.loads(pinfile('results_20261109/cohort/COHORT_ADMISSION.json',earliest))['selected']==frozen
    put('COHORT_RECHECK.json',dict(passed=True,source_pins_rehashed=pins,source_rows=len(rows),ranked_eligible=len(ordered),selection_rules_recomputed=True,
        token_admission='Reused/read frozen vocabulary-only token IDs; no new native tokenizer or model invocation. Tokenizer arithmetic was not independently rerun.',
        selected=[dict(id=r['id'],domain=r['domain'],tokens=len(r['prompt_ids']),cap=r['cap'],prompt_sha256=r['formatted_prompt_sha256']) for r in frozen],
        pr62_jsons_reread=39,history=history,initial_selected_bytes_equal_final=True,new_GPU_requests=0))

def timeline():
    t=read(OUT/'TIMELINE.json');members={x['path']:x for x in t['manifests']};late=[]
    for a in t['attempts']:
        relative=a['manifest'].split('results_20261109/',1)[1];p=RECORDS/relative
        a['local_manifest_mtime_bjt']=stamp(p.stat().st_mtime);a['local_exact_file_precedes_reservation']=p.stat().st_mtime<=a['started']
        a['git_commit_after_reservation']=datetime.datetime.fromisoformat(a['freeze_commit_time']).timestamp()>a['started']
        native=WORK/'runs'/a['id']/'native'
        if a['id']=='tapes-v2-native-producer':
            r=read(native/'result.json');paths=[native/x['path'] for x in r['proposal_tapes']];first=min(paths,key=lambda p:p.stat().st_mtime)
            a['first_output_file']=str(first);a['first_output_bjt']=stamp(first.stat().st_mtime)
        if a['git_commit_after_reservation']:late.append(a['id'])
    put('TIMELINE_FINAL.json',dict(t,post_execution_committed_jobs=late,post_execution_committed_requests=sum(a['requests'] for a in t['attempts'] if a['id'] in late),
        local_exact_manifests_all_precede_reservation=all(a['local_exact_file_precedes_reservation'] for a in t['attempts']),
        warning='Local mtime supports a per-job pre-launch file sequence, not all-before-any or independently notarized publication. Inherited manifest utc is not the concrete job creation time.'))

def panel():
    frozen=json.loads(pinfile('results_20261109/JOB_MANIFEST_LIVE.json','2a884e28e3c31c2cb20eebf853c48e03698364fe'));current=read(RECORDS/'JOB_MANIFEST_LIVE.json');assert frozen==current
    roots=read(RECORDS/'cohort/COHORT_FREEZE.json')['inputs'];ids=[x['id'] for x in roots];first=[0,1,7,2,6,3,5,4];schedule=[[(a+s)%8 for a in first] for s in range(8)];assert current['schedule']==schedule
    assert all(sorted(r[p] for r in schedule)==list(range(8)) for p in range(8))
    adjacency=collections.Counter((a,b) for row in schedule for a,b in zip(row,row[1:]));assert len(adjacency)==56 and set(adjacency.values())=={1}
    matrix=np.zeros((8,16));counts=np.zeros((8,16),dtype=int);receipt_hashes={};executables=collections.defaultdict(set);times=[]
    original=read(RECORDS/'LIVE_RECORDS.json');aggregate={(r['worker'],r['kind'],r['root']):r for r in original['records']}
    for n,j in enumerate(frozen['jobs']):
        assert j['session']==n//8 and j['position']==n%8 and j['arm']==schedule[n//8][n%8]
        order=sorted(roots,key=lambda r:digest(f"20261109|session{n//8}|{r['id']}".encode()));assert j['root_order']==[r['id'] for r in order]
        folder=WORK/'runs'/j['id'];assert read(folder/'JOB.json')==j and read(folder/'JOB_NATIVE.json')==j['job']
        executables[j['arm_label']].add(j['exe_sha256'])
        meta=read(folder/'native/result.json');assert meta['total_observed_API_calls']['context_creates']==2
        for i,item in enumerate(j['job']['inputs']):
            raw=(folder/'native'/item['name']/'receipt.json').read_bytes();r=json.loads(raw);kind='primer' if i<2 else 'measurement';root=item['input']['id'];saved=aggregate[(j['id'],kind,root)]
            assert saved['receipt']==r and saved['receipt_sha256']==digest(raw)
            receipt_hashes[j['id']+'/'+item['name']]=digest(raw)
            if i>=2:
                x=order[i-2];assert item['input']==x and x['cap']==96
                matrix[j['arm'],ids.index(root)]+=r['service_seconds'];counts[j['arm'],ids.index(root)]+=1
        times.append(dict(job=j['id'],first_test=read(folder/'RESULT_MARKERS.json')['markers'][2]['native_main_to_pre_record_seconds']))
    assert np.all(counts==8) and len(aggregate)==1152
    results=read(RECORDS/'LIVE_RESULTS.json');rng=np.random.Generator(np.random.PCG64(20261109));draws=rng.integers(0,16,(10000,16))
    # Independently accumulate integer cluster multiplicities, rather than reuse
    # the original analyzer's advanced-indexing bootstrap implementation.
    multiplicity=np.array([np.bincount(row,minlength=16) for row in draws]);boot=multiplicity@matrix.T;contrasts=[]
    specs=[('primary',1,0),('primary',3,2),('primary',5,4),('primary',7,6),('secondary',3,1),('secondary',7,5),('secondary',5,1),('secondary',7,3)]
    for family,num,den in specs:
        point=matrix[num].sum()/matrix[den].sum();bounds=np.quantile(boot[:,num]/boot[:,den],[.00625,.99375],method='linear')
        saved=next(r for r in results[family] if r['numerator_arm']==num and r['denominator_arm']==den)
        diff=max(abs(point-saved['ratio']),*np.abs(bounds-np.array(saved['adjusted_interval_ratio'])).tolist());assert diff<1e-12
        contrasts.append(dict(family=family,numerator=num,denominator=den,change_pct=(point-1)*100,interval_change_pct=((bounds-1)*100).tolist(),maximum_ratio_arithmetic_difference=diff))
    analyzer_old=pinfile('analyze_results.py','2a884e28e3c31c2cb20eebf853c48e03698364fe');assert analyzer_old==pinfile('analyze_results.py')
    # Retain all blocks; compute gap sensitivity only as explicitly post-hoc descriptive checks.
    gap_sensitivity=[]
    for num,den in ((1,0),(3,2),(5,4),(7,6)):
        per=[]
        for session in range(8):
            totals=[]
            for arm in (num,den):totals.append(sum(r['receipt']['service_seconds'] for r in original['records'] if r['kind']=='measurement' and r['session']==session and r['arm']==arm))
            per.append((totals[0]/totals[1]-1)*100)
        without=[sum(r['receipt']['service_seconds'] for r in original['records'] if r['kind']=='measurement' and r['session']!=0 and r['arm']==a) for a in (num,den)]
        gap_sensitivity.append(dict(numerator=num,denominator=den,all_session_changes=per,excluding_entire_session0_change_pct=(without[0]/without[1]-1)*100,posthoc_descriptive_only=True,no_rows_removed_from_primary=True))
    put('PANEL_RECHECK.json',dict(passed=True,measurements=1024,primers=128,all_frozen_jobs_and_receipts_exact=True,all_position_and_within_block_neighbor_balance=True,
        contrasts=contrasts,executables={k:sorted(v) for k,v in executables.items()},analysis_source_unchanged=True,analysis_sha256=digest(analyzer_old),
        arithmetic_tolerance_scope='1e-12 only for reordering of statistical sums; numerical vector/KV audit remains strict all-byte SHA256 equality without tolerance.',
        receipt_hashes=receipt_hashes,gap_sensitivity=gap_sensitivity,new_GPU_requests=0))

def reader_repair():
    admission=read(RECORDS/'READER_REPAIR_ADMISSION.json');entry=admission['reusable_completed_jobs']['live-s0-p0-a0'];folder=Path(entry['folder']);verified=[]
    for name,h in entry['files'].items():assert digest((folder/name).read_bytes())==h;verified.append(name)
    old=pinfile('timing.py','2a884e28e3c31c2cb20eebf853c48e03698364fe').decode();new=pinfile('timing.py','da569cf8d3fccc861a5f7c423708f2cbb2007b41').decode()
    assert 'wanted += [consumed+i for i in e[\'requested_rows\']]' in old and "wanted += e['requested_rows']" in new
    counterexample=None
    for p in (folder/'native').glob('*/receipt.json'):
        r=read(p);groups=[e for e in r['executions'] if e['phase']=='VERIFY']
        for i,e in enumerate(groups[:-1]):
            nxt=groups[i+1]
            if e['width']==3 and nxt['position']==e['position']+3 and nxt['width']==1:
                counterexample=dict(receipt=str(p),first=e,second=nxt,old_reader=e['requested_rows']+[3+x for x in nxt['requested_rows']],correct=e['requested_rows']+nxt['requested_rows']);break
        if counterexample:break
    assert counterexample and counterexample['old_reader']==[0,1,2,6] and counterexample['correct']==[0,1,2,3]
    for name in ('entry.cpp','worker.cpp','resident_context.hpp','same_work.hpp'):
        p='results_20261109/candidate_frontend_v2/'+name;assert pinfile(p,'2a884e28e3c31c2cb20eebf853c48e03698364fe')==pinfile(p)
    rows=ledger();first=next(a for a in rows if a['id']=='live-s0-p0-a0');second=next(a for a in rows if a['id']=='live-s0-p1-a1');assert sum(a['id']=='live-s0-p0-a0' for a in rows)==1
    put('READER_REPAIR_RECHECK.json',dict(passed=True,files_rehashed=len(verified),all_original_bytes_unchanged=True,one_original_attempt=True,native_reexecution=0,
        first_worker_start_bjt=stamp(first['started']),first_worker_end_bjt=stamp(first['ended']),failure_record_bjt=admission['observed_utc'],
        repair_commit='da569cf8d3fccc861a5f7c423708f2cbb2007b41',second_worker_start_bjt=stamp(second['started']),inter_worker_gap_s=second['started']-first['ended'],
        counterexample=counterexample,native_source_unchanged=True,source_diff=git('diff','2a884e28','da569cf8','--',PREFIX+'timing.py').decode(),
        scope='Offline reader repair cannot retroactively change recorded native service clocks; interruption can affect subsequent thermal/cache environment. All-block and descriptive whole-session sensitivity retained.'))

if __name__=='__main__':
    for f in (cohort,timeline,panel,reader_repair):f();print('DESIGN_RECHECK',f.__name__,flush=True)
