module serial_wrapper(input clk,rst,input [7:0] data,output observe);
reg [821:0] s;always @(posedge clk or negedge rst)if(!rst)s<=0;else s<={s[813:0],data};
wire [2:0] n,expected,actual;wire [3:0] nd,closed,state,completed,occupied,ee,se;wire [15:0] revision,counts;
wire [671:0] draw,saved;wire [167:0] draft;wire muted,alarm,busy,live,mvalid;wire [1:0] trend;wire [10:0] distance;wire [19:0] dwell;
stage1_regions editor(clk,rst,s[1:0],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],s[10],s[18:11],s[19],s[20],s[21],s[53:22],s[821:54],
n,nd,revision,draw,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalid,saved,draft);
wire [3:0] mask;wire [23:0] color,label_color;wire label_on,ready,under;wire [7:0] glyph;wire [2:0] gx;wire [3:0] gy;
stage1_render #(.SPLIT_DRAFT(1)) picture(clk,rst,s[20],saved,counts,closed,s[1:0],s[64:54],s[74:65],s[77:75],s[78],state,completed,expected,actual,
s[89:79],s[99:90],s[100],mask,color,label_on,glyph,gx,gy,label_color,ready,under,draft,n,nd!=0);
assign observe=^{n,nd,revision,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,mvalid,
mask,color,label_on,glyph,gx,gy,label_color,ready,under};endmodule
