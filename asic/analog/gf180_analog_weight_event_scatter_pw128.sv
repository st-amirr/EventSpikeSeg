`timescale 1ns/1ps
// Physical pointwise configuration matching a 128-input/128-output actor.
module gf180_analog_weight_event_scatter_pw128 (
  input logic clk,
  input logic reset,
  input logic event_valid_i,
  output logic event_ready_o,
  input logic [7:0] input_channel_i,
  input logic [9:0] input_x_i,
  input logic [9:0] input_y_i,
  input logic [1:0] multiplicity_i,
  input logic [23:0] bin_tag_i,
  output logic contribution_valid_o,
  input logic contribution_ready_i,
  output logic [7:0] output_channel_base_o,
  output logic [7:0] input_channel_local_o,
  output logic tap_index_o,
  output logic [9:0] output_x_o,
  output logic [9:0] output_y_o,
  output logic [1:0] multiplicity_o,
  output logic [23:0] bin_tag_o,
  output logic address_overflow_o,
  output logic channel_error_o
);
  gf180_analog_weight_event_scatter_parallel #(
    .COORD_WIDTH(10), .CHANNEL_WIDTH(8), .WEIGHT_ADDR_WIDTH(14),
    .BIN_WIDTH(24), .INPUT_CHANNELS(128), .OUTPUT_CHANNELS(128),
    .GROUPS(1), .KERNEL_WIDTH(1), .KERNEL_HEIGHT(1),
    .PAD_X(0), .PAD_Y(0), .OUTPUT_WIDTH(80), .OUTPUT_HEIGHT(55)
  ) engine (
    .clk, .reset,
    .event_valid_i, .event_ready_o,
    .input_channel_i, .input_x_i, .input_y_i,
    .multiplicity_i, .bin_tag_i,
    .contribution_valid_o, .contribution_ready_i,
    .output_channel_base_o, .input_channel_local_o, .tap_index_o,
    .output_x_o, .output_y_o, .multiplicity_o, .bin_tag_o,
    .address_overflow_o, .channel_error_o
  );
endmodule
