"""Focused colour/FPS-only production regressions; legacy interfaces retained."""
from refined_testlib import R,run
from stage1_test_sources import OSD_ZERO_NAMED,EXTRA_OSD
import argparse,random

def stats():
    rng=random.Random(1030);now=0xffe00000;start=0;started=False;seen=None;count=0;fps=0;rows=[]
    for i in range(5000):
        now=(now+rng.choice((0,1,17000,33333,100000,1000000,2100000)))&0xffffffff
        image=(i//3)&0xffffffff;epoch=(i//1000)&0xffff
        if i<20:image=0xffffffff if i<10 else 0
        if i%31 in (20,21):image=max(0,image-2)
        sample=i%5!=0
        delta=((image-(seen[1] if seen else 0)+0x80000000)&0xffffffff)-0x80000000
        fresh=sample and (seen is None or epoch!=seen[0] or delta>0)
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
stage1_demo_fps dut(clk,rst,now_us,sample,image,epoch,fps);
initial begin repeat(3)@(negedge clk);rst=1;
ROWS
rst=0;@(negedge clk);if(fps)$fatal(1,"reset");
$display("STAGE1_DEMO_FPS_PASS vectors5000 wrap/duplicate/idle/replay-absence/window/reset");$finish;end endmodule'''.replace('ROWS','\n'.join(rows))
    run('stage1_demo_fps',src,[R/'rtl/color_regions/stage1_memory_video_out.v'],timeout=120)

def footer():
    ports=OSD_ZERO_NAMED.replace(".I_ui_mode(2'd0)",'.I_ui_mode(mode)').replace(".I_run_state(4'd0)",'.I_run_state(state)').replace(".I_teaching(80'd0)",'.I_teaching(teaching)')
    rest=r'''.I_clk(clk),.I_rst_n(rst),.I_vs(1'b0),.I_hs(1'b0),.I_de(de),
.I_rgb(24'd0),.I_meta(meta),.I_region_draft(168'd0),.I_x0(11'd0),.I_y0(10'd0),.I_zoom(3'd0),.I_mode(2'd0),.I_state(vs),
.I_tracking(tracking),.I_show(1'b0),.I_video_ok(video),.I_pair(1'b0),.I_detection_valid(detection),.I_sample_valid(1'b0),
.I_rotate(1'b0),.I_diag(2'd0),.I_image_id(32'd99),.I_geometry_commit(1'b0),.I_latency_valid(1'b1),.I_latency_us(32'd1234),.I_frame_age({24'd0,fps}),
.I_ddr_diag(128'd0),.I_pixel_diag(128'd0),.I_recovery(recovery),.I_camera(camera)'''
    src=r'''module tb;reg clk=0;always #5 clk=~clk;reg rst=0,de=0;
reg [1:0] mode=0;reg [3:0] state=0;reg video=1,tracking=1,detection=1;reg [2:0] vs=0;
reg [79:0] teaching=0;reg [767:0] meta=0;reg [17:0] camera=90;
reg [7:0] fps=60,fault=8'h32;reg [38:0] recovery=39'd0;reg lane=1;
stage1_osd #(.SHOW_FPS(1)) dut(PORTS REST);
stage1_osd #(.SHOW_FPS(0)) baseline(PORTS REST);
reg [359:0] chars=" 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()";
reg [47:0] word="FPS060";
reg [7:0] expected[0:127];integer c,j,k,cm,flags;reg cal,dead;
function [7:0] encode(input [7:0] a);integer n;begin encode=0;for(n=0;n<45;n=n+1)if(chars[(44-n)*8+:8]==a)encode=n;end endfunction
task fps_at(input integer row,first);integer n;begin
for(n=0;n<6;n=n+1)expected[row*64+first+n]=encode(word[(5-n)*8+:8]);end endtask
initial begin recovery[31:16]=16'h1234;repeat(3)@(negedge clk);rst=1;
for(c=0;c<144;c=c+1)begin
cm=c%4;flags=(c/4)%4;mode=cm;state=c%8;teaching=0;teaching[55:54]=flags;teaching[3:0]=c%9;
teaching[59:56]=c%3;teaching[7:4]=c%16;teaching[72]=1;teaching[71:64]=50;
meta=0;cal=c>=64;meta[567:565]=cal?(c%5)+1:0;meta[563:560]=c>=96?c%13:0;meta[255]=1;meta[415:413]=4;
dead=c%11==0;camera=dead?{1'b0,4'd9,4'd4,2'd3,7'd90}:18'd90;
fps=60;fault=8'h32;lane=1;
@(negedge clk);dut.x=0;dut.y=625;baseline.x=0;baseline.y=625;de=1;
@(negedge clk);de=0;repeat(1600)@(negedge clk);
if(!dut.footer_ready || !baseline.footer_ready)$fatal(1,"format deadline c%0d",c);
for(j=0;j<128;j=j+1)expected[j]=baseline.characters[j];
if(cal)fps_at(0,24);
else if(cm!=3)fps_at(1,13);
else if(flags==3)fps_at(1,21);
else if(flags==2)fps_at(1,24);
else fps_at(1,44);
if(dead)for(j=106;j<128;j=j+1)expected[j]=baseline.characters[j];
for(j=0;j<128;j=j+1)if(dut.characters[j]!==expected[j])$fatal(1,"footer preserve c%0d mode%0d flags%0d cal%0d char%0d got%0d expected%0d",c,cm,flags,cal,j,dut.characters[j],expected[j]);
dut.y=650;video=~video;tracking=~tracking;detection=~detection;state=state+1;vs=vs+1;fps=0;fault=0;lane=0;
repeat(8)@(negedge clk);if(dut.footer_current!==baseline.footer_current)$fatal(1,"changed legacy footer gate");
dut.y=680;mode=mode+1;repeat(8)@(negedge clk);if(dut.footer_current!==baseline.footer_current)$fatal(1,"changed legacy footer gate");
for(j=0;j<128;j=j+1)if(dut.characters[j]!==expected[j])$fatal(1,"snapshot changed c%0d",c);
end
rst=0;@(negedge clk);if(dut.footer_current)$fatal(1,"reset exposed old chars");
$display("STAGE1_DEMO_FPS_FOOTER_PASS cases144 glyphs18432 calibration/help/TEACH/IN/dwell/SEQ-OFF/fault-priority/legacy-gate/reset");$finish;end endmodule'''.replace('PORTS',ports).replace('REST',rest)
    modules=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]+EXTRA_OSD
    run('stage1_demo_fps_footer',src,modules,timeout=120)

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

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--part",choices=("all","stats","footer","colours"),default="all");a=p.parse_args()
 for name,fn in (("stats",stats),("footer",footer),("colours",colours)):
  if a.part in ("all",name):fn()
