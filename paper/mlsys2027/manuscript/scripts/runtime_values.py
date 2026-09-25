"""Paper formatting of authoritative runtime values; no new estimators."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / 'benchmarks/m4_runtime' / name).read_text())
def values():
    a=load('FORMAL_ANALYSIS.json'); p=load('runtime_policy_protocol_v0.json')
    f=load('CALIBRATION_FREEZE.json'); q=load('QUALIFICATION_REPORT.json')
    out={}; sources={}
    def add(name,value,source,digits=None):
        out[name]=str(value) if digits is None else f'{value:.{digits}f}'
        sources[name]=source
    for tag,key,ci in [('Guard','geometric_mean_target_over_guard','target_over_guard_95pct_prompt_bootstrap_ci'),('Always','geometric_mean_target_over_always_spec','target_over_always_spec_95pct_prompt_bootstrap_ci'),('Oracle','geometric_mean_guard_over_oracle','guard_over_oracle_95pct_prompt_bootstrap_ci')]:
        add('RT'+tag,a['overall'][key],'FORMAL_ANALYSIS.json:overall.'+key,4)
        for i,suffix in enumerate(['Lo','Hi']):add('RT'+tag+suffix,a['overall'][ci][i],f'FORMAL_ANALYSIS.json:overall.{ci}[{i}]',4)
    add('RTFallback',100*a['control']['fallback_request_fraction'],'FORMAL_ANALYSIS.json:control.fallback_request_fraction * 100',1)
    for name,value,source in [
        ('RTK',p['k'],'runtime_policy_protocol_v0.json:k'),('RTCap',p['max_output_tokens'],'runtime_policy_protocol_v0.json:max_output_tokens'),
        ('RTRounds',f['selected']['E'],'CALIBRATION_FREEZE.json:selected.E'),('RTMargin',int(f['selected']['margin']),'CALIBRATION_FREEZE.json:selected.margin'),
        ('RTCalibration',len(load('CALIBRATION_SPLIT.json')['tasks']),'CALIBRATION_SPLIT.json:len(tasks)'),
        ('RTQualification',len(load('QUALIFICATION_SPLIT.json')['tasks']),'QUALIFICATION_SPLIT.json:len(tasks)'),
        ('RTPrompts',a['overall']['prompt_count'],'FORMAL_ANALYSIS.json:overall.prompt_count'),
        ('RTQualPairs',q['required_per_condition'],'QUALIFICATION_REPORT.json:required_per_condition'),
        ('RTReps',p['repetitions'],'runtime_policy_protocol_v0.json:repetitions'),
        ('RTObservations',p['formal']['tasks']*p['repetitions']*len(p['conditions']),'runtime_policy_protocol_v0.json:formal.tasks * repetitions * len(conditions)'),
        ('RTExact',a['correctness']['required_direct_id_pairs_per_condition'],'FORMAL_ANALYSIS.json:correctness.required_direct_id_pairs_per_condition'),
        ('RTBootstrap',format(a['bootstrap_resamples'],','),'FORMAL_ANALYSIS.json:bootstrap_resamples'),
        ('RTSeed',a['bootstrap_seed'],'FORMAL_ANALYSIS.json:bootstrap_seed')]:add(name,value,source)
    return out,sources
def tex():
    return '% Generated from frozen runtime evidence by runtime_values.py.\n'+''.join('\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in values()[0].items())
if __name__=='__main__':
    (HERE/'tables/runtime_values.tex').write_text(tex())
