"""Run the unchanged 228-check validator; preserve its frozen historical receipt."""
from pathlib import Path
import subprocess
import sys
import json

HERE = Path(__file__).resolve().parents[1]
EVID = HERE.parent / 'evidence'
historical = EVID / 'NUMERICAL_QA.json'
original = historical.read_bytes()
try:
    subprocess.run([sys.executable, str(HERE/'scripts/validate_evidence.py')], check=True)
    result = historical.read_bytes()
    parsed = json.loads(result)
    assert parsed['status'] == 'PASS' and len(parsed['checks']) == 228
    (EVID/'NUMERICAL_QA_V05.json').write_bytes(result)
finally:
    historical.write_bytes(original)
