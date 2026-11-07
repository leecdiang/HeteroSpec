"""CPU source derivation repeatability; no native worker execution."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parent
paths=[ROOT/'_host/source'/n for n in ('llama-context.cpp','llama-context.h','llama-graph.cpp','local_attention.h')]+[ROOT/'native/worker.cpp']
def snap():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=snap()
for script in ('port_native.py','native/port_worker.py','native/add_observations.py','native/finalize_source.py'):
 subprocess.run([sys.executable,'-X','utf8','-B',str(ROOT/script)],check=True)
after=snap();assert before==after,('SOURCE_DERIVATION_DRIFT',before,after)
(ROOT/'p0/SOURCE_REPRODUCTION.json').write_text(json.dumps(dict(status='PASS_BYTE_IDENTICAL_SOURCE_DERIVATION',files=after,native_worker_starts=0),indent=2)+'\n')
print('SOURCE BYTE REPRODUCTION PASS')
