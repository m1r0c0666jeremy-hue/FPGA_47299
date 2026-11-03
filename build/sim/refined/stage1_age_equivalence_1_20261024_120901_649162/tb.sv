module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=1;reg [2:0] nr=4;reg [3:0] draft=0;
reg sk=0,pk=0,mk=0,can=1,live=1,changed=0,sample=0;reg [3:0] im=0,nm=0;reg [43:0] ds=0;
wire [3:0] sa,sb,ca,cb,oa,ob,ea,eb;wire [2:0] xa,xb,aa,ab;wire ma,mb,ala,alb;wire [1:0] ta,tb;
wire [10:0] da,db;wire [19:0] wa,wb;
stage1_sequence_baseline #(.CYCLES_PER_MS(1)) a(clk,rst,mode,nr,draft,sk,pk,mk,can,live,changed,sample,im,nm,ds,sa,xa,aa,ca,oa,ma,ala,ta,da,wa,ea);
stage1_sequence #(.CYCLES_PER_MS(1)) b(clk,rst,mode,nr,draft,sk,pk,mk,can,live,changed,sample,im,nm,ds,sb,xb,ab,cb,ob,mb,alb,tb,db,wb,eb);
integer cycle=0,i;reg [31:0] rng=32'h1021dabc;
always @(posedge clk)begin #1;cycle=cycle+1;
if({sa,xa,aa,ca,oa,ma,ala,ta,da,wa,ea}!=={sb,xb,ab,cb,ob,mb,alb,tb,db,wb,eb})
$fatal(1,"age equivalence cycle%0d state%0d/%0d dwell%0d/%0d trend%0d/%0d",cycle,sa,sb,wa,wb,ta,tb);
end
initial begin repeat(3)@(negedge clk);rst=1;
for(i=0;i<1010000*1;i=i+1)begin @(negedge clk);sample=i%(10*1)==0;im=1;ds=100;end
if(wa!=999900)$fatal(1,"saturation not reached");
live=0;sample=0;repeat(70000*1)@(negedge clk);live=1;
for(i=0;i<4000*1;i=i+1)begin @(negedge clk);sample=i%(16*1)==0;im=0;ds=100+i/1%50;end
for(i=0;i<200000;i=i+1)begin
@(negedge clk);rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
mode=rng[1:0];nr=rng[4:2]%5;draft=rng[5]?0:3;sk=rng[6];pk=rng[7];mk=rng[8];can=rng[9];
live=rng[10];changed=rng[11] && rng[12];sample=rng[13];im=rng[17:14];nm=rng[21:18];ds={12'd0,rng};end
$display("STAGE1_AGE_EQUIVALENCE_PASS period=%0d cycles=%0d",1,cycle);$finish;end endmodule