// One shared shift/add coordinate mapper, run for 18 blanking clocks per view.
// Rectangle ends use ceil((end+1)*p/q)-1; reflection is of the displayed pixels.
`default_nettype none
module refined_overlay_geometry(input wire clk,rst_n,commit,
 input wire [639:0] meta,input wire [10:0] x0,input wire [10:0] y0,
 input wire [2:0] zoom,input wire rotate,
 output reg ready,output reg [251:0] points);
 reg busy;reg [4:0] index;reg axis_y,endpoint,is_tip,large_sample;
 reg [10:0] source;reg [43:0] box;
 reg signed [13:0] delta,left_edge,right_edge,mapped;
 reg signed [14:0] middle;
 function signed [13:0] ceiling;input signed [13:0] n;input [2:0] z;
 reg signed [13:0] triple;begin triple=(n<<<1)+n;
 case(z)1:ceiling=(triple+14'sd1)>>>1;2:ceiling=n<<<1;3:ceiling=triple;4:ceiling=n<<<2;default:ceiling=n;endcase
 end endfunction
 always @*begin
 axis_y=index<16?index[1]:index[0];is_tip=index>=16;endpoint=index[0]^rotate;
 large_sample=meta[567:565]!=0 && meta[567:565]!=2;
 box=index[2]?{meta[230],meta[183:174],meta[229],meta[173:164],meta[163:142]}:{meta[228],meta[141:132],meta[227],meta[131:122],meta[121:100]};source=0;
 if(index<8)begin
 if(axis_y)source=endpoint?box[43:33]:box[32:22];else source=endpoint?box[21:11]:box[10:0];end
 else if(index<12)source=axis_y?(endpoint?809:270):(endpoint?1439:480);
 else if(index<16)source=axis_y?(endpoint?555:524):(endpoint?975:944);
 else source=axis_y?{meta[226],meta[99:90]}:meta[89:79];
 delta=$signed({3'd0,source})-$signed(axis_y?{3'd0,y0}:{3'd0,x0});
 left_edge=ceiling(delta,zoom);right_edge=ceiling(delta+14'sd1,zoom)-14'sd1;
 middle=($signed({left_edge[13],left_edge})+$signed({right_edge[13],right_edge}))>>>1;
 mapped=is_tip?middle[13:0]:endpoint?right_edge:left_edge;
 if(rotate)mapped=(axis_y?14'sd983:14'sd1919)-mapped;
 end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin ready<=0;busy<=0;index<=0;points<=0;end
 else begin
 if(busy)begin points[index*14+:14]<=mapped;if(index==17)begin ready<=1;busy<=0;end else index<=index+1'b1;end
 if(commit)begin ready<=0;busy<=1;index<=0;end
 end end
endmodule
`default_nettype wire
