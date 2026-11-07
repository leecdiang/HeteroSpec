"""Bounded independent CPU M1 worker;never loads or queries a GPU."""
import os,sys,time
from pathlib import Path
from common import V,load,save,sha
from run import root,helper,git
from lifecycle import Child
s=load(root()/'RUN_SPEC.json');d=root()/'M1';d.mkdir(exist_ok=False)
save(d/'STARTED.json',dict(epoch=time.time(),source_commit=git('rev-parse','HEAD'),model_source_sha256=sha(V/'model.py'),maximum_seconds=300,reference_kind='ABSTRACT_REFERENCE',RTX_DAG='UNKNOWN',GPU_queries=0))
w=Child(helper())
try:w.run([sys.executable,'-B',str(V/'model.py')],d/'worker',300,os.environ.copy(),2*1024**3,log_cap=65536)
finally:w.terminate()
save(d/'ENDED.json',dict(status='COMPLETE',model_csv_sha256=sha(V/'MODEL.csv'),review_sha256=sha(V/'MODEL_REVIEW.json'),GPU_queries=0))
