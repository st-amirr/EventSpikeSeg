`timescale 1ns/1ps
// Storage-free wide-vector multicast. The source must hold its ready/valid
// payload stable until both branches accept it; only two acceptance bits are
// retained, avoiding a duplicate register bank for a full feature-map vector.
module resident_spike_vector_fork2 #(
  parameter integer VECTOR_WIDTH = 16,
  parameter integer TAG_WIDTH = 24
) (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [VECTOR_WIDTH-1:0] in_vector_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic out0_valid_o, input logic out0_ready_i,
  output logic [VECTOR_WIDTH-1:0] out0_vector_o,
  output logic out0_completion_o,
  output logic [TAG_WIDTH-1:0] out0_tag_o,
  output logic out1_valid_o, input logic out1_ready_i,
  output logic [VECTOR_WIDTH-1:0] out1_vector_o,
  output logic out1_completion_o,
  output logic [TAG_WIDTH-1:0] out1_tag_o
);
  logic accepted0_reg, accepted1_reg;
  assign out0_valid_o = in_valid_i && !accepted0_reg;
  assign out1_valid_o = in_valid_i && !accepted1_reg;
  assign in_ready_o = (accepted0_reg || out0_ready_i) &&
                      (accepted1_reg || out1_ready_i);
  assign out0_vector_o = in_vector_i;
  assign out1_vector_o = in_vector_i;
  assign out0_completion_o = in_completion_i;
  assign out1_completion_o = in_completion_i;
  assign out0_tag_o = in_tag_i;
  assign out1_tag_o = in_tag_i;

  always_ff @(posedge clk) begin
    if (reset) begin
      accepted0_reg <= 1'b0;
      accepted1_reg <= 1'b0;
    end else if (in_valid_i && in_ready_o) begin
      accepted0_reg <= 1'b0;
      accepted1_reg <= 1'b0;
    end else if (in_valid_i) begin
      if (out0_ready_i) accepted0_reg <= 1'b1;
      if (out1_ready_i) accepted1_reg <= 1'b1;
    end
  end
endmodule
