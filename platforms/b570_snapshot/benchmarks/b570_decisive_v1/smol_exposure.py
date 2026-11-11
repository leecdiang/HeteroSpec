"""Supplement the initially too-narrow PR177 path filter; never replace inputs."""
from smol import *

def supplement():
 commit='610fd3a364bec6e8a3881ef666bedacd2035679a';pins=[];roots=set()
 for n in ('selected-inputs.json','exclusions.json'):
  path='benchmarks/rtx_rechunk_discrimination_v1/evidence/'+n
  raw=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',commit+':'+path],cwd=HERE)
  v=json.loads(raw)
  if n=='selected-inputs.json':roots.update(x['root_id'] for x in v)
  else:roots.update(v['root_ids'])
  dest=SROOT/'cohort'/('PR177-'+n);write(dest,v)
  pins.append(dict(commit=commit,path=path,git_bytes_sha256=hashlib.sha256(raw).hexdigest(),retained_json_sha256=sha(dest)))
 p=read(SROOT/'cohort/PANEL.json');selected={x['root_id'] for g in ('development','test') for x in p[g]}
 assert not selected&roots
 write(SROOT/'cohort/EXPOSURE_SUPPLEMENT.json',dict(utc=utc(),sources=pins,additional_authenticated_roots=sorted(roots),selected_intersection=[],original_selection_and_order_unchanged=True,selection_reason='Removing roots outside the already selected top16 does not change hash-ranked selection',initial_path_filter_too_narrow=True,no_replacement_or_performance_filter=True))

if __name__=='__main__':supplement()
