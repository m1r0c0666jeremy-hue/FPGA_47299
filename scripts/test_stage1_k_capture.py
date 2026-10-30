"""Real full-resolution classifier/banks with a mid-image K/session change."""
from refined_testlib import R,run


def main():
    source=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,valid=0;
reg [95:0] rgb=0;reg [7:0] kval=50,session=1;
reg [31:0] fid=0;wire [31:0] out_id,dropped;wire ov;wire [767:0] meta;
function [63:0] model(input integer lo,hi);begin model=64'h8000000000000000|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
wire [127:0] models={model(45,75),model(345,30)};
stage1_k_capture #(.V4(1)) dut(.I_clk(clk),.I_rst_n(rst),.I_sof(sof),.I_valid(valid),.I_fault(1'b0),
 .I_rgb(rgb),.I_pair(1'b0),.I_enable(1'b1),.I_session(session),.I_models(models),.I_revision(16'd1),
 .I_gains(24'h400400),.I_cal_status(8'd0),.I_cal_active(1'b0),.I_needs_cal(1'b0),.I_result_ready(1'b1),
 .O_frame_id(out_id),.O_valid(ov),.O_meta(meta),.O_dropped(dropped),.I_source_id(fid),.I_source_us(fid*17000),
 .I_now_us(fid*17000+100),.I_epoch(16'd7),.I_time_valid(1'b1),.I_model_state(2'd1),.I_quality(42'd0),.I_k_value(kval));
integer f,x,y,j,count=0,tips=0,tag_k,tag_s;
function [23:0] pixel(input integer x,y);begin
 pixel=24'h303030;
 if(x>=600 && x<=632 && y>=342 && y<=366)pixel=24'hc82020;
 if(x>=480 && x<=512 && y>=342 && y<=366)pixel=24'hc8c820;
end endfunction
always @(negedge clk)if(rst && ov && meta[31:0]<=10)begin
 count=count+1;
 case(meta[31:0])1,2,3:begin tag_k=50;tag_s=1;end
 4,5,6:begin tag_k=100;tag_s=2;end
 7:begin tag_k=0;tag_s=3;end
 default:begin tag_k=200;tag_s=4;end endcase
 if(!meta[249] || {meta[248],meta[230:224]}!==8'(tag_k) || meta[242:235]!==8'(tag_s) || !meta[247])
 $fatal(1,"K capture frozen identity f%0d K%0d/%0d session%0d/%0d",meta[31:0],{meta[248],meta[230:224]},tag_k,meta[242:235],tag_s);
 if(meta[47:37]!=616 || meta[57:48]!=354 || meta[68:58]!=496 || meta[78:69]!=354)
 $fatal(1,"analytical symmetric marker centroids f%0d A%0d/%0d B%0d/%0d",meta[31:0],meta[47:37],meta[57:48],meta[68:58],meta[78:69]);
 if(meta[32])begin
 tips=tips+1;
 if(meta[89:79]!==11'(616+tag_k*120/100) || meta[99:90]!==10'd354)
 $fatal(1,"capture K geometry f%0d K%0d tip%0d/%0d",meta[31:0],tag_k,meta[89:79],meta[99:90]);
 end
 if((meta[31:0]==3 || meta[31:0]==6 || meta[31:0]==10) && !meta[32])$fatal(1,"new K did not reacquire three frames");
 $display("K_CAPTURE_FRAME id%0d K%0d session%0d valid%b",meta[31:0],tag_k,tag_s,meta[32]);$fflush();
end
initial begin repeat(8)@(negedge clk);rst=1;
for(f=1;f<=10;f=f+1)begin
 @(negedge clk);fid=f;
 case(f)4:begin kval=100;session=2;end 7:begin kval=0;session=3;end 8:begin kval=200;session=4;end endcase
 for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin
  @(negedge clk);sof=x==0 && y==0;valid=1;
  for(j=0;j<4;j=j+1)rgb[95-j*24-:24]=pixel(x+j,y);
  if(f==3 && y==360 && x==0)begin kval=100;session=2;end
 end
 @(negedge clk);valid=0;sof=0;repeat(2000)@(negedge clk);
end
@(negedge clk);fid=11;sof=1;@(negedge clk);sof=0;repeat(100000)@(negedge clk);
if(count!=10 || tips!=3 || dropped!=0)$fatal(1,"K capture coverage count%0d tips%0d dropped%0d",count,tips,dropped);
$display("STAGE1_K_CAPTURE_PASS frames10 pixels9216000 mid-image-K/session/frozen-bank/three-frame-reacquisition");$finish;
end
initial begin #100000000;$fatal(1,"K capture timeout");end
endmodule'''
    names=('stage1_memory_video_out','stable_model_lane','stable_filter4','stable_grid','regions_divide')
    run('stage1_k_capture',source,[R/'rtl/color_regions'/f'{n}.v' for n in names],timeout=1800)


if __name__=='__main__':main()
