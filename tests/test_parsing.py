import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


main_mod = load_module(REPO_ROOT / "main.py", "mediainfo_main")
branded_mod = load_module(REPO_ROOT / "Branded" / "main.hokan-sho.py", "mediainfo_branded")


class MediaInfoParsingTests(unittest.TestCase):
    def test_resolution_handles_missing_digits(self):
        lines = ["Width : N/A\n", "Height : Unknown\n"]
        self.assertEqual(main_mod._resolution(lines), (None, None))
        self.assertEqual(branded_mod._resolution(lines), (None, None))

    def test_resolution_parses_when_digits_exist(self):
        lines = ["Width : 1 920 pixels\n", "Height : 1 080 pixels\n"]
        self.assertEqual(main_mod._resolution(lines), (1920, 1080))
        self.assertEqual(branded_mod._resolution(lines), (1920, 1080))

    def test_clean_kbps_normalizes_kbps(self):
        line = "Bit rate : 384 kb/s"
        self.assertEqual(main_mod._clean_kbps(line), "384 kbps")
        self.assertEqual(branded_mod._clean_kbps(line), "384 kbps")

    def test_extract_info_does_not_crash_on_malformed_resolution(self):
        sample = (
            "Video\n"
            "Width : N/A\n"
            "Height : N/A\n"
            "Bit rate : 2 000 kb/s\n"
            "\n"
            "Audio\n"
            "Language :\n"
            "Language : English\n"
            "Format : AAC\n"
            "Channel(s) : 2 channels\n"
            "Sampling rate : 48.0 kHz\n"
            "Bit rate : 192 kb/s\n"
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "Example.MediaInfo.txt"
            path.write_text(sample, encoding="utf-8")
            info = main_mod.extract_info(str(path))
            self.assertIn("Quality", info)
            self.assertEqual(info["Quality"], "N/A")


if __name__ == "__main__":
    unittest.main()
