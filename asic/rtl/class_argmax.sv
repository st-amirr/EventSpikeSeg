`timescale 1ns/1ps
module class_argmax #(
  parameter integer CLASS_COUNT = 6,
  parameter integer SCORE_WIDTH = 24,
  parameter integer CLASS_WIDTH = 3
) (
  input  logic signed [CLASS_COUNT*SCORE_WIDTH-1:0] scores_i,
  output logic [CLASS_WIDTH-1:0] class_o
);
  integer class_index;
  integer best_index;
  logic signed [SCORE_WIDTH-1:0] best_score;
  logic signed [SCORE_WIDTH-1:0] candidate;

  always_comb begin
    best_index = 0;
    best_score = scores_i[0 +: SCORE_WIDTH];
    for (class_index = 1; class_index < CLASS_COUNT; class_index = class_index + 1) begin
      candidate = scores_i[class_index*SCORE_WIDTH +: SCORE_WIDTH];
      if (candidate > best_score) begin
        best_score = candidate;
        best_index = class_index;
      end
    end
    class_o = best_index[CLASS_WIDTH-1:0];
  end
endmodule
