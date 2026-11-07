"""Seal qualified host identities and pre-output schedules using reviewed tools."""
from qualify_rtx import *
from design import burst
from baselines import baseline_set

def main():
    assert read(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json')['passed']
    assert read(ROOT/'APPEND_SCOPE_QUALIFICATION.json')['passed']
    assert read(ROOT/'R2-CLOCK-QUALIFICATION.json')['passed']
    assert read(ROOT/'CLEAN_BUILD_PROOF.json')['all_passed']
    assert read(ROOT/'R1_NATURAL_DECISION.json')['decision']=='CLOSE_R1_NATURAL_ONLY_CONTINUE_R2_AND_PORTABILITY'
    builds={}
    for recipe in ('loop4','packed'):
        p=ROOT/'freezes'/recipe
        config=read(p/'BUILD_INPUTS.json');frozen=read(p/'BUILD_FREEZE.json')
        __import__('build_freeze').verify(config,frozen)
        builds[recipe]=dict(configuration=dict(path=str(p/'BUILD_INPUTS.json'),sha256=sha(p/'BUILD_INPUTS.json')),freeze=dict(path=str(p/'BUILD_FREEZE.json'),sha256=sha(p/'BUILD_FREEZE.json')),files=len(frozen['files']),compiled_translation_units=len(frozen['compile_commands']),actual_loaded_modules=frozen['loaded_modules'],runtime_build=read(ROOT/f'runtime-v{VERSION}-{recipe}/BUILD.json'),complete_raw_compiler_reports=str(ROOT/'build-closure'/recipe),not_an_equivalence_proof=True)
    sources={p.name:sha(p) for p in HERE.glob('*.py')}
    put(ROOT/'SOURCE_AND_BUILD.json',dict(design_head=DESIGN,scientific_parent='a28f3474acac793d07b6e6f462cb70bbccfa6ceb',candidate_version=VERSION,complete_builds=builds,common_native_source_snapshot=dict(path=str(ROOT/'NATIVE_REVISION_2.json'),sha256=sha(ROOT/'NATIVE_REVISION_2.json')),source_preparation_recipe_sha256=sha(HERE/'host_rtx.py'),host_execution_files=sources,compiled_native_qualification=dict(path=str(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json'),sha256=sha(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json')),actual_append_scope=dict(path=str(ROOT/'APPEND_SCOPE_QUALIFICATION.json'),sha256=sha(ROOT/'APPEND_SCOPE_QUALIFICATION.json')),fresh_directory_native_build_and_GPU_qualification=dict(path=str(ROOT/'CLEAN_BUILD_PROOF.json'),sha256=sha(ROOT/'CLEAN_BUILD_PROOF.json')),original_references={family:read(ROOT/('R-'+family)/'BUILD.json') for family in ('Qwen','Smol')},no_formal_timing_outputs=True))
    strategies={};development={}
    for arm in ARMS:
        proof=ROOT/f'Qwen-v2-target-only-{arm}-M-QUALIFICATION.json';assert read(proof)['passed'];out=Path(read(proof)['candidate'])
        observed=prior.native_fields(out/'native/result.json',['total_observed_API_calls','phase1_residency'])
        assert observed['phase1_residency']=='target_only' and observed['total_observed_API_calls']['context_creates']==1
        strategies[arm]=dict(status='INCLUDE',target_only_qualification=str(proof),source_binding=str(ROOT/'SOURCE_AND_BUILD.json'),trace_binding=str(out/'native/r0-heavy/receipt.json'),actual_context_creates=1,actual_residency=observed['phase1_residency'],reason='Include even where GPU paths coalesce: the whole/local planner frontend cost paths are not identical. No timing-based exclusion.')
        development[arm]=sum(read(out/'native'/f'r{i}-clean/receipt.json')['service_seconds'] for i in range(4))
    review=dict(schema='phase1.r2-baselines.v2',selection_scope='development_before_R2',reference_id='Qwen-immutable-original-R-C1024',development_binding=str(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json'),reviewer='Original RTX host source/native-trace/qualification review',strategies=strategies,observed_development_best=min(development,key=development.get),fixed_exposed_development_totals_s=development,test_outputs_seen=0)
    baseline_set(review);put(ROOT/'R2/BASELINE_REVIEW.json',review)
    primers=[r['id'] for r in roots('Qwen')[:2]];workers=burst(read(ROOT/'R2/INPUTS.json')['Qwen'],primers,review);assert len(workers)==24
    put(ROOT/'R2/WORKERS.json',workers)
    put(ROOT/'R2/PLAN.json',dict(version='review-v2-native-v2',roots=16,sessions=4,arms=baseline_set(review)['arms'],measurements=384,primers=48,persistent_workers=24,order='four predeclared cyclic rows, not complete Williams balance',primary='L_D4 against EVERY fixed target-only M; four-contrast family,10000 PCG64 root-cluster bootstrap draws',secondary='Matched-residency sensitivity separately; actual per-worker host windows descriptive and conditional on these four sessions',baseline_review_sha256=sha(ROOT/'R2/BASELINE_REVIEW.json'),input_sha256=sha(ROOT/'R2/NATIVE_INPUTS.json'),complete_builds_sha256=sha(ROOT/'SOURCE_AND_BUILD.json'),host_clock_qualification_sha256=sha(ROOT/'R2-CLOCK-QUALIFICATION.json'),peak_memory_scope='Observed device-global2s-sampled peak, not an exact per-process high-water mark',service_and_append_windows_distinct=True,expected_new_reference_requests=16,new_test_forward_outputs=0,draws=10000,no_retries_replacements_or_extensions=True))
    inputs=[ROOT/'R1-STRUCT-SCHEDULE.json',ROOT/'SOURCE_AND_BUILD.json',ROOT/'NATIVE_QUALIFICATION_COMPLETE.json',ROOT/'R2/PLAN.json',ROOT/'R2/WORKERS.json',ROOT/'R2/NATIVE_INPUTS.json',ROOT/'R2/BASELINE_REVIEW.json']
    put(ROOT/'PRE_OUTPUT_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=DESIGN,files={str(p):sha(p) for p in inputs},host_python_files=sources,all_four_factorial_paths_real_and_qualified=True,R1_natural_closed_only=True,formal_R1_measurements=0,R2_new_test_forward_outputs=0,complete_loaded_module_and_dependency_freeze=True))
    print('Sealed real qualified native code, fixed mechanism matrix and six-arm R2; zero formal outputs',flush=True)

if __name__=='__main__':main()
