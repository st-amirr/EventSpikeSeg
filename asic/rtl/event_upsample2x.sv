`timescale 1ns/1ps
// Nearest-neighbor 2x event-address fanout. One input spike becomes the four
// coordinates (2x,2y), (2x+1,2y), (2x,2y+1), (2x+1,2y+1). A completion token
// is forwarded exactly once and is never expanded.
module event_upsample2x #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer X_LSB = 0,
  parameter integer X_WIDTH = 10,
  parameter integer Y_LSB = 10,
  parameter integer Y_WIDTH = 9
) (
  input  logic clk,
  input  logic reset,

  input  logic in_valid,
  output logic in_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in_payload,
  input  logic in_completion,
  input  logic [TAG_WIDTH-1:0] in_bin_tag,

  output logic out_valid,
  input  logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic coordinate_overflow_o
);
  logic [PAYLOAD_WIDTH-1:0] payload_reg;
  logic completion_reg;
  logic [TAG_WIDTH-1:0] bin_tag_reg;
  logic [3:0] pending_reg;
  integer selected_copy;
  integer expanded_x;
  integer expanded_y;
  integer max_x;
  integer max_y;

  assign in_ready = (pending_reg == 0);
  assign out_valid = (pending_reg != 0);
  assign out_completion = completion_reg;
  assign out_bin_tag = bin_tag_reg;

  always_comb begin
    selected_copy = 0;
    if (pending_reg[1]) selected_copy = 1;
    if (pending_reg[2]) selected_copy = 2;
    if (pending_reg[3]) selected_copy = 3;
    // Select the lowest pending copy so output order is deterministic.
    if (pending_reg[0]) selected_copy = 0;
    else if (pending_reg[1]) selected_copy = 1;
    else if (pending_reg[2]) selected_copy = 2;
    else if (pending_reg[3]) selected_copy = 3;

    out_payload = payload_reg;
    expanded_x = 2 * $unsigned(payload_reg[X_LSB +: X_WIDTH]) +
                 (selected_copy & 1);
    expanded_y = 2 * $unsigned(payload_reg[Y_LSB +: Y_WIDTH]) +
                 ((selected_copy >> 1) & 1);
    max_x = (1 << X_WIDTH) - 1;
    max_y = (1 << Y_WIDTH) - 1;
    coordinate_overflow_o = out_valid && !completion_reg &&
                            (expanded_x > max_x || expanded_y > max_y);
    if (!completion_reg) begin
      out_payload[X_LSB +: X_WIDTH] = expanded_x[X_WIDTH-1:0];
      out_payload[Y_LSB +: Y_WIDTH] = expanded_y[Y_WIDTH-1:0];
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      payload_reg <= '0;
      completion_reg <= 1'b0;
      bin_tag_reg <= '0;
      pending_reg <= '0;
    end else begin
      if (out_valid && out_ready)
        pending_reg[selected_copy] <= 1'b0;
      if (in_valid && in_ready) begin
        payload_reg <= in_payload;
        completion_reg <= in_completion;
        bin_tag_reg <= in_bin_tag;
        pending_reg <= in_completion ? 4'b0001 : 4'b1111;
      end
    end
  end
endmodule
