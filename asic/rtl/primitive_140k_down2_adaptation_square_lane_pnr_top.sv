`timescale 1ns/1ps
module primitive_140k_down2_adaptation_square_lane_pnr_top (
  input logic clk,
  input logic [23:0] candidate_i,
  input logic [23:0] shared_penalty_i,
  output logic [47:0] square_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_square_lane lane (
    .candidate_i(candidate_i), .shared_penalty_i(shared_penalty_i),
    .square_o(square_o)
  );
endmodule
