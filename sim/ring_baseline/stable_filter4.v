// Keep a classified pixel only when at least one of its eight neighbours agrees.
// Three source mask rows; output is one row late. Bottom zero row drains in 320
// clocks while a new frame's first row is written to the unused third RAM bank.
`default_nettype none
module stable_filter4(input wire clk,rst_n,valid,input wire [10:0] x,input wire [9:0] y,
 input wire [1:0] bank,input wire [7:0] mask,
 output reg ov,output reg [1:0] ob,output reg [10:0] ox,output reg [9:0] oy,output reg [3:0] ha,hb);
 (* ram_style="block" *) reg [7:0] row0[0:319],row1[0:319],row2[0:319];
 reg [7:0] q0,q1,q2,low;reg pv;reg [1:0] pbank;reg [8:0] pg;reg [9:0] py;
 reg drain;reg [1:0] dbank;reg [8:0] dg;
 wire feed=drain || (valid && y!=0);
 wire [8:0] rg=drain?dg:x[10:2];wire [9:0] ry=drain?10'd720:y;
 wire [1:0] wrbank=y%3;reg [7:0] up,mid;
 reg [11:0] ua,ub,ma,mb,la,lb;reg [3:0] nu_a,nu_b,nm_a,nm_b,nl_a,nl_b;
 reg [11:0] wu_a,wu_b,wm_a,wm_b,wl_a,wl_b;
 reg flush;reg [1:0] fb;reg [9:0] fy;reg [3:0] out_a,out_b,flush_a,flush_b;
 wire [12:0] fua={1'b0,ua},fub={1'b0,ub},fma={1'b0,ma},fmb={1'b0,mb},fla={1'b0,la},flb={1'b0,lb};
 integer i;
 always @(posedge clk)begin
 q0<=row0[rg];q1<=row1[rg];q2<=row2[rg];
 if(valid)case(wrbank)0:row0[x[10:2]]<=mask;1:row1[x[10:2]]<=mask;2:row2[x[10:2]]<=mask;endcase
 end
 always @*begin
 case(py%3)0:begin up=q1;mid=q2;end 1:begin up=q2;mid=q0;end default:begin up=q0;mid=q1;end endcase
 if(py==1)up=0;
 for(i=0;i<4;i=i+1)begin nu_a[i]=up[2*i];nu_b[i]=up[2*i+1];nm_a[i]=mid[2*i];nm_b[i]=mid[2*i+1];nl_a[i]=low[2*i];nl_b[i]=low[2*i+1];end
 wu_a={nu_a,ua[11:4]};wu_b={nu_b,ub[11:4]};wm_a={nm_a,ma[11:4]};wm_b={nm_b,mb[11:4]};wl_a={nl_a,la[11:4]};wl_b={nl_b,lb[11:4]};
 out_a=0;out_b=0;flush_a=0;flush_b=0;
 for(i=0;i<4;i=i+1)begin
 out_a[i]=wm_a[i+4] && (|wu_a[i+3+:3] || wm_a[i+3] || wm_a[i+5] || |wl_a[i+3+:3]);
 out_b[i]=wm_b[i+4] && (|wu_b[i+3+:3] || wm_b[i+3] || wm_b[i+5] || |wl_b[i+3+:3]);
 flush_a[i]=ma[i+8] && ((|fua[i+7+:3]) || fma[i+7] || fma[i+9] || (|fla[i+7+:3]));
 flush_b[i]=mb[i+8] && ((|fub[i+7+:3]) || fmb[i+7] || fmb[i+9] || (|flb[i+7+:3]));
 end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin pv<=0;pbank<=0;pg<=0;py<=0;low<=0;drain<=0;dbank<=0;dg<=0;
 ua<=0;ub<=0;ma<=0;mb<=0;la<=0;lb<=0;flush<=0;fb<=0;fy<=0;ov<=0;ob<=0;ox<=0;oy<=0;ha<=0;hb<=0;end
 else begin
 ov<=0;flush<=0;pv<=feed;pg<=rg;py<=ry;pbank<=drain?dbank:bank;low<=drain?8'd0:mask;
 if(valid && y==719 && x==1276)begin drain<=1;dg<=0;dbank<=bank;end
 else if(drain)begin if(dg==319)drain<=0;else dg<=dg+1'b1;end
 if(pv)begin
 if(pg==0)begin ua<={nu_a,8'd0};ub<={nu_b,8'd0};ma<={nm_a,8'd0};mb<={nm_b,8'd0};la<={nl_a,8'd0};lb<={nl_b,8'd0};end
 else begin
 ua<=wu_a;ub<=wu_b;ma<=wm_a;mb<=wm_b;la<=wl_a;lb<=wl_b;
 ov<=1;ob<=pbank;ox<={(pg-9'd1),2'd0};oy<=py-1'b1;ha<=out_a;hb<=out_b;
 if(pg==319)begin flush<=1;fb<=pbank;fy<=py-1'b1;end end end
 if(flush)begin ov<=1;ob<=fb;ox<=1276;oy<=fy;ha<=flush_a;hb<=flush_b;end
 end end
endmodule
`default_nettype wire
