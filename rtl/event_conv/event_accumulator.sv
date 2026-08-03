`timescale 1ns/1ps

module event_accumulator #(
    parameter integer WEIGHT_WIDTH = 8,
    parameter integer ACC_WIDTH = 24
) (
    input  logic clk,
    input  logic reset,
    input  logic clear,
    input  logic valid,
    input  logic signed [WEIGHT_WIDTH-1:0] weight,
    output logic signed [ACC_WIDTH-1:0] accumulated_current
);
    logic signed [ACC_WIDTH:0] extended_current;
    logic signed [ACC_WIDTH:0] extended_weight;
    logic signed [ACC_WIDTH:0] sum_wide;
    localparam logic signed [ACC_WIDTH-1:0] ACC_MAX = {1'b0, {(ACC_WIDTH-1){1'b1}}};
    localparam logic signed [ACC_WIDTH-1:0] ACC_MIN = {1'b1, {(ACC_WIDTH-1){1'b0}}};

    always_comb begin
        extended_current = {{1{accumulated_current[ACC_WIDTH-1]}}, accumulated_current};
        extended_weight = {
            {(ACC_WIDTH + 1 - WEIGHT_WIDTH){weight[WEIGHT_WIDTH-1]}}, weight
        };
        sum_wide = extended_current + extended_weight;
    end

    always_ff @(posedge clk) begin
        if (reset || clear)
            accumulated_current <= '0;
        else if (valid) begin
            if (sum_wide > $signed(ACC_MAX))
                accumulated_current <= ACC_MAX;
            else if (sum_wide < $signed(ACC_MIN))
                accumulated_current <= ACC_MIN;
            else
                accumulated_current <= sum_wide[ACC_WIDTH-1:0];
        end
    end
endmodule
