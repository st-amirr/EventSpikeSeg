`timescale 1ns/1ps
// Non-spiking per-pixel temporal class-current readout. Hidden spike events add
// one signed 1x1 weight vector. Every PREDICTION_BINS completion tokens trigger
// a dense pixel enumeration with first-index-tie argmax and score reset.
module temporal_class_readout #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer X_LSB = 0,
  parameter integer X_WIDTH = 10,
  parameter integer Y_LSB = 10,
  parameter integer Y_WIDTH = 9,
  parameter integer CHANNEL_LSB = 19,
  parameter integer CHANNEL_WIDTH = 7,
  parameter integer INPUT_CHANNELS = 16,
  parameter integer CLASS_COUNT = 11,
  parameter integer CLASS_WIDTH = (CLASS_COUNT <= 1) ? 1 : $clog2(CLASS_COUNT),
  parameter integer OUTPUT_WIDTH = 640,
  parameter integer OUTPUT_HEIGHT = 440,
  parameter integer PIXEL_COUNT = OUTPUT_WIDTH * OUTPUT_HEIGHT,
  parameter integer PIXEL_WIDTH = (PIXEL_COUNT <= 1) ? 1 : $clog2(PIXEL_COUNT),
  parameter integer SCORE_WIDTH = 24,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer PREDICTION_BINS = 10,
  parameter integer BIN_COUNT_WIDTH =
    (PREDICTION_BINS <= 1) ? 1 : $clog2(PREDICTION_BINS),
  parameter integer WEIGHT_COUNT = CLASS_COUNT * INPUT_CHANNELS,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] READOUT_WEIGHTS = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in_payload,
  input  logic in_completion,
  input  logic [TAG_WIDTH-1:0] in_bin_tag,
  output logic prediction_valid,
  input  logic prediction_ready,
  output logic [X_WIDTH-1:0] prediction_x_o,
  output logic [Y_WIDTH-1:0] prediction_y_o,
  output logic [CLASS_WIDTH-1:0] prediction_class_o,
  output logic frame_done_valid,
  input  logic frame_done_ready,
  output logic [TAG_WIDTH-1:0] frame_bin_tag_o,
  output logic address_error_o
);
  localparam [1:0] COLLECT = 2'd0, FLUSH = 2'd1, FRAME_DONE = 2'd2;
  localparam integer MAX_SCORE = (1 << (SCORE_WIDTH - 1)) - 1;
  localparam integer MIN_SCORE = -(1 << (SCORE_WIDTH - 1));
  logic [1:0] state_reg;
  logic signed [SCORE_WIDTH-1:0] score_mem [0:PIXEL_COUNT-1][0:CLASS_COUNT-1];
  logic [BIN_COUNT_WIDTH-1:0] bin_count_reg;
  logic [PIXEL_WIDTH-1:0] flush_pixel_reg;
  logic [TAG_WIDTH-1:0] frame_tag_reg;
  integer input_x;
  integer input_y;
  integer input_channel;
  integer input_pixel;
  integer class_index;
  integer pixel_index;
  integer signed contribution;
  integer signed updated_score;
  integer signed best_score;
  integer best_class;

  assign in_ready = (state_reg == COLLECT);
  assign prediction_valid = (state_reg == FLUSH);
  assign frame_done_valid = (state_reg == FRAME_DONE);
  assign frame_bin_tag_o = frame_tag_reg;

  always_comb begin
    input_x = $unsigned(in_payload[X_LSB +: X_WIDTH]);
    input_y = $unsigned(in_payload[Y_LSB +: Y_WIDTH]);
    input_channel = $unsigned(in_payload[CHANNEL_LSB +: CHANNEL_WIDTH]);
    input_pixel = input_y * OUTPUT_WIDTH + input_x;
    address_error_o = in_valid && !in_completion &&
                      (input_x >= OUTPUT_WIDTH || input_y >= OUTPUT_HEIGHT ||
                       input_channel >= INPUT_CHANNELS);

    prediction_x_o = $unsigned(flush_pixel_reg) % OUTPUT_WIDTH;
    prediction_y_o = $unsigned(flush_pixel_reg) / OUTPUT_WIDTH;
    best_score = MIN_SCORE;
    best_class = 0;
    for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      if (class_index == 0 ||
          $signed(score_mem[flush_pixel_reg][class_index]) > best_score) begin
        best_score = $signed(score_mem[flush_pixel_reg][class_index]);
        best_class = class_index;
      end
    end
    prediction_class_o = best_class[CLASS_WIDTH-1:0];
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      bin_count_reg <= '0;
      flush_pixel_reg <= '0;
      frame_tag_reg <= '0;
      for (pixel_index = 0; pixel_index < PIXEL_COUNT; pixel_index = pixel_index + 1)
        for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1)
          score_mem[pixel_index][class_index] <= '0;
    end else begin
      case (state_reg)
        COLLECT: if (in_valid && in_ready) begin
          if (in_completion) begin
            if (bin_count_reg + 1 >= PREDICTION_BINS) begin
              bin_count_reg <= '0;
              flush_pixel_reg <= '0;
              frame_tag_reg <= in_bin_tag;
              state_reg <= FLUSH;
            end else begin
              bin_count_reg <= bin_count_reg + 1'b1;
            end
          end else if (!address_error_o) begin
            for (class_index = 0; class_index < CLASS_COUNT;
                 class_index = class_index + 1) begin
              contribution = $signed(READOUT_WEIGHTS[
                (class_index*INPUT_CHANNELS + input_channel)*WEIGHT_WIDTH +:
                WEIGHT_WIDTH
              ]);
              updated_score = $signed(score_mem[input_pixel][class_index]) + contribution;
              if (updated_score > MAX_SCORE) updated_score = MAX_SCORE;
              if (updated_score < MIN_SCORE) updated_score = MIN_SCORE;
              score_mem[input_pixel][class_index] <= updated_score[SCORE_WIDTH-1:0];
            end
          end
        end
        FLUSH: if (prediction_valid && prediction_ready) begin
          for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1)
            score_mem[flush_pixel_reg][class_index] <= '0;
          if (flush_pixel_reg + 1 >= PIXEL_COUNT)
            state_reg <= FRAME_DONE;
          else
            flush_pixel_reg <= flush_pixel_reg + 1'b1;
        end
        FRAME_DONE: if (frame_done_valid && frame_done_ready)
          state_reg <= COLLECT;
        default: state_reg <= COLLECT;
      endcase
    end
  end
endmodule
