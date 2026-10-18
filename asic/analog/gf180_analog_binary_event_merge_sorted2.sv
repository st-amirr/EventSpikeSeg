`timescale 1ns/1ps
// Bounded-state binary residual OR for two address-sorted sparse event streams.
// Each input must emit strictly increasing canonical addresses within a bin.
// The merge holds one packet per input, emits the lower address, and collapses
// equal addresses to one event. No event-count-sized SRAM or MAX_EVENTS cap.
module gf180_analog_binary_event_merge_sorted2 #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer KEY_LSB = 0,
  parameter integer KEY_WIDTH = 26
) (
  input logic clk,
  input logic reset,
  input logic in0_valid_i,
  output logic in0_ready_o,
  input logic [PAYLOAD_WIDTH-1:0] in0_payload_i,
  input logic in0_completion_i,
  input logic [TAG_WIDTH-1:0] in0_bin_tag_i,
  input logic in1_valid_i,
  output logic in1_ready_o,
  input logic [PAYLOAD_WIDTH-1:0] in1_payload_i,
  input logic in1_completion_i,
  input logic [TAG_WIDTH-1:0] in1_bin_tag_i,
  output logic out_valid_o,
  input logic out_ready_i,
  output logic [PAYLOAD_WIDTH-1:0] out_payload_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_bin_tag_o,
  output logic tag_mismatch_o,
  output logic address_order_error_o,
  output logic overflow_o
);
  logic head0_valid_reg, head1_valid_reg;
  logic [PAYLOAD_WIDTH-1:0] head0_payload_reg, head1_payload_reg;
  logic [TAG_WIDTH-1:0] head0_tag_reg, head1_tag_reg;
  logic input0_done_reg, input1_done_reg;
  logic [TAG_WIDTH-1:0] done0_tag_reg, done1_tag_reg;
  logic input0_tag_seen_reg, input1_tag_seen_reg;
  logic [TAG_WIDTH-1:0] input0_tag_reg, input1_tag_reg;
  logic input0_last_seen_reg, input1_last_seen_reg;
  logic [KEY_WIDTH-1:0] input0_last_key_reg, input1_last_key_reg;
  logic clear_head0, clear_head1;
  logic fault_active;

  function automatic [KEY_WIDTH-1:0] packet_key(
    input logic [PAYLOAD_WIDTH-1:0] packet
  );
    packet_key = packet[KEY_LSB +: KEY_WIDTH];
  endfunction

  assign fault_active = tag_mismatch_o || address_order_error_o || overflow_o;
  assign in0_ready_o = !head0_valid_reg && !input0_done_reg && !fault_active;
  assign in1_ready_o = !head1_valid_reg && !input1_done_reg && !fault_active;
  assign overflow_o = 1'b0;

  always_comb begin
    out_valid_o = 1'b0;
    out_payload_o = '0;
    out_completion_o = 1'b0;
    out_bin_tag_o = done0_tag_reg;
    clear_head0 = 1'b0;
    clear_head1 = 1'b0;

    if (!fault_active) begin
      if (head0_valid_reg && head1_valid_reg &&
          head0_tag_reg == head1_tag_reg) begin
        out_valid_o = 1'b1;
        out_bin_tag_o = head0_tag_reg;
        if (packet_key(head0_payload_reg) <= packet_key(head1_payload_reg)) begin
          out_payload_o = head0_payload_reg;
          clear_head0 = 1'b1;
          if (packet_key(head0_payload_reg) == packet_key(head1_payload_reg))
            clear_head1 = 1'b1;
        end else begin
          out_payload_o = head1_payload_reg;
          clear_head1 = 1'b1;
        end
      end else if (head0_valid_reg && input1_done_reg &&
                   head0_tag_reg == done1_tag_reg) begin
        out_valid_o = 1'b1;
        out_payload_o = head0_payload_reg;
        out_bin_tag_o = head0_tag_reg;
        clear_head0 = 1'b1;
      end else if (head1_valid_reg && input0_done_reg &&
                   head1_tag_reg == done0_tag_reg) begin
        out_valid_o = 1'b1;
        out_payload_o = head1_payload_reg;
        out_bin_tag_o = head1_tag_reg;
        clear_head1 = 1'b1;
      end else if (!head0_valid_reg && !head1_valid_reg &&
                   input0_done_reg && input1_done_reg &&
                   done0_tag_reg == done1_tag_reg) begin
        out_valid_o = 1'b1;
        out_completion_o = 1'b1;
        out_bin_tag_o = done0_tag_reg;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      head0_valid_reg <= 1'b0;
      head1_valid_reg <= 1'b0;
      head0_payload_reg <= '0;
      head1_payload_reg <= '0;
      head0_tag_reg <= '0;
      head1_tag_reg <= '0;
      input0_done_reg <= 1'b0;
      input1_done_reg <= 1'b0;
      done0_tag_reg <= '0;
      done1_tag_reg <= '0;
      input0_tag_seen_reg <= 1'b0;
      input1_tag_seen_reg <= 1'b0;
      input0_tag_reg <= '0;
      input1_tag_reg <= '0;
      input0_last_seen_reg <= 1'b0;
      input1_last_seen_reg <= 1'b0;
      input0_last_key_reg <= '0;
      input1_last_key_reg <= '0;
      tag_mismatch_o <= 1'b0;
      address_order_error_o <= 1'b0;
    end else begin
      if (in0_valid_i && in0_ready_o) begin
        if (in0_completion_i) begin
          input0_done_reg <= 1'b1;
          done0_tag_reg <= in0_bin_tag_i;
          if (input0_tag_seen_reg && input0_tag_reg != in0_bin_tag_i)
            tag_mismatch_o <= 1'b1;
          if (input1_done_reg && done1_tag_reg != in0_bin_tag_i)
            tag_mismatch_o <= 1'b1;
        end else begin
          head0_valid_reg <= 1'b1;
          head0_payload_reg <= in0_payload_i;
          head0_tag_reg <= in0_bin_tag_i;
          if (input0_tag_seen_reg && input0_tag_reg != in0_bin_tag_i)
            tag_mismatch_o <= 1'b1;
          if (!input0_tag_seen_reg) begin
            input0_tag_seen_reg <= 1'b1;
            input0_tag_reg <= in0_bin_tag_i;
          end
          if (input0_last_seen_reg &&
              packet_key(in0_payload_i) <= input0_last_key_reg)
            address_order_error_o <= 1'b1;
          input0_last_seen_reg <= 1'b1;
          input0_last_key_reg <= packet_key(in0_payload_i);
          if (input1_done_reg && done1_tag_reg != in0_bin_tag_i)
            tag_mismatch_o <= 1'b1;
        end
      end

      if (in1_valid_i && in1_ready_o) begin
        if (in1_completion_i) begin
          input1_done_reg <= 1'b1;
          done1_tag_reg <= in1_bin_tag_i;
          if (input1_tag_seen_reg && input1_tag_reg != in1_bin_tag_i)
            tag_mismatch_o <= 1'b1;
          if (input0_done_reg && done0_tag_reg != in1_bin_tag_i)
            tag_mismatch_o <= 1'b1;
        end else begin
          head1_valid_reg <= 1'b1;
          head1_payload_reg <= in1_payload_i;
          head1_tag_reg <= in1_bin_tag_i;
          if (input1_tag_seen_reg && input1_tag_reg != in1_bin_tag_i)
            tag_mismatch_o <= 1'b1;
          if (!input1_tag_seen_reg) begin
            input1_tag_seen_reg <= 1'b1;
            input1_tag_reg <= in1_bin_tag_i;
          end
          if (input1_last_seen_reg &&
              packet_key(in1_payload_i) <= input1_last_key_reg)
            address_order_error_o <= 1'b1;
          input1_last_seen_reg <= 1'b1;
          input1_last_key_reg <= packet_key(in1_payload_i);
          if (input0_done_reg && done0_tag_reg != in1_bin_tag_i)
            tag_mismatch_o <= 1'b1;
        end
      end

      if (!tag_mismatch_o && !address_order_error_o) begin
        if (head0_valid_reg && head1_valid_reg &&
            head0_tag_reg != head1_tag_reg)
          tag_mismatch_o <= 1'b1;
        if (head0_valid_reg && input1_done_reg &&
            head0_tag_reg != done1_tag_reg)
          tag_mismatch_o <= 1'b1;
        if (head1_valid_reg && input0_done_reg &&
            head1_tag_reg != done0_tag_reg)
          tag_mismatch_o <= 1'b1;
        if (input0_done_reg && input1_done_reg &&
            done0_tag_reg != done1_tag_reg)
          tag_mismatch_o <= 1'b1;
      end

      if (out_valid_o && out_ready_i) begin
        if (out_completion_o) begin
          input0_done_reg <= 1'b0;
          input1_done_reg <= 1'b0;
          input0_tag_seen_reg <= 1'b0;
          input1_tag_seen_reg <= 1'b0;
          input0_last_seen_reg <= 1'b0;
          input1_last_seen_reg <= 1'b0;
        end else begin
          if (clear_head0) head0_valid_reg <= 1'b0;
          if (clear_head1) head1_valid_reg <= 1'b0;
        end
      end
    end
  end

  initial begin
    if (KEY_WIDTH <= 0 || KEY_LSB < 0 || KEY_LSB + KEY_WIDTH > PAYLOAD_WIDTH)
      $error("canonical event address key is outside packet payload");
  end
endmodule
