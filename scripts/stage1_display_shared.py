"""One frame-frozen numeric engine feeds the existing footer layout selectors."""
import re

def number_source():
    return r'''
`default_nettype none
module stage1_footer_numbers(input wire clk,rst_n,latch,
 input wire [31:0] latency,age,input wire [19:0] dwell,
 input wire [6:0] gain,target,input wire [7:0] k,input wire [79:0] teaching,
 output reg [175:0] numbers,output reg ready);
 reg [23:0] values[0:9];reg [3:0] field;reg [2:0] state;reg [4:0] bit_index;
 reg [23:0] binary,quotient;reg [6:0] remainder;reg [31:0] bcd,adjusted;
 wire [7:0] trial={remainder,binary[23]};wire take=trial>=100;
 integer i,j;
 always @*begin adjusted=bcd;
 for(i=0;i<8;i=i+1)if(bcd[i*4+:4]>=5)adjusted[i*4+:4]=bcd[i*4+:4]+3;end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin numbers<=0;ready<=0;field<=0;state<=0;bit_index<=0;
 binary<=0;quotient<=0;remainder<=0;bcd<=0;for(j=0;j<10;j=j+1)values[j]<=0;end
 else begin
 case(state)
 1:begin binary<=values[field];quotient<=0;remainder<=0;bcd<=0;bit_index<=0;
 state<=(field==2 || field==6 || field==7)?2:3;end
 2:begin binary<=binary<<1;quotient<={quotient[22:0],take};remainder<=take?trial-100:trial;
 if(bit_index==23)begin binary<={quotient[22:0],take};bit_index<=0;state<=3;end
 else bit_index<=bit_index+1'b1;end
 3:begin binary<=binary<<1;bcd<={adjusted[30:0],binary[23]};
 if(bit_index==23)state<=4;else bit_index<=bit_index+1'b1;end
 4:begin
 case(field)
 0:numbers[31:0]<=bcd;1:numbers[63:32]<=bcd;2:numbers[79:64]<=bcd[15:0];
 3:numbers[91:80]<=bcd[11:0];4:numbers[103:92]<=bcd[11:0];5:numbers[115:104]<=bcd[11:0];
 6:numbers[131:116]<=bcd[15:0];7:numbers[147:132]<=bcd[15:0];8:numbers[163:148]<=bcd[15:0];
 9:numbers[175:164]<=bcd[11:0];endcase
 if(field==9)begin ready<=1;state<=0;end else begin field<=field+1'b1;state<=1;end
 end
 default:begin end endcase
 if(latch)begin
 values[0]<=latency>9999999?24'd9999999:latency[23:0];
 values[1]<=age>999?24'd999:age[23:0];values[2]<={4'd0,dwell};
 values[3]<={17'd0,gain};values[4]<={17'd0,target};values[5]<={16'd0,k};
 values[6]<={8'd0,teaching[34:19]};values[7]<={8'd0,teaching[50:35]};
 values[8]<={13'd0,teaching[18:8]};values[9]<={16'd0,teaching[71:64]};
 ready<=0;field<=0;state<=1;
 end end end
endmodule
`default_nettype wire
'''

def external_numbers(s, teaching=False):
    name='stage1_teach_text' if teaching else 'stage1_ui_formatter'
    s=s.replace('module '+name+'(', 'module '+name+' #(parameter SHARED_NUMBERS=0)(',1)
    tail='input wire [7:0] current_k);' if teaching else 'input wire [7:0] I_k_value,input wire I_k_adjust);'
    assert tail in s
    s=s.replace(tail,tail[:-2]+',input wire [175:0] I_numbers);',1)
    fields={'time_bcd':(131,116),'duration_bcd':(147,132),'count_bcd':(163,148),'dwell_bcd':(79,64),'route_k_bcd':(175,164)} if teaching else {'gain_bcd':(91,80),'target_bcd':(103,92),'k_bcd':(115,104),'dwell_bcd':(79,64)}
    # The standalone compatibility path is constant-pruned in production.
    for n in fields:
        s=re.sub(r'\b'+n+r'(?=\s*<=)', 'local_'+n,s)
        s=re.sub(r'(reg \[[^\]]+\][^;]*?)\b'+n+r'\b',lambda m:m[1]+'local_'+n,s)
    declarations=''
    for n,(hi,lo) in fields.items():
        declarations+=f'wire [{hi-lo}:0] {n}=SHARED_NUMBERS?I_numbers[{hi}:{lo}]:local_{n};\n'
    at=s.index(' always @')
    return s[:at]+declarations+s[at:]

def decorate(out):
    ui=out['rtl/color_regions/stage1_ui_formatter.v'];split=ui.index('module stage1_teach_text(')
    out['rtl/color_regions/stage1_ui_formatter.v']=external_numbers(ui[:split])+external_numbers(ui[split:],True)+number_source()
    s=out['rtl/color_regions/stage1_osd.v']
    hook=''' stage1_footer_numbers numeric_engine(I_clk,I_rst_n,I_de && y==625 && x==0,
 I_latency_us,I_frame_age,I_area_dwell,I_camera[6:0],I_gain_target,I_k_value,I_teaching,footer_numbers,footer_numbers_ready);
'''
    marker=' stage1_teach_text teaching_text('
    assert marker in s
    s=s.replace(marker,hook+' stage1_teach_text #(.SHARED_NUMBERS(1)) teaching_text(',1)
    s=s.replace('stage1_ui_formatter region_text(', 'stage1_ui_formatter #(.SHARED_NUMBERS(1)) region_text(',1)
    s=s.replace('teaching_glyph,teaching_override,I_k_value);','teaching_glyph,teaching_override,I_k_value,footer_numbers);',1)
    s=s.replace('status_id,I_tip_reason,I_k_value,I_k_adjust);','status_id,I_tip_reason,I_k_value,I_k_adjust,footer_numbers);',1)
    start=s.index(' 1:begin binary<=field_value(field_index);');end=s.index(' 3:format_state<=4;',start)
    s=s[:start]+''' 1:if(footer_numbers_ready)begin
 format_col<=0;format_row<=0;format_state<=3;end
'''+s[end:]
    start=s.index(' // Only latency and frame age need decimal conversion');end=s.index(' reg [2:0] format_state;',start)
    s=s[:start]+''' wire [175:0] footer_numbers;wire footer_numbers_ready;wire [31:0] numbers[0:1];
 assign numbers[0]=footer_numbers[31:0];assign numbers[1]=footer_numbers[63:32];
 reg [7:0] characters[0:127];
'''+s[end:]
    s=s.replace('reg [2:0] format_state;reg field_index;reg [4:0] bit_index;', 'reg [2:0] format_state;')
    start=s.index(' reg [23:0] binary;');end=s.index('reg [4:0] template_index;',start)
    s=s[:start]+' reg [5:0] format_col;reg format_row,footer_ready;\n'+s[end:]
    s=s.replace('field_index<=0;bit_index<=0;binary<=0;decimal<=0;','').replace('field_index<=0;footer_ready<=0;','footer_ready<=0;')
    s=s.replace('stage1_render #(.SPLIT_DRAFT(1))','stage1_render #(.SPLIT_DRAFT(1),.LINE_CACHE(1))',1)
    out['rtl/color_regions/stage1_osd.v']=s
