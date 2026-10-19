"""Keep the overview/calibration footer and its two decimal fields only."""
def compact_osd_asset(source):
    start=source.index(' function [23:0] field_value;')
    end=source.index('endfunction',start)+len('endfunction')
    s=source[:start]+''' // Only latency and frame age need decimal conversion in the overview.
 function [23:0] field_value;input id;begin
 field_value=id?(fage>999?24'd999:fage):(flatency>9999999?24'd9999999:flatency);
 end endfunction'''+source[end:]
    changes=[
      ('fmode,fdiag;','fmode;'),
      ('reg [31:0] flatency,fage;reg [127:0] fddr,fpixel;reg [38:0] frecovery;reg [17:0] fcamera;',
       'reg [31:0] flatency,fage;'),
      ('reg [31:0] numbers[0:31];','reg [31:0] numbers[0:1];'),
      ('reg [4:0] field_index,bit_index;','reg field_index;reg [4:0] bit_index;'),
      ('if(field_index==31)','if(field_index)'),
      ('fdiag<=0;',''),('fdiag<=I_diag;',''),
      ('fddr<=0;fpixel<=0;frecovery<=0;fcamera<=0;',''),
      ('fddr<=I_ddr_diag;fpixel<=I_pixel_diag;frecovery<=I_recovery;fcamera<=I_camera;',''),
      (' 5:format_state<=6;',
       ' 5:begin number_word_q<=numbers[token_data[8]];hex_word_q<=hex_value;format_state<=6;end'),
      (' 6:format_state<=7;',
       ' 6:begin number_digit_q<=number_word_q>>(token_data[3:0]*4);hex_digit_q<=hex_word_q>>(token_data[3:0]*4);format_state<=7;end')]
    for before,after in changes:
        assert s.count(before)==1,before
        s=s.replace(before,after,1)
    anchor=' reg [23:0] binary;'
    assert s.count(anchor)==1
    s=s.replace(anchor,''' // The existing token wait states separate RAM selection and digit mux.
 // They add no footer/pixel latency and do not change character write cycles.
 reg [31:0] number_word_q,hex_word_q;reg [3:0] number_digit_q,hex_digit_q;
'''+anchor,1)
    anchor='format_row<=0;footer_ready<=0;'
    assert s.count(anchor)==1
    s=s.replace(anchor,anchor+'number_word_q<=0;hex_word_q<=0;number_digit_q<=0;hex_digit_q<=0;',1)
    return s
