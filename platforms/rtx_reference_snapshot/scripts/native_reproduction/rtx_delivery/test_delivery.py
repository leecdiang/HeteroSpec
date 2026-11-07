"""CPU-only hostile/corrupt transport regression checks."""
import hashlib
import json
import pathlib
import tempfile
import unittest
import warnings
import zipfile
import delivery


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        # TemporaryDirectory's cleanup also needs extended paths on Windows.
        self.temp.name = str(delivery.filesystem_path(self.root))

    def archive(self, name='file.txt', payload=b'evidence', expected=None, extra=None):
        zpath = self.root / 'test.zip'
        manifest = {name: dict(bytes=len(payload), sha256=expected or hashlib.sha256(payload).hexdigest())}
        with zipfile.ZipFile(zpath, 'w') as z:
            z.writestr(name, payload)
            if extra:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore'); z.writestr(extra, b'not indexed')
            z.writestr('MEMBERS.json', json.dumps(manifest))
        return zpath

    def test_intact_archive_and_refuse_overwrite(self):
        path = self.archive(); out = self.root / 'fresh'
        delivery.extract(path, out)
        self.assertEqual(delivery.verify(out), 1)
        with self.assertRaises(ValueError): delivery.extract(path, out)

    def test_corrupted_member_rejected(self):
        path = self.archive(expected='0' * 64)
        with self.assertRaisesRegex(ValueError, 'SHA256'): delivery.extract(path, self.root / 'fresh')

    def test_deep_windows_source_path(self):
        name = '/'.join(['nested-source-directory'] * 14) + '/source.cpp'
        out = self.root / 'fresh'
        delivery.extract(self.archive(name=name), out)
        self.assertEqual(delivery.verify(out), 1)

    def test_mutated_extracted_member_rejected(self):
        out = self.root / 'fresh'; delivery.extract(self.archive(), out)
        (out / 'file.txt').write_bytes(b'changed!')
        with self.assertRaises(ValueError): delivery.verify(out)

    def test_extra_member_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unindexed'):
            delivery.extract(self.archive(extra='hidden.exe'), self.root / 'fresh')

    def test_duplicate_member_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            delivery.extract(self.archive(extra='file.txt'), self.root / 'fresh')

    def test_path_escape_rejected(self):
        for name in ('../outside', '/absolute', 'C:/absolute', 'a\\..\\outside'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                delivery.inside(self.root, name)

    def test_corrupt_part_never_creates_restore_output(self):
        part = self.root / 'part001'; part.write_bytes(b'incomplete')
        index = self.root / 'PARTS.json'
        delivery.save(index, {'parts': [{'path': part.name, 'bytes': 99, 'sha256': '0' * 64}]})
        out = self.root / 'fresh'
        with self.assertRaises(ValueError): delivery.restore(index, out)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
