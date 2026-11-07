"""Real E1 selector sanitizer and request serializer; no native execution here."""
import json
from pathlib import Path

NAMES=('HS_E1_LAYER','HS_E1_PHASE','HS_E1_Q','HS_E1_MIN_KEY')
def selectors(context):
    layer,phase,q,key=context['layer'],context['phase'],context['q'],context['min_key']
    if not (type(layer)is int and 0<=layer<=255 and phase in ('prefill','continuation') and type(q)is int and q in (1,2,3,4)
            and type(key)is int and key==(128 if q in (2,4) else 0)):
        raise ValueError('invalid frozen E1 coordinate')
    return dict(zip(NAMES,map(str,(layer,int(phase=='continuation'),q,key))))

def clean_environment(parent,mask,trace,context):
    if mask!=0:raise ValueError('native MQ capture must be unrepaired')
    env={k:v for k,v in parent.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
    env.update(HS_SCOPE_MASK='0',HS_NATIVE_CAPTURE=str(trace),HS_Q95_LAYOUT='QB',
               HS_Q95_CAPTURE=str(Path(trace).parent/'snapshots'),**selectors(context))
    return env

def serialized_binding(body,context,child_environment):
    expected=selectors(context)
    if any(child_environment.get(k)!=v for k,v in expected.items()):raise ValueError('selector lost in native child environment')
    if body.get('hs_closeout_mode') not in ('counts','heavy') or body.get('cache_prompt') is not False:
        raise ValueError('invalid E1 request mode/cache')
    # Selector transport is the native getenv API, not an invented HTTP field.
    # Bind the actual serialized HTTP body to the exact serialized child selectors.
    wire=json.dumps(body,ensure_ascii=False).encode()
    restored=json.loads(wire)
    if restored!=body or not isinstance(restored.get('prompt'),list):raise ValueError('request serialization changed IDs')
    return dict(transport='native child environment via verified sanitizer; HTTP observation mode via real serializer',
                selectors=expected,body=restored,wire_utf8=wire.decode(),
                selectors_verified_in_child_environment=True,HTTP_selector_echo_claim=False)

def condition(context):
    selectors(context);q=context['q']
    return dict(name='E1_NATIVE_MQ',prefill_ub=q,maximum_k=q-1,mask=0,spec=q>1,
                required_output_rows=q if q>1 else 1,layout='QB',capture=True)
