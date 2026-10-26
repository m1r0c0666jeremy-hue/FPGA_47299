"""Actual editor geometry and scene invalidation while a rectangle scan runs."""
from refined_testlib import R,run

BENCH=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0;reg [1:0] mode=1;
reg down=0,k2=0,k3=0,k4=0,tracking=1,camera=1,video=1,gb=0;
reg [31:0] image=0;reg [767:0] meta=0;wire [2:0] count;wire [3:0] draft,occupied;
integer phase,action,i,observations=0,before_observations;
stage1_scene #(.CYCLES_PER_MS(200)) dut(.clk(clk),.rst_n(rst),.mode(mode),.down2(down),.click2(k2),.click3(k3),.click4(k4),.cancel(1'b0),
.tracking(tracking),.video_ok(video),.camera_ready(camera),.gain_busy(gb),.session(8'd1),.pair(1'b0),.frame_commit(1'b0),
.detection_valid(1'b1),.image_id(image),.meta(meta),.region_count(count),.draft_count(draft),.occupied(occupied),
.image_healthy(camera && video && !gb),.image_reason(4'd3),.shown_point(39'd0));
always @(posedge clk)if(rst && dut.observation_ready && !dut.observer_cancel)observations=observations+1;
task clocks;input integer n;begin repeat(n)@(negedge clk);end endtask
task image_at;input integer x,y;begin image=image+1;meta[31:0]=image;meta[89:79]=x;meta[99:90]=y;end endtask
task corner;input integer x,y;begin image_at(x,y);clocks(10);down=1;clocks(1);down=0;k2=1;clocks(1);k2=0;clocks(10);end endtask
task setup;begin
rst=0;mode=1;tracking=1;camera=1;video=1;gb=0;down=0;k2=0;k3=0;k4=0;
meta=0;meta[255]=1;meta[247]=1;meta[32]=1;meta[415:413]=4;meta[242:235]=1;meta[244]=1;meta[559:544]=1;meta[719:704]=1;
clocks(2);rst=1;clocks(4);corner(100,100);corner(300,200);corner(500,100);corner(700,200);
if(count!=2 || draft!=0)$fatal(1,"scene editor setup count%0d draft%0d",count,draft);
end endtask
initial begin
for(action=0;action<6;action=action+1)for(phase=0;phase<4;phase=phase+1)begin
setup;image_at(200,150);
while(!dut.observer_busy)clocks(1);
clocks(phase);before_observations=observations;
case(action)
0:mode=0;
1:camera=0;
2:video=0;
3:gb=1;
4:meta[559:544]=2;
// Actual edit revision cancels a pending scan, including its publication edge.
5:begin k4=1;clocks(1);k4=0;end
endcase
clocks(10);
if(observations!=before_observations || dut.observer_busy)$fatal(1,"scene stale geometry/position action%0d phase%0d",action,phase);
end
setup;image_at(200,150);clocks(12);
if(dut.inside_mask!=1)$fatal(1,"new scene observation missing");
image_at(600,150);clocks(12);if(dut.inside_mask!=2)$fatal(1,"recovery did not use fresh image");
$display("STAGE1_SCENE_OBSERVER_PASS editor/mode/camera/video/gain/model/revision/phases0-3/recovery");$finish;
end endmodule'''

if __name__=='__main__':
    run('stage1_scene_observer',BENCH,[R/'rtl/color_regions/stage1_regions.v',R/'rtl/color_regions/stage1_sequence.v'],timeout=60)
