"""Prepare formal comparison runner; source frozen later, zero model requests here."""
from pathlib import Path
import json,hashlib
R=Path(__file__).parent
s=(R/'candidate_runner.py').read_text(encoding='utf8')
s=s.replace("native=config['native'];ub=config['ub'];k=config.get('k',2);cap=config.get('cap',128)","native=config['native'];ub=config['ub'];k=config.get('k',2);cap=config.get('cap',128)\n  executable=Path(config['executable'])")
s=s.replace("str(BIN/('b570-candidate-native.exe' if native else 'b570-candidate-target.exe'))","str(executable)")
# Device preflight uses the new helper only for enumeration, no model load.
# Each actual session then verifies physical B570 and complete per-model GPU offload.
(R/'formal_runner.py').write_text(s,encoding='utf8')
print('Formal runner prepared; paid old R and old N1 use original binaries in new output directories.')
