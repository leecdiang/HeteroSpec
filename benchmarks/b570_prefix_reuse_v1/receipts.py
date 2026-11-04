from host import *
def admission():
 rows=[]
 for role in ('reference-00','candidate-00'):
  u=ROOT/'units'/('admit-'+role);n=read(u/'native/result.json');r=read(u/'RECEIPT.json');assert n['status']=='COMPLETE' and r['success']
  rows.append(dict(role=role,context=4096,resident_models=n['resident_models'],min_free_device=n['min_free_device'],min_free_ram=n['min_free_ram'],load_seconds=n['load_seconds'],native_sha256=sha(u/'native/result.json'),supervisor_sha256=sha(u/'SUPERVISOR.json'),receipt=r))
 write(ROOT/'HOST_ADMISSION.json',dict(utc=utc(),status='ADMITTED_C4096_TARGET_ONLY',host='WIN-B041QJEBS30',gpu='Intel Arc B570',driver='32.0.101.9150',model=read(ROOT/'INHERITED_AUTHENTICATION.json')['model'],kv='F16',non_flash=True,qmax=32,cap=128,capacity_rungs_attempted=[4096],admissions=rows,resource_reservation=sha(ROOT/'RESOURCE_RESERVATION.json'),original_k1_history_preserved=True,old_R_replaced=False))
def publish_local():
 dest=HERE/'evidence';dest.mkdir(exist_ok=True)
 for name in ('HOST_ADMISSION.json','TOKENIZER_AND_CENSUS.json','COHORT_RECEIPT.json','RESOURCE_RESERVATION.json','INHERITED_AUTHENTICATION.json','panel.json','schedule.json'):
  p=ROOT/name
  if p.exists():shutil.copyfile(p,dest/name)
 for role in ('reference-00','candidate-00','reference-01','candidate-01','candidate-02'):
  for name in ('FILES.json','SOURCE.json'):
   p=ROOT/role/name
   if p.exists():shutil.copyfile(p,dest/(role+'-'+name))
 for n in ('allocator_probe.cpp','worker.cpp'):
  shutil.copyfile(HERE/n,ROOT/n)
 if (ROOT/'manifest.json').exists():
  panel=read(ROOT/'panel.json');ids={r['id'] for r in panel['calibration']+panel['test']}
  selected=[r for r in read(ROOT/'manifest.json')['rows'] if r['id'] in ids]
  p=dest/'SELECTED_NATIVE_INPUTS.json'
  if not p.exists():write(p,selected)
if __name__=='__main__':
 if sys.argv[1]=='admission':admission()
 publish_local()
