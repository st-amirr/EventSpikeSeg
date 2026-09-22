`timescale 1ns/1ps
module primitive_140k_down2_adaptation_penalty_reduce64_pnr_top (
  input logic clk,
  input logic [64*24-1:0] penalties_i,
  output logic [23:0] shared_penalty_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_penalty_reduce reducer (
    .penalties_i(penalties_i), .shared_penalty_o(shared_penalty_o)
  );
endmodule
