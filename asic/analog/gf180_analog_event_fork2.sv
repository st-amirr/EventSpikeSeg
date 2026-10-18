`timescale 1ns/1ps
// GF180 physical wrapper for the lossless categorical event multicast used
// throughout the fixed analog EventSpikeSeg graph.  Numerical state/weights
// remain in analog cells; only packet metadata and completion tokens pass here.
module gf180_analog_event_fork2 (
  input logic clk,
  input logic reset,
  input logic in_valid_i,
  output logic in_ready_o,
  input logic [31:0] in_payload_i,
  input logic in_completion_i,
  input logic [23:0] in_bin_tag_i,
  output logic out0_valid_o,
  input logic out0_ready_i,
  output logic [31:0] out0_payload_o,
  output logic out0_completion_o,
  output logic [23:0] out0_bin_tag_o,
  output logic out1_valid_o,
  input logic out1_ready_i,
  output logic [31:0] out1_payload_o,
  output logic out1_completion_o,
  output logic [23:0] out1_bin_tag_o
);
  event_fork2 #(.PAYLOAD_WIDTH(32), .TAG_WIDTH(24)) fork_cell (
    .clk, .reset,
    .in_valid(in_valid_i), .in_ready(in_ready_o),
    .in_payload(in_payload_i), .in_completion(in_completion_i),
    .in_bin_tag(in_bin_tag_i),
    .out0_valid(out0_valid_o), .out0_ready(out0_ready_i),
    .out0_payload(out0_payload_o), .out0_completion(out0_completion_o),
    .out0_bin_tag(out0_bin_tag_o),
    .out1_valid(out1_valid_o), .out1_ready(out1_ready_i),
    .out1_payload(out1_payload_o), .out1_completion(out1_completion_o),
    .out1_bin_tag(out1_bin_tag_o)
  );
endmodule
