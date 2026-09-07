`timescale 1ns/1ps
// Spatial hierarchy for a register-resident actor. Every child owns dedicated
// PLIF state for one output tile. Inputs, completion, and results advance only
// when every tile can participate, preserving one transaction per tile without
// adding addressed runtime-state storage.
module tiled_resident_channelized_plif_actor #(
  parameter integer INPUT_CHANNELS = 1,
  parameter integer INPUT_WIDTH = 4,
  parameter integer INPUT_HEIGHT = 4,
  parameter integer OUTPUT_CHANNELS = 1,
  parameter integer OUTPUT_WIDTH = 4,
  parameter integer OUTPUT_HEIGHT = 4,
  parameter integer TILE_WIDTH = 4,
  parameter integer TILE_HEIGHT = 4,
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
  parameter integer INPUT_COUNT = INPUT_CHANNELS*INPUT_WIDTH*INPUT_HEIGHT,
  parameter integer OUTPUT_COUNT = OUTPUT_CHANNELS*OUTPUT_WIDTH*OUTPUT_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*
                                   KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0,
  parameter logic [OUTPUT_CHANNELS*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [OUTPUT_CHANNELS*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [AMPLITUDE_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [DURATION_WIDTH-1:0] ADAPTATION_DURATION = '0,
  parameter integer TILE_COLUMNS = (OUTPUT_WIDTH+TILE_WIDTH-1)/TILE_WIDTH,
  parameter integer TILE_ROWS = (OUTPUT_HEIGHT+TILE_HEIGHT-1)/TILE_HEIGHT,
  parameter integer TILE_COUNT = TILE_COLUMNS*TILE_ROWS
) (
  input logic clk, input logic reset,
  input logic presynaptic_valid_i, output logic presynaptic_ready_o,
  input logic [INPUT_COUNT-1:0] presynaptic_spike_vector_i,
  input logic completion_valid_i, output logic completion_ready_o,
  input logic [TAG_WIDTH-1:0] completion_tag_i,
  output logic result_valid_o, input logic result_ready_i,
  output logic [OUTPUT_COUNT-1:0] spike_vector_o,
  output logic [TAG_WIDTH-1:0] completion_tag_o,
  output logic error_o
);
  logic [TILE_COUNT-1:0] tile_presynaptic_ready;
  logic [TILE_COUNT-1:0] tile_completion_ready;
  logic [TILE_COUNT-1:0] tile_result_valid;
  logic [TILE_COUNT-1:0] tile_error;
  logic [TAG_WIDTH-1:0] tile_tag [0:TILE_COUNT-1];
  logic tag_error;

  assign presynaptic_ready_o = (&tile_presynaptic_ready) && !completion_valid_i;
  assign completion_ready_o = (&tile_completion_ready) && !presynaptic_valid_i;
  assign result_valid_o = &tile_result_valid;
  assign completion_tag_o = tile_tag[0];
  assign error_o = (|tile_error) || tag_error;

  integer tag_index;
  always_comb begin
    tag_error = 1'b0;
    tag_index = 0;
    if (result_valid_o)
      for (tag_index = 1; tag_index < TILE_COUNT; tag_index = tag_index + 1)
        if (tile_tag[tag_index] != tile_tag[0]) tag_error = 1'b1;
  end

  generate
    for (genvar tile_y = 0; tile_y < TILE_ROWS; tile_y = tile_y + 1) begin : row
      for (genvar tile_x = 0; tile_x < TILE_COLUMNS; tile_x = tile_x + 1) begin : column
        localparam integer INDEX = tile_y*TILE_COLUMNS+tile_x;
        localparam integer LOCAL_WIDTH =
          (((tile_x+1)*TILE_WIDTH) <= OUTPUT_WIDTH) ? TILE_WIDTH :
          OUTPUT_WIDTH-tile_x*TILE_WIDTH;
        localparam integer LOCAL_HEIGHT =
          (((tile_y+1)*TILE_HEIGHT) <= OUTPUT_HEIGHT) ? TILE_HEIGHT :
          OUTPUT_HEIGHT-tile_y*TILE_HEIGHT;
        localparam integer LOCAL_SPATIAL_COUNT = LOCAL_WIDTH*LOCAL_HEIGHT;
        localparam integer OUTPUT_ORIGIN_X = tile_x*TILE_WIDTH;
        localparam integer OUTPUT_ORIGIN_Y = tile_y*TILE_HEIGHT;
        localparam integer RAW_INPUT_MIN_X =
          OUTPUT_ORIGIN_X*STRIDE_X-PAD_X;
        localparam integer RAW_INPUT_MIN_Y =
          OUTPUT_ORIGIN_Y*STRIDE_Y-PAD_Y;
        localparam integer RAW_INPUT_MAX_X =
          (OUTPUT_ORIGIN_X+LOCAL_WIDTH-1)*STRIDE_X-PAD_X+
          (KERNEL_WIDTH-1)*DILATION_X;
        localparam integer RAW_INPUT_MAX_Y =
          (OUTPUT_ORIGIN_Y+LOCAL_HEIGHT-1)*STRIDE_Y-PAD_Y+
          (KERNEL_HEIGHT-1)*DILATION_Y;
        localparam integer INPUT_ORIGIN_X =
          (RAW_INPUT_MIN_X < 0) ? 0 : RAW_INPUT_MIN_X;
        localparam integer INPUT_ORIGIN_Y =
          (RAW_INPUT_MIN_Y < 0) ? 0 : RAW_INPUT_MIN_Y;
        localparam integer INPUT_END_X =
          (RAW_INPUT_MAX_X >= INPUT_WIDTH) ? INPUT_WIDTH-1 : RAW_INPUT_MAX_X;
        localparam integer INPUT_END_Y =
          (RAW_INPUT_MAX_Y >= INPUT_HEIGHT) ? INPUT_HEIGHT-1 : RAW_INPUT_MAX_Y;
        localparam integer LOCAL_INPUT_WIDTH = INPUT_END_X-INPUT_ORIGIN_X+1;
        localparam integer LOCAL_INPUT_HEIGHT = INPUT_END_Y-INPUT_ORIGIN_Y+1;
        localparam integer LOCAL_INPUT_SPATIAL_COUNT =
          LOCAL_INPUT_WIDTH*LOCAL_INPUT_HEIGHT;
        logic [INPUT_CHANNELS*LOCAL_INPUT_SPATIAL_COUNT-1:0] local_input_spikes;
        logic [OUTPUT_CHANNELS*LOCAL_SPATIAL_COUNT-1:0] local_spikes;

        initial begin
          if (LOCAL_INPUT_WIDTH <= 0 || LOCAL_INPUT_HEIGHT <= 0)
            $error("resident output tile has an empty input receptive halo");
        end

        // Each global input bit is wired only to tiles whose receptive field
        // can consume it. This is static physical routing, not runtime state.
        for (genvar input_channel = 0; input_channel < INPUT_CHANNELS;
             input_channel = input_channel + 1)
          for (genvar input_y = 0; input_y < LOCAL_INPUT_HEIGHT;
               input_y = input_y + 1)
            for (genvar input_x = 0; input_x < LOCAL_INPUT_WIDTH;
                 input_x = input_x + 1) begin : input_halo
              localparam integer LOCAL_INPUT_INDEX =
                input_channel*LOCAL_INPUT_SPATIAL_COUNT+
                input_y*LOCAL_INPUT_WIDTH+input_x;
              localparam integer GLOBAL_INPUT_INDEX =
                input_channel*INPUT_WIDTH*INPUT_HEIGHT+
                (INPUT_ORIGIN_Y+input_y)*INPUT_WIDTH+INPUT_ORIGIN_X+input_x;
              assign local_input_spikes[LOCAL_INPUT_INDEX] =
                presynaptic_spike_vector_i[GLOBAL_INPUT_INDEX];
            end

        resident_channelized_plif_actor #(
          .INPUT_CHANNELS(INPUT_CHANNELS), .INPUT_WIDTH(LOCAL_INPUT_WIDTH),
          .INPUT_HEIGHT(LOCAL_INPUT_HEIGHT), .INPUT_TILE_X(INPUT_ORIGIN_X),
          .INPUT_TILE_Y(INPUT_ORIGIN_Y), .OUTPUT_CHANNELS(OUTPUT_CHANNELS),
          .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT),
          .OUTPUT_TILE_X(tile_x*TILE_WIDTH), .OUTPUT_TILE_Y(tile_y*TILE_HEIGHT),
          .OUTPUT_TILE_WIDTH(LOCAL_WIDTH), .OUTPUT_TILE_HEIGHT(LOCAL_HEIGHT),
          .GROUPS(GROUPS), .KERNEL_WIDTH(KERNEL_WIDTH),
          .KERNEL_HEIGHT(KERNEL_HEIGHT), .STRIDE_X(STRIDE_X),
          .STRIDE_Y(STRIDE_Y), .DILATION_X(DILATION_X),
          .DILATION_Y(DILATION_Y), .PAD_X(PAD_X), .PAD_Y(PAD_Y),
          .WEIGHT_WIDTH(WEIGHT_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
          .MEM_WIDTH(MEM_WIDTH), .BETA_WIDTH(BETA_WIDTH),
          .BETA_FRAC_BITS(BETA_FRAC_BITS), .TAG_WIDTH(TAG_WIDTH),
          .AGE_WIDTH(AGE_WIDTH), .AMPLITUDE_WIDTH(AMPLITUDE_WIDTH),
          .DURATION_WIDTH(DURATION_WIDTH), .ENABLE_INHIBITION(ENABLE_INHIBITION),
          .ENABLE_ADAPTATION(ENABLE_ADAPTATION), .KERNEL_WEIGHTS(KERNEL_WEIGHTS),
          .CHANNEL_BETAS(CHANNEL_BETAS), .CHANNEL_THRESHOLDS(CHANNEL_THRESHOLDS),
          .INHIBITION_STRENGTH(INHIBITION_STRENGTH),
          .ADAPTATION_STRENGTH(ADAPTATION_STRENGTH),
          .ADAPTATION_DURATION(ADAPTATION_DURATION)
        ) tile (
          .clk, .reset,
          // All children see the same transaction only after the wrapper has
          // established that every child is ready. This preserves lockstep tile
          // state while keeping ready independent of valid.
          .presynaptic_valid_i(presynaptic_valid_i && presynaptic_ready_o),
          .presynaptic_ready_o(tile_presynaptic_ready[INDEX]),
          .presynaptic_spike_vector_i(local_input_spikes),
          .completion_valid_i(completion_valid_i && completion_ready_o),
          .completion_ready_o(tile_completion_ready[INDEX]), .completion_tag_i,
          .result_valid_o(tile_result_valid[INDEX]),
          .result_ready_i(result_ready_i),
          .spike_vector_o(local_spikes), .completion_tag_o(tile_tag[INDEX]),
          .error_o(tile_error[INDEX])
        );

        for (genvar channel = 0; channel < OUTPUT_CHANNELS; channel = channel + 1)
          for (genvar local_y = 0; local_y < LOCAL_HEIGHT; local_y = local_y + 1)
            for (genvar local_x = 0; local_x < LOCAL_WIDTH; local_x = local_x + 1) begin : map
              localparam integer LOCAL_INDEX =
                channel*LOCAL_SPATIAL_COUNT+local_y*LOCAL_WIDTH+local_x;
              localparam integer GLOBAL_INDEX = channel*OUTPUT_WIDTH*OUTPUT_HEIGHT+
                (tile_y*TILE_HEIGHT+local_y)*OUTPUT_WIDTH+tile_x*TILE_WIDTH+local_x;
              assign spike_vector_o[GLOBAL_INDEX] = local_spikes[LOCAL_INDEX];
            end
      end
    end
  endgenerate
endmodule
