`timescale 1ns/1ps
// Simulation/reference wrapper for one exact epoch-80 down2.standard group.
// Do not use this monolithic 64-channel wrapper for physical characterization;
// use the five primitive_140k_down2_adaptation_* blocks instead. Their explicit
// shared-value interfaces preserve this wrapper's cross-channel semantics.
// Channel 0 occupies the least-significant slice of each packed vector.
module primitive_140k_down2_adaptation_64_pnr_top (
  input logic clk,
  input logic [64*24-1:0] candidates_i,
  input logic [63:0] update_mask_i,
  input logic [64*6-1:0] ages_i,
  input logic [64*19-1:0] amplitudes_i,
  input logic [64*24-1:0] elapsed_bins_i,
  output logic [64*24-1:0] membranes_o,
  output logic [63:0] spikes_o,
  output logic [64*6-1:0] ages_o,
  output logic [64*19-1:0] amplitudes_o,
  output logic [23:0] shared_penalty_o,
  output logic [23:0] membrane_energy_o
);
  localparam logic signed [64*24-1:0] DOWN2_THRESHOLDS = {
    24'sh008eea, 24'sh0077c5, 24'sh008dc9, 24'sh00916f,
    24'sh008ae0, 24'sh008a61, 24'sh008595, 24'sh008b09,
    24'sh007b13, 24'sh009fbf, 24'sh00844b, 24'sh008e57,
    24'sh007b46, 24'sh0088b6, 24'sh009490, 24'sh007c77,
    24'sh009995, 24'sh0091aa, 24'sh0078da, 24'sh00870b,
    24'sh0091bc, 24'sh008c1f, 24'sh009258, 24'sh0083f6,
    24'sh0087bd, 24'sh008a4e, 24'sh0082d6, 24'sh009f21,
    24'sh0072d9, 24'sh007ac9, 24'sh0090e2, 24'sh0090fa,
    24'sh0077f1, 24'sh0088c3, 24'sh008251, 24'sh0089c1,
    24'sh008872, 24'sh006d25, 24'sh0082c0, 24'sh00739e,
    24'sh0080ae, 24'sh0083cd, 24'sh008de2, 24'sh009064,
    24'sh0094e5, 24'sh008aa8, 24'sh006bda, 24'sh007a83,
    24'sh00865b, 24'sh00808a, 24'sh00749c, 24'sh009068,
    24'sh0082d3, 24'sh008488, 24'sh008912, 24'sh008be6,
    24'sh00826c, 24'sh008063, 24'sh008978, 24'sh007437,
    24'sh008631, 24'sh007ce4, 24'sh007a5a, 24'sh007a01
  };

  logic unused_clk;
  assign unused_clk = clk;

  retinotopic_mechanism_update #(
    .CHANNELS(64), .MEM_WIDTH(24), .AGE_WIDTH(6),
    .AMPLITUDE_WIDTH(19), .DURATION_WIDTH(21), .ELAPSED_WIDTH(24),
    .FRAC_BITS(16), .AGE_FRAC_BITS(0)
  ) mechanism (
    .candidates_i(candidates_i),
    .base_thresholds_i(DOWN2_THRESHOLDS),
    .update_mask_i(update_mask_i),
    .ages_i(ages_i), .amplitudes_i(amplitudes_i),
    .elapsed_bins_i(elapsed_bins_i),
    .inhibition_enabled_i(1'b0), .adaptation_enabled_i(1'b1),
    .inhibition_strength_i(24'd0),
    .adaptation_strength_i(19'd875),
    .adaptation_duration_i(21'd320026),
    .membranes_o(membranes_o), .spikes_o(spikes_o),
    .ages_o(ages_o), .amplitudes_o(amplitudes_o),
    .shared_penalty_o(shared_penalty_o),
    .membrane_energy_o(membrane_energy_o)
  );
endmodule
