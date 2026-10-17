"""Private, cycle-preserving calibration arithmetic resource experiment."""
def calibration_asset(source):
    old=''' if(mx==r)begin hn=60*($signed({1'b0,g})-$signed({1'b0,b}));if(hn<0)hn=hn+360*(mx-mn);end
 else if(mx==g)hn=120*(mx-mn)+60*($signed({1'b0,b})-$signed({1'b0,r}));
 else hn=240*(mx-mn)+60*($signed({1'b0,r})-$signed({1'b0,g}));'''
    assert old in source
    source=source.replace(old,''' hue_chroma=mx-mn;
 if(mx==r)begin hue_a=g;hue_b=b;
 hue_offset=g<b?(({3'd0,hue_chroma}<<2)+({3'd0,hue_chroma}<<1)):11'd0;end
 else if(mx==g)begin hue_a=b;hue_b=r;hue_offset={3'd0,hue_chroma}<<1;end
 else begin hue_a=r;hue_b=g;hue_offset={3'd0,hue_chroma}<<2;end
 hue_difference=$signed({1'b0,hue_a})-$signed({1'b0,hue_b});
 hue_units=hue_offset+{{2{hue_difference[8]}},hue_difference};
 hn=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);''')
    key=' reg family,in_cluster;'
    assert key in source
    source=source.replace(key,''' reg [7:0] hue_a,hue_b,hue_chroma;
 reg signed [8:0] hue_difference;reg [10:0] hue_offset,hue_units;
 reg family,in_cluster;''')
    key=' function [7:0] apply_gain;'
    assert key in source
    source=source.replace(key,''' // PIX_R and PIX_B already run on separate clocks. Select operands,
 // rather than relying on the mapper to share two multiplier expressions.
 wire [7:0] wb_pixel=state==PIX_R?pixel[23:16]:pixel[7:0];
 wire [11:0] wb_gain=state==PIX_R?staged_r:staged_b;
 wire [19:0] wb_product=wb_pixel*wb_gain;
 function [7:0] apply_gain;''')
    for old in ('pixel[23:16]*staged_r','pixel[7:0]*staged_b'):
        assert old in source;source=source.replace(old,'wb_product')
    def scaled(value,pad,factor):
        term="{"+str(pad)+"'d0,"+value+"}"
        return '('+'+'.join('('+term+'<<'+str(bit)+')' if bit else term for bit in range(6) if factor&(1<<bit))+')'
    replacements={
      "({2'd0,dlow}*3)":scaled('dlow',24,3),
      'slow*3':scaled('slow',27,3),
      "({3'd0,frame_samples[i]}*5)":scaled('frame_samples[i]',23,5),
      "({3'd0,frame_eligible[i]}*3)":scaled('frame_eligible[i]',23,3),
      'positive_sum*10':scaled('positive_sum',20,10),
      'cluster*9':scaled('cluster',20,9),
      "({3'd0,retained[i]}*5)":scaled('retained[i]',23,5),
      "({3'd0,frame_samples[i]}*4)":scaled('frame_samples[i]',23,4),
      '(mx-mn)*16':"(({24'd0,mx}-{24'd0,mn})<<4)",
      'mx*3':scaled('mx',24,3),
      'cluster*5':scaled('cluster',20,5),
      'eligible*3':scaled('eligible',20,3),
      "((3-pi[1:0])*24)":"(((3-pi[1:0])<<4)+((3-pi[1:0])<<3))",
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    return source
