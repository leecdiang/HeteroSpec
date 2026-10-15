"""Static legality and backend preconditions, never output/latency-driven routing."""
import argparse, json
from common import ROOT, load

VERSION='039a24bf61374042e0dc9f3a3619ea40b218a5ad'

def static_errors(x):
    errors=[]
    for field in ('q','k','h','hk','q_nb','q_offset','q_buffer_bytes','mask_nb','mask_ne','phase','role','state_provenance','version'):
        if field not in x:errors.append('missing '+field)
    if errors:return errors
    if x['version']!=VERSION:errors.append('unbound implementation version')
    if x['q'] not in (1,2):errors.append('q outside implemented domain')
    if x['k']<1 or x['hk']<1 or x['h']<1 or x['h']%max(x['hk'],1):errors.append('nondivisible GQA or invalid extent')
    nb=x['q_nb']
    if len(nb)!=4 or nb[0]!=4 or any(b<0 or b%4 for b in nb):errors.append('illegal Q strides')
    else:
        extent=x['q_offset']+4+127*nb[0]+(x['q']-1)*nb[1]+(x['h']-1)*nb[2]
        if x['q_offset']<0 or extent>x['q_buffer_bytes']:errors.append('Q view outside owner buffer')
        # No element aliasing is admitted. Cross-stride condition is not assumed.
        addresses=[d*nb[0]+j*nb[1]+h*nb[2] for j in range(max(0,min(x['q'],2))) for h in range(max(0,x['h'])) for d in range(128)]
        if len(set(addresses))!=len(addresses):errors.append('aliased Q coordinates')
    mn=x['mask_ne'];mb=x['mask_nb']
    if len(mn)!=4 or len(mb)!=4 or mn[0]!=x['k'] or mn[1]<x['q'] or mn[2:]!=[1,1] or mb[0]!=4 or mb[1]!=4*x['k']:
        errors.append('mask shape/stride outside frozen contract')
    if x['phase'] not in ('PREFILL','CONTINUE','VERIFY','RECONCILE','ORDINARY'):errors.append('unknown phase')
    if x['role'] not in ('target','draft'):errors.append('unknown role')
    if x['role']=='draft' and x['q']!=1:errors.append('draft local representation not admitted')
    if not x['state_provenance']:errors.append('state provenance required')
    return errors

def evaluate(x):
    errors=static_errors(x);legal=not errors
    representations={}
    for layout in ('MQ','PQ','QB'):
        elevated=layout=='QB' and x.get('q')==2
        support=legal and not elevated
        representations[layout]=dict(
            static_legal=legal,
            cpu_numeric_correspondence='SYNTHETIC_FIXTURES_ONLY_NOT_AN_OPERAND_CERTIFICATE',
            vulkan_mul_mat_support=support if legal else None,
            vulkan_evidence_level='SOURCE_PROVEN_PROPERTY' if legal else 'UNKNOWN',
            reason='source0.ne[3]=1 != source1.ne[3]=2 for both QK and AV' if elevated else 'source0.ne[3]=source1.ne[3]=1; other device-dependent assignment remains unknown',
            source='ggml-vulkan.cpp:18982 ggml_backend_vk_device_supports_op',
            actual_backend_observation='UNKNOWN',full_request_qualification=False,cost_eligibility='UNKNOWN')
    return dict(version=VERSION,errors=errors,representations=representations,
                state_identity='DECLARED_NOT_OBSERVED',midrequest_switch_allowed=False,
                cpu_scope='72 geometries / synthetic stored inputs; no GPU reference guarantee',
                decision='NO_RUNTIME_POLICY_AUTHORIZED',method_status='VALIDATION_INFRASTRUCTURE')

def example(q=2):
    return dict(q=q,k=128,h=32,hk=8,q_nb=[4,16384,512,16384*q],q_offset=32,
                q_buffer_bytes=32+128*32*q*4,mask_nb=[4,512,16384,16384],mask_ne=[128,32,1,1],
                phase='VERIFY',role='target',state_provenance='synthetic_fixed_operand',version=VERSION)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',nargs='?');a=p.parse_args()
    print(json.dumps(evaluate(load(a.input) if a.input else example()),indent=2))
