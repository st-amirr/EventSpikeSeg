`timescale 1ns/1ps
// Small ordered elastic queue between one scatter output and its destination
// state bank. Per-bank order is the fixed-point accumulation order.
module contribution_fifo #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer DEPTH = 4,
  parameter integer POINTER_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer COUNT_WIDTH = $clog2(DEPTH+1)
) (
  input logic clk, input logic reset,
  input logic in_valid, output logic in_ready,
  input logic [PAYLOAD_WIDTH-1:0] in_payload,
  output logic out_valid, input logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic [COUNT_WIDTH-1:0] occupancy_o
);
  logic [PAYLOAD_WIDTH-1:0] memory [0:DEPTH-1];
  logic [POINTER_WIDTH-1:0] write_pointer_reg;
  logic [POINTER_WIDTH-1:0] read_pointer_reg;
  logic [COUNT_WIDTH-1:0] count_reg;
  logic push;
  logic pop;

  initial if (DEPTH <= 0) $error("contribution FIFO depth must be positive");

  assign in_ready = (count_reg < DEPTH) || (out_valid && out_ready);
  assign out_valid = count_reg != 0;
  assign out_payload = memory[read_pointer_reg];
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
        memory[write_pointer_reg] <= in_payload;
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
