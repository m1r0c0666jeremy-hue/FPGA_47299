`timescale 1ns/1ps
// Three asynchronous domains, real result/snapshot mailboxes, actual frame store,
// display commit and first-line reader request. No synthetic metadata shortcut.
module tb_color_regions_association;
reg cc=0,dc=0,pc=0;always #5 cc=~cc;always #7 dc=~dc;always #4 pc=~pc;
reg rst=0,send_result=0;reg [415:0] cap_meta=0;wire rr,dv;wire [415:0] dmeta;
target_mailbox #(.WIDTH(416)) result_link(cc,rst,send_result,cap_meta,rr,dc,rst,dv,dmeta);
reg request=0;reg [9:0] command=1;wire reqready,dr;wire [9:0] dcommand;
target_mailbox #(.WIDTH(10)) request_link(pc,rst,request,command,reqready,dc,rst,dr,dcommand);
reg beginf=0,write=0;reg [1:0] bank=0;reg [31:0] fid=0;reg [24:0] addr=0;
wire ss,sg,sready,ps;wire [450:0] sd,pd;
regions_frame_store #(.WORDS(4)) store(dc,rst,beginf,bank,fid,write,addr,dv,dmeta,dr&&sready,dcommand,ss,sd,sg);
target_mailbox #(.WIDTH(451)) snapshot_link(dc,rst,ss,sd,sready,pc,rst,ps,pd);
reg vs=0,de=0;wire commit;wire [1:0] ob,oz,om;wire [31:0] oi;wire [10:0] cx,x0;wire [9:0] cy,y0;
wire [415:0] active;wire show,pair,det,sample;wire [2:0] state;
regions_display view(pc,rst,vs,de,ps,pd,command[0],1'b1,1'b0,1'b1,command[8:1],2'd0,2'd0,command[9],
 commit,ob,oi,cx,x0,cy,y0,oz,om,active,show,pair,det,sample,state);
wire busy,read_en;wire [24:0] read_addr;reg rdvalid=0;wire ovs,ohs,ode,ok;wire [23:0] rgb;
regions_line_reader reader(commit,sg,rst,dc,1'b0,1'b0,ob,oi,1'b1,rdvalid,128'd0,busy,read_en,read_addr,
 pc,vs,1'b0,de,x0,y0,oz,ovs,ohs,ode,rgb,ok);
integer checks=0,read_checks=0;reg expecting_read=0;reg [24:0] expected_addr;reg [31:0] expected_id;
function [24:0] base(input [1:0] b);
begin case(b)0:base=0;1:base=7000000;2:base=14000000;3:base=21000000;endcase end endfunction
function [415:0] packet(input [31:0] id,input [9:0] cmd,input box);
begin packet=0;packet[31:0]=id;packet[255]=1;packet[415:413]=1;packet[244]=cmd[0];packet[243]=cmd[9];packet[242:235]=cmd[8:1];packet[247]=1;
packet[245]=box;packet[141:100]={10'd219,10'd200,11'd319,11'd300};packet[408]=1;packet[407:384]=24'h123456;end endfunction
always @(posedge dc)begin
 rdvalid<=read_en;
 if(read_en && expecting_read)begin
  if(read_addr!==expected_addr || reader.frame_id_d!==expected_id)$fatal(1,"reader image identity bank/address %0d expected%0d id%0d expected%0d",read_addr,expected_addr,reader.frame_id_d,expected_id);
  expecting_read=0;read_checks=read_checks+1;
 end
end
task capture(input [1:0] b,input [31:0] id);integer k;
begin
 @(negedge dc);beginf=1;bank=b;fid=id;@(negedge dc);beginf=0;
 for(k=0;k<4;k=k+1)begin write=1;addr=base(b)+k*8;@(negedge dc);end
 write=0;
end endtask
task result(input [415:0] m);
begin
 while(!rr)@(negedge cc);
 @(negedge cc);send_result=1;cap_meta=m;@(negedge cc);send_result=0;
 repeat(15)@(negedge dc);
end endtask
task display_frame(input [31:0] id,input [1:0] b,input has_meta,input has_box);integer waitn;
begin
 @(negedge pc);vs=1;request=1;expecting_read=1;expected_addr=base(b)+48*1920;expected_id=id;
 @(negedge pc);request=0;vs=0;waitn=0;
 while(!commit && waitn<100)begin @(negedge pc);waitn=waitn+1;end
 if(!commit || oi!==id || ob!==b || active[255]!==has_meta || (det&&active[245])!==has_box)$fatal(1,"display identity id%0d bank%0d meta%b box%b",oi,ob,active[255],det&&active[245]);
 repeat(1000)@(negedge pc);
 if(expecting_read)$fatal(1,"no immutable first-line request");
 // An active bank change cannot retarget the following line requests.
 if(reader.frame_id_d!==id)$fatal(1,"line generation changed");
 checks=checks+1;
end endtask
initial begin
 repeat(5)@(negedge dc);rst=1;repeat(20)@(negedge pc);
 capture(3,1);result(packet(1,1,1));capture(0,2);display_frame(1,3,1,1);
 capture(1,3);display_frame(3,1,0,0);
 result(packet(2,1,1));display_frame(2,0,1,1);
 result(packet(3,1,0));display_frame(3,1,1,0);
 command=0;display_frame(3,1,0,0);
 // Reusing the selected bank aborts its outstanding image immediately.
 @(negedge dc);beginf=1;bank=1;fid=7;#1;if(sg)$fatal(1,"reuse did not revoke selected image");
 @(negedge dc);beginf=0;repeat(20)@(negedge pc);if(ok)$fatal(1,"reader did not abort reused image");
 // In-flight wide transfer is cancelled by common reset; no ghost metadata.
 @(negedge cc);send_result=1;cap_meta=packet(7,1,1);@(negedge cc);send_result=0;rst=0;
 repeat(5)@(negedge dc);rst=1;command=1;repeat(20)@(negedge pc);
 capture(2,8);display_frame(8,2,0,0);
 if(checks!=6 || read_checks!=6)$fatal(1,"coverage counts");
 $display("PASS association: 6 asynchronous full transactions, 416/451-bit CDC, actual selected bank/first-line ID, late/empty results, command, reuse abort and reset");$finish;
end
initial begin #2000000;$fatal(1,"timeout");end
endmodule
