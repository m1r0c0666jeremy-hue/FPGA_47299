// Native progressive1080p30. DE and positive sync share one registered stage.
`default_nettype none
module fhd_vtc #(
 parameter H_ActiveSize=1920,H_FrameSize=2200,H_SyncStart=2008,H_SyncEnd=2052,
 parameter V_ActiveSize=1080,V_FrameSize=1125,V_SyncStart=1084,V_SyncEnd=1089
)(input wire I_vtc_rstn,I_vtc_clk,
 output reg O_vtc_vs,O_vtc_hs,O_vtc_de_valid,O_vtc_user,O_vtc_last);
 reg [11:0] hcnt,vcnt;
 always @(posedge I_vtc_clk or negedge I_vtc_rstn)begin
  if(!I_vtc_rstn)begin hcnt<=0;vcnt<=0;O_vtc_vs<=0;O_vtc_hs<=0;O_vtc_de_valid<=0;O_vtc_user<=0;O_vtc_last<=0;end
  else begin
   if(hcnt==H_FrameSize-1)begin hcnt<=0;vcnt<=vcnt==V_FrameSize-1?0:vcnt+1'b1;end
   else hcnt<=hcnt+1'b1;
   O_vtc_vs<=vcnt>=V_SyncStart && vcnt<V_SyncEnd;
   O_vtc_hs<=hcnt>=H_SyncStart && hcnt<H_SyncEnd;
   O_vtc_de_valid<=hcnt<H_ActiveSize && vcnt<V_ActiveSize;
   O_vtc_user<=hcnt==0 && vcnt==0;
   O_vtc_last<=hcnt==H_ActiveSize-1 && vcnt<V_ActiveSize;
  end
 end
endmodule
`default_nettype wire
