"""Small stable-release additions; no native camera or buffer changes."""
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'

def runtime_source():
    return r'''
// Pixel-domain telemetry. Input sample means an actual valid video pixel.
module stage1_runtime_stats(input wire clk,rst_n,input wire [31:0] now_us,
 input wire sample,input wire [31:0] image_id,input wire [15:0] epoch,
 input wire [17:0] camera,input wire [127:0] ddr_diag,pixel_diag,
 input wire [38:0] recovery,input wire lane_async,
 output reg [7:0] fps,fault,output wire lane_seen);
 reg started,seen;reg [31:0] window_start,last_id;reg [15:0] last_epoch;
 reg [7:0] count;reg [15:0] old_recoveries,old_underflow,old_unexpected;
 reg [11:0] old_timeout;reg [3:0] old_camera;
 (* async_reg="true" *)reg [2:0] lane_sync;
 assign lane_seen=lane_sync[2];
 wire fresh=sample && (!seen || epoch!=last_epoch || $signed(image_id-last_id)>0);
 wire [31:0] elapsed=now_us-window_start;
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin started<=0;seen<=0;window_start<=0;last_id<=0;last_epoch<=0;
 count<=0;fps<=0;fault<=0;old_recoveries<=0;old_underflow<=0;old_unexpected<=0;old_timeout<=0;old_camera<=0;lane_sync<=0;end
 else begin
 lane_sync<={lane_sync[1:0],lane_async};
 if(!started)begin started<=1;window_start<=now_us;count<=fresh?1:0;end
 else if(elapsed>=1000000)begin
 // A sample exactly at a window boundary belongs to the next window.
 fps<=elapsed>=2000000?0:count;window_start<=now_us;count<=fresh?1:0;
 end else if(fresh && count!=255)count<=count+1'b1;
 if(fresh)begin seen<=1;last_id<=image_id;last_epoch<=epoch;end
 old_camera<=camera[12:9];old_recoveries<=recovery[31:16];
 old_timeout<=ddr_diag[87:76];old_unexpected<=ddr_diag[119:104];old_underflow<=pixel_diag[19:4];
 // Codes are domain-prefixed hexadecimal, retained after recovery.
 if(pixel_diag[19:4]!=old_underflow)fault<={4'h4,pixel_diag[3:0]};
 if(ddr_diag[119:104]!=old_unexpected)fault<=8'h31;
 if(ddr_diag[87:76]!=old_timeout)fault<={4'h3,ddr_diag[75:72]};
 if(recovery[31:16]!=old_recoveries || recovery[38])fault<={4'h2,recovery[37:34]};
 if(camera[12:9]!=0 && camera[12:9]!=old_camera)fault<={4'h1,camera[12:9]};
 end end
endmodule
'''

def decorate(out):
    top=out['rtl/color_regions/stage1_top.v']
    top=top.replace('stable_camera_capture #', 'wire lane_seen_async;\nstable_camera_capture #',1)
    top=top.replace('.O_status_async(camera_status_async)', '.O_lane_seen(lane_seen_async),.O_status_async(camera_status_async)',1)
    top=top.replace('.I_camera_status(camera_ui_status)', '.I_camera_status(camera_ui_status),.I_lane_seen(lane_seen_async)',1)
    out['rtl/color_regions/stage1_top.v']=top
    video=out['rtl/color_regions/stage1_memory_video_out.v']
    video=video.replace('input wire [31:0] I_source_id', 'input wire I_lane_seen,input wire [31:0] I_source_id',1)
    hook='''wire [7:0] runtime_fps,runtime_fault;wire runtime_lane;
    stage1_runtime_stats runtime_stats(I_pixel_clk,I_process_rst_n,I_board_us,
     S_hdmi_out_de && video_ok && image_time_valid,selected_frame_id,image_epoch,
     I_camera_status,ddr_ui,pixel_diagnostics,recovery_ui,I_lane_seen,runtime_fps,runtime_fault,runtime_lane);
    stage1_osd #(.RUNTIME_INFO(1)) u_osd ('''
    assert 'stage1_osd u_osd (' in video
    video=video.replace('stage1_osd u_osd (',hook,1)
    video=video.replace('.I_ddr_diag(ddr_ui)', '.I_fps(runtime_fps),.I_fault(runtime_fault),.I_lane_seen(runtime_lane),.I_ddr_diag(ddr_ui)',1)
    video+=runtime_source()
    out['rtl/color_regions/stage1_memory_video_out.v']=video
    s=out['rtl/color_regions/stage1_osd.v']
    s=s.replace('module stage1_osd(', 'module stage1_osd #(parameter RUNTIME_INFO=0)(',1)
    s=s.replace('input wire I_k_adjust\n', 'input wire I_k_adjust,input wire [7:0] I_fps,I_fault,input wire I_lane_seen\n',1)
    # Same shared converter, reusing the former AGE field, no extra divider.
    s=s.replace('I_latency_us,I_frame_age,I_area_dwell', "I_latency_us,(RUNTIME_INFO?{24'd0,I_fps}:I_frame_age),I_area_dwell",1)
    s=s.replace('reg flat_valid;', 'reg runtime_override;reg [1:0] fruntime_teach;reg [7:0] runtime_glyph;reg [7:0] ffault;reg [15:0] frecoveries;reg flane;\n reg flat_valid;',1)
    s=s.replace('flat_valid<=0;flatency<=0;fage<=0;', 'fruntime_teach<=0;ffault<=0;frecoveries<=0;flane<=0;flat_valid<=0;flatency<=0;fage<=0;',1)
    s=s.replace('flat_valid<=I_latency_valid;', 'fruntime_teach<=I_teaching[55:54];ffault<=I_fault;frecoveries<=I_recovery[31:16];flane<=I_lane_seen;flat_valid<=I_latency_valid;',1)
    # All text is frozen together. Live safety logic is outside the OSD.
    start=s.index(' wire footer_current=');end=s.index('\n',start)
    s=s[:start]+' wire footer_current=footer_ready;'+s[end:]
    s=s.replace("color_a=I_pair?24'hffff40:24'hff6060,color_b=I_pair?24'he080ff:24'h6090ff", "color_a=I_pair?24'h6090ff:24'hff6060,color_b=I_pair?24'he080ff:24'hffff40")
    s=s.replace("4:decoded_glyph=fpair==0?8'd28:8'd35;", "4:decoded_glyph=fpair==0?8'd28:8'd12;")
    s=s.replace("6:decoded_glyph=fpair==0?8'd12:8'd26;", "6:decoded_glyph=fpair==0?8'd35:8'd26;")
    a=s.index(' label_width=j==0?');b=s.index(' lx=bx0',a)
    s=s[:a]+" label_width=j==0?(I_pair?56:48):(I_pair?72:72);\n"+s[b:]
    a=s.index(' case({I_pair,j[0]})');b=s.index('\nendcase\n end end end',a)+len('\nendcase')
    labels=' case({I_pair,j[0]})\n'
    for n,word in enumerate(('RED A2','YELLOW B2','BLUE A2','PURPLE B2')):
        labels+=f"2'd{n}:case(lc)\n"+''.join(f"{i}:label_glyph=8'd{CHARS.index(c)};\n" for i,c in enumerate(word))+'endcase\n'
    s=s[:a]+labels+'endcase'+s[b:]
    # Keep every calibration instruction, TEACH IN/dwell/result and key label.
    def full(start,end):
        text='FPS000 E00 R0000 L0'
        lines=[]
        for i,c in enumerate(text):
            v=f"8'd{CHARS.index(c)}"
            if 3<=i<=5:v=f"8'd1+footer_numbers[{(5-i)*4+32}+:4]"
            if i in (8,9):v=f"8'd1+ffault[{(9-i)*4}+:4]"
            if 12<=i<=15:v=f"8'd1+frecoveries[{(15-i)*4}+:4]"
            if i==18:v="flane?8'd2:8'd1"
            lines.append(f"{start+i}:runtime_glyph={v};")
        return f"begin runtime_override=format_col>={start} && format_col<{end};case(format_col)\n"+'\n'.join(lines)+"\n default:runtime_glyph=0;endcase end\n"
    def compact(start):
        lines=[]
        for i,c in enumerate('FPS000L0'):
            v=f"8'd{CHARS.index(c)}"
            if 3<=i<=5:v=f"8'd1+footer_numbers[{(5-i)*4+32}+:4]"
            if i==7:v="flane?8'd2:8'd1"
            lines.append(f"{start+i}:begin runtime_override=1;runtime_glyph={v};end")
        return 'case(format_col)\n'+'\n'.join(lines)+'\n default:begin end endcase\n'
    hook=" always @*begin runtime_override=0;runtime_glyph=0;\n"
    hook+="if(fm[567:565]!=0)begin if(!format_row)"+full(24,64)+"end\n"
    hook+="else if(stage_snapshot_mode!=3)begin if(format_row)"+full(13,42)+"end\n"
    hook+="else if(format_row)begin\nif(fruntime_teach==3)begin\n"+compact(21)
    hook+="case(format_col)38:begin runtime_override=1;runtime_glyph=8'd15;end\n39:begin runtime_override=1;runtime_glyph=8'd1+ffault[7:4];end\n40:begin runtime_override=1;runtime_glyph=8'd1+ffault[3:0];end\n42:begin runtime_override=1;runtime_glyph=8'd28;end\n"
    for j in range(4):hook+=f"{43+j}:begin runtime_override=1;runtime_glyph=8'd1+frecoveries[{(3-j)*4}+:4];end\n"
    hook+="default:begin end endcase\nend else if(fruntime_teach==2)begin\n"+compact(24)+"end else "+full(44,63)+"end\nend\n"
    s=s.replace(' wire geometry_ready;',hook+' wire geometry_ready;',1)
    old='characters[(format_row?COLS:0)+format_col]<='
    assert old in s
    # Terminal camera faults always outrank telemetry. No runtime selection uses
    # live mode/teaching inputs: these are part of the same625-line snapshot.
    s=s.replace(old,old+'RUNTIME_INFO && runtime_override && !(format_row && stage_camera_dead && format_col>=42)?runtime_glyph:',1)
    out['rtl/color_regions/stage1_osd.v']=s
