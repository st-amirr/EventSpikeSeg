`timescale 1ns/1ps
// Predictive ASAP7 article-PPA binding for the reduced-spatial checkpoint DAG.
// Native storage is accounted separately by the exact SRAM banking manifest.
module eventspikeseg_1rw_sram_macro #(
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
  localparam integer MACRO_WIDTH = 128;
  localparam integer WIDTH_TILES = (DATA_WIDTH + MACRO_WIDTH - 1) / MACRO_WIDTH;
  localparam integer PADDED_WIDTH = WIDTH_TILES * MACRO_WIDTH;
  logic [PADDED_WIDTH-1:0] macro_read_data;
  logic [PADDED_WIDTH-1:0] padded_write_data;
  logic [10:0] selected_address;
  integer address_bit;

  initial begin
    if (DEPTH > 2048 || DATA_WIDTH > 256)
      $error("ASAP7 reduced-DAG SRAM binding exceeds 2048x256 support");
  end

  always_comb begin
    selected_address = '0;
    for (address_bit = 0; address_bit < ADDRESS_WIDTH; address_bit = address_bit + 1)
      selected_address[address_bit] = write_enable_i ?
        write_address_i[address_bit] : read_address_i[address_bit];
    padded_write_data = '0;
    padded_write_data[DATA_WIDTH-1:0] = write_data_i;
    read_data_o = macro_read_data[DATA_WIDTH-1:0];
  end

  always_ff @(posedge clk) read_valid_o <= read_enable_i;

  generate for (genvar tile = 0; tile < WIDTH_TILES; tile = tile + 1) begin : width_tile
    if (DEPTH <= 512) begin : depth_512
      fakeram_512x128 memory (
        .rd_out(macro_read_data[tile*MACRO_WIDTH +: MACRO_WIDTH]),
        .addr_in(selected_address[8:0]), .we_in(write_enable_i),
        .wd_in(padded_write_data[tile*MACRO_WIDTH +: MACRO_WIDTH]),
        .clk, .ce_in(read_enable_i || write_enable_i)
      );
    end else begin : depth_2048
      fakeram_2048x128 memory (
        .rd_out(macro_read_data[tile*MACRO_WIDTH +: MACRO_WIDTH]),
        .addr_in(selected_address), .we_in(write_enable_i),
        .wd_in(padded_write_data[tile*MACRO_WIDTH +: MACRO_WIDTH]),
        .clk, .ce_in(read_enable_i || write_enable_i)
      );
    end
  end endgenerate
endmodule
