"""Read-only historical recovery and bounded host preparation; no native launch."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, time, uuid, zipfile

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec')
PR134 = Path('C:/hs/b570-formal-request-20261020')
PR135 = Path('C:/hs/b570-draft-prefill-submit-20261020-r2')
DESIGN = '03cc11662f0ff21514efd40e9a09d4c7e1d2c672'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(name, value):
    (ROOT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def item(p):
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}

def gitfile(ref, path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'], cwd=REPO)

def main():
    started = time.monotonic()
    assert not (ROOT/'PREPARATION.json').exists(), 'Do not overwrite preparation'
    design = ROOT/'design'; design.mkdir()
    for name in ['HOST_PROMPT.md','PROTOCOL.md','README.md','REGISTRATION_TEMPLATE.json',
                 'VALIDATION.json','toolkit.py','test_toolkit.py']:
        (design/name).write_bytes(gitfile(DESIGN, 'docs/experiments/b570_prefill_closeout_v1/'+name))
    # Authenticate historical manifests against their committed bytes, not new references.
    provenance = []
    for ref, prefix, base, names in [
        ('51febaddcf49bb18565e568cf964a6e5c78876c9','benchmarks/b570_formal_request_v1',PR134,
         ['RAW_LOGITS_MANIFEST.json','INPUT_PANEL.json','MODEL_IDENTITY.json','BUILD_MANIFEST.json']),
        ('e44c4df04c895b55ef734ee7b0659189158f95ab','benchmarks/b570_draft_prefill_submission_v1/attempt2',PR135,
         ['RAW_LOGITS_MANIFEST.json','INPUT_PANEL.json','MODEL_IDENTITY.json','BUILD_MANIFEST.json','QUALIFICATION_RECHECK.json'])]:
        for name in names:
            committed = gitfile(ref, prefix+'/'+name)
            assert json.loads(committed) == read(base/name), (ref, name)
            provenance.append({'commit':ref,'file':prefix+'/'+name,'local':item(base/name),
                               'git_blob_sha256':hashlib.sha256(committed).hexdigest(),
                               'json_content_equal':True})
    panel = read(PR134/'INPUT_PANEL.json')
    assert panel == read(PR135/'INPUT_PANEL.json')
    assert [x['id'] for x in panel['inputs']] == ['HumanEval/38','HumanEval/65','HumanEval/115','HumanEval/127']
    shutil.copy2(PR134/'INPUT_PANEL.json',ROOT/'INPUT_PANEL.json')
    raw = []
    for row in read(PR134/'RAW_LOGITS_MANIFEST.json'):
        p = PR134/row['path']; actual = item(p)
        assert actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'], p
        raw.append(dict(actual, reference_relative_path=row['path']))
    assert len(raw)==914
    qb = [x for x in raw if '/qual-2/' in x['reference_relative_path']]
    assert len(qb)==346
    references = []
    for i, inp in enumerate(panel['inputs']):
        original = read(PR134/f'qual-{i}/result.json')
        repaired = read(PR135/f'qual-{i}/result.json')
        assert original['status']=='QUALIFICATION_PASS' and repaired['status']=='QUALIFICATION_PASS'
        a = original['requests'][2]; b = repaired['requests'][0]
        for key in ['ids','eog','length','terminal_id','stop_reason','cycles']:
            assert a[key]==b[key], (inp['id'],key)
        assert (a['length'],a['stop_reason']) == [(64,'CAP'),(53,'EOG'),(41,'EOG'),(64,'CAP')][i]
        for f in sorted((PR134/f'qual-{i}/qual-2').rglob('*.f32')):
            other = PR135/f'qual-{i}/qual-0'/f.relative_to(PR134/f'qual-{i}/qual-2')
            assert f.read_bytes()==other.read_bytes(), other
        references.append({'input_id':inp['id'],'prompt_tokens':len(inp['prompt_ids']),
                           'cap':inp['cap'],'endpoint':[a['length'],a['stop_reason']],
                           'cycles':len(a['cycles']),'original_result':item(PR134/f'qual-{i}/result.json'),
                           'attempt2_result':item(PR135/f'qual-{i}/result.json'),
                           'attempt2_receipt':read(PR135/f'qual-{i}.PROCESS_RECEIPT.json')})
    write('REFERENCE_RECOVERY.json',{'status':'ORIGINAL_BYTES_RECOVERED','provenance':provenance,
          'original_all_vector_count':len(raw),'original_QB_vector_count':len(qb),
          'attempt2_QB_bytes_rechecked':346,'references':references,
          'scope':'Read-only local recovery; not new E1 qualification or external certification.'})
    write('RAW_RECOVERY_MANIFEST.json', raw)
    models = []
    for row in read(PR134/'MODEL_IDENTITY.json'):
        p = Path(row['path']); actual=item(p)
        assert actual==row, p
        models.append(actual)
    write('MODEL_RECHECK.json',models)
    runtime=[]
    for p in sorted((PR135/'build/Release').glob('*.dll')):
        original=PR134/'build/Release'/p.name
        assert sha(p)==sha(original), p
        runtime.append(item(p))
    write('RUNTIME_MANIFEST.json',runtime)
    history=[]
    history_paths=[]
    for base in [PR134,Path('C:/hs/b570-draft-cpu-20261020'),
                 Path('C:/hs/b570-draft-prefill-submit-20261020'),PR135]:
        ledger=read(base/'BUDGET_LEDGER.json')
        assert abs(sum(s['charged_seconds'] for s in ledger['sessions'])-ledger['new_charged_seconds'])<1e-7
        history.append({'root':str(base),'ledger':ledger,'ledger_identity':item(base/'BUDGET_LEDGER.json')})
        history_paths += [p for p in base.rglob('*') if p.is_file() and 'build' not in p.parts
                          and p.suffix in ['.json','.log','.md','.py','.ps1','.cpp','.patch','.txt']]
    timing=[]
    for i in range(3):
        result=PR135/f'time-{i}/result.json'; receipt=PR135/f'time-{i}.PROCESS_RECEIPT.json'
        entry={'session':i,'result_exists':result.exists(),'receipt_exists':receipt.exists()}
        if result.exists():
            n=read(result)
            entry.update(status=n['status'],requests=len(n['requests']),result_identity=item(result),
                         normal_cleanup_returned=n.get('normal_cleanup_returned',False),
                         request_categories=[x['category'] for x in n['requests']],
                         summed_service_seconds=sum(x['service_seconds'] for x in n['requests']),
                         last_write_utc=datetime.datetime.fromtimestamp(result.stat().st_mtime,datetime.timezone.utc).isoformat())
            if receipt.exists(): entry['receipt']=read(receipt)
            else: entry['accounting']='Unreceipted historical partial native execution; process wall/exit/cleanup unknown. Never zero-charge or complete this old UUID.'
        timing.append(entry)
    write('HISTORY.json',{'preserved_ledgers':history,'uncommitted_attempt2_timing':timing,
          'receipt_backed_cumulative_seconds':history[-1]['ledger']['all_history_cumulative_seconds'],
          'additional_unreceipted_process_seconds':None,'historical_total_exactly_known':False,
          'new_study_will_not_pool_or_resume':True})
    with zipfile.ZipFile(ROOT/'HISTORICAL_COMPACT.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(history_paths)):
            z.write(p,str(p.relative_to(Path('C:/hs'))).replace('\\','/'))
    write('HISTORICAL_COMPACT_MANIFEST.json',item(ROOT/'HISTORICAL_COMPACT.zip'))
    write('AUTHORIZATION.json',{'user_request':'从 `HOST_PROMPT.md` 开始  ，pr141，',
          'interpretation':'Execute the linked host handoff and its bounded matrix after all prospective gates; no historical resume, merge or publication.',
          'design_commit':DESIGN,'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write('PREPARATION.json',{'uuid':str(uuid.uuid4()),'started_utc':'2026-10-21T10:45:26.0062489Z',
          'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'cpu_preparation_seconds':time.monotonic()-started,'model_processes':0,'model_requests':0})
    print(json.dumps({'status':'HISTORY_AND_RAW_RECOVERED','qb_vectors':346,'all_vectors':914,
                     'historical_timing':timing,'cpu_seconds':time.monotonic()-started},indent=2))

if __name__=='__main__': main()
