"""Fresh saved-oracle tests for split+shared-port+eight-row stamp rendering."""
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
    paths=[R/n for n in e['fixture_inputs'] if n.endswith('/tb.sv')];assert len(paths)==1
    return paths[0].read_text()


for helper in ('guards.py','coupled.py'):
    src=(O/helper).read_text().replace("O/'stage1_render.v'","O/'stage1_render_stamp.v'")
    src=src.replace('private_split_draft_guards','private_split_stamp_guards')
    src=src.replace('private_split_edit_render','private_split_stamp_edit_render')
    src=src.replace('coupled_validation.json','coupled_stamp_validation.json')
    exec(compile(src,str(O/helper),'exec'),{'__file__':str(O/helper),'__name__':'__private_stamp__'})
script=O/'probe.py'
section="source=bench('stage1_render_14_624')"+script.read_text().split("source=bench('stage1_render_14_624')",1)[1]
section=section.replace("O/'stage1_render.v'","O/'stage1_render_stamp.v'")
section=section.replace('private_split_draft_render','private_split_stamp_render').replace('private_split_draft_overlay','private_split_stamp_overlay')
section=section.replace('PRIVATE_SPLIT_DRAFT_REPLAY_PASS','PRIVATE_SPLIT_STAMP_REPLAY_PASS')
exec(compile(section,str(script),'exec'),globals())
