"""Full-source v3 native descendant, compile only; permanent deny retained."""
import hashlib,json
from pathlib import Path
PIN='4ef88dc28b9765eb8f6d3e01706ca885c64f6fef88c1c6fe05a017599ca95538'
def sha(b):return hashlib.sha256(b).hexdigest()
def derive(path):
 raw=Path(path).read_bytes()
 if sha(raw)!=PIN:raise ValueError('Complete PR229 native worker identity mismatch')
 text=raw.decode();changes=[]
 def replace(name,old,new):
  nonlocal text
  if text.count(old)!=1:raise ValueError('Exact native derivation site changed: '+name)
  text=text.replace(old,new);changes.append({'id':name,'matches':1,'old_sha256':sha(old.encode()),'new_sha256':sha(new.encode())})
 replace('shared-frozen-job-and-v3-client','#include "native_client.hpp"','#include "bridge_job.hpp"')
 if text.count('controller_io(account)')!=3:raise ValueError('Full real writer IO entry count changed')
 text=text.replace('controller_io(account)','bridge_io(account)');changes.append({'id':'all-three-real-writer-IO-entries','matches':3})
 replace('external-whole-job-SHA-argument','hs::n1chain::require(argc==2,"native worker JOB.json; execution NOT ADMITTED");','hs::n1chain::require(argc==3,"native worker JOB.json JOB_SHA256; execution NOT ADMITTED");')
 replace('parse-hashed-sealed-job','const auto job=hs::n1chain::load_json(argv[1]);','hs::n1chain::BridgeJob verified_job(argv[1],argv[2]);const auto job=hs::n1chain::J::parse(verified_job.value.dump());hs::n1chain::require(job.at("role")==job.at("stage"),"native stage/role binding differs");')
 replace('v3-live-controller-identity','hs::n1chain::ControlledNativeClient account(job.at("accounting_socket"),job.at("run_id"),job.at("accounting_manifest_sha256"),job.at("worker_id"),5000,hs::n1chain::ControllerPeer{job.at("controller_owner").at("pid").get<pid_t>(),job.at("controller_owner").at("start_ticks").get<std::string>(),job.at("controller_owner").at("boot_id").get<std::string>()},job.at("owner_lease_sha256"),job.at("capture_root"));','hs::n1chain::BridgeClient account(job.at("accounting_socket"),job.at("run_id"),job.at("manifest_sha256"),job.at("worker_id"),5000,verified_job.controller(),job.at("lease_sha256"),job.at("capture_root"),verified_job.binding());')
 gate='ProductionGate gate;gate.before_backend_init("main-entry");'
 if text.count(gate)!=1 or text.index(gate)>text.index('BridgeJob verified_job'):raise ValueError('Concrete denial before any job/native object lost')
 out=text.encode();return out,{'schema':'hs.production-bridge.native-worker-derivation.v1','original_worker_sha256':sha(raw),'original_worker_bytes':len(raw),'descendant_worker_sha256':sha(out),'descendant_worker_bytes':len(out),'changes':changes,'original_numerical_lifecycle_code_unchanged':True,'permanent_production_gate_retained':True,'native_executables_started':0}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise SystemExit('Fresh native derivation directory required')
 value,receipt=derive(a.source);a.out.mkdir(parents=True);(a.out/'worker.cpp').write_bytes(value);(a.out/'DERIVATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
