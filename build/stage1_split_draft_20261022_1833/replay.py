"""Replay saved render/RGB oracles after fixing the private harness declaration order."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
from audit_stage1 import sha


def edit(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)


proof=json.loads((R/'reports/stage1/software_current_20261022_1545.json').read_text())


def bench(name):
    e=proof['regression'][name]
    assert all(sha(R/n)==h for n,h in e['fixture_inputs'].items())
    paths=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')]
    assert len(paths)==1
    return paths[0].read_text()


script=O/'probe.py'
section="source=bench('stage1_render_14_624')"+script.read_text().split("source=bench('stage1_render_14_624')",1)[1]
exec(compile(section,str(script),'exec'))
