"""Close the complete panel, preserve every slot, and archive original bytes."""
from pathlib import Path
import collections,csv,gzip,hashlib,json,math,shutil,subprocess,sys,time,zipfile
BASE=Path(__file__).resolve().parent
A=json.loads((BASE/'RTX_ACTIVE.json').read_text());ROOT=Path(A['raw']);CODE=Path(A['code']);OUTPUTS=BASE.parent/'outputs'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def main():
    packaging_start=time.perf_counter();analysis=read(ROOT/'ANALYSIS.json');ledger=read(ROOT/'LEDGER.json')
    assert analysis['status']=='COMPLETE_FINITE_PANEL' and ledger['native_process_starts']==12 and ledger['requests_completed']==148
    assert all(r['exit_code']==0 and r['normal_cleanup_returned'] for r in ledger['receipts'])
    records=[];slots=[];module_rows=[];pair_checks=[]
    for mode in ('reference','qual','time'):
        for i in range(4):
            p=ROOT/f'{mode}-{i}/result.json';d=read(p)
            dest=CODE/f'{mode}_evidence';dest.mkdir(exist_ok=True)
            with gzip.open(dest/f'{mode}-{i}.json.gz','wb') as f:f.write(p.read_bytes())
            for suffix in ('PROCESS_RECEIPT.json','ENVIRONMENT.json','stdout.log','stderr.log'):
                shutil.copyfile(ROOT/f'{mode}-{i}.{suffix}',dest/f'{mode}-{i}.{suffix}')
            for j,r in enumerate(d['requests']):
                records.append(dict(mode=mode,session=i,request=j,**r))
                slots.append(dict(gate='REFERENCE' if mode=='reference' else 'E1' if mode=='qual' else 'E2',process=f'{mode}-{i}',
                    task=r['task'],input_id=r['input_id'],label=r['label'],category=r['category'],status='COMPLETED',
                    length=r['length'],stop_reason=r['stop_reason'],service_seconds=r['service_seconds']))
            expected={Path(x['path']).name.lower():x['sha256'] for x in read(CODE/'BUILD_MANIFEST.json')['DLLs']}
            seen={}
            for name in d['modules']:
                p=Path(name)
                if p.name.lower() in expected:
                    h=sha(p);assert h==expected[p.name.lower()];seen[p.name.lower()]=h
            assert {'ggml-base.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=set(seen)
            module_rows.append(dict(process=f'{mode}-{i}',module_hashes=seen,verified=True))
    # Recheck every independent qualification raw vector against the sealed own-geometry reference.
    for i in range(4):
        ref=read(ROOT/f'reference-{i}/result.json');qual=read(ROOT/f'qual-{i}/result.json')
        for j,r in enumerate(qual['requests']):
            ri=0 if j==0 else 1;left=ROOT/f'reference-{i}'/ref['requests'][ri]['folder'];right=ROOT/f'qual-{i}'/r['folder']
            af={str(p.relative_to(left)):sha(p) for p in left.rglob('*.f32')};bf={str(p.relative_to(right)):sha(p) for p in right.rglob('*.f32')}
            assert af==bf and af
            pair_checks.append(dict(task=i,label=r['label'],full_vector_pairs=len(af),byte_hash_equal=True))
    for task in range(4):
        for label in ('PQ','QB'):
            for category in ('clean_before','profile','clean_after'):
                slots.append(dict(gate='E3',process='',task=task,input_id=read(CODE/'INPUT_PANEL.json')['inputs'][task]['id'],label=label,
                                  category=category,status='NOT_STARTED_CONDITIONAL_NOT_NEEDED',length='',stop_reason='',service_seconds=''))
    with (CODE/'ALL_SLOTS.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(slots[0]));w.writeheader();w.writerows(slots)
    for name in ('ANALYSIS.json','BLOCKS.csv','TIMING_TABLE.csv','LEDGER.json','QUALIFICATION_GATE.json'):
        shutil.copyfile(ROOT/name,CODE/name)
    cost=dict(native_processes=12,requests=148,reference_requests=8,qualification_requests=12,warmups=64,measured=64,
        native_owned_seconds=ledger['owned_native_seconds'],model_load_seconds=sum(read(ROOT/r['slot']/'result.json')['model_load_seconds'] for r in ledger['receipts']),
        service_seconds_by_category={k:sum(r['service_seconds'] for r in records if r['category']==k) for k in ('reference','qual','warmup','measured')},
        request_seconds_by_category={k:sum(r['request_seconds'] for r in records if r['category']==k) for k in ('reference','qual','warmup','measured')},
        failed_native_processes=0,failed_requests=0,scientific_retries=0,conditional_unstarted_profile_positions=24,
        builds=5,build_process_seconds='UNRECORDED; original preparation logs and staging failure preserved',
        hardware_kernel_starts='NOT_COUNTED',GPU_active_seconds='NOT_MEASURED',
        scope='Native parent lifetime includes model load, capture, comparisons, result persistence and cleanup; service/request windows are separate. Preparation, E0 review and packaging are separate auxiliary costs, not a complete OS-process ledger.')
    save(CODE/'COST_TABLE.json',cost);save(CODE/'MODULE_RECHECK.json',module_rows);save(CODE/'QUALIFICATION_RECHECK.json',pair_checks)
    with (ROOT/'BLOCKS.csv').open(encoding='utf-8',newline='') as f:blocks=list(csv.DictReader(f))
    alternative=math.prod(float(x['QB_dual_PQ']) for x in blocks)**(1/16)
    assert abs(alternative-analysis['primary_QB_dual_PQ'])<1e-12
    reg=read(CODE/'PREREGISTRATION.json');post=[]
    for x in list(reg['models'].values())+reg['identity']['DLLs']+[reg['identity']['executable']]:
        h=sha(x['path']);assert h==x['sha256'];post.append(dict(path=x['path'],sha256=h,status='UNCHANGED'))
    save(CODE/'POST_EXECUTION_IDENTITY.json',post)
    save(CODE/'FINAL_VALIDATION.json',dict(status='PASS',all148_requests_visible=True,all12_exits_clean=True,
        full_logit_pairs=sum(x['full_vector_pairs'] for x in pair_checks),all_reference_and_qualification_raw_hashes_rechecked=True,
        native_modules_match_pinned_DLLs=True,models_runtime_DLLs_unchanged=True,alternative_product_estimator=alternative,
        no_exclusions_or_retries=True,qualification_preceded_timing=True,scope='Same-host archival reconstruction and independent arithmetic check; not external certification'))
    need_profile=analysis['E3']=='CONSIDER_SPARSE_PROFILE'
    save(CODE/'E3_DISPOSITION.json',dict(status='NOT_STARTED_NOT_NEEDED' if not need_profile else 'NOT_STARTED_NO_ATTRIBUTION_QUESTION',
        reason='The full-service/economics screen closes profiling.' if not need_profile else 'Full-service layout benefit and economics answer the registered software questions. No physical intervention is proposed, and phase subtotals cannot establish a critical path. Further observer overhead cannot change the finite-panel screen.',
        native_profile_processes=0,no_critical_path_or_hardware_claim=True))
    pct=100*analysis['reduction'];econ=analysis['QB_target_only'];screen=analysis['screen'];aa=100*analysis['largest_input_AA_imbalance']
    lines=[f'# RTX platform closure: completed finite-panel result', '',
      f'**E0 repaired, E1 passed, E2 completed: {screen}.**', '',
      f'Primary QB / dual-PQ service ratio **{analysis["primary_QB_dual_PQ"]:.8f}**, a **{pct:.3f}%** reduction. Largest input-aggregate A/A imbalance **{aa:.3f}%**; engineering threshold **{100*analysis["engineering_threshold"]:.3f}%**. QB / target-only ratio **{econ:.8f}** ({analysis["speculative_economics"]}).', '',
      '| Fixed exposed input | Output | QB / dual-PQ | QB / target-only |', '|---|---|---:|---:|']
    for row in analysis['inputs']:
        q=read(ROOT/f'qual-{row["task"]}/result.json')['requests'][0]
        lines.append(f'| {row["input_id"]} | {q["length"]}/{q["stop_reason"]} | {row["QB_dual_PQ"]:.6f} | {row["QB_R"]:.6f} |')
    lines += ['', '## Reference and scope', '',
      'PR136 was audited at65b938c19b9856c6c37af6c1d224989c22cd469f. The original E0 stop is preserved under e0_20261020. Following the user’s explicit repair instruction, a new prospective request driver/reference identity was frozen at351415f112c695f6bc84ae718b323c7b59d3990d before the first model process. This is a prospective service study using the same model/tokenizer/output bytes and21 original numerical DLLs, not an assertion that PR104 contained complete logits or that its resident timer had the new service window.', '',
      'Four independently generated R/PQ k1 references preserve the old R endpoints;1,106 complete float32 vocabulary vectors are sealed at18f8ef3a7a7cd61846d3deca4a7f62f9f0d9f9ee before independent E1. E1 produced1,794 vectors, all compared byte-for-byte against the matching new R or PQ reference, including discarded target verification rows. R/PQ/QB endpoints match, and speculative cycle/pending/proposal/accept/reject/correction/bonus/KV-bound traces match. All36 target layers show actual caller rows2, physical attention q2 for QB and serial q1 for PQ, GQA32/8, observed key extents/dtypes/strides/masks and RTX placement. Operator tensor readbacks were not requested because that would split the CUDA graph. Visible key counts are derived from registered causal positions; physical mask extents/strides are observed.', '',
      'Qualification was sealed at913407f7 before clean timing. E2 contains4 independent native processes,64 measured requests and64 separately charged warmups, one per input/arm/process. Every output and cycle/state check passes. All16 paired blocks, both identical PQ controls and all session signs remain visible. No failed native process, scientific retry, outlier removal or post-hoc input selection occurred.', '',
      'The primary timer covers fresh target/draft context and graph reservation through prefills, generation, greedy decisions, output/state handling, synchronization and teardown. Both model weights remain resident for R; model loading is separate. R retains historical target ubatch1; speculative target uses ubatch4 and draft ubatch1. This measures the frozen execution policy, not an optimized production-serving ceiling. Timing has no node observer, full-vector file writes or correctness comparisons inside service. Host decode phase intervals are not mutually exclusive GPU critical-path shares.', '',
      '## Decision', '',
      'The preregistered2%/A/A/every-session engineering screen is applied without significance or equivalence claims. '+('The complete layout advantage is established on this fixed panel.' if screen.startswith('ESTABLISHED') else 'A practical complete-service layout advantage is not established on this fixed panel.'),
      'The A/A imbalance exceeds the2% practical margin. The small layout point estimate is noise-limited and unresolved; two session aggregates favor PQ. This is not proof of equivalence, no true layout effect, or a precisely measured1.07% gain. No outlier removal or follow-up precision hunt repairs that uncertainty.',
      'E3 disposition is recorded separately; no additional profiler, counter sweep, hardware/RTL/actor study or favorable-number search was run. No physical bottleneck or accelerator claim follows.', '',
      '## Accounting and archive', '',
      f'New scope UUID `{A["uuid"]}`:12 native processes /148 total requests, native parent lifetime {cost["native_owned_seconds"]:.6f}s; separately recorded model loading {cost["model_load_seconds"]:.6f}s. All12 processes exited normally and cleanup returned. Native GPU-active duration and hardware kernel count are unmeasured. The original preparation DLL-staging failure and five successful compiler/archive/link invocations remain documented; compiler lifetime was not captured before that staging error. Historical RTX ledgers and their separate units/caps are preserved; no B570 allowance was transferred.', '',
      '`ALL_SLOTS.csv` preserves148 successful requests and24 conditional E3 positions not started. `COST_TABLE.json`, native receipts, the full raw SHA256 manifest, compact compressed results, state traces and immutable local archive descriptors accompany this result. The complete local ZIP contains raw vectors, executable, original numerical DLLs and frozen sources; model weights are identified by hash and remain at their retained paths rather than duplicated. All ZIP members are reopened and checked against their raw hashes. Raw archive availability is local, not an external authenticated raw download or independent audit.', '',
      'The finite panel uses four previously exposed inputs, one model pair, one RTX machine/date and k1; no unseen-input, cross-device, universal-equality or energy claim is made. Old PR104 layout values retain their original scope. The paper handoff distinguishes layout benefit from speculative economics and includes all negative/weak observations; no paper reconstruction has begun.'
    ]
    (CODE/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    handoff=f'''# RTX 论文交接\n\n本次协议与完整结果见同目录 RESULT.md。\n\n- QB/双 PQ 完整服务比值：{analysis['primary_QB_dual_PQ']:.8f}，降低 {pct:.3f}%。\n- QB/target-only：{econ:.8f}；{analysis['speculative_economics']}。\n- 实际 q2 与36层目标模型几何已核验，完整 logits、终点和周期状态均通过资格检查。\n- {screen}。不把目标验证阶段差值写成 GPU 关键路径份额，不推广到未见输入或硬件加速器。\n- 旧 PR104 常驻请求窗口与本次新建上下文服务窗口分别陈述。缺失的历史完整 logits 由新身份的前瞻参考补齐，不能写成历史原本具备。\n\n先审阅独立结果 PR，再进行论文重构。\n'''
    (CODE/'PAPER_HANDOFF.md').write_text(handoff,encoding='utf-8')
    shutil.copyfile(__file__,CODE/'package_rtx_results.py')
    members=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():members.append((p,'raw/'+str(p.relative_to(ROOT)).replace('\\','/')))
    for p in sorted((BASE/'rtx-runtime-v2/bin').glob('*')):
        if p.is_file():members.append((p,'runtime/bin/'+p.name))
    for p in sorted((BASE/'rtx-runtime-v2/source').glob('*')):
        if p.is_file():members.append((p,'runtime/source/'+p.name))
    for p in sorted(CODE.rglob('*')):
        if p.is_file():members.append((p,'registered_result/'+str(p.relative_to(CODE)).replace('\\','/')))
    manifest=[dict(path=name,bytes=p.stat().st_size,sha256=sha(p)) for p,name in members]
    save(CODE/'FULL_RAW_MANIFEST.json',dict(files=manifest,raw_root=str(ROOT),total_logical_bytes=sum(x['bytes'] for x in manifest)))
    archive=OUTPUTS/'HeteroSpec_RTX_完整实验记录.zip'
    print(json.dumps(dict(event='ARCHIVE_START',members=len(members),logical_bytes=sum(x['bytes'] for x in manifest))),flush=True)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for p,name in members:z.write(p,name)
        z.write(CODE/'FULL_RAW_MANIFEST.json','FULL_RAW_MANIFEST.json')
    print('ARCHIVE_WRITTEN_REOPENING_ALL_MEMBERS',flush=True)
    with zipfile.ZipFile(archive) as z:
        assert z.read('FULL_RAW_MANIFEST.json')==(CODE/'FULL_RAW_MANIFEST.json').read_bytes()
        for x in manifest:
            h=hashlib.sha256();size=0
            with z.open(x['path']) as f:
                while chunk:=f.read(8*1024*1024):h.update(chunk);size+=len(chunk)
            assert h.hexdigest()==x['sha256'] and size==x['bytes'],x['path']
    descriptor=dict(archive=pin(archive),members=len(members)+1,all_members_reopened_and_sha256_verified=True,
       raw_vectors=sum(x['path'].endswith('.f32') for x in manifest),model_weights_included=False,numerical_DLL_bytes_included=True,
       native_executable_included=True,availability='LOCAL_RAW_ARCHIVE; compact records and full SHA256 manifest in GitHub PR',packaging_wall_seconds=time.perf_counter()-packaging_start)
    save(CODE/'RAW_ARCHIVE.json',descriptor);save(OUTPUTS/'HeteroSpec_RTX_归档校验.json',descriptor)
    shutil.copyfile(CODE/'RESULT.md',OUTPUTS/'HeteroSpec_RTX_实验报告.md')
    shutil.copyfile(CODE/'TIMING_TABLE.csv',OUTPUTS/'HeteroSpec_RTX_全部计时.csv')
    shutil.copyfile(CODE/'PAPER_HANDOFF.md',OUTPUTS/'HeteroSpec_RTX_论文交接.md')
    print(json.dumps(descriptor,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
