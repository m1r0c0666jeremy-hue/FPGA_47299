"""Add an explicit SOF identity sideband; preserve original vendor arithmetic."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
def isp_assets():
    out={}
    for name in ('demosaic','raw_matrix_3x3_buffer','zhenghe'):
        data=(R/f'user_source/hdl_source/isp/demosaic_4x_2_0/{name}.v').read_bytes()
        try:s=data.decode('utf-8')
        except UnicodeDecodeError:s=data.decode('gb18030')
        s=s.replace('\r\n','\n')
        # Two vendor separator comments have an unclosed /* before the next
        # port comment. Drop only those separators for standard Verilog parsers.
        s=re.sub(r'^\s*/\*//(?:input|output)\s*$', '',s,flags=re.M)
        for module in ('demosaic','raw_matrix_3x3_buffer','zhenghe'):
            s=re.sub(r'\b'+module+r'(?=\s*#)', 'refined_'+module,s)
        if name=='zhenghe':
            s=s.replace('input                   I_clk', 'input [32:0] I_frame_tag, output reg [32:0] O_frame_tag,\n    input                   I_clk',1)
            s=s.replace('endmodule','reg [32:0] frame_tag;\nalways @(posedge I_clk or negedge I_rst_n)\nif(!I_rst_n)begin frame_tag<=0;O_frame_tag<=0;end\nelse begin if(I_tuser)frame_tag<=I_frame_tag;O_frame_tag<=frame_tag;end\nendmodule')
        else:
            s=s.replace('input           I_clk', 'input [32:0] I_frame_tag,output wire [32:0] O_frame_tag,\n    input           I_clk',1)
            if name=='raw_matrix_3x3_buffer':
                s=s.replace('zhenghe_d(', 'zhenghe_d(.I_frame_tag(converter_tag),.O_frame_tag(zhenghe_tag),')
                extra='''reg [32:0] converter_tag;wire [32:0] zhenghe_tag;
reg [32:0] tag0,tag1,tag2;
always @(posedge I_clk or negedge I_rst_n)
if(!I_rst_n)begin converter_tag<=0;tag0<=0;tag1<=0;tag2<=0;end
else begin if(axi4s_video_tuser)converter_tag<=I_frame_tag;
tag0<=zhenghe_tag;tag1<=tag0;tag2<=tag1;end
assign O_frame_tag=tag2;
'''
            else:
                s=s.replace('wire demosaic_tlast', 'wire [32:0] matrix_tag;\nwire demosaic_tlast',1)
                s=s.replace(')raw_matrix_3x3_buffer_d\n(', ')raw_matrix_3x3_buffer_d\n(.I_frame_tag(I_frame_tag),.O_frame_tag(matrix_tag),')
                extra='''reg [32:0] tags[0:4];integer ti;
always @(posedge I_clk or negedge I_rst_n)
if(!I_rst_n)for(ti=0;ti<5;ti=ti+1)tags[ti]<=0;
else begin tags[0]<=matrix_tag;for(ti=1;ti<5;ti=ti+1)tags[ti]<=tags[ti-1];end
assign O_frame_tag=tags[4];
'''
            anchor='mipi_to_raw_converter mipi_to_raw_converter_r0(' if name=='raw_matrix_3x3_buffer' else 'bilinear_interpolation #('
            s=s.replace(anchor,extra+anchor,1)
        assert 'input [32:0] I_frame_tag' in s,name
        out[f'rtl/color_regions/refined_{name}.v']=s
    return out
