"""Execute repaired common-state/trace controls with unchanged numerical DLLs."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read
import host
from audit_probe import run
root=Path(sys.argv[1]);epoch=root/'attention-epoch-00'
host.execute(epoch,'capacity',[],admit=True);host.execute(epoch,'capacity-oracle',[],oracle=True,admit=True)
host.execute(epoch,'repair-probes-00',read(root/'REPAIR_PROBE_SLOTS-00.json'))
run(epoch,'repair-probes-00',root/'REPAIR_PROBE_AUDIT-00.json',root/'reference-q8-epoch-00')
