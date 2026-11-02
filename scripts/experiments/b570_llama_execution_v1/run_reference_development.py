"""Re-admit the explicit projection contract, then run the full natural matrix."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
import host
epoch=Path(sys.argv[1]);host.execute(epoch,'capacity',[],admit=True)
host.execute(epoch,'capacity-oracle',[],oracle=True,admit=True)
r=host.baseline(epoch);print(r['status'],flush=True)
