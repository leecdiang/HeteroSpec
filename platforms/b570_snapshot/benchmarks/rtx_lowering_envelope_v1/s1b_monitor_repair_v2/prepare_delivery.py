"""CPU-only forward copy of existing delivery, leaving historical sources intact."""
from common import V

def main():
    old=V.parent/'s1b_cost_v1'
    for name in ['archive.py','evidence_s1b.py','offline_s1b.py','PROTOCOL.md','AMENDMENT.md']:
        p=V/name;assert not p.exists();p.write_bytes((old/name).read_bytes())
    p=V/'evidence_s1b.py';s=p.read_text()
    s=s.replace("return dict(run_id=p['run_id'],slots=rows","return dict(run_id=p['run_id'],execution_id=p['execution_id'],F0_sha256=sha(Path(frozen)/'F0.json'),slots=rows")
    p.write_text(s,encoding='utf-8')
    p=V/'offline_s1b.py';s=p.read_text().replace('s1b_cost_v1/','s1b_monitor_repair_v2/').replace("s1b_cost_v1'","s1b_monitor_repair_v2'")
    s=s.replace("r=super().snapshot(status);r['conservative_owned_seconds']","r=super().snapshot(status);r.update(run_id=f['run_id'],execution_id=f['execution_id']);r['conservative_owned_seconds']")
    s=s.replace("'add','--sparse',rel","'add','--sparse','--force',rel+'/delivery/raw',rel")
    p.write_text(s,encoding='utf-8')
    p=V/'archive.py';s=p.read_text().replace("'REMOTE_F0_BYTES.json']","'REMOTE_F0_BYTES.json','strict_lifecycle.py','monitor_contract.py','monitor_worker.py','monitor_audit.py','identified_state.py','exact_binding.py','CENSUS_EXACT_AUTHENTICATED.json']")
    s=s.replace("descriptor['members']=len(manifest);save","descriptor['members']=len(manifest);f=load(Path(frozen)/'F0.json');descriptor.update(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(Path(frozen)/'F0.json'));save")
    p.write_text(s,encoding='utf-8')
    print('CPU delivery paths/identities bound to new registration; no GPU')
if __name__=='__main__':main()
