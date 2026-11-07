"""Read-only access to the frozen numerical code; no backend is loaded."""
import pathlib
import sys
import os
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'host/aligned_numerical_v2'
sys.path.insert(0,str(OLD))
from panel_common import load,save,sha,encode,digest,parse,modules,need,MODES,STAGES
from analyzer import analyze_files,compare
from native_audit import audit_raw
from run_s1 import runtime_gate,available_ram

BASE='02ac1d7313cb9d29617cda122c4c7556c7f2289e'
RUN_ID='b570-supervised-numerical-v4-20261016-01'
OUT=ROOT/'host_outputs/supervised_numerical_v4'
RUN=OUT/RUN_ID
LIMITS=load(OLD/'F0.json')['limits']
LIMITS=dict(LIMITS,host_attempts=69,graph_calls=68,owned_seconds=900,output_bytes=1024**3)
PYTHON=pathlib.Path('C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe')
GIT='C:/hs/pr108-tools/git/cmd/git.exe'
