module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0;reg [95:0] rgb=0;wire [639:0] meta;wire [31:0] id,drop;wire ov;
function [63:0] model(input integer lo,hi);model=64'h8000000000000000|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);endfunction
wire [127:0] models={model(195,255),model(345,30)};
stable_capture dut(clk,rst,sof,v,1'b0,rgb,1'b0,1'b1,8'd7,models,16'd1,24'h400400,8'd0,1'b0,1'b0,1'b1,id,ov,meta,drop);
function [127:0] c(input integer x,y);begin c=0;c[120]=1;c[61:42]=256;c[72:62]=x;c[82:73]=y;c[41:0]={10'(y+8),10'(y-8),11'(x+8),11'(x-8)};end endfunction
integer x,y,l,n=0;reg [23:0] p;
initial begin repeat(4)@(negedge clk);rst=1;@(negedge clk);
// This is the legitimate identity state left by a previous manual session.
dut.tracker.have_id=1;dut.tracker.locked=1;dut.tracker.streak=3;dut.tracker.last_id=0;dut.tracker.last_command=3;dut.tracker.last_revision=0;
dut.tracker.olda=c(128,320);dut.tracker.oldb=c(240,320);
for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin @(negedge clk);sof=x==0 && y==0;v=1;
for(l=0;l<4;l=l+1)begin p=24'h282828;
if((((x+l>=80 && x+l<96)||(x+l>=144 && x+l<160)) && ((y>=272 && y<288)||(y>=336 && y<352))) || (x+l>=640 && x+l<643 && y>=320 && y<336))p=24'hb41414;
if(x+l>=520 && x+l<536 && y>=320 && y<336)p=24'h1428b4;
rgb[95-24*l-:24]=p;end end
@(negedge clk);sof=1;v=0;@(negedge clk);sof=0;
while(!ov && n<213000)begin @(negedge clk);n=n+1;end
if(!ov || meta[31:0]!=1 || !meta[247])$fatal(1,"capture result deadline");
if(meta[203:184]!=48 || meta[47:37]!=641 || meta[379:378]!=1)$fatal(1,"stale history still evicted new tool %h",meta);
$display("REFINED_HISTORY_PASS after full RGB frame, four old-location decoys plus new central thin marker, selected count%0d x%0d",meta[203:184],meta[47:37]);$finish;end 
reg candidate_hold_active=0;reg [1023:0] candidate_hold_value=0;integer candidate_hold_checks=0;
always @(posedge dut.clk)begin
 if(!dut.rst_n)candidate_hold_active<=0;
 else begin
  if(candidate_hold_active)begin
   if(dut.candidates!==candidate_hold_value || dut.gs)$fatal(1,"capture changed candidate bus before tracker done");
   candidate_hold_checks=candidate_hold_checks+1;
  end
  if(dut.ts)begin candidate_hold_active<=1;candidate_hold_value<=dut.candidates;end
  if(dut.td)candidate_hold_active<=0;
 end
end
final begin
 if(candidate_hold_checks==0)$fatal(1,"candidate hold contract not exercised");
 $display("CAPTURE_CANDIDATE_HOLD_PASS checked%0d source clocks",candidate_hold_checks);
end

endmodule