"""Run the unchanged seven replay/rejection tests and preserve their old receipt."""
from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[2];E=HERE.parent/'evidence'
def main():
    old=E/'M4_GUARD_ALWAYS_SECONDARY_TEST_QA_V06.json';original=old.read_bytes()
    try:
        subprocess.run([sys.executable,str(REPO/'scripts/platform/m4_runtime/test_guard_always_secondary.py')],cwd=REPO,check=True)
        result=json.loads(old.read_text())
        assert result==json.loads(original)
        (E/'DIRECT_ID_M4_TEST_QA_V07.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    finally:old.write_bytes(original)
if __name__=='__main__':main()
