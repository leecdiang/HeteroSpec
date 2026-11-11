"""Freeze a finite campaign only after full-panel qualification; no model execution."""
import argparse,datetime,itertools,json,pathlib,random,statistics,subprocess,sys,uuid
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import sha,read,save
from campaign import host
P=pathlib.Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('out',type=P);a=ap.parse_args();root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    q=read(root/'qualification-v2-QUALIFICATION.json');assert q['status']=='PASS' and q['requests']==204
    rows=read(root/'qualification-v2/result.json')['requests'];refs={}
    for task in range(12):
        for k in (1,3):
            r=next(r for r in rows if r['slot']['task']==task and r['k']==k and r['arm']=='PQ' and r['lifecycle']=='fresh' and r['capture'])
            refs[task,k]=str(root/'qualification-v2'/(r['folder']+'.json'))
    seed=20261026;rng=random.Random(seed);perms=list(itertools.permutations(['PQ_A','PQ_B','QB']));rng.shuffle(perms);basecells=[(1,'resident'),(3,'resident'),(1,'fresh'),(3,'fresh')];orders=[]
    # Across twelve task positions, each of four cells occupies every position exactly three times.
    for s in range(6):
        tasks=list(range(12));rng.shuffle(tasks);cellbase=list(basecells);rng.shuffle(cellbase);slots=[]
        def add(task,k,life,label,category,block):
            slots.append(dict(slot_id=f's{s}-{len(slots):04d}',session=s,task=task,k=k,lifecycle=life,label=label,category=category,block_id=block,attempt=0,capture=False,counters=False,reference=refs[task,k]))
        warmtask=next(i for i,t in enumerate(read(root/'PANEL.json')['inputs']) if t['id']=='GSM8K/test/443')
        for ci,(k,life) in enumerate(cellbase):
            for label in perms[(s+ci)%6]:add(warmtask,k,life,label,'warmup',f's{s}-warm-{ci}')
        for position,task in enumerate(tasks):
            cells=cellbase[position%4:]+cellbase[:position%4]
            for ci,(k,life) in enumerate(cells):
                cellindex=basecells.index((k,life))
                # Six permutations twice per session/cell; every input sees all six permutations over sessions.
                for label in perms[(s+task+cellindex)%6]:add(task,k,life,label,'measurement',f's{s}-t{task}-k{k}-{life}')
        assert len(slots)==156
        save(out/f'SESSION_{s}.json',slots);orders+=slots
    files={str(p):sha(p) for p in (root/'bridge-build-v2/bin').iterdir() if p.is_file()}
    files.update({str(p):sha(p) for p in P(__file__).parent.glob('*.py')});files[str(P(__file__).parent/'worker.cpp')]=sha(P(__file__).parent/'worker.cpp')
    for p in [root/'PANEL.json',root/'MODEL_CONTRACT.json',root/'qualification-v2-QUALIFICATION.json',root/'bridge-build-v2-BUILD.json',*map(P,refs.values())]:files[str(p)]=sha(p)
    models=read(root/'MODEL_CONTRACT.json')['families']['Qwen']['models']
    for v in models.values():assert sha(v['path'])==v['sha256'];files[v['path']]=v['sha256']
    pilot=read(root/'pilot/result.json')['requests'];control=pilot[17:]
    on=statistics.mean(r['service_seconds'] for r in control if r['counters']);off=statistics.mean(r['service_seconds'] for r in control if not r['counters'])
    machine=host();assert machine['AC']==1
    config=dict(schema=1,campaign_id=str(uuid.uuid4()),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),handoff_commit='d18d85191136ef2128f2d82fd43be153bbc5d1f4',status='FROZEN_BEFORE_FORMAL',new_formal_requests=0,host=machine,
      sessions=6,requests_per_session=156,measurements=864,warmups=72,total_requests=936,seed=seed,
      cells=[dict(k=k,lifecycle=l) for k,l in basecells],arms=['PQ_A','PQ_B','QB'],panel='12 fixed previously exposed Qwen3 inputs; no unseen population inference',
      native_worker_timeout_seconds=900,total_native_owned_seconds_cap=6000,maximum_technical_session_retries=1,maximum_native_processes=7,
      retries='Only timeout, process/device failure, or interrupted output. Entire session new attempt, preserve every prior row, no mixing attempts. No numerical retry and no speed/significance retry.',
      dates='Six independently loaded process sessions on one available host date; two chronological groups of three for sensitivity. Date effect unidentifiable; no cross-date robustness claim.',
      session_gap='At least 30 seconds after cleanup; require idle GPU util<=5, temperature<=60C and AC power; bounded 300-second admission wait.',
      reference='Common newly qualified target-only R endpoints at UB1; both k share R. For each k, full output/decision/state/logit comparison against PQ fresh heavy, including rejected/unexamined rows.',
      runtime=dict(ctx=1024,target_ub=4,draft_ub=1,threads=24,kv='F16',flash=False,greedy=True,cap=128,native_eog=True,prompt_reuse=False,model_residency='Both weights loaded once per process for every cell',resident='Separate PQ and QB context pairs created before first warmup, retained across requests and both k; KV metadata cleared every request',fresh='Context pair init/reserve/destroy inside service timer; same request implementation'),
      timer='steady_clock: before observer reset/result construction + reset/create/reserve, prefill/generate/greedy/cycle/result state/sync, fresh destruction, through final metadata assembly. Excludes model loading, resident provisioning, reference comparison, JSON file serialization/output. Common prefill+generation request window also retained.',
      warmup='One complete 443 request per cell/arm at process start, 12 per session; fresh contexts recreated even for warmup. All warmups independently charged and compared. No adaptive additional warmups.',
      order='Task shuffle; cyclic balanced four-cell order; all six arm permutations each repeated twice per session/cell and once per input/cell across six sessions.',
      observer=dict(clean='baseline: no counters, no callback, no full-logit writes',pilot_counter_on_mean_seconds=on,pilot_counter_off_mean_seconds=off,pilot_relative_difference=on/off-1,interpretation='Small engineering sample cannot identify observer effect independently of noise. Counters off for formal.',cuda_graph_capture_instantiate_replay='unobserved quantitatively; debug warmup text and ggml reuse are not CUDA Graph counters'),
      estimator='Per session/input/cell log(T_QB / arithmetic_mean(T_PQ_A,T_PQ_B)); equal mean across 12 inputs then six process sessions; exponentiate. Complete paired blocks only, no outlier removal.',
      intervals=dict(primary='Paired process-session cluster percentile bootstrap, 20000 replicates, seed20261026; Bonferroni 98.75% intervals per each of four cells for familywise95%',secondary='pointwise95% paired session bootstrap for k/lifecycle and interaction of log layout effects; exploratory',sensitivity='per-session; omit-one-session; first3/last3; t interval df5; per-input regressions; single-date limitation'),
      practical='Established only if primary simultaneous CI upper<0.98, point reduction exceeds max(2%,largest input-aggregate abs(PQ_A/PQ_B-1)), and every session favors QB. Report every component. Crossing does not establish equivalence or zero effect.',
      fixed_budget='No sample extension based on effect, significance, CI width or negative sessions; numerical failure removes affected cell from qualified timing and retains failure evidence.',
      schedule_hashes={f'SESSION_{s}.json':sha(out/f'SESSION_{s}.json') for s in range(6)},files=files,model_hashes=models)
    save(out/'FREEZE.json',config);print(json.dumps({k:config[k] for k in ('campaign_id','sessions','measurements','warmups','total_requests')}))
if __name__=='__main__':main()
