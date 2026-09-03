`timescale 1ns/1ps
// Stream wrapper for a direct resident actor. Input data packets are complete
// presynaptic spike vectors; an input completion packet commits the population.
// The held result is emitted as one vector packet followed by one completion
// packet, preserving the existing fork/join completion-token contract.
module streaming_resident_channelized_plif_actor #(
  parameter integer INPUT_CHANNELS = 1,
  parameter integer INPUT_WIDTH = 4,
  parameter integer INPUT_HEIGHT = 4,
  parameter integer OUTPUT_CHANNELS = 1,
  parameter integer OUTPUT_WIDTH = 4,
  parameter integer OUTPUT_HEIGHT = 4,
  parameter integer SPATIAL_TILE_WIDTH =
    (OUTPUT_WIDTH < 8) ? OUTPUT_WIDTH : 8,
  parameter integer SPATIAL_TILE_HEIGHT =
    (OUTPUT_HEIGHT < 8) ? OUTPUT_HEIGHT : 8,
  parameter integer GROUPS = 1,
  parameter integer KERNEL_WIDTH = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 1,
  parameter integer PAD_Y = 1,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer MEM_WIDTH = 16,
  parameter integer BETA_WIDTH = 16,
  parameter integer TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 16,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*INPUT_WIDTH*INPUT_HEIGHT,
  parameter integer OUTPUT_COUNT = OUTPUT_CHANNELS*OUTPUT_WIDTH*OUTPUT_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*
                                   KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [AGE_WIDTH-1:0] ADAPTATION_DURATION = '0
) (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [INPUT_COUNT-1:0] in_spike_vector_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [OUTPUT_COUNT-1:0] out_spike_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o,
  output logic error_o
);
  logic presynaptic_ready;
  logic completion_ready;
  logic result_valid;
  logic result_ready;
  logic [OUTPUT_COUNT-1:0] result_vector;
  logic [TAG_WIDTH-1:0] result_tag;

  assign in_ready_o = in_completion_i ? completion_ready : presynaptic_ready;

  tiled_resident_channelized_plif_actor #(
    .INPUT_CHANNELS(INPUT_CHANNELS), .INPUT_WIDTH(INPUT_WIDTH),
    .INPUT_HEIGHT(INPUT_HEIGHT), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
    .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
    .TILE_WIDTH(SPATIAL_TILE_WIDTH), .TILE_HEIGHT(SPATIAL_TILE_HEIGHT),
    .GROUPS(GROUPS), .KERNEL_WIDTH(KERNEL_WIDTH),
    .KERNEL_HEIGHT(KERNEL_HEIGHT), .STRIDE_X(STRIDE_X),
    .STRIDE_Y(STRIDE_Y), .DILATION_X(DILATION_X),
    .DILATION_Y(DILATION_Y), .PAD_X(PAD_X), .PAD_Y(PAD_Y),
    .WEIGHT_WIDTH(WEIGHT_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
    .MEM_WIDTH(MEM_WIDTH), .BETA_WIDTH(BETA_WIDTH), .TAG_WIDTH(TAG_WIDTH),
    .AGE_WIDTH(AGE_WIDTH), .ENABLE_INHIBITION(ENABLE_INHIBITION),
    .ENABLE_ADAPTATION(ENABLE_ADAPTATION), .KERNEL_WEIGHTS(KERNEL_WEIGHTS),
    .CHANNEL_BETAS(CHANNEL_BETAS), .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
    .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
    .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
    .ADAPTATION_DURATION(ADAPTATION_DURATION)
  ) actor (
    .clk, .reset,
    .presynaptic_valid_i(in_valid_i && !in_completion_i),
    .presynaptic_ready_o(presynaptic_ready),
    .presynaptic_spike_vector_i(in_spike_vector_i),
    .completion_valid_i(in_valid_i && in_completion_i),
    .completion_ready_o(completion_ready), .completion_tag_i(in_tag_i),
    .result_valid_o(result_valid), .result_ready_i(result_ready),
    .spike_vector_o(result_vector), .completion_tag_o(result_tag),
    .error_o(error_o)
  );

  resident_spike_vector_edge #(
    .VECTOR_WIDTH(OUTPUT_COUNT), .TAG_WIDTH(TAG_WIDTH)
  ) output_edge (
    .clk, .reset, .result_valid_i(result_valid), .result_ready_o(result_ready),
    .spike_vector_i(result_vector), .completion_tag_i(result_tag),
    .out_valid_o, .out_ready_i, .out_vector_o(out_spike_vector_o),
    .out_completion_o, .out_tag_o
  );
endmodule
