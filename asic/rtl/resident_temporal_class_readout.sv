`timescale 1ns/1ps
// Register/latch-resident temporal 1x1 class-current readout. Binary input
// spike vectors gate fixed signed weights in parallel at every pixel. Class
// currents remain local through the prediction window; no SRAM fetch is used.
module resident_temporal_class_readout #(
  parameter integer INPUT_CHANNELS = 2,
  parameter integer CLASS_COUNT = 3,
  parameter integer OUTPUT_WIDTH = 2,
  parameter integer OUTPUT_HEIGHT = 2,
  parameter integer SPATIAL_COUNT = OUTPUT_WIDTH*OUTPUT_HEIGHT,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*SPATIAL_COUNT,
  parameter integer SCORE_COUNT = CLASS_COUNT*SPATIAL_COUNT,
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer ACC_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer PREDICTION_BINS = 10,
  parameter integer BIN_COUNT_WIDTH = (PREDICTION_BINS <= 1) ? 1 :
                                      $clog2(PREDICTION_BINS),
  parameter integer SPATIAL_WIDTH = (SPATIAL_COUNT <= 1) ? 1 :
                                    $clog2(SPATIAL_COUNT),
  parameter integer X_WIDTH = (OUTPUT_WIDTH <= 1) ? 1 : $clog2(OUTPUT_WIDTH),
  parameter integer Y_WIDTH = (OUTPUT_HEIGHT <= 1) ? 1 : $clog2(OUTPUT_HEIGHT),
  parameter integer CLASS_WIDTH = (CLASS_COUNT <= 1) ? 1 :
                                  $clog2(CLASS_COUNT),
  parameter integer WEIGHT_COUNT = CLASS_COUNT*INPUT_CHANNELS,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] READOUT_WEIGHTS = '0
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
  output logic [TAG_WIDTH-1:0] frame_tag_o
);
  localparam logic [1:0] COLLECT = 2'd0, EMIT = 2'd1, HOLD_DONE = 2'd2;
  localparam longint signed MAX_ACC = (64'sd1 << (ACC_WIDTH-1))-1;
  localparam longint signed MIN_ACC = -(64'sd1 << (ACC_WIDTH-1));
  logic [1:0] state_reg;
  logic [BIN_COUNT_WIDTH-1:0] bin_count_reg;
  logic [SPATIAL_WIDTH-1:0] spatial_reg;
  logic [SCORE_COUNT*ACC_WIDTH-1:0] score_reg;
  integer selection_score_index;
  integer selection_class_index;
  integer signed selected_class;
  longint signed best_score;
  longint signed candidate_score;

  assign in_ready_o = state_reg == COLLECT;
  assign prediction_valid_o = state_reg == EMIT;
  assign frame_done_valid_o = state_reg == HOLD_DONE;
  assign prediction_x_o = $unsigned(spatial_reg) % OUTPUT_WIDTH;
  assign prediction_y_o = $unsigned(spatial_reg) / OUTPUT_WIDTH;

  always_comb begin
    selected_class = 0;
    best_score = $signed(score_reg[
      $unsigned(spatial_reg)*ACC_WIDTH +: ACC_WIDTH]);
    candidate_score = 0;
    selection_score_index = 0;
    for (selection_class_index = 1; selection_class_index < CLASS_COUNT;
         selection_class_index = selection_class_index+1) begin
      selection_score_index = selection_class_index*SPATIAL_COUNT+
                              $unsigned(spatial_reg);
      candidate_score = $signed(score_reg[
        selection_score_index*ACC_WIDTH +: ACC_WIDTH]);
      if (candidate_score > best_score) begin
        best_score = candidate_score;
        selected_class = selection_class_index;
      end
    end
    prediction_class_o = selected_class[CLASS_WIDTH-1:0];
  end

  generate
    for (genvar generated_score_index = 0;
         generated_score_index < SCORE_COUNT;
         generated_score_index = generated_score_index+1) begin : generated_score
      localparam integer GENERATED_CLASS = generated_score_index/SPATIAL_COUNT;
      localparam integer GENERATED_SPATIAL = generated_score_index%SPATIAL_COUNT;
      localparam integer GENERATED_SCORE_LSB = generated_score_index*ACC_WIDTH;
      longint signed generated_sum_value;
      integer generated_input_channel;
      integer generated_weight_index;

      always_comb begin
        generated_sum_value = $signed(score_reg[
          GENERATED_SCORE_LSB +: ACC_WIDTH]);
        for (generated_input_channel = 0;
             generated_input_channel < INPUT_CHANNELS;
             generated_input_channel = generated_input_channel+1) begin
          generated_weight_index = GENERATED_CLASS*INPUT_CHANNELS+
                                   generated_input_channel;
          if (in_spike_vector_i[
                generated_input_channel*SPATIAL_COUNT+GENERATED_SPATIAL])
            generated_sum_value = generated_sum_value +
              $signed(READOUT_WEIGHTS[
                generated_weight_index*WEIGHT_WIDTH +: WEIGHT_WIDTH]);
        end
      end

      always_ff @(posedge clk) begin
        if (reset)
          score_reg[GENERATED_SCORE_LSB +: ACC_WIDTH] <= '0;
        else if (state_reg == COLLECT && in_valid_i && in_ready_o &&
                 !in_completion_i) begin
          if (generated_sum_value > MAX_ACC)
            score_reg[GENERATED_SCORE_LSB +: ACC_WIDTH] <= MAX_ACC;
          else if (generated_sum_value < MIN_ACC)
            score_reg[GENERATED_SCORE_LSB +: ACC_WIDTH] <= MIN_ACC;
          else
            score_reg[GENERATED_SCORE_LSB +: ACC_WIDTH] <=
              generated_sum_value[ACC_WIDTH-1:0];
        end else if (state_reg == EMIT && prediction_valid_o &&
                     prediction_ready_i &&
                     $unsigned(spatial_reg) == GENERATED_SPATIAL)
          score_reg[GENERATED_SCORE_LSB +: ACC_WIDTH] <= '0;
      end
    end
  endgenerate

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      bin_count_reg <= '0;
      spatial_reg <= '0;
      frame_tag_o <= '0;
    end else case (state_reg)
      COLLECT: if (in_valid_i && in_ready_o) begin
        if (in_completion_i) begin
          frame_tag_o <= in_tag_i;
          if (bin_count_reg+1 >= PREDICTION_BINS) begin
            spatial_reg <= '0;
            state_reg <= EMIT;
          end else bin_count_reg <= bin_count_reg+1'b1;
        end
      end
      EMIT: if (prediction_valid_o && prediction_ready_i) begin
        if (spatial_reg+1 >= SPATIAL_COUNT) state_reg <= HOLD_DONE;
        else spatial_reg <= spatial_reg+1'b1;
      end
      HOLD_DONE: if (frame_done_ready_i) begin
        bin_count_reg <= '0;
        spatial_reg <= '0;
        state_reg <= COLLECT;
      end
      default: state_reg <= COLLECT;
    endcase
  end
endmodule
