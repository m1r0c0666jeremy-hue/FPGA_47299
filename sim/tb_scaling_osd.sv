`timescale 1ns/1ps
// Real raster input to OSD, then compare captured pixels to an independent image model.
module tb_scaling_osd;
    reg clk=0,rst=0,vs=0,de=0;
    always #5 clk=~clk;
    reg [10:0] cx=0,cross_x=0;
    reg [9:0] cy=0,cross_y=0;
    reg [1:0] zoom=0,mode=0,direction=0;
    reg [2:0] status=0;
    reg ok=1;
    wire ovs,ohs,ode;wire [23:0] rgb;
    scaling_osd dut(clk,rst,vs,1'b0,de,24'h4080a0,cx,cross_x,cy,cross_y,zoom,mode,direction,status,ok,ovs,ohs,ode,rgb);
    integer f=0,i,n,count=0;
    reg [1023:0] folder,path;
    always @(posedge clk) begin
        #1;
        if(ode && f) begin $fwrite(f,"%c%c%c",rgb[23:16],rgb[15:8],rgb[7:0]);count=count+1;end
    end
    initial begin
        if($value$plusargs("OUT=%s",folder)) begin end
        repeat(4) @(negedge clk);rst=1;
        for(n=0;n<6;n=n+1) begin
            case(n)
            0:begin cx=0;cy=0;cross_x=0;cross_y=0;zoom=0;mode=0;direction=0;status=0;ok=1;end
            1:begin cx=1279;cy=719;cross_x=1279;cross_y=623;zoom=1;mode=1;direction=1;status=1;ok=1;end
            2:begin cx=1279;cy=0;cross_x=1278;cross_y=2;zoom=2;mode=2;direction=2;status=2;ok=1;end
            3:begin cx=0;cy=719;cross_x=2;cross_y=622;zoom=2;mode=3;direction=3;status=3;ok=1;end
            4:begin cx=640;cy=360;cross_x=640;cross_y=312;zoom=0;mode=0;direction=0;status=0;ok=0;end
            5:begin cx=640;cy=360;cross_x=640;cross_y=312;zoom=0;mode=0;direction=1;status=0;ok=1;end
            endcase
            $sformat(path,"%0s/osd_%0d.ppm",folder,n);
            f=$fopen(path,"wb");$fwrite(f,"P6\n1280 720\n255\n");count=0;
            vs=1;repeat(4) @(negedge clk);vs=0;repeat(4) @(negedge clk);
            de=1;repeat(1280*720) @(negedge clk);de=0;
            repeat(4) @(negedge clk);
            if(count!=1280*720) $fatal(1,"OSD output size %d",count);
            $fclose(f);f=0;
        end
        $display("PASS OSD raster captures: six full frames, all modes/states/directions and crosshair corners");
        $finish;
    end
endmodule
