`timescale 1ns/1ps
// Technology-independent 1R1W actor-local SRAM boundary. RTL simulation uses
// the behavioral branch; physical full-chip builds must bind the black-box
// branch to a characterized compiler macro with matching latency and polarity.
module actor_local_state_sram #(
  parameter integer DATA_WIDTH = 64,
  parameter integer DEPTH = 256,
  parameter integer ADDRESS_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer USE_MACRO = 0
) (
  input logic clk,
  input logic read_enable_i,
  input logic [ADDRESS_WIDTH-1:0] read_address_i,
  output logic read_valid_o,
  output logic [DATA_WIDTH-1:0] read_data_o,
  input logic write_enable_i,
  input logic [ADDRESS_WIDTH-1:0] write_address_i,
  input logic [DATA_WIDTH-1:0] write_data_i
);
  generate if (USE_MACRO == 0) begin : behavioral
    logic [DATA_WIDTH-1:0] memory [0:DEPTH-1];
    always_ff @(posedge clk) begin
      read_valid_o <= read_enable_i;
      if (read_enable_i) read_data_o <= memory[read_address_i];
      if (write_enable_i) memory[write_address_i] <= write_data_i;
    end
  end else begin : compiled_macro
    eventspikeseg_1r1w_sram_macro #(
      .DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH), .ADDRESS_WIDTH(ADDRESS_WIDTH)
    ) macro (
      .clk, .read_enable_i, .read_address_i, .read_valid_o, .read_data_o,
      .write_enable_i, .write_address_i, .write_data_i
    );
  end endgenerate
endmodule

(* blackbox *) module eventspikeseg_1r1w_sram_macro #(
  parameter integer DATA_WIDTH = 64,
  parameter integer DEPTH = 256,
  parameter integer ADDRESS_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH)
) (
  input logic clk,
  input logic read_enable_i,
  input logic [ADDRESS_WIDTH-1:0] read_address_i,
  output logic read_valid_o,
  output logic [DATA_WIDTH-1:0] read_data_o,
  input logic write_enable_i,
  input logic [ADDRESS_WIDTH-1:0] write_address_i,
  input logic [DATA_WIDTH-1:0] write_data_i
);
endmodule
