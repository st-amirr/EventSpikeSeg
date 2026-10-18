`timescale 1ns/1ps
// Low-area actor output serializer. The analog comparators produce a 128-bit
// page bitmap; this block scans lanes in ascending order and emits set lanes.
// A registered lane index replaces the 128-entry priority scan to keep the
// physical control logic compact. At 50 MHz, the worst-case scan is 2.56 us
// per 128-neuron page (excluding backpressure).
module gf180_analog_spike_event_serializer128_v3 #(
  parameter integer ADDRESS_WIDTH = 26,
  parameter integer TAG_WIDTH = 24,
  parameter integer PAGE_WIDTH = 128,
  parameter integer PAGE_STRIDE = 128,
  parameter integer MAX_ADDRESS = (1 << ADDRESS_WIDTH) - 1
) (
  input logic clk,
  input logic reset,
  input logic page_valid_i,
  output logic page_ready_o,
  input logic [ADDRESS_WIDTH-1:0] page_base_i,
  input logic [PAGE_WIDTH-1:0] spike_bitmap_i,
  input logic [7:0] lane_count_i,
  input logic page_last_i,
  input logic [TAG_WIDTH-1:0] page_bin_tag_i,
  output logic event_valid_o,
  input logic event_ready_i,
  output logic [ADDRESS_WIDTH-1:0] event_address_o,
  output logic event_completion_o,
  output logic [TAG_WIDTH-1:0] event_bin_tag_o,
  output logic tag_mismatch_o,
  output logic address_order_error_o,
  output logic address_overflow_o,
  output logic lane_count_error_o
);
  logic page_active_reg;
  logic [PAGE_WIDTH-1:0] bitmap_reg;
  logic [ADDRESS_WIDTH-1:0] page_base_reg;
  logic [7:0] lane_count_reg;
  logic [7:0] lane_index_reg;
  logic page_last_reg;
  logic [TAG_WIDTH-1:0] bin_tag_reg;
  logic bin_tag_seen_reg;
  logic previous_page_seen_reg;
  logic [ADDRESS_WIDTH-1:0] previous_page_base_reg;
  logic lane_valid;
  logic selected_spike;
  logic page_scan_done;
  logic [ADDRESS_WIDTH:0] selected_address_extended;
  logic fault_active;
  integer check_lane;

  assign lane_valid = lane_index_reg < lane_count_reg;
  assign selected_spike = lane_valid && bitmap_reg[lane_index_reg];
  assign page_scan_done = !lane_valid;
  assign selected_address_extended = {1'b0, page_base_reg} + lane_index_reg;
  assign fault_active = tag_mismatch_o || address_order_error_o ||
                        address_overflow_o || lane_count_error_o;

  always_comb begin
    page_ready_o = !fault_active &&
      (!page_active_reg || (page_scan_done && !page_last_reg));
    event_valid_o = !fault_active && page_active_reg &&
      (selected_spike || (page_scan_done && page_last_reg));
    event_completion_o = event_valid_o && page_scan_done && page_last_reg;
    event_address_o = selected_address_extended[ADDRESS_WIDTH-1:0];
    event_bin_tag_o = bin_tag_reg;
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      page_active_reg <= 1'b0;
      bitmap_reg <= '0;
      page_base_reg <= '0;
      lane_count_reg <= '0;
      lane_index_reg <= '0;
      page_last_reg <= 1'b0;
      bin_tag_reg <= '0;
      bin_tag_seen_reg <= 1'b0;
      previous_page_seen_reg <= 1'b0;
      previous_page_base_reg <= '0;
      tag_mismatch_o <= 1'b0;
      address_order_error_o <= 1'b0;
      address_overflow_o <= 1'b0;
      lane_count_error_o <= 1'b0;
    end else begin
      if (page_valid_i && page_ready_o) begin
        page_active_reg <= 1'b1;
        bitmap_reg <= spike_bitmap_i;
        page_base_reg <= page_base_i;
        lane_count_reg <= lane_count_i;
        lane_index_reg <= '0;
        page_last_reg <= page_last_i;
        previous_page_base_reg <= page_base_i;
        previous_page_seen_reg <= 1'b1;
        if (lane_count_i > PAGE_WIDTH) lane_count_error_o <= 1'b1;
        if (!bin_tag_seen_reg) begin
          bin_tag_reg <= page_bin_tag_i;
          bin_tag_seen_reg <= 1'b1;
        end else if (bin_tag_reg != page_bin_tag_i) begin
          tag_mismatch_o <= 1'b1;
        end
        if (previous_page_seen_reg &&
            ({1'b0, page_base_i} <
             ({1'b0, previous_page_base_reg} + PAGE_STRIDE)))
          address_order_error_o <= 1'b1;
        for (check_lane = 0; check_lane < PAGE_WIDTH;
             check_lane = check_lane + 1) begin
          if (spike_bitmap_i[check_lane] && (check_lane < lane_count_i) &&
              (({1'b0, page_base_i} + check_lane) > MAX_ADDRESS))
            address_overflow_o <= 1'b1;
        end
      end

      if (page_active_reg && !selected_spike && !page_scan_done) begin
        lane_index_reg <= lane_index_reg + 1'b1;
      end else if (event_valid_o && event_ready_i) begin
        if (event_completion_o) begin
          page_active_reg <= 1'b0;
          bitmap_reg <= '0;
          lane_count_reg <= '0;
          lane_index_reg <= '0;
          page_last_reg <= 1'b0;
          bin_tag_seen_reg <= 1'b0;
          previous_page_seen_reg <= 1'b0;
        end else begin
          lane_index_reg <= lane_index_reg + 1'b1;
        end
      end
    end
  end

  initial begin
    if (PAGE_WIDTH <= 0 || PAGE_STRIDE < PAGE_WIDTH)
      $error("serializer pages must have positive width and non-overlapping stride");
    if (ADDRESS_WIDTH <= 0 || TAG_WIDTH <= 0)
      $error("serializer address and bin-tag widths must be positive");
  end
endmodule
