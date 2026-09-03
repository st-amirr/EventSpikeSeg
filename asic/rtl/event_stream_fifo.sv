`timescale 1ns/1ps
// Lossless elastic FIFO for the unified spike/completion stream. Data and
// completion packets share one ordered queue, so a bin token cannot overtake
// any spike that belongs to that bin.
module event_stream_fifo #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer DEPTH = 2,
  parameter integer POINTER_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer COUNT_WIDTH = $clog2(DEPTH+1)
) (
  input logic clk, input logic reset,
  input logic in_valid, output logic in_ready,
  input logic [PAYLOAD_WIDTH-1:0] in_payload,
  input logic in_completion,
  input logic [TAG_WIDTH-1:0] in_bin_tag,
  output logic out_valid, input logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic [COUNT_WIDTH-1:0] occupancy_o
);
  logic [PAYLOAD_WIDTH-1:0] payload_memory [0:DEPTH-1];
  logic completion_memory [0:DEPTH-1];
  logic [TAG_WIDTH-1:0] tag_memory [0:DEPTH-1];
  logic [POINTER_WIDTH-1:0] write_pointer_reg;
  logic [POINTER_WIDTH-1:0] read_pointer_reg;
  logic [COUNT_WIDTH-1:0] count_reg;
  logic push;
  logic pop;

  initial begin
    if (DEPTH <= 0) $error("event stream FIFO depth must be positive");
  end

  // A full queue can replace its retiring head in the same cycle without a
  // throughput bubble. The consumer observes the old head before the write.
  assign in_ready = (count_reg < DEPTH) || (out_valid && out_ready);
  assign out_valid = count_reg != 0;
  assign out_payload = payload_memory[read_pointer_reg];
  assign out_completion = completion_memory[read_pointer_reg];
  assign out_bin_tag = tag_memory[read_pointer_reg];
  assign occupancy_o = count_reg;
  assign push = in_valid && in_ready;
  assign pop = out_valid && out_ready;

  always_ff @(posedge clk) begin
    if (reset) begin
      write_pointer_reg <= '0;
      read_pointer_reg <= '0;
      count_reg <= '0;
    end else begin
      if (push) begin
        payload_memory[write_pointer_reg] <= in_payload;
        completion_memory[write_pointer_reg] <= in_completion;
        tag_memory[write_pointer_reg] <= in_bin_tag;
        if (write_pointer_reg + 1 >= DEPTH) write_pointer_reg <= '0;
        else write_pointer_reg <= write_pointer_reg + 1'b1;
      end
      if (pop) begin
        if (read_pointer_reg + 1 >= DEPTH) read_pointer_reg <= '0;
        else read_pointer_reg <= read_pointer_reg + 1'b1;
      end
      case ({push, pop})
        2'b10: count_reg <= count_reg + 1'b1;
        2'b01: count_reg <= count_reg - 1'b1;
        default: count_reg <= count_reg;
      endcase
    end
  end
endmodule
