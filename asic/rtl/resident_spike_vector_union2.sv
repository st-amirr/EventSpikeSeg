`timescale 1ns/1ps
// Binary residual OR for two actor-result streams. Each input contributes one
// spike vector followed by its completion token. Coincident spikes are emitted
// once, and one matched completion follows the merged vector.
module resident_spike_vector_union2 #(
  parameter integer VECTOR_WIDTH = 16,
  parameter integer TAG_WIDTH = 24
) (
  input logic clk, input logic reset,
  input logic in0_valid_i, output logic in0_ready_o,
  input logic [VECTOR_WIDTH-1:0] in0_vector_i,
  input logic in0_completion_i,
  input logic [TAG_WIDTH-1:0] in0_tag_i,
  input logic in1_valid_i, output logic in1_ready_o,
  input logic [VECTOR_WIDTH-1:0] in1_vector_i,
  input logic in1_completion_i,
  input logic [TAG_WIDTH-1:0] in1_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [VECTOR_WIDTH-1:0] out_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o,
  output logic tag_mismatch_o
);
  logic [VECTOR_WIDTH-1:0] vector0_reg, vector1_reg;
  logic vector0_seen_reg, vector1_seen_reg;
  logic completion0_seen_reg, completion1_seen_reg;
  logic [TAG_WIDTH-1:0] tag0_reg, tag1_reg;
  logic emitting_completion_reg;
  logic pair_complete;

  assign pair_complete = completion0_seen_reg && completion1_seen_reg &&
                         tag0_reg == tag1_reg;
  assign in0_ready_o = !emitting_completion_reg && !completion0_seen_reg &&
                       (in0_completion_i ? vector0_seen_reg : !vector0_seen_reg);
  assign in1_ready_o = !emitting_completion_reg && !completion1_seen_reg &&
                       (in1_completion_i ? vector1_seen_reg : !vector1_seen_reg);
  assign out_valid_o = pair_complete;
  assign out_vector_o = vector0_reg | vector1_reg;
  assign out_completion_o = emitting_completion_reg;
  assign out_tag_o = tag0_reg;

  always_ff @(posedge clk) begin
    if (reset) begin
      vector0_reg <= '0;
      vector1_reg <= '0;
      vector0_seen_reg <= 1'b0;
      vector1_seen_reg <= 1'b0;
      completion0_seen_reg <= 1'b0;
      completion1_seen_reg <= 1'b0;
      tag0_reg <= '0;
      tag1_reg <= '0;
      emitting_completion_reg <= 1'b0;
      tag_mismatch_o <= 1'b0;
    end else begin
      if (in0_valid_i && in0_ready_o) begin
        if (in0_completion_i) begin
          completion0_seen_reg <= 1'b1;
          tag0_reg <= in0_tag_i;
          if (completion1_seen_reg && tag1_reg != in0_tag_i)
            tag_mismatch_o <= 1'b1;
        end else begin
          vector0_reg <= in0_vector_i;
          vector0_seen_reg <= 1'b1;
        end
      end
      if (in1_valid_i && in1_ready_o) begin
        if (in1_completion_i) begin
          completion1_seen_reg <= 1'b1;
          tag1_reg <= in1_tag_i;
          if (completion0_seen_reg && tag0_reg != in1_tag_i)
            tag_mismatch_o <= 1'b1;
        end else begin
          vector1_reg <= in1_vector_i;
          vector1_seen_reg <= 1'b1;
        end
      end
      if (pair_complete && out_valid_o && out_ready_i) begin
        if (!emitting_completion_reg) emitting_completion_reg <= 1'b1;
        else begin
          vector0_reg <= '0;
          vector1_reg <= '0;
          vector0_seen_reg <= 1'b0;
          vector1_seen_reg <= 1'b0;
          completion0_seen_reg <= 1'b0;
          completion1_seen_reg <= 1'b0;
          emitting_completion_reg <= 1'b0;
        end
      end
    end
  end
endmodule
