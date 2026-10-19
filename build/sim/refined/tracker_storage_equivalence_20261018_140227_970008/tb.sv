module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,start=0,complete=1;
reg [31:0] id=0,rng=32'h47299;reg [9:0] command=3;reg [15:0] revision=0;
reg [1023:0] candidates=0;wire [436:0] g,d;integer f,j,k,n,tips=0,checks=0;reg [15:0] reasons=0;
reference_tracker gold(.clk(clk),.rst_n(rst),.start(start),.frame_id(id),.command(command),.revision(revision),.complete(complete),.candidates(candidates),.done(g[0:0]),.a(g[128:1]),.b(g[256:129]),.tip_valid(g[257:257]),.tip_x(g[268:258]),.tip_y(g[278:269]),.reason(g[282:279]),.history_valid(g[283:283]),.history_boxes(g[367:284]),.selection_state(g[369:368]),.history_command(g[379:370]),.history_revision(g[395:380]),.history_frame(g[427:396]),.history_loss(g[432:428]),.tip_bounds(g[436:433]));
stable_tracker dut(.clk(clk),.rst_n(rst),.start(start),.frame_id(id),.command(command),.revision(revision),.complete(complete),.candidates(candidates),.done(d[0:0]),.a(d[128:1]),.b(d[256:129]),.tip_valid(d[257:257]),.tip_x(d[268:258]),.tip_y(d[278:269]),.reason(d[282:279]),.history_valid(d[283:283]),.history_boxes(d[367:284]),.selection_state(d[369:368]),.history_command(d[379:370]),.history_revision(d[395:380]),.history_frame(d[427:396]),.history_loss(d[432:428]),.tip_bounds(d[436:433]));
task tick;begin @(negedge clk);if(g!==d)$fatal(1,"tracker storage output mismatch f%0d gstate%0d dstate%0d pair%0d/%0d g%h d%h",f,gold.state,dut.state,gold.pair_index,dut.pair_index,g,d);checks=checks+1;end endtask
function [31:0] random32;begin rng=rng*1664525+1013904223;random32=rng;end endfunction
function [127:0] object(input integer x,y);reg [127:0] v;begin
v={random32(),random32(),random32(),random32()};v[120]=1;v[61:42]=48+(rng%4000);v[89:83]=rng%101;
v[72:62]=x;v[82:73]=y;v[41:0]={10'd600,10'd32,11'd1000,11'd64};object=v;end endfunction
initial begin repeat(4)tick;rst=1;
for(f=0;f<3000;f=f+1)begin
 if(f>100 && f%137==0)begin rst=0;repeat(3)tick;rst=1;end
 if(f==200)begin rst=0;repeat(2)tick;rst=1;id=32'hfffffffe;end
 if(f<=100 || f%11!=0)id=id+1;
 if(f>100 && f%23==0)id=id+20;
 if(f>100 && f%31==0)id=id-2;
 if(f>100 && f%157==0)revision=revision+1;
 command=(f>100 && f%43==0)?0:3;complete=!(f>100 && f%47==0);
 candidates=0;
 for(j=0;j<8;j=j+1)begin
  candidates[j*128+:128]=object(random32()%1280,random32()%720);
  candidates[j*128+120]=(f>100 && (rng%3)!=0);
 end
 candidates[((f/7)%4)*128+:128]=object(600+(f%16),300);
 candidates[(4+(f/11)%4)*128+:128]=object(700+(f%16),400);
 if(f>100 && f%53==0)for(j=0;j<4;j=j+1)candidates[j*128+120]=0;
 if(f>100 && f%59==0)for(j=4;j<8;j=j+1)candidates[j*128+120]=0;
 start=1;tick;start=0;n=0;
 while(!gold.done && n<150)begin tick;n=n+1;end
 if(!gold.done)$fatal(1,"tracker storage completion timeout");
 if(gold.tip_valid)tips=tips+1;reasons[gold.reason]=1;tick;
end
if(tips<10 || !reasons[8])$fatal(1,"insufficient transaction coverage tips%0d reasons%h",tips,reasons);
$display("TRACKER_STORAGE_EQUIVALENCE_PASS 3000 held-input transactions, %0d cycles all437 external bits equal, tips%0d reasons%h; canonical production with held candidate input",checks,tips,reasons);$finish;
end endmodule