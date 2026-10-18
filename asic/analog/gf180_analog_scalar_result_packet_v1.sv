`timescale 1ns/1ps
// Categorical output boundary for a time-shared analog comparator.
// result_valid marks a settled, sampled decision, never the raw comparator edge.
// Address order is channel/y/x, matching the graph's lower 26-bit sort key.
// result_last means the LAST NEURON OF THE ENTIRE ACTOR BIN, not a page.
// The service controller must visit every neuron, including non-spiking ones.
// No numerical membrane, parameter, or threshold is digitized here.
module gf180_analog_scalar_result_packet_v1 (
  input wire clk, reset,
  input wire result_valid_i,
  output wire result_ready_o,
  input wire result_spike_i,
  input wire [25:0] result_address_i,
  input wire [23:0] result_bin_tag_i,
  input wire result_last_i,
  output wire event_valid_o,
  input wire event_ready_i,
  output wire [31:0] event_payload_o,
  output wire event_completion_o,
  output wire [23:0] event_bin_tag_o,
  output reg tag_mismatch_o,
  output reg address_order_error_o
);
  reg spike_pending, completion_pending;
  reg bin_open;
  reg [25:0] address_reg, previous_address;
  reg [23:0] tag_reg;
  wire fault = tag_mismatch_o || address_order_error_o;
  wire invalid_result = bin_open &&
      ((result_bin_tag_i != tag_reg) || (result_address_i <= previous_address));
  assign result_ready_o = !fault && !spike_pending && !completion_pending;
  assign event_valid_o = !fault && (spike_pending || completion_pending);
  assign event_completion_o = !spike_pending && completion_pending;
  // Reserved upper fields zero: hidden-layer binary events, no raw multiplicity.
  assign event_payload_o = {6'b0, address_reg};
  assign event_bin_tag_o = tag_reg;
  always @(posedge clk) begin
    if (reset) begin
      spike_pending <= 0;
      completion_pending <= 0;
      bin_open <= 0;
      address_reg <= 0;
      previous_address <= 0;
      tag_reg <= 0;
      tag_mismatch_o <= 0;
      address_order_error_o <= 0;
    end else begin
      if (result_valid_i && result_ready_o) begin
        if (bin_open && result_bin_tag_i != tag_reg) tag_mismatch_o <= 1;
        if (bin_open && result_address_i <= previous_address) address_order_error_o <= 1;
        if (!invalid_result) begin
          bin_open <= 1;
          previous_address <= result_address_i;
          address_reg <= result_address_i;
          tag_reg <= result_bin_tag_i;
          spike_pending <= result_spike_i;
          completion_pending <= result_last_i;
        end
      end
      if (event_valid_o && event_ready_i) begin
        if (spike_pending) spike_pending <= 0;
        else begin
          completion_pending <= 0;
          bin_open <= 0;
        end
      end
    end
  end
endmodule
