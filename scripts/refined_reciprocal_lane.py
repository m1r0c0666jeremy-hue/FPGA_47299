"""Private exact reciprocal classifier prototype; does not change production."""
def reciprocal_asset(source):
    old='reg [127:0] c0,c1,c2;reg [16:0] lo0,hi0,lo1,hi1,h2;\n reg [7:0] m2,d2;reg [1:0] amplitude;'
    new='reg [127:0] c0,c1,c2;reg [16:0] h2;\n reg [7:0] d2;reg [1:0] amplitude;reg [34:0] reciprocal_product;'
    assert old in source;source=source.replace(old,new)
    table='\n // ceil(2^17 / d); q0 is exact floor(n/d) or one too large.\n'
    table+=' (* rom_style="bram" *) reg [17:0] reciprocal_rom[0:255];\n reg [17:0] reciprocal;\n wire [7:0] reciprocal_address=mx-mn;\n initial begin\n'
    for d in range(256):
        table+=f' reciprocal_rom[{d}]=18\'d{((131072+d-1)//d) if d else 0};\n'
    table+=''' end
 always @(posedge clk)reciprocal<=reciprocal_rom[reciprocal_address];
 wire [8:0] hue_ceil=reciprocal_product[25:17];
 wire [16:0] trial_product=hue_ceil*d2;
 wire overestimate=trial_product>h2;
 function hue_ge;input [8:0] q,bound;input over;begin
 hue_ge=q>bound || (q==bound && !over);end endfunction
 function hue_lt;input [8:0] q,bound;input over;begin
 hue_lt=q<bound || (q==bound && over);end endfunction
'''
    source=source.replace(' always @(posedge clk or negedge rst_n)begin',table+' always @(posedge clk or negedge rst_n)begin')
    old='lo0<=0;hi0<=0;lo1<=0;hi1<=0;h2<=0;m2<=0;d2<=0;'
    assert old in source;source=source.replace(old,'h2<=0;d2<=0;reciprocal_product<=0;')
    old=''' lo0<=c1[62:54]*d;hi0<=c1[53:45]*d;
 lo1<=c1[126:118]*d;hi1<=c1[117:109]*d;
 h2<=hn;m2<=m;d2<=d;c2<=c1;'''
    assert old in source;source=source.replace(old,' reciprocal_product<=hn*reciprocal;h2<=hn;d2<=d;c2<=c1;')
    for name,bound in [('h2>=lo0','62:54'),('h2<hi0','53:45'),('h2>=lo1','126:118'),('h2<hi1','117:109')]:
        assert name in source
        source=source.replace(name,f'{"hue_ge" if ">=" in name else "hue_lt"}(hue_ceil,c2[{bound}],overestimate)')
    return source

def one_logic_asset(source):
    """Permit exactly one capture lane to implement its small trial in LUTs.

    SWUG106 section4.2.10 documents dsp_style on multiplier output nets.
    The 17x18 main product retains automatic DSP mapping in every lane.
    """
    assert 'module stable_model_lane(' in source
    source=source.replace('module stable_model_lane(', 'module stable_model_lane #(parameter LOGIC_TRIAL=0)(')
    old=' wire [16:0] trial_product=hue_ceil*d2;'
    assert old in source
    return source.replace(old,''' wire [16:0] trial_product;
 generate if(LOGIC_TRIAL)begin:logic_trial
 (* dsp_style="no" *) wire [16:0] value=hue_ceil*d2;
 assign trial_product=value;
 end else begin:dsp_trial
 wire [16:0] value=hue_ceil*d2;
 assign trial_product=value;
 end endgenerate''')
