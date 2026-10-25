"""Full regression for the restored 720p source-coordinate delivery contract."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]


def fingerprint():
    files = []
    for folder in ("rtl", "user_source", "ip", "scripts", "sim", "tests", "td_project"):
        files.extend(p for p in (R / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".log", ".logw"))
    return {p.relative_to(R).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    out = R / "reports/720p/regression" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out.mkdir(parents=True)
    before = fingerprint()
    (out / "inputs.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    jobs = [
        ("source_coordinates", ["scripts/test_720p_source_coordinates.py"]),
        ("geometry", ["scripts/test_refined_geometry.py"]),
        ("controls", ["scripts/test_refined_controls.py"]),
        ("elaboration", ["scripts/test_refined_compile.py"]),
        ("four_state_video", ["scripts/test_refined_video.py", "--case-range", "0", "2", "--workers", "2"]),
        ("video_80_and_faults", ["scripts/run_720p_native.py", "video", "--full", "--faults", "--workers", "3"]),
        ("joint_video", ["scripts/run_720p_native.py", "live", "--workers", "2"]),
        ("delivery_cli", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_720p_delivery.py", "-v"]),
    ]

    def execute(job):
        name, argv = job
        log = out / (name + ".log")
        started = time.monotonic()
        with log.open("w", encoding="utf-8") as stream:
            code = subprocess.run([sys.executable, "-X", "utf8", *argv], cwd=R, stdout=stream, stderr=subprocess.STDOUT).returncode
        result = dict(name=name, argv=argv, exit_code=code, seconds=round(time.monotonic() - started, 3), log=log.relative_to(R).as_posix(), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        print("720P_REGRESSION_JOB", name, "PASS" if code == 0 else "FAIL", result["seconds"], flush=True)
        return result

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(execute, job) for job in jobs]):
            results.append(future.result())
    unchanged = before == fingerprint()
    summary = dict(passed=unchanged and all(r["exit_code"] == 0 for r in results), inputs_unchanged=unchanged, jobs=results,
                   scope="new 720p contract suite; original 160 checks are separately re-audited historical evidence",
                   limits="Verilator long tests are two-state; Icarus runs retain four-state checks. Hardware pending.")
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("720P_REGRESSION_RESULT", out, summary["passed"], flush=True)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
