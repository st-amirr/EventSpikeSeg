(* blackbox *) module gf180_analog_full25_event_graph_interconnect_v1 (
  input logic clk, input logic reset,
  input logic ingress_valid_i, output logic ingress_ready_o,
  input logic [31:0] ingress_payload_i, input logic ingress_completion_i,
  input logic [23:0] ingress_bin_tag_i,
  input logic [24:0] actor_out_valid_i, output logic [24:0] actor_out_ready_o,
  input logic [799:0] actor_out_payload_i, input logic [24:0] actor_out_completion_i,
  input logic [599:0] actor_out_bin_tag_i,
  output logic [24:0] actor_in_valid_o, input logic [24:0] actor_in_ready_i,
  output logic [799:0] actor_in_payload_o, output logic [24:0] actor_in_completion_o,
  output logic [599:0] actor_in_bin_tag_o,
  output logic head_event_valid_o, input logic head_event_ready_i,
  output logic [31:0] head_event_payload_o, output logic head_event_completion_o,
  output logic [23:0] head_event_bin_tag_o,
  output logic [8:0] residual_error_o,
  output logic [2:0] upsample_error_o,
  output logic [1:0] concat_error_o,
  output logic skip_tag_mismatch_o
);
endmodule

(* blackbox *) module gf180_analog_scalar_result_packet_v1 (
  input wire clk, reset,
  input wire result_valid_i,
  output wire result_ready_o,
  input wire result_spike_i,
  input wire [25:0] result_address_i,
  input wire [23:0] result_bin_tag_i,
  input wire result_last_i,
  output wire event_valid_o,
  input wire event_ready_i,
  output wire [31:0] event_payload_o,
  output wire event_completion_o,
  output wire [23:0] event_bin_tag_o,
  output reg tag_mismatch_o,
  output reg address_order_error_o
);
endmodule
