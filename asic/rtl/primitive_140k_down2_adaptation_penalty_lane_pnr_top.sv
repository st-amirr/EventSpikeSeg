`timescale 1ns/1ps
// Shared lane macro. The hierarchy ties adaptation_duration_i to each actor's
// exported checkpoint value, so one routed structure covers all 15 actors.
module primitive_140k_down2_adaptation_penalty_lane_pnr_top (
  input logic clk,
  input logic update_i,
  input logic [5:0] age_i,
  input logic [18:0] amplitude_i,
  input logic [23:0] elapsed_bins_i,
  input logic [20:0] adaptation_duration_i,
  output logic [23:0] penalty_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_penalty_lane lane (
    .update_i(update_i), .age_i(age_i), .amplitude_i(amplitude_i),
    .elapsed_bins_i(elapsed_bins_i), .adaptation_duration_i(adaptation_duration_i),
    .penalty_o(penalty_o)
  );
endmodule
