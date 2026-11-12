"""OASST provided-history tree census; no tokenizer, model or GPU execution.

All source rows remain in the denominator, including malformed records. Branches
are histories within a tree, never independent conversation roots. Text is not
stripped, normalized, truncated, ranked or filtered by language/quality.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json


def _string(value):
    return isinstance(value, str) and bool(value)


def build_corpus(messages):
    """Return raw messages, unique user turns, all leaf paths and denominators.

    A supported ``user_turns`` item has ``root``, zero-based ``turn_index``,
    ``chain_to_node`` message IDs, and ``messages`` in chat roles with verbatim
    content. Unsupported prompter rows are retained, without a generation input.
    ``root_to_leaf_paths`` keeps assistant-ending and dangling-user paths alike.
    """
    if not isinstance(messages, list):
        raise TypeError('messages must be the complete source split as a list')
    source = deepcopy(messages)
    id_counts = Counter(r.get('message_id') for r in source
                        if isinstance(r, dict) and _string(r.get('message_id')))
    unique = {r['message_id']: i for i, r in enumerate(source)
              if isinstance(r, dict) and _string(r.get('message_id'))
              and id_counts[r['message_id']] == 1}
    child_counts = Counter(r.get('parent_id') for r in source
                           if isinstance(r, dict) and _string(r.get('parent_id')))
    own = []
    for raw in source:
        issues = []
        if not isinstance(raw, dict):
            own.append(['RECORD_NOT_OBJECT'])
            continue
        mid = raw.get('message_id')
        if not _string(mid):
            issues.append('INVALID_MESSAGE_ID')
        elif id_counts[mid] != 1:
            issues.append('DUPLICATE_MESSAGE_ID')
        if 'parent_id' not in raw:
            issues.append('MISSING_PARENT_FIELD')
        elif raw['parent_id'] is not None and not _string(raw['parent_id']):
            issues.append('INVALID_PARENT_ID')
        if not _string(raw.get('message_tree_id')):
            issues.append('INVALID_DECLARED_ROOT')
        if raw.get('role') not in ('prompter', 'assistant'):
            issues.append('UNSUPPORTED_ROLE')
        if not isinstance(raw.get('text'), str):
            issues.append('INVALID_TEXT')
        own.append(issues)

    records = []
    for start, raw in enumerate(source):
        chain = []
        seen = set()
        issues = set()
        at = start
        complete = False
        while True:
            if at in seen:
                issues.add('PARENT_CYCLE')
                break
            seen.add(at)
            chain.append(at)
            issues.update(own[at])
            row = source[at]
            if not isinstance(row, dict) or 'parent_id' not in row:
                break
            parent = row['parent_id']
            if parent is None:
                complete = True
                break
            if not _string(parent):
                break
            if id_counts[parent] > 1:
                issues.add('AMBIGUOUS_PARENT_ID')
                break
            if parent not in unique:
                issues.add('PARENT_NOT_IN_SPLIT')
                break
            at = unique[parent]
        chain.reverse()
        actual_root = None
        if complete:
            first = source[chain[0]]
            actual_root = first.get('message_id')
            for depth, index in enumerate(chain):
                item = source[index]
                if item.get('role') != ('prompter' if depth % 2 == 0 else 'assistant'):
                    issues.add('ROLE_SEQUENCE_NOT_ALTERNATING_FROM_PROMPTER')
                if item.get('message_tree_id') != actual_root:
                    issues.add('DECLARED_ROOT_DOES_NOT_MATCH_ANCESTRY')
        else:
            issues.add('INCOMPLETE_ANCESTRY')
        obj = raw if isinstance(raw, dict) else {}
        records.append(dict(source_index=start, message_id=obj.get('message_id'),
                            parent_id=obj.get('parent_id'),
                            declared_root=obj.get('message_tree_id'),
                            root=actual_root if _string(actual_root) else None,
                            role=obj.get('role'), status='SUPPORTED' if not issues else 'UNSUPPORTED',
                            own_issues=own[start], issues=sorted(issues),
                            ancestry_complete=complete, chain_source_indices=chain,
                            chain_to_node=[source[i].get('message_id')
                                           if isinstance(source[i], dict) else None for i in chain],
                            not_dropped_from_denominator=True))

    turns = []
    for record in records:
        if record['role'] != 'prompter':
            continue
        row = dict(source_index=record['source_index'], message_id=record['message_id'],
                   root=record['root'], declared_root=record['declared_root'],
                   status=record['status'], issues=record['issues'],
                   chain_to_node=record['chain_to_node'], turn_index=None,
                   not_dropped_from_denominator=True)
        if record['status'] == 'SUPPORTED':
            chain = [source[i] for i in record['chain_source_indices']]
            row['turn_index'] = (len(chain) - 1) // 2
            row['messages'] = [dict(role='user' if r['role'] == 'prompter' else 'assistant',
                                    content=r['text']) for r in chain]
        turns.append(row)

    paths = []
    represented = set()
    for record in records:
        mid = record['message_id']
        # Count source child references even when the child's ID is ambiguous;
        # an invalid child must not silently turn its parent into a valid leaf.
        if _string(mid) and child_counts[mid]:
            continue
        chain = record['chain_source_indices']
        represented.update(chain)
        identity = dict(leaf_source_index=record['source_index'],
                        root=record['root'], message_ids=record['chain_to_node'])
        path_id = hashlib.sha256(json.dumps(identity, sort_keys=True,
                                            separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        paths.append(dict(path_id=path_id, root=record['root'],
                          declared_root=record['declared_root'],
                          leaf_message_id=mid, leaf_source_index=record['source_index'],
                          chain_source_indices=chain, message_ids=record['chain_to_node'],
                          user_message_ids=[source[i].get('message_id') for i in chain
                                            if isinstance(source[i], dict) and source[i].get('role') == 'prompter'],
                          terminal_role=record['role'], status=record['status'], issues=record['issues'],
                          complete_assistant_ending=(record['status'] == 'SUPPORTED'
                                                     and record['role'] == 'assistant'),
                          dangling_user_ending=(record['status'] == 'SUPPORTED'
                                                and record['role'] == 'prompter'),
                          independent_root_unit=False, not_dropped_from_denominator=True))

    # Declared roots with broken/missing root records remain visible. In corrupt
    # input a source row can also resolve to a different actual root; the two
    # namespaces are reported separately rather than pretending they partition.
    root_keys = sorted({_r for r in records for _r in (r['declared_root'], r['root']) if _string(_r)})
    roots = []
    for root in root_keys:
        members = [r for r in records if r['declared_root'] == root or r['root'] == root]
        rt = [r for r in turns if r['root'] == root and r['status'] == 'SUPPORTED']
        rp = [p for p in paths if p['root'] == root or p['declared_root'] == root]
        states = {r['status'] for r in members}
        roots.append(dict(root=root, source_message_rows=len(members),
                          root_message_source_indices=[r['source_index'] for r in members
                                                       if r['message_id'] == root and r['parent_id'] is None],
                          status=('SUPPORTED' if states == {'SUPPORTED'} else
                                  'UNSUPPORTED' if states == {'UNSUPPORTED'} else 'PARTIALLY_SUPPORTED'),
                          supported_unique_user_turns=len(rt), leaf_paths=len(rp),
                          supported_assistant_ending_paths=sum(p['complete_assistant_ending'] for p in rp),
                          supported_dangling_user_paths=sum(p['dangling_user_ending'] for p in rp)))
    supported_turns = [r for r in turns if r['status'] == 'SUPPORTED']
    return dict(schema='heterospec.N.provided_corpus.v1', history_origin='provided_conversation',
                selection='COMPLETE_BOUND_SPLIT_NO_LANGUAGE_QUALITY_RANK_LENGTH_OR_GEOMETRY_FILTER',
                raw_messages=source, message_records=records, user_turns=turns,
                root_to_leaf_paths=paths, roots=roots,
                pathless_source_indices=sorted(set(range(len(source))) - represented),
                counts=dict(source_message_rows=len(source),
                            supported_message_rows=sum(r['status'] == 'SUPPORTED' for r in records),
                            unsupported_message_rows=sum(r['status'] != 'SUPPORTED' for r in records),
                            declared_root_ids=len({r['declared_root'] for r in records if _string(r['declared_root'])}),
                            resolved_root_ids=len({r['root'] for r in records if _string(r['root'])}),
                            root_records=len(roots), user_source_rows=len(turns),
                            supported_unique_user_turns=len(supported_turns),
                            unsupported_user_source_rows=len(turns) - len(supported_turns),
                            leaf_paths=len(paths),
                            supported_assistant_ending_paths=sum(p['complete_assistant_ending'] for p in paths),
                            supported_dangling_user_paths=sum(p['dangling_user_ending'] for p in paths),
                            unsupported_leaf_paths=sum(p['status'] != 'SUPPORTED' for p in paths),
                            path_expanded_user_turn_occurrences=sum(len(p['user_message_ids']) for p in paths),
                            pathless_source_rows=len(set(range(len(source))) - represented)),
                scope='Provided histories only. No tokenizer/native head, capacity, output generation, numerical qualification or timing is inferred.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('messages_json')
    parser.add_argument('new_output')
    args = parser.parse_args()
    with open(args.messages_json) as stream:
        result = build_corpus(json.load(stream))
    with open(args.new_output, 'x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
