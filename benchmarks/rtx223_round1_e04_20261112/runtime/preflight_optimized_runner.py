"""Run unchanged focused cases under -O with a fresh output directory only."""
from pathlib import Path
import hashlib,json,sys

HERE=Path(__file__).resolve().parent;original=HERE/'preflight_v2.py';raw=original.read_bytes();text=raw.decode('utf8')
old="OUT=ROOT/'e04/preflight-v2'";new="OUT=ROOT/'e04/preflight-v2-O'"
if text.count(old)!=1:raise RuntimeError('expected exactly one output-directory binding')
effective=text.replace(old,new);out=HERE.parent/'e04/preflight-v2-O';code=0
try:exec(compile(effective,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
except SystemExit as exc:code=exc.code
receipt={'kind':'SAME_FOCUSED_CASES_OPTIMIZED_PYTHON','python':sys.version,'python_flags':str(sys.flags),'optimized':not __debug__,'original_test_source':str(original),'original_source_sha256':hashlib.sha256(raw).hexdigest(),'only_text_substitution':{'from':old,'to':new},'effective_test_source_sha256':hashlib.sha256(effective.encode('utf8')).hexdigest(),'case_logic_unchanged':True,'returncode':code,'GPU_launches':0,'DLL_loads':0}
(out/'OPTIMIZED_RUN.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
raise SystemExit(code)
