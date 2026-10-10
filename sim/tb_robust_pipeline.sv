`timescale 1ns/1ps
module tb_robust_pipeline;
 reg clk=0,sc=0,rst=0;always #5 clk=~clk;always #7 sc=~sc;
 reg sof=0,iv=0,fault=0;reg [95:0] rgb=0;reg [9:0] desired=0,sent=0;
 wire ready,cv;wire [9:0] cmd;
 reg [9:0] active=0;
 wire send=ready && desired!=sent;
 always @(posedge sc) if(!rst)sent<=0;else if(send)sent<=desired;
 always @(posedge clk) if(!rst)active<=0;else if(cv)active<=cmd;
 target_mailbox #(.WIDTH(10)) mb(sc,rst,send,desired,ready,clk,rst,cv,cmd);
 wire dv,tv;wire [31:0] id;wire [255:0] dm,tm;
 target_detector #(.COLOR_MIN(40),.COLOR_DIFF(12),.RATIO_NUM(9),.RATIO_DEN(8),.AREA_MIN(32),.AREA_MAX(921600),.FILL_PERCENT_MIN(0),.YP_MIN(40),.YP_DIFF(12),.YP_RATIO_NUM(9),.YP_RATIO_DEN(8),.YP_BALANCE(4),.WIDTH(128),.HEIGHT(64)) detector(clk,rst,sof,iv,fault,rgb,id,dv,dm,active[9],active[0],active[8:1]);
 target_tracker #(.SEP_MAX(1468),.WIDTH(128),.HEIGHT(64)) tracker(clk,rst,active[0],active[8:1],dv,dm,tv,tm,active[9]);
 integer f,e,n,ss,vv,ff,cc,checked=0,tracked=0,expected_count,streak=0,locks=0,rejected=0;
 reg [95:0] word;reg [255:0] expected;reg [9:0] prev_cmd=0;
 reg expect_valid=0;reg [31:0] last=0;
 integer ax,ay,bx,by,tx,ty,sep;
 string stimulus,oracle;
 // Reference checks compare exact detector statistics from Python, then an
 // independent three-consecutive-frame acceptance model for this static tool.
 always @(negedge clk) if(rst) begin
  if(active!=prev_cmd)begin streak=0;prev_cmd=active;end
  if(dv)begin
   n=$fscanf(e,"%h\n",expected);
   if(n!=1||dm!==expected)$fatal(1,"frame %0d detector actual=%h expected=%h",checked,dm,expected);
   checked=checked+1;
   ax=expected[47:37];ay=expected[57:48];bx=expected[68:58];by=expected[78:69];
   tx=ax+((ax-bx+1)/2);ty=ay+((ay-by+1)/2);sep=(ax-bx)*(ax-bx)+(ay-by)*(ay-by);
   expect_valid=0;
   if(active[0]&&expected[244]&&expected[243]==active[9]&&expected[242:235]==active[8:1])begin
    if(expected[32]&&sep>=256&&sep<=2155024&&tx>=0&&tx<128&&ty>=0&&ty<64)begin
     if(last!=0&&expected[31:0]!=last+1)streak=0;
     streak=streak+1;expect_valid=streak>=3;
    end else streak=0;
    last=expected[31:0];
   end else rejected=rejected+1;
  end
  if(tv)begin
   if(tm[32]!==expect_valid)$fatal(1,"tracker #%0d lock expected=%0d actual=%0d",tracked,expect_valid,tm[32]);
   if(tm[244:235]!==expected[244:235])$fatal(1,"tracker relabelled old frame");
   if(tm[254:245]!==expected[254:245]||tm[230:224]!==expected[230:224])$fatal(1,"tracker changed independent candidate statistics");
   if(tm[32])locks=locks+1;tracked=tracked+1;
  end
 end
 initial begin
  if(!$value$plusargs("STIM=%s",stimulus)||!$value$plusargs("EXPECT=%s",oracle)||!$value$plusargs("COUNT=%d",expected_count))$fatal;
  f=$fopen(stimulus,"r");e=$fopen(oracle,"r");repeat(5)@(negedge clk);rst=1;
  while(!$feof(f))begin
   @(negedge clk);#1;n=$fscanf(f,"%d %d %d %d %h\n",ss,vv,ff,cc,word);
   if(n==5)begin sof=ss;iv=vv;fault=ff;desired=cc;rgb=word;end
  end
  @(negedge clk);#1;sof=0;iv=0;repeat(250)@(negedge clk);
  if(checked!=expected_count||tracked!=checked||locks<4||rejected<3)$fatal(1,"coverage checked=%0d tracked=%0d locks=%0d stale=%0d",checked,tracked,locks,rejected);
  $display("PASS dualcolor pipeline: frames=%0d locks=%0d stale_rejected=%0d, asynchronous commands and frame-stamped config",checked,locks,rejected);$finish;
 end
 initial begin #100000000;$fatal(1,"pipeline timeout");end
endmodule
