"""One running reader: mid-picture changes take effect at frame commit only."""
import ast,hashlib,json,re
from refined_testlib import R
from test_native_zoom_core import execute,PIXEL

def main():
 source=R/'scripts/test_native_zoom_video.py'
 tree=ast.parse(source.read_text(encoding='utf-8'))
 expr=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tb' for t in n.targets))
 tb=ast.literal_eval(expr.func.value).replace('PIXEL',PIXEL)
 tb=tb.replace('integer z=0,rot=0,origin_x=0,origin_y=48;', '''integer z=0,rot=0,origin_x=0,origin_y=48;
integer edits=0,commits=0,active_zoom=0,active_rotate=0,active_x0=0,active_y0=48;
always @(posedge pc)if(rst && commit)begin
 commits=commits+1;active_zoom=z;active_rotate=rot;active_x0=origin_x;active_y0=origin_y;
end''')
 anchor='commit=py==0 && px==96;'
 assert anchor in tb
 tb=tb.replace(anchor,'''// Deliberately change every display input in the middle of active video.
if(py==400 && px==333)begin
 edits=edits+1;
 case(edits%6)
 1,4:begin z=1;origin_x=427;origin_y=304;end
 2,5:begin z=2;origin_x=640;origin_y=408;end
 default:begin z=0;origin_x=0;origin_y=48;end
 endcase
 rot=edits%6>=3;
end
'''+anchor)
 a=tb.index('if(oy<624)begin');b=tb.index('checked=checked+1;',a)
 region=tb[a:b]
 for old,new in [('z','active_zoom'),('rot','active_rotate'),('origin_x','active_x0'),('origin_y','active_y0')]:
  region=re.sub(r'\b'+old+r'\b',new,region)
 tb=tb[:a]+region+tb[b:]
 tb=tb.replace('checked=checked+1;', '''checked=checked+1;
  if(checked%798720==0)$display("NATIVE_TRANSITIONS_FRAME_PASS frame%0d zoom%0d rotate%0d",commits,active_zoom,active_rotate);''')
 tb=tb.replace('if(checked==798720)begin', '''if(checked==4792320)begin
  if(commits!=6 || edits!=6)$fatal(1,"transition coverage commits%0d edits%0d",commits,edits);''')
 tb=tb.replace('NATIVE_VIDEO_PASS zoom%0d rotate%0d pixels798720 actual75MHz/133MHz dense_detail_or_average DDR_bubbles/write_yield',
  'NATIVE_TRANSITIONS_PASS six_frames pixels4792320 mid_picture_changes/three_zooms/two_rotations/edge_ROI/frame_atomic actual75MHz/133MHz zoom%0d rotate%0d')
 tb=tb.replace('#20000000;', '#120000000;')
 modules=['native_line_reader.v','native_line_core.v','native_read_adapter.v','native_downsample2.v','stable_packer.v',
  'stable_model_lane.v','stable_filter4.v','refined_zoom_geometry.v','refined_reset_bridge.v',str(R/'rtl/04_tracking/target_mailbox.v')]
 output=execute('transitions',tb,modules,timeout=2400)
 receipt=output/'native_receipt.json';d=json.loads(receipt.read_text(encoding='utf-8'))
 d['producer_inputs'][source.relative_to(R).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
 receipt.write_text(json.dumps(d,indent=2),encoding='utf-8')

if __name__=='__main__':main()
