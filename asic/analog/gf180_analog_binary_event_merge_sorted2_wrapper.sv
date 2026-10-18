`timescale 1ns/1ps
module gf180_analog_binary_event_merge_sorted2_wrapper (
  input logic clk, input logic reset,
  input logic in0_valid_i, output logic in0_ready_o,
  input logic [31:0] in0_payload_i, input logic in0_completion_i,
  input logic [23:0] in0_bin_tag_i,
  input logic in1_valid_i, output logic in1_ready_o,
  input logic [31:0] in1_payload_i, input logic in1_completion_i,
  input logic [23:0] in1_bin_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [31:0] out_payload_o, output logic out_completion_o,
  output logic [23:0] out_bin_tag_o,
  output logic tag_mismatch_o, output logic address_order_error_o,
  output logic overflow_o
);
  gf180_analog_binary_event_merge_sorted2 #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .KEY_LSB(0), .KEY_WIDTH(26)
  ) merge_cell (
    .clk, .reset,
    .in0_valid_i, .in0_ready_o, .in0_payload_i, .in0_completion_i,
    .in0_bin_tag_i, .in1_valid_i, .in1_ready_o, .in1_payload_i,
    .in1_completion_i, .in1_bin_tag_i, .out_valid_o, .out_ready_i,
    .out_payload_o, .out_completion_o, .out_bin_tag_o,
    .tag_mismatch_o, .address_order_error_o, .overflow_o
  );
endmodule
