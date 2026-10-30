"""Independent stable-release telemetry, hue identities and footer snapshots."""
from refined_testlib import R,run
from stage1_test_sources import OSD_ZERO_NAMED,EXTRA_OSD
import argparse,random

def stats():
    rng=random.Random(1030);now=0xffe00000;start=0;started=False;seen=None;count=0;fps=0;rows=[]
    for i in range(5000):
        now=(now+rng.choice((0,1,17000,33333,100000,1000000,2100000)))&0xffffffff
        image=(i//3)&0xffffffff;epoch=(i//1000)&0xffff
        if i<20:image=0xffffffff if i<10 else 0
        sample=i%5!=0;fresh=sample and seen!=(epoch,image)
        if not started:started=True;start=now;count=int(fresh)
        elif ((now-start)&0xffffffff)>=1000000:
            fps=0 if ((now-start)&0xffffffff)>=2000000 else count
            start=now;count=int(fresh)
        elif fresh:count=min(255,count+1)
        if fresh:seen=(epoch,image)
        rows.append(f"now_us=32'h{now:08x};sample={int(sample)};image=32'h{image:08x};epoch=16'h{epoch:04x};@(negedge clk);if(fps!==8'd{fps})$fatal(1,\"fps vector {i} got%0d\",fps);")
    src='''module tb;reg clk=0;always #5 clk=~clk;reg rst=0;
reg [31:0] now_us=0,image=0;reg [15:0] epoch=0;reg sample=0,lane=0;
reg [17:0] camera=0;reg [127:0] dd=0,pd=0;reg [38:0] recovery=0;wire [7:0] fps,fault;wire ls;
stage1_runtime_stats dut(clk,rst,now_us,sample,image,epoch,camera,dd,pd,recovery,lane,fps,fault,ls);
initial begin repeat(3)@(negedge clk);rst=1;
ROWS
sample=0;camera[12:9]=5;@(negedge clk);if(fault!==8'h15)$fatal(1,"camera code");
camera=0;repeat(4)@(negedge clk);if(fault!==8'h15)$fatal(1,"fault lost after recovery");
dd[87:76]=1;dd[75:72]=2;@(negedge clk);if(fault!==8'h32)$fatal(1,"DDR code");
pd[19:4]=1;pd[3:0]=1;@(negedge clk);if(fault!==8'h41)$fatal(1,"pixel code");
recovery[31:16]=1;recovery[37:34]=4;@(negedge clk);if(fault!==8'h24)$fatal(1,"recovery code");
lane=1;repeat(4)@(negedge clk);if(!ls || fault!==8'h24)$fatal(1,"lane should be diagnostic only");
rst=0;@(negedge clk);if(fps || fault || ls)$fatal(1,"reset");
$display("STAGE1_RUNTIME_PASS vectors5000 wrap/duplicate/idle/replay-absence/window/diagnostic/reset");$finish;end endmodule'''.replace('ROWS','\n'.join(rows))
    run('stage1_runtime',src,[R/'rtl/color_regions/stage1_memory_video_out.v'],timeout=120)

def footer():
    ports=OSD_ZERO_NAMED.replace(".I_ui_mode(2'd0)",'.I_ui_mode(mode)').replace(".I_run_state(4'd0)",'.I_run_state(state)')
    src=r'''module tb;reg clk=0;always #5 clk=~clk;reg rst=0,de=0;
reg [1:0] mode=0;reg [3:0] state=0;reg video=1,tracking=1,detection=1;reg [2:0] vs=0;
reg [7:0] fps=60,fault=8'h32;reg [38:0] recovery=39'd0;reg lane=1;
stage1_osd #(.RUNTIME_INFO(1)) dut(PORTS .I_clk(clk),.I_rst_n(rst),.I_vs(1'b0),.I_hs(1'b0),.I_de(de),
.I_rgb(24'd0),.I_meta(768'd0),.I_region_draft(168'd0),.I_x0(11'd0),.I_y0(10'd0),.I_zoom(3'd0),.I_mode(2'd0),.I_state(vs),
.I_tracking(tracking),.I_show(1'b0),.I_video_ok(video),.I_pair(1'b0),.I_detection_valid(detection),.I_sample_valid(1'b0),
.I_rotate(1'b0),.I_diag(2'd0),.I_image_id(32'd99),.I_geometry_commit(1'b0),.I_latency_valid(1'b1),.I_latency_us(32'd1234),.I_frame_age(32'd9),
.I_ddr_diag(128'd0),.I_pixel_diag(128'd0),.I_recovery(recovery),.I_camera(18'd90),.I_fps(fps),.I_fault(fault),.I_lane_seen(lane));
reg [359:0] chars=" 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()";reg [167:0] want=" FPS 060 E32 R1234 L1";
integer m,j;reg [7:0] ascii;
task snap;begin @(negedge clk);dut.x=0;dut.y=625;de=1;@(negedge clk);de=0;repeat(1600)@(negedge clk);if(!dut.footer_ready)$fatal(1,"format deadline");end endtask
initial begin recovery[31:16]=16'h1234;repeat(3)@(negedge clk);rst=1;
for(m=0;m<4;m=m+1)begin mode=m;fps=60;fault=8'h32;lane=1;recovery[31:16]=16'h1234;snap;
for(j=0;j<21;j=j+1)begin ascii=chars[(44-dut.characters[80+j])*8+:8];if(ascii!==want[(20-j)*8+:8])$fatal(1,"runtime glyph mode%0d col%0d got%c",m,j,ascii);end
// Scan two different footer rows while every old live qualifier changes.
dut.y=650;video=~video;tracking=~tracking;detection=~detection;state=state+1;vs=vs+1;fps=0;fault=0;lane=0;
repeat(8)@(negedge clk);if(!dut.footer_current)$fatal(1,"live state erased first footer row");
dut.y=680;mode=mode+1;repeat(8)@(negedge clk);if(!dut.footer_current)$fatal(1,"live state erased second footer row");
for(j=0;j<21;j=j+1)begin ascii=chars[(44-dut.characters[80+j])*8+:8];if(ascii!==want[(20-j)*8+:8])$fatal(1,"snapshot changed");end
snap;if(dut.characters[85]!==1 || dut.characters[86]!==1 || dut.characters[87]!==1)$fatal(1,"next snapshot did not update FPS");
end
rst=0;@(negedge clk);if(dut.footer_current)$fatal(1,"reset exposed old chars");
$display("STAGE1_RUNTIME_FOOTER_PASS modes4 rows650/680 faults/FPS/next-frame/reset");$finish;end endmodule'''.replace('PORTS',ports)
    modules=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]+EXTRA_OSD
    run('stage1_runtime_footer',src,modules,timeout=120)

def colours():
    src=r'''module tb;reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,pair=0;wire [127:0] models;
stable_calibration dut(.clk(clk),.rst_n(rst),.sof(sof),.valid(1'b0),.rgb(96'd0),.pair(pair),.enter(1'b0),.sample(1'b0),.cancel(1'b0),.gain_changed(1'b0),.models(models));
integer p,h,phase;reg expected;reg [127:0] held;
initial begin repeat(3)@(negedge clk);rst=1;repeat(3)@(negedge clk);
for(p=0;p<2;p=p+1)begin pair=p;sof=1;@(negedge clk);sof=0;@(negedge clk);
if(models[62:54]!=(p?195:345) || models[53:45]!=(p?255:30) || models[126:118]!=(p?255:45) || models[117:109]!=(p?330:75))$fatal(1,"default A/B hue mapping");
held=models;
for(phase=3;phase<=4;phase=phase+1)for(h=0;h<360;h=h+1)begin
force dut.cp=p[0];force dut.phase=phase[2:0];force dut.hue=h[8:0];#1;
expected=p?(phase==3?(h>=165 && h<270):(h>=255 && h<345)):(phase==3?(h>=330 || h<45):(h>=30 && h<90));
if(dut.family!==expected)$fatal(1,"family pair%0d phase%0d hue%0d",p,phase,h);
release dut.cp;release dut.phase;release dut.hue;end
dut.phase=0;end
$display("STAGE1_RY_BP_COLOURS_PASS defaults4 families1440 existing-thresholds/A-forward");$finish;end endmodule'''
    run('stage1_ry_bp_colours',src,[R/'rtl/color_regions/stable_calibration.v',R/'rtl/color_regions/regions_divide.v'],timeout=120)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--part',choices=['stats','footer','colours','all'],default='all');a=p.parse_args()
    for n,f in [('stats',stats),('footer',footer),('colours',colours)]:
        if a.part in ('all',n):f()
