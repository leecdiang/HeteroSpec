"""Freeze conservative record/log and filesystem envelopes before any GPU start."""
import shutil
from common import V,load,save
def main():
    p=V/'BUDGET.json';old=load(p);shutil.copyfile(p,V/'PRELIMINARY_CPU_BUDGET.json')
    b=old;st=b['storage'];lim=b['limits']
    # Native JSON hard total192KiB + four32KiB streams +64KiB per-slot
    # commands/admission/audit/lifecycle/terminal records =384KiB per slot.
    lim['numeric_native_JSON_total_bytes']=192*1024;lim['numeric_native_JSON_file_bytes']=64*1024
    lim['census_native_JSON_total_bytes']=15*1024**2
    lim['numeric_nonCAS_bytes_per_slot']=384*1024;lim['control_bytes']=32*1024**2
    lim['readiness_process_commit_bytes']=256*1024**2;lim['controller_commit_bytes']=512*1024**2
    st['numeric_record_log_envelopes_bytes']=720*lim['numeric_nonCAS_bytes_per_slot']
    raw=st['complete_immutable_reference_unique_bytes']+st['all720_outputs_no_dedup_bytes']+st['first_mutant_input_readback_reserve_bytes']+st['numeric_record_log_envelopes_bytes']+st['census_envelope_bytes']+lim['control_bytes']
    zip_bound=raw+raw//100+1024**2
    st['raw_upper_bound_bytes']=raw;st['archive_upper_bound_bytes']=zip_bound;st['filesystem_allocation_metadata_reserve_bytes']=64*1024**2
    st['all_derived_upper_bound_bytes']=2*raw+2*zip_bound+st['preparation_git_metadata_allowance_bytes']+st['filesystem_allocation_metadata_reserve_bytes']
    lim['raw_root_bytes']=raw;assert st['all_derived_upper_bound_bytes']<lim['total_derived_bytes']
    b['pre_GPU_budget_refinement']='CPU-derived final envelopes count all four child log streams, writer-enforced native record limits, complete audit/ledger metadata, filesystem allocation reserve. No new GPU data or post-outcome relaxation.'
    # This is the unexecuted preparation budget. The exact prior version remains.
    p.write_text(__import__('json').dumps(b,separators=(',',':'))+'\n',encoding='utf-8')
    print('Final conservative upper bound',st['all_derived_upper_bound_bytes'],'<',lim['total_derived_bytes'])
if __name__=='__main__':main()
