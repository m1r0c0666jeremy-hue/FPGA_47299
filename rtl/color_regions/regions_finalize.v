// Resolve a frozen colour/frame bank. No online root traversal in the line path.
// Candidate128: root127:121, valid120, score119:92, ROI91:90, fill89:83,
// cy82:73, cx72:62, pixels61:42, ymax41:32, ymin31:22, xmax21:11, xmin10:0.
`default_nettype none
module regions_finalize #(parameter WIDTH=1280,HEIGHT=720,AREA_MIN=16,DEADLINE=65536)(
 input wire clk,rst_n,start,bank,input wire [7:0] label_count,input wire [9:0] edge_count,
 input wire invalid,output reg busy,done,failed,
 output reg [127:0] candidate0,candidate1,output reg more,output reg [1:0] clipped,
 output reg [7:0] stat_addr,output reg stat_write,output reg [148:0] stat_data,input wire [148:0] stat_q,
 output reg [9:0] edge_addr,input wire [13:0] edge_q
);
 localparam IDLE=0,INIT=1,EDGE_REQ=2,EDGE_WAIT=3,EDGE_GET=4,FIND_REQ=5,FIND_WAIT=6,FIND_GET=7,
 UNION=8,RANK_UP=9,NEXT_EDGE=10,FOLD=11,SRC_WAIT=12,SRC_GET=13,DST_WAIT=14,DST_GET=15,
 FOLD_WRITE=16,NEXT_FOLD=17,EVAL=18,EVAL_WAIT=19,EVAL_GET=20,AREA=21,DIV_START=22,DIV_WAIT=23,
 SCORE=24,KEEP=25,NEXT_EVAL=26,SELECT=27,FINISH=28;
 reg [4:0] state;reg fb;reg [7:0] count,idx;reg [9:0] num_edges,ei;
 reg [16:0] elapsed;
 reg [6:0] parent[0:127];reg [2:0] rank[0:127];
 reg [6:0] cursor,root_a,root_b,edge_b;reg [2:0] rank_a,rank_b;
 reg [6:0] pq;reg [2:0] rq;reg [3:0] depth;reg [1:0] find_kind;
 reg [148:0] source_stat,eval_stat;
 reg [11:0] bw;reg [10:0] bh;
 reg [31:0] mul_a,mul_result;reg [10:0] mul_b;reg [3:0] mul_count;
 reg [31:0] area,div_num,div_den;reg [1:0] div_kind;reg div_start;
 wire div_busy,div_done;wire [31:0] div_q;
 reg [10:0] cx;reg [9:0] cy;reg [6:0] fill;
 reg [127:0] g0,g1,r0,r1,item;reg [1:0] qualified;
 wire [11:0] width_now={1'b0,stat_q[103:93]}-{1'b0,stat_q[92:82]}+1'b1;
 wire [10:0] height_now={1'b0,stat_q[123:114]}-{1'b0,stat_q[113:104]}+1'b1;
 regions_divide u_div(clk,rst_n,div_start,div_num,div_den,div_busy,div_done,div_q);
 function better;
  input [127:0] a,b;
  begin better=a[120] && (!b[120] || a[119:92]>b[119:92] ||
    (a[119:92]==b[119:92] && (a[31:22]<b[31:22] || (a[31:22]==b[31:22] && a[10:0]<b[10:0]))));end
 endfunction
 function [148:0] add_stats;
  input [148:0] a,b;reg [148:0] v;
  begin v=0;
   v[19:0]=a[19:0]+b[19:0];v[50:20]=a[50:20]+b[50:20];v[81:51]=a[81:51]+b[81:51];
   v[92:82]=a[92:82]<b[92:82]?a[92:82]:b[92:82];v[103:93]=a[103:93]>b[103:93]?a[103:93]:b[103:93];
   v[113:104]=a[113:104]<b[113:104]?a[113:104]:b[113:104];v[123:114]=a[123:114]>b[123:114]?a[123:114]:b[123:114];
   v[145:124]=a[145:124]+b[145:124];v[148:146]=a[148:146]|b[148:146];add_stats=v;
  end
 endfunction
 always @(posedge clk)begin pq<=parent[cursor];rq<=rank[cursor];end
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;busy<=0;done<=0;failed<=0;candidate0<=0;candidate1<=0;more<=0;clipped<=0;
   fb<=0;count<=0;idx<=0;num_edges<=0;ei<=0;elapsed<=0;cursor<=0;root_a<=0;root_b<=0;edge_b<=0;
   rank_a<=0;rank_b<=0;depth<=0;find_kind<=0;source_stat<=0;eval_stat<=0;bw<=0;bh<=0;
   mul_a<=0;mul_b<=0;mul_result<=0;mul_count<=0;area<=0;div_num<=0;div_den<=0;div_kind<=0;div_start<=0;
   cx<=0;cy<=0;fill<=0;g0<=0;g1<=0;r0<=0;r1<=0;item<=0;qualified<=0;
   stat_addr<=0;stat_write<=0;stat_data<=0;edge_addr<=0;
  end else begin
   done<=0;stat_write<=0;div_start<=0;
   if(busy)elapsed<=elapsed+1'b1;
   case(state)
    IDLE:if(start)begin
     busy<=1;failed<=invalid || label_count>128 || edge_count>512;fb<=bank;count<=label_count;num_edges<=edge_count;idx<=0;ei<=0;elapsed<=0;
     g0<=0;g1<=0;r0<=0;r1<=0;qualified<=0;clipped<=0;more<=0;candidate0<=0;candidate1<=0;
     state<=invalid || label_count>128 || edge_count>512 || label_count==0?FINISH:INIT;
    end
    INIT:begin parent[idx[6:0]]<=idx[6:0];rank[idx[6:0]]<=0;
      if(idx+1==count)begin idx<=0;state<=num_edges==0?FOLD:EDGE_REQ;end else idx<=idx+1'b1;end
    EDGE_REQ:begin edge_addr<={fb,ei[8:0]};state<=EDGE_WAIT;end
    EDGE_WAIT:state<=EDGE_GET;
    EDGE_GET:begin cursor<=edge_q[13:7];edge_b<=edge_q[6:0];depth<=0;find_kind<=0;state<=FIND_REQ;end
    FIND_REQ:state<=FIND_GET;
    FIND_WAIT:state<=FIND_GET;
    FIND_GET:begin
      if(pq!=cursor)begin
       if(depth==7)begin failed<=1;state<=FINISH;end
       else begin cursor<=pq;depth<=depth+1'b1;state<=FIND_REQ;end
      end else case(find_kind)
       0:begin root_a<=cursor;rank_a<=rq;cursor<=edge_b;depth<=0;find_kind<=1;state<=FIND_REQ;end
       1:begin root_b<=cursor;rank_b<=rq;state<=UNION;end
       2:begin
         root_a<=cursor;
         if(cursor==idx[6:0])state<=NEXT_FOLD;
         else begin stat_addr<={fb,idx[6:0]};state<=SRC_WAIT;end
       end
       default:state<=FINISH;
      endcase
    end
    UNION:begin
      if(root_a!=root_b)begin
       if(rank_a>=rank_b)parent[root_b]<=root_a;else parent[root_a]<=root_b;
       if(rank_a==rank_b)begin rank[root_a]<=rank_a+1'b1;end
      end
      state<=NEXT_EDGE;
    end
    NEXT_EDGE:if(ei+1==num_edges)begin idx<=0;state<=FOLD;end else begin ei<=ei+1'b1;state<=EDGE_REQ;end
    FOLD:begin cursor<=idx[6:0];find_kind<=2;depth<=0;state<=FIND_REQ;end
    SRC_WAIT:state<=SRC_GET;
    SRC_GET:begin source_stat<=stat_q;stat_addr<={fb,root_a};state<=DST_WAIT;end
    DST_WAIT:state<=DST_GET;
    DST_GET:begin stat_data<=add_stats(stat_q,source_stat);stat_write<=1;state<=FOLD_WRITE;end
    FOLD_WRITE:state<=NEXT_FOLD;
    NEXT_FOLD:if(idx+1==count)begin idx<=0;state<=EVAL;end else begin idx<=idx+1'b1;state<=FOLD;end
    EVAL:if(parent[idx[6:0]]!=idx[6:0])state<=NEXT_EVAL;
      else begin stat_addr<={fb,idx[6:0]};state<=EVAL_WAIT;end
    EVAL_WAIT:state<=EVAL_GET;
    EVAL_GET:begin
      eval_stat<=stat_q;bw<=width_now;bh<=height_now;
      if(stat_q[148])begin clipped<=clipped|stat_q[147:146];state<=NEXT_EVAL;end
      else if(stat_q[19:0]<AREA_MIN || width_now<2 || height_now<2 || width_now*4>WIDTH*3 || height_now*4>HEIGHT*3)state<=NEXT_EVAL;
      else begin mul_a<=width_now;mul_b<=height_now;mul_result<=0;mul_count<=0;state<=AREA;end
    end
    AREA:begin
      if(mul_b[0])mul_result<=mul_result+mul_a;
      mul_a<=mul_a<<1;mul_b<=mul_b>>1;
      if(mul_count==10)begin
       area<=mul_result+(mul_b[0]?mul_a:0);div_num<=({12'd0,eval_stat[19:0]}<<6)+({12'd0,eval_stat[19:0]}<<5)+({12'd0,eval_stat[19:0]}<<2);
       div_den<=mul_result+(mul_b[0]?mul_a:0);div_kind<=0;state<=DIV_START;
      end else mul_count<=mul_count+1'b1;
    end
    DIV_START:if(!div_busy)begin div_start<=1;state<=DIV_WAIT;end
    DIV_WAIT:if(div_done)begin
      case(div_kind)
       0:begin fill<=div_q>100?100:div_q[6:0];div_num<={1'b0,eval_stat[50:20]};div_den<={12'd0,eval_stat[19:0]};div_kind<=1;state<=DIV_START;end
       1:begin cx<=div_q[10:0];div_num<={1'b0,eval_stat[81:51]};div_kind<=2;state<=DIV_START;end
       2:begin cy<=div_q[9:0];mul_a<={12'd0,eval_stat[19:0]};mul_b<=64+fill;mul_result<=0;mul_count<=0;state<=SCORE;end
      endcase
    end
    SCORE:begin
      if(mul_b[0])mul_result<=mul_result+mul_a;
      mul_a<=mul_a<<1;mul_b<=mul_b>>1;
      if(mul_count==7)begin
       item<=0;item[127:121]<=idx[6:0];item[120]<=1;
       item[119:92]<=mul_result+(mul_b[0]?mul_a:0)+({10'd0,eval_stat[145:124]}<<2);
       item[91:90]<=eval_stat[147:146];item[89:83]<=fill;item[82:73]<=cy;item[72:62]<=cx;
       item[61:42]<=eval_stat[19:0];item[41:32]<=eval_stat[123:114];item[31:22]<=eval_stat[113:104];
       item[21:11]<=eval_stat[103:93];item[10:0]<=eval_stat[92:82];state<=KEEP;
      end else mul_count<=mul_count+1'b1;
    end
    KEEP:begin
      if(qualified!=3)qualified<=qualified+1'b1;
      if(better(item,g0))begin g1<=g0;g0<=item;end else if(better(item,g1))g1<=item;
      if(item[90] && better(item,r0))r0<=item;
      if(item[91] && better(item,r1))r1<=item;
      state<=NEXT_EVAL;
    end
    NEXT_EVAL:if(idx+1==count)state<=SELECT;else begin idx<=idx+1'b1;state<=EVAL;end
    SELECT:begin
      if(r0[120] && r1[120] && r0[127:121]!=r1[127:121])begin candidate0<=r0;candidate1<=r1;end
      else begin candidate0<=g0;candidate1<=g1;end
      more<=qualified==3;state<=FINISH;
    end
    FINISH:begin
      if(failed)begin candidate0<=0;candidate1<=0;more<=0;end
      busy<=0;done<=1;state<=IDLE;
    end
   endcase
   if(busy && elapsed>=DEADLINE-1 && state!=FINISH)begin failed<=1;state<=FINISH;stat_write<=0;end
  end
 end
endmodule
`default_nettype wire
