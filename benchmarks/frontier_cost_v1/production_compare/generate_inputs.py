"""Extract two full prompts without running or selecting on model results."""
import argparse
import hashlib
import json
from pathlib import Path
from protocol import CAP, DRAFT_SHA, JOB_MANIFEST_SHA, K, TARGET_SHA, canonical, digest, validate_inputs, write_new


def generate(path):
    if digest(path) != JOB_MANIFEST_SHA:
        raise ValueError('Authenticated original job manifest required')
    source = json.loads(Path(path).read_text())
    jobs = [job for job in source['jobs'] if job['session'] == 0 and job['arm_label'] == 'LOCAL-loop4-k7']
    if len(jobs) != 1:
        raise ValueError('Unique source job required')
    job = jobs[0]
    if job['job']['target_sha256'] != TARGET_SHA or job['job']['draft_sha256'] != DRAFT_SHA:
        raise ValueError('Original target/draft identities differ')
    entries = sorted((entry for entry in job['job']['inputs'] if entry['name'].startswith('test-')),
                     key=lambda entry: entry['input']['id'])[:2]
    inputs = []
    for index, entry in enumerate(entries):
        original = entry['input']
        inputs.append({'name': f'diagnostic-{index}', 'original_id': original['id'],
                       'original_job': job['id'], 'original_entry': entry['name'],
                       'original_cap': original['cap'], 'cap': CAP, 'k': K,
                       'prompt_ids': original['prompt_ids'],
                       'prompt_sha256': hashlib.sha256(canonical(original['prompt_ids'])).hexdigest(),
                       'formatted_prompt_sha256': original['formatted_prompt_sha256']})
    result = {'schema': 'heterospec.production-pair-inputs.v1',
              'source_manifest_sha256': JOB_MANIFEST_SHA,
              'selection': 'First two lexicographic test roots in session0 LOCAL-loop4-k7; original entire prompt IDs, cap reduced from96 to16; no timing selection.',
              'target_sha256': TARGET_SHA, 'draft_sha256': DRAFT_SHA, 'inputs': inputs}
    validate_inputs(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-job-manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    write_new(args.out, generate(args.original_job_manifest))
