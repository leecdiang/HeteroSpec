"""S3 successor CPU adapter: fixed roots -> real ABI jobs and command inventory.
No subprocess/model import or GPU execution. Native launch is a separate step.
"""
import argparse, copy, hashlib, json
from pathlib import Path
from schedule import schedule

OLD_ROOTS_SHA='a2ab60ee871fac53ec36c8bbae08fd0cb06e3efe046083b34d3351783288c771'
MODEL_SHA='efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689'
ELF_SHA={'R':'5c23a74ffaeec433f9dbc37ce1e014f374839b84da0eb19e4cd36146cc7d5199',
         'model':'fc2190a8fee10869f1f98a061bf6d1d1484b115fe3800d3aee6020229b135a58'}
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def roots_check(roots):
    xs=roots['inputs'];need(len(xs)==12,'exactly twelve roots')
    need(len({x['id'] for x in xs})==12,'duplicate IDs')
    need(len({tuple(x['prompt_ids']) for x in xs})==12,'duplicate token input')
    for i,x in enumerate(xs):
        need(x['slot']==i and x['domain']==('code' if i<6 else 'math'),'fixed six/six slot order')
        need(x['cap']==128 and type(x['cap']) is int,'cap128')
        need(1<=len(x['prompt_ids'])<=192,'untruncated short prompt')
        need(all(type(t) is int and 0<=t<151936 for t in x['prompt_ids']),'token IDs')
    return xs

def freeze(archive,out):
    a=Path(archive);need(digest(a/'roots/ROOTS.json')==OLD_ROOTS_SHA,'original R roots bytes')
    old=read(a/'roots/ROOTS.json');roots_check(old)
    keys=('id','domain','slot','cap','prompt_ids','source_revision','source_file','source_sha256')
    compact=lambda x:{k:x[k] for k in keys if k in x}
    save(out/'R_ROOTS.json',dict(inputs=[compact(x) for x in old['inputs']],cohort='R',source_roots_sha256=OLD_ROOTS_SHA))
    pool=read(a/'input_materials/0-TOKENIZED_UNIVERSE.json')['inputs']
    exposure={x['id']:x for x in read(a/'roots/EXPOSURE_TABLE.json')['table']}
    oldids={x['id'] for x in old['inputs']};seen={tuple(x['prompt_ids']) for x in old['inputs']}
    selected=[];seen_text={x['normalized_description_sha256'] for x in old['inputs']}
    for domain in ('code','math'):
        candidates=[x for x in pool if x['domain']==domain and x['id'] not in oldids
                    and exposure[x['id']]['candidate_for_final_selection']]
        candidates.sort(key=lambda x:(hashlib.sha256(('s3-holdout-20261113:'+x['id']).encode()).hexdigest(),x['id']))
        group=[]
        for x in candidates:
            tok=tuple(x['prompt_ids'])
            textkey=x['normalized_description_sha256']
            if tok in seen or textkey in seen_text:continue
            seen.add(tok);seen_text.add(textkey);group.append(dict(compact(x),slot=len(selected)+len(group)))
            if len(group)==6:break
        need(len(group)==6,'insufficient H candidates');selected.extend(group)
    h=dict(inputs=selected,cohort='H',selection='SHA256(s3-holdout-20261113:+ID), first six/domain after historical exclusions',
        scope='Prospective new panel relative to archived S3 audit, NOT training-unseen; later project exposure not yet reconciled',
        later_project_exposure='NOT_CHECKED',native_status='NOT_RUN',
        input_archive_pool_sha256=digest(a/'input_materials/0-TOKENIZED_UNIVERSE.json'))
    roots_check(h);save(out/'H_CANDIDATE_ROOTS.json',h)
    save(out/'INPUT_PROVENANCE.json',dict(archive_commit='ab695a766d055f7d3c6b1fed0720c579c749bcdb',
         model_forwards=0,new_tokenization=0,source='S3_F2_20261110_RESOURCE02/S3_F2.tar.gz',
         R='original byte-verified token IDs; no rerender',H='same archived tokenizer/template; final later-exposure review pending'))

def materialize(archive,rootfile,cohort,day,model,out):
    need(day in ((1,2) if cohort=='R' else (1,)),'invalid cohort/date')
    roots=read(rootfile);xs=roots_check(roots);a=Path(archive)
    need(roots.get('cohort')==cohort,'cohort binding')
    if cohort=='R':
        need(digest(a/'roots/ROOTS.json')==OLD_ROOTS_SHA,'original source identity')
        originals=read(a/'roots/ROOTS.json')['inputs']
        need(all(all(x[k]==o[k] for k in ('id','domain','slot','cap','prompt_ids')) for x,o in zip(xs,originals)),'R must retain exact original inputs')
    templates={arm:read(a/f'prospective/jobs/s3-v1-panel-root00-r0-{arm}.json') for arm in ('B','C')}
    ref=read(a/'prospective/jobs/s3-v1-R-root00-repeat0.json');workers=[]
    def add(identity,slot,arm,roles,stage,meta=None):
        inp={k:xs[slot][k] for k in ('id','domain','prompt_ids','cap')};inp['family']='Qwen32B'
        job=copy.deepcopy(ref if arm=='R' else templates[arm]);job['target_model']=str(model)
        need(job['target_sha256']==MODEL_SHA,'model contract');job['inputs']=[]
        for role in roles:
            name=f'new-root{slot:02d}' if arm=='R' else f'new-root{slot:02d}-{role}' if stage=='qualification' else role
            entry=dict(name=name,input=inp,capture=role in ('reference','heavy'))
            if arm=='R':entry['state_positions']=list(range(len(inp['prompt_ids']),len(inp['prompt_ids'])+128))
            job['inputs'].append(entry)
        rel='jobs/'+identity+'.json';save(out/rel,job)
        workers.append(dict(worker_id=identity,arm=arm,slot=slot,day=day,stage=stage,job=rel,
            job_sha256=digest(out/rel),requests=len(roles),reserved_rows=len(roles)*(len(inp['prompt_ids'])+128),
            roles=roles,executable='R' if arm=='R' else 'model',**(meta or {})))
    slots=range(12) if day==1 else (0,6)
    # Each root's reference repeat + heavy/clean bridges is adjacent, enabling bounded scratch later.
    for slot in slots:
        for rep in range(2):add(f'{cohort}-d{day}-q{slot:02d}-R{rep}',slot,'R',['reference'],'qualification')
        for arm in ('B','C'):add(f'{cohort}-d{day}-q{slot:02d}-{arm}',slot,arm,['heavy','clean'],'qualification')
    for w in schedule(cohort):
        if w['day']!=day:continue
        add(w['pair_id']+'-'+w['arm'],w['root_slot'],w['arm'],['warm','measured'],'formal',dict(pair_id=w['pair_id'],round=w['round']))
    planned=sum(w['requests'] for w in workers)
    expected=168 if day==1 else 108
    need(planned==expected,'all warmups and heavy/clean bridges counted')
    save(out/'MANIFEST.json',dict(schema='hs.s3.successor.cpu.v1',cohort=cohort,day=day,workers=workers,
        roots=roots,planned_requests=planned,planned_rows=sum(w['reserved_rows'] for w in workers),
        cohort_request_ceiling=292 if cohort=='R' else 176,cohort_row_ceiling=93440 if cohort=='R' else 56320,
        native_execution='NOT_RUN',GPU_authorized=False,
        day2_dependency='day1 full qualification and same deployment; date start >=24h' if day==2 else None))
    return workers

def commands(plan,config,out):
    """Build argv only. Never mint a historical admission grant or start a worker."""
    p=Path(plan);m=read(p/'MANIFEST.json');c=read(config)
    need(set(c['executables'])>=set(('R','model')),'R/model paths required')
    result=[]
    for w in m['workers']:
        exe=c['executables'][w['executable']];need(Path(exe).is_absolute(),'absolute executable path')
        job=(p/w['job']).resolve();need(digest(job)==w['job_sha256'],'job changed')
        result.append(dict(worker_id=w['worker_id'],argv=[exe,str(job),str(Path(c['output_root'])/w['worker_id']/'native')],
            env=dict(CUDA_VISIBLE_DEVICES=c['gpu_uuid'],CUDA_DEVICE_ORDER='PCI_BUS_ID',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1'),
            expected_original_elf_sha256=ELF_SHA[w['executable']],
            reservation='SUCCESSOR_LAUNCHER_REQUIRED_NOT_FABRICATED',phase=w['stage']))
    save(out,dict(status='CPU_ARGV_ONLY_NOT_EXECUTABLE_AUTHORIZATION',commands=result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    f=sub.add_parser('freeze');f.add_argument('--archive',type=Path,required=True);f.add_argument('--out',type=Path,required=True)
    m=sub.add_parser('materialize')
    for n in ('archive','roots','model','out'):m.add_argument('--'+n,type=Path,required=True)
    m.add_argument('--cohort',choices=['R','H'],required=True);m.add_argument('--day',type=int,required=True)
    c=sub.add_parser('commands')
    for n in ('plan','config','out'):c.add_argument('--'+n,type=Path,required=True)
    x=p.parse_args()
    if x.action=='freeze':freeze(x.archive,x.out)
    elif x.action=='materialize':materialize(x.archive,x.roots,x.cohort,x.day,x.model,x.out)
    else:commands(x.plan,x.config,x.out)
