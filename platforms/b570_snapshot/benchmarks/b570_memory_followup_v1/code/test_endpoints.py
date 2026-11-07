from common import *
from runner import endpoint
import copy
inp=load(R/'ENGINEERING_INPUTS.json')[0];v=load(R/'VOCAB_CHECKS.json');eog=v['runtime_eog_ids'][0];normal=next(i for i in range(v['vocab_tokens']) if i not in v['runtime_eog_ids'])
x=dict(ids=[normal,eog],eog=[False,True],length=2,terminal_id=eog,stop_reason='EOG',prompt_ids=inp['prompt_ids'],reset_target_min=-1,reset_target_max=-1,draft_decode_calls=0,memory_violation=False)
endpoint(x,inp,128)
bad=[dict(ids=[normal,eog,normal],eog=[False,True,False],length=3,terminal_id=normal),dict(eog=[False,False]),dict(stop_reason='CAP'),dict(length=128),dict(terminal_id=normal),dict(ids=[normal,v['vocab_tokens']]),dict(reset_target_max=0),dict(memory_violation=True)]
for m in bad:
 y=copy.deepcopy(x);y.update(m)
 try:endpoint(y,inp,128)
 except AssertionError:pass
 else:raise AssertionError('Invalid native endpoint accepted')
save(R/'ENDPOINT_NEGATIVE_TESTS.json',dict(status='PASS',negative_cases=len(bad),valid_native_eog_positive_control=1,forwards=0));print('Eight boundary rejection checks PASS')
