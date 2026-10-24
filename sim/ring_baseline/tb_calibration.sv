module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,v=0,pair=0,enter=0,sample=0,cancel=0,gain_changed=0;
reg [95:0] rgb=0;wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,frame_status;wire [23:0] fg;
stable_calibration dut(clk,rst,sof,v,rgb,pair,enter,sample,cancel,gain_changed,gr,gb,models,rev,active,needs,status,fp,fg,frame_status);
integer f,x,y,i,n;reg [127:0] saved,collision_model;reg [23:0] px;reg collide;
task frames;input integer kind;begin
for(f=0;f<8;f=f+1)for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin
@(negedge clk);sof=x==0 && y==0;v=1;
for(i=0;i<4;i=i+1)begin px=24'h647850;
if(kind==1 && x+i>=638 && x+i<641)px=24'hc81e14;
if(kind==2 && x+i>=638 && x+i<641)px=24'h142896;
if(kind==3)px=24'h101010;
if(kind>=4)px=24'h808080;
if(kind==5 && x+i>=638 && x+i<641)px=24'hc8c814;
if(kind==6 && x+i>=638 && x+i<641)px=24'hb414c8;
if(kind==7)px=24'hffffff;
if(kind==8)px=24'h20a0a0;
if(kind==9)begin px=24'h808080;if(x+i==640)px=24'hc81e14;end
if(kind==10)begin px=24'h808080;if(x+i>=632 && x+i<640)px=24'hc81e14;if(x+i>=640 && x+i<648)px=24'h1428c8;end
rgb[95-i*24-:24]=px;end end
@(negedge clk);sof=1;v=1;@(negedge clk);sof=0;v=0;
n=0;while((status[5] || dut.collecting || dut.waiting) && n<500000)begin
collide=dut.state==23 && dut.phase==3;collision_model=models;sof=collide;
@(negedge clk);if(collide && (models!==collision_model || frame_status[7:6]!=3))$fatal(1,"partial profile/status publication on coincident SOF");n=n+1;end
sof=0;
if(n>=500000)$fatal(1,"calibration timeout status%h state%0d",status,dut.state);
end endtask
initial begin repeat(3)@(negedge clk);rst=1;@(negedge clk);enter=1;@(negedge clk);enter=0;
if(!active)$fatal(1,"enter");sample=1;@(negedge clk);sample=0;frames(0);
if(status[7:6]!=2 || gr!=1228 || gb!=1536)$fatal(1,"white profile %h gains%0d/%0d",status,gr,gb);
sample=1;@(negedge clk);sample=0;frames(1);if(status[7:6]!=3)$fatal(1,"thin A sample failed %h",status);
sample=1;@(negedge clk);sample=0;frames(2);if(active || status[3:0]!=0)$fatal(1,"B sample failed %h",status);
sof=1;@(negedge clk);sof=0;@(negedge clk);saved=models;
if(models[44:37]<24 || models[36:29]<8 || !models[127] || !models[63])$fatal(1,"models invalid");
pair=1;sof=1;@(negedge clk);sof=0;@(negedge clk);if(gr!=1024 || gb!=1024)$fatal(1,"pair independence");
pair=0;sof=1;@(negedge clk);sof=0;@(negedge clk);if(models!==saved || gr!=1228)$fatal(1,"profile not saved");
enter=1;@(negedge clk);enter=0;sample=1;@(negedge clk);sample=0;frames(3);
if(status[3:0]!=2)$fatal(1,"dark white not rejected %h",status);
cancel=1;@(negedge clk);cancel=0;sof=1;@(negedge clk);sof=0;if(models!==saved)$fatal(1,"failed calibration replaced good profile");
// Inject the already-validated publication state to test exact cancellation
// priority, not to replace the full white/A/B/quantile acquisition above.
@(negedge clk);dut.state=23;dut.phase=3;dut.cp=0;dut.peak=240;dut.hlo=30;dut.hhi=30;
dut.mlow=200;dut.dlow=180;dut.slow=14;dut.staged_a=saved[63:0];dut.staged_r=512;dut.staged_b=2048;
cancel=1;sof=1;@(negedge clk);cancel=0;sof=0;@(negedge clk);
if(dut.profiles[0]!==saved || gr!=1228 || gb!=1536 || fg!={12'd1228,12'd1536} || frame_status[7:6]!=0)$fatal(1,"cancel/SOF at publication replaced complete profile or used staged gains");
// A different pair at RAW SOF cancels temporary gains and selects its entire
// formal group at that edge, not one frame of the previous pair's stage gains.
dut.phase=2;dut.cp=0;dut.staged_r=512;dut.staged_b=2048;pair=1;sof=1;
@(negedge clk);sof=0;@(negedge clk);
if(active || fg!={12'd1024,12'd1024} || frame_status[7:6]!=0 || !fp)$fatal(1,"pair/SOF stage-gain contamination");
pair=0;sof=1;@(negedge clk);sof=0;@(negedge clk);
gain_changed=1;@(negedge clk);gain_changed=0;sof=1;@(negedge clk);sof=0;@(negedge clk);if(!needs || gr!=1228 || models!==saved)$fatal(1,"gain invalidation discarded complete profile");
// Reject saturation, required gain outside 0.5..2 and material contamination.
enter=1;@(negedge clk);enter=0;sample=1;@(negedge clk);sample=0;frames(7);if(status[3:0]!=2)$fatal(1,"overexposed white accepted");
sample=1;@(negedge clk);sample=0;frames(8);if(status[3:0]!=3)$fatal(1,"gain outside limits accepted");
sample=1;@(negedge clk);sample=0;frames(4);if(status[7:6]!=2)$fatal(1,"neutral white failed");
sample=1;@(negedge clk);sample=0;frames(9);if(status[3:0]!=4)$fatal(1,"insufficient material accepted");
sample=1;@(negedge clk);sample=0;frames(10);if(status[3:0]!=4)$fatal(1,"mixed 50/50 colours accepted");
// Changing the pair cancels partial A/B data without overwriting either profile.
pair=1;@(negedge clk);if(active)$fatal(1,"pair switch did not cancel");
sof=1;@(negedge clk);sof=0;@(negedge clk);if(!needs)$fatal(1,"other profile invalidation lost");
enter=1;@(negedge clk);enter=0;sample=1;@(negedge clk);sample=0;frames(4);
sample=1;@(negedge clk);sample=0;frames(5);if(status[7:6]!=3)$fatal(1,"yellow learning failed");
sample=1;@(negedge clk);sample=0;frames(6);if(active || status[3:0]!=0)$fatal(1,"purple learning failed");
sof=1;@(negedge clk);sof=0;@(negedge clk);
if(needs || models[62:54]!=52 || models[53:45]!=69 || models[126:118]!=285 || models[117:109]!=302)$fatal(1,"yellow/purple quantile/expansion %h",models);
saved=models;n=rev;pair=0;repeat(6)@(negedge clk);if(models!==saved || rev!=n || !fp)$fatal(1,"parameters changed inside frame");
sof=1;@(negedge clk);sof=0;@(negedge clk);if(!needs || fp || rev==n)$fatal(1,"SOF version/pair switch");
rst=0;@(negedge clk);rst=1;@(negedge clk);if(needs || gr!=1024 || gb!=1024 || active || rev!=0)$fatal(1,"reset did not restore defaults");
enter=1;@(negedge clk);enter=0;sample=1;@(negedge clk);sample=0;sof=1;v=0;@(negedge clk);sof=0;
repeat(4)begin v=1;@(negedge clk);end v=0;sof=1;@(negedge clk);sof=0;@(negedge clk);
if(status[3:0]!=1)$fatal(1,"short calibration frame accepted");cancel=1;@(negedge clk);cancel=0;if(active)$fatal(1,"cancel partial sample");
$display("STABLE_CALIBRATION_PASS red/blue and yellow/purple white/A/B eight full frames, 3px band, quantiles, neutral background, independent profiles, cancel, dark/overexposure/gain/sample/mixed rejects, gain invalidate, SOF versions, reset");$finish;end endmodule