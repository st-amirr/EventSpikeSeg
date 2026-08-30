`timescale 1ns/1ps
// Production non-spiking temporal readout. One wide 1R1W SRAM word owns all
// signed class scores for a pixel. Reset scrubs the bank explicitly because a
// compiled SRAM has no portable power-up contents.
module temporal_class_readout_sram #(
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
  parameter integer SCORE_WORD_WIDTH = CLASS_COUNT * SCORE_WIDTH,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer PREDICTION_BINS = 10,
  parameter integer BIN_COUNT_WIDTH =
    (PREDICTION_BINS <= 1) ? 1 : $clog2(PREDICTION_BINS),
  parameter integer WEIGHT_COUNT = CLASS_COUNT * INPUT_CHANNELS,
  parameter integer USE_SCORE_SRAM_MACRO = 0,
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
  localparam [2:0] SCRUB = 3'd0, COLLECT = 3'd1,
    UPDATE_CAPTURE = 3'd2, FLUSH_READ = 3'd3,
    FLUSH_CAPTURE = 3'd4, FLUSH_OUTPUT = 3'd5,
    FRAME_DONE = 3'd6;
  localparam integer MAX_SCORE = (1 << (SCORE_WIDTH - 1)) - 1;
  localparam integer MIN_SCORE = -(1 << (SCORE_WIDTH - 1));

  logic [2:0] state_reg;
  logic [BIN_COUNT_WIDTH-1:0] bin_count_reg;
  logic [PIXEL_WIDTH-1:0] scrub_pixel_reg;
  logic [PIXEL_WIDTH-1:0] flush_pixel_reg;
  logic [PIXEL_WIDTH-1:0] update_pixel_reg;
  logic [CHANNEL_WIDTH-1:0] update_channel_reg;
  logic [TAG_WIDTH-1:0] frame_tag_reg;
  logic [SCORE_WORD_WIDTH-1:0] flush_score_reg;
  logic score_read_enable;
  logic [PIXEL_WIDTH-1:0] score_read_address;
  logic score_read_valid;
  logic [SCORE_WORD_WIDTH-1:0] score_read_data;
  logic score_write_enable;
  logic [PIXEL_WIDTH-1:0] score_write_address;
  logic [SCORE_WORD_WIDTH-1:0] score_write_data;
  logic [SCORE_WORD_WIDTH-1:0] updated_score_word;
  integer input_x;
  integer input_y;
  integer input_channel;
  integer input_pixel;
  integer class_index;
  integer signed contribution;
  integer signed updated_score;
  integer signed best_score;
  integer best_class;

  assign in_ready = (state_reg == COLLECT);
  assign prediction_valid = (state_reg == FLUSH_OUTPUT);
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

    score_read_enable = 1'b0;
    score_read_address = '0;
    if (state_reg == COLLECT && in_valid && !in_completion && !address_error_o) begin
      score_read_enable = 1'b1;
      score_read_address = input_pixel[PIXEL_WIDTH-1:0];
    end else if (state_reg == FLUSH_READ) begin
      score_read_enable = 1'b1;
      score_read_address = flush_pixel_reg;
    end

    updated_score_word = score_read_data;
    for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      contribution = $signed(READOUT_WEIGHTS[
        (class_index*INPUT_CHANNELS + $unsigned(update_channel_reg))*WEIGHT_WIDTH +:
        WEIGHT_WIDTH
      ]);
      updated_score = $signed(score_read_data[
        class_index*SCORE_WIDTH +: SCORE_WIDTH
      ]) + contribution;
      if (updated_score > MAX_SCORE) updated_score = MAX_SCORE;
      if (updated_score < MIN_SCORE) updated_score = MIN_SCORE;
      updated_score_word[class_index*SCORE_WIDTH +: SCORE_WIDTH] =
        updated_score[SCORE_WIDTH-1:0];
    end

    score_write_enable = 1'b0;
    score_write_address = '0;
    score_write_data = '0;
    if (state_reg == SCRUB) begin
      score_write_enable = 1'b1;
      score_write_address = scrub_pixel_reg;
    end else if (state_reg == UPDATE_CAPTURE && score_read_valid) begin
      score_write_enable = 1'b1;
      score_write_address = update_pixel_reg;
      score_write_data = updated_score_word;
    end else if (state_reg == FLUSH_OUTPUT && prediction_ready) begin
      score_write_enable = 1'b1;
      score_write_address = flush_pixel_reg;
    end

    prediction_x_o = $unsigned(flush_pixel_reg) % OUTPUT_WIDTH;
    prediction_y_o = $unsigned(flush_pixel_reg) / OUTPUT_WIDTH;
    best_score = MIN_SCORE;
    best_class = 0;
    for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      if (class_index == 0 ||
          $signed(flush_score_reg[class_index*SCORE_WIDTH +: SCORE_WIDTH]) >
          best_score) begin
        best_score = $signed(flush_score_reg[
          class_index*SCORE_WIDTH +: SCORE_WIDTH
        ]);
        best_class = class_index;
      end
    end
    prediction_class_o = best_class[CLASS_WIDTH-1:0];
  end

  actor_local_state_sram #(
    .DATA_WIDTH(SCORE_WORD_WIDTH), .DEPTH(PIXEL_COUNT),
    .ADDRESS_WIDTH(PIXEL_WIDTH), .USE_MACRO(USE_SCORE_SRAM_MACRO)
  ) score_bank (
    .clk,
    .read_enable_i(score_read_enable), .read_address_i(score_read_address),
    .read_valid_o(score_read_valid), .read_data_o(score_read_data),
    .write_enable_i(score_write_enable), .write_address_i(score_write_address),
    .write_data_i(score_write_data)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= SCRUB;
      bin_count_reg <= '0;
      scrub_pixel_reg <= '0;
      flush_pixel_reg <= '0;
      update_pixel_reg <= '0;
      update_channel_reg <= '0;
      frame_tag_reg <= '0;
      flush_score_reg <= '0;
    end else begin
      case (state_reg)
        SCRUB: begin
          if (scrub_pixel_reg + 1'b1 >= PIXEL_COUNT) begin
            scrub_pixel_reg <= '0;
            state_reg <= COLLECT;
          end else begin
            scrub_pixel_reg <= scrub_pixel_reg + 1'b1;
          end
        end
        COLLECT: if (in_valid && in_ready) begin
          if (in_completion) begin
            if (bin_count_reg + 1 >= PREDICTION_BINS) begin
              bin_count_reg <= '0;
              flush_pixel_reg <= '0;
              frame_tag_reg <= in_bin_tag;
              state_reg <= FLUSH_READ;
            end else begin
              bin_count_reg <= bin_count_reg + 1'b1;
            end
          end else if (!address_error_o) begin
            update_pixel_reg <= input_pixel[PIXEL_WIDTH-1:0];
            update_channel_reg <= input_channel[CHANNEL_WIDTH-1:0];
            state_reg <= UPDATE_CAPTURE;
          end
        end
        UPDATE_CAPTURE: if (score_read_valid)
          state_reg <= COLLECT;
        FLUSH_READ: state_reg <= FLUSH_CAPTURE;
        FLUSH_CAPTURE: if (score_read_valid) begin
          flush_score_reg <= score_read_data;
          state_reg <= FLUSH_OUTPUT;
        end
        FLUSH_OUTPUT: if (prediction_valid && prediction_ready) begin
          if (flush_pixel_reg + 1'b1 >= PIXEL_COUNT)
            state_reg <= FRAME_DONE;
          else begin
            flush_pixel_reg <= flush_pixel_reg + 1'b1;
            state_reg <= FLUSH_READ;
          end
        end
        FRAME_DONE: if (frame_done_valid && frame_done_ready)
          state_reg <= COLLECT;
        default: state_reg <= SCRUB;
      endcase
    end
  end
endmodule
