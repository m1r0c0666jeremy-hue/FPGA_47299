"""Deterministic display-only pipeline repairs; detector and clocks unchanged."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
T=R/'scripts/templates/stage1_display_timing'

def viewport_source():
    return (T/'viewport.txt').read_text(encoding='utf-8').rstrip()+'\n'

def reader_source():
    p=T/'reader_before.txt'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='6359e2a2bc68e4c5f1c274569522f2fc154b1659e7295769664d24a137f1b9fd'
    s=p.read_text(encoding='utf-8')
    def replace(a,b):
        nonlocal s
        assert s.count(a)==1,a
        s=s.replace(a,b)
    replace(' wire [3:0] hit;stable_model_lane c0(I_ddr_clk,d_rst,pair_rgb[47:24],models,hit[1:0]);',
        ' // One shared 48-bit input register isolates the line-group barrel mux.\n reg [47:0] class_pair_q;\n always @(posedge I_ddr_clk or negedge d_rst)\n if(!d_rst)class_pair_q<=0;else class_pair_q<=pair_rgb;\n wire [3:0] hit;stable_model_lane c0(I_ddr_clk,d_rst,class_pair_q[47:24],models,hit[1:0]);')
    replace('stable_model_lane c1(I_ddr_clk,d_rst,pair_rgb[23:0],models,hit[3:2]);','stable_model_lane c1(I_ddr_clk,d_rst,class_pair_q[23:0],models,hit[3:2]);')
    replace('reg [3:0] vp;reg [10:0] xp[0:3];reg [9:0] yp[0:3];','reg [4:0] vp;reg [10:0] xp[0:4];reg [9:0] yp[0:4];')
    replace('for(j=0;j<4;j=j+1)begin xp[j]<=0;yp[j]<=0;end','for(j=0;j<5;j=j+1)begin xp[j]<=0;yp[j]<=0;end')
    replace('vp<={vp[2:0],state==CLASS};','vp<={vp[3:0],state==CLASS};')
    replace('for(j=1;j<4;j=j+1)begin xp[j]<=xp[j-1];yp[j]<=yp[j-1];end','for(j=1;j<5;j=j+1)begin xp[j]<=xp[j-1];yp[j]<=yp[j-1];end')
    for a,b in [('if(vp[3])begin','if(vp[4])begin'),('if(!xp[3][1])half_mask<=hit;','if(!xp[4][1])half_mask<=hit;'),('filter_x<=xp[3]-2;filter_y<=yp[3];','filter_x<=xp[4]-2;filter_y<=yp[4];'),('(job_y==0 && close_wait>=12)','(job_y==0 && close_wait>=13)')]:
        replace(a,b)
    return s

def assets():
    return {'rtl/color_regions/refined_overlay_geometry.v':(T/'overlay.txt').read_text(encoding='utf-8'),
            'rtl/color_regions/refined_line_reader.v':reader_source()}

def decorate(out):
    s=out['rtl/color_regions/stage1_memory_video_out.v']
    needle='    stage1_viewport #(.V4(1)) u_viewport('
    assert s.count(needle)==1
    s=s.replace(needle,'''    reg [1:0] viewport_ui_last;
    always @(posedge I_pixel_clk or negedge I_process_rst_n)
    if(!I_process_rst_n)viewport_ui_last<=0;else viewport_ui_last<=I_ui_mode;
    wire viewport_abort=I_key_cancel || I_key4 || !I_camera_ready || I_gain_busy || I_ui_mode!=viewport_ui_last;
'''+needle)
    needle='.I_point(teach_desired_point),.O_point(teach_active_point));'
    assert s.count(needle)==1
    s=s.replace(needle,'.I_point(teach_desired_point),.O_point(teach_active_point),.I_abort(viewport_abort));')
    out['rtl/color_regions/stage1_memory_video_out.v']=s
