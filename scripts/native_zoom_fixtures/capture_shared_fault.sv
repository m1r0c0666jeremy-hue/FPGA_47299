`timescale 1ns/1ps
module tb;
integer meta_matches=0,raw_groups=0,filtered_groups=0;integer n;
reg clk=0;always #8.333 clk=~clk;reg rst=0,sof=0,valid=0,fault=0;
reg [95:0] rgb=0;reg [7:0] kval=50,session=1;
reg [31:0] fid=0;wire [31:0] out_id,dropped;wire ov;wire [767:0] meta;
function [63:0] model(input integer lo,hi);begin model=64'h8000000000000000|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
wire [127:0] models={model(195,255),model(345,30)};
wire [31:0] ref_id,ref_dropped;wire ref_valid;wire [767:0] ref_meta;
stage1_k_capture #(.V4(1)) dut(.I_clk(clk),.I_rst_n(rst),.I_sof(sof),.I_valid(valid),.I_fault(fault),
 .I_rgb(rgb),.I_pair(1'b0),.I_enable(1'b1),.I_session(session),.I_models(models),.I_revision(16'd1),
 .I_gains(24'h400400),.I_cal_status(8'd0),.I_cal_active(1'b0),.I_needs_cal(1'b0),.I_result_ready(1'b1),
 .O_frame_id(out_id),.O_valid(ov),.O_meta(meta),.O_dropped(dropped),.I_source_id(fid),.I_source_us(fid*17000),
 .I_now_us(fid*17000+100),.I_epoch(16'd7),.I_time_valid(1'b1),.I_model_state(2'd1),.I_quality(42'd0),.I_k_value(kval));
frozen_native_capture #(.V4(1)) reference(.I_clk(clk),.I_rst_n(rst),.I_sof(sof),.I_valid(valid),.I_fault(fault),
 .I_rgb(rgb),.I_pair(1'b0),.I_enable(1'b1),.I_session(session),.I_models(models),.I_revision(16'd1),
 .I_gains(24'h400400),.I_cal_status(8'd0),.I_cal_active(1'b0),.I_needs_cal(1'b0),.I_result_ready(1'b1),
 .O_frame_id(ref_id),.O_valid(ref_valid),.O_meta(ref_meta),.O_dropped(ref_dropped),.I_source_id(fid),.I_source_us(fid*17000),
 .I_now_us(fid*17000+100),.I_epoch(16'd7),.I_time_valid(1'b1),.I_model_state(2'd1),.I_quality(42'd0),.I_k_value(kval));
integer f,x,y,j,count=0,tips=0,tag_k,tag_s;
function [23:0] pixel(input integer x,y);begin
 pixel=24'h303030;
 if(x>=600 && x<=632 && y>=342 && y<=366)pixel=24'hc82020;
 if(x>=480 && x<=512 && y>=342 && y<=366)pixel=24'h2020c8;
end endfunction
initial begin repeat(8)@(negedge clk);rst=1;
for(f=1;f<=6;f=f+1)begin
 @(negedge clk);fid=f;
 case(f)4:begin kval=100;session=2;end 7:begin kval=0;session=3;end 8:begin kval=200;session=4;end endcase
 for(y=0;y<(f==4?50:720);y=y+1)for(x=0;x<1280;x=x+4)begin
  @(negedge clk);sof=x==0 && y==0;valid=1;fault=(f==2 && y==719 && x>=1260) || (f==5 && y>=360);
  for(j=0;j<4;j=j+1)rgb[95-j*24-:24]=pixel(x+j,y);
  if(f==3 && y==360 && x==0)begin kval=100;session=2;end
  @(negedge clk);valid=0;sof=0;
 end
 @(negedge clk);valid=0;sof=0;fault=0;repeat(2000)@(negedge clk);
end
@(negedge clk);fid=7;sof=1;@(negedge clk);sof=0;repeat(100000)@(negedge clk);
if(meta_matches!=6 || raw_groups<1000000 || filtered_groups<1000000)$fatal(1,"fault coverage meta%0d raw%0d filtered%0d",meta_matches,raw_groups,filtered_groups);
$display("NATIVE_SHARED_FAULT_PASS frames6 EOF_fault/midframe_fault/50row_short/recovery raw_filter_identity metadata_all768");$finish;
end
initial begin #200000000;$fatal(1,"K capture timeout");end
reg [767:0] expected_meta[0:15];reg [15:0] ready_meta=0;

reg raw_v=0,filtered_v=0;reg [7:0] old_mask=0;reg [15:0] old_filter=0;
reg [22:0] old_raw_identity=0,old_filtered_identity=0;
always @(posedge clk)if(!rst)begin raw_v<=0;filtered_v<=0;end
else begin
 raw_v<=reference.vp[3];old_mask<=reference.mask;
 old_raw_identity<={reference.tags[3],reference.xp[3],reference.yp[3]};
 filtered_v<=reference.fv;old_filter<={reference.fa,reference.fb};
 old_filtered_identity<={reference.ft,reference.fx,reference.fy};
end
always @(negedge clk)if(rst)begin
 if(dut.vp[4]!==raw_v)$fatal(1,"raw valid alignment");
 if(dut.vp[4])begin
  if(dut.mask!==old_mask || {dut.tags[4],dut.xp[4],dut.yp[4]}!==old_raw_identity)$fatal(1,"raw identity/mask");
  raw_groups=raw_groups+1;
 end
 if(dut.fv!==filtered_v)$fatal(1,"filter valid alignment");
 if(dut.fv)begin
  if({dut.fa,dut.fb}!==old_filter || {dut.ft,dut.fx,dut.fy}!==old_filtered_identity)$fatal(1,"filter identity/mask");
  filtered_groups=filtered_groups+1;
 end
 if(ref_valid)begin expected_meta[ref_meta[31:0]]=ref_meta;ready_meta[ref_meta[31:0]]=1;end
 if(ov && meta[31:0]<=6)begin
  n=meta[31:0];if(!ready_meta[n] || expected_meta[n]!==meta)$fatal(1,"full metadata mismatch id%0d",n);
  
 if((n==2 || n==4 || n==5) && meta[247])$fatal(1,"invalid frame accepted id%0d",n);
 if((n==1 || n==3 || n==6) && !meta[247])$fatal(1,"recovery frame incomplete id%0d",n);
 ready_meta[n]=0;meta_matches=meta_matches+1;
 $display("PRIVATE_FAULT_FRAME id%0d complete%b",n,meta[247]);$fflush();
 end
end
endmodule