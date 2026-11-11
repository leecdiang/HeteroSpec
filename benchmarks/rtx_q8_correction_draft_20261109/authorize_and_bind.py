"""Record received authorization and bind all execution sources before inference."""
from common import HERE,AUDIT,ORIGINAL,OLD,read,put,sha,now

def main():
    p=read(HERE/'JOB_MANIFEST.json');p['status']='AUTHORIZED_EXACT_37_NOT_EXECUTED';p['authorization']='Explicit user reply: 完善草案后，执行37次GPU补证'
    put(HERE/'EXECUTION_AUTHORIZATION.json',dict(recorded_utc=now(),user_instruction='完善草案后，执行37次GPU补证',GPU_requests_authorized=37,
        formal_timing_rerun_authorized=False,source_input_criteria_changes_authorized=False,publication_readback_required_before_first_GPU_output=True))
    put(HERE/'EXECUTION_PLAN.json',p)
    paths=[HERE/n for n in ('common.py','check_output.py','run_supplement.py','PROTOCOL.md','JOB_MANIFEST.json','EXECUTION_PLAN.json','EXECUTION_AUTHORIZATION.json',
        'REFERENCE_COVERAGE.json','LEDGER_SNAPSHOT.json','RESOURCE_DRAFT.json','OFFLINE_VALIDATION.json')]
    paths += [AUDIT/'core.py',AUDIT/'evidence/OPTIONAL_SUPPLEMENT_DRAFT.json',ORIGINAL/'SOURCE_BINDINGS.json',ORIGINAL/'DRIVER_MODULE_PINS.json',OLD/'SOURCE-v2.json']
    put(HERE/'EXECUTION_SOURCE_BINDINGS.json',dict(schema='heterospec.rtx213.supplement-source.v1',files={str(p):sha(p) for p in paths},
        model_weights_included=False,qualification_only=True,new_GPU_requests=0,native_epoch='Unmodified original scalar R and PR213 Windows frontend-v2'))
    print('Recorded explicit37-request authorization and complete pre-output execution binding',flush=True)

if __name__=='__main__':main()
