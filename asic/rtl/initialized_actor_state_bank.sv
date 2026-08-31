`timescale 1ns/1ps
// One actor-local state bank with deterministic sequence-start zeroization.
// Compiled SRAM bits have no architectural reset. All banks may scrub in
// parallel; the actor must not accept events until initialization_done_o.
module initialized_actor_state_bank #(
  parameter integer DATA_WIDTH = 65,
  parameter integer DEPTH = 256,
  parameter integer ADDRESS_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer USE_MACRO = 0
) (
  input logic clk,
  input logic reset,
  output logic initialization_done_o,

  input logic read_valid_i,
  output logic read_ready_o,
  input logic [ADDRESS_WIDTH-1:0] read_address_i,
  output logic read_response_valid_o,
  output logic [DATA_WIDTH-1:0] read_data_o,

  input logic write_valid_i,
  output logic write_ready_o,
  input logic [ADDRESS_WIDTH-1:0] write_address_i,
  input logic [DATA_WIDTH-1:0] write_data_i,
  output logic request_conflict_o
);
  logic [ADDRESS_WIDTH-1:0] scrub_address_reg;
  logic memory_read_enable;
  logic memory_read_valid;
  logic memory_write_enable;
  logic [ADDRESS_WIDTH-1:0] memory_write_address;
  logic [DATA_WIDTH-1:0] memory_write_data;

  assign read_ready_o = initialization_done_o && !write_valid_i;
  assign write_ready_o = initialization_done_o;
  assign memory_read_enable = read_valid_i && read_ready_o;
  assign memory_write_enable = !initialization_done_o || (write_valid_i && write_ready_o);
  assign memory_write_address = initialization_done_o ? write_address_i : scrub_address_reg;
  assign memory_write_data = initialization_done_o ? write_data_i : '0;
  assign read_response_valid_o = initialization_done_o && memory_read_valid;

  actor_local_state_sram #(
    .DATA_WIDTH(DATA_WIDTH),
    .DEPTH(DEPTH),
    .ADDRESS_WIDTH(ADDRESS_WIDTH),
    .USE_MACRO(USE_MACRO)
  ) state_memory (
    .clk,
    .read_enable_i(memory_read_enable),
    .read_address_i(read_address_i),
    .read_valid_o(memory_read_valid),
    .read_data_o,
    .write_enable_i(memory_write_enable),
    .write_address_i(memory_write_address),
    .write_data_i(memory_write_data)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      initialization_done_o <= 1'b0;
      scrub_address_reg <= '0;
      request_conflict_o <= 1'b0;
    end else begin
      if (!initialization_done_o) begin
        if ($unsigned(scrub_address_reg) + 1 >= DEPTH) begin
          initialization_done_o <= 1'b1;
          scrub_address_reg <= '0;
        end else begin
          scrub_address_reg <= scrub_address_reg + 1'b1;
        end
      end
      if (initialization_done_o && read_valid_i && write_valid_i)
        request_conflict_o <= 1'b1;
    end
  end
endmodule
