from pathlib import Path
import sys,re
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
s=(R/'rtl/color_regions/stage1_render.v').read_text()
def replace(a,b):
    global s
    assert a in s,a[:100]
    s=s.replace(a,b)
replace('MAP_FINISH=16;','MAP_FINISH=16,CLEAR=17,STAMP_READ=18,STAMP_WRITE=19,NEXT_EDGE=20;')
replace('reg [31:0] line_mem[0:319];','reg [31:0] line_mem[0:1279];')
replace('reg [1:0] bank_valid;reg [9:0] bank_row[0:1];','reg [7:0] bank_valid;reg [9:0] bank_row[0:7];')
replace('reg [9:0] row;reg [7:0] word_index;reg [1:0] region_phase;reg [31:0] pending;',
        'reg [9:0] row;reg [7:0] word_index;reg [31:0] stamp_q;reg [10:0] stamp_lo,stamp_hi;reg stamp_valid;')
replace('reg [10:0] span_lo[0:31],span_hi[0:31];reg [31:0] span_valid;',
        'wire [10:0] span_lo[0:31],span_hi[0:31];wire [31:0] span_valid=0;')
start=s.index(' reg [7:0] nibble;');end=s.index(' always @(posedge clk)begin',start)
s=s[:start]+''' reg [2:0] left_bit,right_bit;reg [7:0] edge_bits;reg [31:0] stamp_mask;
 wire [10:0] read_address=y[2:0]*11'd160+{3'd0,x[10:3]};
 wire [10:0] write_address=row[2:0]*11'd160+{3'd0,word_index};
'''+s[end:]
replace(' if(state==GEN && region_phase==3)line_mem[write_address]<=generated_word;',
''' stamp_q<=line_mem[write_address];
 if(state==CLEAR)line_mem[write_address]<=0;
 else if(state==STAMP_WRITE)line_mem[write_address]<=stamp_q|stamp_mask;''')
replace('bank_valid[y[0]]','bank_valid[y[2:0]]');replace('bank_row[y[0]]','bank_row[y[2:0]]')
start=s.index(' always @*begin nibble=');end=s.index(' integer label_index;',start)
s=s[:start]+''' always @*begin
 left_bit=word_index==stamp_lo[10:3]?stamp_lo[2:0]:3'd0;
 right_bit=word_index==stamp_hi[10:3]?stamp_hi[2:0]:3'd7;
 edge_bits=(8'hff<<left_bit)&(8'hff>>(7-right_bit));stamp_mask=0;
 for(k=0;k<8;k=k+1)if(edge_bits[k])stamp_mask[k*4+:4]=4'b0001<<edge_id[4:3];
 end
'''+s[end:]
replace('bank_valid<=0;bank_row[0]<=0;bank_row[1]<=0;row<=0;word_index<=0;region_phase<=0;pending<=0;span_valid<=0;',
        'bank_valid<=0;row<=0;word_index<=0;stamp_lo<=0;stamp_hi<=0;stamp_valid<=0;')
replace('if(write_is_row)begin if(edge_id==31)begin word_index<=0;region_phase<=0;state<=GEN;end\n else begin edge_id<=edge_id+1\'b1;state<=READ_EDGE;end end',
        'if(write_is_row)state<=stamp_valid?STAMP_READ:NEXT_EDGE;')
replace('ROW_BEGIN:begin edge_id<=0;field<=0;span_valid<=0;bank_valid[row[0]]<=0;state<=READ_EDGE;end',
'''ROW_BEGIN:begin edge_id<=0;field<=0;word_index<=0;bank_valid[row[2:0]]<=0;state<=CLEAR;end
 CLEAR:if(word_index==159)begin word_index<=0;state<=READ_EDGE;end else word_index<=word_index+1'b1;''')
replace('span_valid[edge_id]<=span_ok;span_lo[edge_id]<=lo_pixel<0?0:lo_pixel[10:0];span_hi[edge_id]<=hi_pixel>1279?1279:hi_pixel[10:0];',
'''stamp_valid<=span_ok;stamp_lo<=lo_pixel<0?0:lo_pixel[10:0];stamp_hi<=hi_pixel>1279?1279:hi_pixel[10:0];
 word_index<=lo_pixel<0?0:lo_pixel[10:3];''')
start=s.index(' GEN:begin');end=s.index(' default:begin end',start)
s=s[:start]+''' STAMP_READ:state<=STAMP_WRITE;
 STAMP_WRITE:if(word_index==stamp_hi[10:3])state<=NEXT_EDGE;
 else begin word_index<=word_index+1'b1;state<=STAMP_READ;end
 NEXT_EDGE:if(edge_id==31)begin bank_valid[row[2:0]]<=1;bank_row[row[2:0]]<=row;ready<=1;state<=WAIT_ROW;end
 else begin edge_id<=edge_id+1'b1;state<=READ_EDGE;end
 WAIT_ROW:if(row<623 && (row<7 || {1'b0,y}+11'd6>={1'b0,row}))begin row<=row+1'b1;state<=ROW_BEGIN;end
'''+s[end:]
p=O/'stage1_render.v';p.write_text(s)
source=(R/'build/sim/refined/stage1_render_14_624_20261021_104617_468979/tb.sv').read_text()
run('private_stage1_stamp_render',source,[R/'rtl/color_regions/stage1_arith.v',p],timeout=1800)
source=(R/'build/sim/refined/stage1_overlay_20261021_105321_795816/tb.sv').read_text()
mods=[R/'rtl/color_regions'/f'{n}.v' for n in ('stage1_osd','stage1_arith','stage1_ui_formatter','stage1_ui_text','refined_english_font_rom','refined_english_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
run('private_stage1_stamp_overlay',source,mods+[p],timeout=1800)
