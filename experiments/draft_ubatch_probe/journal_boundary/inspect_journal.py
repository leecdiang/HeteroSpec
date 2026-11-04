#!/usr/bin/env python3
"""Read-only interpretation of PR183 native-fixture journals, never restoration."""
import argparse, collections, hashlib, json
from pathlib import Path

def require(ok, message):
    if not ok: raise ValueError(message)

def token(x):
    require(type(x) is int and x >= 0, 'invalid token ID')
    return x

def derive(record, prompt):
    require(record.get('stop_is_synthetic_eog_predicate') is True and type(record.get('target_ubatch')) is int and record['target_ubatch'] == 1, 'unsupported fixture semantics')
    prompt = [token(x) for x in prompt]
    require(bool(prompt), 'explicit nonempty prompt required')
    ids = [token(x) for x in record['ids']]
    require(bool(ids), 'empty endpoint')
    cap, stop = record['cap'], record['stop_after_output_index']
    require(type(cap) is int and cap > 0 and type(stop) is int and stop >= 0, 'invalid termination metadata')
    require(len(ids) == (min(cap, stop) if stop else cap), 'endpoint length disagrees with cap/stop')
    cycles = record['cycles']
    require(isinstance(cycles, list), 'cycles must be a list')
    prefix, emitted, seed = list(prompt), [ids[0]], ids[0]
    last = 'initial'
    boundary_row = None
    last_is_boundary = None
    for index, c in enumerate(cycles):
        final = index == len(cycles)-1
        props = [token(x) for x in c['proposals']]
        decisions = [token(x) for x in c['decisions']]
        require(len(props) == 3 and len(decisions) == 4, 'only fixed k=3 fixture supported')
        a = c['accepted']; last = c['last']
        require(type(a) is int and 0 <= a <= 3, 'invalid accepted count')
        require(type(c['base']) is int and type(c['keep']) is int, 'frontier positions must be integers')
        require(c['base'] == len(prefix), 'base does not follow committed prefix')
        require(all(props[j] == decisions[j] for j in range(a)), 'accepted proposal disagrees with decision')
        generated = props[:a]
        if last == 'accepted':
            require(final and a > 0, 'accepted-only cycle must terminate with accepted output')
        elif last == 'correction':
            require(a < 3 and decisions[a] != props[a], 'invalid correction branch')
            generated += [decisions[a]]
        elif last == 'bonus':
            require(a == 3, 'bonus requires all proposals accepted')
            generated += [decisions[3]]
        else:
            raise ValueError('unknown terminal branch')
        emitted += generated
        prefix += [seed] + props[:a]
        require(c['keep'] == len(prefix), 'keep disagrees with committed prefix')
        require(c['pending'] is None if final else c['pending'] == generated[-1], 'loop pending field disagrees with source control flow')
        if not final: seed = token(c['pending'])
        boundary_row = a
        last_is_boundary = a == 3
    require(emitted == ids, 'journal decisions do not reconstruct endpoint')
    require(bool(cycles) == (len(ids) > 1), 'missing or spurious cycles')
    consumed_last = last == 'accepted'
    expected = prompt + (ids if consumed_last else ids[:-1])
    require(prefix == expected, 'endpoint-derived frontier disagrees with cycles')
    # This is a logical source interpretation only. The journal contains no KV
    # bytes or boundary full-logit vector and does not certify the live context.
    return {
        'terminal_branch': last,
        'interpretation': 'LOGICAL_SOURCE_DERIVATION_ONLY',
        'loop_pending_null_means': 'no next iteration, not absence of an emitted unconsumed token',
        'emitted_token_count': len(ids),
        'logical_committed_prefix_ids': expected,
        'logical_committed_end_exclusive': len(expected),
        'last_emitted_token': {'id': ids[-1], 'output_index': len(ids)-1,
                               'logical_position': len(prompt)+len(ids)-1,
                               'included_in_logical_committed_prefix': consumed_last},
        'emitted_unconsumed_suffix': [] if consumed_last else [{'id': ids[-1], 'logical_position': len(expected)}],
        'boundary_logit_source': {
            'phase': 'verify' if cycles else 'prefill',
            'source_row_index': boundary_row,
            'default_last_verify_row_is_this_row': last_is_boundary,
            'full_vector_in_journal': False,
            'trim_repairs_or_restores_logits': False,
        },
        'recovery': {'status': 'UNPROVEN', 'checkpoint_present_in_this_journal': False,
                     'resume_authorized': False,
                     'missing': ['verified boundary full logits', 'KV state bytes and provenance',
                                 'native positions and pending capsule', 'validated restore/continuation procedure']},
    }

def inspect(raw, prompt):
    records=[]; started=None; counts=collections.Counter()
    for number,line in enumerate(raw.splitlines(),1):
        require(bool(line.strip()), 'blank journal line')
        obj=json.loads(line)
        if obj.get('status')=='STARTED':
            require(started is None, 'nested attempt start');started=obj
        elif obj.get('status')=='COMPLETED':
            require(started is not None, 'completion without start')
            r=obj['result']
            for lhs,rhs in [('ubatch','draft_ubatch'),('reject','forced_reject_index'),('cap','cap'),('stop','stop_after_output_index')]:
                require(started[lhs]==r[rhs], 'attempt identity mismatch')
            annotation=derive(r,prompt);counts[annotation['terminal_branch']]+=1
            records.append({'completed_line':number,'original_line_sha256':hashlib.sha256(line).hexdigest(),'annotation':annotation})
            started=None
        else: raise ValueError('unsupported journal event')
    return {'schema':'pr183-journal-boundary-sidecar-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'prompt_ids_supplied_explicitly':prompt,'prompt_binding_status':'CALLER_SUPPLIED_NOT_VERIFIED_BY_JOURNAL','old_records_modified':False,
            'scope':'PR183 native fixture only; not a PR151 worker checkpoint adapter',
            'completed_attempts':len(records),'terminal_branch_counts':dict(counts),
            'incomplete_attempt':started,'recovery_status':'UNPROVEN','records':records}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--journal',type=Path,required=True)
    p.add_argument('--prompt-ids',required=True,help='Explicit comma-separated IDs; not inferred from keep/base')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prompt=[int(x) for x in a.prompt_ids.split(',')]
    result=inspect(a.journal.read_bytes(),prompt)
    with a.output.open('x',encoding='utf-8',newline='\n') as f: json.dump(result,f,indent=2);f.write('\n')
if __name__=='__main__': main()
