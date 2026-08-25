`timescale 1ns/1ps
module class_current_update #(
  parameter integer CLASS_COUNT = 11,
  parameter integer SCORE_WIDTH = 24,
  parameter integer CONTRIBUTION_WIDTH = 8,
  parameter integer CLASS_WIDTH = 4
) (
  input  logic clk,
  input  logic reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic signed [CLASS_COUNT*SCORE_WIDTH-1:0] scores_i,
  input  logic signed [CLASS_COUNT*CONTRIBUTION_WIDTH-1:0] contributions_i,
  input  logic prediction_flush_i,
  output logic out_valid,
  input  logic out_ready,
  output logic signed [CLASS_COUNT*SCORE_WIDTH-1:0] scores_o,
  output logic state_live_o,
  output logic prediction_valid_o,
  output logic [CLASS_WIDTH-1:0] class_o
);
  localparam integer MAX_SCORE = (1 << (SCORE_WIDTH - 1)) - 1;
  localparam integer MIN_SCORE = -(1 << (SCORE_WIDTH - 1));
  logic signed [CLASS_COUNT*SCORE_WIDTH-1:0] updated_scores;
  integer signed old_score;
  integer signed contribution;
  integer signed updated_score;
  integer signed best_score;
  integer best_index;
  integer class_index;
  logic any_live;

  assign in_ready = !out_valid || out_ready;

  always_comb begin
    updated_scores = '0;
    best_score = MIN_SCORE;
    best_index = 0;
    any_live = 1'b0;
    for (class_index = 0; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      old_score = $signed(scores_i[class_index*SCORE_WIDTH +: SCORE_WIDTH]);
      contribution = $signed(
        contributions_i[class_index*CONTRIBUTION_WIDTH +: CONTRIBUTION_WIDTH]
      );
      updated_score = old_score + contribution;
      if (updated_score > MAX_SCORE) updated_score = MAX_SCORE;
      if (updated_score < MIN_SCORE) updated_score = MIN_SCORE;
      updated_scores[class_index*SCORE_WIDTH +: SCORE_WIDTH] =
        updated_score[SCORE_WIDTH-1:0];
      if (updated_score != 0) any_live = 1'b1;
      if (class_index == 0 || updated_score > best_score) begin
        best_score = updated_score;
        best_index = class_index;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      out_valid <= 1'b0;
      scores_o <= '0;
      state_live_o <= 1'b0;
      prediction_valid_o <= 1'b0;
      class_o <= '0;
    end else if (!out_valid || out_ready) begin
      out_valid <= in_valid;
      prediction_valid_o <= 1'b0;
      if (in_valid) begin
        class_o <= best_index[CLASS_WIDTH-1:0];
        prediction_valid_o <= prediction_flush_i;
        if (prediction_flush_i) begin
          scores_o <= '0;
          state_live_o <= 1'b0;
        end else begin
          scores_o <= updated_scores;
          state_live_o <= any_live;
        end
      end
    end
  end
endmodule
