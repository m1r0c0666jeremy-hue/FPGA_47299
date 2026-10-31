"""Atomic delayed publication and arithmetic checks for targeted display repair."""
from refined_testlib import R,run
from pathlib import Path
import random

def viewport():
    rng=random.Random(10311957);rows=[];cx=640;cy=360;last=0
    for i in range(600):
        z=i%5;rot=(i//5)%2;replay=(i//10)%2
        w,h=((1280,624),(853,416),(640,312),(427,208),(320,156))[z]
        px,py=(rng.randrange(1280),rng.randrange(720))
        valid=i%17!=0;match=i%19!=0;fid=last if i%13==0 else i+1;cal=i%23==0
        meta=fid|(int(valid)<<32)|(px<<79)|(py<<90)|(1<<235)|(1<<244)|(1<<247)|(int(match)<<255)|(4<<413)|(7<<704)|(int(cal)<<565)|(1<<720)|(fid*17000<<640)
        packet=meta|(fid<<768)|(2<<800)|(1<<802)|(fid*17000<<803)|(7<<835)|(1<<851)
        point=(i*50<<23)|(replay<<22)|(int(valid)<<21)|(py<<11)|px
        if match and valid and (replay or fid!=last):
            def step(cur,dest):
                d=dest-cur
                return cur+max(-24,min(24,d)) if abs(d)>4 else cur
            cx=step(cx,px);cy=step(cy,py)
        cx=max(w//2,min(1280-w+w//2,cx));cy=max(h//2,min(720-h+h//2,cy))
        x0=cx-w//2;y0=cy-h//2
        if match and cal:cx=640;cy=360;x0=0;y0=48
        last=fid
        rows.append((packet,point,z,rot,cx,cy,x0,y0))
    stim='\n'.join(f"data=852'h{v[0]:0213x};point=39'd{v[1]};zoom=3'd{v[2]};rotate=1'b{v[3]};frame; if(cx!={v[4]} || cy!={v[5]} || x0!={v[6]} || y0!={v[7]})$fatal(1,\"oracle {i}\");" for i,v in enumerate(rows))
    tb=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,vs=0,de=0,snap=0,rotate=0;reg [1:0] abort=0;reg [851:0] data=0;reg [38:0] point=0;
reg [7:0] session=1;reg tracking=1,pair=0;reg [2:0] zoom=0;reg [1:0] mode=0;
wire commit,gcommit;wire [1:0] bank,gbank,om,gom;wire [31:0] id,gid,us,gus;wire [15:0] epoch,gepoch;
wire [10:0] cx,x0,gcx,gx0;wire [9:0] cy,y0,gcy,gy0;wire [2:0] oz,goz;wire [767:0] meta,gmeta;wire [38:0] shown,gshown;
wire show,gshow,op,gop,rot,grot,tv,gtv;
stage1_viewport #(.V4(1)) dut(clk,rst,vs,de,snap,data,tracking,1'b1,1'b0,1'b0,session,zoom,mode,pair,
commit,bank,id,cx,x0,cy,y0,oz,om,meta,show,op,,,,rotate,rot,us,epoch,tv,point,shown,abort);
reference_stage1_viewport #(.V4(1)) gold(clk,rst,vs,de,snap,data,tracking,1'b1,1'b0,1'b0,session,zoom,mode,pair,
gcommit,gbank,gid,gcx,gx0,gcy,gy0,goz,gom,gmeta,gshow,gop,,,,rotate,grot,gus,gepoch,gtv,point,gshown);
wire [939:0] pub={bank,id,cx,x0,cy,y0,oz,om,meta,show,op,rot,us,epoch,tv,shown};
wire [939:0] expected={gbank,gid,gcx,gx0,gcy,gy0,goz,gom,gmeta,gshow,gop,grot,gus,gepoch,gtv,gshown};
reg [939:0] held;integer n,cases=0,phase,kind;
task frame;begin
vs=1;@(negedge clk);vs=0;@(negedge clk);held=pub;snap=1;
@(negedge clk);snap=0;if(commit || pub!==held)$fatal(1,"published on capture");
for(n=0;n<3;n=n+1)begin @(negedge clk);if(commit || pub!==held)$fatal(1,"partial publication stage%0d",n);end
@(negedge clk);if(!commit || pub!==expected)$fatal(1,"atomic publication id%0d stage%0d",id,dut.phase);
@(negedge clk);if(commit)$fatal(1,"duplicate commit");cases=cases+1;
end endtask
initial begin repeat(4)@(negedge clk);rst=1;repeat(2)@(negedge clk);
STIMULUS
// Every abort phase, active-video onset, context change, and newer response.
for(kind=0;kind<7;kind=kind+1)for(phase=0;phase<4;phase=phase+1)begin
vs=1;@(negedge clk);vs=0;@(negedge clk);held=pub;snap=1;@(negedge clk);snap=0;
repeat(phase)@(negedge clk);
case(kind)0:abort=1;1:de=1;2:session=2;3:pair=1;4:tracking=0;5:mode=1;6:point[22]=!point[22];endcase
if(kind<2)begin
repeat(6)begin @(negedge clk);if(commit || pub!==held)$fatal(1,"fault/deadline leaked kind%0d phase%0d",kind,phase);end
end else begin
// Replacing the point source/configuration must keep the healthy image.
// No old payload can publish on the clock that detects the changed context.
repeat(4)begin @(negedge clk);if(commit || pub!==held)$fatal(1,"stale point published kind%0d phase%0d",kind,phase);end
@(negedge clk);
if(!commit || shown!==(point[22]?point:{16'd0,1'b0,data[32],data[99:79]}))$fatal(1,"context reprepare lost frame kind%0d phase%0d",kind,phase);
@(negedge clk);if(commit)$fatal(1,"context duplicate commit");
end
abort=0;de=0;session=1;pair=0;tracking=1;mode=0;
end
for(phase=0;phase<4;phase=phase+1)begin
vs=1;@(negedge clk);vs=0;@(negedge clk);snap=1;@(negedge clk);snap=0;repeat(phase)@(negedge clk);
data[31:0]=1000+phase;data[799:768]=1000+phase;snap=1;held=pub;
@(negedge clk);snap=0;repeat(3)begin @(negedge clk);if(commit || pub!==held)$fatal(1,"old snapshot leaked");end
@(negedge clk);if(!commit || id!=1000+phase)$fatal(1,"new snapshot not published");@(negedge clk);
end
// A stop event and route-state update on the publication edge must not emit
// the pre-stop virtual point. The new real source appears one clock later.
vs=1;@(negedge clk);vs=0;@(negedge clk);point[22]=1;snap=1;
@(negedge clk);snap=0;repeat(3)@(negedge clk);abort=2;
@(negedge clk);if(commit)$fatal(1,"stop edge emitted old replay point");abort=0;point[22]=0;
repeat(4)begin @(negedge clk);if(commit)$fatal(1,"source transition emitted stale point");end
@(negedge clk);if(!commit || shown[22] || shown[20:0]!==data[99:79])$fatal(1,"stop did not resume real image/point");@(negedge clk);
vs=1;@(negedge clk);vs=0;@(negedge clk);snap=1;@(negedge clk);snap=0;@(negedge clk);rst=0;
@(negedge clk);rst=1;repeat(8)@(negedge clk);if(commit || id!=0)$fatal(1,"old publication after reset");
$display("STAGE1_VIEWPORT_PIPELINE_PASS cases600 fault8 reprepare20 replace4 reset blanking-live-low atomic");$finish;end endmodule'''.replace('STIMULUS',stim)
    run('stage1_viewport_pipeline',tb,[R/'rtl/color_regions/stage1_regions.v',R/'rtl/color_regions/stage1_sequence.v',R/'rtl/color_regions/refined_zoom_geometry.v',R/'sim/stage1_viewport_before_retime.v'],timeout=60)

def overlay():
    # The independent rational oracle from the diagnosis is immutable; execute
    # its bench against the adopted formal RTL rather than its private copy.
    probe=R/'build/timing_diagnosis_20261031_1957'
    source=(probe/'tb.sv').read_text(encoding='utf-8').replace('PRIVATE_OVERLAY_PIPELINE_PASS','STAGE1_OVERLAY_PIPELINE_PASS')
    run('stage1_overlay_pipeline',source,[R/'rtl/color_regions/refined_overlay_geometry.v',probe/'reference.v'],timeout=60)

if __name__=='__main__':
    viewport();overlay()
