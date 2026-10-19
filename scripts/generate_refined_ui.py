"""Compact upright footer/labels using the tracked official Anlogic symbol."""
from pathlib import Path
import hashlib,json,math
import re
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
STATES=['待命','中央选取','确认中','跟踪中','缺色','失锁保持','中央重选','尖端越界','无效帧',
        '白纸校准','空背景校准','A色校准','B色校准','采样处理中','采样失败','请重新校准','视频未就绪','按键冲突','无新帧','等待结果']
ERRORS=['','无效采集帧','白纸质量不足','增益超范围','混色或采样不足','模型重叠','背景不可分','材料保留不足','采样窗暗部过多','亮度改变','中性弱色差过多','主色相不匹配','有效样本不足']
HELP=['','中央白纸 KEY3采样 KEY2取消','移走双色标记 绿框对准误检物 KEY3采样 KEY2取消',
      'A近尖端色对准中央 KEY3采样 KEY2取消','B后方色对准中央 KEY3采样 KEY2取消']
MODEL_STATES=['默认参数','材料已学习','需要更新']
MODES=['原图','色彩高亮','灰度','色彩二值']
LABELS=' 红蓝黄紫色AB1'
BUSY='8帧采样或串行回放 请保持画面 KEY2取消'
RETRY=' KEY3重采 KEY2取消'
def ui_assets():
    from refined_compact_osd_logic import compact_osd_asset
    chars=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms'+''.join(dict.fromkeys(''.join(STATES+ERRORS+HELP+MODES+MODEL_STATES)+LABELS+BUSY+RETRY+'校准状态:RGB/.-%>() 板内延迟落后帧恢复行等待故障源坐标拍收'))
    chars=''.join(dict.fromkeys(chars));assert len(chars)<=256,('footer glyphs',len(chars))
    ids={c:i for i,c in enumerate(chars)}
    def literal(t):return [f"8'd{ids[c]}" for c in t]
    def number(i,n,valid='fm[604]'):
        if i in (24,25):i-=24
        return [f"({valid})?(8'd1+numbers[{i}][{4*(n-1-k)}+:4]):8'd{ids['-']}" for k in range(n)]
    def hx(expr,n,valid="1'b1"):
        return [f"({valid})?(8'd1+({expr}>>{4*(n-1-k)} & 4'hf)):8'd{ids['-']}" for k in range(n)]
    def field(expr,valid='fm[604]'):return [f"({valid})?(8'd1+{expr}):8'd{ids['-']}"]
    def fn(name,texts,width):
        out=f'function [7:0] {name};input [4:0] id;input [5:0] pos;begin {name}=0;case(id)\n'
        for i,t in enumerate(texts):
            if not t:continue
            out+=f'{i}:case(pos)\n'+''.join(f"{j}:{name}=8'd{ids[c]};\n" for j,c in enumerate(t))+ 'endcase\n'
        return out+'endcase end endfunction\n'
    valid='fm[255] && fm[415:413]==4'
    overview0=[f'mode_char(fmode,{i})' for i in range(4)]+literal(' ')+["fzoom==1?8'd2:fzoom==2?8'd3:fzoom==3?8'd4:fzoom==4?8'd5:8'd2",f"fzoom==1?8'd{ids['.']}:8'd{ids['X']}","fzoom==1?8'd6:8'd0",f"fzoom==1?8'd{ids['X']}:8'd0"]+literal(' ')+[f"fpair?8'd{ids['黄']}:8'd{ids['红']}",f"fpair?8'd{ids['紫']}:8'd{ids['蓝']}"]+literal(' ')+[f"frotate?8'd{ids[c]}:8'd{ids[d]}" for c,d in zip('180','000')]+literal(' 状态:')+[f'status_char(status_id,{i})' for i in range(8)]+literal(' ')+[f'model_char(model_id,{i})' for i in range(5)]
    latency_ok='flat_valid && flatency<10000000'
    ms=number(24,7,latency_ok)
    overview1=literal('板内延迟 ')+ms[:4]+literal('.')+ms[4:5]+literal('ms 落后 ')+number(25,3,'flat_valid && fage<1000')+literal('帧 F:')+hx('fimage',8)+literal(' V:')+hx('fm[559:544]',4,valid)
    cal0=literal('校准:')+[f'status_char(status_id,{i})' for i in range(9)]+literal(' E')+hx('fm[563:560]',2,valid)+literal(' F:')+hx('fimage',8)+literal(' V:')+hx('fm[559:544]',4,valid)
    # One visible view; retain the calibration overlay and detailed retry text.
    # Numeric/parameter/performance pages no longer enter the display program.
    lines=[overview0,overview1,cal0]
    longest=max(max(map(len,lines)),len(BUSY),max(len(e+RETRY) for e in ERRORS),max(map(len,HELP)))
    # Preserve the initial overview's 16px appearance while reducing storage.
    # Enlarging its glyph ROM would consume the memory saved by page removal.
    size=16;columns=64
    assert longest*size<=1120
    def cases(name,tokens):return 'case(col)\n'+''.join(f'{i}:{name}={expr};\n' for i,expr in enumerate(tokens))+'endcase\n'
    # A serial display program replaces a large combinational text/field mux.
    # One token addresses one glyph. It never runs in the per-pixel shader.
    templates=lines+[literal(t) for t in HELP[1:]]+[literal(BUSY)]+[literal(e+RETRY) for e in ERRORS]
    validity=["1'b1"];hex_fields=[];small_fields=[];dynamic=[];program=[0]*2048
    def idx(values,v):
        if v not in values:values.append(v)
        return values.index(v)
    def token(expr):
        m=re.fullmatch(r"8'd(\d+)",expr)
        if m:return int(m[1])
        m=re.fullmatch(r"\((.+)\)\?\(8'd1\+numbers\[(\d+)\]\[(\d+)\+:4\]\):8'd\d+",expr)
        if m:return (1<<13)|(int(m[2])<<8)|(idx(validity,m[1])<<4)|(int(m[3])//4)
        m=re.fullmatch(r"\((.+)\)\?\(8'd1\+\((.+)>>([0-9]+) & 4'hf\)\):8'd\d+",expr)
        if m:return (2<<13)|(idx(hex_fields,m[2])<<8)|(idx(validity,m[1])<<4)|(int(m[3])//4)
        m=re.fullmatch(r"(mode|status|model)_char\(.+,(\d+)\)",expr)
        if m:return (5<<13)|({'mode':0,'status':1,'model':2}[m[1]]<<8)|int(m[2])
        m=re.fullmatch(r"\((.+)\)\?\(8'd1\+(.+)\):8'd\d+",expr)
        if m:return (4<<13)|(idx(small_fields,m[2])<<8)|(idx(validity,m[1])<<4)
        return (3<<13)|(idx(dynamic,expr)<<8)
    for row,tokens in enumerate(templates):
        assert len(tokens)<=columns
        for col,t in enumerate(tokens):program[row*64+col]=token(t)
    dynamic_text=[0]*512
    for i,t in enumerate(MODES):
        for j,c in enumerate(t):dynamic_text[i*4+j]=ids[c]
    for i,t in enumerate(STATES):
        for j,c in enumerate(t):dynamic_text[64+i*16+j]=ids[c]
    for i,t in enumerate(MODEL_STATES):
        for j,c in enumerate(t):dynamic_text[384+i*8+j]=ids[c]
    functions='''reg [4:0] template_index;reg token_valid;reg [31:0] hex_value;reg [7:0] decoded_glyph;
wire [15:0] token_data;wire [7:0] dynamic_glyph;
wire [10:0] program_addr={template_index,format_col};
wire [8:0] dynamic_addr=token_data[12:8]==0?({7'd0,fmode}<<2)+{5'd0,token_data[3:0]}:
token_data[12:8]==1?9'd64+({4'd0,status_id}<<4)+{5'd0,token_data[3:0]}:
9'd384+({7'd0,model_id}<<3)+{5'd0,token_data[2:0]};
stable_footer_program_rom program_rom(I_clk,program_addr,token_data);
stable_footer_text_rom text_rom(I_clk,dynamic_addr,dynamic_glyph);
always @*begin
template_index={4'd0,format_row};
if(fm[567:565]!=0)begin
if(!format_row)template_index=2;
else if(fm[563:560]!=0)template_index=8+{1'b0,fm[563:560]};
else if(fm[564])template_index=7;
else template_index=2+{2'd0,fm[567:565]};end
token_valid=1;case(token_data[7:4])
'''+''.join(f'{i}:token_valid={v};\n' for i,v in enumerate(validity))+'''default:token_valid=0;endcase
hex_value=0;case(token_data[12:8])
'''+''.join(f'{i}:hex_value={v};\n' for i,v in enumerate(hex_fields))+'''endcase
decoded_glyph=0;case(token_data[15:13])
0:decoded_glyph=token_data[7:0];
1:decoded_glyph=token_valid?8'd1+number_digit_q:8'd'''+str(ids['-'])+''';
2:decoded_glyph=token_valid?8'd1+hex_digit_q:8'd'''+str(ids['-'])+''';
3:case(token_data[12:8])
'''+''.join(f'{i}:decoded_glyph={v};\n' for i,v in enumerate(dynamic))+'''endcase
4:begin if(!token_valid)decoded_glyph=8'd'''+str(ids['-'])+''';else case(token_data[12:8])
'''+''.join(f"{i}:decoded_glyph=8'd1+{v};\n" for i,v in enumerate(small_fields))+'''default:decoded_glyph=0;endcase end
5:decoded_glyph=dynamic_glyph;
endcase end
'''
    s=(R/'scripts/refined_osd.v.txt').read_text(encoding='utf-8')
    for key,value in {'@FONT@':str(size),'@COLUMNS@':str(columns),'@FUNCTIONS@':functions,
                      '@WAIT_GLYPHS@':','.join(f"8'd{ids[c]}" for c in '等待结果'),
                      '@FADDR@':f'(footer_glyph<<{int(math.log2(size))})+footer_gy' if size in (16,32) else '(footer_glyph<<4)+(footer_glyph<<3)+footer_gy'}.items():s=s.replace(key,value)
    s=compact_osd_asset(s)
    out={'rtl/color_regions/stable_osd.v':s}
    # Keep the historical ROM intact. Palette 0 is transparent; palette 3 is
    # an exterior one-pixel outline, never substituted for original colours.
    original=[0]*8192
    for addr,value in re.findall(r"mem\[(\d+)\]=2'h([0-9a-f]);",(R/'rtl/09_osd_ui/scaling_logo_rom.v').read_text()):
        original[int(addr)]=int(value,16)
    pixels=[0]*8192
    for yy in range(64):
        for xx in range(98):
            def colour(x,y):return original[y*96+x] if 0<=x<96 and 0<=y<62 else 0
            value=colour(xx-1,yy-1)
            if not value and any(colour(xx-1+dx,yy-1+dy) for dx in (-1,0,1) for dy in (-1,0,1)):value=3
            pixels[yy*98+xx]=value
    out['rtl/color_regions/refined_logo_rom.v']='module refined_logo_rom(input wire clk,input wire [12:0] addr,output reg [1:0] q);\n(* ram_style="block" *) reg [1:0] mem[0:8191];\ninitial begin\n'+''.join(f"mem[{i}]=2'h{v:x};\n" for i,v in enumerate(pixels))+'end\nalways @(posedge clk)q<=mem[addr];\nendmodule\n'
    def data_rom(name,width,rows):
        depth=len(rows);addr=(depth-1).bit_length()
        return f'module {name}(input wire clk,input wire [{addr-1}:0] addr,output reg [{width-1}:0] q);\n(* syn_preserve=1 *) reg [{addr-1}:0] registered_addr;\n(* rom_style="bram" *) reg [{width-1}:0] mem[0:{depth-1}];\ninitial begin\n'+''.join(f"mem[{i}]={width}'h{v:x};\n" for i,v in enumerate(rows))+'end\nalways @(posedge clk)begin registered_addr<=addr;q<=mem[registered_addr];end\nendmodule\n'
    out['rtl/color_regions/stable_footer_program_rom.v']=data_rom('stable_footer_program_rom',16,program)
    # Historical resource experiment: "block" falls back to AUTO in TD.
    # SWUG106 section 4.2.6 specifies "bram"; verify actual mapping before
    # claiming a memory saving. Keep the current compiled candidate frozen.
    out['rtl/color_regions/refined_footer_program_rom.v']=data_rom('refined_footer_program_rom',16,program).replace('rom_style="bram"','ram_style="block"')
    # Leave one complete row after the image for the HDMI/performance pipeline.
    # The formatter still finishes well before the first text row (640).
    out['rtl/color_regions/refined_osd.v']=s.replace('module stable_osd(', 'module refined_osd(').replace('stable_footer_program_rom program_rom','refined_footer_program_rom program_rom').replace('I_de && y==620 && x==0','I_de && y==625 && x==0')
    out['rtl/color_regions/stable_footer_text_rom.v']=data_rom('stable_footer_text_rom',8,dynamic_text)
    fontfile=Path('C:/Windows/Fonts/simhei.ttf')
    def rom(module,chars,size,depth,addrwidth):
        font=ImageFont.truetype(str(fontfile),size);rows=[]
        for ch in chars:
            im=Image.new('1',(size,size));ImageDraw.Draw(im).text((0,-max(1,size//16)),ch,font=font,fill=1)
            rows.extend(sum(int(im.getpixel((x,y)))<<(size-1-x) for x in range(size)) for y in range(size))
        rows +=[0]*(depth-len(rows))
        text=f'module {module}(input wire clk,input wire [{addrwidth-1}:0] addr,output reg [{size-1}:0] data);\n(* ram_style="block" *) reg [{size-1}:0] rom[0:{depth-1}];\ninitial begin\n'
        text+=''.join(f"rom[{i}]={size}'h{v:0{size//4}x};\n" for i,v in enumerate(rows))+'end\nalways @(posedge clk)data<=rom[addr];\nendmodule\n'
        return text
    depth=1<<(len(chars)*size-1).bit_length()
    out['rtl/color_regions/stable_footer_glyph_rom.v']=rom('stable_footer_glyph_rom',chars,size,depth,depth.bit_length()-1)
    out['rtl/color_regions/stable_glyph_rom.v']=rom('stable_glyph_rom',LABELS,16,256,8)
    manifest=dict(font_size=size,footer_columns=columns,longest_line=longest,glyphs=len(chars),characters=chars,diagnostic_pages=1,decimal_fields=2,diagnostic_toggle=False,
                  source_font_sha256=hashlib.sha256(fontfile.read_bytes()).hexdigest(),
                  official_symbol_sha256=hashlib.sha256((R/'assets/osd/anlogic/anlogic_logo_mobile_official.svg').read_bytes()).hexdigest())
    out['assets/osd/anlogic/refined_ui_manifest.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    return out

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    for name,text in ui_assets().items():
        p=R/name;data=text.replace('\r\n','\n').encode('utf-8')
        if a.check:assert p.read_bytes()==data,name
        else:p.write_bytes(data)
    print('REFINED_UI_CHECK_PASS' if a.check else 'REFINED_UI_GENERATED')
