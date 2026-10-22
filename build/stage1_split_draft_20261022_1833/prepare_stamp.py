"""Regenerate the old stamp prototype from today's formal renderer, then add split input."""
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1]
old=R/'build/stage1_span_probe_20261021_1110/probe.py'
body=old.read_text();stop="p=O/'stage1_render.v';p.write_text(s)"
assert body.count(stop)==1
namespace={'__file__':str(old),'__name__':'__private_transform__'}
exec(compile(body.split(stop,1)[0],str(old),'exec'),namespace)
s=namespace['s']


def edit(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)


def write(name,value):
    with (O/name).open('x',encoding='utf-8') as f:f.write(value)


probe=(O/'probe.py').read_text()
begin="s=(R/'rtl/color_regions/stage1_render.v').read_text()"
end="write('stage1_render.v',s)"
assert probe.count(begin)==probe.count(end)==1
transform=probe.split(begin,1)[1].split(end,1)[0]
exec(compile(transform,str(O/'probe.py'),'exec'),globals())
s=s.replace('Packed state RAM + two 8-pixel scanline buffers.','Packed state RAM + eight scanlines with serial stamps.')
write('stage1_render_stamp.v',s)
gate=(O/'gate.py').read_text()
gate=edit(gate,"for label in ('baseline','split','split_shared'):","for label in ('split_shared_stamp',):")
gate=edit(gate,"shared=label=='split_shared'","shared=label in ('split_shared','split_shared_stamp')")
gate=edit(gate,"elif n=='stage1_render' and split:p=O/'stage1_render.v'","elif n=='stage1_render' and split:p=O/'stage1_render_stamp.v'")
gate=edit(gate,"O/'gate_comparison.json'","O/'gate_stamp_comparison.json'")
write('gate_stamp.py',gate)
print('PRIVATE_STAMP_PREPARED; no formal RTL changes')
