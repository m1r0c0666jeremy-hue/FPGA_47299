"""Package the restored 720p project with explicit historical bit provenance."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
import zipfile

R = Path(__file__).resolve().parents[1]
BASELINE = R / "reports/720p/baseline"
COMPILED_COMMIT = "09cccd89e34f2508aeae342a4b1e6819a920d889"
BIT_SHA = "18fbffee70889073d44f3598029cce8bc5b0662d37f0911e138998315f83844a"
EVIDENCE_SHA = "9ec0eb66550b2c67db809c6ce4e5cc69258b0187d89d891bf0f99f6469ead9d3"
PINNED_REPORTS = {
    "inputs.json": "970d0781b9c66096ac5a2aba9fd3206a82d29649a49c4075dc7185154084a265",
    "summary.json": "6e74256e12b517ae6872b5e2654a36fef094c25f9fe1f887bee29a5af576097b",
    "delivery.json": "190013e50df8201bc0d4a65ef2750790bd1c1e0d94d7e5c2e4b27f056d091ee2",
    "target_color_regions_phy.ts": "8cb2b405009e30cf846ebba4026fdf9e7a991fc42f3c19c149921b45e3839e89",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_historical(evidence):
    """Recheck pinned provenance, not branch names or stale absolute machine paths."""
    def require(condition, reason):
        if not condition:
            raise ValueError("EVIDENCE_MISMATCH: " + reason)

    for name, expected in PINNED_REPORTS.items():
        require((BASELINE / name).is_file() and sha((BASELINE / name).read_bytes()) == expected, name)
    summary = json.loads((BASELINE / "summary.json").read_text(encoding="utf-8"))
    delivery = json.loads((BASELINE / "delivery.json").read_text(encoding="utf-8"))
    inputs = json.loads((BASELINE / "inputs.json").read_text(encoding="utf-8"))
    require(summary == delivery["build"]["summary"], "physical summary disagrees with delivery")
    require(summary["head"] == COMPILED_COMMIT and summary["exit_code"] == 0 and summary["stage"] == "full", "unsuccessful build")
    require(summary["resource_pass"] and summary["timing_pass"] and summary["inputs_unchanged"], "physical gate failed")
    require(min(summary["slack_ns"].values()) >= 0, "negative timing")
    require(evidence.is_file() and sha(evidence.read_bytes()) == EVIDENCE_SHA, "historical source/evidence archive")
    with zipfile.ZipFile(evidence) as archive:
        manifest = json.loads(archive.read("SOURCE_MANIFEST.json"))
        require(len(manifest) == 1835, "historical member count")
        for name, expected in manifest.items():
            require(sha(archive.read(name)) == expected, name)
        normalize = lambda mapping: {n.replace("\\", "/"): value for n, value in mapping.items()}
        for name, item in delivery["regression"].items():
            raw = archive.read(item["record"])
            log = archive.read(str(Path(item["record"]).with_suffix(".log")).replace("\\", "/"))
            require(sha(raw) == item["record_sha256"] and sha(log) == item["log_sha256"], name)
            record = json.loads(raw)
            success = record.get("exit_code") == 0 or ("exit_code" not in record and record.get("passed") is True)
            require(success and not record.get("expected_failure") and b"PASS" in log, name)
            deps = normalize(record["inputs"])
            require(deps == normalize(item["inputs"]), name + " dependency list")
            for dependency, expected in deps.items():
                require(sha(archive.read(dependency)) == expected, dependency)
        require(len(delivery["regression"]) == 160, "historical regression count")
        route = delivery["build"]["attempt"]
        proof = summary["checkpoint_provenance"]
        for attempt in (route, proof["parent"]):
            before = json.loads(archive.read(attempt + "/inputs.json"))
            after = json.loads(archive.read(attempt + "/inputs_after.json"))
            require(before == after == inputs, attempt + " frozen inputs")
            for name, expected in inputs.items():
                require(sha(archive.read(attempt + "/compiled_source/" + name)) == expected, name)
        for suffix, key in (("summary.json", "parent_summary_sha256"), ("source_context.json", "parent_context_sha256"), ("inputs.json", "parent_inputs_sha256")):
            require(sha(archive.read(proof["parent"] + "/" + suffix)) == proof[key], suffix)
        require(sha(archive.read(proof["parent"] + "/" + proof["checkpoint_name"])) == proof["checkpoint_sha256"], "placed checkpoint")
        for name, expected in summary["route_checkpoints"].items():
            require(sha(archive.read(route + "/" + name)) == expected, name)
    return dict(historical_regression_count=160, historical_archive_members_verified=1835, compiled_input_count=len(inputs),
                resources=summary["resources"], slack_ns=summary["slack_ns"], historical_evidence_sha256=EVIDENCE_SHA)


def source_files(root):
    files = {}
    for folder in ("rtl", "user_source", "ip", "assets", "scripts", "sim", "docs", "tests", ".scratch", "reports/720p"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".logw"):
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    for name in ("README.md", ".gitattributes", ".gitignore", "tools/iverilog/manifest.json", "tools/native_sim/manifest.json"):
        if (root / name).is_file():
            files[name] = (root / name).read_bytes()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=R / "build" / ("delivery_720p_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")))
    parser.add_argument("--source-root", type=Path, default=R)
    parser.add_argument("--bit", type=Path, default=R / "build/baseline_720p/target_color_regions.bit")
    parser.add_argument("--historical-evidence", type=Path, default=R / "build/baseline_720p/osd_memory_same_source.zip")
    args = parser.parse_args()
    evidence_audit = verify_historical(args.historical_evidence)
    inputs = json.loads((BASELINE / "inputs.json").read_text(encoding="utf-8"))
    files = source_files(args.source_root)
    # The exact TD project is itself one of the compiled inputs.
    for name in inputs:
        path = args.source_root / name
        if not path.is_file():
            raise ValueError("COMPILED_INPUT_MISMATCH: " + name)
        files[name] = path.read_bytes()
        if sha(files[name]) != inputs[name]:
            raise ValueError("COMPILED_INPUT_MISMATCH: " + name)
    bit = args.bit.read_bytes()
    if sha(bit) != BIT_SHA:
        raise ValueError("BIT_MISMATCH: requires the audited historical 720p SRAM image")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "720p_source_coordinates_sram.bit").write_bytes(bit)
    shutil.copyfile(args.historical_evidence, args.output / "historical_build_evidence.zip")
    archive = args.output / "720p_same_source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(files.items()):
            output.writestr(name, data)
    summary = json.loads((BASELINE / "summary.json").read_text(encoding="utf-8"))
    manifest = dict(
        created_local=datetime.datetime.now().isoformat(), reused_historical_build=True,
        compiled_source_commit=COMPILED_COMMIT, compiled_input_count=len(inputs),
        compiled_inputs=inputs, bit="720p_source_coordinates_sram.bit", bit_sha256=sha(bit),
        source_zip=archive.name, source_zip_sha256=sha(archive.read_bytes()),
        source_files={name: sha(data) for name, data in sorted(files.items())},
        source_coordinate_space=[1280, 720], video_area=[1280, 624], footer_height=96,
        pixel_clock_mhz=75, refresh_hz=75_000_000 / (1650 * 750),
        hardware_status="pending", historical_physical_summary=summary,
        historical_evidence="historical_build_evidence.zip", historical_evidence_audit=evidence_audit,
    )
    (args.output / "delivery.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("720P_DELIVERY_PASS", args.output)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(3)
