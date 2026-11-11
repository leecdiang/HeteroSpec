import tempfile
import unittest
from pathlib import Path
from deliver import split_archive, assemble_archive


class SplitDeliveryTests(unittest.TestCase):
    def test_ordered_split_preserves_every_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'RAW_EVIDENCE.zip'
            source.write_bytes(bytes(range(256))*37)
            manifest=split_archive(source,1000)
            self.assertEqual(len(manifest['parts']),10)
            restored=assemble_archive(root,manifest,root/'restored.zip')
            self.assertEqual(source.read_bytes(),restored.read_bytes())

    def test_corrupt_part_is_rejected_before_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'RAW_EVIDENCE.zip';source.write_bytes(b'abcdef')
            manifest=split_archive(source,3)
            (root/manifest['parts'][1]['name']).write_bytes(b'abx')
            with self.assertRaises(AssertionError):assemble_archive(root,manifest,root/'restored.zip')

    def test_unsafe_part_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'RAW_EVIDENCE.zip';source.write_bytes(b'abcdef')
            manifest=split_archive(source,3);manifest['parts'][0]['name']='../other'
            with self.assertRaises(AssertionError):assemble_archive(root,manifest,root/'restored.zip')


if __name__=='__main__':unittest.main()
