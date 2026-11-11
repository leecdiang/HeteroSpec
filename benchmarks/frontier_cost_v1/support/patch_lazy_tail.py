"""Generate a fresh source candidate from a reviewed, whole-file-pinned worker.

No in-place edits, compiler launches, model loading, GPU work, reference changes,
or baseline archive mutation. Both compile modes need new native qualification.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = {
    "afda80c01222a8ecbee11fa689c7231fbedc44d4558c5c28810cd2578a0f57f3": {
        "variant": "authenticated_windows_sourcekit", "replay": False,
        "provenance": "PR203 pins: rtx-phase1-source.zip; native/frontend/worker.cpp",
    },
    "4a748ebd7d7aea489ff00e88b55f3584ae10cdabf244bd34f90040f34c18ec40": {
        "variant": "reconstructed_linux_stage04", "replay": False,
        "provenance": "pinned sourcekit + PR203 sources.port + adapt_host.adapt",
    },
    "429ca63224bffdc62fff65cc0c4b4199ea0ae9677fa3b087d1bbbe1d01b12938": {
        "variant": "reconstructed_linux_m2", "replay": True,
        "provenance": "reconstructed_linux_stage04 + PR209 M2/transform.py",
    },
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("source anchor absent or duplicated: " + old[:90])
    return text.replace(old, new, 1)

def transform(raw: bytes) -> tuple[bytes, dict]:
    pin = INPUTS.get(sha(raw))
    if pin is None:
        raise ValueError("unreviewed worker SHA256; no permissive override")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    old = text
    header = '''#include "lazy_draft_tail.hpp"
#ifndef HETEROSPEC_DEFER_DRAFT_TAIL
#error Bind HETEROSPEC_DEFER_DRAFT_TAIL explicitly to 0 or 1 in the frozen build
#endif
#if HETEROSPEC_DEFER_DRAFT_TAIL != 0 && HETEROSPEC_DEFER_DRAFT_TAIL != 1
#error HETEROSPEC_DEFER_DRAFT_TAIL must be 0 or 1
#endif
'''
    text = once(text, '#include "resident_context.hpp"', header + '#include "resident_context.hpp"')
    loop = 'for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);draft->decode({proposal},base+1+j,false,"PROPOSE");}'
    changed = 'for(int j=0;j<k;j++){int proposal=draft->sample(-1,"proposal-"+std::to_string(cycle)+"-"+std::to_string(j));proposals.push_back(proposal);if(!HETEROSPEC_DEFER_DRAFT_TAIL || j+1<k)draft->decode({proposal},base+1+j,false,"PROPOSE");}'
    text = once(text, loop, changed)
    text = once(text, 'bool done=commit(pending);',
                'bool done=commit(pending);\n    int deferred_tail_skipped=0,deferred_tail_recovered=0;')
    replay_guard = '!replay && ' if pin['replay'] else ''
    reconcile = '''
        if (''' + replay_guard + '''HETEROSPEC_DEFER_DRAFT_TAIL) {
            const auto outcome=heterospec_tail::complete_if_retained(base,k,keep,proposals.back(),
                [&](int token,int position){draft->decode({token},position,false,"PROPOSE");});
            if(outcome==heterospec_tail::Outcome::materialized)++deferred_tail_recovered;
            else ++deferred_tail_skipped;
        }
        '''
    # Retain the existing keep expression, target trim, replay guard and capture.
    text = once(text, 'int keep=base+1+accepted;target->trim(keep);',
                'int keep=base+1+accepted;' + reconcile + 'target->trim(keep);')
    text = once(text, 'r["request_seconds"]=since(request_start);',
                'r["draft_tail_policy"]=HETEROSPEC_DEFER_DRAFT_TAIL?"deferred-last-q1":"eager-control";\n'
                '    r["draft_tail_skipped"]=deferred_tail_skipped;r["draft_tail_recovered"]=deferred_tail_recovered;\n'
                '    r["request_seconds"]=since(request_start);')
    out = text.replace("\n", newline).encode("utf-8")
    delta = ''.join(difflib.unified_diff(old.splitlines(True), text.splitlines(True),
                                      fromfile='reviewed/worker.cpp', tofile='candidate/worker.cpp'))
    receipt = dict(schema='heterospec.deferred-draft-tail-source.v1', **pin,
                   input_worker_sha256=sha(raw), output_worker_sha256=sha(out),
                   header_sha256=sha((HERE/'lazy_draft_tail.hpp').read_bytes()),
                   generator_sha256=sha(Path(__file__).read_bytes()),
                   source_patch=delta, compile_modes=[0, 1],
                   patch_scope='frontend last draft proposal materialization only; original q1 call, phase label, keep and target decode retained',
                   numerical_source_edited=False, numerical_reference_edited=False,
                   newly_generated_source_not_native_build=True,
                   native_gpu_qualification='NOT_RUN', native_timing='NOT_RUN',
                   host_executed_worker_identity='not claimed; reconstructed variants identified explicitly')
    return out, receipt

def generate(source: Path, destination: Path) -> dict:
    if source.is_symlink() or not source.is_file():
        raise ValueError('regular explicit source file required')
    if destination.exists() or destination.is_symlink():
        raise ValueError('fresh destination required; preserve earlier attempt')
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise ValueError('fresh destination required; preserve earlier attempt')
    raw = source.read_bytes()
    out, receipt = transform(raw)  # Validate everything before creating output.
    destination.mkdir(parents=True)
    (destination/'worker.cpp').write_bytes(out)
    (destination/'lazy_draft_tail.hpp').write_bytes((HERE/'lazy_draft_tail.hpp').read_bytes())
    (destination/'LAZY_TAIL.patch').write_text(receipt.pop('source_patch'), encoding='utf-8')
    receipt['patch_sha256'] = sha((destination/'LAZY_TAIL.patch').read_bytes())
    (destination/'SOURCE_CANDIDATE.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    if source.read_bytes() != raw:
        raise RuntimeError('source changed concurrently; candidate may not be used')
    return receipt

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(generate(a.source, a.out), indent=2))
