`timescale 1ns/1ps
// GF180 wrapper for fixed nearest-neighbor event fanout in the analog model DAG.
// Events are categorical addresses; voltage, weight, and membrane data do not
// cross this macro.
module gf180_analog_event_upsample2x (
  input logic clk,
  input logic reset,
  input logic in_valid_i,
  output logic in_ready_o,
  input logic [31:0] in_payload_i,
  input logic in_completion_i,
  input logic [23:0] in_bin_tag_i,
  output logic out_valid_o,
  input logic out_ready_i,
  output logic [31:0] out_payload_o,
  output logic out_completion_o,
  output logic [23:0] out_bin_tag_o,
  output logic coordinate_overflow_o
);
  event_upsample2x #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24),
    .X_LSB(0), .X_WIDTH(10), .Y_LSB(10), .Y_WIDTH(9)
  ) upsample_cell (
    .clk, .reset,
    .in_valid(in_valid_i), .in_ready(in_ready_o),
    .in_payload(in_payload_i), .in_completion(in_completion_i),
    .in_bin_tag(in_bin_tag_i),
    .out_valid(out_valid_o), .out_ready(out_ready_i),
    .out_payload(out_payload_o), .out_completion(out_completion_o),
    .out_bin_tag(out_bin_tag_o), .coordinate_overflow_o
  );
endmodule
