`timescale 1ns/1ps
// One fully connected 3x3 convolution output: nine hardwired synapse terms.
module xl_primitive_conv9_pnr_top (
  input  logic clk,
  input  logic [8:0] spike_vector_i,
  output logic [31:0] current_delta_o
);
  logic unused_clk;
  assign unused_clk = clk;
  resident_convolution_synapses #(
    .INPUT_CHANNELS(1),
    .INPUT_WIDTH(3), .INPUT_HEIGHT(3),
    .INPUT_TILE_X(-1), .INPUT_TILE_Y(-1),
    .OUTPUT_CHANNELS(1),
    .OUTPUT_WIDTH(1), .OUTPUT_HEIGHT(1),
    .OUTPUT_TILE_WIDTH(1), .OUTPUT_TILE_HEIGHT(1),
    .GROUPS(1),
    .KERNEL_WIDTH(3), .KERNEL_HEIGHT(3),
    .PAD_X(1), .PAD_Y(1),
    .KERNEL_WEIGHTS({
      24'sh000600, -24'sh000300, 24'sh000900,
      24'sh001200,  24'sh000800, -24'sh000500,
      24'sh000400,  24'sh000b00, 24'sh000700
    })
  ) synapses (
    .spike_vector_i(spike_vector_i),
    .current_delta_o(current_delta_o)
  );
endmodule
