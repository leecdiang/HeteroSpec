import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("prepare_request", Path(__file__).parents[1] / "request/prepare_native.py")
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class SourcePreparationTests(unittest.TestCase):
    def test_source_anchors_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "anchor not unique"):
            prepare.transform("unrelated source")

    def test_repeat_transform_rejected(self):
        source = Path("D:/rtx211-q8-20261109/frontend-v2/worker.cpp")
        if not source.is_file():
            self.skipTest("historical source not installed on this machine")
        transformed = prepare.transform(source.read_text(encoding="utf8"))
        self.assertIn("cycle_k.at(size_t(cycle))", transformed)
        with self.assertRaisesRegex(ValueError, "anchor not unique"):
            prepare.transform(transformed)


if __name__ == "__main__":
    unittest.main()
