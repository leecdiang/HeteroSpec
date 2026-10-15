"""Static legality and backend preconditions, never output/latency-driven routing."""
import argparse, json
from common import ROOT, load

VERSION='039a24bf61374042e0dc9f3a3619ea40b218a5ad'
BACKEND='a9bcbe815d0fc1b9a7914fceb55b7275750169ec58dc8c4a09691ea0ea12f92c'
MAX_INT=(1<<63)-1
INTEGER_FIELDS=('q','k','h','hk','q_offset','q_buffer_bytes','k_buffer_bytes','v_buffer_bytes','mask_buffer_bytes')
VECTOR_FIELDS=('q_nb','k_ne','v_ne','k_nb','v_nb','mask_nb','mask_ne')
TEXT_FIELDS=('backend_dll_sha256','kv_dtype','mask_type','phase','role','state_provenance','version')

def schema_errors(x):
    if type(x) is not dict:return ['input must be a JSON object']
    errors=[]
    for field in INTEGER_FIELDS+VECTOR_FIELDS+TEXT_FIELDS+('mask_nonempty',):
        if field not in x:errors.append('missing '+field)
    if errors:return errors
    for field in INTEGER_FIELDS:
        if type(x[field]) is not int or not 0<=x[field]<=MAX_INT:errors.append(field+' must be an integer in [0, INT64_MAX]')
    for field in VECTOR_FIELDS:
        value=x[field]
        if type(value) is not list or len(value)!=4 or any(type(n) is not int or not 0<=n<=MAX_INT for n in value):
            errors.append(field+' must be a four-element nonnegative int64 array')
    for field in TEXT_FIELDS:
        if type(x[field]) is not str or not x[field].strip():errors.append(field+' must be a nonempty string')
    if type(x['mask_nonempty']) is not bool:errors.append('mask_nonempty must be boolean')
    return errors

def q_rows_overlap(q,h,query_stride,head_stride):
    # Rows contain 128 contiguous F32 elements. Only two query rows are admitted.
    if h>1 and head_stride<512:return True
    if q==1:return False
    if h==1:return query_stride<512
    # Cross-query differences are query_stride + t*head_stride, |t|<=h-1.
    nearest=(-query_stride)//head_stride
    return any(abs(query_stride+max(1-h,min(h-1,t))*head_stride)<512
               for t in (nearest,nearest+1))

def static_errors(x):
    errors=schema_errors(x)
    if errors:return errors
    if x['version']!=VERSION:errors.append('unbound implementation version')
    if x['q'] not in (1,2):errors.append('q outside implemented domain')
    if x['k']<1 or x['hk']<1 or x['h']<1 or x['h']%max(x['hk'],1):errors.append('nondivisible GQA or invalid extent')
    if errors:return errors
    nb=x['q_nb']
    if len(nb)!=4 or nb[0]!=4 or x['q_offset']%4 or any(b<0 or b%4 for b in nb):errors.append('illegal Q strides/offset')
    else:
        extent=x['q_offset']+4+127*nb[0]+(x['q']-1)*nb[1]+(x['h']-1)*nb[2]
        if x['q_offset']<0 or extent>x['q_buffer_bytes']:errors.append('Q view outside owner buffer')
        if q_rows_overlap(x['q'],x['h'],nb[1],nb[2]):errors.append('aliased Q coordinates')
    mn=x['mask_ne'];mb=x['mask_nb']
    if len(mn)!=4 or len(mb)!=4 or mn[0]!=x['k'] or mn[1]<x['q'] or mn[2:]!=[1,1] or mb[0]!=4 or mb[1]!=4*x['k']:
        errors.append('mask shape/stride outside frozen contract')
    if x['kv_dtype']!='F16' or x['mask_type']!='F32' or x['mask_nonempty'] is not True:errors.append('dtype/nonempty-mask precondition missing')
    if x['k_ne']!=[128,x['k'],x['hk'],1] or x['v_ne']!=[x['k'],128,x['hk'],1]:errors.append('K/V shape outside reviewed family')
    if x['k_nb']!=[2,256,256*x['k'],256*x['k']*x['hk']] or x['v_nb']!=[2,2*x['k'],256*x['k'],256*x['k']*x['hk']]:errors.append('K/V strides outside reviewed contiguous family')
    if x['k_buffer_bytes']<256*x['k']*x['hk'] or x['v_buffer_bytes']<256*x['k']*x['hk']:errors.append('K/V buffer too small for declared contiguous view')
    if len(mn)==4 and x['mask_buffer_bytes']<4*mn[0]*mn[1]:errors.append('mask buffer too small')
    if x['phase'] not in ('PREFILL','CONTINUE','VERIFY','RECONCILE','ORDINARY'):errors.append('unknown phase')
    if x['role'] not in ('target','draft'):errors.append('unknown role')
    if x['role']=='draft' and x['q']!=1:errors.append('draft local representation not admitted')
    if not x['state_provenance']:errors.append('state provenance required')
    return errors

def evaluate(x):
    errors=static_errors(x);legal=not errors
    if type(x) is not dict:x={}
    bound=x.get('backend_dll_sha256')==BACKEND
    representations={}
    for layout in ('MQ','PQ','QB'):
        elevated=layout=='QB' and x.get('q')==2
        admitted=legal and not (layout!='MQ' and (x.get('role')=='draft' or x.get('phase')=='PREFILL'))
        batch_equal=(not elevated) if admitted and bound else None
        rejected=batch_equal is False
        if not legal:reason='STATIC_INPUT_REJECTED'
        elif not admitted:reason='ROLE_PHASE_BINDING_NOT_ADMITTED'
        elif not bound:reason='BACKEND_VERSION_UNBOUND'
        elif rejected:reason='BATCH3_MISMATCH_REJECTS_MUL_MAT'
        else:reason='BATCH3_EQUAL_ONLY_FULL_SUPPORT_NOT_EVALUATED'
        representations[layout]=dict(
            static_legal=admitted,
            cpu_numeric_correspondence='SYNTHETIC_FIXTURES_ONLY_NOT_AN_OPERAND_CERTIFICATE' if admitted else 'NOT_ASSESSED',
            vulkan_mul_mat_batch3_equal=batch_equal,
            vulkan_mul_mat_support=False if rejected else None,
            vulkan_support_scope='BATCH3_NECESSARY_CONDITION_ONLY',
            vulkan_batch3_evidence_level='SOURCE_PROVEN_PROPERTY' if admitted and bound else 'UNKNOWN',
            vulkan_evidence_level='SOURCE_PROVEN_PROPERTY' if rejected else 'UNKNOWN',
            backend_version_bound=bound,
            reason=reason,
            source='ggml-vulkan.cpp:18976 ggml_backend_vk_device_supports_op',
            actual_backend_observation='UNKNOWN',full_request_qualification=False,cost_eligibility='UNKNOWN')
    return dict(schema_version=2,version=VERSION,errors=errors,representations=representations,
                state_identity='DECLARED_NOT_OBSERVED',midrequest_switch_allowed=False,
                cpu_scope='72 geometries / synthetic stored inputs; no GPU reference guarantee',
                declaration_scope='Caller-supplied descriptors and nonempty mask declaration; not a buffer/state observation. Dq=Dv=128 and contiguous singleton-batch K/V only.',
                decision='NO_RUNTIME_POLICY_AUTHORIZED',method_status='VALIDATION_INFRASTRUCTURE')

def example(q=2):
    return dict(q=q,k=128,h=32,hk=8,q_nb=[4,16384,512,16384*q],q_offset=32,
                q_buffer_bytes=32+128*32*q*4,mask_nb=[4,512,16384,16384],mask_ne=[128,32,1,1],
                k_ne=[128,128,8,1],v_ne=[128,128,8,1],k_nb=[2,256,32768,262144],v_nb=[2,256,32768,262144],kv_dtype='F16',mask_type='F32',mask_nonempty=True,
                k_buffer_bytes=262144,v_buffer_bytes=262144,mask_buffer_bytes=16384,backend_dll_sha256=BACKEND,
                phase='VERIFY',role='target',state_provenance='synthetic_fixed_operand',version=VERSION)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',nargs='?');a=p.parse_args()
    try:result=evaluate(load(a.input) if a.input else example())
    except (OSError,ValueError) as e:result=evaluate(None);result['errors']=['input read failed: '+str(e)]
    print(json.dumps(result,indent=2,allow_nan=False))
    raise SystemExit(2 if result['errors'] else 0)
