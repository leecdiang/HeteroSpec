"""V2 pre-forward exposure audit, including V1 outputs and logical shard archives."""
import gzip,hashlib,io,json,re,subprocess,tarfile,tempfile,zipfile
from pathlib import Path
from datetime import datetime,timezone
from prepare import ROOT,STUDY,OLD,save
SALT='RTX_INDEPENDENT_PROPOSAL_REPLAY_V2|reserved|20261001|'
IDS=re.compile(r'HumanEval[/_\-](\d+)')
TEXT={'.json','.jsonl','.txt','.md','.log','.csv','.yaml','.yml'}
OUTPUT=re.compile(r'generated_ids|generated_token_ids|process_toke|next token:|"logits"|"token_ids"|"first_divergence"|"exact"\s*:|"timings"|"completion"|"prediction_ids"|"native_events"|"output_ids"|"accepted_ids"')
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    with gzip.open('D:/HeteroSpec-PC/datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:tasks={r['task_id']:r['prompt'] for r in map(json.loads,f)}
    catalog=[];exclusions={t:[] for t in tasks};errors=[];seen=set();archive_seen=set()
    def inspect(label,data):
        text=data.decode('utf-8-sig',errors='replace'); low=label.lower();ids={'HumanEval/'+i for i in IDS.findall(text+' '+label)}&tasks.keys()
        kind='NO_TASK_ASSOCIATION';why='no HumanEval identity or original prompt'
        if not ids and OUTPUT.search(text):ids={t for t,p in tasks.items() if p in text}
        if ids:
            source='/frozen_source/' in low or '!frozen_source/' in low
            inputfile=Path(low).name in ['prompt.txt','user_specification.md','preregistration.md','protocol.json','reserved_set.json','reserved_validation_set.json','read_receipts.json'] or '/prompts/' in low
            if inputfile or source and not OUTPUT.search(text):kind='INPUT_OR_SOURCE_ONLY';why='input, protocol or frozen source; no result inferred from membership'
            elif OUTPUT.search(text):kind='OUTPUT_EXPOSED';why='model output, committed IDs, scores or scientific comparison present'
            elif any(w in low for w in ['eligible','universe','inventory','manifest','identity','freeze','exposure','selection','schedule']):
                kind='INVENTORY_ONLY';why='identity or universe listing without inference events; original exclusions retained separately'
            elif any(w in low for w in ['report','closeout','results','run','native','stdout','stderr','telemetry','analysis','capture']):kind='AMBIGUOUS_EXCLUDED';why='task associated with result-bearing record; conservative exclusion'
            else:kind='INPUT_OR_SOURCE_ONLY';why='task listing without observed output-bearing fields'
        row={'path':label,'bytes':len(data),'sha256':digest(data),'task_ids':sorted(ids),'classification':kind,'reason':why}
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
    prior=json.loads((OLD/'benchmarks/rtx_transfer_latency_v1/RESERVED_SET.json').read_text(encoding='utf-8'))
    for t in prior['excluded_task_ids']:exclusions[t].append({'path':'PR42:RESERVED_SET.json','reason':'retain prior conservative known/ambiguous exposure exclusion'})
    roots=['C:/Users/ASUS/Documents/Codex','C:/Users/ASUS/Downloads','C:/Users/ASUS/Desktop','D:/HeteroSpec-PC','D:/','E:/','F:/']
    files=[]
    for root in roots:
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
            if 'rtx_independent_proposal_replay_v2' in key or '/2026-10-01/rtx-h2-v2/' in key:continue
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
    # PRs are read directly from exact Git objects; no bulk duplicate checkout.
    for ref in ['61a1eb104d9bd1f6220a066d797dcc10dfed268d','3d60ac010523bbb0bf5c9db879d221159473bf0e']:
        names=subprocess.check_output(['git','diff','--name-only','f8290281156f6b3de8fbc8b44fd10a4afa7bcd89',ref],cwd=ROOT,text=True).splitlines()
        blobs={}
        for name in names:
            if Path(name).suffix.lower() not in TEXT:continue
            b=subprocess.check_output(['git','show',ref+':'+name],cwd=ROOT);blobs[name]=b;inspect('git:'+ref+':'+name,b)
        for name,b in blobs.items():
            if Path(name).name not in ['ARCHIVE.json','ARCHIVES.json']:continue
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
    eligible=sorted(t for t in tasks if not exclusions[t]);keys={t:digest((SALT+t).encode()) for t in eligible};selected=sorted(eligible,key=lambda t:(keys[t],t))[:24]
    status='PASS' if len(selected)==24 and not errors else 'RESERVED_POOL_BLOCKED'
    save(ROOT/'work/exposure_catalog.json',{'catalog':catalog,'errors':errors})
    save(STUDY/'EXPOSURE_AUDIT.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':status,'scope_roots':roots,'git_heads':['61a1eb104d9bd1f6220a066d797dcc10dfed268d','3d60ac010523bbb0bf5c9db879d221159473bf0e'],'catalog_entries':len(catalog),'logical_unique_archives':len(archive_seen),'catalog_sha256':digest((ROOT/'work/exposure_catalog.json').read_bytes()),'errors':errors,'exclusion_reasons':{t:e for t,e in exclusions.items() if e},'eligible_pool':eligible,'new_inference_executed':False,'scope_limit':'available host scientific directories and exact PR objects; protected system and model/vendor/dataset trees excluded'})
    template='Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'
    save(STUDY/'RESERVED_SET.json',{'status':status,'salt':SALT,'universe':sorted(tasks),'eligible_pool':eligible,'selection_keys':keys,'selected_task_ids':selected if status=='PASS' else [],'input_hashes':{t:digest((template+tasks[t]).encode('utf-8')) for t in selected},'model_forward_count':0,'tokenizer_forward_count':0})
    print(json.dumps({'status':status,'eligible':len(eligible),'selected':selected,'errors':errors,'catalog_entries':len(catalog)}))
if __name__=='__main__':main()
