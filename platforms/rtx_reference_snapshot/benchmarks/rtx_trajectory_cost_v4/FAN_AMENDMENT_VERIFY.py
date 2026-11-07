"""Independent, zero-inference audit of the explicit fan-only protocol amendment."""
import sys,json,hashlib
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def material(fields):return {k:v for k,v in fields.items() if not k.startswith(('fan_','aura_','keyboard_','lighting_'))}
def fans(fields):return {k:v for k,v in fields.items() if k.startswith('fan_profile_') or k in ['fan_mode','fan_manual','fan_auto','fan_target','fan_rpm']}

def check(root):
    root=Path(root);m=root/'metadata' if (root/'metadata').exists() else root/'benchmarks/rtx_trajectory_cost_v4'
    src=root/'frozen_source/scripts/platform/rtx_trajectory_cost_v4' if (root/'metadata').exists() else root/'scripts/platform/rtx_trajectory_cost_v4'
    sys.path.insert(0,str(src));import verify_A,verify_receipts
    auth=read(m/'FAN_AMENDMENT.json');baseline=read(m/'FAN_AMENDMENT_HOST_BASELINE.json');original=read(m/'ENVIRONMENT.json')
    anonymous=read(root/'MANIFEST.json').get('anonymous',False) if (root/'MANIFEST.json').exists() else False
    require(auth['user_authorization_verbatim']=='我调了下风扇转速而已，不影响实验，继续完成吧','direct fan-continuation authority missing')
    require(auth['existing_pre_live_reused_without_model_rerun']==228 and auth['fresh_unexposed_cohort_claimed'] is False,'reuse/exposure scope changed')
    require(read(m/'JOINT_BLOCKED.json')['reason']=="RuntimeError('HOST_CONFIGURATION_CHANGED')" and read(m/'A_TERMINAL.json')['same_cohort_A_resume_forbidden'],'original stop record lost')
    require(read(root/'work/A-pre-live/records.json')['status']=='PROVENANCE_INVALID','original phase classification changed')
    if not anonymous:
        for name,v in auth['preserved_original_files'].items():require(sha(root/name)==v['sha256'],'original stop/prefix file changed '+name)
    require(original['os']==baseline['os'] and original['gpu']['values'][:3]==baseline['gpu']['values'][:3],'OS/GPU identity changed')
    require(material(original['GHelper_config_fields'])==material(baseline['GHelper_config_fields']),'non-fan material settings changed')
    before=read(root/'work/HOST_OBSERVATION_A_PRE_LIVE_AFTER.json')
    require(material(original['GHelper_config_fields'])==material(before['GHelper_config_fields']),'pre-live drift included non-fan material settings')
    pre=verify_A.pre_live(root,m);pre.pop('rows');require(pre['status']=='PRE_LIVE_QUALIFIED' and pre['H2_R_ONLY']['exact_pairs']==57,'numerical pre-live gate failed')
    result={'status':'PASS','amendment_scope':'Directly authorized fan-only host-policy amendment after predictor observation and before native live outcomes; original strict-protocol stop and classification preserved. No new unexposed cohort or original no-deviation claim.','original_pre_live_valid_raw_conditions':228,'numerical_pre_live':pre,'fresh_model_retries':0,'non_fan_material_settings_equal':True,'B_fan_control_stability':None,'B_observed_conditions':0,'anonymous':anonymous}
    for name in ['A-live','B-formal']:
        p=root/'work'/name/'records.json'
        if not p.exists():continue
        manifest=read(p)
        for entry in manifest['runs']:
            r=read(root/entry['path']/'record.json')
            for edge in ['device_before','device_after']:
                observed=r[edge]['ghelper_amendment_observation']
                require(material(observed['fields'])==material(baseline['GHelper_config_fields']),'non-fan settings drift during new model run')
                require(observed['utc']>=auth['recorded_utc'],'host observation predates authority')
        if name=='B-formal':
            expected=fans(read(m/'FAN_AMENDMENT_B_HOST_BASELINE.json')['GHelper_config_fields']);stable=True
            for entry in manifest['runs']:
                r=read(root/entry['path']/'record.json')
                stable=stable and all(fans(r[edge]['ghelper_amendment_observation']['fields'])==expected for edge in ['device_before','device_after'])
            result.update(B_fan_control_stability=stable,B_observed_conditions=len(manifest['runs']))
    if not anonymous:
        for stage in ['FAN_AMENDMENT']:
            if (m/(stage+'_REMOTE_RECEIPT.json')).exists():result[stage+'_membership']=verify_receipts.checkpoint(root,m,stage)
    return result
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),ensure_ascii=True))
