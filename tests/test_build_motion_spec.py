import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MotionSpecTests(unittest.TestCase):
    def write_tracks(self, path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["frame", "point_id", "x", "y", "visible"])
            writer.writeheader()
            for frame, value in enumerate([0, 1, 3, 1, 0, 1, 3, 1, 0]):
                writer.writerow({"frame": frame, "point_id": "left", "x": value, "y": 0, "visible": 1})
                writer.writerow({"frame": frame, "point_id": "right", "x": 3 - value, "y": 0, "visible": 1})

    def test_tracks_produce_extension_and_alternation_report(self):
        with tempfile.TemporaryDirectory() as directory:
            tracks = Path(directory) / "tracks.csv"
            output = Path(directory) / "motion-spec.json"
            self.write_tracks(tracks)
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

    def test_impact_batch_compilation_and_scoring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracks = root / "tracks.csv"
            motion = root / "motion.json"
            impact = root / "impact.json"
            jobs = root / "jobs.json"
            score_input = root / "candidates.json"
            scores = root / "scores.json"
            self.write_tracks(tracks)
            subprocess.run([sys.executable, str(ROOT / "scripts" / "build_motion_spec.py"), str(tracks), "--fps", "10", "--left", "left", "--right", "right", "--axis", "1", "0", "--out", str(motion)], check=True)
            subprocess.run([sys.executable, str(ROOT / "scripts" / "build_impact_spec.py"), str(tracks), str(motion), "--fps", "10", "--left", "left", "--right", "right", "--subject", "A cat", "--target", "a cushion", "--anchor", "the shoulders", "--target-point", "3", "0", "--contact-threshold-px", "1", "--out", str(impact)], check=True)
            batch = [{"source_id": "clip-1", "base_prompt": "10-second vertical 9:16 phone video.", "subject": "A cat", "action": "paw strikes", "motion_spec": "motion.json", "impact_spec": "impact.json", "framing_lock": "the cat stays in a tight left-facing crop.", "reference_images": ["storyboard.png"]}]
            (root / "batch.json").write_text(json.dumps(batch), encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "compile_omni_batch.py"), str(root / "batch.json"), "--out", str(jobs)], check=True)
            compiled = json.loads(jobs.read_text(encoding="utf-8"))
            self.assertEqual([job["metadata"]["profile"] for job in compiled], ["cadence", "impact", "framing"])
            self.assertIn("Impact lock", compiled[1]["prompt"])
            self.assertEqual(compiled[0]["reference_images"], ["storyboard.png"])
            score_input.write_text(json.dumps([{"candidate_id": "clip-1-impact", "profile": "impact", "source_motion_spec": "motion.json", "generated_motion_spec": "motion.json", "source_impact_spec": "impact.json", "generated_impact_spec": "impact.json"}]), encoding="utf-8")
            subprocess.run([sys.executable, str(ROOT / "scripts" / "score_impact_batch.py"), str(score_input), "--out", str(scores)], check=True)
            ranked = json.loads(scores.read_text(encoding="utf-8"))["ranked"]
            self.assertEqual(ranked[0]["overall_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
