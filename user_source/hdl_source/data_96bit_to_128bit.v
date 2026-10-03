// ============================================================================
//  data_96bit_to_128bit.v   —— 修正版（只补复位，数据路径与原实现等价）
//
//  原实现的问题：I_rst_n 端口声明了但整个模块一次都没用到，
//  S_cnt / O_128b_valid / O_128b_data / O_128b_frame_start 都没有复位。
//  后果：有效数据期间复位不会清掉已攒的打包分组，96→128 位边界会错位
//        （仿真 tb_pack 已复现，见 reports/simulation.log 的 KNOWN_LIMITATION）。
//
//  替换对象：user_source/hdl_source/data_96bit_to_128bit.v
//  等价性：正常流（valid 连续、无复位）行为与原实现完全一致，只多了复位分支。
// ============================================================================

module data_96bit_to_128bit (
    input wire        I_clk,
    input wire        I_rst_n,          // 低有效异步复位（本次修正真正使用它）

    input wire        I_96b_frame_start,
    input wire        I_96b_valid,
    input wire[95:0]  I_96b_data,

    output reg        O_128b_frame_start,
    output reg        O_128b_valid,
    output reg[127:0] O_128b_data
);

    reg[95:0]  S_96b_data_1d;
    reg        S_96b_valid_1d;
    reg[1:0]   S_cnt;

    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            S_96b_valid_1d     <= 1'b0;
            S_96b_data_1d      <= 96'd0;
            O_128b_frame_start <= 1'b0;
        end
        else begin
            S_96b_valid_1d     <= I_96b_valid;
            S_96b_data_1d      <= I_96b_data;
            O_128b_frame_start <= I_96b_frame_start;
        end
    end

    // 打包分组计数：valid 间断清零（原行为），另加复位清零
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n)
            S_cnt <= 2'd0;
        else if(I_96b_valid)
            S_cnt <= S_cnt + 2'd1;
        else
            S_cnt <= 2'd0;
    end

    // 输出级：加复位后输出 0，其余与原 case 一一对应
    always @(posedge I_clk or negedge I_rst_n) begin
        if(!I_rst_n) begin
            O_128b_valid <= 1'b0;
            O_128b_data  <= 128'd0;
        end
        else if(I_96b_valid) begin
            case(S_cnt)
                2'd0 : begin O_128b_valid <= 1'b0; O_128b_data <= 128'd0;                              end
                2'd1 : begin O_128b_valid <= 1'b1; O_128b_data <= {S_96b_data_1d,        I_96b_data[95:64]}; end
                2'd2 : begin O_128b_valid <= 1'b1; O_128b_data <= {S_96b_data_1d[63:0],  I_96b_data[95:32]}; end
                2'd3 : begin O_128b_valid <= 1'b1; O_128b_data <= {S_96b_data_1d[31:0],  I_96b_data};        end
                default: begin O_128b_valid <= 1'b0; O_128b_data <= 128'd0;                           end
            endcase
        end
        else begin
            O_128b_valid <= 1'b0;
            O_128b_data  <= 128'd0;
        end
    end

endmodule
