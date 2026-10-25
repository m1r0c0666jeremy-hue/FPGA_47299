"""Public packaging CLI contract; assertions use independently frozen artifact IDs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

R = Path(__file__).resolve().parents[1]
BIT_SHA = "18fbffee70889073d44f3598029cce8bc5b0662d37f0911e138998315f83844a"


class DeliveryContract(unittest.TestCase):
    def test_negative_timing_evidence_is_rejected_without_candidate(self):
        with tempfile.TemporaryDirectory(prefix="720p_evidence_") as folder:
            checkout = Path(folder) / "checkout"
            (checkout / "scripts").mkdir(parents=True)
            shutil.copyfile(R / "scripts/package_720p.py", checkout / "scripts/package_720p.py")
            evidence = checkout / "reports/720p/baseline"
            shutil.copytree(R / "reports/720p/baseline", evidence)
            summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
            summary["slack_ns"]["HWNS"] = -0.002
            summary["timing_pass"] = False
            (evidence / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            out = Path(folder) / "candidate"
            result = subprocess.run([
                sys.executable, str(checkout / "scripts/package_720p.py"),
                "--source-root", str(R), "--bit", str(R / "build/baseline_720p/target_color_regions.bit"),
                "--output", str(out),
            ], cwd=R, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("EVIDENCE_MISMATCH", result.stderr)
            self.assertFalse(out.exists())

    def test_wrong_bit_is_rejected_without_candidate(self):
        with tempfile.TemporaryDirectory(prefix="720p_wrong_bit_") as folder:
            wrong = Path(folder) / "wrong.bit"
            wrong.write_bytes(b"not the audited 720p image")
            out = Path(folder) / "candidate"
            result = subprocess.run([
                sys.executable, str(R / "scripts/package_720p.py"),
                "--bit", str(wrong), "--output", str(out),
            ], cwd=R, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("BIT_MISMATCH", result.stderr)
            self.assertFalse(out.exists())

    def test_changed_compiled_input_is_rejected_without_candidate(self):
        with tempfile.TemporaryDirectory(prefix="720p_mutation_") as folder:
            root = Path(folder) / "source"
            inputs = json.loads((R / "reports/720p/baseline/inputs.json").read_text(encoding="utf-8"))
            for name in inputs:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(R / name, target)
            geometry = root / "rtl/color_regions/refined_zoom_geometry.v"
            geometry.write_bytes(geometry.read_bytes().replace(b"11'd1280", b"11'd1920"))
            out = Path(folder) / "candidate"
            result = subprocess.run([
                sys.executable, str(R / "scripts/package_720p.py"),
                "--source-root", str(root), "--output", str(out),
            ], cwd=R, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("COMPILED_INPUT_MISMATCH: rtl/color_regions/refined_zoom_geometry.v", result.stderr)
            self.assertFalse(out.exists())

    def test_unchanged_720p_is_delivered_with_historical_provenance(self):
        with tempfile.TemporaryDirectory(prefix="720p_delivery_") as folder:
            result = subprocess.run([
                sys.executable, str(R / "scripts/package_720p.py"),
                "--output", folder + "/candidate",
            ], cwd=R, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            out = Path(folder) / "candidate"
            manifest = json.loads((out / "delivery.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bit_sha256"], BIT_SHA)
            self.assertEqual(hashlib.sha256((out / "720p_source_coordinates_sram.bit").read_bytes()).hexdigest(), BIT_SHA)
            self.assertEqual(manifest["compiled_input_count"], 297)
            self.assertTrue(manifest["reused_historical_build"])
            self.assertEqual(manifest["hardware_status"], "pending")
            self.assertEqual(manifest["source_coordinate_space"], [1280, 720])
            with zipfile.ZipFile(out / "720p_same_source.zip") as archive:
                inputs = json.loads((R / "reports/720p/baseline/inputs.json").read_text(encoding="utf-8"))
                for name, expected in inputs.items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected, name)


if __name__ == "__main__":
    unittest.main()
