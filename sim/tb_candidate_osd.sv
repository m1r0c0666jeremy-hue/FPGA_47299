`timescale 1ns/1ps
module tb_candidate_osd;
 reg clk=0,rst=0;always #6.667 clk=~clk;
 integer h=0,v=725,frame=0,ox=0,oy=0,pixels=0,fd;
 wire vs=v>=725&&v<730,hs=h>=1390&&h<1430,de=v<720&&h<1280;
 reg [255:0] meta=0;reg [10:0] x0=0;reg [9:0] y0=48;reg [1:0] zoom=0,mode=0;
 reg [2:0] state=0;reg show=0,tip=0,video_ok=1;
 wire ovs,ohs,ode;wire [23:0] rgb;
 reg [1:0] vd=0,hd=0,dd=0;
 target_osd dut(clk,rst,vs,hs,de,24'h203040,meta,x0,y0,zoom,mode,state,show,tip,video_ok,meta[243],ovs,ohs,ode,rgb,meta[255]);
 string filename;integer f,j,n,sh,ti,st,vo,xx,yy,zz,mm;
 always @(posedge clk)begin vd<={vd[0],vs};hd<={hd[0],hs};dd<={dd[0],de};end
 always @(negedge clk)if(rst)begin
  if(frame>0 && {ovs,ohs,ode}!=={vd[1],hd[1],dd[1]})$fatal(1,"OSD sync latency");
  if(ode)begin
   $fwrite(fd,"%c%c%c",rgb[23:16],rgb[15:8],rgb[7:0]);pixels=pixels+1;
  end
  if(h==1649)begin h=0;if(v==749)begin v=0;frame=frame+1;end else v=v+1;end else h=h+1;
  if(frame==1&&v==721&&h==0)begin
   if(pixels!=921600)$fatal(1,"OSD pixel count");$fclose(fd);
   $display("PASS OSD capture state=%0d show=%0d zoom=%0d pixels=%0d",state,show,zoom,pixels);$finish;
  end
 end
 initial begin
  if(!$value$plusargs("CONFIG=%s",filename))$fatal;
  f=$fopen(filename,"r");n=$fscanf(f,"%d %d %d %d %d %d %d %d %h",sh,ti,st,vo,xx,yy,zz,mm,meta);
  if(n!=9)$fatal;show=sh;tip=ti;state=st;video_ok=vo;x0=xx;y0=yy;zoom=zz;mode=mm;$fclose(f);
  if(!$value$plusargs("OUT=%s",filename))$fatal;
  fd=$fopen(filename,"wb");$fwrite(fd,"P6\n1280 720\n255\n");
  repeat(5)@(negedge clk);rst=1;
 end
endmodule
