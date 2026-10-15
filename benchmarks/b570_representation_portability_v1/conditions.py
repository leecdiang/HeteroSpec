"""Static legality and backend preconditions, never output/latency-driven routing."""
import argparse, json
from common import ROOT, load

VERSION='039a24bf61374042e0dc9f3a3619ea40b218a5ad'
BACKEND='a9bcbe815d0fc1b9a7914fceb55b7275750169ec58dc8c4a09691ea0ea12f92c'

def static_errors(x):
    errors=[]
    for field in ('q','k','h','hk','q_nb','q_offset','q_buffer_bytes','k_ne','v_ne','k_nb','v_nb','k_buffer_bytes','v_buffer_bytes','mask_buffer_bytes','backend_dll_sha256','kv_dtype','mask_type','mask_nonempty','mask_nb','mask_ne','phase','role','state_provenance','version'):
        if field not in x:errors.append('missing '+field)
    if errors:return errors
    if x['version']!=VERSION:errors.append('unbound implementation version')
    if x['q'] not in (1,2):errors.append('q outside implemented domain')
    if x['k']<1 or x['hk']<1 or x['h']<1 or x['h']%max(x['hk'],1):errors.append('nondivisible GQA or invalid extent')
    nb=x['q_nb']
    if len(nb)!=4 or nb[0]!=4 or x['q_offset']%4 or any(b<0 or b%4 for b in nb):errors.append('illegal Q strides/offset')
    else:
        extent=x['q_offset']+4+127*nb[0]+(x['q']-1)*nb[1]+(x['h']-1)*nb[2]
        if x['q_offset']<0 or extent>x['q_buffer_bytes']:errors.append('Q view outside owner buffer')
        # No element aliasing is admitted. Cross-stride condition is not assumed.
        addresses=[d*nb[0]+j*nb[1]+h*nb[2] for j in range(max(0,min(x['q'],2))) for h in range(max(0,x['h'])) for d in range(128)]
        if len(set(addresses))!=len(addresses):errors.append('aliased Q coordinates')
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
    bound=x.get('backend_dll_sha256')==BACKEND
    representations={}
    for layout in ('MQ','PQ','QB'):
        elevated=layout=='QB' and x.get('q')==2
        admitted=legal and not (layout!='MQ' and (x.get('role')=='draft' or x.get('phase')=='PREFILL'))
        support=admitted and not elevated
        representations[layout]=dict(
            static_legal=admitted,
            cpu_numeric_correspondence='SYNTHETIC_FIXTURES_ONLY_NOT_AN_OPERAND_CERTIFICATE',
            vulkan_mul_mat_support=support if admitted and bound else None,
            vulkan_evidence_level='SOURCE_PROVEN_PROPERTY' if admitted and bound else 'UNKNOWN',
            backend_version_bound=bound,
            reason='source0.ne[3]=1 != source1.ne[3]=2 for both QK and AV' if elevated else 'source0.ne[3]=source1.ne[3]=1; other device-dependent assignment remains unknown',
            source='ggml-vulkan.cpp:18976 ggml_backend_vk_device_supports_op',
            actual_backend_observation='UNKNOWN',full_request_qualification=False,cost_eligibility='UNKNOWN')
    return dict(version=VERSION,errors=errors,representations=representations,
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
    print(json.dumps(evaluate(load(a.input) if a.input else example()),indent=2))
