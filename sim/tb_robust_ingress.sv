`timescale 1ns/1ps
module tb_robust_ingress;
 parameter CP=8,DP=7;
 reg cc=0,dc=0,rst=0,sf=0,valid=0,ready=1,read_busy=0;
 always #(CP) cc=~cc;always #(DP) dc=~dc;
 reg [31:0] frame=0;reg [127:0] pixel=0;
 wire wr,busy,begin_frame,overflow;wire [24:0] addr;wire [127:0] data;
 wire [1:0] bank,rp;wire [31:0] id;
 video_in dut(rst,cc,sf,frame,begin_frame,bank,id,overflow,valid,pixel,1'b0,dc,1'b0,read_busy,busy,rp,wr,addr,data,ready);
 reg snapshot=0;reg [1:0] selected=0;wire snap,good;wire [290:0] snap_data;
 target_frame_store #(.WORDS(960)) store(dc,rst,begin_frame,bank,id,wr,addr,1'b0,256'd0,snapshot,selected,snap,snap_data,good);
 wire full_snap,full_good;wire [290:0] full_data;
 target_frame_store full_store(dc,rst,begin_frame,bank,id,wr,addr,1'b0,256'd0,snapshot,selected,full_snap,full_data,full_good);
 integer received=0,begins=0,active_id=0,beat=0,total=0;reg check_data=1;reg [24:0] base=0;
 function [127:0] pattern(input integer f,input integer n);pattern={32'haced0000|f,32'h01234567^n,32'hfedcba98+n,32'h10000000*f+n};endfunction
 function [24:0] bank_base(input [1:0] b);case(b)0:bank_base=0;1:bank_base=7000000;2:bank_base=14000000;3:bank_base=21000000;endcase endfunction
 always @(posedge dc) if(rst) begin
  if(begin_frame) begin
   if(wr)$fatal(1,"ambiguous frame boundary");
   begins=begins+1;received=0;active_id=id;base=bank_base(bank);
  end
  if(wr) begin
   if(check_data && (data!==pattern(active_id,received) || addr!==base+received*8))
    $fatal(1,"payload/order bank error CP=%0d DP=%0d f=%0d beat=%0d addr=%0d data=%h",CP,DP,active_id,received,addr,data);
   received=received+1;total=total+1;
  end
 end
 always @(posedge cc)if(rst && dut.fifo_push && dut.S_fifo_rst)$fatal(1,"FIFO write during reset");
 task send_frame(input integer f,input integer words,input integer stalled);
  integer n;
  begin
   @(negedge cc);frame=f;sf=1;valid=1;pixel=pattern(f,0);
   @(negedge cc);sf=0;valid=0;
   for(n=1;n<words;n=n+1) begin
    // Camera cannot stop; cadence below matches packed line rate at all clocks.
    valid=1;pixel=pattern(f,n);@(negedge cc);valid=0;
    repeat(3)@(negedge cc);
    if(stalled && n==250)begin ready=0;read_busy=1;end
    if(stalled && n==280)begin ready=1;read_busy=0;end
   end
   repeat(1800)@(negedge cc);
  end
 endtask
 task check_complete(input [1:0] b,input integer expected_good);
  begin
   @(negedge dc);selected=b;snapshot=1;@(negedge dc);snapshot=0;
   if(snap_data[290]!==expected_good[0])$fatal(1,"bank completion expected=%0d actual=%b",expected_good,snap_data[290]);
  end
 endtask
 initial begin
  repeat(10)@(negedge cc);rst=1;repeat(12)@(negedge cc);
  send_frame(1,960,0);if(received!=960||overflow)$fatal(1,"first frame loss");check_complete(0,1);
  send_frame(2,960,1);if(received!=960||overflow)$fatal(1,"stall loss");check_complete(1,1);
  send_frame(3,730,0);if(received!=720)$fatal(1,"short frame");check_complete(2,0);
  send_frame(4,960,0);if(received!=960||overflow)$fatal(1,"short recovery");check_complete(3,1);
  // Full 720p frame verifies 172800 exact words and address range.
  send_frame(5,172800,1);if(received!=172800||overflow)$fatal(1,"full frame");
  @(negedge dc);selected=0;snapshot=1;@(negedge dc);snapshot=0;
  if(!full_data[290] || full_data[287:256]!=5)$fatal(1,"full-frame DDR acceptance");
  // Sustained DDR outage must reject a frame, then recover on a new SOF.
  ready=0;check_data=0;send_frame(6,1200,0);if(!overflow)$fatal(1,"overflow not reported");
  ready=1;repeat(1800)@(negedge cc);check_data=1;
  send_frame(7,960,0);if(received!=960||overflow)$fatal(1,"overflow recovery");check_complete(2,1);
  // Reset while data buffered: no stale outputs in the new session.
  @(negedge cc);ready=0;frame=8;sf=1;valid=1;pixel=pattern(8,0);
  @(negedge cc);sf=0;
  for(beat=1;beat<50;beat=beat+1)begin pixel=pattern(8,beat);@(negedge cc);end
  rst=0;valid=0;repeat(12)@(negedge cc);rst=1;ready=1;repeat(12)@(negedge cc);
  send_frame(9,960,0);if(received!=960||overflow)$fatal(1,"reset recovery");check_complete(0,1);
  // Next SOF during a previous burst, including its registered output beat.
  @(negedge cc);frame=10;sf=1;valid=1;pixel=pattern(10,0);
  @(negedge cc);sf=0;valid=0;
  for(beat=1;beat<250;beat=beat+1)begin
   valid=1;pixel=pattern(10,beat);@(negedge cc);valid=0;repeat(3)@(negedge cc);
  end
  if(!busy)$fatal(1,"boundary overlap scenario did not exercise an active burst");
  send_frame(11,960,0);if(received!=960||overflow)$fatal(1,"overlapping boundary recovery");check_complete(2,1);
  $display("PASS ingress CP=%0d DP=%0d: SOF+data, 960/full172800, stalls, short/overflow/reset recovery, exact payload/address",CP,DP);$finish;
 end
 initial begin #500000000;$fatal(1,"timeout");end
endmodule
