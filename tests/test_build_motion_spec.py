import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MotionSpecTests(unittest.TestCase):
    def test_tracks_produce_extension_and_alternation_report(self):
        with tempfile.TemporaryDirectory() as directory:
            tracks = Path(directory) / "tracks.csv"
            output = Path(directory) / "motion-spec.json"
            with tracks.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["frame", "point_id", "x", "y", "visible"])
                writer.writeheader()
                for frame, value in enumerate([0, 1, 3, 1, 0, 1, 3, 1, 0]):
                    writer.writerow({"frame": frame, "point_id": "left", "x": value, "y": 0, "visible": 1})
                    writer.writerow({"frame": frame, "point_id": "right", "x": 3 - value, "y": 0, "visible": 1})
            subprocess.run([sys.executable, str(ROOT / "scripts" / "build_motion_spec.py"), str(tracks), "--fps", "10", "--left", "left", "--right", "right", "--axis", "1", "0", "--out", str(output)], check=True)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertGreater(report["left"]["extensions_per_second"], 0)
            self.assertIn("alternation_ratio", report["alternation"])

    def test_comparison_reports_rate_delta(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            generated = Path(directory) / "generated.json"
            output = Path(directory) / "delta.json"
            template = {"left": {"extensions_per_second": 2, "median_interval_s": 0.5, "median_amplitude_px": 10, "median_peak_speed_px_s": 20}, "right": {"extensions_per_second": 2, "median_interval_s": 0.5, "median_amplitude_px": 10, "median_peak_speed_px_s": 20}, "alternation": {"alternation_ratio": 1}}
            source.write_text(json.dumps(template), encoding="utf-8")
            template["left"]["extensions_per_second"] = 1
            generated.write_text(json.dumps(template), encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "compare_motion_specs.py"), str(source), str(generated), "--out", str(output)], check=True)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["limbs"]["left"]["extensions_per_second"]["delta"], -1.0)


if __name__ == "__main__":
    unittest.main()
