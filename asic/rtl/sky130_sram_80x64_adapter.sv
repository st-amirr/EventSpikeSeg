`timescale 1ns/1ps
// Fixed actor-tile binding for the characterized SKY130 OpenRAM 80x64 macro.
// This adapter is intentionally not a full-model bank-selection policy.
`ifdef EVENTSPIKESEG_EXTERNAL_SRAM_MACRO
module eventspikeseg_1rw_sram_macro #(
  parameter integer DATA_WIDTH = 64,
  parameter integer DEPTH = 64,
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
  logic [5:0] macro_address;
  logic [79:0] macro_write_data;
  logic [79:0] macro_read_data;

`ifndef SYNTHESIS
  initial begin
    if (DATA_WIDTH > 80) $error("SKY130 actor-tile SRAM width exceeds 80 bits");
    if (DEPTH > 64) $error("SKY130 actor-tile SRAM depth exceeds 64 words");
  end
`endif

  always_comb begin
    macro_address = write_enable_i ? write_address_i : read_address_i;
    macro_write_data = '0;
    macro_write_data[DATA_WIDTH-1:0] = write_data_i;
    read_data_o = macro_read_data[DATA_WIDTH-1:0];
  end

  always_ff @(posedge clk) read_valid_o <= read_enable_i;

  sky130_sram_1rw1r_80x64_8 macro (
    .clk0(clk),
    .csb0(!(read_enable_i || write_enable_i)),
    .web0(!write_enable_i),
    .wmask0(10'b1111111111),
    .addr0(macro_address),
    .din0(macro_write_data),
    .dout0(macro_read_data),
    .clk1(clk),
    .csb1(1'b1),
    .addr1(6'b0),
    .dout1()
  );
endmodule

`ifndef EVENTSPIKESEG_EXTERNAL_SRAM_MODEL
(* blackbox *) module sky130_sram_1rw1r_80x64_8 (
  input logic clk0,
  input logic csb0,
  input logic web0,
  input logic [9:0] wmask0,
  input logic [5:0] addr0,
  input logic [79:0] din0,
  output logic [79:0] dout0,
  input logic clk1,
  input logic csb1,
  input logic [5:0] addr1,
  output logic [79:0] dout1
);
endmodule
`endif
`endif
