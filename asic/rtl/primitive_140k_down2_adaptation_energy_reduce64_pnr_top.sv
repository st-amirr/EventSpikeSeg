`timescale 1ns/1ps
module primitive_140k_down2_adaptation_energy_reduce64_pnr_top (
  input logic clk,
  input logic [64*48-1:0] squares_i,
  output logic [23:0] membrane_energy_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_energy_reduce reducer (
    .squares_i(squares_i), .membrane_energy_o(membrane_energy_o)
  );
endmodule
