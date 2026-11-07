"""Production entry negatives; no valid author approval or process launch."""
import ast,copy,hashlib
from common import V,load,save,sha
import run_s1b as R
from strict_lifecycle import StrictChild
from clock_source import require_clock

def main():
    f=load(V/'F0.json');p=load(V/'PLAN.json');rows=[]
    f['monitor_contract']['actual_clock']=require_clock() # explicit prospective CPU fixture
    a=dict(stage='S1B_CLEAN_BLOCK_0_EXACT',run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),author_message='CPU_NEGATIVE_FIXTURE_NOT_AUTHOR_APPROVAL',author_message_sha256='0'*64,clean_first_trace_deferred_amendment_accepted=True)
    def reject(name,fn):
        error=None
        try:fn()
        except Exception as e:error=repr(e)
        assert error,name;rows.append(dict(case=name,expected_accept=False,accepted=False,error=error))
    reject('entry_wrong_F0',lambda:R.authority('clean0',f,a|dict(F0_sha256='0'*64)))
    reject('entry_execution_in_run_id',lambda:R.authority('clean0',f,a|dict(run_id=f['execution_id'])))
    reject('entry_swapped_ids',lambda:R.authority('clean0',f,a|dict(run_id=f['execution_id'],execution_id=f['run_id'])))
    reject('entry_no_author_message_hash',lambda:R.authority('clean0',f,a))
    reject('entry_other_execution',lambda:R.authority('clean0',f,a|dict(execution_id='pr116-s1b-exact-r1')))
    pp=copy.deepcopy(p);pp['clean_slots'][0]['run_id']=f['execution_id']
    reject('entry_wrong_slot_identity_before_any_device',lambda:R.check(f,pp))
    ff=copy.deepcopy(f);ff['monitor_contract']['max_monitor_interval_ns']+=1
    reject('entry_threshold_change',lambda:R.check(ff,p))
    reject('production_monitor_cannot_enable_CPU_hooks',lambda:StrictChild(f['console_helper'],f['monitor_contract']).run([f['hosts']['clean']['path']],V/'NEVER_CREATED',60,{},128*1024**2,cpu_hooks=dict(stall_after=0)))
    assert not (V/'NEVER_CREATED.PROCESS.json').exists()
    for s in V.glob('*.py'):ast.parse(s.read_bytes(),filename=str(s))
    rows.append(dict(case='all_Python_sources_parse_CPU_only',accepted=True,expected_accept=True))
    save(V/'CPU_QPC_POST_ACTUAL_CLOCK_TESTS.json',dict(status='PASS',test_count=len(rows),cases=rows,GPU_queries=0,CUDA_loads=0,graph_calls=0))
    print('PASS',len(rows),'production-entry negative/syntax checks;no process launch')
if __name__=='__main__':main()
