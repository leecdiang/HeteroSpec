"""Analyze the fixed single-pass development costs without a significance test."""
from develop import *
import math
from itertools import combinations

def analyze():
    frozen=json.loads((ROOT/'SHARED_RULE_FREEZE.json').read_bytes());families={}
    for family in ('Qwen','Smol'):
        arms={};coverage=dict(rejection_after_acceptance=0,all_accept_bonus=0,unequal_cap_tail=0,native_EOG=0)
        for arm in json.loads((ROOT/'SCREEN_RULES.json').read_bytes())['order']:
            proof=json.loads((ROOT/(family+'-'+arm+'-QUALIFICATION.json')).read_bytes());assert proof['passed']
            base=arm_output(family,arm);binding=json.loads((base/'binding.json').read_bytes());method=arm.split('-')[0];assert binding['exe']==frozen['runtimes'][method]['build']['exe']
            meta=json.loads((base/'native/result.json').read_bytes());values=[]
            for i in range(4):
                r=json.loads((base/'native'/f'r{i}-clean/receipt.json').read_bytes());w=json.loads((base/'native'/f'r{i}-warmup/receipt.json').read_bytes());h=json.loads((base/'native'/f'r{i}-heavy/receipt.json').read_bytes())
                assert r['endpoint']==w['endpoint']==h['endpoint']
                assert all(v==0 for v in r['observed_API_calls_within_service'].values())
                native=sum(r['target_phases'].values())+sum(r['draft_phases'].values());planning=r['planning_s'];copies=r['output_copy_s'];reset=r['setup_seconds'];teardown=r['teardown_seconds'];other=r['service_seconds']-native-planning-copies-reset-teardown;assert other>=-1e-7
                values.append(dict(root=roots(family)[i]['id'],service_s=r['service_seconds'],warmup_s=w['service_seconds'],qualification_s=h['service_seconds'],native_decode_sync_s=native,reset_s=reset,planning_s=planning,output_copy_s=copies,teardown_s=teardown,other_service_s=other,target_phases=r['target_phases'],draft_phases=r['draft_phases'],target_calls=r['target_calls'],draft_calls=r['draft_calls'],output_tokens=len(r['ids']),stop=r['stop_reason'],online_API_calls=r['observed_API_calls_within_service']))
                coverage['rejection_after_acceptance']+=int(any(c['rejected'] and c['accepted']>0 for c in r['cycles']));coverage['all_accept_bonus']+=int(any(c['commit_kind']=='bonus' for c in r['cycles']));coverage['native_EOG']+=int(r['stop_reason']=='EOG');coverage['unequal_cap_tail']+=int(bool(r['cycles']) and r['stop_reason']=='CAP' and r['cycles'][-1]['accepted'] in [1,2])
            arms[arm]=dict(rows=values,measurement_service_s=sum(x['service_s'] for x in values),warmup_service_s=sum(x['warmup_s'] for x in values),qualification_service_s=sum(x['qualification_s'] for x in values),model_load_s=meta['model_load_s'],pool_setup_s=meta['pool_setup_s'],initial_plan_compile_once_s=meta['resident_initial_plan_compile_s'])
        comparisons={}
        for control in ('M','D1','D4'):
            a=arms['LOCAL-'+control];b=arms['SIMPLE-'+control];ratios=[x['service_s']/y['service_s'] for x,y in zip(a['rows'],b['rows'])]
            comparisons[control]=dict(LOCAL_over_SIMPLE_total_service_ratio=a['measurement_service_s']/b['measurement_service_s'],equal_root_geometric_ratio=math.exp(sum(map(math.log,ratios))/len(ratios)),per_root_ratios=ratios,LOCAL_slower_roots=[x['root'] for x,y in zip(a['rows'],b['rows']) if x['service_s']>y['service_s']])
        all_pairs={}
        for numerator,denominator in combinations(arms,2):
            a,b=arms[numerator],arms[denominator]
            ratios=[x['service_s']/y['service_s'] for x,y in zip(a['rows'],b['rows'])]
            all_pairs[numerator+'/'+denominator]=dict(total_service_ratio=a['measurement_service_s']/b['measurement_service_s'],equal_root_geometric_ratio=math.exp(sum(map(math.log,ratios))/4),per_root_ratios=ratios)
        families[family]=dict(arms=arms,contrasts=comparisons,all_fifteen_descriptive_contrasts=all_pairs,observed_lifecycle_coverage=coverage)
    result=dict(families=families,fixed_one_pass_only=True,independent_roots_per_family=4,confidence_or_significance_claim=False,ratios_above_one_favor_SIMPLE=True,initial_plan_compile_is_one_time_per_resident_context=True,planning_and_copy_costs_already_in_service=True,model_pool_setup_outside_resident_service_but_reported=True,new_natural_test_outputs_generated=False)
    path=ROOT/'DEVELOPMENT_COST_SCREEN.json'
    if path.exists():assert json.loads(path.read_bytes())==result
    else:put(path,result)
    for family,j in families.items():print(family,j['contrasts'],flush=True)

if __name__=='__main__':analyze()
