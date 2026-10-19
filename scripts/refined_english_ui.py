"""OSD-only successor: bounded English text and one synchronous 8x16 font."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
PACK_PROGRAM=True
STATES=['IDLE','CENTER SELECT','CONFIRMING','TRACKING','MISSING COLOR','HOLD LOST',
        'RESELECT CENTER','TIP OUT OF VIEW','INVALID FRAME','CAL WHITE','CAL BACKGROUND',
        'CAL A','CAL B','PROCESSING','SAMPLE FAILED','RECALIBRATE','VIDEO NOT READY',
        'KEY CONFLICT','NO NEW FRAME','WAIT RESULT']
ERRORS=['','INVALID FRAME','POOR WHITE PAPER','GAIN OUT OF RANGE','MIXED/FEW SAMPLES',
        'MODELS OVERLAP','BG NOT SEPARABLE','LOW MATERIAL KEEP','TOO MANY DARK PIX',
        'BRIGHTNESS CHANGED','WEAK COLOR CONTRAST','HUE FAMILY MISMATCH','TOO FEW VALID PIX']
HELP=['','WHITE PAPER IN CENTER. KEY3:SAMPLE KEY2:CANCEL',
      'REMOVE MARKERS. AIM AT INTERFERENCE. KEY3:SAMPLE KEY2:CANCEL',
      'A NEAR TIP IN CENTER. KEY3:SAMPLE KEY2:CANCEL',
      'B REAR COLOR IN CENTER. KEY3:SAMPLE KEY2:CANCEL']
MODES=['RAW','HILITE','GRAY','MASK'];MODELS=['DEFAULT','LEARNED','UPDATE']
LABELS=['RED A1','BLUE B1','YELLOW A1','PURPLE B1']
BUSY='SAMPLING 8 FRAMES/PROCESSING. HOLD STILL. KEY2:CANCEL'
RETRY=' KEY3:RETRY KEY2:CANCEL'
CHARS=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZms.:-/()'

def data_rom(name,width,rows,two_cycles=True):
    depth=len(rows);aw=(depth-1).bit_length()
    s=f'module {name}(input wire clk,input wire [{aw-1}:0] addr,output reg [{width-1}:0] q);\n'
    if two_cycles:s+=f'(* syn_preserve=1 *) reg [{aw-1}:0] registered_addr;\n'
    s+=f'(* rom_style="bram" *) reg [{width-1}:0] mem[0:{depth-1}];\ninitial begin\n'
    s+=''.join(f"mem[{i}]={width}'h{v:x};\n" for i,v in enumerate(rows))+'end\n'
    s+=('always @(posedge clk)begin registered_addr<=addr;q<=mem[registered_addr];end\n' if two_cycles else 'always @(posedge clk)q<=mem[addr];\n')
    return s+'endmodule\n'

def english_assets(historical):
    ids={c:i for i,c in enumerate(CHARS)}
    assert len(CHARS)==len(ids)<=64
    assert max(map(len,STATES))<=16 and max(map(len,MODES))<=8 and max(map(len,MODELS))<=8
    def lit(t):return [f"8'd{ids[c]}" for c in t]
    def number(i,n,valid):return [f"({valid})?(8'd1+numbers[{i}][{4*(n-1-k)}+:4]):8'd{ids['-']}" for k in range(n)]
    def hx(expr,n,valid="1'b1"):return [f"({valid})?(8'd1+({expr}>>{4*(n-1-k)} & 4'hf)):8'd{ids['-']}" for k in range(n)]
    def choose(expr,values):return [':'.join(f"{expr}=={j}?8'd{ids[value[k]]}" for j,value in enumerate(values[:-1]))+f":8'd{ids[values[-1][k]]}" for k in range(len(values[0]))]
    valid='fm[255] && fm[415:413]==4'
    zoom=choose('fzoom',['1X  ','1.5X','2X  ','3X  ','4X  '])
    pair=choose('fpair',['R/B','Y/P'])
    direction=choose('frotate',['000','180'])
    overview0=[f'mode_char(fmode,{i})' for i in range(8)]+lit(' ')+zoom+lit(' ')+pair+lit(' ')+direction+lit(' STATE:')+[f'status_char(status_id,{i})' for i in range(16)]+lit(' ')+[f'model_char(model_id,{i})' for i in range(8)]
    ms=number(0,7,'flat_valid && flatency<10000000')
    overview1=lit('LAT ')+ms[:4]+lit('.')+ms[4:5]+lit('ms AGE ')+number(1,3,'flat_valid && fage<1000')+lit(' FR F:')+hx('fimage',8)+lit(' V:')+hx('fm[559:544]',4,valid)
    cal=lit('CAL:')+[f'status_char(status_id,{i})' for i in range(16)]+lit(' E')+hx('fm[563:560]',2,valid)+lit(' F:')+hx('fimage',8)+lit(' V:')+hx('fm[559:544]',4,valid)
    templates=[overview0,overview1,cal]+[lit(t) for t in HELP[1:]]+[lit(BUSY)]+[lit(e+RETRY) for e in ERRORS]
    assert len(templates)==21 and max(map(len,templates))<=64
    validity=["1'b1"];hex_fields=[];dynamic=[]
    def idx(values,value):
        if value not in values:values.append(value)
        return values.index(value)
    def token(expr):
        m=re.fullmatch(r"8'd(\d+)",expr)
        if m:return int(m[1])
        m=re.fullmatch(r"\((.+)\)\?\(8'd1\+numbers\[(\d+)\]\[(\d+)\+:4\]\):8'd\d+",expr)
        if m:return (1<<13)|(int(m[2])<<8)|(idx(validity,m[1])<<4)|(int(m[3])//4)
        m=re.fullmatch(r"\((.+)\)\?\(8'd1\+\((.+)>>([0-9]+) & 4'hf\)\):8'd\d+",expr)
        if m:return (2<<13)|(idx(hex_fields,m[2])<<8)|(idx(validity,m[1])<<4)|(int(m[3])//4)
        m=re.fullmatch(r'(mode|status|model)_char\(.+,(\d+)\)',expr)
        if m:return (5<<13)|({'mode':0,'status':1,'model':2}[m[1]]<<8)|int(m[2])
        return (3<<13)|(idx(dynamic,expr)<<8)
    encoded=[[token(t) for t in line] for line in templates]
    starts=[];lengths=[len(t) for t in encoded]
    if PACK_PROGRAM:
        program=[]
        for line in encoded:starts.append(len(program));program.extend(line)
        assert len(program)<=1024
        used=len(program);program +=[0]*(1024-len(program))
    else:
        program=[0]*2048;used=sum(lengths)
        for i,line in enumerate(encoded):starts.append(i*64);program[i*64:i*64+len(line)]=line
    texts=[0]*512
    for base,stride,values in ((0,8,MODES),(64,16,STATES),(384,8,MODELS)):
        for i,t in enumerate(values):
            for j,c in enumerate(t):texts[base+i*stride+j]=ids[c]
    functions='''reg [4:0] template_index;reg token_valid;reg [31:0] hex_value;reg [7:0] decoded_glyph;
wire [15:0] token_data;wire [7:0] dynamic_glyph;
'''
    if PACK_PROGRAM:
        functions+='reg [9:0] template_start;reg [6:0] template_length;\nalways @*begin template_start=0;template_length=0;case(template_index)\n'
        functions+=''.join(f"{i}:begin template_start=10'd{start};template_length=7'd{length};end\n" for i,(start,length) in enumerate(zip(starts,lengths)))
        functions+='endcase end\nwire [9:0] program_addr=template_start+{4\'d0,format_col};\nreg program_in_range,program_in_range_q;\nalways @(posedge I_clk)begin program_in_range<=({1\'b0,format_col}<template_length);program_in_range_q<=program_in_range;end\n'
    else:functions+='wire [10:0] program_addr={template_index,format_col};\n'
    functions+='''wire [8:0] dynamic_addr=token_data[12:8]==0?({7'd0,fmode}<<3)+{5'd0,token_data[2:0]}:
token_data[12:8]==1?9'd64+({4'd0,status_id}<<4)+{5'd0,token_data[3:0]}:
9'd384+({7'd0,model_id}<<3)+{5'd0,token_data[2:0]};
refined_footer_program_rom program_rom(I_clk,program_addr,token_data);
refined_english_text_rom text_rom(I_clk,dynamic_addr,dynamic_glyph);
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
'''+f"1:decoded_glyph=token_valid?8'd1+number_digit_q:8'd{ids['-']};\n2:decoded_glyph=token_valid?8'd1+hex_digit_q:8'd{ids['-']};\n3:case(token_data[12:8])\n"+''.join(f'{i}:decoded_glyph={v};\n' for i,v in enumerate(dynamic))+'''endcase
5:decoded_glyph=dynamic_glyph;
endcase
'''+('if(!program_in_range_q)decoded_glyph=0;\n' if PACK_PROGRAM else '')+'end\n'
    s=historical['rtl/color_regions/refined_osd.v']
    a=s.index('reg [4:0] template_index;');b=s.index(' always @(posedge I_clk or negedge I_rst_n)',a)
    s=s[:a]+functions+s[b:]
    s=s.replace('localparam FONT=16,COLS=64;','localparam FONT=16,CHAR_WIDTH=8,COLS=64;')
    s=s.replace('COLS*FONT','COLS*CHAR_WIDTH').replace('footer_px==FONT-1','footer_px==CHAR_WIDTH-1')
    s=s.replace('reg [3:0] label_glyph,label_gx,label_gy;', 'reg [7:0] label_glyph;reg [3:0] label_gx,label_gy;reg [6:0] label_width;')
    s=s.replace('label_text=0;\n back_on=0;', 'label_text=0;label_width=0;\n back_on=0;')
    old='lx=bx0<0?0:bx0>1216?1216:bx0;'
    s=s.replace(old,'label_width=j==0?(I_pair?72:48):(I_pair?72:56);\n lx=bx0<0?0:bx0>(1280-label_width)?(1280-label_width):bx0;')
    s=s.replace('if(ldx[13:6]==0 && ldy[13:4]==0)', 'if(ldx>=0 && ldx<label_width && ldy[13:4]==0)')
    s=s.replace('label_gx=ldx[3:0];label_gy=ldy[3:0];lc=ldx[5:4];', 'label_gx={1\'b0,ldx[2:0]};label_gy=ldy[3:0];lc=ldx[6:3];')
    old='case(lc)0:label_glyph=j==0?(I_pair?3:1):(I_pair?4:2);1:label_glyph=5;2:label_glyph=j==0?6:7;3:label_glyph=8;endcase'
    new='case({I_pair,j[0]})\n'
    for i,t in enumerate(LABELS):new+=f'2\'d{i}:case(lc)\n'+''.join(f"{k}:label_glyph=8'd{ids[c]};\n" for k,c in enumerate(t))+'endcase\n'
    s=s.replace(old,new+'endcase')
    a=s.index(' localparam [31:0] WAIT_WORD=');b=s.index('\n wire footer_current',a)
    s=s[:a]+" localparam [87:0] WAIT_WORD={"+','.join(f"8'd{ids[c]}" for c in 'WAIT RESULT')+'};'+s[b:]
    s=s.replace('footer_col<4','footer_col<11').replace('(3-footer_col)*8','(10-footer_col)*8')
    a=s.index(' wire [11:0] footer_addr=');b=s.index(' refined_logo_rom logo',a)
    s=s[:a]+''' wire [9:0] shared_font_addr=footer_text?{footer_glyph[5:0],footer_gy[3:0]}:{label_glyph[5:0],label_gy};
 wire [7:0] shared_font_row;wire [1:0] logo_pixel;
 refined_english_font_rom shared_font(I_clk,shared_font_addr,shared_font_row);
'''+s[b:]
    s=s.replace('footer_font_row[FONT-1-footer_px_d]','shared_font_row[7-footer_px_d[2:0]]').replace('label_font_row[15-label_gx_d]','shared_font_row[7-label_gx_d[2:0]]')
    assert 'stable_glyph_rom' not in s and 'stable_footer_glyph_rom' not in s and 'label_width=0;' in s
    old_manifest=json.loads(historical['assets/osd/anlogic/refined_ui_manifest.json'])
    original={int(i):int(v,16) for i,v in re.findall(r"rom\[(\d+)\]=16'h([0-9a-f]+);",historical['rtl/color_regions/stable_footer_glyph_rom.v'])}
    rows=[]
    for c in CHARS:
        i=old_manifest['characters'].index(c)
        glyph=[original[i*16+y] for y in range(16)]
        assert all(v&255==0 for v in glyph),(c,'font crop would discard pixels')
        rows.extend(v>>8 for v in glyph)
    rows +=[0]*(1024-len(rows))
    manifest=dict(font_width=8,font_height=16,footer_columns=64,characters=CHARS,glyphs=len(CHARS),
                  states=STATES,errors=ERRORS,help=HELP,modes=MODES,models=MODELS,labels=LABELS,busy=BUSY,retry=RETRY,
                  packed_program=PACK_PROGRAM,program_depth=len(program),program_used=used,
                  template_starts=starts,template_lengths=lengths,source_font_sha256=old_manifest['source_font_sha256'])
    return {'rtl/color_regions/refined_osd.v':s,
            'rtl/color_regions/refined_footer_program_rom.v':data_rom('refined_footer_program_rom',16,program),
            'rtl/color_regions/refined_english_text_rom.v':data_rom('refined_english_text_rom',8,texts),
            'rtl/color_regions/refined_english_font_rom.v':data_rom('refined_english_font_rom',8,rows,False),
            'assets/osd/anlogic/english_ui_manifest.json':json.dumps(manifest,indent=2)+'\n'}
