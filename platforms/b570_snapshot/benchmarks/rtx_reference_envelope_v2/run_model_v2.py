"""One permitted CPU model replacement:streamed shared V and probability-port costs."""
import os,sys,time
from pathlib import Path
from common import V,load,save,sha
from run import root,helper,git
from lifecycle import Child
s=load(root()/'RUN_SPEC.json');d=root()/'M1/revision1';d.mkdir(exist_ok=False)
save(d/'STARTED.json',dict(epoch=time.time(),source_commit=git('rev-parse','HEAD'),source_sha256=sha(V/'model.py'),maximum_seconds=600,reference_kind='ABSTRACT_REFERENCE',replacement=1,allowed_replacements=1,prior_model_preserved='M1/revision0',reason='prior coarse whole-key AV operand denied streamed baseline reuse and omitted probability/partial-accumulator bank reads;correct before any hardware inference',GPU_queries=0))
w=Child(helper())
try:w.run([sys.executable,'-B',str(V/'model.py')],d/'worker',600,os.environ.copy(),2*1024**3,log_cap=65536)
finally:w.terminate()
save(d/'ENDED.json',dict(status='COMPLETE',model_csv_sha256=sha(V/'MODEL.csv'),review_sha256=sha(V/'MODEL_REVIEW.json'),GPU_queries=0))
