"""Profile quality/state are frame-frozen and share publication/cancel priority."""
from refined_testlib import R
from sc500_test_evidence import run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,sof=0,pair=0,cancel=0,changed=0;
wire [11:0] gr,gb;wire [127:0] models;wire [15:0] rev;wire active,needs,fp;wire [7:0] status,fs;wire [23:0] gains;
wire [1:0] model_state;wire [41:0] quality;
stable_calibration dut(clk,rst,sof,1'b0,96'd0,pair,1'b0,1'b0,cancel,changed,gr,gb,models,rev,active,needs,status,fp,gains,fs,model_state,quality);
task frame;begin @(negedge clk);sof=1;@(negedge clk);sof=0;@(negedge clk);end endtask
reg [127:0] saved;reg [41:0] qsaved;reg [15:0] version;
initial begin repeat(4)@(negedge clk);rst=1;frame;if(model_state!=0 || quality!=0)$fatal(1,"default state");saved=models;
@(negedge clk);dut.phase=4;dut.cp=0;dut.state=35;dut.best_valid=1;dut.best_model=saved[127:64];dut.staged_a=saved[63:0];dut.staged_quality={9'd24,12'd1000,9'd32,12'd1200};
@(negedge clk);if(model_state!=0 || models!==saved)$fatal(1,"publication changed frame state");frame;
if(model_state!=1 || quality!={9'd24,12'd1000,9'd32,12'd1200})$fatal(1,"learned quality not published");qsaved=quality;version=rev;
@(negedge clk);dut.phase=4;dut.cp=0;dut.state=35;dut.best_valid=1;dut.best_model=saved[127:64];dut.staged_a=saved[63:0];dut.staged_quality=42'd1;cancel=1;sof=1;
@(negedge clk);cancel=0;sof=0;frame;if(quality!==qsaved || model_state!=1 || dut.profile_quality[0]!==qsaved)$fatal(1,"cancel replaced quality");
changed=1;@(negedge clk);changed=0;if(model_state!=1)$fatal(1,"model state changed inside frame");frame;
if(model_state!=2 || !needs || models!==saved || quality!==qsaved)$fatal(1,"required state discarded complete profile");
pair=1;frame;if(model_state!=2 || quality!=0)$fatal(1,"other pair invalidation/quality");pair=0;frame;if(model_state!=2 || quality!==qsaved)$fatal(1,"pair quality lost");
rst=0;@(negedge clk);rst=1;frame;if(model_state!=0 || quality!=0 || needs)$fatal(1,"reset defaults");
$display("REFINED_MODEL_STATE_PASS defaults/learned/needs-update, counts/minimum, atomic publication/cancel, pair independence and frame freeze");$finish;end endmodule'''
run('model_state_quality',src,[R/'rtl/color_regions/stable_calibration.v',R/'rtl/color_regions/regions_divide.v'])
