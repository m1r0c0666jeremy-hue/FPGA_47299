"""Redistribute exact hue arithmetic over the existing four register stages."""
NEW_HUE_PIPELINE = r''' // Compute channel selection/chroma on the input-register stage.
 // Keep the original four-clock hit/model alignment; no extra pixel delay.
 reg [7:0] maximum1,minimum1,chroma1;
 reg signed [8:0] difference1;
 reg [1:0] sector1;
 reg [7:0] raw_maximum,raw_minimum,raw_a,raw_b;
 reg signed [8:0] raw_difference;
 reg [1:0] raw_sector;
 reg [10:0] hue_offset,hue_units;
 always @*begin
 raw_maximum=rgb[23:16]>rgb[15:8]?(rgb[23:16]>rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]>rgb[7:0]?rgb[15:8]:rgb[7:0]);
 raw_minimum=rgb[23:16]<rgb[15:8]?(rgb[23:16]<rgb[7:0]?rgb[23:16]:rgb[7:0]):(rgb[15:8]<rgb[7:0]?rgb[15:8]:rgb[7:0]);
 if(raw_maximum==rgb[23:16])begin raw_a=rgb[15:8];raw_b=rgb[7:0];raw_sector=rgb[15:8]<rgb[7:0]?3:0;end
 else if(raw_maximum==rgb[15:8])begin raw_a=rgb[7:0];raw_b=rgb[23:16];raw_sector=1;end
 else begin raw_a=rgb[23:16];raw_b=rgb[15:8];raw_sector=2;end
 raw_difference=$signed({1'b0,raw_a})-$signed({1'b0,raw_b});
 mx=maximum1;mn=minimum1;
 case(sector1)
 0:hue_offset=0;
 1:hue_offset={3'd0,chroma1}<<1;
 2:hue_offset={3'd0,chroma1}<<2;
 3:hue_offset=({3'd0,chroma1}<<2)+({3'd0,chroma1}<<1);
 endcase
 hue_units=hue_offset+{{2{difference1[8]}},difference1};
 n=({7'd0,hue_units}<<6)-({7'd0,hue_units}<<2);
 end
'''

def retime_hue_asset(source):
    start=source.index(' reg [7:0] hue_a,hue_b,hue_chroma;')
    end=source.index(' always @(posedge clk',start)
    result=source[:start]+NEW_HUE_PIPELINE+source[end:]
    changes=[
      ('r<=0;g<=0;b<=0;', 'r<=0;g<=0;b<=0;maximum1<=0;minimum1<=0;chroma1<=0;difference1<=0;sector1<=0;'),
      ('r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;', 'r<=rgb[23:16];g<=rgb[15:8];b<=rgb[7:0];c0<=models;\n maximum1<=raw_maximum;minimum1<=raw_minimum;chroma1<=raw_maximum-raw_minimum;difference1<=raw_difference;sector1<=raw_sector;'),
      ('m<=mx;d<=mx-mn;hn<=n[16:0];','m<=mx;d<=chroma1;hn<=n[16:0];')]
    for before,after in changes:
        assert result.count(before)==1,before
        result=result.replace(before,after)
    return result
