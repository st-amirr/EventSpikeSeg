`timescale 1ns/1ps
// Spatially interleaved mechanism-enabled PLIF population.  Each lane owns
// every channel at its assigned spatial locations, preserving the atomic
// cross-channel inhibition/adaptation update while allowing unrelated pixels
// to accumulate and commit independently.
module banked_retinotopic_asynchronous_plif_actor #(
  parameter integer ADDRESS_WIDTH = 8,
  parameter integer CHANNEL_COUNT = 4,
  parameter integer SPATIAL_DEST_COUNT = 16,
  parameter integer DEST_COUNT = CHANNEL_COUNT*SPATIAL_DEST_COUNT,
  parameter integer SPATIAL_LANE_COUNT = 4,
  parameter integer LOCAL_SPATIAL_DEST_COUNT =
    (SPATIAL_DEST_COUNT+SPATIAL_LANE_COUNT-1)/SPATIAL_LANE_COUNT,
  parameter integer LOCAL_DEST_COUNT = CHANNEL_COUNT*LOCAL_SPATIAL_DEST_COUNT,
  parameter integer LOCAL_ADDRESS_WIDTH =
    (LOCAL_DEST_COUNT <= 1) ? 1 : $clog2(LOCAL_DEST_COUNT),
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 16,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer USE_STATE_MACRO = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [AGE_WIDTH-1:0] ADAPTATION_DURATION = '0
) (
  input logic clk, input logic reset,
  input logic contribution_valid, output logic contribution_ready,
  input logic [ADDRESS_WIDTH-1:0] destination_i,
  input logic signed [WEIGHT_WIDTH-1:0] weight_i,
  input logic epoch_end_valid, output logic epoch_end_ready,
  input logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  output logic spike_valid, input logic spike_ready,
  output logic [ADDRESS_WIDTH-1:0] spike_destination_o,
  output logic epoch_done_valid, input logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic address_error_o,
  output logic initialization_done_o
);
  logic [SPATIAL_LANE_COUNT-1:0] lane_contribution_ready;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_end_ready;
  logic [SPATIAL_LANE_COUNT-1:0] lane_spike_valid;
  logic [SPATIAL_LANE_COUNT-1:0] lane_spike_ready;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_done_valid;
  logic [SPATIAL_LANE_COUNT-1:0] lane_epoch_done_ready;
  logic [SPATIAL_LANE_COUNT-1:0] lane_error;
  logic [SPATIAL_LANE_COUNT-1:0] lane_initialized;
  logic [SPATIAL_LANE_COUNT*LOCAL_ADDRESS_WIDTH-1:0] lane_spike_destination;
  logic [SPATIAL_LANE_COUNT*EPOCH_TAG_WIDTH-1:0] lane_epoch_tag;
  logic [LOCAL_ADDRESS_WIDTH-1:0] local_destination;
  integer input_channel;
  integer input_spatial;
  integer input_lane;
  integer input_local_spatial;
  integer selected_output_lane;
  integer selected_local_spike;
  integer output_channel;
  integer output_local_spatial;
  integer output_global_spatial;
  integer output_global_destination;
  integer lane_index;
  logic tags_match;

  initial begin
    if (SPATIAL_LANE_COUNT <= 0 || SPATIAL_LANE_COUNT > SPATIAL_DEST_COUNT)
      $error("spatial lane count exceeds the logical population");
  end

  always_comb begin
    input_channel = $unsigned(destination_i)/SPATIAL_DEST_COUNT;
    input_spatial = $unsigned(destination_i)%SPATIAL_DEST_COUNT;
    input_lane = input_spatial%SPATIAL_LANE_COUNT;
    input_local_spatial = input_spatial/SPATIAL_LANE_COUNT;
    local_destination =
      input_channel*LOCAL_SPATIAL_DEST_COUNT+input_local_spatial;
    contribution_ready = initialization_done_o && !epoch_end_valid &&
      ($unsigned(destination_i) < DEST_COUNT) &&
      lane_contribution_ready[input_lane];

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
    output_global_destination =
      output_channel*SPATIAL_DEST_COUNT+output_global_spatial;
    spike_valid = |lane_spike_valid;
    spike_destination_o = output_global_destination[ADDRESS_WIDTH-1:0];
    lane_spike_ready = '0;
    if (spike_valid) lane_spike_ready[selected_output_lane] = spike_ready;

    tags_match = 1'b1;
    for (lane_index = 1; lane_index < SPATIAL_LANE_COUNT;
         lane_index = lane_index+1)
      if (lane_epoch_tag[lane_index*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] !=
          lane_epoch_tag[0 +: EPOCH_TAG_WIDTH]) tags_match = 1'b0;
    epoch_tag_o = lane_epoch_tag[0 +: EPOCH_TAG_WIDTH];
  end

  assign initialization_done_o = &lane_initialized;
  assign epoch_end_ready = initialization_done_o && (&lane_epoch_end_ready);
  assign epoch_done_valid = (&lane_epoch_done_valid) && tags_match;
  assign lane_epoch_done_ready =
    {SPATIAL_LANE_COUNT{epoch_done_valid && epoch_done_ready}};
  assign address_error_o =
    (contribution_valid && ($unsigned(destination_i) >= DEST_COUNT)) ||
    (|lane_error) || ((&lane_epoch_done_valid) && !tags_match);

  genvar generated_lane;
  generate for (generated_lane = 0; generated_lane < SPATIAL_LANE_COUNT;
                generated_lane = generated_lane+1) begin : lanes
    logic selected_contribution_valid;
    assign selected_contribution_valid = contribution_valid &&
      ($unsigned(destination_i) < DEST_COUNT) &&
      (input_lane == generated_lane);
    retinotopic_asynchronous_plif_actor #(
      .ADDRESS_WIDTH(LOCAL_ADDRESS_WIDTH), .CHANNEL_COUNT(CHANNEL_COUNT),
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
      .clk, .reset, .contribution_valid(selected_contribution_valid),
      .contribution_ready(lane_contribution_ready[generated_lane]),
      .destination_i(local_destination), .weight_i,
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
