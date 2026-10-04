"""Prediction transport, complete CAS archive, clean restore and additive Draft PR."""
import base64, gzip, io, shutil, tarfile, traceback, uuid
from prepare import *
import integrity as g

BRANCH='codex/rtx-target-verification-intervention-v1'
ART=ROOT/'artifacts/rtx_target_verification_intervention_v1'
PREFIX='benchmarks/rtx_target_verification_intervention_v1'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def commit(message,paths):
    subprocess.run(['git','add','--sparse','--',*paths],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    r=subprocess.run(['git','commit','-m',message],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode and b'nothing to commit' not in r.stdout:raise RuntimeError(r.stderr.decode(errors='replace'))
    return git('rev-parse','HEAD').decode().strip()
def push():
    subprocess.run(['git','push','--set-upstream','origin',BRANCH],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=1800)
    head=git('rev-parse','HEAD').decode().strip();remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert head==remote;return head
def blob(head,name):
    oid=git('rev-parse',head+':'+name).decode().strip()
    response=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/git/blobs/{oid}'],timeout=600)
    row=json.loads(response);assert row['sha']==oid and row['encoding']=='base64';b=base64.b64decode(row['content'])
    return b,oid

def remote_seal():
    if (OUT/'SEAL_MODE.json').exists():
        mode=read(OUT/'SEAL_MODE.json');assert mode['seal_sha256']==sha(OUT/'PREDICTION_SEAL.json');return
    g.verify_seal(full=True);ART.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(OUT/'PREDICTION_SEAL.json',DOC/'PREDICTION_SEAL.json')
    files=[DOC/name for name in ['PREDICTION_SEAL.json','FREEZE.json','PROTOCOL.json','COHORT.json','INPUT_CONTRACT.json','ASSET_ENVIRONMENT.json']]
    for item in read(OUT/'PREDICTION_SEAL.json')['predictions'].values():
        result=ROOT/item['result'];files.append(result)
        row=read(result)
        files += [result.parent/f for f in row['files'] if f.endswith('tape.jsonl')]
    tarpath=ART/'PREDICTIONS.tar.gz'
    with tarfile.open(tarpath,'w:gz',compresslevel=3) as tf:
        for p in files:tf.add(p,arcname=str(p.relative_to(ROOT)).replace('\\','/'),recursive=False)
    manifest={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
    save(DOC/'PREDICTION_TRANSPORT.json',{'files':manifest,'archive_sha256':sha(tarpath),'bytes':tarpath.stat().st_size,'scope':'all258 prediction records and their own tapes, complete IDs/endpoints and upstream identity bindings'})
    content=commit('Seal all RTX v1 H0/H1 predictions before formal native execution',[PREFIX,'artifacts/rtx_target_verification_intervention_v1/PREDICTIONS.tar.gz'])
    try:
        head=push();remote,oid=blob(head,'artifacts/rtx_target_verification_intervention_v1/PREDICTIONS.tar.gz');assert hashlib.sha256(remote).hexdigest()==sha(tarpath)
        readback=OUT/'prediction-remote-readback.tar.gz';readback.write_bytes(remote);checked=0
        with tarfile.open(readback,'r:gz') as tf:
            for member in tf:
                p=manifest[member.name];b=tf.extractfile(member).read();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];checked+=1
        assert checked==len(manifest)
        receipt={'mode':'REMOTE_BEFORE_NATIVE','readback_pass':True,'commit':head,'blob':oid,'archive_sha256':sha(readback),'files_checked':checked,'seal_sha256':sha(OUT/'PREDICTION_SEAL.json'),'utc':utc(),'timestamp_scope':'remote content membership and local ledger order; not independent absolute process time'}
        save(DOC/'PREDICTION_REMOTE_READBACK.json',receipt);save(OUT/'SEAL_MODE.json',receipt);g.event('REMOTE_READBACK_PASS',commit=head,files=checked,seal_sha256=receipt['seal_sha256'])
    except Exception as exc:
        receipt={'mode':'LOCAL_SEAL_ONLY','seal_sha256':sha(OUT/'PREDICTION_SEAL.json'),'utc':utc(),'remote_attempt_commit':content,'error':repr(exc),'traceback':traceback.format_exc(),'remote_before_native':False}
        save(DOC/'PREDICTION_REMOTE_FAILURE.json',receipt);save(OUT/'SEAL_MODE.json',receipt);g.event('LOCAL_SEAL_ONLY',reason=repr(exc))

def collect():
    paths=[];omitted=[]
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        relative=p.relative_to(OUT)
        if relative.parts[0] in ['native-build','worker-bin','archive','clean-restored','remote-restored','remote-readback']:
            if p.suffix.lower() in ['.exe','.dll']:omitted.append(str(p.relative_to(ROOT)).replace('\\','/'))
            continue
        if p.name.endswith('.tmp') or p.name.startswith('LOCK') or p.name in ['STATE.json','STATUS.json','LEDGER.jsonl']:continue
        paths.append(p)
    # Snapshot mutable progress once; original ledger remains append-only.
    snap=OUT/'archive-snapshot';snap.mkdir(exist_ok=True)
    for name in ['STATUS.json','LEDGER.jsonl']:
        if (OUT/name).exists():shutil.copyfile(OUT/name,snap/name)
    paths=[p for p in paths if snap not in p.parents]
    mapping={str(p.relative_to(ROOT)).replace('\\','/'):p for p in paths}
    for name in ['STATUS.json','LEDGER.jsonl']:
        if (snap/name).exists():mapping[str((OUT/name).relative_to(ROOT)).replace('\\','/')]=snap/name
    save(DOC/'ARCHIVE_OMISSIONS.json',{'paths':sorted(set(omitted)),'external_assets':read(DOC/'ASSET_ENVIRONMENT.json')['files'],'scope':'model weights and external/new runtime binaries omitted; hashes identify omitted assets but offline restore cannot authenticate their bytes'})
    for directory in [DOC,HERE]:
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp'):mapping[str(p.relative_to(ROOT)).replace('\\','/')]=p
    # The frozen original parser is used by execution; retain its complete source.
    for p in (ROOT/'scripts/platform/rtx_trajectory_cost_v4').glob('*.py'):mapping[str(p.relative_to(ROOT)).replace('\\','/')]=p
    return mapping

def archive_and_verify():
    # This snapshot records measured results while clearly leaving archive checks
    # pending. Final report/receipts are committed and read back after the archive.
    report(prearchive=True)
    ART.mkdir(parents=True,exist_ok=True);archive=OUT/'archive';archive.mkdir(exist_ok=True)
    mapping=collect();manifest={'schema':'heterospec.cas.archive.v1','files':{},'omissions':read(DOC/'ARCHIVE_OMISSIONS.json'),'utc':utc()};cas={}
    for name,p in sorted(mapping.items()):
        h=sha(p);manifest['files'][name]={'sha256':h,'bytes':p.stat().st_size};cas.setdefault(h,p)
    save(archive/'MANIFEST.json',manifest);tarpath=archive/'raw-cas-v1.tar.gz'
    with tarfile.open(tarpath,'w:gz',compresslevel=3) as tf:
        tf.add(archive/'MANIFEST.json',arcname='MANIFEST.json',recursive=False)
        for h,p in sorted(cas.items()):tf.add(p,arcname='cas/'+h,recursive=False)
    from restore import restore
    dest=OUT/'clean-restored';restored=restore(tarpath,dest);assert restored['files']==manifest['files']
    with (archive/'restored-verifier.stdout.log').open('wb') as so,(archive/'restored-verifier.stderr.log').open('wb') as se:
        subprocess.run([sys.executable,str(dest/'scripts/platform/rtx_target_verification_intervention_v1/independent_verify.py'),'--root',str(dest),'--output',str(dest/'recompute')],stdout=so,stderr=se,check=True)
    original=read(OUT/'independent-recompute/SUMMARY.json');recomputed=read(dest/'recompute/SUMMARY.json')
    fields=['planned','valid','invalid_units','unexecuted','failed_attempts','g0_arrays','sham_pairs','historical_comparisons','groups','known_cases','seal_mode','task_unit','graph_summary']
    assert all(original[k]==recomputed[k] for k in fields)
    assert read(OUT/'independent-recompute/TASK_COMPARISONS.json')==read(dest/'recompute/TASK_COMPARISONS.json')
    parts=[]
    with tarpath.open('rb') as f:
        while True:
            b=f.read(48*1024*1024)
            if not b:break
            h=hashlib.sha256(b).hexdigest();p=ART/(h+'.part');p.write_bytes(b);parts.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':len(b),'sha256':h})
    shutil.copyfile(archive/'MANIFEST.json',ART/'MANIFEST.json')
    save(ART/'ARCHIVE.json',{'schema':'heterospec.cas.parts.v1','bytes':tarpath.stat().st_size,'sha256':sha(tarpath),'parts':parts,'logical_files':len(mapping),'unique_blobs':len(cas)})
    save(DOC/'ARCHIVE_RECEIPT.json',{'status':'PASS','clean_restore':'PASS','independent_restored_recompute':'PASS','scientific_fields_equal':fields,'archive_sha256':sha(tarpath),'bytes':tarpath.stat().st_size,'logical_files':len(mapping),'parts':len(parts),'utc':utc()})
    g.event('ARCHIVE_RESTORE_VERIFIED',files=len(mapping),archive_sha256=sha(tarpath))

def report(blocked=False,prearchive=False):
    destination=Path(os.environ.get('HETEROSPEC_DELIVERABLE_DIR',str(ROOT/'outputs')));destination.mkdir(parents=True,exist_ok=True)
    status=read(OUT/'STATUS.json');environment=read(DOC/'ASSET_ENVIRONMENT.json')['environment']
    if blocked:
        error=read(DOC/'STOP_REASON.json');text=f"# RTX 实验阻塞报告\n\n状态：{status['status']}。正式计划645条，已有效完成{status['completed']}条；其余未执行。\n\n具体停止原因：{error['error']}。发生于{error['stage']}阶段。原始尝试均保留，不修改历史expected数组。\n\nGPU：{environment['gpu']}。固定base：{BASE}。模型、数据和54个runtime文件身份已核验。G0及后续阶段仅以实际收据为准。\n\n本轮无法作出合格干预或参考恢复结论；/15、/18恢复未建立。恢复前先读STOP_REASON.json、BUDGET.json和RESUME.md；不自动重置预算或开始新科学版本。\n"
    else:
        summary=read(OUT/'independent-recompute/SUMMARY.json');table=read(OUT/'independent-recompute/TASK_COMPARISONS.json');freeze=read(DOC/'FREEZE.json');archive=({'logical_files':0,'archive_sha256':'PENDING','bytes':0} if prearchive else read(DOC/'ARCHIVE_RECEIPT.json'))
        prediction_match=sum(row['comparisons']['H1/N1'] for row in summary['groups'].values())==129
        cases_recovered=all(summary['known_cases'][t]=='restored' for t in ['HumanEval/15','HumanEval/18'])
        no_regressions=all(not row['new_regressions'] for row in summary['groups'].values())
        finding=('固定条件上的第二后端干预闭环及指定参考恢复目标成立。' if prediction_match and cases_recovered and no_regressions else '完整预测闭环'+('成立' if prediction_match else '未成立')+'；主候选'+('满足' if cases_recovered and no_regressions else '没有满足')+'指定参考恢复及无新增回归的目标。')
        text=f"# RTX 完整实验报告\n\n状态：VERIFIED_COMPLETE。645/645正式单元有效，失败尝试{summary['failed_attempts']}；独立raw重算及干净归档恢复均通过。\n\n本机GPU：{environment['gpu']}；Windows {environment['os']['Version']}；Python3.11.9；CUDA0，target37/37及draft29/29层offload。固定base `{BASE}`；implementation `{freeze['implementation_commit']}`。模型、数据与54个原runtime文件SHA256匹配V4。原CLI默认12线程与旧文档24线程不一致，本轮显式24线程重新资格；早期记录保留。\n\nG0覆盖120条完整数组、30对plain/sham；其中45条H资格复用同一未改变H路径的实际记录，75条native在显式24线程下另行执行。此前默认线程资格120条及2条pilot单独保留。6个MBPP工程任务的30条输出不纳入正式分母。负例、恢复及启动工具返回后后台生存fixture均通过，不能据此承诺注销或重启生存。\n\n| 分组 | H0/N0 | H1/N1 | N0/R | N1/R | 恢复任务 | 新增回归 |\n|---|---:|---:|---:|---:|---:|---:|\n"
        for name,label in [('old19','旧19'),('new24','新24')]:
            row=summary['groups'][name];n=row['pairs'];text+='| '+label+' | '+' | '.join(f"{row['comparisons'][k]}/{n}" for k in ['H0/N0','H1/N1','N0/R','N1/R'])+f" | {len(row['restored'])} | {len(row['new_regressions'])} |\n"
        text+='\n结论：'+finding+'\n\n已知案例：'+ '；'.join(t+': '+summary['known_cases'][t] for t in ['HumanEval/15','HumanEval/18','HumanEval/25'])+'。restored表示本轮三次重复均完整恢复指定参考；remaining_deviation表示没有完整恢复。\n\n'
        text+='| 实际图观察路径 | caller token数集合 | occupied token数集合 | logits输出数集合 |\n|---|---|---|---|\n'
        for path,values in sorted(summary['graph_summary'].items()):
            text+='| '+path+' | '+str(values['caller_lengths'])+' | '+str(values['occupied_counts'])+' | '+str(values['logits_output_counts'])+' |\n'
        text+='\n原版R正式路径未增加图回调；其caller日志及G0观察版控制独立保留。表中只列实际捕获的图，未用容量值推算occupied值。\n\n'
        text+='| 任务 | H0/N0 | H1/N1 | N0/R | N1/R | 重复稳定 | 参考变化 |\n|---|---:|---:|---:|---:|---|---|\n'
        for r in table:text+='| '+r['task']+' | '+' | '.join(str(r['comparisons'][k]['matches'])+'/3' for k in ['H0/N0','H1/N1','N0/R','N1/R'])+' | '+str(r['stable'])+' | '+r['reference_change']+' |\n'
        text+=f"\n旧R/H0/N0全部171条历史数组及endpoint比较通过。新24题来自固定官方sanitized MBPP commit e49bbfe381c9c0e564b937f1c4e163a2273c65cc，数据SHA256 ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9；静态曝光排除及排序在新题forward前完成。新仅表示审计范围内无已知本项目执行曝光。\n\nH及native保持各自caller grouping。Prefill和draft UB2固定，target continuation候选UB1。图回调保留实际caller tokens、positions、logits mask和occupied graph维度，容量不等于实际token数。首个pending在source采样并accept一次；完整KV、pending logits、source-before/source-after/destination字节及clone行为控制保留。Opaque sampler无法序列化，不宣称其字节相等。\n\n258条H0/H1预测和各自产生的proposal tapes封存后，native才开始。封存模式：{summary['seal_mode']}。原生接收prompt、资产和固定参数，使用自己的live draft，未输入H tapes或未来答案。本机append-only hash ledger及Git内容归属支持顺序，不认证独立绝对实验时间。\n\n独立parser直接重读raw，未导入研究比较helpers。归档{archive['logical_files']}个逻辑文件，SHA256 `{archive['archive_sha256']}`，{archive['bytes']}字节；CAS逐文件还原并重算科学字段一致。省略权重及外部/新runtime二进制，离线哈希清单不能认证省略字节。\n\n贡献范围：固定单模型对、RTX/CUDA、旧19及新24任务上的预测干预native闭环和有限参考恢复计数。不推断功能正确率、生产lossless、唯一kernel、必要/最小性、速度或能耗。具体是否成功以H1/N1完整匹配与/15、/18参考恢复共同判断。未改论文、旧实验状态或作者tag。\n"
    if prearchive:
        text=text.replace('独立raw重算及干净归档恢复均通过。','独立raw重算通过；本文件为归档前快照，干净归档恢复与远程交付尚待执行，最终报告及收据另行提交并回读。').replace('CAS逐文件还原并重算科学字段一致。','CAS归档、逐文件还原及科学字段重算尚未执行，不能由本快照声称通过。')
    (DOC/'STUDY_REPORT.md').write_text(text,encoding='utf-8',newline='\n');(destination/'RTX_实验报告.md').write_text(text,encoding='utf-8',newline='\n')
    for name in ['SUMMARY.json','TASK_COMPARISONS.csv','TASK_COMPARISONS.json','GRAPH_OBSERVATIONS.json']:
        p=OUT/'independent-recompute'/name
        if p.exists():shutil.copyfile(p,destination/name)
    shutil.copyfile(DOC/'RESUME.md',destination/'RESUME.md')

def final_delivery():
    report()
    # Keep each transport push bounded even when the full evidence is several GB.
    # The final index is committed only after every immutable CAS part is uploaded.
    receipt={'status':'LOCAL_ONLY','utc':utc()}
    try:
        index=read(ART/'ARCHIVE.json');pending=[];batch_bytes=0
        for part in index['parts']:
            pending.append(part['path']);batch_bytes+=part['bytes']
            if batch_bytes>=384*1024*1024:
                commit('Upload immutable RTX v1 CAS evidence parts',pending);push();pending=[];batch_bytes=0
        if pending:commit('Upload remaining RTX v1 CAS evidence parts',pending);push()
        commit('Archive and independently verify complete RTX intervention v1 evidence',[PREFIX,'artifacts/rtx_target_verification_intervention_v1'])
        head=push();index=read(ART/'ARCHIVE.json');remote=OUT/'remote-readback';remote.mkdir(exist_ok=True);tarpath=remote/'raw-cas-v1.tar.gz';received=[]
        with tarpath.open('wb') as f:
            for p in index['parts']:
                b,oid=blob(head,p['path']);assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];f.write(b);received.append({'path':p['path'],'blob':oid,'sha256':p['sha256']})
        assert sha(tarpath)==index['sha256']
        from restore import restore
        dest=OUT/'remote-restored';restore(tarpath,dest)
        with (remote/'verifier.stdout.log').open('wb') as so,(remote/'verifier.stderr.log').open('wb') as se:
            subprocess.run([sys.executable,str(dest/'scripts/platform/rtx_target_verification_intervention_v1/independent_verify.py'),'--root',str(dest),'--output',str(dest/'recompute')],stdout=so,stderr=se,check=True)
        orig=read(OUT/'independent-recompute/SUMMARY.json');other=read(dest/'recompute/SUMMARY.json')
        for k in ['valid','groups','known_cases','failed_attempts','seal_mode']:assert orig[k]==other[k]
        receipt={'status':'DELIVERY_COMPLETE','utc':utc(),'content_commit':head,'archive_sha256':index['sha256'],'readback':'all remote parts, clean restore, independent raw verification PASS','parts':received}
    except Exception as exc:receipt.update(status='DELIVERY_PARTIAL',error=repr(exc),traceback=traceback.format_exc(),utc=utc())
    save(DOC/'DELIVERY_RECEIPT.json',receipt)
    commit('Record RTX v1 remote restore delivery receipts',[PREFIX])
    try:
        head=push();body=OUT/'PR_BODY.md'
        body.write_text('This study tests one target post-prefill UB2-to-UB1 intervention while preserving UB2 prefill and live draft. It retains 19 exposed regression tasks plus24 statically selected MBPP tasks, three repetitions and all645 planned formal units.\n\nSee benchmarks/rtx_target_verification_intervention_v1/STUDY_REPORT.md for actual qualification, full-array results, deviations, prediction seal order, independent raw verification and delivery status. Existing scientific records and manuscript artifacts are unchanged. No merge, release or performance claim.\n\nValidation: original/instrumented and plain/sham qualification; independent raw parser; clean CAS archive restoration and scientific-field comparison. Remote status is recorded separately in DELIVERY_RECEIPT.json.\n',encoding='utf-8')
        existing=subprocess.check_output(['gh','pr','list','--repo','leecdiang/HeteroSpec','--head',BRANCH,'--json','url'],text=True)
        prs=json.loads(existing)
        url=prs[0]['url'] if prs else subprocess.check_output(['gh','pr','create','--repo','leecdiang/HeteroSpec','--draft','--base','main','--head',BRANCH,'--title','RTX target verification intervention v1: qualified finite-cohort evidence','--body-file',str(body)],text=True).strip()
        if prs:
            subprocess.run(['gh','pr','edit',url,'--repo','leecdiang/HeteroSpec','--title','RTX target verification intervention v1: qualified finite-cohort evidence','--body-file',str(body)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        receipt.update(pr=url,final_commit=head);save(DOC/'PR_RECEIPT.json',{'url':url,'draft':True,'head':head,'utc':utc()})
    except Exception as exc:receipt['pr_error']=repr(exc)
    save(DOC/'DELIVERY_RECEIPT.json',receipt)
    commit('Record additive RTX v1 Draft PR identity',[PREFIX]);push()
    report()
    destination=Path(os.environ.get('HETEROSPEC_DELIVERABLE_DIR',str(ROOT/'outputs')))
    shutil.copyfile(DOC/'DELIVERY_RECEIPT.json',destination/'DELIVERY_RECEIPT.json')
    if 'pr' in receipt:
        for p in [DOC/'STUDY_REPORT.md',destination/'RTX_实验报告.md']:
            with p.open('a',encoding='utf-8') as f:f.write('\n远程交付：'+receipt['status']+'。Draft PR：'+receipt['pr']+'。\n')
    finalhead=commit('Publish final Chinese RTX v1 report and Draft PR link',[PREFIX]);push()
    remote_report,report_blob=blob(finalhead,PREFIX+'/STUDY_REPORT.md');assert hashlib.sha256(remote_report).hexdigest()==sha(DOC/'STUDY_REPORT.md')
    bundle=OUT/'archive/research.git.bundle';subprocess.run(['git','bundle','create',str(bundle),'HEAD','^'+BASE],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    save(OUT/'FINAL_LOCAL_SEAL.json',{'head':finalhead,'report_blob':report_blob,'report_sha256':sha(DOC/'STUDY_REPORT.md'),'bundle_sha256':sha(bundle),'delivery':receipt,'utc':utc()})

def blocked_delivery():
    report(True)
    save(DOC/'DELIVERY_RECEIPT.json',{'status':'LOCAL_ONLY','reason':'qualification/capture stop; complete retained prefix pending archival transport','utc':utc()})
    commit('Retain RTX intervention qualification stop and unexecuted schedule',[PREFIX,'scripts/platform/rtx_target_verification_intervention_v1'])
    try:
        head=push();body=OUT/'BLOCKED_PR_BODY.md';body.write_text('Qualification stopped before the full planned experiment could be completed. The exact reason, actual counts and retained evidence are recorded in benchmarks/rtx_target_verification_intervention_v1/STOP_REASON.json and STUDY_REPORT.md. No qualified intervention or reference-recovery conclusion is claimed. This additive Draft PR preserves the investigation and unexecuted schedule for review.\n',encoding='utf-8')
        url=subprocess.check_output(['gh','pr','create','--repo','leecdiang/HeteroSpec','--draft','--base','main','--head',BRANCH,'--title','RTX target intervention v1: retained qualification stop','--body-file',str(body)],text=True).strip()
        save(DOC/'PR_RECEIPT.json',{'url':url,'draft':True,'head':head,'utc':utc()});save(DOC/'DELIVERY_RECEIPT.json',{'status':'DELIVERY_PARTIAL','pr':url,'head':head,'raw':'local retained prefix','utc':utc()})
    except Exception as exc:save(DOC/'DELIVERY_FAILURE.json',{'error':repr(exc),'utc':utc()})
