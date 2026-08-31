`timescale 1ns/1ps
// Lossless two-way multicast for one packed event/completion-token stream.
// Both branches must accept a packet before the input advances.  This is the
// basic control primitive for fixed EventSpikeSeg DAG fanout paths.
module event_fork2 #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24
) (
  input  logic clk,
  input  logic reset,

  input  logic in_valid,
  output logic in_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in_payload,
  input  logic in_completion,
  input  logic [TAG_WIDTH-1:0] in_bin_tag,

  output logic out0_valid,
  input  logic out0_ready,
  output logic [PAYLOAD_WIDTH-1:0] out0_payload,
  output logic out0_completion,
  output logic [TAG_WIDTH-1:0] out0_bin_tag,

  output logic out1_valid,
  input  logic out1_ready,
  output logic [PAYLOAD_WIDTH-1:0] out1_payload,
  output logic out1_completion,
  output logic [TAG_WIDTH-1:0] out1_bin_tag
);
  logic [PAYLOAD_WIDTH-1:0] payload_reg;
  logic completion_reg;
  logic [TAG_WIDTH-1:0] bin_tag_reg;
  logic pending0_reg;
  logic pending1_reg;

  assign in_ready = !(pending0_reg || pending1_reg);
  assign out0_valid = pending0_reg;
  assign out1_valid = pending1_reg;
  assign out0_payload = payload_reg;
  assign out1_payload = payload_reg;
  assign out0_completion = completion_reg;
  assign out1_completion = completion_reg;
  assign out0_bin_tag = bin_tag_reg;
  assign out1_bin_tag = bin_tag_reg;

  always_ff @(posedge clk) begin
    if (reset) begin
      payload_reg <= '0;
      completion_reg <= 1'b0;
      bin_tag_reg <= '0;
      pending0_reg <= 1'b0;
      pending1_reg <= 1'b0;
    end else begin
      if (pending0_reg && out0_ready)
        pending0_reg <= 1'b0;
      if (pending1_reg && out1_ready)
        pending1_reg <= 1'b0;

      if (in_valid && in_ready) begin
        payload_reg <= in_payload;
        completion_reg <= in_completion;
        bin_tag_reg <= in_bin_tag;
        pending0_reg <= 1'b1;
        pending1_reg <= 1'b1;
      end
    end
  end
endmodule
