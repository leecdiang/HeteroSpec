"""Materialize the unchanged 22x3 native obligations, never execute a case."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=ROOT/'qualification/CASES.json'
original=json.loads(source.read_bytes())
records=[]
for case in original['cases']:
    for arm,expectation in case['arms'].items():
        required=['new binary/core/source/model/module/device identity','runner admission and exact resource reservation','native case receipt and independently bound input']
        if expectation['expected_decision']=='EXACT_FULL_OUTPUT_STATE_PASS':
            required += ['original-path replay and all quantized activation bytes','all requested full vectors','target/draft untrimmed and committed active state/geometry','native dispatch and output ownership']
        elif expectation['expected_decision']=='REBUILD_THEN_EXACT_PASS':
            required += ['actual graph rebuild event and refreshed output mask','all requested full vectors and native states after rebuild']
        elif 'OWNER_INVALID' in expectation['expected_decision']:
            required += ['failure injection in native owner after required stage','rejected reset/retry/continuation on the same owner']
        else:
            required += ['actual native adapter rejects this case before numerical dispatch','zero unexpected dispatches']
        records.append({'id':case['id'],'arm':arm,'expected_decision':expectation['expected_decision'],
            'frozen_q':case.get('frozen_q'),'native_result':'NOT_RUN','numerical_result':'NOT_RUN','clean_guard_result':'NOT_RUN',
            'missing_native_evidence':required,'CPU_fixture_can_substitute':False})
result={'schema':'heterospec.e02.native-qualification-matrix.v1','parent_cases_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'cases':22,'arms':3,'cells':len(records),'records':records,'timing_admitted':False,
    'model_requests':0,'CUDA_contexts':0,'kernel_launches':0,'actual_q8_capture':'NOT_RUN',
    'stop_reason':'Authoritative original-thread/host-process evidence unavailable; full-backend prelaunch kernel cap also unresolved'}
(HERE/'NATIVE_MATRIX.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ('cases','arms','cells','timing_admitted','model_requests','kernel_launches')}))
