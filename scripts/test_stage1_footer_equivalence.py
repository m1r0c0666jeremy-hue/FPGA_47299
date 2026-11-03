"""Compare every cached footer glyph against frozen pre-sharing production RTL."""
from refined_testlib import R,run
from stage1_test_sources import OSD_ZERO_NAMED,EXTRA_OSD
import re,hashlib

bindings=dict(re.findall(r'\.(\w+)\(([^)]+)\)',OSD_ZERO_NAMED))
bindings.update(I_ui_mode='mode',I_run_state='state',I_area_count='n',I_draft_count='draft',I_occupied='occupied',
 I_expected_area='expected',I_actual_area='actual',I_edit_error='edit_error',I_start_error='start_error',
 I_area_dwell='dwell',I_gain_busy='gb',I_gain_failed='gf',I_gain_target='target',I_tip_reason='reason',
 I_teaching='teaching',I_k_value='k',I_k_adjust='kp',I_area_muted='muted',I_tip_live='tip',
 I_region_draft="168'd0",I_clk='clk',I_rst_n='rst',I_vs="1'b0",I_hs="1'b0",I_de='de',I_rgb="24'd0",
 I_meta='meta',I_x0="11'd0",I_y0="10'd0",I_zoom='zoom',I_mode='process_mode',I_state='video_state',
 I_tracking='tracking',I_show='show',I_video_ok='video_ok',I_pair='pair',I_detection_valid='detection',I_sample_valid='sample',
 I_rotate='rotate',I_diag="2'd0",I_image_id='image_id',I_geometry_commit="1'b0",I_latency_valid='lv',
 I_latency_us='latency',I_frame_age='age',I_ddr_diag="128'd0",I_pixel_diag="128'd0",I_recovery="39'd0",I_camera='camera')
ports=','.join('.'+n+'('+v+')' for n,v in bindings.items())
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0;reg [1:0] mode,process_mode;
reg [3:0] state,draft,occupied,edit_error,start_error,reason;reg [2:0] n,expected,actual,zoom,video_state;
reg [19:0] dwell;reg [6:0] target;reg [7:0] k;reg [79:0] teaching;reg [767:0] meta;
reg gb,gf,kp,muted,tip,tracking,show,video_ok,pair,detection,sample,rotate,lv;
reg [31:0] image_id,latency,age;reg [17:0] camera;
stage1_osd dut(PORTS);
reference_stage1_osd original(PORTS);
integer c,j,cycles;reg [31:0] seed=32'h1256abef;
function [31:0] rand32;input unused;begin seed=seed^(seed<<13);seed=seed^(seed>>17);seed=seed^(seed<<5);rand32=seed;end endfunction
task inputs_next;begin
mode=rand32(0);process_mode=rand32(0);state=rand32(0)%8;n=rand32(0)%5;draft=rand32(0)%3;
occupied=rand32(0);expected=rand32(0)%4;actual=rand32(0)%5;edit_error=rand32(0)%10;start_error=rand32(0)%4;
dwell=rand32(0);target=rand32(0)%106;k=rand32(0)%201;teaching={rand32(0),rand32(0),rand32(0)};
teaching[3:0]=rand32(0)%9;reason=rand32(0);gb=rand32(0);gf=rand32(0);kp=rand32(0);muted=rand32(0);tip=rand32(0);
meta=0;meta[36:33]=rand32(0)%9;meta[247]=1;meta[255]=1;meta[568]=rand32(0);meta[722:721]=rand32(0);
meta[567:565]=c%7==0?(c%4)+1:0;meta[564]=c%11==0;meta[563:560]=c%13==0?c%13:0;
meta[559:544]=rand32(0);meta[415:413]=4;
zoom=c%5;video_state=c%8;tracking=rand32(0);show=rand32(0);video_ok=rand32(0);pair=rand32(0);
detection=rand32(0);sample=rand32(0);rotate=rand32(0);image_id=rand32(0);lv=rand32(0);
case(c%8)0:latency=0;1:latency=9999999;2:latency=10000000;3:latency=32'hffffffff;default:latency=rand32(0)%11000000;endcase
age=c%4==0?32'hffffffff:rand32(0)%1100;camera={1'b1,4'd7,4'd0,2'd0,7'(rand32(0)%106)};
if(c%9==0)camera={1'b0,4'd9,4'(1+c%5),2'd3,7'd90};
end endtask
initial begin inputs_next;repeat(3)@(negedge clk);rst=1;
for(c=0;c<256;c=c+1)begin
 @(negedge clk);inputs_next;dut.y=625;dut.x=0;original.y=625;original.x=0;de=1;
 @(negedge clk);de=0;
 // All live inputs change while both frame snapshots must stay immutable.
 inputs_next;
 if(c%7==0)begin
 repeat(40)@(negedge clk);inputs_next;dut.y=625;dut.x=0;original.y=625;original.x=0;de=1;
 @(negedge clk);de=0;inputs_next;end
 if(c%11==0)begin
 repeat(20)@(negedge clk);rst=0;repeat(3)@(negedge clk);rst=1;
 inputs_next;dut.y=625;dut.x=0;original.y=625;original.x=0;de=1;
 @(negedge clk);de=0;inputs_next;end
 repeat(1500)@(negedge clk);
 if(!dut.footer_ready || !original.footer_ready)$fatal(1,"footer completion deadline case%0d",c);
 for(j=0;j<128;j=j+1)if(dut.characters[j]!==original.characters[j])
 $fatal(1,"footer equivalence case%0d char%0d new%0d old%0d",c,j,dut.characters[j],original.characters[j]);
end
$display("STAGE1_FOOTER_EQUIVALENCE_PASS cases=256 glyphs=32768 snapshot/overlap/reset/deadline/all-modes/numeric-boundaries");$finish;
end endmodule'''.replace('PORTS',ports)
task=R/(R/'build/current_display_shared_path.txt').read_text(encoding='utf-8')
for name,h in {'stage1_osd':'7e7e18c38fc0f5a3d31a3e54d525cb1e596e037bba6cccd7ca732c7f09e0b9b4',
 'stage1_ui_formatter':'7affae560756f399df515dc5139d0cf3ffe105211e8533f067e1c3aeb82ac62f',
 'stage1_render':'7f442aad1036d8b863c11411cd5509c63f0ceb1f2632af1997569e2600daca99'}.items():
 assert hashlib.sha256((task/'reference'/f'{name}.v').read_bytes()).hexdigest()==h
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]+EXTRA_OSD
mods += [task/'reference'/f'{n}.v' for n in ('stage1_osd','stage1_ui_formatter','stage1_render')]
run('stage1_footer_equivalence',src,mods,timeout=300)
