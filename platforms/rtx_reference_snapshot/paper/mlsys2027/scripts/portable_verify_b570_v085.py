#!/usr/bin/env python3
"""Run the sealed B570 verifier with cross-platform Windows basename semantics.

The sealed source and all evidence stay byte-identical. Only Path.name for
recorded backslash paths is interpreted as Windows, as on the measurement host.
No assertion is skipped or expected endpoint changed.
"""
import argparse,importlib.util,json,sys
from pathlib import Path,PureWindowsPath
class EvidencePath(type(Path())):
 @property
 def name(self):
  return PureWindowsPath(str(self)).name if '\\' in str(self) else super().name
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
 entry=root/'scripts/platform/b570_partition_intervention_v1/verify_complete.py';sys.path.insert(0,str(entry.parent))
 spec=importlib.util.spec_from_file_location('sealed_b570_complete',entry);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.Path=EvidencePath
 r=module.complete(root);print(json.dumps(r));raise SystemExit(bool(r['errors']))
