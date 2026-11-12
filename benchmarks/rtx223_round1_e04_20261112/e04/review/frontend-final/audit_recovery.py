"""Final independent CPU build closure review; no producer verifier imports."""
from pathlib import Path
import datetime
import json
from independent_common import need, sha, identity, read_json, audit_core

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / 'e04/frontend/run-v4'
RECOVERY = ROOT / 'e04/frontend/recovery-v1'


def main():
    out = HERE / 'FINAL_FRONTEND_REVIEW.json'
    need(not out.exists(), 'fresh final independent receipt required')
    expected = {'PREPARED.json': '84dee75b8eea7b7c8809d853bdfdb6c09030fc6515acf70cb8c82d25537cf5de',
                'FREEZE.json': '9c51ea9279f36ad3561c524f303c6f2f676446cedc86c456da9e6f56dedd3d2f',
                'POSTFREEZE.json': '6e1330b268a2b48842f84fd1c9b5fc297f5b0df6ecd68d62d41dc52fced08a16',
                'BUILD.json': 'f247f7637485370d806397cdecc08a890dc766fb59da4a767aadb6a320ce668d'}
    for name, digest in expected.items():
        need(sha(RECOVERY / name) == digest, 'recovery final receipt identity differs: ' + name)
    baseline = read_json(HERE / 'V4_INPUT_REHASH.json')
    original = read_json(RUN / 'FREEZE.json')
    recipe = read_json(RUN / 'RECIPE.json')
    prepared = read_json(RECOVERY / 'PREPARED.json')
    frozen = read_json(RECOVERY / 'FREEZE.json')
    post = read_json(RECOVERY / 'POSTFREEZE.json')
    build = read_json(RECOVERY / 'BUILD.json')
    need(baseline['freeze']['sha256'] == sha(RUN / 'FREEZE.json') == prepared['original_freeze_sha256'], 'base freeze changed')
    need(baseline['recipe']['sha256'] == sha(RUN / 'RECIPE.json') == prepared['original_recipe_sha256'] == build['recipe_sha256'], 'original recipe changed')
    need(baseline['verified_entries'] == original['entries'], 'independent all-input rehash belongs to different freeze')
    need(datetime.datetime.fromisoformat(baseline['utc']) > datetime.datetime.fromisoformat(post['verified_utc']), 'independent rehash did not finish after completed recovery')
    base = {e['path']: e for e in baseline['verified_entries']}
    current = {}
    extra = []
    for item in frozen['entries']:
        path = Path(item['path'])
        need(item['path'] not in current and path.resolve().is_relative_to(ROOT / 'e04/frontend'), 'duplicate/outside recovery input')
        current[item['path']] = item
        stat = path.stat()
        need(stat.st_size == item['bytes'] and stat.st_mtime_ns == item['mtime_ns'], 'current recovery input stat differs')
        if item['path'] in base:
            need(item == base[item['path']], 'base snapshot changed in recovery')
        else:
            need(sha(path) == item['sha256'], 'new recovery input bytes differ')
            extra.append(item)
    need(set(base) <= set(current) and post['entries_rehashed'] == len(current), 'original complete closure lost/incorrect count')
    need(frozen['entries'][:-1] == prepared['entries'], 'new prepared closure not exact recovery freeze prefix')
    need(frozen['entries'][-1]['path'] == str((RECOVERY / 'PREPARED.json').resolve()), 'prepared itself not frozen')
    need(frozen['prepared_sha256'] == expected['PREPARED.json'], 'freeze not bound to independently supplied prepared digest')
    need(prepared['original_tree_membership'] == original['tree_membership'], 'original tree membership changed')
    for p, h in prepared['workflow_files'].items():
        need(current[p]['sha256'] == h and sha(p) == h, 'actual recovery helper not frozen')
    controller = (RECOVERY / 'workflow/recovery_v1.py').read_text(encoding='utf8')
    need("Path(__file__).resolve()==workflow/'recovery_v1.py'" in controller and "Path(module.__file__).resolve()==workflow/name" in controller, 'actual staged workflow/import identity guards missing')
    for helper in ('input_freeze.py', 'dep_witness_v3.py', 'closure_witness_v1.py', 'link_witness.py', 'frozen_build_v4.py'):
        need(helper in controller, 'required workflow helper is not explicitly bound')
    need(post['locks_held_through_packed_codegen_link_and_final_verification'] is True and post['uninterrupted_dual_core_lock_session'] is False, 'lock interval scope incorrect')
    need(build['separate_per_core_lock_sessions'] is True and build['loop4_codegen_repeated'] is False, 'recovery history incorrect')
    need(build['exact_selected_duplicate_member_occurrence'] == 'NOT_ATTESTED' and build['native_gate'] == 'BLOCKED', 'overclaimed member/native gate')
    frozen_hashes = {p: e['sha256'] for p, e in current.items()}
    cores = [audit_core(RUN, recipe, core, frozen_hashes, RECOVERY if core == 'packed' else RUN) for core in ('loop4', 'packed')]
    output_by_core = {o['core']: o for o in build['outputs']}
    summaries = []
    for core in cores:
        c = core['core']
        declared = output_by_core[c]
        need(declared['exe_sha256'] == core['exe']['sha256'] and declared['object']['sha256'] == core['object']['sha256'], 'actual output differs from final build receipt')
        if c == 'packed':
            need(post['packed_object']['sha256'] == core['object']['sha256'], 'packed generated-object lock identity differs')
        witness = read_json(RECOVERY / (c + '-WHOLE_ARCHIVE_WITNESS.json'))
        observed = {e['path']: e['sha256'] for e in core['archives']}
        need(observed == {e['path']: e['sha256'] for e in witness['archive_containers']}, 'whole archive receipt disagrees with independently parsed container bytes')
        need(len(witness['map_labels']) == core['independently_resolved_map_archive_member_labels'], 'raw map label count differs')
        need(len(witness['member_labels']) == core['loaded_lines'] + sum(len(g['reading_lines']) for g in core['duplicate_name_different_payload_groups']) or len(witness['member_labels']) > core['loaded_lines'], 'empty/inconsistent member labels')
        pe = read_json(HERE / ('pe-' + c) / 'PE_RECEIPT.json')
        need(pe['target']['sha256'] == core['exe']['sha256'] and pe['target_EXE_runs'] == 0, 'offline PE belongs to another output')
        detail = HERE / ('FINAL_' + c.upper() + '_RAW_REVIEW.json')
        need(not detail.exists(), 'fresh core detail required')
        detail.write_text(json.dumps(core, indent=2), encoding='utf8')
        summaries.append({'core': c, 'actual_EXE': core['exe'], 'detail': identity(detail), 'PE_receipt': identity(HERE / ('pe-' + c) / 'PE_RECEIPT.json'),
                          'dependencies': core['dependency_count'], 'resolved_CPU': core['resolved_CPU'][0][1], 'resolved_features': len(core['resolved_CPU']) - 1,
                          'archive_containers': core['archive_count'], 'archive_members': core['archive_member_count'],
                          'map_archive_member_labels': core['independently_resolved_map_archive_member_labels'],
                          'duplicate_name_differing_payload_groups': len(core['duplicate_name_different_payload_groups'])})
    result = {'schema': 'heterospec.e04.independent-final-frontend-review.v1', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_CPU_BUILD_WHOLE_ARCHIVE_CLOSURE_AND_PE_DISK_IDENTITY_ONLY',
              'recovery_receipts': {n: identity(RECOVERY / n) for n in expected}, 'independent_input_rehash': identity(HERE / 'V4_INPUT_REHASH.json'),
              'original_input_entries_independently_rehashed_after_recovery': len(base), 'additional_recovery_entries_independently_rehashed': len(extra),
              'original_toolchain_members': 19542, 'cores': summaries, 'failed_attempts_preserved': ['v1', 'v2', 'v3', 'v4-narrow-member-witness'],
              'lock_scope': 'Producer source and retained receipts establish separate loop4-v4 and packed-recovery Win32 share-read lock sessions over owned input closures. Reviewer independently rehashed disk inputs after recovery; did not observe all handle intervals or all filesystem reads.',
              'exact_duplicate_member_occurrence': 'NOT_ATTESTED; every candidate payload lies inside an independently hashed frozen archive container',
              'unattested': ['Arbitrary compiler/linker filesystem reads', 'Mutable Windows/system DLLs and Python runtime', 'Exact ambiguous duplicate-member occurrence and COFF symbol-resolution choices', 'Normal EXE/DLL load and CRT/TLS/fatbinary initialization', 'Runtime numeric DLL binding, q8 vectors and model correctness', 'Full-lifecycle physical CUDA kernel budget', 'GPU performance and real request coverage'],
              'producer_verifier_imported': False, 'worker_EXE_runs': 0, 'numeric_DLL_LoadLibrary_calls': 0, 'CUDA_calls': 0, 'models': 0,
              'GPU_launches': 0, 'native_admission': False, 'numerical_qualification': False, 'performance_qualification': False}
    out.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'receipt': str(out), 'sha256': sha(out), 'cores': summaries}, indent=2))


if __name__ == '__main__':
    main()
