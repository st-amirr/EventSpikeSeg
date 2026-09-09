`timescale 1ns/1ps
// Fully-spiking EventSpikeSegXL attention. Each Q/K/V actor emits one bitmap and
// then a same-bin completion. This block retains all three maps until rendezvous.
module resident_spike_mask_attention #(
  parameter integer HEADS = 4,
  parameter integer HEAD_DIM = 8,
  parameter integer SPATIAL_COUNT = 1,
  parameter integer TAG_WIDTH = 24,
  parameter logic [HEADS*24-1:0] HEAD_THRESHOLDS = {HEADS{24'h010000}},
  parameter integer VECTOR_WIDTH = HEADS*HEAD_DIM*SPATIAL_COUNT
) (
  input logic clk, input logic reset,
  input logic in_q_valid_i, output logic in_q_ready_o,
  input logic [VECTOR_WIDTH-1:0] in_q_vector_i,
  input logic in_q_completion_i, input logic [TAG_WIDTH-1:0] in_q_tag_i,
  input logic in_k_valid_i, output logic in_k_ready_o,
  input logic [VECTOR_WIDTH-1:0] in_k_vector_i,
  input logic in_k_completion_i, input logic [TAG_WIDTH-1:0] in_k_tag_i,
  input logic in_v_valid_i, output logic in_v_ready_o,
  input logic [VECTOR_WIDTH-1:0] in_v_vector_i,
  input logic in_v_completion_i, input logic [TAG_WIDTH-1:0] in_v_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [VECTOR_WIDTH-1:0] out_v_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o,
  output logic tag_mismatch_o
);
  logic [VECTOR_WIDTH-1:0] q_reg, k_reg, v_reg;
  logic q_data_seen_reg, k_data_seen_reg, v_data_seen_reg;
  logic q_done_reg, k_done_reg, v_done_reg;
  logic [TAG_WIDTH-1:0] q_tag_reg, k_tag_reg, v_tag_reg;
  logic completion_phase_reg;
  wire rendezvous = q_data_seen_reg && k_data_seen_reg && v_data_seen_reg
                  && q_done_reg && k_done_reg && v_done_reg;
  wire tags_match = (q_tag_reg == k_tag_reg) && (q_tag_reg == v_tag_reg);

  integer channel_index;
  integer spatial_index;
  integer lane;
  integer coincidences;
  logic [23:0] threshold_q;
  always_comb begin
    out_v_vector_o = '0;
    for (channel_index = 0; channel_index < HEADS*HEAD_DIM; channel_index = channel_index + 1)
      for (spatial_index = 0; spatial_index < SPATIAL_COUNT; spatial_index = spatial_index + 1) begin
      coincidences = 0;
      for (lane = 0; lane < HEAD_DIM; lane = lane + 1)
        coincidences = coincidences
          + (q_reg[(((channel_index/HEAD_DIM)*HEAD_DIM+lane)*SPATIAL_COUNT)+spatial_index]
             & k_reg[(((channel_index/HEAD_DIM)*HEAD_DIM+lane)*SPATIAL_COUNT)+spatial_index]);
      threshold_q = HEAD_THRESHOLDS >> ((channel_index / HEAD_DIM) * 24);
      out_v_vector_o[channel_index*SPATIAL_COUNT+spatial_index] =
        v_reg[channel_index*SPATIAL_COUNT+spatial_index]
        & ((coincidences << 16) >= threshold_q);
      end
  end

  assign in_q_ready_o = !rendezvous && (in_q_completion_i ? !q_done_reg : !q_data_seen_reg);
  assign in_k_ready_o = !rendezvous && (in_k_completion_i ? !k_done_reg : !k_data_seen_reg);
  assign in_v_ready_o = !rendezvous && (in_v_completion_i ? !v_done_reg : !v_data_seen_reg);
  assign out_valid_o = rendezvous && tags_match;
  assign out_completion_o = completion_phase_reg;
  assign out_tag_o = q_tag_reg;

  always_ff @(posedge clk) begin
    if (reset) begin
      q_reg <= '0; k_reg <= '0; v_reg <= '0;
      q_data_seen_reg <= 1'b0; k_data_seen_reg <= 1'b0; v_data_seen_reg <= 1'b0;
      q_done_reg <= 1'b0; k_done_reg <= 1'b0; v_done_reg <= 1'b0;
      q_tag_reg <= '0; k_tag_reg <= '0; v_tag_reg <= '0;
      completion_phase_reg <= 1'b0;
      tag_mismatch_o <= 1'b0;
    end else begin
      if (in_q_valid_i && in_q_ready_o) begin
        if (in_q_completion_i) begin q_done_reg <= 1'b1; q_tag_reg <= in_q_tag_i; end
        else begin q_reg <= in_q_vector_i; q_data_seen_reg <= 1'b1; end
      end
      if (in_k_valid_i && in_k_ready_o) begin
        if (in_k_completion_i) begin k_done_reg <= 1'b1; k_tag_reg <= in_k_tag_i; end
        else begin k_reg <= in_k_vector_i; k_data_seen_reg <= 1'b1; end
      end
      if (in_v_valid_i && in_v_ready_o) begin
        if (in_v_completion_i) begin v_done_reg <= 1'b1; v_tag_reg <= in_v_tag_i; end
        else begin v_reg <= in_v_vector_i; v_data_seen_reg <= 1'b1; end
      end
      if (rendezvous && !tags_match)
        tag_mismatch_o <= 1'b1;
      if (out_valid_o && out_ready_i) begin
        if (!completion_phase_reg)
          completion_phase_reg <= 1'b1;
        else begin
          q_data_seen_reg <= 1'b0; k_data_seen_reg <= 1'b0; v_data_seen_reg <= 1'b0;
          q_done_reg <= 1'b0; k_done_reg <= 1'b0; v_done_reg <= 1'b0;
          completion_phase_reg <= 1'b0;
        end
      end
    end
  end

  initial begin
    if (HEADS < 1 || HEAD_DIM < 1 || SPATIAL_COUNT < 1)
      $fatal(1, "resident_spike_mask_attention dimensions must be positive");
  end
endmodule
