from calibrate import *
def main():
    observed={r['id']:r for r in read(ROOT/'allocator-census01/allocator.json')}
    tokenized=[json.loads(s) for s in (ROOT/'tokenize01/tokens.jsonl').read_text(encoding='utf8').splitlines()];rows=[]
    for r in tokenized:
        if r['id'] not in observed:continue
        h=study.lcp(r['cached_ids'],r['request_ids']);assert observed[r['id']]['physical_head']==h
        rows.append({**{k:r[k] for k in ('id','root_id','cached_ids','request_ids','source_sha256')},'effective_head':h,'physical_head':h,'native_dense_verified':True,'history_exposed':False})
    manifest=dict(schema_version=1,native_tokenization=True,corpus_revision=study.CFG['corpus_revision'],tokenizer_sha256=sha(MODEL),template_sha256=hashlib.sha256(read(ROOT/'tokenize01/template.json')['template'].encode()).hexdigest(),deployment_id='RTX-C4096-exact-lcp-file-snapshot-v1',capacity=4096,padding=256,qmax=32,output_cap=128,cache_granule=1,reuse_policy='exact_lcp',exposure_audit_sha256=sha(ROOT/'exposure-audit.json'),rows=rows)
    panel=study.select(manifest);peer=read(ROOT/'B570_COHORT_RECEIPT.json')
    for name in ('calibration','test'):
        assert [(r['id'],r['root_id'],r['request_token_sha256'],r['cached_token_sha256']) for r in panel[name]]==[(r['id'],r['root_id'],r['request_token_sha256'],r['cached_token_sha256']) for r in peer[name]]
    put(ROOT/'common-manifest.json',manifest);put(ROOT/'common-panel.json',panel);put(ROOT/'common-census.json',study.inspect_manifest(manifest));put(ROOT/'common-schedule.json',study.schedule(panel))
    print('schema census and deterministic panel verified',len(rows))
if __name__=='__main__':main()
