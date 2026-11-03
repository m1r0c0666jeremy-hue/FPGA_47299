"""Bind camera regressions to the scripts and exact testbench that produced them.

This local adapter leaves the shared runner unchanged while inherited camera
prefixes receive the same immutable fixture/producer evidence as stage1 tests.
"""
from pathlib import Path
import hashlib
import json
import os
import traceback

from refined_testlib import R, run as original_run


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(name, source, modules, *args, **kwargs):
    modules = list(map(Path, modules))
    scripts = {R/'scripts/refined_testlib.py', Path(__file__).resolve()}
    for frame in traceback.extract_stack():
        path = Path(frame.filename).resolve()
        if path.is_relative_to(R/'scripts') and path.is_file():
            scripts.add(path)
    # The relay obtains three literal fixture strings from this producer.
    if R/'scripts/test_refined_camera_relay_integration.py' in scripts:
        scripts.add(R/'scripts/test_refined_camera.py')
    producers = {p.relative_to(R).as_posix(): digest(p) for p in scripts}
    fixtures = {p.relative_to(R).as_posix(): digest(p) for p in modules
                if p.is_relative_to(R/'scripts') and p.suffix != '.py'}
    # Path.write_text uses platform newline conversion in the unchanged runner.
    expected_tb = hashlib.sha256(source.replace('\n', os.linesep).encode('utf-8')).hexdigest()
    reports = R/'reports/refined/regression'
    earlier = set(reports.glob(name+'_*.json'))
    result = None
    try:
        result = original_run(name, source, modules, *args, **kwargs)
        return result
    finally:
        assert all(digest(R/path) == sha for path, sha in producers.items()), 'Camera producer changed during simulation'
        assert all(digest(R/path) == sha for path, sha in fixtures.items()), 'Camera fixture changed during simulation'
        records = [reports/(result.name+'.json')] if result is not None else list(set(reports.glob(name+'_*.json'))-earlier)
        for path in records:
            data = json.loads(path.read_text(encoding='utf-8'))
            tb = Path(data['output'])/'tb.sv'
            assert digest(tb) == expected_tb, 'Camera testbench differs from the executed source'
            data.setdefault('producer_inputs', {}).update(producers)
            data.setdefault('fixture_inputs', {}).update(fixtures)
            data['fixture_inputs'][tb.relative_to(R).as_posix()] = expected_tb
            path.write_text(json.dumps(data, indent=2), encoding='utf-8')
