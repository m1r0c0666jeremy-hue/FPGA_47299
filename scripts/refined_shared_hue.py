"""Factor the exact HSV numerator before multiplication by the constant 60."""
def shared_hue_asset(source):
 old=''' always @*begin
 mx=r>g?(r>b?r:b):(g>b?g:b);mn=r<g?(r<b?r:b):(g<b?g:b);
 if(mx==r)begin n=60*($signed({1'b0,g})-$signed({1'b0,b}));if(n<0)n=n+360*(mx-mn);end
 else if(mx==g)n=120*(mx-mn)+60*($signed({1'b0,b})-$signed({1'b0,r}));
 else n=240*(mx-mn)+60*($signed({1'b0,r})-$signed({1'b0,g}));
 end'''
 assert old in source
 new=''' // Hue = 60 * (channel difference + sector * chroma).
 // For all byte RGB values hue_units is nonnegative and at most 6*255.
 // The 11-bit modular sum is exact in that range; the product fits 17 bits.
 reg [7:0] hue_a,hue_b,hue_chroma;
 reg signed [8:0] hue_difference;
 reg [10:0] hue_offset,hue_units;
 always @*begin
 mx=r>g?(r>b?r:b):(g>b?g:b);mn=r<g?(r<b?r:b):(g<b?g:b);
 hue_chroma=mx-mn;
 if(mx==r)begin hue_a=g;hue_b=b;
 hue_offset=g<b?(({3'd0,hue_chroma}<<2)+({3'd0,hue_chroma}<<1)):11'd0;end
 else if(mx==g)begin hue_a=b;hue_b=r;hue_offset={3'd0,hue_chroma}<<1;end
 else begin hue_a=r;hue_b=g;hue_offset={3'd0,hue_chroma}<<2;end
 hue_difference=$signed({1'b0,hue_a})-$signed({1'b0,hue_b});
 hue_units=hue_offset+{{2{hue_difference[8]}},hue_difference};
 n=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);
 end'''
 return source.replace(old,new)
