"""Prospective-only final lock: explicitly stop if both q1 layouts return but differ."""
import datetime
import io
import pathlib
import sys
import unittest
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(HERE))
from common import load,save,sha
path=HERE/'DIAGNOSTIC_F0.json'
path.rename(HERE/'DIAGNOSTIC_F0_DRAFT_01.json')
f0=load(HERE/'DIAGNOSTIC_F0_DRAFT_01.json')
f0['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
f0['preexecution_revision']='If both q1 layouts return, enforce full-vector bitwise equality before q2. Also reject unavailable RSS. No executable change or launch.'
f0['sources']={name:sha(ROOT/name) for name in f0['sources']}
save(path,f0)
stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_admission.py')
r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
save(HERE/'CPU_ADMISSION_TESTS_FINAL.json',dict(success=r.wasSuccessful(),tests=r.testsRun,log=stream.getvalue(),
    F0_sha256=sha(path),all_launches_mocked=True,actual_diagnostic_processes=0))
assert r.wasSuccessful()
print(sha(path))
