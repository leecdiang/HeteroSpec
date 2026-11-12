"""Independent broad-container closure check for retained v4 loop4 artifact."""
from pathlib import Path
import datetime
import json
from independent_common import need, sha, identity, read_json, audit_core

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / 'e04/frontend/run-v4'


def main():
    output = HERE / 'V4_LOOP4_BROAD_CLOSURE.json'
    need(not output.exists(), 'fresh review receipt required')
    prepared = read_json(RUN / 'PREPARED_INPUTS.json')
    frozen = read_json(RUN / 'FREEZE.json')
    recipe = read_json(RUN / 'RECIPE.json')
    need(sha(RUN / 'PREPARED_INPUTS.json') == 'a85e83634a9b041526e8fb4ba4d66ebb99944aa75462e1f1db190305b46b68a1', 'prepared identity differs')
    need(sha(RUN / 'RECIPE.json') == frozen['recipe_sha256'] == prepared['recipe_sha256'], 'recipe not bound')
    need(sha(RUN / 'PREPARED_INPUTS.json') == frozen['prepared_inputs_sha256'], 'prepared not frozen')
    by_path = {}
    for item in frozen['entries']:
        path = Path(item['path'])
        stat = path.stat()
        need(path.resolve().is_relative_to(ROOT / 'e04/frontend'), 'input outside owned e04 frontend')
        need(stat.st_size == item['bytes'] and stat.st_mtime_ns == item['mtime_ns'] and sha(path) == item['sha256'], 'frozen input bytes/stat differ: ' + str(path))
        need(item['path'] not in by_path, 'duplicate freeze entry')
        by_path[item['path']] = item['sha256']
    for item in prepared['entries']:
        need(by_path.get(item['path']) == item['sha256'], 'prepared member not in final freeze')
    roots = [Path(recipe[k]) for k in ('toolchain', 'source', 'dependencies')] + [RUN / 'workflow']
    members = {str(p.resolve()) for base in roots for p in base.rglob('*') if p.is_file()}
    need(members == set(prepared['tree_membership']) == set(frozen['tree_membership']), 'tree membership differs')
    for path, digest in recipe['workflow_files'].items():
        need(by_path.get(path) == digest, 'staged active helper not frozen')
    workflow = (RUN / 'workflow/frozen_build_v4.py').read_text(encoding='utf8')
    need("Path(active_freeze_module.__file__).resolve()==workflow/'input_freeze.py'" in workflow, 'actual freeze helper identity not checked')
    need("Path(active_dependency_module.__file__).resolve()==workflow/'dep_witness_v3.py'" in workflow, 'actual parser helper identity not checked')
    need('execute the staged, frozen workflow copy' in workflow and "actual==info['prescan_dependencies']" in workflow, 'workflow staging/actual dependency guard absent')
    read_freeze = (RUN / 'workflow/input_freeze.py').read_text(encoding='utf8')
    need('0x80000000,0x1,None,3,0x80,None' in read_freeze, 'Win32 read-only sharing contract absent')
    need(frozen['pre_codegen'] is True and frozen['OS_DLLs_attested'] is False, 'incorrect freeze scope')
    input_receipt = HERE / 'V4_INPUT_REHASH.json'
    if not input_receipt.exists():
        input_receipt.write_text(json.dumps({'schema': 'heterospec.e04.independent-input-rehash.v1',
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'freeze': identity(RUN / 'FREEZE.json'),
            'prepared': identity(RUN / 'PREPARED_INPUTS.json'), 'recipe': identity(RUN / 'RECIPE.json'),
            'entries_independently_rehashed': len(by_path), 'verified_entries': frozen['entries'],
            'tree_membership': frozen['tree_membership'], 'producer_verifier_imported': False}, indent=2), encoding='utf8')
    core = audit_core(RUN, recipe, 'loop4', by_path)
    tool_count = sum(Path(p).is_relative_to(Path(recipe['toolchain'])) for p in members)
    result = {'schema': 'heterospec.e04.independent-v4-loop4-broad-closure.v1',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_INPUT_BYTES_AND_ACTUAL_CPU_COMPILE_LINK_ONLY',
              'producer_attempt_status': 'Narrow member witness failed after successful loop4 compile/link; packed absent; no uninterrupted two-core completion claimed',
              'prepared': identity(RUN / 'PREPARED_INPUTS.json'), 'freeze': identity(RUN / 'FREEZE.json'), 'recipe': identity(RUN / 'RECIPE.json'),
              'independently_rehashed_input_entries': len(by_path), 'tree_members': len(members), 'reused_run_v1_toolchain_members': tool_count,
              'workflow': recipe['workflow_files'], 'loop4': core,
              'scope': 'Disk equality to pre-codegen manifest and actual raw compiler/linker witnesses; producer source Win32 share-read locking reviewed; reviewer did not observe an uninterrupted lock interval or trace every OS filesystem read.',
              'producer_verifier_imported': False, 'old_files_locked': False, 'normal_numeric_DLL_loads': 0, 'models': 0, 'CUDA_calls': 0,
              'native_admission': False, 'numerical_qualification': False, 'performance_qualification': False}
    output.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'receipt': str(output), 'sha256': sha(output), 'inputs': len(by_path), 'dependency_count': core['dependency_count'], 'archives': core['archive_count'], 'ambiguous_member_groups': len(core['duplicate_name_different_payload_groups'])}, indent=2))


if __name__ == '__main__':
    main()
