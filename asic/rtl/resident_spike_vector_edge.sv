`timescale 1ns/1ps
// Converts one resident actor result transaction (bitmap + completion tag) into
// the two-phase stream expected by downstream accumulation: first the bitmap,
// then the completion token. The producing actor holds its result stable through
// both handshakes, so this edge stores one phase bit and does not duplicate the
// feature-map vector or tag.
module resident_spike_vector_edge #(
  parameter integer VECTOR_WIDTH = 16,
  parameter integer TAG_WIDTH = 24
) (
  input logic clk, input logic reset,
  input logic result_valid_i, output logic result_ready_o,
  input logic [VECTOR_WIDTH-1:0] spike_vector_i,
  input logic [TAG_WIDTH-1:0] completion_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [VECTOR_WIDTH-1:0] out_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o
);
  logic completion_phase_reg;

  assign result_ready_o = result_valid_i && completion_phase_reg && out_ready_i;
  assign out_valid_o = result_valid_i;
  assign out_vector_o = spike_vector_i;
  assign out_completion_o = completion_phase_reg;
  assign out_tag_o = completion_tag_i;

  always_ff @(posedge clk) begin
    if (reset) begin
      completion_phase_reg <= 1'b0;
    end else if (result_valid_i && out_ready_i)
      completion_phase_reg <= !completion_phase_reg;
    else if (!result_valid_i)
      completion_phase_reg <= 1'b0;
  end
endmodule
