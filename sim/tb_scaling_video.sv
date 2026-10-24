`timescale 1ns/1ps
module tb_scaling_video;
    reg pc=0,dc=0,rst=0;
    always #6.667 pc=~pc;
    always #7.5 dc=~dc; // Actual DDR user clock: 66.667 MHz.
    integer h=0,v=725,frame=0,cycles=0;
    wire vs=v>=725 && v<730, hs=h>=1390 && h<1430, de=v<720 && h<1280;
    integer zarg=0,xarg=0,yarg=48,marg=0,fault=0,frames=1,dynamic=0;
    integer expected_x=0,expected_y=48,expected_z=0,expected_base=14000000;
    reg [1:0] read_buffer=2;
    reg [1:0] zoom=0, mode=0;
    reg [10:0] x0=0;
    reg [9:0] y0=48;
    wire busy,rd;
    wire [24:0] addr;
    reg valid=0,ready=1,wrbusy=0,wren=0;
    reg [127:0] data=0;
    wire svs,shs,sde,ok;
    wire [23:0] rgb;
    scaling_line_reader dut(rst,dc,wrbusy,wren,read_buffer,ready,valid,data,busy,rd,addr,pc,vs,hs,de,x0,y0,zoom,svs,shs,sde,rgb,ok);
    wire pvs,phs,pde,ovs,ohs,ode;
    wire [23:0] prgb,orgb;
    wire [1:0] active_mode;
    image_preprocess process(pc,rst,mode,svs,shs,sde,rgb,pvs,phs,pde,prgb,active_mode);
    wire [10:0] center_x=x0+(640>>zoom);
    wire [9:0] center_y=y0+(312>>zoom);
    scaling_osd osd(pc,rst,pvs,phs,pde,prgb,center_x,11'd640,center_y,10'd312,zoom,active_mode,2'd1,3'd0,ok,ovs,ohs,ode,orgb);
    function [23:0] pixel(input integer xx,yy);
        pixel={8'(xx),8'(yy),8'(((xx>>8)*64)+((yy>>8)*16)+((xx^yy)&15))};
    endfunction
    function [127:0] word_at(input integer aa);
        integer j,bytepos,xx,yy,channel; reg [23:0] p;
        begin
            for(j=0;j<16;j=j+1) begin
                bytepos=((aa%7000000)/8)*16+j;
                xx=(bytepos/3)%1280;yy=bytepos/3840;channel=bytepos%3;p=pixel(xx,yy);
                word_at[127-j*8-:8]=p>>(16-channel*8);
            end
        end
    endfunction
    integer qaddr[0:4095],due[0:4095],head=0,tail=0,dc_cycle=0,hold_until=0,write_count=0;
    integer row,transactions=0;reg injected=0;
    // Ordered return queue with independent backpressure and concurrent write bursts.
    always @(negedge dc) begin
        dc_cycle=dc_cycle+1;
        ready=(dc_cycle%19!=0)&&(dc_cycle%23!=0);
        valid=0;
        if(head!=tail && due[head]<=dc_cycle) begin
            valid=1;data=word_at(qaddr[head]);head=(head+1)%4096;
        end
    end
    // Match video_in's registered final beat and ownership state transitions.
    // Model a permanently nonempty camera FIFO to expose read starvation.
    always @(posedge dc) begin
        if(!rst) begin wrbusy<=0;wren<=0;write_count<=0;end
        else begin
            wren<=wrbusy && ready;
            if(wrbusy && ready && write_count==239) wrbusy<=0;
            else if(!busy) wrbusy<=1;
            if(wrbusy) begin if(ready) write_count<=write_count+1;end
            else write_count<=0;
        end
    end
    always @(posedge dc) if(rst && rd) begin
        if(wrbusy||wren) $fatal(1,"read/write ownership collision");
        if(addr<expected_base || addr>=expected_base+720*1920 || addr%8!=0) $fatal(1,"invalid DDR address / frame bank %d",addr);
        row=(addr-expected_base)/1920;
        if(fault!=0 && !injected && row==(fault==1?100:660)) begin
            injected=1;hold_until=dc_cycle+(fault==1?20000:600000);
        end
        qaddr[tail]=addr;due[tail]=(dc_cycle+37>hold_until)?dc_cycle+37:hold_until;
        tail=(tail+1)%4096;transactions=transactions+1;
        if(tail==head) $fatal(1,"test queue full");
    end
    integer sxcount=0,sycount=0,ox=0,oy=0,checked=0,black_count=0,osd_count=0;
    reg s_vs_last=0,o_vs_last=0,failed_frame=0;
    reg [23:0] expected;
    integer ppm=0;reg [1023:0] capture;
    reg [8:0] vs_delay=0,hs_delay=0,de_delay=0;
    always @(posedge pc) begin
        if(!rst) begin vs_delay<=0;hs_delay<=0;de_delay<=0;end
        else begin vs_delay<={vs_delay[7:0],vs};hs_delay<={hs_delay[7:0],hs};de_delay<={de_delay[7:0],de};end
    end
    always @(negedge pc) begin
        if(rst) begin
            if(cycles>20 && ({ovs,ohs,ode} !== {vs_delay[8],hs_delay[8],de_delay[8]}))
                $fatal(1,"RGB pipeline synchronization latency changed");
            if(svs&&!s_vs_last) begin
                sxcount=0;sycount=0;failed_frame=0;
                expected_x=x0;expected_y=y0;expected_z=zoom;expected_base=read_buffer*7000000;
            end
            s_vs_last=svs;
            if(sde) begin
                if(sycount<624) begin
                    if(!ok) begin failed_frame=1;black_count=black_count+1;end
                    if(failed_frame) expected=0;
                    else expected=pixel(expected_x+(sxcount>>expected_z),expected_y+(sycount>>expected_z));
                    // The frame failure flag is registered one cycle later than detection.
                    if(rgb!==expected && !(fault!=0 && !ok && black_count<=2))
                        $fatal(1,"scaled RGB x=%d y=%d zoom=%d got=%h expected=%h ok=%b",sxcount,sycount,zarg,rgb,expected,ok);
                    checked=checked+1;
                    if(fault!=0 && frame==frames && sxcount==1279 && sycount==623 && failed_frame)
                        $fatal(1,"final active frame did not recover");
                end else if(rgb!==0) $fatal(1,"scaler should not read OSD rows");
                if(sxcount==1279) begin sxcount=0;sycount=sycount+1;end else sxcount=sxcount+1;
            end
            if(ovs&&!o_vs_last) begin ox=0;oy=0;end
            o_vs_last=ovs;
            if(ode) begin
                if(oy==624 && ox==0 && orgb!==24'h102030) $fatal(1,"OSD panel origin");
                if(oy==312 && ox==645 && orgb!==24'hffff00) $fatal(1,"yellow crosshair");
                if(oy==315 && ox==645 && fault==0 && marg==0 && orgb!==pixel(expected_x+(ox>>expected_z),expected_y+(oy>>expected_z)))
                    $fatal(1,"outside crosshair changed");
                if(oy>=624) osd_count=osd_count+1;
                if(ppm && frame==1) $fwrite(ppm,"%c%c%c",orgb[23:16],orgb[15:8],orgb[7:0]);
                if(ox==1279) begin ox=0;oy=oy+1;end else ox=ox+1;
            end
            // Change all requested parameters and the available DDR bank mid-frame.
            // The independent checker keeps the old values until the next VS.
            if(dynamic && frame==1 && v==100 && h==1400) begin
                x0=959;y0=563;zoom=2;read_buffer=3;
            end
            if(h==1649) begin h=0;if(v==749) begin v=0;frame=frame+1;end else v=v+1;end else h=h+1;
            cycles=cycles+1;
            if(frame==frames && v==749 && h==1600) begin
                if(ppm) $fclose(ppm);
                if(checked!=frames*1280*624) $fatal(1,"pixel count %d",checked);
                if(osd_count!=frames*1280*96) $fatal(1,"OSD count %d",osd_count);
                if(fault==0 && black_count!=0) $fatal(1,"unexpected underrun");
                if(fault!=0 && (!injected || black_count==0 || !ok)) $fatal(1,"fault/recovery not covered");
                $display("PASS scaling video: zoom=%d mode=%d x0=%d y0=%d frames=%d pixels=%d DDR=%d black=%d",zarg,marg,xarg,yarg,frames,checked,transactions,black_count);
                $finish;
            end
        end
    end
    initial begin
        if($value$plusargs("ZOOM=%d",zarg)) begin end
        if($value$plusargs("X=%d",xarg)) begin end
        if($value$plusargs("Y=%d",yarg)) begin end
        if($value$plusargs("MODE=%d",marg)) begin end
        if($value$plusargs("FAULT=%d",fault)) begin end
        if($value$plusargs("FRAMES=%d",frames)) begin end
        if($value$plusargs("DYNAMIC=%d",dynamic)) begin end
        if($value$plusargs("CAPTURE=%s",capture)) begin ppm=$fopen(capture,"wb");$fwrite(ppm,"P6\n1280 720\n255\n");end
        zoom=zarg;x0=xarg;y0=yarg;mode=marg;
        repeat(12) @(negedge pc);rst=1;
    end
    initial begin #100000000; $fatal(1,"video timeout");end
endmodule
