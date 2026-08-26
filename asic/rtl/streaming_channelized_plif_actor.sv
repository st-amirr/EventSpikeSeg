`timescale 1ns/1ps
// Unified ready/valid event-stream wrapper for one permanent channelized
// convolution/PLIF actor. Data packets carry (x,y,channel); completion packets
// close one 5 ms epoch. Output spikes and completion use the same stream.
module streaming_channelized_plif_actor #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer X_LSB = 0,
  parameter integer X_WIDTH = 10,
  parameter integer Y_LSB = 10,
  parameter integer Y_WIDTH = 9,
  parameter integer CHANNEL_LSB = 19,
  parameter integer CHANNEL_WIDTH = 7,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer MEM_WIDTH = 16,
  parameter integer BETA_WIDTH = 16,
  parameter integer INPUT_CHANNELS = 2,
  parameter integer OUTPUT_CHANNELS = 2,
  parameter integer GROUPS = 1,
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
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS / GROUPS,
  parameter integer WEIGHT_COUNT =
    OUTPUT_CHANNELS * INPUTS_PER_GROUP * KERNEL_WIDTH * KERNEL_HEIGHT,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [15:0] ADAPTATION_DURATION = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in_payload,
  input  logic in_completion,
  input  logic [TAG_WIDTH-1:0] in_bin_tag,
  output logic out_valid,
  input  logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic actor_error_o
);
  localparam integer INPUT_CHANNEL_WIDTH =
    (INPUT_CHANNELS <= 1) ? 1 : $clog2(INPUT_CHANNELS);
  localparam integer OUTPUT_CHANNEL_WIDTH =
    (OUTPUT_CHANNELS <= 1) ? 1 : $clog2(OUTPUT_CHANNELS);
  logic presynaptic_ready;
  logic epoch_end_ready;
  logic spike_valid;
  logic spike_ready;
  logic [OUTPUT_CHANNEL_WIDTH-1:0] spike_channel;
  logic [X_WIDTH-1:0] spike_x;
  logic [X_WIDTH-1:0] spike_y;
  logic epoch_done_valid;
  logic epoch_done_ready;
  logic [TAG_WIDTH-1:0] epoch_tag;
  logic routing_error;
  logic input_channel_error;

  assign in_ready = in_completion ? epoch_end_ready : presynaptic_ready;
  assign out_valid = spike_valid || epoch_done_valid;
  assign out_completion = epoch_done_valid;
  assign out_bin_tag = epoch_tag;
  assign spike_ready = out_ready && spike_valid;
  assign epoch_done_ready = out_ready && epoch_done_valid;
  assign input_channel_error = in_valid && !in_completion &&
                               $unsigned(in_payload[CHANNEL_LSB +: CHANNEL_WIDTH]) >=
                               INPUT_CHANNELS;
  assign actor_error_o = routing_error || input_channel_error;

  always_comb begin
    out_payload = '0;
    if (spike_valid) begin
      out_payload[X_LSB +: X_WIDTH] = spike_x;
      out_payload[Y_LSB +: Y_WIDTH] = spike_y[Y_WIDTH-1:0];
      out_payload[CHANNEL_LSB +: CHANNEL_WIDTH] =
        {{(CHANNEL_WIDTH-OUTPUT_CHANNEL_WIDTH){1'b0}}, spike_channel};
    end
  end

  channelized_convolution_plif_actor #(
    .COORD_WIDTH(X_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH), .MEM_WIDTH(MEM_WIDTH),
    .BETA_WIDTH(BETA_WIDTH), .EPOCH_TAG_WIDTH(TAG_WIDTH),
    .INPUT_CHANNELS(INPUT_CHANNELS), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
    .GROUPS(GROUPS), .KERNEL_WIDTH(KERNEL_WIDTH), .KERNEL_HEIGHT(KERNEL_HEIGHT),
    .STRIDE_X(STRIDE_X), .STRIDE_Y(STRIDE_Y), .DILATION_X(DILATION_X),
    .DILATION_Y(DILATION_Y), .PAD_X(PAD_X), .PAD_Y(PAD_Y),
    .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
    .ENABLE_INHIBITION(ENABLE_INHIBITION), .ENABLE_ADAPTATION(ENABLE_ADAPTATION),
    .KERNEL_WEIGHTS(KERNEL_WEIGHTS), .CHANNEL_BETAS(CHANNEL_BETAS),
    .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
    .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
    .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
    .ADAPTATION_DURATION(ADAPTATION_DURATION)
  ) actor (
    .clk, .reset,
    .presynaptic_valid(in_valid && !in_completion && !input_channel_error),
    .presynaptic_ready,
    .presynaptic_channel_i(in_payload[CHANNEL_LSB +: INPUT_CHANNEL_WIDTH]),
    .presynaptic_x_i(in_payload[X_LSB +: X_WIDTH]),
    .presynaptic_y_i({{(X_WIDTH-Y_WIDTH){1'b0}},
                      in_payload[Y_LSB +: Y_WIDTH]}),
    .epoch_end_valid(in_valid && in_completion), .epoch_end_ready,
    .epoch_tag_i(in_bin_tag), .spike_valid, .spike_ready,
    .spike_channel_o(spike_channel), .spike_x_o(spike_x), .spike_y_o(spike_y),
    .epoch_done_valid, .epoch_done_ready, .epoch_tag_o(epoch_tag),
    .routing_error_o(routing_error)
  );
endmodule
