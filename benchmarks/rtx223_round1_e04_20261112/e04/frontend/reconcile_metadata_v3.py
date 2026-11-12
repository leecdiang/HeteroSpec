"""Additive pin-evidence correction only; no binary, codegen input or old receipt changes."""
from pathlib import Path
import datetime,hashlib,json
HERE=Path(__file__).resolve().parent;OUT=HERE/'expected-modules-v1'
AUDIT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e03/audit/DISK_IDENTITIES.json')
EXPECTED_AUDIT='3403a3bd1654e9424ca94de0b197ebc0310ce41912ffc02c775ea6c765c18252'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def put(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,indent=2)
def main():
    need(sha(AUDIT)==EXPECTED_AUDIT,'prior audit identity changed')
    prior=json.loads(AUDIT.read_bytes());roles={v['role']:v for v in prior['inventory'] if v.get('role') in ('loop4','packed')}
    old_closure=OUT/'MODULE_CLOSURE_v2.json';closure=json.loads(old_closure.read_bytes());evidence={}
    for name,module in closure['modules'].items():
        if name in ('ggml-cuda.dll','vcomp140.dll'):continue
        evidence[name]={}
        for role,data in roles.items():
            records=[x for x in data['disk_files'] if Path(x['path']).name.casefold()==name]
            need(len(records)==1,'prior role module missing/ambiguous')
            entry=records[0];need(entry['matches'] is True and entry['expected']==entry['sha256']==module['sha256'],'prior module pin mismatch')
            evidence[name][role]={'audit_path':entry['path'],'expected':entry['expected'],'audit_observed':entry['sha256'],'matches':True}
        need(sha(module['path'])==module['sha256'],'staged module changed')
    need(len(evidence)==7,'seven prior-pinned dependency modules required')
    closure['schema']='heterospec.e04.isolated-module-disk-closure.v3'
    closure['prior_contract_pin_scope']='All seven base/CUDA/MSVC dependencies match BOTH prior loop4/packed expected hashes; VCOMP prior identity UNKNOWN; new numerical DLL is unqualified.'
    closure['prior_pin_evidence']={'audit':str(AUDIT),'audit_sha256':EXPECTED_AUDIT,'modules':evidence}
    closure['metadata_reconciliation']='Per-module v2 MATCHES_BOTH_PRIOR_LOOP4_PACKED_CONTRACT_PINS labels were already supported. Earlier scope prose incorrectly said MSVC pins were absent; this v3 makes the actual seven-module evidence explicit.'
    closure['supersedes']={'path':str(old_closure),'sha256':sha(old_closure),'scope':'metadata clarification only; binary identities and native gate unchanged'}
    new_closure=OUT/'MODULE_CLOSURE_v3.json';put(new_closure,closure)
    old_binding=HERE/'DEPLOYMENT_BINDING_v1.json';binding=json.loads(old_binding.read_bytes())
    binding['schema']='heterospec.e04.frontend-numeric-artifact-binding.v3';binding['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    binding['bound_manifests'].pop(str(old_closure));binding['bound_manifests'][str(new_closure)]=sha(new_closure);binding['module_closure_sha256']=sha(new_closure)
    binding['prior_dependency_pin_scope']='Seven base/CUDA/MSVC module hashes match both historical exact-contract loop4/packed expected pins; VCOMP remains UNKNOWN/proposed native-unqualified.'
    binding['prior_audit_sha256']=EXPECTED_AUDIT;binding['supersedes']={'path':str(old_binding),'sha256':sha(old_binding),'scope':'metadata pin-evidence clarification only'}
    binding['artifact_assembler_sources'][str(Path(__file__))]=sha(__file__)
    new_binding=HERE/'DEPLOYMENT_BINDING_v2.json';put(new_binding,binding)
    old_status=HERE/'STATUS.json';status=json.loads(old_status.read_bytes());status['schema']='heterospec.e04.frontend-status.v2';status['created_utc']=binding['created_utc'];status['supersedes']={'path':str(old_status),'sha256':sha(old_status)}
    status['artifacts'].pop('DEPLOYMENT_BINDING_v1.json');status['artifacts'].pop('expected-modules-v1/MODULE_CLOSURE_v2.json');status['artifacts']['DEPLOYMENT_BINDING_v2.json']=sha(new_binding);status['artifacts']['expected-modules-v1/MODULE_CLOSURE_v3.json']=sha(new_closure)
    status['expected_deployment']['prior_exact_loop4_packed_pinned_dependencies']=7
    status['expected_deployment']['prior_VCOMP_identity']='UNKNOWN; proposed unqualified identity unchanged'
    status['metadata_reconciliation']=closure['metadata_reconciliation'];new_status=HERE/'STATUS_v2.json';put(new_status,status)
    old_readme=HERE/'README_ZH.md';text=old_readme.read_text(encoding='utf8')
    text=text.replace('DEPLOYMENT_BINDING_v1.json','DEPLOYMENT_BINDING_v2.json').replace('MODULE_CLOSURE_v2.json','MODULE_CLOSURE_v3.json')
    text=text.replace('base/CUDA 四项与旧 loop4/packed 固定 pin 完全相同；三项 MSVC runtime 匹配旧入口磁盘副本，但旧 audit 没有相应 contract pin。','base/CUDA 四项与三项 MSVC runtime 共七项，均与旧 audit 中 loop4 和 packed 两个角色的固定 expected pin 完全相同。')
    text+='\n本文件由 README_ZH.md 追加修订而来，修正此前关于三项 MSVC prior pin 缺失的保守描述；实际旧 audit 已存在这些 expected hash。旧文件与全部二进制保留不变。当前状态入口为 STATUS_v2.json。\n'
    new_readme=HERE/'README_ZH_v2.md'
    with new_readme.open('x',encoding='utf8',newline='\n') as f:f.write(text)
    superseded=[old_closure,old_binding,old_status,old_readme]
    index={'schema':'heterospec.e04.frontend-latest-index.v1','current':{str(p.relative_to(HERE)):sha(p) for p in (new_closure,new_binding,new_status,new_readme)},'superseded_metadata_preserved':{str(p.relative_to(HERE)):sha(p) for p in superseded},'reason':closure['metadata_reconciliation'],'binary_and_frozen_input_changes':0,'recompiles':0,'normal_numeric_DLL_loads':0,'GPU_launches':0,'native_release':'BLOCKED'}
    put(HERE/'LATEST.json',index)
    print(json.dumps(index['current'],indent=2))
if __name__=='__main__':main()
