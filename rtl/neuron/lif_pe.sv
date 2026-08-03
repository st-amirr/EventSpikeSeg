`timescale 1ns/1ps

module lif_pe #(
    parameter integer MEM_WIDTH = 16,
    parameter integer ACC_WIDTH = 24,
    parameter integer BETA_SHIFT = 4
) (
    input  logic clk,
    input  logic reset,
    input  logic valid,
    input  logic signed [ACC_WIDTH-1:0] current,
    input  logic signed [MEM_WIDTH-1:0] threshold,
    output logic spike,
    output logic signed [MEM_WIDTH-1:0] membrane
);
    logic signed [ACC_WIDTH:0] extended_membrane;
    logic signed [ACC_WIDTH:0] leaked;
    logic signed [ACC_WIDTH:0] candidate_wide;
    logic signed [MEM_WIDTH-1:0] candidate;
    localparam logic signed [MEM_WIDTH-1:0] MEM_MAX = {1'b0, {(MEM_WIDTH-1){1'b1}}};
    localparam logic signed [MEM_WIDTH-1:0] MEM_MIN = {1'b1, {(MEM_WIDTH-1){1'b0}}};

    always_comb begin
        extended_membrane = {{(ACC_WIDTH + 1 - MEM_WIDTH){membrane[MEM_WIDTH-1]}}, membrane};
        leaked = extended_membrane - (extended_membrane >>> BETA_SHIFT);
        candidate_wide = leaked + {{1{current[ACC_WIDTH-1]}}, current};
        if (candidate_wide > $signed(MEM_MAX))
            candidate = MEM_MAX;
        else if (candidate_wide < $signed(MEM_MIN))
            candidate = MEM_MIN;
        else
            candidate = candidate_wide[MEM_WIDTH-1:0];
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            membrane <= '0;
            spike <= 1'b0;
        end else if (valid) begin
            if (candidate >= threshold) begin
                membrane <= candidate - threshold;
                spike <= 1'b1;
            end else begin
                membrane <= candidate;
                spike <= 1'b0;
            end
        end else begin
            spike <= 1'b0;
        end
    end
endmodule
