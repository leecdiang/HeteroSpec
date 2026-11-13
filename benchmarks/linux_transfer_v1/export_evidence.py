"""Export an allowlisted scientific record; keep raw host/network records private.

Public text is a derived representation. The index binds BOTH original private
bytes and exported bytes, so redaction never masquerades as raw archive readback.
Large native vectors/states remain private and receive a complete binary index.
"""
from pathlib import Path
import argparse, gzip, hashlib, json, re
from common import need, read, save, sha

def export(work,out,private_literals=()):
 w=Path(work).resolve();out=Path(out).resolve()
 need(not out.exists() and not out.is_relative_to(w),'Use a fresh export outside raw work')
 out.mkdir(parents=True);root=w.parent;home=Path.home()
 replacements=[(str(root),'<PRIVATE_ROOT>'),(str(home),'<HOME>')]
 replacements += [(x,'<PRIVATE_HOST_ID>') for x in private_literals if x]
 replacements.sort(key=lambda x:-len(x[0]))
 def clean(s):
  for a,b in replacements:s=s.replace(a,b)
  s=re.sub(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}','<ALLOCATED_GPU_UUID>',s)
  # Allocation strings need no public host/index/user provenance.
  s=re.sub(r'("allocation_id"\s*:\s*)"[^"\n]*"',r'\1"<EXPLICIT_PRIVATE_ALLOCATION>"',s)
  return s
 selected=set()
 for name in ('EXACT_MODEL_BINDINGS.json','PIPELINE_START.json','PIPELINE_INPUT_WAIT_RESUME.json',
              'PIPELINE_STATUS.json','PIPELINE_STATUS-02.json','PIPELINE_STATUS-03.json',
              'CONTINUATION-02.json','PANEL_CONTINUATION-03.json',
              'pipeline-events.jsonl','ledger.jsonl','CUDA_SOURCE_REVIEW.json',
              'UPSTREAM_ARCHIVE_IMPORT.json','UPSTREAM_REBUILD_CHECK.json'):
  if (w/name).is_file():selected.add(w/name)
 for prefix in ('inputs-01','reference-01','panel-01'):
  if (w/prefix).exists():
   selected.update(p for p in (w/prefix).rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl'))
 for directory in w.glob('qualification-*'):
  if directory.is_dir():selected.update(p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl'))
 for directory in w.glob('build-*-*'):
  if not directory.is_dir():continue
  for name in ('BUILD.json','DEPENDENCIES.json','configure/command.json','compile/command.json','native/ACTUAL_COMMANDS.txt'):
   if (directory/name).is_file():selected.add(directory/name)
 for directory in w.glob('stage-*'):
  if not directory.is_dir():continue
  for name in ('SOURCE_LOCK.json','SOURCE_LOCK.input.json','PORT.json','PORT.input.json','POSIX_HOST.patch'):
   if (directory/name).is_file():selected.add(directory/name)
 # Retained failures from coordinators/builds are relevant; arbitrary download
 # logs/headers and all-machine inventories are deliberately not traversed.
 for p in w.glob('*phase-*.log'):selected.add(p)
 records=[];index=[]
 for p in sorted(selected):
  rel=str(p.relative_to(w));text=p.read_text();public=clean(text)
  need('https://cdn-lfs' not in public and 'X-Amz-' not in public and 'xet-hf' not in public,'Signed/network material entered scientific allowlist')
  need(not re.search(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])',public),'Unreviewed IPv4-shaped value in export: '+rel)
  if p.suffix=='.json':json.loads(public)
  if p.suffix=='.jsonl':
   for row in public.splitlines():json.loads(row)
  encoded=public.encode();records.append({'path':rel,'text':public})
  index.append({'path':rel,'raw_bytes':p.stat().st_size,'raw_sha256':sha(p),'exported_bytes':len(encoded),'exported_sha256':hashlib.sha256(encoded).hexdigest(),'transformed':public!=text})
 # Every native binary capture, including failed qualification epochs, is indexed.
 # No timestamp/filename inference is used as a substitute for reading the bytes.
 binaries=[]
 for prefix in ('reference-01',*[p.name for p in w.glob('qualification-*') if p.is_dir()], 'panel-01'):
  directory=w/prefix
  if not directory.exists():continue
  for p in sorted(directory.rglob('*')):
   if p.is_file() and p.suffix in ('.f32','.bin'):
    binaries.append({'path':str(p.relative_to(w)),'bytes':p.stat().st_size,'sha256':sha(p)})
 data=json.dumps({'schema':'linux-transfer.public-text-bundle.v1','records':records},ensure_ascii=False,separators=(',',':')).encode()
 bundle=out/'scientific-records.json.gz'
 with bundle.open('xb') as f:
  with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z:z.write(data)
 save(out/'TEXT_INDEX.json',{'files':index,'bundle_sha256':sha(bundle),'uncompressed_bytes':len(data),'public_text_is_derived':True})
 save(out/'BINARY_CAPTURE_INDEX.json',{'files':binaries,'count':len(binaries),'bytes':sum(x['bytes'] for x in binaries),'public_raw_capture_archive':False,'scope':'Every .f32/.bin under reference, retained qualification epochs and panel; complete raw bytes hashed locally, not a claim of public binary archive readback'})
 save(out/'EXPORT_SCOPE.json',{'schema':'linux-transfer.public-export.v1','text_files':len(index),'binary_captures':len(binaries),
  'raw_records_retained_privately':True,'excluded':['company inventory/configuration','other users/processes','credentials','download headers/redirects/logs','model weights','compiled executables and SDK binaries'],
  'original_hash_fields_unchanged':True,'path_placeholders':['<PRIVATE_ROOT>','<HOME>','<PRIVATE_HOST_ID>','<ALLOCATED_GPU_UUID>','<EXPLICIT_PRIVATE_ALLOCATION>'],
  'no_public_binary_archive_readback_claim':True,'text_index_sha256':sha(out/'TEXT_INDEX.json'),'binary_index_sha256':sha(out/'BINARY_CAPTURE_INDEX.json'),'bundle_sha256':sha(bundle)})
 print(json.dumps({'text_files':len(index),'binary_captures':len(binaries),'bundle_bytes':bundle.stat().st_size}))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True);p.add_argument('--out',required=True);p.add_argument('--private-literal',action='append',default=[])
 a=p.parse_args();export(a.work,a.out,a.private_literal)
