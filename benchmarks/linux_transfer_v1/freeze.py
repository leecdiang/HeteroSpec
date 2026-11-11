"""Bind native evidence before timing; a manifest validator is not an equivalence proof."""
from pathlib import Path
import argparse
from common import need, read, save, sha

def bound(p):
    p=Path(p).resolve();need(p.is_file(),'Missing native evidence: '+str(p));return {'path':str(p),'sha256':sha(p)}

def reference(build, repeats, out):
    b=read(build);need(b['role']=='reference' and b['cuda'] and b['reference_source_is_pristine'],'Independent Linux GPU reference required')
    r=read(repeats);need(r.get('mode')=='reference_repeat' and r['passed'] and r['pairs'],'Actual repeated R captures required')
    need(all(x['equal'] and x['reference_sha256']==sha(x['reference']) and x['candidate_sha256']==sha(x['candidate']) for x in r['pairs']),'R repeat captures changed or differ')
    kinds={x['kind'] for x in r['pairs']};need({'full_requested_logits','active_sequence_serialized','frontier'}<=kinds,'R repeat scope incomplete')
    save(out,{'schema':'linux-transfer.reference-freeze.v1','status':'REFERENCE_FROZEN',
        'build':bound(build),'repeat_evidence':bound(repeats),'oracle_executable':b['executable_sha256'],
        'policy':'This Linux deployment only; does not replace or claim cross-GPU equality with Windows R'})

def confirmation(reference_freeze,registry,plan,out):
    ref=read(reference_freeze);need(ref['status']=='REFERENCE_FROZEN','Reference first')
    specs=read(registry);p=read(plan);executables={};evidence=[]
    need(specs['contract_checks']['linux_reference_precedes_candidate_outputs'] is True,'Host must substantiate ordering')
    needed={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
    need(needed<=set(specs['checks']) and all(specs['checks'][k]['passed'] is True for k in needed),"Incomplete native qualification; do not replace with helper tests")
    for k in sorted(needed):evidence.append({'kind':k,**bound(specs['checks'][k]['evidence'])})
    for item in specs['executables']:
        b=read(item['build']);need(b['cuda'] and b['dependency_closure_complete'],'Incomplete native build')
        need(sha(b['executable'])==b['executable_sha256'],'Changed executable')
        modules=read(item['loaded_modules']);need(modules,'Actual module map missing')
        executables[b['executable_sha256']]={'build':bound(item['build']),'loaded_modules':modules}
    need(len(executables)>=2,'Both candidate projection cores required')
    jobs=[]
    for w in p['workers']:
        f=Path(plan).parent/w['job'];need(sha(f)==w['job_sha256'],'Changed frozen job');jobs.append(sha(f))
    save(out,{'schema':'linux-transfer.freeze.v1','status':'QUALIFIED_AND_FROZEN',
         'reference':bound(reference_freeze),'qualification_registry':bound(registry),'plan':bound(plan),
         'evidence':evidence,'executables':executables,'job_sha256':jobs,
         'warning':'This binds the submitted native evidence; it does not independently prove that a human-labelled check is scientifically sufficient.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='mode',required=True)
    r=s.add_parser('reference');r.add_argument('build',type=Path);r.add_argument('repeat_comparison',type=Path);r.add_argument('out',type=Path)
    c=s.add_parser('confirmation');c.add_argument('reference_freeze',type=Path);c.add_argument('registry',type=Path);c.add_argument('plan',type=Path);c.add_argument('out',type=Path)
    a=p.parse_args()
    if a.mode=='reference':reference(a.build,a.repeat_comparison,a.out)
    else:confirmation(a.reference_freeze,a.registry,a.plan,a.out)
