`timescale 1ns/1ps
module tb_imagepreprocess_10_3;
    parameter integer W=1280, H=720;
    reg clk=0,rst=0,vs=0,hs=0,de=0;
    reg [23:0] rgb=0;
    reg [1:0] mode=0;
    wire ov,oh,od;
    wire [23:0] op;
    wire [1:0] active;
    always #6.667 clk=~clk;
    image_preprocess #(.WIDTH(W)) dut(clk,rst,mode,vs,hs,de,rgb,ov,oh,od,op,active);
    reg [7:0] reference_gray [0:W*H-1];
    reg [23:0] expected_rgb[0:4];
    reg [4:0] expected_vs=0,expected_hs=0,expected_de=0;
    integer checked=0,cycles=0;
    integer x,y,f,k,gx,gy,mag,g;
    reg [23:0] value,expected;
    // Independent full-frame Sobel reference, not the RTL shift-register implementation.
    function integer luminance(input [23:0] p);
        luminance=(p[23:16]+2*p[15:8]+p[7:0]+2)/4;
    endfunction
    function [23:0] source_pixel(input integer xx,yy,frame);
        reg [7:0] r,g,b;
        begin
            // Mix flat areas, edges, isolated features, and exact binary thresholds.
            case(frame%4)
                0: begin r=(xx*13+yy*7)%256; g=(xx*3+yy*17)%256; b=(xx^yy)%256; end
                1: begin r=(xx<W/2)?8'd10:8'd240; g=r; b=r;
                         if(yy==H/2) begin r=255;g=255;b=255;end end
                2: begin r=xx%256;g=yy%256;b=(xx+yy)%256;end
                3: begin r=126+(xx%4);g=r;b=r;end
            endcase
            source_pixel={r,g,b};
        end
    endfunction
    task tick(input bit vv,hh,dd,input [23:0] pp,ee);
        begin
            @(negedge clk);vs=vv;hs=hh;de=dd;rgb=pp;
            for(integer j=4;j>0;j=j-1) expected_rgb[j]=expected_rgb[j-1];
            expected_rgb[0]=dd?ee:0;
            expected_vs={expected_vs[3:0],vv};
            expected_hs={expected_hs[3:0],hh};
            expected_de={expected_de[3:0],dd};
            @(posedge clk);#1;cycles=cycles+1;
            if(ov!==expected_vs[4] || oh!==expected_hs[4] || od!==expected_de[4] || op!==expected_rgb[4])
                $fatal(1,"pixel/timing mismatch mode=%0d frame=%0d xy=%0d,%0d cycle=%0d actual=%h expected=%h",active,f,x,y,cycles,op,expected_rgb[4]);
            if(od) checked=checked+1;
        end
    endtask
    initial begin
        for(k=0;k<5;k=k+1) expected_rgb[k]=0;
        repeat(5) @(negedge clk);rst=1;
        // Four full frames, with distinct mode requests. Mid-frame requests must wait.
        for(f=0;f<4;f=f+1) begin
            mode=f;
            tick(1,0,0,0,0); tick(1,0,0,0,0); tick(0,0,0,0,0);
            if(active!==f[1:0]) $fatal(1,"frame mode latch");
            for(y=0;y<H;y=y+1) begin
                for(x=0;x<W;x=x+1) begin
                    value=source_pixel(x,y,f);g=luminance(value);
                    reference_gray[y*W+x]=g;
                    expected=value;
                    case(f)
                        1: begin
                            mag=0;
                            if(x>=2 && y>=2) begin
                                gx=reference_gray[(y-2)*W+x]+2*reference_gray[(y-1)*W+x]+g
                                   -reference_gray[(y-2)*W+x-2]-2*reference_gray[(y-1)*W+x-2]-reference_gray[y*W+x-2];
                                gy=reference_gray[y*W+x-2]+2*reference_gray[y*W+x-1]+g
                                   -reference_gray[(y-2)*W+x-2]-2*reference_gray[(y-2)*W+x-1]-reference_gray[(y-2)*W+x];
                                if(gx<0) gx=-gx;if(gy<0) gy=-gy;
                                mag=gx+gy;if(mag>255) mag=255;
                            end
                            expected={3{mag[7:0]}};
                        end
                        2: expected={3{g[7:0]}};
                        3: expected=(g>=128)?24'hffffff:24'h000000;
                    endcase
                    if(x==W/2 && y==H/2) mode=(f+1)%4;
                    tick(0,0,1,value,expected);
                    if(active!==f[1:0]) $fatal(1,"mode changed inside frame");
                end
                // Line blanking with HS pulse, all modes retain timing alignment.
                repeat(4) tick(0,1,0,24'habcdef,0);
                repeat(2) tick(0,0,0,0,0);
            end
            repeat(8) tick(0,0,0,0,0);
        end
        if(checked!=4*W*H) $fatal(1,"output pixel count %0d",checked);
        // Reset while pipelines carry active data; next frame must warm up anew.
        tick(0,0,1,24'hffffff,24'hffffff);
        @(negedge clk);rst=0;de=1;rgb=24'hffffff;
        repeat(3) @(negedge clk);
        if(od!==0 || op!==0 || active!==0) $fatal(1,"reset flush");
        de=0;vs=0;hs=0;rst=1;
        expected_vs=0;expected_hs=0;expected_de=0;
        for(k=0;k<5;k=k+1) expected_rgb[k]=0;
        mode=1; tick(1,0,0,0,0);tick(0,0,0,0,0);
        for(y=0;y<2;y=y+1) begin
            for(x=0;x<W;x=x+1) tick(0,0,1,24'hffffff,0);
            repeat(6) tick(0,0,0,0,0);
        end
        repeat(8) tick(0,0,0,0,0);
        $display("PASS four %0dx%0d frames: RGB/Sobel/gray/binary, thresholds, borders, HS/VS/DE, frame-latched modes, reset and stale-line masking; pixels=%0d",W,H,checked);
        $finish;
    end
    initial begin #1000000000; $fatal(1,"timeout"); end
endmodule
