`timescale 1ns/1ps
// Exact spatial hierarchy for the register-resident temporal class readout.
// Every child owns the class-current state for one spatial tile. Transactions
// enter all tiles in lockstep, while predictions leave in global row-major
// order. This changes elaboration hierarchy only; it does not share, address,
// truncate, or duplicate persistent score state.
module tiled_resident_temporal_class_readout #(
  parameter integer INPUT_CHANNELS = 2,
  parameter integer CLASS_COUNT = 3,
  parameter integer OUTPUT_WIDTH = 8,
  parameter integer OUTPUT_HEIGHT = 8,
  parameter integer TILE_WIDTH = 8,
  parameter integer TILE_HEIGHT = 8,
  parameter integer SPATIAL_COUNT = OUTPUT_WIDTH*OUTPUT_HEIGHT,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*SPATIAL_COUNT,
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer ACC_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer PREDICTION_BINS = 10,
  parameter integer X_WIDTH = (OUTPUT_WIDTH <= 1) ? 1 : $clog2(OUTPUT_WIDTH),
  parameter integer Y_WIDTH = (OUTPUT_HEIGHT <= 1) ? 1 : $clog2(OUTPUT_HEIGHT),
  parameter integer CLASS_WIDTH = (CLASS_COUNT <= 1) ? 1 : $clog2(CLASS_COUNT),
  parameter integer WEIGHT_COUNT = CLASS_COUNT*INPUT_CHANNELS,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] READOUT_WEIGHTS = '0,
  parameter integer TILE_COLUMNS = (OUTPUT_WIDTH+TILE_WIDTH-1)/TILE_WIDTH,
  parameter integer TILE_ROWS = (OUTPUT_HEIGHT+TILE_HEIGHT-1)/TILE_HEIGHT,
  parameter integer TILE_COUNT = TILE_COLUMNS*TILE_ROWS,
  parameter integer TILE_INDEX_WIDTH = (TILE_COUNT <= 1) ? 1 : $clog2(TILE_COUNT),
  parameter integer SPATIAL_WIDTH = (SPATIAL_COUNT <= 1) ? 1 : $clog2(SPATIAL_COUNT)
) (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [INPUT_COUNT-1:0] in_spike_vector_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic prediction_valid_o, input logic prediction_ready_i,
  output logic [X_WIDTH-1:0] prediction_x_o,
  output logic [Y_WIDTH-1:0] prediction_y_o,
  output logic [CLASS_WIDTH-1:0] prediction_class_o,
  output logic frame_done_valid_o, input logic frame_done_ready_i,
  output logic [TAG_WIDTH-1:0] frame_tag_o,
  output logic error_o
);
  logic [TILE_COUNT-1:0] tile_in_ready;
  logic [TILE_COUNT-1:0] tile_prediction_valid;
  logic [TILE_COUNT-1:0] tile_prediction_ready;
  logic [TILE_COUNT-1:0] tile_frame_done_valid;
  logic [CLASS_WIDTH-1:0] tile_prediction_class [0:TILE_COUNT-1];
  logic [TAG_WIDTH-1:0] tile_frame_tag [0:TILE_COUNT-1];
  logic [SPATIAL_WIDTH-1:0] emit_spatial_reg;
  logic [TILE_INDEX_WIDTH-1:0] selected_tile_index;
  logic tag_error;
  integer tag_index;

  assign in_ready_o = &tile_in_ready;
  assign prediction_x_o = $unsigned(emit_spatial_reg) % OUTPUT_WIDTH;
  assign prediction_y_o = $unsigned(emit_spatial_reg) / OUTPUT_WIDTH;
  assign selected_tile_index =
    (($unsigned(prediction_y_o)/TILE_HEIGHT)*TILE_COLUMNS)+
    ($unsigned(prediction_x_o)/TILE_WIDTH);
  assign prediction_valid_o = tile_prediction_valid[selected_tile_index];
  assign prediction_class_o = tile_prediction_class[selected_tile_index];
  assign frame_done_valid_o = &tile_frame_done_valid;
  assign frame_tag_o = tile_frame_tag[0];
  assign error_o = tag_error;

  always_comb begin
    tag_error = 1'b0;
    tag_index = 0;
    if (frame_done_valid_o)
      for (tag_index = 1; tag_index < TILE_COUNT; tag_index = tag_index+1)
        if (tile_frame_tag[tag_index] != tile_frame_tag[0])
          tag_error = 1'b1;
  end

  always_ff @(posedge clk) begin
    if (reset)
      emit_spatial_reg <= '0;
    else if (prediction_valid_o && prediction_ready_i) begin
      if (emit_spatial_reg+1 >= SPATIAL_COUNT)
        emit_spatial_reg <= '0;
      else
        emit_spatial_reg <= emit_spatial_reg+1'b1;
    end
  end

  generate
    for (genvar tile_y = 0; tile_y < TILE_ROWS; tile_y = tile_y+1) begin : row
      for (genvar tile_x = 0; tile_x < TILE_COLUMNS; tile_x = tile_x+1) begin : column
        localparam integer INDEX = tile_y*TILE_COLUMNS+tile_x;
        localparam integer LOCAL_WIDTH =
          (((tile_x+1)*TILE_WIDTH) <= OUTPUT_WIDTH) ? TILE_WIDTH :
          OUTPUT_WIDTH-tile_x*TILE_WIDTH;
        localparam integer LOCAL_HEIGHT =
          (((tile_y+1)*TILE_HEIGHT) <= OUTPUT_HEIGHT) ? TILE_HEIGHT :
          OUTPUT_HEIGHT-tile_y*TILE_HEIGHT;
        localparam integer LOCAL_SPATIAL_COUNT = LOCAL_WIDTH*LOCAL_HEIGHT;
        localparam integer LOCAL_INPUT_COUNT = INPUT_CHANNELS*LOCAL_SPATIAL_COUNT;
        localparam integer LOCAL_X_WIDTH =
          (LOCAL_WIDTH <= 1) ? 1 : $clog2(LOCAL_WIDTH);
        localparam integer LOCAL_Y_WIDTH =
          (LOCAL_HEIGHT <= 1) ? 1 : $clog2(LOCAL_HEIGHT);
        logic [LOCAL_INPUT_COUNT-1:0] local_input_spikes;
        logic [LOCAL_X_WIDTH-1:0] unused_prediction_x;
        logic [LOCAL_Y_WIDTH-1:0] unused_prediction_y;

        assign tile_prediction_ready[INDEX] =
          prediction_ready_i && prediction_valid_o &&
          (selected_tile_index == INDEX);

        for (genvar channel = 0; channel < INPUT_CHANNELS; channel = channel+1)
          for (genvar local_y = 0; local_y < LOCAL_HEIGHT; local_y = local_y+1)
            for (genvar local_x = 0; local_x < LOCAL_WIDTH; local_x = local_x+1) begin : map
              localparam integer LOCAL_INDEX =
                channel*LOCAL_SPATIAL_COUNT+local_y*LOCAL_WIDTH+local_x;
              localparam integer GLOBAL_INDEX =
                channel*SPATIAL_COUNT+
                (tile_y*TILE_HEIGHT+local_y)*OUTPUT_WIDTH+
                tile_x*TILE_WIDTH+local_x;
              assign local_input_spikes[LOCAL_INDEX] =
                in_spike_vector_i[GLOBAL_INDEX];
            end

        resident_temporal_class_readout #(
          .INPUT_CHANNELS(INPUT_CHANNELS), .CLASS_COUNT(CLASS_COUNT),
          .OUTPUT_WIDTH(LOCAL_WIDTH), .OUTPUT_HEIGHT(LOCAL_HEIGHT),
          .WEIGHT_WIDTH(WEIGHT_WIDTH), .ACC_WIDTH(ACC_WIDTH),
          .TAG_WIDTH(TAG_WIDTH), .PREDICTION_BINS(PREDICTION_BINS),
          .READOUT_WEIGHTS(READOUT_WEIGHTS)
        ) tile (
          .clk, .reset,
          .in_valid_i(in_valid_i && in_ready_o),
          .in_ready_o(tile_in_ready[INDEX]),
          .in_spike_vector_i(local_input_spikes),
          .in_completion_i, .in_tag_i,
          .prediction_valid_o(tile_prediction_valid[INDEX]),
          .prediction_ready_i(tile_prediction_ready[INDEX]),
          .prediction_x_o(unused_prediction_x),
          .prediction_y_o(unused_prediction_y),
          .prediction_class_o(tile_prediction_class[INDEX]),
          .frame_done_valid_o(tile_frame_done_valid[INDEX]),
          .frame_done_ready_i(
            frame_done_ready_i && frame_done_valid_o
          ),
          .frame_tag_o(tile_frame_tag[INDEX])
        );
      end
    end
  endgenerate
endmodule
