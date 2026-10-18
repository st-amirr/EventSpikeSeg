`timescale 1ns/1ps
// One 128-neuron page, implemented as four contiguous 32-neuron scan banks.
// The banks run in parallel and a three-node sorted merge tree restores the
// canonical address order. Membrane state and thresholding remain analog.
module gf180_analog_spike_event_page128_v1 (
  input logic clk,
  input logic reset,
  input logic page_valid_i,
  output logic page_ready_o,
  input logic [25:0] page_base_i,
  input logic [127:0] spike_bitmap_i,
  input logic [7:0] lane_count_i,
  input logic page_last_i,
  input logic [23:0] page_bin_tag_i,
  output logic event_valid_o,
  input logic event_ready_i,
  output logic [25:0] event_address_o,
  output logic event_completion_o,
  output logic [23:0] event_bin_tag_o,
  output logic page_format_error_o,
  output logic address_order_error_o,
  output logic tag_mismatch_o
);
  logic [3:0] bank_page_ready;
  logic [3:0] bank_event_valid;
  logic [3:0] bank_event_ready;
  logic [3:0] bank_merge_ready;
  logic [3:0] bank_completion;
  logic [3:0] bank_tag_error;
  logic [3:0] bank_order_error;
  logic [3:0] bank_overflow_error;
  logic [3:0] bank_lane_error;
  logic [25:0] bank_address [0:3];
  logic [23:0] bank_tag [0:3];
  logic [5:0] bank_lane_count [0:3];
  logic [25:0] bank_base [0:3];
  logic [31:0] bank_payload [0:3];
  logic [23:0] bank_payload_tag [0:3];

  logic m01_valid, m01_ready, m01_completion;
  logic m23_valid, m23_ready, m23_completion;
  logic root_valid, root_completion;
  logic [31:0] m01_payload, m23_payload, root_payload;
  logic [23:0] m01_tag, m23_tag, root_tag;
  logic m01_tag_error, m23_tag_error, root_tag_error;
  logic m01_order_error, m23_order_error, root_order_error;
  logic m01_overflow, m23_overflow, root_overflow;
  logic input_format_error;
  logic [26:0] last_address_extended;
  integer bank;

  always_comb begin
    input_format_error = (lane_count_i == 0) || (lane_count_i > 128);
    last_address_extended = {1'b0, page_base_i} + lane_count_i - 1'b1;
    if (lane_count_i != 0 && last_address_extended > 27'h3ffffff)
      input_format_error = 1'b1;
    for (bank = 0; bank < 4; bank = bank + 1) begin
      if (lane_count_i <= bank * 32)
        bank_lane_count[bank] = 0;
      else if (lane_count_i >= (bank + 1) * 32)
        bank_lane_count[bank] = 32;
      else
        bank_lane_count[bank] = lane_count_i - bank * 32;
      bank_base[bank] = page_base_i + bank * 32;
      bank_payload[bank] = {6'b0, bank_address[bank]};
      bank_payload_tag[bank] = bank_tag[bank];
    end
    page_ready_o = !page_format_error_o && (&bank_page_ready);
    bank_event_ready = bank_merge_ready;
    event_valid_o = root_valid && !page_format_error_o &&
      !(|bank_tag_error) && !(|bank_order_error) && !(|bank_overflow_error) &&
      !(|bank_lane_error) && !m01_tag_error && !m23_tag_error &&
      !root_tag_error && !m01_order_error && !m23_order_error &&
      !root_order_error && !m01_overflow && !m23_overflow && !root_overflow;
    event_completion_o = event_valid_o && root_completion;
    event_address_o = root_payload[25:0];
    event_bin_tag_o = root_tag;
    address_order_error_o = (|bank_order_error) || m01_order_error ||
      m23_order_error || root_order_error;
    tag_mismatch_o = (|bank_tag_error) || m01_tag_error || m23_tag_error ||
      root_tag_error;
  end

  always_ff @(posedge clk) begin
    if (reset) page_format_error_o <= 1'b0;
    else if (page_valid_i && page_ready_o && input_format_error)
      page_format_error_o <= 1'b1;
  end

  genvar g;
  generate for (g = 0; g < 4; g = g + 1) begin : bank_gen
    gf180_analog_spike_event_serializer32_v1 #(
      .ADDRESS_WIDTH(26), .TAG_WIDTH(24), .PAGE_WIDTH(32), .PAGE_STRIDE(32)
    ) bank_serializer (
      .clk, .reset,
      .page_valid_i(page_valid_i && page_ready_o),
      .page_ready_o(bank_page_ready[g]),
      .page_base_i(bank_base[g]),
      .spike_bitmap_i(spike_bitmap_i[g*32 +: 32]),
      .lane_count_i(bank_lane_count[g]),
      .page_last_i, .page_bin_tag_i,
      .event_valid_o(bank_event_valid[g]),
      .event_ready_i(bank_event_ready[g]),
      .event_address_o(bank_address[g]),
      .event_completion_o(bank_completion[g]),
      .event_bin_tag_o(bank_tag[g]),
      .tag_mismatch_o(bank_tag_error[g]),
      .address_order_error_o(bank_order_error[g]),
      .address_overflow_o(bank_overflow_error[g]),
      .lane_count_error_o(bank_lane_error[g])
    );
  end endgenerate

  gf180_analog_binary_event_merge_sorted2 #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .KEY_LSB(0), .KEY_WIDTH(26)
  ) merge_01 (
    .clk, .reset,
    .in0_valid_i(bank_event_valid[0]), .in0_ready_o(bank_merge_ready[0]),
    .in0_payload_i(bank_payload[0]), .in0_completion_i(bank_completion[0]),
    .in0_bin_tag_i(bank_payload_tag[0]),
    .in1_valid_i(bank_event_valid[1]), .in1_ready_o(bank_merge_ready[1]),
    .in1_payload_i(bank_payload[1]), .in1_completion_i(bank_completion[1]),
    .in1_bin_tag_i(bank_payload_tag[1]),
    .out_valid_o(m01_valid), .out_ready_i(root_ready_01),
    .out_payload_o(m01_payload), .out_completion_o(m01_completion),
    .out_bin_tag_o(m01_tag), .tag_mismatch_o(m01_tag_error),
    .address_order_error_o(m01_order_error), .overflow_o(m01_overflow)
  );

  gf180_analog_binary_event_merge_sorted2 #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .KEY_LSB(0), .KEY_WIDTH(26)
  ) merge_23 (
    .clk, .reset,
    .in0_valid_i(bank_event_valid[2]), .in0_ready_o(bank_merge_ready[2]),
    .in0_payload_i(bank_payload[2]), .in0_completion_i(bank_completion[2]),
    .in0_bin_tag_i(bank_payload_tag[2]),
    .in1_valid_i(bank_event_valid[3]), .in1_ready_o(bank_merge_ready[3]),
    .in1_payload_i(bank_payload[3]), .in1_completion_i(bank_completion[3]),
    .in1_bin_tag_i(bank_payload_tag[3]),
    .out_valid_o(m23_valid), .out_ready_i(root_ready_23),
    .out_payload_o(m23_payload), .out_completion_o(m23_completion),
    .out_bin_tag_o(m23_tag), .tag_mismatch_o(m23_tag_error),
    .address_order_error_o(m23_order_error), .overflow_o(m23_overflow)
  );

  logic root_ready_01, root_ready_23;
  gf180_analog_binary_event_merge_sorted2 #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .KEY_LSB(0), .KEY_WIDTH(26)
  ) merge_root (
    .clk, .reset,
    .in0_valid_i(m01_valid), .in0_ready_o(root_ready_01),
    .in0_payload_i(m01_payload), .in0_completion_i(m01_completion),
    .in0_bin_tag_i(m01_tag),
    .in1_valid_i(m23_valid), .in1_ready_o(root_ready_23),
    .in1_payload_i(m23_payload), .in1_completion_i(m23_completion),
    .in1_bin_tag_i(m23_tag),
    .out_valid_o(root_valid), .out_ready_i(event_ready_i),
    .out_payload_o(root_payload), .out_completion_o(root_completion),
    .out_bin_tag_o(root_tag), .tag_mismatch_o(root_tag_error),
    .address_order_error_o(root_order_error), .overflow_o(root_overflow)
  );
endmodule
