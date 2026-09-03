`timescale 1ns/1ps
// Mechanism-enabled convolution actor with one independent contribution stream
// per spatial bank.  All output channels for a pixel stay in the same lane so
// peer inhibition and threshold adaptation remain one atomic update group.
module parallel_banked_retinotopic_channelized_plif_actor #(
  parameter integer COORD_WIDTH = 10,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
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
  parameter integer SPATIAL_DEST_COUNT = OUTPUT_WIDTH*OUTPUT_HEIGHT,
  parameter integer DEST_COUNT = OUTPUT_CHANNELS*SPATIAL_DEST_COUNT,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer SPATIAL_LANE_COUNT = 4,
  parameter integer LOCAL_SPATIAL_DEST_COUNT =
    (SPATIAL_DEST_COUNT+SPATIAL_LANE_COUNT-1)/SPATIAL_LANE_COUNT,
  parameter integer LOCAL_DEST_COUNT = OUTPUT_CHANNELS*LOCAL_SPATIAL_DEST_COUNT,
  parameter integer LOCAL_ADDRESS_WIDTH =
    (LOCAL_DEST_COUNT <= 1) ? 1 : $clog2(LOCAL_DEST_COUNT),
  parameter integer TAP_COUNT = KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*TAP_COUNT,
  parameter integer AGE_WIDTH = 16,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer USE_STATE_MACRO = 0,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [AGE_WIDTH-1:0] ADAPTATION_DURATION = '0
) (
  input logic clk, input logic reset,
  input logic presynaptic_valid, output logic presynaptic_ready,
  input logic [INPUT_CHANNEL_WIDTH-1:0] presynaptic_channel_i,
  input logic [COORD_WIDTH-1:0] presynaptic_x_i,
  input logic [COORD_WIDTH-1:0] presynaptic_y_i,
  input logic epoch_end_valid, output logic epoch_end_ready,
  input logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  output logic spike_valid, input logic spike_ready,
  output logic [OUTPUT_CHANNEL_WIDTH-1:0] spike_channel_o,
  output logic [COORD_WIDTH-1:0] spike_x_o,
  output logic [COORD_WIDTH-1:0] spike_y_o,
  output logic epoch_done_valid, input logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic routing_error_o,
  output logic initialization_done_o
);
  logic scatter_ready;
  logic scatter_idle;
  logic [SPATIAL_LANE_COUNT-1:0] contribution_valid;
  logic [SPATIAL_LANE_COUNT-1:0] contribution_ready;
  logic [SPATIAL_LANE_COUNT*OUTPUT_CHANNEL_WIDTH-1:0] destination_channel;
  logic [SPATIAL_LANE_COUNT*COORD_WIDTH-1:0] destination_x;
  logic [SPATIAL_LANE_COUNT*COORD_WIDTH-1:0] destination_y;
  logic signed [SPATIAL_LANE_COUNT*WEIGHT_WIDTH-1:0] contribution_weight;
  logic scatter_error;
  logic [SPATIAL_LANE_COUNT*LOCAL_ADDRESS_WIDTH-1:0] local_destination;
  logic [SPATIAL_LANE_COUNT-1:0] lane_spike_valid;
  logic [SPATIAL_LANE_COUNT-1:0] lane_spike_ready;
  logic [SPATIAL_LANE_COUNT*LOCAL_ADDRESS_WIDTH-1:0] lane_spike_destination;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_end_ready;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_done_valid;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_done_ready;
  logic [SPATIAL_LANE_COUNT*EPOCH_TAG_WIDTH-1:0] lane_epoch_tag;
  logic [SPATIAL_LANE_COUNT-1:0] lane_error;
  logic [SPATIAL_LANE_COUNT-1:0] lane_initialized;
  integer lane_index;
  integer lane_channel;
  integer lane_x;
  integer lane_y;
  integer lane_spatial;
  integer lane_local_spatial;
  integer selected_output_lane;
  integer selected_local_spike;
  integer output_channel;
  integer output_local_spatial;
  integer output_global_spatial;
  logic tags_match;

  initial begin
    if (SPATIAL_LANE_COUNT <= 0 || SPATIAL_LANE_COUNT > SPATIAL_DEST_COUNT)
      $error("spatial lane count exceeds the logical population");
  end

  parallel_channelized_convolution_scatter #(
    .COORD_WIDTH(COORD_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH),
    .INPUT_CHANNELS(INPUT_CHANNELS), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
    .GROUPS(GROUPS), .INPUT_CHANNEL_WIDTH(INPUT_CHANNEL_WIDTH),
    .OUTPUT_CHANNEL_WIDTH(OUTPUT_CHANNEL_WIDTH), .KERNEL_WIDTH(KERNEL_WIDTH),
    .KERNEL_HEIGHT(KERNEL_HEIGHT), .STRIDE_X(STRIDE_X), .STRIDE_Y(STRIDE_Y),
    .DILATION_X(DILATION_X), .DILATION_Y(DILATION_Y), .PAD_X(PAD_X),
    .PAD_Y(PAD_Y), .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
    .CHANNEL_LANE_COUNT(1), .SPATIAL_LANE_COUNT(SPATIAL_LANE_COUNT),
    .KERNEL_WEIGHTS(KERNEL_WEIGHTS)
  ) scatter (
    .clk, .reset,
    .spike_valid(presynaptic_valid && presynaptic_ready),
    .spike_ready(scatter_ready), .idle_o(scatter_idle),
    .spike_channel_i(presynaptic_channel_i),
    .spike_x_i(presynaptic_x_i), .spike_y_i(presynaptic_y_i),
    .contribution_valid, .contribution_ready,
    .destination_channel_o(destination_channel),
    .destination_x_o(destination_x), .destination_y_o(destination_y),
    .weight_o(contribution_weight), .channel_error_o(scatter_error)
  );

  always_comb begin
    for (lane_index = 0; lane_index < SPATIAL_LANE_COUNT;
         lane_index = lane_index+1) begin
      lane_channel = $unsigned(destination_channel[
        lane_index*OUTPUT_CHANNEL_WIDTH +: OUTPUT_CHANNEL_WIDTH]);
      lane_x = $unsigned(destination_x[lane_index*COORD_WIDTH +: COORD_WIDTH]);
      lane_y = $unsigned(destination_y[lane_index*COORD_WIDTH +: COORD_WIDTH]);
      lane_spatial = lane_y*OUTPUT_WIDTH+lane_x;
      lane_local_spatial = lane_spatial/SPATIAL_LANE_COUNT;
      local_destination[lane_index*LOCAL_ADDRESS_WIDTH +: LOCAL_ADDRESS_WIDTH] =
        lane_channel*LOCAL_SPATIAL_DEST_COUNT+lane_local_spatial;
    end

    selected_output_lane = 0;
    for (lane_index = SPATIAL_LANE_COUNT-1; lane_index >= 0;
         lane_index = lane_index-1)
      if (lane_spike_valid[lane_index]) selected_output_lane = lane_index;
    selected_local_spike = $unsigned(lane_spike_destination[
      selected_output_lane*LOCAL_ADDRESS_WIDTH +: LOCAL_ADDRESS_WIDTH]);
    output_channel = selected_local_spike/LOCAL_SPATIAL_DEST_COUNT;
    output_local_spatial = selected_local_spike%LOCAL_SPATIAL_DEST_COUNT;
    output_global_spatial =
      output_local_spatial*SPATIAL_LANE_COUNT+selected_output_lane;
    spike_channel_o = output_channel[OUTPUT_CHANNEL_WIDTH-1:0];
    spike_y_o = output_global_spatial/OUTPUT_WIDTH;
    spike_x_o = output_global_spatial%OUTPUT_WIDTH;
    spike_valid = |lane_spike_valid;
    lane_spike_ready = '0;
    if (spike_valid) lane_spike_ready[selected_output_lane] = spike_ready;

    tags_match = 1'b1;
    for (lane_index = 1; lane_index < SPATIAL_LANE_COUNT;
         lane_index = lane_index+1)
      if (lane_epoch_tag[lane_index*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] !=
          lane_epoch_tag[0 +: EPOCH_TAG_WIDTH]) tags_match = 1'b0;
    epoch_tag_o = lane_epoch_tag[0 +: EPOCH_TAG_WIDTH];
  end

  assign presynaptic_ready = scatter_ready && !epoch_end_valid;
  assign initialization_done_o = &lane_initialized;
  assign epoch_end_ready = scatter_idle && initialization_done_o &&
                           (&lane_epoch_end_ready);
  assign epoch_done_valid = (&lane_epoch_done_valid) && tags_match;
  assign lane_epoch_done_ready =
    {SPATIAL_LANE_COUNT{epoch_done_valid && epoch_done_ready}};
  assign routing_error_o = scatter_error || (|lane_error) ||
                           ((&lane_epoch_done_valid) && !tags_match);

  genvar generated_lane;
  generate for (generated_lane = 0; generated_lane < SPATIAL_LANE_COUNT;
                generated_lane = generated_lane+1) begin : lanes
    retinotopic_asynchronous_plif_actor #(
      .ADDRESS_WIDTH(LOCAL_ADDRESS_WIDTH), .CHANNEL_COUNT(OUTPUT_CHANNELS),
      .SPATIAL_DEST_COUNT(LOCAL_SPATIAL_DEST_COUNT),
      .DEST_COUNT(LOCAL_DEST_COUNT), .MEM_WIDTH(MEM_WIDTH),
      .CURRENT_WIDTH(CURRENT_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH),
      .BETA_WIDTH(BETA_WIDTH), .BETA_FRAC_BITS(BETA_FRAC_BITS),
      .EPOCH_TAG_WIDTH(EPOCH_TAG_WIDTH), .AGE_WIDTH(AGE_WIDTH),
      .ENABLE_INHIBITION(ENABLE_INHIBITION),
      .ENABLE_ADAPTATION(ENABLE_ADAPTATION), .USE_STATE_MACRO(USE_STATE_MACRO),
      .CHANNEL_BETAS(CHANNEL_BETAS), .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
      .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
      .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
      .ADAPTATION_DURATION(ADAPTATION_DURATION)
    ) lane (
      .clk, .reset, .contribution_valid(contribution_valid[generated_lane]),
      .contribution_ready(contribution_ready[generated_lane]),
      .destination_i(local_destination[
        generated_lane*LOCAL_ADDRESS_WIDTH +: LOCAL_ADDRESS_WIDTH]),
      .weight_i(contribution_weight[
        generated_lane*WEIGHT_WIDTH +: WEIGHT_WIDTH]),
      .epoch_end_valid(epoch_end_valid && epoch_end_ready),
      .epoch_end_ready(lane_epoch_end_ready[generated_lane]), .epoch_tag_i,
      .spike_valid(lane_spike_valid[generated_lane]),
      .spike_ready(lane_spike_ready[generated_lane]),
      .spike_destination_o(lane_spike_destination[
        generated_lane*LOCAL_ADDRESS_WIDTH +: LOCAL_ADDRESS_WIDTH]),
      .epoch_done_valid(lane_epoch_done_valid[generated_lane]),
      .epoch_done_ready(lane_epoch_done_ready[generated_lane]),
      .epoch_tag_o(lane_epoch_tag[
        generated_lane*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH]),
      .address_error_o(lane_error[generated_lane]),
      .initialization_done_o(lane_initialized[generated_lane])
    );
  end endgenerate
endmodule
