`timescale 1ns/1ps
// GF180 wrapper for lossless two-input event merge and bin rendezvous.
// Packet metadata is categorical; numerical weights and PLIF state remain analog.
module gf180_analog_event_join2 (
  input logic clk, input logic reset,
  input logic in0_valid_i, output logic in0_ready_o,
  input logic [31:0] in0_payload_i, input logic in0_completion_i,
  input logic [23:0] in0_bin_tag_i,
  input logic in1_valid_i, output logic in1_ready_o,
  input logic [31:0] in1_payload_i, input logic in1_completion_i,
  input logic [23:0] in1_bin_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [31:0] out_payload_o, output logic out_completion_o,
  output logic [23:0] out_bin_tag_o, output logic tag_mismatch_o
);
  event_join2 #(.PAYLOAD_WIDTH(32), .TAG_WIDTH(24)) join_cell (
    .clk, .reset,
    .in0_valid(in0_valid_i), .in0_ready(in0_ready_o),
    .in0_payload(in0_payload_i), .in0_completion(in0_completion_i),
    .in0_bin_tag(in0_bin_tag_i),
    .in1_valid(in1_valid_i), .in1_ready(in1_ready_o),
    .in1_payload(in1_payload_i), .in1_completion(in1_completion_i),
    .in1_bin_tag(in1_bin_tag_i),
    .out_valid(out_valid_o), .out_ready(out_ready_i),
    .out_payload(out_payload_o), .out_completion(out_completion_o),
    .out_bin_tag(out_bin_tag_o), .tag_mismatch_o
  );
endmodule
