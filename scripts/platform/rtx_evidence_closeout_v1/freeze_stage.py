"""Actual prospective GitHub byte boundaries, source/binary and dependency archive."""
from run_common import *
import importlib.metadata, shutil, zipfile
import stages

def archive(path,files):
    assert all(not n.startswith('/') and not any(p in ('.','..') for p in n.split('/')) for n in files),'unsafe logical archive name'
    index={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in sorted(files.items())}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('INDEX.json',json.dumps(dict(files=index),ensure_ascii=False,indent=2)+'\n')
        for n,p in sorted(files.items()):z.write(p,n)
    with zipfile.ZipFile(path) as z:
        assert set(z.namelist())==set(index)|{'INDEX.json'}
        for n,a in index.items():
            b=z.read(n);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
    return dict(bytes=Path(path).stat().st_size,sha256=sha(path),logical_files=len(index))

def dependencies():
    deps={};files={}
    for package in ['Jinja2','MarkupSafe','pyahocorasick','matplotlib','numpy','Pillow','contourpy','cycler','fonttools','kiwisolver','packaging','pyparsing','python-dateutil','six']:
        dist=importlib.metadata.distribution(package);rows={}
        for rel in dist.files:
            p=Path(dist.locate_file(rel))
            if p.is_file() and '__pycache__' not in p.parts:
                safe='/'.join('_parent_' if part=='..' else part for part in str(rel).replace('\\','/').split('/'))
                key=package+'/'+safe;files['python-packages/'+key]=p;rows[str(rel)]=dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
        deps[package]=dict(version=dist.version,files=rows)
    base=Path(sys.base_prefix)
    for p in base.iterdir():
        if p.is_file() and p.suffix.lower() in ['.exe','.dll','.zip','._pth']:files['python-runtime/'+p.name]=p
    for p in (base/'Lib').rglob('*.py'):
        if 'site-packages' not in p.parts:files['python-runtime/'+p.relative_to(base).as_posix()]=p
    for p in (base/'DLLs').glob('*'):
        if p.is_file():files['python-runtime/DLLs/'+p.name]=p
    helper=Path('D:/HeteroSpec-PC/tools/llama-b10839/llama.dll')
    assert sha(helper)==read(PUB/'MODEL_CONTRACT.json')['native_runtime_DLL_sha256']
    save(PUB/'DEPENDENCIES.json',dict(python=sys.version,executable=dict(path=sys.executable,sha256=sha(sys.executable)),base_prefix=str(base),packages=deps,helper_llama_dll_sha256=sha(helper),all_runtime_files={k:dict(sha256=sha(p),bytes=p.stat().st_size,path=str(p)) for k,p in files.items()}))
    return files

def prepare_f0a():
    d=read(DESIGN/'DESIGN.json');assert not list((LOCAL/'runs').rglob('REQUEST_STARTED.json'))
    h=host();old=read(OLDPUB/'DISPLAY_CHANGE_ADMISSION.json')['samples'][0];policy=read(OLDPUB/'HOST_POLICY.json')
    assert h['AC']==1 and all(h[k]==old[k] for k in ['gpu','driver','total_MiB']) and h['power_scheme_guid']==policy['power_scheme_guid']
    save(PUB/'HOST_ADMISSION.json',dict(status='PASS',sample=h,display_routing='User disabled discrete direct panel connection; inherited iGPU display admission',old_policy_sha256=sha(OLDPUB/'HOST_POLICY.json'),cooldown='120s idle then3 samples10s apart util<=5 temp<=55 range<=2, cap600s; applied before every worker'))
    save(PUB/'ENGINEERING_PLAN.json',dict(jobs=stages.eng_plan(d),planned_paid_per_family=302,cap_per_family=360,includes_loads_warmups_and_requests=True))
    save(PUB/'PROFILE_PLAN.json',dict(jobs=stages.profile_plan(d),planned_requests_per_family=96,loads_per_family=4,warmups_per_family=4,planned_paid_per_family=104,cap_per_family=128,Latin_positions='task index mod4 rotates four modes; six tasks have disclosed finite imbalance'))
    (PUB/'COUNTER_SEMANTICS.md').write_text('''# RTX closeout counter binding

One resident worker, one sequence, one request writer. No numerical operators, sampling, KV operations or templates change. baseline suppresses new integer work; counts has integer hooks only; lite adds steady-clock API entry/return and natural sampling-ready markers without extra synchronization; heavy enables inherited graph/logits capture and explicit synchronization. All modes retain the same request mode/identity response adapter, so baseline is its counters-disabled control rather than a separate old executable.

P_all sums actual returned draft vectors; P_verified sums vectors passed to sample_and_accept_n. Each sampled accepted prefix is compared numerically, and only IDs actually pushed to generated_tokens count as committed acceptance. Matching but uncommitted suffixes are terminal_discarded. A first differing proposal is first_mismatch_rejected, later positions unexamined_after_mismatch. Generated vectors never verified are unverified_before_verify. The five destinations sum P_all. Output is initial target token plus committed accepted proposals plus full-acceptance bonus or mismatch correction plus ordinary/tail fallback. First EOG is included. Histograms use actual committed progress, never an acceptance independence assumption.

Draft continuation calls/rows in the standardized UB1 conservation fields are actual process_ubatch graph_compute calls/occupied token rows, split into proposal and catchup. Additional caller_calls/caller_rows retain llama_decode API submissions; a caller may contain several physical UB1 graphs. Target caller widths and physical micrograph widths are retained separately. Physical rows mean native tokens submitted to graph_compute, not GPU hardware occupancy. rollback_calls counts the existing target post-verification KV trim call; other existing draft/checkpoint trims are visible in inherited heavy traces. Replay paths retain actual work and mark their proposal accounting unsupported instead of manufacturing conservation. Attempted positions count actual comparisons, accepted positions actual committed prefixes.

The primary clock includes JSON encoding, resident HTTP submission, complete JSON/IDs/stop parse and endpoint validation; disk persistence, hashes and loaded-module attestation are outside and separately retained. cache_n measures reused prompt tokens; response tokens_cached is occupied final KV and is retained under its original name. Formal counts mode includes no elapsed hooks/heavy/ETW/added sync. Native work summaries are part of the measured response channel, and their overhead is never subtracted.

The bounded lite attempt records API enqueue spans and natural sampling-ready markers. Asynchronous outputs and target/draft overlap prevent asserting a completed mutually exclusive wall basis from these hooks; coefficients require that stronger proof. Raw unavailable timing is retained rather than adding synchronization or fitting confirmation costs.
''',encoding='utf-8',newline='\n')
    files=dependencies()
    files['helpers/gguf.py']=REPO/'scripts/platform/jsa_third_family_v1/gguf.py'
    for version in sorted((LOCAL/'native').glob('cpu-build-v*')):
        old=read(LOCAL/'native/BASE_SOURCE_HASHES.json')
        for p in version.rglob('*'):
            if p.is_file() and (not 'source' in p.relative_to(version).parts or old.get(p.relative_to(version/'source').as_posix())!=sha(p)):
                files['native/cpu-versions/'+version.name+'/'+p.relative_to(version).as_posix()]=p
    for p in (LOCAL/'native').glob('CPU_PATCH_ATTEMPT_*.json'):files['native/'+p.name]=p
    for p in (LOCAL/'native/source').rglob('*'):
        if p.is_file():files['native/source/'+p.relative_to(LOCAL/'native/source').as_posix()]=p
    files['native/llama-server.exe']=LOCAL/'native/build/bin/llama-server.exe';files['native/vocabulary.exe']=LOCAL/'native/vocabulary.exe'
    for p in (LOCAL/'native').glob('build-*.log'):files['native/'+p.name]=p
    info=archive(PUB/'SOURCE_RUNTIME.zip',files)
    save(PUB/'SOURCE_RUNTIME_MANIFEST.json',info)
    freeze('F0A')

def freeze(phase):
    payload={p.relative_to(REPO).as_posix():sha(p) for root in [PUB,Path(__file__).parent,DESIGN] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    f=dict(phase=phase,utc=now(),design_head=DESIGN_HEAD,base_head=BASE_HEAD,payload_sha256=payload,budgets=read(DESIGN/'DESIGN.json')['budgets'],timer='Inclusive resident JSON submission through full IDs/stop parse and endpoint validation',runtime=read(PUB/'NATIVE_BUILD.json'),all_forward_dependencies_sealed=True)
    if phase=='F0B':
        assert not any(e['phase']=='formal' for e in stages.Ledger().events)
        f.update(plan_sha256=digest(read(PUB/'FORMAL_PLAN.json')),input_sha256=digest(read(PUB/'CONFIRMATION_INPUTS.json')),model_sha256=digest(read(PUB/'BREAK_EVEN_MODEL.json')),model_file_sha256=sha(PUB/'BREAK_EVEN_MODEL.json'),model_frozen_before_first_formal=True)
    save(PUB/(phase+'.json'),f)
    subprocess.run(['git','add','--sparse','scripts/platform/rtx_evidence_closeout_v1','benchmarks/rtx_evidence_closeout_v1'],cwd=REPO,check=True)
    subprocess.run(['git','add','--sparse','-f','benchmarks/rtx_evidence_closeout_v1/SOURCE_RUNTIME.zip'],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Freeze RTX closeout '+phase+' before paid '+('engineering' if phase=='F0A' else 'confirmation')],cwd=REPO,check=True)
    branch=git('branch','--show-current');subprocess.run(['git','push','-u','origin',branch],cwd=REPO,check=True)
    commit=git('rev-parse','HEAD');assert api('git/ref/heads/'+branch)['object']['sha']==commit
    tree=api('git/trees/'+commit+'?recursive=1');assert not tree.get('truncated');items={x['path']:x for x in tree['tree']}
    wanted={**payload,(PUB/(phase+'.json')).relative_to(REPO).as_posix():sha(PUB/(phase+'.json'))};checked={}
    for name,h in wanted.items():
        blob=api('git/blobs/'+items[name]['sha']);b=base64.b64decode(blob['content']);assert hashlib.sha256(b).hexdigest()==h
        checked[name]=dict(sha256=h,bytes=len(b),git_blob=items[name]['sha'])
    receipt=dict(phase=phase,commit=commit,utc=now(),actual_remote_blobs_verified=True,before_first_formal_forward=not any(e['phase']=='formal' for e in stages.Ledger().events),readback=checked,**{k:f[k] for k in ['plan_sha256','input_sha256','model_sha256','model_frozen_before_first_formal'] if k in f})
    save(LOCAL/(phase+'_REMOTE_RECEIPT.json'),receipt);save(PUB/(phase+'_REMOTE_READBACK.json'),receipt)
    status(phase+'_REMOTE_BYTES_VERIFIED',commit=commit,files=len(checked),new_formal_forwards=0)

def projection():
    rows=stages.records('core');plan=read(PUB/'FORMAL_PLAN.json');selected=read(PUB/'SELECTED_ORDINARY.json');by={};total=0
    for f in read(DESIGN/'DESIGN.json')['families']:
        for arm in ['R','M0','M3','R_prod','C3']:
            times=[r['wall_ms']/1000 for r in rows if r['family']==f and not r['warmup'] and ((r.get('ub')==(1 if arm=='R' else selected[f]) and arm in ['R','R_prod']) or (r['condition']==arm and r.get('ub')is None))]
            assert times
            loads=[read(p)['seconds'] for p in (LOCAL/'runs/core'/f).rglob('LIFETIME.json')]
            # Conservative engineering maximum at cap128, plus maximum whole worker lifetime
            # for each formal load/warm reservation. Cooling is outside owned processes.
            estimate=240*max(times)+10*max(loads)+240
            by[f+'/'+arm]=dict(max_engineering_request_seconds=max(times),reserved_owned_seconds=estimate)
            total+=estimate
    life=stages.Ledger().lifetime();save(PUB/'CONFIRMATION_BUDGET_PROJECTION.json',dict(utc=now(),engineering_owned_seconds=life,confirmation_reserved_owned_seconds=total,total_projected_owned_seconds=life+total,owned_cap_seconds=16*3600,within_cap=life+total<16*3600,per_family_arm=by,minimum_cooling_wall_seconds=150*140,request_shape_note='Projection is descriptive reserve from actual engineering timings; controller continuously enforces true hard lifetime and7day caps'))
    assert life+total<16*3600,'insufficient full confirmation owned-lifetime reserve'

if __name__=='__main__':prepare_f0a()
