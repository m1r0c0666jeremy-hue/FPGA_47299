`timescale 1ns/1ps
module tb_color_regions_capture;
reg clk=0;always #5 clk=~clk;
reg rst_n=0,sof=0,valid=0,fault=0,pair=0,en=1,ready=1;reg [7:0] session=1;reg [95:0] rgb=0;
wire [31:0] id,dropped;wire ov;wire [415:0] meta;
regions_capture u(clk,rst_n,sof,valid,fault,rgb,pair,en,session,ready,id,ov,meta,dropped);
integer frames=0,outputs=0,locked=0,cleared=0,x,y,p,f,pair_arg=0,move_arg=0,shift_x,shift_y;reg [23:0] pixel;
function [23:0] scene(input integer xx,yy,ff);
integer mx,my;
begin
scene=24'h686868;
mx=xx-(move_arg && ff>=5?(ff-4)*8:0);my=yy-(move_arg && ff>=5?(ff-4)*4:0);
if(ff<=6)begin
 if(mx>=300 && mx<=319 && my>=200 && my<=219)scene=move_arg?(pair?24'h646450:24'h645050):(pair?24'h505028:24'h502828);
 if(mx>=900 && mx<=929 && my>=500 && my<=529)scene=move_arg?(pair?24'h787860:24'h786060):(pair?24'h646430:24'h643030);
 if(mx>=600 && mx<=639 && my>=300 && my<=319 && (!move_arg || mx<602 || mx>637 || my<302 || my>317))scene=move_arg?(pair?24'h544c60:24'h484c60):(pair?24'h302030:24'h202040);
end
end endfunction
always @(negedge clk)if(ov)begin
outputs=outputs+1;
$display("RESULT id=%0d full=%b A=%b B=%b A2=%b errors=%h box=%h / %h / %h",meta[31:0],meta[247],meta[245],meta[246],meta[318],meta[234:231],meta[141:100],meta[183:142],meta[297:256]);
if(!meta[255] || meta[415:413]!=1 || !meta[247])$fatal(1,"missing completion/full header");
if(meta[31:0]>=5 && meta[31:0]<=6)begin
 if(!meta[245] || !meta[246] || !meta[318] || meta[382])$fatal(1,"expected 2 red / 1 blue confirmed");
 // Larger red sorts first. Neither box may include the distant red component.
 shift_x=move_arg?(meta[31:0]-4)*8:0;shift_y=move_arg?(meta[31:0]-4)*4:0;
 if(meta[141:100]!=={10'(529+shift_y),10'(500+shift_y),11'(929+shift_x),11'(900+shift_x)})$fatal(1,"A box");
 if(meta[297:256]!=={10'(219+shift_y),10'(200+shift_y),11'(319+shift_x),11'(300+shift_x)})$fatal(1,"second A box");
 if(meta[183:142]!=={10'(319+shift_y),10'(300+shift_y),11'(639+shift_x),11'(600+shift_x)})$fatal(1,"B box");
 if(move_arg && (meta[223:204]!==20'd224 || meta[254:248]!==7'd28))$fatal(1,"thin low-saturation ring statistic");
 locked=locked+1;
end
if(meta[31:0]>=7)begin
 if(meta[245] || meta[246] || meta[318] || meta[382])$fatal(1,"stale box after empty scene");
 cleared=cleared+1;
end
end
initial begin
if($value$plusargs("PAIR=%d",pair_arg))pair=pair_arg;
if($value$plusargs("MOVE=%d",move_arg))begin end
repeat(3)@(negedge clk);rst_n=1;repeat(2000)@(negedge clk);
for(f=1;f<=9;f=f+1)begin
 @(negedge clk);sof=1;valid=0;@(negedge clk);sof=0;
 repeat(6)@(negedge clk);
 for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+4)begin
   valid=1;for(p=0;p<4;p=p+1)rgb[95-p*24-:24]=scene(x+p,y,f);
   @(negedge clk);
 end
 valid=0;repeat(450)@(negedge clk);
end
sof=1;@(negedge clk);sof=0;repeat(200000)@(negedge clk);
if(outputs!=9 || locked!=2 || cleared!=3 || dropped!=0)$fatal(1,"outputs=%d locked=%d clear=%d drop=%d",outputs,locked,cleared,dropped);
$display("PASS capture: pair=%0d moving=%0d, 9 full frames, 2 separated A, dark B, confirmation, empty clears, four pixels/clock",pair,move_arg);
if(move_arg)$display("PASS moving low-saturation materials: unequal A sizes, B thin ring 28%% fill, dynamic ROI and no bright-seed requirement");$finish;
end
initial begin #40000000;$fatal(1,"timeout");end
endmodule
