`timescale 1ns/1ps

// Simulation-only wrapper for the checkpoint-exact enc3.pointwise 1x1 actor.
module xl_actor_activity_vcd_tb (
  input logic clk, input logic reset,
  input logic presynaptic_valid_i, output logic presynaptic_ready_o,
  input logic [127:0] presynaptic_spike_vector_i,
  input logic completion_valid_i, output logic completion_ready_o,
  input logic [23:0] completion_tag_i,
  output logic result_valid_o, input logic result_ready_i,
  output logic [127:0] spike_vector_o,
  output logic [23:0] completion_tag_o, output logic error_o
);
  resident_actor_tile_pnr_top dut (.*);
  initial begin
    $dumpfile("enc3_pointwise_1x1_activity.vcd");
    // Dump bounded scopes: transaction-level stimulus/results plus persistent
    // PLIF state. The generated combinational addition chain is intentionally
    // excluded here; a later gate-netlist simulation must dump mapped nets for
    // power annotation.
    $dumpvars(1, dut);
    $dumpvars(1, dut.actor.mechanism.population);
  end
endmodule
