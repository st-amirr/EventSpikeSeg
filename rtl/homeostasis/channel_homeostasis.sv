`timescale 1ns/1ps

module channel_homeostasis #(
    parameter integer WIDTH = 16,
    parameter integer COUNT_WIDTH = 16
) (
    input  logic clk,
    input  logic reset,
    input  logic valid,
    input  logic [COUNT_WIDTH-1:0] spike_count,
    input  logic [WIDTH-1:0] decay,
    input  logic [WIDTH-1:0] increment,
    output logic [WIDTH-1:0] adaptation
);
    logic [WIDTH:0] decayed;
    logic [WIDTH+COUNT_WIDTH:0] next_wide;
    localparam logic [WIDTH-1:0] MAXIMUM = {WIDTH{1'b1}};

    always_comb begin
        decayed = adaptation > decay ? adaptation - decay : '0;
        next_wide = decayed + spike_count * increment;
    end

    always_ff @(posedge clk) begin
        if (reset)
            adaptation <= '0;
        else if (valid)
            adaptation <= next_wide > MAXIMUM ? MAXIMUM : next_wide[WIDTH-1:0];
    end
endmodule
