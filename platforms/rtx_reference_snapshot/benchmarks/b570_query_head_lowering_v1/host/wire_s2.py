"""Prepare the real inherited actor wire only after S1 fixes a mask variant."""
import copy, pathlib, sys
from common import load
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import core

def request_for(slot,old_root,selected_variant):
    core.need(selected_variant in ('QH_C','QH_D'),'S1-frozen mask variant required')
    old=pathlib.Path(old_root);task=slot['task'];arm=slot['arm'];channel=slot['channel']
    prior=load(old/'p0/PLAN_P1.json')['slots']
    source_arm={'R':'R','R_SHADOW':'R_SHADOW','M_R':'M_R_QB','M_B':'M_B_QB',
                'C_R_PQ':'C_R_PQ','C_B_PQ':'C_B_PQ','C_R_QH':'C_R_QB','C_B_QH':'C_B_QB'}[arm]
    candidates=[x for x in prior if x['task']==task and x['arm']==source_arm and x['mode']==channel]
    core.need(candidates,'missing fixed original request recipe')
    frozen=candidates[0];normalized=copy.deepcopy(frozen['request']);normalized['study']=core.STUDY;normalized['recipe']['name']=arm
    layout='ordinary' if arm=='R' else 'MQ' if arm=='R_SHADOW' else 'PQ' if arm.endswith('PQ') else selected_variant
    normalized['recipe']['continuation']=layout
    req=dict(request_id=slot['id'],prompt_ids=normalized['prompt_ids'],cap=128,capture=False,observation_mode=channel,
             own_bind_sham=False,phase96_diagnostic=False,boundary_cuts=[])
    if arm!='R':req['normalized112']=normalized
    return dict(request=req,wire=core.encode(req),layout=layout,producer_ub=normalized['producer_plan']['ubatch'],capacity=normalized['target_output_capacity'],
                runtime_role='original' if arm=='R' else 'new_qh_actor',origin='S2_REQUEST_PREPARATION_NOT_EXECUTED',
                source_recipe_slot=frozen['slot'],selected_variant=selected_variant)
