import hashlib,json,pathlib,shutil
base=pathlib.Path('D:/rtx158');repo=pathlib.Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr158')
out=repo/'benchmarks/rtx_reference_repair_v1/host_execution/delivery';assert out.is_dir()
for name in ('PUBLISH_DELIVERY01.log','PUBLIC_ACCESS02.log','PUBLISHED_ACCESS03.log','FINALIZE_DELIVERY01.json'):
    shutil.copy2(base/'operations'/name,out/name)
source=out/'closeout_source';source.mkdir()
for name in ('publish_verified_delivery.py','public_access_recovery.py','verify_published_access.py','finalize_delivery_report.py','attach_closeout_records.py'):
    shutil.copy2(base/'operations'/name,source/name)
receipt=json.loads((base/'publication03/PUBLISHED_ACCESS_READBACK.json').read_text())
pins=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source.iterdir())]
record={'native_requests_added':0,'repository_visibility':'private','permissions_changed':False,'release_published':True,'published_index_readback':receipt['status'],'raw_index_sha256':receipt['index_sha256'],'source_files':pins,'retained_failures':['PUBLISH_DELIVERY01 exit1 after successful publication: stale pre-publication asset URL assertion.','PUBLIC_ACCESS02 exit1: anonymous HTTP404 on existing private repository.'],'resolution':'PUBLISHED_ACCESS03 freshly fetched published metadata and authenticated index, matching size/SHA256. No raw/metadata asset changes, no scientific retry. Corrected finalizer is pinned here; earlier source remains unchanged in TRANSPORT_METADATA.zip.'}
(out/'ACCESS_CORRECTION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
notes=(base/'publication01/RELEASE_NOTES.md').read_text(encoding='utf-8')
notes+='\nAccess: this is an existing private repository. Authorized repository readers are required; visibility and permissions are unchanged. Full authenticated raw/member and transport-metadata readback passed, followed by a fresh authenticated index download after publication. Anonymous HTTP404 and the earlier stale draft-URL assertion are retained in PR159 delivery records; anonymous public availability is not claimed.\n'
(base/'operations/RELEASE_NOTES_FINAL.md').write_text(notes,encoding='utf-8')
print('ACCESS_CORRECTION_RETAINED',len(pins))
