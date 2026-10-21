"""Prospective revision/run registration, fixtures created before watchers arm."""
import argparse,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from common import BASE,HERE,DESIGN,sha,write_new,now,need,owned,load,task_storage
from coverage import boundary_tests
P=argparse.ArgumentParser();P.add_argument('--id',required=True);P.add_argument('--revision',type=int,required=True);P.add_argument('--round',type=int,default=-1);P.add_argument('--cases',nargs='*');P.add_argument('--order',choices=['listed','reversed','sha256_case_id'],default='listed');P.add_argument('--freeze');args=P.parse_args()
need(0<=args.revision<6,'development revision budget')
need(re.fullmatch(r'[A-Za-z0-9_-]{1,80}',args.id) is not None,'invalid run ID')
matrix=json.loads((DESIGN/'ACCEPTANCE.json').read_text(encoding='utf-8'))['cases'];chosen=[r for r in matrix if not args.cases or r['id'] in args.cases]
if args.order=='reversed':chosen.reverse()
if args.order=='sha256_case_id':chosen.sort(key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())
storage_admission=task_storage(projected=(8000*5120+65536 if any(r['id']=='normal_late_panel' for r in chosen) else 0)+4*1024**2)
root=owned(BASE/'runs'/args.id);root.mkdir(parents=True,exist_ok=False);protected=root/'protected';external=root/'external';protected.mkdir();external.mkdir()
for n in ('slots','inputs','sealed','history'):(protected/n).mkdir()
registry={};cases=[]
def slot(name):
    name=args.id+'__'+name
    p=protected/'slots'/name;p.mkdir();(p/'BASELINE.bin').write_bytes(b'CPU_BASELINE');(p/'FENCE.bin').write_bytes(b'CPU_FENCE_BASELINE');registry[name]=dict(path=str(p),state='PREPARED');return name
inactive=slot('inactive_fixture')
for r in chosen:
    name=r['id'];(external/name).mkdir()
    slots=[slot(name+'_'+str(i)) for i in range(16 if name=='normal_transition' else 2 if name=='late_closed_slot_write' else 1)]
    target={'notification_loss':'watcher','log_overflow':'log','resource_read_failure':'resource','directory_read_timeout':'directory','watcher_stall':'watcher','journal_write_failure':'journal','wrong_module':str(Path(sys.executable).resolve()),'truncated_stdout':'stdout','abnormal_exit':'child','child_timeout':'child','quick_exit':'child'}.get(name,'positive')
    filesystem=name in ('frozen_input','inactive_output','sealed_results','late_closed_slot_write','terminal_pending_completion')
    if filesystem:
        target=(protected/'inputs/frozen_input.bin' if name=='frozen_input' else protected/'slots'/inactive/'BASELINE.bin' if name=='inactive_output' else protected/'slots'/slots[0]/'BASELINE.bin' if name=='late_closed_slot_write' else protected/'sealed'/(name+'.bin'))
        if not target.exists():target.write_bytes(b'CPU_SACRIFICIAL_FROZEN')
        target=str(target.resolve())
    cases.append(dict(r,slots=slots,target=target,filesystem=filesystem))
if any(r['id']=='normal_late_panel' for r in chosen):
    for i in range(8000):
        d=protected/'history'/str(i//1000);d.mkdir(exist_ok=True);(d/(str(i)+'.bin')).write_bytes(b'CPU_HISTORY_'+str(i).encode())
hashes={p.relative_to(DESIGN).as_posix():sha(p) for p in DESIGN.rglob('*') if p.is_file() and ('host' in p.relative_to(DESIGN).parts or p.name in ('ACCEPTANCE.json','BUDGET.json','check_receipts.py'))}
registry_path=DESIGN/'results/DEVELOPMENT_REGISTRY.jsonl'
past=[json.loads(s) for s in registry_path.read_text(encoding='utf-8').splitlines()] if registry_path.exists() else []
if args.round<0:
    previous=[r for r in past if r['revision']==args.revision]
    need(all(r['code_hashes']==hashes for r in previous),'code changed within a registered revision')
    full=not args.cases
    need(sum(r['full_suite'] for r in previous)+int(full)<=2,'full suite quota')
    need(sum(r['targeted_cases'] for r in previous)+(0 if full else len(chosen))<=24,'targeted quota')
    review_path=DESIGN/'SOURCE_REVIEW_FREEZE.json';build_path=DESIGN/'results/BUILD_RECORD.json'
    review=load(review_path);build=load(build_path)
    from development_binding import source_hashes
    need(review.get('scope')=='source_review_only' and review.get('review_status')=='scoped-clean','reviewed development source required')
    need(build['source_review_sha256']==sha(review_path) and build['source_hashes']==source_hashes(review),'reviewed build binding required')
    need(hashes=={**source_hashes(review),'host/LauncherCapture.dll':build['dll_sha256']},'development runtime source drift')
    registration=dict(id=args.id,revision=args.revision,full_suite=full,targeted_cases=0 if full else len(chosen),code_hashes=hashes,registered_ns=now(),purpose='CPU development; all attempts retained')
    with registry_path.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(registration,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
else:
    need(args.freeze is not None,'confirmation requires prospective freeze')
    fpath=DESIGN/'results/CONFIRMATION_FREEZE.json';freeze=load(fpath);remote=load(DESIGN/'results/REMOTE_FREEZE.json')
    need(sha(fpath)==args.freeze==remote['freeze_sha256'],'frozen identity mismatch')
    need(all(sha(DESIGN/k)==v for k,v in freeze['bound_files'].items()),'frozen source/artifact drift')
    need(0<=args.round<3 and args.id==freeze['rounds'][args.round]['id'],'unregistered confirmation identity')
    need(args.order==freeze['rounds'][args.round]['order'] and not args.cases,'fixed complete confirmation matrix required')
    need(args.revision==freeze['final_development_revision'],'final reviewed revision required')
    if args.round>0:
        gate=load(DESIGN/'results'/('ROUND_'+str(args.round-1)+'_GATE.json'))
        need(gate['qualified_round']==args.round-1 and gate['freeze_sha256']==args.freeze,'prior round qualification missing')
        need(sha(BASE/gate['raw_audit_path'])==gate['raw_audit_sha256'],'prior raw audit drift')
caps=external/'source_caps';caps.mkdir()
for rel,digest in hashes.items():
    p=caps/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((DESIGN/rel).read_bytes());need(sha(p)==digest,'source cap changed during registration')
cfg=dict(schema=1,id=args.id,root=str(root),revision=args.revision,round=args.round,order=args.order,freeze_sha256=args.freeze,cases=cases,registry=registry,code_hashes=hashes,registered_ns=now(),storage_admission=storage_admission,GPU_queries=0,GPU_initializations=0,model_file_reads=0,model_requests=0,graph_computes=0,scientific_native_starts=0,launcher_log_dir=str(external/'launcher'),launcher_seconds=180,protected_roots=[str(protected),str(DESIGN)])
if args.round<0:cfg.update(source_review_sha256=sha(review_path),build_record_sha256=sha(build_path))
write_new(root/'CONFIG.json',cfg);write_new(external/'BOUNDARY_TESTS.json',boundary_tests())
print(json.dumps(dict(config=str(root/'CONFIG.json'),code_hashes=hashes,cases=[r['id'] for r in cases],registered_ns=cfg['registered_ns'])))
