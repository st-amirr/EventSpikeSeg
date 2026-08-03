`timescale 1ns/1ps

module f_inst_top1 #(
    parameter integer CHANNELS = 4,
    parameter integer WIDTH = 16
) (
    input  logic [CHANNELS*WIDTH-1:0] candidates,
    input  logic [CHANNELS-1:0] candidate_mask,
    output logic [CHANNELS-1:0] winners
);
    integer channel;
    integer winner_index;
    logic found;
    logic signed [WIDTH-1:0] value;
    logic signed [WIDTH-1:0] best;

    always_comb begin
        winners = '0;
        found = 1'b0;
        winner_index = 0;
        best = {1'b1, {(WIDTH-1){1'b0}}};
        for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
            value = candidates[channel*WIDTH +: WIDTH];
            if (candidate_mask[channel] && (!found || value > best)) begin
                found = 1'b1;
                best = value;
                winner_index = channel;
            end
        end
        if (found)
            winners[winner_index] = 1'b1;
    end
endmodule
