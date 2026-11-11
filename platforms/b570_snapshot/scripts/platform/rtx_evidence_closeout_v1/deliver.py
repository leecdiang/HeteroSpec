"""Independent CPU analyses, full negative results, actual local/remote CAS restores, Draft PR."""
from run_common import *
import collections, statistics, zipfile
import closeout, mechanism, stages
from freeze_stage import archive

def export_records():
    rr=[];rawindex=[]
    for p in sorted((LOCAL/'runs/formal').rglob('REQUEST_STARTED.json')):
        s=read(p)
        if s['warmup']:continue
        record=p.parent/'RECORD.json';done=p.parent/'COMPLETED.json'
        if done.exists():
            assert sha(record)==read(done)['record_sha256'];r=read(record)
            rawindex.append(dict(slot=r['slot'],path=record.relative_to(LOCAL).as_posix(),sha256=sha(record)))
            rr.append({k:v for k,v in r.items() if k not in ['response','trace_range']})
        else:
            b=next(b for b in read(PUB/'FORMAL_PLAN.json')['blocks'] if any(x['slot']==s['slot'] for x in b['slots']))
            rr.append(dict(slot=s['slot'],family=s['family'],condition=s['condition']['name'],task=next(x['task'] for x in b['slots'] if x['slot']==s['slot']),session=b['session'],round=b['round'],phase='formal',warmup=False,freeze_commit=s['freeze_commit'],input_sha256=s['input_sha256'],status='FAILED' if (p.parent/'FAILED.json').exists() else 'STARTED_NO_COMPLETE_RECORD'))
    save(PUB/'FORMAL_RECORDS.json',rr);save(PUB/'RAW_RECORD_INDEX.json',rawindex)
    save(PUB/'WORKLOAD_RECORDS.json',[{k:r.get(k) for k in ['slot','family','condition','task','session','round','status','wall_ms','output','source_identity_sha256','workload','workload_error','feature_units']} for r in rr])
    save(PUB/'PAID_LEDGER.json',dict(events=stages.Ledger().events,owned_lifetime_seconds=stages.Ledger().lifetime(),lifetimes=[dict(path=p.relative_to(LOCAL).as_posix(),**read(p)) for p in sorted((LOCAL/'runs').rglob('LIFETIME.json'))]))
    return rr

def analyse():
    d=read(DESIGN/'DESIGN.json');p=read(PUB/'FORMAL_PLAN.json');i=read(PUB/'CONFIRMATION_INPUTS.json');r=read(PUB/'FORMAL_RECORDS.json');f=read(LOCAL/'F0B_REMOTE_RECEIPT.json');m=read(PUB/'BREAK_EVEN_MODEL.json')
    save(PUB/'RESULTS.json',closeout.analyse(d,p,i,r,f))
    save(PUB/'MODEL_VALIDATION.json',mechanism.analyse(d,p,i,r,f,m))
    independent(LOCAL/'cpu-independent-live',REPO,PUB,LOCAL)

def independent(root,repo,pub,local):
    root.mkdir(parents=True,exist_ok=False);code=repo/'scripts/platform/rtx_evidence_closeout_v1';design=repo/'docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json'
    results=[]
    for name in ['closeout','mechanism']:
        out=root/(name+'.json');c=[sys.executable,str(code/(name+'.py')),'--design',str(design),'analyse','--plan',str(pub/'FORMAL_PLAN.json'),'--inputs',str(pub/'CONFIRMATION_INPUTS.json'),'--records',str(pub/'FORMAL_RECORDS.json'),'--freeze',str(local/'F0B_REMOTE_RECEIPT.json'),'--out',str(out)]
        if name=='mechanism':c+=['--model',str(pub/'BREAK_EVEN_MODEL.json')]
        r=subprocess.run(c,capture_output=True,timeout=240);(root/(name+'.stdout')).write_bytes(r.stdout);(root/(name+'.stderr')).write_bytes(r.stderr)
        expected=pub/('RESULTS.json' if name=='closeout' else 'MODEL_VALIDATION.json')
        assert r.returncode==0 and read(out)==read(expected)
        results.append(dict(analyser=name,exit_code=r.returncode,exact_object_digest=digest(read(out)),source_output_sha256=sha(expected),reproduced_output_sha256=sha(out),exact_byte_equal=sha(out)==sha(expected)))
    save(root/'RECEIPT.json',dict(status='PASS',utc=now(),zero_gpu_forwards=True,independent_processes=results))
    return read(root/'RECEIPT.json')

def reports():
    result=read(PUB/'RESULTS.json');d=read(DESIGN/'DESIGN.json');rows=read(PUB/'FORMAL_RECORDS.json');selection=read(PUB/'SELECTED_ORDINARY.json')
    lines=['# RTX closeout：真实平台结果','',f'设计 #89 / `{DESIGN_HEAD}`，继承 #84 / `{BASE_HEAD}`。本次正式计划3600槽，已支付输出与费用按完整原生数组逐项核验；cap128、五轮中位数、两连续会话等权。负结果和不合格比较均保留。','',f'工程选出的普通 UB：`{selection}`。只按12个旧曝光题×2次完整保持参考的工程费用选择，未看新确认结果。','','|家族|比较|合格请求费用比|','|---|---|---|']
    for f,entry in result['families'].items():
        for c in entry['comparisons']:
            ratio=c.get('qualified_ratio');lines.append(f'|{f}|{c["comparison"]}|{ratio if ratio is not None else "未合格 / 缺项"}|')
    lines+=['','比值>1表示候选请求费用更低。R_prod/C3用于普通部署基线比较，M3/C3用于目标路径匹配的增量draft收益。完整域、任务、会话和退化项见 RESULTS.json；不据此按域在线分流。','','分阶段盈亏模型：MODEL_TIMING_UNAVAILABLE。72个真实lite请求已保留enqueue与自然采样就绪标记；异步完成与重叠不能证明规定的互斥完成wall分解。没有增加同步，没有编造系数，也没有用新确认费用拟合。轻量原生计数、四模式输出核验和配对观测扰动另见机制报告。','','公开转换文件的完整字节已认证；官方checkpoint转换血缘仍未认证。其他私有主机、不可达历史和预训练内容未观测，不宣称全局未见任务。跨日期置信区间、能源、多请求吞吐不属于本次证据。','','完整记录、源码和计数语义、实际命令/模块/内存日志、已支付失败、原始ID与生命周期收录于 RAW_EVIDENCE 档案与本地作者档案。超过单文件上限时，按 RAW_EVIDENCE_PARTS.json 的顺序连接分片为 ZIP；逐片和完整 SHA256 及 ZIP 内 INDEX 均须一致。独立CPU及实际本地/远端档案恢复核验收据随结果保留。']
    (PUB/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    bins=[];work=[]
    for r in rows:
        if r['status']!='COMPLETED':continue
        w=r.get('workload');metric=None;err=r.get('workload_error')
        if w and not err:
            try:metric=mechanism.workload_metrics(w,r['output']['length'])
            except (KeyError,AssertionError) as e:err=repr(e)
        bins.append(dict(slot=r['slot'],family=r['family'],condition=r['condition'],domain=r['task'].split('/')[0],stop=r['output']['stop_reason'],prompt_bin=next((n for n in d['mechanism']['prompt_bins_upper'] if w and w['prompt_ids_count']<=n),None),output_bin=next(n for n in d['mechanism']['output_bins_upper'] if r['output']['length']<=n),wall_ms=r['wall_ms'],workload_metrics=metric,workload_error=err))
    save(PUB/'LENGTH_DOMAIN_STOP_RECORDS.json',bins)
    errs=[r['slot'] for r in rows if r.get('workload_error') or not r.get('workload')]
    (PUB/'MECHANISM_REPORT.md').write_text('# 工作量与模型核验\n\n全部已支付请求保留；主输出/费用资格与工作计数、模型覆盖独立判断。\n\n实际proposal五种去向、两种接受率、周期进展/位置、target/draft caller与物理micrograph计数见 WORKLOAD_RECORDS.json，轻重模式核对见 HEAVY_COUNTER_AUDIT.json。物理行计数不等于硬件占用。\n\n四观测模式逐题费用与完整raw一致性见 OBSERVER_OVERHEAD.json。单次差值为描述性配对，不能当精确观测因果开销，不从正式费用中扣除。\n\nMODEL_TIMING_UNAVAILABLE：实际lite hooks只证明API排队和自然采样就绪，无法形成规定basis下完整请求wall的互斥完成跨度。component_ms、系数、GPU event费用、预测、MAPE、MAE、signed residual与break-even方向均不可用；覆盖分母与缺项在 MODEL_VALIDATION.json 全部保留。没有确认后重拟合。\n\n缺失/不合格计数槽数：'+str(len(errs))+'。固定prompt/output bins、域/EOG/CAP及负例见 LENGTH_DOMAIN_STOP_RECORDS.json 和 RESULTS.json。\n\n图中只展示实测完整费用和原生工作量；费用分项与预测散点留空并标明不可用。旧Qwen1.106与历史约1.035分别属于不同冻结/面板/计时，不声称本轮代码优化提升。\n',encoding='utf-8',newline='\n')
    figures(rows,d)

def figures(rows,d):
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,f in zip(axes,d['families']):
        names=['R','M0','M3','R_prod','C3'];a=[]
        for arm in names:
            rr=[r['wall_ms'] for r in rows if r['family']==f and r['condition']==arm and r['status']=='COMPLETED'];a.append(statistics.median(rr) if rr else float('nan'))
        ax.bar(names,a);ax.set_title(f);ax.set_ylabel('Observed complete request ms')
    fig.suptitle('Absolute request cost (pooled descriptive medians; qualified effects use registered aggregation)');fig.tight_layout();fig.savefig(PUB/'REQUEST_COST.svg');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4));ax.axis('off');ax.text(.05,.65,'Cost decomposition and prediction scatter: unavailable',fontsize=13);ax.text(.05,.35,'No valid mutually exclusive completed wall calibration.\nNo coefficients or predictions fabricated; full coverage denominators retained.',fontsize=11);fig.savefig(PUB/'MODEL_UNAVAILABLE.svg');plt.close(fig)

def pack_files():
    files={}
    for root,prefix in [(PUB,'repository/benchmarks/rtx_evidence_closeout_v1'),(Path(__file__).parent,'repository/scripts/platform/rtx_evidence_closeout_v1'),(DESIGN,'repository/docs/experiments/rtx_evidence_closeout_20261011')]:
        for p in root.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('RAW_EVIDENCE'):files[prefix+'/'+p.relative_to(root).as_posix()]=p
    for root in [LOCAL/'runs',LOCAL/'ledger',LOCAL/'cooldown',LOCAL/'static-native']:
        for p in root.rglob('*'):
            if p.is_file():files['closeout/'+p.relative_to(LOCAL).as_posix()]=p
    for n in ['F0A_REMOTE_RECEIPT.json','F0B_REMOTE_RECEIPT.json','HISTORY_NEW_OBJECTS.json','AUDIT_PULL_HEADS.json']:
        p=LOCAL/n
        if p.exists():files['closeout/'+n]=p
    files['repository/scripts/platform/jsa_third_family_v1/gguf.py']=REPO/'scripts/platform/jsa_third_family_v1/gguf.py'
    for p in (LOCAL/'cpu-independent-live').rglob('*'):
        if p.is_file():files['closeout/'+p.relative_to(LOCAL).as_posix()]=p
    return files

def split_archive(source,part_bytes=64*1024**2):
    source=Path(source);assert 0<part_bytes<95*1024**2;parts=[]
    with source.open('rb') as stream:
        while data:=stream.read(part_bytes):
            path=source.with_name(source.stem+f'.part{len(parts)+1:03d}')
            with path.open('xb') as out:out.write(data)
            parts.append(dict(name=path.name,bytes=len(data),sha256=sha(path)))
    return dict(format='ordered-binary-split-of-complete-ZIP-v1',archive_bytes=source.stat().st_size,archive_sha256=sha(source),parts=parts,reconstruction='Concatenate parts in listed order; verify each size/SHA256 and complete ZIP size/SHA256, then restore and verify every INDEX entry.')

def assemble_archive(folder,manifest,destination):
    folder=Path(folder);destination=Path(destination)
    with destination.open('xb') as out:
        for a in manifest['parts']:
            assert Path(a['name']).name==a['name'] and '/' not in a['name'] and '\\' not in a['name']
            p=folder/a['name'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
            with p.open('rb') as stream:
                while data:=stream.read(1024**2):out.write(data)
    assert destination.stat().st_size==manifest['archive_bytes'] and sha(destination)==manifest['archive_sha256']
    return destination

def restore(source,root,with_analysis):
    root.mkdir(exist_ok=False)
    with zipfile.ZipFile(source) as z:
        idx=json.loads(z.read('INDEX.json'))['files']
        for n,a in idx.items():
            p=(root/n).resolve();assert p.is_relative_to(root.resolve()) and len(str(p))<260
            b=z.read(n);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    result=dict(status='PASS',utc=now(),archive_sha256=sha(source),logical_files_verified=len(idx),zero_gpu_forwards=True)
    if with_analysis:result['cpu']=independent(root/'cpu-reproduced',root/'repository',root/'repository/benchmarks/rtx_evidence_closeout_v1',root/'closeout')
    # Source/runtime ZIP independently validates every saved byte, including full native source.
    native=root/'repository/benchmarks/rtx_evidence_closeout_v1/SOURCE_RUNTIME.zip'
    with zipfile.ZipFile(native) as z:
        sourceidx=json.loads(z.read('INDEX.json'))['files']
        for n,a in sourceidx.items():
            b=z.read(n);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
        result['source_runtime_files_verified']=len(sourceidx)
    return result

def publish(stop=None):
    if not (PUB/'PAID_LEDGER.json').exists():save(PUB/'PAID_LEDGER.json',dict(events=stages.Ledger().events,owned_lifetime_seconds=stages.Ledger().lifetime()))
    if stop:
        save(PUB/'STOP_REPORT.json',stop)
        (PUB/'RESULTS.md').write_text('# RTX closeout 协议停止报告\n\n'+stop['reason']+'\n\n没有扩大预算或换k/mask/家族来追正结果。已有真实请求、失败、加载及生命周期全部保留。原始正式计划3600槽；未执行槽和缺项不伪造成完成。\n',encoding='utf-8',newline='\n')
    files=pack_files();info=archive(PUB/'RAW_EVIDENCE.zip',files)
    transport=[PUB/'RAW_EVIDENCE.zip'];parts=None
    if info['bytes']>=95*1024**2:
        parts=split_archive(PUB/'RAW_EVIDENCE.zip');save(PUB/'RAW_EVIDENCE_PARTS.json',parts)
        transport=[PUB/a['name'] for a in parts['parts']]
        assert all(p.stat().st_size<95*1024**2 for p in transport)
        assemble_archive(PUB,parts,LOCAL/'split-roundtrip-CAS.zip')
    full=dict(files)
    for p in (LOCAL/'native').rglob('*'):
        if p.is_file() and 'build' not in p.parts and p.suffix not in ['.obj','.o','.a','.dll','.exe']:full['closeout/'+p.relative_to(LOCAL).as_posix()]=p
    full['closeout/native/build/bin/llama-server.exe']=LOCAL/'native/build/bin/llama-server.exe'
    full['closeout/native/vocabulary.exe']=LOCAL/'native/vocabulary.exe'
    output=PRIMARY/'outputs/HeteroSpec_RTX_PR89_完整记录.zip';author=archive(output,full)
    save(PUB/'ARCHIVE_MANIFEST.json',dict(scientific=info,transport=parts or dict(format='single-ZIP'),private_author=dict(path=str(output),**author),weights_and_numerical_DLLs_external_pinned_full_bytes=True))
    localreceipt=restore(PUB/'RAW_EVIDENCE.zip',LOCAL/'restored-result-local',with_analysis=not bool(stop));save(PUB/'RESTORE_LOCAL.json',localreceipt)
    # Explicit paths prevent accidentally staging the oversized local assembled ZIP.
    paths=[p.relative_to(REPO).as_posix() for root in [Path(__file__).parent,PUB] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='RAW_EVIDENCE.zip']
    if not parts:paths.append((PUB/'RAW_EVIDENCE.zip').relative_to(REPO).as_posix())
    subprocess.run(['git','add','--sparse','-f','--',*paths],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Deliver RTX closeout '+('protocol stop evidence' if stop else 'complete request cost and workload results')],cwd=REPO,check=True)
    network_retry(lambda:subprocess.run(['git','push','origin',git('branch','--show-current')],cwd=REPO,check=True),'result-CAS-push')
    commit=git('rev-parse','HEAD');tree=api('git/trees/'+commit+'?recursive=1');assert not tree.get('truncated');items={x['path']:x for x in tree['tree']};checked=[]
    remote=LOCAL/'authenticated-remote-CAS.zip';remote_parts=LOCAL/'authenticated-remote-parts';remote_parts.mkdir(exist_ok=False)
    for path in transport+([PUB/'RAW_EVIDENCE_PARTS.json'] if parts else []):
        item=items[path.relative_to(REPO).as_posix()];b=base64.b64decode(api('git/blobs/'+item['sha'])['content'])
        assert len(b)==path.stat().st_size and hashlib.sha256(b).hexdigest()==sha(path)
        with (remote_parts/path.name).open('xb') as out:out.write(b)
        checked.append(dict(path=path.relative_to(REPO).as_posix(),git_blob=item['sha'],bytes=len(b),sha256=sha(path)))
    if parts:assemble_archive(remote_parts,read(remote_parts/'RAW_EVIDENCE_PARTS.json'),remote)
    else:
        with remote.open('xb') as out:out.write((remote_parts/'RAW_EVIDENCE.zip').read_bytes())
    assert sha(remote)==info['sha256']
    receipt=restore(remote,LOCAL/'restored-result-remote',with_analysis=not bool(stop));receipt.update(actual_authenticated_remote_bytes=True,remote_commit=commit,transport_blobs=checked);save(PUB/'RESTORE_REMOTE.json',receipt)
    subprocess.run(['git','add','--sparse','benchmarks/rtx_evidence_closeout_v1/RESTORE_REMOTE.json'],cwd=REPO,check=True);subprocess.run(['git','commit','-m','Record authenticated remote CAS restoration'],cwd=REPO,check=True);network_retry(lambda:subprocess.run(['git','push'],cwd=REPO,check=True),'restoration-receipt-push')
    body=LOCAL/'PR_BODY.md';body.write_text(('PR #89 的真实 RTX 执行结果。'+('触发具体协议停止线；保留所有已付记录与未完成项。' if stop else '完成固定普通 UB 筛选、四模式机制尝试及 3600 正式请求与 150 预热；保留逐比较完整资格、负收益和退化任务。')+'\n\n固定三家族、k3、Q8、ctx1024、counts通道。F0A/F0B在对应推理前commit/push并逐GitHub blob读回。完整科学CAS和作者源码档案、独立CPU复算、本地与认证远端实际恢复收据随结果交付。\n\n原生计数、分母及物理micrograph行数单独审计。真实lite仅提供异步API/自然就绪标记，不能证明互斥完成wall分解，因此模型保留 MODEL_TIMING_UNAVAILABLE，不增加同步、不用正式费用拟合。\n\n请从 benchmarks/rtx_evidence_closeout_v1/RESULTS.md 阅读结果/停止原因；此PR不合并或修改论文/release。\n'),encoding='utf-8')
    title='RTX closeout: '+('protocol stop and complete paid evidence' if stop else 'strong ordinary baselines and verified request workload')
    existing=json.loads(subprocess.check_output(['gh','pr','list','--repo','leecdiang/HeteroSpec','--head',git('branch','--show-current'),'--state','open','--json','url'],cwd=REPO))
    assert len(existing)<=1
    if existing:
        url=existing[0]['url'];subprocess.run(['gh','pr','edit',url,'--repo','leecdiang/HeteroSpec','--title',title,'--body-file',str(body)],cwd=REPO,check=True)
    else:
        url=subprocess.check_output(['gh','pr','create','--draft','--repo','leecdiang/HeteroSpec','--base','codex/rtx-evidence-closeout-plan-20261011','--head',git('branch','--show-current'),'--title',title,'--body-file',str(body)],cwd=REPO).decode().strip()
    save(LOCAL/'RESULT_PR.json',dict(url=url,utc=now(),status='PROTOCOL_STOP' if stop else 'COMPLETE',attachment_pending=True))
    status('PROTOCOL_STOP_DELIVERED' if stop else 'COMPLETE',result_PR=url)

def complete():
    export_records();analyse();reports();publish()

if __name__=='__main__':complete()
