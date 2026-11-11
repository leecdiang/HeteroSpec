"""Read-only access to the frozen numerical code; no backend is loaded."""
import pathlib
import sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'host/aligned_numerical_v2'
sys.path.insert(0,str(OLD))
from panel_common import load,save,sha,encode,digest,parse,modules,need,MODES,STAGES
from analyzer import analyze_files,compare
from native_audit import audit_raw
from run_s1 import runtime_gate,available_ram

BASE='58511a4dfa39776503a14ed3176931c26cf657c4'
RUN_ID='b570-supervised-numerical-v3-20261015-01'
OUT=ROOT/'host_outputs/supervised_numerical_v3'
RUN=OUT/RUN_ID
LIMITS=load(OLD/'F0.json')['limits']
PYTHON=pathlib.Path('C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe')
GIT='C:/hs/pr108-tools/git/cmd/git.exe'
