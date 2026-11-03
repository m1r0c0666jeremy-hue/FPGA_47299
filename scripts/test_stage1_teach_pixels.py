"""Every output video pixel against rational coordinates, all zooms/directions."""
from fractions import Fraction
from refined_testlib import R,run

def ceil(n):return -((-n.numerator)//n.denominator)

def main():
    cases=[(z,r,1,1) for z in range(5) for r in (0,1)]+[(4,1,0,1),(4,1,1,0)]
    src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0,vs=0,snapshot=0,show=1,use_point=1,rotate=0;reg [2:0] zoom=0;
reg [851:0] packet=0;wire commit;wire [767:0] meta;wire [10:0] x0;wire [9:0] y0;wire [38:0] shown;
wire [2:0] active_zoom;wire active_rotate;wire [23:0] rgb;wire ode;
wire [38:0] desired={16'd500,use_point,1'b1,10'd376,11'd720};
stage1_viewport #(.V4(1)) view(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_de(de),.I_snapshot(snapshot),.I_data(packet),
.I_tracking(1'b0),.I_show(show),.I_conflict(1'b0),.I_live(1'b1),.I_session(8'd1),.I_zoom(zoom),.I_mode(2'd0),
.I_pair(1'b0),.I_rotate(rotate),.O_commit(commit),.O_meta(meta),.O_x0(x0),.O_y0(y0),.O_zoom(active_zoom),.O_rotate(active_rotate),.I_point(desired),.O_point(shown));
stage1_osd osd(.I_clk(clk),.I_rst_n(rst),.I_vs(vs),.I_hs(1'b0),.I_de(de),.I_rgb(24'h123456),
.I_meta(meta),.I_x0(x0),.I_y0(y0),.I_zoom(active_zoom),.I_mode(2'd0),.I_state(3'd0),
.I_tracking(1'b0),.I_show(show),.I_video_ok(1'b1),.I_pair(1'b0),.I_detection_valid(1'b0),.I_sample_valid(1'b0),
.I_rotate(active_rotate),.I_image_id(32'd1),.I_geometry_commit(commit),.I_latency_valid(1'b0),.I_latency_us(32'd0),.I_frame_age(32'd0),
.I_ddr_diag(128'd0),.I_pixel_diag(128'd0),.I_recovery(39'd0),.I_camera(18'd90),.I_gain_target(7'd90),.I_tip_reason(4'd0),
.I_ui_mode(2'd3),.I_region_vertices(672'd0),.I_region_draft(168'd0),.I_region_counts(16'd0),.I_region_closed(4'd0),
.I_area_count(3'd0),.I_expected_area(3'd0),.I_actual_area(3'd0),.I_draft_count(4'd0),.I_run_state(4'd0),.I_completed(4'd0),.I_occupied(4'd0),
.I_area_muted(1'b0),.I_area_trend(2'd0),.I_area_distance(11'd0),.I_area_dwell(20'd0),.I_edit_error(4'd0),.I_start_error(4'd0),
.I_area_busy(1'b0),.I_tip_live(1'b0),.I_gain_busy(1'b0),.I_gain_failed(1'b0),.I_gain_slot(3'd5),.I_k_value(8'd50),.I_k_adjust(1'b0),.I_teaching(80'd0),.I_point(shown[22:0]),.O_de(ode),.O_rgb(rgb));
integer x,y,c,pixels=0,checked=0,green=0,tx,ty,ex,ey,source_index=0,ox,oy;reg checking=0;reg [23:0] e0,e1;reg v0=0,v1=0;
always @(posedge clk)begin
if(de)begin ox=source_index%1280;oy=source_index/1280;source_index=source_index+1;
e0<=show && use_point && ((ox>=tx-6 && ox<=tx+6 && oy>=ty-1 && oy<=ty+1)||(oy>=ty-6 && oy<=ty+6 && ox>=tx-1 && ox<=tx+1))?24'h40ff90:24'h123456;end
e1<=e0;v0<=de;v1<=v0;#1;
if(checking && (ode!==v1 || (v1 && rgb!==e1)))$fatal(1,"replay pixel c%0d xy%0d/%0d got%h expected%h",c,x,y,rgb,e1);
if(checking && ode)begin checked=checked+1;pixels=pixels+1;if(rgb==24'h40ff90)green=green+1;end
end
task frame;begin
checking=0;de=0;rst=0;repeat(3)@(negedge clk);rst=1;
packet=0;packet[31:0]=1;packet[32]=1;packet[89:79]=50;packet[99:90]=50;packet[242:235]=1;packet[247]=1;packet[255]=1;
packet[415:413]=4;packet[671:640]=10000;packet[719:704]=7;packet[720]=1;packet[799:768]=1;packet[802]=1;packet[834:803]=10000;packet[850:835]=7;packet[851]=1;
vs=1;@(negedge clk);snapshot=1;@(negedge clk);snapshot=0;vs=0;repeat(200)@(negedge clk);
if(x0!=ex || y0!=ey)$fatal(1,"viewport oracle c%0d actual%0d/%0d expected%0d/%0d",c,x0,y0,ex,ey);
checking=1;checked=0;green=0;source_index=0;
for(y=0;y<624;y=y+1)for(x=0;x<1650;x=x+1)begin @(negedge clk);de=x<1280;end
@(negedge clk);de=0;repeat(3)@(negedge clk);checking=0;
if(checked!=798720 || green!=(show && use_point?69:0))$fatal(1,"replay pixels checked%0d green%0d",checked,green);
end endtask
initial begin
'''
    sizes=[(1280,624),(853,416),(640,312),(427,208),(320,156)]
    for c,(z,r,show,use) in enumerate(cases):
        w,h=sizes[z];cx=664 if use else 616;cy=376 if use else 336
        cx=max(w//2,min(1280-w+w//2,cx));cy=max(h//2,min(720-h+h//2,cy))
        x0,y0=cx-w//2,cy-h//2;p,q=((1,1),(3,2),(2,1),(3,1),(4,1))[z]
        def mapped(v,origin,extent):
            left=ceil(Fraction((v-origin)*p,q));right=ceil(Fraction((v-origin+1)*p,q))-1
            middle=(left+right)//2;return extent-1-middle if r else middle
        tx,ty=mapped(720,x0,1280),mapped(376,y0,624)
        src+=f'c={c};zoom={z};rotate={r};show={show};use_point={use};tx={tx};ty={ty};ex={x0};ey={y0};frame;\n'
    src+='$display("STAGE1_TEACH_PIXELS_PASS cases=12 pixels=%0d",pixels);$finish;end endmodule'
    mods=['stage1_regions','stage1_sequence','refined_zoom_geometry','stage1_osd','stage1_render','stage1_ui_formatter','stage1_ui_text',
          'refined_overlay_geometry','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom']
    run('stage1_teach_pixels',src,[R/'rtl/color_regions'/f'{n}.v' for n in mods],timeout=900)

if __name__=='__main__':main()
