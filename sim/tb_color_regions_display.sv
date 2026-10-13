`timescale 1ns/1ps
module tb_color_regions_display;
reg clk=0;always #5 clk=~clk;
reg rst=0,vs=0,de=0,snap=0,tracking=1,show=1,conflict=0,live=1,pair=0;
reg [7:0] session=1;reg [1:0] zoom=0,mode=0;reg [450:0] data=0;
wire commit;wire [1:0] bank,oz,om;wire [31:0] fid;wire [10:0] cx,x0;wire [9:0] cy,y0;wire [415:0] meta;
wire os,op,dv,sv;wire [2:0] state;
regions_display u(clk,rst,vs,de,snap,data,tracking,show,conflict,live,session,zoom,mode,pair,
 commit,bank,fid,cx,x0,cy,y0,oz,om,meta,os,op,dv,sv,state);
task packet(input integer id,input integer bk,input bit enable,input bit detected);
begin data=0;data[450]=1;data[449:448]=bk;data[447:416]=id;data[31:0]=id;
data[255]=1;data[415:413]=1;data[247]=1;data[408]=1;data[244]=enable;data[245]=detected;
data[242:235]=session;data[243]=pair;end endtask
task blank;
begin @(negedge clk);de=0;vs=1;@(negedge clk);vs=0;repeat(2)@(negedge clk);snap=1;@(negedge clk);snap=0;#1;
if(!commit)$fatal(1,"blank snapshot not committed");@(negedge clk);de=1;@(negedge clk);end endtask
integer i;
initial begin
repeat(3)@(negedge clk);rst=1;packet(7,2,1,1);blank;
if(!dv || !sv || fid!=7 || bank!=2 || x0!=0 || y0!=48 || cx!=640 || cy!=360)$fatal(1,"initial transaction");
zoom=2;mode=3;packet(8,3,1,1);snap=1;@(negedge clk);snap=0;
if(commit || fid!=7 || bank!=2 || oz!=0 || om!=0)$fatal(1,"midframe transaction");
blank;if(fid!=8 || bank!=3 || oz!=2 || om!=3 || x0!=480 || y0!=282)$fatal(1,"zoom transaction");
for(i=1;i<=14;i=i+1)begin blank;if(!dv)$fatal(1,"stale too early %d",i);end
blank;if(dv || sv || state!=7)$fatal(1,"15 repeated frames must hide");
packet(9,0,1,0);blank;if(!dv || meta[245] || state!=1)$fatal(1,"new empty clears");
pair=1;#1;if(dv || sv)$fatal(1,"pair identity");packet(10,1,1,1);blank;if(!dv)$fatal(1,"pair renew");
session=2;#1;if(dv)$fatal(1,"session identity");packet(11,2,1,1);blank;if(!dv)$fatal(1,"session renew");
tracking=0;#1;if(dv)$fatal(1,"stop");packet(12,3,0,0);blank;if(dv || !sv || state!=0)$fatal(1,"standby sample");
live=0;#1;if(sv || state!=6)$fatal(1,"video loss");
$display("PASS display atomic blank commit, centered zoom, 15 stale frames, empty, session/pair/enable, sample and video loss");$finish;
end
endmodule
