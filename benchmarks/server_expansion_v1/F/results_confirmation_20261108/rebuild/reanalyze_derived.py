"""Verify derived text, bind retained receipt commitments, rerun fixed statistics.

This observer never requalifies vectors/KV or establishes actual GPU allocation.
Raw receipt hashes and sanitized receipt hashes are distinct and both retained.
"""
from pathlib import Path,PurePosixPath
import argparse,gzip,hashlib,importlib.util,json,math
ANALYZER_SHA256='8b1d0f7b794132bf5a33208d5c85124246bd112685f8bf33283156b70d7b0887'
def sha(data):return hashlib.sha256(data).hexdigest()
def need(x,m):
    if not x:raise RuntimeError(m)
def read(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def relative(name):
    p=PurePosixPath(name);need(not p.is_absolute() and p.parts and all(x not in ('..','') for x in p.parts),'Unsafe path');return str(p)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('bundle','analyzer','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();base=a.bundle.resolve();out=a.out.resolve();need(not out.exists(),'Fresh observer output; retain prior epochs')
    scope=read(base/'EXPORT_SCOPE.json')
    for name,key in (('scientific-records.json.gz','bundle_sha256'),('TEXT_INDEX.json','text_index_sha256'),('BINARY_CAPTURE_INDEX.json','binary_index_sha256')):need(sha((base/name).read_bytes())==scope[key],'Export file changed: '+name)
    ti=read(base/'TEXT_INDEX.json');bi=read(base/'BINARY_CAPTURE_INDEX.json');compressed=(base/'scientific-records.json.gz').read_bytes();raw=gzip.decompress(compressed)
    need(len(raw)==ti['uncompressed_bytes'] and ti['bundle_sha256']==sha(compressed),'Bundle length/hash binding')
    bundle=json.loads(raw);need(bundle['schema']=='linux-transfer.public-text-bundle.v1','Bundle schema')
    index={relative(x['path']):x for x in ti['files']};records={relative(x['path']):x['text'] for x in bundle['records']}
    need(len(index)==len(ti['files'])==len(records)==len(bundle['records'])==scope['text_files'] and set(index)==set(records),'Complete unique text index')
    for name,text in records.items():need(len(text.encode())==index[name]['exported_bytes'] and sha(text.encode())==index[name]['exported_sha256'],'Derived record changed: '+name)
    need(len(bi['files'])==bi['count']==scope['binary_captures'] and sum(x['bytes'] for x in bi['files'])==bi['bytes'],'Binary index cardinality/byte accounting')
    need(len({relative(x['path']) for x in bi['files']})==bi['count'],'Unique safe binary names')
    need(sha(a.analyzer.read_bytes())==ANALYZER_SHA256,'Different fixed analyzer source; no silent upgrade')
    plan=json.loads(records['panel-01/PLAN.json']);flat=json.loads(records['panel-01/ANALYZER_RECORDS.private.json'])['records'];reported=json.loads(records['panel-01/RESULTS.json'])
    expected={(x['root'],x['session'],x['arm']) for x in plan['slots']};found={(x['root'],x['session'],x['arm']) for x in flat}
    need(len(expected)==len(found)==len(flat)==plan['measurements'] and expected==found,'No partial/duplicate slot inference')
    out.mkdir();rebound=[];bindings=[]
    registry=index['panel-01/REGISTRY-COMPLETE.json']['raw_sha256']
    for row in flat:
        path=row['evidence_path'];marker='/panel-01/';need(path.count(marker)==1,'Known logical panel receipt path')
        logical=relative('panel-01/'+path.split(marker,1)[1]);need(logical in records,'Missing retained native receipt')
        need(row['evidence_sha256']==index[logical]['raw_sha256'],'Raw native commitment differs')
        receipt=json.loads(records[logical]);need(receipt['service_seconds']==row['service_s'],'Native service clock differs')
        need(row['qualification_registry_sha256']==registry,'Qualification registry differs')
        run=logical.split('/native/',1)[0];need(row['native_capability_sha256']==index[run+'/native/CAPABILITY.json']['raw_sha256'],'Actual capability binding differs')
        need(json.loads(records[run+'/HOST.json'])['status']=='COMPLETE','Actual host job incomplete')
        dest=out/'evidence'/logical;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_text(records[logical],encoding='utf8')
        derived=sha(dest.read_bytes());need(derived==index[logical]['exported_sha256'],'Materialized derived receipt differs')
        rebound.append(dict(row,evidence_path=str(dest),evidence_sha256=derived))
        bindings.append(dict(logical_path=logical,raw_receipt_sha256=row['evidence_sha256'],derived_receipt_sha256=derived,metric_unchanged=True,only_analysis_evidence_path_and_hash_rebound=True))
    spec=importlib.util.spec_from_file_location('fixed_qualified_analyzer',a.analyzer);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    actual=module.analyze(plan,rebound);need(actual==reported,'Exact fixed statistics did not reproduce')
    save(out/'DERIVED_EVIDENCE_REBINDINGS.json',dict(bindings=bindings,raw_and_derived_hashes_not_interchangeable=True))
    save(out/'RESULTS_REPRODUCED.json',actual)
    save(out/'CHECKED.json',dict(statistics_reproduced_exactly=True,text_files_verified=len(records),measurements=len(flat),analyzer_sha256=ANALYZER_SHA256,bundle_sha256=scope['bundle_sha256'],derived_text_only=True,native_vector_KV_qualification_reexecuted=False,actual_GPU_allocation_reverified=False,public_raw_capture_archive=False,source_metrics_and_all_slots_unchanged=True))
    print('DERIVED_TEXT_AND_FIXED_STATISTICS_REPRODUCED',len(flat),flush=True)
if __name__=='__main__':main()
