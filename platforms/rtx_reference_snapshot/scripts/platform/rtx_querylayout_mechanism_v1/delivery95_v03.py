"""CPU-only deterministic results, complete CAS, real local/remote restore and Draft PR."""
from common95 import *
from freeze95 import archive,split
import shutil,io
CODE=Path(__file__).parent
BASE='design/rtx-querylayout-mechanism-20261012'
TITLE='RTX result: operator replay and same-reference repair cost'

def cpu_audit(repo,local,out):
    subprocess.run([str(PYTHON),str(CODE/'audit95_v02.py'),'--repo',str(repo),'--local',str(local),'--out',str(out)],check=True)
    return read(out)

def report(result):
    lines=['# RTX query-layout result','', 'Design #95; authenticated #94/#91 ancestry. Exposed tasks and two adjacent sessions; no new-input or cross-date claim.','',
           'Counts: '+json.dumps(result['counts'],ensure_ascii=False),'',
           '## Same-reference native qualification and request cost','',
           '|Family|Pair|Qualified|Cost ratio|Regressions|','|---|---|---|---:|---|']
    for f,r in result['families'].items():
        for p in r['comparisons']:lines.append('|'+f+'|'+p['pair']+'|'+str(p['qualified'])+'|'+('null' if p['cost_ratio'] is None else format(p['cost_ratio'],'.6f'))+'|'+(', '.join(p['regressions']) or 'none')+'|')
    lines+=['','PQ/QB and GS/QB >1 favor QB as consistency-repair implementation. M_QB/C_QB is incremental draft value; R ratios are complete same-reference request comparisons, not isolated repair component times. Absolute per-task/session medians, domains, every regression, mismatch and missing slot are in RESULTS.json.','',
        '## Mechanism and limits','',json.dumps({k:v for k,v in result['mechanism'].items() if k in ['status','contexts','expected_contexts','own_path_correspondence','native_model_decision_claim','kernel_scheduling','reason']},ensure_ascii=False),
        '', 'Actual captured bytes and independent arithmetic comparison are archived. Runtime operation dispatch is real; kernel symbol, algorithm and launch scheduling remain UNKNOWN. Fused post-mask scores are NOT_COMPARABLE. No synthetic full-path logits or reduction-order proof. Capture-on/off and own-path correspondence are separate controls; failures narrow native causal inference. Historical MBPP229 q6/8 geometry is NOT_ADMITTED by frozen q<=4/k3 scope.','',
        'MODEL_TIMING_UNAVAILABLE remains true. No formal-wall-time fitting, energy, throughput or component-cost attribution.','',
        '## Scientific closeout','', '|Statement|Status|Allowed scope|','|---|---|---|']
    for c in result['scientific_closeout']:lines.append('|'+c['statement']+'|'+c['status']+'|'+c['allowed_wording']+'|')
    lines+=['','## Reproduction','', 'Run the standalone stdlib audit95_v02.py against repository and local directories reconstructed from RAW_EVIDENCE. ZIP INDEX.json covers every retained logical byte. SOURCE_RUNTIME.zip has its own complete index; the inherited PR91 scientific archive and source/runtime are preserved as immutable nested archives. Independent local and freshly authenticated GitHub-byte restoration receipts are mandatory. Failed attempts and started slots are retained; there are no formal retries. No parent archive, manuscript, main or release was modified.','']
    lines += ['', '## Preserved implementation and delivery faults', '', 'Four original Smol/Llama PQ warm failures remain charged and were never retried. Prospective V02 changes only the host graph capacity bound by the predeclared maximum q=4; all numerical DLLs and operators are unchanged. QB eligibility was recovered from existing final tensor aliases and twelve exact outputs, without GPU reruns. Original frozen files remain immutable. V03 repairs only parent-archive inclusion and auditor metadata after all 2016 formal requests completed; the failed archive index, manifest, original reports and controller failure are retained. See IMPLEMENTATION_FAULT_CORRECTION.json, RESOURCE_CORRECTION.json and DELIVERY_CORRECTION_V03.json.', '']
    return '\n'.join(lines)

def extract_checked(path,target):
    target.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(path) as z:
        index=read_zip_index(z);assert set(z.namelist())==set(index)|{'INDEX.json'}
        for name,v in index.items():
            pp=target/name;assert pp.resolve().is_relative_to(target.resolve()),'unsafe archive member'
            b=z.read(name);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
            pp.parent.mkdir(parents=True,exist_ok=True)
            with pp.open('xb') as f:f.write(b)
    return len(index)
def read_zip_index(z):return json.loads(z.read('INDEX.json'))['files']
def check_nested(path):
    with zipfile.ZipFile(path) as z:
        index=read_zip_index(z)
        for n,v in index.items():
            b=z.read(n);assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256']
    return len(index)

def restore_verify(path,target,expected):
    logical=extract_checked(path,target)
    nested=check_nested(target/'local/SOURCE_RUNTIME.zip')
    corrected=check_nested(target/'local/SOURCE_RUNTIME_V02.zip')
    parent=target/'local/parent-remote/RAW_EVIDENCE.zip';parent_count=check_nested(parent)
    actual=cpu_audit(target/'repository',target/'local',target/'INDEPENDENT_RECOMPUTED.json');assert actual==expected,'restored independent result differs'
    return dict(status='PASS',logical_files=logical,source_runtime_files=nested,corrected_source_runtime_files=corrected,parent_scientific_files=parent_count,archive_sha256=sha(path),independent_recomputed_sha256=sha(target/'INDEPENDENT_RECOMPUTED.json'),exact_object_equal=True)

def publish_paths(paths,message):
    subprocess.run(['git','add','--sparse','-f','--',*[p.relative_to(REPO).as_posix() for p in paths]],cwd=REPO,check=True)
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=REPO).returncode:subprocess.run(['git','commit','-m',message],cwd=REPO,check=True)
    retry(lambda:subprocess.run(['git','push','-u','origin',git('branch','--show-current')],cwd=REPO,check=True),'result-push')
    return git('rev-parse','HEAD')

def paths():return [p for root in [PUB,CODE] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]

def closeout():
    status('CPU_INDEPENDENT_CLOSEOUT')
    primary=LOCAL/'INDEPENDENT_RESULTS.json'
    result=read(primary) if primary.exists() else cpu_audit(REPO,LOCAL,primary)
    for name,value in [('RESULTS.json',result),('QUALIFICATION.json',{f:r['qualification'] for f,r in result['families'].items()}),('INDEPENDENT_CPU.json',dict(status=result['status'],script_sha256=sha(CODE/'audit95_v02.py'),result_sha256=sha(primary),synthetic_checks=read(PUB/'SYNTHETIC_CHECKS_V02.json'),script_path='scripts/platform/rtx_querylayout_mechanism_v1/audit95_v02.py'))]:
        p=PUB/name
        if not p.exists():save(p,value)
        else:assert read(p)==value
    md=PUB/'RESULTS.md'
    if not md.exists():md.write_text(report(result),encoding='utf-8')
    cas=LOCAL/'RAW_EVIDENCE.zip';manifest=PUB/'RAW_EVIDENCE_MANIFEST.json'
    if not cas.exists():
        status('SCIENTIFIC_ARCHIVE_BUILD')
        files={'repository/'+p.relative_to(REPO).as_posix():p for p in paths()}
        for p in LOCAL.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(LOCAL)
            if rel.parts[0] in ['native','native-repair','parent-restored','restore-local','restore-remote']:continue
            if rel.parts[0]=='parent-remote' and p.name!='RAW_EVIDENCE.zip':continue
            if rel.as_posix() in ['STATUS.json','RAW_EVIDENCE.zip','controller.lock','controller-v02.lock']:continue
            files['local/'+rel.as_posix()]=p
        info=archive(cas,files);parts=split(cas,'RAW_EVIDENCE');save(manifest,dict(**info,parts=parts,complete_untruncated_scientific_archive=True))
    local_receipt=PUB/'LOCAL_RESTORE.json'
    if not local_receipt.exists():
        status('LOCAL_SCIENTIFIC_RESTORE')
        save(local_receipt,restore_verify(cas,LOCAL/'restore-local',result))
    cas_head=publish_paths(paths(),'Archive RTX operator replay and same-reference cost evidence')
    remote_receipt=PUB/'REMOTE_RESTORE.json'
    if not remote_receipt.exists():
        status('ACTUAL_AUTHENTICATED_REMOTE_RESTORE',commit=cas_head)
        tree=api('git/trees/'+cas_head+'?recursive=1');assert not tree.get('truncated');items={v['path']:v for v in tree['tree']}
        remote=LOCAL/'remote-scientific';remote.mkdir(exist_ok=True);restored=remote/'RAW_EVIDENCE.zip';checked=[]
        with restored.open('xb') as f:
            for part in read(manifest)['parts']:
                p=PUB/part['name'];oid=items[p.relative_to(REPO).as_posix()]['sha'];b=verified_blob(oid)
                assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'];f.write(b);checked.append(dict(**part,git_blob=oid))
        assert sha(restored)==read(manifest)['sha256'] and restored.stat().st_size==read(manifest)['bytes']
        receipt=restore_verify(restored,LOCAL/'restore-remote',result)
        save(remote_receipt,dict(**receipt,utc=now(),commit=cas_head,actual_authenticated_remote_bytes=True,parts=checked))
    final_head=publish_paths(paths(),'Verify independent local and authenticated remote RTX restoration')
    for name in ['RESULTS.json','QUALIFICATION.json','REMOTE_RESTORE.json','LOCAL_RESTORE.json']:
        path=PUB/name;remote=api('contents/'+path.relative_to(REPO).as_posix()+'?ref='+final_head,raw=True);assert remote==path.read_bytes()
    prfile=LOCAL/'RESULT_PR.json'
    if not prfile.exists():
        prs=json.loads(subprocess.check_output(['gh','pr','list','--repo','leecdiang/HeteroSpec','--head',git('branch','--show-current'),'--state','all','--json','url,number,isDraft,baseRefName,headRefName']))
        if prs:
            assert len(prs)==1;pr=prs[0];assert pr['isDraft'] and pr['baseRefName']==BASE
        else:
            body=LOCAL/'RESULT_PR_BODY.md';text=report(result)
            # GitHub description is concise; all detailed arrays/tables remain in indexed files.
            intro='Actual bounded RTX query-layout study under PR95, inheriting authenticated independent PR94/PR91 audit.\n\n'
            counts=json.dumps(result['counts'],ensure_ascii=False)
            table='\n'.join(text.split('## Same-reference native qualification and request cost')[1].split('## Mechanism and limits')[0].strip().splitlines()[:24])
            body.write_text(intro+'Exact counts: `'+counts+'`\n\n'+table+'\n\nMechanism: '+result['mechanism']['status']+'. Kernel scheduling UNKNOWN; full-model decision causality UNRESOLVED. MODEL_TIMING_UNAVAILABLE retained. Negative/blocked arms and every missing/mismatched slot are preserved with null qualified costs.\n\nValidation: synthetic CPU falsification, independent stdlib recomputation, complete indexed scientific CAS, local and actual authenticated fresh GitHub restoration, exact-object recomputation. See benchmarks/rtx_querylayout_mechanism_v1/RESULTS.md and RESULTS.json. No main/manuscript/release or parent observations modified. AI assisted this private experiment implementation.\n',encoding='utf-8')
            url=retry(lambda:subprocess.check_output(['gh','pr','create','--repo','leecdiang/HeteroSpec','--base',BASE,'--head',git('branch','--show-current'),'--draft','--title',TITLE,'--body-file',str(body)]),'draft-result-PR').decode().strip()
            pr=json.loads(subprocess.check_output(['gh','pr','view',url,'--repo','leecdiang/HeteroSpec','--json','url,number,isDraft,baseRefName,headRefName']))
        save(prfile,dict(**pr,utc=now(),head=final_head,actual_restoration_verified=True))
    status('COMPLETE_DRAFT_RESULT_PR',url=read(prfile)['url'],counts=result['counts'],mechanism=result['mechanism']['status'])
    return read(prfile)

if __name__=='__main__':
    import correction95_v02
    correction95_v02.delivery95.closeout=closeout
    correction95_v02.corrected_delivery()
