"""Native DDR reader to all four display pages, with both calibrated pairs."""
import argparse,hashlib,json,ast
from refined_testlib import R,literal_fixture
from test_native_zoom_core import execute

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--zoom',type=int,choices=(0,1,2),required=True);a=ap.parse_args()
 source=R/'scripts/test_native_zoom_video.py'
 tree=ast.parse(source.read_text(encoding='utf-8'))
 expr=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='tb' for t in n.targets))
 tb=ast.literal_eval(expr.func.value)
 pixel=r'''
function [23:0] pixel(input integer x,y);begin
case((x/64)%5)0:pixel=24'hff2020;1:pixel=24'h2020ff;2:pixel=24'hffff20;
3:pixel=24'ha020ff;default:pixel=24'h808080;endcase end endfunction
function [23:0] average(input integer x,y);begin average=pixel(x,y);end endfunction
'''
 tb=tb.replace('PIXEL',pixel)
 def model(lo,hi):return (1<<63)|(lo<<54)|(hi<<45)|(32<<37)|(16<<29)
 models=[model(330,30)|(model(210,270)<<64),model(45,75)|(model(255,330)<<64)]
 tb=tb.replace('integer z=0,rot=0,origin_x=0,origin_y=48;',
  'integer z=0,rot=0,parg=0,origin_x=0,origin_y=48;reg [127:0] models=0;')
 tb=tb.replace(".I_models(128'h80000000000000008000000000000000)",'.I_models(models)')
 tb=tb.replace('if($value$plusargs("ROTATE=%d",rot))begin end',
  'if($value$plusargs("ROTATE=%d",rot))begin end\nif($value$plusargs("PAIR=%d",parg))begin end\n'+
  f"models=parg?128'h{models[1]:032x}:128'h{models[0]:032x};")
 extra=r'''
wire [3:0] page_de;wire [23:0] page_rgb[0:3];genvar mode;
generate for(mode=0;mode<4;mode=mode+1)begin:pages
stable_preprocess page(pc,rst,2'(mode),1'(parg),ovs,ohs,ode,rgb,mask,,,page_de[mode],page_rgb[mode],);
end endgenerate
function [1:0] color_mask(input [23:0] p);begin
if(parg==0)color_mask=p==24'hff2020 ? 1 : p==24'h2020ff ? 2 : 0;
else color_mask=p==24'hffff20 ? 1 : p==24'ha020ff ? 2 : 0;
end endfunction
function [23:0] page_expected(input [23:0] p,input integer m,input [1:0] hit);
integer gray,dark;begin gray=(p[23:16]+2*p[15:8]+p[7:0]+2)/4;dark=gray/4;
case(m)0:page_expected=p;
1:page_expected=hit[0]?(parg?24'hffff40:24'hff6060):hit[1]?(parg?24'he080ff:24'h6090ff):{8'(dark),8'(dark),8'(dark)};
2:page_expected={8'(gray),8'(gray),8'(gray)};3:page_expected=hit!=0?24'hffffff:0;
endcase end endfunction
reg prior_de=0;reg [23:0] prior_rgb;reg [1:0] prior_mask;integer page_count=0,input_count=0,md;
always @(posedge pc)begin #1;
 if(rst && prior_de)begin
  for(md=0;md<4;md=md+1)begin
   if(!page_de[md] || page_rgb[md]!==page_expected(prior_rgb,md,prior_mask))
    $fatal(1,"native page z%0d r%0d pair%0d mode%0d got%h",z,rot,parg,md,page_rgb[md]);
   page_count=page_count+1;
  end
 end
 prior_de=ode && input_count<20480;prior_rgb=rgb;prior_mask=color_mask(rgb);
 if(ode)input_count=input_count+1;
end
'''
 tb=tb.replace('integer ox=0,oy=0,checked=0,sx,sy;', 'integer ox=0,oy=0,checked=0,sx,sy;\n'+extra)
 tb=tb.replace('checked=checked+1;','if(mask!==color_mask(expected))$fatal(1,"native mask z%0d r%0d pair%0d xy%0d/%0d got%b expected%b",z,rot,parg,ox,oy,mask,color_mask(expected));\n  checked=checked+1;')
 tb=tb.replace('if(checked==798720)begin','if(checked==20482)begin\n  if(page_count!=81920)$fatal(1,"page coverage %0d",page_count);')
 tb=tb.replace('NATIVE_VIDEO_PASS zoom%0d rotate%0d pixels798720 actual75MHz/133MHz dense_detail_or_average DDR_bubbles/write_yield',
  'NATIVE_COLOR_MODES_PASS zoom%0d rotate%0d both_masks four_pages pixels20480 actual75MHz/133MHz')
 modules=['native_line_reader.v','native_line_core.v','native_read_adapter.v','native_downsample2.v','stable_packer.v',
  'stable_model_lane.v','stable_filter4.v','stable_preprocess.v','refined_zoom_geometry.v','refined_reset_bridge.v',str(R/'rtl/04_tracking/target_mailbox.v')]
 for pair in (0,1):
  for rot in (0,1):
   out=execute(f'colors_{a.zoom}_{pair}_{rot}',tb,modules,args=[f'+ZOOM={a.zoom}',f'+ROTATE={rot}',f'+PAIR={pair}'],timeout=600)
   receipt=out/'native_receipt.json';d=json.loads(receipt.read_text(encoding='utf-8'))
   d['producer_inputs'][source.relative_to(R).as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
   receipt.write_text(json.dumps(d,indent=2),encoding='utf-8')
if __name__=='__main__':main()
