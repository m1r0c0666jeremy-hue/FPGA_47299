from pathlib import Path
import hashlib,json,re,zipfile
O=Path(__file__).resolve().parent;R=O.parents[1]
before=json.loads((O/'before.json').read_text());z=zipfile.ZipFile(O/'before.zip')
def replace(name,content):
 p=R/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==before[name],name
 p.write_bytes(content.encode('utf8'))
old=z.read('rtl/color_regions/stage1_regions.v').decode()
header=old[:old.index(' reg [671:0] vertices;')]
body=r'''
 // Only two corners per area are stored. Wide legacy ports are zero padded;
 // no arbitrary polygon, iterative multiplier/divider or bitmap is instantiated.
 reg [41:0] rectangles[0:3];reg [41:0] draft;
 reg seen;reg [31:0] last_id;reg [15:0] last_epoch,last_model;
 reg [7:0] last_session,session_last,point_session;reg [1:0] mode_last;
 reg [16:0] subms;reg [8:0] tip_age;reg [20:0] edit_point;
 reg [15:0] point_model;reg point_pending;reg [1:0] edit_request;
 reg observation,configuration_changed,metrics_good;
 reg [3:0] observed_in,observed_near;
 wire source_ok=detection_valid && meta[255] && meta[247] && meta[32] && meta[415:413]==4 &&
 meta[31:0]==image_id && meta[242:235]==session && meta[243]==pair && meta[244] &&
 meta[89:79]<1280 && meta[99:90]<720;
 assign tip_live=tracking && camera_ready && video_ok && source_ok && tip_age<250 && !gain_busy;
 assign metrics_valid=metrics_good && tip_live && seen && image_id==last_id && session==last_session &&
 meta[719:704]==last_epoch && meta[559:544]==last_model;
 assign busy=edit_request!=0;
 assign trend=2'd0;assign distance=11'd0;
 reg [671:0] saved_data,draw_data;reg [15:0] draw_counts;reg [3:0] draw_closed;
 integer j;
 always @*begin
 saved_data=0;draw_data=0;draw_counts=0;draw_closed=0;
 for(j=0;j<4;j=j+1)begin
 saved_data[j*168+:42]=rectangles[j];draw_data[j*168+:42]=rectangles[j];
 if(j<region_count)begin draw_counts[j*4+:4]=2;draw_closed[j]=1;end
 else if(j==region_count && draft_count!=0)begin draw_data[j*168+:42]=draft;draw_counts[j*4+:4]=draft_count;end
 end end
 assign saved_vertices=saved_data;assign draft_vertices={126'd0,draft};
 assign render_vertices=draw_data;assign render_counts=draw_counts;assign closed_mask=draw_closed;
 wire [10:0] dx0=draft[10:0],dx1=draft[31:21];wire [9:0] dy0=draft[20:11],dy1=draft[41:32];
 wire [10:0] xmin=dx0<dx1?dx0:dx1,xmax=dx0>dx1?dx0:dx1;
 wire [9:0] ymin=dy0<dy1?dy0:dy1,ymax=dy0>dy1?dy0:dy1;
 wire [41:0] normalized={ymax,xmax,ymin,xmin};
 reg overlap;
 always @*begin overlap=0;
 for(integer a=0;a<4;a=a+1)if(a<region_count &&
 xmin<=rectangles[a][31:21] && xmax>=rectangles[a][10:0] &&
 ymin<=rectangles[a][41:32] && ymax>=rectangles[a][20:11])overlap=1;
 end
 function contains;input [41:0] r;input [10:0] px;input [9:0] py;
 begin contains=px>=r[10:0] && px<=r[31:21] && py>=r[20:11] && py<=r[41:32];end endfunction
 function border_band;input [41:0] r;input [10:0] px;input [9:0] py;
 reg signed [12:0] l,t,h,b,sx,sy;
 begin l=$signed({2'd0,r[10:0]});h=$signed({2'd0,r[31:21]});
 t=$signed({3'd0,r[20:11]});b=$signed({3'd0,r[41:32]});
 sx=$signed({2'd0,px});sy=$signed({3'd0,py});
 // A two-source-pixel rectangular guard band. No Euclidean distance is claimed.
 border_band=sx>=l-13'sd2 && sx<=h+13'sd2 && sy>=t-13'sd2 && sy<=b+13'sd2 &&
 !(sx>l+13'sd2 && sx<h-13'sd2 && sy>t+13'sd2 && sy<b-13'sd2);
 end endfunction
 stage1_sequence #(.CYCLES_PER_MS(CYCLES_PER_MS)) sequence_controller(clk,rst_n,mode,region_count,draft_count,
 click2,click3,click4,!busy,tip_live,configuration_changed,observation,observed_in,observed_near,44'd0,
 run_state,expected_area,actual_area,completed,occupied,muted,alarm,,,dwell_ms,start_error);
 // Payload is invalid above region/draft counts and is overwritten before reuse.
 always @(posedge clk)begin
 if(edit_request==1 && mode==1 && region_count<4 && draft_count<2)begin
 if(draft_count==0)draft[20:0]<=edit_point;else draft[41:21]<=edit_point;end
 if(edit_request==2 && mode==1 && draft_count==2 && region_count<4 &&
 xmax-xmin>=6 && ymax-ymin>=6 && !overlap)begin
 for(integer a=0;a<4;a=a+1)if(region_count==a)rectangles[a]<=normalized;
 end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 region_count<=0;draft_count<=0;revision<=0;seen<=0;last_id<=0;last_epoch<=0;last_model<=0;last_session<=0;
 session_last<=0;point_session<=0;point_model<=0;mode_last<=0;subms<=0;tip_age<=250;
 edit_point<=0;point_pending<=0;edit_request<=0;observation<=0;configuration_changed<=0;
 observed_in<=0;observed_near<=0;metrics_good<=0;edit_error<=0;
 end else begin
 observation<=0;configuration_changed<=0;mode_last<=mode;session_last<=session;
 if(subms==CYCLES_PER_MS-1)begin subms<=0;if(tip_age<250)tip_age<=tip_age+1'b1;end
 else subms<=subms+1'b1;
 if(!seen || image_id!=last_id || session!=last_session || meta[719:704]!=last_epoch || meta[559:544]!=last_model)begin
 if(source_ok && tracking && camera_ready && video_ok && !gain_busy)begin
 seen<=1;last_id<=image_id;last_session<=session;last_epoch<=meta[719:704];last_model<=meta[559:544];tip_age<=0;
 for(integer a=0;a<4;a=a+1)begin
 observed_in[a]<=a<region_count && contains(rectangles[a],meta[89:79],meta[99:90]);
 observed_near[a]<=a<region_count && border_band(rectangles[a],meta[89:79],meta[99:90]);end
 observation<=1;metrics_good<=1;
 if(seen && (meta[719:704]!=last_epoch || meta[559:544]!=last_model))begin configuration_changed<=1;observation<=0;end
 end end
 if(mode==1 && down2)begin point_pending<=tip_live && !busy;
 if(tip_live && !busy)begin edit_point<={meta[99:90],meta[89:79]};point_session<=session;point_model<=meta[559:544];end
 else edit_error<=busy?4'd8:4'd5;end
 if(mode==1 && !busy)begin
 if(click2)begin
 if(point_pending && tip_live && point_session==session && point_model==meta[559:544])edit_request<=1;
 else edit_error<=5;point_pending<=0;end
 else if(click3)edit_request<=2;else if(click4)edit_request<=3;
 end
 if(edit_request!=0)begin edit_request<=0;edit_error<=0;
 if(mode==1)case(edit_request)
 1:if(region_count==4)edit_error<=4;else if(draft_count==2)edit_error<=6;
 else begin draft_count<=draft_count+1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 2:if(draft_count!=2)edit_error<=1;else if(region_count==4)edit_error<=4;
 else if(xmax-xmin<6 || ymax-ymin<6)edit_error<=2;
 else if(overlap)edit_error<=3;
 else begin region_count<=region_count+1'b1;draft_count<=0;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 3:if(draft_count!=0)begin draft_count<=draft_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 else if(region_count!=0)begin region_count<=region_count-1'b1;revision<=revision+1'b1;configuration_changed<=1;metrics_good<=0;end
 else edit_error<=7;
 default:begin end endcase end
 if(cancel || (!down2 && (!tip_live || session!=point_session || meta[559:544]!=point_model)))point_pending<=0;
 if(mode!=mode_last || session!=session_last)begin point_pending<=0;configuration_changed<=1;observation<=0;
 if(mode!=1)edit_request<=0;end
 end end
endmodule
`default_nettype wire
'''
replace('rtl/color_regions/stage1_regions.v',header+body)
old=z.read('rtl/color_regions/stage1_render.v').decode()
header=old[:old.index(' localparam IDLE=')]
mapped=re.search(r' function signed \[13:0\] mapped;.*?end endfunction',old,re.S)[0]
color=re.search(r' function \[23:0\] color_for;.*?end endfunction',old,re.S)[0]
body=r'''
 // Rectangles only: four comparison-based outlines, no bitmap RAM or ALU.
 reg [41:0] points[0:3];reg [1:0] sizes[0:3];
 reg [3:0] fclosed,fcompleted;reg [1:0] fmode;
 reg [3:0] fstate;reg [2:0] fexpected,factual,fzoom;reg frotate;
 reg [10:0] fx0;reg [9:0] fy0;
 reg [1:0] state,region_id,field,label_id;reg [5:0] label_attempt;reg label_up;
 reg signed [13:0] map_ax,map_ay,map_bx,map_by;
 reg signed [13:0] left_x[0:3],right_x[0:3],top_y[0:3],bottom_y[0:3];
 reg [10:0] labels_x[0:3];reg [9:0] labels_y[0:3];reg [3:0] labels_valid;
 reg [3:0] mask_comb,mask_q;
 assign pixel_mask=mask_q;
'''+mapped+'\n'+color+r'''
 wire [20:0] point_q=field[1] && sizes[region_id]>1?points[region_id][41:21]:points[region_id][20:0];
 wire signed [13:0] mapped_q=mapped(field[0]?{1'b0,point_q[20:11]}:point_q[10:0],
 field[0]?{1'b0,fy0}:fx0,fzoom,frotate,field[0]);
 wire signed [13:0] sort_l=map_ax<map_bx?map_ax:map_bx,sort_r=map_ax>map_bx?map_ax:map_bx;
 wire signed [13:0] sort_t=map_ay<map_by?map_ay:map_by,sort_b=map_ay>map_by?map_ay:map_by;
 reg collision;integer j;
 always @*begin collision=0;
 for(integer a=0;a<4;a=a+1)if(a<label_id && labels_valid[a] && labels_valid[label_id] &&
 labels_x[label_id]<labels_x[a]+50 && labels_x[label_id]+50>labels_x[a] &&
 labels_y[label_id]<labels_y[a]+18 && labels_y[label_id]+18>labels_y[a])collision=1;
 end
 wire signed [13:0] sx=$signed({3'd0,x}),sy=$signed({4'd0,y});
 always @*begin mask_comb=0;
 for(integer a=0;a<4;a=a+1)if(de && x<1280 && y<624 && ready && !underrun && sizes[a]!=0)begin
 if(sizes[a]==1)begin
 if(fmode==1 && sx>=left_x[a]-14'sd2 && sx<=left_x[a]+14'sd2 && sy>=top_y[a]-14'sd2 && sy<=top_y[a]+14'sd2)mask_comb[a]=1;
 end else begin
 if(((sx==left_x[a] || sx==right_x[a]) && sy>=top_y[a] && sy<=bottom_y[a]) ||
 ((sy==top_y[a] || sy==bottom_y[a]) && sx>=left_x[a] && sx<=right_x[a]))mask_comb[a]=1;
 if(fmode==1 && ((sx>=left_x[a]-14'sd2 && sx<=left_x[a]+14'sd2 && sy>=top_y[a]-14'sd2 && sy<=top_y[a]+14'sd2) ||
 (sx>=right_x[a]-14'sd2 && sx<=right_x[a]+14'sd2 && sy>=bottom_y[a]-14'sd2 && sy<=bottom_y[a]+14'sd2)))mask_comb[a]=1;
 end end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)mask_q<=0;else if(commit)mask_q<=0;else mask_q<=mask_comb;end
 reg [6:0] label_dx;reg [10:0] lx;reg [9:0] ly;
 always @*begin
 pixel_color=24'h9098a0;
 for(integer a=0;a<4;a=a+1)if(mask_q[a])pixel_color=color_for(a[1:0],fstate,fcompleted,fexpected,factual,fclosed[a]);
 label_on=0;label_glyph=0;label_gx=x[2:0];label_gy=0;label_color=24'h9098a0;label_dx=0;lx=0;ly=0;
 for(integer a=3;a>=0;a=a-1)begin lx=labels_x[a];ly=labels_y[a];
 if(ready && !underrun && labels_valid[a] && x>=lx && x<lx+48 && y>=ly && y<ly+16)begin
 label_on=1;label_dx=x-lx;label_gx=label_dx[2:0];label_gy=y-ly;
 label_color=color_for(a[1:0],fstate,fcompleted,fexpected,factual,fclosed[a]);
 case(label_dx[6:3])0:label_glyph=11;1:label_glyph=28;2:label_glyph=15;3:label_glyph=11;4:label_glyph=0;default:label_glyph=11+a;endcase
 end end end
 always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
 state<=0;region_id<=0;field<=0;label_id<=0;label_attempt<=0;label_up<=0;
 fclosed<=0;fcompleted<=0;fmode<=0;fstate<=0;fexpected<=0;factual<=0;fzoom<=0;frotate<=0;fx0<=0;fy0<=0;
 map_ax<=0;map_ay<=0;map_bx<=0;map_by<=0;labels_valid<=0;ready<=0;underrun<=0;
 for(j=0;j<4;j=j+1)begin sizes[j]<=0;left_x[j]<=0;right_x[j]<=0;top_y[j]<=0;bottom_y[j]<=0;labels_x[j]<=0;labels_y[j]<=0;end
 end else begin
 if(state!=0 && de && y<624)underrun<=1;
 case(state)
 1:begin
 case(field)0:map_ax<=mapped_q;1:map_ay<=mapped_q;2:map_bx<=mapped_q;3:map_by<=mapped_q;endcase
 if(field==3)begin field<=0;state<=2;end else field<=field+1'b1;
 end
 2:begin
 left_x[region_id]<=sort_l;right_x[region_id]<=sort_r;top_y[region_id]<=sort_t;bottom_y[region_id]<=sort_b;
 labels_x[region_id]<=sort_l<0?0:sort_l>1232?1232:sort_l;
 labels_y[region_id]<=sort_t>=18?(sort_t>626?608:sort_t-18):(sort_t< -3?0:sort_t+3);
 labels_valid[region_id]<=sizes[region_id]!=0 && sort_r>=0 && sort_l<1280 && sort_b>=0 && sort_t<624;
 if(region_id==3)begin state<=3;label_id<=0;label_attempt<=0;label_up<=labels_y[0]>304;end
 else begin region_id<=region_id+1'b1;state<=1;end
 end
 3:if(!collision || !labels_valid[label_id])begin
 if(label_id==3)begin ready<=1;state<=0;end
 else begin label_id<=label_id+1'b1;label_attempt<=0;label_up<=labels_y[label_id+1'b1]>304;end
 end else if(label_attempt==35)begin underrun<=1;ready<=1;state<=0;end
 else begin label_attempt<=label_attempt+1'b1;
 if(label_up && labels_y[label_id]>=18)labels_y[label_id]<=labels_y[label_id]-18;
 else if(!label_up && labels_y[label_id]<=590)labels_y[label_id]<=labels_y[label_id]+18;
 else begin label_up<=~label_up;labels_x[label_id]<=labels_x[label_id]>=64?labels_x[label_id]-64:labels_x[label_id]+64;end
 end
 default:begin end
 endcase
 if(commit)begin
 fclosed<=closed_mask;fcompleted<=completed;fmode<=ui_mode;fstate<=run_state;fexpected<=expected_area;factual<=actual_area;
 fzoom<=zoom;frotate<=rotate;fx0<=x0;fy0<=y0;labels_valid<=0;ready<=counts==0;underrun<=de && y<624;
 region_id<=0;field<=0;state<=counts==0?0:1;label_attempt<=0;
 for(j=0;j<4;j=j+1)begin
 points[j]<=SPLIT_DRAFT && draft_visible && draft_region==j?draft_vertices[41:0]:vertices[j*168+:42];
 sizes[j]<=counts[j*4+:4]<=2?counts[j*4+:2]:2'd0;
 if(counts[j*4+:4]>2)underrun<=1;
 end end
 end end
endmodule
`default_nettype wire
'''
replace('rtl/color_regions/stage1_render.v',header+body)
print('RECTANGLE_RTL_WRITTEN; two corners, no polygon instances, no renderer RAM/ALU')
