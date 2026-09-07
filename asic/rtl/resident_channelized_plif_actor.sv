`timescale 1ns/1ps
// Complete direct-state actor: a static convolutional synapse fabric feeds a
// fully resident PLIF population. One transaction is a binary spike bitmap;
// repeated transactions retain event multiplicity by accumulating repeatedly.
module resident_channelized_plif_actor #(
  parameter integer INPUT_CHANNELS = 1,
  parameter integer INPUT_WIDTH = 4,
  parameter integer INPUT_HEIGHT = 4,
  parameter integer INPUT_TILE_X = 0,
  parameter integer INPUT_TILE_Y = 0,
  parameter integer OUTPUT_CHANNELS = 1,
  parameter integer OUTPUT_WIDTH = 4,
  parameter integer OUTPUT_HEIGHT = 4,
  parameter integer OUTPUT_TILE_X = 0,
  parameter integer OUTPUT_TILE_Y = 0,
  parameter integer OUTPUT_TILE_WIDTH = OUTPUT_WIDTH,
  parameter integer OUTPUT_TILE_HEIGHT = OUTPUT_HEIGHT,
  parameter integer GROUPS = 1,
  parameter integer KERNEL_WIDTH = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 1,
  parameter integer PAD_Y = 1,
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer CURRENT_WIDTH = 32,
  parameter integer MEM_WIDTH = 24,
  parameter integer BETA_WIDTH = 24,
  parameter integer BETA_FRAC_BITS = 23,
  parameter integer TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 6,
  parameter integer AMPLITUDE_WIDTH = 19,
  parameter integer DURATION_WIDTH = 21,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer INPUT_SPATIAL_COUNT = INPUT_WIDTH*INPUT_HEIGHT,
  parameter integer OUTPUT_SPATIAL_COUNT = OUTPUT_TILE_WIDTH*OUTPUT_TILE_HEIGHT,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*INPUT_SPATIAL_COUNT,
  parameter integer DEST_COUNT = OUTPUT_CHANNELS*OUTPUT_SPATIAL_COUNT,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer TAP_COUNT = KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*TAP_COUNT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [AMPLITUDE_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [DURATION_WIDTH-1:0] ADAPTATION_DURATION = '0
) (
  input logic clk, input logic reset,
  input logic presynaptic_valid_i, output logic presynaptic_ready_o,
  input logic [INPUT_COUNT-1:0] presynaptic_spike_vector_i,
  input logic completion_valid_i, output logic completion_ready_o,
  input logic [TAG_WIDTH-1:0] completion_tag_i,
  output logic result_valid_o, input logic result_ready_i,
  output logic [DEST_COUNT-1:0] spike_vector_o,
  output logic [TAG_WIDTH-1:0] completion_tag_o,
  output logic error_o
);
  logic signed [DEST_COUNT*CURRENT_WIDTH-1:0] current_delta;
  logic population_dense_ready;
  logic population_completion_ready;
  logic unused_contribution_ready;

  resident_convolution_synapses #(
    .INPUT_CHANNELS(INPUT_CHANNELS), .INPUT_WIDTH(INPUT_WIDTH),
    .INPUT_HEIGHT(INPUT_HEIGHT), .INPUT_TILE_X(INPUT_TILE_X),
    .INPUT_TILE_Y(INPUT_TILE_Y), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
    .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
    .OUTPUT_TILE_X(OUTPUT_TILE_X), .OUTPUT_TILE_Y(OUTPUT_TILE_Y),
    .OUTPUT_TILE_WIDTH(OUTPUT_TILE_WIDTH),
    .OUTPUT_TILE_HEIGHT(OUTPUT_TILE_HEIGHT),
    .GROUPS(GROUPS), .KERNEL_WIDTH(KERNEL_WIDTH),
    .KERNEL_HEIGHT(KERNEL_HEIGHT), .STRIDE_X(STRIDE_X),
    .STRIDE_Y(STRIDE_Y), .DILATION_X(DILATION_X),
    .DILATION_Y(DILATION_Y), .PAD_X(PAD_X), .PAD_Y(PAD_Y),
    .WEIGHT_WIDTH(WEIGHT_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
    .KERNEL_WEIGHTS(KERNEL_WEIGHTS)
  ) synapses (
    .spike_vector_i(presynaptic_spike_vector_i),
    .current_delta_o(current_delta)
  );

  // Input and completion readiness are independent. The producer/wrapper selects
  // exactly one transaction type per cycle; making either ready depend on the
  // opposite valid signal creates a combinational loop when tiles are aggregated.
  assign presynaptic_ready_o = population_dense_ready;
  assign completion_ready_o = population_completion_ready;

  generate if (ENABLE_INHIBITION != 0 || ENABLE_ADAPTATION != 0) begin : mechanism
    resident_retinotopic_plif_population #(
      .DEST_COUNT(DEST_COUNT), .ADDRESS_WIDTH(ADDRESS_WIDTH),
      .CHANNEL_COUNT(OUTPUT_CHANNELS),
      .SPATIAL_DEST_COUNT(OUTPUT_SPATIAL_COUNT), .CONTRIBUTION_LANES(1),
      .WEIGHT_WIDTH(WEIGHT_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
      .MEM_WIDTH(MEM_WIDTH), .BETA_WIDTH(BETA_WIDTH),
      .BETA_FRAC_BITS(BETA_FRAC_BITS), .TAG_WIDTH(TAG_WIDTH),
      .AGE_WIDTH(AGE_WIDTH), .AMPLITUDE_WIDTH(AMPLITUDE_WIDTH),
      .DURATION_WIDTH(DURATION_WIDTH), .ENABLE_INHIBITION(ENABLE_INHIBITION),
      .ENABLE_ADAPTATION(ENABLE_ADAPTATION), .CHANNEL_BETAS(CHANNEL_BETAS),
      .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
      .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
      .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
      .ADAPTATION_DURATION(ADAPTATION_DURATION)
    ) population (
      .clk, .reset, .contribution_valid_i('0),
      .contribution_ready_o(unused_contribution_ready), .destination_i('0),
      .weight_i('0),
      .dense_current_valid_i(presynaptic_valid_i && presynaptic_ready_o),
      .dense_current_ready_o(population_dense_ready),
      .dense_current_delta_i(current_delta),
      .completion_valid_i(completion_valid_i && completion_ready_o),
      .completion_ready_o(population_completion_ready), .completion_tag_i,
      .spike_valid_o(result_valid_o), .spike_ready_i(result_ready_i),
      .spike_vector_o, .completion_tag_o, .address_error_o(error_o)
    );
  end else begin : ordinary
    resident_plif_population #(
      .DEST_COUNT(DEST_COUNT), .ADDRESS_WIDTH(ADDRESS_WIDTH),
      .CHANNEL_COUNT(OUTPUT_CHANNELS),
      .SPATIAL_DEST_COUNT(OUTPUT_SPATIAL_COUNT), .CONTRIBUTION_LANES(1),
      .WEIGHT_WIDTH(WEIGHT_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
      .MEM_WIDTH(MEM_WIDTH), .BETA_WIDTH(BETA_WIDTH),
      .BETA_FRAC_BITS(BETA_FRAC_BITS), .TAG_WIDTH(TAG_WIDTH),
      .CHANNEL_BETAS(CHANNEL_BETAS),
      .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS)
    ) population (
      .clk, .reset, .contribution_valid_i('0),
      .contribution_ready_o(unused_contribution_ready), .destination_i('0),
      .weight_i('0),
      .dense_current_valid_i(presynaptic_valid_i && presynaptic_ready_o),
      .dense_current_ready_o(population_dense_ready),
      .dense_current_delta_i(current_delta),
      .completion_valid_i(completion_valid_i && completion_ready_o),
      .completion_ready_o(population_completion_ready), .completion_tag_i,
      .spike_valid_o(result_valid_o), .spike_ready_i(result_ready_i),
      .spike_vector_o, .completion_tag_o, .address_error_o(error_o)
    );
  end endgenerate
endmodule
