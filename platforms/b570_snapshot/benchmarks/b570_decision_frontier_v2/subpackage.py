"""Deduplicated LOCAL PRIVATE CPU numeric evidence subset; no GGUF or remote upload."""
import json,shutil,zipfile
from pathlib import Path
from pinned_sources import *

def package(destination):
 require(not destination.exists(),'private package destination must be fresh');destination.mkdir();objects=destination/'objects';objects.mkdir();selection=read(ROOT/'SUBPACKAGE_SELECTION.json');sources=list(selection['sources'])
 for p in sorted(ROOT.glob('*')):
  if p.is_file() and p.suffix in ('.py','.json','.md','.txt') and p.name not in ('SUBPACKAGE_RECEIPT.json','F0_CANDIDATE.json','F0_READBACK.json'):sources.append({'logical_path':'v2/'+p.name,'actual_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 # Fixed registration, original manifests and exact native/request source bodies as references.
 ref=Path(REFS['v1_benchmark'])
 for logical,p in [('references/PR105_F0.json',ref/'registration/F0.json'),('references/PR105_WRONG_DONORS.json',ref/'registration/DONORS.json'),('references/PR105_RAW_MANIFEST.json',ref/'RAW_MANIFEST.json'),('references/PR103_ARCHIVE_MANIFEST.json',ROOT/'source_refs/PR103_ARCHIVE_MANIFEST.json'),('references/PR103_F0.json',Path(REFS['pr103_fresh'])/'FREEZE.json'),('references/PR101_F0_BASE.json',Path(REFS['baseline'])/'F0_BASE.json'),('references/PR101_ARCHIVE_MANIFEST.json',Path(REFS['baseline'])/'ARCHIVE_MANIFEST.json'),('references/PR101_worker.cpp',Path(REFS['baseline'])/'native/worker.cpp')]:sources.append({'logical_path':logical,'actual_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 for name,pin in REFS['source_modules'].items():p=Path(pin['path']);sources.append({'logical_path':'pinned-source/'+name,'actual_path':str(p),'bytes':p.stat().st_size,'sha256':pin['sha256']})
 entries=[];seen=set()
 for s in sources:
  require(s['logical_path'] not in seen,'duplicate logical package path');seen.add(s['logical_path']);p=Path(s['actual_path']);require(p.suffix!='.gguf' and p.stat().st_size==s['bytes'] and sha(p)==s['sha256'],'package input changed');obj=objects/s['sha256']
  if not obj.exists():shutil.copyfile(p,obj)
  entries.append({'logical_path':s['logical_path'],'object':'objects/'+s['sha256'],'bytes':s['bytes'],'sha256':s['sha256']})
 manifest={'schema':1,'scope':'SELECTED_NUMERIC_EVIDENCE_SUBSET_NOT_COMPLETE_PR103_PR105_ARCHIVE','historical_comparisons':44,'logical_files':len(entries),'unique_objects':len(list(objects.iterdir())),'files':entries,'external_full_KV_mixtures':selection['external_mixtures'],'external_dependency_scope':'actual KV bytes read and verified in canonical audit; full state objects omitted from small numeric subpackage, available only through fixed original archive','unselected_raw_payload_links':'original RESULT/REQUEST bodies preserved, may reference additional unselected payloads outside this package','no_GGUF':True,'remote_raw_availability':'REMOTE_PENDING','independent_machine':'NOT_PERFORMED'};write(destination/'MANIFEST.json',manifest)
 archive=destination.parent/(destination.name+'.zip');require(not archive.exists(),'archive exists')
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
  z.write(destination/'MANIFEST.json','MANIFEST.json')
  for obj in sorted(objects.iterdir()):z.write(obj,'objects/'+obj.name)
 # Fresh restore proof reads the packed CAS and all logical references, no original-run fallback.
 fresh=destination.parent/(destination.name+'-fresh-read');require(not fresh.exists(),'fresh package restore exists');fresh.mkdir()
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():
   p=(fresh/name).resolve();require(p.is_relative_to(fresh.resolve()),'ZIP escape');p.parent.mkdir(parents=True,exist_ok=True)
   with z.open(name) as src,p.open('xb') as dst:shutil.copyfileobj(src,dst)
 restored=read(fresh/'MANIFEST.json')
 for e in restored['files']:p=fresh/e['object'];require(p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'fresh CAS pin')
 by={e['logical_path']:e for e in restored['files']};canon=read(fresh/by['v2/CANONICAL_AUDIT.json']['object']);checked=0
 for row in canon['rows']:
  # Vector source SHA and exact F64 bytes rebound from this restored subset.
  data=[]
  for h in row['vector_sha256']:
   b=(fresh/'objects'/h).read_bytes();require(digest(b)==h and len(b)==128256*4,'restored full FP32 vector');data.append(b)
  import numpy as np
  zz=[np.frombuffer(b,dtype='<f4').astype(np.float64) for b in data];I=zz[3]-zz[1]-zz[2]+zz[0];actual=(fresh/'objects'/row['full_residual_sha256']).read_bytes();require(I.astype('<f8').tobytes()==actual,'restored numeric residual changed');r,u=row['original_pair'];require(float(I[u]-I[r])==row['original_I'],'restored scalar contrast');checked+=1
 receipt={'status':'PASS_LOCAL_PRIVATE_SUBSET_FRESH_READ','archive_path':str(archive),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'logical_files':len(entries),'unique_objects':manifest['unique_objects'],'full_FP32_vectors_unique':len({h for r in canon['rows'] for h in r['vector_sha256']}),'full_F64_residuals_unique':len({r['full_residual_sha256'] for r in canon['rows']}),'restored_comparisons_checked':checked,'actual_fresh_root':str(fresh),'not_whole_archive_replacement':True,'external_KV_states_explicit':True,'no_GGUF_or_credentials':True,'remote':'REMOTE_PENDING','independent_machine':'NOT_PERFORMED'};write(ROOT/'SUBPACKAGE_RECEIPT.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--destination',type=Path,required=True);a=ap.parse_args();package(a.destination)
