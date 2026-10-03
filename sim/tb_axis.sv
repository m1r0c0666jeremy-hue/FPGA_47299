`timescale 1ns/1ps
module tb_axis;
    reg clk=0,rst=0,valid=0,start=0,finish=0;
    reg [39:0] data=0;
    wire v,sof,eol;
    wire [39:0] out_data;
    integer frame_index,line_index,beat;
    always #5 clk=~clk;
    uial2axis #(.IMG_WIDTH(1280),.IMG_HEIGHT(720),.INPUT_DATA_WIDTH(40))
        dut(clk,rst,data,valid,start,finish,v,out_data,sof,eol);
    initial begin
        repeat(3) @(negedge clk); rst=1;
        for(frame_index=0;frame_index<2;frame_index=frame_index+1) begin
            start=1; @(negedge clk); start=0;
            for(line_index=0;line_index<720;line_index=line_index+1) begin
                for(beat=0;beat<320;beat=beat+1) begin
                    valid=1; data={frame_index[7:0],line_index[15:0],beat[15:0]}; #1;
                    if(!v || out_data!==data || sof !== (line_index==0 && beat==0) || eol !== (beat==319))
                        $fatal(1,"AXIS marker/data mismatch");
                    @(negedge clk);
                    // Arbitrary valid gaps are legal at the RAW10 adapter boundary.
                    if(beat%37==10) begin
                        valid=0; #1;
                        if(v || sof || eol || out_data!==0) $fatal(1,"gap output");
                        repeat(2) @(negedge clk);
                    end
                end
                valid=0; repeat(5) @(negedge clk);
            end
            finish=1; @(negedge clk); finish=0;
        end
        // An explicit new frame start resynchronizes a partial frame.
        start=1; @(negedge clk); start=0; valid=1; #1;
        if(!sof) $fatal(1,"frame resynchronization");
        $display("PASS RAW10 adapter: two frames, valid gaps, 4 pixels/beat, SOF/EOL, frame resync");
        $finish;
    end
    initial begin #10000000; $fatal(1,"timeout"); end
endmodule
