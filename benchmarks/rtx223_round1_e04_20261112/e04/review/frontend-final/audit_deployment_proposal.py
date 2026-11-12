"""Read-only deployment candidate disk review; no producer parser/loader imports."""
from pathlib import Path
import argparse
import datetime
import json
import struct
from independent_common import need, sha, identity, read_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FRONTEND = ROOT / 'e04/frontend'
EXPECTED_PRIOR = '3403a3bd1654e9424ca94de0b197ebc0310ce41912ffc02c775ea6c765c18252'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--binding', required=True)
    p.add_argument('--binding-sha', required=True)
    p.add_argument('--closure', required=True)
    p.add_argument('--closure-sha', required=True)
    args = p.parse_args()
    out = HERE / 'DEPLOYMENT_PROPOSAL_REVIEW.json'
    need(not out.exists(), 'fresh deployment review required')
    binding_path = FRONTEND / args.binding
    closure_path = FRONTEND / args.closure
    need(sha(binding_path) == args.binding_sha and sha(closure_path) == args.closure_sha, 'final metadata digest differs')
    binding = read_json(binding_path)
    closure = read_json(closure_path)
    staged_path = FRONTEND / 'expected-modules-v1/STAGED_DEPENDENCIES.json'
    staged = read_json(staged_path)
    proposed_path = FRONTEND / 'expected-modules-v1/PROPOSED_VCOMP_IDENTITY.json'
    proposed = read_json(proposed_path)
    prior_path = Path(staged['prior_audit'])
    need(sha(prior_path) == staged['prior_audit_sha256'] == EXPECTED_PRIOR, 'old expected-pin audit identity differs')
    prior = read_json(prior_path)
    prior_roles = {row['role']: {Path(item['path']).name.casefold(): item for item in row['disk_files']} for row in prior['inventory'] if row['role'] in ('loop4', 'packed')}
    need(set(prior_roles) == {'loop4', 'packed'}, 'both prior arms not recorded')
    cache = {}
    def disk(path):
        path = Path(path).resolve()
        key = str(path)
        if key not in cache:
            cache[key] = identity(path)
        return cache[key]
    for path, expected in binding['bound_manifests'].items():
        need(disk(path)['sha256'] == expected, 'bound metadata changed: ' + path)
    for path, expected in binding['artifact_assembler_sources'].items():
        need(disk(path)['sha256'] == expected, 'artifact assembler identity changed')
    need(binding['native_release'] == 'BLOCKED' and binding['actually_loaded_modules'] is None and binding['numeric_DLL_OS_load'] == 'NOT_RUN', 'disk binding overclaims runtime status')
    need(binding['binding_kind'] == 'EXTERNAL_DISK_ARTIFACT_ONLY' and binding['source_toolchain_binding_is_not_runtime_qualification'] is True, 'disk scope absent')
    need(closure['actually_loaded_modules'] is None and closure['expected_modules_are_disk_bindings_only'] is True, 'module closure overclaims actual loading')
    need(closure['VCOMP_classification'] == 'PROPOSED_NEW_MODULE_IDENTITY_NOT_NATIVE_QUALIFIED', 'vcomp proposal classification lost')
    need('UNKNOWN' in binding['prior_VCOMP_identity'], 'vcomp prior identity overclaimed')
    final_frontend = read_json(HERE / 'FINAL_FRONTEND_REVIEW.json')
    audited_frontends = {row['core']: row['actual_EXE'] for row in final_frontend['cores']}
    for item in binding['frontends']:
        need(disk(item['path'])['sha256'] == item['sha256'] == audited_frontends[item['core']]['sha256'], 'frontend binary differs from independent audited EXE')
    numeric = binding['numeric_DLL']
    offline_numeric = read_json(HERE / 'pe-native/PE_RECEIPT.json')
    need(disk(numeric['source'])['sha256'] == disk(numeric['staged'])['sha256'] == numeric['sha256'] == offline_numeric['target']['sha256'], 'numeric staged copy differs from independently audited new DLL')
    need(len(closure['modules']) == 9, 'unexpected candidate DLL count')
    module_rows = []
    for name, module in closure['modules'].items():
        candidate = disk(module['path'])
        need(candidate['sha256'] == module['sha256'] and candidate['bytes'] == module['bytes'], 'candidate module bytes differ: ' + name)
        with Path(module['path']).open('rb') as f:
            header = f.read(64)
            need(header[:2] == b'MZ', 'candidate missing DOS PE header')
            f.seek(struct.unpack_from('<I', header, 60)[0])
            pe_header = f.read(26)
            need(pe_header[:4] == b'PE\0\0' and struct.unpack_from('<H', pe_header, 4)[0] == 0x8664 and struct.unpack_from('<H', pe_header, 24)[0] == 0x20b, 'candidate not AMD64 PE32+')
        row = {'module': name, 'candidate': candidate, 'PE_machine': 'AMD64', 'classification': module['provenance']}
        if name in staged['modules']:
            original = staged['modules'][name]
            row['source'] = disk(original['source'])
            need(row['source']['sha256'] == candidate['sha256'], 'staged copy differs from exact declared source')
            pins = {}
            for role, files in prior_roles.items():
                record = files.get(name.casefold())
                need(record is not None and isinstance(record['expected'], str), 'old expected pin missing')
                need(record['expected'] == record['sha256'] == candidate['sha256'] and record['matches'] is True, 'old expected-pin audit does not match staged candidate')
                need(disk(record['path'])['sha256'] == candidate['sha256'], 'current original-entry disk differs from prior expected pin')
                pins[role] = {'path': record['path'], 'expected': record['expected'], 'current_disk_sha256': disk(record['path'])['sha256']}
            row['prior_expected_pins'] = pins
            need(module['provenance'] == 'MATCHES_BOTH_PRIOR_LOOP4_PACKED_CONTRACT_PINS', 'prior-pin classification differs from actual complete old evidence')
        elif name == 'vcomp140.dll':
            need(proposed['classification'] == module['provenance'] == 'PROPOSED_NEW_MODULE_IDENTITY_NOT_NATIVE_QUALIFIED', 'vcomp classified as qualified')
            need(disk(proposed['source'])['sha256'] == proposed['sha256'] == candidate['sha256'], 'proposed current System32 copy differs')
            row['source'] = disk(proposed['source'])
            row['prior_expected_identity'] = 'UNKNOWN; no qualification inferred from current System32 bytes'
            row['prior_expected_pin_rows'] = {role: files.get(name.casefold()) for role, files in prior_roles.items()}
        elif name == 'ggml-cuda.dll':
            need(module['provenance'] == 'NEW_FRESH_NUMERICAL_BINARY_NOT_NATIVE_QUALIFIED', 'new numeric DLL incorrectly qualified')
            row['source'] = disk(numeric['source'])
        else:
            raise ValueError('unrecognized candidate module')
        module_rows.append(row)
    need(binding['module_closure_sha256'] == sha(closure_path), 'external binding references another closure')
    for path, before in cache.items():
        # Rehash the candidate copies again. Large old/source objects were independently hashed once;
        # no claim of reviewer-held locks over them is made.
        if Path(path).parent == Path(closure['directory']):
            need(sha(path) == before['sha256'], 'candidate copy changed during offline review')
    result = {'schema': 'heterospec.e04.independent-deployment-proposal-review.v1',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS_DISK_CANDIDATE_IDENTITY_ONLY_NATIVE_BLOCKED',
              'binding': identity(binding_path), 'closure': identity(closure_path), 'prior_expected_audit': identity(prior_path),
              'module_count': len(module_rows), 'modules': module_rows, 'independently_hashed_files': len(cache),
              'frontends_match_independent_PE_and_build_receipts': True, 'new_numeric_copy_matches_independent_PE_receipt': True,
              'old_expected_pin_matches': {'loop4': 7, 'packed': 7}, 'VCOMP_prior_identity': 'UNKNOWN',
              'symbol_name_checks': {'producer_count': len(closure['non_system_symbol_checks']), 'independently_recomputed_here': False, 'scope': 'Not a runtime loader or ABI compatibility proof'},
              'prior_metadata_concern': 'Initial concern about MSVC3 prior pins was corrected after direct inspection of both old audit expected rows; no provenance gap remains for all7 pinned modules.',
              'limits': ['Candidate disk files and metadata only', 'No claim of reviewer-held locks over original source/old files', 'No actual loader search-path/API-set/driver/plugin resolution', 'No normal DLL initialization/export calls', 'VCOMP remains proposed new identity, not same-contract qualified', 'No numerical correctness, complete physical kernel quota or performance qualification'],
              'producer_verifier_imported': False, 'worker_EXE_runs': 0, 'numeric_DLL_LoadLibrary_calls': 0, 'CUDA_calls': 0, 'model_requests': 0, 'GPU_launches': 0, 'native_admission': False}
    out.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'receipt': str(out), 'sha256': sha(out), 'modules': len(module_rows), 'files_hashed': len(cache), 'old_pins': result['old_expected_pin_matches']}, indent=2))


if __name__ == '__main__':
    main()
