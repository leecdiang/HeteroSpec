"""Conservative ZIP/member overhead and complete preparation-copy allowance."""
from common import V,load,save
def main():
    b=load(V/'BUDGET.json');save(V/'PRE_FINAL_STORAGE_BUDGET.json',b);s=b['storage'];lim=b['limits']
    s['preparation_git_metadata_allowance_bytes']=512*1024**2;s['archive_max_entries']=65536;s['archive_name_UTF8_bytes_max']=128;s['archive_header_allowance_bytes']=32*1024**2
    s['archive_upper_bound_bytes']=s['raw_upper_bound_bytes']+s['raw_upper_bound_bytes']//100+s['archive_header_allowance_bytes']
    s['all_derived_upper_bound_bytes']=2*s['raw_upper_bound_bytes']+2*s['archive_upper_bound_bytes']+s['preparation_git_metadata_allowance_bytes']+s['filesystem_allocation_metadata_reserve_bytes']
    s['byte_counter_semantics']='Logical artifact file bytes (stat.st_size), not NTFS allocated clusters or whole-volume use.64MiB extra bookkeeping allowance is not a claimed bound on physical NTFS overhead. Separate free-volume guard protects physical capacity.'
    lim['minimum_volume_free_before_start_bytes']=8*1024**3;lim['minimum_volume_free_during_stage_bytes']=1024**3
    assert s['all_derived_upper_bound_bytes']<lim['total_derived_bytes']
    (V/'BUDGET.json').write_text(__import__('json').dumps(b,separators=(',',':'))+'\n',encoding='utf-8')
    print('Final logical artifact bound:',s['all_derived_upper_bound_bytes'],'<',lim['total_derived_bytes'])
if __name__=='__main__':main()
