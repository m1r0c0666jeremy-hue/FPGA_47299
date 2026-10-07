// DDR-domain association of immutable detection results and four image banks.
// Completion requires exactly 172800 sequential writes in the expected bank.
// Reader selection freezes bank+generation until the next display request.
`default_nettype none
module target_frame_store #(parameter WORDS=172800)(
    input wire I_clk,I_rst_n,I_begin,input wire [1:0] I_bank,
    input wire [31:0] I_frame_id,
    input wire I_write,input wire [24:0] I_addr,
    input wire I_result,input wire [255:0] I_meta,
    input wire I_snapshot,input wire [1:0] I_read_bank,
    output reg O_snapshot,output reg [290:0] O_data,
    output wire O_selected_good
);
    reg [31:0] ids[0:3];
    reg [255:0] metadata[0:3];
    reg [3:0] known,complete,has_meta;
    reg active,bad;
    reg [1:0] writing,selected;
    reg [31:0] selected_id;
    reg selected_once;
    reg [18:0] count;
    reg [24:0] expected;
    function [24:0] base_for(input [1:0] bank);
        case(bank) 0:base_for=0;1:base_for=7000000;2:base_for=14000000;3:base_for=21000000;endcase
    endfunction
    assign O_selected_good=selected_once && known[selected] && complete[selected] &&
        ids[selected]==selected_id && !(I_begin && I_bank==selected);
    integer i;
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            known<=0;complete<=0;has_meta<=0;active<=0;bad<=0;writing<=0;
            selected<=0;selected_id<=0;selected_once<=0;count<=0;expected<=0;O_snapshot<=0;O_data<=0;
            for(i=0;i<4;i=i+1) begin ids[i]<=0;metadata[i]<=0;end
        end else begin
            O_snapshot<=0;
            if(I_result) for(i=0;i<4;i=i+1) begin
                if(known[i] && ids[i]==I_meta[31:0]) begin metadata[i]<=I_meta;has_meta[i]<=1;end
            end
            if(I_write && active) begin
                if(I_addr!=expected || count>=WORDS) begin bad<=1;complete[writing]<=0;end
                else begin
                    expected<=expected+8;count<=count+1'b1;
                    if(count==WORDS-1 && !bad) complete[writing]<=1;
                end
            end
            if(I_begin) begin
                ids[I_bank]<=I_frame_id;known[I_bank]<=1;complete[I_bank]<=0;has_meta[I_bank]<=0;
                writing<=I_bank;count<=0;expected<=base_for(I_bank);active<=1;
                // A leftover registered write on a frame boundary is ambiguous.
                bad<=I_write;
            end
            if(I_snapshot) begin
                selected<=I_read_bank;selected_id<=ids[I_read_bank];selected_once<=1;
                O_snapshot<=1;O_data<=0;
                O_data[290]<=known[I_read_bank] && complete[I_read_bank] && !(I_begin && I_bank==I_read_bank);
                O_data[289:288]<=I_read_bank;O_data[287:256]<=ids[I_read_bank];
                if(has_meta[I_read_bank] && metadata[I_read_bank][31:0]==ids[I_read_bank] &&
                   complete[I_read_bank] && !(I_begin && I_bank==I_read_bank)) O_data[255:0]<=metadata[I_read_bank];
            end
        end
    end
endmodule
`default_nettype wire
