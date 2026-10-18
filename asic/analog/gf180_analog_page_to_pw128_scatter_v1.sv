`timescale 1ns/1ps
// Connect a sorted 128-lane spike page to pointwise analog-weight selectors.
// Membrane values, weights, and contributions remain analog; this block only
// decodes categorical event addresses and preserves event multiplicity/tag.
module gf180_analog_channel_pixel_page_to_pw128_scatter_v1 (
  input  logic         clk,
  input  logic         reset,
  input  logic         page_valid_i,
  output logic         page_ready_o,
  input  logic [12:0]  pixel_index_i,
  input  logic [127:0] spike_bitmap_i,
  input  logic [7:0]   lane_count_i,
  input  logic         page_last_i,
  input  logic [23:0]  page_bin_tag_i,
  output logic         bin_complete_o,
  output logic [23:0]  completed_bin_tag_o,
  output logic         page_format_error_o,
  output logic         address_order_error_o,
  output logic         tag_mismatch_o,
  output logic         address_decode_error_o,
  output logic         selector_valid_o,
  input  logic         selector_ready_i,
  output logic [7:0]   output_channel_base_o,
  output logic [7:0]   input_channel_local_o,
  output logic         tap_index_o,
  output logic [9:0]   output_x_o,
  output logic [9:0]   output_y_o,
  output logic [1:0]   multiplicity_o,
  output logic [23:0]  bin_tag_o,
  output logic         selector_address_overflow_o,
  output logic         selector_channel_error_o
);
  logic page_event_valid, page_event_ready, page_event_completion;
  logic [25:0] page_event_channel;
  logic [23:0] page_event_tag;
  logic scatter_event_ready;
  logic scatter_event_valid;
  logic address_in_range;
  logic [31:0] pixel_remainder;
  logic [7:0] decoded_channel;
  logic [9:0] decoded_x, decoded_y;

  // The bitmap lane is the input channel; one page is the channel vector at
  // one pixel. This avoids a large full-address divide on every sparse event.
  always_comb begin
    address_in_range = (page_event_channel < 26'd128) && (pixel_index_i < 13'd4400);
    decoded_channel = page_event_channel[7:0];
    pixel_remainder = pixel_index_i % 13'd80;
    decoded_y = pixel_index_i / 13'd80;
    decoded_x = pixel_remainder[9:0];
  end

  assign scatter_event_valid = page_event_valid && !page_event_completion && address_in_range;
  assign page_event_ready = page_event_completion || !address_in_range || scatter_event_ready;
  assign address_decode_error_o = page_event_valid && !page_event_completion && !address_in_range;
  assign bin_complete_o = page_event_valid && page_event_completion;
  assign completed_bin_tag_o = page_event_tag;

  gf180_analog_spike_event_page128_v1 page (
    .clk, .reset,
    .page_valid_i, .page_ready_o,
    .page_base_i(26'd0), .spike_bitmap_i, .lane_count_i, .page_last_i, .page_bin_tag_i,
    .event_valid_o(page_event_valid), .event_ready_i(page_event_ready),
    .event_address_o(page_event_channel), .event_completion_o(page_event_completion),
    .event_bin_tag_o(page_event_tag),
    .page_format_error_o, .address_order_error_o, .tag_mismatch_o
  );

  gf180_analog_weight_event_scatter_pw128 scatter (
    .clk, .reset,
    .event_valid_i(scatter_event_valid), .event_ready_o(scatter_event_ready),
    .input_channel_i(decoded_channel), .input_x_i(decoded_x), .input_y_i(decoded_y),
    .multiplicity_i(2'd1), .bin_tag_i(page_event_tag),
    .contribution_valid_o(selector_valid_o), .contribution_ready_i(selector_ready_i),
    .output_channel_base_o, .input_channel_local_o, .tap_index_o,
    .output_x_o, .output_y_o, .multiplicity_o, .bin_tag_o,
    .address_overflow_o(selector_address_overflow_o),
    .channel_error_o(selector_channel_error_o)
  );
endmodule
