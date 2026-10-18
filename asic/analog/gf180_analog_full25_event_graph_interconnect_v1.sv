`timescale 1ns/1ps
// Generated categorical interconnect for the original 25-actor analog graph.
// Only event addresses, completion tokens, and bin tags pass through this module.
// PLIF numerical state/weights and class-current computation remain analog.
module gf180_analog_full25_event_graph_interconnect_v1 (
  input logic clk, input logic reset,
  input logic ingress_valid_i, output logic ingress_ready_o,
  input logic [31:0] ingress_payload_i, input logic ingress_completion_i,
  input logic [23:0] ingress_bin_tag_i,
  input logic [24:0] actor_out_valid_i, output logic [24:0] actor_out_ready_o,
  input logic [24:0][31:0] actor_out_payload_i, input logic [24:0] actor_out_completion_i,
  input logic [24:0][23:0] actor_out_bin_tag_i,
  output logic [24:0] actor_in_valid_o, input logic [24:0] actor_in_ready_i,
  output logic [24:0][31:0] actor_in_payload_o, output logic [24:0] actor_in_completion_o,
  output logic [24:0][23:0] actor_in_bin_tag_o,
  output logic head_event_valid_o, input logic head_event_ready_i,
  output logic [31:0] head_event_payload_o, output logic head_event_completion_o,
  output logic [23:0] head_event_bin_tag_o,
  output logic [8:0] residual_error_o,
  output logic [2:0] upsample_error_o,
  output logic [1:0] concat_error_o,
  output logic skip_tag_mismatch_o
);
  // Per-edge valid/ready payload and bin completion signals.
  logic e00_valid, e00_ready, e00_completion;
  logic [31:0] e00_payload;
  logic [23:0] e00_tag;
  logic e01_valid, e01_ready, e01_completion;
  logic [31:0] e01_payload;
  logic [23:0] e01_tag;
  logic e02_valid, e02_ready, e02_completion;
  logic [31:0] e02_payload;
  logic [23:0] e02_tag;
  logic e03_valid, e03_ready, e03_completion;
  logic [31:0] e03_payload;
  logic [23:0] e03_tag;
  logic e04_valid, e04_ready, e04_completion;
  logic [31:0] e04_payload;
  logic [23:0] e04_tag;
  logic e05_valid, e05_ready, e05_completion;
  logic [31:0] e05_payload;
  logic [23:0] e05_tag;
  logic e06_valid, e06_ready, e06_completion;
  logic [31:0] e06_payload;
  logic [23:0] e06_tag;
  logic e07_valid, e07_ready, e07_completion;
  logic [31:0] e07_payload;
  logic [23:0] e07_tag;
  logic e08_valid, e08_ready, e08_completion;
  logic [31:0] e08_payload;
  logic [23:0] e08_tag;
  logic e09_valid, e09_ready, e09_completion;
  logic [31:0] e09_payload;
  logic [23:0] e09_tag;
  logic e10_valid, e10_ready, e10_completion;
  logic [31:0] e10_payload;
  logic [23:0] e10_tag;
  logic e11_valid, e11_ready, e11_completion;
  logic [31:0] e11_payload;
  logic [23:0] e11_tag;
  logic e12_valid, e12_ready, e12_completion;
  logic [31:0] e12_payload;
  logic [23:0] e12_tag;
  logic e13_valid, e13_ready, e13_completion;
  logic [31:0] e13_payload;
  logic [23:0] e13_tag;
  logic e14_valid, e14_ready, e14_completion;
  logic [31:0] e14_payload;
  logic [23:0] e14_tag;
  logic e15_valid, e15_ready, e15_completion;
  logic [31:0] e15_payload;
  logic [23:0] e15_tag;
  logic e16_valid, e16_ready, e16_completion;
  logic [31:0] e16_payload;
  logic [23:0] e16_tag;
  logic e17_valid, e17_ready, e17_completion;
  logic [31:0] e17_payload;
  logic [23:0] e17_tag;
  logic e18_valid, e18_ready, e18_completion;
  logic [31:0] e18_payload;
  logic [23:0] e18_tag;
  logic e19_valid, e19_ready, e19_completion;
  logic [31:0] e19_payload;
  logic [23:0] e19_tag;
  logic e20_valid, e20_ready, e20_completion;
  logic [31:0] e20_payload;
  logic [23:0] e20_tag;
  logic e21_valid, e21_ready, e21_completion;
  logic [31:0] e21_payload;
  logic [23:0] e21_tag;
  logic e22_valid, e22_ready, e22_completion;
  logic [31:0] e22_payload;
  logic [23:0] e22_tag;
  logic e23_valid, e23_ready, e23_completion;
  logic [31:0] e23_payload;
  logic [23:0] e23_tag;
  logic e24_valid, e24_ready, e24_completion;
  logic [31:0] e24_payload;
  logic [23:0] e24_tag;
  logic e25_valid, e25_ready, e25_completion;
  logic [31:0] e25_payload;
  logic [23:0] e25_tag;
  logic e26_valid, e26_ready, e26_completion;
  logic [31:0] e26_payload;
  logic [23:0] e26_tag;
  logic e27_valid, e27_ready, e27_completion;
  logic [31:0] e27_payload;
  logic [23:0] e27_tag;
  logic e28_valid, e28_ready, e28_completion;
  logic [31:0] e28_payload;
  logic [23:0] e28_tag;
  logic e29_valid, e29_ready, e29_completion;
  logic [31:0] e29_payload;
  logic [23:0] e29_tag;
  logic e30_valid, e30_ready, e30_completion;
  logic [31:0] e30_payload;
  logic [23:0] e30_tag;
  logic e31_valid, e31_ready, e31_completion;
  logic [31:0] e31_payload;
  logic [23:0] e31_tag;
  logic e32_valid, e32_ready, e32_completion;
  logic [31:0] e32_payload;
  logic [23:0] e32_tag;
  logic e33_valid, e33_ready, e33_completion;
  logic [31:0] e33_payload;
  logic [23:0] e33_tag;
  logic e34_valid, e34_ready, e34_completion;
  logic [31:0] e34_payload;
  logic [23:0] e34_tag;
  logic e35_valid, e35_ready, e35_completion;
  logic [31:0] e35_payload;
  logic [23:0] e35_tag;
  logic e36_valid, e36_ready, e36_completion;
  logic [31:0] e36_payload;
  logic [23:0] e36_tag;
  logic e37_valid, e37_ready, e37_completion;
  logic [31:0] e37_payload;
  logic [23:0] e37_tag;
  logic e38_valid, e38_ready, e38_completion;
  logic [31:0] e38_payload;
  logic [23:0] e38_tag;
  logic e39_valid, e39_ready, e39_completion;
  logic [31:0] e39_payload;
  logic [23:0] e39_tag;
  logic e40_valid, e40_ready, e40_completion;
  logic [31:0] e40_payload;
  logic [23:0] e40_tag;
  logic e41_valid, e41_ready, e41_completion;
  logic [31:0] e41_payload;
  logic [23:0] e41_tag;
  logic e42_valid, e42_ready, e42_completion;
  logic [31:0] e42_payload;
  logic [23:0] e42_tag;
  logic e43_valid, e43_ready, e43_completion;
  logic [31:0] e43_payload;
  logic [23:0] e43_tag;
  logic e44_valid, e44_ready, e44_completion;
  logic [31:0] e44_payload;
  logic [23:0] e44_tag;
  logic e45_valid, e45_ready, e45_completion;
  logic [31:0] e45_payload;
  logic [23:0] e45_tag;
  logic e46_valid, e46_ready, e46_completion;
  logic [31:0] e46_payload;
  logic [23:0] e46_tag;
  logic e47_valid, e47_ready, e47_completion;
  logic [31:0] e47_payload;
  logic [23:0] e47_tag;
  logic e48_valid, e48_ready, e48_completion;
  logic [31:0] e48_payload;
  logic [23:0] e48_tag;
  logic e49_valid, e49_ready, e49_completion;
  logic [31:0] e49_payload;
  logic [23:0] e49_tag;
  logic e50_valid, e50_ready, e50_completion;
  logic [31:0] e50_payload;
  logic [23:0] e50_tag;
  logic e51_valid, e51_ready, e51_completion;
  logic [31:0] e51_payload;
  logic [23:0] e51_tag;
  logic e52_valid, e52_ready, e52_completion;
  logic [31:0] e52_payload;
  logic [23:0] e52_tag;
  logic raw_event_ingress_valid, raw_event_ingress_ready, raw_event_ingress_completion;
  logic [31:0] raw_event_ingress_payload;
  logic [23:0] raw_event_ingress_tag;
  logic detail_stem_valid, detail_stem_ready, detail_stem_completion;
  logic [31:0] detail_stem_payload;
  logic [23:0] detail_stem_tag;
  logic detail1_standard_valid, detail1_standard_ready, detail1_standard_completion;
  logic [31:0] detail1_standard_payload;
  logic [23:0] detail1_standard_tag;
  logic detail1_residual_valid, detail1_residual_ready, detail1_residual_completion;
  logic [31:0] detail1_residual_payload;
  logic [23:0] detail1_residual_tag;
  logic stem_valid, stem_ready, stem_completion;
  logic [31:0] stem_payload;
  logic [23:0] stem_tag;
  logic enc1_standard_valid, enc1_standard_ready, enc1_standard_completion;
  logic [31:0] enc1_standard_payload;
  logic [23:0] enc1_standard_tag;
  logic enc1_residual_valid, enc1_residual_ready, enc1_residual_completion;
  logic [31:0] enc1_residual_payload;
  logic [23:0] enc1_residual_tag;
  logic enc1_extra_depthwise_valid, enc1_extra_depthwise_ready, enc1_extra_depthwise_completion;
  logic [31:0] enc1_extra_depthwise_payload;
  logic [23:0] enc1_extra_depthwise_tag;
  logic enc1_extra_pointwise_valid, enc1_extra_pointwise_ready, enc1_extra_pointwise_completion;
  logic [31:0] enc1_extra_pointwise_payload;
  logic [23:0] enc1_extra_pointwise_tag;
  logic enc1_extra_residual_valid, enc1_extra_residual_ready, enc1_extra_residual_completion;
  logic [31:0] enc1_extra_residual_payload;
  logic [23:0] enc1_extra_residual_tag;
  logic down2_standard_valid, down2_standard_ready, down2_standard_completion;
  logic [31:0] down2_standard_payload;
  logic [23:0] down2_standard_tag;
  logic enc2_depthwise_valid, enc2_depthwise_ready, enc2_depthwise_completion;
  logic [31:0] enc2_depthwise_payload;
  logic [23:0] enc2_depthwise_tag;
  logic enc2_pointwise_valid, enc2_pointwise_ready, enc2_pointwise_completion;
  logic [31:0] enc2_pointwise_payload;
  logic [23:0] enc2_pointwise_tag;
  logic enc2_residual_valid, enc2_residual_ready, enc2_residual_completion;
  logic [31:0] enc2_residual_payload;
  logic [23:0] enc2_residual_tag;
  logic enc2_extra_depthwise_valid, enc2_extra_depthwise_ready, enc2_extra_depthwise_completion;
  logic [31:0] enc2_extra_depthwise_payload;
  logic [23:0] enc2_extra_depthwise_tag;
  logic enc2_extra_pointwise_valid, enc2_extra_pointwise_ready, enc2_extra_pointwise_completion;
  logic [31:0] enc2_extra_pointwise_payload;
  logic [23:0] enc2_extra_pointwise_tag;
  logic enc2_extra_residual_valid, enc2_extra_residual_ready, enc2_extra_residual_completion;
  logic [31:0] enc2_extra_residual_payload;
  logic [23:0] enc2_extra_residual_tag;
  logic down3_depthwise_valid, down3_depthwise_ready, down3_depthwise_completion;
  logic [31:0] down3_depthwise_payload;
  logic [23:0] down3_depthwise_tag;
  logic down3_pointwise_valid, down3_pointwise_ready, down3_pointwise_completion;
  logic [31:0] down3_pointwise_payload;
  logic [23:0] down3_pointwise_tag;
  logic enc3_depthwise_valid, enc3_depthwise_ready, enc3_depthwise_completion;
  logic [31:0] enc3_depthwise_payload;
  logic [23:0] enc3_depthwise_tag;
  logic enc3_pointwise_valid, enc3_pointwise_ready, enc3_pointwise_completion;
  logic [31:0] enc3_pointwise_payload;
  logic [23:0] enc3_pointwise_tag;
  logic enc3_residual_valid, enc3_residual_ready, enc3_residual_completion;
  logic [31:0] enc3_residual_payload;
  logic [23:0] enc3_residual_tag;
  logic enc3_extra_depthwise_valid, enc3_extra_depthwise_ready, enc3_extra_depthwise_completion;
  logic [31:0] enc3_extra_depthwise_payload;
  logic [23:0] enc3_extra_depthwise_tag;
  logic enc3_extra_pointwise_valid, enc3_extra_pointwise_ready, enc3_extra_pointwise_completion;
  logic [31:0] enc3_extra_pointwise_payload;
  logic [23:0] enc3_extra_pointwise_tag;
  logic enc3_extra_residual_valid, enc3_extra_residual_ready, enc3_extra_residual_completion;
  logic [31:0] enc3_extra_residual_payload;
  logic [23:0] enc3_extra_residual_tag;
  logic context1_depthwise_valid, context1_depthwise_ready, context1_depthwise_completion;
  logic [31:0] context1_depthwise_payload;
  logic [23:0] context1_depthwise_tag;
  logic context1_pointwise_valid, context1_pointwise_ready, context1_pointwise_completion;
  logic [31:0] context1_pointwise_payload;
  logic [23:0] context1_pointwise_tag;
  logic context1_residual_valid, context1_residual_ready, context1_residual_completion;
  logic [31:0] context1_residual_payload;
  logic [23:0] context1_residual_tag;
  logic context2_depthwise_valid, context2_depthwise_ready, context2_depthwise_completion;
  logic [31:0] context2_depthwise_payload;
  logic [23:0] context2_depthwise_tag;
  logic context2_pointwise_valid, context2_pointwise_ready, context2_pointwise_completion;
  logic [31:0] context2_pointwise_payload;
  logic [23:0] context2_pointwise_tag;
  logic context2_residual_valid, context2_residual_ready, context2_residual_completion;
  logic [31:0] context2_residual_payload;
  logic [23:0] context2_residual_tag;
  logic project3_valid, project3_ready, project3_completion;
  logic [31:0] project3_payload;
  logic [23:0] project3_tag;
  logic project3_nearest_valid, project3_nearest_ready, project3_nearest_completion;
  logic [31:0] project3_nearest_payload;
  logic [23:0] project3_nearest_tag;
  logic decoder2_concat_valid, decoder2_concat_ready, decoder2_concat_completion;
  logic [31:0] decoder2_concat_payload;
  logic [23:0] decoder2_concat_tag;
  logic decoder2_fuse_valid, decoder2_fuse_ready, decoder2_fuse_completion;
  logic [31:0] decoder2_fuse_payload;
  logic [23:0] decoder2_fuse_tag;
  logic project2_valid, project2_ready, project2_completion;
  logic [31:0] project2_payload;
  logic [23:0] project2_tag;
  logic project2_nearest_valid, project2_nearest_ready, project2_nearest_completion;
  logic [31:0] project2_nearest_payload;
  logic [23:0] project2_nearest_tag;
  logic semantic_skip_sum_valid, semantic_skip_sum_ready, semantic_skip_sum_completion;
  logic [31:0] semantic_skip_sum_payload;
  logic [23:0] semantic_skip_sum_tag;
  logic semantic_nearest_valid, semantic_nearest_ready, semantic_nearest_completion;
  logic [31:0] semantic_nearest_payload;
  logic [23:0] semantic_nearest_tag;
  logic final_concat_valid, final_concat_ready, final_concat_completion;
  logic [31:0] final_concat_payload;
  logic [23:0] final_concat_tag;
  logic final_fuse_standard_valid, final_fuse_standard_ready, final_fuse_standard_completion;
  logic [31:0] final_fuse_standard_payload;
  logic [23:0] final_fuse_standard_tag;
  assign detail_stem_valid = actor_out_valid_i[0];
  assign detail_stem_payload = actor_out_payload_i[0];
  assign detail_stem_completion = actor_out_completion_i[0];
  assign detail_stem_tag = actor_out_bin_tag_i[0];
  assign detail1_standard_valid = actor_out_valid_i[1];
  assign detail1_standard_payload = actor_out_payload_i[1];
  assign detail1_standard_completion = actor_out_completion_i[1];
  assign detail1_standard_tag = actor_out_bin_tag_i[1];
  assign stem_valid = actor_out_valid_i[2];
  assign stem_payload = actor_out_payload_i[2];
  assign stem_completion = actor_out_completion_i[2];
  assign stem_tag = actor_out_bin_tag_i[2];
  assign enc1_standard_valid = actor_out_valid_i[3];
  assign enc1_standard_payload = actor_out_payload_i[3];
  assign enc1_standard_completion = actor_out_completion_i[3];
  assign enc1_standard_tag = actor_out_bin_tag_i[3];
  assign enc1_extra_depthwise_valid = actor_out_valid_i[4];
  assign enc1_extra_depthwise_payload = actor_out_payload_i[4];
  assign enc1_extra_depthwise_completion = actor_out_completion_i[4];
  assign enc1_extra_depthwise_tag = actor_out_bin_tag_i[4];
  assign enc1_extra_pointwise_valid = actor_out_valid_i[5];
  assign enc1_extra_pointwise_payload = actor_out_payload_i[5];
  assign enc1_extra_pointwise_completion = actor_out_completion_i[5];
  assign enc1_extra_pointwise_tag = actor_out_bin_tag_i[5];
  assign down2_standard_valid = actor_out_valid_i[6];
  assign down2_standard_payload = actor_out_payload_i[6];
  assign down2_standard_completion = actor_out_completion_i[6];
  assign down2_standard_tag = actor_out_bin_tag_i[6];
  assign enc2_depthwise_valid = actor_out_valid_i[7];
  assign enc2_depthwise_payload = actor_out_payload_i[7];
  assign enc2_depthwise_completion = actor_out_completion_i[7];
  assign enc2_depthwise_tag = actor_out_bin_tag_i[7];
  assign enc2_pointwise_valid = actor_out_valid_i[8];
  assign enc2_pointwise_payload = actor_out_payload_i[8];
  assign enc2_pointwise_completion = actor_out_completion_i[8];
  assign enc2_pointwise_tag = actor_out_bin_tag_i[8];
  assign enc2_extra_depthwise_valid = actor_out_valid_i[9];
  assign enc2_extra_depthwise_payload = actor_out_payload_i[9];
  assign enc2_extra_depthwise_completion = actor_out_completion_i[9];
  assign enc2_extra_depthwise_tag = actor_out_bin_tag_i[9];
  assign enc2_extra_pointwise_valid = actor_out_valid_i[10];
  assign enc2_extra_pointwise_payload = actor_out_payload_i[10];
  assign enc2_extra_pointwise_completion = actor_out_completion_i[10];
  assign enc2_extra_pointwise_tag = actor_out_bin_tag_i[10];
  assign down3_depthwise_valid = actor_out_valid_i[11];
  assign down3_depthwise_payload = actor_out_payload_i[11];
  assign down3_depthwise_completion = actor_out_completion_i[11];
  assign down3_depthwise_tag = actor_out_bin_tag_i[11];
  assign down3_pointwise_valid = actor_out_valid_i[12];
  assign down3_pointwise_payload = actor_out_payload_i[12];
  assign down3_pointwise_completion = actor_out_completion_i[12];
  assign down3_pointwise_tag = actor_out_bin_tag_i[12];
  assign enc3_depthwise_valid = actor_out_valid_i[13];
  assign enc3_depthwise_payload = actor_out_payload_i[13];
  assign enc3_depthwise_completion = actor_out_completion_i[13];
  assign enc3_depthwise_tag = actor_out_bin_tag_i[13];
  assign enc3_pointwise_valid = actor_out_valid_i[14];
  assign enc3_pointwise_payload = actor_out_payload_i[14];
  assign enc3_pointwise_completion = actor_out_completion_i[14];
  assign enc3_pointwise_tag = actor_out_bin_tag_i[14];
  assign enc3_extra_depthwise_valid = actor_out_valid_i[15];
  assign enc3_extra_depthwise_payload = actor_out_payload_i[15];
  assign enc3_extra_depthwise_completion = actor_out_completion_i[15];
  assign enc3_extra_depthwise_tag = actor_out_bin_tag_i[15];
  assign enc3_extra_pointwise_valid = actor_out_valid_i[16];
  assign enc3_extra_pointwise_payload = actor_out_payload_i[16];
  assign enc3_extra_pointwise_completion = actor_out_completion_i[16];
  assign enc3_extra_pointwise_tag = actor_out_bin_tag_i[16];
  assign context1_depthwise_valid = actor_out_valid_i[17];
  assign context1_depthwise_payload = actor_out_payload_i[17];
  assign context1_depthwise_completion = actor_out_completion_i[17];
  assign context1_depthwise_tag = actor_out_bin_tag_i[17];
  assign context1_pointwise_valid = actor_out_valid_i[18];
  assign context1_pointwise_payload = actor_out_payload_i[18];
  assign context1_pointwise_completion = actor_out_completion_i[18];
  assign context1_pointwise_tag = actor_out_bin_tag_i[18];
  assign context2_depthwise_valid = actor_out_valid_i[19];
  assign context2_depthwise_payload = actor_out_payload_i[19];
  assign context2_depthwise_completion = actor_out_completion_i[19];
  assign context2_depthwise_tag = actor_out_bin_tag_i[19];
  assign context2_pointwise_valid = actor_out_valid_i[20];
  assign context2_pointwise_payload = actor_out_payload_i[20];
  assign context2_pointwise_completion = actor_out_completion_i[20];
  assign context2_pointwise_tag = actor_out_bin_tag_i[20];
  assign project3_valid = actor_out_valid_i[21];
  assign project3_payload = actor_out_payload_i[21];
  assign project3_completion = actor_out_completion_i[21];
  assign project3_tag = actor_out_bin_tag_i[21];
  assign decoder2_fuse_valid = actor_out_valid_i[22];
  assign decoder2_fuse_payload = actor_out_payload_i[22];
  assign decoder2_fuse_completion = actor_out_completion_i[22];
  assign decoder2_fuse_tag = actor_out_bin_tag_i[22];
  assign project2_valid = actor_out_valid_i[23];
  assign project2_payload = actor_out_payload_i[23];
  assign project2_completion = actor_out_completion_i[23];
  assign project2_tag = actor_out_bin_tag_i[23];
  assign final_fuse_standard_valid = actor_out_valid_i[24];
  assign final_fuse_standard_payload = actor_out_payload_i[24];
  assign final_fuse_standard_completion = actor_out_completion_i[24];
  assign final_fuse_standard_tag = actor_out_bin_tag_i[24];
  assign raw_event_ingress_valid = ingress_valid_i;
  assign raw_event_ingress_payload = ingress_payload_i;
  assign raw_event_ingress_completion = ingress_completion_i;
  assign raw_event_ingress_tag = ingress_bin_tag_i;
  assign actor_in_valid_o[0] = e00_valid;
  assign actor_in_payload_o[0] = e00_payload;
  assign actor_in_completion_o[0] = e00_completion;
  assign actor_in_bin_tag_o[0] = e00_tag;
  assign e00_ready = actor_in_ready_i[0];
  assign actor_in_valid_o[1] = e01_valid;
  assign actor_in_payload_o[1] = e01_payload;
  assign actor_in_completion_o[1] = e01_completion;
  assign actor_in_bin_tag_o[1] = e01_tag;
  assign e01_ready = actor_in_ready_i[1];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_0 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e02_valid), .in0_ready_o(e02_ready), .in0_payload_i(e02_payload), .in0_completion_i(e02_completion), .in0_bin_tag_i(e02_tag),
    .in1_valid_i(e03_valid), .in1_ready_o(e03_ready), .in1_payload_i(e03_payload), .in1_completion_i(e03_completion), .in1_bin_tag_i(e03_tag),
    .out_valid_o(detail1_residual_valid), .out_ready_i(detail1_residual_ready), .out_payload_o(detail1_residual_payload), .out_completion_o(detail1_residual_completion), .out_bin_tag_o(detail1_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[0]), .overflow_o() );
  assign actor_in_valid_o[2] = e04_valid;
  assign actor_in_payload_o[2] = e04_payload;
  assign actor_in_completion_o[2] = e04_completion;
  assign actor_in_bin_tag_o[2] = e04_tag;
  assign e04_ready = actor_in_ready_i[2];
  assign actor_in_valid_o[3] = e05_valid;
  assign actor_in_payload_o[3] = e05_payload;
  assign actor_in_completion_o[3] = e05_completion;
  assign actor_in_bin_tag_o[3] = e05_tag;
  assign e05_ready = actor_in_ready_i[3];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_1 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e06_valid), .in0_ready_o(e06_ready), .in0_payload_i(e06_payload), .in0_completion_i(e06_completion), .in0_bin_tag_i(e06_tag),
    .in1_valid_i(e07_valid), .in1_ready_o(e07_ready), .in1_payload_i(e07_payload), .in1_completion_i(e07_completion), .in1_bin_tag_i(e07_tag),
    .out_valid_o(enc1_residual_valid), .out_ready_i(enc1_residual_ready), .out_payload_o(enc1_residual_payload), .out_completion_o(enc1_residual_completion), .out_bin_tag_o(enc1_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[1]), .overflow_o() );
  assign actor_in_valid_o[4] = e08_valid;
  assign actor_in_payload_o[4] = e08_payload;
  assign actor_in_completion_o[4] = e08_completion;
  assign actor_in_bin_tag_o[4] = e08_tag;
  assign e08_ready = actor_in_ready_i[4];
  assign actor_in_valid_o[5] = e09_valid;
  assign actor_in_payload_o[5] = e09_payload;
  assign actor_in_completion_o[5] = e09_completion;
  assign actor_in_bin_tag_o[5] = e09_tag;
  assign e09_ready = actor_in_ready_i[5];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_2 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e10_valid), .in0_ready_o(e10_ready), .in0_payload_i(e10_payload), .in0_completion_i(e10_completion), .in0_bin_tag_i(e10_tag),
    .in1_valid_i(e11_valid), .in1_ready_o(e11_ready), .in1_payload_i(e11_payload), .in1_completion_i(e11_completion), .in1_bin_tag_i(e11_tag),
    .out_valid_o(enc1_extra_residual_valid), .out_ready_i(enc1_extra_residual_ready), .out_payload_o(enc1_extra_residual_payload), .out_completion_o(enc1_extra_residual_completion), .out_bin_tag_o(enc1_extra_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[2]), .overflow_o() );
  assign actor_in_valid_o[6] = e12_valid;
  assign actor_in_payload_o[6] = e12_payload;
  assign actor_in_completion_o[6] = e12_completion;
  assign actor_in_bin_tag_o[6] = e12_tag;
  assign e12_ready = actor_in_ready_i[6];
  assign actor_in_valid_o[7] = e13_valid;
  assign actor_in_payload_o[7] = e13_payload;
  assign actor_in_completion_o[7] = e13_completion;
  assign actor_in_bin_tag_o[7] = e13_tag;
  assign e13_ready = actor_in_ready_i[7];
  assign actor_in_valid_o[8] = e14_valid;
  assign actor_in_payload_o[8] = e14_payload;
  assign actor_in_completion_o[8] = e14_completion;
  assign actor_in_bin_tag_o[8] = e14_tag;
  assign e14_ready = actor_in_ready_i[8];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_3 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e15_valid), .in0_ready_o(e15_ready), .in0_payload_i(e15_payload), .in0_completion_i(e15_completion), .in0_bin_tag_i(e15_tag),
    .in1_valid_i(e16_valid), .in1_ready_o(e16_ready), .in1_payload_i(e16_payload), .in1_completion_i(e16_completion), .in1_bin_tag_i(e16_tag),
    .out_valid_o(enc2_residual_valid), .out_ready_i(enc2_residual_ready), .out_payload_o(enc2_residual_payload), .out_completion_o(enc2_residual_completion), .out_bin_tag_o(enc2_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[3]), .overflow_o() );
  assign actor_in_valid_o[9] = e17_valid;
  assign actor_in_payload_o[9] = e17_payload;
  assign actor_in_completion_o[9] = e17_completion;
  assign actor_in_bin_tag_o[9] = e17_tag;
  assign e17_ready = actor_in_ready_i[9];
  assign actor_in_valid_o[10] = e18_valid;
  assign actor_in_payload_o[10] = e18_payload;
  assign actor_in_completion_o[10] = e18_completion;
  assign actor_in_bin_tag_o[10] = e18_tag;
  assign e18_ready = actor_in_ready_i[10];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_4 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e19_valid), .in0_ready_o(e19_ready), .in0_payload_i(e19_payload), .in0_completion_i(e19_completion), .in0_bin_tag_i(e19_tag),
    .in1_valid_i(e20_valid), .in1_ready_o(e20_ready), .in1_payload_i(e20_payload), .in1_completion_i(e20_completion), .in1_bin_tag_i(e20_tag),
    .out_valid_o(enc2_extra_residual_valid), .out_ready_i(enc2_extra_residual_ready), .out_payload_o(enc2_extra_residual_payload), .out_completion_o(enc2_extra_residual_completion), .out_bin_tag_o(enc2_extra_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[4]), .overflow_o() );
  assign actor_in_valid_o[11] = e21_valid;
  assign actor_in_payload_o[11] = e21_payload;
  assign actor_in_completion_o[11] = e21_completion;
  assign actor_in_bin_tag_o[11] = e21_tag;
  assign e21_ready = actor_in_ready_i[11];
  assign actor_in_valid_o[12] = e22_valid;
  assign actor_in_payload_o[12] = e22_payload;
  assign actor_in_completion_o[12] = e22_completion;
  assign actor_in_bin_tag_o[12] = e22_tag;
  assign e22_ready = actor_in_ready_i[12];
  assign actor_in_valid_o[13] = e23_valid;
  assign actor_in_payload_o[13] = e23_payload;
  assign actor_in_completion_o[13] = e23_completion;
  assign actor_in_bin_tag_o[13] = e23_tag;
  assign e23_ready = actor_in_ready_i[13];
  assign actor_in_valid_o[14] = e24_valid;
  assign actor_in_payload_o[14] = e24_payload;
  assign actor_in_completion_o[14] = e24_completion;
  assign actor_in_bin_tag_o[14] = e24_tag;
  assign e24_ready = actor_in_ready_i[14];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_5 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e25_valid), .in0_ready_o(e25_ready), .in0_payload_i(e25_payload), .in0_completion_i(e25_completion), .in0_bin_tag_i(e25_tag),
    .in1_valid_i(e26_valid), .in1_ready_o(e26_ready), .in1_payload_i(e26_payload), .in1_completion_i(e26_completion), .in1_bin_tag_i(e26_tag),
    .out_valid_o(enc3_residual_valid), .out_ready_i(enc3_residual_ready), .out_payload_o(enc3_residual_payload), .out_completion_o(enc3_residual_completion), .out_bin_tag_o(enc3_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[5]), .overflow_o() );
  assign actor_in_valid_o[15] = e27_valid;
  assign actor_in_payload_o[15] = e27_payload;
  assign actor_in_completion_o[15] = e27_completion;
  assign actor_in_bin_tag_o[15] = e27_tag;
  assign e27_ready = actor_in_ready_i[15];
  assign actor_in_valid_o[16] = e28_valid;
  assign actor_in_payload_o[16] = e28_payload;
  assign actor_in_completion_o[16] = e28_completion;
  assign actor_in_bin_tag_o[16] = e28_tag;
  assign e28_ready = actor_in_ready_i[16];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_6 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e29_valid), .in0_ready_o(e29_ready), .in0_payload_i(e29_payload), .in0_completion_i(e29_completion), .in0_bin_tag_i(e29_tag),
    .in1_valid_i(e30_valid), .in1_ready_o(e30_ready), .in1_payload_i(e30_payload), .in1_completion_i(e30_completion), .in1_bin_tag_i(e30_tag),
    .out_valid_o(enc3_extra_residual_valid), .out_ready_i(enc3_extra_residual_ready), .out_payload_o(enc3_extra_residual_payload), .out_completion_o(enc3_extra_residual_completion), .out_bin_tag_o(enc3_extra_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[6]), .overflow_o() );
  assign actor_in_valid_o[17] = e31_valid;
  assign actor_in_payload_o[17] = e31_payload;
  assign actor_in_completion_o[17] = e31_completion;
  assign actor_in_bin_tag_o[17] = e31_tag;
  assign e31_ready = actor_in_ready_i[17];
  assign actor_in_valid_o[18] = e32_valid;
  assign actor_in_payload_o[18] = e32_payload;
  assign actor_in_completion_o[18] = e32_completion;
  assign actor_in_bin_tag_o[18] = e32_tag;
  assign e32_ready = actor_in_ready_i[18];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_7 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e33_valid), .in0_ready_o(e33_ready), .in0_payload_i(e33_payload), .in0_completion_i(e33_completion), .in0_bin_tag_i(e33_tag),
    .in1_valid_i(e34_valid), .in1_ready_o(e34_ready), .in1_payload_i(e34_payload), .in1_completion_i(e34_completion), .in1_bin_tag_i(e34_tag),
    .out_valid_o(context1_residual_valid), .out_ready_i(context1_residual_ready), .out_payload_o(context1_residual_payload), .out_completion_o(context1_residual_completion), .out_bin_tag_o(context1_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[7]), .overflow_o() );
  assign actor_in_valid_o[19] = e35_valid;
  assign actor_in_payload_o[19] = e35_payload;
  assign actor_in_completion_o[19] = e35_completion;
  assign actor_in_bin_tag_o[19] = e35_tag;
  assign e35_ready = actor_in_ready_i[19];
  assign actor_in_valid_o[20] = e36_valid;
  assign actor_in_payload_o[20] = e36_payload;
  assign actor_in_completion_o[20] = e36_completion;
  assign actor_in_bin_tag_o[20] = e36_tag;
  assign e36_ready = actor_in_ready_i[20];
  gf180_analog_binary_event_merge_sorted2_wrapper u_residual_8 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e37_valid), .in0_ready_o(e37_ready), .in0_payload_i(e37_payload), .in0_completion_i(e37_completion), .in0_bin_tag_i(e37_tag),
    .in1_valid_i(e38_valid), .in1_ready_o(e38_ready), .in1_payload_i(e38_payload), .in1_completion_i(e38_completion), .in1_bin_tag_i(e38_tag),
    .out_valid_o(context2_residual_valid), .out_ready_i(context2_residual_ready), .out_payload_o(context2_residual_payload), .out_completion_o(context2_residual_completion), .out_bin_tag_o(context2_residual_tag),
    .tag_mismatch_o(), .address_order_error_o(residual_error_o[8]), .overflow_o() );
  assign actor_in_valid_o[21] = e39_valid;
  assign actor_in_payload_o[21] = e39_payload;
  assign actor_in_completion_o[21] = e39_completion;
  assign actor_in_bin_tag_o[21] = e39_tag;
  assign e39_ready = actor_in_ready_i[21];
  gf180_analog_event_upsample2x u_upsample_0 (
    .clk(clk), .reset(reset),
    .in_valid_i(e40_valid), .in_ready_o(e40_ready), .in_payload_i(e40_payload), .in_completion_i(e40_completion), .in_bin_tag_i(e40_tag),
    .out_valid_o(project3_nearest_valid), .out_ready_i(project3_nearest_ready), .out_payload_o(project3_nearest_payload), .out_completion_o(project3_nearest_completion), .out_bin_tag_o(project3_nearest_tag), .coordinate_overflow_o(upsample_error_o[0]) );
  logic decoder2_concat_upper_valid, decoder2_concat_upper_ready, decoder2_concat_upper_completion, decoder2_concat_upper_overflow;
  logic [31:0] decoder2_concat_upper_payload;
  logic [23:0] decoder2_concat_upper_tag;
  event_channel_offset #(.PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .CHANNEL_OFFSET(64)) u_channel_offset_0 (
    .in_valid(e42_valid), .in_ready(e42_ready), .in_payload(e42_payload), .in_completion(e42_completion), .in_bin_tag(e42_tag),
    .out_valid(decoder2_concat_upper_valid), .out_ready(decoder2_concat_upper_ready), .out_payload(decoder2_concat_upper_payload), .out_completion(decoder2_concat_upper_completion), .out_bin_tag(decoder2_concat_upper_tag), .channel_overflow_o(decoder2_concat_upper_overflow) );
  gf180_analog_event_join2 u_concat_0 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e41_valid), .in0_ready_o(e41_ready), .in0_payload_i(e41_payload), .in0_completion_i(e41_completion), .in0_bin_tag_i(e41_tag),
    .in1_valid_i(decoder2_concat_upper_valid), .in1_ready_o(decoder2_concat_upper_ready), .in1_payload_i(decoder2_concat_upper_payload), .in1_completion_i(decoder2_concat_upper_completion), .in1_bin_tag_i(decoder2_concat_upper_tag),
    .out_valid_o(decoder2_concat_valid), .out_ready_i(decoder2_concat_ready), .out_payload_o(decoder2_concat_payload), .out_completion_o(decoder2_concat_completion), .out_bin_tag_o(decoder2_concat_tag), .tag_mismatch_o(concat_error_o[0]) );
  assign actor_in_valid_o[22] = e43_valid;
  assign actor_in_payload_o[22] = e43_payload;
  assign actor_in_completion_o[22] = e43_completion;
  assign actor_in_bin_tag_o[22] = e43_tag;
  assign e43_ready = actor_in_ready_i[22];
  assign actor_in_valid_o[23] = e44_valid;
  assign actor_in_payload_o[23] = e44_payload;
  assign actor_in_completion_o[23] = e44_completion;
  assign actor_in_bin_tag_o[23] = e44_tag;
  assign e44_ready = actor_in_ready_i[23];
  gf180_analog_event_upsample2x u_upsample_1 (
    .clk(clk), .reset(reset),
    .in_valid_i(e45_valid), .in_ready_o(e45_ready), .in_payload_i(e45_payload), .in_completion_i(e45_completion), .in_bin_tag_i(e45_tag),
    .out_valid_o(project2_nearest_valid), .out_ready_i(project2_nearest_ready), .out_payload_o(project2_nearest_payload), .out_completion_o(project2_nearest_completion), .out_bin_tag_o(project2_nearest_tag), .coordinate_overflow_o(upsample_error_o[1]) );
  gf180_analog_event_join2 u_skip_sum (
    .clk(clk), .reset(reset),
    .in0_valid_i(e46_valid), .in0_ready_o(e46_ready), .in0_payload_i(e46_payload), .in0_completion_i(e46_completion), .in0_bin_tag_i(e46_tag),
    .in1_valid_i(e47_valid), .in1_ready_o(e47_ready), .in1_payload_i(e47_payload), .in1_completion_i(e47_completion), .in1_bin_tag_i(e47_tag),
    .out_valid_o(semantic_skip_sum_valid), .out_ready_i(semantic_skip_sum_ready), .out_payload_o(semantic_skip_sum_payload), .out_completion_o(semantic_skip_sum_completion), .out_bin_tag_o(semantic_skip_sum_tag), .tag_mismatch_o(skip_tag_mismatch_o) );
  gf180_analog_event_upsample2x u_upsample_2 (
    .clk(clk), .reset(reset),
    .in_valid_i(e48_valid), .in_ready_o(e48_ready), .in_payload_i(e48_payload), .in_completion_i(e48_completion), .in_bin_tag_i(e48_tag),
    .out_valid_o(semantic_nearest_valid), .out_ready_i(semantic_nearest_ready), .out_payload_o(semantic_nearest_payload), .out_completion_o(semantic_nearest_completion), .out_bin_tag_o(semantic_nearest_tag), .coordinate_overflow_o(upsample_error_o[2]) );
  logic final_concat_upper_valid, final_concat_upper_ready, final_concat_upper_completion, final_concat_upper_overflow;
  logic [31:0] final_concat_upper_payload;
  logic [23:0] final_concat_upper_tag;
  event_channel_offset #(.PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .CHANNEL_OFFSET(32)) u_channel_offset_1 (
    .in_valid(e50_valid), .in_ready(e50_ready), .in_payload(e50_payload), .in_completion(e50_completion), .in_bin_tag(e50_tag),
    .out_valid(final_concat_upper_valid), .out_ready(final_concat_upper_ready), .out_payload(final_concat_upper_payload), .out_completion(final_concat_upper_completion), .out_bin_tag(final_concat_upper_tag), .channel_overflow_o(final_concat_upper_overflow) );
  gf180_analog_event_join2 u_concat_1 (
    .clk(clk), .reset(reset),
    .in0_valid_i(e49_valid), .in0_ready_o(e49_ready), .in0_payload_i(e49_payload), .in0_completion_i(e49_completion), .in0_bin_tag_i(e49_tag),
    .in1_valid_i(final_concat_upper_valid), .in1_ready_o(final_concat_upper_ready), .in1_payload_i(final_concat_upper_payload), .in1_completion_i(final_concat_upper_completion), .in1_bin_tag_i(final_concat_upper_tag),
    .out_valid_o(final_concat_valid), .out_ready_i(final_concat_ready), .out_payload_o(final_concat_payload), .out_completion_o(final_concat_completion), .out_bin_tag_o(final_concat_tag), .tag_mismatch_o(concat_error_o[1]) );
  assign actor_in_valid_o[24] = e51_valid;
  assign actor_in_payload_o[24] = e51_payload;
  assign actor_in_completion_o[24] = e51_completion;
  assign actor_in_bin_tag_o[24] = e51_tag;
  assign e51_ready = actor_in_ready_i[24];
  assign head_event_valid_o = e52_valid;
  assign head_event_payload_o = e52_payload;
  assign head_event_completion_o = e52_completion;
  assign head_event_bin_tag_o = e52_tag;
  assign e52_ready = head_event_ready_i;
  gf180_analog_event_fork2 u_fork_raw_event_ingress (
    .clk(clk), .reset(reset),
    .in_valid_i(raw_event_ingress_valid), .in_ready_o(raw_event_ingress_ready), .in_payload_i(raw_event_ingress_payload), .in_completion_i(raw_event_ingress_completion), .in_bin_tag_i(raw_event_ingress_tag),
    .out0_valid_o(e00_valid), .out0_ready_i(e00_ready), .out0_payload_o(e00_payload), .out0_completion_o(e00_completion), .out0_bin_tag_o(e00_tag),
    .out1_valid_o(e04_valid), .out1_ready_i(e04_ready), .out1_payload_o(e04_payload), .out1_completion_o(e04_completion), .out1_bin_tag_o(e04_tag) );
  gf180_analog_event_fork2 u_fork_detail_stem (
    .clk(clk), .reset(reset),
    .in_valid_i(detail_stem_valid), .in_ready_o(detail_stem_ready), .in_payload_i(detail_stem_payload), .in_completion_i(detail_stem_completion), .in_bin_tag_i(detail_stem_tag),
    .out0_valid_o(e01_valid), .out0_ready_i(e01_ready), .out0_payload_o(e01_payload), .out0_completion_o(e01_completion), .out0_bin_tag_o(e01_tag),
    .out1_valid_o(e03_valid), .out1_ready_i(e03_ready), .out1_payload_o(e03_payload), .out1_completion_o(e03_completion), .out1_bin_tag_o(e03_tag) );
  assign e02_valid = detail1_standard_valid;
  assign e02_payload = detail1_standard_payload;
  assign e02_completion = detail1_standard_completion;
  assign e02_tag = detail1_standard_tag;
  assign detail1_standard_ready = e02_ready;
  assign e50_valid = detail1_residual_valid;
  assign e50_payload = detail1_residual_payload;
  assign e50_completion = detail1_residual_completion;
  assign e50_tag = detail1_residual_tag;
  assign detail1_residual_ready = e50_ready;
  gf180_analog_event_fork2 u_fork_stem (
    .clk(clk), .reset(reset),
    .in_valid_i(stem_valid), .in_ready_o(stem_ready), .in_payload_i(stem_payload), .in_completion_i(stem_completion), .in_bin_tag_i(stem_tag),
    .out0_valid_o(e05_valid), .out0_ready_i(e05_ready), .out0_payload_o(e05_payload), .out0_completion_o(e05_completion), .out0_bin_tag_o(e05_tag),
    .out1_valid_o(e07_valid), .out1_ready_i(e07_ready), .out1_payload_o(e07_payload), .out1_completion_o(e07_completion), .out1_bin_tag_o(e07_tag) );
  assign e06_valid = enc1_standard_valid;
  assign e06_payload = enc1_standard_payload;
  assign e06_completion = enc1_standard_completion;
  assign e06_tag = enc1_standard_tag;
  assign enc1_standard_ready = e06_ready;
  gf180_analog_event_fork2 u_fork_enc1_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc1_residual_valid), .in_ready_o(enc1_residual_ready), .in_payload_i(enc1_residual_payload), .in_completion_i(enc1_residual_completion), .in_bin_tag_i(enc1_residual_tag),
    .out0_valid_o(e08_valid), .out0_ready_i(e08_ready), .out0_payload_o(e08_payload), .out0_completion_o(e08_completion), .out0_bin_tag_o(e08_tag),
    .out1_valid_o(e11_valid), .out1_ready_i(e11_ready), .out1_payload_o(e11_payload), .out1_completion_o(e11_completion), .out1_bin_tag_o(e11_tag) );
  assign e09_valid = enc1_extra_depthwise_valid;
  assign e09_payload = enc1_extra_depthwise_payload;
  assign e09_completion = enc1_extra_depthwise_completion;
  assign e09_tag = enc1_extra_depthwise_tag;
  assign enc1_extra_depthwise_ready = e09_ready;
  assign e10_valid = enc1_extra_pointwise_valid;
  assign e10_payload = enc1_extra_pointwise_payload;
  assign e10_completion = enc1_extra_pointwise_completion;
  assign e10_tag = enc1_extra_pointwise_tag;
  assign enc1_extra_pointwise_ready = e10_ready;
  gf180_analog_event_fork2 u_fork_enc1_extra_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc1_extra_residual_valid), .in_ready_o(enc1_extra_residual_ready), .in_payload_i(enc1_extra_residual_payload), .in_completion_i(enc1_extra_residual_completion), .in_bin_tag_i(enc1_extra_residual_tag),
    .out0_valid_o(e12_valid), .out0_ready_i(e12_ready), .out0_payload_o(e12_payload), .out0_completion_o(e12_completion), .out0_bin_tag_o(e12_tag),
    .out1_valid_o(e47_valid), .out1_ready_i(e47_ready), .out1_payload_o(e47_payload), .out1_completion_o(e47_completion), .out1_bin_tag_o(e47_tag) );
  gf180_analog_event_fork2 u_fork_down2_standard (
    .clk(clk), .reset(reset),
    .in_valid_i(down2_standard_valid), .in_ready_o(down2_standard_ready), .in_payload_i(down2_standard_payload), .in_completion_i(down2_standard_completion), .in_bin_tag_i(down2_standard_tag),
    .out0_valid_o(e13_valid), .out0_ready_i(e13_ready), .out0_payload_o(e13_payload), .out0_completion_o(e13_completion), .out0_bin_tag_o(e13_tag),
    .out1_valid_o(e16_valid), .out1_ready_i(e16_ready), .out1_payload_o(e16_payload), .out1_completion_o(e16_completion), .out1_bin_tag_o(e16_tag) );
  assign e14_valid = enc2_depthwise_valid;
  assign e14_payload = enc2_depthwise_payload;
  assign e14_completion = enc2_depthwise_completion;
  assign e14_tag = enc2_depthwise_tag;
  assign enc2_depthwise_ready = e14_ready;
  assign e15_valid = enc2_pointwise_valid;
  assign e15_payload = enc2_pointwise_payload;
  assign e15_completion = enc2_pointwise_completion;
  assign e15_tag = enc2_pointwise_tag;
  assign enc2_pointwise_ready = e15_ready;
  gf180_analog_event_fork2 u_fork_enc2_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc2_residual_valid), .in_ready_o(enc2_residual_ready), .in_payload_i(enc2_residual_payload), .in_completion_i(enc2_residual_completion), .in_bin_tag_i(enc2_residual_tag),
    .out0_valid_o(e17_valid), .out0_ready_i(e17_ready), .out0_payload_o(e17_payload), .out0_completion_o(e17_completion), .out0_bin_tag_o(e17_tag),
    .out1_valid_o(e20_valid), .out1_ready_i(e20_ready), .out1_payload_o(e20_payload), .out1_completion_o(e20_completion), .out1_bin_tag_o(e20_tag) );
  assign e18_valid = enc2_extra_depthwise_valid;
  assign e18_payload = enc2_extra_depthwise_payload;
  assign e18_completion = enc2_extra_depthwise_completion;
  assign e18_tag = enc2_extra_depthwise_tag;
  assign enc2_extra_depthwise_ready = e18_ready;
  assign e19_valid = enc2_extra_pointwise_valid;
  assign e19_payload = enc2_extra_pointwise_payload;
  assign e19_completion = enc2_extra_pointwise_completion;
  assign e19_tag = enc2_extra_pointwise_tag;
  assign enc2_extra_pointwise_ready = e19_ready;
  gf180_analog_event_fork2 u_fork_enc2_extra_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc2_extra_residual_valid), .in_ready_o(enc2_extra_residual_ready), .in_payload_i(enc2_extra_residual_payload), .in_completion_i(enc2_extra_residual_completion), .in_bin_tag_i(enc2_extra_residual_tag),
    .out0_valid_o(e21_valid), .out0_ready_i(e21_ready), .out0_payload_o(e21_payload), .out0_completion_o(e21_completion), .out0_bin_tag_o(e21_tag),
    .out1_valid_o(e42_valid), .out1_ready_i(e42_ready), .out1_payload_o(e42_payload), .out1_completion_o(e42_completion), .out1_bin_tag_o(e42_tag) );
  assign e22_valid = down3_depthwise_valid;
  assign e22_payload = down3_depthwise_payload;
  assign e22_completion = down3_depthwise_completion;
  assign e22_tag = down3_depthwise_tag;
  assign down3_depthwise_ready = e22_ready;
  gf180_analog_event_fork2 u_fork_down3_pointwise (
    .clk(clk), .reset(reset),
    .in_valid_i(down3_pointwise_valid), .in_ready_o(down3_pointwise_ready), .in_payload_i(down3_pointwise_payload), .in_completion_i(down3_pointwise_completion), .in_bin_tag_i(down3_pointwise_tag),
    .out0_valid_o(e23_valid), .out0_ready_i(e23_ready), .out0_payload_o(e23_payload), .out0_completion_o(e23_completion), .out0_bin_tag_o(e23_tag),
    .out1_valid_o(e26_valid), .out1_ready_i(e26_ready), .out1_payload_o(e26_payload), .out1_completion_o(e26_completion), .out1_bin_tag_o(e26_tag) );
  assign e24_valid = enc3_depthwise_valid;
  assign e24_payload = enc3_depthwise_payload;
  assign e24_completion = enc3_depthwise_completion;
  assign e24_tag = enc3_depthwise_tag;
  assign enc3_depthwise_ready = e24_ready;
  assign e25_valid = enc3_pointwise_valid;
  assign e25_payload = enc3_pointwise_payload;
  assign e25_completion = enc3_pointwise_completion;
  assign e25_tag = enc3_pointwise_tag;
  assign enc3_pointwise_ready = e25_ready;
  gf180_analog_event_fork2 u_fork_enc3_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc3_residual_valid), .in_ready_o(enc3_residual_ready), .in_payload_i(enc3_residual_payload), .in_completion_i(enc3_residual_completion), .in_bin_tag_i(enc3_residual_tag),
    .out0_valid_o(e27_valid), .out0_ready_i(e27_ready), .out0_payload_o(e27_payload), .out0_completion_o(e27_completion), .out0_bin_tag_o(e27_tag),
    .out1_valid_o(e30_valid), .out1_ready_i(e30_ready), .out1_payload_o(e30_payload), .out1_completion_o(e30_completion), .out1_bin_tag_o(e30_tag) );
  assign e28_valid = enc3_extra_depthwise_valid;
  assign e28_payload = enc3_extra_depthwise_payload;
  assign e28_completion = enc3_extra_depthwise_completion;
  assign e28_tag = enc3_extra_depthwise_tag;
  assign enc3_extra_depthwise_ready = e28_ready;
  assign e29_valid = enc3_extra_pointwise_valid;
  assign e29_payload = enc3_extra_pointwise_payload;
  assign e29_completion = enc3_extra_pointwise_completion;
  assign e29_tag = enc3_extra_pointwise_tag;
  assign enc3_extra_pointwise_ready = e29_ready;
  gf180_analog_event_fork2 u_fork_enc3_extra_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(enc3_extra_residual_valid), .in_ready_o(enc3_extra_residual_ready), .in_payload_i(enc3_extra_residual_payload), .in_completion_i(enc3_extra_residual_completion), .in_bin_tag_i(enc3_extra_residual_tag),
    .out0_valid_o(e31_valid), .out0_ready_i(e31_ready), .out0_payload_o(e31_payload), .out0_completion_o(e31_completion), .out0_bin_tag_o(e31_tag),
    .out1_valid_o(e34_valid), .out1_ready_i(e34_ready), .out1_payload_o(e34_payload), .out1_completion_o(e34_completion), .out1_bin_tag_o(e34_tag) );
  assign e32_valid = context1_depthwise_valid;
  assign e32_payload = context1_depthwise_payload;
  assign e32_completion = context1_depthwise_completion;
  assign e32_tag = context1_depthwise_tag;
  assign context1_depthwise_ready = e32_ready;
  assign e33_valid = context1_pointwise_valid;
  assign e33_payload = context1_pointwise_payload;
  assign e33_completion = context1_pointwise_completion;
  assign e33_tag = context1_pointwise_tag;
  assign context1_pointwise_ready = e33_ready;
  gf180_analog_event_fork2 u_fork_context1_residual (
    .clk(clk), .reset(reset),
    .in_valid_i(context1_residual_valid), .in_ready_o(context1_residual_ready), .in_payload_i(context1_residual_payload), .in_completion_i(context1_residual_completion), .in_bin_tag_i(context1_residual_tag),
    .out0_valid_o(e35_valid), .out0_ready_i(e35_ready), .out0_payload_o(e35_payload), .out0_completion_o(e35_completion), .out0_bin_tag_o(e35_tag),
    .out1_valid_o(e38_valid), .out1_ready_i(e38_ready), .out1_payload_o(e38_payload), .out1_completion_o(e38_completion), .out1_bin_tag_o(e38_tag) );
  assign e36_valid = context2_depthwise_valid;
  assign e36_payload = context2_depthwise_payload;
  assign e36_completion = context2_depthwise_completion;
  assign e36_tag = context2_depthwise_tag;
  assign context2_depthwise_ready = e36_ready;
  assign e37_valid = context2_pointwise_valid;
  assign e37_payload = context2_pointwise_payload;
  assign e37_completion = context2_pointwise_completion;
  assign e37_tag = context2_pointwise_tag;
  assign context2_pointwise_ready = e37_ready;
  assign e39_valid = context2_residual_valid;
  assign e39_payload = context2_residual_payload;
  assign e39_completion = context2_residual_completion;
  assign e39_tag = context2_residual_tag;
  assign context2_residual_ready = e39_ready;
  assign e40_valid = project3_valid;
  assign e40_payload = project3_payload;
  assign e40_completion = project3_completion;
  assign e40_tag = project3_tag;
  assign project3_ready = e40_ready;
  assign e41_valid = project3_nearest_valid;
  assign e41_payload = project3_nearest_payload;
  assign e41_completion = project3_nearest_completion;
  assign e41_tag = project3_nearest_tag;
  assign project3_nearest_ready = e41_ready;
  assign e43_valid = decoder2_concat_valid;
  assign e43_payload = decoder2_concat_payload;
  assign e43_completion = decoder2_concat_completion;
  assign e43_tag = decoder2_concat_tag;
  assign decoder2_concat_ready = e43_ready;
  assign e44_valid = decoder2_fuse_valid;
  assign e44_payload = decoder2_fuse_payload;
  assign e44_completion = decoder2_fuse_completion;
  assign e44_tag = decoder2_fuse_tag;
  assign decoder2_fuse_ready = e44_ready;
  assign e45_valid = project2_valid;
  assign e45_payload = project2_payload;
  assign e45_completion = project2_completion;
  assign e45_tag = project2_tag;
  assign project2_ready = e45_ready;
  assign e46_valid = project2_nearest_valid;
  assign e46_payload = project2_nearest_payload;
  assign e46_completion = project2_nearest_completion;
  assign e46_tag = project2_nearest_tag;
  assign project2_nearest_ready = e46_ready;
  assign e48_valid = semantic_skip_sum_valid;
  assign e48_payload = semantic_skip_sum_payload;
  assign e48_completion = semantic_skip_sum_completion;
  assign e48_tag = semantic_skip_sum_tag;
  assign semantic_skip_sum_ready = e48_ready;
  assign e49_valid = semantic_nearest_valid;
  assign e49_payload = semantic_nearest_payload;
  assign e49_completion = semantic_nearest_completion;
  assign e49_tag = semantic_nearest_tag;
  assign semantic_nearest_ready = e49_ready;
  assign e51_valid = final_concat_valid;
  assign e51_payload = final_concat_payload;
  assign e51_completion = final_concat_completion;
  assign e51_tag = final_concat_tag;
  assign final_concat_ready = e51_ready;
  assign e52_valid = final_fuse_standard_valid;
  assign e52_payload = final_fuse_standard_payload;
  assign e52_completion = final_fuse_standard_completion;
  assign e52_tag = final_fuse_standard_tag;
  assign final_fuse_standard_ready = e52_ready;
  assign ingress_ready_o = raw_event_ingress_ready;
  assign actor_out_ready_o[0] = detail_stem_ready;
  assign actor_out_ready_o[1] = detail1_standard_ready;
  assign actor_out_ready_o[2] = stem_ready;
  assign actor_out_ready_o[3] = enc1_standard_ready;
  assign actor_out_ready_o[4] = enc1_extra_depthwise_ready;
  assign actor_out_ready_o[5] = enc1_extra_pointwise_ready;
  assign actor_out_ready_o[6] = down2_standard_ready;
  assign actor_out_ready_o[7] = enc2_depthwise_ready;
  assign actor_out_ready_o[8] = enc2_pointwise_ready;
  assign actor_out_ready_o[9] = enc2_extra_depthwise_ready;
  assign actor_out_ready_o[10] = enc2_extra_pointwise_ready;
  assign actor_out_ready_o[11] = down3_depthwise_ready;
  assign actor_out_ready_o[12] = down3_pointwise_ready;
  assign actor_out_ready_o[13] = enc3_depthwise_ready;
  assign actor_out_ready_o[14] = enc3_pointwise_ready;
  assign actor_out_ready_o[15] = enc3_extra_depthwise_ready;
  assign actor_out_ready_o[16] = enc3_extra_pointwise_ready;
  assign actor_out_ready_o[17] = context1_depthwise_ready;
  assign actor_out_ready_o[18] = context1_pointwise_ready;
  assign actor_out_ready_o[19] = context2_depthwise_ready;
  assign actor_out_ready_o[20] = context2_pointwise_ready;
  assign actor_out_ready_o[21] = project3_ready;
  assign actor_out_ready_o[22] = decoder2_fuse_ready;
  assign actor_out_ready_o[23] = project2_ready;
  assign actor_out_ready_o[24] = final_fuse_standard_ready;
endmodule
