
module tb;
reg clk=0; always #5 clk=~clk;
reg rst=0,vs=0,snapshot=0,rotate=0;
reg [2:0] zoom=0; reg [851:0] data=0;
wire commit,valid; wire [767:0] meta;
wire [10:0] x0; wire [9:0] y0;
wire [2:0] shown_zoom; wire shown_rotate;
stable_display #(.V4(1)) display_view(
 .I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(1'b0),.I_snapshot(snapshot),.I_data(data),
 .I_tracking(1'b1),.I_show(1'b1),.I_conflict(1'b0),.I_live(1'b1),.I_session(8'd1),
 .I_zoom(zoom),.I_mode(2'd0),.I_pair(1'b0),.I_rotate(rotate),
 .O_commit(commit),.O_meta(meta),.O_x0(x0),.O_y0(y0),.O_zoom(shown_zoom),
 .O_rotate(shown_rotate),.O_detection_valid(valid));
integer z,r;
task submit;
begin
 @(negedge clk);vs=1;
 @(negedge clk);vs=0;
 repeat(2)@(negedge clk);snapshot=1;
 @(negedge clk);snapshot=0;
 if(!commit)$fatal(1,"display did not commit the source snapshot");
end endtask
initial begin
 repeat(4)@(negedge clk);rst=1;
 data[31:0]=77;data[799:768]=77;data[802]=1;
 data[255]=1;data[247]=1;data[244]=1;data[242:235]=1;data[415:413]=4;data[32]=1;
 data[719:704]=7;data[850:835]=7;
 data[47:37]=600;data[57:48]=360;data[68:58]=680;data[78:69]=360;
 data[89:79]=640;data[99:90]=360;
 data[141:100]={10'd367,10'd352,11'd607,11'd592};
 data[183:142]={10'd367,10'd352,11'd687,11'd672};
 for(z=0;z<5;z=z+1)for(r=0;r<2;r=r+1)begin
  zoom=z;rotate=r;submit;
  if(!valid || shown_zoom!==zoom || shown_rotate!==rotate)$fatal(1,"invalid committed view");
  if(meta!==data[767:0])$fatal(1,"source metadata changed with zoom/orientation");
  if(meta[89:79]!==11'd640 || meta[99:90]!==10'd360)$fatal(1,"tip no longer in 1280x720 source coordinates");
  if(meta[47:37]!==11'd600 || meta[68:58]!==11'd680)$fatal(1,"marker source coordinates changed");
 end
 // A mismatched source identity must not present a stale target as valid.
 data[799:768]=78;submit;
 if(valid || meta!==768'd0)$fatal(1,"mismatched frame exposed stale source coordinates");
 $display("SOURCE_COORDINATES_720P_PASS five zooms x two rotations; unchanged source tip/markers/boxes; mismatched frame invalidated");
 $finish;
end
endmodule
