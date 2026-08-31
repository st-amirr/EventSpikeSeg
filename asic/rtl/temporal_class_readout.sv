`timescale 1ns/1ps
// Non-spiking per-pixel temporal class-current readout. All class scores for
// one pixel share one actor-local SRAM word, so a hidden spike performs one
// read-modify-write. Prediction drains and clears one pixel at a time.
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
  parameter integer CLASS_COUNT = 6,
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
  parameter integer USE_STATE_MACRO = 0,
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
  output logic address_error_o,
  output logic initialization_done_o
);
  localparam [2:0] COLLECT = 3'd0, SCORE_WAIT = 3'd1, SCORE_WRITE = 3'd2,
                   FLUSH_READ_ISSUE = 3'd3, FLUSH_READ_WAIT = 3'd4,
                   FLUSH_HOLD = 3'd5, FLUSH_WRITE = 3'd6, FRAME_DONE = 3'd7;
  localparam integer MAX_SCORE = (1 << (SCORE_WIDTH - 1)) - 1;
  localparam integer MIN_SCORE = -(1 << (SCORE_WIDTH - 1));
  localparam integer SCORE_WORD_WIDTH = CLASS_COUNT * SCORE_WIDTH;

  logic [2:0] state_reg;
  logic [BIN_COUNT_WIDTH-1:0] bin_count_reg;
  logic [PIXEL_WIDTH-1:0] input_pixel_reg;
  logic [CHANNEL_WIDTH-1:0] input_channel_reg;
  logic [PIXEL_WIDTH-1:0] flush_pixel_reg;
  logic [TAG_WIDTH-1:0] frame_tag_reg;
  logic score_initialization_done;
  logic score_read_valid, score_read_ready, score_read_response_valid;
  logic [PIXEL_WIDTH-1:0] score_read_address;
  logic [SCORE_WORD_WIDTH-1:0] score_read_data;
  logic score_write_valid, score_write_ready;
  logic [PIXEL_WIDTH-1:0] score_write_address;
  logic [SCORE_WORD_WIDTH-1:0] score_write_data;
  logic [SCORE_WORD_WIDTH-1:0] score_write_data_reg;
  logic [SCORE_WORD_WIDTH-1:0] flush_score_data_reg;
  logic score_request_conflict;

  integer input_x;
  integer input_y;
  integer input_channel;
  integer input_pixel;
  integer class_index;
  integer signed contribution;
  integer signed updated_score;
  integer signed best_score;
  integer best_class;

  assign in_ready = score_initialization_done && (state_reg == COLLECT);
  assign prediction_valid = (state_reg == FLUSH_HOLD);
  assign frame_done_valid = (state_reg == FRAME_DONE);
  assign frame_bin_tag_o = frame_tag_reg;
  assign initialization_done_o = score_initialization_done;
  assign score_read_valid =
    ((state_reg == COLLECT) && in_valid && in_ready && !in_completion &&
     !address_error_o) || (state_reg == FLUSH_READ_ISSUE);
  assign score_read_address = (state_reg == FLUSH_READ_ISSUE) ?
                              flush_pixel_reg : input_pixel[PIXEL_WIDTH-1:0];
  assign score_write_valid = (state_reg == SCORE_WRITE) ||
                             (state_reg == FLUSH_WRITE);
  assign score_write_address = (state_reg == FLUSH_WRITE) ?
                               flush_pixel_reg : input_pixel_reg;
  assign score_write_data = (state_reg == FLUSH_WRITE) ? '0 : score_write_data_reg;

  always_comb begin
    input_x = $unsigned(in_payload[X_LSB +: X_WIDTH]);
    input_y = $unsigned(in_payload[Y_LSB +: Y_WIDTH]);
    input_channel = $unsigned(in_payload[CHANNEL_LSB +: CHANNEL_WIDTH]);
    input_pixel = input_y * OUTPUT_WIDTH + input_x;
    address_error_o = score_request_conflict ||
                      (in_valid && !in_completion &&
                       (input_x >= OUTPUT_WIDTH || input_y >= OUTPUT_HEIGHT ||
                        input_channel >= INPUT_CHANNELS));

    prediction_x_o = $unsigned(flush_pixel_reg) % OUTPUT_WIDTH;
    prediction_y_o = $unsigned(flush_pixel_reg) / OUTPUT_WIDTH;
    best_score = MIN_SCORE;
    best_class = 0;
    for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      if (class_index == 0 ||
          $signed(flush_score_data_reg[class_index*SCORE_WIDTH +: SCORE_WIDTH]) >
          best_score) begin
        best_score =
          $signed(flush_score_data_reg[class_index*SCORE_WIDTH +: SCORE_WIDTH]);
        best_class = class_index;
      end
    end
    prediction_class_o = best_class[CLASS_WIDTH-1:0];
  end

  initialized_actor_state_bank #(
    .DATA_WIDTH(SCORE_WORD_WIDTH), .DEPTH(PIXEL_COUNT),
    .ADDRESS_WIDTH(PIXEL_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) score_bank (
    .clk, .reset, .initialization_done_o(score_initialization_done),
    .read_valid_i(score_read_valid), .read_ready_o(score_read_ready),
    .read_address_i(score_read_address),
    .read_response_valid_o(score_read_response_valid), .read_data_o(score_read_data),
    .write_valid_i(score_write_valid), .write_ready_o(score_write_ready),
    .write_address_i(score_write_address), .write_data_i(score_write_data),
    .request_conflict_o(score_request_conflict)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      bin_count_reg <= '0;
      input_pixel_reg <= '0;
      input_channel_reg <= '0;
      flush_pixel_reg <= '0;
      frame_tag_reg <= '0;
      score_write_data_reg <= '0;
      flush_score_data_reg <= '0;
    end else begin
      case (state_reg)
        COLLECT: if (in_valid && in_ready) begin
          if (in_completion) begin
            if (bin_count_reg + 1 >= PREDICTION_BINS) begin
              bin_count_reg <= '0;
              flush_pixel_reg <= '0;
              frame_tag_reg <= in_bin_tag;
              state_reg <= FLUSH_READ_ISSUE;
            end else begin
              bin_count_reg <= bin_count_reg + 1'b1;
            end
          end else if (!address_error_o && score_read_ready) begin
            input_pixel_reg <= input_pixel[PIXEL_WIDTH-1:0];
            input_channel_reg <= input_channel[CHANNEL_WIDTH-1:0];
            state_reg <= SCORE_WAIT;
          end
        end
        SCORE_WAIT: if (score_read_response_valid) begin
          score_write_data_reg <= score_read_data;
          for (class_index = 0; class_index < CLASS_COUNT;
               class_index = class_index + 1) begin
            contribution = $signed(READOUT_WEIGHTS[
              (class_index*INPUT_CHANNELS + input_channel_reg)*WEIGHT_WIDTH +:
              WEIGHT_WIDTH
            ]);
            updated_score =
              $signed(score_read_data[class_index*SCORE_WIDTH +: SCORE_WIDTH]) +
              contribution;
            if (updated_score > MAX_SCORE) updated_score = MAX_SCORE;
            if (updated_score < MIN_SCORE) updated_score = MIN_SCORE;
            score_write_data_reg[class_index*SCORE_WIDTH +: SCORE_WIDTH] <=
              updated_score[SCORE_WIDTH-1:0];
          end
          state_reg <= SCORE_WRITE;
        end
        SCORE_WRITE: if (score_write_ready) state_reg <= COLLECT;
        FLUSH_READ_ISSUE: if (score_read_ready) state_reg <= FLUSH_READ_WAIT;
        FLUSH_READ_WAIT: if (score_read_response_valid) begin
          flush_score_data_reg <= score_read_data;
          state_reg <= FLUSH_HOLD;
        end
        FLUSH_HOLD: if (prediction_ready) state_reg <= FLUSH_WRITE;
        FLUSH_WRITE: if (score_write_ready) begin
          if (flush_pixel_reg + 1 >= PIXEL_COUNT)
            state_reg <= FRAME_DONE;
          else begin
            flush_pixel_reg <= flush_pixel_reg + 1'b1;
            state_reg <= FLUSH_READ_ISSUE;
          end
        end
        FRAME_DONE: if (frame_done_ready) state_reg <= COLLECT;
        default: state_reg <= COLLECT;
      endcase
    end
  end
endmodule
