`timescale 1ns/1ps
module tb_video_timing;
    reg clk=0, rst=0;
    always #6.667 clk=~clk;
    wire vs,hs,de,sof,eol;
    uivtc #(.H_ActiveSize(1280),.H_FrameSize(1650),.H_SyncStart(1390),.H_SyncEnd(1430),
            .V_ActiveSize(720),.V_FrameSize(750),.V_SyncStart(725),.V_SyncEnd(730))
        timing(rst,clk,vs,hs,de,sof,eol);
    reg [23:0] pixels=0;
    wire mvs,mhs,mde,read_en;
    wire [23:0] output_pixel;
    hdmi_mixer #(.H_OFFSET(0),.V_OFFSET(0),.IMG_WIDTH(1280),.IMG_HEIGHT(720),.DEBUG_MODE(0))
        mixer(clk,rst,vs,hs,de,sof,eol,4'hf,read_en,pixels,mvs,mhs,mde,output_pixel);
    reg [23:0] pipe0=0,pipe1=0;
    reg [23:0] expected_pixel;
    reg pd0=0,pd1=0,expected_de;
    integer cycles=0, start_cycle=0, frames=0, count_pixels=0, lines=0, line_pixels=0;
    integer last_hs=0, hsync_count=0;
    reg started=0,hs_prev=0;
    always @(negedge clk) pixels <= pixels+24'h010307;
    always @(posedge clk) begin
        expected_pixel=pipe1; expected_de=pd1;
        pipe1=pipe0; pipe0=pixels;
        pd1=pd0; pd0=de;
        #1;
        cycles=cycles+1;
        if(rst && cycles>20) begin
            if(output_pixel !== expected_pixel || mde !== expected_de || read_en !== de)
                $fatal(1,"mixer data/DE latency mismatch at %0d",cycles);
            if(hs && !hs_prev) begin
                if(hsync_count>0 && cycles-last_hs!=1650) $fatal(1,"line period");
                last_hs=cycles; hsync_count=hsync_count+1;
            end
            hs_prev=hs;
            if(sof) begin
                if(!de) $fatal(1,"SOF without valid");
                if(started) begin
                    if(cycles-start_cycle!=1237500 || count_pixels!=921600 || lines!=720)
                        $fatal(1,"frame period=%0d pixels=%0d lines=%0d",cycles-start_cycle,count_pixels,lines);
                    frames=frames+1;
                    if(frames==2) begin
                        $display("PASS video: 2 complete 1280x720 frames, 1650x750 period, EOL/SOF, RGB/DE latency");
                        $finish;
                    end
                end
                started=1; start_cycle=cycles; count_pixels=0; lines=0; line_pixels=0;
            end
            if(started && de) begin count_pixels=count_pixels+1; line_pixels=line_pixels+1; end
            if(started && eol) begin
                if(!de || line_pixels!=1280) $fatal(1,"EOL alignment/line width");
                lines=lines+1; line_pixels=0;
            end
        end
    end
    initial begin repeat(12) @(negedge clk); rst=1; end
    initial begin #60000000; $fatal(1,"timeout"); end
endmodule
