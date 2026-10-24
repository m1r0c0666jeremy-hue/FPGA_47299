`timescale 1ns/1ps
module tb_scaling_controls;
    reg clk=0,camclk=0,rst=0;
    always #6.667 clk=~clk;
    always #21 camclk=~camclk;
    reg [2:0] keys=7;
    reg [1:0] sw=0;
    wire req,up,ack,ae_req;
    wire [15:0] ae,ag;
    wire [10:0] cx;
    wire [9:0] cy;
    wire [1:0] zoom,dir;
    wire [2:0] status;
    scaling_controls #(.CYCLES_PER_MS(4),.DEBOUNCE_MS(20)) dut(clk,rst,keys,sw,ack,req,up,cx,cy,zoom,dir,status);
    camera_gain_control gain(camclk,rst,req,up,1'b1,1'b1,ack,ae_req,ae,ag);
    task ms(input integer n); repeat(n*4) @(negedge clk); endtask
    task select_dir(input [1:0] s); sw=s; ms(25); endtask
    task tap(input [2:0] k); keys=k; ms(25); keys=7; ms(25); endtask
    integer before_x,before_y,i;
    reg vs=0;
    reg [10:0] vx=640;
    reg [9:0] vy=360;
    reg [1:0] vz=0;
    wire [10:0] ax,rx,sx;
    wire [9:0] ay,ry,sy;
    wire [1:0] az,ad;
    wire [2:0] ast;
    scaling_viewport viewport(clk,rst,vs,vx,vy,vz,2'd0,3'd0,ax,rx,sx,ay,ry,sy,az,ad,ast);
    task commit; vs=1; repeat(2) @(negedge clk);vs=0;repeat(2) @(negedge clk);endtask
    initial begin
        // Held key during reset must never arm the UI.
        keys=5; ms(2);rst=1;ms(100);
        if(cy!=360) $fatal(1,"held-at-reset moved");
        keys=7;ms(25);
        keys=5;ms(4);keys=7;ms(25);
        if(cy!=360) $fatal(1,"bounce escaped debounce");
        tap(5);if(cy!=362) $fatal(1,"short move must be 2");
        select_dir(1);tap(5);if(cx!=642) $fatal(1,"right mapping");
        select_dir(2);tap(5);if(cx!=640) $fatal(1,"left mapping");
        select_dir(3);tap(5);if(cy!=360) $fatal(1,"up mapping");
        select_dir(1);keys=5;ms(25);before_x=cx;before_y=cy;
        select_dir(3);ms(430);
        if(cx<=before_x || cy!=before_y || dir!=1) $fatal(1,"hold direction changed");
        before_x=cx;ms(1200);
        if(cx-before_x<50) $fatal(1,"long-press acceleration absent");
        keys=7;ms(25);if(dir!=3) $fatal(1,"idle direction stale");
        before_x=cx;before_y=cy;keys=1;ms(200);
        if(cx!=before_x || cy!=before_y || status!=3) $fatal(1,"conflicting keys acted");
        keys=5;ms(25);if(cy!=before_y-2) $fatal(1,"single-key recovery");keys=7;ms(25);
        select_dir(1);tap(3);if(zoom!=1) $fatal(1,"zoom 2x");
        keys=3;ms(1400);keys=7;ms(25);if(zoom!=2) $fatal(1,"zoom max");
        select_dir(0);tap(3);if(zoom!=1) $fatal(1,"zoom out");tap(3);tap(3);if(zoom!=0) $fatal(1,"zoom min");
        select_dir(2);tap(6);if(ag!=91 || ae!=1990) $fatal(1,"KEY2 brighten %d",ag);
        select_dir(0);tap(6);if(ag!=90) $fatal(1,"KEY2 darken");
        keys=6;ms(15000);keys=7;ms(25);if(ag!=16) $fatal(1,"gain lower bound %d",ag);
        select_dir(2);keys=6;ms(16000);keys=7;ms(25);if(ag!=105) $fatal(1,"gain upper bound");
        select_dir(1);keys=5;ms(14000);keys=7;ms(25);if(cx!=1279) $fatal(1,"right saturation");
        select_dir(2);keys=5;ms(14000);keys=7;ms(25);if(cx!=0) $fatal(1,"left saturation");
        select_dir(0);keys=5;ms(8000);keys=7;ms(25);if(cy!=719) $fatal(1,"bottom saturation");
        select_dir(3);keys=5;ms(8000);keys=7;ms(25);if(cy!=0) $fatal(1,"top saturation");
        // Viewport independently tests clamping, pan and atomic frame commit.
        commit();if(rx!=0||ry!=48||sx!=640||sy!=312) $fatal(1,"initial viewport");
        vx=1279;vy=719;vz=2;repeat(4) @(negedge clk);
        if(ax!=640||az!=0) $fatal(1,"mid-frame metadata changed");
        commit();if(rx!=960||ry!=564||sx!=1278||sy!=622) $fatal(1,"4x lower right");
        vz=1;commit();if(rx!=640||ry!=408||sx!=1279||sy!=623) $fatal(1,"2x lower right");
        vz=0;commit();if(ry!=96||ay!=719||sy!=623) $fatal(1,"zoomout lost source coordinate");
        vy=0;vx=0;commit();if(ry!=0||sy!=0) $fatal(1,"1x full-source pan");
        for(i=0;i<3;i=i+1) begin vz=i;commit();if(rx!=0||ry!=0) $fatal(1,"top left clamp");end
        $display("PASS controls: debounce, reset release, 2/10px repeats, direction lock, conflict, gain CDC/bounds, zoom/bounds, viewport atomicity and edges");
        $finish;
    end
    initial begin #10000000;$fatal(1,"timeout");end
endmodule
