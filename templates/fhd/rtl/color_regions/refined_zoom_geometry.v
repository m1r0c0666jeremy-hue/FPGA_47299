// Exact source extents floor((N-1)*q/p)+1; reflected DDA phases for1920x984.
`default_nettype none
module refined_zoom_geometry(input wire [2:0] zoom,input wire rotate,
 output wire [10:0] width,height,
 output wire [2:0] p,q,output wire [2:0] phase_x,phase_y);
 assign {width,height,p,q}=
  zoom==1?{11'd1280,11'd656,3'd3,3'd2}:
  zoom==2?{11'd960,11'd492,3'd2,3'd1}:
  zoom==3?{11'd640,11'd328,3'd3,3'd1}:
  zoom==4?{11'd480,11'd246,3'd4,3'd1}:{11'd1920,11'd984,3'd1,3'd1};
 assign phase_x=rotate && zoom==1?3'd1:3'd0;
 assign phase_y=rotate && zoom==1?3'd1:3'd0;
endmodule
`default_nettype wire
