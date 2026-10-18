`timescale 1ns/1ps
// Physical configuration for the 128-channel, 3x3 depthwise actors used by
// enc3/context stages. The reusable generic engine stays in its own source.
module gf180_analog_weight_event_scatter_depthwise128 (
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
  output logic [10:0] weight_address_o,
  output logic [7:0] output_channel_o,
  output logic [9:0] output_x_o,
  output logic [9:0] output_y_o,
  output logic [1:0] multiplicity_o,
  output logic [23:0] bin_tag_o,
  output logic address_overflow_o,
  output logic channel_error_o
);
  gf180_analog_weight_event_scatter #(
    .COORD_WIDTH(10),
    .CHANNEL_WIDTH(8),
    .WEIGHT_ADDR_WIDTH(11),
    .BIN_WIDTH(24),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(128),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55)
  ) engine (
    .clk, .reset,
    .event_valid_i, .event_ready_o,
    .input_channel_i, .input_x_i, .input_y_i,
    .multiplicity_i, .bin_tag_i,
    .contribution_valid_o, .contribution_ready_i,
    .weight_address_o, .output_channel_o, .output_x_o, .output_y_o,
    .multiplicity_o, .bin_tag_o, .address_overflow_o, .channel_error_o
  );
endmodule
