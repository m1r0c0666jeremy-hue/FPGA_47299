"""Colour and effective FPS only, over the qualified 4081ad0 data path."""
CHARS = ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'


def runtime_source():
    return r'''
// Counts complete source identities first shown as valid video; not HDMI ticks.
module stage1_demo_fps(input wire clk,rst_n,input wire [31:0] now_us,
 input wire sample,input wire [31:0] image_id,input wire [15:0] epoch,
 output reg [7:0] fps);
 reg started,seen;
 reg [31:0] window_start,last_id;
 reg [15:0] last_epoch;
 reg [7:0] count;
 wire fresh=sample && (!seen || epoch!=last_epoch || $signed(image_id-last_id)>0);
 wire [31:0] elapsed=now_us-window_start;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 started<=0;seen<=0;window_start<=0;last_id<=0;last_epoch<=0;count<=0;fps<=0;
 end else begin
 if(!started)begin started<=1;window_start<=now_us;count<=fresh?1:0;end
 else if(elapsed>=1000000)begin
 fps<=elapsed>=2000000?0:count;
 window_start<=now_us;count<=fresh?1:0;
 end else if(fresh && count!=255)count<=count+1'b1;
 if(fresh)begin seen<=1;last_id<=image_id;last_epoch<=epoch;end
 end end
endmodule
'''


def decorate(out):
    v = out['rtl/color_regions/stage1_memory_video_out.v']
    old = 'stage1_osd u_osd ('
    assert old in v
    v = v.replace(old, '''wire [7:0] demo_fps;
    stage1_demo_fps fps_counter(I_pixel_clk,I_process_rst_n,I_board_us,
     S_hdmi_out_de && video_ok && image_time_valid,selected_frame_id,image_epoch,demo_fps);
    stage1_osd #(.SHOW_FPS(1)) u_osd (''', 1)
    assert '.I_frame_age(frame_age)' in v
    # Only the OSD numeric field is reused. Real image-age safety stays intact.
    v = v.replace('.I_frame_age(frame_age)', ".I_frame_age({24'd0,demo_fps})", 1)
    out['rtl/color_regions/stage1_memory_video_out.v'] = v + runtime_source()

    s = out['rtl/color_regions/stage1_osd.v']
    s = s.replace('module stage1_osd(', 'module stage1_osd #(parameter SHOW_FPS=0)(', 1)
    s = s.replace('reg flat_valid;', 'reg [1:0] fps_teach;\n reg [5:0] fps_start;reg fps_row,fps_override;reg [7:0] fps_glyph;\n reg flat_valid;', 1)
    s = s.replace('flat_valid<=0;flatency<=0;fage<=0;',
                  'fps_teach<=0;flat_valid<=0;flatency<=0;fage<=0;', 1)
    s = s.replace('flat_valid<=I_latency_valid;',
                  'fps_teach<=I_teaching[55:54];flat_valid<=I_latency_valid;', 1)
    old = "color_a=I_pair?24'hffff40:24'hff6060,color_b=I_pair?24'he080ff:24'h6090ff"
    assert old in s
    s = s.replace(old, "color_a=I_pair?24'h6090ff:24'hff6060,color_b=I_pair?24'he080ff:24'hffff40")
    s = s.replace("4:decoded_glyph=fpair==0?8'd28:8'd35;", "4:decoded_glyph=fpair==0?8'd28:8'd12;")
    s = s.replace("6:decoded_glyph=fpair==0?8'd12:8'd26;", "6:decoded_glyph=fpair==0?8'd35:8'd26;")
    a = s.index(' label_width=j==0?')
    b = s.index(' lx=bx0', a)
    s = s[:a] + " label_width=j==0?(I_pair?56:48):72;\n" + s[b:]
    a = s.index(' case({I_pair,j[0]})')
    b = s.index('\nendcase\n end end end', a) + len('\nendcase')
    labels = ' case({I_pair,j[0]})\n'
    for n, word in enumerate(('RED A2', 'YELLOW B2', 'BLUE A2', 'PURPLE B2')):
        labels += f"2'd{n}:case(lc)\n" + ''.join(
            f"{i}:label_glyph=8'd{CHARS.index(c)};\n" for i, c in enumerate(word)) + 'endcase\n'
    s = s[:a] + labels + 'endcase' + s[b:]
    # Every placement uses the same625-line snapshot as the old formatter.
    # Preserve calibration help, TEACH NEXT/IN/T, failure text and key hints.
    hook = ''' always @*begin
 fps_start=13;fps_row=1;
 if(fm[567:565]!=0)begin fps_start=24;fps_row=0;end
 else if(stage_snapshot_mode==3)fps_start=fps_teach==3?21:fps_teach==2?24:44;
 fps_override=SHOW_FPS && format_row==fps_row &&
 format_col>=fps_start && format_col<fps_start+6 &&
 !(format_row && stage_camera_dead && format_col>=42);
 fps_glyph=0;
 case(format_col-fps_start)
'''
    for i, c in enumerate('FPS000'):
        value = f"8'd{CHARS.index(c)}" if i < 3 else f"8'd1+footer_numbers[{(5-i)*4+32}+:4]"
        hook += f"{i}:fps_glyph={value};\n"
    hook += "default:fps_glyph=0;endcase\n end\n"
    assert ' wire geometry_ready;' in s
    s = s.replace(' wire geometry_ready;', hook + ' wire geometry_ready;', 1)
    old = 'characters[(format_row?COLS:0)+format_col]<='
    assert old in s
    s = s.replace(old, old + 'fps_override?fps_glyph:', 1)
    out['rtl/color_regions/stage1_osd.v'] = s
