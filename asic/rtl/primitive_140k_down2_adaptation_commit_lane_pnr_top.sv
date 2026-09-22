`timescale 1ns/1ps
// Shared lane macro. Actor checkpoint strength/duration remain configuration
// inputs rather than synthesis-time constants.
module primitive_140k_down2_adaptation_commit_lane_pnr_top (
  input logic clk,
  input logic [23:0] candidate_i,
  input logic [23:0] base_threshold_i,
  input logic update_i,
  input logic [5:0] age_i,
  input logic [18:0] amplitude_i,
  input logic [23:0] elapsed_bins_i,
  input logic [23:0] shared_penalty_i,
  input logic [23:0] membrane_energy_i,
  input logic [18:0] adaptation_strength_i,
  input logic [20:0] adaptation_duration_i,
  output logic [23:0] membrane_o,
  output logic spike_o,
  output logic [5:0] age_o,
  output logic [18:0] amplitude_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_commit_lane lane (
    .candidate_i(candidate_i), .base_threshold_i(base_threshold_i),
    .update_i(update_i), .age_i(age_i), .amplitude_i(amplitude_i),
    .elapsed_bins_i(elapsed_bins_i), .shared_penalty_i(shared_penalty_i),
    .membrane_energy_i(membrane_energy_i),
    .adaptation_strength_i(adaptation_strength_i),
    .adaptation_duration_i(adaptation_duration_i), .membrane_o(membrane_o),
    .spike_o(spike_o), .age_o(age_o), .amplitude_o(amplitude_o)
  );
endmodule
