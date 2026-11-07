"""V3 pre-forward exposure audit, adapted from V2 with H2 included and all relevant current-main archive indices."""
import gzip,hashlib,io,json,re,subprocess,tarfile,tempfile,zipfile,sys
from pathlib import Path
from datetime import datetime,timezone
from prepare import ROOT,STUDY,OLD,save
SALT='RTX_TRAJECTORY_SUFFICIENCY_V3|reserved|20261001|'
IDS=re.compile(r'HumanEval[/_\-](\d+)')
TEXT={'.json','.jsonl','.txt','.md','.log','.csv','.yaml','.yml'}
OUTPUT=re.compile(r'generated_ids|generated_token_ids|committed_ids|proposal_ids|logits_sha256|process_toke|next token:|"logits"|"token_ids"|"first_divergence"|"exact"\s*:|"timings"|"completion"|"prediction_ids"|"native_events"|"output_ids"|"accepted_ids"')
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    with gzip.open('D:/HeteroSpec-PC/datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:tasks={r['task_id']:r['prompt'] for r in map(json.loads,f)}
    catalog=[];exclusions={t:[] for t in tasks};errors=[];seen=set();archive_seen=set()
    def inspect(label,data):
        text=data.decode('utf-8-sig',errors='replace'); low=label.lower();ids={'HumanEval/'+i for i in IDS.findall(text+' '+label)}&tasks.keys()
        kind='NO_TASK_ASSOCIATION';why='no HumanEval identity or original prompt'
        pure=False;mentioned=sorted(ids)
        try:
            values=[json.loads(x) for x in text.splitlines()] if Path(low).suffix=='.jsonl' else [json.loads(text)]
            pure=bool(values) and all(isinstance(v,dict) and (set(v)<={'status','eligible','selected','errors','catalog_entries'} and 'selected' in v or v.get('vocab_only') is True and v.get('forward_calls')==0 and set(v)<={'task_id','prompt_ids','forward_calls','vocab_only'}) for v in values)
            if Path(low.rsplit('!',1)[-1]).name=='execution_ledger.jsonl':
                actual=[v for v in values if v.get('event') in ['process_started','model_call_completed','native_forward_observed']]
                ids={v['task_id'] for v in actual if v.get('task_id') in tasks};pure=not ids
        except (ValueError,TypeError):pass
        if not ids and OUTPUT.search(text):ids={t for t,p in tasks.items() if p in text}
        if pure:kind='INPUT_OR_SOURCE_ONLY';why='strict JSON audit summary or vocab-only zero-forward metadata; rejected launch is not an output exposure'
        elif ids:
            source='/frozen_source/' in low or '!frozen_source/' in low
            inputfile=Path(low).name in ['prompt.txt','user_specification.md','preregistration.md','protocol.json','joint_protocol.json','reserved_set.json','reserved_validation_set.json','read_receipts.json','input_contract.json'] or '/prompts/' in low
            if inputfile or source and not OUTPUT.search(text):kind='INPUT_OR_SOURCE_ONLY';why='input, protocol or frozen source; no result inferred from membership'
            elif any(w in Path(low.rsplit('!',1)[-1]).name for w in ['eligible','universe','inventory','manifest','identity','freeze','exposure','selection','schedule']):
                kind='INVENTORY_ONLY';why='identity or universe listing without inference events; original exclusions retained separately'
            elif OUTPUT.search(text):kind='OUTPUT_EXPOSED';why='model output, committed IDs, scores or scientific comparison present'
            elif any(w in low for w in ['report','closeout','results','run','native','stdout','stderr','telemetry','analysis','capture']):kind='AMBIGUOUS_EXCLUDED';why='task associated with result-bearing record; conservative exclusion'
            else:kind='INPUT_OR_SOURCE_ONLY';why='task listing without observed output-bearing fields'
        row={'path':label,'bytes':len(data),'sha256':digest(data),'task_ids':sorted(ids),'mentioned_input_task_ids':mentioned,'classification':kind,'reason':why}
        catalog.append(row)
        if kind in ['OUTPUT_EXPOSED','AMBIGUOUS_EXCLUDED']:
            for t in ids:exclusions[t].append({'path':label,'sha256':row['sha256'],'reason':why})
    def archive(label,stream,h=None):
        if h and h in archive_seen:return
        if h:archive_seen.add(h)
        try:
            with tarfile.open(fileobj=stream,mode='r|*') as a:
                for m in a:
                    if not m.isfile():continue
                    if Path(m.name).suffix.lower() in TEXT:inspect(label+'!'+m.name,a.extractfile(m).read())
                    elif m.name.endswith(('.tar.gz','.tgz')):archive(label+'!'+m.name,io.BytesIO(a.extractfile(m).read()))
        except Exception as e:errors.append({'path':label,'error':repr(e)})
    prior=json.loads((ROOT/'benchmarks/rtx_transfer_latency_v1/RESERVED_SET.json').read_text(encoding='utf-8'))
    for t in prior['excluded_task_ids']:exclusions[t].append({'path':'PR42:RESERVED_SET.json','reason':'retain prior conservative known/ambiguous exposure exclusion'})
    roots=['C:/Users/ASUS/Documents/Codex','C:/Users/ASUS/Downloads','C:/Users/ASUS/Desktop','D:/HeteroSpec-PC','D:/','E:/','F:/']
    if '--reclassify-preserved-catalog' in sys.argv:
        cached=json.loads((ROOT/'work/audit-attempts/attempt2/exposure_catalog.json').read_text(encoding='utf-8'))
        errors=cached['errors'];catalog=cached['catalog']
        for row in catalog:
            low=row['path'].lower()
            # Correct only demonstrable audit selection summaries, never inference data.
            name=Path(low.replace('\\','/')).name
            if name.startswith('audit_stdout') and '!' not in row['path'] and row['task_ids']:
                payload=Path(row['path']).read_bytes()
                if digest(payload)!=row['sha256']:raise RuntimeError('cached audit summary bytes changed')
                v=json.loads(payload)
                if set(v)<={'status','eligible','selected','errors','catalog_entries'} and isinstance(v.get('selected'),list):
                    row['classification']='INPUT_OR_SOURCE_ONLY';row['reason']='auditor selection/count summary only; no model output or inference events'
            if row['classification'] in ['OUTPUT_EXPOSED','AMBIGUOUS_EXCLUDED']:
                for t in row['task_ids']:exclusions[t].append({'path':row['path'],'sha256':row['sha256'],'reason':row['reason']})
        archive_seen=set(r['path'].split('!')[0] for r in catalog if '!' in r['path'])
        files=[];roots_to_scan=[]
    else:roots_to_scan=roots
    files=[]
    for root in roots_to_scan:
        if not Path(root).exists():continue
        cmd=['rg','--files','--hidden','--no-ignore',root]
        for g in ['!.git/**','!node_modules/**','!AppData/**','!$RECYCLE.BIN/**','!System Volume Information/**','!.venv*/**','!python311/**','!hf-cache/**','!models/**','!datasets/**','!tools/**']:cmd+=['-g',g]
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # Protected non-scientific folders are scope exclusions; actual relevant reads fail closed below.
        for name in p.stdout.decode('utf-8',errors='replace').splitlines():
            path=Path(name);key=str(path).lower().replace('\\','/')
            if key in seen:continue
            seen.add(key)
            if not any(s in key for s in ['heterospec','rtx-','b570','humaneval','5070','358h','m4_']):continue
            if any('/'+s+'/' in key for s in ['.git','node_modules','models','datasets','tools','vendor','pinned-source','llama-source','timer-source','timer-build','python311','hf-cache']):continue
            if '/rtx_trajectory_cost_v3/' in key or '/work/h2-bin/' in key:continue
            if path.suffix.lower() in TEXT or key.endswith(('.tar.gz','.tgz','.zip')):files.append(path)
    for path in sorted(files):
        try:
            if path.name.lower().endswith(('.tar.gz','.tgz')):
                if 'source' in path.name.lower():continue
                h=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
                with path.open('rb') as f:archive(str(path),f,h)
            elif path.suffix.lower()=='.zip':
                with zipfile.ZipFile(path) as z:
                    for m in z.infolist():
                        if Path(m.filename).suffix.lower() in TEXT:inspect(str(path)+'!'+m.filename,z.read(m))
            else:inspect(str(path),path.read_bytes())
        except Exception as e:errors.append({'path':str(path),'error':repr(e)})
    # All relevant published branch heads are either ancestors of the audited
    # main or separately scanned for their added/modified scientific members.
    branches=json.loads((ROOT/'work/BRANCH_SCOPE.json').read_text(encoding='utf-8')) if (ROOT/'work/BRANCH_SCOPE.json').exists() else []
    extras=[r['sha'] for r in branches if not r['ancestor_of_main']]
    refs=extras if '--reclassify-preserved-catalog' in sys.argv else ['61a1eb104d9bd1f6220a066d797dcc10dfed268d','abff99356815371648dc38f1466e66701e96840e',*extras]
    for ref in refs:
        baseline='abff99356815371648dc38f1466e66701e96840e' if ref in extras else 'f8290281156f6b3de8fbc8b44fd10a4afa7bcd89'
        names=subprocess.check_output(['git','diff','--name-only','--diff-filter=AM',baseline,ref],cwd=ROOT,text=True).splitlines()
        blobs={}
        for name in names:
            if Path(name).suffix.lower() not in TEXT:continue
            b=subprocess.check_output(['git','show',ref+':'+name],cwd=ROOT);blobs[name]=b;inspect('git:'+ref+':'+name,b)
        for name,b in blobs.items():
            if 'ARCHIVE' not in Path(name).name.upper():continue
            obj=json.loads(b)
            def find(v):
                if isinstance(v,dict):
                    if isinstance(v.get('parts'),list):yield v
                    for x in v.values():yield from find(x)
                elif isinstance(v,list):
                    for x in v:yield from find(x)
            for a in find(obj):
                with tempfile.TemporaryFile() as f:
                    assembled=hashlib.sha256()
                    for part in a['parts']:
                        pn=part.get('path',part.get('name',part.get('file')))
                        if not pn:raise RuntimeError('unrecognized shard identity')
                        if not pn.startswith('artifacts/'):pn=str(Path(name).parent/pn).replace('\\','/')
                        payload=subprocess.check_output(['git','show',ref+':'+pn],cwd=ROOT)
                        expected=part.get('sha256')
                        if expected and digest(payload)!=expected:raise RuntimeError('shard digest differs')
                        f.write(payload);assembled.update(payload)
                    expected=a.get('sha256',a.get('archive_sha256'))
                    if expected and assembled.hexdigest()!=expected:raise RuntimeError('assembled archive digest differs')
                    f.seek(0);archive('git:'+ref+':'+name+'!logical_archive',f,assembled.hexdigest())
    prior_v2=json.loads((ROOT/'benchmarks/rtx_independent_proposal_replay_v2/RESERVED_SET.json').read_text(encoding='utf-8'))
    for t in tasks:
        if t not in prior_v2['eligible_pool'] or t in prior_v2['selected_task_ids']:
            exclusions[t].append({'path':'main:H2V2:RESERVED_SET.json','reason':'retain prior conservative exclusions and all 24 executed H2 V2 reserved tasks'})
    eligible=sorted(t for t in tasks if not exclusions[t]);keys={t:digest((SALT+t).encode()) for t in eligible};selected=sorted(eligible,key=lambda t:(keys[t],t))[:24]
    status='AUDIT_BLOCKED' if errors else ('PASS' if len(selected)==24 else 'RESERVED_POOL_BLOCKED')
    save(ROOT/'work/exposure_catalog.json',{'catalog':catalog,'errors':errors})
    save(STUDY/'EXPOSURE_AUDIT.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':status,'scope_roots':roots,'branch_scope':branches,'extra_branch_heads_scanned':extras,'git_heads':['61a1eb104d9bd1f6220a066d797dcc10dfed268d','abff99356815371648dc38f1466e66701e96840e'],'catalog_entries':len(catalog),'logical_unique_archives':len(archive_seen),'catalog_sha256':digest((ROOT/'work/exposure_catalog.json').read_bytes()),'errors':errors,'exclusion_reasons':{t:e for t,e in exclusions.items() if e},'eligible_pool':eligible,'new_inference_executed':False,'auditor_sha256':digest(Path(__file__).read_bytes()),'retained_scan_catalog_sha256':digest((ROOT/'work/audit-attempts/attempt2/exposure_catalog.json').read_bytes()) if '--reclassify-preserved-catalog' in sys.argv else None,'metadata_correction':'Only two hash-verified AUDIT_STDOUT pure selection summaries reclassified; raw/output/ambiguous classifications retained' if '--reclassify-preserved-catalog' in sys.argv else None,'scope_limit':'available host scientific directories and exact PR objects; protected system and model/vendor/dataset trees excluded'})
    template='Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'
    save(STUDY/'RESERVED_SET.json',{'status':status,'salt':SALT,'universe':sorted(tasks),'eligible_pool':eligible,'selection_keys':keys,'selected_task_ids':selected if status=='PASS' else [],'input_hashes':{t:digest((template+tasks[t]).encode('utf-8')) for t in selected},'model_forward_count':0,'tokenizer_forward_count':0})
    print(json.dumps({'status':status,'eligible':len(eligible),'selected':selected,'errors':errors,'catalog_entries':len(catalog)}))
if __name__=='__main__':main()
