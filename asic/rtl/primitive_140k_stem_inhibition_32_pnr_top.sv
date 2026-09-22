`timescale 1ns/1ps
// One retinotopic stem mechanism group using the exact epoch-80 140k
// thresholds and peer-membrane inhibition strength. Channel 0 occupies the
// least-significant 24-bit slice, matching retinotopic_mechanism_update.
module primitive_140k_stem_inhibition_32_pnr_top (
  input logic clk,
  input logic [32*24-1:0] candidates_i,
  input logic [31:0] update_mask_i,
  output logic [32*24-1:0] membranes_o,
  output logic [31:0] spikes_o,
  output logic [23:0] shared_penalty_o,
  output logic [23:0] membrane_energy_o
);
  localparam logic signed [32*24-1:0] STEM_THRESHOLDS = {
    24'sh0082b5, 24'sh005b7b, 24'sh008167, 24'sh0083d5,
    24'sh007582, 24'sh00c41f, 24'sh008306, 24'sh00b6db,
    24'sh009897, 24'sh008dbe, 24'sh005343, 24'sh00aabb,
    24'sh0096eb, 24'sh00507b, 24'sh00888a, 24'sh008bfd,
    24'sh0092c0, 24'sh005703, 24'sh008c3b, 24'sh006e80,
    24'sh0078cb, 24'sh008aab, 24'sh00abee, 24'sh005e3d,
    24'sh005589, 24'sh009a26, 24'sh007773, 24'sh0090b4,
    24'sh005da9, 24'sh009713, 24'sh0077aa, 24'sh0083ba
  };

  logic unused_clk;
  logic [32*6-1:0] unused_ages;
  logic [32*19-1:0] unused_amplitudes;
  assign unused_clk = clk;

  retinotopic_mechanism_update #(
    .CHANNELS(32), .MEM_WIDTH(24), .AGE_WIDTH(6),
    .AMPLITUDE_WIDTH(19), .DURATION_WIDTH(21), .ELAPSED_WIDTH(24),
    .FRAC_BITS(16), .AGE_FRAC_BITS(0)
  ) mechanism (
    .candidates_i(candidates_i),
    .base_thresholds_i(STEM_THRESHOLDS),
    .update_mask_i(update_mask_i),
    .ages_i('0), .amplitudes_i('0), .elapsed_bins_i('0),
    .inhibition_enabled_i(1'b1), .adaptation_enabled_i(1'b0),
    .inhibition_strength_i(24'd929),
    .adaptation_strength_i(19'd0), .adaptation_duration_i(21'd0),
    .membranes_o(membranes_o), .spikes_o(spikes_o),
    .ages_o(unused_ages), .amplitudes_o(unused_amplitudes),
    .shared_penalty_o(shared_penalty_o),
    .membrane_energy_o(membrane_energy_o)
  );
endmodule
