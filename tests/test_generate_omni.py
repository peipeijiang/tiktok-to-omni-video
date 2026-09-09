import base64
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_omni  # noqa: E402


class ReferenceImageTests(unittest.TestCase):
    def test_local_storyboard_is_encoded_only_for_request(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "storyboard.png"
            image.write_bytes(b"reference-image")
            result = generate_omni.materialize_reference_images(["storyboard.png"], Path(directory))
            self.assertEqual(result, ["data:image/png;base64," + base64.b64encode(b"reference-image").decode("ascii")])

    def test_remote_reference_is_kept_as_documented_url(self):
        result = generate_omni.materialize_reference_images(["https://example.com/storyboard.png"], Path.cwd())
        self.assertEqual(result, ["https://example.com/storyboard.png"])

    def test_more_than_three_references_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_omni.materialize_reference_images(["https://example.com/1.png"] * 4, Path.cwd())


if __name__ == "__main__":
    unittest.main()
