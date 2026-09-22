`timescale 1ns/1ps
// One ordinary PLIF cell using checkpoint-exact EventSpikeSeg140k detail_stem channel 0 constants.
module primitive_140k_plif_1_pnr_top (
  input logic clk, input logic reset,
  input logic contribution_valid_i, output logic contribution_ready_o,
  input logic [23:0] weight_i,
  input logic dense_current_valid_i, output logic dense_current_ready_o,
  input logic [31:0] dense_current_delta_i,
  input logic completion_valid_i, output logic completion_ready_o,
  input logic [23:0] completion_tag_i,
  output logic spike_valid_o, input logic spike_ready_i,
  output logic spike_o, output logic [23:0] completion_tag_o,
  output logic address_error_o
);
  resident_plif_population #(
    .DEST_COUNT(1), .ADDRESS_WIDTH(1), .CHANNEL_COUNT(1),
    .SPATIAL_DEST_COUNT(1), .CONTRIBUTION_LANES(1),
    .CHANNEL_BETAS(24'h712e2a),
    .CHANNEL_THRESHOLDS(24'h005cd3)
  ) plif (
    .clk(clk), .reset(reset),
    .contribution_valid_i(contribution_valid_i),
    .contribution_ready_o(contribution_ready_o),
    .destination_i(1'b0), .weight_i(weight_i),
    .dense_current_valid_i(dense_current_valid_i),
    .dense_current_ready_o(dense_current_ready_o),
    .dense_current_delta_i(dense_current_delta_i),
    .completion_valid_i(completion_valid_i),
    .completion_ready_o(completion_ready_o),
    .completion_tag_i(completion_tag_i),
    .spike_valid_o(spike_valid_o), .spike_ready_i(spike_ready_i),
    .spike_vector_o(spike_o), .completion_tag_o(completion_tag_o),
    .address_error_o(address_error_o)
  );
endmodule
