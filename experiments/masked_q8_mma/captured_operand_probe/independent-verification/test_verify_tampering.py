"""Exercise verify.py integrity failures on temporary copies, including -O.

Uses only the standard library itself; the verifier subprocess requires NumPy.
No original input artifacts are modified.
"""
import argparse
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir', type=Path, default=HERE.parent,
                    help='Directory containing authorized original evidence files')
parser.add_argument('--output', type=Path, default=HERE / 'tamper-tests.json',
                    help='Destination test report; defaults beside this script')
args = parser.parse_args()
INPUTS = args.input_dir
FILENAMES = ('operands.json.gz', 'operand-sample.json.gz')
NAME = 'blk.0.attn_q.weight'
original = {name: (INPUTS / name).read_bytes() for name in FILENAMES}
identities = {name: hashlib.sha256(data).hexdigest() for name, data in original.items()}
manifest = json.loads(gzip.decompress(original['operands.json.gz']))
sample = json.loads(gzip.decompress(original['operand-sample.json.gz']))


def selected_record(records):
    return next(row for row in records if row['model'] == '8B' and row['descriptor']['weight']['name'] == NAME)


def mutate(case, records, samples):
    record = selected_record(records)
    if case == 'valid':
        return None
    if case == 'same_length_payload_flip':
        value = bytearray(base64.b64decode(samples[NAME]['input'], validate=True))
        value[0] ^= 1
        samples[NAME]['input'] = base64.b64encode(value).decode()
        return 'SHA-256 digest mismatch'
    if case == 'truncated_payload':
        value = base64.b64decode(samples[NAME]['input'], validate=True)
        samples[NAME]['input'] = base64.b64encode(value[:-4]).decode()
        return 'decoded byte length mismatch'
    if case == 'invalid_base64':
        samples[NAME]['input'] = '!' + samples[NAME]['input'][1:]
        return 'invalid base64'
    if case == 'missing_blob':
        del samples[NAME]['packed32']
        return 'blob field set mismatch'
    if case == 'missing_operator':
        del samples[NAME]
        return 'sample operator set mismatch'
    if case == 'duplicate_descriptor':
        records.append(copy.deepcopy(record))
        return 'expected one 8B descriptor, found 2'
    if case == 'duplicate_route':
        record['routes'].append(copy.deepcopy(record['routes'][0]))
        return 'duplicate route records'
    if case == 'missing_route':
        record['routes'].pop(0)
        return 'route set mismatch'
    if case == 'wide_live_link_mismatch':
        next(row for row in record['routes'] if row['q'] == 32 and row['route'] == 'wide')['sha'] = '0' * 64
        return 'wide32/live output digest mismatch'
    if case == 'route_prefix_digest_mismatch':
        next(row for row in record['routes'] if row['q'] == 2 and row['route'] == 'tile')['sha'] = '0' * 64
        return 'aggregate route-prefix digest verification failed'
    raise ValueError('unknown test case: ' + case)


cases = ('valid', 'same_length_payload_flip', 'truncated_payload', 'invalid_base64',
         'missing_blob', 'missing_operator', 'duplicate_descriptor',
         'duplicate_route', 'missing_route', 'wide_live_link_mismatch',
         'route_prefix_digest_mismatch')
results = []
with tempfile.TemporaryDirectory(prefix='independent-operand-tamper-') as root:
    root = Path(root)
    for case in cases:
        folder = root / case
        work = folder / 'independent-verification'
        work.mkdir(parents=True)
        shutil.copyfile(HERE / 'verify.py', work / 'verify.py')
        records = copy.deepcopy(manifest)
        samples = copy.deepcopy(sample)
        expected_error = mutate(case, records, samples)
        for name, data in (('operands.json.gz', records), ('operand-sample.json.gz', samples)):
            (folder / name).write_bytes(gzip.compress(json.dumps(data).encode(), compresslevel=1, mtime=0))
        for optimize in (False, True):
            command = [sys.executable] + (['-O'] if optimize else []) + [str(work / 'verify.py')]
            run = subprocess.run(command, capture_output=True, text=True, timeout=30)
            passed = (run.returncode == 0 if expected_error is None else
                      run.returncode != 0 and 'ValueError:' in run.stderr and expected_error in run.stderr)
            if expected_error is None and run.returncode == 0:
                parsed = json.loads(run.stdout)
                passed = passed and parsed['all_blob_verifications_pass'] and parsed['all_prefix_manifest_checks_pass']
            results.append({'case': case, 'python_optimized': optimize,
                            'returncode': run.returncode, 'passed': bool(passed),
                            'expected_error': expected_error,
                            'last_stderr_line': run.stderr.strip().splitlines()[-1] if run.stderr.strip() else None})
unchanged = all(hashlib.sha256((INPUTS / name).read_bytes()).hexdigest() == identities[name] for name in FILENAMES)
report = {'tests': len(results), 'positive_tests': 2, 'negative_tests': len(results) - 2,
          'passed_tests': sum(row['passed'] for row in results),
          'original_input_sha256': identities, 'original_inputs_unchanged': unchanged,
          'all_passed': all(row['passed'] for row in results) and unchanged,
          'results': results}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
if not report['all_passed']:
    raise ValueError('independent verifier tamper suite failed')
