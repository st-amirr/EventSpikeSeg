`timescale 1ns/1ps
// Permanent sparse convolution/PLIF actor with channel-aware synaptic fanout,
// canonical local state indexed by (output_channel,y,x), and compile-time
// per-output-channel beta/threshold parameter tables.
module channelized_convolution_plif_actor #(
  parameter integer COORD_WIDTH = 10,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer MEM_WIDTH = 16,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer INPUT_CHANNELS = 2,
  parameter integer OUTPUT_CHANNELS = 2,
  parameter integer GROUPS = 1,
  parameter integer INPUT_CHANNEL_WIDTH =
    (INPUT_CHANNELS <= 1) ? 1 : $clog2(INPUT_CHANNELS),
  parameter integer OUTPUT_CHANNEL_WIDTH =
    (OUTPUT_CHANNELS <= 1) ? 1 : $clog2(OUTPUT_CHANNELS),
  parameter integer KERNEL_WIDTH = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 1,
  parameter integer PAD_Y = 1,
  parameter integer OUTPUT_WIDTH = 16,
  parameter integer OUTPUT_HEIGHT = 16,
  parameter integer SPATIAL_DEST_COUNT = OUTPUT_WIDTH * OUTPUT_HEIGHT,
  parameter integer DEST_COUNT = OUTPUT_CHANNELS * SPATIAL_DEST_COUNT,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer TAP_COUNT = KERNEL_WIDTH * KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS / GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS * INPUTS_PER_GROUP * TAP_COUNT,
  parameter integer PACKED_WEIGHT_COUNT = WEIGHT_COUNT,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter logic signed [PACKED_WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter KERNEL_WEIGHT_FILE = "",
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [15:0] ADAPTATION_DURATION = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic presynaptic_valid,
  output logic presynaptic_ready,
  input  logic [INPUT_CHANNEL_WIDTH-1:0] presynaptic_channel_i,
  input  logic [COORD_WIDTH-1:0] presynaptic_x_i,
  input  logic [COORD_WIDTH-1:0] presynaptic_y_i,
  input  logic epoch_end_valid,
  output logic epoch_end_ready,
  input  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  output logic spike_valid,
  input  logic spike_ready,
  output logic [OUTPUT_CHANNEL_WIDTH-1:0] spike_channel_o,
  output logic [COORD_WIDTH-1:0] spike_x_o,
  output logic [COORD_WIDTH-1:0] spike_y_o,
  output logic epoch_done_valid,
  input  logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic routing_error_o
);
  logic scatter_spike_ready;
  logic contribution_valid;
  logic contribution_ready;
  logic [OUTPUT_CHANNEL_WIDTH-1:0] destination_channel;
  logic [COORD_WIDTH-1:0] destination_x;
  logic [COORD_WIDTH-1:0] destination_y;
  logic signed [WEIGHT_WIDTH-1:0] contribution_weight;
  logic scatter_channel_error;
  logic actor_address_error;
  logic actor_epoch_end_valid;
  logic actor_epoch_end_ready;
  logic [ADDRESS_WIDTH-1:0] actor_destination;
  logic [ADDRESS_WIDTH-1:0] spike_destination;
  integer linear_destination;
  integer spike_spatial_index;
  integer spike_channel_index;
  integer spike_x_index;
  integer spike_y_index;

  channelized_convolution_scatter #(
    .COORD_WIDTH(COORD_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH),
    .INPUT_CHANNELS(INPUT_CHANNELS), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
    .GROUPS(GROUPS), .INPUT_CHANNEL_WIDTH(INPUT_CHANNEL_WIDTH),
    .OUTPUT_CHANNEL_WIDTH(OUTPUT_CHANNEL_WIDTH), .KERNEL_WIDTH(KERNEL_WIDTH),
    .KERNEL_HEIGHT(KERNEL_HEIGHT), .STRIDE_X(STRIDE_X), .STRIDE_Y(STRIDE_Y),
    .DILATION_X(DILATION_X), .DILATION_Y(DILATION_Y), .PAD_X(PAD_X),
    .PAD_Y(PAD_Y), .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
    .PACKED_WEIGHT_COUNT(PACKED_WEIGHT_COUNT), .KERNEL_WEIGHTS(KERNEL_WEIGHTS),
    .KERNEL_WEIGHT_FILE(KERNEL_WEIGHT_FILE)
  ) scatter (
    .clk, .reset,
    .spike_valid(presynaptic_valid && presynaptic_ready),
    .spike_ready(scatter_spike_ready), .spike_channel_i(presynaptic_channel_i),
    .spike_x_i(presynaptic_x_i), .spike_y_i(presynaptic_y_i),
    .contribution_valid, .contribution_ready,
    .destination_channel_o(destination_channel), .destination_x_o(destination_x),
    .destination_y_o(destination_y), .weight_o(contribution_weight),
    .channel_error_o(scatter_channel_error)
  );

  always_comb begin
    linear_destination =
      $unsigned(destination_channel) * SPATIAL_DEST_COUNT +
      $unsigned(destination_y) * OUTPUT_WIDTH + $unsigned(destination_x);
    actor_destination = linear_destination[ADDRESS_WIDTH-1:0];

    spike_channel_index = $unsigned(spike_destination) / SPATIAL_DEST_COUNT;
    spike_spatial_index = $unsigned(spike_destination) % SPATIAL_DEST_COUNT;
    spike_y_index = spike_spatial_index / OUTPUT_WIDTH;
    spike_x_index = spike_spatial_index % OUTPUT_WIDTH;
    spike_channel_o = spike_channel_index[OUTPUT_CHANNEL_WIDTH-1:0];
    spike_x_o = spike_x_index[COORD_WIDTH-1:0];
    spike_y_o = spike_y_index[COORD_WIDTH-1:0];
  end

  assign presynaptic_ready = scatter_spike_ready && contribution_ready &&
                             !epoch_end_valid;
  assign actor_epoch_end_valid = epoch_end_valid && scatter_spike_ready;
  assign epoch_end_ready = actor_epoch_end_ready && scatter_spike_ready;
  assign routing_error_o = scatter_channel_error || actor_address_error;

  generate if (ENABLE_INHIBITION || ENABLE_ADAPTATION) begin : mechanism_state
  retinotopic_asynchronous_plif_actor #(
    .ADDRESS_WIDTH(ADDRESS_WIDTH), .CHANNEL_COUNT(OUTPUT_CHANNELS),
    .SPATIAL_DEST_COUNT(SPATIAL_DEST_COUNT), .DEST_COUNT(DEST_COUNT),
    .MEM_WIDTH(MEM_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH), .BETA_WIDTH(BETA_WIDTH),
    .BETA_FRAC_BITS(BETA_FRAC_BITS), .EPOCH_TAG_WIDTH(EPOCH_TAG_WIDTH),
    .ENABLE_INHIBITION(ENABLE_INHIBITION), .ENABLE_ADAPTATION(ENABLE_ADAPTATION),
    .CHANNEL_BETAS(CHANNEL_BETAS), .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
    .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
    .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
    .ADAPTATION_DURATION(ADAPTATION_DURATION)
  ) neuron_array (
    .clk, .reset, .contribution_valid, .contribution_ready,
    .destination_i(actor_destination), .weight_i(contribution_weight),
    .epoch_end_valid(actor_epoch_end_valid), .epoch_end_ready(actor_epoch_end_ready),
    .epoch_tag_i, .spike_valid, .spike_ready,
    .spike_destination_o(spike_destination), .epoch_done_valid,
    .epoch_done_ready, .epoch_tag_o, .address_error_o(actor_address_error)
  );
  end else begin : simple_state
  asynchronous_plif_actor #(
    .ADDRESS_WIDTH(ADDRESS_WIDTH), .DEST_COUNT(DEST_COUNT),
    .MEM_WIDTH(MEM_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH),
    .BETA_WIDTH(BETA_WIDTH), .BETA_FRAC_BITS(BETA_FRAC_BITS),
    .EPOCH_TAG_WIDTH(EPOCH_TAG_WIDTH), .CHANNEL_COUNT(OUTPUT_CHANNELS),
    .SPATIAL_DEST_COUNT(SPATIAL_DEST_COUNT), .USE_CHANNEL_PARAMETERS(1),
    .CHANNEL_BETAS(CHANNEL_BETAS), .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS)
  ) neuron_array (
    .clk, .reset, .contribution_valid, .contribution_ready,
    .destination_i(actor_destination), .weight_i(contribution_weight),
    .epoch_end_valid(actor_epoch_end_valid), .epoch_end_ready(actor_epoch_end_ready),
    .epoch_tag_i, .beta_i({BETA_WIDTH{1'b0}}),
    .threshold_i({MEM_WIDTH{1'b0}}), .spike_valid, .spike_ready,
    .spike_destination_o(spike_destination), .epoch_done_valid,
    .epoch_done_ready, .epoch_tag_o, .address_error_o(actor_address_error)
  );
  end endgenerate
endmodule
