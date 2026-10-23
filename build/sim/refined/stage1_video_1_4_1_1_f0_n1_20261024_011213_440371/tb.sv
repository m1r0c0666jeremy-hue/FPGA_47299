`timescale 1ns/1ps
module tb_stable_video;
    reg pc=0,dc=0,rst=0;
    always #6.667 pc=~pc;
    always #7.5 dc=~dc; // Actual DDR user clock: 66.667 MHz.
    integer h=0,v=725,frame=0,cycles=0;
    wire vs=v>=725 && v<730, hs=h>=1390 && h<1430, de=v<720 && h<1280;
    integer rarg=0,parg=0,zarg=0,xarg=0,yarg=48,marg=0,fault=0,frames=1,dynamic=0;
    integer expected_rotate=0,expected_x=0,expected_y=48,expected_z=0,expected_base=14000000;
    reg [1:0] read_buffer=2;
    reg [2:0] zoom=0;reg [1:0] mode=0;
    reg [10:0] x0=0;
    reg [9:0] y0=48;
    wire busy,rd;
    wire [24:0] addr;
    reg valid=0,ready=1,wrbusy=0,wren=0;
    reg [127:0] data=0;
    wire svs,shs,sde,ok;
    wire [23:0] rgb;
    reg commit=0,vs_prev=0;integer countdown=0;
    wire [1:0] source_mask;reg [127:0] models;
    function [63:0] model(input integer lo,hi);begin model=(64'h8000000000000000)|(64'(lo)<<54)|(64'(hi)<<45)|(64'd32<<37)|(64'd16<<29)|(64'd1<<27);end endfunction
    reg [1:0] mask_reference[0:921599];reg [1023:0] mask_path;
    always @(posedge pc)begin vs_prev<=vs;commit<=0;
      if(vs&&!vs_prev)countdown<=20;
      else if(countdown>0)begin countdown<=countdown-1;if(countdown==1)commit<=1;end end
    refined_line_reader dut(commit,1'b1,rst,dc,wrbusy,wren,read_buffer,32'd123,models,ready,valid,data,busy,rd,addr,pc,vs,hs,de,x0,y0,zoom,svs,shs,sde,rgb,source_mask,ok,1'(rarg),1'b1,,,,32'd0,1'b0);
    wire pvs,phs,pde,ovs,ohs,ode;
    wire [23:0] prgb,orgb;
    wire [1:0] active_mode;
    stable_preprocess process(pc,rst,mode,1'(parg),svs,shs,sde,rgb,source_mask,pvs,phs,pde,prgb,active_mode);
    wire [10:0] center_x=x0+(640>>zoom);
    wire [9:0] center_y=y0+(312>>zoom);
    stage1_osd osd(.I_region_draft(168'd0),.I_ui_mode(2'd0),.I_region_vertices(672'd0),.I_region_counts(16'd0),.I_region_closed(4'd0),.I_area_count(3'd0),.I_expected_area(3'd0),.I_actual_area(3'd0),.I_draft_count(4'd0),.I_run_state(4'd0),.I_completed(4'd0),.I_occupied(4'd0),.I_area_muted(1'b0),.I_area_trend(2'd0),.I_area_distance(11'd0),.I_area_dwell(20'd0),.I_edit_error(4'd0),.I_start_error(4'd0),.I_area_busy(1'b0),.I_tip_live(1'b0),.I_gain_busy(1'b0),.I_gain_failed(1'b0),.I_gain_slot(3'd5),.I_clk(pc),.I_rst_n(rst),.I_vs(pvs),.I_hs(phs),.I_de(pde),.I_rgb(prgb),
      .I_geometry_commit(commit),.I_tracking(1'b0),.I_detection_valid(1'b0),.I_sample_valid(1'b0),.I_pair(1'(parg)),.I_meta(768'd0),.I_x0(x0),.I_y0(y0),.I_zoom(zoom),.I_mode(active_mode),.I_state(3'd1),
      .I_rotate(1'(expected_rotate)),.I_diag(2'd0),.I_image_id(32'd123),.I_show(1'b0),.I_video_ok(ok),.O_vs(ovs),.O_hs(ohs),.O_de(ode),.O_rgb(orgb));
    function [23:0] pixel(input integer xx,yy);
        pixel={8'(xx),8'(yy),8'(((xx>>8)*64)+((yy>>8)*16)+((xx^yy)&15))};
    endfunction
    function [23:0] page_pixel(input [23:0] rgb,input integer md,input [1:0] mask);
integer gray;begin gray=(rgb[23:16]+2*rgb[15:8]+rgb[7:0]+2)/4;
case(md)0:page_pixel=rgb;1:begin gray=gray/4;page_pixel=mask[0]?(parg?24'hffff40:24'hff6060):mask[1]?(parg?24'he080ff:24'h6090ff):{8'(gray),8'(gray),8'(gray)};end
2:page_pixel={8'(gray),8'(gray),8'(gray)};3:page_pixel=mask!=0?24'hffffff:0;endcase end endfunction
    function integer ratio_p(input integer z);case(z)1,3:ratio_p=3;2:ratio_p=2;4:ratio_p=4;default:ratio_p=1;endcase endfunction
    function integer ratio_q(input integer z);ratio_q=z==1?2:1;endfunction
    function integer sample_x(input integer x);sample_x=expected_x+((expected_rotate?1279-x:x)*ratio_q(expected_z))/ratio_p(expected_z);endfunction
    function integer sample_y(input integer y);sample_y=expected_y+((expected_rotate?623-y:y)*ratio_q(expected_z))/ratio_p(expected_z);endfunction
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
            if(cycles>20 && ({ovs,ohs,ode} !== {vs_delay[4],hs_delay[4],de_delay[4]}))
                $fatal(1,"RGB pipeline synchronization latency changed");
            if(svs&&!s_vs_last) begin
                sxcount=0;sycount=0;failed_frame=0;
                expected_rotate=rarg;expected_x=x0;expected_y=y0;expected_z=zoom;expected_base=read_buffer*7000000;
            end
            s_vs_last=svs;
            if(sde) begin
                if(sycount<624) begin
                    if(!ok) begin failed_frame=1;black_count=black_count+1;end
                    if(failed_frame) expected=0;
                    else expected=pixel(sample_x(sxcount),sample_y(sycount));
                    // The frame failure flag is registered one cycle later than detection.
                    if(rgb!==expected && !(fault!=0 && !ok && black_count<=2))
                        $fatal(1,"scaled RGB x=%d y=%d zoom=%d got=%h expected=%h ok=%b",sxcount,sycount,zarg,rgb,expected,ok);
                    if(fault==0 && source_mask!==mask_reference[(sample_y(sycount))*1280+(sample_x(sxcount))])
                      $fatal(1,"source mask mismatch xy%0d/%0d got%h",sxcount,sycount,source_mask);
                    checked=checked+1;
                    if(fault!=0 && frame==frames && sxcount==1279 && sycount==623 && failed_frame)
                        $fatal(1,"final active frame did not recover");
                end else if(rgb!==0) $fatal(1,"scaler should not read OSD rows");
                if(sxcount==1279) begin sxcount=0;sycount=sycount+1;end else sxcount=sxcount+1;
            end
            if(ovs&&!o_vs_last) begin ox=0;oy=0;end
            o_vs_last=ovs;
            if(ode) begin
                if(oy==624 && ox==0 && orgb!==24'h101824) $fatal(1,"OSD panel origin");

                if(oy==315 && ox==645 && fault==0 && marg==0 && orgb!==pixel(sample_x(ox),sample_y(oy)))
                    $fatal(1,"outside crosshair changed");
                if(oy<624 && fault==0 && orgb!==page_pixel(pixel(sample_x(ox),sample_y(oy)),marg,
                  mask_reference[(sample_y(oy))*1280+(sample_x(ox))]))$fatal(1,"page mismatch mode%0d xy%0d/%0d got%h",marg,ox,oy,orgb);
                if(oy>=624) osd_count=osd_count+1;
                if(ppm && frame==1) $fwrite(ppm,"%c%c%c",orgb[23:16],orgb[15:8],orgb[7:0]);
                if(ox==1279) begin ox=0;oy=oy+1;end else ox=ox+1;
            end
            // Change all requested parameters and the available DDR bank mid-frame.
            // The independent checker keeps the old values until the next VS.
            if(dynamic && frame==1 && v==100 && h==1400) begin
                x0=959;y0=563;zoom=4;read_buffer=3;rarg=1-rarg;
            end
            if(h==1649) begin h=0;if(v==749) begin v=0;frame=frame+1;end else v=v+1;end else h=h+1;
            cycles=cycles+1;
            if(frame==frames && v==749 && h==1600) begin
                if(ppm) $fclose(ppm);
                if(checked!=frames*1280*624) $fatal(1,"pixel count %d",checked);
                if(osd_count!=frames*1280*96) $fatal(1,"OSD count %d",osd_count);
                if(fault==0 && black_count!=0) $fatal(1,"unexpected underrun");
                if(fault!=0 && (!injected || black_count==0 || !ok)) $fatal(1,"fault/recovery not covered");
                $display("STABLE_VIDEO_PASS: zoom=%d mode=%d x0=%d y0=%d frames=%d pixels=%d DDR=%d black=%d",zarg,marg,xarg,yarg,frames,checked,transactions,black_count);
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
        if($value$plusargs("PAIR=%d",parg))begin end
        if($value$plusargs("MASK=%s",mask_path))begin end
        $readmemh(mask_path,mask_reference);
        models=parg?{model(255,330),model(45,75)}:{model(195,255),model(345,30)};
        if($value$plusargs("ROTATE=%d",rarg))begin end
        zoom=zarg;x0=xarg;y0=yarg;mode=marg;
        repeat(12) @(negedge pc);rst=1;
    end
    initial begin #100000000; $fatal(1,"video timeout");end
endmodule
