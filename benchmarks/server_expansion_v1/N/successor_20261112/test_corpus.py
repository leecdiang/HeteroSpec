"""Meaningful zero-forward denominator/ancestry fixtures; no model imports."""
import copy
import unittest
from corpus import build_corpus


def message(mid, parent, role, text='text', root='r', **extra):
    return dict(message_id=mid, parent_id=parent, message_tree_id=root,
                role=role, text=text, **extra)


class CorpusTests(unittest.TestCase):
    def test_shared_branch_prefix_is_not_a_new_root_or_turn(self):
        rows = [message('r', None, 'prompter'), message('a', 'r', 'assistant'),
                message('u', 'a', 'prompter'), message('a1', 'u', 'assistant'),
                message('a2', 'u', 'assistant')]
        r = build_corpus(rows)
        self.assertEqual(r['counts']['resolved_root_ids'], 1)
        self.assertEqual(r['counts']['supported_unique_user_turns'], 2)
        self.assertEqual(r['counts']['supported_assistant_ending_paths'], 2)
        self.assertEqual(r['counts']['path_expanded_user_turn_occurrences'], 4)
        self.assertEqual(r['user_turns'][1]['chain_to_node'], ['r', 'a', 'u'])
        self.assertEqual(r['user_turns'][1]['turn_index'], 1)
        self.assertTrue(all(not p['independent_root_unit'] for p in r['root_to_leaf_paths']))

    def test_dangling_user_and_whitespace_are_retained(self):
        rows = [message('r', None, 'prompter', '  \n', lang='xx', rank=99),
                message('a', 'r', 'assistant', ''), message('u', 'a', 'prompter', '\tquestion\n')]
        original = copy.deepcopy(rows)
        r = build_corpus(rows)
        self.assertEqual(rows, original)
        self.assertEqual(r['raw_messages'], original)
        self.assertEqual(r['counts']['supported_dangling_user_paths'], 1)
        self.assertEqual(r['user_turns'][1]['messages'], [
            dict(role='user', content='  \n'), dict(role='assistant', content=''),
            dict(role='user', content='\tquestion\n')])

    def test_orphan_invalidates_descendants_without_dropping_rows(self):
        rows = [message('a', 'missing', 'assistant'), message('u', 'a', 'prompter')]
        r = build_corpus(rows)
        self.assertEqual(r['counts']['source_message_rows'], 2)
        self.assertEqual(r['counts']['unsupported_message_rows'], 2)
        self.assertEqual(r['counts']['unsupported_user_source_rows'], 1)
        self.assertIn('PARENT_NOT_IN_SPLIT', r['user_turns'][0]['issues'])
        self.assertNotIn('messages', r['user_turns'][0])
        self.assertEqual(r['counts']['unsupported_leaf_paths'], 1)

    def test_cycle_with_no_leaf_is_visible_in_denominator(self):
        rows = [message('a', 'b', 'assistant'), message('b', 'a', 'prompter')]
        r = build_corpus(rows)
        self.assertEqual(r['counts']['unsupported_message_rows'], 2)
        self.assertEqual(r['counts']['leaf_paths'], 0)
        self.assertEqual(r['counts']['pathless_source_rows'], 2)
        self.assertTrue(all('PARENT_CYCLE' in x['issues'] for x in r['message_records']))

    def test_duplicate_never_silently_chooses_first_parent(self):
        rows = [message('r', None, 'prompter'), message('a', 'r', 'assistant'),
                message('a', 'r', 'assistant', 'other'), message('u', 'a', 'prompter')]
        r = build_corpus(rows)
        self.assertEqual(r['counts']['supported_message_rows'], 1)
        self.assertEqual(r['counts']['unsupported_message_rows'], 3)
        self.assertIn('AMBIGUOUS_PARENT_ID', r['user_turns'][1]['issues'])

    def test_bad_role_text_and_declared_root_propagate(self):
        rows = [message('r', None, 'prompter'), message('a', 'r', 'prompter', None, root='wrong'),
                message('u', 'a', 'prompter')]
        r = build_corpus(rows)
        issues = r['user_turns'][-1]['issues']
        self.assertIn('INVALID_TEXT', issues)
        self.assertIn('ROLE_SEQUENCE_NOT_ALTERNATING_FROM_PROMPTER', issues)
        self.assertIn('DECLARED_ROOT_DOES_NOT_MATCH_ANCESTRY', issues)
        self.assertEqual(r['counts']['declared_root_ids'], 2)

    def test_malformed_record_and_missing_fields_remain(self):
        r = build_corpus([None, {}, message('r', None, 'assistant')])
        self.assertEqual(r['counts']['source_message_rows'], 3)
        self.assertEqual(r['counts']['unsupported_message_rows'], 3)
        self.assertEqual(len(r['root_to_leaf_paths']), 3)
        self.assertIn('MISSING_PARENT_FIELD', r['message_records'][1]['issues'])

    def test_deep_chain_has_no_python_recursion_dependency(self):
        rows = [message('r', None, 'prompter')]
        for i in range(1, 1100):
            rows.append(message(str(i), 'r' if i == 1 else str(i - 1),
                                'assistant' if i % 2 else 'prompter'))
        r = build_corpus(rows)
        self.assertEqual(r['counts']['unsupported_message_rows'], 0)
        self.assertEqual(r['counts']['supported_assistant_ending_paths'], 1)
        self.assertEqual(r['user_turns'][-1]['turn_index'], 549)


if __name__ == '__main__':
    unittest.main()
