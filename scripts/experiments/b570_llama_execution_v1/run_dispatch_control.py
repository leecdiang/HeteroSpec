"""Qualify diagnostic dispatch logging against the immutable natural baseline."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write
import host
from audit_probe import run
root=Path(sys.argv[1]).resolve();epoch=root/'dispatch-epoch-00'
c=read(root/'host-01.json');c.update(target_gpu_layers=999,draft_gpu_layers=0,candidate_build=str(root/'candidate-dispatch-00/BUILD.json'))
c['policy']['purpose']='Dispatch observer control; frozen selected placement and numerical oracle retained'
write(root/'host-dispatch-00.json',c);host.prepare(root/'host-dispatch-00.json',epoch)
host.execute(epoch,'capacity',[],admit=True);host.execute(epoch,'capacity-oracle',[],oracle=True,admit=True)
slots=read(root/'OPERATOR_LOCALIZE_SLOTS-00.json');slots[0]['id']='dispatch-control-00/layer0'
host.execute(epoch,'dispatch-control-00',slots)
run(epoch,'dispatch-control-00',root/'DISPATCH_NATIVE_CONTROL-00.json',root/'capacity-01/profile-1-epoch')
