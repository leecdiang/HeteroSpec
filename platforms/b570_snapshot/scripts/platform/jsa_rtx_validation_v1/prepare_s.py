"""Freeze all same-day slots before the first formal request."""
from common import *
def main():
    assert read(PUB/'S_BRIDGE_QUALIFICATION.json')['status']=='PASS'
    inputs=read(PUB/'S_INPUTS.json');conditions=read(REPO/'docs/experiments/jsa_rtx_validation_20261010/DESIGN.json')['S']['conditions'];blocks=[]
    for session in range(2):
        for rep in range(4):
            shift=(session+rep)%4;order=conditions[shift:]+conditions[:shift]
            tasks=sorted(inputs,key=lambda t:(hashlib.sha256((f'JSA_RTX_VALIDATION_V1|S|{session}|{rep}|'+t['id']).encode()).hexdigest(),t['id']))
            for position,c in enumerate(order):
                block=f's{session+1}-r{rep+1}-p{position+1}-{c["name"]}'
                blocks.append({'block':block,'session':session+1,'round':rep+1,'position':position+1,'condition':c,'tasks':[t['id'] for t in tasks],'slots':[block+'|'+t['id'] for t in tasks]})
    code=['common.py','run_s.py'];code_hash={n:sha(Path(__file__).parent/n) for n in code}
    save(PUB/'S_F0.json',{'study_id':'JSA_RTX_VALIDATION_V1_FAST_S','utc':now(),'design_head':'0e1949eaf1289f96e2ffaa83babb3b22c8c3e322','starting_head':head(),'author_amendment':'AMENDMENT_FAST_S.md','calendar_date':'2026-10-10','timezone':'Asia/Shanghai','sessions':2,'formal_requests':768,'warmups':32,'block_count':32,'blocks':blocks,'inputs_sha256':sha(PUB/'S_INPUTS.json'),'asset_check_sha256':sha(PUB/'ASSET_CHECK.json'),'code_sha256':code_hash,'warmup_prompt_sha256':hashlib.sha256(WARM.encode()).hexdigest(),'primary':'matched_target/target_scopes client request','statistic':'two individual session log effects; arithmetic mean of session log effects and exponentiation; no cross-date CI','cooling':'idle120 then 3 samples10s apart; util<=5,temp<=55,range<=2; max600s','missing':'no retry or replacement; retain exception and proceed independent blocks','no_cross_date_claim':True})
    save(LOCAL/'S_SLOTS.json',{slot:{'status':'PLANNED','block':b['block']} for b in blocks for slot in b['slots']})
    print('768 slots and 32 blocks frozen',flush=True)
if __name__=='__main__':main()
