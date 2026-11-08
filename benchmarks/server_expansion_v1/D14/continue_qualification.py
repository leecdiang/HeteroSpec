"""Retain the900s failure; requalify natural requests in bounded native groups.

Only development orchestration changes. Frozen R, numerical binaries, exact
comparisons, inputs and formal slots remain unchanged. Partial failed native
outputs are not admitted as qualification evidence.
"""
from pathlib import Path
import argparse, copy, fcntl, json, shutil, sys, types
import integrate as d

def main():
    p=argparse.ArgumentParser()
    for key in ('work','baseline','runtime','builds','repo','admission','target','draft'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);p.add_argument('--run-panel',action='store_true')
    a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    need(sha(a.work/'termination-fixture-01/FIXTURE.json')==sha(Path(__file__).parent/'EOG_FIXTURE_V1.json'),'Published fixed diagnostic identity')
    source={str(x.resolve()):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')}
    save(a.work/'CONTINUATION-02-SOURCE_FREEZE.private.json',dict(source_commit=a.source_commit,files=source,
        independent_R_sha256=sha(a.work/'reference-01/REFERENCE_FREEZE.json'),
        fixture_sha256=sha(a.work/'termination-fixture-01/FIXTURE.json'),formal_panel_permitted_only_after_all_native_gates=a.run_panel))
    lock=(a.baseline.parent/'STUDY_SCHEDULING.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
    for path,h in source.items():need(sha(path)==h,'Continuation source changed while waiting')
    old=a.work/'qualification-01';failed=old/'runs'/(d.FAMILY+'-natural-W_L4_M')
    need(read(failed/'HOST.json')['status']=='FAILED' and read(failed/'HOST.json')['worker_wall_s']>=900,'Retained original timeout required')
    need(not (a.work/'qualification-02').exists(),'Fresh explicit continuation epoch')
    original_factory=d.study;reuse=[];original_bank=d.native.Bank

    def verify_run(out,job,build):
        h=read(out/'HOST.json');launch=read(out/'launch.json')
        need(h['status']=='COMPLETE' and launch['job_sha256']==sha(job) and launch['build_sha256']==sha(build),'Only exact complete native jobs may be reused')
        b=read(build);need(sha(b['executable'])==b['executable_sha256'],'Reused executable changed')
        for name,row in read(out/'LOADED_MODULES.json').items():
            if row['kind']=='ELF_file':need(sha(name)==row['sha256'],'Actual reused module changed')
        need(read(out/'native/CAPABILITY.json')==read(job)['capability_request'],'Reused native capability mismatch')
        reuse.append(dict(job_sha256=sha(job),launch_sha256=sha(out/'launch.json'),native_result_sha256=sha(out/'native/result.json'),native_replayed=False))

    def factory(args):
        s=original_factory(args);base_execute=s.execute
        def execute(self,label,family,job,core='reference'):
            if core=='reference':
                prior_job=old/'jobs'/(label+'.json');prior=old/'runs'/label
                if prior_job.exists():
                    base=copy.deepcopy(self.models[family]);base.update(job);base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(residency='target_only',draft=False)
                    base['capability_request']=d.capability(self.models[family],read(self.w/'MODEL_STRUCTURES.json'),'reference',base.get('lowering','WHOLE_UB1'))
                    need(read(prior_job)==base,'Retained R job differs; do not guess reuse')
                    verify_run(prior,prior_job,self.ref_build);self.modules.setdefault((core,family),prior/'LOADED_MODULES.json');return prior
            return base_execute(label,family,job,core)
        s.execute=types.MethodType(execute,s)
        def matrix(self,family):
            cases=read(self.w/'inputs-01'/(family+'-GEOMETRY.json'))['cases'];ref=old/'runs'/(family+'-matrix-R')
            verify_run(ref,old/'jobs'/(family+'-matrix-R.json'),self.ref_build)
            for arm,(core,cut,draft) in d.ARMS.items():
                if draft:continue
                proof=old/(family+'-matrix-'+arm+'-CHECKED.json');report=read(proof);need(report['passed'],'Prior geometry proof failed')
                locations={}
                for i,group in enumerate(report['groups']):
                    label=family+'-matrix-'+arm+f'-group{i}';out=old/'runs'/label
                    verify_run(out,old/'jobs'/(label+'.json'),a.builds/core/'BUILD.json')
                    need(sha(out/'native/result.json')==group['actual_native_result_sha256'],'Prior geometry native result changed')
                    locations.update({name:out for name in group['cases']})
                need(set(locations)=={c['name'] for c in cases},'All12 original geometry cases')
                for row in report['rows']:
                    actual=locations[row['case']]/'native'/row['case']/'captures'/str(row['position']);expected=ref/'native'/row['case']/'captures'/str(row['position'])
                    need(sha(actual/'frontier.f32')==row['vector']['actual_sha256'] and sha(expected/'frontier.f32')==row['vector']['reference_sha256'],'Original full-vector operand changed')
                    if 'active_KV' in row:
                        need(sha(actual/'sequence.bin')==row['active_KV']['actual_raw_sha256'] and sha(expected/'sequence.bin')==row['active_KV']['reference_raw_sha256'],'Original state operand changed')
                dest=self.out/proof.name;shutil.copy2(proof,dest);self.reports.append(dest)
            print('REUSED_COMPLETE_GEOMETRY_ALL_FOUR_M',flush=True)
        s.matrix=types.MethodType(matrix,s)
        def natural(self,family):
            roots=read(self.w/'inputs-01'/(family+'-DEVELOPMENT.json'))['inputs'];cap_input=dict(roots[0],cap=1)
            free=self.execute(family+'-free-independent-R',family,dict(inputs=[dict(name=f'dev-{i}',input=x,capture=True) for i,x in enumerate(roots)]))
            banks={i:original_bank(self,family,i,x,free/'native'/f'dev-{i}') for i,x in enumerate(roots)}
            extra=read(self.w/'termination-fixture-01/FIXTURE.json');need(extra['model_forwards']==0 and extra['formal_samples_added']==0,'Frozen semantic diagnostic only')
            for x in extra['inputs']:
                i=len(roots);roots.append(x)
                reference=self.execute(family+f'-EOG-fixture{i}-R',family,dict(inputs=[dict(name=f'dev-{i}',input=x,capture=True)]))
                need(read(reference/'native'/f'dev-{i}/receipt.json')['terminal_kind']=='EOG','Fixed diagnostic did not observe real native EOG; retain failure')
                banks[i]=original_bank(self,family,i,x,reference/'native'/f'dev-{i}')
            cap_ref=self.execute(family+'-cap1-independent-R',family,dict(inputs=[dict(name='cap1',input=cap_input,capture=True)]))
            # Structural capture-work estimate, independent of model outputs and
            # numerical arm. Heavy/clean pairs stay atomic; every pair remains.
            profile=self.structures[family];per_token=profile['layers']*(profile['K_elements']+profile['V_elements'])*2
            items=[(f'dev-{i}',x) for i,x in enumerate(roots)]+[('cap1',cap_input)]
            estimate=lambda x:per_token*(int(x['cap'])*len(x['prompt_ids'])+int(x['cap'])*(int(x['cap'])-1)//2)
            groups=[];ceiling=12*1024**3
            for name,x in sorted(items,key=lambda item:(-estimate(item[1]),item[0])):
                target=next((g for g in groups if g['estimated_capture_bytes']+estimate(x)<=ceiling),None)
                if target is None:target=dict(items=[],estimated_capture_bytes=0);groups.append(target)
                target['items'].append((name,x));target['estimated_capture_bytes']+=estimate(x)
            plan=[dict(names=[name for name,_ in g['items']],estimated_capture_bytes=g['estimated_capture_bytes']) for g in groups]
            save(self.out/'NATURAL_PARTITION_PLAN.json',dict(groups=plan,all_original_pairs_preserved=True,worker_timeout_s=900,
                criterion='First-fit decreasing conservative target-state capture bytes,12GiB per group; one oversized pair may occupy a group alone',model_outputs_used_for_grouping=False))
            for arm,(core,cut,draft) in d.ARMS.items():
                paths={};details=[]
                for i,g in enumerate(groups):
                    inputs=[dict(name=name+'-'+kind,input=x,capture=kind=='heavy') for name,x in g['items'] for kind in ('heavy','clean')]
                    out=self.execute(family+'-natural-'+arm+f'-group{i}',family,dict(inputs=inputs,lowering=cut,draft=draft,draft_width=4 if draft else 1,residency='matched' if draft else 'target_only',profile=False),core)
                    meta=read(out/'native/result.json');need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'Real per-worker residency retained')
                    for name,_ in g['items']:paths[name]=(out,meta)
                    details.append(dict(group=i,names=plan[i]['names'],native_result_sha256=sha(out/'native/result.json'),host_sha256=sha(out/'HOST.json'),
                        module_map_sha256=sha(out/'LOADED_MODULES.json'),contexts=meta['total_observed_API_calls']['context_creates']))
                    print('COMPLETE_NATURAL_GROUP',arm,i,flush=True)
                rows=[]
                for i,x in enumerate(roots):
                    out,meta=paths[f'dev-{i}'];rows.append(banks[i].check(out/'native'/f'dev-{i}-heavy',out/'native'/f'dev-{i}-clean',meta,draft))
                out,meta=paths['cap1'];cap=read(out/'native/cap1-heavy/receipt.json');clean=read(out/'native/cap1-clean/receipt.json');r=read(cap_ref/'native/cap1/receipt.json')
                need(d.native.endpoint(cap)==d.native.endpoint(clean)==d.native.endpoint(r),'cap1 endpoint contract')
                need(not cap['cycles'] and cap['target_final_kv']==dict(min=0,max=len(cap_input['prompt_ids'])-1),'cap1 pending not materialized')
                need(all(v==0 for v in clean['observed_API_calls_within_service'].values()),'cap1 clean API calls')
                physical=self.physical(cap,cap_input,draft);self.physical(clean,cap_input,draft)
                for row in (cap,clean):row['study_cap']=1;self.trace(row,cap_input['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                vector=d.checks.vector_pair(out/'native/cap1-heavy/target/initial.f32',cap_ref/'native/cap1/captures'/str(len(cap_input['prompt_ids']))/'frontier.f32',meta['vocab'])
                state=d.checks.state_pair(out/'native/cap1-heavy/target/state/terminal/sequence.bin',cap_ref/'native/cap1/captures'/str(len(cap_input['prompt_ids']))/'sequence.bin',len(cap_input['prompt_ids']),self.parse,self.profiles[family])
                self.report(family+'-natural-'+arm+'-CHECKED',dict(passed=all(r['passed'] for r in rows) and vector['equal'] and state['equal'],family=family,arm=arm,roots=rows,
                    cap1=dict(full_vector=vector,active_state=state,physical=physical,actual_termination=r['terminal_kind']),target_only=not draft,groups=details,
                    complete_native_controls=True,development_contexts_recreated_between_groups=True,original_failed_worker_not_admitted=True))
                # An explicitly derived directory mapping for the unchanged graph
                # checker, never a fabricated native HOST/result receipt.
                view=self.out/'runs'/(family+'-natural-'+arm);(view/'native').mkdir(parents=True)
                for name,(actual,_) in paths.items():
                    for kind in ('heavy','clean'):(view/'native'/(name+'-'+kind)).symlink_to(actual/'native'/(name+'-'+kind),target_is_directory=True)
                save(view/'DERIVED_VIEW.json',dict(native_worker=False,groups=details,original_request_bytes_unchanged=True))
            save(self.out/'REFERENCE_AND_GEOMETRY_REUSE.json',dict(reused=reuse,old_failed_native_outputs_admitted=False,raw_operands_rehashed=True))
        s.natural=types.MethodType(natural,s)
        save(s.out/'TIMEOUT_REPAIR.json',dict(old_failed_host_sha256=sha(failed/'HOST.json'),old_failed_job_sha256=sha(old/'jobs'/(d.FAMILY+'-natural-W_L4_M.json')),
            reason='Combined ten-request heavy natural qualification exceeded900s after six completed requests; retain partial output without admitting it',
            numerical_binaries_changed=False,independent_R_changed=False,formal_slots_retried=False,
            development_reexecution=True,scope='Explicit new development orchestration epoch, not selective formal retry',
            added_EOG_fixture_sha256=sha(a.work/'termination-fixture-01/FIXTURE.json'),
            added_fixture_scope='Four original R development endpoints were CAP128; one frozen short-instruction EOG diagnostic is added, without changing formal roots'))
        return s
    d.study=factory
    try:
        d.qualify(a);d.negatives(a)
        if a.run_panel:
            import run_panel
            run_panel.execute(a)
    except BaseException as e:
        save(a.work/'CONTINUATION-02-STATUS.json',dict(status='FAILED_RETAINED',error=str(e),formal_performance='NOT_RUN'));raise
    save(a.work/'CONTINUATION-02-STATUS.json',dict(status='COMPLETE' if a.run_panel else 'QUALIFIED_FORMAL_NOT_RUN',
        qualification_sha256=sha(a.work/'qualification-02/NATIVE_CHECKS_COMPLETE.json'),original_timeout_preserved=True,
        results_sha256=sha(a.work/'panel-01/RESULTS.json') if a.run_panel else None))

if __name__=='__main__':main()
