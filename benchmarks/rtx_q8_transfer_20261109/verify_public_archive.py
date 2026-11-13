"""Verify downloaded GitHub packet bytes and recompute its frozen statistics."""
from pathlib import Path
import base64,gzip,hashlib,importlib.util,json,os,subprocess,time
from admission import ROOT,REPO,put,sha
from archive_results import DEST

def main():
    start=time.monotonic();download=DEST/'github-readback';meta=json.loads((download/'DOWNLOAD.json').read_bytes())
    parts=json.loads((ROOT/'public_archive/PARTS.json').read_bytes());packet=download/'scientific-records.json.gz'
    with packet.open('xb') as target:
        for p in parts['parts']:
            raw=base64.b64decode((download/(p['name']+'.b64')).read_bytes(),validate=False)
            assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'];target.write(raw)
    assert packet.stat().st_size==parts['joined_bytes'] and sha(packet)==parts['joined_sha256']
    with gzip.open(packet,'rt',encoding='utf8') as f:bundle=json.load(f)
    assert bundle['schema']=='heterospec.rtx211.text-bundle.v1'
    index=json.loads((ROOT/'public_archive/TEXT_INDEX.json').read_bytes());expected={x['path']:x for x in index['files']}
    assert len(expected)==len(bundle['records']) and len({r['path'] for r in bundle['records']})==len(expected)
    restored=download/'text-restored';restored.mkdir(exist_ok=False)
    for r in bundle['records']:
        data=r['text'].encode('utf8');e=expected[r['path']]
        assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
        p=restored/r['path'];assert p.resolve().is_relative_to(restored.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    source=restored/'scripts/analyze_results.py';raw=source.read_bytes().replace(b'\r\n',b'\n')
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    expected_blob=subprocess.check_output(['git','-C',str(REPO),'rev-parse','2a884e28e3c31c2cb20eebf853c48e03698364fe:benchmarks/rtx_q8_transfer_20261109/analyze_results.py'],text=True).strip();assert blob==expected_blob
    spec=importlib.util.spec_from_file_location('github_statistics',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    statistics=download/'statistics-recomputed';statistics.mkdir(exist_ok=False)
    for name in ('LIVE_RECORDS.json','SAME_WORK_CLEAN_RECORDS.json','cohort/COHORT_FREEZE.json'):
        p=statistics/name;p.parent.mkdir(parents=True,exist_ok=True);os.link(restored/'records'/name,p)
    module.ROOT=statistics;same=module.diagnostic();live=module.live()
    assert same==json.loads((ROOT/'SAME_WORK_RESULTS.json').read_bytes())
    assert live==json.loads((ROOT/'LIVE_RESULTS.json').read_bytes())
    put(ROOT/'PUBLIC_READBACK.json',dict(passed=True,repository=meta['repository'],published_commit=meta['commit'],remote_download=meta,
        joined_sha256=sha(packet),joined_bytes=packet.stat().st_size,parts_readback=len(parts['parts']),text_records_verified=len(expected),
        full_packet_downloaded_from_github=True,all_published_text_bytes_verified=True,public_statistics_exact=True,
        prospective_analysis_blob=blob,raw_binary_readback='Separate local complete CAS byte verification, not claimed as a remote numerical rerun.',
        model_weights_included=False,new_model_requests=0,wall_seconds=time.monotonic()-start))
    print('Full GitHub text packet bytes verified and both fixed analyses reproduced exactly',flush=True)

if __name__=='__main__':main()
