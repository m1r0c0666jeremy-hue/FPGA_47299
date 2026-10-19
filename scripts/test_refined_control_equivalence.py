"""Per-clock equivalence including minute-long holds and counter saturation."""
from refined_testlib import R,run
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [2:0] keys=7;reg [1:0] sw=1;reg [7:0] cal=0;reg pause=0,ack=0;
wire [21:0] a,b;wire ack_a=a[0],ack_b=b[0];
stable_controls #(.CYCLES_PER_MS(1),.DEBOUNCE_MS(1),.CHORD_WINDOW_MS(WINDOW)) original(clk,rst,keys,sw,ack,cal,a[0],a[1],a[4:2],a[5],a[6],a[14:7],a[15],a[16],a[17],a[18],a[19],a[20],a[22:21],pause);
refined_controls #(.CYCLES_PER_MS(1),.DEBOUNCE_MS(1),.CHORD_WINDOW_MS(WINDOW)) candidate(clk,rst,keys,sw,ack,cal,b[0],b[1],b[4:2],b[5],b[6],b[14:7],b[15],b[16],b[17],b[18],b[19],b[20],b[22:21],pause);
integer cycle=0,gains=0,zooms=0;reg [2:0] oldzoom=0;reg oldgain=0;
always @(negedge clk)if(rst)begin
if(a[20:0]!==b[20:0] || b[22:21]!=0 || original.held!==candidate.held || original.chord!==candidate.chord || original.cal_ui!==candidate.cal_ui)$fatal(1,"control equivalence cycle%0d held%0d repeat%0d a%h b%h",cycle,original.held,candidate.repeat_age,a,b);
if(a[0]!=oldgain)gains=gains+1;if(a[4:2]!=oldzoom)zooms=zooms+1;
oldgain=a[0];oldzoom=a[4:2];ack=a[0];cycle=cycle+1;end
task waitms(input integer n);begin repeat(n)@(posedge clk);#1;end endtask
task press(input integer mask,n);begin keys=~mask;waitms(n);keys=7;waitms(12);end endtask
integer j;reg [31:0] rng=32'h47299;
initial begin repeat(4)@(posedge clk);#1;rst=1;waitms(12);
press(1,67000);press(4,67000);sw=0;waitms(12);press(4,3200);
press(2,30);press(2,1100);press(3,1100);press(6,1100);
press(5,1100);cal=8'h20;waitms(50);press(2,40);cal=0;waitms(20);
for(j=0;j<30000;j=j+1)begin
rng=rng*32'd1664525+32'd1013904223;
if(j%11==0)keys=rng[7:5];if(j%101==0)sw=rng[10:9];if(j%139==0)pause=1;else pause=0;
waitms(1);end keys=7;pause=0;waitms(20);
if(gains<200 || zooms<8)$fatal(1,"equivalence coverage %0d/%0d",gains,zooms);
$display("REFINED_CONTROL_EQUIVALENCE_PASS window%0d %0d clocks gain%0d zoom%0d; retained controls equal, diagnostic paging disabled; repeat, saturation, chords, calibration and pause",WINDOW,cycle,gains,zooms);$finish;
end endmodule'''.replace('wire [21:0] a,b;','wire [22:0] a,b;')
for window in (100,135):
    run(f'controls_repeat_equivalence_{window}',src.replace('module tb;',f'module tb;localparam WINDOW={window};'),[R/'rtl/color_regions'/f'{n}.v' for n in ('stable_controls','refined_controls')])
