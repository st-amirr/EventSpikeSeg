`timescale 1ns/1ps
// One exact 3x3 kernel from EventSpikeSeg140k detail_stem output 0/input 0.
module primitive_140k_conv9_pnr_top (
  input logic clk,
  input logic [8:0] spike_vector_i,
  output logic [31:0] current_delta_o
);
  logic unused_clk;
  assign unused_clk = clk;
  resident_convolution_synapses #(
    .INPUT_CHANNELS(1), .INPUT_WIDTH(3), .INPUT_HEIGHT(3),
    .INPUT_TILE_X(-1), .INPUT_TILE_Y(-1),
    .OUTPUT_CHANNELS(1), .OUTPUT_WIDTH(1), .OUTPUT_HEIGHT(1),
    .OUTPUT_TILE_WIDTH(1), .OUTPUT_TILE_HEIGHT(1), .GROUPS(1),
    .KERNEL_WIDTH(3), .KERNEL_HEIGHT(3), .PAD_X(1), .PAD_Y(1),
    .KERNEL_WEIGHTS({
      24'sh10ab56, 24'sh127ff6, 24'sh10425d,
      24'sh0c709d, 24'sh0bb3ec, 24'sh099d95,
      24'shffd442, 24'sh0063b7, 24'sh00ac56
    })
  ) synapses (.spike_vector_i(spike_vector_i), .current_delta_o(current_delta_o));
endmodule
