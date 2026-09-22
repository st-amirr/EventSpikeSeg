`timescale 1ns/1ps
// Exact RMS membrane energy across one 128-channel location.
module primitive_140k_adaptation_energy_reduce128_pnr_top (
  input logic clk,
  input logic [128*48-1:0] squares_i,
  output logic [23:0] membrane_energy_o
);
  logic unused_clk;
  assign unused_clk = clk;
  retinotopic_adaptation_energy_reduce #(.CHANNELS(128)) reducer (
    .squares_i(squares_i), .membrane_energy_o(membrane_energy_o)
  );
endmodule
