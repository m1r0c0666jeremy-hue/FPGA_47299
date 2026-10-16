// Exact source extents floor((N-1)*q/p)+1, plus reflected DDA start phases.
`default_nettype none
module refined_zoom_geometry(input wire [2:0] zoom,input wire rotate,
 output wire [10:0] width,output wire [9:0] height,
 output wire [2:0] p,q,output wire [2:0] phase_x,phase_y);
 assign {width,height,p,q}=
  zoom==1?{11'd853,10'd416,3'd3,3'd2}:
  zoom==2?{11'd640,10'd312,3'd2,3'd1}:
  zoom==3?{11'd427,10'd208,3'd3,3'd1}:
  zoom==4?{11'd320,10'd156,3'd4,3'd1}:{11'd1280,10'd624,3'd1,3'd1};
 assign phase_x=rotate && zoom==3?3'd1:3'd0;
 assign phase_y=rotate && zoom==1?3'd1:3'd0;
endmodule
`default_nettype wire
