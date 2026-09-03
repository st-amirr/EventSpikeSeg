`timescale 1ns/1ps
// Generated file: do not hand edit. Source is model_spec.yaml graph + ROM images.
// Lane configuration SHA256: none_single_lane_reference
module eventspikeseg140k_replay_top #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer RESIDUAL_MAX_EVENTS = 64,
  parameter integer EDGE_FIFO_DEPTH = 2,
  parameter integer USE_STATE_MACRO = 0
) (
  input logic clk, input logic reset,
  input logic input_valid, output logic input_ready,
  input logic [PAYLOAD_WIDTH-1:0] input_payload,
  input logic input_completion,
  input logic [TAG_WIDTH-1:0] input_bin_tag,
  output logic prediction_valid, input logic prediction_ready,
  output logic [9:0] prediction_x_o, output logic [8:0] prediction_y_o,
  output logic [2:0] prediction_class_o,
  output logic frame_done_valid, input logic frame_done_ready,
  output logic [TAG_WIDTH-1:0] frame_bin_tag_o,
  output logic fault_o
);
  localparam integer EDGE_FIFO_COUNT_WIDTH = $clog2(EDGE_FIFO_DEPTH+1);
  logic ingress_valid;
  logic ingress_ready;
  logic [PAYLOAD_WIDTH-1:0] ingress_payload;
  logic ingress_completion;
  logic [TAG_WIDTH-1:0] ingress_bin_tag;
  logic all_memories_initialized;
  assign ingress_valid = input_valid && all_memories_initialized;
  assign input_ready = ingress_ready && all_memories_initialized;
  assign ingress_payload = input_payload;
  assign ingress_completion = input_completion;
  assign ingress_bin_tag = input_bin_tag;
  logic n_context1_depthwise_valid;
  logic n_context1_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context1_depthwise_payload;
  logic n_context1_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_context1_depthwise_bin_tag;
  logic n_context1_pointwise_valid;
  logic n_context1_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context1_pointwise_payload;
  logic n_context1_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_context1_pointwise_bin_tag;
  logic n_context1_residual_or_valid;
  logic n_context1_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context1_residual_or_payload;
  logic n_context1_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_context1_residual_or_bin_tag;
  logic n_context2_depthwise_valid;
  logic n_context2_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context2_depthwise_payload;
  logic n_context2_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_context2_depthwise_bin_tag;
  logic n_context2_pointwise_valid;
  logic n_context2_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context2_pointwise_payload;
  logic n_context2_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_context2_pointwise_bin_tag;
  logic n_context2_residual_or_valid;
  logic n_context2_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_context2_residual_or_payload;
  logic n_context2_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_context2_residual_or_bin_tag;
  logic n_decoder2_concat_valid;
  logic n_decoder2_concat_ready;
  logic [PAYLOAD_WIDTH-1:0] n_decoder2_concat_payload;
  logic n_decoder2_concat_completion;
  logic [TAG_WIDTH-1:0] n_decoder2_concat_bin_tag;
  logic n_decoder2_fuse_valid;
  logic n_decoder2_fuse_ready;
  logic [PAYLOAD_WIDTH-1:0] n_decoder2_fuse_payload;
  logic n_decoder2_fuse_completion;
  logic [TAG_WIDTH-1:0] n_decoder2_fuse_bin_tag;
  logic n_detail1_residual_or_valid;
  logic n_detail1_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_detail1_residual_or_payload;
  logic n_detail1_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_detail1_residual_or_bin_tag;
  logic n_detail1_standard_valid;
  logic n_detail1_standard_ready;
  logic [PAYLOAD_WIDTH-1:0] n_detail1_standard_payload;
  logic n_detail1_standard_completion;
  logic [TAG_WIDTH-1:0] n_detail1_standard_bin_tag;
  logic n_detail_stem_valid;
  logic n_detail_stem_ready;
  logic [PAYLOAD_WIDTH-1:0] n_detail_stem_payload;
  logic n_detail_stem_completion;
  logic [TAG_WIDTH-1:0] n_detail_stem_bin_tag;
  logic n_down2_standard_valid;
  logic n_down2_standard_ready;
  logic [PAYLOAD_WIDTH-1:0] n_down2_standard_payload;
  logic n_down2_standard_completion;
  logic [TAG_WIDTH-1:0] n_down2_standard_bin_tag;
  logic n_down3_depthwise_valid;
  logic n_down3_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_down3_depthwise_payload;
  logic n_down3_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_down3_depthwise_bin_tag;
  logic n_down3_pointwise_valid;
  logic n_down3_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_down3_pointwise_payload;
  logic n_down3_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_down3_pointwise_bin_tag;
  logic n_enc1_residual_or_valid;
  logic n_enc1_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc1_residual_or_payload;
  logic n_enc1_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc1_residual_or_bin_tag;
  logic n_enc1_standard_valid;
  logic n_enc1_standard_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc1_standard_payload;
  logic n_enc1_standard_completion;
  logic [TAG_WIDTH-1:0] n_enc1_standard_bin_tag;
  logic n_enc1_extra_depthwise_valid;
  logic n_enc1_extra_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc1_extra_depthwise_payload;
  logic n_enc1_extra_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_enc1_extra_depthwise_bin_tag;
  logic n_enc1_extra_pointwise_valid;
  logic n_enc1_extra_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc1_extra_pointwise_payload;
  logic n_enc1_extra_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_enc1_extra_pointwise_bin_tag;
  logic n_enc1_extra_residual_or_valid;
  logic n_enc1_extra_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc1_extra_residual_or_payload;
  logic n_enc1_extra_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc1_extra_residual_or_bin_tag;
  logic n_enc2_depthwise_valid;
  logic n_enc2_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_depthwise_payload;
  logic n_enc2_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_enc2_depthwise_bin_tag;
  logic n_enc2_pointwise_valid;
  logic n_enc2_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_pointwise_payload;
  logic n_enc2_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_enc2_pointwise_bin_tag;
  logic n_enc2_residual_or_valid;
  logic n_enc2_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_residual_or_payload;
  logic n_enc2_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc2_residual_or_bin_tag;
  logic n_enc2_extra_depthwise_valid;
  logic n_enc2_extra_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_extra_depthwise_payload;
  logic n_enc2_extra_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_enc2_extra_depthwise_bin_tag;
  logic n_enc2_extra_pointwise_valid;
  logic n_enc2_extra_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_extra_pointwise_payload;
  logic n_enc2_extra_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_enc2_extra_pointwise_bin_tag;
  logic n_enc2_extra_residual_or_valid;
  logic n_enc2_extra_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc2_extra_residual_or_payload;
  logic n_enc2_extra_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc2_extra_residual_or_bin_tag;
  logic n_enc3_depthwise_valid;
  logic n_enc3_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_depthwise_payload;
  logic n_enc3_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_enc3_depthwise_bin_tag;
  logic n_enc3_pointwise_valid;
  logic n_enc3_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_pointwise_payload;
  logic n_enc3_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_enc3_pointwise_bin_tag;
  logic n_enc3_residual_or_valid;
  logic n_enc3_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_residual_or_payload;
  logic n_enc3_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc3_residual_or_bin_tag;
  logic n_enc3_extra_depthwise_valid;
  logic n_enc3_extra_depthwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_extra_depthwise_payload;
  logic n_enc3_extra_depthwise_completion;
  logic [TAG_WIDTH-1:0] n_enc3_extra_depthwise_bin_tag;
  logic n_enc3_extra_pointwise_valid;
  logic n_enc3_extra_pointwise_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_extra_pointwise_payload;
  logic n_enc3_extra_pointwise_completion;
  logic [TAG_WIDTH-1:0] n_enc3_extra_pointwise_bin_tag;
  logic n_enc3_extra_residual_or_valid;
  logic n_enc3_extra_residual_or_ready;
  logic [PAYLOAD_WIDTH-1:0] n_enc3_extra_residual_or_payload;
  logic n_enc3_extra_residual_or_completion;
  logic [TAG_WIDTH-1:0] n_enc3_extra_residual_or_bin_tag;
  logic n_final_concat_valid;
  logic n_final_concat_ready;
  logic [PAYLOAD_WIDTH-1:0] n_final_concat_payload;
  logic n_final_concat_completion;
  logic [TAG_WIDTH-1:0] n_final_concat_bin_tag;
  logic n_final_fuse_standard_valid;
  logic n_final_fuse_standard_ready;
  logic [PAYLOAD_WIDTH-1:0] n_final_fuse_standard_payload;
  logic n_final_fuse_standard_completion;
  logic [TAG_WIDTH-1:0] n_final_fuse_standard_bin_tag;
  logic n_project2_valid;
  logic n_project2_ready;
  logic [PAYLOAD_WIDTH-1:0] n_project2_payload;
  logic n_project2_completion;
  logic [TAG_WIDTH-1:0] n_project2_bin_tag;
  logic n_project2_upsample2x_valid;
  logic n_project2_upsample2x_ready;
  logic [PAYLOAD_WIDTH-1:0] n_project2_upsample2x_payload;
  logic n_project2_upsample2x_completion;
  logic [TAG_WIDTH-1:0] n_project2_upsample2x_bin_tag;
  logic n_project3_valid;
  logic n_project3_ready;
  logic [PAYLOAD_WIDTH-1:0] n_project3_payload;
  logic n_project3_completion;
  logic [TAG_WIDTH-1:0] n_project3_bin_tag;
  logic n_project3_upsample2x_valid;
  logic n_project3_upsample2x_ready;
  logic [PAYLOAD_WIDTH-1:0] n_project3_upsample2x_payload;
  logic n_project3_upsample2x_completion;
  logic [TAG_WIDTH-1:0] n_project3_upsample2x_bin_tag;
  logic n_semantic_half_multiplicity_sum_valid;
  logic n_semantic_half_multiplicity_sum_ready;
  logic [PAYLOAD_WIDTH-1:0] n_semantic_half_multiplicity_sum_payload;
  logic n_semantic_half_multiplicity_sum_completion;
  logic [TAG_WIDTH-1:0] n_semantic_half_multiplicity_sum_bin_tag;
  logic n_semantic_native_upsample2x_valid;
  logic n_semantic_native_upsample2x_ready;
  logic [PAYLOAD_WIDTH-1:0] n_semantic_native_upsample2x_payload;
  logic n_semantic_native_upsample2x_completion;
  logic [TAG_WIDTH-1:0] n_semantic_native_upsample2x_bin_tag;
  logic n_stem_valid;
  logic n_stem_ready;
  logic [PAYLOAD_WIDTH-1:0] n_stem_payload;
  logic n_stem_completion;
  logic [TAG_WIDTH-1:0] n_stem_bin_tag;
  logic r_0_valid;
  logic r_0_ready;
  logic [PAYLOAD_WIDTH-1:0] r_0_payload;
  logic r_0_completion;
  logic [TAG_WIDTH-1:0] r_0_bin_tag;
  logic e_0_valid;
  logic e_0_ready;
  logic [PAYLOAD_WIDTH-1:0] e_0_payload;
  logic e_0_completion;
  logic [TAG_WIDTH-1:0] e_0_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_0_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_0_high_watermark;
  logic r_1_valid;
  logic r_1_ready;
  logic [PAYLOAD_WIDTH-1:0] r_1_payload;
  logic r_1_completion;
  logic [TAG_WIDTH-1:0] r_1_bin_tag;
  logic e_1_valid;
  logic e_1_ready;
  logic [PAYLOAD_WIDTH-1:0] e_1_payload;
  logic e_1_completion;
  logic [TAG_WIDTH-1:0] e_1_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_1_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_1_high_watermark;
  logic r_2_valid;
  logic r_2_ready;
  logic [PAYLOAD_WIDTH-1:0] r_2_payload;
  logic r_2_completion;
  logic [TAG_WIDTH-1:0] r_2_bin_tag;
  logic e_2_valid;
  logic e_2_ready;
  logic [PAYLOAD_WIDTH-1:0] e_2_payload;
  logic e_2_completion;
  logic [TAG_WIDTH-1:0] e_2_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_2_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_2_high_watermark;
  logic r_3_valid;
  logic r_3_ready;
  logic [PAYLOAD_WIDTH-1:0] r_3_payload;
  logic r_3_completion;
  logic [TAG_WIDTH-1:0] r_3_bin_tag;
  logic e_3_valid;
  logic e_3_ready;
  logic [PAYLOAD_WIDTH-1:0] e_3_payload;
  logic e_3_completion;
  logic [TAG_WIDTH-1:0] e_3_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_3_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_3_high_watermark;
  logic r_4_valid;
  logic r_4_ready;
  logic [PAYLOAD_WIDTH-1:0] r_4_payload;
  logic r_4_completion;
  logic [TAG_WIDTH-1:0] r_4_bin_tag;
  logic e_4_valid;
  logic e_4_ready;
  logic [PAYLOAD_WIDTH-1:0] e_4_payload;
  logic e_4_completion;
  logic [TAG_WIDTH-1:0] e_4_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_4_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_4_high_watermark;
  logic r_5_valid;
  logic r_5_ready;
  logic [PAYLOAD_WIDTH-1:0] r_5_payload;
  logic r_5_completion;
  logic [TAG_WIDTH-1:0] r_5_bin_tag;
  logic e_5_valid;
  logic e_5_ready;
  logic [PAYLOAD_WIDTH-1:0] e_5_payload;
  logic e_5_completion;
  logic [TAG_WIDTH-1:0] e_5_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_5_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_5_high_watermark;
  logic r_6_valid;
  logic r_6_ready;
  logic [PAYLOAD_WIDTH-1:0] r_6_payload;
  logic r_6_completion;
  logic [TAG_WIDTH-1:0] r_6_bin_tag;
  logic e_6_valid;
  logic e_6_ready;
  logic [PAYLOAD_WIDTH-1:0] e_6_payload;
  logic e_6_completion;
  logic [TAG_WIDTH-1:0] e_6_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_6_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_6_high_watermark;
  logic r_7_valid;
  logic r_7_ready;
  logic [PAYLOAD_WIDTH-1:0] r_7_payload;
  logic r_7_completion;
  logic [TAG_WIDTH-1:0] r_7_bin_tag;
  logic e_7_valid;
  logic e_7_ready;
  logic [PAYLOAD_WIDTH-1:0] e_7_payload;
  logic e_7_completion;
  logic [TAG_WIDTH-1:0] e_7_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_7_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_7_high_watermark;
  logic r_8_valid;
  logic r_8_ready;
  logic [PAYLOAD_WIDTH-1:0] r_8_payload;
  logic r_8_completion;
  logic [TAG_WIDTH-1:0] r_8_bin_tag;
  logic e_8_valid;
  logic e_8_ready;
  logic [PAYLOAD_WIDTH-1:0] e_8_payload;
  logic e_8_completion;
  logic [TAG_WIDTH-1:0] e_8_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_8_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_8_high_watermark;
  logic r_9_valid;
  logic r_9_ready;
  logic [PAYLOAD_WIDTH-1:0] r_9_payload;
  logic r_9_completion;
  logic [TAG_WIDTH-1:0] r_9_bin_tag;
  logic e_9_valid;
  logic e_9_ready;
  logic [PAYLOAD_WIDTH-1:0] e_9_payload;
  logic e_9_completion;
  logic [TAG_WIDTH-1:0] e_9_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_9_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_9_high_watermark;
  logic r_10_valid;
  logic r_10_ready;
  logic [PAYLOAD_WIDTH-1:0] r_10_payload;
  logic r_10_completion;
  logic [TAG_WIDTH-1:0] r_10_bin_tag;
  logic e_10_valid;
  logic e_10_ready;
  logic [PAYLOAD_WIDTH-1:0] e_10_payload;
  logic e_10_completion;
  logic [TAG_WIDTH-1:0] e_10_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_10_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_10_high_watermark;
  logic r_11_valid;
  logic r_11_ready;
  logic [PAYLOAD_WIDTH-1:0] r_11_payload;
  logic r_11_completion;
  logic [TAG_WIDTH-1:0] r_11_bin_tag;
  logic e_11_valid;
  logic e_11_ready;
  logic [PAYLOAD_WIDTH-1:0] e_11_payload;
  logic e_11_completion;
  logic [TAG_WIDTH-1:0] e_11_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_11_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_11_high_watermark;
  logic r_12_valid;
  logic r_12_ready;
  logic [PAYLOAD_WIDTH-1:0] r_12_payload;
  logic r_12_completion;
  logic [TAG_WIDTH-1:0] r_12_bin_tag;
  logic e_12_valid;
  logic e_12_ready;
  logic [PAYLOAD_WIDTH-1:0] e_12_payload;
  logic e_12_completion;
  logic [TAG_WIDTH-1:0] e_12_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_12_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_12_high_watermark;
  logic r_13_valid;
  logic r_13_ready;
  logic [PAYLOAD_WIDTH-1:0] r_13_payload;
  logic r_13_completion;
  logic [TAG_WIDTH-1:0] r_13_bin_tag;
  logic e_13_valid;
  logic e_13_ready;
  logic [PAYLOAD_WIDTH-1:0] e_13_payload;
  logic e_13_completion;
  logic [TAG_WIDTH-1:0] e_13_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_13_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_13_high_watermark;
  logic r_14_valid;
  logic r_14_ready;
  logic [PAYLOAD_WIDTH-1:0] r_14_payload;
  logic r_14_completion;
  logic [TAG_WIDTH-1:0] r_14_bin_tag;
  logic e_14_valid;
  logic e_14_ready;
  logic [PAYLOAD_WIDTH-1:0] e_14_payload;
  logic e_14_completion;
  logic [TAG_WIDTH-1:0] e_14_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_14_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_14_high_watermark;
  logic r_15_valid;
  logic r_15_ready;
  logic [PAYLOAD_WIDTH-1:0] r_15_payload;
  logic r_15_completion;
  logic [TAG_WIDTH-1:0] r_15_bin_tag;
  logic e_15_valid;
  logic e_15_ready;
  logic [PAYLOAD_WIDTH-1:0] e_15_payload;
  logic e_15_completion;
  logic [TAG_WIDTH-1:0] e_15_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_15_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_15_high_watermark;
  logic r_16_valid;
  logic r_16_ready;
  logic [PAYLOAD_WIDTH-1:0] r_16_payload;
  logic r_16_completion;
  logic [TAG_WIDTH-1:0] r_16_bin_tag;
  logic e_16_valid;
  logic e_16_ready;
  logic [PAYLOAD_WIDTH-1:0] e_16_payload;
  logic e_16_completion;
  logic [TAG_WIDTH-1:0] e_16_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_16_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_16_high_watermark;
  logic r_17_valid;
  logic r_17_ready;
  logic [PAYLOAD_WIDTH-1:0] r_17_payload;
  logic r_17_completion;
  logic [TAG_WIDTH-1:0] r_17_bin_tag;
  logic e_17_valid;
  logic e_17_ready;
  logic [PAYLOAD_WIDTH-1:0] e_17_payload;
  logic e_17_completion;
  logic [TAG_WIDTH-1:0] e_17_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_17_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_17_high_watermark;
  logic r_18_valid;
  logic r_18_ready;
  logic [PAYLOAD_WIDTH-1:0] r_18_payload;
  logic r_18_completion;
  logic [TAG_WIDTH-1:0] r_18_bin_tag;
  logic e_18_valid;
  logic e_18_ready;
  logic [PAYLOAD_WIDTH-1:0] e_18_payload;
  logic e_18_completion;
  logic [TAG_WIDTH-1:0] e_18_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_18_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_18_high_watermark;
  logic r_19_valid;
  logic r_19_ready;
  logic [PAYLOAD_WIDTH-1:0] r_19_payload;
  logic r_19_completion;
  logic [TAG_WIDTH-1:0] r_19_bin_tag;
  logic e_19_valid;
  logic e_19_ready;
  logic [PAYLOAD_WIDTH-1:0] e_19_payload;
  logic e_19_completion;
  logic [TAG_WIDTH-1:0] e_19_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_19_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_19_high_watermark;
  logic r_20_valid;
  logic r_20_ready;
  logic [PAYLOAD_WIDTH-1:0] r_20_payload;
  logic r_20_completion;
  logic [TAG_WIDTH-1:0] r_20_bin_tag;
  logic e_20_valid;
  logic e_20_ready;
  logic [PAYLOAD_WIDTH-1:0] e_20_payload;
  logic e_20_completion;
  logic [TAG_WIDTH-1:0] e_20_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_20_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_20_high_watermark;
  logic r_21_valid;
  logic r_21_ready;
  logic [PAYLOAD_WIDTH-1:0] r_21_payload;
  logic r_21_completion;
  logic [TAG_WIDTH-1:0] r_21_bin_tag;
  logic e_21_valid;
  logic e_21_ready;
  logic [PAYLOAD_WIDTH-1:0] e_21_payload;
  logic e_21_completion;
  logic [TAG_WIDTH-1:0] e_21_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_21_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_21_high_watermark;
  logic r_22_valid;
  logic r_22_ready;
  logic [PAYLOAD_WIDTH-1:0] r_22_payload;
  logic r_22_completion;
  logic [TAG_WIDTH-1:0] r_22_bin_tag;
  logic e_22_valid;
  logic e_22_ready;
  logic [PAYLOAD_WIDTH-1:0] e_22_payload;
  logic e_22_completion;
  logic [TAG_WIDTH-1:0] e_22_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_22_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_22_high_watermark;
  logic r_23_valid;
  logic r_23_ready;
  logic [PAYLOAD_WIDTH-1:0] r_23_payload;
  logic r_23_completion;
  logic [TAG_WIDTH-1:0] r_23_bin_tag;
  logic e_23_valid;
  logic e_23_ready;
  logic [PAYLOAD_WIDTH-1:0] e_23_payload;
  logic e_23_completion;
  logic [TAG_WIDTH-1:0] e_23_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_23_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_23_high_watermark;
  logic r_24_valid;
  logic r_24_ready;
  logic [PAYLOAD_WIDTH-1:0] r_24_payload;
  logic r_24_completion;
  logic [TAG_WIDTH-1:0] r_24_bin_tag;
  logic e_24_valid;
  logic e_24_ready;
  logic [PAYLOAD_WIDTH-1:0] e_24_payload;
  logic e_24_completion;
  logic [TAG_WIDTH-1:0] e_24_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_24_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_24_high_watermark;
  logic r_25_valid;
  logic r_25_ready;
  logic [PAYLOAD_WIDTH-1:0] r_25_payload;
  logic r_25_completion;
  logic [TAG_WIDTH-1:0] r_25_bin_tag;
  logic e_25_valid;
  logic e_25_ready;
  logic [PAYLOAD_WIDTH-1:0] e_25_payload;
  logic e_25_completion;
  logic [TAG_WIDTH-1:0] e_25_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_25_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_25_high_watermark;
  logic r_26_valid;
  logic r_26_ready;
  logic [PAYLOAD_WIDTH-1:0] r_26_payload;
  logic r_26_completion;
  logic [TAG_WIDTH-1:0] r_26_bin_tag;
  logic e_26_valid;
  logic e_26_ready;
  logic [PAYLOAD_WIDTH-1:0] e_26_payload;
  logic e_26_completion;
  logic [TAG_WIDTH-1:0] e_26_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_26_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_26_high_watermark;
  logic r_27_valid;
  logic r_27_ready;
  logic [PAYLOAD_WIDTH-1:0] r_27_payload;
  logic r_27_completion;
  logic [TAG_WIDTH-1:0] r_27_bin_tag;
  logic e_27_valid;
  logic e_27_ready;
  logic [PAYLOAD_WIDTH-1:0] e_27_payload;
  logic e_27_completion;
  logic [TAG_WIDTH-1:0] e_27_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_27_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_27_high_watermark;
  logic r_28_valid;
  logic r_28_ready;
  logic [PAYLOAD_WIDTH-1:0] r_28_payload;
  logic r_28_completion;
  logic [TAG_WIDTH-1:0] r_28_bin_tag;
  logic e_28_valid;
  logic e_28_ready;
  logic [PAYLOAD_WIDTH-1:0] e_28_payload;
  logic e_28_completion;
  logic [TAG_WIDTH-1:0] e_28_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_28_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_28_high_watermark;
  logic r_29_valid;
  logic r_29_ready;
  logic [PAYLOAD_WIDTH-1:0] r_29_payload;
  logic r_29_completion;
  logic [TAG_WIDTH-1:0] r_29_bin_tag;
  logic e_29_valid;
  logic e_29_ready;
  logic [PAYLOAD_WIDTH-1:0] e_29_payload;
  logic e_29_completion;
  logic [TAG_WIDTH-1:0] e_29_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_29_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_29_high_watermark;
  logic r_30_valid;
  logic r_30_ready;
  logic [PAYLOAD_WIDTH-1:0] r_30_payload;
  logic r_30_completion;
  logic [TAG_WIDTH-1:0] r_30_bin_tag;
  logic e_30_valid;
  logic e_30_ready;
  logic [PAYLOAD_WIDTH-1:0] e_30_payload;
  logic e_30_completion;
  logic [TAG_WIDTH-1:0] e_30_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_30_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_30_high_watermark;
  logic r_31_valid;
  logic r_31_ready;
  logic [PAYLOAD_WIDTH-1:0] r_31_payload;
  logic r_31_completion;
  logic [TAG_WIDTH-1:0] r_31_bin_tag;
  logic e_31_valid;
  logic e_31_ready;
  logic [PAYLOAD_WIDTH-1:0] e_31_payload;
  logic e_31_completion;
  logic [TAG_WIDTH-1:0] e_31_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_31_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_31_high_watermark;
  logic r_32_valid;
  logic r_32_ready;
  logic [PAYLOAD_WIDTH-1:0] r_32_payload;
  logic r_32_completion;
  logic [TAG_WIDTH-1:0] r_32_bin_tag;
  logic e_32_valid;
  logic e_32_ready;
  logic [PAYLOAD_WIDTH-1:0] e_32_payload;
  logic e_32_completion;
  logic [TAG_WIDTH-1:0] e_32_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_32_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_32_high_watermark;
  logic r_33_valid;
  logic r_33_ready;
  logic [PAYLOAD_WIDTH-1:0] r_33_payload;
  logic r_33_completion;
  logic [TAG_WIDTH-1:0] r_33_bin_tag;
  logic e_33_valid;
  logic e_33_ready;
  logic [PAYLOAD_WIDTH-1:0] e_33_payload;
  logic e_33_completion;
  logic [TAG_WIDTH-1:0] e_33_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_33_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_33_high_watermark;
  logic r_34_valid;
  logic r_34_ready;
  logic [PAYLOAD_WIDTH-1:0] r_34_payload;
  logic r_34_completion;
  logic [TAG_WIDTH-1:0] r_34_bin_tag;
  logic e_34_valid;
  logic e_34_ready;
  logic [PAYLOAD_WIDTH-1:0] e_34_payload;
  logic e_34_completion;
  logic [TAG_WIDTH-1:0] e_34_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_34_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_34_high_watermark;
  logic r_35_valid;
  logic r_35_ready;
  logic [PAYLOAD_WIDTH-1:0] r_35_payload;
  logic r_35_completion;
  logic [TAG_WIDTH-1:0] r_35_bin_tag;
  logic e_35_valid;
  logic e_35_ready;
  logic [PAYLOAD_WIDTH-1:0] e_35_payload;
  logic e_35_completion;
  logic [TAG_WIDTH-1:0] e_35_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_35_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_35_high_watermark;
  logic r_36_valid;
  logic r_36_ready;
  logic [PAYLOAD_WIDTH-1:0] r_36_payload;
  logic r_36_completion;
  logic [TAG_WIDTH-1:0] r_36_bin_tag;
  logic e_36_valid;
  logic e_36_ready;
  logic [PAYLOAD_WIDTH-1:0] e_36_payload;
  logic e_36_completion;
  logic [TAG_WIDTH-1:0] e_36_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_36_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_36_high_watermark;
  logic r_37_valid;
  logic r_37_ready;
  logic [PAYLOAD_WIDTH-1:0] r_37_payload;
  logic r_37_completion;
  logic [TAG_WIDTH-1:0] r_37_bin_tag;
  logic e_37_valid;
  logic e_37_ready;
  logic [PAYLOAD_WIDTH-1:0] e_37_payload;
  logic e_37_completion;
  logic [TAG_WIDTH-1:0] e_37_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_37_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_37_high_watermark;
  logic r_38_valid;
  logic r_38_ready;
  logic [PAYLOAD_WIDTH-1:0] r_38_payload;
  logic r_38_completion;
  logic [TAG_WIDTH-1:0] r_38_bin_tag;
  logic e_38_valid;
  logic e_38_ready;
  logic [PAYLOAD_WIDTH-1:0] e_38_payload;
  logic e_38_completion;
  logic [TAG_WIDTH-1:0] e_38_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_38_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_38_high_watermark;
  logic r_39_valid;
  logic r_39_ready;
  logic [PAYLOAD_WIDTH-1:0] r_39_payload;
  logic r_39_completion;
  logic [TAG_WIDTH-1:0] r_39_bin_tag;
  logic e_39_valid;
  logic e_39_ready;
  logic [PAYLOAD_WIDTH-1:0] e_39_payload;
  logic e_39_completion;
  logic [TAG_WIDTH-1:0] e_39_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_39_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_39_high_watermark;
  logic r_40_valid;
  logic r_40_ready;
  logic [PAYLOAD_WIDTH-1:0] r_40_payload;
  logic r_40_completion;
  logic [TAG_WIDTH-1:0] r_40_bin_tag;
  logic e_40_valid;
  logic e_40_ready;
  logic [PAYLOAD_WIDTH-1:0] e_40_payload;
  logic e_40_completion;
  logic [TAG_WIDTH-1:0] e_40_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_40_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_40_high_watermark;
  logic r_41_valid;
  logic r_41_ready;
  logic [PAYLOAD_WIDTH-1:0] r_41_payload;
  logic r_41_completion;
  logic [TAG_WIDTH-1:0] r_41_bin_tag;
  logic e_41_valid;
  logic e_41_ready;
  logic [PAYLOAD_WIDTH-1:0] e_41_payload;
  logic e_41_completion;
  logic [TAG_WIDTH-1:0] e_41_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_41_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_41_high_watermark;
  logic r_42_valid;
  logic r_42_ready;
  logic [PAYLOAD_WIDTH-1:0] r_42_payload;
  logic r_42_completion;
  logic [TAG_WIDTH-1:0] r_42_bin_tag;
  logic e_42_valid;
  logic e_42_ready;
  logic [PAYLOAD_WIDTH-1:0] e_42_payload;
  logic e_42_completion;
  logic [TAG_WIDTH-1:0] e_42_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_42_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_42_high_watermark;
  logic r_43_valid;
  logic r_43_ready;
  logic [PAYLOAD_WIDTH-1:0] r_43_payload;
  logic r_43_completion;
  logic [TAG_WIDTH-1:0] r_43_bin_tag;
  logic e_43_valid;
  logic e_43_ready;
  logic [PAYLOAD_WIDTH-1:0] e_43_payload;
  logic e_43_completion;
  logic [TAG_WIDTH-1:0] e_43_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_43_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_43_high_watermark;
  logic r_44_valid;
  logic r_44_ready;
  logic [PAYLOAD_WIDTH-1:0] r_44_payload;
  logic r_44_completion;
  logic [TAG_WIDTH-1:0] r_44_bin_tag;
  logic e_44_valid;
  logic e_44_ready;
  logic [PAYLOAD_WIDTH-1:0] e_44_payload;
  logic e_44_completion;
  logic [TAG_WIDTH-1:0] e_44_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_44_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_44_high_watermark;
  logic r_45_valid;
  logic r_45_ready;
  logic [PAYLOAD_WIDTH-1:0] r_45_payload;
  logic r_45_completion;
  logic [TAG_WIDTH-1:0] r_45_bin_tag;
  logic e_45_valid;
  logic e_45_ready;
  logic [PAYLOAD_WIDTH-1:0] e_45_payload;
  logic e_45_completion;
  logic [TAG_WIDTH-1:0] e_45_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_45_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_45_high_watermark;
  logic r_46_valid;
  logic r_46_ready;
  logic [PAYLOAD_WIDTH-1:0] r_46_payload;
  logic r_46_completion;
  logic [TAG_WIDTH-1:0] r_46_bin_tag;
  logic e_46_valid;
  logic e_46_ready;
  logic [PAYLOAD_WIDTH-1:0] e_46_payload;
  logic e_46_completion;
  logic [TAG_WIDTH-1:0] e_46_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_46_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_46_high_watermark;
  logic r_47_valid;
  logic r_47_ready;
  logic [PAYLOAD_WIDTH-1:0] r_47_payload;
  logic r_47_completion;
  logic [TAG_WIDTH-1:0] r_47_bin_tag;
  logic e_47_valid;
  logic e_47_ready;
  logic [PAYLOAD_WIDTH-1:0] e_47_payload;
  logic e_47_completion;
  logic [TAG_WIDTH-1:0] e_47_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_47_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_47_high_watermark;
  logic r_48_valid;
  logic r_48_ready;
  logic [PAYLOAD_WIDTH-1:0] r_48_payload;
  logic r_48_completion;
  logic [TAG_WIDTH-1:0] r_48_bin_tag;
  logic e_48_valid;
  logic e_48_ready;
  logic [PAYLOAD_WIDTH-1:0] e_48_payload;
  logic e_48_completion;
  logic [TAG_WIDTH-1:0] e_48_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_48_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_48_high_watermark;
  logic r_49_valid;
  logic r_49_ready;
  logic [PAYLOAD_WIDTH-1:0] r_49_payload;
  logic r_49_completion;
  logic [TAG_WIDTH-1:0] r_49_bin_tag;
  logic e_49_valid;
  logic e_49_ready;
  logic [PAYLOAD_WIDTH-1:0] e_49_payload;
  logic e_49_completion;
  logic [TAG_WIDTH-1:0] e_49_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_49_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_49_high_watermark;
  logic r_50_valid;
  logic r_50_ready;
  logic [PAYLOAD_WIDTH-1:0] r_50_payload;
  logic r_50_completion;
  logic [TAG_WIDTH-1:0] r_50_bin_tag;
  logic e_50_valid;
  logic e_50_ready;
  logic [PAYLOAD_WIDTH-1:0] e_50_payload;
  logic e_50_completion;
  logic [TAG_WIDTH-1:0] e_50_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_50_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_50_high_watermark;
  logic r_51_valid;
  logic r_51_ready;
  logic [PAYLOAD_WIDTH-1:0] r_51_payload;
  logic r_51_completion;
  logic [TAG_WIDTH-1:0] r_51_bin_tag;
  logic e_51_valid;
  logic e_51_ready;
  logic [PAYLOAD_WIDTH-1:0] e_51_payload;
  logic e_51_completion;
  logic [TAG_WIDTH-1:0] e_51_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_51_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_51_high_watermark;
  logic r_52_valid;
  logic r_52_ready;
  logic [PAYLOAD_WIDTH-1:0] r_52_payload;
  logic r_52_completion;
  logic [TAG_WIDTH-1:0] r_52_bin_tag;
  logic e_52_valid;
  logic e_52_ready;
  logic [PAYLOAD_WIDTH-1:0] e_52_payload;
  logic e_52_completion;
  logic [TAG_WIDTH-1:0] e_52_bin_tag;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_52_occupancy;
  logic [EDGE_FIFO_COUNT_WIDTH-1:0] edge_52_high_watermark;
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_0 (
    .clk,
    .reset,
    .in_valid(r_0_valid),
    .in_ready(r_0_ready),
    .in_payload(r_0_payload),
    .in_completion(r_0_completion),
    .in_bin_tag(r_0_bin_tag),
    .out_valid(e_0_valid),
    .out_ready(e_0_ready),
    .out_payload(e_0_payload),
    .out_completion(e_0_completion),
    .out_bin_tag(e_0_bin_tag),
    .occupancy_o(edge_0_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_0_high_watermark <= '0;
    else if (edge_0_occupancy > edge_0_high_watermark)
      edge_0_high_watermark <= edge_0_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_1 (
    .clk,
    .reset,
    .in_valid(r_1_valid),
    .in_ready(r_1_ready),
    .in_payload(r_1_payload),
    .in_completion(r_1_completion),
    .in_bin_tag(r_1_bin_tag),
    .out_valid(e_1_valid),
    .out_ready(e_1_ready),
    .out_payload(e_1_payload),
    .out_completion(e_1_completion),
    .out_bin_tag(e_1_bin_tag),
    .occupancy_o(edge_1_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_1_high_watermark <= '0;
    else if (edge_1_occupancy > edge_1_high_watermark)
      edge_1_high_watermark <= edge_1_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_2 (
    .clk,
    .reset,
    .in_valid(r_2_valid),
    .in_ready(r_2_ready),
    .in_payload(r_2_payload),
    .in_completion(r_2_completion),
    .in_bin_tag(r_2_bin_tag),
    .out_valid(e_2_valid),
    .out_ready(e_2_ready),
    .out_payload(e_2_payload),
    .out_completion(e_2_completion),
    .out_bin_tag(e_2_bin_tag),
    .occupancy_o(edge_2_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_2_high_watermark <= '0;
    else if (edge_2_occupancy > edge_2_high_watermark)
      edge_2_high_watermark <= edge_2_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_3 (
    .clk,
    .reset,
    .in_valid(r_3_valid),
    .in_ready(r_3_ready),
    .in_payload(r_3_payload),
    .in_completion(r_3_completion),
    .in_bin_tag(r_3_bin_tag),
    .out_valid(e_3_valid),
    .out_ready(e_3_ready),
    .out_payload(e_3_payload),
    .out_completion(e_3_completion),
    .out_bin_tag(e_3_bin_tag),
    .occupancy_o(edge_3_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_3_high_watermark <= '0;
    else if (edge_3_occupancy > edge_3_high_watermark)
      edge_3_high_watermark <= edge_3_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_4 (
    .clk,
    .reset,
    .in_valid(r_4_valid),
    .in_ready(r_4_ready),
    .in_payload(r_4_payload),
    .in_completion(r_4_completion),
    .in_bin_tag(r_4_bin_tag),
    .out_valid(e_4_valid),
    .out_ready(e_4_ready),
    .out_payload(e_4_payload),
    .out_completion(e_4_completion),
    .out_bin_tag(e_4_bin_tag),
    .occupancy_o(edge_4_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_4_high_watermark <= '0;
    else if (edge_4_occupancy > edge_4_high_watermark)
      edge_4_high_watermark <= edge_4_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_5 (
    .clk,
    .reset,
    .in_valid(r_5_valid),
    .in_ready(r_5_ready),
    .in_payload(r_5_payload),
    .in_completion(r_5_completion),
    .in_bin_tag(r_5_bin_tag),
    .out_valid(e_5_valid),
    .out_ready(e_5_ready),
    .out_payload(e_5_payload),
    .out_completion(e_5_completion),
    .out_bin_tag(e_5_bin_tag),
    .occupancy_o(edge_5_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_5_high_watermark <= '0;
    else if (edge_5_occupancy > edge_5_high_watermark)
      edge_5_high_watermark <= edge_5_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_6 (
    .clk,
    .reset,
    .in_valid(r_6_valid),
    .in_ready(r_6_ready),
    .in_payload(r_6_payload),
    .in_completion(r_6_completion),
    .in_bin_tag(r_6_bin_tag),
    .out_valid(e_6_valid),
    .out_ready(e_6_ready),
    .out_payload(e_6_payload),
    .out_completion(e_6_completion),
    .out_bin_tag(e_6_bin_tag),
    .occupancy_o(edge_6_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_6_high_watermark <= '0;
    else if (edge_6_occupancy > edge_6_high_watermark)
      edge_6_high_watermark <= edge_6_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_7 (
    .clk,
    .reset,
    .in_valid(r_7_valid),
    .in_ready(r_7_ready),
    .in_payload(r_7_payload),
    .in_completion(r_7_completion),
    .in_bin_tag(r_7_bin_tag),
    .out_valid(e_7_valid),
    .out_ready(e_7_ready),
    .out_payload(e_7_payload),
    .out_completion(e_7_completion),
    .out_bin_tag(e_7_bin_tag),
    .occupancy_o(edge_7_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_7_high_watermark <= '0;
    else if (edge_7_occupancy > edge_7_high_watermark)
      edge_7_high_watermark <= edge_7_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_8 (
    .clk,
    .reset,
    .in_valid(r_8_valid),
    .in_ready(r_8_ready),
    .in_payload(r_8_payload),
    .in_completion(r_8_completion),
    .in_bin_tag(r_8_bin_tag),
    .out_valid(e_8_valid),
    .out_ready(e_8_ready),
    .out_payload(e_8_payload),
    .out_completion(e_8_completion),
    .out_bin_tag(e_8_bin_tag),
    .occupancy_o(edge_8_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_8_high_watermark <= '0;
    else if (edge_8_occupancy > edge_8_high_watermark)
      edge_8_high_watermark <= edge_8_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_9 (
    .clk,
    .reset,
    .in_valid(r_9_valid),
    .in_ready(r_9_ready),
    .in_payload(r_9_payload),
    .in_completion(r_9_completion),
    .in_bin_tag(r_9_bin_tag),
    .out_valid(e_9_valid),
    .out_ready(e_9_ready),
    .out_payload(e_9_payload),
    .out_completion(e_9_completion),
    .out_bin_tag(e_9_bin_tag),
    .occupancy_o(edge_9_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_9_high_watermark <= '0;
    else if (edge_9_occupancy > edge_9_high_watermark)
      edge_9_high_watermark <= edge_9_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_10 (
    .clk,
    .reset,
    .in_valid(r_10_valid),
    .in_ready(r_10_ready),
    .in_payload(r_10_payload),
    .in_completion(r_10_completion),
    .in_bin_tag(r_10_bin_tag),
    .out_valid(e_10_valid),
    .out_ready(e_10_ready),
    .out_payload(e_10_payload),
    .out_completion(e_10_completion),
    .out_bin_tag(e_10_bin_tag),
    .occupancy_o(edge_10_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_10_high_watermark <= '0;
    else if (edge_10_occupancy > edge_10_high_watermark)
      edge_10_high_watermark <= edge_10_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_11 (
    .clk,
    .reset,
    .in_valid(r_11_valid),
    .in_ready(r_11_ready),
    .in_payload(r_11_payload),
    .in_completion(r_11_completion),
    .in_bin_tag(r_11_bin_tag),
    .out_valid(e_11_valid),
    .out_ready(e_11_ready),
    .out_payload(e_11_payload),
    .out_completion(e_11_completion),
    .out_bin_tag(e_11_bin_tag),
    .occupancy_o(edge_11_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_11_high_watermark <= '0;
    else if (edge_11_occupancy > edge_11_high_watermark)
      edge_11_high_watermark <= edge_11_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_12 (
    .clk,
    .reset,
    .in_valid(r_12_valid),
    .in_ready(r_12_ready),
    .in_payload(r_12_payload),
    .in_completion(r_12_completion),
    .in_bin_tag(r_12_bin_tag),
    .out_valid(e_12_valid),
    .out_ready(e_12_ready),
    .out_payload(e_12_payload),
    .out_completion(e_12_completion),
    .out_bin_tag(e_12_bin_tag),
    .occupancy_o(edge_12_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_12_high_watermark <= '0;
    else if (edge_12_occupancy > edge_12_high_watermark)
      edge_12_high_watermark <= edge_12_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_13 (
    .clk,
    .reset,
    .in_valid(r_13_valid),
    .in_ready(r_13_ready),
    .in_payload(r_13_payload),
    .in_completion(r_13_completion),
    .in_bin_tag(r_13_bin_tag),
    .out_valid(e_13_valid),
    .out_ready(e_13_ready),
    .out_payload(e_13_payload),
    .out_completion(e_13_completion),
    .out_bin_tag(e_13_bin_tag),
    .occupancy_o(edge_13_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_13_high_watermark <= '0;
    else if (edge_13_occupancy > edge_13_high_watermark)
      edge_13_high_watermark <= edge_13_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_14 (
    .clk,
    .reset,
    .in_valid(r_14_valid),
    .in_ready(r_14_ready),
    .in_payload(r_14_payload),
    .in_completion(r_14_completion),
    .in_bin_tag(r_14_bin_tag),
    .out_valid(e_14_valid),
    .out_ready(e_14_ready),
    .out_payload(e_14_payload),
    .out_completion(e_14_completion),
    .out_bin_tag(e_14_bin_tag),
    .occupancy_o(edge_14_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_14_high_watermark <= '0;
    else if (edge_14_occupancy > edge_14_high_watermark)
      edge_14_high_watermark <= edge_14_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_15 (
    .clk,
    .reset,
    .in_valid(r_15_valid),
    .in_ready(r_15_ready),
    .in_payload(r_15_payload),
    .in_completion(r_15_completion),
    .in_bin_tag(r_15_bin_tag),
    .out_valid(e_15_valid),
    .out_ready(e_15_ready),
    .out_payload(e_15_payload),
    .out_completion(e_15_completion),
    .out_bin_tag(e_15_bin_tag),
    .occupancy_o(edge_15_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_15_high_watermark <= '0;
    else if (edge_15_occupancy > edge_15_high_watermark)
      edge_15_high_watermark <= edge_15_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_16 (
    .clk,
    .reset,
    .in_valid(r_16_valid),
    .in_ready(r_16_ready),
    .in_payload(r_16_payload),
    .in_completion(r_16_completion),
    .in_bin_tag(r_16_bin_tag),
    .out_valid(e_16_valid),
    .out_ready(e_16_ready),
    .out_payload(e_16_payload),
    .out_completion(e_16_completion),
    .out_bin_tag(e_16_bin_tag),
    .occupancy_o(edge_16_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_16_high_watermark <= '0;
    else if (edge_16_occupancy > edge_16_high_watermark)
      edge_16_high_watermark <= edge_16_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_17 (
    .clk,
    .reset,
    .in_valid(r_17_valid),
    .in_ready(r_17_ready),
    .in_payload(r_17_payload),
    .in_completion(r_17_completion),
    .in_bin_tag(r_17_bin_tag),
    .out_valid(e_17_valid),
    .out_ready(e_17_ready),
    .out_payload(e_17_payload),
    .out_completion(e_17_completion),
    .out_bin_tag(e_17_bin_tag),
    .occupancy_o(edge_17_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_17_high_watermark <= '0;
    else if (edge_17_occupancy > edge_17_high_watermark)
      edge_17_high_watermark <= edge_17_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_18 (
    .clk,
    .reset,
    .in_valid(r_18_valid),
    .in_ready(r_18_ready),
    .in_payload(r_18_payload),
    .in_completion(r_18_completion),
    .in_bin_tag(r_18_bin_tag),
    .out_valid(e_18_valid),
    .out_ready(e_18_ready),
    .out_payload(e_18_payload),
    .out_completion(e_18_completion),
    .out_bin_tag(e_18_bin_tag),
    .occupancy_o(edge_18_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_18_high_watermark <= '0;
    else if (edge_18_occupancy > edge_18_high_watermark)
      edge_18_high_watermark <= edge_18_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_19 (
    .clk,
    .reset,
    .in_valid(r_19_valid),
    .in_ready(r_19_ready),
    .in_payload(r_19_payload),
    .in_completion(r_19_completion),
    .in_bin_tag(r_19_bin_tag),
    .out_valid(e_19_valid),
    .out_ready(e_19_ready),
    .out_payload(e_19_payload),
    .out_completion(e_19_completion),
    .out_bin_tag(e_19_bin_tag),
    .occupancy_o(edge_19_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_19_high_watermark <= '0;
    else if (edge_19_occupancy > edge_19_high_watermark)
      edge_19_high_watermark <= edge_19_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_20 (
    .clk,
    .reset,
    .in_valid(r_20_valid),
    .in_ready(r_20_ready),
    .in_payload(r_20_payload),
    .in_completion(r_20_completion),
    .in_bin_tag(r_20_bin_tag),
    .out_valid(e_20_valid),
    .out_ready(e_20_ready),
    .out_payload(e_20_payload),
    .out_completion(e_20_completion),
    .out_bin_tag(e_20_bin_tag),
    .occupancy_o(edge_20_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_20_high_watermark <= '0;
    else if (edge_20_occupancy > edge_20_high_watermark)
      edge_20_high_watermark <= edge_20_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_21 (
    .clk,
    .reset,
    .in_valid(r_21_valid),
    .in_ready(r_21_ready),
    .in_payload(r_21_payload),
    .in_completion(r_21_completion),
    .in_bin_tag(r_21_bin_tag),
    .out_valid(e_21_valid),
    .out_ready(e_21_ready),
    .out_payload(e_21_payload),
    .out_completion(e_21_completion),
    .out_bin_tag(e_21_bin_tag),
    .occupancy_o(edge_21_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_21_high_watermark <= '0;
    else if (edge_21_occupancy > edge_21_high_watermark)
      edge_21_high_watermark <= edge_21_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_22 (
    .clk,
    .reset,
    .in_valid(r_22_valid),
    .in_ready(r_22_ready),
    .in_payload(r_22_payload),
    .in_completion(r_22_completion),
    .in_bin_tag(r_22_bin_tag),
    .out_valid(e_22_valid),
    .out_ready(e_22_ready),
    .out_payload(e_22_payload),
    .out_completion(e_22_completion),
    .out_bin_tag(e_22_bin_tag),
    .occupancy_o(edge_22_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_22_high_watermark <= '0;
    else if (edge_22_occupancy > edge_22_high_watermark)
      edge_22_high_watermark <= edge_22_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_23 (
    .clk,
    .reset,
    .in_valid(r_23_valid),
    .in_ready(r_23_ready),
    .in_payload(r_23_payload),
    .in_completion(r_23_completion),
    .in_bin_tag(r_23_bin_tag),
    .out_valid(e_23_valid),
    .out_ready(e_23_ready),
    .out_payload(e_23_payload),
    .out_completion(e_23_completion),
    .out_bin_tag(e_23_bin_tag),
    .occupancy_o(edge_23_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_23_high_watermark <= '0;
    else if (edge_23_occupancy > edge_23_high_watermark)
      edge_23_high_watermark <= edge_23_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_24 (
    .clk,
    .reset,
    .in_valid(r_24_valid),
    .in_ready(r_24_ready),
    .in_payload(r_24_payload),
    .in_completion(r_24_completion),
    .in_bin_tag(r_24_bin_tag),
    .out_valid(e_24_valid),
    .out_ready(e_24_ready),
    .out_payload(e_24_payload),
    .out_completion(e_24_completion),
    .out_bin_tag(e_24_bin_tag),
    .occupancy_o(edge_24_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_24_high_watermark <= '0;
    else if (edge_24_occupancy > edge_24_high_watermark)
      edge_24_high_watermark <= edge_24_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_25 (
    .clk,
    .reset,
    .in_valid(r_25_valid),
    .in_ready(r_25_ready),
    .in_payload(r_25_payload),
    .in_completion(r_25_completion),
    .in_bin_tag(r_25_bin_tag),
    .out_valid(e_25_valid),
    .out_ready(e_25_ready),
    .out_payload(e_25_payload),
    .out_completion(e_25_completion),
    .out_bin_tag(e_25_bin_tag),
    .occupancy_o(edge_25_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_25_high_watermark <= '0;
    else if (edge_25_occupancy > edge_25_high_watermark)
      edge_25_high_watermark <= edge_25_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_26 (
    .clk,
    .reset,
    .in_valid(r_26_valid),
    .in_ready(r_26_ready),
    .in_payload(r_26_payload),
    .in_completion(r_26_completion),
    .in_bin_tag(r_26_bin_tag),
    .out_valid(e_26_valid),
    .out_ready(e_26_ready),
    .out_payload(e_26_payload),
    .out_completion(e_26_completion),
    .out_bin_tag(e_26_bin_tag),
    .occupancy_o(edge_26_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_26_high_watermark <= '0;
    else if (edge_26_occupancy > edge_26_high_watermark)
      edge_26_high_watermark <= edge_26_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_27 (
    .clk,
    .reset,
    .in_valid(r_27_valid),
    .in_ready(r_27_ready),
    .in_payload(r_27_payload),
    .in_completion(r_27_completion),
    .in_bin_tag(r_27_bin_tag),
    .out_valid(e_27_valid),
    .out_ready(e_27_ready),
    .out_payload(e_27_payload),
    .out_completion(e_27_completion),
    .out_bin_tag(e_27_bin_tag),
    .occupancy_o(edge_27_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_27_high_watermark <= '0;
    else if (edge_27_occupancy > edge_27_high_watermark)
      edge_27_high_watermark <= edge_27_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_28 (
    .clk,
    .reset,
    .in_valid(r_28_valid),
    .in_ready(r_28_ready),
    .in_payload(r_28_payload),
    .in_completion(r_28_completion),
    .in_bin_tag(r_28_bin_tag),
    .out_valid(e_28_valid),
    .out_ready(e_28_ready),
    .out_payload(e_28_payload),
    .out_completion(e_28_completion),
    .out_bin_tag(e_28_bin_tag),
    .occupancy_o(edge_28_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_28_high_watermark <= '0;
    else if (edge_28_occupancy > edge_28_high_watermark)
      edge_28_high_watermark <= edge_28_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_29 (
    .clk,
    .reset,
    .in_valid(r_29_valid),
    .in_ready(r_29_ready),
    .in_payload(r_29_payload),
    .in_completion(r_29_completion),
    .in_bin_tag(r_29_bin_tag),
    .out_valid(e_29_valid),
    .out_ready(e_29_ready),
    .out_payload(e_29_payload),
    .out_completion(e_29_completion),
    .out_bin_tag(e_29_bin_tag),
    .occupancy_o(edge_29_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_29_high_watermark <= '0;
    else if (edge_29_occupancy > edge_29_high_watermark)
      edge_29_high_watermark <= edge_29_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_30 (
    .clk,
    .reset,
    .in_valid(r_30_valid),
    .in_ready(r_30_ready),
    .in_payload(r_30_payload),
    .in_completion(r_30_completion),
    .in_bin_tag(r_30_bin_tag),
    .out_valid(e_30_valid),
    .out_ready(e_30_ready),
    .out_payload(e_30_payload),
    .out_completion(e_30_completion),
    .out_bin_tag(e_30_bin_tag),
    .occupancy_o(edge_30_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_30_high_watermark <= '0;
    else if (edge_30_occupancy > edge_30_high_watermark)
      edge_30_high_watermark <= edge_30_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_31 (
    .clk,
    .reset,
    .in_valid(r_31_valid),
    .in_ready(r_31_ready),
    .in_payload(r_31_payload),
    .in_completion(r_31_completion),
    .in_bin_tag(r_31_bin_tag),
    .out_valid(e_31_valid),
    .out_ready(e_31_ready),
    .out_payload(e_31_payload),
    .out_completion(e_31_completion),
    .out_bin_tag(e_31_bin_tag),
    .occupancy_o(edge_31_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_31_high_watermark <= '0;
    else if (edge_31_occupancy > edge_31_high_watermark)
      edge_31_high_watermark <= edge_31_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_32 (
    .clk,
    .reset,
    .in_valid(r_32_valid),
    .in_ready(r_32_ready),
    .in_payload(r_32_payload),
    .in_completion(r_32_completion),
    .in_bin_tag(r_32_bin_tag),
    .out_valid(e_32_valid),
    .out_ready(e_32_ready),
    .out_payload(e_32_payload),
    .out_completion(e_32_completion),
    .out_bin_tag(e_32_bin_tag),
    .occupancy_o(edge_32_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_32_high_watermark <= '0;
    else if (edge_32_occupancy > edge_32_high_watermark)
      edge_32_high_watermark <= edge_32_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_33 (
    .clk,
    .reset,
    .in_valid(r_33_valid),
    .in_ready(r_33_ready),
    .in_payload(r_33_payload),
    .in_completion(r_33_completion),
    .in_bin_tag(r_33_bin_tag),
    .out_valid(e_33_valid),
    .out_ready(e_33_ready),
    .out_payload(e_33_payload),
    .out_completion(e_33_completion),
    .out_bin_tag(e_33_bin_tag),
    .occupancy_o(edge_33_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_33_high_watermark <= '0;
    else if (edge_33_occupancy > edge_33_high_watermark)
      edge_33_high_watermark <= edge_33_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_34 (
    .clk,
    .reset,
    .in_valid(r_34_valid),
    .in_ready(r_34_ready),
    .in_payload(r_34_payload),
    .in_completion(r_34_completion),
    .in_bin_tag(r_34_bin_tag),
    .out_valid(e_34_valid),
    .out_ready(e_34_ready),
    .out_payload(e_34_payload),
    .out_completion(e_34_completion),
    .out_bin_tag(e_34_bin_tag),
    .occupancy_o(edge_34_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_34_high_watermark <= '0;
    else if (edge_34_occupancy > edge_34_high_watermark)
      edge_34_high_watermark <= edge_34_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_35 (
    .clk,
    .reset,
    .in_valid(r_35_valid),
    .in_ready(r_35_ready),
    .in_payload(r_35_payload),
    .in_completion(r_35_completion),
    .in_bin_tag(r_35_bin_tag),
    .out_valid(e_35_valid),
    .out_ready(e_35_ready),
    .out_payload(e_35_payload),
    .out_completion(e_35_completion),
    .out_bin_tag(e_35_bin_tag),
    .occupancy_o(edge_35_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_35_high_watermark <= '0;
    else if (edge_35_occupancy > edge_35_high_watermark)
      edge_35_high_watermark <= edge_35_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_36 (
    .clk,
    .reset,
    .in_valid(r_36_valid),
    .in_ready(r_36_ready),
    .in_payload(r_36_payload),
    .in_completion(r_36_completion),
    .in_bin_tag(r_36_bin_tag),
    .out_valid(e_36_valid),
    .out_ready(e_36_ready),
    .out_payload(e_36_payload),
    .out_completion(e_36_completion),
    .out_bin_tag(e_36_bin_tag),
    .occupancy_o(edge_36_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_36_high_watermark <= '0;
    else if (edge_36_occupancy > edge_36_high_watermark)
      edge_36_high_watermark <= edge_36_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_37 (
    .clk,
    .reset,
    .in_valid(r_37_valid),
    .in_ready(r_37_ready),
    .in_payload(r_37_payload),
    .in_completion(r_37_completion),
    .in_bin_tag(r_37_bin_tag),
    .out_valid(e_37_valid),
    .out_ready(e_37_ready),
    .out_payload(e_37_payload),
    .out_completion(e_37_completion),
    .out_bin_tag(e_37_bin_tag),
    .occupancy_o(edge_37_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_37_high_watermark <= '0;
    else if (edge_37_occupancy > edge_37_high_watermark)
      edge_37_high_watermark <= edge_37_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_38 (
    .clk,
    .reset,
    .in_valid(r_38_valid),
    .in_ready(r_38_ready),
    .in_payload(r_38_payload),
    .in_completion(r_38_completion),
    .in_bin_tag(r_38_bin_tag),
    .out_valid(e_38_valid),
    .out_ready(e_38_ready),
    .out_payload(e_38_payload),
    .out_completion(e_38_completion),
    .out_bin_tag(e_38_bin_tag),
    .occupancy_o(edge_38_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_38_high_watermark <= '0;
    else if (edge_38_occupancy > edge_38_high_watermark)
      edge_38_high_watermark <= edge_38_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_39 (
    .clk,
    .reset,
    .in_valid(r_39_valid),
    .in_ready(r_39_ready),
    .in_payload(r_39_payload),
    .in_completion(r_39_completion),
    .in_bin_tag(r_39_bin_tag),
    .out_valid(e_39_valid),
    .out_ready(e_39_ready),
    .out_payload(e_39_payload),
    .out_completion(e_39_completion),
    .out_bin_tag(e_39_bin_tag),
    .occupancy_o(edge_39_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_39_high_watermark <= '0;
    else if (edge_39_occupancy > edge_39_high_watermark)
      edge_39_high_watermark <= edge_39_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_40 (
    .clk,
    .reset,
    .in_valid(r_40_valid),
    .in_ready(r_40_ready),
    .in_payload(r_40_payload),
    .in_completion(r_40_completion),
    .in_bin_tag(r_40_bin_tag),
    .out_valid(e_40_valid),
    .out_ready(e_40_ready),
    .out_payload(e_40_payload),
    .out_completion(e_40_completion),
    .out_bin_tag(e_40_bin_tag),
    .occupancy_o(edge_40_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_40_high_watermark <= '0;
    else if (edge_40_occupancy > edge_40_high_watermark)
      edge_40_high_watermark <= edge_40_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_41 (
    .clk,
    .reset,
    .in_valid(r_41_valid),
    .in_ready(r_41_ready),
    .in_payload(r_41_payload),
    .in_completion(r_41_completion),
    .in_bin_tag(r_41_bin_tag),
    .out_valid(e_41_valid),
    .out_ready(e_41_ready),
    .out_payload(e_41_payload),
    .out_completion(e_41_completion),
    .out_bin_tag(e_41_bin_tag),
    .occupancy_o(edge_41_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_41_high_watermark <= '0;
    else if (edge_41_occupancy > edge_41_high_watermark)
      edge_41_high_watermark <= edge_41_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_42 (
    .clk,
    .reset,
    .in_valid(r_42_valid),
    .in_ready(r_42_ready),
    .in_payload(r_42_payload),
    .in_completion(r_42_completion),
    .in_bin_tag(r_42_bin_tag),
    .out_valid(e_42_valid),
    .out_ready(e_42_ready),
    .out_payload(e_42_payload),
    .out_completion(e_42_completion),
    .out_bin_tag(e_42_bin_tag),
    .occupancy_o(edge_42_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_42_high_watermark <= '0;
    else if (edge_42_occupancy > edge_42_high_watermark)
      edge_42_high_watermark <= edge_42_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_43 (
    .clk,
    .reset,
    .in_valid(r_43_valid),
    .in_ready(r_43_ready),
    .in_payload(r_43_payload),
    .in_completion(r_43_completion),
    .in_bin_tag(r_43_bin_tag),
    .out_valid(e_43_valid),
    .out_ready(e_43_ready),
    .out_payload(e_43_payload),
    .out_completion(e_43_completion),
    .out_bin_tag(e_43_bin_tag),
    .occupancy_o(edge_43_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_43_high_watermark <= '0;
    else if (edge_43_occupancy > edge_43_high_watermark)
      edge_43_high_watermark <= edge_43_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_44 (
    .clk,
    .reset,
    .in_valid(r_44_valid),
    .in_ready(r_44_ready),
    .in_payload(r_44_payload),
    .in_completion(r_44_completion),
    .in_bin_tag(r_44_bin_tag),
    .out_valid(e_44_valid),
    .out_ready(e_44_ready),
    .out_payload(e_44_payload),
    .out_completion(e_44_completion),
    .out_bin_tag(e_44_bin_tag),
    .occupancy_o(edge_44_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_44_high_watermark <= '0;
    else if (edge_44_occupancy > edge_44_high_watermark)
      edge_44_high_watermark <= edge_44_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_45 (
    .clk,
    .reset,
    .in_valid(r_45_valid),
    .in_ready(r_45_ready),
    .in_payload(r_45_payload),
    .in_completion(r_45_completion),
    .in_bin_tag(r_45_bin_tag),
    .out_valid(e_45_valid),
    .out_ready(e_45_ready),
    .out_payload(e_45_payload),
    .out_completion(e_45_completion),
    .out_bin_tag(e_45_bin_tag),
    .occupancy_o(edge_45_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_45_high_watermark <= '0;
    else if (edge_45_occupancy > edge_45_high_watermark)
      edge_45_high_watermark <= edge_45_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_46 (
    .clk,
    .reset,
    .in_valid(r_46_valid),
    .in_ready(r_46_ready),
    .in_payload(r_46_payload),
    .in_completion(r_46_completion),
    .in_bin_tag(r_46_bin_tag),
    .out_valid(e_46_valid),
    .out_ready(e_46_ready),
    .out_payload(e_46_payload),
    .out_completion(e_46_completion),
    .out_bin_tag(e_46_bin_tag),
    .occupancy_o(edge_46_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_46_high_watermark <= '0;
    else if (edge_46_occupancy > edge_46_high_watermark)
      edge_46_high_watermark <= edge_46_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_47 (
    .clk,
    .reset,
    .in_valid(r_47_valid),
    .in_ready(r_47_ready),
    .in_payload(r_47_payload),
    .in_completion(r_47_completion),
    .in_bin_tag(r_47_bin_tag),
    .out_valid(e_47_valid),
    .out_ready(e_47_ready),
    .out_payload(e_47_payload),
    .out_completion(e_47_completion),
    .out_bin_tag(e_47_bin_tag),
    .occupancy_o(edge_47_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_47_high_watermark <= '0;
    else if (edge_47_occupancy > edge_47_high_watermark)
      edge_47_high_watermark <= edge_47_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_48 (
    .clk,
    .reset,
    .in_valid(r_48_valid),
    .in_ready(r_48_ready),
    .in_payload(r_48_payload),
    .in_completion(r_48_completion),
    .in_bin_tag(r_48_bin_tag),
    .out_valid(e_48_valid),
    .out_ready(e_48_ready),
    .out_payload(e_48_payload),
    .out_completion(e_48_completion),
    .out_bin_tag(e_48_bin_tag),
    .occupancy_o(edge_48_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_48_high_watermark <= '0;
    else if (edge_48_occupancy > edge_48_high_watermark)
      edge_48_high_watermark <= edge_48_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_49 (
    .clk,
    .reset,
    .in_valid(r_49_valid),
    .in_ready(r_49_ready),
    .in_payload(r_49_payload),
    .in_completion(r_49_completion),
    .in_bin_tag(r_49_bin_tag),
    .out_valid(e_49_valid),
    .out_ready(e_49_ready),
    .out_payload(e_49_payload),
    .out_completion(e_49_completion),
    .out_bin_tag(e_49_bin_tag),
    .occupancy_o(edge_49_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_49_high_watermark <= '0;
    else if (edge_49_occupancy > edge_49_high_watermark)
      edge_49_high_watermark <= edge_49_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_50 (
    .clk,
    .reset,
    .in_valid(r_50_valid),
    .in_ready(r_50_ready),
    .in_payload(r_50_payload),
    .in_completion(r_50_completion),
    .in_bin_tag(r_50_bin_tag),
    .out_valid(e_50_valid),
    .out_ready(e_50_ready),
    .out_payload(e_50_payload),
    .out_completion(e_50_completion),
    .out_bin_tag(e_50_bin_tag),
    .occupancy_o(edge_50_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_50_high_watermark <= '0;
    else if (edge_50_occupancy > edge_50_high_watermark)
      edge_50_high_watermark <= edge_50_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_51 (
    .clk,
    .reset,
    .in_valid(r_51_valid),
    .in_ready(r_51_ready),
    .in_payload(r_51_payload),
    .in_completion(r_51_completion),
    .in_bin_tag(r_51_bin_tag),
    .out_valid(e_51_valid),
    .out_ready(e_51_ready),
    .out_payload(e_51_payload),
    .out_completion(e_51_completion),
    .out_bin_tag(e_51_bin_tag),
    .occupancy_o(edge_51_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_51_high_watermark <= '0;
    else if (edge_51_occupancy > edge_51_high_watermark)
      edge_51_high_watermark <= edge_51_occupancy;
  end
  event_stream_fifo #(.PAYLOAD_WIDTH(PAYLOAD_WIDTH), .TAG_WIDTH(TAG_WIDTH), .DEPTH(EDGE_FIFO_DEPTH)) edge_fifo_52 (
    .clk,
    .reset,
    .in_valid(r_52_valid),
    .in_ready(r_52_ready),
    .in_payload(r_52_payload),
    .in_completion(r_52_completion),
    .in_bin_tag(r_52_bin_tag),
    .out_valid(e_52_valid),
    .out_ready(e_52_ready),
    .out_payload(e_52_payload),
    .out_completion(e_52_completion),
    .out_bin_tag(e_52_bin_tag),
    .occupancy_o(edge_52_occupancy)
  );
  always_ff @(posedge clk) begin
    if (reset) edge_52_high_watermark <= '0;
    else if (edge_52_occupancy > edge_52_high_watermark)
      edge_52_high_watermark <= edge_52_occupancy;
  end
  event_fork2 fork_input (
    .clk,
    .reset,
    .in_valid(ingress_valid),
    .in_ready(ingress_ready),
    .in_payload(ingress_payload),
    .in_completion(ingress_completion),
    .in_bin_tag(ingress_bin_tag),
    .out0_valid(r_0_valid),
    .out0_ready(r_0_ready),
    .out0_payload(r_0_payload),
    .out0_completion(r_0_completion),
    .out0_bin_tag(r_0_bin_tag),
    .out1_valid(r_1_valid),
    .out1_ready(r_1_ready),
    .out1_payload(r_1_payload),
    .out1_completion(r_1_completion),
    .out1_bin_tag(r_1_bin_tag)
  );
  event_fork2 fork_detail_stem (
    .clk,
    .reset,
    .in_valid(n_detail_stem_valid),
    .in_ready(n_detail_stem_ready),
    .in_payload(n_detail_stem_payload),
    .in_completion(n_detail_stem_completion),
    .in_bin_tag(n_detail_stem_bin_tag),
    .out0_valid(r_2_valid),
    .out0_ready(r_2_ready),
    .out0_payload(r_2_payload),
    .out0_completion(r_2_completion),
    .out0_bin_tag(r_2_bin_tag),
    .out1_valid(r_3_valid),
    .out1_ready(r_3_ready),
    .out1_payload(r_3_payload),
    .out1_completion(r_3_completion),
    .out1_bin_tag(r_3_bin_tag)
  );
  assign r_4_valid = n_detail1_standard_valid;
  assign n_detail1_standard_ready = r_4_ready;
  assign r_4_payload = n_detail1_standard_payload;
  assign r_4_completion = n_detail1_standard_completion;
  assign r_4_bin_tag = n_detail1_standard_bin_tag;
  event_fork2 fork_stem (
    .clk,
    .reset,
    .in_valid(n_stem_valid),
    .in_ready(n_stem_ready),
    .in_payload(n_stem_payload),
    .in_completion(n_stem_completion),
    .in_bin_tag(n_stem_bin_tag),
    .out0_valid(r_5_valid),
    .out0_ready(r_5_ready),
    .out0_payload(r_5_payload),
    .out0_completion(r_5_completion),
    .out0_bin_tag(r_5_bin_tag),
    .out1_valid(r_6_valid),
    .out1_ready(r_6_ready),
    .out1_payload(r_6_payload),
    .out1_completion(r_6_completion),
    .out1_bin_tag(r_6_bin_tag)
  );
  assign r_7_valid = n_enc1_standard_valid;
  assign n_enc1_standard_ready = r_7_ready;
  assign r_7_payload = n_enc1_standard_payload;
  assign r_7_completion = n_enc1_standard_completion;
  assign r_7_bin_tag = n_enc1_standard_bin_tag;
  event_fork2 fork_enc1_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc1_residual_or_valid),
    .in_ready(n_enc1_residual_or_ready),
    .in_payload(n_enc1_residual_or_payload),
    .in_completion(n_enc1_residual_or_completion),
    .in_bin_tag(n_enc1_residual_or_bin_tag),
    .out0_valid(r_8_valid),
    .out0_ready(r_8_ready),
    .out0_payload(r_8_payload),
    .out0_completion(r_8_completion),
    .out0_bin_tag(r_8_bin_tag),
    .out1_valid(r_9_valid),
    .out1_ready(r_9_ready),
    .out1_payload(r_9_payload),
    .out1_completion(r_9_completion),
    .out1_bin_tag(r_9_bin_tag)
  );
  assign r_10_valid = n_enc1_extra_depthwise_valid;
  assign n_enc1_extra_depthwise_ready = r_10_ready;
  assign r_10_payload = n_enc1_extra_depthwise_payload;
  assign r_10_completion = n_enc1_extra_depthwise_completion;
  assign r_10_bin_tag = n_enc1_extra_depthwise_bin_tag;
  assign r_11_valid = n_enc1_extra_pointwise_valid;
  assign n_enc1_extra_pointwise_ready = r_11_ready;
  assign r_11_payload = n_enc1_extra_pointwise_payload;
  assign r_11_completion = n_enc1_extra_pointwise_completion;
  assign r_11_bin_tag = n_enc1_extra_pointwise_bin_tag;
  event_fork2 fork_enc1_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc1_extra_residual_or_valid),
    .in_ready(n_enc1_extra_residual_or_ready),
    .in_payload(n_enc1_extra_residual_or_payload),
    .in_completion(n_enc1_extra_residual_or_completion),
    .in_bin_tag(n_enc1_extra_residual_or_bin_tag),
    .out0_valid(r_12_valid),
    .out0_ready(r_12_ready),
    .out0_payload(r_12_payload),
    .out0_completion(r_12_completion),
    .out0_bin_tag(r_12_bin_tag),
    .out1_valid(r_13_valid),
    .out1_ready(r_13_ready),
    .out1_payload(r_13_payload),
    .out1_completion(r_13_completion),
    .out1_bin_tag(r_13_bin_tag)
  );
  event_fork2 fork_down2_standard (
    .clk,
    .reset,
    .in_valid(n_down2_standard_valid),
    .in_ready(n_down2_standard_ready),
    .in_payload(n_down2_standard_payload),
    .in_completion(n_down2_standard_completion),
    .in_bin_tag(n_down2_standard_bin_tag),
    .out0_valid(r_14_valid),
    .out0_ready(r_14_ready),
    .out0_payload(r_14_payload),
    .out0_completion(r_14_completion),
    .out0_bin_tag(r_14_bin_tag),
    .out1_valid(r_15_valid),
    .out1_ready(r_15_ready),
    .out1_payload(r_15_payload),
    .out1_completion(r_15_completion),
    .out1_bin_tag(r_15_bin_tag)
  );
  assign r_16_valid = n_enc2_depthwise_valid;
  assign n_enc2_depthwise_ready = r_16_ready;
  assign r_16_payload = n_enc2_depthwise_payload;
  assign r_16_completion = n_enc2_depthwise_completion;
  assign r_16_bin_tag = n_enc2_depthwise_bin_tag;
  assign r_17_valid = n_enc2_pointwise_valid;
  assign n_enc2_pointwise_ready = r_17_ready;
  assign r_17_payload = n_enc2_pointwise_payload;
  assign r_17_completion = n_enc2_pointwise_completion;
  assign r_17_bin_tag = n_enc2_pointwise_bin_tag;
  event_fork2 fork_enc2_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc2_residual_or_valid),
    .in_ready(n_enc2_residual_or_ready),
    .in_payload(n_enc2_residual_or_payload),
    .in_completion(n_enc2_residual_or_completion),
    .in_bin_tag(n_enc2_residual_or_bin_tag),
    .out0_valid(r_18_valid),
    .out0_ready(r_18_ready),
    .out0_payload(r_18_payload),
    .out0_completion(r_18_completion),
    .out0_bin_tag(r_18_bin_tag),
    .out1_valid(r_19_valid),
    .out1_ready(r_19_ready),
    .out1_payload(r_19_payload),
    .out1_completion(r_19_completion),
    .out1_bin_tag(r_19_bin_tag)
  );
  assign r_20_valid = n_enc2_extra_depthwise_valid;
  assign n_enc2_extra_depthwise_ready = r_20_ready;
  assign r_20_payload = n_enc2_extra_depthwise_payload;
  assign r_20_completion = n_enc2_extra_depthwise_completion;
  assign r_20_bin_tag = n_enc2_extra_depthwise_bin_tag;
  assign r_21_valid = n_enc2_extra_pointwise_valid;
  assign n_enc2_extra_pointwise_ready = r_21_ready;
  assign r_21_payload = n_enc2_extra_pointwise_payload;
  assign r_21_completion = n_enc2_extra_pointwise_completion;
  assign r_21_bin_tag = n_enc2_extra_pointwise_bin_tag;
  event_fork2 fork_enc2_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc2_extra_residual_or_valid),
    .in_ready(n_enc2_extra_residual_or_ready),
    .in_payload(n_enc2_extra_residual_or_payload),
    .in_completion(n_enc2_extra_residual_or_completion),
    .in_bin_tag(n_enc2_extra_residual_or_bin_tag),
    .out0_valid(r_22_valid),
    .out0_ready(r_22_ready),
    .out0_payload(r_22_payload),
    .out0_completion(r_22_completion),
    .out0_bin_tag(r_22_bin_tag),
    .out1_valid(r_23_valid),
    .out1_ready(r_23_ready),
    .out1_payload(r_23_payload),
    .out1_completion(r_23_completion),
    .out1_bin_tag(r_23_bin_tag)
  );
  assign r_24_valid = n_down3_depthwise_valid;
  assign n_down3_depthwise_ready = r_24_ready;
  assign r_24_payload = n_down3_depthwise_payload;
  assign r_24_completion = n_down3_depthwise_completion;
  assign r_24_bin_tag = n_down3_depthwise_bin_tag;
  event_fork2 fork_down3_pointwise (
    .clk,
    .reset,
    .in_valid(n_down3_pointwise_valid),
    .in_ready(n_down3_pointwise_ready),
    .in_payload(n_down3_pointwise_payload),
    .in_completion(n_down3_pointwise_completion),
    .in_bin_tag(n_down3_pointwise_bin_tag),
    .out0_valid(r_25_valid),
    .out0_ready(r_25_ready),
    .out0_payload(r_25_payload),
    .out0_completion(r_25_completion),
    .out0_bin_tag(r_25_bin_tag),
    .out1_valid(r_26_valid),
    .out1_ready(r_26_ready),
    .out1_payload(r_26_payload),
    .out1_completion(r_26_completion),
    .out1_bin_tag(r_26_bin_tag)
  );
  assign r_27_valid = n_enc3_depthwise_valid;
  assign n_enc3_depthwise_ready = r_27_ready;
  assign r_27_payload = n_enc3_depthwise_payload;
  assign r_27_completion = n_enc3_depthwise_completion;
  assign r_27_bin_tag = n_enc3_depthwise_bin_tag;
  assign r_28_valid = n_enc3_pointwise_valid;
  assign n_enc3_pointwise_ready = r_28_ready;
  assign r_28_payload = n_enc3_pointwise_payload;
  assign r_28_completion = n_enc3_pointwise_completion;
  assign r_28_bin_tag = n_enc3_pointwise_bin_tag;
  event_fork2 fork_enc3_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc3_residual_or_valid),
    .in_ready(n_enc3_residual_or_ready),
    .in_payload(n_enc3_residual_or_payload),
    .in_completion(n_enc3_residual_or_completion),
    .in_bin_tag(n_enc3_residual_or_bin_tag),
    .out0_valid(r_29_valid),
    .out0_ready(r_29_ready),
    .out0_payload(r_29_payload),
    .out0_completion(r_29_completion),
    .out0_bin_tag(r_29_bin_tag),
    .out1_valid(r_30_valid),
    .out1_ready(r_30_ready),
    .out1_payload(r_30_payload),
    .out1_completion(r_30_completion),
    .out1_bin_tag(r_30_bin_tag)
  );
  assign r_31_valid = n_enc3_extra_depthwise_valid;
  assign n_enc3_extra_depthwise_ready = r_31_ready;
  assign r_31_payload = n_enc3_extra_depthwise_payload;
  assign r_31_completion = n_enc3_extra_depthwise_completion;
  assign r_31_bin_tag = n_enc3_extra_depthwise_bin_tag;
  assign r_32_valid = n_enc3_extra_pointwise_valid;
  assign n_enc3_extra_pointwise_ready = r_32_ready;
  assign r_32_payload = n_enc3_extra_pointwise_payload;
  assign r_32_completion = n_enc3_extra_pointwise_completion;
  assign r_32_bin_tag = n_enc3_extra_pointwise_bin_tag;
  event_fork2 fork_enc3_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc3_extra_residual_or_valid),
    .in_ready(n_enc3_extra_residual_or_ready),
    .in_payload(n_enc3_extra_residual_or_payload),
    .in_completion(n_enc3_extra_residual_or_completion),
    .in_bin_tag(n_enc3_extra_residual_or_bin_tag),
    .out0_valid(r_33_valid),
    .out0_ready(r_33_ready),
    .out0_payload(r_33_payload),
    .out0_completion(r_33_completion),
    .out0_bin_tag(r_33_bin_tag),
    .out1_valid(r_34_valid),
    .out1_ready(r_34_ready),
    .out1_payload(r_34_payload),
    .out1_completion(r_34_completion),
    .out1_bin_tag(r_34_bin_tag)
  );
  assign r_35_valid = n_context1_depthwise_valid;
  assign n_context1_depthwise_ready = r_35_ready;
  assign r_35_payload = n_context1_depthwise_payload;
  assign r_35_completion = n_context1_depthwise_completion;
  assign r_35_bin_tag = n_context1_depthwise_bin_tag;
  assign r_36_valid = n_context1_pointwise_valid;
  assign n_context1_pointwise_ready = r_36_ready;
  assign r_36_payload = n_context1_pointwise_payload;
  assign r_36_completion = n_context1_pointwise_completion;
  assign r_36_bin_tag = n_context1_pointwise_bin_tag;
  event_fork2 fork_context1_residual_or (
    .clk,
    .reset,
    .in_valid(n_context1_residual_or_valid),
    .in_ready(n_context1_residual_or_ready),
    .in_payload(n_context1_residual_or_payload),
    .in_completion(n_context1_residual_or_completion),
    .in_bin_tag(n_context1_residual_or_bin_tag),
    .out0_valid(r_37_valid),
    .out0_ready(r_37_ready),
    .out0_payload(r_37_payload),
    .out0_completion(r_37_completion),
    .out0_bin_tag(r_37_bin_tag),
    .out1_valid(r_38_valid),
    .out1_ready(r_38_ready),
    .out1_payload(r_38_payload),
    .out1_completion(r_38_completion),
    .out1_bin_tag(r_38_bin_tag)
  );
  assign r_39_valid = n_context2_depthwise_valid;
  assign n_context2_depthwise_ready = r_39_ready;
  assign r_39_payload = n_context2_depthwise_payload;
  assign r_39_completion = n_context2_depthwise_completion;
  assign r_39_bin_tag = n_context2_depthwise_bin_tag;
  assign r_40_valid = n_context2_pointwise_valid;
  assign n_context2_pointwise_ready = r_40_ready;
  assign r_40_payload = n_context2_pointwise_payload;
  assign r_40_completion = n_context2_pointwise_completion;
  assign r_40_bin_tag = n_context2_pointwise_bin_tag;
  assign r_41_valid = n_context2_residual_or_valid;
  assign n_context2_residual_or_ready = r_41_ready;
  assign r_41_payload = n_context2_residual_or_payload;
  assign r_41_completion = n_context2_residual_or_completion;
  assign r_41_bin_tag = n_context2_residual_or_bin_tag;
  assign r_42_valid = n_project3_valid;
  assign n_project3_ready = r_42_ready;
  assign r_42_payload = n_project3_payload;
  assign r_42_completion = n_project3_completion;
  assign r_42_bin_tag = n_project3_bin_tag;
  assign r_43_valid = n_project3_upsample2x_valid;
  assign n_project3_upsample2x_ready = r_43_ready;
  assign r_43_payload = n_project3_upsample2x_payload;
  assign r_43_completion = n_project3_upsample2x_completion;
  assign r_43_bin_tag = n_project3_upsample2x_bin_tag;
  assign r_44_valid = n_decoder2_concat_valid;
  assign n_decoder2_concat_ready = r_44_ready;
  assign r_44_payload = n_decoder2_concat_payload;
  assign r_44_completion = n_decoder2_concat_completion;
  assign r_44_bin_tag = n_decoder2_concat_bin_tag;
  assign r_45_valid = n_decoder2_fuse_valid;
  assign n_decoder2_fuse_ready = r_45_ready;
  assign r_45_payload = n_decoder2_fuse_payload;
  assign r_45_completion = n_decoder2_fuse_completion;
  assign r_45_bin_tag = n_decoder2_fuse_bin_tag;
  assign r_46_valid = n_project2_valid;
  assign n_project2_ready = r_46_ready;
  assign r_46_payload = n_project2_payload;
  assign r_46_completion = n_project2_completion;
  assign r_46_bin_tag = n_project2_bin_tag;
  assign r_47_valid = n_project2_upsample2x_valid;
  assign n_project2_upsample2x_ready = r_47_ready;
  assign r_47_payload = n_project2_upsample2x_payload;
  assign r_47_completion = n_project2_upsample2x_completion;
  assign r_47_bin_tag = n_project2_upsample2x_bin_tag;
  assign r_48_valid = n_semantic_half_multiplicity_sum_valid;
  assign n_semantic_half_multiplicity_sum_ready = r_48_ready;
  assign r_48_payload = n_semantic_half_multiplicity_sum_payload;
  assign r_48_completion = n_semantic_half_multiplicity_sum_completion;
  assign r_48_bin_tag = n_semantic_half_multiplicity_sum_bin_tag;
  assign r_49_valid = n_semantic_native_upsample2x_valid;
  assign n_semantic_native_upsample2x_ready = r_49_ready;
  assign r_49_payload = n_semantic_native_upsample2x_payload;
  assign r_49_completion = n_semantic_native_upsample2x_completion;
  assign r_49_bin_tag = n_semantic_native_upsample2x_bin_tag;
  assign r_50_valid = n_detail1_residual_or_valid;
  assign n_detail1_residual_or_ready = r_50_ready;
  assign r_50_payload = n_detail1_residual_or_payload;
  assign r_50_completion = n_detail1_residual_or_completion;
  assign r_50_bin_tag = n_detail1_residual_or_bin_tag;
  assign r_51_valid = n_final_concat_valid;
  assign n_final_concat_ready = r_51_ready;
  assign r_51_payload = n_final_concat_payload;
  assign r_51_completion = n_final_concat_completion;
  assign r_51_bin_tag = n_final_concat_bin_tag;
  assign r_52_valid = n_final_fuse_standard_valid;
  assign n_final_fuse_standard_ready = r_52_ready;
  assign r_52_payload = n_final_fuse_standard_payload;
  assign r_52_completion = n_final_fuse_standard_completion;
  assign r_52_bin_tag = n_final_fuse_standard_bin_tag;
  logic error_actor_detail_stem;
  logic initialized_actor_detail_stem;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(2),
    .OUTPUT_CHANNELS(8),
    .GROUPS(1),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(8),
    .OUTPUT_HEIGHT(8),
    .KERNEL_WEIGHTS(1152'h162ee91a3303172505f60780394a077f5125cf80808c80808c80807f7f7f2f8095808080807f7f807f7f807f7f7f2d847f7f807f198004122d240f191618211819162a3a281c18127f7f807f7f807f2280807f7f80797f804d7f808080808080213b428080aec410d327352f06010301fd0105010405020401feff0401088080808080ae8080dd7f7f7f7f7f7ff21625),
    .CHANNEL_BETAS(128'h796a752d71fe7a7670e2773a767c712e),
    .CHANNEL_THRESHOLDS(128'h0165015b0196018f01a2016c029c0173),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_detail_stem (
    .clk,
    .reset,
    .in_valid(e_0_valid),
    .in_ready(e_0_ready),
    .in_payload(e_0_payload),
    .in_completion(e_0_completion),
    .in_bin_tag(e_0_bin_tag),
    .out_valid(n_detail_stem_valid),
    .out_ready(n_detail_stem_ready),
    .out_payload(n_detail_stem_payload),
    .out_completion(n_detail_stem_completion),
    .out_bin_tag(n_detail_stem_bin_tag),
    .actor_error_o(error_actor_detail_stem),
    .initialization_done_o(initialized_actor_detail_stem)
  );
  logic error_actor_detail1_standard;
  logic initialized_actor_detail1_standard;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(8),
    .OUTPUT_CHANNELS(8),
    .GROUPS(1),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(8),
    .OUTPUT_HEIGHT(8),
    .KERNEL_WEIGHTS({
      4096'h808080808080808080bba9ba160605411b1e6e7f7f7f5d7f7f7f7f868080fc8d90f9b3a47f7f7f7f6c7f7f7f7fa3cb99f3c6bcbfb5e0127f7f9b477f80807fb8a2a32adaa63d24fc8080809de99cc6f8aae79e9010aae80afff47b7f7f7f6b7f7f7f7f808080879998b5ced77f7f7f7f7f7f7f7f7fab84b9bca28dcc8c8e808080808080808080b480a4fbd7e7fe2e4080808c80809295808055274f31a1e909a7f27f7f7f7f367f7f7f7fa880d58080b0a48fb97f7f7f7f7f7f7f7f7f8089bb8080be8080b0291f7f3b047f03f944fbe444e38043b880158080808080808080807faf807f060b7f137f7f7f7f7f7f7f7f7f7f808080ad8099c680407f7f7f7f7f7f7f7f7f80808080debc80800574597f7f7f7fe3507fa980804abf2e61cf7f8080808080808080807f7fd543dd804199807f7f7f7f7f7f7f7f7fdd9a938080809d80807f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7d7f4a7b186f60c2bf938080808080ef80808a8080bf24282828c980808080ad807fd9807fed093a92f853a181f3ebcbf67f7f7f7f7f7f7f7f7f80808080808080808048717f7f7f7f7f7f7f80ff708080c0808080808080808080808080e880b8998080d1a0d77f7f7f7f7f0f7f7f64808080808080808080517f7fde7f7fa97f7f8080808080808080807f7f7f7f7f7f7f7f7ffd8e80ba8080808e9b80808497a1928886,
      512'h80d99b8bccd3bd16ceec7868587f7f405e705c8080808080808180807f7f7f7f727f7f687ff2f831ddeab0ca808e8080808080808080bbb1d490ea0dd9c3cc09
    }),
    .CHANNEL_BETAS(128'h79df7a067a7d776c767779cf75fa7aa3),
    .CHANNEL_THRESHOLDS(128'h0187016e017501a601c501a301c30172),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_detail1_standard (
    .clk,
    .reset,
    .in_valid(e_2_valid),
    .in_ready(e_2_ready),
    .in_payload(e_2_payload),
    .in_completion(e_2_completion),
    .in_bin_tag(e_2_bin_tag),
    .out_valid(n_detail1_standard_valid),
    .out_ready(n_detail1_standard_ready),
    .out_payload(n_detail1_standard_payload),
    .out_completion(n_detail1_standard_completion),
    .out_bin_tag(n_detail1_standard_bin_tag),
    .actor_error_o(error_actor_detail1_standard),
    .initialization_done_o(initialized_actor_detail1_standard)
  );
  logic error_actor_stem;
  logic initialized_actor_stem;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(2),
    .OUTPUT_CHANNELS(32),
    .GROUPS(1),
    .KERNEL_WIDTH(5),
    .KERNEL_HEIGHT(5),
    .STRIDE_X(2),
    .STRIDE_Y(2),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(2),
    .PAD_Y(2),
    .OUTPUT_WIDTH(4),
    .OUTPUT_HEIGHT(4),
    .KERNEL_WEIGHTS({
      4096'h8aa5a8d4b0fff601edeefe0b111202fd161715fd0e142bfade808080808080958580c4d5d82f3f1719442c4e2cfb65fff800352fc3150ebf800329148098e5187baf2f2eded94b44338a80d5ffa931fa128523fed4e380e5115bc24208f2c9de392dbeb1b0fafd0f01df0be91a2be80bf501181e05031c172b233b394480808080808c808c9d80809180808080809094808080808080ab7f7f2ec9a47f7f4dd68f7f7f7fdb806d7f4cbd80d310208075bf806b7f64eb9a7f544d258016557ab980f92304808087c18080808080808080808080809729c08080dd808080808080808080808080808080808080808080808080808080808080808086a98f808e9f9ba1808001f410060ef423233317211c2a2345bbc0d9c28ef2ddecbcc615071107f73624222112ff0e0f06fa56251618225627082d20710ce3401245b0a3c3eb8d8080809a05222c3f0b2418501206c1b7b6c0caa18099808080808091942b311b191ae1dbbda8cab180808080ede0cfd6ca0e1b2e3d1b1d49483d0c2c4e452818133a371e0fdbdcf7dfe499acb6bd9eadc7f4030ecedffe0203f2f408050c03fd0c091dfef4000220271e02f3161716fdf5120507f5ea0a01ffeae2091113f2e70b5637427f7f0c160d5457d2d9f3fa169fb0aec7e9808ab2bbd9f70d112b258080b0add380808098a4a1c8efe8052b1a42385580dce6f5f09cf319fff5c1f0,
      4096'he7e5eaf00be2f7d0c8bfe0d6ccf1f605fbf30ad91c1200fb0502f419f7220a0ff81e0e20082c4b727f7f7f7f7f7f7f117a7f7f7f456e7f7f230b0dbea3b1b7f00780808046049e80806c441380807f2c0680807f7f318080552906010c251f12091efdf1f8050efcf6fb090cfef2ff0610a0b5fc110abbbbf2fcfed5c80a0500cdc0150f15ced0101e2805dde38099f0e2dc2c89c78abfc3bdaf80bf8eab92918b8080393d4d0f1b1618f72905fee9ddceecdceaddd702d405fbbca6313a390b80fd0102ef804c203322a47f462efda87f1619c7877f36f4cc807f5005f4982114df8880fe0bdfb1801d2e30cb807f7f7f80803f587f80804e7f7f80807f7f7fd2807f7f7fcd808080317f7faea36a747fa780687f41808019feea80804e5613808080999c8f8091c3ff0702030f243146323210394f43260938686f5c2efdf707faf8e2dce5e8ccdec7d3e7eee8cdafe1fc25f40c686e2ef611555a3dd9f646164bde083e1959e2f53e7f1fb4a5f71939babd151f59cd06387f7feaf9407f72c1024e64808323010480802edc37808cd9e12180ba112e2580d21b295824cb184650d480c95443a689ca17368080e83a5f8080b9343c80807f7f7f8080777f7f808056607f80807f7f7f80807f7f7f7f51e880807f60de808b7f472980807f4ce180807f7f298080807f2280efc9ad808043522a146d808094521bdd80808186,
      4096'h80807f807f807f7f2180db804b7f781e80807fcaa980808080f91509333573413b672e20fc0b092defb4a4808080a79f9a898080dbb4af9fbe233af4e7cdb994e1a3e5ccedb7808a80aec19980b2032d5580be092b49808de80f0d80aefa1f279ab4022c3b8080d9111995bb2f323f0f295a7a7adad83246708c9fd6020d80807f7f708080a87f7f8080a9597f808015697f8080197f7f7f7f6eb9807f7f6380807f7f7fc0807f7f4b96807f7f3b8080a3cfb6efcfa2c81cdec1b6ddc0f3e2bbb0c5a3aa80b2938f9b2c7353604e2945e9fa200af31527fae7fff506e6d3fd141c298080b7a48ed0f0150c0a3413160a0d2103f703018fd5c9ac908080918080adbf08eea1271f1706031e0d112117dde2d0d1d4f1f7fd04e1fbf113fbf7fdf420ff0f01faf5ff00e3fd1f06ffa9dbd5dfa7cfe4edd5d5d4d6070be8daf3eefeeeb2da04eaca8cb1f3dc809fc66180cd0c808080e5687a8057ce8080808080807f808080801cf6db806480ada5c780808080808080808080332b28dd311d4591199eb9fc5dd3dda2ae150fe900dbc9fb2e0af7a5ad080ee2d5168a801c45e2bae4cc223df1a400dbcf3e8080808080e2dbdec3af121f1c07120f010b1226060702031080808080808092bdae8096c5e6c1b311eaeef902fdf711eff47f7f7f80807f7ff380807f7f5a80807f7fdd80807f7ffa808080806a7128808001787f85,
      512'h8005705780803d47688087707f69040e05c380f9fd06d2af051419eac5332330f6df5a462305eaecf30b3838fef2152314f8fc131c07dcd6f005f2e4d0020d07
    }),
    .CHANNEL_BETAS(512'h76b1795c78c173cd7a9f77cc76d47705726b7578785b6c85736e797070d171ec755478db745b763c78997a316b52777a79137849787679d17a157976750473f4),
    .CHANNEL_THRESHOLDS(512'h020b016e0206020f01d60310020c02db02620237014d02ab025c014202220230024b015c023101ba01e3022b02b001790156026901de02430177025c01df020f),
    .ENABLE_INHIBITION(1),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h00e8),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_stem (
    .clk,
    .reset,
    .in_valid(e_1_valid),
    .in_ready(e_1_ready),
    .in_payload(e_1_payload),
    .in_completion(e_1_completion),
    .in_bin_tag(e_1_bin_tag),
    .out_valid(n_stem_valid),
    .out_ready(n_stem_ready),
    .out_payload(n_stem_payload),
    .out_completion(n_stem_completion),
    .out_bin_tag(n_stem_bin_tag),
    .actor_error_o(error_actor_stem),
    .initialization_done_o(initialized_actor_stem)
  );
  logic error_actor_enc1_standard;
  logic initialized_actor_enc1_standard;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(32),
    .OUTPUT_CHANNELS(32),
    .GROUPS(1),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(4),
    .OUTPUT_HEIGHT(4),
    .KERNEL_WEIGHTS({
      4096'h7f7f6d7fa08844c2805053d6aaf129fa007afded2b0b1565d5e7809c9080bdae808e91801f0aff162008080d127f7f7f66356d7f7f7fd3a280f0d3340f7f277f7f3e4b31307f7f7fb7ec80c6128680808080801b3a332d7a6f2d7f7f7f7f7f7f7f7f7f8080808080808080808880aa808a808080802ee7cc6be8ca7f7f7f80ef2380ddb1808080fe3c3ebfbe1d80b0fbe000e27f7f370fee03a7c7a6c1c8b98080802e20f37f0a8410a4c9808e808080808080807f7f677a7a7fdd7f7f7f546f6a7f7fa4954cbc24099380a880a080cc418080e3808ff280fa322a3d511f1a643e7f70797f12081101e6808080808080b102a7aa3966082335f5ca06571b647f781f5e74c47f777fd28c8080808c8080a780b0c080cf8a4efbf0fc413d9bd72316f4e815d5c56c7f667f5c567f5c547f7f333a17ec1b18ca7f37f9f94f63bff9c9efc105edfbfe10010df5f311acdc04d025d31b7f7d2ab69005cfa200d5de2a0bea070b2ce5e5f080a8d8b18080808080bbe8d40ad1a30acb8005016a1dda2a657f38d38080b68080998080ceb98edbc281dcf680fd552b497f68ead816808080c38080a580803812f6ddd1aef91a00fbe0ccfda88040fd142e357f1afa3c225d7f1721ce0eedd8160c0c0def02c8b4b6b0e2067f7c7f6e47537f3836536a63463334521bc1c51fada0df8499e180d51638adc5eb80f12dca2c24ecacc9a686,
      4096'hac7f22527f77f07f6c7f4ef7f12f02c0593be32d554f7d6f172b192a68757f7f162b7f45fd4ae3217f7a2c7f7f7a4c4e2c00e6dbfd01dcceb3ca80c78894bbc66b630a297f7f80c0a40704c7eb1680f8149c7f57f1a4db018fa8eba60a060ee529dd80f0f3080a0c1bfe022bfb4c74ea1e6d5c8080ab466853045b2f8afacf4ae9ea374c5956467f29d5f54f351a795d442d4b50484b4fb1b5de7f5a2d564c0ee0cfcd8bc2d880998b809481f226fca89880a5c08070b922e496af8080800a5035955c57800945bd3e48d8492f8602206fe8ed7f7f5af617f815f6e130f5159e91b0f0bec580ecc480d8dacaa0b69b80ca808083c7b980d50d95b380d311fbdde7b1a9938e8f07ff9e2d309787d09404cac311bfef80b59d7fddfb3c2a0bf1c5c5cf3717e4e0e281a9866b7f2b5263d8f0512edaca4f05b1111cf9e049d7ac2815b48080a0cf3495808080bf92808ce2ce80f3eb8080b5106b7f4a7f7f087f5f1f0644d78bf480f15c1af0e224fcffcf02012befd9d6df0c809fdaed1326fa2018a8fa36070c0c0302f60700ed643a3fffef40aa14774c50050106f7940e7f32211b635d537f697fbad2808fcb8092988d0acb1f451e184b2c15cce8e9a8e61414de00e62828bc20218080b8041f9bf80f8380c0b55734557321c13253d6686f31e025de808097abbee5a4dde880e1ea27380918350291a7c21a1742ff1644c3,
      4096'h195a88a8d2bc2852db2c58ded3d9d8e6bb9c80adddf8960913d34d0fd727d8d4fcc5e7bdef0c3e2dc31019ecd71a1c1de0a8fff99cb280846d5b5d7f4626437a762d151336dfe2d8c82c290a2d10f034130824ba31be0833cc55f6f527fc0a34e6d7d5fdcd2f1ff3e3ee1504120580bac19fdeca80ccbbef042cf21206a8fbf980808080808080808080808080808080809b19217a80e02730113a4b325514d57522df4cecf20ae81e10d8070c71514f657f7f7f23577faa3258c41d5cf7c67f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f557f7f7f7f7f7f7f7f7f157f7f7f7f7f7f99f27f80800180801f7f3c7f7f0b3f7f8580b2ab80878dd0a48f80f523af00aa8c07eac57f8bdb72bb807f2a807f2615e180827f7e7fb5938dbcdec9b9b08080809c8080be80c1808097b08080e380b56f96808080808080808049ed63f280627f7f7f218d7f49f57f7f7f7f80371080fb7f80787ff59a807f28e47572cd7f7f7f7f787f7f7f7f808e1580818080808ae19c83df0c80e288808080808f80b580809c808080808080808080d38080b780800ac4807f7a497f3c257f7f7f80d68082dac5807403b59e878080a580be8d9e80fd9d80f980808080e83380b92180121f08fefaf3fdfe09fef0bbb980dff30c267f1d80dd4c808083808080f9da3a82802a80ab41e8802380805e8f802fc090239580017f08188080d680980e,
      4096'h80ed1980895080b64b809970f58052c8804b7fdd4de6b51f8080808080809bb05d80808080808080e17b80803d8f4045bef04b80802b8080858080ba8098e48011fb809d5880a77f47d9708080ed8080048080c1b28080ac89ad90de96a48004c092959da4d99d804aec806b78417f9080d58080ee808080c9cc1d80808247bcb8b7fcc6b0d08785bcbadaa7bfba80edc280191510e7d612dedff5d094a580a34f867f6ae6f1a489e89484c09e8080a92980a001a8c31d80fd7f808057809e563d3448dddae3dfcd89adf7041e12303f7f682be33de6d916d0899ef9f03f16130a9faafde70dfa1005f5130bf7e3e903d3c0b414c6ce6443567f481ae9c81326393043200fc4c9b06c1bbb1bd887b385803027067f64317d7f7f01dfeb8280808780800ee8020ce619f4c204382ddd6012e505f0eee0dee95656fe9ecd015c7d435b4e3fc48080b1c7beeed3adb087a31d403f4856218081d6101eefb7bfeb808080604c2a7f5f307f7662c3c3e1e6f3f6ab8bc5829e80b2c4b9b91cfbd9d6e24cfee27f76fd7f7f24612505eeff0bc8d4add1cce38f859ce6f9ef523af98b9fd2f0f852120acef8e7cce50105d9e3feb8a7dab0c8d4cce6a81dd4b297cdb90905dd7f2acf7f7f646b37f331c6c09c9ab1caddb1ad91803800ec31d9bb808080337b57495f6ff1d418b6f3dbf97f50dc104f764b46fce5efaa9e9aa5b4aa9396,
      4096'h88b8a69d1f110326ff1b0a10fc505f5a7f7f7f7f7f7f55493316d310d64549594a4b30ed3d7f7f7fde0290808197b0f2fe377f6f2a29572d3e5aff06f4176b5c215237f313140803e3d40a4f57565ee0f40dd7c6bf37093333ec803ff91b7f5b665bfe82bb9fd9cca0c4babcdab0e6ce3e3c142aa6b4fafdf715eeb0feecc4dadbd0b7e3a5f115db808080e0d0c4e0df85809cc9aebfcc187f170bf7f1024129365140667f7f7b7f0d4042482f1613ff01e9f6ff9ea0cf0900e0ec0ed9821b0236ef5a711d2e5f16263f214027010fff21e4fbafcc9d08f8149ed2eab396c30b4a155a1ef32e3b3cd3e6d7a380b0ba9dbce8d4e58e8085fffdefb6c80be31c157f7f7f8080808080808080808080808f808050d98b809480808080bb80067f430f7f7ff5e2fcee20f6bfcfddc37f3e670b7f7fd9d9b7bc7f697f7f7f7f7f7f70f9027f3b7f7f7f7f7f7f7f7f7f7f7f7f7f66f17f6b3e7f7f7f7f838080e3b702b480808bc47f1cc7232d80507f7f7f7f7f7f7f7f7f808080a6dec16a7f63803c2e487f507f5a7face9156143766279eb7f7f7f7f757f7f7f7f808080808080808080570ee5c4fb55037b7ff9ddb6f27ea0af1e0680808080808080808080df809da48033061e7f7f7f7f7f7f7f7f7fc893808056de803e1d8080808080802cadc97560147604f480808051f1aae5f1f8b09d8080b69780808080808080808080,
      4096'h808092250a477b419280c680808080a1f3802760bc6180b5df394f7f717f7f7aaf04d5808080808080808080808080808680e58080998080e7198036783ed0d9804ef7eb00d8e5d908f107c7f37f7f7f80808080808044537f7f32aa7ff675b0c5247ff05e7f714f7f7f7f7f7f7f7f7f7f838e7f803e7f47a37fec07a380ba12808980800a5dce803c7f277f7f7f7f7f7f7f7f7f7f808080948080808080b87f7f1f7f7fef58552d7f472a7f784f59307feae67f7f7f1e3e66808080808080808080f6127fa4177fd67f78d37fa1a17f4ac66240808080808080808080808080808080d1b9807f7f7f7f7f7f7f7f7f8026e1804ac18016278080808080808080808080d48092868080808080af8080808080e98080808080808080808080808080808080809aa79a80fd808080808affc0e230d81180d27f7f7f7f7f764e137f1d1fe0ce294382b6e17f7f7f707f7f7f7f7f9c80f08e80138580f50d7f03ef7f6ea9cd21e907f704f10ef1fff380e01e80fdfc8093bbc03c396c5d2425d2b28d10d280d607808080d38080f48080808080c0f00b964377aa8afc15667cb4ce00a68080094645727c52d4664d8f25803271520813808040bbcbfaf97f7f658d8080f58080808080287f511f797fcffdda0203e6e09ed5c69413e41c6cd9e51b3c366180aad68006418080b9664733652f44e64e7f7f7f7f7f657f7f7f7f7f7f74,
      4096'h7f7f44234a2d80978080969b8080807f517f7f657f327f7f9c1aa1f6171f1f08667ef3082cb1d715dcd60a15faf10c398080d4333b1a687f50733c7f787f7f7f737f7f6e0fe3fbdcaee809facdc3577f7f7f7f7f7f18ae8016eb8080d9808080ee8080cdebae8280888080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f5a7f7f37cd29142a07c906f8057fa70a1980802b80804d7f6e08cfa034fac07d7f7f7f355272fc767f7f7f7f7f7f7f7f7f7f7f7f5b7f7f7f7f668080d58080808080857f2f6e55afe87f80127f7f7f0a7f7fc87f7fd88080754fb61f3bbe7fef807f95097f1127c76993bc3fb18066fa818013bf80aa7f4f028080808080808080807f7f7ff77f7fcd7f7fd180daa280d0028cb280808080a280808080f0cf10b88080ceb1fb7f7f7f7f7f24a67f58ed801423b2e815a3fa8f809b1db30380c6f8a3c4e7eec48d80a980fbe207121de5f95875d8f69380d6d2808080a380808080808b808080808080a380809480ce7f6180642680637f9a7f4d666e093f7ecb1dc7df3eddd0a88080808a80ded2807f2f5de68a80b0bdad2618804483166280de4c95c2040bfaec16fdf9fd09f73a0b7f7f69f0dab32e05077f7f5b7b7f131a1f1e7f7f4f7f7f74317f7f797e7f7f7f7f4bef32eeee7f4f7f7fc5d19680d3b5808080d08724d9de69d493e8371e7f47dc7f41e65e808280cd00a77f56ff44f2,
      4096'h2f5c231e487f192febc17f57b57f5e917f7142662d377f687f80808080808080808058516d395f7f4c5d7fc69add3a2c67fb197f808080cbcf80141cef2b11277f586c7f7f7ffdfb7f7f6f7f357f7f8fb616e5d46ca0e67f808080b680b97f0ee36f30f03c462616b9b69880888080808080b3e79ddbc79ef88006d09c8d80fdbdea33677ff1d08037eedd1c251d731dcaf157aa724380100290250e883153ec617f7f0a165e7f7f7f7f7f7f7f7f7f7f7f653a7f7f4f7f7f9d4c7fd4adbeee9efaf4e123f3fad30b15da1addf32ebaab80caa48dd23f80ac9580808380b206197341e5dcba8080c7808080808080808080803489197fe9247feaf2f85980808fcdf776ad607f0b7f7f217f7f808080808080808080497f7f7fee7fb71b10807f7f80337f80cc7f95ad8b80dd2d808080b42646cc596f8080807f7f7f6e7f7f28647f7f7f157f7f3e5d7f4e687f5b7f65d9a3f4807f7f7f7f7f7f7f7f7f80f8dd8001cc8080800ee9802013808fc180127f117ffab5c305bf117f7f52257f557f7ff64054a4a704353174a736635d7f6d087f7f500c687b7f7f7f6a7f7f7f7f7f7f7f2f0d427f7f7f7f7f7f7f7f7fe131f680292980d4d580808080809f8080804c7f7f473d2d80d18480808080ba80b8a480581b7f170a7f0aa00bdc07807fb9657f1f7febff1cfbedc9c7ebe37f7fd3806109804080cca480738e80da9ebe80,
      4096'h80808080808080807f7f7f7f7f7f7f7f7f808a8080a58080506b1b808094808080e5a61491f03180588088437f7f7f7f7f7f7f7f7f8080807f46447f7f7f7f566f7f7f7f7f737fb6cec7fa809f471c6c8080962925804ddd808080808080808080807f7f7f7f7f7f7f7f7f777f227f7f087f7f63808e80a18080703b808080808080808080ad7f7f0b7f7f587f7f7f1377a57f7f727f7f7f8080a8dd808028655f8080808080808080808080808099b0aaec7f8f0b808080b998128080808086f58080c1807f7f7f7f2503f7d0c633402aeaf0cf20127ff0ea865283807f430f80808080808080808080808080808080808065198f7f4e807f51207f7f7f7f277f7f7f7ff8beea10d511a6ba138080804780808080807f7fa77f7f037f7f718080808080808080807f7f7f7f7f7f7f7f7f88366f8080d180808080808080d18080f080c73c7f804d7f4e7f7f6e7f7f167f7f7f7f7f05397e7f7f7f7f7f7f7ffb7f0e7f4f267f7f7f7f547f7fb57f357f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f3a7fb0f3570a7f7ff180808080808080808080808080b0808080807f7f7f7f7f7f7f7f7f027f7f5b7f7f7f7f7f80809dbf807f131afe808080808080808080801be7fd735a7f7f7f8080468df58080aa8080808080808d8080808080808080808080807f7f7f7f7f5c7f7f7f43cacc586aee7f7f7f,
      4096'h31586e56757f809be08080808080b2fd02eddc9cf58080808180967f7f7f4df5680481dd060b0105f119020df8246a70103d5330eaf50105eba6af8b8080831f7f7fdaec137f7f7fadb90d5343457f7f605b20158080d21a3f37222ac9eb38e4a596892c1e0e808896ce1a4f18ddef808080cffed2230eaad1d9c1808080c0cef8df18f93301f4d3d5f5dbd830eec73411111193e1fd7f7f7f071b0299a5c883aebe8080c590bef99cde0798c39da7bda022130e80910d8ad20b80d6f2ad92cf57677929607f374468c2b43980b9daac121bb41bd5c1d6f0d7ab80dfa8a68080805d7f7f717f7fae08f0d8d5cc9ea39fa580b1cfbfd9c4c3efc8d3ba808080ca808020c4b18093cb2d682dc0d1f0fc80fcac950cf69617d9e0aeed271b20374676291251430164243b594a3e7b5e1d55386a636f090c0bdb4c6614e7280cb8f4fecefa3cf7f90e0a190e09fafa1109f3dd050bfc1964bfe593d69780aab88027faaee4edd2efb5e180bad0809eeb80a4b8d4cdd032f8051dd0c728414408f92707fd452cf7c56e0fde17e7b1237e35317f6e2d7f7f14551efa10e4ddcc9599e3ffc1bce29ea1aef5010507f13e074f3980b8808bc7aeccf3fb0e4d61eef55ef623763c07d1453e4f5c7f7fe0de59cedc2aaec91b3b506f7f7f7f7f7f4ef121180c2417ece984fb2538193048d7191dd0f562d9fd4fa4e10f37fbed10fdeb39f6,
      4096'hb65f45385648075476077d074f67ed3727ea0e3df20b2946315d5f4911542e7f7f7f2c15fb7f4a547945202b543603243d03fc33f31d47c2c9c0cfbbf2a6013fbe8880d1b6b78080a56d347f3ee227b2d2ceeb1e7fd1d4348eb6c6d3801a0cb0510a955b0d1b39011230150d1ccba48073f7c3d69ec2b7c51238577fcdf427d2fa03ec0c1e8da4e32e10624518737f1f674500597af9460383f1080b0fe5c611fec504808ef38080ea80808016e85118ed3b1e101a4c497f697f7f7f7671a9b60dddc416d680bfeed4d9efe626b0cd27bcb7ead6d780808080eac9e0e4bcfad38bb44bef4e4feb6e71b77f2bfa0e40fd1662d0b76b3b644602537f5b467f7f7f53537f8080ec47e01a4fa645068303efd9e929d1ff41b0a31d345d4f3456744757bac7a68380a49f80b14639702b2b70f9bbfe7f45423b2b385f1443660c2747137808baac08ddabecdfc5aee4bfcca9f2d4bd16cdcb35e51c30ef3a7af2377fc17f7f803f7f8021807fd12b809ac909ac80228a801980802180807f7f7f30347f7f3f7f9ee7ecc9cbf5ff0219352bdfef7f7f80808039b280fbfccb50800e80f0b980808080808080f37abe87587f3237808080808080808080808080fe01d280a9804de2808580bdf880439ded808fbcdd2e2280b5d13254707f7f7f7f57972a7f8c057f3a5d4f277f42ed267f7f7f80808080808080808080808080808080,
      4096'h8080147f7f257f7f7f7f2d3f7f4a3a3a737f42f11d7f7f7f7f7f77e67f7f4943daf7feff2e7f8080808030806909807f7f7f7f7f7f7f7f7f9646e77f75677f522e8480e78080ae808080808080808080808080297f5ee9ca91d80711953b9380cb8080b2ea86d4808080d2808b807f7f7f7f7f7f7f7f7fd8ac453e49ce7f7f160f240ab2ae11bc8080132126460b47051454b20e29d2d399808c9ed6c2e32ca70480a2b6f7fa0ffe1503000d0f123629e7c7cc928080b5e2b2f5e7d93808ff9b07ea81cbe180b1d88080808080888080804c02b9dec001c8a01d1f4c342dd831a09680154a4ee5f94eeb9d048580809eda80a680800612dc2447e1f05c0d8004ec80dacc8093803c1d2754eedfc6878044493c211201e71915f02a16e5023aaccb06988882b48080808080ff696a900a71c6d031132a500220ebf533373d2dc340231734004eb780808f8080808080f45c5399264886b83039270d5f5813387f03fe2af538f6dd02ecd839334823e95212ec1d2511f601c220c327181131352cf83e120ccdb903e5d5f510a9b8c54c121f56facb0385800a11d62402bdb4c6947f7f7f8080809580968089b5f0f330e37fe90d7f7f147f7ce42f7bcc91807f023e8088f42a0cb5ea0905fa10017f7f7f317f7f7f707f517f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f3d147f551a4e80e3c97f6a7f7f7f7f7f7f7f7f7f7f7f7f7f,
      4096'h7fa342637f7f80397f8080e37f7f7f7f7f37d8473ea1808080808080808080227f804a7f8080b38002d59180808080807f7f7f7f7f7f7f7f7f3a7f7f135ef880808021808094808080808080809980d7808080808080808080808080808f02ece77f7f25657f7f7f037fd580808180808080bab98080978080808009d61238e2437f7f7f7f7f7f7f6a637f7f59144c3480435a80808021e58080808080a380a8b8ff07ed817f7f597f7f7f7f417f8080808080808080807f7f7f7f7f7f7f225df17f4180807f8080808080808080808080800c44b7802d90c01cd67f7f7f7f567f7f7fea08de1a4e14f3dd03057f577f1cb280e4808012a70eff80807f6780ab838088807fc0e97f7f7f7f7f7f7f7f7f7f8080d4de884280c47f80808087a50caf8913372f7f80807e990ccd7f7f7f7f7f7f7f7f7f808080d5a2ddddb1337f7f7f7f7f7f7f7f7f7f27517fa5ab4c8080808080b880808080808080808080808080807f7f7f7fed7f7fee7f7f48e349169266da808080808080808080808080808080808080807f7f7f7f7f6f7f7f7f7f59eb6021d17ff9ff808080808080808080267f7f80ea18808080808080808080168d808080bf8080808080808080808080808080800a7c6fcf6d7f8080802a513a7f80cb1f33c47f7f7f7f7f7f7f4bc380bc9bd0f1c180cd804e342ec6fe7b091a6222a9db36c3b57f26537f7f3f7f7f,
      4096'h767f7f7ce6fae404d8db16cae080808080808080ab80d10bb50ffeac36c2c4c1d1129f808080808008b530eadc3c210257b2ae808080c8ae8080a8809da3b49c96929dcd94b3abc8dbbb13eea0801380a20fb6ea0c80f8900d257f7f7f7fa3fbdbfbd8c0aa0cc7613d123922217d7f3a8080808080a7808080808080808080808080fc7f7f7f7f7f7f7f7f6b24347b7f157f692f4d7f7f6ef17f7f517f776c4db8697eaf84d980b4e580e702d7bc9a7f7f7f7f7f7f7f7f7f85e340382c7f7ab4d280808980808b808080b693808080d1bf9da4107f28307f097b124c00d47fe6e240672006c4b40aceb01f8084f07f7f7b4474737f7f7f80dc809ce2b42e45f54c215b362a23c7eee45c6c584c587f69367f1080c58080ee90aa0878e824498a017f9229e4efd0d5e9daf7f3f1012b305b7f7e0d2a1acff181e49f80a480806639757f3f4244adbc80809bb880e7cd80ccd3c3dde8a65b8080a97f7f7f7b317f19314dd698d79a80868080a18080988080808080807f7f7f7f7f7f3e617f6c2a8f7f50b92c0bed29f7d755e2e509222b808080a291b727e1127f787f7f377d71777f5f4b4f30517f2b597f280f7032133a14dc0a317f7f173f7f7f4e75727622f0d8b4e9809b80800f80802c8080851d4a7f3c347fed2c7e4a7f717f7f7f2c2e7f7d051661160d7f166dcb99ec8080a580808f244926193f1f7f4f516f7f7f7d,
      4096'h7f3f575b2a1e4137647f7f727f7f7f3315722fdc3c2f0ac28780fcc9bc8aeada7f7f7f2a0c2d7f7f7f8091a980808080908049fccc43602579422a80a780afc39ad1ef8fe2ed0604f206eee6f67f7f7f7f7f7f7f7f7fbbcc0d4b56461b15d17f7f7f3e316a7f7f7f8086808e4758802e657f7f7f7f7f6c7f7f7f7d7a7f7f7f7f6b7f76727f79766543db1be77f7f75773924f9e2d18080804d15f880bbb98081aff17f3a80e2c480ba80c5218c9c9d8001222d447f7f54687f80a386f31fbef0faafc6d680e8fe8080808080808080ae8080808080bdd1bfa4b48081d527643480a389a0fd037f7f086c62cf3c29ac80ed968019c580ad80ae96cb282951c41f2e537f7f3146637f7f7f3b4f41281d10eb0cf6e7e11bb2d180a796cca9bda0808080808ab07f596659222c7f7f7fda18b3ef65be9cb580ce13e518632afc0adb7f7f4d7f7fd27f2404547ffa08c480c0808bf011806d5613182cd08580807f978e085ef31f3a1737f8f2fbf9009bf2d21a1ce1f8808080808080f780d0eecb808080c20000cd1d0a808080da1180b98080808080c6808094a780467f7f7f707f7f7f7f8433785f7f7f317f09c89680355b80c73c80c38080347f7f7f7f7f80e675907f7fed7b7f808080147f95e5f1808080808028808080807f7f7f7f7f7f7f7f7f7f69807f7f157f2ce5808dc1d746fd809480b97f7f7f7f7f7f7f7180dd80,
      4096'h8080808080804ef8807f1c807bce8080808007fe8082c2809880803d7f7f7f7f57368b80f8c6eea180807731b17f3e0a72443d27487f3ee6303d2233e5f67f092b7ff890a27f7f7f7f7f7f7f7f7fd2c08013708022ae80da27957f7f2ef25d34f995af434cd39e2fc22b7f15c7565e371aa32ef95b23f0282b787ffc807fc2856b94837fef2bf10820e6030cf25977f3020811b2b19103901f13ef3e17b71d4cf4807f7f35c6f380808080c2808080808077c4aeacd38080c3b460d70d808080808080808732ede23b7f7f7f808080ae24a1617f097f107f808080bb8080808080ab80cb8080b91fca747f7f7feffd77f8f30b56891d80808046445c4efb3912eb1f80808080801280800a7f7f6a7f6d457f7f2a7f4b107f6bb835200f7f7f7f7f597fd8d12e808080b7de8080899759424d7869495218dd7f695c4516c31ebe807fa180188dbb160ee4a680cec9f6143e377f7f3c7f08554c7f6d7f7f7f7f7f3c06baff7f808080808080062980c1a3d7561d2dc780e6c8a94248507f8080317d7f7f7f7e7f72667e3ba2005f1741501afc808087a380a6ca80ab7710e735afd521b20ef20beaeff7040df610ef321c466b7f467f69c080a9d59a80c8a89d7f404c48214043e8eb5980c44080cb0ac2fb8dcfd69987ec8080805af7686bfc0276090cc180a74b8080398080a48080878aac908080fa1cda26e3f699b206cf80,
      4096'h801d8080ca8080f8b0a5d0b9b006d594b080aa1ba2fe80802f6c274249026e5c1e6a808082c49701c4b42de180824680e6069daf60284d5fd9744a4a7f7f373153fd7218bd23808080808080808080eba0303f801ab1a903162a4612edae9f90a67f7f7f7f48143a7d5e808097ca8091b480b42bf3044c527f274928eeec5b7f550e7f281ae4140d6df4177f7f7f00afa2de87a4ccbb80ddc7a5d0e9bbdbdad07f18f48090807f3af93a7fbc7f7faf7f7ff6117f7f7f7f7fee7f7f808080453480828080075900335d092efc2c687f7f80cc807f4f7f808084807f7f76fe0692487f747f7f7f7f7f808080faf38a808080de7f807f7f437f7f7f7f7f7f7f7f7f7f7f7f807f7f777f7f647fd59d8180167fb5808f807fb4ea80d080808080806c7f807f7fec7ff7802380b87fa68080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f807f7f80867f80808080804980808080800080545c80a5ca010f0a01377f80dc7f807f7f807f7f800a7f8080808080ab808080807fe9117f7f7f7f7f267f7f7f7f7f1a7f7f7fde660c7f7f417f7f4ecbb0ddeb7f80f564f77f7f7f7f7f7ff37fbc7f6ef17f7f7f7f7f7f808080803580808080801c805f7f7fb88080c1edeefa247f80a180c48080808080ffa3808080e380df56db8b807f697f7f587f7f7f7fa00908b0b2eab9f8de4726807f2080808080fc8080289aa77f0d7480,
      4096'hb6d38080809f80807f7f7f7f7f7f7f7f7f805235ae802f8fe17fc080802b8080a5808038ed0041809fd7fe32287f7fe3c27f7f7f7fdb10807f017f49547f7f147f7f657f7ff87f60544a2b637f7f7f7f8080808080e98080808080808080808080807f7f7f567f7f7f7f7f7f7f807f7f807f7f1f218080bb8080bf8080a480801380db7f7faa297f798f7f7f7f7f7f7f7f5d7f6a147f7f7fb880808080f726be058080be808080808080808080808080809f80808080808080c991a6808080808080809f808080808080808080807f7f7f7c7f7f7f7f7fe080889acf807f5a7fb380aa8084a480808a8080808080807f7f7f8080808080809f80807f431a57a7fb7f7f60d3eae9d3f5f6f4c7fb80d8a8510c8280c6f933808c1680807fe0dc808080808080b0f4447e7f7f7f7f7f7f7f7f808080808064800771808080b680809986f6a1990868ded03aa045298075da80637f7f7f80cc807f5c7d7fe33a7f9a7f7fab7f7f487f7fc7ac7080807f434e808080ca8ea8f580808080809580808095807f7f7f287f7f7f7f7f4f273c7f7f7f7f7f7f80f49c80809b8080808080808080e95b7f7f80b37fe8257f5b7f7f7f7f7f7f7f7f7f7f7f809380e88c800431368080808080cb808080808080808a15e1df7fb280e68080a2adaa968080808080bb7f71398080dc8080808080807ff9f97f80a17f3c427fa7817f80807f7f15
    }),
    .CHANNEL_BETAS(512'h757e7950780c784974a3780576da7b5872aa6b9675c6702473b0770b72bf6591747979b4750f6fb376e376586d37741d785c77e674b073c079456d5167e671bb),
    .CHANNEL_THRESHOLDS(512'h01a6019302a9021d01d3027b01ed01d801e00231016102aa01f9018201e1020601e7018602ae01c4021501b502420195018e01bf018f023a017001f601e501c3),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_enc1_standard (
    .clk,
    .reset,
    .in_valid(e_5_valid),
    .in_ready(e_5_ready),
    .in_payload(e_5_payload),
    .in_completion(e_5_completion),
    .in_bin_tag(e_5_bin_tag),
    .out_valid(n_enc1_standard_valid),
    .out_ready(n_enc1_standard_ready),
    .out_payload(n_enc1_standard_payload),
    .out_completion(n_enc1_standard_completion),
    .out_bin_tag(n_enc1_standard_bin_tag),
    .actor_error_o(error_actor_enc1_standard),
    .initialization_done_o(initialized_actor_enc1_standard)
  );
  logic error_actor_enc1_extra_depthwise;
  logic initialized_actor_enc1_extra_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(32),
    .OUTPUT_CHANNELS(32),
    .GROUPS(32),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(4),
    .OUTPUT_HEIGHT(4),
    .KERNEL_WEIGHTS(2304'h3f366f00e8122827547f3f3066d1287f011a31023314e5010e07187f7f7f2a7f4ed247fd9b4545ff7f2480378048105423ea2733f3271c0c2f1f03110d1d47130a1c0b09102a2237024029e12b13f9d48016f51909da0129f43e7f7f7f593ffb567f6530fd23e6d20e33f239cb4ff2c5122d839f80b2028f1a00eb0e193bc47880ed7f20806fa07f7f481d7fc18031804022237dfc2e7f3e46808c8feef5e04f57237f067fc8dce81bfd1180bebde601023334247b7f7c5c0bf6f2140c2011600ec9e5d903f95cde57fcb9d62aed477f291630c91414f32931282ff8461b80b58043415726020b6c0d4f3917360a1309d9dae71c0b15fcd9071906118080808080808080ab2e2f3f2319242c284a7f191244ab0914f21380808080809680ac7f),
    .CHANNEL_BETAS(512'h78af789e777b794078fe790d764f7a11789579d877fc7af3768f796a781f798e796577cd7a55793078ac77fd77d47a047aa67998788c77927bd979de79977a6f),
    .CHANNEL_THRESHOLDS(512'h022101bc024601f701a3029102410284022f025101de0265020f0204019a01f7023101e5026a022502320224026201a901e6028e020502230235027601ce01e3),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_enc1_extra_depthwise (
    .clk,
    .reset,
    .in_valid(e_8_valid),
    .in_ready(e_8_ready),
    .in_payload(e_8_payload),
    .in_completion(e_8_completion),
    .in_bin_tag(e_8_bin_tag),
    .out_valid(n_enc1_extra_depthwise_valid),
    .out_ready(n_enc1_extra_depthwise_ready),
    .out_payload(n_enc1_extra_depthwise_payload),
    .out_completion(n_enc1_extra_depthwise_completion),
    .out_bin_tag(n_enc1_extra_depthwise_bin_tag),
    .actor_error_o(error_actor_enc1_extra_depthwise),
    .initialization_done_o(initialized_actor_enc1_extra_depthwise)
  );
  logic error_actor_enc1_extra_pointwise;
  logic initialized_actor_enc1_extra_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(32),
    .OUTPUT_CHANNELS(32),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(4),
    .OUTPUT_HEIGHT(4),
    .KERNEL_WEIGHTS({
      4096'hfff4971705f62713cfde01e3e0d8100d0a0aeffa2417e3f0d4f6f4cbf8df05f6d87f80114680808d7f8031807f7f7f7f3f40c3801942807f1d1d226737c0468034337f957980ea804a34807f7b850bf68028c1417f80ead37f806b7ffbb5227fdf1f00807f808080c8053ce7800b7f82807f808080ba6c806f7f7f7f007f807fe28a80e2ca7fc57ff6e54fbd803e34a77f80c24aea77d854cf12c9802280ddbc5495d390997ff97a2ec3b2038080add27f7f80c024e48080f85c75550fe3807f04b180804efc819c127fad5338ad80fa8000540a9fe47fc5b2d01280e2ef7a80e080a0d6969d1d43800880d580d083800a1680c480f2008082ea4b3b19cab9bfdf9080808081f5339e7f80368f98b580a89480a1801c58258072248116805c806e80ddde807f7f7fd37f807f80158080f480bd42fa047fb4367f8080fe80228080e3807f7f80808075807f807f917f7f7f8096806fa4807f0f80b276a68061834c9680a0807f2a60b413a4f5ab8480803680e070b40cca0cc843099a0fb0ed74bbc4b8ae803c707f4150e707d217a8534bcc16e01adb07ce503211e9fee61980ca7d80fb6580d6b38080248016ce7f7f457f14fb7e8c807f63a5e4e0eeaf309880e30354805f978080fa806d8080808080807f8080807f54808080d0e3807f9480806d55807abc8380de897f8080808080817f8093807f29808080802b80b880,
      4096'hdef41cd1e1dade14ef050416de2adbe629dffdebeb12e2f0fbfe11ef0512dbd9ed7f80f37f80d4bc43802c8072e27f7f593804af6733807f018150bfd1e74b8010ec1cf8de7fbd7f30b3d5dc35dc1d51c67f51ef7fb680ba2d801efa0995d20880ecb1baae1c808080887f7780b980d080807f807f80ff7f809580a7d2800e8080313480aa80808005b6285c241c5303c380b2806a6f80807f80ec630ed980847f7f7f808022807f7f7f7b80802f7fe67f7f80b3807f0680807f7f7f087f808021a7c7778049ad808007807f80bc80808090ec8080a57ffd80bd127fe0805180012b80007fed808082807fa80980808080f37f0e7f87c37f80b48080d3807f80ab7e80db7f80e695f4801a803fd37f7f316d72b17f3c807f3d80adc6bb802c807f7c95a1807f7f7f7f7fb980194b4b7f7f7f807f807f80807f7f7fdc0e7f807f4aff25000b45dda31cf08c01be7f45ff637f8047cfd4bc808055e9d8062d9f0e80c7350dcdd92e904c9c77ecfa3f7f1c70c486807f3780ec1741af6e079ef580a07f0c80dc80808081802d807f0a7f067f69fda23f5780737f097f7fe4cf228055b00f804480807f80f0c998807f7f7f7f7f800fd2ca8080807f761ad07f8080f8809518807fedac80b88b7f8080808080807f809f8045488080808019808c80b08f807f806a088080e1807f8080808080807f807780697f8080808008803d80
    }),
    .CHANNEL_BETAS(512'h77f176a7761d7596767675c375db77e07211728475ca7560756877b1736b6dc976d177be76a47045768472607549758276a3750b786576e2756f77796bd36bc8),
    .CHANNEL_THRESHOLDS(512'h01ad01b301f801ee01ea0211020401f70252021301b90242022301cc0207023a01f401c0027a01e201ee01ca022001c801a901f201e3023201ad01e30244022b),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_enc1_extra_pointwise (
    .clk,
    .reset,
    .in_valid(e_10_valid),
    .in_ready(e_10_ready),
    .in_payload(e_10_payload),
    .in_completion(e_10_completion),
    .in_bin_tag(e_10_bin_tag),
    .out_valid(n_enc1_extra_pointwise_valid),
    .out_ready(n_enc1_extra_pointwise_ready),
    .out_payload(n_enc1_extra_pointwise_payload),
    .out_completion(n_enc1_extra_pointwise_completion),
    .out_bin_tag(n_enc1_extra_pointwise_bin_tag),
    .actor_error_o(error_actor_enc1_extra_pointwise),
    .initialization_done_o(initialized_actor_enc1_extra_pointwise)
  );
  logic error_actor_down2_standard;
  logic initialized_actor_down2_standard;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(32),
    .OUTPUT_CHANNELS(64),
    .GROUPS(1),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(2),
    .STRIDE_Y(2),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'h32310ef81b030f280dfff8e705e6eeddddde0731094b49060f1d06d7eae2d1e2d5fdecf2d7b8cee5c3d2e1d3dffaf715fafdfd01ebe42dfd012ffc0222f5f72706e2fde6c2f7d0b636f8093b041834f8f3200c022003ec0edada10e2dc23e1e707daece4dcd2eeead2edf2f716f6fd28f0e018dbdb06e3dafef5eeecf0d718dfe32802001adff50af9f72c13032b0804f7f5f2d7e3edebdd01edd1cbe5d0d7d1d9ceeb0d03080e0bed02f805e2e92305080cf0ef1d07fc1afae4e2e0eb01f2cee1dfcfe2dfc81aebea2003fb0af1e418e8d31bfee40be1eb2bf7f519e6f8f5f3e2ebdcf5bcc4e4cfb0d6eeecdd02e8d40de5dd2d15ef25ebed230efb1de6ef09d1dc0ed2bfded1cbc3f2ebb5b9ea27e6e121f9f433fbe217e2e12ceae727e9daed1c200b19102f170ff7ebb20cd2ce13dcd51f2af11e05df02e1b20afbf108f8ed1c06e919ff180b01f824fcf0240c295641213b252d30360d1efcf517f0e43c2a393e104a4112150ee7f3faf7e0f0d5d84b3616331aec27fbcd03fb9f0cfcb32618a625e30909e7effcdefb412d103b0fdb1cf5c007e9cdfdd8e0130ee920dde307ffce03c6affadfeae8d9e10cc2cbe1f71aaddbf0bdf70edbcfc4f9d8c4feeed11ddec823e4c417acbd21fcd52ad1a915efb3eb01032034fb1f14e804d3f3fcf4e50a09f5330901fafedaf2bbbd390fbe21f2ab2704b207cdb3fdad8c02d6,
      4096'hbc4015003e0d014c0ef6f8d3e0100a1b13110e3205ed15a2d705b1c608e8c213ecbb23f5c3cde6e4fe05ff2100ec1fe6edf0ccd207c3c7fdbeecf6b7aff7b2c4fcfb08f704faf5faf6ebf203e6f9f5daeefb020c17040d1006fc20041609f2ff15e7fd11f5f7f8f0eefaeff1f80512f5050400fe0508020105f1fd15e4ec040e110c05060bf1f3f901100ff5fb00edf202160a16fa0719f6fa05edfd0ee80608e2f2fcff0b08f8030aff010704f301f7f808ecedf8f7f310ecfaf7e2f203eb0103e9f200f1f50602030bfdfdfff9f801fc09f80308fbfdf7f6dcf108d8ebf1cee6f6081210030d05010313f5fe12fbfc11f3fd0ff4fcfff000f2f303f5fa00ff040910e3f00d090416fd050e05f303f50814e8ff0fe8f105ed0413eff9ffe2f5fcfff607ed00fdd9f30bfafbf9e6f207eef40504fe1205100ffd0510ebfc03e500f0dcf2f602f6fdfbfefdf4f2fb050a08f2f3f5eaf8fdfaff07f4f6ffebee00c001e3e6eedad2ecf9dde6f1e4d6e3e7e9ed0a17220bf602fdee10f7220bea01f2ea4433192d2e190f1b0d1e1cd3deece4e5defdfaf1e8fc07fee0f2e7fb01322739020a190b1c174130431c173d1e1b3d1a23370b0e2004ec29c5dccbfa10e4fc00e03b3a44190b39f52d4022203d08fa0a05fb19a5cacea7d0c7c9d6a8121c29190b040d150d0b034bf7073b0de92e11fbf6e4efdeffe6e9edf101deeeecea,
      4096'hf4f945341429042218192a19462403171e0afa0ff50fe0d4f2f4ffeeea12fefd08ddfdffe8e619403e10233c22403dfb0615e1f010e6ed00e8f0fce3dde1deeeec2410f20e00e904fdfde9dee5d6e3d9ca00fa33363412e603fd0302d2e2d5d5f4e4cdc1ded2e5fbacc3dcc1b4c00c2a591a13241b0f25fe02120cf3020be904fb0f071c1a08f601faf0ebf3ece5ef07fd0203fe120a0c24110d1ecdd5c1d4d8ddc7efd7ced7d6c8e5e3d3ddc7effdebeb01f9d7f2dbe6d8e8e4e6fddacdd2d0d9d8c7e6ddb0c4d3f3ea01fde70ed9d5f2c8c2bacfced7b7afb5f5ebe8f4ecf20fedf9e6f1efd8f3f1c9d2d6dddedbe7e1e4c5bdd0e1f2fbefe7effcf6f9e5cadbe6e4fadecec3f9ddd917e001f6e0def2f8ebebf3e1c8ddb9e5fdf6f4fdfe0b00fbc7a0d7e09acef5a2bb05fe0a11020c110407dde3efe706f2f1e4f8cee7ded8dceed2cbd1e2e8ea11f2f8f4eaecebd9dbf6dfe300f0f1f4f8fef9f40210fc09bfb2badcd1c9e1d6d908040410fdfa0802fdf8f718293537101817e7eafde5e0eaf4f3e70e1721ff1e1209fd06e1d8d0dfd7dedcc4b7e3e1d0f4e1d7e1dac7eceedef702ef0afb04f8f6f0f1e3eae3e8e6edefe4dfebe2e2e0d81019031d151de7e8e00d0805251614f3faf9f5e5f4f0fbf7f2f2fcf4f2f0121a20e1f2ef0e0e0d0d0e05eeecf907171309170de9fe03f5fdf5080f10e9f3e5040407150905,
      4096'hf3fcf411210c152411e4faff0e04000b1004eef7efeadad809f8f0eeecef0d1211160909fbfaedf70708ebfd02f90405fd0101edfb04d0e7dd09fe00f9f4f3ebe4f4ea0704ecf102e4f506071b170f0c0303fdeaf3ed05ede5e6fd06f60505fe23211bdde7f4ebebf2fe0311eef301e5f7f8fb00ece7f4d7dee6e6efe8f3eae0eeefe6e8edf1f2e2e1e90a09040f1618090a020d0c110afb0aedf105eafbf3f5e8efebebf2fce6f214171edcd8eb0308fff2f7e9eff5e318170e00fe03fcf6ed0dfefe12fb13050d16f0f2fbeceef9efeaf50cf6f905f8ffe1e7d411fe01160b14fbf9fc1c1f18121c25021718fbfeff321617180909fdf900fd0909e9e7012c2b211d1505060412110a0df3f2f9f5fefb0e0a1c0b1124f3010df6fc1203f607f7fd1c0604fe0804fcf0dfef02020cf7fc0ef3f9fecfd2c7cbd1dfcfd4e1fbff03ebf908f8fe0901f5ee01e9f711f8fff701fbfcefed0e0427f9f5fbf4f3040507070a1612131823fc08f9f502e8f8e9efeff2000a0b1409fe0af0fdf4211a1f0c0e0b001511f9effdeff403e2e7f7d4e3e2dbcaeee0e4fef0f002e7ebfef00104f4eef9ebeef3dae0f8110cfc080d0f07020d29252400012004001aeff8f5f2f808f50b05e4d4cbeeddcce7e1dcf8f8faeeeef503faf5060f0cfa03030f0109e0dbc0a2a4bd808080272f08122742fe0e34e4f0f7fb1ee90e2e06c9c8a2a7e0,
      4096'hcea7d8ca0c05251b14fb0111eb06f6e1e9eecfd5efbbedfbab1cecd2e2e4f08080a99ad7c6a5a68f443f204a5e46273233ccd9bdead9c9d2d2cd1d261f2d3e1c1a1015dfd3d2dbf9c1f306cbdeecdfff0ddffa02e6ef03f7e2ec06d0cdf6dbd9caf1ecd3f0e2cd08100df21301dce6fd7f5e154e5d65507b43f90906080506e6eaeabcb295f601c41429d020180f1b2a2c1d100ce11f230d111f07e40ceed5d0e7eee7d4ac9705080b293e24282f1ff0edd4f9d5dee7f6dcd2c5c9ebdde1e3e2dbebf7edd4f4d4c9d8c17f747f5f6f6338431f1236454c4e6d5d5650e8ff0c0e1c2e1def0efd14ff440eed0ae0dce805e2daffeae0e1da17281d080e0d1224fcfbf6fcfcfdfd0307fbe7f7e4f7f2f4e6e9e9d7ecd8f0eceadfe3d6eaeae6e9eaebddecd4f0eee7eff6f1eff3f5f1f0fdfdf4f6fffcebe8ebe5e8f8eaf2f4d800fbfafbff03070009f1f9f2f7fbfaf0faf5d8e2d7e6efeeecece4e1f0e3eaecefe7eceaf3f5eceaf6f9edf2f8e5e8f1eef0eff3f5e9eaf8e1e9edf2e8ede7e7f4efec03f4fcfcf2f2f9e9f900edf8f9ed0100060102000305fef3f7e6f500eeebf2eae4d8cfedf0e8f7edd4eef0def802f5f303f705f8f10202f8fcf6f9f6f0edf6f5f5effce8e6f2eff1fcf8f3fbfbe6ebd4f1f2e6e9eaece9f1dcf1f2e6dee8e7e8dacdebebeef0f0df00faf9f9faf9eaf5ebe4e8e1f3fef0f3f6feedefdeed,
      4096'hebf0e1e5e6f2edf3f8f5f4f2f7f0f1f0f0fbf6eef7fcf200fbf3fa060003fdf909d9becdd1d5e5e4e0d7e705c9e2e6d5d8e82e15f52121fb080f0b0ce51c01f101fffd03eaf7f3e7e5f5f3f1f1edd8dff4d3e0e1d9d1f3e3fdf2da09ecf2f7290c1af9f5f7ebd5dc0bf4030706fef80c0f0907fcfbfcfdfa0801c0ccd6d2ccc5dbeacd08fb1208f3051a0e1904f1faece109e8f3f5e0d1c3e3c2baf4d1bc0f010911fe1a0f0d1800f402090b23f51828dfcfdacad7e9cbd00adce2eae4dae0e3dfeb26392e1e1d1c26321909072402f81d0b133c0c0a06f3f101101bf617dcf0ff00e7f209eef1fafbf0f1f0edf8fcf3f3f8f3eef303dcfbf7e2f5e8e0f8ebd1e5d5d1b0d9bdb6dfc49ce1f1d7e0dae5effaf44d342c2d1b0c1b1604d3dfd6e7e6e2d0cee2ddd8b0d2b0aed5c7c3fad5e9fae311faf719e7e2e9d9e2f9e2ef02fdfaeffb1d06f20703f501e5f6e9e100f3e4321e2d2a1b32262d260c0bf107f4160f1411cdc0bad7c4d0c0cdabd2c9aad5e9eedbcbe232130b0bf8fa1af8010a08de0e01c9e1e9cb2111e71706fd2710e3fcf6ed15f6df14f0d80affe30e0efe1c2af6e2f4d90a0ffd0902f711f5e313fdda22f4cc1b0fff1e0bf12d09ef290800201bf51d0a01390b0e33082f3a182bc4d9f8e9d2acc3dacae0e8d6edeed5f3efdb0de61632d8031ce7022703f23200fa1e0b02f70d06dbcb16f9f2fed7c0a9,
      4096'hd1d0a0fcbca5522dff2f20062f140c2503f522fffc341d0605e2ec07d7e803ebdee6ddd2e8ddc9f7d9c603060208f9e52514fef708fafe0ae80102e403dee8f2e1f20ee2d5120523fb20f70c11ef2605fa25fcfb2001151beee710e3fc0af6efd6b2c2fcecf6bb01ebefcbd9f4f2f4d1dbdb17fc201e0d3534100cdfbcb3ffcec201e1def3baa0cddbc0dad6b3bbaf87d2e4c50ebba5f7fd0f0bf1f5fa0a00abb9c0a3969f90b89b25fcec2810fd42261e18fd0ef7f60d1d1312f9dcd1ecd2cbdad0b95c4e22716f26656c2e01f4091614151f0b06ddd4e2fad6cbc9d8c8250d01200a1433190f754a47684a456b5a5212efd703f6cd000dceece3e7ecede9f6f0f0f117d829270b015a1a3923302d123f4d3644def2d0daccdfd6d7cecdf2e5e202c7f3b4d8606c1b5b5b345e47413507143613183515251cf8e51115f70412fbbed6e0b2ddc8b5ceb4d0adb8ccd3d204fdf8fbddcd0804e2fcd9aaedcadefee4d7e3b7d885968c83a68b86938d3c1d39472f2d5c3139110b05230c11251326e8eae2f7f30f07240d111b170df0020f0c0db9dcc9b5d2dcadc7bf1a2df21629e218f3ed202406303d2459441402dbcbf4f1c102f7e6cfcec4eae7cae2cbb7250f273d282e2f302d2001fd1f280e231d21d8bbb8fde4eddae1dc0d0d0ef3ddf5f2f9fbddf9e30408eb02000ef1ede10cfdf7081909e2ff0bf3f102e206130421,
      4096'h09f03b301938232c31100a361b0b3b260b06ed090905f60a29142e1c2b161734332bdcf0e11b1b0bf3fbda032a151d241fff3d1e06f70510edf7fae005e4e8edfbf3dc1305e0ddfcdef612f5fc291b1812060dfe08f81a24212d253d23223a513ec3dfeadfe3dcf1edd23533253c372839382aec02eef81e05e1e405f5fc18ded9f9f1fcf7eeecff0915080406120b1bf70d321309411f28350e2f5530364e2903fbeee2d7ebffd6dff8f3fcfe0c0f0201faeff3ef0c11f00201e3ec21e6f30bddf2f4e21309111f111b06fe01f1fcdf0e11fadfdee1dec7d9e1f6ebdaedf6275d304e6663495d57241aff0413030a0ff0e1cfd0f3eee0e5e2d3f4001920ec23231712f3f0cafef3d2e3ecd9f602fd000b0df1fffee8daecfee804e5e5efeceb03ecdcefe6e1e1003b1d042c090d14fbdcf2ea09efffe8ebd6fffff406f2fafcf2eb364631453c5746403f1f0f250b0a120e06eef508f9f91c013b081a241403222efd020cf203dabdf2dbb2d7cbadfee906fee7f5f0e2e6080c050b0b0e0a05ffcbc0c6c4c9c3c2beb90f1e0e110a00180b043a2f3c413e454a2f5f21151c0efc0d0d050ef0f8e00908e6e7f5d90501fc020df8f900e30f23140703100e06042207efeceeba03f4dff5eeda07e7b3e0b1907f62597f33147f3812339c9e009380eeae80e1f6d7f4e3a8ecc0b9e00b0db9090ebbefd541cbd236c0d4f9b8cc30,
      4096'h0bf4a2bd0999d2c70b06eb2be7d421efbb3cf2fd06b6b10b9eb983d0bac5e1ccabc99c7f364c6f1c3d7ff73e02e2f2f6adade68eb1f0bfc5abdbebace2a62e08052b0eda1ae9ea4153627f3a357c3141cfc4e5afc4ebe0ecf5a29b8ac4a293a19b8f7e3d5e3ede331ff4641304f32800f730090980a39dcdc680b5e0b61210ddaadbd8e9cdb47f4f757f32197f561b10e7eb1ee5dc16d0e4a0b1cda0bdc081aeaa0206eaa3a58d8b8c80d88593c588acef9ea447696d112734b2c7f0dbc8d6c7cfc5d9b688a28c9c9180ad8fb1801bf4f12307ec24fefa0ed8ef0ee9d0f4c3b5f4f9d4eef9ffc9c2c31a1b1f1e170d0e0b26ee220d182a380d281c0d17e8e8f2f10013f2d4c9bae0d6cfcbb6b9abb5c0d3b6a4b3a3982c40f820fffdea0b161301e4edd2b780a7963106fdec22f3f3f9e2d5ecc6d6d7d1b8c1b834201a32150724140ddbe2b0b5daf080b4cf0aeafa0bf2eedc00e2271d3222211206281fc6a3e3aec6e0d0dfcdeab1f9ccf2ecc9f5fe13e3c8d9d9d9f9bbc337241a0e161308091920d5f03bf107fff1bae6eb0df7fb19ed1411263656423e2f38426ccbf1ddd2d0c4c1b6c9bbcde5d3e1f9c7d5edfffc03fcfd14f9f6000a1625ff09fd0a0504dbe2e0e4dcc7ccd1d1061733181024ff11074047293943343d46500bfd2000faffe7180edae20ee8f315e0eff2e6ccb4beccd9c7e8d7eacbf0ddc8f9effff0,
      4096'h0605d6fb2a11161b155025066310084e0410bbb1ecc7bdcbc1b29e2936f84d45ee0d38ea2e1c216cf6027f0519ecb9bd18c2cf3911fdd7c18002d39306cd8b102836487c7f53757a35eeeb6319ce3c24d9ccbfa51cdab40edcaa3c00e13503ee2fcaf20bd4c75509e87f170906e9b04608dd13e6c93115175414e829ffe716f7b3681fd32b18c56b3e0a7f58fa4436027f74557f7f717f67637f381d7f3216722a0315dff340fdee54f2d7183ee96245005c3b1aefc7cefb04bcf1e1c71bfbe05f4ffd4128f0e5d6da2415da2623c93a04004311fa2bee084a1c1f66fd024eeb22eee6d80bfdd2fce099632bd37c7ad23144d6f9e5f85b1b2068030423390bfae208ffe1f20900104b61114a583c2510e27137e76820dc4113037a301b4b190b3f080004fde713eae0cfc1e7bea0aecd8aac7f46437472187f69270ba1f921d94efaae09d0e5cfd8e2cadae2cee5b3ecdfd9d303f8b1eeda00eff5030c0610ffcc2103dfe726ebcd38f3080ddbf70ffd17eab4c6eacdd9eafced8080a18087c78080aa2236e739542e7f5c35d2a8bbcbd4dde6ebf5ec9ed7bcdee2e3b8c92e19f12a1100212c317f7f797f7f7f7f7f7f8080809e8082be82ababa5a2afa59ca3a09f1bdfd721f2d47f1d373038f53f31162244f7bdb6dfa59f8085abb0b59efcefbddbcdad937f7f5d7f7a697f6d57dac9c4f0e2e4edd7bddcbb08cfe4fbb8ce,
      4096'h189f80808d8080808088e113e0f2f10121f8fe9ac58080e295cbe1a3aecaaad7cba1e9bfa89d9d808080808080804d52246e40196c5f2334341b1508fd1b240fd6c7cbb9b7e9b6b8c61b1d041d1e0a201d16ede6d3ccbdcbabc3ddb8c0dac3d8d3cddedfdcf7de00feebedf0fcd2e6bee9e1b7cdc3d408f9f5f0fdf4ea02f3f0dbea0ad7eefdd7e5f8c8f0dedce3dcf3e5dde4d5dbe0c9afedcd513d333738153126030d01e515020dfbffd8d6f0f0def1d2e0dcf2141f20101b10131922e5eaf7dad9f9d8e2f2f8fefceaf6ede3dee61d300b3d2efe21420b141406120c030e0cfbc2d8cabcfdd8f3f9e0e1e70605f617fd08fbc8b6c5f4c9e607d1cde9e7b3dfe4deddcfc8eb1ceae00eecb8d0e1fe09020dfd0b130c08140e0c0605f80b1afff8e5e5eee1d1d6e0db14031af1e8f20afceb1e4e1714400c10fcf8fe2416051d0eef040500eb03e4d8f8d3e9d3f8f00ef5fdf109e8f4fdfefff7f7f8f4ecf014eb0a1f1a0bdeecfdfdf0f3f3fd06b3cad640615a33503f283723fc0429e1cf0dfcbef1df0c25cdeff0cae1fbf22418c80924e108171b23211a2c10193c2514c4c7c39cedb2bcd7f3184d0510430a38462b372c32584822353003fef91025efdaedd0ed252cfb2331f10a190d201c13241e0a3f27ddc8ddbed9bfc5cfe20a291b094c3c1e4029fc1a38fc3d40044041bbccdbfaf4ba1bed15ecf71eec25ecd8,
      4096'heefe393f32273e0dfff9fd1d2f29fd340f0029111147451f2b21f4fe15acd51d8eb0eacbebf02a2f482d40433155461a3d2e213b1efa1602d6e1dfe915f2b7ebd30c02050003ebd0d2e0e4eff8ecc5d2ead1d916152ef7f71ceafa070be7050618fad9c3ececdc01e5d5fcfaeaf3311c300c432d132c38170c31082639212636a598a4caaefcc580b8c1b8bdd8b6ceddb6da51e99e38eecc4c3bb01398d7c6c1d0d6c499edabe1e400044048068080a280808097ab89d6d3d9e6c100f9f6d32b200dee2a4c24514c5237774e2d5f626b72effeee37f318392a249180db9a94e5878bc62c3928491c7a6a1556cfcbf0ffe4dafcf8fdb9a183aa95bfe1ae9e032d1e0d282839332b6f7f7f7f7f7f7f7f5bd51326c2e3f5dcead5c6bcdbd0d8bdcad8ef2ffcb6081dda3a640c68535966215b6b4f48bc8c1eafc0ca8080c3e5bc98f612b5a6c9b07f7f577f7f5b7f7f501afaf420cbfb12dee8c0c5b1aaafb9c1c5dc8180b7a190bf93ab9305b0d5fe0cce3df60ac6b290b3aaa8a49fcfc980bda8ccd598b6018080a78080808084804c6a53584d6465796f353d1d221616354c57e5e8e7f6eee7f9f9f6dfe8e9e2ddeceae6f2b9bcd2d1c101bfbebfe3e7ebd9e1e6e9d9e6e0f1eaeae9f9e3eef4dff0ded2e0e0e0eaece1e2efe4ecfee1e6edd3cadde4e6effaedeaeceb05d8eaf9dfe0fdd6d8f4e2ec00d5f4f6e6e5e0e5deec,
      4096'he5dee7e2e7e1e2e6f4e3eaf3dbd6e7dcf2f7deecfdddebe4efeae9eae1f0eaf40cdbedfcddeae6edf1f7e6d8e9ebe7e5f0fefdefeffcf2eef2d8e3eae0e0e5e5dde6dfd3d5c9dacfe1e0c9dfe2edd0eceac7d8ebf0edf1e7eae2f1ede6e4e8eee3eaf2e3eff2ebf001e7f4fdf2ff03e3f2ece9f5ebe0dbede2e4e4e1dcdae2dae6dae0ddcddbebe4e5f0e0f4f0eaf502edfff5ecee05d8fdf3eef005e2e6eae0d6f5dce4f1e2e2eeeffbf6f1f5f7ecf1ffe6f3f2e1f1f8e7f3fbf1edf0e8f1eae7c8d2a3bd80808080aec2ecdaf1eee717f1223b402e38251c5979d6c08b18e52e1cddd77f707f6c2e566e3f78e30ec41f2c24f30dfb808080808080808080577f7f5d2cf41c23ff7f7f7f7f7f7f7f7f7fb380a6b28fa8ad80b5e9f5200dde2907102df1fefea0a6e1e7da26b687adb0b1a2d3b6e2808080808080808080df8080b78080ebb29c7f7f7f7f7f7f7f7f7f7f766e7f7f7f7f7f7fc8bdcdd1cbb8d4d3e393cbf0a6130a1514143838235133527f7f73467f4d7f7f3f7f7f7f386506554d110c472b7f7f677f605d7f7f7f83809590829be6bae4d6d210c7f0eedfd2cc89a6cbb7b2c880809f385066367f5c482709e84b7e5c607d0d3f7ff1e6de09f0e50fed2b92808097b5808080807670324b7f6c7f7f7f1d13d51829f66a5319fd0dfe0e0b1fe7f6e00813f3ffec06dae9f9f4271c113b21204021cbb8b7c3a8,
      4096'hd2d4aba90e01f90003facef6dbd0ebb9cee193a5d89ac4e1b9c6d2e1becfb2d1c6baddc2c6a3c5a00023e7f91c0ee6f010c4b3a6c2f0c7a1bec0324315260c22fd0925cad8a3bbe0b4a9aab3d9d9b6cedcb9b5cebefd060a04fc1be3e8f6d5e0dcda01de9bd7cae114e8dbfde5dce4f7ec01032126f50027fd1013f10bf3f4d2ee03a4a0a1c8b4b4d3b6f01e1b1e060506defa0ca0deaccdf3cdc6e7b4aaa38ab3d48080b586f9cfedef22ffdccee619240bf7f300d2f6142b1d05160f12e00615c0c2c5d2d3d9bfe5da12f5020e0815efebe82f2a294724691e1c610c0a0d09f61fecdb0911e9ef0401e6e9eecd01edf5f5e5fdc4e1c5edf4edf3e8d4d5d7d7e4e9dde5ece6e4e4dae9e8f2f3eaf0f2ece3e3e2e3dddbe6cae4cdeedbe303dbe7f6d5cde1f401f0ff08e8faf6e3eaefe7f1fae5e1e9e1ebfcf2ebf3f4e7e3e4ecf7e9f5f5e1eaed06faf3230a0b211009f3dd0202e9fef4eee10301f601000004eff5e905f2fe06f8f205f1f0f901f70202f6f1fbf7e4e8f6e6f103e3d9d8efdfecf4ecf6f8e3dd05f7f1fd03e2f1fa1c22181d241916190defddeaf5e0f3f6e2e8daf5e6ebfdf5e0ffe4e6fffcff0309000d0205fffcfaeff4fadeeff6f9efe5f2f9efdfdf0011fe0d10000603eef2ecf5f1eaf1fcf2f309fbf50e09fc08fef1e0dcf9dcdbe5d1c3d2f1faf8f7f901eaf2e8e40e02ef120df3041407f2fe05,
      4096'hf9fd0cfefde4ded0e2dfdadbc6c2f106fbf503feeefff9f001fff909fcf8f7edf2f1f6f5fbf1f1f8e9e1e1d7e9e0e3dbdfd6e1fbedf7fdf601f8f3f0e9e9f0eae4e6d7dce7e7e1e9ede9e0e2e1eaf7e9edf0f0efe9ebe4f1e6f1f2eaefebe8f1e9eef1edecefede9f0f7fafbf9f7f9fdffd4ddd5e9e8e5e1dee4e6eddfeeede3dfdddffbf5f4f2f5e9eef5f3cedfe3e2e0e0e5e0e0e4e6e2e6e7e5dfddc9dbe0e3eae4ecedeaeeeeebedf1fdf80002eefdfffd00faf7fefbf9d9e1d5e9dfe2dadad1e3f1e1f6ecdffaf1ece0e9eaf1f7f8f3f7f2fc01fc0304f6fdf6eaf8eee9f8eae7e2dce1eff9f3fdfef5f8f701e2dadbe2e5dbdee0d3dfe7e0e8e7dfe6e4d8cee1cfdedce6d5ccd5f5f3fafffefaeae4f0ebf9ffff01fb00fb04ecfbf1eff0e9e1e3e4f0f1eff8fbf0e8f0eee5ebedf3f2eafcf5f0e6ece7f8f6edfbf2effc000906070af4fb04f2efeefbf80401fbfccae1dad5f7e4c0eacf140c080d0afdf6faf4f7fa080bfe08f9f9fbe9e5f4f0f4fdf000e703faf00205fef80102020209fdfd0ef7f3070e0707150f120a050af3f6f5060508fbf8fcfdf0f9f9f3f604f901fe03ee05fb010204f301f3f5fffe09f7f7fff8f5e9fff5ecf9fef3f9fdf004fefd0808030efcf80e00fe0d020b02010901faf9060afffdfefd000808fcfe0de1e7d3f200ea01f4e9feede7fbf9f7010807dcf6e7f2edf5ececebf3efec,
      4096'hf2f4f4f3f2edf4fce8070806040005fcedeffbeff8fefbfce7eaf0efedf3f3eef8e2dde4e3f0f2f6f0ea10110e0b0908f9f6f5e9fbeafcf8f9fdf8fdf6e8edfdf9f2fcf9f4faf50704f604f4fbf609fdfa13040a16040f06fe020c0702080703d6afc6f1a8caa18080e0dc07e1df11f1e40747385e7153507f5054d1f8d70ec9a6edb190aaccfaadbae8c581b03f1ee5120bd8a1eac7e6ddcbddd7e1dde6d2d8b2c0b2acb68a988012244c2f04163910360af612edfe0be1d60ee6f404fff3210ee13af8ee14f7cdf0ecc7d4d2e30fdbe701d3e6fe14f9f7ebe6db05cbe02a3137180b1c2400225b644f684d5a7f6d685420123e0c2a08061fefe310d2d7f9dcd7ec22162b19052b1d0b4f352a432e1f434f294898c5d2dbb7f1a0ccb3c2fafbe31bdab5aeaf25381a1f2812363828130d1d270d2a360d3cf00b0adedbfbe9df0896a6dd96a3bc80849cf2d2f7f6d1e1d7d2a3eced23e4faf3eff21dd5ef00f1def6e7cfe0aed6dc80bbf680aa9f362a4d2236253f2e3818191a04fe0b09f30e202f202d3536353e41f9fd0cf20803020a0fe0cadcf9e2e7e2e3e1f30a0703fefd0c0311eefdf00704000402f2ff100e10250c0d19fffbeee402f5ff000afa14211a2b2d2e3a2f28dde8e3e7f0ddebeefff3fef6f900edf9f5f8ff03fb00ff03fb040be8f6f3fd01080d0a03ebfb010707fbfcfcf902130f000205060a0cfa00,
      4096'hfc06150afc0b04e9edfbf8060704011afef6f4edf6f7fcedf5fb0107f5fdfcfc0601f8f9f91918110d0d12f7f8f7f6f3f403f6f8060d11f6fef8f40f0fff071106ff0b1002fdd4e5d4fff7e4010bfc0414080201010515100308fcfe00fe040604fef9fdfaf3010804ffef000905020dfffb16e6dfbfdef7d8eaf7e9f30408ed0300fb0202e5f304f1020bf8f302f2fe03eff604f4faf4fdfef70bfb0304050121e0b12361181024b4482f165e5818633b04e9c386f5e386caa880f411ca273edc20fecaf6d6f12ffdef27f3e9dfe2ede110fa2cfa1c8bc2a3b6b18bbfc289e3fd071b5063574b49f103eb01f4f42bffcab3c7acf500c9fdffb9d6190beee924ede404ccc4bfefd5d1250395d9f1e5efefd91b06d405f3c52f0bc5311ec5e4bcb308d1d00ec4a102fce20af2d22807d26a4a12637b2d5d57601d12ef4e2bfa3727f214dfe02c06e03b090302f1ef1807f42915e6dcdad1224f56f1f0f4bedaf6031c0014f3dab7bfddccd2c500c7acc0dfdeede3f6f8e8c81ef4f64910fe3021faed10fc2b2ee50b2dec1ef5c136039c1dea8ddfeab95721f75142e50b13ff442df74f21f827ebe978342611f4de1cf5d84320db4bf3c30de4dd0fdec811f1b6c8bf8fe604aca1ab80c5d7c4a4aae7aab3c77f7f7f737c7f68747f80a1809cdc9f83cd80f7d400cab7c1d4c0a339f4eae1ef39f2edf2d8cdc6c5c9c1afb0cca1,
      4096'ha3cda380808080ba6d574e364a3d372a240f080cfccdece1e4e2dbfff89d84cd8d8380352f404ee52222112df3f903e5e2bdbbcdbcbc809e8faf89b79b98446c4c4b333b40260d627f7f76795c7f78513335262c4538365c33b8bbbbb4b8aeadb5a4184d38302e1564171c7f42677f2d23604c418589a9808080808080bb97b7c58e808e80805774785a704b556129d6d4c9bbaebecbd9bd10d9e0decdd0c7a9bd80808e808080808080b2f2e9abdfccccbed0e4cca8d79e8ffaa2c6d5cec9c09f8ea9808080aaba8080a48080807f7f7f7f75437f675f3661323f19ee380fdde4122ee7220003e3b0f5cbd1e2b9aff5c9a13031634350292b19203cf73b4b14331be805f318d605f6e9e9de9eecfc12fffd3412160f3def1023eff712f80d4c3e1e191bdc0f01e321e2de10d5eb17e90236010927fa093ff910eee6d106f2e3f7e8cd301736311c1d1809fb26fcfb21ebf022d7e02bf7f738f6d307f3b707c6e20fded60fdfe43eecf432e8f74cfd0058ff1c31d607fdbbcae6c9b7febcb5dcb39b042a7ffe1c52f4323127f7e126f2e63303fb58001e771258171c3f04193402f5f8d1d0ac39f40c35fae7480af71ff6f01f10fa2ef6fb2a1fdb35f1e818e9d92708073a20010909daddae95cfaf80d6c89211500d2c2cd9293dcafae6ce26e2cdefdeb211c1f2edadb4c8818023e70014e6f72cf0010ce2e407d6e009e5d5,
      4096'h0bf6f93b19302b3838162a07313a29364539c7a2cee0d2ebe8e1cdf2f5d10205f91bf10aef0ff6f1170d32301aff0ef91619170a2012d8cccfedf2b2f1decddedeecedfcff1214f8f1fbf0fd06e4182002bed3bee3efd80404e70f20011e200a1b1b13cdb9eafacbe8140609d3dccd06fbf2f0f9e9e80cf804010d2b2c25d4dec9f1f4e1fde6e8fdcfcefa0fe90b0e21242bf0233938091619fe0ef70f1a19322920c19fb2edf9e2fc0c06ef0bfb0815120d2d14bdc8a905f9d5ff08dac6fcf1e116fe0d0c1bd2bcecec1efefa0e1ff8f3ecfe0efe1d1d19fa1bec1a2e1837381fe5f3e2ec02f0e902e9abc4b9cdd7b7ced3d5a6c3bbd4e8e8d4fee90f1800252d0325382f002009223515132512e90de2fc2af400fffcdae6de0e13fa1a09093d1e3c0c024a19100bc9c5b9bfb3a8f9e0ebcccbf1d20115c6d1240f0306cff31cf9033b0a12211cf24c4c5e4a1a2d431a15247855463e3d2802271f550928576f4a3b2e1b723a68d8cbf8b2cff2b0a4f00a151322022e1f0f59d506da0d00d0fad3df5b5b5f291e1d592c4ff9ef0b1f1f412a3c43bfbfd7e0e1f3f6eff2808080a0a59597d19183808080a589808085cec0f40e2b194b6466d4dbccecefd806fbfeecbad1c7cbe8afdcdd808080808e8cc4c9c51a0fd1ee3cd32344eb3a2f562d1c4771536b0a2823e80b4cc8e91f808080809980b2b5bc808180bfab9a07cf,
      4096'hb21d0f1d5f64607f6c60d0ccc9b8bcb6d4c8e33a6c4bfe192004fedbd9e8a7e8bebcffdfd54a403e66fb6378377fa5bd97afc6a79bbdc780808080b99a80a0b327202120172c0fe80f040eec1ffff7fef7ebe707fc46212f2a27f60af0ecf4d2fce8b900d3cfd0dfdad3b8c6b4e206f7f1e8dfdcd9d711e6d909dcef00eedffaced6ecc1dcc9b5c2f1f7f8ebebf3ebe3edfafed702fcd3ecddcb0e09f82a180e2101e509152b1607090900f600f6d402d6d9edd4d91519142f220d130601fcf1edfce1fdf7e3ee1f070c070a070a121c190ae629f8c4d6d4bfd9f0d0ecdbdad9c8caf012f7442bed290eef24f2fb27ec1c160101cae3f2e0f6e4bed4c2c8e2ffeaded4d7fbc91c133e1cfb351a0a1a2417003110081d0b030c04001feff10de3e3e309e4f5f6c8dad4a103c9f5f3d2f0f0d0dbefecbb00fec3f6e6cc2d1a024215fb330bfdc9d5e6b5a8c6ad9fc61d040709fe0d0af80b1ffc0403f0fcefe9f72110092b1b15fee4e3efebeceae9f0d0e0e1191d1ffefe1bfbf41df3f00ee2f001dde7010a061afd0008e5fc06fc0417f80d22e4171f081318ee03ffe2feff1801fc09f7f8faffefe2daf2ddecf3d6f0ff15212ef90c12f5fd060af7f6eff2ffd5e3f9050209e8fbf9f401fd291d16fe000bfb04fbf1f9f7eef6efe2dcf7f7ff01dafc0ad7ea01f80c02fa0d09f705fcf2e7e7eae8eedbfae6e1def3d8dff2c1,
      4096'hd0dafc0f1af6ff22ea0028e30504edec09e4f80f00e4ebf2eae4faf6ecfb0708f7f601e3fc0df1000af9000ef6010800111ef90811dcf618eeedfceeedf6d2dee2110f2cfde2fde6d704edfce2e8fcfcfb0006381015120bfa1f0105ede5e0d5dceed0d1ddf9f3e4ebe0e1dddae6f5fff8e6fcf2dff5f1ebf702f6ee04f1f308fa0cfc06fffee4f309f7fe07fffbf8fe0affcfe6ebe6ebf7e6efdbef0300030a1001f3fa160c121217140c130efa02faf90601effae7e4eeed0501f7fef5f102f80902010e01ffff090705160c090afffbe2e7e3fbfdf1f1ece6fa071010090b021206e7f803ff04faf301f7fcf1f8050200fd0001f608030d090b0a1403f906f80afdf902faf8160d0a20120b100b09040b0c090001080504040cfe080afd060804e8f2d70c0603fdf8ea0a110417171f0d0a0ff707fb011403030710f70a05f70cfbeff1ebf800f1030a04fffffa050d09fe0a05030f0f0e0c080f05091a070ce3e8e3efeee5f4ebee1919251817100d100efe060d060f120c0d18f8fd04f8f2fa1006f1fbff07f806fef8edef0307fc0e0bfd1004fb1816111d1010110c0eda0001ddf3fa0214011e1507532404532810ddcac2f3d1c4ddd1a65326085037115a4f1714021624f8042f1a201bd8e0fae3bf06d1becfacacfee0c000d5bdfa1d3710384f144a4dfdf3cd0ff9d90ef5cde8cad0f5e0cb00ebc82614122b0214,
      4096'h3f1014f5dac505e9cf1bfddafcf5e60b03e62409d5182501371a00412b121207d72212de1a08d02821df1c16ed2d15f60e263227281517282d3531154015ff4b3506ccb6d9e9d0d616d8b0351a011a2f013527071529f746452e4e3b342f131a281131400e231207e814fee606fbf81a0df32e11f44b101c1b220d290f194d2c120f070f2208131e13f432130429112531292a100cee1e140b10f2ff10130e0dea1b22060bfdfb0110001d2b05051902ebfc11d516f7d43010ef2716fa2e21f3d5f7f6dceae6c2e7d0e5feedf1f9e8f9fbdc1efa0e200c041a02da14f8ea1900df0bf6bdf0e3ea10eef402f6e6eae5000ee8f1f8e8f1fff8d60508cc1310cbcefae4dd02decbe5defafef50b09f31711f0edeed60ffddb0800ddf006fbe1f6e40f07e3e318effe0ae4f004daf4f9e7eff0ce06f5e6fffad6fcf3dce8edd5f50cdf0116dd030fcb111c0a0d2705112bfbf2e3e7f2f2f1e9e9f90804e518ffeb15ffe7d6e411e2e003f00c11f9fdf70e00eb180be70502f5e4e9e3f9e9faf0e7eef3f2fbe2e9dffdeede10fee81100e2f7e8f5ece9d902efd70703ef09f5e40efcdeeff7dc07f4d2f9f5cf221ef7211c071119e907e5f8fce5d302fce4f2f9defefdea05f9e506ffeafe05f2e8ecd7ed0fe3f217dcf40ae0fa0cf80314e80010d8040f0019241e5b4831f2dcdcf1e7e005e7f3fdf4e1ebe4e9f9fddd0000eb2823,
      4096'hff051b010d08013016125b35371d201533241a1c312ca4c4a9c5c6b2d1fedf2d28186c583e3a3055909da9c8aabedfd3eecee9ccfe07e91d160cefd8cae9cdd11e00f324080c33100a452718bdf8c4d9e9d7e6f7ed06f9fd15faf7363916b6b2c3afb0c8d4d7cfa4d6d9c6d8f5cee2d600214914fa1b364741c7c8cce8c5ceefe7e6b5b2a5dec6c7e1ccccc6be9fe5e0bcd8dfc71622f72318e20803fb15081a311419202233c8ebcae5dbd5e3ebf61ae4da01eccf05fde0d7c9e4fee4f51efa01e6e4fe090e0d13121ff1dbe80208fff4f602ddecdcf9e6d60f06ffebe4e9fffef2281b0fe4f0fafbf2150bfd24a3e0cdc6e9e6e3dccea0cdccd1ede0f3ece608000af7f608f4e401e6e5ebe8e9e104e5f0080621fe0f120d152019fb061fedff11f7fd05fddeffffeefcfcd817fceeedeee0ff0fea080c0c170e1016161f030cf30803e202e7e106f7f709f1f80c01f805f5ff0dfe0c00100c111501150afa2c1103fa09fc070ffd1605060801ff0bf5fcfdf9f705fc030ef0000efbf5160715190c182516211510091308171b142306e9d3ef02f5d2daebfaf6f501f1f002ecee0d030df819f1151c061f030916110d1807fef6f1f7feedf1f9f3e3f5f0f3f305eceff8d900fffb02050308130d0b0f071a12102a070705faec0d02ed04fcf5fafaf1f4e6dfeeebe219020918fa06100c16f5fe04f507f5f21405e5eef5ec,
      4096'he8e4fdeffef5f4e8f4f0ebece9f4120108180311140e091704060804070e091003ca07edabb0f3dbc202d1ed10f3eb1e01e831fb355cf2e056f802eedce7f5d0e9e6d0e7cfc1d1efbdb1fce9b8a2c618d9d009e7d9d329d5e469c4dc4ffee4bbb2e2d0bc98cac4cb39ebcc44d0c743f2ec2507e442e7db4901da2f0efa45282442171cd6b5ea15b8e128e2e944d9ca4fdbab35ffb8c8e4dee3e6f800f20739e6f26300f247fbfc31f1fc4fe7095001081ee3f1ccc8b7fac8a7ecb8b8f8bfb6f9cac293b300d3d7bbf1beb735fbf84feef9300109bbd4d9d0d0bbe9a9a3dee1e1bb1db5e5b0804bff01580f10581d123cfefe3ef70329f80326f1f32b150f4c0e1dc8c9fcefb9aee0c1800cd3c807cbb102cfc5b7e1c6ccd6e10609c91edcd924f3d00bcce7c8d2eacbd2b4eac5804df1d4720aef6c160a38ecd447f0cf41f5eff8dddff3f1d7f7dee2f0cddae3e1dbd9c8cceaebf2eceff8e8ebf4efe0dbede3e3d1ddddceced0d0c2cfd9d0d8e0d5d2cfd2d7ced6d4d7f0f6e7f1fef1f9fadae5e1ded4d3e0dddaf5e5f708f3f605f501eefaf2e9eb02eeeffaddced6eeede3d6d9e1fff6f905fbf5060205e8def1e1e8faebe8eee1d9e2ebefe2d6d8dafee6eff9eaf5fef6f60cf2ff01e80210f4051f00ff18fe0514feffddd2d6e3d2d3d1c8cb031505ec08f5f1000af4f7fffef1fdfeeffae8e4e1efe6eeebf0e1dbdbde,
      4096'he3d3e0d2ccd803fb0301f0f407f8f3f7e801efe9fbe8ddeeead8e1ebdfd6e3d5d1bfbfd4c6c8cac5c2cce3dedeeae3e1e1d4ddf1ecf3ece9e9ead4e5efdae8f3f2e7ebdcd7dbe0ddd9e1d8d7dbcbf6e5f0fde1f4f7ee01edd7f0f1e1eaefe0eef203dde2eee3d4da12c8fa06f5f2f4d90cf6001220fd171f031e25e5eed4d7d5e1d9c4edbfebe8c8dce7c7ece8f80303f210f0e4110306f309f3f80deeea16f2fe0ee6d404e30201e7ef13d8edf9e4010be0fdf3e0f5faece9fa0f210d203823132e39de09f1d900f0d90317dcf5fbe3ecffe4ecfaeacfeefff0fbf3fde3f00d1e060e2913161f0f2937122838192d3bdbd0e3c1e6fae0cbd2bccfcbc8c4d5c4c2cf0d161c2129182e5b33f80a13071600111f1fd3dce6d5c5f9f6ded7e4f8ed05fbcceef0d1fb1029080a1c110e1eecfe12030d1608170cef0e1cfc051504281dcfb5b9d8ccd1cbc9c8ecc0b3e2c0b2e1d6dde11317061536ff3b22f5f4dd0de0ecfaf9e7d4d9efe0e3efeee4e9ec0b16f50219fe0b26e50501f80610fd080eee0b16ccd3c0e1fccf0ff309cab1c2d8e1077f7f7f4e3a550b395035505a23fd2e513e3af8fe25b6abe5cab1091b4a0c233264162828775c38eace0bc3e9293e3743f7c2c2ba99d5f3d403a998c4bfa9d45e2d64fff81a2022520520e8dcd4d5f4daef4c4f4cd7de10b0b8051c0614aeb9d09aa6cef1faedd5d7cfc0dbed0ee8,
      4096'h0fc39ed9feca14dccae196a804cd9b0d2d565ad42024b3d912e6d2e5b8b1aec2abe1552949f307fbf3d64810f4fbf7ccf109cfe72e4c1c25353a00312c494c600be0fd31525e47384bdab118dcba41fbfce8191507081304e4c9d8c7aac5d0e0eb7d663a3f324844374ac2c1a680808097baac320621e9d8f2adcef2522e282708082d2653d1f0b68398960e0cfb10dc22f9b7ec09cf15e3cdcccba9d5f8cd0af50001f90d0bf3ebeee8eff0f105fdedf3e910080d20160c1918121802001717000ef8f60c0908100e080c01fc02070700fefff3edeff502f4ff0309f5f2f51b1718111b11131406050800080b0c06fd06050d02020206f9fefdfc0603ff00fffffaf00e1a000d0d060b0c0607090aff0106f0f7feedf5ef00fe0805fbeafe09fe01020afa0008fd0dfd010f0101160102f8010c1010f7f4f8f0f0f3f8f1f0f9e8e51119141e17151826120a0d0f00fb0607ff0ae5f1f3f1f9ea080afa0a10180f150c0109f9fd0907110e0afe0a08fdf3f8fc000001f2ecfd06090c11080704f7f9fd00f602fbe9f2f40afff6f9f3f802fafe08f40a080003150c14e5edf1f2fc00fce7f2fd0100f908f6e8f6edf60cfd010800fe0301f10003f80207ff0301051006040e120cfd0ef8f3f1eff9e9f5f2f7f1eef600fbf9fe0301070404000403000614feffe0fefcec0103fa03e6e203f4f3fbf8e91c1414211a0420081111,
      4096'h050f0d101d12130d040eff0000f602faea0b0f000e08f513fff2f3fcfefff80300f2f4f4e6ed0af6effefbf7091d09110ff70b09fd10fd09f7f803f6fc070909fd0bfdf4fff0f8edfefdf30006edf2f8ef01fbe7f8f5f2f804fe05fb00fdf9fffd02edeaed020802faf4fe060df80fffe60af5f0030dfa180206091a0406fbfb03f3f4f6f5f3f2fe10fc00f5fe010409080b07f7fdf9fcf802faf7f9f3f2eff3f708050407090c0c0c0b0efaf1fff80005f80503faea0b0afa1ef2fb01f4f1eef7f6f5ecf105eef5fcf1f7f803fc0103010afdf7f4f1ef0904fb0801f0fbf6f9dafbf6bc99940a2e1eccbac6e2a8b523f7c3f28080b58080858380d5d1e3efb8dc0dee0b4e25502232676b6b7fe1cb07f3d2164b517f2108415607e11c0b234408172b235855747f15020327fbf63000225a1f4342364c404058808080808080808080545d5a533c4f57333f42255a4a3b6158427fbc97c6c3bce3def300fadbfdd1e202c8f513ef0aad90cef2a68ae7e4ed26f8e72e16245dddd8dbedccecf9fd0a9ca1898e8080808082aae580b5be9da6e89de3f7f880d3bcdeb9eb537f7f7f7f7f7f7f7f695d4a36263a282e3595ac808bbc9980b6808080808080aceaaccf0a2c462b1f455b4340bfb5b480abab98aeb0ac80be8980b080808080858e808e80c5e1c422224336353f7f70750a04ecefe617a7c70ec7b7e9cce1e5c5beef,
      4096'hc4a3e2acc0e18f809b91d0acabbfec8db69c1e39bc5b742e5d3b18b5a880bda4c4cab09ff6fb08b9c117e0bfe1d9dbebed17ceddf6e3f1f532deeb39eaac0bfc0b6b1e6b00feddd77f7f7f7f7f7f7f7f7f4b7f7f407f7f5f4b7f80c0d28ebcd080bf973e322aee247ec5f02f477d7f1a717f1e2b3099ccae9eb4c0808d9d24757f262b7f25424534607c533a6b5e2d403247647f6c5e7f7f6fbde7e3bdecf5a2d7b79f99e100d5d8cbfacc20410f052347e00f2f80808080a98098a591d0eaffd0ebeadcda1a535a7f6f7f7f7f6e7fedffefe6e6dccae9bf84cfbb80bdc5809ac1dc040ae1f1e6acb1b9d9cdeeddafc6908080d7de97bbb7b2989896809a9194cda280818dfbed17c2a4eb808099627d7f74637f767275384d4af81333251f26080f17040d211c18fbf802eb03fdf70800e9fde8ef04f816060c150c0c120a060e1c03feee01eaef01f6f6fbea0501050802f30c16fcf2fdfdfdebf5f7faf8fe0cf50002f1091afde6ebf700fafcf8f5fef5efe300f1fcfcfaff0df9e40b01fd0b09f6fa01fcffedf5f9fbfeede0fdf7f2f0f9eeecf800ee0803ff0003f008f1ec0304f5f901fe08f6f003faf504fcf6eb00f702fb0005fdf4fdf1f103fcf801eeebd3ebcde9fbe7061407f1ebe1fefdeffc09f3fc00eaf2e5f3ece5e6f003f7f9f5f709fcecf4f5ecef0808f705fc00eeec0afef60a00fbfef1e7fef7faffff,
      4096'hea0804fa08fff90dfbedf3eaf2eee1e7e5e8d4defbc5f8f2d0ecfcd71202000b060a1208fef2fae8f9f4fb04f8f2fef7e8fefcf5fefdfa00f3f80307f8fcfff3e51e16f7193519fb0a070b03050313071704d8d7acfcf1d6efdece373b3627293b360b1ed8cfd70ddfe8e0d7c8acd2c4a8e5c1dddaa6f5f8fd2100f1f2e7d5cc95e9d9b1deb0cda10d1ffc22f3f80ef5dcf3e0cc0bfaeefaebd313150b08fe35161044b791b1d3cfaec8c98eebf3001cffeef7fdee05f4fcfffb2213ee0611110e3923233318080409ea1929e607010afcecfadad8ef9897cb23312a231c1f251d1cf502d81f5b11351bf74015083f1f00372e0ac1d3d1dbd8d2c4e4ae92a6a1979c859aad85f6fdbb1ce0b4d9b7a967514366332673514924271e191828312c1de2e226bbd5fdb3d2eb232a1a1417271f16238080808a998680859807e9fd20f8090c03fdc0e5ffaff9f997afe41816331b0c002807fc492e4b5c3729402a1304e8f00d051d293225c2da02bbe2e3c90204db19f4f61120010a1bd80407ec13e0052a06b6ce01bed804abef0fff363bcc0b0fe1331e112d522d2d582c30549cabb9a7dcd6a1d0d2e10803ee011bf50722e00239f0083e030a4588c5d3cebfdbaadfd7ce0d2acc092e010032e20017db0015eafe15e7da16e9cf1f020efdd7fc18de0425fe0503fce32eff0d34fc0536b1bef0c3af02f0e2e498d7f3b8e4ecb0,
      4096'hdce8b7e6fcdbeb0cebf023c0ec17b502eed6e7f1eae5f8e6f20bcbb9bccbe217cbe1e9e4fd0fee0a3ded183604140bd80b28f20411f5061792daf1aae3fea5d3e9e604f9fe0102f4213cb8c7bad2d4afd8ded4b7bccfa4c805c9c6c9cbdf19d3e718f4f0fce808ffe3dfe1f121fee2fd0fcef60fe80e23cbf217d2fd17d2f305ff270b37fc273a211fbfd5dbd2c9e1cee8e86c7f7f4c7f7f547f7feed3f891bcc8a6d8d8eedec2c0cde6a6cbdd391c0f2f0f0d0d173c2b2d530f0e3bfc101a21ff22b3f619cfbdc107122df0fe10eef116304341f41328e80c0b80809ba19ca6b4a8c2556458194d470e543cf8012aebe20feee907e8dff280d0bebcd4b00a0720db0b23edfffcf1180cd0f42ddbe80b8084a580808e8091eda7a5cb9189be90aad24f666c31404917245126fcd100f8cbdee7d851373781e6ec313efdd90c09d5dddfc7c8d50d2d2ff40324db0c1c2e0418311b2313371ec4d6f9c1c7e3b59fbb9f9cca97a9b6c8b1f58392d081a4cc80b1dae60e02ea12fee23204e4e5dfd8d107d6f4e2e21c1895f8d4ee03e4eb0808c2de16c7da04c7d8f3bed7e7c6d9ecebe10cfe0301181ff6261a0f19120b1af3ef436146627475637b4ef6f1e2f2e4eedaf1bfa1b3a99ccdc0b3cbc3fa1317e010ef09fd0d12f31b3aff2922190dd7c5aebdc5c89787ac0fccfd12f1d533f4fbf3d4dde801fdfc0af82a110a12061a,
      4096'hfaedfdde94ece996d7dc9fd3edd9edf8eef102e7e91c07fe31110110ebe92307e224120515fb16180e1d16050e0af30dd2acacc9b5b8b1c7de0106ee0b04e7f1e9e7d8d4ddf403df19d3e63111e61efdee1209ef28f7ef1c0213f704e7dcfab8dbb9aee0c6acd1e8f2cbdbcef6f7e43f3139423341372a2b3f1d113a190f1b0a09eef8e1fbf4f8dfc3cbc4a8bbcbadbdd0d2ebd3e3b0e204a3beceb1420b033a04f625f8f1eacae9fcc605e6c5ea2a15d5201bf42e01001e04d71efee71603f0f5fafafdfcf9ff00f4e9ebece6e9f0e2dedff4f3f0fd06f40700f6f4f1fdf3f4fbedeceaecf3edfcf2ecf8eff5f1eff0eff1ecf4e9eaeefbf9f8f8f1f8fdfef9f9fcfcff0204fd00eef1f6f8f6fcf9fff8edefecf1f8ed00f8f0e6f1e7f1e9f3e9ecdeeef9ebf1f2edf4f1e7f1fafdf3f9fdfefefaecf3f3ecf1f6e7eee3e2f4eaf2f3eff800fcf4fbfc0000f8fbf9fcf8f2f0f9f3f1f9fdfeefedecf1f6fae6e4e8f5fcf3fb00fc010505e6f5f0f4f7fcf60107f6fbeafbfbfaf6f8f1f3fbf4f7f8f8f1f3e90200f702010000fcfdeaeeeef0f5f4e7f5f7ecefe9f3eaf0e4e9e4d5e7e0d8dce1dee2ddf2fcf9fcfdf8fdfaeef8f9fbf7fefe020005ede9eee9eff5ebe3e8fcfcf4fafbfafaf3f4f9f8fb02fcfa010508f3f6f2f1f6f8fafaff96d5eca4ce0be80bcbfafef103ed1012f60114f5310e28501b392dc88ab8c0cf,
      4096'hcfaec8bf1a2d17144e3ef62910020f0b30ff13abc0af27d90b2d0d3838042acac100cb8fc1808080fb21051c2147dacf0ef9b4b4cf92b0b0808817faf915f1e207e3f8b2cc05b3c6feb0c3b01a0b3a2d0c3a12f12dfde3d6d4d1d1cbafc6dfddece4ac0ad0a3d9fdfb06e92329dd3e161204a2f80f3dccc0df010df70b080205e9efb6dafccd18d9bbbfc43b042d35221a22fb1ffadefce6e1e8262330c2d6dddcdef2bcc7dc99b804aa9ad39dada223130013fdfc17e9cd2114151a141116f6139cb8cad9c0dad5c9d0556b577272597f7f5f7f737f6a627f577f7ff7ddddf5c2cd0fdfd8f1f1d4d023dfd5dbd3c8dba3b6b9bf94dbbaf308efe7f92ce8f4eae8d2ea361400616d5fd3b5a5f9e8df13f40bfc0601230d142bf5eb20fe2b3b070c4b3c4f91a9bc0fe00326181501f92f0522376a234c1feefc11012711320efcb0d53109f8242905b88e80de9580f4d5ebf6f0b0f4c4b213fd080ee2ad2f09f201280edca6a408c0b7120d12d2cf9df7b7a90cd4e701e3cd1b0afc231731f4d7bc1b0afd211bfeeec1aadbcbdc0201e3f6e7e32c2a264e3a54c5cc92fcefd210091604dbc91bfeb21ed5e915e9a72701d1281feaf3e202f2f501f1dbf1e4e7071e1d40565b62ffcfbdf5d1c0eae3c01304c62a0df02c10f9c2a890fdf4d9040a090d020d37272f73665aa89d81f0ccb821f50cc5b79fe7bdcadbc5a9f6d3ed18,
      4096'h2608150c39e0cdc026050f39381d2ae5bc1dfdd922f6e0fad1be12da0b2b1725fbf7f2f4f9f5f5f6fbe9e5e0e0e2e7dfe6f3f1f2f0f5f4fbf5f3fcf0e9e7efeef9f1e6f7e0e0e7e5e2e5e2e8f0ede5f0ece5f6ece2e8e5ebe5f6ebf0ededeaf6f6fcf7efeff0f3f6e8e8f3f1f4f6ede6e9dcdcdce4e1ebe2e2e6e6e3e3ebeaf9e5e5f8e2ecede8ecebebe7f3e8d7e4e8e7ebe5e6f1ebe4e6ede9f4ece402dce8deefe2ebeceee5e9eeedf5eff4f5f4f3faf4f8f8f9f6f3f7f7e9dfd9e8e0e5e1dff3f0e2d4f5f5ecf3f2f4d7e6e0ece5f1e9e8eff6f0eff2fef1f1f2fdf1ebe9ecf1f1e7e9e9eaf1eefbf4f2f7f7f4e3dee0e5e0ece8e9f6e6e4e7dddeebe0dcf5d3ceddccd3e7d6d1e9f5f4eaf4eaf1f5edfff7edf1f0faf7f8f6fee3e6e8ddebede4e202f2eaeaeaedf5eaeaebe9e4def2e9e6efefece7e6e0e7eee6e6edebfaf2fcf0f3f3f1f2f1eed3e6e4d2ddcac1c9f4faeefaedf4f0f007e7ece5e7ebe9ddd0d8d9d1d3d9ddd6d4ccd0ede6e3e4e5dce1d4deeef2e7ede7e7e7e8ebfaf6f4f4ede6eef0ede3e4dbe8eae7e2ebede5e4d7e3dad6d2e0e1f8f0f4e6d5e9d1cecef2f5eef4e8f1ede9e7e8dce9e4e3dce4e2e1eee4e6e0e2e7d6d9d6eaeff3eedfe1eadee0f8eff8eaedefefeceaf2f3e7fbecebf3ede5eddadde3dce1d5d1cdeef5eaeaede8f7eaf5dae6e6e5d8e5e6e4e7fffbfdf7f9ffebe7ece7eee1,
      4096'heaeae5e0d7daeff3e7f2eff0f5e9f6e0dfd3e0d5dfd1d9daf4d4ebe1d6e1cac4cbd0cbd6d6cad0c0b3d3f3e8f4efebf0e5dce5f1f8f4f8eaf5f9eef2f7eae6e8dce6d9cecde5e6e4e8e4e2e4dbe0ebdce7ebe7e9eef1f2e1dcdde6dbe1e8e2ee02060508090a11080ef9f9fc00f9fcfbfd02010008fc00fffbfef4fdfe0902fe04fb01fbff03fa010a010306fef7f604fe02fff50100fe0403f803f9070a0706050906090b080c05fd0202feff010000fff3fbf1f2fffb0102f4010701fd0302080104040407fe030c0507fefc0502f5feff00fd05fb0308ff05fd050506f7fffdfa01fdfffcfe0104020405fd0201ff0a050701020200fcfffafdfefbf8fdf7f900020402080cfb060100fefbfcfa04020202fb0a030c0d060b060b09f8fdfdff0302f802ff0204030002030f060afd04f8ff0200040802f9fb00f7f8f7fdfbfcfafcfdfa02fdfd02fc050807030402fc020300fffe0701030a08fdfb0200fdfefcfcf60002ff05fffc02ff06020000fc0903fa08fdfdfd00fefe02f6fffefe80808080808080809502070b190d26e6e9ef808080808080818080819380caa78d8c80801205363616041c3104cfa8a38ebca18080e3808080809993808480480c1d3812f5fb24dd4b7f3d7f5e2c7a4a58e1f0f0d3f6f9f8e0c84a69576e3c7e535474858280f188b2e2ae8b00f114fae2ddfccfc1d1aac4e3c8defcc3bce9fa,
      4096'hf202d8d828fdfd2e3d2979372a7f713b7f777f7f7f7f7f6d1fefe5f802f3edf3d6e94509b87f4ef4523b097e687f6a4c537f6b36cdf4d7b9e6f9b6b5e0ebfcf614181de7a2cfdbf40911ee04f71aeb24f80d31f80f1d0bf3e7e11cea0d3800f8fec9cdc6e400eb93ccc3d3dce414fb09e3f20bfbe0ff3f4230483445d5d708d2fb13e6ee068080808080808080803c45155558337f5a284f571f644144756128130efc24fb08e616060c08f3212202161805b7cdc9eb02dbc5fbbf1aecef2920041b2a11f1dbf1f5eaeff9fceef1caba09e6dd150df4e5ecf3f4f6f50e22fa04fc001c201439351fb3c4caf6dff805f8fafcd9f81101f40f0e00e0eacef6efe7f9dbd0efe0ce18fae90f0008f8fcf812090c1b150112fad516220613180dd4d0c4f3ebd21d12f4cde8cee1fbee06fcf0e1bec41418f511350c0b0efa011d02080d02d7c1901defd6e7e8d1dbddcfe2e9ecf7fcea1df8f80ffbe321221afbf0f1fd04f707fbf2dacecae6ebd90400e7e5eadcfd04e20bf4d4fbfad41315f4f1e8f80c0305101d2b201935e4e5caddd6d0ebf2fdfd050f0bf9e00805f30702e4f0080407260d09f9ea0c04fa22340ccaf2d5efe6e8fff1e4d1f3da01f9eb0e050ee5d1c6dfd7c7fbdbd8100a0c01040c02f2eae4e6d3cfbbb8dbd4afe8f7f0d7e3e3e8d8d3e3e8e6ebf9e1d1cfebbec8c5c6cfd4a0bdd5fef2e6e100c4eceddadc,
      4096'he0f7d90efbf4d2e90c0ff7ff0bfd03fcf3ebdac8feffe6e5e7cb242632190f1000fdf9efedcaecd4c9ded4bee4eddef40df9e4fbed0e2323fa121af101eefbfceaf5fbddf3fede201d020a14ed02ffe71a10e00ee8cc0317ee16050701060afeecf20800d1fd0110ece80e091b17101c100f10f5020e0b12fb06f2020600f5efe0feffdaeadf0205db06fce7fc05e3141b23050916f3f7fb0402fb0c0304ffe8e6d0cacccdd4ebb4bacafc06e8f5e4eaf7eee80dff1102002117f51e1e2214221a080bfa02e3d1d4cfd1cbcfcbd1090ff40d16ebfd0fda1009f91206f00106f7070a04080b0b0e080df5fbfcfbf7fd02fbfef2f7f1f0f600f9f8f1f408fff702f9f6fdfefafcfefa0302fd0103080a0b0e0a07080d060304030002ff0007f807020c080c0d090b100900000801ff0a01f80200f80203fdff01f3ebfaf8f00103f1030003fff80806020a01fafafefbfe0304fcfbf6fdfc0403000d050203ff01fcfe04ff0104f70106fd0102ff00fffefef704020002f8f8fdfafffafb0000fbfefff6f3f1fc01fbfdfdfc0101fbfefdfbfdfdfa0305ff060a02fd0b07fdfa00fd0706fe0704ff00020101060207ff02f7fcfdfc040303010300f8ff0001040402f8fbfcfbfcf9f8f6f8000508010602060103fefcf7fdf7fdfaffff01fbf8fdf7fdfcf6fd0e0f0f0c09110e070e010105fbfd01fdfdfa0301fc0101010301f7
    }),
    .CHANNEL_BETAS(1024'h774376cb794676dc765577ad78f176cd78ed76277699740977d87701763277c6776d714a780579746f7878d46f88761775d37789770d74b678d876d874a276f377c476da7599796477ec77d477267795771076d37803774677947831784374577473779b7698780f76ad76de785c753877fd78e67886799c742775ea77a37781),
    .CHANNEL_THRESHOLDS(1024'h023c01df02370246022b022a0216022c01ec027f0211023901ed0223025201f20266024701e3021c0247023002490210021f0229020b027d01cb01eb0244024401e0022302090227022201b5020b01ce0203020f023802420254022b01af01ea0219020201d20242020b021202240230020a0202022601d1021901f401e901e8),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00db),
    .ADAPTATION_DURATION(16'h1388)
  ) actor_down2_standard (
    .clk,
    .reset,
    .in_valid(e_12_valid),
    .in_ready(e_12_ready),
    .in_payload(e_12_payload),
    .in_completion(e_12_completion),
    .in_bin_tag(e_12_bin_tag),
    .out_valid(n_down2_standard_valid),
    .out_ready(n_down2_standard_ready),
    .out_payload(n_down2_standard_payload),
    .out_completion(n_down2_standard_completion),
    .out_bin_tag(n_down2_standard_bin_tag),
    .actor_error_o(error_actor_down2_standard),
    .initialization_done_o(initialized_actor_down2_standard)
  );
  logic error_actor_enc2_depthwise;
  logic initialized_actor_enc2_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(64),
    .GROUPS(64),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'he42efafdf92a133f457f5a7f463e4d54086c3903171a06163e14133f1a482dca4023282e30f12a20043f22fc2cf6c1f31aff251b083ffbfdf6eee8db0907d96b2143341a450617281ffbf618fc14fbec07e7f3f328062d133d143c40f705f6f54e1816fe11f7f704030120141703151208f4eff2f82f14300ccf1222032c303b1d250fe52003e20deb050713eb52314f09dbe008e3ee0bfacc4e042308ef0917fe0430050e0adef90b2a1c5a55456411ff7f661aef20111ffc12e6dfe53f1a2e4e2cf4521900371c2b02d41c1fdd1432102bf4e131ff00155e403ce1d621b4d61104100ef315f0f9fcf71315f305fdf32924f674132c20fc1a5e2f4e471b4719111a23092c182240521df55b29341cf220eac1172a2942417f7fc5397f7f707f12240bf6f2fcdfdddb7f41617fb9477f4c7fd0d7f9f827f1f5f6eb35132608ea152f0cde16ecf802f70bfa070f173a2f1a414300565c223d3dd5f31af5fc204a0c6259f6777f6d3df2f207f9000a12ff124b387c054d6e0e10552e3c164420fa123028f7eecb1be3182e2c366306613ee1247f7f7f3327282d102e331f3142fd162615013911e5330833ff9a1e400d5526352a1de61910f60b18fdd2d701f004361710fa18f0cc0c1e040c34224731f9f9503c377f497f63da317f7f7fdc0b2af6e41e60ea141413eef40cfb16f41046234531a62d300d3846197f18eb5bb0ff,
      512'h39e8010aebf015f202ec091afc11030bfaf800665c2d35ead7022b461a031708dd061e1819471c6439fa4b7f4d7e3304f43beb08382f1c1f15f41ff7ec09251a
    }),
    .CHANNEL_BETAS(1024'h7932793e780478c9790d786578837827781e78a67801777578327878785e77e877c87869793b788577af785b78b277e3790c78267838799e785278e679d678c177f978cc78077817781177f17783789f7816781a787377f378b078c7780b79f079b1787277f7790679fb77c6780b78c377eb7835780f786d780279257847780a),
    .CHANNEL_THRESHOLDS(1024'h020f0240020201f301e201f0022501e5022a020b0239020f02160219021801e90210021701e30204021b0200023a01f4020701f401f60265022801e7020b01fd0219022a022401e601d601e201f601ed020c01f3020f021101f9020201f6023e020e021a01f902130231021b01e801f401f101ea020e0209020a01e9020701fd),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d6),
    .ADAPTATION_DURATION(16'h136f)
  ) actor_enc2_depthwise (
    .clk,
    .reset,
    .in_valid(e_14_valid),
    .in_ready(e_14_ready),
    .in_payload(e_14_payload),
    .in_completion(e_14_completion),
    .in_bin_tag(e_14_bin_tag),
    .out_valid(n_enc2_depthwise_valid),
    .out_ready(n_enc2_depthwise_ready),
    .out_payload(n_enc2_depthwise_payload),
    .out_completion(n_enc2_depthwise_completion),
    .out_bin_tag(n_enc2_depthwise_bin_tag),
    .actor_error_o(error_actor_enc2_depthwise),
    .initialization_done_o(initialized_actor_enc2_depthwise)
  );
  logic error_actor_enc2_pointwise;
  logic initialized_actor_enc2_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(64),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'h04f923dee4d60beefade3b3201e641e0023dc21226e4fbe4e9f3fb2d1f0c2006ff03e011ffe2ebedec0cfe3013ecf7e9040cf5071f11f7d90c070805fcea130c5019fed8cf1b271630bb20f0f1ceaae102a601ecc0ee80f30cf9e6b033f7be15465e01e6f301d13a251117ea7fd58527dd6bc4d8f7cd0a8d7dfaf368803fd809fa1230f8f90108dd01100d0a09fd20f8faf6f3051ce1f2110a01000813e9020519edf62bfdebee0cef0906102203ef0cf10d0012fb0906fd0af9fff8fdecd40003f0f35406e133d901fff812ec3705cb0e0e09100d4a1ddf09f61404d6ecfc390ef024f4ebea001104133a2e4c2820ecebf3dc1e47f0fe24180404e43befe3fef4d803f509fbec36f5ebf6ec0217e6f00e0e14e80adefb18f1f802f7e4e5fbaee5ca07fef90007ecf7caecf2a3d5fbd7d106f70bd9e5054dadf70c0510cd0606cd88c208d87ff9010d0da1321435060d31d547cf9c27eb1d19033baa14fbcedef280dab20402d8e12480fc3a80e3fdc7f43c77f2adf1f250800bf7e63dd1f417e2eefae4e426c6f1f808ebd8e1f114bf04ebf2f4f9fae6130d02eee9ebcdd3f9e1d6e30df9db16d6fdea0d0fc409fbfce1e5130ae9fd07de0a020be1e6c0eb18dfbe00c1e5f7ecf9f3d6f0ee09e7efccfef9ecd1feceef09cf0506cde4c2d7c8d5a4f1f30dcee9b91eef10f9aadfe1a3dbd0f29888d00cf8b6f808e63f9cf50c,
      4096'hd8dee019e32df22803f0dfed2d14f8a6f8d9e4dcf506260ddcf9e8b8baff8c9fc9cefcfa08070790f4a6e5e9800ffc13ffe1e88080ccfe028004fefb1b981532ff22f20223f522f4fceb2b01d8f903bcfb0ecf11e505f0ef110401eb00e5ee2418fce8efdede27e0fdf71ff1041306e4f704d40d06ee02f310fd0906fed81d0c20351ee3e5fbf6fcfff4fc0b12ee04e31409d317f803eae6dcf3f531eff5032dfb07e8140af3f403031a221b1718e1eaf2f1f712251efaf72502fe19df0701fc01f60ae5ea01e6ee02041210f5fe07de101eeeeefc010fe4ee040408f1f4000f02e0e6fbfffaefea0f121bfbf0dff7cafdfdea0ef50504d21301ffed1addf10fe2d9eccb28dbe9110df3f4e9090bdcfddec513cdd603e529dcf805e0bff0f3bfc506fafa13f800d7e5c1ff01dcf3d5a7c0dd34ca8ce5f23eb8fef9f6e6a72513bb91dd22c97fe448004c0ff6de7ff880e6e910c6f8f11e04cd12fabd02f6f288058026e7e50cf48dd78237d080c00707e1c066dca3cf096480fc05bc4cdcfbf6070905aae3d5f9b607e1e4e7fedce9e7e208dffa02c5cce2eef2e1fef0c1f20611ede704f0aee1e7e2eb09fb00d4ead5a927c6eafcf6f1c50df5f9e4c4dad30ce6d4fae9e1f1f5f404ebfa2af4f80dedfc12f6d4eeedf310d8f8f311e0eb12cef0b1f007f3faedd50a17ff2ac5e8f5c0e8d90be7aeeb0813dcfafdf927c61c0a,
      4096'hf8bff483b1c9f88408a8d0b8dbb6c9c8ffe4d9b3f3c29df1fc05ecabb480d8a5d9810ce5e690f89dddcaf807c9b7c0b780eca08c83df0de3b5edfdd9d580c916f1ef09c2f2daf280fbf0efe2ffd6e6ecf707defd1ed7d5dee301e9f4eeafc90803ad0011f6baeaece9e80df800e7f4bea4fcd4d8e706f8c5f90202e9e1bfcd02e3c4e5abe0f4def906bad2f8e4ecedc7ecf806bdf6d5de0fde02fedbe9bfcdcdcf80ed04e9bcdcb4f3d8eef2a3c5f1a1b9c6e3a7a1df01d4a6f807e60a98e30307fa10e5e9f909e6fcf8fdd3d5e7e8fae405f614ebf6e5ee14fcf40424e3e20b13f5ecfdeee11ffbfc1ffd0f1510e209dc19f7040f120ad715f1fc24c4e2df0719151cebe9e7f9c2f8dfe4f507f2f7edff02ef0b02dfe2f8e702ffe2fad9e80f19c5021fede10df40c070bef1a0800e3e3e600e8e4170cee13f3f7def4d7ee0e09cbef85d0e005a519c2e2f7daa7d0b4ece180eff20b80dd2c1906d5d080d0d4e7a723f8e980f5d5f0cd32c8afb1e002922480c8a5e6e59bc31afbfebf97cccfc520f5d2e6e4dff102f518d5dbe81fb82502ddc006e80fe5d5fc0a0be5fb1122dba9dde5f0c1deec1a1731f6f6b514baf2f5ecc6aa0cf110bcfefbdb11bb0911f6cbf9d5e4fcdf08f502ecfd0800f8bb00dbe3dfecd70415d501f0bac1e6dccde9b9faf027ee05a5fec201feabf3e7f0dfe5f2c996e1fdf794f6f5e7259ff006,
      4096'h86b6f2d6e97f0e50f404d826f47aede7eef41fd7070e65f9a3ec34dc051ad9b83b8021eef7024df0c7a82ad2802a39f80de5038080c600568004030924ca12e2e9c3f5cbddcafcf904dddaf0e4eafe8b0ae2d1bd0fe6f4edb7f3f0d8b1dbf4ccfcb8f3fc12c901cae6d5ec10b8e3d8e5d0e0c8adaadbfe059e04fce5fbb6ec00b2eddcffe4e4d219fe09252508fedcf5eaff07ddfefdfc1ab402ee13cee9fde8d8bcf2fb1002ed8201e815e3aaab11b5eef739dbb91bf93c99ffff091dde45c4e30c0cf1e8f901e2061900f2f24701d40711f405fdea31f103f4fd14050cf4f911e50c0302fe1609faf90904fd0fe6c0f1f406d9fb04f8311205faf72ae5e307e880f313799c2409fef8df56088093fafadbe3f1c4dbbd069e0216210a1e2c03ef40e6ef1376d9f0fd45b10765bdb7dc0732061e152cf7df07fbed13801ff80c0195f480e9e8edbdf7a7d1dff5cfeddef0efeba9d2d19712c3e7d4c1a9abcfcef8b8d5f0fca3deb1e6f8fb10c3b0c3d695c7c19080f715f3c5f10baf0898f308e3fa1087ccc7f7cd0dc40fefdadf03d8ff0ad4e0cedaf7a9eff8effcceebf81acddbdbf7f4d6dfe5eb053bf2f8b4dfd6e4c6d0c3ceef0fb8eef9f1e72cd4090e13111802f80522dcff0e1602f923fbedfb100b1dfa06e6fef8f9f40717e410152dfaea010edb0bf8fc07e820180adff9dcfb030b221bfbfb20f9fd0cf0f1fb00,
      4096'hf5bcf69ee614f4dbf9ebe1e2dff7f1ebedd612b4cfe6c90ac1f4f5e2e2d0dcf2e9ace8ef24d4e7c9fae712fedcc2d7d1b0dff0a59b280012d6fb07e807d408e8fbfa03f00db4fae405f00cedc7eefbefecf8eef707f80b191bf5f108d4fbf312f11616fcf6ea06e4d80b060a06e9f407f202a5f6f114f81b05f90608cc1d110e0d18fdebe8ff03e0fde41f0e07e4f5f6100bdad206fbf5f1fdfcfbf206fb031705e8fdf3f2ecd7e017131c0c05d8f9ee0005f4fae8fe01eefbfa03fff1f5f2210102fcdcdbffeee4f11bfc0003d902c8f0e7f50406deed0bf70804d2ecd2f907f0d6f818f3b1c6e0f3de12f7f5fce2edfcb4d2eb02e90bdacc0b06ea089fe20087b0f5b90f2fbd37e3bfd2cbccfdee3bf5c12ab3fe9e413dd8ee16f2d6051ba5eff62df835f237bfd8d0cd1180c50080bf8bd780d01c037f8007ede20cb925120401f5c4e20dd6e60c29d1ea01ca0b05cae0ddcce307cecde40fffc0e3b6c3e8f2c612e600fddbb61baf2ff0e1c5a7d2ad57dae4f8d4f991f5f20608ddd400ceeff4efd5e9dbe1ee08eff2f0fcf9edc803f408f604d0fef2f90afae5e4d9e2ecfcb8f7fef7df04f3fceb0e0ad9e4e2b0e1e5fed1e50dfff2f5fcf4e12ed1defefe041be5d902200ffbf5e8fffa0bf619e1e4030c0909d6e1fd05f2e51d04f41e1feef1080d04251dedf5f62328fbdb22cd0efafaf0e200074308fc06d113d605,
      4096'h1b0705f209fefbf9fdfffc09ff04feeffdfcfdfb07fef2fc00fc02f706e503140ff7fdf409f800f20907030d13fa05f7fffd020b0816fff4f7ff0108fcfd0206e7e806b6e3cfebedefc4f408f6d1fcdff802fcc3f2d4e3fcbbf9f70ae6bff2f60ede07fee1be1d05eef7fcf8f2d3dbaccad1c4b9e607f8ed11fdeedbe5e30701e9fefbd0f3f0079c09def2ecf9c4ead001f8d103e9ceb10dff09e6faeab0d7fa0fcfee08cfa8ebf1f9f11a0cfbd9d4bcaa19aed5dbf001dee306fbddd0bbfb1300fa06f1fbe1e6d809132d0b2dc1db05ed0bf728f3efbfedfefbe5ecf5cbe5fd11e0f5fe04dd0dd7f8f7150ef312f8d4e5dc21e3201cf40901f3ffebf9dae7f93927fde4f20809cc0f071bee08f4fa070b00e20a0a2dc8fc370905020bd6f6061a0114f1f3e50cf90510fcfef2e006f8eb0dec07f6040afefe030505ede51610f108f9ee04fbecfc0204eb11fdc6faaaeae4d414f5ee04e70101fae7e1e7f5e9fda0e2ff11d2efdb11d804d4c8f3cdbfed100d12140bfb01bf0a03e90fbfcdff76f4e1ffee2512fe063cdf2009fdbdfcb4ef28f2ec3180f1effdfff51003f23116ed04b9fc11e6e71a4ef2392cd9d6efd23027412643ea9032f8fae7001614e7181205e0d3e908b10e0102e3e6ea05e3f6e7c8e2e0f8a5e9edf1eadb08b0c423fcc60408edc010ce11ed0d00ddbededeaef18c06cbd307b800f1fd05d6cce00f,
      4096'he9e2f080ebe50880ef9df7bbde99ec9a11d5b6a9cdbaa7f3a2f3e996b780bad8c4a8f7e5e280e69af4f01cf3c4cee5d793c4a080b2e307a8bdec10cfbe80d0fb131a12d1ff1a25fdfd36f60d23ebe7f8dc06e4ef15ebd0012209010b03f1fd1e1501ed2208f7fff40fec08f60bf51af6f2fe17e521f901dc44050201bb15edf5e6dbfee3d115efed04e2f8fee9f9e3f5f3efe7dddb01feecd9fffeedfbece8dae3dbfcf805f6d5defde215f2edf3f3f204ee06ccbd0701d0d609ffed1fc209000008020af7ef17da09e1071bf5dd14e710f3ee130cfee8fb1c04f8fbefdb000704fc0cfc01ed0612e8130afc0a06222ff9e2c803e010fbe40f01070cee0ce20d34691e09e1c511df20c804fff4f534e94a25a91722feb7f34efffc0bd8b5fb46450f1e15e9d027f3ed27081f37f33112cef3cc114034fddd36ff001adfe3dbde18de03d503d8e9db06fb130315e0e23af213fbf8f9e1f3fbfdf6f019ebef03fa08f8f30df2e9f5e90410f01502e3f7e305020af5fe14f6fd06f8f2effdf738f7f0d90def03e502ca09e5df05f6f5f2d702f4f2f8f7e1d7e5f6f2e7e3e7def1d609c702fceedaf0d9ebe3f60dd3f600c6c3c5f7faed08faedf2f0f5e6f9c2d9f3daf9f9d6de11e42afc03f908e835e8e2da081aeb010b0b37d4fbf7ecdff0f5c719d9fe0004f937d71be50f019ee11080cceefb0ccaedf3509ef90219f4e21fe0,
      4096'hf6f718f0ed0900fc0111fc12f1faeafefc06fb031103f0f0fffffc0b1fee13f40cf6050cfdf71d0df6f8fa1813eafc0eee08f2130e07fdeb1201fe0feb1103fff1dffc8af6ede8cc02ebf5e7d7c9fe990203ffc8e8d6cd0addee0dced79eddcef3c2fe030a9fead9eee7e901b5c5e2afbfb6b6d6abe5fbc6b9fb11dbfacace000f14fbfeedebe3c5001b12fb000b2c08eb01f533ecf9e4f72100f503f4d7e7192ef0da0700e808033fec212b4010f8dbf128f3383b0e011e2afafdd620deeb150cfcfcf8f406141304f01301fff4f9fe04fbf913f000edf818fefd0aeffcf3f70a0c00fa0901fd01f7ff0e010c0b0900f3fff317fb0305100700ff10ee05f905fef0f0b6d80de1f3fffcf1e801f0f0c01bdb0ed3fed7f3ecc7f10ad4d7f0c7dbfc87f8ef12cfe4dd03df11f4bed3e0bddad4f6b18f06f3e8d400fad44596e9fcec1ff61f07a7f4ed093ff10ef7f922edf5c3d9bdf92cdbf8f2f0ec96130ea30ef43b09e2fb122842591553e405d2092acf229507a7fc0de2000105ffe715f21fe0d6e3e40201e4fff50ce746fa441f16ed2b2bedc6171f4eb4f4f124d40923e6f1a1d1dee81fb8ce14c4e60e80cde7bee9f825d5a807f10c88fdf6193de043a6159feaf71bdaef05fce532fd05b0dd1df2cdf510f5fdaa29daf6ffe1e20603fae99d00fe0809e1d214fce406cceee11a1ff53210c9faf5f3d0fced20cee5f8f5
    }),
    .CHANNEL_BETAS(1024'h77c076b279d577e67792796978ca76d178f677e578d4778a774879ce797976f2788378ea7794799f788479347690778376e7780677c7793577c577797758781076ab78c77851796d786a788978997986788d77667870790477f278e076c1797077eb78b278137951773a7780792e78867838787077f3787276da781e77ba7834),
    .CHANNEL_THRESHOLDS(1024'h021d020d0239022a0244020c021d024501e7024c0237023c0204021d0235021b0246024c020a02230249022c024b0241021d023301fe025101db021b024a02340206023c021a021f01e601fb021701dc01fd0214023c023c0228022401e401f40236022001f9022d020f0228024d020c0228020e026401e2022d021b020001db),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00e1),
    .ADAPTATION_DURATION(16'h134e)
  ) actor_enc2_pointwise (
    .clk,
    .reset,
    .in_valid(e_16_valid),
    .in_ready(e_16_ready),
    .in_payload(e_16_payload),
    .in_completion(e_16_completion),
    .in_bin_tag(e_16_bin_tag),
    .out_valid(n_enc2_pointwise_valid),
    .out_ready(n_enc2_pointwise_ready),
    .out_payload(n_enc2_pointwise_payload),
    .out_completion(n_enc2_pointwise_completion),
    .out_bin_tag(n_enc2_pointwise_bin_tag),
    .actor_error_o(error_actor_enc2_pointwise),
    .initialization_done_o(initialized_actor_enc2_pointwise)
  );
  logic error_actor_enc2_extra_depthwise;
  logic initialized_actor_enc2_extra_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(64),
    .GROUPS(64),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'h322a370fd5f8cfc6f220e60e25def04fed52131522092cfefc01f628141ee8b8ec2701137f177f16394d3dfa2bc3101dc8d8fb1a141e1e0d402fdb17170b2eede5dbf2f6cfc5cca209040b1df51af90a2c2afc28e49ffd2210274e1b54f90b123d201d101b1bfae706e3f7ea1908011d23fdfe3c332ce91efbbdf72b00232f0543ffbf02373d3940033afb8d073e19401a5a50493544063f0c21ee4bf1dd0240223d3c0d380af111120408261b3d09fc15d500071cfe3feeb50942ff4606f80cf603f8111b1910f517ffb20e2921124a27562abc2a4f0d361f1b0807c3022b052b1109ea02f0ee060d0536263a0fd9f92c13090201f9f3ece8fef20417f9f53406033c2f1dff053200210d012f0bdac80106dffa3018337f7f7f2ad6494c177b260016f4e8fa492046390b4cf9a3163b1a4a05f9061f16fbf5e5d8ebf80de8fdfcf9ecf920d834f79f062ff6363c372e2e1b22170f121ff3f31b04e31f0ae103fd0ff2fdf228021efef20bebde04ef11fe26032902e30d36fe17362e09100e0b15041d6540242bf2fe6e2f267f7f7f62fd627f7f7f234e3e13fd4c203b27250631ebcdf11a04123af732f699fb4d125c0f1bf11630f80b03e22d083a24fd080f0ef623ff14f6cd022a1733693c2b52eb184c1b495911631b99fa5b094f380543fae608ddd217fe08010fed010c03eb5f2e6c14b7323923547f7f7f68ff7030e9,
      512'h2110f0e0020b06230e255a2a5d45ff125b074b0213240df8252113121f171e24f12e101c156f37274d0d69793265fc050c01e506360b164a143804db0304f610
    }),
    .CHANNEL_BETAS(1024'h78a876fe7834786e785978d5794378fc781b7951788e77ce78ca78d6788478ce77937843789e7806791e77f6790e79f3781477e07877781077cc78d5777a78a679a07870778e77e778b97882780c776477be781978ab780b79bf789f78607aac78bf771b7870791a78eb7873780b792578707837785377fb785579d3789d78ce),
    .CHANNEL_THRESHOLDS(1024'h0216023a0201022101f902060249020201e802390216027401fa023a022f01f401e9021301ea0208020a020a022d020101fe01cf01d101e1021301ea0214021e01d602180220021e01e401fa022f0213021402200226022a0206021a0216025a01f201ea01f10248022d021601dd01fb020d021702240203021c01f6020401f7),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d4),
    .ADAPTATION_DURATION(16'h1368)
  ) actor_enc2_extra_depthwise (
    .clk,
    .reset,
    .in_valid(e_18_valid),
    .in_ready(e_18_ready),
    .in_payload(e_18_payload),
    .in_completion(e_18_completion),
    .in_bin_tag(e_18_bin_tag),
    .out_valid(n_enc2_extra_depthwise_valid),
    .out_ready(n_enc2_extra_depthwise_ready),
    .out_payload(n_enc2_extra_depthwise_payload),
    .out_completion(n_enc2_extra_depthwise_completion),
    .out_bin_tag(n_enc2_extra_depthwise_bin_tag),
    .actor_error_o(error_actor_enc2_extra_depthwise),
    .initialization_done_o(initialized_actor_enc2_extra_depthwise)
  );
  logic error_actor_enc2_extra_pointwise;
  logic initialized_actor_enc2_extra_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(64),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'hfaf7050de604f905f309080af1f717f6e612ddfc00f7fd03eb030707f0f9f504ff10060318f310fafe00ff1ffbf3eaf10206defafd2201f206feff06f9eceefecb7f06bf8cac9a3d218003af339b0aba1eb13ceb800d80bdddeda21fde1011945148cd08ab26c14f23fff00a600f30733d4fd9b6e6c804b0391c80f88025115cf40d01f5caf8f90505f40002f6ec08f5ed06e3f8fbece6e8f1f8d6081e0aedf50ef6e008bbe2f307f701fc0e0bf0f4f1ebfafb160cfef4cf1bf8fdd7eaf4f0dc10d1fc48000540010829fd0d0e2528faf2033aee070b470c18f7ef02fb28191f021720ffdec81ff8010f1f09093ddcffd2fbe111faf60021070114fd16e619c62db7c8c249461417fbcfc7da171eed56c4d635ffabd7d54533f126f703ca2bb1e9f63e087ee5dc0909e50b1680c8d780381cf7e9a303077ffceb083ae7f00340e9e40301e51006e9f20c04baf23bf708e7f200f1e5fa07db110736fce2fdf30df180df162af3e9fd21c202bea5f528bf06d2fb22bbfaf218cbe90c01feee1f14e8b3d20c5c153f0a31f430cbed2fe705328af10ebe097f2024e0c0f3c0fcb780c5f60be405ffe8f3d98429b88021c52dff8bcaf180a0fc2d8700c5f91c32fc8ccab8e3f731fcdcdb0be8ce05e3daedddece4eee8ced602f615edfefee4d9d0a9f3d2f6070e99e3e2f4e8f1c7b1d4a3d0f5e2f3c5b9fa02eec0f3c7f10a8d0ade,
      4096'hd0abc8dc220ada4307e1b9d1164be9fe1d9c1bdeb9dd4e7ff90d330cb30aecc3bb25e9024626d5d3c1dce480801fde411cef39bc80f203ee800fc1fe51d84ae113db0917d0060dfdf11b01160106ffe3e9fd0b0217f707f101fbe810fbfc0d27f7fd08fceefb28f7060816130c22e9f5f1fdd71205f5fcfb3bfe0c06f0eb0ddb09ece611daf7e406f5062522f1ed09f4fc1fefe5f2f0f5fee7fefefafefc1808f9deef011aeb19ef0f17121402fc0bc0f52f15d9062806e12dee04edf6e6f741f8cd0303ea05e308f8020212000406e8f504f1fa070106ef0401eafe02fde7f5f7e0040ff5ed08f2fcfb0df2e9f6e7da0003f3f9ebedfeeafd08f3de04ec00dfe8dfe0ce40f4cee5deddf50b1504fe02ac8f0dddcfe5f15dde0321ffe4d5051a06abdbf91cbfc322ede5048ed6dc518031f01ef5f7020212ffd714e60dd91d63e88ae4fd31062bea13f8e4dce50bc80ff1e35ed8ad06d10c15fc231db704f21b1b800a0d42f52cd002eafeadc3e2d496e7d7f4bcc10bef05c6ffe4ef46f2f9ab04d305e1ecd2d403ede30616e4d5fdf3c51fe8ec0affb7e7d8fb020bf2e607e2010bdcf814c623ecf1fefb08f8c9b4dfc4e7dad6fcfcf7d51bf0f9daaad9c2cfd9f0f3f21424fcf603e4eb16f6fd0d26f725f7e40bf80d1804f8ef09fa1e1be2e1f6e7ff11e3fa0110200b0aeb1fe5de111707f5c1e8f81d06f7fb11e9060a10,
      4096'h9d80b5c8e0dcba100bcddde6a28efebb80f0f3c6cde280d3e7fbe20580cfcf80c0e0c606dc80f2e1eaed070580b780dfafb4999280b806b0ae1e80b3a180dbd3e3e106e8bde0dd0ff8fce91adad323e3cb090af8e3e2b7c6e8fde111f1cfd3e9f7d4f800c6a5f9dcddfafe18fbbccfe9b5efe6fbd102fed7fc1cd0abc6d4ead719b8ee9b0207bdf1fdccced5d60de346e5a063edc3e0c62724d842fadb32f4e2fd802df21ba31bc2dc3efaeeacd50a9016271b8d82022024e000dde510ac5c403c22152cadc5e007fafa385ae09b20803de2ec2dfc0a0d80c1f3c0f63f21e82bdc7f250b8df6f823e80733187fbed57ff2348c40330efc8072fdd80d1e0abaf5dbc50912d601f204fa0a0f05f10d09ebf506ef050cf5fce206fef5f80601e8f3f8f9f600ffe20efdfff5fc05f500dff3dfe9fe0ee100fac1060ae4baf9bf04f0eb2422c5ffedd2f308ae1fdaebafe4b8fae4f2e5bdebdbc8b302a30b21f5d5ad275409fee719f269ead52ddec888d67fe6f282e633af07ba1ce4bd38f6f9ade7ca80dfc2e2eaaef707deee08cbbbfed3a0ebcaccf7e1b7f4fbecdef3b5e0e48ccc88f70af68122b6ea040ee28cc480d5b2d8c2bf80f70dc7ccf4a79bb980e5b2ac85e7a0e4edeed6e50994e02ded051b55e1daf1fab5455ef8f1df00cde8f2800a07d4f33fd1c4d3cbddfdc080fd9df62cdf36df80ab026380d897f93308d72a,
      4096'h818deb1417002cda0c33dbc40d44c30b2adc250b24f04ef1400928f0b12bc4df0a8a0ffd1cd9f0b7038a1bc18014c6df19b4fafe829bf4179cfcc1bf3ccaf9c1e5c9f0110315df0100c6e0e9bdd2fadddddecde5e0ebf318ef04ff0fd3d907c4e8f30005f0cedadff80410eac2d4b4c0daf6bdb3a9d4fbe4bae6af9de5b1dfd5ae99f1803bedf000de07fcad1676a07521041cc80efbf04e0c1456e3cca6c0044acce103631ebbe7e180f6a980fe348026c75dcdc3cafa2680afcb05fbd67f7f22d01902e9f2df04eb17fdfd05061af2dbffe3fb04020ae40ffe0a0afef2e6f7f0f9fb1119f10ae9e0fe0412fafecad1f400fdfe20f705fc03f5091b08ecfdd1e911ecc5f4eadf03f4e3dcfe13a0d72d18c2f0fa82d2b303f3f7dd22143ace0728e5d700d6fea8d60af8e3310db9362724020241eb1ff202de1005d6adddc47fa9c0d2d5e4caaa08f2cbb0f6a594059b91f1db94ccdb9be8f203c40f80c0d48093acd7ffce80d0bccbf31cc29cba80e6b7b5969680e9fcc7b3f880eea981b6e1d5ab0cc6c7f9ae2704eedffbbac304c194ddbbdfebddb8e5d510d9f6cab1ea99efbcdbfdd88011d9ebebfbd3c4e2a4d7a9edadd7abc7e9d2dc13adb6c480c4e7d9d3f5f6f719e30800e803f0d9e9fee6d516eb0403ebe4e90208fd0904f8f8e605b0f30305ac050cf3eaff01ededead9eeeaf3eedef9fcdffaf8dad9dbb4fce3,
      4096'hccbef7bbd5fec615fcd8aaedcaebdde58fd408c3afd2df0c0af216fed5e3e380e8b8fffff980fcc301e4fe8e80f09cb3dce9069d99ecf7c8b701ad8ff9800cf907d1f7db09d4e6edf6e4f801f6b9e5e7d6df04cab7eacf01e7fcc601e7f409e5dff30000e2e2fef9d60bf9ddd6e5d1ebc8efcadfe7f2f703ee00e4d8d5d2d0c7ebcced01c5edeffd0f0df80206051cf10312d9fb0af6f3ecfe05d304ff00eed7e4f603faf2f103df07fd081fff04e0e20ceffeebcce5fad3f60dfce0ffae052510fa1009d1f1e3f0fc051600e0bee2c5b4cfea21f9dad9ebe9f5e90cdcf5e3f3d2b7e414e091edc610dff121e2f8e9bce4f9d91eefe81ad6e9e7f0dcdae3ddc5ed8b01e33b0af7dcfbecfef00c1efe3e081105f2f9020e161401162c102711c2dcbdf61020d10c0f00e0f9ef96cee2ea25ec01e7ac03fe2ce0f0e9f428db0ad8bec4d0ae03029b0106b0e7f2ccd9d8cfb4b316a389e0c7fbdd0426fdd4ded5aadfb7e4039e02f5db12cce0f6d8ccd0eac2cd92e3a9ee0601f017bbedaeb5efac19ccf0e01b18c40aeee6d304eee0dffbcef209f0f1d8fe0016f4e8ecd408e6daf6ca10f4112010cfe901060fcce0d9ccf3d4f5dbbe0ef9fcf30be3d0ede80cc5f335fd2113fff30af7e106d1efe006ffeeed0d1a05f1def8ebf7db01fe290ef1181c1504f6e10b36ff0ad60919d708efe2ffe2e3e1cef3ee44081501fcf80306,
      4096'hfd04ff02fb080c030108050cf60c04fdebf300fffd01ec0110fbee00f2f80e0504f3fbfeeff5080011030004080c03fb0404f30b1502fffbf4fe060303feeceef8ad14d3c7ffaafcf3d3f013dca100e9cc03ddd1e1e6c9fdc8fd07fcf9f901c2edd8f403038008faf305fafbd5d0a7c6ca03cbb88ceaf1f5fe0cb9cdac91d7f10fc40a23c920ef11ed14061bdcf041caea43dcec3cf8f5dbdc01c50720c724f30d011108eee925fe0c1afa381bdcdd11e8ddfdcf1cefe4e60d17e8ebfff218ee03bef73fe31d0c01f8061436b7e35df7e23b040e12f4d7d10503f6fa43ed391cd2e0dd06b2eb26c8273d2a611c050bb6d018f62e4132ffde230d0b05c2edeee41bc5e5e9c6b9f722ccf61137c8ce4d80b615a32d19f2e8a4b6f1cc1a2fdc5617004ff009aac74df7066c27507f16fd6fe2f2804c6a36ed9e6d3a28f8abd4e8d716db0f0e262a0609fa31ee10061a1610e409480df802eaea0cfcfff6d4d81a1bf4d2190216ee251517141614fa25f2cafaf1e305f707051afeec3af10cd8040bcb190de7bf12cd1e1dc4ede2f1eac416deb719e7c1fda0f7fb05141e04f4fc0126dfb9f4cd2306141acfff3101db561d1205fb1af03bf4eb0e0210e1a201f602c53916fcc6f1341435a3bd35c18ff0801f23d82fd82ce68ba6e480eaf619d8b01d7f020480d6fc30c223e71167f0da7fe2eb804105f0ed80263e05c52dce80b5,
      4096'h8080d39e9cc6b9fe13c0c0e4a9960b9780e998aeb9cf85d4d3f7a711afb2ea80a280dce99780f4acd3e910df9bbe80d1acd89b8b80bf0981b0f886ab8c80a4ec35c9ec020b00c5d9ffe7f00ef2d30dfafd0901e9efe6e1e0f6f5c9011104f9dedebff3f7e50cfeda08fcec12ee0bceedfcebf4ccdafc0ae10a04d2f9e3bce806c2cdd19f0103b9e5e9ee12d10f10cf10ee19f2d205dddaf7db0d0809fed9c9f21d80e10604e2e4e61cd80fe29ff5fbe205f94105d606fcf6d20cedfbfa9a09630fd906fa0afaeff91000170d1500f6e5e4f20024f7e4d2fbe3fc050a10e0e50208fe05fbced213f205241045f0070a12f913f1160b0a070d20f6fb20c4dafd3047f90219f7e7d4f8e720f524bcdd64d8ea29ea11f709eb11ddfdea11190b080af03b180ebb131309151df8f944340225d7c4e72265f6f8dc0af6fc5fbfe6d0f9c9bb0ae1e4e5c1f902e6fdfae9df1cedd816f0e5e6d0ddedd50be4ffed09e2c8def9f9fb1fc2f7ebfbfb09f7ed02ded8fee8f6cad0140201f40cd7fbd3b70128f0c6f2eeb208ede9f8f9f4e8d2e4f3d9ddf9f4fee1f8def001f8e2fee900f8e5fcc4f6f8e8baf4e6010106f1b9fcc9cfc4fcecf8cbfaeedef8fcd0d9d59de9d0e7d1ed02651fb2f3e71403000251ea58000f650cd2ff033236051d02ae0b180cf5ba0f0e5f0bc7e716ebfed394fadc950c09030cb722037f03f6d7f20aa423a8,
      4096'hf6f71206d3cde7f8edd41922f00adcecf6f407f9f1fec7ece5fecf08e9f801f0f50efb0402d20b0f01fb050a020ff021ecfbd2f3dafdfc091207040ed8c0ed01c7a019d007f0c1f0ebded6f3b3e5eedaa0ece9e2f3f8b102e201f7fcbfd704a1f3a902ffde8006c904f6fbe49bdbacf0bce7c4cd8bcb06c7cdf6b7b0e881d5ef27f6eb28f3fef81b072fff2701012525db380dec23ed14ed0dfcfc0ef7f33d37dfe3d41510fa1df61d2c01ff21ecfcb7d8dffaf71f15f71819f73900ebf622c40c07e0d60ef2d204080c051321f41922fff21304c80ee5f0fdf7b2f4031019fcc71dfdf90609fb18f5073df4110501e117e0b604f30504000c00ff01e10100edc380fce2bf0cb4e8f1e7c10701fbefcbd4e103cf2ddf08d90a100b03e5d8f89fe88005ee089f0db4fbf21ad680c5b6e8faea06b880c6f7e2ce03c89c1c800dc69811ca26e902f9f41ce9d3ff12f4efc321d4e8b8dcfe14d8fdf2f6f5fbed02f8d75ff8f0eb25fc22e20bfee22ade015cbdf5921a09f2fae70401e1e7be14e8a5bb8af78410eb87cce9e703b64b00806fcb0b1afa34f2037fec0869edf5ed80da0d9a871855e59185efddbfaf80903e80efc766e2aefb0a42a8eeafdc33e52f24c219e7a31bf3e8dc0cfb31db07d1fe2610b2f91308f98032a3f9f6f70feb16d331edf50bf5ed9ef4f91cd807bea543415e033208da4d04dbd301001eb5d5eb74
    }),
    .CHANNEL_BETAS(1024'h784275c778fd78187752798177e1774777c476cf78c477c97827798178c477ca7850784977c4772d77b778fa77a8777b77e2784d78a47995789377c578217853786b79027908798b785b77c278d778ad783177f376c577f2775a787a77a9776b7879796478387814785d77c678f8781c7819789b767378d6775a778e786d77d4),
    .CHANNEL_THRESHOLDS(1024'h020901fe024802270215020a01f8021301e8024a0225021701e7020e02470202022f024b020401fa023f0210023e01e9022a020301e9024d01e502270238022301f1024802160219021a01fe021b01d601f602190224021f020d0239020901ee0229021601f502200205021c024d020f02020206023401f50228021501e301fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00df),
    .ADAPTATION_DURATION(16'h1364)
  ) actor_enc2_extra_pointwise (
    .clk,
    .reset,
    .in_valid(e_20_valid),
    .in_ready(e_20_ready),
    .in_payload(e_20_payload),
    .in_completion(e_20_completion),
    .in_bin_tag(e_20_bin_tag),
    .out_valid(n_enc2_extra_pointwise_valid),
    .out_ready(n_enc2_extra_pointwise_ready),
    .out_payload(n_enc2_extra_pointwise_payload),
    .out_completion(n_enc2_extra_pointwise_completion),
    .out_bin_tag(n_enc2_extra_pointwise_bin_tag),
    .actor_error_o(error_actor_enc2_extra_pointwise),
    .initialization_done_o(initialized_actor_enc2_extra_pointwise)
  );
  logic error_actor_down3_depthwise;
  logic initialized_actor_down3_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(64),
    .GROUPS(64),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(2),
    .STRIDE_Y(2),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hfaeafae8f713e7efedf900131d020d2f231c1601fa1d201507130605fe13cbd8ebeef8d2e0f80e23252d4b4308e5edeff1e80b060e0005162e1b2b19ff04fc23170f41032d0720200e092d190015361e3ee2d3f40b00fd0003fc29fa19fe1414fff62c1809282e331b201c1e08f6f707faf6ff0cf7cfd1e6f6e5ef03191a1317370de70e04e7f202ff2de1f3fb283118fbf6ee0cff14140707f6ecf009eceb03f4f1df08f0f7f40e3a2a0ff21015130c1bfbf9fd3d054d142835201014ece8f6fd03f4060810f103031a1602cdf8ec2e4bff441a144a0f0f000b04efff0dfefef6f412feeb0cf3e900f7f3f00f19e80c17f1f7e90512f9f51cf6051efbfa0bfaf802f0ec0207febe11daea09f3c5200b02fa1b20351a48080406fe1202020304f10cea0c06fc0d0301413a30111632201839f1f304f2f6f405fd0d1af9082e161f22fb17f2eb2b061b3e17261511fd15e6cdf8ecedfee6dafdd4e0f1fafefa0e0e0ff509052e1115dee4f0f702e00b13eafcfded2900102214121a150114fef514161117dfed05f9e806f8d7eee10efceafef3ea150613fefb091403f71203100c11f60e3b191f0d0712f80cf4f700f1e7effe0de511150006e00502fbe701db0d1c0ef90e0408fd230bf91b1310111a02fc1e03faf0f70af9101d090e1c1f0a042ffe1318280c06fd121113020b052912fafa06172e1833132408010418070d,
      512'h0c100c00f60b04fd10041c0601f6f70df9dcf01bf4f507fcff1115f81ff9090d02051c15141c2227fefd1a0d1536fb1b260f10301d36091440263c433d200737
    }),
    .CHANNEL_BETAS(1024'h7826776f77f677f377cf77f87924786f776378ca77f9792477fe780b77be770e77a8777d775777cc789277c9787f7862779878327780788577a177d37813788577c7778d786f7804785377e077cf77bd7824781479127790778a795f777a781d797e77e0788e788277f97801781877d377637825771c7774789476ab77f07885),
    .CHANNEL_THRESHOLDS(1024'h0238021801f7021d01ec01ff022001f301fd01f901fa01fa020101f9023e01f10217022601f802020222020802170212020d02270217020c020a020a020e020f01fd01dc021b020101ec01ee021702010203020201fb022801f4020901ed020c021001f201f401fa020a01ea01e201ff01e701eb022801f1020001f401fd01e5),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00cd),
    .ADAPTATION_DURATION(16'h13ff)
  ) actor_down3_depthwise (
    .clk,
    .reset,
    .in_valid(e_22_valid),
    .in_ready(e_22_ready),
    .in_payload(e_22_payload),
    .in_completion(e_22_completion),
    .in_bin_tag(e_22_bin_tag),
    .out_valid(n_down3_depthwise_valid),
    .out_ready(n_down3_depthwise_ready),
    .out_payload(n_down3_depthwise_payload),
    .out_completion(n_down3_depthwise_completion),
    .out_bin_tag(n_down3_depthwise_bin_tag),
    .actor_error_o(error_actor_down3_depthwise),
    .initialization_done_o(initialized_actor_down3_depthwise)
  );
  logic error_actor_down3_pointwise;
  logic initialized_actor_down3_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(128),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hf1200208fc000d000800f4f7eeecf6e3fdf0fb14f80dfff407eee9dcf6eff20df83400fcebf80e310007ebf003131b18f6f8f60ef3f408fd1dfdf615f427d9f900fffcf6f60003f500f9fb02fcfaf80104fc00ff04fe030100fc0300fcfefbfef9fdfeff00f80101fff8fff8fb0604fd0000fffdfe0201ff0400f801000200fcf6ee0306fff403f6faf7fbfdeff6faf8f603f0f0fd04eefaf401f208f80200fcfbf30306e802f708f1f9f7f8fdf5fcf40000f304eefff9f9f400fefcfbf0fcf80af0f900f3f3fef4fef5f31401f70ae9faf8f5ee04f4eb0ffc00f60af8fdef03fbdef6f7f6fc0406ed00ff0f0209e9f7ff0a0af9fde206eeedf70c03141b08f300f3ff0114f60efdf5edf403e8ed0febeff7f0e7feefeffa06fcfb0c040403eb01f5fdfef9e9fbf9f404e80701edddfddd0d03f9eff606f9f703efeff9e904f6fff6f8fefd07f204fafeff01fbf8f3fe0bfeff00f9f9fff6fafbfefb00fff7fcfc08fdfafdfb020303f9fffb03f9f6070401fd060aff05fcfefc0006fefefb0111d2fa0fe9dd04fbdefdeffeecee11d2d1ffcbe207ea0deb020f0001e2f3f2f2eaca0af9f8e901b60101fcf6fcf1b109c5faefe500dcf2d0dafaf7e6debdebe807e0f8f5f5090feb09ff0614fb03edf40503e7fb16fd0103090214fbf0020c0ce7d9ff06f4f1fee4f2eff2eadc0afb0201da1916daebf6ecf504f2e410f1ff00,
      4096'hf9fa01f6fcf6fdfb02f4fcf900faf603f301f2ebfb01e204fb01fbf0ecfafb0108eefdf2f7f20202f1fcf2f0efddedfffbfcf9f2e7f705ef0200f4ecfee3fbf006d8e6e1cfe285c89ad8c5b9e6e5efc5c700db90c2e1c8c3f701dec7f1eabcdcfea90df0dafe03e6ecfdf9e0dac0ca01a409aed9dccc06c0c5efe2b198b5a9b906d6fb2b08fe18faf60a06210dfd1c08f705fcf1421e1308f019fd1ef81213030febf20efb25fff8ff0a12faf81be9ec09f209190cfcf209000218ff25e806d801e10eecd0d5e0d0bdc2e8e0e7e814d8ddfee5cde2fdd7ddff2418f8e40fc8edf5b00311cee3efd9e3dee905f5bfaaf3b800c1e7ddc9f7c4ddf3f7c7dba8d1ebfb13fcfefaf4f8fdebf7eae501f4f6fb02f3fe01e7fef1e2fcf8faf4f0f6f6db0504fc02fffa010c00feffe5f3fbfb11fd01ed000afcfcf312fdf106fb01e7fcfff7070af9f2c7f8dbede7f9fd0404f3e4fce1d609f8ebda080c04200a06fbeaf8dc09fff7f104d0f9fee004f9eed7f4dbfff1f5d4e203d1ff06f9d3e6d9eaccfdd6faf2d4e6d8cdcee4dad9e7c2f9c6e007d5c1edfcf6eae10bf3dcd806e3fbe19efc01cff8fbd803f4f2f1e5ebd1fdcc05e0c6ecedfdd7cffde9c4c4b1b3c504e4fee1e0d38dc589e2efaafdd2fbeecc060599cdf7b6b0f50ddcd8ce17d3ccfdae0c07bbf5fddbf4f5ebf7dd9ec3ec9fefa8e2e1c8f9dfd6efd9cbbfb0b4d1,
      4096'h0dfe1a0c01fa1cdb0406effc080529ccee12d5fd13f5f70305fb1111180be81ae4d10c14f311fbe50df7174a1404d90dd904e60c1fddf7fff3fa1907eae408ddf80c02e7f7f6e5edd8fbf5d7d703e3eef8fdf705c903ecd302e9d4dbe7f6d4e8ee01f001f5ee020af8edede0e5ecf8e6effbe2f319fbfaf107f8d50ae002e1f9e80c04e6eaeb03ef00f6f4f0040de00e06faf50fda0e01daeafe0be9e710dceb080d01f5f90002f8e6f3e6e7f6ea20fef1f80b0df71503fc14fa0a17ee130b12f8e910ff03031e1404ff02f9fbe72feffcf8f6f10dfb130d0000ff1e0bf6e80af9d5ff01f11dffebf70601210d13e300f30ef819de00f604f6f81ffd04eb06c310daf6220c0515fb16fc021b18f704dbfcfa0deb14f80d2b04fd15000fff03e1efeafffd0cfd05dd0103f5f2f904e2e2080917f8e705fb07d41117dd16121418ed1af6c2e6f6ebf7faf9fee8e5f4defcfcfe010dcbf8f2e6e3eaf5f411fbfdd1fcf2e5fb0afc060beff3e6f7e9f717fae4f40004f7f501071207e003ea00f70af2fdf9caf5e1fdf6caf3daf1ead3f40b01f7faf8c21cd1e2fdf0efe0fefdf3f7fbe3f6f2f0f51110f4f1f9f3e3eb05cae404dcf0f315ffc718fae00cd5ebece50cd0f300c0b4acb8a3bfe0b6e3ecf6a6c40feca1ccf6c5c4ff0adbece40abfd100a40200c4fcf9c2e9eee4f9eabda4e892f3bdd8e7c9edbfb1f1ddbcb3b1aeb3,
      4096'hf900f7e8f6f8f2e7e6eaeae1f800f0f9ecef0006cb11edeaf8fefbfbf9f50afaf61609fafbf1f804fff5f3f7f2fa08fa01e5ffe1e806fff5f9fcf7f8fc0ff3001eb319fed9e9bad180d0c0adfad5048e9efcacd0d2d2dcadfd01f8e217f2a0c705ba0e08f0d701b3e7f9f20be8e080098004adcbdbc0f3a2c5fc29de80938081f9f1fcfcf401feec06f5fdfdf1f5fa01fefbfbecf90509f6fe01fe02f103f701eef105040100fa030600f403f7f8fefd02fbfdf6fb00030103fa03f8fefbfbfd11ee00fff2f6e6fafdf4ee0400edfbe6f505fbeb02fcfa03fc04ea0501efdbf9f3dffb08f102f8e4f6fa02e8f9ea06f5f3f9f80ce5f70603f20903d811fd0206f507f8e702f6f6f202f001f4fef7f7fcfefdf8fef5fe0906fb00f6f9f9fff7f102ee03f6f0fffc0e00fcfbf8ecf805ebf6e804f806f602ea0a00f302f6f40400fb02faeaeeef04ecfeea0b170aed020bfdfdead814fbea08fff9eee8da00030afce1070703fefd0bf309f6fbe9ecf8f801090e1fed03fdeef700f3ed09e5ec0103f8fbfd03f50200fe06fd04fd0c0307fc0605f4fefe0107f7001107fdfbfffff9f6fdfcfaf601f2fd09fa0afa0cf500fc0bfcf8f3f802fefd0302fc03f8fdf70fe9fd02f2e0bbeee5c8f2e9e1ebfed0d50be7bfebead1e2fd05e6ebe4fcebe601ce07f8eae4fce1ed05daf706caccf3bb19dde4e4e504cce201dae6e3cbe0e1,
      4096'h0a010c12fde7f5e70601fd20f4f80e030b19fff124160bebfa0ffe1ef80b05eef7e0fd15f800fcf7e3f5110407f7e6f70be90bf60b050504dbf611fa23d602fe00fcfb04f501fd02180305fb08f60cfdf803e0f812fc0019fd0a080e0a0002edefc9120207fe04fc0000ee1f01e8e4fefc11f8fbf1ee02ef08f616f4f8e5050aff04f8fbd4bba4dcb0f3ddc6d3f3e8e6c7f30fa3c917ebbff90fe5b6e5edc5f507ba0af4e2fc00c6fbfbf5dff4b5d9edacfabbe8f6e807bbe506d8e7b5acc4c2fcfafbfff9f901f801fefefdf8fbffff050001fafcff04f9fffbfefff5f8fefdfafbfe00fbfeff0301fbfdfbfcfefbfa01fbfaf8fdfd0000fffe01ff01fefcf9ffe2ebdde3f1aae081ecd8c4e5e6e7f3bafaf1a3b9eedda9f201d2ccdbfcd1f302bd0ff2dced0ccc0cfc01e7d9c1cff3a9f4bbe80ddf06c4da09f4c5c6dbbfcff6eafffef8f9ddeadce0e5f8fbf6fbd9f30200caf2fffbe5f80b09dfe70ee2f918d3fff6e6e90ae6eef7ffe4ebf9ecf5d2eae8daeedcf5efe1edf1d0e4c3d9dbffe5f9f5e9ebb1ddb4eceac606e0fff5d5fe16b5c8f3edb4fffddce2e01cc2db02c40106c402fed101fef8dff3b7c9ecb702c3d2e6ec02dded00f1d6b5acc3d203f10c03fd1c1111fe0203f905f707f503fae9f304f0f20805020024141505fae8ed0002f701ffdf040df0160c07de02e71501f5f8f0fef3f4f8fd10fdec03f0,
      4096'h03f2031ce5d4bce7c0ede5e8ccfa03ecfb0200f7ccfed7c1f4f7cbd6ddfdf300edfffcf6e1f7f8f214130deae1e4fb0cdcf8f2e5fa0a0406fefffe00fafccae607edfaf8fc000505fdff00f8f8040008fcf3f705fafa1dff0405fffafefae110fe05fff6051301020bf5f1020411fd0bf1f5f205f0f30209f5000106f5f700fff6dafa0913f70905faf900e9fe0a0b13050101eff3f8270a0f040308020fdffaf70204ff0aef04f401eaea09f0ecd203f306f7ebf9f20226ed031afefee600fb04ccf31f211312eb0b090a0df9050d010b1110eb10f6061304091d2a190e0cf9fcf8fbf514e9efd9fb03ef12ed03eafaea120802f5e2fa1febf313e701df1901faf806fafdf70bfcfef4010008f6fff10400edef07fbf00c00f7180df403eff5f6f60c01f7f000f1ff02f0fe16ebe500ff07fffa00e503faf1fefef80ef004fdfa01f5fbde06fadce8f0efebf207f701f8f7fd06dd110bdcf8f9e6efd4f3f0fff310fdf9e50003f5f4fdfde6e0fdccf7fbeeeff4f4fb00e0f2f5f5f4fb00e6db10010008f60ff7e2ef0d0afdfe041401f804f906090c030beffe060d0ffc0d07ee010300fe12fdf7071603140311fe0df30ff3fc0b04010103fe0503f6f6fcfe04d9fffbfce8fce9e8dcf80904faffe1e3fde8d724f408f001fa1003f105eef7fed10bf8fdecfedcf300defc01edd5e1e613e4f8f4d500e8ebfc08d7f4c401e5,
      4096'h020206090bfb01010dedfb05040303fcf7fef700f7ff0105080513030505100400e40807fdfd00fb0102fb150e08fdfdf60ffc00faf1fff8fbfafff30cec01fe000cfef209e0b5d4c1dfe3ce03f301eae4f7f5c1f2f7d8e3fff0ebf0ebfdd1d700beff09d4eb02f9fe0de5ed02e7d7f9c6ffdff4f2e2ffffeffae3d0d0d3dbd9feb4f2f1dbf0abe1a7fddacffadb09f3a7f3e9b2c0facdb4f815e3ece5fce1e420abf104e6ed0ec40cfc01ebf5c4bcffb7ffd6d9f8e1f5d6e406dcc4b6a7d8cbf3c8fee1bacf89b1a3c9d8afecddeccabf06e790c2e2bccb0102eec6cfeebce011a8f405c0eefac701f3e1e1e4c389f4910e8fc8e7d503b4c506deb49aa79bb9fefbf7fbf4f5e9ecf0fbeae2eef1eef8feffffe8ea04e9e7fff8f3eaf7fbf1ffecef060705f30406f5f600f9ebeb03e6f7fbe5f8020304fc0bfbe60500f7e9f4e7e210eecbdeb4d2a0d6d7afd9e8fcd1bb0509a8bdfaf3b0fb0bdcd7c2ebc5dbf2bcf0f6db05f7e7f7f8e8e6e2c2bae9acebadebe5d405bcdaf6e0e1a5a19ebcfe03131309020dfd04050cf3ffee0f080113e90d14010af8000c21f80ffcf906fadaf10ceeedfd04fa0df9f514110600f405f8f9fae7ee09f9f1f5f216e010f103fd02f204e5e9e0edf3f2f9f7faf8eaed0bf2ee05fcf8f408fd0df3f4fce9e7fedb020fe1fb01d500fbe4f2f3e1e7f4d305e304ffdef9ecf901f8c9f1f1e3fc,
      4096'h17cd00e9dadac6bc9cdfeebfebd903b1bbf9d59dc0d8b2bb00f9f1dada0bccd201b3fa07bee909a805fad2eee6ca98f299fec8c7dfc2f2c1d7fddee5b7a8bbbbffe4f4f4eaeaecf004f6f70513e7f8f1fdfbd7d110ebec04f608eaf915f308e9e4e6fbfdebf707eef1f7f10205dcf5020115f702e9e6f8dae1fde4e709e20bed04f4effd0ff005d80afeeff90becf416f2e410dcf80bfb1005ff09e900e8e7fce3110ff905f3ff030809edf9080106fff814f7f10efdfd030df0f700fcfef7ff02f8f80300f4fc0a03f1fdfbf0fefd03ed03fdf3fafff706ff04020600fd0f09f8ee0407020003fcf8f6f10bfd03f800fc08fb02f8fa03fdfcff00f9fff7f8fafac6f9f3bcd298d091e0eab6dafb01d4be08ee94abeac5a4f7f1cfc0b8eab5dc04bf00f7b3ef15f2ef07eedfe9bfb7ec9af5b7dae9cbf7b9da07e3c8ba99c0cafcfffffefc0000fd020000fffafdfe00fbfd02fffcfffffefefd0200fcfcff01fe00fdfffefeff00fefbfdfefdfefe0001fefdfffc03ff00fffffd0103010001e50cf9f7d2dc0b09fef2c8bbfdfaf8ef16f5040ff217f5e300f7dbc3f7ecf5ea0f13ef00e8dd0b04ebdf02e4f5d2eff4fef7cf0008f102dd1902ef03edfebae101ec09fef703fef0fddffa070aeb0ce4f9f9e9fc0ef70d1305030a040bf7f400fbcdfc03f30ffef60701ed0710f3db04fafc0bfbecf0f8f9fcf7f9f106e6fde9,
      4096'hf8ebef1c00f9ebfaf0f7ebd6e7f0fb02eaeb1ef3d50606e806ede9ebdcfff4090d0309fcf404f0edfff7fae1f3f5e1f9e9ffe3e0dd19f7f40cf507f2d6f5f9def807f50227f9ecea05f7f0e6ef02fd0e23f019e6f1de00fdea0405ecf9fdfdea021c10fef3d0ed071bf7ea1000fcfef406ff1807f3fff50d10f4050003150606010bf8f1f101f7f0f9f5f60105fcedfe05f302fcf50503f5f60607fd01f6faf511fcfefcfcfa040502f7f303fdfb02fdf008f9f6fd0200f50bfcf907fcfefefffef8fbf90cfe08ff01ea0407ea04fdf108f0dd0a14f9040df0010dfc0d17f9fe06f800f70200fff7f212e8fef509f6dffb0b12edf7f3fc03faf701fa11f405e301f0fefad1d3aeccb3cddac7e3f2f7cccb01f0a2bce0e3c901fde9d8effcd0cdfab0fd02e3e3f9d3ffeee6d2dda1c5f7acf0bfe3ebd0f9bbd0f1e2c49bb6abc4f3ff02f902f700f610eb020df80c00f101fdfee90ef7fa121402090df50804f3fef00b0af8f807f4fcfff2fcfceee004f9010401fef9f8fbfc04fcef03f6fafe0bfeff01030107fe0ee80009ff060d07fafbedfe05f80b00f5ff10fd020402f8f2f40102fcf8fd04fb09f20503f8f2f8f404f2ffeceefdfcf9fd07ec00edfd0104e8fe0503ef11080ef70a110e0004fbf9e8fe0a05fc140b060a08070ffbfa0013f604f41014fe00f5f6f103f203eb030cf8150ceffffdf8f3fe140d0000060d,
      4096'hfc02fcfafafffbfaf5fbfafefcf2f20dfff9fdfff1060cf4fdff0bf5f5fdf6fbfc0400fcfef9fc05f7f2fc0200fdf8fcf9fcfef6fe04fef9090302fefefaf4fefb140219dabff4f1c7f5d5c6d40405d4d406e5e2f129f9c8f0e6f303d4f5f3e3fecd090cd402ebddececf40ff9f9c816ce1de7e107dbf5dcf1ff0fdaceefded103ed0ff400fb0cff04f30407ec0205f2f40bde0108041919fc1711090117ef01ecfa030dea0c06f6f7f6f20efe08fc15f5f6f60df1f6f602fffd1efdf0ebf7fa08f4f5feeff103f813e30004080302eff008e6e600eaf308fdfd00ff1b00e9f2effbfa02ecf3f8fafdf8f41f00f7f603fb0107fff3e701eefdf903f506f1feff0d00060dff060bfae2fb0104f4ff0afef107ff050711fcfdfef6f603130c080ffff6fd00080a00fdfa0d0b030804f90e0308fb0a01fb03fe0403ed04eefaf3000ee9fc09fcfdf5f40eee060102fbfdf7f6fdfff612f3f31103010a06100cf9eafcf4fe01f2f0ffe3f80ee60f00f8eeeafc1f04ebefebfa02ebf103080aee02eaf4ece9eaec27f3f4f201f8fddc18e10214ea1e0d020305e9f0eafdfcefea09fb092df7f7ecedf613fb16f9e916010725f6041509f8f7051afcf4f2020318f2f807e5e9f9e7d5cfe3e3e203e204fc07dfe7f8e1d4f800eeecf0f701e1ea18e4f1f8bf0606dff6fcf4f8f4e4f9ebd5ebecddfcc8fceadbede8cff4e5deddcccde7,
      4096'h022000f7ea03eee8d4fd00f0f904e9090f0df903f018fde9fe0303f9f1f7e40516f9080bf6fdff00fef6edebe0fa03f3fd0d04f60ef4fef31efa0514ecfcfefffdebf9f4aae080de97eec3b3eeec02e0bbf0fa9eb5f3dcba0211d1b9e227bee51c9bf70cd4ef0ac611f103ecddc4c1f898f3b7cde3e4f9c1c7f5d3d29698c1baf3dc050dfcdad4cde400f3f5f1ee0cd8d9f0e5d6f2f4f5e8fdfdf4e6fcf2fa091fc60afaea08fbe7061cf6f905fce9ebd223dbfb00eafafafc02f2f3d4e4becefaf5f705fceff0eb04f3040102f2fef7fb02fffae4fd21fe0100fde102f8f61afef7fbe9effffff4f905f10b0317f5faf0ed07f7ee05fd01ec06fd0202f30e12f20301ebeff8effb02e900fd02f5ffeefe02f4ed07fae806f9ff05f6f70bf6ebffedf7f9fdeb04fe05faf11001d5fcf7f4f3fcfefdfcfffdf8fe08f30af6f7ff04f10102f4dde1dfe7ea06d40700f7eff002ebdffdf4e804f60f10e1ec18ecf1fae7f703cceb0cfdf609fc0f02f0f0f1f1f9e813d8eef5e6e5000ad5f6cef6dd23f8fdfaf00e00eff3040c05fc0308f5e9faea071d0326f00c08fc081601060af7f40a1bef0afee3131e0ff9000ff902f20af80220ee00fa01fdfe02ebedf7e6fdea07fdf3e6d8f8e2f7eff3f1f00cf7f40febe1fc14eeebff03f7f8f014f0fd09d605fae6f8feefedf90101faf3e7f2f1fdf1f0eddbf8e6ebf7e2e8f5dfddf5,
      4096'h0aee1501f1f610e80b02f6d706d30ef0f904d71500f412070eec02101809e31de6e4f101f719fefffdedd903261df8ece1220a08eaeef3fff7f405fbe9030fdd06f502fceff7fcf60007f9eef7fcf5feedf901f8f60709f500f8f7f6fdf6effafffdfdff010a00fcf8f4faf4f2faf9fb03f7f3f6f70100f7fe010200faf9f1fe01d6ff12d8e4ade79df3e0b8f1dd12ddb7ff05b6cbe6e1c101f5cfb7d009caf707a80cf9caf108d4e80ef9e0f3b2bdeeb2059adde2d300bef905d9d59db2c3c7fafb00fef607fff606fff812fef5f60204eef80b090a09fbfefa010102ff080d0608fcfff30a04f2ff0801f4f00afdfffeff02070804fdf709ff00030604ffed11e3f6f7f7ee0eff0ee508e906e2f9effaf7f9100fefddfcf303ff0eecf3f6f0f5d2ef01fdf9ffe0efe5e20ee2f1e6e8e80b04f8e1e8f505ddfbdfe601e815ec0eed032bf5f1f0efeb1512fd01ed0f29ebfc0a00e8fa1fcf0006f1e7f3efe5f5f1ba08f007ebedec06fc0905fdf6f6f1e017f6f8c8fff5e2f411f2fadfb0fdeefa0cdeec010f11f80cfffdf513f0e0171bfef108eafa0b09f1e9f1f423f9e7e504eb02ef15fd0907f6f1ea0b00ef23f4fb061c010e0b0523f7f7f3110205180f11d3f90ff7f5d1f6e8eafcf1f1020af1cd13f8cfdfeccfd6ff0cf3d0fbf5eaf4eed3fef3efe2f7ddfef7f70bf6edc3f6bd0bd6ebebecf9ddeaf31fdfd9d7decf,
      4096'h08eaf2ed01faefdde8def8fb05e501e0ec05e7e912efebf9fb050e06f503dbf100c6f60ee2fffbe4f6fceaf4eaece8ebe6fcfae1e5dff0fdd7ffdddaeed4dfe2fdd0f8feeaedb8eaa5ffdfbbc6dcf202d00703cbc2efebd20300ced9e5e2cefce6d209fce2fa0dcb02fa01f2dfe7cce9c7e1cad3effe08ded405fce0c9cbcfcdfd00fe00fff406fc0bf4f805fdfb0ff702fcf2fa00fff70cee010305ff0503f5f5f706fdf9fafe05f204f70403fbf002f9fc03faebfa04f7fbfd0f0106f7fe06f808fef2f00bf3eaf1f1efedf9f9f1fd0af805f9e213ffebf2f8f9f7eefbfbf90efa02fcf302ff05fef8fdf402f90100eafafff701f902021003f205edfcef00faf4fcf8f7e4f5dce6e3ede8f5f305edf905f4d8ffff00f100130e00ebfddbed0dd8fe0af0fa06f1fb06e4f7eae7dbf1d4fdecf0f3e500e6f6f3f3dbefc6dfe312fe081f01f307fdf9e90311011afb0806090ff10601fef904f9143001ff13ef04e6051702fdf1ee13f9f8130704e3ff030cf904fbf30104fe05070010fbff0b03f8f702f9ff06fc0b00fe00fdf2fbeefef7f4f80bfb190714fb08f90009fdf4fbee0108fafafbf7f6f9eb0c06fdf006f708f809edf9f900f503feee0204fd07f9d7f403dbf8eff8f208dbe7f5eaf009f3fbfbdef3edddf2fb0801000706e6ddefe40d0202f0ffd403ef180303efe503fbf8eef4f6f703f4fefff6e309e80cf6,
      4096'h03f10d07e3d9efddd5f1dfd0dddf03e4e8111a00d80df6f3fef9e9e5d1f4caf6e0dcfbf7ef010df609171209e8e9fbf2e9f8d8e40bf7fbe1d6fd07e3ebf2dcdcf3faf4f2f9ee07d6f2e1ebf30ed8f7fa0ff301ebde05e0d4fce5e6e502faf8d81809fee9e3f10901ff04fd02f3ed07f3e7f9f8f004f409f9fbfaf30be108e9f600f703fe00fa01f7fa0000fffefff4fffc01fc03f5fafe05fa0104010004f407fd00fe01fcf6fdfefcfdf4fefb02fb02fe02fcfef5fd0003fd0104f8fefefd0312f0ff17f3f902f3f613fe21f3fa2cf9fffefaf60d0829f706070409dc120a0efddf0a01f20a06020d2b12fb061706de07010bf8100df812eaf9170e12e4f8e60b121623f00cf8ead91913fbf4052202ecf9e711f1ed0def00f6fe1dfb00f711ee1e0406f70dfa101a0d0603f9150c10f51401001e16f6fc18fe03050819f4db06fafbfefefc0cf503fefe01fe0108eefbfff8fd0cf3080afbf80205030600fa00f20105fbf703ff02fff4080af9f7f8fafe0200eeeefff6fcfffffd01f7fffeeff2eef5dceaa4ed8cd4deabd6f1fad0d407fcb6c0f2e0bbf709d5c0de0fd6dffebef0fdbaf40eeb030bf4f8e2b8ccdbb0efdaddfcdcf6c2e2fae1ccb6afb1bbfeeff60df705daf4d7f0fc0700feefeee5f8f6befffaf008060af2f9f302fb0300ef01ff000c05cd0706e208faf6e7d8d81ad7f0eef8f505dbf305f2eaedfd0d,
      4096'hf2dd04fdd300dce4caf9efc7e9fef6ecd2fff8f0e4f8f5dbfbf5eaf2f302d905f4e109f6e2fcfaf8f6f8f7f8e6d7e3eed5f1d5f0fb07f6dee7fc01e7dcd1d6ef00e4f9ded6e0dee0c6e7e7d0fcf8f3eef2f90cc9ca0cd1c8f4fed6d8d3f7ecf9f1e0fff9c7f80be6e80adfcff0dafafed9f8fce5eadefed5fefdddf1e1fdd4d503f6fdff04fb0202fffcf803f709f505f8ff090600ff0300ff0605fdf90101f3fffe02030500fffdfdfaf800f801f7f6ff0306fff6fdfe05f8fdf5fe0af500f512eff906f0ececede2e6e9fcf8e605e9e5f9dcf314ebeeedfb01fffefb06e1ece6cbfafde6f70acd04ffe400fbecea07e511e3f0ecc9f6e0e1f9e8d6eccee2e002e304f4f3dad2e7f0dfeefdebe905d4dfffeecefce7cfeef8fceef6ebfbf1e00bd600f3ecf802dbfcf9e3f0fbdad4e5d90df8fedae1f8e3f000dfd9f2d6e6de03fafc0000fc01040400020003fc0503fafd00ff020308fe06ff02090a00ff04f5fefdfffe00fffe0300fafffb01fafcfb06ff0000fd00fefbff0603fefa00fdf5cb000dd3e0bbcdabd9f8a9d8f9f8d1c30ccc94cce4d3bdfed7d5e2e3f4c4dcf0b70ff09fedf8d8edfcdbdef8c4a7fcb3f3a8e0d2bcfbb7ba0002c1bfa6b5c3ff06fef0edf0e8f9f305eef801e7f5f7f6f301f6e60c08f9f2fcfaf1f2fdf5fef6ecfdfcfa090303f1f0fbf9fafbfdfbf6fefc0603fe02fe06f9faf900ede3f7,
      4096'h14d30c061ffcecf9d8f7f6fb02f204eddd0803c6fed90901061409f70801f8e9fd050dfdf7dcfdf0f600db14e8f7e0f9ca09e9e6d0effa01fff1ebdce5e711e2ffe612f3eee5c2f1d6d6e8eafcea08ece50bedd0e1f0e5f0010cdeecfa16f0e905d7ff08eefcf7dffbfbecf2efb9ccf2c9eaefe6e8e60bd9f102e7eae1c9e0e4feed0121e7f7fae2f3110713010e00fa1c02ea001c07d2020700f80dfcf41efc07350de9c9150501ec100cf8fff9f50517f3ecfffdeff5f211f417ff1614e1f116e60c22f0020ce8edf809f401ff11ccddfcde191ae8f50efa08050ffc01f811e1d80403eefffedf030dea1e1112d6ffe0fbfa02ece4f5fad4f20aedf8d5f2d800c6fb10cace9ed094c9c4afd0e901d1c507fba1b5dfdba8faeacac9cbf2c3def9b706f8b9f721dbf004f2cced9eb7df9debb4e8dbd208b9e2fff4ca8b97a1b40803fefe01fb05f504f90400f40100fffdf6f0ff01fc0907feff04ff0902fa02fbf6fb01fbfa0404fefdf60105fffef9fe04fdf8fcfa02fa040604f904f8fe01f7daff0d170cfe0f1a0d0bef150b0f162c100b11f6d8fb1106fcf30b0f0c0c05fc1200e8f6fff9f5fd0bf7fcfb0512ee132414f7fc06f506e4ffec1d051e0e02fd04070400fefafd01e9ff08fcfafff0fff8fdf006f9ed0cf4f7fc00fe0100f303f6030200fafdfdf700f40df6feeffd000305fee8fefffb000707f907fb0103
    }),
    .CHANNEL_BETAS(2048'h77a9787c77c678297833785d781f77ce789b789d782b781a782877b077fd78a678747848778477c1785577bc778278247775785c7860785777ca784c7796781977f177b0787f784778dd7862787977be76f3786a777077b477dc770577a2781b77d477d877f5784e785b78a978147819783b77ff782c779e785a786077ed780e777d774177d877a978a5785177f4785c7862785477c477dd77d7781776c0785a782e78e87811784f77b977c37842780977c8785e785a777a788778a777fe781577c6789277ee785f77eb77e277e5785c786a77f778317835787177ff783b7830784b771d78bf77b8781b777e77de78b37843783f7817784f786177e877e577c7),
    .CHANNEL_THRESHOLDS(2048'h020701f2022d0206022101f302270231022c0205020d021301ff0213020a0216020102040206020f01fe020301ff022401fa0212020101fb02060234021b02170217022801fe01f601f2020a01fb021f020a02090214020f02230202020e02210212020801fc021d020102160206021a0229022501ec020b021b01fb0206022e020501f4020f0206020f02200214020801fe0217021c022a01ff021b01fb020c0201020101de01fe022d02120209021e01fc01f8020d0204022001ee01ef020a020f01fe02230207021b0215021a01f801fb01f101fe0203020f0223021701f80211020b020c020502240213021b0208021a02260202021d0216020401fd0220),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00db),
    .ADAPTATION_DURATION(16'h136b)
  ) actor_down3_pointwise (
    .clk,
    .reset,
    .in_valid(e_24_valid),
    .in_ready(e_24_ready),
    .in_payload(e_24_payload),
    .in_completion(e_24_completion),
    .in_bin_tag(e_24_bin_tag),
    .out_valid(n_down3_pointwise_valid),
    .out_ready(n_down3_pointwise_ready),
    .out_payload(n_down3_pointwise_payload),
    .out_completion(n_down3_pointwise_completion),
    .out_bin_tag(n_down3_pointwise_bin_tag),
    .actor_error_o(error_actor_down3_pointwise),
    .initialization_done_o(initialized_actor_down3_pointwise)
  );
  logic error_actor_enc3_depthwise;
  logic initialized_actor_enc3_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(128),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'h191227e1ed16d1d1e02530112138f6e8eae8f80ef1f10c0c06051a3e0527071f22170b17f5f2030900f806ee03fbeb02e5091a0f3606e9eefc25fd2b2d2512f20323fee3ffe9f306ed1500fde8030df817fb19250cf710060d0ac7dbb0c4ebb6a6ec0bf0fbecfbef07ef05f302f309080207100f1000e7fd0f0f1509f2eef1ff001713ecfb13f7f1f3131212fafbf2ec1cf90f170cff30011b0c240734301228fc232419d4272bbdfd15b6fdf3fd08f8fcef19ef0cf9fd1808eb1b100332112d26ee29383f5d0b022d090a08200c4a0101070c01faeff1f04019233c06151812252bf1fb23f51221f60df7e701050bfd03f6f13124ee17fbe3021dd801fbf411f902fcef1109e8fafa0ff6f20cf822fb33172a02ff13f417f50a07151a131c04f1e8fadff1f7010e0d1918050c022616181e16110c021ef7f415ed100cfc0bf42105101c08efeeefeb1508120f01fafffc02f900edf6fbee12faf20cfe060237254211352a061d1a08ecf3eee706eaf4ec0f0e14020e14f31b2b03fef303f8f0050bfd09fc0106f50b1e2232011d0cf8090301f30b4f471206121b0c3d3d132c3c382f2c3e182cf9ef080ce602fd00ebf20cf2f1d71aff0016f6fceff6ea032606f8f906eefd00020efa06f010f60afe101105f01312d61ce9e4fc0ad0000215030afef7f21b1a14f11815f20406edfa00f8ecf0f4f80ae707010906f8eb161a,
      4096'h0ef4fefff8fdf1f8f7fe010008fbf1fb0c1506e7e6f8071cfcfbfc1df909f60cedfc120d06fe1707060e28f81c09150817091ff20f1812e3d7fefe050a15f608fdf423fb040aecf5f2f7d90c17193042444d17f3211c0533342153f600f2f101ef01f4fa15faf81504e70306e8060ee9f0ebe503fef01e0b121a0911e801011d2bfe1b06213f265e08fefc040f1ee70a07190919f6021103f813f11de612fb2f243532f408e60d0e0203f2eb20fefb00fb0707391ffd07f01513001008091e1126d5bee3200ed706f80b12f01604fef907082704e7091b1f19080c1aeffe06faf211ed05edecf6f102fb0f2e061207003919fb18f6e6090a1d20ea01f610200225faf8f7fef015e805f6fc004c0b221c0d0f21f2f50aecf814101ef70e28140407f6ec0604eae9f3ea03fbfbebfa0c110304e90001f2160b1217121118f1faea0205ec0bff0519fae3fafbfa0606283c4c132016100534fafd0503f0030c0902170e110ef810f5f4f3e7e5ef08fff50e0a03fefff3f902f308f207f8df2705011d231d38fefcebfce6ffefea19ec17fccfe9ede1f0fbe3f40bece021ffdf101bf31718fff7141b23061f07130a15ed0a1804e652051432403546f605f6fd1406f1f519180223f603fcf70c0e170d0dfb0e0b2a111f181c06f50009fa1cf50f1105e9ebfd090a01fdec01e9fa0b2a0c03fffbf5fb1711ec0bee14f7f6201de41c,
      1024'h17f90504000802230c211916eefd09ef16110d10ef08f814fd030b0206330d220309142305e2040af3f60c030002fe03000e06070108fbece309ff381e243c1a530bea0cea010507fe0d3a0d27120a12e8ef0800ea010efb22031f1902010a0811f4f210f70ff00cf3f4f90b04fcfb111c0dfe160e2b36feff1ede04ede81119
    }),
    .CHANNEL_BETAS(2048'h7939785677fa78dc77d377e478697809783f782a77a9782e780977fe780b7813787b781d789277fa77f078ab77e977e777c277fb77db780677f877f477a7782677e277fc78317794781277fa780d789677b7783a7773778377f4782178a2780477fd77c277d87804782e7802782e781c77f577f077ba781c780b77ec7837784577f7772c77d877fe7828781d7818780077f8784c780e77fb7854781b787877ff7805783977d2782177ef7814781d78017850780a77e9787077f6789d780377da780477df77ed77e378537781780678307827787e77e6788277d0781c782477b877ee77f9780e77dc77fe77d877dd77da788877dc779b784977e777df76a97816),
    .CHANNEL_THRESHOLDS(2048'h0203022601f101ce01ef01e801fb021601ec01d60203020201f201f101d001f701ee01f30212021901ef01d801f7020b01ed01e201ec0202020301fa01f301f001ff01f4020f01fe0201020701e801fb020b020b0202020101f701e201da0203022001ee020e01e6020e020b0200020c020f01e402010209020a01f401ff01e201fb01eb01f50223020a0212020401f10201020a020a021501e801f901e001f102020215020c01f0021f0204020402180203021201f601f2020201f701ff01ee01e901fc01f4021a020e0229020b01fa01f501d601f301f001ec01f201e201ed020101f101ea01e801e201e101f3020d01dc01ef01ed01fe01f5020f01f4020a),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00be),
    .ADAPTATION_DURATION(16'h149c)
  ) actor_enc3_depthwise (
    .clk,
    .reset,
    .in_valid(e_25_valid),
    .in_ready(e_25_ready),
    .in_payload(e_25_payload),
    .in_completion(e_25_completion),
    .in_bin_tag(e_25_bin_tag),
    .out_valid(n_enc3_depthwise_valid),
    .out_ready(n_enc3_depthwise_ready),
    .out_payload(n_enc3_depthwise_payload),
    .out_completion(n_enc3_depthwise_completion),
    .out_bin_tag(n_enc3_depthwise_bin_tag),
    .actor_error_o(error_actor_enc3_depthwise),
    .initialization_done_o(initialized_actor_enc3_depthwise)
  );
  logic error_actor_enc3_pointwise;
  logic initialized_actor_enc3_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hfcf9fa1501ececf2f906fafb06f0fd090521f1f6da0416fc0afdf5fd04fcee11e2e2f311fdfe05f9fdd506d40316f204ffeef8f6e6f5ec01f502fcf407e4eff41f07fc050301fac30305f7f8000d00f90ff7fde6f5f1fc031201fb07f6ebfaeefffcf611fdf5f5e5f42ceaf214fc0103fc06d0f00600f1f80bfb0b09fdf615f307d8ff180704eae9fa08fbfbfcfd0700f7e8d4f9fef5f6fe0610f6f9fe040a02f8f6fb02fe04fc02f5f9fbe60706f504ff070306f7f7fb04fe03fafcfffd0bfcf714fa00fa04fc12f6ecf6fef5fff4f9f70301f205ffd9fef802f80006ecf7f90506f6fa06f4fc0702fdf306e701fc00fdfff3f3fceefbf102000e0cf9f804f3e8fefaf1fbedf5ec00f608fbf5fffefee6f701fa22eae2fefbfbf809f7e8fb08f80805f7f9fd0aecfe10072af7f2e706f5fdfe06ee06e6feee032418fffc05f8fb0b030801f5011efcfaf40008f0f71ae20e03f6ebfdca09e0fcfb0e0710fef903f7feec0601ecf205eff11f0307050900fe08fffae8fcfff5ff0ae9fbf8fcf7e304f51afc13fbeffe02f2000a03f8fdfc07fb0502f80b01e91201fa1df2fbfb0f0400fc08ff05f1f3150610fdd6e9fe04020202030702fdfb03fcf20b08e60a11f7fe03f9fbf71dffeeee05f8fce808ecff010803faf404f2fbfaf9fbfa060702f6faf7fdfd06f707ff04f9cefbfa01fcf20009fe0700fd1206feec03f40a00,
      4096'hfa0bfaf705f92008fefef7fafefbfc010007fe0104f50902e80dfa0cfdfe00fffefafd03020201f60004f907f9e9f4ffff09feff0302ec000502fd010106e8f803f5ee000404f80602fafc0103fce602f50005f006fc02fd08fefaf9f7f2eafa04f803ff01fefd0501effb0404fd0001fceffb0200f0fe0402f9f50e02f9f9fbebdbf40afefeedfbfa1303f70af3f911e2fcc4012dfffc01fff80601efef0319fdf1f60f0803f8dcf3e7feff1100ebfdf616f403fbfaf6fffcfb06f2f8f10af9f5392600010df00ae904e5f3e215f10300fff31dfef5daf3f902f2e000deeef801040826f2f403f9ff01e20711f70626fbf7040508f6050406fc06f6f40927facffd00f1f800f008f2fefcfb00faf507f4f7e7f9f9eae7fed0f3fbedfa02fcf6f80904fb07fe02f7feecf507f8cde20004ea02faed08f500fffffc040905d6f8fcd6dc03ff00fff5fdf4f908e5ffb0fce8fc05ff05fcef12e009fafd07eee60affe91103fe09ffeafed9f8e4d6f8fde5f7f109fdfcedff01f0fedae3fa0eb914ea02ff1205e5f7ff04f409fd02fff9faf4f8e5f82705e3fdfb000021f80d07fb0ffe02fdf905f0f9f121fe1705e81806fdfcfb01fefb0202f907f7f700fdf1fbfed012fffa03f71012ff1cff06feed0dd3080318fb00ef0217fb05060a13f301ff000608fdf8071303fa0606f6080401f8f8fafafdeff702eef608020208f400,
      4096'hea02faf8fe020308fc030302fd01fbf9effefa00fd02020103ecfe0601f8fc000dfefef10401ffef0101ffec03e7e106f5fcff03faff010100fefd0308fff3fdf4f1f7050501f5080af7fb0607f6ef02010102020505ed05ed00fbf5fefb041400fbfbfd0200020904e801f7f4fafc0e01f7020704f3fc06f8feec04fc06e40dc3d90cd2f0faf9fefaf50cfdfe00f8f2e4ffe0f797bec3fad9fdecb401f9f20011c7e512fa0bfcd600ecf4e2f6e39af90300fbf6dcdcec0b0efae506ecf5cfe8b980cdf8fcf6069601c6e8f6e4ea8200d1e3feb4f2f4d0cbca090beff41b80fafb00f3ed0df4fff5f9a305d4df0a09c808eefbf5f5c9ebf2e30e8011e8ea8400e7f700fbfaf5f503f6f2010500fa0000fe07010c0200e1fee3fcfe09ff06fdfbf5fef9f8fa02f9fb02f8f905f5cef205fd030604e5f8f7fc00f9fbed04ffebf7f0e8e606fdfcfa0604fdf80008f5ce01eafd06f9f10002f80306f901faf7f0fafcf6f8030c0906fafee90802fdfcf9f6fafaf1fb02f00306e404eaf400fbfa04e11605e5f402ed1f08fd14fcfaf6ff04ff08f104cfe7c506c3fc02fc040de7f9080614eeeb020f11f3e90109f9e5d6fb030afffee50ef5fe0ff8f2f504fcdaff0c9fde05120108e6011eff02e512be05f215faccfb06ee00f00904080316c408f80402060808050000c005eafb02f8f00cf603fefbf0fd0be1fe9efcfcfdb5fe,
      4096'hf6f000f5fafaf8fffbfffdfc04fffefcf6fbfafdf1f8f500fbfcf8f70000f600f5f502fd05fdfef1fee2efe7fe03f8fe0204fdfdfff8ee030503f5f8fdfbf302f7fcf704fc0104e9fefff905f000f8fb0301ffed03fff803fefc0203fdfef902030201fcfdfefdeafcfbf7f00101fefe0003f8fdfcfd01fb05fce7fbf9fafdfbde0ffbf404fbfbfe00f7f8fcfbf4fa01fae7f508e6ffe005e6f7fefcfeff06fdf8ff090407fa000aee0d0007f7def6fdfa0c07f9f5f7fa07fc0101f90505e5fdfde4f4020801f6fffaf8fcfa0100d2fefaffffe604fc1a00ed06fef803f1def503fbfd00fb0af9fe0ae608fa05fbf9fdf6fc0608fee9ff08e306cc0b0101cd05edf0f0e906feed0106fcfc02f9030100edfae1feb7bbdafcbaeb0addf2f6f700f1f9f3ff0007f6f903def5e6f4deddf8fbfaf8fde9f7f8fb09f9e6fd02fee4e802a7e4fffcf60bcff3f9fb01e7f4d8fed2faffe6fef6edefe10100f100f4dcfa0507f9f702fef7eef7e5f9cfe700faedf8eceff603f602fecd07c3e2fff5d7fed3f2f0e3fc03e500f2ecf40af6fbe9f7ecdc12f1aec5c912c7e104cbeff4e1f7cfdff3e807fdebd5fad81acaedc69c0afafc0500e9f7ed02fcfbf20feaffc1e2f892cd09ed010db515dae310d1dfdbefd2f807b9faf9cb01b008f8d3f1f5a2ea01eefde9f4fef8e2e18f159bc2f5fef401e7fefc0803f304d1feb1dbf3e29503,
      4096'he702fef102f6fa0002f6f8f702f601010805f700f5f7ee08e4fefe0003fff4fef00b0600fd03fafffefafc1704dde802fff905fceb0501000301060406ffef0afedaee050704f9000409f6fffaf1dffafa0405f1ff040804f70502f50cedeafb05fffe04f9fd02f504e7fef8f9f6fcf601f307fafbf2fbfcf1fae0080104eb0402f5fcec02eff8effdfefdfe0104fefff5e4f1fbd4e1f6fcf5f901ea0201f6ffe7f6f80104fef7f7f2faf9e7fdfcf20800020003fef1eefc0402e303f5f7fb00f9edf5fdf80107e103f7fefef8fbfdf3fffcfedefdf5e2f4f1fd01eafbfdedfc030b03ef06f801faeffafbe7fcfd05eaf9f1faf3fffef9fc0003e603f9eef2f403f2fb16fefff9fafb08f8fa02f9030408f9eff502f0f201ff08f9ff05f7f80202fffc04fefdfbf0fdebf9eb060ffffdfe020001fc01eefd02fdfff5fdf7fffef711e8fe01fbfdf9f2fb0103f309f4fefdfbfcf302ffeef8fbfe03f0fbe6f70601fefb05faf6f5f505efedfafbfdfd01fbfcf5fc04effffa06fc0605fffa09f8ea0500fe01fff2fcfaed0206fefdfafdf400f000f1f2f1fef001fefa000106f1f507ff01010205ff05f7fe0cf9e1ed050dfffff9040ef3020704fe09fdfee408fee6f003fa00fcfc05100e020907ebfe03ff00fafc08010308fdfcfd0bfdf9fcfaf7f5fe030701fbfef802f8040dff00fcf805f106f7fcffea01e807f800edfd,
      4096'he20400fff7050b02fa02fbfc06f6f3f7fdf7f7fc10eaf602e808fb07f60202fc0206faf6fe03f4ecf3e0070803eef000f2f508fbfe08fb030afc0c0407f3f00e00fff8fffdf5fb150100f300f0fde9edf303ff0304f7fb12020403fb01eafe00fff900fa0004f601fdf8f4fb0000fbee04f1eb01fdf4f9fcfefbf002fd16030afefa000201fbfffffd0501fe02fdfffffe05f6fffd0102000000fffd0101fbfffc000004010000fdfffbfafa0203feff010101000100000101fffbfd00fc010202030501ff01ff00fefdfd01fb00ffff00fefeff00fef503ff00fef5fffefbffff000104fffe000103ff00fefffeff01fdfef70000fdfe020000fffeff0001fff0f8fdecfdf8f2fa0209f90503fcf907fdf2e2fedcdef1faf2f901effcfaf2fef6f400fafb0502ebf3e8f3e70301f303f903fc00fcfceefe00feef01fbf7ecfeede8f9fffffb04e4f8fdfe02ee04f4f9fefb04e90103ecfbeafcfaeb00f9d9fa0003f8ef01f602e9f9eefad9f00204f401f7f001fd0000fffbfcdbfffbf6eafdb5f4f7c1f4e6e302f1f60ff8f6f8f9ff02f6effba1d3bcffb0faf2defc02e106efe0f8f6f60607f2f4e0fce1f1abb504f4f207f7dff8f1020d0aefed04f6cd02f484ccfa03fff7b60904e209c9f2a0f7d60300d5fa00f0edd6fdf1f703eca2ef0dfbf7ef08ff03e602b9fdafdaf8f1e100f503fdfaf0fefdcdf487f4f805800d,
      4096'hf3f9f5f80600f0f7f1fbf2f60cf0fe07f501e8fd0703fb02eaf402df06f6d80302f602110dfd04e9f4f806cefd010001fc17fefafbf5df06f405eb04fee208fdfb25090800f700e4f3f4e205e708eef10801fcfe0601cffefc00fafaf8e5ee08fd0f04e60afdf0fdfe00fddfe5f9020e0803f51005fef6f411fedcecf6f8e7f7c10809ca01f3fa0df3f5fffdf8fb05030d03dcfbc2d7c2fed306fcdbf901f1f7f3000b06fdfcfbfd01d8f4e7f2b1b5fc07fafef8f4fded03fc01f4fff309e2010796dff90603f8be0203f1ffe6eea008e90b03d9fdeef30ef70701f3f6ffadf405f4fcfc1609ffee04c5f8d2d501f1f013e70304ffe306f60104abf6050688fbecfc00fbfa10eaeff905fafb03f80303eef5ef0a01e0fb08eff107fa0e02fa06eeec050f030404fdf9e3fef504fbf904fe11fb04eaf9fb03f802eb02fc00e207ec11070404ffffe4ef0df5f9e60300ff06f7feef020efbf8fa0504e5fbede510fafdf8f1f8f0fff2ece1e8061af9fafcf9faf4f302e4fc040efceeebf9f8faf4faf5010105f9fbf7f814f904f500f505fef0fffefc04fcfcf9f6fef6f60efc0a0ae9fcf1fe01fad3fc07fffcf9e903fd06f70500f905ebfbf5fd01fefe0dd501090bdf01fdfff3fdf9e407080402f400f4f5fd0dfffce5fffeff03e6f6f10e0006fcf1e200f3fc02ff0c04effbfdfd06fcf5eafd03f201f9fbfcf4ed010518f0,
      4096'h07f90505040102f9fbf609040901fbfa06f2f4fe03f7ee0100f404f1fef8f201ed07fcfffc03fd02fd02fd13060609fefcfb02fdf900f7fe06010ffe04f80af9ffecf3010201f50efafe0a0000f408fefaf600fafbf406fd010302fbfdfa02010203010400f602fbfd03fdf2f80200f40006040100fcfff9ed0208fcfeff0701f5fff4f3fcf405f1f5f005fc0008f3fbf9fff3f102f8fd02e5f1fe050504ee0008fff7fdfe01f9ec06f9eff8ffe9f9fd040dfafeef02fa0401ff03fdf5fcddfe04f5f502f8040209fbfdfc0cf1fd01f80afa06fd07f2db0ef70401e500f3fa1b04fb07fb04fcf707fce706fbeaf6fc08fefbfe0005edfe06f9f9f00b08fdea01e1ed01f0fc0113fc0601fb0105ff02ff0efdec0afeebf300f212fe060408f502f80602fa00fd00fbfd03060805f8f50103fc02fe0001eeff02fefb0100f5ebfa01f3eafffdfbf421000002fe0606e000f4030a0e03fffa010c01fa09fdfafd0b01fc01fefb06fb0306ee0b06e500fdfa04f600fefd0701ff0cfef70b0300fe07d4fff9dc02fbf0fefbf2fc0704fbf200fd02f101e608e707cbfefaf3fe0003ee01f503ecfcfe01eefaf4fdfd02c5d9fafff3fef7f5fbfc050805f7fbf606e0fe15c4eb04fa02f7f6fd06f900f0fdbcf9f3fd03f20601020603fe00f5f8f6d4f5f9f905fe0005feff04e1fae6eafdf4fdfb0003fbf8e70002f8ffe6faf702d30a,
      4096'he3fc010003f6ee0cfff3f3fff8faf40505f602f709f5e6fde7f4fdff0509ef04f804faf70303fdf801e2f718fad6f009fc070103e904f6fbfcfb0f04fb00dffaf4eee5030609050b00f4f70205fde7fefb0801fdf5f6f4f9f60303000af7ef0200fafaf502ff00fff7cf0009fd0004f4fff6effd05fffa03e301f3fffdfefbfffc07fb0503fc0a02fffdf8fe04fefeff04fd07090a01f701f70efdff0400fafc0407010102fffd0401fef90802f2f8fd04fefe01f805fc00fefeff01ff00fd0901fceeff05fdfa03010107030afdf5ff06fefffd01fd010307fffb0000f8fbfffc01fe08ff05030300edfb09fd0000f901f6fa03ffecfd01fd00fa0d0100f5fdcce800c6020302e2fe0305f204fb09f4fdfae9f08dc2c807cef1fdc6f500f602e9e303f2fc08f6eff8dbfee5f5dfbf01f6eaf609df0ce1040206e3f70ffccc00f58ff303fdfd09c005eef606e5e79af4e4e301d2ee04e4eedc07fcd9f9f6a90302fefbe50302fbdffae40fc7d40bf7d303e8f1f1f702f9edf0fdbdfbf7f6980e120af7f8ffeef9ed00fc1cff0b03f902fa06f60906070201fef40301fe05030413fefa0f0500fd0301ea0406f906f0010805fefcfefefbfc07ff060cfffb04fefaf929fd020108f201ff0503edf705f413f9ffecfefdd4fa0300030cf704fefb0002fd15fbfa04effa0507f1fe0006f9f8f9f7fbfcfa0006ef040103ff000400,
      4096'hd0eefede08f4f3ed06fdfffd03ff03f6f1f8f6f4bac0ed04cff3fdcdf602ef05d2e3f706fdf8ffe2f3ccfdbe00f3db09faf0f507f1f6fc0605fcf0fafdfbc809fbb3f5fe040504bc06ebecffe001b9f2d8f2fad3ffffe8f7d705f8e1fbedb30004f405e203f5fdecedcefdc1e2f9f4e3f7eff3f7fefeeb030204a6ebf9f5c6eef4f5ffee01f0f0ff00e6fd03f8fdfef4ee07fff1e2ff0303e0da0decff0309fdea06fb01fbffec0403ecf902f0eaf9f903ee0803eb0ff4030702ef01fefef0f4f5b0fa02f00404fe02f70c02f2ed0505f4faf7ea01f4f9f9f5fafcfafdfcedf50107fbf101fb06f4e9ff03d2edfa03f8eeff010500f5f704da04f5eafffdce05edeafde405f2f3fb03e2050706e8ecf1f5ecd3ef93a5e1fec7fd12e6f20804fcefebfe0502fbe8dd02c1f9d3eff2bc00f3ea09fcf205e6040d08e90906f3ddf7ff94c903f1f701bb050cffffdfe1e5fdc80207d5f4ebe50af0fdf7cefe02aee6010b03e8f5f603faf5e6008ee9f1feeafefce6e301e90303d605c5e004f4b5eeff0dfbf9fe0010fcfcfef000fdfefcf802fffffc0b0ff9fdf90801fc050001000dfcfe05fe010308fbf7040104f0f2010a0303fefb090a050200fa000401f7fbfdeef4fd05fafa11f7f3fb0218feeb000103ff0304fe0e05fc01fe02fff3f8fa040006090200f90308eafe030a01fef7fbf700ff03fc04fdf602f4040301f605,
      4096'he1f804dc00dbe4eb0505e9fcfe05f9fcf0ebf6f6c7d8ec00e4f0f6e3f705f901dfe4f505ff02fbdaf0e2fdceedf5d200f8fffe06fa00e5fc0402ec09feffe3fe00eff1ff0301ffd7f8fceff6d604e5f0eff40ae102f5e4f0e6fa0be2fff8d2f0fb0d00e6fdf4f9e7fde902ebfe0305f2fbf3e8f8fef1fafdf1fad808f8fadffdeff9f8ea01f914f8f80602050af6f8041b13edf7ec0818f9020a03f909fcff06fff70c14f60400f6ff1103070905ebff05f900fdf7fcf4fdfa01fbfffaf5fefb16f2220203ffff06fbf808fcfd07f300fbf50afafb0108f815ff0505f8eb0102fd03071efc04fce31311f8fa00f9fe03ff07e3fb000400080bfcf71100fc0602ebfc0001041017fc03050204f5f701fbef0efb08ff09f001daeefb00020104fcfd0efdfd080203010dfc0d1805dddc01f9050505ef02f8fd07041007fa09e5f9edf9e80007fbf21bf6fe1602fafff4fa030202fbfefdf7fa0efafae7fde0f2fb02f921fcfaf3f8fb04e1f7f1effcf6fd01f50901010702fd01fcf2f6020201fbf3fefd0efbf400f9fcffedff02fef900020afafd0c04fe00ef0300f902f90102fdff01fafe0201f7fffaf60dfbf0f90302fffb02fa00fc03fcfe06f500fee5ff05f9e8fe04fbfd130108f60107fbe7fff6f900090000fc020b0302fbf9faedfbfef603030001fffe01fcfbfdf8fcfefe01fbf7fc04f602fff802f5fe0001fdfe,
      4096'heb0a030e02fe071a01f7f907fef9f90024f6ef19ee03fe00f50601f31013010018fe03f50500fc0a0313fa02fae203fe0d0101fb01fe04fd06fbf808fc08f2faf5f9eb01fff9effe09090cfc1607e6ff0e06fef70001fff71105fafa10f8f805000202fd0209fcfe0fef0012fe08fdf401fef5fcfd020300e403fc0e03f8f200f2f101f305e7f50101f3f70000fa030ce2e4e104dfd6effef50a00e5ecfd0709eaed01010903fdfdf2ecfafcf702ebfe0307ff00fff6edfd05feea0506f1e8fef1eef400f8ff01ebf9f806f9e7120cf0f1f9f5e907f5e8f5f90205f7faf1e1fcfd08f7fbf8faf9e6f1ecf8f0e0000def00f0e601fdfffafef7fdf5f8fffefffe0001fc0501fe1a010404fbfefffe040308fd100206fa0101f70efd0110fc00ff04fa03fe04ff03090500080104f8f0fffafefffd01050204fffd030807fff200fdefffff0202fd03fa020003fcfafefefb01ff070906fe020cfd01f007f7010600fc0607fd0afefb03fbf602fd0001f601f8fc02fcf3000003fe0508ff0bf905f8f500ef05f80707ff01fcfe02fc00020503fb01fbf1fa05da08fbfa0002fdfce705fd0303fe05fffefcfc0205d8f0fc08f2f603f806f5fbfd020c01f6fceb0c0bdff00400ff030b01f50602fbf1d9f8f6f6fef400f701090f03f9fefff2e70dfcfa0206010bfe0205e0f508ed09fcf0fce60902f5f1fcfc0b01ea07f9f8e0ff,
      4096'h0909070dfefcf50c0bfb0104ff030004000b07fc02080002fefafc020402f4fafe0308ff01fd0203fdf4ff0dfbecf700000a010300040303fcfff8000708f50502f0fd020001030b00060804fa06ff05080efdfdfb05fb0211fffffefdf5f104fe08f7130603010c0008fbf7fefdfffefd01fa0302ee0501f2fdf507fd02ff0dd3f5f7f8ffeaee0bf600ef07fbeefdf9e905eefabc07ebfac703effb0505e4f8ece907f80300f7ea07deedeff0d1dbf5f1f800f3fe00e6fefb08fffff9fdd5f3feb9e0ff00faf4de00fcf8fde4fdbbf7ea0ff8f2f1fd08ece1fff7fafde6bdf4fffc03f4ff00fce7feedfee0edeefdfb00f702f801f3f5f5e6f3b3ee01f7c604b817ee17fbf50ff608f9060209f5fa0213d6ec04cdc3fdfea30905e0e4f2d8f5040b24f80604fd01eef209f302e6f300090dfdf6dc04e9faf10802f5fcf2cff2eac60a05f4070aa3f616e00df118a6ed0003fec803f11602defbeee2ff23a0f4fbf8fff204f9fe1ff3e2fdcfe2fefcdf04f4effcfcf2f8f9ddfdc601f8fec2f9301c061bfcfcec0202fd05fdfefef3ff091e1600f1b100fbed070be7fcfc080215f6fbfd080602110b1ddfdbfcff0904f7f2fbfa0506dfff0203dd0503f10001f4d8d2ff0002fec6010dff070510fd02f506fbf1020719f9f8fffe07fdfcde0401fd08dffcf0030df7e9faf0f513f8f9f9fce0f60afefbfcdbfdee03fbfae603,
      4096'h20e5fef909f1f0f002f908fc00fffefaf9e8f7fd03d8ecfa0aed01fcf502f9ff030bfdf9f6fbf90cf4fa0901eefe01fdfef80302f9fdf2ff06020405f7f9edfbfc09eafeff000d00f80304f4f8f621faf6fa00d900f7f9ffe802f7f804eefffafd02fdf2fafbfdfef8f4f8fd0406fbf4f9eaf2f5ffe8fffdf5f90bf7fcf905ffbef206bafefcf4f906e801fd000e01ffe806def8b6dcb2f6bdf5ffe10000f401f0f2f6fdf9f608e400dff8daf4d7bc08f8e2fb00cff6e30a0ff8fef500ffd3faec80d408060afaba01dfe912e40399eed9eb07d9f318e1efda03fddb02f9a0fb060203f70bf7fedefda90dbfe505fafcf9e6fafe05faf0f3cd0a9a01f0f4a7fe0d0d0108f106ee0c00000200f407f702f102f60af905fdfdf805fffc050706f90b0afbfa0304fafb0007f60500ea0a01050e00fd02050003fffcfb0304fcf703f7ebf00605000906010d04fbf3100301050401f0fb060303f101010dfe0ef503f901ff0200030203fee60305f70d040003f306fdffeefff9fa01f501fe11000200f5ff02fefc0002fefb03fef8fb0703f1000600f0f7f0ffe90300f50403f9fbf507f6060bfe06000dfbfff807d5f003faff0102fbf4010402fe09fe08fdf00bf7def005000210f5fc06f1fe0212e5fa04fbfbe4080108f2040503f807f5020003f6030a04f403e6fbdff6e8fcfff6fc08faf60a05f1fdfae500def9ef00f8f8,
      4096'hf405f8f906f7f408faea02fffdfc04f814f80ff2a4e4d9ffb81df6e201f708ffdfeafbe9fcf9fb03010401f0fbb0c0fc0115fe06fbf9e60402f80df3fb06defceeb7cf050cfdfbc2f718dafaf6fcb6fae50a07d4fe02ea0b34fdf8d9f3eaa3ff04f705e8fd0a03e7f7c1f4d3ce0cfaf906040a0605f5f304c4f9990f00f1a105f9ee00fefd08fbf9f500f602f9fd0303ee09f8f000e2e904dff8f6f00205fb020af601100201fcf50111fdfc03deed05f30a0504f3000a0702051ff508fbf1000407ff05fcfcf90af9f9f202ecf5f0fa05ff000004fae5fef40304ebfef2f81402f509f800fe0d0303d800e8e3f5f8f800f41709fe02fc00f3fef3fa0109e4fef5f7f2ff090402dfea0500ee05f21301f907f1fcebeb0306ebfbfbe308f7f7fffbeefb00fbfaf8fcfee902e706f7e70b0318fffff304ee000d08f5fcfefaf3fcee1c01fe00fefcccf6f4e2fcfd0dedf4e2f4fef205fbcaffee07fcea04f9e20efa030405fa0007d90c14f1f2e3fff81201fee211f9f408fb24fbe10df0f4edfcf308fcf7fdff1d01fe02fbff05fffefb05f9fafcffff0a02f710fb00000111ff0007fb01fc0004fb0412f8fe06f9ed0001f8000200030403020009fe0001f806fff7f5020303f806fa02fa02fdfcecfffd03ff07000209070f0100edfeef0105fefe0701f901fbfe01f805fdf5000003fdf90efefd02fffd0100fb08fd06f802,
      4096'hb6fc06ac0aedede60be5120504f6f501f6f9e2fb8cb8c9f8b0e701cfed04ef0be2e7f3fffdf9f4e901dbf4d3dfceaef9fcf00900e1fbda070bfef70e0303beeef380ca0afbfc0bb3fbfee5f3f4fa97fdd9f508bf05f8cdfabafdfed0faee9f03f90905e40303f4e4f9b700b9cd0514e203edecf5fff7f7fbbf09a1f801038906f1fbfc050ceef1ee10faee00080e09fbe309d0f5fafd1807fbf7f4f407fcf607ffe6050a11fdfde8fad005fd00f8ec010105050aee04ff0303fd1315f9f308fffe0e1305fefc01ed0bf4e808f513f4f500fcf91002f5d3fefbff04f301e7250502fffc11fdfae4e006fff0cb02fc0316fb0fec030709060307fbd4f300f70ff507ecfaed02efe9d9f5e901f9f808f1f4e9eed4efb4b8df01ddde06d3f5fef400e1d6f117f402f1f7edd5fdbff3f4f305fdf60106d7fbd9fc0608da09f9f7c3fef1acf006fc0703c8fd0900f9daf9fcf4dbeafac001f8ddf9dbfff8d8fff7c5e9030206de02f9fcead6db07c8d806fee7fbf7f5f90210fbfaecfcdbf7f7f3cbfbfd03fd030107190b03f5f1fefcfefd05120b0cfcfbde02fee918f7fffd03f5f8fffa09ff000100fd0019ff0502e6f5fe06f5fcfcf903f10109fe0102070bf00d11d5e905fc07000e02ff07ff00f7e5f6f807fd140e0315070202010709f3ff01fdfa0310020efa00fbe2ff0e0c0efaecfdf3ecfefc0502fa1bf90514fe0cf403,
      4096'hf30401ec040df9f8f908f4f803020606f6f8ddfbe8d7e2fbf4f9fdeffb05fe0502e6fc02f8fcfdf5f6e2feeb0408e9fe0005fe04f1fee6ff06fcfffafbfd040906f6f404f600f8d80303f2fae4feeff8e6f902e2fdffe9fdf8fb04e1fff4dffefa0302fefd01fcf8f5e7f4e9ebfa00f8feedf7fcf901f4faf9fdf203faf6dffcf8f3fbfbfdee01fa00f2fffb000108fcfcf9ed02f2f7f5fefb0dfc00fa03f1fa00faf903fffc04f503eafef0000604020203fc02f1fbf003060307fdfdfbf8f9fdfe01fbfffff5fcff00fa01f7fef3f9030003f0fe00f9090203fdeefcf3ff020004fbfffe01ffff03eff9f107fefc0404f900f8fff30107ffffdefe0300e9fa0004f9f500ff05fef6fe0ffd02fdff03f306ee02fe020efff801f9f900fef7010afbfe110402fff6f5ea03f303f6f70404ff0104fbfcfafeff02f8f801fcfff9f6fc0f03030200f409010103f109f8fa06feffea04fdecfff2000209f9f704f800010009fbfaf7f304fefff5fd05fefffc01fcfbff050009fbfff2fffc01faf8f6040505f700fb08fff9fffcf7040304fc07fe050809fefdf909fdff09fafef50e0d0601fd0402f7f7f70206fceff5fe01f3fd000603f800ff0102f8fe05f30208ecfb0003fefe02040afc0009ecf00a0208030500fd0a05fa03fb0106fffa0301faf6040609fff9fef2fa09f8f7f9f2fffd0509fffd000011fdfcf5fdfff707,
      4096'hcdf3fed40aeef3f403e003f8fdf8f601f403f4fab5dcca02bded0ecef005f601efe5fefbfa0506ebfece01dde8d8d00106050209d1e8e6fb0009f3fff6f9caf8ee9fd909fd0308c2faeae906db09a9ecd40606cafeffdef6d7f700ec02f5a9f80a1000e704f0fde7eeb9f5c5d60901eefef9fdf0ffffe803eaffa0eff8f0b205eaf8fa000003090900fd0206fdf6000a060317040c0a0301f706fcfd040404f81112fbfe0204fa09fffdfc0a0ae5f3ff030e08fef401fefdff020aff0202f1ff08ecedff0306fd100004f80311f1df08fefffd0f03fc0e1afb05f8ff00f8fa03fb020b0f0006fbfa04d8fff3e7fcfdf2fdf81504020201fc0c0209020005f400fa0b0504fdfb0a00fa000101fbfcfaff0ffc020109060cfeef0afaff010308fcfb0304fd04fe02fa04fa02030ae9efff0af4f8fdfefe000104fd00030500f50b01f400010401010b0000060400f1f6fd0702ff0709ff0009100500fc04f5ff07fdfdff070401fbfd04fafb00f700fef6fef10501fceefffc0cfdf4fefa07f702f01703e90af407e9fe0d06f909f8f7f8e713f005f016120513e8fbe3f3fd02042af30508fffe07fbf60b07fc031ceffefb0502030b04ff00f7fd0bf5fff622fbe80018fcfe01fcfbf30af7050517f3fe1202fcfd01fbef0409ff0004fce5f4f006f8061afbf804e90a0afbdf0f02ff1a01160501fff10706fdfcf0e906ff0f04,
      4096'he7ec01e30dee1be5fb04f7031bfa0b08f0eee9f604f430fa03f403edf3edf80cefe4ff1602ff03e403df11ee0200fa05060d06fce2fe0306f403e8f707faf109f8041ffe0704f4feef01effdf1100a060808f73bfb0700fef30303dbfcd50717fe040516f2f7ebfe1008f1d10fe80513fcfde00f04f800f42d07edf5ff0805f6e90108d3e80af00c07fe0e030306f3f6e30ffd00cbe5e9facde909e3ff04fbff16010605f8fbf712f5f5030cfbe7dd060cfdf800ea05ee05fa010405ff02e6ebffaee707fd0004f9ec0704fbe9f7de07f011f5dd06f8f700f00304fd0101d7f5fd10fcf500fffce6f6dcfeeefcff08fafdf5f9f303f2f8f5c501dbf2fbffc5f0f0fe0001fffff2fb0cfb06fb0201f608fcf9e9120ffdf904f6f7020b070517fa040103000205f1fb0ffe090e01e2e9ff05fb02fcfbfc05ffff0311f70804f106fdeef9020007f70508f8f506fff6ed01071008ff0c01e702f503ffef1705f5fd0405f6ff0807060efc06ff02e9fbfffd02fa1203fcfefcfae902fbf604fdf810d0e7fb18f2e6fd10f408f5fdfc03fefcebefdef90feae702e0e9f3fe01120b00f2fdfefdfb05f7f3feeaf71afedcea03fa00fa01eefaff05070511fd0805defafd07e2ff06ef0c1803f8f9fbfdfccf05f7f90510f9f500faf603fcf303ecf8f0fffafef8060dfd04fed6f90cf3fbf9f702fc0cfdfcfffa02e4fef2f1f700feff,
      4096'h0f07fefc02fb0cf9020af3fc00f7fd0108fbfc00ddfb1305f10601e0fbfd000a04e1fffcfe0000dffe0b050afbe7fafefefffbfe030300fe0003fcf2fffcf2f403f9ff050302fbfdf301f900f911fd08f406fe04f9f508f806fefdf602eff30801f90000ff01fe0106ff0af3f2fd0217fbedf4fe05f8fd030efe01f1fd02f40de405fcf906fa120cfaf900f901fffb04000b04030b09f802ed06f2fb0ffafcff070bfdfe080402fb02f6f60f03ddf80501fefe01f3050004030201020505f9f80ef0fafdfcfd0203fb07fc0af7fade01fffb090c00fcfc110201fefcfdf9f60001fb0807fc0403f9fce0f700fcfcfaf8fdf106fcf8f306fd02fa04fffd00ef070bebfa08fef9fd00f702ff0309fd0202f9fb03f80ffafa0108fb02030cf9ef06040100fd030305e700f709f907fa05fefcfd0001fcf802ff00fffa03fdfe0406010cfc02fbfd0711fcfce50308020cfef603fc13f9fbf404edfcfefdf3f707ffff00000702fafe07fbf9eefe06fd02010002060100ecfc03020406fe00010cfa040b00f3f604f41c0afe0dfafe05fd01e80bf5fbd6eef509dde902fefcfff6fd09fa0702f70406f7020101faf9f5f2fefd00fef7ec03ee0107fef50cfd03e1f306b0eafef10417e6fc0c0209fcfaf105f412f3ea02fdf0fe0dfe0c050804e6f8fd0208f905fa01ededf401fef2fe01eb0100fff4fcf2fdf9cc0ad8fcff07e6fb,
      4096'h06f6f9f7fb01f6f2fdf30003ff03fdfdf6f6fdf7dfe9f2fe01f707fefcfbf0feecf2feff0203fc03fce501e8f1fbf602fcf30801f8f9fc040401f3fcfbf9fef9feeff3030302fae4f9fd05fde8f805f805fdfff6fff4ecfde3fd02edfcfbf8fb0403fae8f7fcfef1f6fb02e30008fdf0f8f9f400ff02fbfff102f3fbfffdfdfecc02fbd4040bdeecfeed0000f90ff5fedcedfdf99adac60bb7e80ac3eefedbf9f2e7f00dfc040ae512dcf9c600ebca0003fd0208d3f5dffdfc01fb08fef5be03d693cf06fa00ffaefeeafa07d6d9c7fccf0a00bc01fedff2d203ffc3fd07ab0fff0b05ed15ef02e7e2b907c5c508f4e9fffceff7070002f7c108bff300068ff5f8fc020ffcedf700fcf9fefefffcf2fc1beff901c9f8e002e31affebf405f5fcfff3fff6fcfefef105eceeedfbdafbfc08fc06020ffcf1070602f4fdfd0ae8f4f7efd70103fb07eb0516fa050b09ecfafffd01f5fdf81efaf904f909ffe4edfafaf4fa06fbfff5f5fce9ffeaf60403f202fbfefd0403fff80804da0100fdea01f7fbf901fe0bfefa0503ff020a0000fff10ff70002050702f8f7000dfc020d030b00fc05fd0102fcf0f1060b03f6fefdee06fcff08fef700fa02fafeff0706f6fc03130103f6ff0bf8fc07fdf508f2fcfaf8061404f5f405edfefc0cfb0103f8fdfb0303fe0102fe06f9f507faff00f901050501fdf7fafc00000204fc0305f7,
      4096'hef02fcedfdf701ef040203fef7ff01fc01f9120009040d07f004ff0306fa05fb03f802fbff0102f7fdf0f3f3fee6e80002f80303f6ffff0105fc0efc0502ea0f06eefa0404fffd0500f3f6fd09ffe000000401fcfcfb020002010401fffdfa0400020c090200000909eefd07040400f605f8faf7fe01ff050102fe03fefaf0fd321f0301fb07fa11f8fd1c0602fbfdf702fad806fdd3dd04fffb0aef0007fe0206fc07f6f7fc0c0e07f4f8f9f205140a03180500d9fcf502f80607f009fe06e508e8f105fcfd0bfffc0a05fc0f0cf50de20ffbf8fcffed04fbfffe060d14b0f0050400f40c08fe02f8fb0c06fafc0002fceff7fc0601fbefd4feddfffc060707000b0403f9f11f01fd0206fdf9fffe0012fefe05f8f601ffef1500fe07fbf7fcf80106020300fefcff0efbf1fcf00202fff7fa000df9fc00fefc05f303f8f30504eaf200fffcfb0900fee7050bfaf4fafa03fcfb040516fc1202fdfffcfef0fefdf704040104fdf9f7f8f70805f4fe0006f5f5fffdf9fe0407fe000cfd06f4f8fb24f90d0104f506fbfdf806f902f70329ed0c13e9f0f5ffecff0103f2f8e4fff9fe02fe00fb010a0c06f7f201f001050a07fdfc1bfff4fef9fae3ff0402e501f2e0fc05090d02eb0811f80e2416fcfff9f9fecbf51402fe10fcfd00f606f20501fb01fc0007fded10faff08f703f9f8fe0efef4fc0d0321e7f6ff06feedfc03,
      4096'hf406fef401041208fff90202fffb02ff07f9010100f9fcfd010afc0f100409fbfc01f7fb0002fa05060b020107fdfcfdfe00ff00f8ff070105010802fefdf9010aecebfe01fff304fe0f090101efeefdfe04fd1503fb020b0402fdfc0ef50bfafff9f70007060bfb00ee01f5e90100f602fe0005fff701fe0f00fdff000bfa01fdfc00fc04e6fef9f70c0afa12f80304e004ea02f9fd05fbfafbfae5f5fbf308f602ff07f7fc00fafadbe7edf608e50700fdfcfc04fd03030101f6f2f5fd010dee0420ff020206f1fd09fefde70af601130201f602fddffef0fd030a06e505f8ff020a07fdfe02e9ed0afce6020605fefa05f006fe0200f706fee109f5fc06fac3f4eed0fdf7f1df0dff0e01f9fafdf3f3fbe80197a9d10bbbeb0ecff0fafb0f04e8feff0807f7d9f8e8f7c0e6d4a407fa00f600e7dfe9fcf506fe18f9f5c0e9d289d9f9f3fb10b2eaf2e3f8e3008df0defef9cc0dede6fcd407fae4f6fd9407fe15f9e602fd01e4f5b4fbb4e70804f807e0f5f3f5ee0001eb0289eff5ea910ae8f702feff02f9f5fb07f602fefd0605eefae105fce7fe0005fc03f301fb07fcf1f2f9fdfd0302f0f9d6fcf203020502030a0206f9faf8fe0303fc00fa00e9fef2fdfb00fd04fcf3f9f6f3fbfefde9f5fdf7f5e703f7f101f90009e2faf5dffd0108f804fffffcf80211f7f6f3ffff1501ea00f806f4f8040601eafd00f9f8f5,
      4096'hf804fe0dfb02220401f8f5fc00fd03010dfb05f906e8fffded0dfd0af9fb11fb050109020203f906ff150a060dfcec0102010500f205fe030702fd0406f3feff09faee040501fb0a04fb07fdf905ec01ecfd0c090500ff0f1702fdfb0cfe05fafefb03fb07030806ffde06efeefb03f3fff7170cfffa0107fef9f816fa10f405e0f3f2e5fc00f3060cfcf3f8f4f2fe1507f400fae1ebe705def70b0e010f0500050100fe0a01fb00f806010104ddcc02fe0cfc0c0d0a12fcfff8fd08f8fff413e5c7f207fa0d0ed80a07fb03f8f8fc09ee0cfe08fc0bc706f0f9f6fcf810cc02f60603e60702fb02f5e90005f91500f8f500fb05f0f6f9fdf9f4da11f6ffd30c0afcf80e04e7fceb0311f7fa0e02050efdf9dc07f90727fa02f7fcfff1f6ff0cf2e9f5070403fcf500fc061304fee001e8fe040403fef604fffe0efbfafff2020618130200050206030e05f3e908fe011ffa0605fae9e002f9fb01f6fae90efdfd0cf814feebf4e2fe04f5f817ed0a16f4fdfd070705020108fc0af206f017f1e90100e5faf914f60108ed03fcfbfe0223fd0bfdebd7ec03e018050606fcfef6f7ec040f04fafde800f9020605e4e002050508faf600fb04ff040a0d07fde006fbdddffe00fefae303f3eb0606f9c906f4fd06f900f8020efdfc00e4f5f1e201fdf3fcf9030905f3fbdafff9f5fef6f200ed0bfafae6ff080affc821f104d303,
      4096'he2f700fafaf6f60800f30105f7f9fb08fb05f30905f7de0ed90402f4f503f7fcfc1204f8f901fd0af2fbfc1ff3d5e50d00f50800f306fffbff020108f807ed0912dbf2020a0404fcfdf70707f8efd605f2fffff8fa02fb080504f503fffffdf5f8fd04100a1004f107f5fff0e6fbf2f4f901fe0a03eb0506eafaedf1ff09ec04def4fdc409f7f9ea05e3050102ff0006e3e3d2fcb2a6d806d0ec04e4ec07f706e4ee0409fafdfcee01dd00dae7f4d602fb0002fbefe8e1fc02f9e80b00ffcdfbfcb7e7fff80b0ac5f8f800f7f8f6c8f3d50106c005f4e4f3cdf5f9d906ebbdfe040b07e606fb01e5e8d204caf205feecfbf1eff0fc09f3fdeb04c4f4fafcb7f80404f90300fd160100fbf8fffefd01000802000402fd02fef20ffe090101f8fbf805fc010401fd04fcfbfdff01f5fa0204fbfd0004fffaff000200fa0201f40404f7f2fd05000009fdfb01ff04faf80002ff020109fe05000b00fbf5fbf807030201fb03ff02fb0803f000fe0100fdf901f9f80001f3000403fdfb0efe05fa0104ed01e9fcf1faf301fe02fc01fe0001fdefec02f9ebecfbfdf9fefd06fef106fff9fffdfa01fff5f6f8f4ebfe01f402fe02ff0000fef803fc03ef05fe01faf7f4fdfc02fcfdfff5f905fffff8fbfffdf7fdfcf7fdfdf1fefefbfff6fcfef0fcff04fffe02ff00f5fa00fcfcff040502fb00f9fefffafbf6fe00f8fdfffbf600,
      4096'he813fef805f90321fcf50901fefcf6fa0dfcec05f1eecc02c705fcd8fbfaf8fff30507fdfffe011c01f9fd06f0dde90506ec05f9fa08f80300fafaf5f807dbfbfadada01fc0811f90319f8070519e00ef207fde3fc02fb000607fd06f7ffdcfd0709f5030a0a0adafdde02f3f211fef503f8fafeff12fc04d405d91602fdf8ffdd0007f8f9fde903f7f9f0fafdf406fc090fff0005f5da02e0fdf5ff0000f4f7f8fe08fe06fcfdf308ee0a1a04d4eafd0cf7fd02ebf60303f9050bfdfdfde5fd05f6ebfa0200f00cfcee03f9f9f5f3fdf8ff00e4fdfbfdff0bfa00020aecf605fdfe05f9fff9fffdfdd8f60af6edf5edfdf00cf101eafff7e7faf3fc0201f406eff6fd020103fefd0605f7fbfffefafefdfded1b040e0000f4fafb00fd0202f8f40afe05fefb06010105fc1000ebdf07100605fcfe090006fdfdf9050302f401ebfb0b03ff08fd0c03fbf80b02fbeb000e0afcfd01fee807ea03fee707f4fafbfcf4fd0f070706fe0203ff00d901f4fbfff10e03fc0dfb01fcfee200ff01ec0600f9fa050002fcfc0801f4fe10fc00fdf6ebe4070ffc0707f8f2fd0ff40200fd050a01f504fc06fdfbfd050afbf3fd04f40afdffef040400fdfd00f9fc0808f80205f5020101000e02f5fc02f5f7f102f405011205f9f302eafd00070205080ffefdfcfa02f7090e00fffaf7fcfdfafdffe60cfefdf103f6ee030efffd0bfdf6,
      4096'h30f601f8090ae3e2f9efffff070805fbd8e4dd01ddc0eaf401f712e2ee0107fc05e7f507fdfef6e6ed01fecbf501f207fef608fde7f8ef00fc03ebfef6fd17ff13cf0000fefefadafbe30b00e9e50bf0dfe9f3d8fa09dd01e3fcfed001fbdcecfaf3ea0103ed001ffb02faf5eb04fdfb01e6e6f1fbfffc0ad4fdf8ed01ffc9f7eff801fa00f0edfcf801f1fffbfafc06f8e9e501fcdaeefb04f5fefafafbf407f4f7eb1105fcfb02f8e1f6fcf3f7d4010602fffaf2f9eb0302fdf205fcfbee00fcfbf603fafffff4edfafcf1e40afdfbfffcf9e400f7ecfefffbf6f0f7ddebfafb0700f003f7fdebf5fff6ddfd040505f806ec000000faf9fbf9ee09fff7f5fffbfcf8eef8f1f9f0f7fbf6fd05fd04fd0618ea08ef0a2007f90703fafc01eafce6f6f503fffcffee06060b090106e006f5f6fafd0201feffff02f5f1fa0001fcf8f102fc0205fdfdfff3ed000407ff0106f7ff0afffc050bfc00fde300ef1cf5fcf7fb16f8fafeddff13f8d80702f716fcffec06fffef5070bfcfa1606f704ffe2fcfd050001f11b03f80400fd02fefe0803fa0c07f4eafef401fa0501f8f701fafdff03fe05fdf5090afa06fbeaff0004fa04feeff7f4fbfc02fff50402eaf6f7e9f1ff02010907fc05090000f6ecffe60cfd07f502f9f6fa04fe09fef2e4fdff0602f50108f7fbfcf90702f6fdfdfaf5fcf701fef4f9fbf0fde6fb04fdf203,
      4096'heb0aebeef2fe26f4fefcfa07faf000031eff21fee0cef001f22ef5e0ea11f4f9eee701e807fdfde50f1103f90dfdf007f8f3eaf20cf1eefe01010600f8f9fd1707d2f3fd0afd0fe9f407fb06f702e4fe04fbfa020500f5051503f5f0f006c5fa05f40d0afcff00f3020217f3e301ff0c03feeefbff0306fd2ef8e507fa18cefbe6f50601fdf9fc0300f800fc02fcf9f81205f70ffd05f6fbf3f8ff0f090419fdfb00fcfc030502fb010519120ddbe200fcf601fff6fe000307fb1115fefcfa0104f6f008fd0af71703fef40bfcf6dffbf708fb0a0601f202f5fd03ec0ff9f410fcf8f5fe0007f90307eff8fcf3fc01ee05fb15fffaf9fff9f403e7f60304f20ad1ed00c6f703edee01dc0c00f3fbfeffede1e9f89eb0d1facbd10bcef304fd0ccff50316f7f9f2f404da05b6fedcbbfffae40a04dff2dc040ef9e00d0c05d5f10189d1fbf70b04a2f7eef008e0f4bff7d5f3f4c0fbedd9f7c601fdda07f5b6fb080c06e100edfbf2dcb607a8c60009e701e9f6f60a0303fad508ceeafff1a00212fe080700f00d0b080309fa03f701001f0bf7f3f60b1c05fb04f5f507fbe9f30fed00fe0601fcd41203ff0406fef80307f20000f90ff8ff050402f0f90b100006ef10fffd09f6effc11f5f1070007021102f4f1f9f5f01512fefd04f0fd17f5fb03f8f805fefbed120b03fd170bf705fbfff0fa01e9000118f31802f9fb0a00,
      4096'hf50009d705f0e30f02ec0308f700f0f500f6f7fcc0e910f8e9e6fb0ff7fdfe00ede20305fd0706e6f6ff04d1f5e8e8f5fee70508f00be3fef9070400f7ff07f7f4beef03fb00f6dc0102f1081200f3f7e3fc07da0007edf2f5fdfafafdfde1f10201fff5f10802f0fcf600e3f20500e6fcfff6f604fdf9ffe307ddfe03fedef6181e00f60411f9e303ed03f5080401f5e4fde9f6d2b8fffae5dffde0f202f40ae8dbf8fe09fd01e812eee5c3e8f3cdf8060bfdf9fe01d6f70102d90cfcf9fd00e1d5f506f00202d1fbf9fa00dc0ae2f8e6fb02ce04f8edfafaf7010dfeebd9fc070a04f700eefce7f0adf2dad70d12e5f8e9eefa03eff6fdd902e205edf8dc05eef80106fff109f603fcfbfd01fefefd0705fafe00fd01ffef04fb0b080602fdfffffcff03ff010afffe0a06fd02fe01f6fcfd00f9fdff0200ff03fafffcf7fa00f00702fd01ff04040bf6fb01fefe01fafc0400fdfc04000d02fe0704fdf6fefefd04fd01f901020800f90c0100fa00010102fefd0cfffafb02fe0e0302fdffe60bfaf7f4fded13fdff0204ffff01070ef8eb0ade000bfbddeb0cedf3fef500030506f6fefdfafafaeb0205f9e8e701fde400040801f1040904e7fcfb08ccf500d8fafafffffbf303f8fc12f2f8d400f41cfce102fe04fde303f9f906f5daf9f9ef02ff070901f5fffe01ffe500fb000a0005fa00fbf7f8f6fbe0e107fce501,
      4096'hc60901ed00f4f7fc0101f6fcfbfefafe0004fef9f404ec02d7fafdf501f9fe02fdf402fb0800fcfcfbf3fb0e05cad300f904fff8f1fdf207f9ff00f105fdd6f30cedf0ff090500f1fdffe700f8f2ca03faf5fff80cfff9fae90102fcfbf0eeffffeffb06070801f8ffdb00ebe8f50005ffeb0203fcea01faebf7c8ee03f4c7fd0806fef2fefc12fffc09f8ff0400fc01150ef506fd082202f60efd120209f6fe00fcf500f9010506050dfd0104fffe02fff901010cfcfd01fffd03fffdf3060502f0130002020008060512010802fe04060a02fa0000160413ff000601f106fcff02ff1df906faf8040005fc02010206fdfa03070104031416fdfd030005f9f8da0512c6fc03d90d0afef416fef6eff8daf4e308a5bcc109c2e504cd050efc04f3e60105020307f3faebefececc999fb030a0909edf4d805e109fb0b0802d0f5028cf3fef6f90ed204f6f102e5fc97ffdd03f5d2fff4e5f2e701fbe1fbff9efef710faf40a0b00e9f8c601cfb80710e1fdebefecfcefecf9c2058cdf00019102f9f800f400fefaf4fafaf8fcfcfefafdffeced05fafbf503faf901fcfafd0101fff5fff9fefd02fefdf2f5e801040803fcfcfffff302f60303fdfbfe030305fcfcfaf6040401fcf00201fefdfbfcfffef9fbfcfc0001f004fafdfaf2fafcf1fcff0001f4fdfbfdfffcf5fd02f2fc0109fb08f6ff02fe00fef002f901fd05f903,
      4096'he50102eb030d0103fcfafcf804fefefc03f811f7f4fa0500f00bf600fbf7f5fb02fe0b0300fcfceb10f70d00fae2e7fa0b0205fffc06fffcfffaf5040e01e602f7f6ee0000f8f51905faf90601f8def8eb0805f103fdfc00f704fcf0fff9ee02fbf601f1fe09fcebfcdef5e7e5fdfe030ae7f600f9f402001bfae5fb0314da0de60d02f6fbece6f901fd0304fd01030207040afee7f0d607f4f20100000102050dfcf8ff0101ffde07fa0201fcf1f1fe050d01feffffe703f1fe10040105f2fd11dfdd0003ff04f8f90ff8fa0701f505e5f906f80204280204fe0704fe07d1f102fbfa0802f8fb0c08d909e5f4070212f8fbfefd000cfd0dfa03e302fbf5fffdfb10fcf802fef3f10a08fb00f9fbf6fe05f8fefdf1f600fcfaf1fcfc0003fcfc14f5fc1709fffcf004e702e9faf0e804fb14fb04f1f4f000fdfc0f07fd03daf71bfde400f804fd01f80cff03e5fbf20800ffffe21508ddf6f2f700e9fef1f009fc05fefcfbfc03f4f9daffd8f7fdfef20bf6f4fa09edf203fc06dafff9fdcb01fb0bfdfcfefc03fe03fe010600fbf5000a0f07110302f900eb00fd06080009f6020c04f80102000001f1fe0904e6fe04100007fafd030004fefe04fb0404f5ff05e0f90508fe040508fe090804fde60904040306fbfbff0e0406feff0804f10b00fd05110305080205ecfffdf6f6f7fb02f30cfe02f905fef700f10604feec0b,
      4096'hb6e2f7d6f9e6def60dee0e08f5f80105eeecd601a0a1b5f5c6d50cb2fbffdc07f6e4f205f9f9ffe9ece803cfffd2d500fcef0608dbf0e5fb0b04fb16f7fce8f80b80d401f60809a80cf3f6f5f91ba0fac4fd14ae04fbedeac0fd01c5f90680f80201fcde08f107e8e5a2019dd0fe0602fee1ebf4070df2f6e0049feceefa80f5050400fdfcfd06fb0100fb01fe02fdff02fbf90300fcff01fd0600ff000100fa01020203fc0101fe02fdfe0203f7fa0001fb01fe0201ff0200fffc03fffff90300fb0600ffffff040000fb04fcfffefe020200020300010101010000fff9ff00feff0002ff04010000fd0003fbfcfe0403fef603fcf901000501000100040104ff03fafa0107f70502f70108fe03010707f9f7f901e4f207fa0501fbfb030bfcfcf80bfef802f7f6040d0b030bf5fbff01030100fb05fffd0100fc050702ff0609f6f3fe04fc01f7fa070700fe00fb01fafffefc04ff040807fcfdf2fffff4fafdfb09020207fefc0b0f00fcfc00fc0207fafa08fef2fcfbf600f707fa04f601ec0104fafe02fa0cfafdfdfc00fbfffd06f803030e05f9fbee17f8060af8fefaf21c0206fcfb020304fdfc02ffe6ed020409fe04fc0b21fc04fd07f502fbf907fce3f8fc050cf80904fe090904f6eafdfd0803f609fc0107fefb06fc08eef503fc00ff0f040b03fbf9fffa05f3fbf9fa05f801fd050402fbfffe00f9fe01f307
    }),
    .CHANNEL_BETAS(2048'h77aa78967802785478107651780f783478f77862780277cd784d7783775d7851779478cf77e9779c77e2780a7852786977ee77be77ea77b177e3787f776977dd78cb778678537781784b7746781577e37849773977b8784d77a977d677fb77c0777477cc783d781d7891780c772e77e277ef785a77bf7749785c785e77cf77d5788d78f577d7770f78787857776c7781772d77ad77fb7829784d784177dc77ce7846781277e877d777fd783877d077f0779e777a7828783c780f78f7774d78097778785b77a8788477e2783b77c0788b77f67744783f77ab78a577ed77eb78907824779a786b76da785e77c278347842780877ff783f77a07857775077f27803),
    .CHANNEL_THRESHOLDS(2048'h01ff01e80215020a022001f702230211021a02080220021001fa0216020902210219020801f9021b021401ef01fb022c01fc021b01f8020802030215021b022502260224020c01fd0205020f0205021c020902160212020b02190205020d02220210021001ea021601fc0216020a022a0227021401e60215021801f602050236020001f801fb0210021602210212020b01f80214021a021f01fa021b01f602100206020d01e8020c02250207020c0220021601f3020c01f7021b01da01f7020b021e0203022701fb02150220021e01f6020401ff020902110217022702150201020d0201020d0207022602140219020502150210020d022102130205020e0210),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d8),
    .ADAPTATION_DURATION(16'h137f)
  ) actor_enc3_pointwise (
    .clk,
    .reset,
    .in_valid(e_27_valid),
    .in_ready(e_27_ready),
    .in_payload(e_27_payload),
    .in_completion(e_27_completion),
    .in_bin_tag(e_27_bin_tag),
    .out_valid(n_enc3_pointwise_valid),
    .out_ready(n_enc3_pointwise_ready),
    .out_payload(n_enc3_pointwise_payload),
    .out_completion(n_enc3_pointwise_completion),
    .out_bin_tag(n_enc3_pointwise_bin_tag),
    .actor_error_o(error_actor_enc3_pointwise),
    .initialization_done_o(initialized_actor_enc3_pointwise)
  );
  logic error_actor_enc3_extra_depthwise;
  logic initialized_actor_enc3_extra_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(128),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hf40941260f3f29541309fe060e123d3a204a211f1103071b22230c10f4fd12172f03060bfdf608fe070f0cf6f7faefd8f8df09392c32e8f60cfdf70afff8f8f7f6d8d3e8e5de08fbf7121ff50e1afe0ff8e8f507f2f7f7f1230b30261309ff130ee006fae4d40c02f52bf81627e228e2e0ff2e1b1e0605e81bebf4feea1f120912f5fa12ee140bf805f7eae9f11315f911e5f410e8061f0e0612fa20df2904e6d7fe160d020610efd6e7d104f219d801ef111b1f110b0108ef08edf8fd502105070bf5311cf1ffe51f2201f8014349fff5030f1906fc0606f916f3262b0a424a12f6f8f4f5fb0b15fe04f4ebdf2f3215000fefc9d7e400fcff23fd10fd030b051f35f41312dc05e3f0eaed0a10f4160f12102d2e00132bfe12f5faf3f00df404e1b9ca070cf712151f08fb0a11fefd160eeee2f1e6fefbecf6f327131f26e8c9eddbd6f20c0803fb091000f0f9e0091408f9eefdf8f5f30af000fffd101123330e070105dedf03e521091ee2e3e9fd0ee7260e02140dfe0befeb1ffd391e125f0e17def30810ecf507f9181404f70c10f7e82408024c3a2e1315060ff60a03102000d7ed061c0cf002fd04f601f0fe050c16ece10507e8f5f7ef03e4eef20c1c0f071e0d1d170616f6ee08e8f7e9ed08edddf7f906ed1ef0f6170e0b20fa06170efbf6fa010a21ff14e619ead7f9e30815ee1310f30104221dfa3420181a1d1e,
      4096'hf8f212fbfc0be5f80ff32918fd220503460f1e0df6fff50508e00b1906effef7fde6050215021c2823192701e6ecf10d35daf73d1613500608faeae517fefb0110231a07f105e2da00020ee80906133c3544251e071fea16fe02c9fe0902f701fb04ffed1706ed0cec06faf5f5e6f7f5ec16050be8eefeff0208f6fd000a07130227e7e215ff0700220b2aeefbf409f1f308f7011f1b2df5ecfafd0af8eff706161a1909200f283bfc2a1d0d13fd0312f41e3610ff0ee902fc0bfd18ff01db0be5272e260a0a0a12f905fa15fdfcf20bfbef041e0807211b23fa0009150fea0820f3000a27e61106e2e61d18162f070219141f2304eeea18d6e4210dea140008e7e0eb2012080ce732f8f1f112e6071b0f0705f002e1dae8ff08fe150515160914060d01041b23f73439e4f107e5e218f7f007090f0114010b1bfd090b03f10cf8ed00f9f908122a01fd1dfeeb0309e901ed1004151b2206e710e314f005feecf1e8efe5f1f916060dda0810110117f6120406dfef19ddf2ebfee51dfb1604fe1a2b2319f3f40d0e04f8f11104fafc071732fa05ee0f17fd131606051c092239442908ee17f7f50dea0408fdf5fef90d0716dff3e906041a122a040ff4f8f30ff4effb130221ea032702060cfceef50bf4dd0d0a0b1100ed1cedf413e705f10aebec1bf606f000faf1eb05f6101209fbf0f3f81aeb130b110ff2eb1807fcfc3a,
      1024'h0712140425fb0114e4eeeaf40df90cf50312f50e090305f6ec140a1210dfdcf6e916ebf7f4f5eaf305eef91702e9f9e80dfdf2feeafe00e3fbf5ed0507160c11fa170b1cf3010eef050fefedd6e2c1c92f1919e806e3f8e6f1160f0afcf6f50405fa0605fce9f8eff202f820070a1ee40315090a1f251e2d061b19ebf50ff204
    }),
    .CHANNEL_BETAS(2048'h789877ba77cc77cf77b4775c7808780178267815784c786c7816780f780a786677ec783378b5782377c9786277c5780277eb77c87825782377ab781f781d77f577b077ea782f789377f978397821783278be786a7836781178007840788f77c7788177ff78a8781f7829780e77f77815782877f977da781c780c78a2780f7818784976d278b777f978117828780377ce781d7818780d782077ff781277b577df782077f4785a78a7783d7831785a7843780e7840785777be7815786b77da77c378007849783177f377eb77bd7807785277fc7845780e77f577bd781b783b77db782d77a2786378097817786a7858780d77cd785978f47812780077ba77827841),
    .CHANNEL_THRESHOLDS(2048'h01de020801fe01ec01e901f1020701e701fd0206020201eb01ec01fa01dd020e022301e501e601e5020301e501fa01f101f101f201e501ee01f2020601e901f801f1021101e901f801ec01fa01ef022b01e301ed01e5020901fd01e00208020b022d01f10206022101f601f1022a01ee01f2021a01eb01e9020401cd01f3020c01e601f701f2021001dd01ed01fc01e301cf021101fa01df020401f401fa01e701f001eb020801df0219020d021b020d01d601ec021301ee0226021201f1021501f601ec022b01e801fc01ed01eb020701f301e501e801fb01ea022501e801ea01f101ec020501ed01df01f8022301f501e801ec01f901e701fa01f201f10203),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c3),
    .ADAPTATION_DURATION(16'h1492)
  ) actor_enc3_extra_depthwise (
    .clk,
    .reset,
    .in_valid(e_29_valid),
    .in_ready(e_29_ready),
    .in_payload(e_29_payload),
    .in_completion(e_29_completion),
    .in_bin_tag(e_29_bin_tag),
    .out_valid(n_enc3_extra_depthwise_valid),
    .out_ready(n_enc3_extra_depthwise_ready),
    .out_payload(n_enc3_extra_depthwise_payload),
    .out_completion(n_enc3_extra_depthwise_completion),
    .out_bin_tag(n_enc3_extra_depthwise_bin_tag),
    .actor_error_o(error_actor_enc3_extra_depthwise),
    .initialization_done_o(initialized_actor_enc3_extra_depthwise)
  );
  logic error_actor_enc3_extra_pointwise;
  logic initialized_actor_enc3_extra_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'h11f2edecf610fcfef106e2f419f4f6fdf7f50404d9fb1a001504fceb1307e102f7f502e5fd04fdfcf60be3e00704f7f701f6f4ff06fbf3f80409fced04e31bfb0317fcf9fc03fcf7060aed02fcf40d0208fbfdd4f1f0ff0deafc0cde03f80ee9f504fc0afedef9e7f6fafbf202fa070b000ef7fefafdfe05f20107f8fcf817fbf8e60100fffef606fbfefcfdeffe0400f6e9f5f2fefdff010b02ffed0c01010007f8fffa01f6f7fafaf101f4f605fbfcfc0300fb06ff01ff01f5050101f1f8faf60df2fafdfd04fe02fa0203ecf8fbf603f700ecfeeee507ff00fbf3fcef0201f4f6f5f5fa08fcf8fef004f7edf1fb01fa09f700fbfd01fef9fe00f6fffb1005d8f70df104f8f801f309f300f4fcec0cf4ee0200fbf9e1fef205feeff1f4e802fff703e8fd0608eff500e0fcf9e5f3fbf9f8e8f9e8f7fcfc0107ecfc0bf6fb0b04fdebfa05faf9e0e80010f7f9fe01f0df0b05e90400f707f2eb02e2f213e0f0f6080306fffafbef06fd0704ddf7ffee0607dc0003ff05fffef80afefffeedfafbff0903050502fe0002fdfbfbfafd02f9ff060300fd0500fe08fe01fafe0001f60203f0fff804fbf8030709f8f906ff0002fa00f9fefffffd0606fdfdfcf9f4fbfbf5fe0003fcfbfc06fd05f5fff2fdf9fe060403fdf9f7fc00fff608030503fd0101fefb010400fe0803f8000afff9fef900feff09020403fbfcfb01000306,
      4096'he7040ff206ef03fcfd0006f5f904020302f8eb050006ecfbebfbf5f3f1fcfa050afc00e300f8faf6e5ebecf602e6f30b06fefcfdfb030407f303eff7fafdee00fbeff804000601fcf505f5ef08faeef5fafa0801090705fd01fb06000006fa03fdfe07f6fdeeeff9fffafdf4030d09f800f9f6fbfc0003fcf7f1eef50006e8f7e9f600f8fe08faf4f7fde9f5fdfe0600e9eef4f800eb23fff7fbf602e8f9f1fd1aee08f7f5f4f805f3e608f80005fcf6f10307fafbffdbfafa01e5ff0af9f8f20423e80000fd01030203ef0bfbfc00ff00ff09e8f9f9f1f6faf008dd0ced11f6fff5fcf60414fad4ff02ffdcf0fcf8fffb13eb050500fdf6fdfd0efbfef70701c0f90dfdfadaf701f701e9eaeef6fb0606eebef6f8e2d7f4c7f5cfdbe5ffe900dc03f1d801fa0603ccd0edf8efddfe0606f8f405ceff2300e30ec10000f0d505f6d6dffe070900ccdcf2f2ff0404de16e9f8faeb080bf5f105e804faf102d7fff0ff0df4fef5eef9fcfef200fc0a06e1ffdff3ea0505fcf8f5f5d5ff0004cef9e80d0310fafaf303faf71d06f8fd010c01f1011104deecf7f207000bfd0312f70801f7f3f9fd0d0704fdf10400ee00fa0c0602090104fdfb0914e1f70af8fcfafdecec02f9f5f4f9f70c1f170bfe1a00f50700f1040ae300f7f60001fafaebfa04f3f9ee040a13090904f602e3faf9fc01f0dc08ffeefb0aefe6fa050611080d,
      4096'hde01fcf102f401fffd0306f4fb040301f9f9fdfffcfeeb00f6f7ecf50608010606f4fdf4fbfe01ebf4eaeb02f8e9ed04fff5f4faeff9fff7e9ffe7fe02fd00f1fdebf9050201fc03f7f300f9f8fefaf5faff01f500f8da07ee050bf8f907e9f7fa0201f802e2fdfafc08f7eee80ff7f4fef0f601020302fbe1faf102fd05eb0294dacfefe3a1f9feeeefba11ecfff00f09f1dbfaeabde8ffbff4dbf4cafdbbfcc4ff10dffeef0202edf9e7edfde7f10108e9df00ec06e207ecf8c708fc01cf040a80e6f6f0f5f3a7f2d8fcd3eff6c7ede6f405b2ee01dae8e0ebedd80dffb4fb0de804f007f5f1cc04d90adadbfbe4dcf7d6e6e9fb08030af1f9de0ef5f39dfafcfffceefaf1ff01fe090509f703fefe0602db00fef2f804e700eefef700f1f9fafefaf7fe07f702e100fb01fbe2f204ff02fcfce8fef8fefcfbf0f9f7fbef00eee4f904fefafcf9ecf001ff0502edf801f7f6080700f8f5effd0a04000ef3fa0003fbf904ecf708fbfcfa06f002ffeff8e9f8f7fa050202f708e802fefcf704d0dee813f2c30002f705e5f9fffafef4ff08dbeb05e6df00d5f7e9f0f90cd208db0201e7f6fcff07f6c4fcfbfed8dc050cf5130cdefe00fa0f02d8fbf4f5e7faeca0fff8f8f0fabce016fcf8ecfed708f7020def0803f7f4d8e30af90805d7fbfcf70afb07f5fcf4f8e000e9e20ff2f2ffd7fffa03f51df4e4fce6f10203b808,
      4096'hf2f1eefdf201f5ff0a0bd3f512fbfe04f7f1fe05db0c1500e8ebf1080101d4fff3f003fcfefafa0d04dcf0fff8fdf704fef9f4030bf805f70209fdf5fcfc03fd020c10f7fef8010703f7f70adbf3dcf304f9f3f8e9e9f3f103250c0d0af70c01f0f7ef15fedcfed5f9fd01d3f202ff0cf913e7f8fff60de5e1edfef3f6f203fedaff01f10bde00f705fcedfcfe01f901faf7dc010df8eefade03e5f0eeffe9fef1f9fae706f4fbfce2faea0603d5ef02090ef400ef000e06f100e50900f0eb00f1dbfc03f9fbf7e107fcfef20bffddf2eff11afb06fe130d09f30b0d06ffec05f6010dfcfee7f5fd00eff7f4f11705f6fdee15fb04f909fef1f8eaff0907d609c3d9d6ec01cb10f5ecfad108f502f3f401f7eae9f4bfe7f8baede7dbe6f2dff7daf607d2eff4f91600ebf200f5caecf1f7f6ee07f402f0ffe1f2c0eaf2e0d013009cdcf204f3fbb9f7e005e4ec01c2f7e3f8fbde09fbd8dfcfe5f6f60f07c5f5f0f6f9fc04ea03d4f7e804dd07fcf80203e30e03f8fa01fcfefbe7f402f7d5fedbfbeaf2f1f20601fa12f70e09faf80e220929d6d6fcd9fff0e0f3fdd1f4eafb27fff711eff50217271bf3ea060822f5fd07ebf6cdf7e1f3f00b11e50f00d5e724e52902fdf406f7f3f401eaecf6e9f1d0ffe7f9080d12e2d2f312eae413effc07f30ad7fde6faf004e806d3d605f5f101f1fefcf8ef0700ea052f0d04f1dafd,
      4096'heaf70a1001cffe06f7faebe90503fcfd02fedf0b02eae0fbd102eb05f40cf7fcf20cfaf3f6fbf918e8f3000c06d9fb0115fb0906d8f70203fa05e709fde7ee0de4c9ef06f800fee5dd0403080804eb07f2f7ff0407f61637eaf808021010db00fdf312fcffeafe02f7fc01ee020af607feda07fdfd010c0800efdbfcfcffec17ecdcebe5fde30dfafe06e4fafd04fdfd03fcf1f6fadcf802e7ed00f8f1f7edf9eaef06e2fb01fef103fef3f20603f1fdf9fcf505f302f1fff6faeffe00e201fbffeced03f609fee0f6faf3fcf2fee8f1faf507daf6f2f1fce6f5f7fafaf1f4f301fcfef7f7f503e1f3fcfde4f3f5eb02fbfffd00fa06f5fcf500ffff0203f6fcfcf6fb030804fbfe00f8f5fd01fcfcfef4020bfaf806f604fefffffef3fefd010dfafcef06f9fffe0203ffe4f303f105fb09f4fef2fdf20105f8fdfdfafff9fcf80a02fffefb06f704fef9fff5fbff02fefdfdfffbf6f8fdfd01fbf801f0f4faf501070b02f7f9f0f9f00001fafa0703fc00f1fc00f6fffdfff60c00fcf70206e7f90cfaf6f805faee03f5effef7fffcfefcf303ff07e704ee03f8f2fcfc00fae70bfdf3fafff3faf1e7f504fde7fafc00000603f002f0f9fbfee9f107fef2fefbe2f8fef9fbfaf3f70507f013fef20002faf9fefdf8ed05f1ee06041308ed0008fb0100030001030702fd02f606f3f4f4ecf9fefcff01f9e8eefcf6f905f708,
      4096'hea1cfb13fd0602f604fb0cfef7f6fefcf6f6f103f90dfbfeecfef4f0f60505ff0809fce9fdeef109f3eafafefdf1f811faef05faed0c01070211f3fcf9fff0fcf5fdeff7fffd1009fbfef800f604fcfde9f9f70801fc090a0df80a01ff00050017fa09fd00fefa0efdf8f1f7f60cfcf6faf3f4f9fa04ff0107f8f4ff0103fffc00fcff0201ffff01fe00fdfd0100000001fcfcfffdfd010300010303fe0101ff010001ff00fd00000102fcfdff01fcffff02fd00ff00fdff00ffff0101fe01feff02fc0000ffffff04ff0003fbff01ff01fe0100fefcfd0001ff01f802fafefe0100000100fefdff0002fffdfcfe0000fffefafd00feff000001000000ff0103d7d1eae7f1d5f50003f4d4faf5fefef400f9e2eee5d60801df0bfae7e602defff5fb08effe0cf9f806ebe1e2fa16f8fe0005f004f6f7e8fc02f6eb030ae701f6e7f4f700030001d4cdfc03f1f104defdfc0302e9effae1f70ddfffe8e7eed6ff07f5f2fcfcf005d6f6f409eee9faf9f7f403e0000400010707f80bfff9eef1efa8c5c4e7e897f6ffe5e3e221e504fb19f10abee7efccc7ffbcf8c8adda0bb5efa1effae5ed0eff13e0a3e7f3fcc9e30cf9fdf002d9f6e6ecd8089df900f2cffcdf8ee3fff4fae3a6c00b0ed4ebf7eae3d3edf5c9edf9dbf5d9e0f6f40211b4fc1805f2eb01e2fbd005ddeaefec05e7e0fed201f103f409fbdefddc14f3fb86e5,
      4096'he302ebe311460404f121d3f011f5fb07ece811f4e8130dfd1ef20ffadeebf8ffffd800dafdfee8e3f119f0ebeaf4effaf708e2faede20ff70af5f8e1f8d7f0fad930eaf409f1ffecd801e7fae7e6ddedfaf1fe11f2daef0ee30cf7d0dd111b05fdfaf1edf1ed00f8ffefe8e505fdf601fc0de00703fff105000b1af8f8eacef2bbdee5dcec9801f4edf8b8fdf2f7f9f60800c303faddd9fcbc10d2c3d5fbbe07caf3ead3fcf5ff05d7dddbe4f9bef1f90ae903fec2f90df9fbfdaffd02e9d3ffeb9dfaf7ef0402a4ccfafae301fab6ece9e601cbfa0bf0f3f9d6faeb0ffcad090bfb04f204d5f5d9fbd4f4eff7fd0ae9fadbf2f50d0309fa02eccf0efe07a3fa09e90403f60af8fbf5ff000600fdfc0cf7f9f205cdfe00000cf2f700f9fadf051bf9f9df06f3f4fde6f5def8f5edf603fa0bd7faf801f9f60cf60d09fbdcfbfb0216eefffcf613f701f4f405e0f9e2fbf7f3fcf8f0f6f301f90e01e4f9e60303f5f9fdf8fdf102ffff17fceefbf60305ff05eff6fcf7fcf6ebeafbfa01f6090b12e90003fb0fff05f605f608f2f6020fe8ef03efeae2f2ff19eb1e1ae6ffee0101f9eeea02f60601fe010107d5e810fb02fcf0ffd405ebfcf3eafced02e015f1f9fef503040905120b040202d3f619fcea070eec06e4e8f8f3d8f8e5e7f5100106f8eec8faf008e70bdc0407fbf10d000afae40c04f70b06fffa1a000fdff3ff,
      4096'hf205fdfefc03fafbeff5f9fdf9fcf4f7f6eef705ebe6fefffffbf1e8ee04e900f601f908f6fafefdf3020001f0eff401fa02f7fb06f805020c01fdf4fdeff6ffed09f9fefc01fef9f2fcfdfef400fdfafdf0f9edf6f8f2f4eef6faebf90306f7fc02f7f602f9f7ef0106f9f20dfafbfdf9f9e5f801f8f8fef1f7f903fcfefff2eb0c0b03ff12f8f7fefc13fd12fffff7f8f7fcfc05f8fa09eff7f005f7fe01ff0001f7e401f9f6f8f9f3f503e3eafa08f90602fdfc0100fdf8fb1401fb0105f5f30507fcfa000911f3fd060bf7f802fffffe0b0504f9e606f1f6fafdee05f605fdfcfa010912030af907ff0be401fcfff9f3fdfd03fcfa0209feebfbfc02ffff0607000303f901f3fbfaf8fc0b04fdfef500e804031603fefcff080b0afcfafe0302fe01fffd0502f30ef4f5f2f4000506f9050408ff0b00fc02f000fcff12fd02f0f50403fa06fb0f1101f703fb06030302150601050d01081007e7ff050201feff010500f8f705fc12f3fef31105edfff7fe01fdfe0006fef6fafafff7ff05d6daecf4efbb09f1fb0de9fd0905fef912f0d80bfcdfdaf8cdfde0eff10ddffeee10fcd300f40422d6d9f0ff18e0ea0105edfc01e8040410f102d8100ceee9fae7bfe205f6f408dcf6fcf7f5ee0fe8fefbf009e6130b13ed0ae503030ef5d601f7fe1d0002e7f5fdf8e7fcf7001805de01ecebf602fc0711f9e8e5f3fafec806,
      4096'hda040e0a01fc0601fcf21707e501fbfd110bf01006fbf6feeef9fde5fb010cfff604fceaf802fbfee8e8fb1ef8d6f8f103ffec09e2f91efef503ede707f0eafcf805eb00fe04ecfcddedf8ff010204e9fef9fffc0cfbf106eaf2090ff804f9f8edfe04f9fd040b10fefbff16f001fdeafee80d01fdff0dfbf2faf205f9fe0a020214231afb0afef2010414f3effff9020e08fb11f80df302f907e60d14f90009070cfdfefefe0109ddebfb11fcd7040109f3f90300ff1bffecfff2000510effcf9f9ef04fb0c04151307fdfd060015ff05fb000e1219070b0f0e000b03021205f8040afcff05f713f802ef07f10e0bfbfef003fdf9fd02f6fdf8ef15fe08fe1ab4cac3c7f591fbf9fef8adf6fefde9020df3cfcef3bcfffcbff7f8d5b403b5fcbbe7fdbc02f0eafce3dbcfc5fed9e4fff9eeecffe9fbed03f3fed4f1fad4d8ecf3a6f907fa0afeafcae4eadafcf8a3eed6ebf5ab00f1d9f1f6cc01d1ec07b1fa01ef05e50dd9f4b6fbe5fad7ecfbfccef9f2f6f3fa080a05fd06d5edf1fdabe3ea02f9020703f70eff00fe0c0cf70003ec0211feeefe0603f5fbecf3fa0303fd1111091bfcfdf8000bf9e8040507fd020e00f6fa0bfff0fb0a01f5f509f308eefe0e1903fd0700f40300f3fb06fef900e8f6f9fdf9040206fc03fd07fcfffeff02f9f5170306f0ed00f6fafff6ecf1f800f515feff0afcf8030211fefef7f1f0,
      4096'ha7cecfccfbacf5fefc03c5fef902fffb00fed3dcf0c8faf9c0f6f1e1d00ad2fbc9f204d1fcfbfcfdeedcd7d7f7eeedfbf4faea04c8f8ecf9f205d9f0fce1dbebf4b2f6010400f7c6d9f8f3e5e804acfbe1eafdc5ecf4e0f1f4c8f3e4f9f0cbf80aef02eff7e8f7c4fae101e7e6f7e8ebf3effdfe0104fbfd03fae7fbf5fdbaf6cefbef11e9c6f4010002e92006ebf91805f8f1f3e7f6e7feecf60003eb08f7f2f7f50419f9f0060b11ed1005fb1001fb0bfef3f7eff1edf706fcf1fd0816e2fe03d0dffbfff9f6f00cf506f6ed00e8f8f2fcd3eef113e4e9eddbf400f3ffd2000ef0f40202fbfd0c08effdecdafae6f30cd80507fdf3ed02ee04f60205ffe304ccc9d3ccffb70cf4f701ce04e8fbeb0d02ffd1d3fac9f0ffd1e8fde5b8ffc9fcbaebf9caf8f400f5ebdbf7f1fbf2e2f701ef0bf5daf9f6fff9fcd0fb09c7e205f7ade302fefdf381d2f1f1e8f403cdf9d8d7f5aefc01efdacfcdf1db0501c10401f5f1f101eaffc00fd6f7ddeb02eeddf9effd0afc08050af1fc00f6f101c5ebe6110d1800fcfffdff0104f6f1f9ff000af9fe0c0008f5fbfd08f40004fc08020512fceb0800f811e2fc010ffce2010210fbf800ec011404f40be80300ffed0ef6f3f4050404fe02090cff0004fd03f4f3fd07f9fe0606f70b02070204090204f6030203f7f2fe08f8f8fdf7000dfcf2feef10f7f700fbfdfef7f3070009f6fd,
      4096'hd7d7e4cbf9d0f4010911dd0101fb01fdf9f6f4eaefd2fffaecf703e4e1ffe2ffe6f302e2fbf702f906f8dcec0cf9e9fdf2f6f1fde3f8eb03fa01e1f20ce2fff506eee302f505ffcbe1fef6f0fc0ac7faf8f2fbcb02fae9f3f9e405f7f3f7d8f9f9fdfee600eafcc9f4ecf6f3f0f7f7ebf805f400fb02fa07f1fb08f4fbfdd8f1fef603ff00fd00fd01fefbfd01fffbfffc00fb05fe010603fdff01fc05020001fbfffe00fffffe0201fc0209f9fd02fffd02000100ffff02fffdfdfeffff03fdfefe000001fe02ffff020101fa02fdff00fb0102fef9000402000102fcfdfd01fdfffeff00feff00fe060400fbfe02fdfefff90003fd00030300fffa0008ff02e8f9090600010104fc00fcf4010300f00402f507f901f603e9fcdf06fcfa0704070bfded00f5f805e7edff08f7e7e00201fcf808f3040dfaf70cf416fc07f1fa05fff00903051403f5f80702f2fffcf8f3fef80f02f4fefd080c05f402fd030104030302f80100fcf6f7fbf6f21c0bfbf6e4f306fbfe07ff02fae707fe05f80fe80317faf802020ff4ff0df7f9fffd0104f6fb09ff03f1fffd02fff3f9f80103020affe7fef7f7f5f3f5f20ff8ee11fe02ff0bfdfd01f6f9fbf6fdfbf6efea00eaf7e3020202f20806f905f807fdf9f7fbfc0309fefbf50dfcfbff00fe07fb03f600fcfc0205f60a07fdff01faf8fffe02f3fb0501f807fdf00207f601fffefb,
      4096'hde0609100b0903f5fe1103f7f20502010f05f10bfaf90001ee06f6fa01f807020409fafa0309fa20eceffc0c0addfcff110504fef80319020902ec0003f2f70debf7ff0902fc00faef0a07fe09f20cfffcfb00000208fd12fbfd0200040df60203000300fefcfe0bfbf2f801ee1004fdffec0cf6fd03fb02f7f9f3fe04fbf51be5f4080802edf6fe05f6f70cf1f6fff5f3e6f9ecf7d70500e60300f6eb0309fe04f303f4fb0007fffffdeefa0109fa02f504eafafef6e20102f6efff05de00f0f603e0fbffff02bfe9fcf7f8f301ecf4e9f7fcf2e9fef9fafbeaf6070beaeaec00f6040001f601f2f0f8f1fcfceffa0603fe020703f7fbf5020004f9fef601effafe05faff0604020507fcfaff0301fc07fbf9040701fefd020500fb03fcfc02fb03fff8fcfcfcfcf8fafd03f9f5050104ffff0300001000fe03fc0101f9fb03fcfffafe000101ff0607fcfb0201fd00f9fb06ff03fc0001060105fbfc02fc0103fffe030101fe01020103fcf4fe02fafcfdf9fcfe00ff02fffffcfc0203ff01d0ee0615ffe7f6fc0012f3f40009f40e04f1f7f6f6f3ec05dbfce8e9fa020dfff20503fbfdfa02f6dde3170b06ccebff000ff408cdfdfdfce703f6fbf80de0fc09e5f0fd05f7f0e1efeaf6eb08fef3f8e507020518fef6edefdd06fcfcf5ebfafa050af1fee6fa0f11f9f601fd13ffe709ee01f5ff0308faf1ede60804fbde0c,
      4096'h0eff03fafbfa03fdfa02f2f6fefef8fef6040701fd0af4fc0907060a09fcfffb0e0d0000fe03fc00edfcff05f2ee0604010002fefe0205fa0b02f401f70903f9f6f40407f90805050700faf8030203fa08f2fbfc03f3f406f90903f60705fcfefefdfb0b04030802000312fdf1f500f1fef1f507ff0e02fef2f801f803050105ddedfbe2ebc7f6f2fa0cdc09f2f70613fb05c9e9ef06f003d6ebe8eaf001d300d1f6fef00601fffbe3cbe30704ceef0105fe0800c509eeeee206cafb0e07e503e7c20502f9fdf2e7f2fcf4e2faf8e1f3f2eff5ddf3f6e9f9edf303fef4efddf9f90206fdf7e3f5f404f4f4f7f70303e003f5fdf3fe04f8f3e1f6f0fc04ffc1f9bdcfc6b5e99415f4f7fedef7ece6f5e7fb01c0d4fdb3f909a70ad7c7d709b9fccdfb06ebff08fdf2cfc3e9fef6dad2f3e7e9e9fef3feeefadbfbbaf60ce9e1f3ea9deb000af8f5b0c5def0fbfe09ad11df07ffb1fdfbef00ffb30de9f1d2b8ebfff6fefc05f2fec90fecf5cae6edf5f5faf2e012f5f60915ea00eaeafafabbf6b5c7c7e1008af300f3ddd309e70df706f705dbe504d2b8f7a7ecd4d6d7febf02d1f5eccff8080103d8e6fae305dae9030c02ee01f2f4dbf2f102c5f417e8c3fa1180f10606e5f198eae500e7faefdbebf6eafab8f325e3ebd4e508e90a0eb80008fffdf2f5bbfeb907deefe5d803efd707cff7fb06f806f5e3feed0cfbfd8bfc,
      4096'h14ff02f8040aff05fcfe02fb23f60103faf71301fc0110fc01f0f90d0004f7002d03fd0d00f9f9f91006f0f803f70afffe01e3f91800f6f9fff905e505f63b05000a13fff601fc1101fdf4f108fd05fd09f6ebf9f50d0df8efebfdfffbef0bf7f601f80ff3effbe3f20904ff1cf5f705fbfb19fafef8f703fb0016f2fff915f298d2d2cff89403fdfaffd4f9ee05f40a10f9bdd8ecccd7fabbe1fde6c405c80bb1fbf3caf7fbf7f7dbbfe8fa04d6ea0902ebf20bc5f7effef4fec6fbffdfdfeefea10bfafcffeb9bd2e204d804fbbbf6e1ef00b802fed1f0deddfde6fa08ab050106f7ef0bebf8cdf5d7f5e1e3ffece008dff5f40306fd0aedf9d5f4f1fe9df6fc010306f7f604fb03fffcfefcfefcfffc010004f902f6fefffefa06fe020300f6fefff401fbfe01f8f3fa0203f0fefc00fafa05f1fdfe01fd02f8f401080002f9f7f5ff0000f80504ffff0709fe03fc01fcfffc0603fff3f30402fd01f9fbfbfe0301fb01f4f8fbfff4080100fafbfefbf60001020204fbf505fafc00fdfefaec03f0fdf501fff603fffc03f60006fe00f3eff8fd0bf1faf4edf1fc08f9f804e207f9fa02fc00fceadef10407eaf4070706fb07e5f808fff605fafbf80ef2f1f7f303fd0101fefaeff6f1f60ffcfbf00af9fffe10fff2f2f10f060cfe01f7faf9fb01fcfbf2f3fafef3f4fbf102fff3fefefcfafd0508fff603fa0606feecfd,
      4096'ha2c1d8cffca3e8fcf513cef2e8fefb1e04eae0e7f7f6ccf2b0ffc8c8befcc3fadbf8eacd00fc02f0b2c6ced600c3db0808130001d0faf2fdf0febcf505e6ccf3ffa0f80802ffecbfdbe6e6d5f4f7c5fbd508eedb0e02e8f8f5db08f604f0c105f6f900e6efd0f6ccf8d5f1e3de2106e601e4f3fafafcfcfdd1ead209fbec8ff3dc111100fef3fa02f511fbf9050204f603f5eafdfe00e400ec05eeecec01f800ee08ffe3fe00faf3dfe2eaf4eeddf1fbfd03f806e9f60ffbf007f5ff0207eafbf2edec03fe04ff08f40000ed03f9eff0e5f702fafefff100fdf308f2fa03f00201fb02e8fbe8f905fb03fef1f20a05e1f7f0f704fa0b08fdf9efe300fd05e800ede8e803020806fb0df5dfeb07fa05fae3f8f3fdfde10606f416eb00ebfce50101ec07fc00eff9f8f1f7f20e08fafffafe0d0e030a00fb090302fcfdfae5f304f211f001ff0908f1f406f9fe05f9d602f20003edf9f4f714edff08e2f2ebfd0f050606e7fff801ddfa050eea0708ff0eef10e801fc02010c15f5fff9faf7f102fb0af3f4fc02fbf703fc05fe04fef9f404f0fdf9f906f9fff8fef30401faf5fbf6ff01f905f9f7f6f3fdfefc01ecf5fb0505fb07fb04fbfff5fdfbfcf6fef6f6f4fa02030401f800f40901f5fdfc0403fafcfdfdfff9fbfbfd01faf6fffc01fe0bfefd00fe00fefbfb02fd03020803f202eef205fc01fc01fe01f201fcfbf3f7,
      4096'h81d1dac5ed80f2fdfff8c404e4f60003fee9b9d4efbdd603a8f2e2c6c30fd4ffb7f80ed4f7e7f5e8eabbd0d9fee0e6f6fc04eefcd0ecf2f0d5f3abf70cd8d4faf684e9f5f3f7009cc8e503ce00fcb0f1dce8edadfa05c6e6cec6fbdef90c9a0015e6fbe7fcd5eac900ca06cadf0ee0cff3d7fbf7fa0d0602edf5f716faf080defc0200fa0102000004fefdfb03ff01fdfffcfe01fafc01020200f9000000ffff01fc03fc00fc00fbfbfcfbf8fd03ff00fc02fb00fe02f80101fd00ff000200fcfe05fbfefffefefafb010001f8fd02fe00fc01fcfcfbf005fd04fff9fdfbfafefd00ff0101ff0001fe0200f6000000000002f8fd0000fefc000203fd00000303b6ddd3c5e5baf3ef050ce60ce3e60408f9eee8ddf7c9f5fcb80514e1d6fdf606c8f50906f4f6f1fa05cbd6d604fef4f7fefee9f7e5f8cdf1fbffcf0804c1def2f8d4e9fdf413f8a2c803fbd5fcf9b0eee9f3f4d4edfd03efe2c4f8e5dd04aeeffbf2edebfafcffc6e8df0de9f2f3f1e6fcfbee07f70cfffa03fad806fcefc4efe2f90917fcf7fcfcfaf2fc04f402fd06fefa01080ff9f0f9e7f9ecf3ff050b040c0cf0e9fdf8090fe5f6f6fffde4fd010bf50602f7fcfb0ff70decf7fdefe6f7fef5f10501fd1bf80804f1050805fef3f8f10802fcf9011b0502000a0d06e4fb0cfa0603fbf7f9020406f9f60c040b0a01f70101040701fb04f4e41702faea00,
      4096'he9e3e7d802f80906fe03e4fe01f9f90401fcedf4f3daff04eb00f8ede5fedf03f8ef09ecf4fefcf4fef6f3f9050af7f9fdfdf103eaffeffdfffee3f900d6fb0cf1fcd7fffd0002dce5fdf8f5f404f0fae9f205d3f3ece601fae702f8f6f3ee00fffefdfc06f5f8e903f2fdea03fc00faf7f7f200f902fffefa070bf6fb00eaf6f8edecf50102f10803f902f8f50a04fefb00f7faf9fbebfef4fff8dfff03ebfdf4f803ef00fb01fceef1f1fe09f7e6fffff0f8fff400fbf90cfef1010006f2efffe2ff03fe04070ff1f7f5fef4fce2f6fdfbfbf3fbf5f804031204f1fa0c0d09fc0104eaf9edffedf7f401e1fc0505ff01efeafff8fffbfff1fbf4020102ecf6f3e802f1f7fcf003fa07f7fde3fafcf5ebf3ebf4f6edf301fa00f6e7fb00f8feeef9f9e20301f201f8f6fb05fe0becfef607f4fbfff8edfb10ff0001f8ebfef7f905e6fd080304ff0508fe04f1fafe01e7fd02f2f5f1e00910e600e2f5dbeaf606f8fff9000302fb00fffef7f6f601f80203f4fefcfcff050104fbf002f308faedf5200907e60802ef050309f7f7f9040dfffe081008e9f8e610f2f200f0ff06050cfffaf705fe0bee01f80c01eefd05fff602fff50211130f00f003f30af210eff4f006fe0407f5f50c0306fafb04fbf0030afc06f502fdf701fcf10b06e2ff06fc0afafa01fe06ff0afa03f20cf8f8fbe6fd010502fdfc02f7eaf7fb02f509,
      4096'hafdfc8dffbb9030801fdd305ff03040605f5e8e6eed3dafbbdeafcdcdb07c601c0fbf5e1fa01fbfde9d5ced905d6d8fc0c02ecfdcdf7d6081003d602fdeadaece6b5e809f6020db1ecf5ece8e2fab7f2d9e1f3d1f7f9cbd4e1d2fdebfc01a7f4f1f4eff602e4f0d2fcd8ece0f1f4f9e1fb01ebf701fcf4fb0efcfb040af5a6efe116160bf8f60206f9fdffeceefafcfe09f5fc050d06effef30101f5fefcf7fb020dfef802f9fffde5e806ff05dcf90203faf701ebf722f9e915e1fe00fbf103f0fced04fc020ff6fd160905fcf7fdf9f7f6fafeffff0411fdf504000009f0fefcfc13f8fbff0402fb01fa04f10bfef6fcf11006001003f7fbf2f20400fff90efa05080d03fa01f9fcfefcf801fcfffe06fefa08fe08f7fcf404fb0203fe0300010ff9f2feffff0bf1f9fc01faf3fc020dff0405f5fe05070506f504fd09f500f8f3f3020007040506ff00040104fc0000fc080106fb020cf80205fe0107f4fc02010504fef2fd03fe0003ffff08fbfcfafa0c00ff0bfdfdfd00eb0a02fef30afb08f602f814fffc08fc11fd08fc00fce8edf909f805060316fbf3ecfbf601fcf9eef8fd04f803f6fa010bf5f70af40003fff6f8f2fd09f8fbf911f7fa020af5f706f3fefeeffb120104040bfef80bfd08fefa1902f5fef5f7f9fc0be5f8090001fdfb07fbf20c110805f500dbfeff0002fdf90000070700f8f311fbfff60607,
      4096'hf8fc04040400fd0205fbf7fa02ff01fefefffe01f80607fdfb00fd060903f3fe08fa04fb0600ff01f800fffbfb04f9fffd01fdfe09fbfd0108fffc00fdff0efcf9fe03fd0301fffd0003f6fd02fffd020eff01fffdf8f209f004fd01fefafafefbfefc1801f8fbf300000aedf2f30107fd02f4ff0002fd08010515fbfffd0004d9efeb04ecc6f5fefbfeea10faf9f51311f2f7fde6ffd2f9e3ebeced00f7eafaeb0504efffee0b24f7ec11f8e5f4fb080df6fafa09fcf0ed0a08d6060dffeb0504c5e603f7f0ffef0ee70206f90603effbfefeebfb14eeebddfe03f20d16d50004ebfef300f7faebf4e508f6eb02e0eefaf10d05fb0f0105f208000700f7d6fdf003fb0cfdf2010afdf40802f80300ff070cf60903f800fbf0faf2fe11f60000ef08fb07fffffd14f2f7fc0b0af2fcfcfcf307050afae403010b0306040af0eef7ec0a05ff00fdf50c0213fb0e0205f8ff06fbfcfdeb06ff0a0a05f800fbf30004010809010f1b09f8020a09010f02f4010206fdfefb0305fd0aeefb0512f7fdf2041802f7ed09f8f9f520f9f900fa07f70af0280cf5f0f9f403f1fa0f0012020c180023fd03f903e6ef010dffdcfdfd00f7fd06fff8e0fff702f3060a00faffe8f9f9040204eb0800f4f613150606fafeed060efcf416effae206121306fefaf30004f0050a132301f4ff02f80110e8fbdf040cfffa14fef9f1e60003000a07,
      4096'hf5dbfbe5fcf104f9fffaf9fdeaff08f400faf5fe0007f7fdfc0500e5f4fbf4f9f2fdfee3fcf904f8f7dff4f901f5f601fe00ff000304f3fc0bf6fdfefff9f7f7fffaf105faf804e7050508f300fcf4fafef9100104f902fd05faf8fcfb00eafc0000030204f6f6f007f4fef206130df3fd04fffbfefeff05fb01ece8fc01dffee704110ffefa04fb04f6fdf0f1f8fcf6fd00f10dfc03fa03e302f4f7fefdea000a0dfaeffdf6f5f9e0d903000ad8fb060aecfff9f0ff2504f803f802fcfbe1fef5fbe605f7000afeea0bf8fa040100f3f8fafb08fef8fc020b0708000006f9000901ffeff5f8f80700fff5f3f70afeedf6e40500f40108f9ffedebfffe0aef13f60901ff17060100f504e10907f1fe04eff5ef0202f0fffaf906190dfdf4f6f71df911fffefefdf9fee0f7f41dfaee0bea08ebfe01f7cefb16e4f8f909d0eff0de1ae903f902f1f3f716dc04ef06ebfd0af001e3f305df0b06f70dfc0adbfceb01070102f7e811d8ec00f3e0fcf3ff0ef203e2020b01fff50c051f050af607efd1eedf0df1e3fefd04f9eefd0206f9020e13ebf4faf9dbfe0008f80204fce20ad1f30503f502f901efd9ff15f7d8f9fe0f020e07d9fb05fe26fccb090614f207eac608fff2fc03bfedf1f1f0fafcf0050deb0ceb000e1e14d5e00ff5112bd004f40709ef18e705fdfceb07eff0f8ecfcffee0e010805110be91cf6f1fcfedb0f,
      4096'hdbd0efeef4e1fafaf1ead61ffaf2ebfa00f2f6e8f7dde7fee7fb0cf5db05ddf3edf00005fb05fffc13fffcf5f319fafbf502eaf2f6eff8f5fffce7f204eafbf001e1ed00fe00eaeaef0401e0f5f4ebf7eef6f3d704f4e3e9e9edfceff3fbf0000afcf9f000f509dff30303ebf5f7ecf3fce1f607fdf4fa0a0e0df5fdf3ff00ff89d4c0cfdd9b031a0404cc1df7ed02f8f905cfdff6d5f7fcb9f606d3d902adfdb9f30ff9ef07f216fde4d809e1e6e3fdf709f202ecf7daf2de07befe12d8e4f9d98eed00ec06ffa0e6f1f6cef4f898efd6f9feb9f805ece2d4dc02c50415a5070cf804e600eafcbff3dc0dc905dff7e4ff03ecffff010b03e60b05f6f805a3eee5efecf107e304fcf9fadbedebfd00ff01f6e504f3fce0f8de07f2efe901dbfbe1f501e4fdfbf803eaebe4f60ce1f6f902f00308d6f3090d0005edf7f7f8daf0e9f7f1fdf6f9fedc11faeaf300f7de01f5fffefcf6f805faf1e2f602fef3dff7fe01fef90bedece8f5e5f9efec04f9f7fbfff9f7fdfd010208f6eafcf6fce2effb0a0cf20b0f04fd00faeef210fffe01f5fafafffc06f1fef2edf2dfe4f40f02f9e809ed02f6f4f2f901f2eae6f3e9fdf70bf3f9f90405060905f7edffe505f2ef14f800fdfe07f70b1204fbf4faf505fbfe050cf2e8f40ef2050605f5e80909fa0af70cfdf7fbff00050c01e8f700fcfa17f9fb03f604ef130702f9f6fd0307,
      4096'he808fffa02f404fef503fef8fd0305f708f9fc04fff9f104f600f6ecf4fe0afbfd0304f20200fffaf2e4f8fcffdef403fdf90002f4f707030102f2fbfa08f5fbf2ecfbfe03fe0cf9fffc03f8fcfdfbfbf411f2fafdf6f7f809060300f6faf3fdfc02000002edf7fd05f101f6f60d09f2fbeffbfbfdfe00040ef7f1f00401fbf6d6f519f3f0cbf60c06f7fc04eff8fbf91600f4fd0fe4e3faecf2f5e208fe19fff80706fcf3f6fe24ff02100806f612faf00ff705f2ed06fafdfbf1f101e4eb0ef1daeffe09f2fef2edf10e08110209faebfbe6eef7ffee09d5ed00f11225d40706f0fcecff03110102ef1312e209e9e5eefa1afffef70e0ae90a0411fb03f006edf01700fffa00f209f7f8f4f6000003fdf8f805f802eef9f7fff702f9fcf6020a07fdf60702fef3ebf0ed0802eff1070bee04060000f308fb02f3fb00eff6fe05f6f902fc0710e508f5fcf602faf5fbebfe031c08f6fb0805fa0411f8fde50004fe0303fc02fb000a05f704f70e02f702f01af1000309ff06fbf602fc09e8f9dadff1e2f4cd010af2f1f0f9ee01f907fdfcf50005ebf4fff5f2f6f80503e301f0fa0108fffff4fbffdbef0d01fbf30105eef706e4fb01fbecfee1f50ceae902f4e4f0fd07f8eee1eafcf2f9f401e8f8f706f1e108f2f310e8f104fbfbfce0fdfbf802fbffef00faf6e800e9de0bf7dff9ecfcf9010300fff20310f5faf4d6f6,
      4096'hebfffe0c06f7fe000dfaff03fe00fd0006000200f6fff6faf407f8f5fdfbfdfde8f8fff40103040ef404050400ebf60007fa020004fd0204f70bf6070908fdfbf0f8fd00fffcfbfb0b080703fffe09f7f502fdf601fe0201fe07fff70205f800fef9010802020b0402000cf9fb00fd0800f5f4ff0300070601faf502010e0200fbf1fcf503f8f4fdf404d7fd02effafef1ff05f3feed00ffe60ce8eee4f7e3f60904f40afcff03fe0df3f7f10711f004f405f202fcfde3f60204f7f00dea07faf716f70105ff0af3f30aee0eed04f2fff0fbfaecebfede0710e602ec02e0f0fa0efafdfcfee7fbdefd1405def7eb12f5edf3e9ecfcf8fbfff7f6031afeea00ea88e6d1cdfaaaf9f8fa1eb407fdfaf40fffeed0e1f5c7fafac4e6e7ead104afffb6e80ccaf7f1f8e5e5b4dbd2fac6ed01f5f0e1fdfaf0e10be9fdcd0910d3d6fbe7a0f706fff60683c9e3efd1f0f7a8f2dcf4fbadfffae0e5d6ed04e7ec149ff203eefafb00d7f7c500ea06cfedfbf3eafc05ecf7010d0d01ff05ef03fdeb8ef9f3ed040302f8f8f8fbfff7faecfcfcf70003eff211eb0400effefdf8f6f9fafc02ef0afa0700fafbf8fde5f0fefffb03f90bf5fffbf2f6fff8f9f30407e302f0fd05effa04fa05f6f5fdf4fd0904ef01f5fc02f7f702f41102f701faf8e9ecf6f8fa000afff2ecfefdff06fff5f609fef7f9f9f906fd01fffe0707f7010307f9,
      4096'he50f0f0affed00f600f902fbf900f6fef9f7f9fd05fff403e801ed05fa02fe000711fbf80301fe03e801f7fdffddfbff06f60801f3ff0806f604f1faf9fbf3f0ffecfe0402fe04f6050c05f8f807fb03f6fb0a0302f3fdfcff0308fd1609fafc0103100200f2fd0af708f8ff1a0103fffffbfdfff904fdf803fcef040209f907f8fcddd1eaf91a09050be6e4100606eff0e203eee7c1e9f202f8fe0412fbde10ecef19f9fd27eeecf3f0f0f0f6040a020801ff0403fe15f905f5dffafceee50a08fce30a03fdfeefe612fdd2f8f8bb07fbeb04ecfa02400401da05daf90ce1060a0cfde90715edef05f50a16f8f7f7eff90f0df4fffe0ffeeafe19eb0200ec0202fa02fffe0efdff0400f4fc030004fdf7f5f900fe00fdfdff0101f700fd03fd08fd03f7fbf9fffd0201ff07fa01f4fff9f8000209fe010102f7f5f802fbff03fb0aedff0004ff01040af408f9faf40508f9fefef6f6f6fcf9070103f4f602020201faf9010df2f606f6fdfbf7f00109fe00f8fd01f901f9fafa00f702fe01faede3d8c401bc09e80509e0ebe2f407fef9f8d1e507ebee00dff0e8e0de01d0ffcefd06eaf8f1f008eef1cbe21ceef4f500f3ff0a041220ffda06bbffeec4e716e2dad9fbfafffbd9d108f0df06fcbef8e2e503cf151e1f3cfcf001ef02f7cbf4f20819eafbe6f7def212fdf3e42116e1ebec04fa00fc07fcfbf4d4fe08f6b815,
      4096'hcdf7ff16fbd60800f8f3e0f2f6f7ff0408fbee0efef2edfae10dd8fefffb0200ef06f1e9f6f90918ebe2f8140fc9ed0012fefefbecf50a0020fee3f8f900f70df2ccf806fdfc00e2f8f8f1f90e02f8f9f6ef0e00fefe0818f3edfafe0f0ef2ff05f7050108f10206ffeef702050308f3fae40cfdfe040501f4efe30102faed07b4c1cbcbf0b7010a0202d80bf104f31c01fce5c9f1bee207cef0f2bec302bffdf8fc05f6fa09f6f610f4b1f50af6f7f1fefcda02eaf4d7f3f2f5c80010d7f10bfbcefc03fa09f7a4e908ffe8d2ffb3fcf3e7f4baeae1dadce7d9f3efe7f4beea0ef5eaf8ffee02c7faedfcd1deeafbddfa00d804fbfa0d09e400fdfbfdf4c1e8f9050103fffe00fdfefc02f8ff0400ff01f9f80c0603fcfe0002fcfe04fc0300fefbfcf9fdfdfbfff60302fc01f0fd0705fdfd08f8fd05040002f4fcfcfdf601fffaf60201000802fc00fcfc02fd06ff03f909fb00fb09050606fcf60303fd0004fdf804f8f8fb08f9fd02fe08ff0302fafa0afbfefcfd00fff7fcff0109f8ff08f1f9fb07f8fffaf200f000e5f6fcfef1dfebf3f3eb0dfefdf9f7fef2fdf5faf6fd05f403f8eaf803ebefee05f1fafdfe01e5ff0cf9fcfe00fefefd0cdddafaeb04daf9fb01fee0fa1501fbf3fefaf504f3ffe5f2fbe1f5e4f1fdef04d8ebf70002fa06ff0900e7f5fe00f4eefbf80e0010f3fa0301fbfd0a0e0af7fcf30500,
      4096'hccddf702f5e9fa04fa02f809f5faf70b0505e60a03f9d801e6fdf4e7fefeecfbe8f7f3ff01120108e3f2040b06dbf4fdfafdf80ee4faf808e9fbe2f801efe5fcf2e207fefffaf3ff030701fb0efe0df2f7f5fcf1030fecebe9f1fc0c080af304ff0405fcfaedfbfd01e3f2fdef03f0f2fbeb0204fe0208f8f0fef50cfd04e40fedfb021004f7fdf8f50500f8f8fc060402f8f909fc07ec04f2feeef8fe04ff00f60ef3fbfe080701ded9fb0b01e3f7040201f706e7f801f7f20dec010402de00f6eff7fffc05f4ff00ecf9f609fbf6f8f700fbfe0b0cf7faf5fd060710fbf102f807050200f2f503f7f8f501f11006e600edf904fc0103fffaf7f1f9f900f30ef20703fd020200ff030407f8fdfe03fbeff6fa070203f6fffc04fc000b05fdfbfe05fcf802fc0402f3fa0802f4f50c0203ff0e05f9fc0a060306fd06fb04f9f302f9f0fdfc04fff607020cfef6fdf804ee020ff403fe020b060505f9060debfffe0401f802fc14070cf9f8faf50b03fefcff0d04010100fffa10f5f9fc09f10a02e6f5d9f8f1fd09fffc00f4eafdffedfcf7daf5efbe09fcefe9e2f3eb00d3fafaf907f3fff5eff011dce1d9f8fff5fff6061ffbfbf802f8f2ffebfbffe509edfa05e00002fffcf0e3fbf3fbceffe1f7f3ff02edf6e0e11beb080dd7f7f8f005ec09f3f1f401f9daff00f0d7da06fcfafe0adffefbfe0304fdfb0dedf701e50a,
      4096'he9dfe8d1fbdefafc05f7e71200faf6f702f1ededfac6fbf6d4f4fcf3ec06e302cfffffde00ed02f3f6dee7e801e60afdfef400fdf9ffe501edfae9fdffdaf305ffcad90200fef3bbe2f413e2f100ddf9fbeefac902fbf4fce3f8f7e4fdf4f0f407faf5f3fdf806e6f5f905e30b02f3eff509f6f80404f7fffd0bdee90405eff31909f3e80715fa09f5fcde080cf7fd00d7e904f9defe0cf7f30308f8f1e40506260b0b0cf1f4f0f306efeaff00e2eefa0207e3ff15f2e2fe10faf80004f716fdfd241500f60409f20004ef12e40805fd10f3ecf9fef7f60fdffafaffe6e915fdf8f80afbff0bf7edfb05f9cceef0f50f0017e9f8fdea00f107011ef2f60105f7f70efafd0efdfffd0204fafdec08fffeff02020a09f7f60309ff0f110b0306fc0afefd010300ffecfef30801fd02f404fbfdfe0108fff00306fafbfcfe03f9f8fbfff204000305fb0000fafffc0708fffaf602f40dfd05f803f3fb00fdecfcfefe0403020306faf509fff8f103fa021305fff3fbff03000702f6fb02fa01fbfff7ed09f9f404000df5000cf9f90b09020700f90407fcf7fbedfe08ef080f010103f804fc04fafb14f8e6f50dfbe21a0101fbf306f1061904f306f6fd03e5ea07f600fc03f7f9f4f6e101f6fb04fd13faef05f9f8f4f20d16dce1000903fdfef6f6f90203fcecdf0ffdf7020efb02f5f8fe09fbf5fbf8fe07f008150107f7fef2,
      4096'he3b8edcf16fd17eee7ebec01081105ef08090bfae51309080c06f7e22308ec000bf4f8e7fef1faff1911e2e9020c1712f7e416fbe2fafa182ffe1a0dfbabdd0c27fcda0ffffe29c3e4fee4f8e413ed1217eb14c50f1b2d041ee909e61224d404fe0e12ef10defdd3ea0cf4f5490415f1f5f810e8fcff060502e80a0c02fcdfebf2020907fe00fdfbff0400fef7fe050303fbfe0e0205ed000003fa0705fd01fefcfff7ff0204fe09eef5000303f2fa00fe000707faff1603f804020bfe05fcfc05fe00fd03f7fbf7fa090b00f80204ff010502fb0402fd06fd0201f8fb14f1fffbff01fafa05070407fefd04f40f07ee00010302000206f8f8f5fef80306f40195c8c2d5ef8cfb0308f8c71befeff6f8f9e9c9e102bfd607b3f6e9c7c209b503d8fb04f7f4fbf90211e7d3d2fceef9f703f4f1ebd6f3ddf4da00aeee09d9d7fbf09bde03fef9faa0e0f8f7c2d710b2f9ddf0f4b001f2dfd7e3d1f5e2f0f9b6e314e4f6e201f6ffc8e9d0f8c8f0f6e1e2fee0fe0cf20706f2f706ebfdf9e4b2e7c7e009e403c400f2ff0ef9f2eb080204ff04dde8f5f8f702d3060beadefee706fafefacaf8000ef6eed2ebeb00e9d7fffff01bfeff08f90805feec02f7e6e4fd02dbe1f7fcfd04d2e61cf7f00a04dd16010309d2f306fa01e4e6fdfa1316e4f9fef308f301f0fb0cfc09fef3fefc0efcfee3ff05f30df806e3f801f90602cf0a,
      4096'hbeffd0f0fab90cfcfeffd3f9fafbfaf7fefcedf1f7e9f8ffd8efffeaf104e201e401f9ebf80afff7f8ecf200fdd2f7f713f8f608e5f5ec03f802e2fc0bec0207f4c7fafb02fff6cae2fbf3e8f307deeef2f7fdddfaf1edfbecf2fcf403f7de00f501f20407eafde103f803e8ff06fbf2fbf4f80306f8f7ffea04f6f60003d7fcd0e4f4f008ecf70be406ea040706f30d06f6f6e3e8db0603f2fc08eccd05d0fb2afa14e90305060d0ff0d1e201ee0efff3fff1fd07fbdb01fff7e2fd10e5ebf7faf4f101f711fbcdf004f5eff0f2f2f3f4f2fdd5f3fef9fbfbe0f601f7f2e5fa03fbf803ffe3fecaf5ecffe2f1fe00f1f904e8f2fdf6f5faf70dfb11fcf4eaedf11500040a08fe07ef032306040cf9f8f801f60716f5070803fe05de04f312f8fcfcebf0f3000b02faf10b0af000f704fbf30cfa04fa05031109f102fcfdebeaf500daf5f5f80ee8eefd000df10bf80613011b0007f10a160709f9f6f503fef903fcee0e0e0efc12f8f7fa1c03f100f3fdfe16fc03f7010b00fef600f6050001e5eaeff9fed405f5fb00e7fde5f5fc010302f3e902f2fdfed70fecea05fdea05e5fbf6fdfe010af6e5ebe21801e2f60410fe050e09fd010fee0ad6fe07e7e70ce8d0fcfcfafcfee5f5f2fce90509daf7f008020500020f2be8ef02ff0c0ae90409fd0b0000e6fc00f6f202fde2130dfdfcf414fa050005fdfbf8d1fd0303e3fe,
      4096'hdc011000ffc9fff001ffe5e8f6fefc04faf4d0faf0fde202ccfdd1e0e7f9e5fbe701fde4fefdfb00e3d0ed0909ceeff706e5f7fdddfb1704f4fccefefcf9e3f9fce0e3f70205f2f4e7faf4f40304e9fdf6f6fbebff0ff00610ee1004fd01ef03e700f8ef00daf1f006ecf2f3fc0100e5f6ebfffdf10000fdf2f6e3eeffffd0f204ff07fb0209fd01fefe02fa02fbfef80f0203f9f6fa0004fc07fcff0306f403070601feff000005fe02fc0302f8ff00fafdfffffafe09fcf9fafcfefaf40bfbfc04f6030301040601f8fc05050101fe04fc02f60500030ef80503f505ff020300010203ff01fe02fe0803fd03f9fe00fffb01fd00fb01fefbfbfcfffd070105eff504f206fafb03f8100701eff00616eaf604f1c3e3c3f9f9f9ec01ed0511fd3c03f53ff80a0b13200aee0a06f53307f8f9e5faf7f8dff2e2f8e3ec05fdfcf320f219fcee0402fddbf614fb1509f4eedd05eefb082811fee3ee112af518f00d090a08f8f606fd0201eaf500d9f9f10903050a0002f51205fb03242306eae8f8feecf7f4fef7f707fdfa05fdf900fcfcfaf0fc01efdef5fc05fc0004f903ef02f9f8fdfa03fcf90309ffecef0105fefffdfcfd00fdfa04ff00ff01fdfde3f8f6f701fcfafc02fff2fb06fcfcf102f8fbf7fef9e1fdfafe05f5effdf0f3f1effb00fafcf9f8f3f8f3f7fff8f307fbfb05f9f6f9f4fefcfd04f8f3fafbfefdfdf8,
      4096'hc5fd0fe9f7eb07ee0100e9f6f4f702f409f0d103f807e5fddef9ece8e605e706fc03fad600ea0005e3dde7f001cff6fd0d030700d80112fdee03def7fbf4e7fef7eaeefffbfa03eafb06eaf10207ee07f1f6feeb03090826fef6fafffd0de80d11fe14f801e9f806faeef5f2f00bffdf00f5fcf90002fcf6f4f6ea0a01fce0f6c3f8e3dafdb80517f004faf4f80df1fd04f7d100fcf3de08def4ede8eefbe60fe3fff2e7f1f9efe8e5ceea0008d3e3f50103f304e8f1e202f2fac5feffe9e603f2c8f102070b07ceeff6fde4fc05c3f5f60000dc04f6e4e7e3e108fefaf6bffcfcf402fb05d6f6ea08f3f3eaea0404d7faefee02f902f0ffeff6fef20206caf1f9eb01f6ef12fa050efee1fffbf8f2fef5001610f5d3f3fee5ed00eded09eaf800e9f6e60b050405110ef0eefdfa11fa06080904e8f3f2fd0303f20807e5e60c0c03e5f9030cf9f7f50802f70306ed05ebea12d9f1190a14ebf30dddfd11000afaf605e600f3f7dcfbf10406e7fa07e3f607fa04f70305f5f30b2f0ff9f9d7fce8fe0e08faf3fcef0101f8f1f502f7ff04fff30dfc00e8fdf105edf3ff03fff8fbfb00f6f9f30003edeafc03fdd9f3f808f5f5fce3fff7fbf304eaf6f507ecfcece6f5030102f8f907fbfc16fffd00fbf8effc03030efc02eef8fd0104f7f1f4fc0603fafbf8fcfefff70008f505f9ebfbebf7fafe02fffcedf3f3ff04fae9f4,
      4096'h82cccdc7f280f708f300b9f9e605f1eaf9efc3c8f6bcccfbbffee0d8b3ffbf0bc3f510c0f5faefe3f7bdc2e9feefebf11307f402a1f0cf03eb02a4ed17d4d906f38ade02f6fdf194cde2e0e8ee0999e8e0e1fbb6fcedd2ddd7c5f5d6d5fdaaff07e8fff5fde6fda0feca01d5dae8e7b9fcd6ea080609010bf90ae0f704fd8af005fefa0307fa02ff0704faf9feff00f803fcf504f101fffdfa0201fd020200030802fef90000fd01f3f8fb07fff7fc0606feff0300020e0806fffffffdfeff04f3fef401ff00020208fff800fafffb02fbfc080606ff0e06fe03fdfcfd03fe0201ff0705f9060204000300fd00fe03f7fbfd0cfcfefffd03fd05fcf901fefefbf1dafae4faf0fdf8fbfa01feebfcfffefe07f6faf6edf8fc04fff2dbeefae0f804f804effc01f6f409efefea13f9f4fefef2f2f9ea0001f7f9fa05efffde000ffc08e4f9f804ffe600fdf6fffd060ef4fbfa04d1fef8fdef06e3fa0903f7fb00fafdfbfaf7f8fdd901f601f90004fb0bfefff4f1fc02f701ecf9f7ff00faf7fbf6050b05fafefbf7fdff0af0f5fdfef8fbf3f91cea04f201eefaeb0700fc0afb15fffdedf8fcfe02e6edf811fce4f2050204f909fa030503f907e8f8f9f9e100f2f7fe050409fc0806fb06010201fdf7f5fa0607fe05f401f7fff802fefb04fcf70400fdf8f60104fdf0fffce80805f5fdedfef5fc0d04fdf4f5eef502fbf301
    }),
    .CHANNEL_BETAS(2048'h785d78e2782a779c77bb784077a6789878a377c477b977a87813773976fa7888776e791b789c774877b3785678907816783577b57872778277b977e17800778378aa778b78987872783677a877fd777e790d78c077c377d1774078c677c178397769771c789f77d3782977cb771a77d3781578347802777f782a78d777fc77fb794f78c1780377aa78497800778678bd784f776c77c577fd785977ef7817779677f77846771d784977a077b1777d77ad773078a8785278ac782a7860784278c2772e789e7769778b774577d577e4781f77ff77f677ff77a8783577dd781177da782a789977fe766d77d9781d786a788877e27833780d77e9784e7774785e77c9),
    .CHANNEL_THRESHOLDS(2048'h020a01e4021d020c021f01f602210214021f0210021c020f01fa020c02090207020f020301fa021d021401f201f8022001f4021b01f30205020e0219020b02190226021c020801ef0205020c0206021601ff0204020c020b021602040213021f020c020801f2021701f9021b020b021b0228021501f10210021701fa0201021801f9020701f2020a02160221020d020c01ff020e0214021f01fe021801f5020e0206020401e001fc0227021002100217020b01fb020801f9021b01d101f30202021401ff022301fb02190218020c01f6020801ed020f020e02170218021301fc020f02010218020502200207020c0201020f021e02090223021401f1020a020c),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d4),
    .ADAPTATION_DURATION(16'h13b7)
  ) actor_enc3_extra_pointwise (
    .clk,
    .reset,
    .in_valid(e_31_valid),
    .in_ready(e_31_ready),
    .in_payload(e_31_payload),
    .in_completion(e_31_completion),
    .in_bin_tag(e_31_bin_tag),
    .out_valid(n_enc3_extra_pointwise_valid),
    .out_ready(n_enc3_extra_pointwise_ready),
    .out_payload(n_enc3_extra_pointwise_payload),
    .out_completion(n_enc3_extra_pointwise_completion),
    .out_bin_tag(n_enc3_extra_pointwise_bin_tag),
    .actor_error_o(error_actor_enc3_extra_pointwise),
    .initialization_done_o(initialized_actor_enc3_extra_pointwise)
  );
  logic error_actor_context1_depthwise;
  logic initialized_actor_context1_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(128),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(2),
    .DILATION_Y(2),
    .PAD_X(2),
    .PAD_Y(2),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'haafb29df1828a1f31212161202ec0af1e1f00701fff508f30402f5223633f8e819080d04de020af6ed07fcfa0d050505feeb0a221c4cfe0f0ff4fde5f8100d170020e9e6f8edfdf9fa0f070b0308fd0a0720fb250601f1110b24ecd7a71efe0e090b1a07030ef5e403fb02051fc624fde102301036d811e8fcf9e4272616f8010c12e9f90808fdf5cbe2160e23d1f8dc2b231e04fd150d0e2f32242616db31daf11cd9f101c722ffb41117ee03121dff0311091f371f3a27dd10f9e3f81fd90324f0104b1b3703f7f6ecf6f2ee05fef40c080106e9eb06fce6f7e805d214743942fad50b2efb1ee0d8e7f1edf228fbe0d8cd07cfb6e20d131f222a0721020907de04f3dfeaf2f4080107030802f61ee6f306eff214ecf720f10120e6e8f7f3f50d1d3ff10a03df0306fff3f61b1e14ecd2e4201a2301032105051e281329f8ff0bbcdcc3faf5fb01e3f91afc0414fbee20f61c12d6f5f8e410151025e6eef7f8e1f707f506f5f807e000b20d25e3feffd7e1f0fa0dfa1cfbff0d4845560fdb3548041bc6eac90efcf42b2e2131041411e30c1bedeb211c1114d02402fe01fccef328e41c0ddceafd0af5e80207f70ff1270efe07e60dfa0310eef5fce80cfdfe0af9181510fd08e1edefeae9fc0e08f6fd08efdb10131fbbd3deaef5bb101307060afe11ec12021416142a18f5fce4f7f4e80a1212f60ceee9eafff8e514e40b,
      4096'h17eef4ff0d07f202f80ce2ede5d81fd5aed09c04f40507ffeb1004efeff90617f40e13e5de2d1b2f07d018330d2b2d243e15e8141b2431f2ef0d1203f32a1f34f5010efb0d33f3fd2c0106ea332216e2dfdfc116cfe230f4c020db1ffbfef800e5100df813ff1c05f41a19f4fef8e4f20cfbf217fb091e111908e5f1ece3ee16ef0c30e8f74511e715fd15cedf19140552e4f5e4f5ff1a0c09f80cdf070bed093c130525162df3f8f9f5071617f6da1a00eb12eefee9e2f8100211072808170e08ece40016181634d93bdeda0affff1a2a0e272bd21b3d0b1e1101180408faf605e40a06faed00f70303e9f1f8ffe0e2e6f1ede10f13f2edf9f9f9f5f71d161beeceed361f1a03fc301aef192a052016fb0c15e31a2c2616060908ff0d26f0050720073211eb1a25fb230a05fa080dfaf3f5133506241fe3001c010c2ef828f5c5fd3c371b1d1b22cfc8eae605fc0ee7df3a40f8f9dfcc43e7e701e0163efa0af6080dfe00f9f81d01300e1afed5ce01f2d9dfea0bf2ea0701ff1808f6f7300f48241c1d00efef19eff21f12edd7e6e2e8dee9d4d3e63eee4df5c6daf4fbf0080604fa08f5f6edf612f41a22d0fcf8e5e90c030bffc4f87a1a48171f23fcf409f6e1e0081838f0f81fe6fc07d1ee14c4031dd7e30f56256012e6482e0313130f111cf41afefafb1c1a24faf005ecf9e7f10aeaeded060efd0812060dffe607f8,
      1024'hec06450041f1de0beef1ff473b02080a101d241df6f2f2070e0a1212091628f8f9e5b81823c82c131d150b1828001ffa0804fcf30f0104f3152524ceddc5e6e5ef14022d08f80ff5e50911e4eb13faedf3e7b0ff27f3eaf61ffed7de07f107ff0009fcfef7282631fdecf11709081a071b0bf6010e09121611edfb06fb0606fa
    }),
    .CHANNEL_BETAS(2048'h77bf777c780178ba77d976e8782877b677c4789778fc784c7877785877dc78ed789d784b781c783a788e779b786277f277d8783f7802791b786b7792782a78207827783977fe786b780e784e78a677dc78aa785078c178057840787478b7780d781477e178e178217899783e784c77ff78a477ef77897815783d77e77869780e78a177cc790b782c783b7809782976f377c6781377e07830781477c7763d7875787d781e77cb781577ea78c2789878cd780c77dc77e6787278d77831780178ff77fd784278697774783177d27872777b784777af77e378067844789b782f7813781b781b783e7802782778897837777478a278b87820783e77b77884780b77e9),
    .CHANNEL_THRESHOLDS(2048'h01ff020201fd0217020601ef020c01ff01fd01f601f3020001f401fa01e6021501bf01f301f001c901fa01f301fa020201f4023301f401ef01f0021801f702350221022901f1020d01ef020b0205020901f501ec0202020001fd01fa020b020c02070214021d021701fb0203021d021501f20206020e01f901fe0213020d01e801dc01fb01fb0201020401da024301f701ec01fe02010203020201f10200021202000200022d01fa021d021901f501e9020301f6021101f001f1020102040212023801ff01dd02090208022c022b01fd020b01df01f70225020b01e4020201f101fc01f80203020d020601f7020201f302070207021b0233020301e801fc021d),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c4),
    .ADAPTATION_DURATION(16'h1450)
  ) actor_context1_depthwise (
    .clk,
    .reset,
    .in_valid(e_33_valid),
    .in_ready(e_33_ready),
    .in_payload(e_33_payload),
    .in_completion(e_33_completion),
    .in_bin_tag(e_33_bin_tag),
    .out_valid(n_context1_depthwise_valid),
    .out_ready(n_context1_depthwise_ready),
    .out_payload(n_context1_depthwise_payload),
    .out_completion(n_context1_depthwise_completion),
    .out_bin_tag(n_context1_depthwise_bin_tag),
    .actor_error_o(error_actor_context1_depthwise),
    .initialization_done_o(initialized_actor_context1_depthwise)
  );
  logic error_actor_context1_pointwise;
  logic initialized_actor_context1_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hd9fd04f0f6f6fdfff0f408fc00f6f6eb00f9eee7e4dcf508fdf20015edf0f403ebedf9d5f9091005eff701feede6f202eafe00f1e0fcf2f0f5f8f40301dfeff600ec06edfbfd04d8e009eff8150ee1ebd0e8f7ecf7eb01eb02ddfbe9e3e3d1fdfdecfb0eedfdf1f1f7fbddefeeea03ddf9feec0c0601ec10f6fd010602f9e8ffba0def0f011ccfcaf3e4f6e91bf2ffc5d138dad6ff2df9f928eeef4716daf7feeae60ba4feeff5f8e0d7fac4e0fbc20704f2dcaed1fe05fef011e6eff61a01f0d806be05f20be42322fbdf1feb262dee0cd9edf400f8cced062eef99c3e1d8e9f9e7f715dcfd0e19e30ae8b4da0ef1f2ed00e1ee00bbe206e7ccc2fdf9010e0bcd0501e5ede8f8f002eafff9d5f005f1e8e1ecf40ce7fafdeb03fec2ec070c0ae2fdf909fde2fdfceadef102fcd703f9f5f9edf9fef80ef4faf20500eceefde7fcc7ebe0fe06f8d9d3f6fcf201f5e9f2efe6f8e9f7fae5f5f8f6ffedf5f5c9f30203f6fbf700f7fbf1ece8dfe0f3eecefef5fffff405ddfdebf2e703f6f6e4f71decf924f823f8e0ff14f80bebec00f70ce4f702faea030436f7efdecf0918f30ae90ce5fb02010b0bfc30fbffe9090510fa0209d91801f5eb1800f7f419e5e70ce1edfc19ff01f11aed0d1109ed0910e41712fb00f6cfcd0807fa041309f71601f1e8e8fffb25ea0027d3ffea10fa0c05e404110717e6f9ed090a14fbf1f8fa,
      4096'h03fffc0501f70a0bf30506fbf1fefcf906f803f3020508fef812ffe0ec01f7ff07f8fcea020001f507030909ffea02fefb02110ef703fb0118ff01fa07f6fbfe0af0fefe07ff05e2f603f30405f1eefcfb0204fffaeaf301ece804f7030fff0200fb0bfefe00faf8fff7ef1215fdfcf202f90905fdf2fdfff709fc09fdeff0f5d3f703d6fffdec05f0f3f8e222fa00ebf309e3e1e9fdf903140410fd03f2f3f3d9ed0cb9f2f4f809e601f210f3feed010405e2f2e5f4dff7f3ee00e5f0f2fce008dbea0801f1fb030ff40110ea0414f7fcf30c0601fff7fdf3060ae8e5e9d3fa07eefb17e0faf309fbee35f8f7d0ef0305f5c6f403f0fe07f305def4f712080b10031f00050f1110061bf104080b061c37e10e1e16dcfb07ef1c0ee8e9062d0d0d07de30f908250725010c0016fa300b0cfa2e3cfe0408030b000dfeffbc13dd13f82dfdfbf419fbf901f2f9fa04f71fdd1e1bf2090716f8f2daf22b1640fe0d00f7e5000dfff70828f7ea2609e30817f6f81a21f92f02f62625351c0c23f0fbefff010efaea03f4020711f9e3fbf9f905f6fc09f9ef00fde6fff203f4fd00eefb08fbf4fdf801f7eee1f80404eae305f202f1020f00fbfe08f8eff4f7e308f9efebfbf0fdf4f9e9ebf200f4e9f408f9f90006f6f8faeb0301f9fdf5f4f1edf6faf7fef107fe04f4f6e1fa03edf6fafb00fc10fbfe03ea0109f9f9f70106ec04,
      4096'hfe120108010ff7eafe121802a7f3050a05def31323e2f60918ef01ebf7f901f701de05d20a0d02f118fc1b07cae7f6fdfc05feffdb08edfaeb0fe4fefd0cfcc519f614fa12f90703fbf90c16f4e30bf8e2060a15f600dee612f1fed914f90e01fcfaf1f1f5fff1f4fa0103e1080eeaf9ffedf0e9faeef7e9f4f51bec02efec03eef9f5dffa9106fbf6f4c4e6eb07eeedeeffebf1bb03f707c3e0f6c2e2ff0104dcf1f1cefbeff4fee6e2ede2e3d7de050ff7f709d9fff7fcfdfffc050008c0e7f404f2e7fbedf9caadf4f5edff0196ddeb0503fd02efd8f7faee02d0ebcc12e9f5fa06fcfb09daf2ffbaeaddfaf0f8ae04e0cbfb05e0d90507fffafbf8e6a30407f9f7fd04eefefcf4fee7fcfdf4feeeeaff00fb04f5fff9d20e16d80bfe070a1000fee9fe0103fef7f304fa03e6140317fdfffcf4fdf905f30006fef910dd0c060bf500fef8f4eff0ef000609f5e5fdfb0405e8ffeaf2f0f7f505fe06f8f900fbfcfcfb0efb08fe03dfe2f800e800d9fef1eb05f800f506000408fe06f0e4032cecf10516b005fbfde4e3062b0201fe1b110504c93605f9c9151fce28eb0131013001f5fe170bf300f41ce134c71efe15f5f006f402f211dbfcf9fa0723bd09e435dc2e13fc1d23c50728e31becaa5d39f10004ff11090c183eeef93827303507fe04f335f6530a14bafff5050bfdd0fae625fcebfc01081d080401000ab506,
      4096'hdc17fceff3fafbfef80210fbf7fcff13f70ff402e8ecfbfd0ef6faee1901ebe8ed01030308faf9f1fae2f802e6f5e604f7fdff0001feeff807fcf9fcf5ed29f7fcf6f2f7f9e5fdf6f9fff3f4ee03ff050bf40001fcfff6fd030cff04f001d90900f802fbfbff01d8080ef4f005dcfd10fe05e404f00305fe04efe904fdf8f6f30bc8f9caf7eff6faf5f31603f8f9f60525f3261f09fd09f7d71007f4eb042afefe0cfc2403ef11ecfdf9fff115d21efcf80b0e1e18052d05210d16f9f1f6f4230b0f1a0f04f7f305fc02ef001611e4f8160a03f8010b2f1df9e9083d091bfd0904e8fcf0fb04e1f809df221efcedfc10fe0126131223fd04290f030c000d010716f719f30be2061511f60b16e813081002f4fafaebeaf201d8db14ee11f005040203e806ec150604f3ecd0e32a131809e208f5011e05f404c60116040de90810f206ff10f6040bede70604f603f7f60201ff02f6fd220510efe8f219f1fa1f11fe1beef20afd13fdf9e7e315d5f30a08fc12050dff0e430619f404fafef90406f2ebf6ebef8701f70502b7129df50beee5f9dfe8b5e51b07a8e9e99bdffb09f9eeebf9cf0d080bf0e3c4e001f6ebd0f1f107eaefddfceafbe500090016d9d5f1eae1fbe8ff0de2a7a705e6e8e8dba504cffd01fd1217bcfbf7ddfaedfa01fb0ff504eeec2403e1021ab7a1d5e1f2068010ecbb04e5eed0faffeb0a0ff9d39311,
      4096'heefc05100ff208071808c90acffd00ec00051c150cf50807d61311e0100d0ce72a09ffea0203fc000cfc11e706e7150214fd10000e02060511030b06fff1c40617080e0a16fb01d1bceb28e602f9d718050f07f20c16f81305f606f12e011cfd02f40d1107fb21150ed0f1223513f3eafbee0bf0f606ef070304160c0106d519ecfcf8f0fefdeffc090a0efe1a05ffebdc06f408d4fee7fefaf3f739020a0102d5f70c1501f4ffeffa04e71af8ffde00f602f5eb0a01f5fadc0efe0402071efff1ecf107f10df90df911fefef6fb01ff16f7f50b0213cef3fa17fcf1efdcf7f7ff11e612e300df0ef7f91edfeae413f0030dd1fffaf715020bf8eaddfefa0804de0f0202010ff8f500f2d6f51df006e0f804e4f5ed14f8000700ecf60206e2fbdcec08d008eff8fae3fde804dcfdcf020efbf3eaf5feeaf202ef0afffcf504e2fbfddcf203f204000ffcf400d603fff60cf8070effe2d1ef0c17fad8c4fcd5f4fdf80704ee00f8f6ef0efef0f0e100060200effefcd7e10aebf2f80400f2070b04fbea0a04e2070df5f8ed0fe20405f106fa0401f3f20205e5f421f50c0002040efafeeb09f3070106dbf8fcf4e702fdf8070a12eafd0504fcfc01f4fe0dece2fa10f3ed06f1f601dffaf3f812f4e8440bf8fbef03f0ef0cd9eefbf207110d010af5fc0507fe2005100403fc1010f8de06f50e02fbf3e7ff080601fe011bf701,
      4096'h000b030d06f2fdff0700000908ff00fcf7f502000d0bfc03f40e0ef1e90b01ff010101fb07f400000ef8f0effae8f406fe0a0ef9fa04fe0203f5fef4fcfaeb060afff400fff90ffcf6160ef2e905e608eefb040d0df7f2eeff0505f20cf1170103f80fff01030ff7faf8fefc0502fef002f31203f500de0107f701fcfef6ed01e4fa040df613f0d406f4b6e918ebfcdbe40cebc4071c00fe0cffe91001f3edfaf8f208b90deef6e9dff2fdf1f0efd60406fdf2ddf5f700f0fc16ec00f722fcf0f7fedf010ee7010114f3f81cf2fd09eefbfe01ef06e1cde90b11fedfe901d213fc03070fe5fb0a1aee0600eaf1f901edfe030200fceaf20defece7f9fc010103bae9f3d3fedcfdfafdfbe3f0e3f601fdfbefd3edcacff9f8edebebd6ecf904efd0f204e606ea04fcf3e1f1fd0005d4fff5fc02e9ed01faf908fef5fe08d408efefdff7f9f9f9f9c6db00eb0ff6f9ddf1e2fcf9f0f908f005e8e3f5ecdbf1e9000205ffe2e4f9f5f2feeabcc8d9ebfce005e7da01f6ea00fa03e9ecf3fcfcda0100e7f3e3f49502f80000c011eb05ffe8ebf5e7fba70002fca8f4f1aae3f706edf60b01c3f9fafaffe9d5f7e9e9cbfbfc11fa01ffdd05f1ff0501f8f3f7e8bff4f30bedfd04fff3ccb5e6f3f2f5e89bf6e002fff102f7ed03fee5fde4eddd1be902edfaff0606d9eff9bcddef0bfefab0fcdedafaf4dfdafaf3f6f907fecd94fe,
      4096'haaf0f6d0f3cfff04f1eeedf2cc0302d5f7f1cbe8c2d5f0fddde6f3c4c704fd0bd5effcd80bec01fde6e8ea06f6ddebf6f7f8faf5e6fff504fef9fc02f7afe8ed04c8f4ed00fefdafdb06f2eae902cde3d0f8fafaf2f4ddfff3caf7d6dcecd708ffef00d9f904fd01eed2c8e7d1f2f3b9f906dafd00fff707fdfbebf5f7f1bff610d7e5d2018005f8fbe09dfb07feffcddeffd2ebb52500f68607f7bbdbebf010e4fcddda0a06eff1e8eae9d8dcbef2fb0604fff4c3ecf2f71aeef7e2e3e9ab00d728eafaf2e8f3bcb9e3e0fbeeea8a19c9d800f4eef6e5faf6e3f7bbfdd8fee6f6f510f60e09ebeef0c6d1f610f2ec87eef0caeeeedbc6f6e9f40612eecacbedecfb0e07fa08f7fc0beaebfd26f309dbdc0c04e8e41b18fc10fff5f10ee4e5f9f2e7fff708f5f8f8effcf6faedfbe0f902f800fdfafafff7e7fefe12022309cbffe3eef308f2faf8f504f909f10ff80802fdfd00f401cf01fd1aedffeffcf5dffa010324eefffb1cfb2f07ece618f3f704ebf5e9e70e0cffe3effd02f6f2f7fd1008f1eeeb0aea06e90e3a030803fb1004bfe6f7fbd5e90012e8090ae8e8eaf9df0000e7fafb03120d12102bd5ef0d03f108f1ef1406eefaf003ef00fbf3f6eb0efcfad8ff0bee0a001df1fcef001aecd7e1eaf2ead2fce80ef5f0b9f3e7d6fefbfcf6fae405f7dde0032104f6dbfb0a0418e8ef0c03ee05fbebe7f3fdfc0b04,
      4096'h0e0fea11fcfa08edfdfaf1f833edf7f415f9fefe0c0dfcf900f7f5e7f2f4ef0604fa10fa04fdf8fdec081421d6dae901fffffafcf2fbe6fbfcffe4eff8290e04f806e9def6eefb0608f6fbf0f402f1ec16f8fa16faebe4f9022efada05e9f3fa03000909fdfce8ff04111bec0adbf6fdfef9f5f6fae6f10ee7f000efffe308fc09faf220f0110afef518f629ec09000cf2de27ee28c6fd1237eae8a7d0000af73cd00de915080ee909e61d0d03fbffe30a141c21010afff2da19e7e2fce6dddeffeb0e0a0f01ef05f3012c0fe1ce0d15e40f1407fed2f80208e402e8041f0e29f300effed4fa36e92626e81ef4340300f3de4316f201f005073913f609ece5210805020107f801f806fc0afeec03fe131900f6f50105f001fb140907f2fe0a02ecf7fdf10408fe0608f615050401fafcff00ff020104fafd0e05f9f60011f1fbfdf4f2f20404fd0ffffd0605010ef7fffcff0506feedf905010505f202ecfe1807020b05fcfd130101f0110a240cfaf500fe0d08fbe200fbfa17f2fb020aff00fcf20707ffb00dfcf0eedff3f40d08f91b11f010d6050300bc05fbb00f02060e04f2f0e3022006fae0edf7f6e4d3f7fd19fe0dfcf204ec0426f70d10f90fc41ff206fbeef8f301d3d1f9ef050be0c1fbf3f4010203e9ebe90ed1eefe09e0f7f400ff0b0104fcee00feb7e11004f806a60623ea07ebe2eb0208092401fdcdf3f8,
      4096'hf805f909feeefbfef6f7f604ecf8feebfdf5ef03fefa04ffe7e6f0cef3fb0ef008f1fde102020306eae5f9fbffe7edff0004f7fbeffeee00f801f0f701fddcf9f4f6f4ea0204f7eeebf6f302f7e9eff0fcf901fdf6faf2f4f8eaff0cf9ebe9f7fef3f3f10605f60afbede8ffe6f9fec500edf6f7ffefed0200fffa07fbeadd0502f2fd0d01f40605ff0c0403f501fdfb19f00b0b000b03fee60418f10efc07030e11000cfef800fefffaf9090bdf040302080203fd061afe0e140cfdfd02e80a0613fc1a000b1dffee01180711ffe5080cfefefc040e081106feff070c000b0203fc0efe03030417fafe020f2b00f7f8fff60809fc02fafd0102fe0cfb0ef306dee9f2e3fdb7060bfd1bccefdbfef6f3dae1cad3abc9fcf4becbfdaedafae7ebece1fee2010212f0d4b2c9eae3f5c3ff0cf9f9e708f8ed02e5f2dfe003cdc7da03dce4d3f1e8e0b5a8f5d4def9edbaecccf8070ce7fbddeddedefacec415cde1fd07e1d5f807c3d8f7a6bbddccfb09a4ed0bb101f1f30ef8fb03ece400e9ccf8fcfd0500f9fefa0d0afe010019f8ffebf00def0de207fffaf3f6ecf7020af8fae10307f901fb030cfa07e9000008f001fc00faf0f6f91402ff070a0405030715f500f1fff90bf506fa0517fc010afffc0903f50b030df700f21704fbf1ecfce9f0090622f101effdfaf900f8e8f40ce90410f5ea05e71307faedfff9fff1040b,
      4096'hc5f8e7e2ebaafa14f7fccb02f112fcf2d9cec1d4c5d1e3fcc1e7dca9edf5e101cad0e7e6f80207e8e5caacdadbeaa30ceaf5eaf4f5fb00f0eff6fd0303c3dcd2e0c1eedae00cedb6b9f9f7e9f8fcc4dec4f9f23bf106cad1f3e2fcccdfe7d1f2f623f6e3e701e2e80ba8edb9dcfb0ea40418b8e614d706fd1801eee5f0ebbd0a12f9f7fff9dffaeef7fac9ed11f7faf2f30ffdf9de050cfaedeffafa04ffe50d08fb02f6f2eefcf2ff02f9f0f8d114f8fef800f915f2fd02fefefff9e73cdff3f713ebf7fdecfb04e0fcfdfdf701c9e20ceb03f8f60a03fd0b05f9e801d520fcfbf7fdf80406e416080308e117fbf4f8f9ddecf7f8f9fa01f8f6f8f9f9d9e6fc040908edeff2ed14fdf00b0303f407f3e5010f01edcf0308e3eb11f0fa17ecfbfd05ef58f60309fb02f1e2140f00e90aeaeffa1d2901f3f6c80c37e909e32903f30a02eefff4ecf808f9e8eacfde19f2eefffff9f9210910d3f80124da2c0fedf11be4eb0704eafa07f1f311dddf0d18fd1506fbf50e290306f0062102fe11fe0ddd02fb08f3090901fcfef6e901fe110ef40efe030800f9e2100d00010315050101fefbfffafff51507e7eb14f71c000409f8130c050dfe18050bfd04e5f41d110e1c11020101f909080b032503e8f908050bfbfd04141ff4f8fe2e000315050000fff9fbfc0225fbf3061b1efffaf6fd070cfefe16eefd07120f0ffbfff408,
      4096'h053df6ef17f4f40609ff08030904fef1df01f605d5cf0e0200f7f9fb08f7ecfe0008093804020cf5dce8e62f0a14e208f606fa261efd03fbff0016ee06eb5b12de05e3f5ed000a09ff0ee309edfa20fa18f7ebf30e0d3104ecff0a2ce00dd6e502fdf6eefeffd9f1fb0aeb04e1e10f170411f4ecf9091d0b02f6ddf802eb0316f1f207fffc0af7ed10f2fbf619f609fd2112ea0b0527f20013fef51d050f07f1ece6ffbf070404040208270ae6faf2060ef7f0f9e2fe0d01f801edfefd0903f30a13f9040e00f3fe13060efaf906f0e4fefc02fa0bcff8f91517f9e610e0f6edf804071501feef0cf00607eb01e0f7e6f903e6ec09e5ddfff3fde7f701fcf000120d1b0cf6f010050bee0606e508fcf70f05e3111304ff10f01d07e9080f0a08070e02f6fb07f91a06fe0d03def5150403fe0df0f5fbf104191b0511fe01fdf9f7f6ff0c0e0708f7cf0a0b16e214f300f605020200f7f0f80e130cec16fb00fffaf1240afffb041b0ff4edf6141ff9eafdf816f8fbf6e10002f907feff00e2ff0d1a1b1d0708ff18f903fb08edfe02100fe11001280f0406ff1c14ef030c0bff2505f5f00bf90f0d061b320115ec11f600041b02ea0617f62e18fb07f3e5dc14060ff71300080405fa270a0d041af017f2fe080c07e001330fd20d202f11f61806e715e305032ef508fff92a2826f61001f34a160704eaf71011f1140dfa0ff7,
      4096'hf9f40702fff500010003fb08f7fdfef700fe0afef70307fdf30107fcfcfbfb0307fd02fb0302ff04fefe00fe0dee0f0312020403f904fbff0409fe0002fff1ff01f701ff040105f5f9fbff010bfeef1502fe04fc03fcf608f0fefdff07fc0009fc020401030209fe00f500f70105f8f700fbfcfcf90bf3fffe0201fbfefdff070908ffe8faf900020b04feee15fc04e2ebfbec09e402fa01f1eaf3e20304f503ef0f00090300000000efe5f7fa00f409f2faeef704faf9ff0002000803022d05f001ee0bfc01f901f60d00fc12fefcee2604f210fe090e09fe2501f5f2db0ee5f40a1216f100e7f7f8080b04fded07f2fc21f7e400e81a07f200eedd04eb1808e212fa190a01fdfa09fde5f0fff700edf6fb02f810000bf4f814fee7fa0c09ef0af5fde503f9f60a12f711f5050414061102f3f9030105ff21fcecf9ff1ed2f916f7f0f31af9f7ffff011809ff0dee0eff0c03faf8f40af11913ffe91ffef10303f5190f05fd00f5f6fd0dfd2c04f9f406fc170709fddcf5f20007f0ffececfff2f90eeffce40d1bf7ff05f9ed0b070f1ffe0dfcff09f4f4da101ffdf2f900f50b20f501090a0ffd1b10fb0006fd1103fa06ff12150401011df912efffecf90f0e142a07fef218f5ea0b03fa0b0fe20507fc121000101f0cfce5fef90d08280b040e1e1b0105011008f219091309f8f303ff1c15090df40208201819fe26ec04,
      4096'h020118f1f1021109fb1ef411e50e03102017fbef07fc0b0cf0ff1007ede8160025ebfde8ff0b0a0e05051df206062afbf603f009f909fd06fd0aff0cfaffd807faf80615030fe5dde70104fc0bf6e016f412ffe6fbedf41b19e3fe061604070501fbf4ecfe030e1210faf12f191608faf7f333f202090200fc1315f60403e90801fbfb0700ca1005f0e4ba0bea1902f703fcf3f5d3130f0aeff114d6dffcfbe711ff01de09010101fdeaebeae1f3090004f1fbf1eff6f106ea080307f9f5e3eb0709f6f5ecfaf0efbcdbe0e7eaf6c41be9e2f9dee901ebf6fcf9ebef03ff15f5f80006100b06e3ea02fad7fbf900f0c6fde9e5fdf8f9e603120f100802cfe1fb1af5f9d3ffb7f309f9e8b9dea5f0feceecfad6e9aee710f8b4e2fd9fd7f1e1fac2e601cbede0f5f2debad6f3e2d1e10fea030cf8d7f9fafaf4fbf8f7fbd1c3d809c1e0eaf1f2e890e2eeeedc0814a3eaacf20c07f3f4cbdaf39ee7f5d4fdda0d0afffae6e201fbf00da8aec1f8dafb880601b001fcd4f2071821d4eef6e286f71410eeef13a221e7f4ede103f41000e8f6eadaeeb8d3f803c4061ab1adfd01f0000ff4f408060c0310b6d4db14dd160c010207f31e00e40b03fb101110e6c5fc000713f5f70405b19b01f0e228efb20ebdf0fc0e0d10ebf7ea01faf8f6060a030b04f3eb0709e9f911a6d6f2eaf10092f702dd02e3e1e205300e120305dfbefc,
      4096'hcae401ac0ed20000fe16d906e702fdceda19c2dc8fbae602dee9f7f5d203ecf6a1f207f2fefb1401e1cad7eedd0bcb0ce008eef4e4e8e2f7df0706f403c805d2eacbe7e7f3e302bbcdfae5fce3f2d2f8d7e5fa0bfc04d5daf7d50ec8bcd0c6e4ff0af0d8e903dfeae0d4d6cbdadd19970517c3010be80d090cefe9ef04ded100d3e7f5cc0097fef1fdeba805c80710d2f1fbebea88eef8fc9edbe892c4f6f6ef0ee2fb9afeeffff4e9cceaeff3aad90300fafb01c304e2f4f20202f8f5dbbdecf6c1f1f9e6eee7a59b04f5e2f5e789bcd1f507e8f3f2cdecf8bdecb7bfdc021406f4dcf1df06dde0f8baa3f2e1effb8000a9b70effd0d5fcefe1e904f0e0abe322f71afcf9f40617f003ef0ef413f40f17ff010bfdea04fbd30817e700f1fb0a331106fa0d04090819130f05450126f20b0109100902f009f3012a0a0b00cf3904191b0f0710f708def611fb13fde81bf20003f7fc08060304faf3120d173c1701020afa10fef71206ee051c0f1a020ff814150efc0a0300010e0c1606010f052df207ff0bcb13070407021bfaf808f9f6fdec15eefdfcfdd4e90c0dfa07faf610eeed24fd0a0f1207eff01101ecf3f9f607f5052cf803ef091d0cfc0af3ff08ee0c1bf302150bebe5f624f704fee0edfd0cf712e8001226fc14ff1a01100ccd02092df32503fe0f1a0c000209f115d9f903f7f4fd0f16fb08050a020a18daf6,
      4096'hdcf0f0cef28904effbedb9f5e0f3f8e3cff8d9e5af080304970afe9efcfbe90ee2ece2cbfd0debf2e9c5dcdce1bbf0f7fc1002f5d1fefdf4f5ffecf5f4e8b5eee8ece2f9f8eefeaba0e0dfede6e796edceeafae1e9ebd2e5e6cafadaf6cbf1edfa0ae8ee1b08e3ebeaa2c4d5fbeaf88000e3c6ece6d5b9f1e2e80a0bf4ca91e00008fa0bfefaf9fc020301fac8fc0300d7ed030811eb0701f31311d8010707fff605fe0400f7fb01fbe5ff0a06ea05fd0f0802fdf60209fe03ee0cff00fdfbfa0ef1f502ff04ed07e6f60c05e8faf804ee04ff0b01fdebf3f2f1fc0512f6030a01f60c0500fdfcf412f900f81007f6f206fe0c02f9fd07ff0204f0fffef5ec0118fad2eef33709fef80adce601f60af8e9feedf8d214fcef36f9f8fbecf801e0fdf4f4f90beef6edfaf3d32aeeeab5fd08fafef205effff3e4f5eaf405fc090611cffb24fb0c0de61523d5321b15140a071cfe11f400fdf1f7e50225fd15ddf706ed081411f81bc1ec43f1daebeaefecf6e3db0203090ffc06f9fc12024cca02fe03070301fd01fa080efa01f205fbfe0bf005fb03faf5fde5080ee8030a13f700eff6eefe0af80607120cf408f812fbf2020307f406ed091007fc04fa04dd1607f6fdfc02ff040006f50d000901ee0df304010a00f8071b0aeffafb11fe030805fd0aff110305fe00ea0d0b100402effdf41b0bf510f503000307f807fdea02,
      4096'h0f0cdffef905fc0eecf3320b1107fe14d7dc10f4d4cf0010e1d3e0f30be111de0301ed41040c15f5e7e7f116f2eddd0104fefc141401f3f3d804fb0af80202eb0ed6fae5efebd4effcfdcf06d6dc01e9fefff2f8fbedecdfe809f81c00f9c9f0001ac8e70bf9efd201d1f502c8fb0b12f11acdeffc350ee308f9f4e701d20201ee11fffad73ae60e151601f2ffe00ce7e3e006fc081bd4fb76efdd2cdb0c01fd06be06d61ad2ebddd91941189af7e4010e04e018dcfefae9e6f5e9dbfdddf8ca1cf3e70e0428f72a1ffdcd0ada2337ee02fa00e6fde0fed71505f50fdcdac7e6eff0ae1ae600faf4ef2ef005dcddea12ffe7ec1afed5060fe3e8ccde1122fafcda10f2dbffdd04fafefed8e9fc09f7f0fcf2eef1c5c20501f8e0eae9e0eff8f4e2d703d8f2fe00d303d7d2f2f9f2e301fe11edeff1f6f102f7f711faf6d204e9f5dee3dbe9e10dbbc501e7d6ece2d5f9d9f3010d0df0f30fefdefcf5d004d9e8f4edf2f2e9f9eef0ffdebce5d3e6fee604faca0aee00f70423f20203f6fde0f4f7ee0ce008ed160206f8e2010201fc0d26f6041407fa16f7ed100be9fc0cf9f62c01f9e5fcfcfbf9160701f615fe10fbfd0b0414ee07ef0720020b0604edeb1d19041a0d01070bf9eb0bf9021d0ced0813fe060b0bfc071e03e2f71d1b23110b05f718f81604010c0700e22e18f4f3f903f22f0a08f7e6010cf91a110510e603,
      4096'hdfdaefe4f42be6070cef00f400fb0102f404dcf6d70806080bf80418e6fafb0de8ecfee40a110a09e9f3d0ddd80dc00dfaf9eafdedfafdf7ddf7f1e400f907de09d9e100fb00f3e2fdefe2f3f11003e4fa07fcecfcf3e4efdbf3fcf1def7ccff0903f9d6f000c9dd0d1cfdd0eeea0707f6f9d804f4f1f4ea0a03e5fc01e4e5f5f50df8290d02f8ea04f40911ebf500f91df8fa032ef2fe06fd18f8b807100c0010f1fafb04f302eeeada1a28cbd8f7fc0cff18fdf8f603030d04ef1009022500f7eaf600060a01f1f4060509fc05fff4c30d07f908e5f2b301f1f9dffed6f5fd02f6f5f7fd061700f308fff9f8f6ffecf9f70df2fa0de90afe08df0cfcf50b0efd0cfcfcf1fff9fcf002f1ef17f8fcf3d80decfbf61908fbfaffe9f525f0faf3e30803f904f4eefaf9f6060de601e3fe08fbe9f5f6f305ff01faf2f807071d0f0505e4f901f707161200f5f8fdf802fc1300f6fff3f8ed05042209e3f0e2eaf3f706fe0ffa020afdf4fd07f2f6ef09f9fc08e7f8f4ea1414f3fafefa0604040224fb07fe16cf12f610f6e6f21c1b02161710fafd23fef9f6922b230123ec26fe3b05fcf8fb13f6052e2624f41c0c3308e1fa070b17000b0e32191d0afff8e67f274d291106f81eeefb0e11e13819e007091402fc09ff132ff417fa081fec30e307d926143702f84009e32d4037f5010b03161c001110f3ff00103c04fcf80afd,
      4096'he4fcfdefffa9f4020703deffd60303eaf6f3dcedbfe9f7fbdae904b9fafcfae1eaf7ebee0c0607f9dfcdeff6e3ead802f5ffdf020ce2e105e9fa10021616e8dbdbf8eaedf8f9fc9da3f6f2fdf4fcc2f1eaeefd1afe06e6e6f9fcfddddff300e4fe16f3dcfb02d5f112b7d5d8fcf509b20215d7f8f3dbf90514fb16f50be4af01f8fa060702f5fb0a000b01fce3f6fafd2601fc110202f2fbed170bf702fc04fe061501f902fcf805f20210001deb20020a04fa06f602eaf9030c0913fbf5ee0603040012fcfa11fdf5f00cfa1afce4f9fc0501f0000f030203e8fbff0afe0011fcfe100502fe011901d3fc0a0201f9ea02ed0217020a00fb06fe0f06fd07fd0b0401f41a03e3fb03fcf3e2f500fbfe0a12f4fc10fcfaf3f4d9170aef11030c0a080502fd07f004070af70ef40be21bfc12f1fdf9e1f9f606fff80706f909d50dfa0af90f08f10d0bf1f20a13300ccf05fbf6fe0104eefd09fc02ffdf15f509100800060404040efcecc813fa3409ed08ff04ec0a050fe8f406040605f400f70405fa0107f309fcf50005080008f9f8f7ef04fff9fc0efe0205fefef4fdf705faf8f8f00e01fc0500fdecf416fdfcfdf90f0401060efefefcf7fbe003ff1c1d070aebeefc01f7000606fb08f7e903f7ed08070306f3d9faef041302f305dce506ffedfbf9f90421ef090310f8f106f908fefef007fb020dfdfde8f6ffff0400f6,
      4096'he8180fecf207f601070602fb16ecf9e4f3fcf1f8f31c050903fe00eafe00050105f108edfefbf6f5fe09f1f7f0fbf1040c0af802e9fc03eef5f3effe05fa01e210f9f701f9fe050d05faef0a0205fbf3fa070a020000fcedfc0703f1e501d10afffdef10fa00f605ed0129f9f405f80404f9e806f9f20af5f407fd02fd16071237e7083bfac714fb03f2f2f8ec1a0bfb2319f807e1f8fef3a9df01bb0800f105052a06eaf1ea0412f002f9f4ffed1fff0901efebfefa0503e2fc10fe0e2800ea002b04f1eb02f4e2fcf7fe04f5f6b6f616f403fa0310eef30605fbfffff120180705e2eafcfddb05f3f6fb071a080b1a0af8fd1800f6dcfb1af21211f2ebe60c08f917f9000105ec091b000ee903ff0c0de908fcfef60000f807f4edfef70c0215f8ff02f80f0400f6fbfcff1203f2fffe0c020702ff0001f503faf306000de102ef0c0c1509fae7f3001403f2e8f80f0b0802f30cfbf6ebec14f5fa1af005fcfcffef0505ff04ff0ae9f61e190cff0502fc03100a06000101f5ffec00eedffaf8eb0d0f000209e4ec290619c310f8093efb20000dd8ef0007fcf1edda060c0a16f2f8ecfe07fe1001eb16fc000100040bf81f00e508e305060ae80700ecd8020fdb301e040621fd01f0f8fb0407f92d09100f0907f200e317de01f917030a330be5fbea0f0334f60dfd0015240c00ee04e42620ee13e1fb13fc190afc09d60d,
      4096'hf1e7e7eb04e6fdf6f202fb01e20d0ade22eff7ef080300fefd0dfbffe203eefcdbe0f2fd00fbf910f5e9e912e8ee120ee6f50ff9faf81a031aea05fcf7beed330eccee1aee0b19f0f8f4e3e70b1ffefafdf70b09fff75f1405f90af20613fffc04faeff71a0311d408e4fa0205fcef17f7ed1c0101ef040d1bf9fceafa16f9ff16ed02f4f204041af114fd07e3fb02180cf3f2f70908f6f6f21b010504041704150e07fc03100302f8f7ee000bda1bfef4061cff1906ff020800ef0203f0f90110fa1c1203fc13cff9fc11071dfff70cfdff0800fb070b05f9f8fe0202f0f82402f61cf8feff1fef08e4ea1c1f04f719fbe81014050e01fffdfff703fc11e80de8f8dcf0f926e10408ef320208eef713e3f6e00c1f24edf758dcf62afa01ebe10ddaf9fc05fff5e9ec04f212d7f0daf535040a12f2fd1ce5ed04dee505cbf2c910ede3e5fd12051023fdd327e10d1ad71609effcdbd7fada0bfc0fe4dc06e9f0f7ede1f7d0020ef4f11b06f7e900fa28f12001fd02cd1e03def0cbeafbfa19fc2ef6ea0b0ae21e1209edd402f007fb0702f32d0af616fbf4d4e421ede4f3da0630f4f703f2fe11edf4f9e6e12bebf8fbe713fa0f35fceff9d1eb30ea0041e5e3f8061cf9f6f717c60a05ebf809eede2613eff6021248ed0fec0505020a262825fff7f2cafe09e70c30d4f4160ded06fe0303ee26f61e120604071c15fd2fccfe,
      4096'heefbe700eee6fb1808ea1303fb08fcf5f2fe01f6fbf80107fef7011d30f601f818f2f23600070605f0f1df17f603e109f8fef9f01cf4f6f7e7f51ad9fe180b04e4f7eff7ff11f50106e10701f4f8eff21f03f9180722f211f1f4fafbf100edfefa1cfef3fe05d30901d8f61be2e71305fe060df402082809effd0c08fff00b05e3eaf0f3f79dfdfb08ebe405d60a0bf1e3e1eae7bfeceb09c5c7d3b7e408fee9ebebfbed04100700e7cedaf5dee2dc070302ee03e900f100edf409e509f3d8dee2e1eae7fa06dbbdbbf3fdd7dce9b1f2d407f41b0511c4edffcd00c0fadff0ee061fe4cff108d2f813b3d3dbd6e910a6f614cbfdfcecfc021ef7f708f6ebb5fffbf800faf2d1f6ff02facefce6fafde6ecf9f201ef1eea05e601f7ebf40405081ddbfdd4fef6e9fedbe8e310dfee0f03fefde005cd09f2f201fd00f1f906e8fbf70bde01f7f0eddedcf9e8fd05e5e3fde7effdeefcdefa09eacff4f1e4fbf9f900fef6f4f505fff4fdf5c8fefedbebd00a03ebfbf3ffe2f808f319f701e3dffbe916ffee0212f502ff02eef116f1f900f1ee03edff0d0a071f0d08f80ef30704fcf510f4fef8f501ec06f60beb13f1fe0901eaf0f5fdf7f0f7e400eff0eefbf70ee707f50608fe1fff08f316e6fffdedf30208f1f308d4daf509fadfcbf6f3fa01f3ed1ee5fd0d11f7f8f5f8f7faf50104f7e50001e5f1fa04e4e2fa00efee0e,
      4096'h06ff0b0e04ecf00dfb090107e9f805e705e2fd0f1bfa0903d30c03d7e80900f50702f8fb06edf60ce810eef401de09ff0d0400fff0fef10407f9eaf300eecd23f3f5fdf7f7f407ffeaf2fe04fdf3e8ee02fffdf1ffeb0f1d0edffc0e1ce3f80001ff190303060afbf8efda1c18eaf7ebf6ff0a04f9f9fdf811f2fb0803f206082418f326ebcf0cfe10e9eafd0705ef09e806f20910d60600d0e6f0e70eea13dd10e7f806fe0b1602ffe22b0501fcf4020d09e408e3fdda03e20efcf7000904d8f1f8e901f904dc0eeaf2fd09efffdb0ff404fa0d02dfede9e80407ec3914e9edf9f301fa0bfe06fc25af0401052912cbf5131ce6f713f800f0020108f7fc18f81a04041dfe04f6fdfb00f90eff06020b13e210e632ebf801f81407dbf5fd390232f9ede302f1f9070ff10606f9fa0c010e032117f7fe0afe09ea130601f802040e0406f801f71f020103eaf6fef8f51402080a010ee92f12e4e90a1e0741dc140401eaef050304f62320ee1a3be7f7f205f85211f42deffef6152d0bf82d03fad3f903eb02bf0af5f4fae116e20909f7fafde4f0e2e50d04deea0ad0fffbffee0aedfee2000cfcfcffe0e4fef0f10800eefcf908db060bf9f30ce8ec0ff4e0dcfaf001f2fc12e4e3d4f1e5e6efe2d701eef506f9f9e6e4fdeaf8f5e9f1ebeff8010af8f514fae910fcdbe8dfe3ff02ddfefaf5f7f7f1edf6ebfe0b14fedeeafa,
      4096'hf0fbf910fffe04fd03f5dc0116f101d5fff9faf90e2ff300fd0bfa02fcf8f10501f8fc11f70afb05f3ff29fefb0021fffafcf7f11101060305fdfb0aff17e8f4010ae6e1f7fe0a05faed02040afef1161bfc09fd1ceff0f90212f3042b0109f2fa020c22fc060c0809fcf7ff2218f915011512faf10c0912fafa0afc04fe10f9cd09040ef8fef301f4f8eee82bef05ccd3020dcee451f4060bf70327fce4eb180a05ffcaf213ff07e206f8f5f1fefaf70402f3f6fd02fdec0b0106e5f400ff03df2704fff82403242c02e7100a0907ed08edf805fdc71824f507ffdfb2d4fde5f5f8eb00f6061219e9ee2a10edf200080102f7fe15e9030ef8fbf1d4f2ff1af6dfdd01bafdae020202eeb5f3caf402ddf9eacbe286cc0304a0fdeec1d3f4f2fceff3f1c11cf5f209d0a1d9e4ead5c702fafaecf6d9f6f1f1de19ffdc07e9c8d8d2c0f1dc03f7ea8587f2e0e8e0f1c4e5b5ea03fef1f6d2f5eec0f7c2cbea09dbfb0df0d4f9fddcfc14a3b9dcdcf2058009efac0b03e0ec0d1fdedafa07d78207df1205f7f220f40802ee30e415f0fbe7edebe8ecd107f7011804f31509090402eafe01e2f3e8f911f3f1eb18bee9dd030209f3f3d8f6e90af80302fbfe0311f40703df0308fafa053805d81adb0718d307e1061112e6fdec102d04d1efc2c7ee03fcf31c00fd00fff5172ff6e0fbe70808f7dff20de91403de0acbe8f9f2190a,
      4096'h17fd0a1e0009ffe2050d1bfcfd11fd2b1ee6eb0b22d7f2f8f116f60ee7f607fb09f6f72bfff1110c28032305f0eb35f7160afff13304e50e12f302f30006cbd618e70dfefdfeeb07fbfe0f0eeffbf305ac110e08fbd6f9e31be7f4ee20d2ea30ffff1dfb070504eb0ac61b221d10f8fffa0cffffffe5f3ee06080cf604f2f906ecd0fff11707041404f417241a0012df20c4f700cf2711f63ff91e0100fdfc04f30d094b00e7231f12b6b80efaf2dc19f20ef722f81001fe0feaffe91dcf0ae62deaf4e1f9f210e110020f0a19122779ed09f61d051e2a1617faf3ebdf47d721030709c9e9057fd6f536d5fbfc3003030817e4f70a340bf60afbe524fa7ff816cdfdfcdffd12f2f60af6ebf31af9f6e5f1fae3f4ecf5f7060afbe6fc0102fbfce5eb01cefa0700fde7fbf10ae6ecf1fe04fdf5fed2fd01effce4eeedff0aeee404e2f2fdfc04fe0b0cf9e010f20cfeecfd0103fc01e8f9ff0009fbe3eefcb8ec0320e702fcfce4fdf10818f901fa02f6f903f10300f8ebfde0f1ea00fb03000716f9fff1f700f60cfa1410f50000fefe18de08040ad810fe002a0fcbe5001204ea13f41ff9fa0e04050a080c11fd23021df40a1613ff03000b111d0f00f9faf412091915ffedfdf311ff130a0bfbfdfddf1107f4f3ea19f900f4fc191a13fc09fefb0af3020414050f03fafe0717060d01041012fe18ffedf8121e050112ee06,
      4096'h2ce8edfaecaafa08e31ecbf9fbeafbfdec1e0606cc1cf4ffa40813deefe514fa0c08ea02fc06fdfc05e7fae507da1ef2f9f9dc022a0505fb09f805fcf909c91ff2442a0301000b07d2e6f9f30af1b51c0deafaed03e5fc2fea0cffed04ec15e50808df2605fcddfc07e0f70017edf908fd2ef7ebeae5e7f8f6fc0501f8d13ddf1311fb19f705ff1708f514fdf208fe13eafd0a190be2f2f9f4e6d8e3150c14f1fe03f036fa090304f3e6e522f2efe9080dfbf8f20efdfdffe4f202fb00f81f00f5defbf1020af205ea020806dffc10f4fa04fd10fa10ddd9fe140014eaffeaf3ff21e4f5ef00ecea010a10e4f5ee0d0aff02da06fefc230cfbfcfcf407ed030806e80f0209ff0af90f07f900fdf800fc1501140207fe0dfaee170e10fefe0b030903fdfd04f6ff070100e6f40def0ffdfe0703030ffe04071a07fff9fff9f4191500040504f212010df910051e03f40ef90203f507ff131907fe031f060609f802fb0f030004fe00f8faed1a0bfefcf2fefd1406fb23feff0203000afc0bf00a0d04e519f10cede113fb12fd19fc03e6e10500dff40a07010df3f5f5010af2fefbfd04fffaeffbf1d6f6ea1ee8ffe2060103ffede9fcf0fdf9fff107000d1beaf7dee6f0edf300241409f81ceeee13e204fffceefcf9d5e2fb16fdc4f2e6d7f5fa0ef617f6050c01ef09ffeee607020401fcfd0407f3fffefcf0ed0702f41e0c,
      4096'h11fcf70c06e404fb03f5f3fcfb0800e9f7fefc04e70ff400dcf029daff00f500190efff308fe0cf304ec04f001e8240003040b030201f10ff80013050014def0180e03f9010909f4dd0903050ef1df00f4fbf90e08faf1f4fcf400070a020bfdfdf9effb03fef904fce2f506f3e80cdef4f7effef5f7e8011700050a02e8ef1020e6ff14f2e8f8f2fdf5f3fadc02f80405040b010711020ce50500e703f9fa0d031c01fb05f9f7090ae3fbe901ef16fe0203fffc12ff0f0313fe05f00214f4fe040f0907f40203fef6fb05fa09efeef509f4fafafe0bf7050300e9fa01f5120b06f9fd01fbfbf9fbf8f6ff0219f1f10cfeea01fa05f7f4fcfa08f90c01e0ebf90bf91614f7fa070b0c13020cd6fd0106f5e9f00610e9070207080ae2ff0e15f70eeeff06fc120709fe03100809ff1606f905080af402f308f504f40df927e3f10bf514fd0b02f203fef308f80b02f620fc1209e90103f109130afdeb1e03061ffef40a01fdfe12f41ae4f2fc132208fbfbf91a050204f9fcea0b1ff901e9daf152f30916ef2a040d141819e91ef5ff05d4e841f01cd80c0611f7e9ef22ea0afbdef30720071b03efef050924f6f4c8fcfd16edef11f125fbeb06f6d5fbf114d708db20e5f2e3e8ee54070516e1e427fff91c05e1fd05edcbf11f01f3e2f2be2106f9f704fff91ddf0eff01a7f912fb0e01ecd8f8f2e40219f50ad906fcf9e515,
      4096'hf6f60cfffafafe080be81d0519e906efe315f302f30300fbfbfcdfe42af7fdf514070222fb120107faefe500fa08fd0810f803f329f009f8f80e0005051a1309f3e1edeff610f7fcf7f9fb0be901030b0af9fb14061df8e4e725f8f7dfebfef0f81bf3170203e61dfcd32613ecf10d04ec0cf306fa0624010ffcece700ef0715ceff09d8ffcde6f70008dded170cf8cce8fddbf3bec5e5fce1fff80be1f5f5f2e0f305f7f6f909f5f1f9ed02e1f0ca07f1fff1ee0f00f7f0e7160de402b7eb04e6bcf0dfeffcf9b6c501efede8f6e2ebe2f1f6f6f8f5d3fbe4cc0ed2d0f0def4f703f303f7fdd9e1eeb7e5d4bef30bbc0313bcfa10e20bf4effb10f400f8dcfafe2a053e0217dbe5e8e9fdf43edefaf1edf3f0081331f20c1d180914f600fd0c000404cbf807040804174b35e9f409f4300223ecea11f5081300f502070ce705f3e3d9f9fb07f7162b10050f0414f6cbe0f31e0c14d706eb1f18fdba10ebe80dfce3f21305fcf70ef21bf3fa05edfceffce3f8ebe9e8e4fae5ffebc4f5fb28fc02f4fc0f02ff0607fef5f90af2f3fbf404010b00edec0505ee03fce6f9fa00070ef307e7f90606f5f2f2ee0202f0faf80d01ffffecfe03fbf6fe010404e9f0eafdf805fafef11ff7f6f0e900fdf2f206dffbfbff0a0ef8f402f1fd0d1403ea1703f8f0f7f5fc060009fcf1fee6fe01e6faf90013f9f5f8ffff080d00fffbf809,
      4096'hdbddfde418bf0d00feeceef7ddf2020c280ae5da04f1e8fe180ff7edfc07f30cf505eef9010df418f90705050105e300050a1a12ec02f7070a060af8f6a2f805f5fd110b09fb13dfd504cdf3e415ee12e501010000040a02edd7e9d6eb10d41b05eff6fa0301ffebf3f0d304060d04bcf606120918fc130de7f7f1120505dfedecf30c0cf7faf8030b03ee01daf8f90107fe0b0209e903fcf40afd04ef0601fb05fcfcfb05f6fc06f50314ed0cde21fd0703fafefb04e7030111fb0aff15d0f8fdeefbfcfb05e800d9fe100615faea0afaff02fef8fae70622ef00f81ef1f81204fd04ebfcfd0a0c0be008f90e14fbe703f10bfc0005f902f903100701f7f0ef0409f4f5f7f3f7fd0cf610fa0608070eda0223d5e7d70ff9f5d7e7e7fb0306ddf1e9f03cf7050a11e9dcd7e2dbf8e606f8f4ecfe12fee501e5eef7e506ea27ea01d514def8fee4e9ec0400f2f2f702f2da00ed0ff517e3ddd906f7efd2f8e8e8fd0befea0bfbd406fede1cf0faf00ceafd05f1edfc0d2bfd07f807edfedbfe01ee09f5de08d111fe0ce4fcff0002f9081608d9fadce90b01e40ffc1a13f5f514d4fcf7fef209ee06f12c0e07e9f4100301fcf612f9fe07051a140606f7dbf30df003f10614faf9dafa00f0030dfdde05e5f80207f7e10a0401f9fde7e7f6f00c030b06e40c05f4e0f8dc0002f3f602d8ffefed10f1faecf804ef1313fcfee7f5,
      4096'hc6f6faddf9aa0afdfbfdccf9f305efef09f4ebf2d7e6f700caededcdedfaf1f0dde5ffeaf5ebf2f9e5ece0e100dfdafefe03fdf7f0f1ebf601f8e8fbeceae6f8f9def8eff6e606cbc4f0f1e8f7f6bdd9d7f6feeaf1eccefbe3e5fae6efdbf3ecf4f3ee04f4fbeaf0f9e0edd9dcf202c4f8cfe6f9f2e3e504f3f9f1fbf7f1bef7f514fcf001ff0603f7f9260714e5fd0af4eff30ad3040ef9fbe8fafd19e8ffedf91b081ffeff0df90315def61432ee00ea11ee241afe0700ea01f6f711ed7a19fefce4030910ef01f006fafeeaf816f84503fc08fc25f0f3f2080f15f906f7e5f314021af902deff00f80005e0e8130b041ffaeef9fb21ef0404fae308fafd06ea2807fe16faffed06dddf08160ae9bd0407f3f805feebf525f7cd0cf60dfa121bde08be04e7fb0fc828121bd1f606f5070426ece801f0e6270cebf4ea1902030908e8fc0c1d0ffbeffa2ce8f20a02df1df8043700d6f904072b08d106f202e200f31e35fcf70017ed27c6cff00100cafffdf1fbfaaee315d207fb0c02f00ffb1413f3f009e40302f6fdf702f403fef31409fe0d06e307ffcd080df2fa040b011608f6f205fbf602060eeeed11fc19030a04071a03ff120c17f90c09fde1f22d111a0b0efe0710f3ff15fe0722fce303e90102fb00f52115f7e406201c0319f0f80c080d25030e3603f00d1c1302fbe8fe050e0bff0d03f70b1f100c01140104,
      4096'h01effffefbe40408f30eec06cef8ffe9f4f4eafafbfa110ade0105bbe8fefa0d02f504e1fcedf90b08dcf301fdcdff0209040605e70d09fc05020afbf8ffd9fb01ebf901060c10f2eefeff0b06ead8fef3fb07f302e4fbe8fcdcfe130bfcf408f8f606fe0802eeffead0d7f70805f8bfffe6fa04fbeeec01f9fff50ffde8e0f9f6f604fff70dfbfd030303040a02fcfc06f9f8fdf91205f917fc0e0b0a0c0ffafdedf90a04fc020afc0c1004070015fefd00fefd0904f2fd0b01f6040005f40100f4f3faff05ee080dfc0e0207f6010212120105fdfffff70004f9f204fcff0004060f050cfeff0301020700fa1309f4fd0e07f0000f040bf00804f30305fbff04f3f0fa09af04ff00e7ddf7e0fd08e7ecf5d708f7fbf3f9d4f1fcc0d1f606db18e000e90302fa05f2c9ccf7ebeef101f704f000e401f0fee010ffe6f9fbe9d6f707e3eded09eed6bf06faf4e1f0c719e6f3fc030302d7f0fb01f801060bf7eef606f3f9fb04fbff16c9c6f0faf2fe8f0af5e1eef2d9e5fd0df015faeee4cc02d501f9eaf10adcf704f307ed32eb00ecd604fcd2f4faf5f915f5f7190eecf7ede0e004cc00e6f40fe108cf0ce2dbff080dff16de05f3ebeedff90618f502e3b9f0e8e0f105fbe7ff05edc82dfbf6f0ec01fcfb11ffd9dfec091800c5d8e7d3e7fb04f639eb0018f7e40f0dd7e413e90f0102c60402dd0f0ff8f0f1d8f7061307,
      4096'h1aeb12e4030a0b0eef0d13fff3f2053831e116fe0be9110205102ec7eef61dff071afe1a05f1f6042304ff0f15032bfe0bff182b090c08081cfdf403fcc0ebf02feb350207f9130218f9fbfe1309f204ed0a1802fdea3b1dea9e03161e3afdf402f106051304dee01907e81f2d05f93402eaef17f61a02e92a1616100606f702c6effde0fcaefdfdfff4d2f9cf01fedeebfdebffedf4f0febcfdf3a0e502f7f207f5fac5fbeef500d4cfe7f7eadedefdfa03ebfedafee8fc1a04fdf80ededaf7e9ecf10404f5fad8c2f9f1fb02edd0d9e2effced04e1e3f2f6d4fce6edd4eaf80709f4faf1fce8fff7b2cfea03ddfda4fddaf10303e9df0704f3efeffce2c1f4b9eff0c007a30a07f9f9b1eba4f6fee2f9dec5e9c2c4faf8a1d9e893cbee10e3dfdc01b502e106f1cec7d6eb04b8d5fffffaf408c407ebff07fffafdfeb0c9dfedc9dffa0b070092a4fddedafbe896e9b902f8f5f4f9dafaf1aaf9dbddc6cffcf9fefae2e9f7efff04c5a6c7bbf4ed80ffcfd3f500e5dcf9e6f1f5dd01c480fd2aef0b0e09f1fe0df609ef07eb10fbfdfff5100afd07fe07f200fbea1afc19f3160eff0af90402fef40808fffee108040305f0fb1fffdbfc0314eafbfd0ed3f5e70e140e0302ed0bf0030305f0f4df0613150cf1f6fff60bfdf406fa0af10afd00f80d0018fcf30505f3e41d220c08eefff80902f7f0f8ffe6040bfafbf8dcf2,
      4096'hda0cfae100b4f919fef6f7f7f6110807f90ccbc2bec1ee06cbd9d9d3d3f209d4ead9d417f70a1801dde5a508e705a1f800f8fe0d41f6e9f3daf6050000daedd5fbc1dbe201f9fcc0b9fde8ddefe8d7d0c5fdfc23fb15cce4d6f300d6dbe8dade0306e8ebf7fec4e4109af7d7d5eb0aad0425b2eefd1442043106f0f6f9c8c20303f101f502fb02000a0308fafd0700090e0514f7f9000900eb0c150004fb0ef5fef5fcfc03fafd02f40d13fc08f71e0602010308fe01f7051cf8fe04fb0ee9130a021005f9fcfdf40c080af9230eef0bfe00020801f80615020301fc0ffe060a02fa0e050103040405f40ffb1efbf407030d07090108f50501190002ff01f50218f0e9070416ff01fc030d110803f7fa02ec171adff90ffdf6f5ffff00fc0122ee15ef110501fc07ffffe5154fe017fa0efefaf71d07f8010ff10e11f914ea480120fa1d12190002060b1003e2edff21f2fc06ec0a2b1cfdf0f2feed140ff516000401e21afe19eb0705ef1afcf9faf60dedf3f4f5180afbfe020807fbff040b16f00ff1fee7f6fdf00d0c08d9fd040f1cfdfaf015f417fffc130debfd05fefa150601eefbf702030afc11fc1be40808fb0b07ff0502100111071206f4ebdb02040206090f0911ddfe03ed0203f0de1d02fb02f207f8f816f7f0fd1800150f1b0af80df701fd00f403f5fd133005fc2105f32309f20b04f805fcfd140504ee02
    }),
    .CHANNEL_BETAS(2048'h78cf76db785e7868772777a4782178987948781b77d5777278df76d6777d7817773276c077ac76f277867726794c7815791e77b7782d77da785078fe777677f078eb7726781f77fc784e780477db76e27751780877f077f076b977b1777477bc7743773f78a577bd76fb78d07685780f782777a878bc77ce77cd77f67877774c768b7869775a7845781877b7776c78167845771d783f7865786d77cb77e37741781477dc76e57891778e7740778077c176f4776577cc77367831799d7740784777377776771d7742768b7786780f7899784d77e177e877a4781c776b77ed77fb789e77d87813779777a3778177c57841785e7824788577a7775c7718776377dc),
    .CHANNEL_THRESHOLDS(2048'h020d01f102230202021701fb0208021c0201021202150201020702030201021d020c020d02030203020e01fc02010224020f020002010208020a01f6020502080220020f020c01fb0208020a020002150201020301fb0200020502070209020c020301fb01ee021c020c021d01f802070220021001f2020e021201ed0205021b02020203020401ec0221020f01f60218020302060206020701ed020401f702140205021601e10200021f02080207021901f001fc022201f8020c01c901f601f001f00208020e01fd020d0214020401f1020102020204020f020502140205020c021a01fb021201f6021302040214020701f7021902160212021101f401f501fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d5),
    .ADAPTATION_DURATION(16'h1364)
  ) actor_context1_pointwise (
    .clk,
    .reset,
    .in_valid(e_35_valid),
    .in_ready(e_35_ready),
    .in_payload(e_35_payload),
    .in_completion(e_35_completion),
    .in_bin_tag(e_35_bin_tag),
    .out_valid(n_context1_pointwise_valid),
    .out_ready(n_context1_pointwise_ready),
    .out_payload(n_context1_pointwise_payload),
    .out_completion(n_context1_pointwise_completion),
    .out_bin_tag(n_context1_pointwise_bin_tag),
    .actor_error_o(error_actor_context1_pointwise),
    .initialization_done_o(initialized_actor_context1_pointwise)
  );
  logic error_actor_context2_depthwise;
  logic initialized_actor_context2_depthwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(128),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(2),
    .DILATION_Y(2),
    .PAD_X(2),
    .PAD_Y(2),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'hfbfa0521173034103b3d19083012344c407f0a14062f0bdf2611f3b6c1a0ed1ef821033505f616fbf91600f6fa231ff1212804c6efb022101a02e8f600f0fefff403f0fcfcf3fa1ce3bec8f1e8f8d60511231a16040f1d04fa0719fe1305da0609fd045b21672cf02f26f632f730e7df3ad6c101c9da06ff0811f80224e81efc3733cf07141e1deeec11f0c8e013051b13fa2f0de5ffefef1a150323ffd4fa340523050bf827db1b3d112d1b223fdde52101edf50afe0608ed061f1b1ffced0d05dd09291621f3f6dcf423dff906def0fcf5f9ef0919eefbe21e04daffe4deffea16f806f9e7f40a01fce1e1ea05fd04352c2825391ef802051b0d0e302032fd160b07f405bcb097051a07181d2710e80a1f0d0b0a17e90203f5e8f402060ae94e064d40ec341df70505f9040603fbf8fe02111d15d214e1e10df51f13180c01fcd7e1e0fe06e7e9f501150e0c103016102cfe2218e7241e35f9d4e6ed0bef2c07e9dc0cf73b1610070c1517ff191b1a0e060fedf413eee6f4d12dff4428d718381d2f46fc3df6e210f7da0a3f062f0cf0f606f6f61a1731fcf3ffd6e2c807e31ff7d61505f70a111226e0df0f1ffd29c9dbbd1120120c1f26f0ecdcfdecea0a1a052cf4fb11e7f816dde405ff15d9b9e113f5011a032511f917001d34e8e3f4f4170ef5111ffbdfe9e6f91cf7e01a0f0602ee02fffd08ff10edea05f7f92a0b,
      4096'h1df90eedf416f4e9031c570637030e09ef8ca01407240f181c0b0707ecfef8f409f030093befdde1f109eb4c363d241c322ef22e2b3155181549fece06dff819d5d0e2f5da252b356105ec070af50afbf7f5261923f8f8f8d4e3ef23102921ea201c0f45e0fe06fb01f13e02fa1f0a14400ffd1d04f72ff8fa19fc0838115adcff21fcfe01f6ee1903f2030be6fa0d1722fefa2007f41f2e100c0ffd0009def1190104221822fcdc03f1e4ed01ec1fffe111edf2183b3a020700f91beff90f4406de41019ddbef44123a3c070734fbf8f9edf8e7110bfcfd000a0ef8f20212fff00cf9e00bf7f20bdae00c41135627262ebcdcfe17101ef3070cf2f500020debd3d5f3182217353b3e07edf706e20a1812430fe3203cf824f21d24ebfcffe8daf203030ff505020ffaebf6dce1fceef4171a20050903fcdf0126032e08ec0af7000bf3f80846367037f228a9aab4fff80401ed16240434f8000f140b0f1400131b182b4b040a2d2c2f2f023014dff9ed01d23a082109ec0a04fbd6f508000a39fce2f4c2f80512eef612080f0c0b221502fae4220b0a0a121800ef0ffafbf91d0adf1ffcec1206d02dff2906f720f9f0f5e5e5e30b0d1610041af0252ad92c10c9e6fa28111805e1ef04f8fe14200934181d301d39fd030bfbf30215ec101a1b2015ea0617f60f02f0f706f4000de30907f0090cf3fe0fea1229192e15ef062b,
      1024'h1333180d160efef302fbec211c2531ec124716381bf9f70ef9171af4eb2a0721e3f8d6ceefdc1f052ef7ea28bbeff62f0d065006e4d8aa02f201f9f1fe08f0f6fe15d81212072a081df9e30be2090af505ee26fafa0c16fd2b16192737224b14c912edf40011f1f80ce7e22dfc072428f90de7dae0d4d910f5d7f701030b0adf
    }),
    .CHANNEL_BETAS(2048'h777a776e782f78ff77f5770c791c7834790e77f5793c77f0789c783679e0795f7875779677e078d8782a779977bb7820775877f7793177c278a17983771f77cc79227812784977dc77f5781979187870762577e7789f77ec7850774e78d678c778be77f778db797c76f8784d784d783677fc78087708790078087766780677f5764b77fe78d078a177f27817782878067758782e78bc791f773e782576bf7872780077e2789d787977b2787c77e779047804774c785d769d7752783976a776f277fb78867813775977c278af783b78aa784477f4772d78fd770378147803780c77e6772f771379e9785277fc78ee76ec76ee788677cc781778ae78a877a17825),
    .CHANNEL_THRESHOLDS(2048'h01fc0204020601e7020801f0020d0209020201fe01ff02020203023101f501f901f7020801f7021401f60211020401f801f8020101ef01e901fd01d202000206020502220204020e021801ea01ef01e20217021001ea01f701f20208020201ef01fa020701f8020a021001f10212020701c4020f01db01c101d0020b01fb01f2021001f701fb01de01e101e001b1020b0211021601f801f4020901f401f1020001ed021201fc01e401f10221021401e901f701f801ed020d022201ca020701f501f70206020801f90209020301e201ef020a01e50205020b01fb01f902100201021d01f70215021301f00203020501df0224020e01f30215020201bf02000215),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c0),
    .ADAPTATION_DURATION(16'h14e5)
  ) actor_context2_depthwise (
    .clk,
    .reset,
    .in_valid(e_37_valid),
    .in_ready(e_37_ready),
    .in_payload(e_37_payload),
    .in_completion(e_37_completion),
    .in_bin_tag(e_37_bin_tag),
    .out_valid(n_context2_depthwise_valid),
    .out_ready(n_context2_depthwise_ready),
    .out_payload(n_context2_depthwise_payload),
    .out_completion(n_context2_depthwise_completion),
    .out_bin_tag(n_context2_depthwise_bin_tag),
    .actor_error_o(error_actor_context2_depthwise),
    .initialization_done_o(initialized_actor_context2_depthwise)
  );
  logic error_actor_context2_pointwise;
  logic initialized_actor_context2_pointwise;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(128),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'he2e50224f2e4e302e003bbdaef00cbf5dd0c06ced5030706edfc25fac917df0cdb02fcfaf6e1dfeaf9f1d5def2ffedea0004f6f3da04f807fe00a5caeff9e3eb13edd8a10adfda04fed600e3fcf6d6f1ddfce895e3f2deeb020afb010cabf7f2dee0f5d90efefdd1dcd6d3f3e7f2e2f9f7e4ecc2f8dff7cbfbecdafcf4d2dff80e18123f022ca217fbfee8ddc2181ffbcb4119e91521c8ffebef5019e52a39f7dd1efc1207dff71919e3e5f8f506cddb1cf602eb1cfe0ef6f80921f9672516ad05de2bb319fd0908d0ece1c3d4d9e30e0d0bf10ef03cc0e9e3112126dcfa0f040413ff0ffd0e3ed81702e6cb14fc0cf6f831ff00eff7d9f7fe0a00f0dfd0e8f4d7bff3f512e7dbf7f9dc09e5f0f4d8fae9e2caf7eafcf7fbf605c1dfcae6e3f7f2fbf8f105e6dfeae3f4e5dcf8f2e6f5f80bf4f9e000f3f708f5ccdff5c004ddebf7d4d1fce9b3e4e80705e2f1e2decdf8fc08d3e3fdce06d9ef02e9faabdcf3eae1eee5f8f2ecdde2cce0ffd5faecfaf907eac5f1dffef1f801edf8e6daefe91a04e8fc38f91ff9ef100918f027c3fe04b40304f51402041301f616f2e2f611ea03f2e6fe0218cdd5f538401bef240214f40904e4faecf60adefa14d1e3eae8fa0be3e8eefde30e10e30d43172603f5f40549f9e8ed34e7f80eecdd2c14e7eaf0df09f40f15220dc4dce80c03ffd3020dd7fbe41207f70b101305eadce40d08,
      4096'h0a0409d5181862f9011b23f81e08dafa1b9cfc0e0af70908f908cf07febadc0c0d0f0bebe90009fcf82bea1c25e74531e1fcfa10fd02fdfc3303fbe8dcf4ea690c13f43b17f70502f4dc04213e14face180326f605e35b51eff1c6fc0a0803fbf8ea17f7ff0ed43ed6df0c350bfbd4fe07d2cf1e140b0106fc15ebfadf05e3f70b080c11ebe8edfbec06b9eedafec4281a2005de0839e40d030a4d18fb13f4f9d3f2f50214f8ded519df0aee041ac8dc0e1ccbef0801dd06e416c2fd182e1dc14c06c2da3a3004fa3a02bd1c3021ccee07ffe2e21609dce1e70e400dfdc60ed5e2d500d2e3102ad7e0fcc8c01506df10ff16fbd6fef301df07e5fb08f0feeefbbbabf1af22e0cfedd4faf700f000e2dffcafc109e7fd180a1d0bd8c3e893d408ef032cde151be3f4a71c1613fcc40e07d5f81803a8fce1102001c9cce6a5f2dae4f6d320f2f5f901ebf626330503e513feff1ecaf3e8ce01f9f1e9b607d3afaa0ee6ea08060c18e6dcf3e803c1f7f300feb9f8a106e1ed01110ed7f50104f9e0f5ed05fdf0e614fd010b00e3fdffe4f6f6e4fef80ef902fbf509d6eaeff9f30514fcfbf903f010f606f8eff804dc001dfffef7fadd020b02f8f8f2f2f1da00fae8e7ececdefcf0f0f5f902eb02f8d1e5f8fcf8fff709f004f6f7f9ed04d5f0e3f6f6f503ff08fbe6ebeeef03e909e40705f604fb01ece0f504f70ce7e3f3a0f0,
      4096'hf3e615f8062110e910062ee6f8fa050c20ede8f216c705f713fde1181df333060cf61613fc080aebecf03cfee80dedd7f6fb0408fbffe61ad7071e20d5ffefdfe51526ed030bf0fbf9050eff10e5ededdf081709faedfacd130e0cfdfaed01f3d216f91708f90d1905e1f5fae3ed0d16ff05130e10f9e50dfb00fb0411dfe80dc1c5e1edd3d8d221ff0cbf1805fe1cdffe03b3e3bcd9fb07f2fde49b05030403e70c02fef31f1ff3d116e3c5dd1acdf006e3f7fce30b000af206c9c6dfbfdde9e4e221aaeadef022ed2809efdcee1f33070deabcf3f1c5c025fcf7a6eedac6e7f826e7ff15db0ff032e8fcc9d6fd22ed07060bcc001c01f5f3f1b60f39f40ef0d3f8d7a5ef10f203f3f9ed3e0dfe4aed1ce7bc24dbd512f91900dcb3e4bad518c50df30108fe5015c7faf0031ef80436d4db0704bdef0a1b09f11c03018005fbadfff304f200f02ecc273608380e1632f0e412daf6030bf6170bf4be1539b4c5272cf1eb16ed061c2dda17efb3fe0af9fdef0bdc00edfd3f0d08e60309e9f5d6d3bbedf73006362d280921563f15451019d7c427e99d21081e03d3a6c8ed0b0703eee3f7e41737fcdd32f3292eff144ce2f707ffdb0912180827e8edddc20669c3f8c3eeeeec0dfffb392123191d2d391108fdc6060932355326ddd12211b3e51bc02a3b11f63a490f213c32c710eff302d20a2f0df03d090cf1f32a3059044a,
      4096'hdfd4f404d2debaef0302f2c1d5f9f3f8d73eded2bba7db0908faeeccc0fd10e9ebedecf9fd0212baeae7dbb4f20eeeba281b0701ea0efbedf5f59a05f115daae03020a802df2dcc903f1ecc5d1ccc4d7faf4f08deee6aecce5111be2bfacc3eeb20df0cf03d2e1dedce0d5f3d7d212f2f10cebbfefe5dad3d5f4cafce4e1f3ef0d112ca928292c1ac5fb223336d93a0e18c5d94b08a2f109ff11f1defcbe1bf818d9f7f4dff32212ee1bda283dea0a29c0dded1cf1edf6ebe807662ec3cdd658e749f27f16250737ec2f0bf350f35a2b06fc1020ecf92f31e70dc1bae265f4f14813331a04c5bf6e1305024a0d19f2e0fb0fd92e00f73350f624f0f31d451b3108e910f5f0cfecf4e0f7b33816f31f1b3b290320cefefbfff1e324de100aeb10e515eceae9f7e5151ceee2e548ecfa0cf1ef281a06f606050cf229f111fb3c45e4f8ec22f421280f10120cfefa2c2919e9f3fd1b0cfff006030dfc0fe24604ee1d162e12fcedefe0ef1d170416080114f60e1728040b11f2f0fb0bf31903200c86a5debdea10acfbe1ffb8e1f2f0c500e4aeb3d8adc9fdfb0efdd080cf93cf00aff3edd1fafec9ec9dfed8dee0a2d4c8ceecdf04a30403f40c09c7c6fa80efbb9dfcda9505ede6f4f3f51ed2e0dbf6f8fc06f0e2fafce7edeff9f7a1f89da7a2fccce7ea05e7efdabd99e8c9a106d6fd0ba0f4c1fde2eeefedf8c4ede5e7cbde,
      4096'hf3d806d0111a3701f00f161d30091c132cd2e035ce932c032602c6d6fbe6f316da01f7d4f5273cf7cf2b112e11d02f35cc0b2c09d0f11afdeff544fddbb7e35cda2fc245eff6130cca2f14162c2830213dfe3c2408fe043b3318d4c6264fd8f612d00b1009f0ec34e10b0051df05e70903d40b4514091a0910101aed0d36f4efddfc011ff1efcaec0901e8ebfaf810ecf14110f1170f070dedfb220f16361004eff1ed2311d3e7fd18fb07d6ef2bede415f8f20c060af60cf20eee2328000ac4f8f622d6efffe7dcf5fdf9d0dde1d0fdfa09e500edf8bfb3f510fa10ebf31015e413c6e402f2fae02904fcdefc0d0efa001807f6fe00fefdf6ee08110cf70205010f26350f14ce02fb09dcd0e105cc11fc153abf2e64f9e7fd034b0d0b2730d2da3401ec0627d5afcde00debfccbf7dbf71812cfe3f3bb00e921c01d0741fbe44cd3c5c42847150b460f8302f613c0cf29e8e9f527cbe0c1fbe82404099efdfadfbdf2b3e42c21d6d4f4c8abe8e60b06f8f90ed81ff9d8c1ecda08d1edc8f3dc1502f4dd031d04240efe120206fe482005ffed39ef8b1efe3010e318f4deffef06070b00fc01492013fee809091735ed131709f107fd1cde2b0b461a17ce0317ceed19dffceefd15ecef2fd20bf721eeeff01933ec023808f614e8ecf933e30b0a130e24ff19e02623e5231b0a06ffee0b23f835fbfdf92df11a04030117ef02,
      4096'hf8fece1118f7e6092af8e23715f823e63315cf2c07e612f534fb0dd21128f8f3e520f30de5152109f71915f92b28ff32f2ef0ffcf7f806fe1efd3bedf1cee712f7fff676e5fe030102070deb12fe0404e0f21237e82de814080bdbe6f04bcdf41611e80dfad706fcedb6f7ff0111070bee24f22c17f2d73217f8e3f1130935fb1a21e011f1f9ca05020fdfced7e6c136001419080e3ae6fde7f22b1ffb1b07f9cc0eece91c16f0b10cdceae3101ae9b91308c9e2fff1f4f3e90be1f0212031b457fdcdbb2f18f2d02504defcf109b1c00a05eae2f8fdcbe4f1e23419f1fd12f3ceefe1ead110fcd2dcecedca15fcf204fd22ddeaf1d8dbe4efe81906dcd3f6df16100875e6f1f2d013d9fabac930f1f6f5280304fb7fcc0af5ed6b28241622ec0320ff29f8c123dc6dd520df001fd7bf3f03edff360401fb07f2f709fb6a59d327110eba1bfae9f70cd6eb01cab3ecd80ffbf3f1f901ccabdff23d2ebad40716b549e3d6f7e8fff52029d4f427de08dd0048efebf4e5d6d9f923ebfbdfced70be5abfce608f33f2c0bff135d47e55112130ba96b0ad1030e2410faa203fad90b17e5f71cfa3a3d24145ae403231e2237ddf00a4509022346fb08fbfbc5caee2ad20846c2f01200fee8662e0cfc2a2a4ef51611f4170aea221fd3f0df06f0db01e914211a1f170d381b170a13002124eb00ec152bfa1e63f3fa3ba32722de090a,
      4096'hcf9fe2b0f8f7e7ffd7f1f2eff6e5a80bcbc6cddcbacde3ff11e7df92a2d4bffcdc090df901fca2dbdfe9d6c908a8d7cbed0de801e2feede5ff1ea4ea07b9ecd4d20eaeac13eec6dae407dfccced7c5d40f09dd97eefebef2e3f0269af580b7a7d8d8d6d8ee0605bf9eefd6f1bef1e9f406acd4ceeeddfee1eee1e705d0b4e200e1a1cdcf210a5b1003f321511d102e0a4208c76be1e208070f1d95b0b6ecb8ff17071423cb1e182a072fd5202bfb192ee31a2563fdf7433312152704c6b5122bd800ed09e8eafce401382604db2b5a28150df241f907181604d8c0b9203cd40018030f222e010532ed1d2c1fdffd2fe8fbe30050100c3f02fc42d1122d301df8f118182de0f9e10f240b0ee9ea21111ed72400ee16bdfafe04fee203e027e9fc15f7102fdff0f4ec2f03f6ee0c22f9c213fdef182df80ff5ed22f4c23a4407ee14fe06db16efe9f3fde90bdf03e1e2e6f613dacdf108f6d3021d2b2dc6f304e6ff17f5fcf701e8ed1dd20cf9140b190d0dff20d8ecea04f3ffe51d06f3eeec0ac382e3c9f2efb7f6d4f4caa2f4f3dfe7d193d694d4d4fdfaf7f9dda4bdb4e3f2bffcfce9f800a3dbb7edb2b7dfd0ddede7fcc6e7d4fde5fdf40295d5c4a6eed8e3dfcdc5a2dab8e6d3e2f6ebe9ceb2b5fef308a5f7d5c207e302d89ef480c6bedbbbe7ceefe4f1bdbcc9c8dbaaf2ed01f5ceddc0e9dbf4d002edf5e7f1de80f1,
      4096'h0d15002dfd22d9ff0fffb00be5c3e7ef0e193feb14fef1f3f00326ef1413fb050116e4ea05e711dc11eb06dbd1f5dada05f7c4f2f7ff03ebfe0fccf40735fec828f7f3e3c0dbe0cdc6e8cda510bbcaf4f6f1f9efd9e5f0d6fcf1e510ecde2bfdeae4c5e3ea15f9d8f9e108c837e8f312f900f1ecfde6eafd03e22318dc07aff0b8dff5d0e519d802dbfe0ed51eecd201ebe1f4f9fe00f4fef40acdd6dec8ddefff04fb0810e5e4e7e1efe6d5fdceede4dc0800f2f2f5fd07d8fbd0d6f1ceedced8f8f6dad301d2e7e5eae3eafae3bac20e0702d4f0f7e2f2f6eeeaebf4a9d9d3e5ebf90cfdf5fbdf01e1c70cd8fd050f00edf8db14f40edff9fdf4f3f4e4ecf2e2140f0e0ffc0ceb2a08193802f200f029dafbfb200f11fb0ffddbf9fc271cfc0afe1102ee0bb1dcb3053929e8f40af3eff811c4bffb04051cf302e3f6fdcae3f302021401241dcef4f7181c30f5e90bf8132e0de1e101db0ae8d8000d1702f10cd2fb1010110712ea05fad2cf0fdc1c06a8f8f2060cf10efc0f120406d80efe10d4dbc424f07c181638fc1c1e0117d12ec9aa23db800df22d11c6ea04bffb0812e024f6de393cfbec5f0d1223f2567806fc030cfff110e30908effdd7b7c970f724d249c5171519f72f10294d374609120101d9fe1607302426d2be2827dcd404e20e2818e5201fc61b122efd0ae63901f0172415110f1d151609de191a2120,
      4096'hb2bcf9ee11f2dffaf7e6e0f4e803eef1eed1c505ded815090ff8d1aecdf8f205f5e402f007e3da02c905e7d5f8cef6ddf200eb06c60bff03f407c3d5e7adf703b8f5e6d7e907cf06f9120edefce3f5c803fd07d0ed08d106e3e2f0c3faa1c2c7ecefe5fb00f7fcfecbd2eee8b302e4ff05e1ffc3ebf817fef9fede02e2ece8ee01fbffc4131f58e7ed0e382631f6dcf811c30819f8f222fb2d13d8eafcc3f90a111412d8ed07e503ca1cfb3813cd3c2ee2041d22e7fa08fb0e122b03d8e3df7f0407fd6004f4050b01061a12331c340aee01341d1ae121561d05e4ef192d00eb1cd82725fc2c0424e50c4138e70ae51f0ca7102b11fe060208250eea01100ddcc9df10fce4cd1410040118d9ece335dbe209f20004c1fb03e805d703131003ff20f50c28fdda18fcfcd6e9c8d02cd8e81af0f5fd020df50a9f0bcb1ce9ece5f706f241eef5e3cae3e00602e2fbb1bbe2b7fce4e6e9f6f6b80627f610bed1ee2bc74be90302e5eff9449ddae3f80d34f2031feaebfa2209d3f2f617fd1907cf082a17ec33fefaaaf6e7e49ec2a8219fe50f412fe9d850ae03f3e559270a130dfbdf17cc16f0f6e2e10ce20528fd07daa013fed096eb01fcf00005ce12e52e2d9a1621d7ee30480d1222e8e33dd2f7dbfc16e9e8d41111e6f2f3232e2300f9171c0fb700bce78616b9c505c7c414f7db3ff81d0a09ebf0d408ffe1ee0cc7f6ecf5,
      4096'hd1eaf4e6cbdbfdff02f008eaeafc23e9d019d1f7f2dc130300f8f6eef914f905f7ee0507fff507ec01f1e7c8ca190ce70de803110603fa1cd6e3e0e4fcf3d2f5e20213e7ebeed8eef60cdfc0f0c4d9dde50fefd0e504c3dad7fe03ffeac8e116d73bd6e7fbdde7e212c2d6f8f4001d04060ce4cae5fc11c4fce2ecf42b00f2ffdbe1fbfe18fc06feeefbc2411a0aebed45fdf817c406090600fcf8be19ebf804ca0cf1dbfd000716c41014062cfcf328fef4d102d7060df916234509c3daf0f1c4f4e82dca0b29fd0709171e132c162f02f3f22b120702fc04fbcdbafb47f2d337f92019fdefedf915fe0b0efc20fd0503d41623f80c080c0e04e12d1628d419c8a0dfefebb6befcdbef9eeeeceba1dfefb3cec7aae003ffef05f580cbb9b801abf7e8b6f4ffa6e5aa03bee5e7a1ede3e3f0e6e8a1fbeff2fbf7df06d6addbd4e1f0a7d5cde6deffd2f6ee06e4e7d8e5f9fa02b6f0dbe4070006f4abfeb8bacbd5c0e8c306eaefc3a0e0dcd9e005bbf6ffaef2ebffdbdce708f9d205d201b7fe0d0cfeb327231cf8dad1233833140f1319cf050be4d331041e0df9fbfcc8d40116ff1206f635ba22db181e4514a34d62daf13a0eebfdf70746033a0df3e4b97beb07057ff10e190c2004ff1e3430172118f44a14fd0c434d1bfeeae5211aebfe41c55a250a350341c4163138eb2df94afcdc29281821f92e1a3933f302131a28,
      4096'hdbb6c8ffe6c8def5fd04cedcea09e900d2e1cdceb2c4fe03f7f3eab5a902c105c1f7ff09f4dad3becbefb69fe5eac6d2e9feec24d017fb15d30fa2cdcbd2f1e2e302d7831aedcbe0f1faeac5d4e0bcddecffe780f9e1b8f3e1f82fcced98bddeb5e6d2cc0debe4d1afabb9e3d3f1fed801c1e294f5dee9bc18e7c007ecccf1f0190bf6220b0fd203fa06c2dbc124ad101f1337de0945f50213fd1d3306201dfaf4fef2fb01fceb0aecc73d09eb19eee01bfce5c1f8fcd3d8fbfef6eeed0420f731f5d90bea100cec1fe109203cf2f5ff0bfe07c7fede0105d0081727ece908e4f3eae9e8d6db0ce5d2e1f9ddf4e8cd0dfdec20f8fcd9fee1edfd1700daf4f5ebbc3422ec01eafff7d4f82a2733d002f71dc6e30032d41207f907be2f12cc1d06eefb08dcfc14fad8cdec210a13ec1ff7e4f2e9fbcc0210f7f4001c0ee6f3d301e5fafbf7071e3dea2004fcfa0ffbe73708fc07fff605fcfb05fddbfdfd220d0a0addfaf705000924ecd4060afa25030205f1ff25131910000bfaecf4250314f2ff0e07d31d1e2ce7ec12411527eff3fe359fee0f05dd13f70bfdc0071bf0f7091407071aef07160ef8fb1b2c270e322300fd17f7f8fa030611d5121bf3ecdb4af7f11951090124ecfcdd080a451ff90bd2f0110ff9d0293eff11f8171b22051102fa2316050cdd13f3bf1e280af0edfa07050a3b11171d180307ec01070aff03,
      4096'h191112bc0d5c260adaf621473e170b2432d1082d1fcb0ff41a13060139d70cf6060b06f3fd11fafac81e16432eb9220be8020dfe1bf31816270d4c0012ede154f11b167ef62c0f14062c31282e294a1421fd3e691f2d733f0edbf5fa3629f5f040d4232e0c370022c4f92f34f10ec60702e8075a122f1c3a1bf0ed13f4031004fff00f27170adef0fbe3d9dae801daef032b14e10e2dfd00f2ec2c030b2920f902f9d1270edfc009eef41114efcceed50f14d8c7e307fb11ff17d723e11322bc0c08f7f7041d01e918faf00ee0f5fbdc12f7e3f906ffcce7fc1310f0f0f0fd08fbafede8eaca1ffdbc1103cf02f1d034f7061d10e8e9efe8fbea03fddff908e6e30404e108f321f5dcf524311df6d4f53fd9f30523f5150bfcf904fa2ce73d0604fcfefcf40bbb1ace21492b00d818f8f30320e2c8f5fef618083405f0e4deeaf80c122d12082de205050ef333000703e4f83e1ee7fa0212dcf8ece63719fbf622f6f3fc020a181a0bfc0af0d4060318ffb0f5211c0b031ff10f031414db3411fce018e618152e14f11119190aeb0f0c0cbedf0fe6972cf31dfdc109ffcc0f00fb0c1f19fd020e38f21f041729ff3b39eff90af8e5eb090f35f9e505dbc9ed39e020dc0f150929160d0830331b253c340c1627ecf500fc15e22ae1d405e7d9cf0bf0162df90cf71ef6052053fcfe081a08e30c1a17090920000602031f25fc20,
      4096'hd9f01a2d1801eefa0507f3511dfa0ce742f3e941d4dc1f0319e5f5e41bc9f60cfa11fab9112a0420a3221bf03ad5d7ffd70d07eec7e9fceb040652bd03a905eea50cea0ce03a3de5f10f0f2e2a301735f002024104ff0ee5edd1dfa33754fcd21acbf5310de22137df2428ffcb160e12f3da334311effd39fcf5eff44cf724e3e7ed04d6002720ef0a081b24f7f02fef07e1e2310b860f06e20dddcf08d7ef040ffb100ffde11301032003190516160616e70f1e1b0900ececdc6dde0cb7054eeed5ff05f7fcf004f40f14b62d1823edf5fd1622dbf91b3a000cc9e61f34da32121d08230a0ccd34101cec3e031217ecff19ec24e6fc10e6000216124f6a000ec7d1e8ca04a9f603eef1d7d6f9ef020cd3fbb4e4a2efe502f8e60fe7b5ded4f6e7fd0b14ffe70fecec16dbe8d819dbddebfef70de31212e1ecdeb1d0fbc3d9dff705f18124ecd4eff611efd7f9d4dfe9f3f6d3a2eaebcec3ee1117e3fae8c5e2bc13edb809ffebe8e5c7e2ebede607e705ebd3b7fd1615da0307b5f812e6e9109cabdbbff7c1edfecafd9e05e8ee9ad3fcaaa207a1e1000becf9a1a0f080d9f4c505f3bc001ed1f488f60911ecb1ff0fd2f6e1ef890b13ecf10557eed280e3eaa5f7bbf1a0ef0b04d307fa14d9f00d0ff7faf9f5fee11eea06fabf80fa1b86a0ffac01e5f3eaea9eb7d616bed6f4bef8049ff412f6e6cc17fff5c1fcd3039be2,
      4096'he5d0d3d3efafe1faec0fdbcfd0fff804df17f5bddee7ff05d7fbd6d4d1f1de01dbfefc0d12e5ebded5fdc1c6f2f6bff7f7fe00fad00df507cbf1c9c8ead115d9f3ebfaa7f1e4dbd7e0eff6bfdde0c6d8ea03d9b2f3dcbac7010411dff8abe8d7c4ebced5fdc3ebddedb1dcd2eff909e404f2f7c016eefbcfed01bff30df8f81cd7cde723f8ee2a02ff03ffe503ed1df2f6fde9e7fbe8fc13e2f1f0dc091500000b07d228e9fd0af40d090ecdcb2302dd0ff4f3f1fc05fd09c4e7d9e4a5e2d1e10af017bbdeefc4ede3020ce1cbd3dddae205dcc1eed7ccc108f1d1e70ad0ee11cf2cd9fd03e3f2f529aec0f318f824eb06f700c8fe1713d91609ca0514eafaf2030afe03f3ff10faf8f1f048230424e90f09dc34bce3fa050c00e20011ef800edb13e910ec422b2d0105e1e22ff0482ddbf218f20af50809ec034ce0e2cfc739e6dadd31f108fc0605082ff1382e2311faf5112bf2f7142d0ae1efed136d061b4eee2d3500d5d51adf29064d0cfcfe02f61beb42f12e021bf315f80e382b1ce3bb23f6cdff165405e9ef341f28de520d01dff9fdd3d321f605fea4f22fd811fb2609f006f0f23d00f8effb302715fc10e8eeebe6eff4dde4f5ea4313fed7da39befc1cccf4d4f8fae10d01e6161c2b1ed2fd011dfced4c05f8e9dee8083fe7e9151b142a04e3da1e30db3440e016140d05f4e11a0042f826eb0ce8ec3419f2e7,
      4096'hebdce6e313e45517151cfbfd32e818020dd1c31deeac15f3232ac4d7f802e1fd0604fb1bde231debed07fefa050d022af3041017edf614fd2d060f08c5eaef1eed040c14f5fb0015f21d06101413f6ffe5fa2cf5eff6db150bfa13e60bf2deea0b26f11510dc242c11ecdbfee0021312ffd9ed1c071b14080513eee41316e10af1f6edf134fb0303f0fb2f1f0bef04f21adcea3b1fb9f7f3140ce8fe11f40bfb0bf6220bfb1a38ecce0547010d0504fe0e051409e0fa0507040e06efc8f0dee5f90ee91d0c0f0f0005093117dcebf91af710faf3f4efe0c801ebe0e9010ffeee0b12e52515e91c0911bf16cde20f07fe07e0eaf61af8f705ed12fc0c17e6f9fcdbd2e515fbcee8f001f8cecbe8e8d302d7fae5dceae405f9fd131ff4d4e7ddfedaf600000cfdf0ecfffce1e802f5f0e0f00511eceaf107f80f1ac8f3f6eceaff0ee9dbc0280be6e4ecfaf7ebe80ac3e00df4ffa5f9f2cedee50f25fafbe3c6d7badff3d8edee02e5e706d4ded9f8ea01f712e4d406e0f0d2fb06f5f7e6d5f4161d2708ee0b1a23e6efff1c293303c9e928aa131341fe30fc03f4041ff7b5f2fa2206f1f6e82ac814e2262b511bd2250ff70128d0f6f1ef0c1d0d2412f1efd52602f1fb5df90d181c1d14133534263b1f20f71a5713f438071501c011332a07df32cf16f2f7380e25e2320c19fc0fd71a0bd61b2e0cfc0106150420e601fb171b,
      4096'hf1dc04f5e0173ae604f62dbc0d0e3b17ebecd7fee0c31f040aeddcdff0fd01ff0aff0c35efe55607111afeffc93dfbf72cf7f03e14121618dedee211d006f1f4e4f534c8fbfddce205fbfad7d8f804c610f9d7c3230cf101fce2080ad6e4fd37d258d50b0acb031d2bd1e0f3fdf932f6fb26e402ef09fbf6f3fcc90a2810e40ffe1612faf9fedaf70dfdc5f0b302c9e4011723d20d41d0fa06e9291af6260fe5e1fc010106fcf1e2fb0a07fa1717f0ec040de3e8dd000cedf302ce0a08351beb0e07dde91533f9f533f1de1a1025c1e6f7fcf5d50a11e5dfe405260efacfeff1dff60ac5e6ea1ccddff9c9ede70bd51a08090defe8e0d9dc01f4f1eadfe2eed40f040945e50dbbfdf50400c8ebfc0a00e5171d121219ff0bebf32a153e1d2004f9f1120e03de1e030cea04e7f52de9df360df2000a0e0e1bf005fe13f52346ce12231bd4eeef01f808dd14e2d5c3ecd90304dbfe11f8d7d9feef1923d7e52741da76b9fb01dd17ef2df1d4ea0fef060500260208ef05f0d7f4f9f911f6eaceeff8eeec0911102a181d05241a230300fa06f9da1aecd542f0371002e3f1d3dc14f81018f8eb3ad319eef7d40715b03c7fcdff2a0505f2e10c0a02fd02f0c2d64dd413de3dfaf61bfdd42618f2332f04fb1afc3a04f7324d68e710f4f61909edd822c5300b13fcf728b919024efd31fcfa05f2001c1f33f01501241dfdeb260b13,
      4096'hc7e4e008d2d2bf00cffdc2f4daf0d808e205f1cec6ebe9fee4ebfceac8dec700af0bd8e406e8c9f6f5c8daf3f2d9dcc6e21bf1effafdeef8f3efb9a508e818e50302bada18e2deeff4fbd1c6d8eecde8eaf5f2bde911bef5ee0924ced6aabfdbe9ddeecdfde8cfcbc10bdedeeff9dc01f7d0f4d9ddd4d3d7fbeaf6ffd6defcf8adb3f6abe3f9d3fcdee700edfee7f6d0d5c3d6d6f9f20209f8fbdcbbaea6c9ece5f5010500ddf7ead0e8dfec07c8efeccde7eafbd0e5f7f1ee06d8cbe3d6e5f9defbcad4e402ccddf7fe07ededf9bcce050611b4e1ead4f1d604ecdaf6a1c2c8d0dee9dcfd03e8d7ccceb8ebe304ebf6f7beebe0f9d9f7d300ede000dadcdd120228231fffff9818f611cccfd8c9c7efdb5027d9df39e6fe12d15d3b0716fa05c4f6de001ae3ece71fd3fdfde9f5dc8fd30fa9e42af8f60208ffd7c1473e34bc3605d0db362312e613eef5f3e9fce0f103f3f1f109fae3d0ec212e32e9d922f9d2f206d9d7d8cfa9d71affca1603f80a051b26f3d9d6cdeaede32edacee1f6d4d8f8e5cdf22d220314e70f651a1716172cdbbb3eeec438132418aee710d70d12eb1331d3d6ff2c3db329214df8c8244005ff25f8d7f41007131f411decc0b51ce6efd94ceeee2aeff92c283d0e4e5d30fcf6155b0119372a1dfcddce156ff50540ef253a12fde138b8f952269d22e622f4f3e11f0f2c3f390e1fe6fa22203c11,
      4096'hbcc1d9e5f99b01f609ffe8fbf6f21810effec0e3b7f0060ef90bf0b5e8fa0d0104f8ea0ff8f833e8d4fbc8acc01aebe022f3de04e5071613de0d9be3b9c9e4e2d9062ac5cbcff32bec10ede5b1e40121e4fff4ac05f1e6a400fc03c8fcc2c507f74fe3ecf9c0041434afbcd4e9fc2ec3fbf1feb7104108eaff05aa1b6513fbef0c13311a170037ede3f92f492df6f81f2edbe91cddf71bf41f1bff0813ffe8fa43030509ec3af21ffb24e7f738db1a3ec1042e161ff7fffe1f00fa0cf9fcfa7ff0e9f67ae505152f3d1d4624403d1e420a0807fd110d42740909e9ee300802d428d7560efc26f32fcf04034afe02ebf5fedc2c300e3b3c27f318070b1e2efd0dbecfe9ed19d41914130711633ded252d2fd2b5251d872e001105bff809a4f704000038dee11002229129413d18da0e3bc40627f18c0f094b032926def3c0b816b003047f021df906f6300b11331e2c4200030df2e4cff85bf327e3b81938bfc84eb32c320e353329c6123b11ca3ee94708b912180cff004010102a0c273028350cf0fff3f7f200eb1c09ddd100f3fedeebe9f4e6f30101f2f1f8ecd4e108e304f5090610fdefe5ef12eeeee2d9e9f5eaf000dcffebfef3f7fbf5d7f3eb05080a09f0e2f0bae5dbebdbdd10f8fee8d1d8f9eafedae5eff6fd03f9d4e80284eee0e4fdf5f1f0fffaf306f3f203edefe8eefaf7f1f2eeebfcea01f7f8eddbd3d6e8,
      4096'h2c1a251bfa17b9d811fed4efc4f6d61ee1032ad3fe51dbfcf7d4142924280aeac3f018f91c0e0619fdf41710feefedc303fecadafdfe01f423ede2f5211e11af272cd2bc1331fb16f8e2d70ffcf3f0030beff3ffdeefe2e7fae71e1f15e419d8eddaddcee8f00fbef614f3db0ee6d528ff2f03c6e2e1b0f2fce80de1d3e8d6daceeecce606052f061eeeee2d3b1747f2051dfb09ea02f7092605eacc041fd4f506e80b09fd033828f622c808d2360304f7f70be914083115ef0c06d5ddca1203b2d432ede9f30d3c173f02ddc1042b46eef8f5d50621ecdb1401f2cae0f0d3f62d490d0d0affda3933043eef090e1de7f91228d2e64f2706f217f122451910eeae1e15d1ea0637dce02b2e5f3207f4004df1c43033a1060a0d10c1ccece62bef09100fce1a06fff5c40d383d19f41642ecf9facdc7f7fc05f61639fbe9eab54dddd6f769b21e540f0604283c15344d43fdfd0d22f3f908e137e6d5ed070f00e347c9231506ff083c06f600caf023e8f105a655112d2103df2702e5192f0a48fed5fd05ede6f5150edaf2140315f7fdf8f8fcd3f212cc04020605cbfa0fd421f615f70501feeb16ffe8f40f01defc0cf10bf6f4ded7fd02f8fdfbf61adcd7e40edee705fb02fff7f3ebebf5ea00cef7fbf4f2fb12d7ef09d605feeff3eaf0e503fb11f004f5f0f8f30ed5cdf2c7ff02ed04f7fe18f501ff0002fcf0e914f8eefd,
      4096'hf8fa10c624e305efcd1d01fc10f6f5f9f7cefbf5ffadfef7fa12f00ff290dcf916131df2062816e4f10cfaec0be817392502070a2109f1e922fb0e01f004e32638eff32fe8041bd00ad216ee431ce4e1f1f90eeddc05f8480ef70ced13550cefeef7ffe2e311061cc800d90200e7e0f8f71bf90407eaccf007131916dc35012cddf500bb2c0743fab702192d4df702021db50010f6d219f82613cde3f9d1dcff23090df10125d204e727eb0727cf4f51ceeb3305fbf5f3fc0ff80ee3ece1d36c080ad33509f1f12616131e0c44391d1d000e15e303f32030172005fa4436fedc0ca137fb0319194be00c363ee403d8f901a7001304ff160b021220f8fc1c33102b07f506e0dde506dbf9c6d1d2ecedfaf11b22e60a36f707f4f0181ef8f7fa01d1f80302120004f10be0f8c7f802dbd0f91feae4e7fadae3061bba103a18fdb61d08dfc32efef40b10eac9c5e7f2cbd00cfcf6c603e3c202f814161103ce040fdcfddfede20a04cce7d1e3df00f3e9f20814f8e8e6f5e2e5f80f17ebd4cbfb11d7ceebd1001d17fee8e6072615183721f1e9e341dfad05111ffad4c80bedfd08fdf4ed0103fd303bf616e8e90c10160812ee1518e309340c00fd2d16f0cc0318bfdcf508fffce310ed2000fced083d2d04ffdf48001319040feeedca0504df0a18f901231aecff6100de1724e4ef1902fcfaf53e09152202f0f40a091637f621,
      4096'h1000ee16f1fbe70507f8d8fff006eafbf9f217ece30efef9000503f31a1611fed6fcf3defb02cd14e3f2e8dffaf0eee3fbf9e5f3df0209f80a041004f6f3e4e0eddf0003e1f41afef00405eceef71215eff4fc0f0efce2e6f7f9f3f2f502feee0eecfd0c04f6f0e4e91e11defdf3e804f9010602010bdc0703f2f10ef312ccf794a7d2ebedb3f512edf5f3ebf5f42deecaef8fe0b9b7f813150befb4f6dce70cf6f0faeaf8c511e3d301a1a8e0efcad2ce01f8ebdb0eff08ea1ea1b513c5eec7d6b40597ebd6c20f0620f6d2c5d2ec12ed06e1a9e4fcbbd001f40fceddcca8e5e22feee616f5fbe607d8f0d9dc0c01ec05f4e8b5f72d1aec01fddc0336f5f113112425e00ef060f9b80c1659dc025607cde3d33806800300fa0ca907fad2ba2109ecfd0ae1e83e49e6f5dd1110232d1e33f2303910fb05ceede64bf4e6b8db7fc5031c7fccd5faffa1fff6b5d8204012c0db1c49d359213639eac3f2227fae08531c382427d1e03210c4f4532609ead2fe0ede6a0ffcf93cc716ff003233f50f1620ee1c0314e5ebdcf8e9f5ee0caadc102206e2fd7fdffd0d061e0c1816fdfdeb17f9f8eb17efd2f1e401fe05eadaf5fa11f0d8ddf7e7fef9fcea24fe2b1ed9f902c0f53317f00410f3e71ef2fbdcf11601f3eef8d7f920ecdb2614fad7f9f0f8e8fdbbeec21fc8e002e6d4ecfdd6ff04fefb0507d5e7ee12e1fc12d2b911b5,
      4096'hf5f0f0ee2e0525100afd1df21903e9f52ec7ea0611cb0bf60306df020de9090335f8fdf7f6fc0b05f2120d2f1cfd133007101b1bf5fa0907e2f5130febf8ef68fc04eb48edf01a04eb091d1f1213f9f80d0c242dfdf02e111edcedf50605fce6020f181301ebfb1cf1ea141cf607d8e604ea0c121efb1ef116fb0512e928df1fe103f3d3fc3afe0400ee251100221925fa11e7200abf3cff18fcd4f007e110f9dfe6141b00f814edf4f9400de305d1ec0cfd1bd7ec030dffecdb4ae7ecd8f4dfb9e10915020ce0e71aef17e4edc9f5ede605fa32e00aedd2ebc5fcf1d21bfbeafb23043f1ded014425bcf6becb0af41bf315ff42e5f20027e8f9d61b13000edff8fbf4e212fe1df117f424ee20d9fc072f92000ee4ce0cfb1a0ccdfc03efe3080f060a08ece8051d040fe41e17eb1d3fdce923fcf6fb0dfff30ffc18d5f5e874030ddd34fe07fcfa11e006111b10d3e1e90227e006ee2f34f6fdddf61cf5e50fca001d200c16d726f5e1002307fbe8fbfd01e32212081fe9f105e8f3f1fee3def2c0f8f0ec0b32d707f30cf00ae7fce7dac2d1f9138ff6f3e6feabf01da60e00fcf5fe00f3030519f905fe21def91c0f2009e0fbf9f706d9e6110b1cf9cae91de8fd1007d5eecbede3010e141ae625f415e7f121f4e1241c14f3efd8f0c50116ffec27e3ebfed90027091326f30ef7da06f3eb43fdde02feedece6f6ec1b80f5,
      4096'hecbd38add8f407eef1f1db21f40309f47dc3c22105a012fafaf9b7cad7ceee1df4f9f3eefedbe8f5ac2b1ff00ede121cacd91808b3fbf4e818fe350a1294d0efb545c057e013f4dcd9e527010d0a330012034144f9e21921f5e3d8d2304dd6e20baa0f3ef5d51125f4de20dbd10c061d08a2fe641fcdd91c09dd0b0b1be723cd14f8f23bf90ac718f81bb2b6d6f5fbf5e83f11c30a0bf1120205610ff843ec01de10f0120cfeeb122ee7b2cacb3718df0006f0f817e0dae30cffe3fc6a3c10d542081dc719fef5f518ffa9f2070aefd91cfb07f0fc22ced2f72c373efbe30419e9140fdbd2eadeb80d0af7f129f603f7012afaf7d9e9fff0e01600dceff4ef11a6abe7e2dfc6e60904f8ebfde7ffe5eddbebadd1c2bce3090000f2b5c1e6ce02e6f104f5fbf8faefbe14aeade6e1ebe2f3f4eaffd315f70ae507b3d0dcc6f1cad9e801beedf1ced1f50af4e6c6e8e9f2e701e68aeae4dbd9f4f50ac3e8b9bddfe1f3d6e502bdfadaf7d1d0e1d809fdfcf8dafea3eef4f5f1ff07ba0e050501f52b1a244120fbbbe5050680bbe500f82ef8274da2fe42031af0042dfd2d3818f598120d0d1107bff92bcbd4dd01f3dabfe40bd5d623ffe8ef07fba21b595123de530bd7b41636e3d729f9e2f3f1d4b7e00df8cbd215f0dcfdf70c172affb0410ed8e5e4b4e41924bad50df1ba29f40315112116f7d1bfcbf90ae61ee4dddde9cf,
      4096'hf9f6f80403cf00f2df050f16f60afd1128ccff0718e7f9f30b01e2e9f6ef1202f4070cea0806e5d8adf42ef003d5e5f4def712fcc6f4d2f51803e2e7e5ebccdc061808120100f20ef10c12f81305041aeefe13edece7e8edfd08e3fb26e4f5da07f2f2f4f703ef1bf0e8fdcee2f413fe04c2eef1150af7fffef4080108fc0bf5dca4e2d3ffabb1dce001dacad6f5b6fd99eebdb0b8e618fd0bf5ffd9c0cbc8f7d7eceedd0bd6bbe6c6f4d5ebdddaecebcfe81bdcef0108d905dca4e600fe0ce3ecbfd0ce3ce1f7e722eaede0e6bbd0c21cffef80e908d014ec0c28bbdfad8cc9cce40dc2eddce9c794d2a5f5c803dfd50cc4e4bbc3ed08f106f2f709dd12db052e1f18130ef30b0ddffdccd8ce0a8ee4f10930c92e1e2008f0f13342190a36e9f0f5f9e50d08e8d927eb1f25c3f1e3c8161bccc815ffd1e7fbecce16175626dd3f12d2bb660fe0f3e007fafc19d6e8d922fee9bcfdee0fcc0f0a350b22de0e11ded704d9ed230bc6eedf14e622ff02fef412f9e5f8dfdb090bfa17f1e1c4f0d9f31100d30efe1cf6d50411ed0ee004fd1cbae30a17c90408e606d710fec110f8fb0f08f0fcfe11f6ea1811011102e3cafc0700faeefa11f426ef2b030ddef40303100e20080b0704e7ef04f611e40becf90a0907001f11e0f5e3f4ee0633fb060105eb09f809040c06fd05f3fb00e5da03f4e60c19fae903eeece3f9fbfc03f5,
      4096'h3ae407d517402b03fc1c58562a1303f931e4df23fde7220a040dc8cb20b9ff05270ae9f6e9191037ea081b542ffb2e2dd7f108fd1eedf4f8edd87f271cd30759dff5e37f02fd1425e3191a4f231d521e15e72f4111fc5f4a0d0dcbf4ef5b0d114be7335ff81adb5fdfdc3f140622e1f6e8dfef5828180f5c0a202a260d4d311be9f1ff0ec6fa07ff00f3efd4d00a331adc20f00f08da0408f7fd1dde1010210111f10103f9e510f50bfb27f7f528d1d53008f10cfb0d07f3daee0a213a17039400e41dd432e7dcf3cbea01c3e9cdd7f6e203ed05f108c2a6f2fe3411e5e4fb28cc41e1eb0502dfec1402f3ebf6f311db0800f1eff7f800e5f2e01dfe0cdfffea050917f20e193ff3f9033a2a51fcd00c22a0f4382effdaf213fcac1b33bffa0c3e1316dbf108f9170a1e25352cd61c38edfb28fb0afedd103efa4819df0dd65c12ed1a61eb0a2b250011343f35230d0d040c2c210701572ee7e7ed1c0c2d160006dd2f1e06250f34f21a163d051db81a0400023b19e3f70c08fbf101def8fafb030aee170906c6e1d0f9e4e2b4f7ded9fe182bd9d84fe5fad7f025fef82e1907adfce9f9ffe3cffaf2e51a34e8f8f6ca0efff1c1eb01f70bf0ecd324e8151ce6f809ecd205030b0108e4e628eaeefff6e9f4e9ecec0bf4ff1fe3301614c3140cfbd1cdc1f4c30cc3d4fde9ceed09df32010aebe9edd2dcecfcead400d9c70ee5,
      4096'h25eff3d2190d0ff619f20838511203090fcbce26b1b718f92d25edf925e9e012e11928e9f105fe32ee33c50e1ec34944b9f0201ff7fcf6f1281e16eed7d6ea6fdc0bd007e60d080b072438ff2d1d48ff19ff18050d1c295055e1efe82a2feb0338c739331af2ec28bb01072ffa1ffdf9fbf4022c0f141119051bec1cfd2505ebb7f7f3b929331ff8f901eb450adb53ee0bdac04903822af41a1abedf07b0f610f818feebf92944f3e70ffb130bf40f38e6fbf208c0eb24100c1325c7f59aa718aaf5ec28fdfbf921d6270ded1628560824f2073e09080f163116dfe416febefe29f0381f16f81561211f5b3cd80a1226fadef530080d3534fb052ff6161217f4e20936f817fe11fdcffb292a3bfcdb1116e6f02222b229f1fbfcf41d1e121ef010fd11d80af4ecf0ace3402f0bc90bfb04031cf1d1f5120902fc0ceff3f894090af00715020c25f91f1f28230ef1060b10180cdddf10f2db0900f3ec1924eee1e7faf338040aff0feff211ddd61aea1300b5e7cc040c0a0e0c1615f82902f701f2bfe9e708c2a8faeddedadadae5cd26cddef4e0be01e5fc0904ffd1c0b2a2e6cdef1c0110e4f6ebf8c8cbc504cfbbd7d90be2f9d405f505dbfa82f418d7f5a504f2f286350dc1e122f9dfcaf8fab0db140cdd9fdfedb2dde8032acedf8dc2accee302e0f517cdd9c0ecb2e3bcfdf2f7f8f1d4f6eef3eccbeae7f0e4e599dcfd,
      4096'h1501e727e4dfc0e8eaf1bee2d61cbdbef0142ce7f831f0f5e8f426fb21201606f002e1ff1af5b7edf2fcf811eedfeaf00301edd8df03d7f50811f63bc70f1ac6fff3c510de0fff091ffdf516cce102ea0af2f11512d7dfef07eff5fcfbe01314fadd08e6fccf20c2d409f8d501facc26f9fb0b0ef2fbebf2fff0e609c4d50304d2c4c416cdbbaf090c0ea7d8c710e502dc13fab7d7f5e311e0130bae9ef2e103bc00dbfe22bfe6f7e9eed0c5edfdbaccef11e7f5c00a060fd003b2eafbdefdc1eddfdb82edeec9e6cdfef59cd3e5d5d1f9f0c4b0e8f5a5da0a0e07eceaa8f9efb8e8d8c208bbeec3eeb9cab5e5f315ee06d6e4a708e406acefe0d5f900ea01f40617fc060508eafaf10ce4f90c1309edfa1613dbfa4ff800fb0618010df6fafdfb02f914fdeeeb01fd040714f9fd0fede205e0ebfdfaccf80bf017f1de0f0ef80e140614e6effa110be3fd0f03dfece0edf5f91ddfdf0dfbf60fe70bf0ed0eeef9f60012f10101f9fef8f4dbf8faf718fb0103e8f3efeb130af7fafd05fedc08f7d40df9f3e4e904f4faf0e2fa07c6fceeeaf3f80103ff07ed08fee2e7ebee05eefbf9ed01fbe803ecf0f1e6facbf8df03f1e5fff104f5f3fcf2dcedfaf9fb00d2fcead7e205dcfdf6f002f5fef7f0d9fffd04db0800ecf2fef2eafd03dbf4e2ddfe0704fa00eee9dbf1e8f9f3fae900fae405d4fceaebf3fafb02fce3efdaf8,
      4096'hfef1eaf7180821e92bfa04eb210e02ec1bd404350406fff2f802c4ee07d223163503f7e8ffda061d041e0b1e27011a0607fc010df7fa110c12f4fd1cd50fe94f0d1f041ed80ddcfef207190e0f18e1efefe007311307221e2bf3e60a09f70c11f5e71e0809e61a10faffe6280e09f1fbfff5fe1d21da0ae6edf8dde4ef0deaedd60bfb0707001b0307021d3027f60d333cece50b08be2df41a0ac5001ce023fb0bf503e310240ec8c21b4bf8f8db0d25c7f622e8d1fcf6f333f003f605d4be07d410161102063e0de20c350d19100d3c1b0f1de4e003073dfbea00ce2910dfc620c4ff1c0a042247d40211fec729fc1f05b00107f81433331bfb28fc10f6f4f8b390ddc7f2c5c600e3f8caf8e109b7fce4e2b3ccb3c9fb11e803dd8fcdb9d006c0ffe4d00ce8b6eeae07cbd0e3c5cfd5f8f806f9c506f3fce5ffacb5e890fbdfcce3c49b01e5e2fbec02ffdcd6e1f3ebff04f2a6eaf0ddd31de8138af2b2cdb1e4d1e0e904dcece9c3cdd3e1b9f9e8f0f6a5edacfde000f801f3c704f7f5ede800ead1d1110619faee04181e00f7ea112bbccb1804ac0ff9dc12e3f3e3cb0c0f17f602e807dd02fdf1fd0b1d06e70d26f2ff0dfcfaf4e9fb2b00110905f603171e19f21df516ff0cdef8172325fc0af1f0fa0720f503250afc17f7df09ee0e0dd1e703ecf9e7d5051600f71c0f0ae9f7f1dddf1d25f804f50f190ef6cc280907,
      4096'hd5bdecf9e5dbdcfbe800bfcaf5f6b9d9f0aee4b7d3e7fffceb06e893dbddf408d4f2ebd9f602bee9d909d1d5fabcf1e2fa00cdf1b804d8f8fe09beedcfcfecdcc2f6e4d0b5dfd608d2f6eaf5e9dae2eef2e8f3befae7dafbfffbd8b7f982cfcae3c2e8f9edf6f3c7c1d7e7fec907e0f00ac1f4e0f3f0e3def5f7e9f2d7e980f1d48de1c804d1bd0ad7fb9ed1d7f19806d5b9b8c0abbb0003f003e9bdbab6c4fd8ffdeaba02dfa0dabaf4cfdce49bebcadc03dbe3aafffedbfedf95e6e5c6eaf4cffdaab32df6dfecf1f1d4ffdce5cfcdf3f3038af1dee5ffe0fc25acfa8db6ceccb8eda5e8e8fce380b6bedbbef7baedf2c2edd2e7d2d9ce08eedcecd7f9d1e610051418082af600fc09faca05fbe8dee90726001659e4fd12f66bd6142419f71afa09f30df4dfeef9d4120cd418efce3b05e5de0401e3f005eff719c01413df21f5f1eed0fe0ae9f7da05100ce9ed08e703fcfceaea14efc7f5e5090cfd1b0901dbf9f7f8fa08e8060809de020ce7f306f503f50800de04f702f9f2d5e7d10100ecf5f1150c2707f1e51533180b1c090001cc45e0b10ffcf70706ff09c3ea11fd020814e52c1107fa1af61a1a144c1dcbd714331df9e6e424de441e319af13eda31d17f0ee60524fc1e27f320415935f909483503f30b3f2c09c9f4f57fe7eb38f4243006ecf3311406162af70f00fcfd10ff4914feef1df314fc24170724e4,
      4096'hf8ddf9ee1bdd7f110f124b0b20defa2626dce3230fcc35fa2420e4cef8e8fe0b3b0013f8d90f5d07f811130bfa1b3239e6100a0ceff4171027f500f4bbea074efefee330fb08fa0b091a2c360e0e16fb1f001606dbef2615edecc3da1b1efae6ec10331d00f8e2360bfa1139ef16f2f507dce02f1fe11e031f06f1e4241ef7050e24f6c40d1d22f3eafd143324fa00ec10c10d0eff0818f50f12f40110e2e9060e0104e5fd00c306ea03103f1ace0023f40512f4faf8ee08f7041af5fd00e52c08fffd43010430130827134530180526f6041e250a16202afe0cf104110afbdf34f01b1efb01130ed5ea0424f3fdec1401d71e1c041913160408090603160d14ccecf8d6f706e107e9eed209f2fd06e1fcdfdce7d7dbe9fb10f3dbe006c70a03e8f7f8def019ed06b000f7e7e4e9f4e4110210f2ce0302f3f4fc16ebf8b6f9e59deef0e7f5f8fd0bf00515fbedfd16180401fc1b00f2f4dc11fa00c4f9e3c5e017fc030c04f20be812cd08eecaffedf500d516dc0102f9160701ce0e08fef8f42a16fcf30ff3d5fbc905dbefda19dcdb151a27ddfe61ebf8eaf621150fe41302dd0aeff604f5d1f610ea0e2af6faf9c3fdf5d7ce06f5fffc05151505fc1924ea091af4f8ee0a09f8f8ebf930defced000dfef60408ec09ee1a02fb14ffd91904f7f6f5cdf4e30bcbf3cfddcd0610dd0e011d12fffaf0f3f8faeaf30de6d9efde,
      4096'he3e5eaa9131becfbcf0af8ef0fe4fad3e6f5bbf8e40d1bf6f8f4e7cb02aaca12ea0909e30cec22e2c526e603ffe9ead4bfddf6dac7e7f50fec01fdecbfc4ebfdd90fdd19da0dee090af30e1af30802ebf90223010403f2f10be1ddd4f83dcbb6eef9f5e5fcd108010e1ee3f9dae60e10fde8ef00030ef90220e0d4d615ddf10d05ec05dffa084d031c03ff0810fafffaf0baf703dfad15fbe3fdf4ff0fc6f7071bef1205ec1c2efa0c1af9f618f41d0118060c120802fc1410fe0103ebf1e861e419e9140f12daffee1200ef14e4d7d7070af1e4f3ea200d1a05f6ff05d9ef10d81022e3f508df2bf6d40d3307f300e4fce9e10c192805f8fc1bfefa1a32102a8f90e2e0f4f3c10eefe6e8ed0106aff2e4acc8f6aad0f20306eaceaba8a8bff4d4f1efc0ff04b7eebaf8badff987d5cfef1ceffbad0c14f5fbfbbddd0489f9f183f29bb1f1eec3f0f509fad4dfdbb7ca210a0acaf803d4fdd1d20e9eee808faed7b3e7d8f3f3e3c7a3c4b8f09809be0d06bcf5baedd0f8e0f408d401dfc8ddf3e9d5f0c4272446d8040825463f180d0221d4ee1ef1aa2bfa1909ad0916cff008252c14f1e31f18fcd834244b09e3260bc6fb3229f5eafcfa2c021e0ef1d8d93fddede34cd20b0439e21a3725183749321006fd1e15fa3a400a16eac10d23e4c61fc62b25fe05093fe8330d50e4fd07f406ca232c1c00041113f9f0041e0f0608,
      4096'h1dd8f300d5f4492a030f03b80c001518c601e3ea26b52a01ca01d3e9e7fc0b04ef21f13a14de3ef5331bede8f142eaf02bfcfb30180d0236cafee90a17faecf8f4f740d9f3fdd1f9f000fccee5f107da1409dfe10c1004c529ff0006d4cced46d649d90903ecf6094fc9f50e1dfa60e2031d08fd06420bcb060cfd023a01dff70b24fa0b182a2efa06fd2b470ef734ea3dd7f95058082afa0a0f221e18f8311202f918e9f015ff21de26484539ff1126030108e8e80211fd24fc671d08f3123afc11077f29152d1510002f3d3e3c2f45ff06466a02037ffef30cdd05177f04064cf6291cfa232a33082524ef041bf000ff0c17422c1cfc5409063eec253622151108e6cff8244b0b1eee1b371ff011ea17d5e16829bb1bfdee03d8080df2dd0213ff0e1b0ae4ff15db0bf11f08143251e9e00f0b09f0f4003c0c3b38d3b5c839e20c047ff8220201eb122bf81a192ff4f2e2207011fb5e20ff18c207e96d05ef05e9da350afbee45c5fff21813ffebf60a06125413e5d63cdb0df2f8ef2e0827161afbd4123533ebde16382c4af3dffc2fa4df3d26d831f9110aef1e31dae30128130af9e92910340309323423ef492fdce529fe0af10a102e0e5311ebf7f44a030eff7fed26330c080608254b251016f3f82a2c181c553b120ee0061b5b210313f81d31fb2d0618ef0510370a14d304ff04f126191117291a2e170ef00a110b
    }),
    .CHANNEL_BETAS(2048'h78ea7980789a780177ec78e177da78e078be7785777a76fe78b578db776e789d77ad78e878a67687779c7908787677d37969790f78e87a58790d783c7719794e7906771b78ac7959796e780578837756799578e577b5785a765779f177e977f176bc771678407819787d7826775e77c6784f77e978d9777677e57916781d76b97908781b7928785378ad77a278cd7954798976fe780f77c1789c780b78ca76b878e9788278c4784d77b4771977ee7926785f785c788778cc782178c1789e77db77e5798178537962773c76f2784b78da77c17925789d77ee783b7766780e7904797379dd79da77d977e177ef779579bb786478a978e47840781078a377a877ab),
    .CHANNEL_THRESHOLDS(2048'h020501f7021101f6020201f30210021c020c021001f8020d01f201ea01f1021c01ff01fd01f201ff01f901ee01f5020f021401f501fd021201f40211020901f5021b0209020501f0020302050208020201ff01fe01fb01fe020c01fa0204020601e201ee01ec021001fc021001e601fd020a01fc01f40204020c01e601fa021901fa01fe01f701ef020b020901f1020d0204020b01f8020a01f001ff01f60208020a020801c30203021601fc01ff021001e601f6020d01f4020201fa01f001f501fb01f8020701fe020001fc01fe01fe01f901fc020802140202020e021d01f302170203020501e5020202020212020d01ee020302070203020201ee01e401f8),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00cc),
    .ADAPTATION_DURATION(16'h1400)
  ) actor_context2_pointwise (
    .clk,
    .reset,
    .in_valid(e_39_valid),
    .in_ready(e_39_ready),
    .in_payload(e_39_payload),
    .in_completion(e_39_completion),
    .in_bin_tag(e_39_bin_tag),
    .out_valid(n_context2_pointwise_valid),
    .out_ready(n_context2_pointwise_ready),
    .out_payload(n_context2_pointwise_payload),
    .out_completion(n_context2_pointwise_completion),
    .out_bin_tag(n_context2_pointwise_bin_tag),
    .actor_error_o(error_actor_context2_pointwise),
    .initialization_done_o(initialized_actor_context2_pointwise)
  );
  logic error_actor_project3;
  logic initialized_actor_project3;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(64),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(1),
    .OUTPUT_HEIGHT(1),
    .KERNEL_WEIGHTS({
      4096'h92ade0b6cd9ff3facee3cdd3cab586f9c8acbdd7b39da6cec9acd2c9a7e1e1c1f6d6bcd7c6f6e3cacbb3f5a7d7d1d2eab9c4c403b3dcc1beddd297b4c2b49cf4b5bcabafead2b0ecc6e3c7fea1c68ee6fce9aad8e8ddd6e2b898f8aee8bbbaaba2b5b4c2d7eec8bcafacaefac8e4ddbe03d3bda3c5c0f9c9a5d2d5afbab480b2a6aaebc5c6a9e2f9d8eef006a3c8c3fb02b6b7dac69da105d2ebb9c6c8caece704ebdeb4d811ebe6bb9decb4fdb5e507d7e1cb09bde9d6d9f4e39bd2eda9b0fcb0c0b8e6e1f9e1bbb0faecdea3e1a70803fdd2b5e404bd01e8a3ef93f8a899c8d1b8d3c0f0fdedb5e1c2abf4c10306c003dab5cdc5cd00d3ccebcdecd8cab4d9c7b10fcadcacf40af6f0dfe6a3a19ef6c1c3b8d7bea1b1e0c4caace4c4f0e5b902d2eebae7e1ded2cbaff6c7edb1c8e5c0c5d805c3edbce9e6e5b0e1ddb7c2eeabe0aec0e3fbb9dcbbeacedf96d6ace7eceaa2bcfadfe201d49ee3aaf0beb0c5cabbdbc2c5dfedc0d1bfc6f3d9e9e8c300d1dfb9d6dd07c4aceae0e5ccaba0cd0106020cff17fe3dd9f000f211bd03e703f1589d02280ce217c7e1effd1b01a83e17bd2bd740d516da4112f0fb2404c40284f7f8e7d0f9dfe0020511b604f027f5ed03c6ed24eb060c0bed09fb0f07ebf4f5a71cf5ee0af1be1ef0f61af308fadfd2fb10ea050df93aea1d12fe22e0ef00df1acdf5e51030d413020097cfd904,
      4096'h2e21e8f2fe350913d0ece2c757ef1a0dcff969dbfd0144f04ae942f51a04e2c509d6f42b1c9e0ff83406aad4e81ee7ade0d0181623ddeed5e9c15ef4f01e1ab5321f23e1e6dde412e6e4eef519d127c21f11c919dba1f7d6ec37012fe04c46faee12ee22d2e9a9270d2dfd1008baf50cf8270bdbecf70d2af4cf53dff2ddf9d20500bdc50be1cf8c8030ef6704727eef21edc9e4e7e3eb0edd57e6ebf0b38026d53ff928d2fc4336238083294128dd391b42212f4c127f4caa8031f91dbdd2fe1ee71450141606faf775a8b41b10d05421177faef2a1f424054733e18009e0b379f824d97ff480871f19de05e4c531cf0625bd69eef1fbcc0820f811042a301697f0051035cd640758f4e10e8006806e3080c31ff0fdaef8dee202b2dc0d7f31ea68d5800560803f8024530a1d80646736fdf0bd80e8bb352369d82bbae4b0390ad1901e3b027f3dff0c15621a1daa24f718fdf40122e6f0d380dcc771d6d93406bfdfb8bcfd7ff480e2b5e2e97f02e1f180a7b77f0f169b3cccf00b8e1a0817e9eff2d4c40a1e0e0136f8f02ce50b21c723edfae2da17381a0dedd6ebece1c6efc22ffd5ef6298025dccae4bf07d4f1d10ff1431b5fb3131cf4f38050da2399f3f6e1c32cc2d3fbcd04e904a3c6f1fcf946efeaac16dee2c6e931d5dde3e8fab82780e6ecd2d1023e06c3f2bdd042f1061cd5af04bc2bdff11714e951d506d4,
      4096'hbb92a96250a97f80f75d7f7f027fa17f0ef2805b2d80807fa67fbbf980aa807fd7037f80592f73695fc4a9377a80b47fb87f667f3f7f0a1a7fbb27b37ff2237f1043807f7f763732d208c1b570ead617f4327f0deb497f3e090145d1237614207f0fb9d57f6ccbd285074a28e280f774f206806e7fe17f807f7f013a7f3c7f5be2d408d0efc6f4f4f305efe4c7cae1eff1e2d6ecd7ddd0f0d4c3def3daf5f4cbf4ede7e8e9f8ece5d4def8d6e1ddecf6e1f4da01cbf7e1e3edf1aff6ead6d502e4dce5bbfaecbbebd2f8f202cadccfede9edb7e2f9dedbedd3e0ffd7e9c4ddd9d0e5ded5e5f5eed6f8d8db00d302eacffcdfe8dff1d505e3dae9f2e7e2b5afeef4d0ea154cda51f90ad9dd12fd2d88087f80ef5be0dfcee2cae12306d6410e6c027fd580bf97a775b3100d205f80e928735d0005d9c818044c1c31d8f1fea165ea05ba0fd17448c1d810fd1bf87fcac2a6b9faef6bf90a07f6d2fbcb4123d72e2e9a3afc4d0c4cd58003ea105b6999e2eedfe3fe7f090ae3633ce740cf380240170adaa6800adcf2dbbef8b340bb54f0a341f4b2f51a1fdb01cdfdddfdafadb70da82b7f25f160b245e9c880d27fdab2c000f71728dec1fcc6c327921cff2ed513d61cb8e59aa1dee5cd1c07fd8016fd04e3def5abda800bbf571c0fe215fbd6094e800c8fe0ae067f10c4250aaf3604115fc20e80ebecd5a5ceece329ecdf8f,
      4096'hf0cdc3fd23bffb12940bf827e0265f0230fdc307deb1802fa2f00ec7f9b6d143f2228d34ce7f6f6807a924ff0841ef223b3bf7342f00597f0c87caf587ae807fecc7c421297ff7e721480cf9204bcfcb2a105eab0f80ff12ed5dccd9c31db3d27f8005c87fccbb874cd30c411edf2ee6f4270b5e164f5ad9f74abc21a9ca261ce6e4f4dcebc5f5fdfbf4d8d6c9c3cff0d8e9ddf3ddd0dbe5c3bbc5f0d7eeead8eaf8e7dbeef8e7e7d7d9f4e1f3eee9f3e7e7c7f2ddf2d7fbf9f4badff3d8e2ded0e5dfb3f5f1e1efd8e7e3fadddde0e7fbe9ecc7f3e7e7f1dbc800d6deaed2ebdde4f5eee2e8f4d4f7dcecf0daf8ebd108eee7d6dde5faeadafceeddedd7c6d7fa4cf7563227af10289dff802fefc7ad80052782fe7f1e900f8004c24e3143980c49c47bcda5a624fe620c242445168005d7e3c6039baad0800a324c914813ca0b1b7feca604e82c52c2c1eced443280d5a6f434f6f11a12c057cb7f0c4238d798e4275e80f403107f073e2e52d7c80ddb13618fe93bab56e0fde2cdc346143a07de1f0628ea1f1300111430e905f30a2f02d11019d1e70cf318e6ffc5fb322e15290ee5e725032a0ae41df419d5321d13211504f405e63b2408e72819f0e21efbffda09161c1807e3231716ff1fe81eff0404df1c48f10d19cd01d827e6eb2ffde706000b2c1201e8f2fcddff18060c05db04021e1815082128f9340505fbfb,
      4096'h22395ddec13d88ba36d6d099fcb0dfced31d6080f26243af3680302a73275da6043bd478b98580f3237701a6be627fe6228003caf08080ee80520db0803eff80d6f57f1c9fe4f97f7fba1e57c53e2fc7e401bd5280cbb3e35b4a127f79e353f1b62c807f84ad1a49451736c80c6bf8fa0d0e47cce81e807f9780faad8d12ef80295ef9f1b42cb82e80cdf2f340af470280434dcec3185bdf2ec608bbd7bc178a26a7ef7f0ae17fc07f0bc0c6807f17b8d9e327105fe59998d7872f800e374399351425c4d88080133ce3b78010803fa7e418c6378ae412e9b852db5d803f43bbc42a804e80e580277f39221edade360a0762fd1980e02014bdc9f99025a239ec3dfe97e380dde61acce8ccd312e53bf1c9340ae1baea05e0e4d2f8c3f5a8e8c7e292253b101b2aad13f29080c52fd1ac3debfb0d3415da00d1cdfcf300c31e80fc06d7b508aabdf1f2fbcfd6ff9bf61d200e01d8a4178cc2d823fefd03c0edc4142480f5b7ccdbcf14281cb9edc12014010af2f08bc8da16a1d7ede725cf0bbf1ddce6bbead31701d131f13d0fd34f230cf5f60216d4fb7f0d7df910d3daf839f6f003052f213f0435b30be713101635e903f544103e081927eff90b4cd7fb3d0506d11623072edccf2a4a1bfd00f050412ce3cf201cff0bd5f125c604efd1f6f50b0fce230cf2e9e721bbed170e1be3072fdff42f0530ced7330b1b4ddbf7dc,
      4096'h1011f5e0dd1ce10e0ed003f231abd307cd0d18dede0625f313e50135f4f7d2b7f6a4ff1110dbf6b812ffd6d2a115e2e7a3dc041401f9cdd6efdc05d5142b27d019f519a30cd4c2d819cdc3cce3a427f2f9fcb516bade00e6ddf9fe1da902fcf88430c50cadfac521fbf1effacae3fbca0318fdadc9d10a11db1616bd12c6b9d81997d1192deb3dd91e26ef7f03ee22eb6c80cbf5e7ead511f54dfffd9f1fff6e04f4d1d8f140ee0200c7f8e10ce5037fffe0062433fcdb27082ee10506f891290fdfc700296010d3ee26073a1818d32db71fe8c414fd1813d2eb11dcff08e5f3cfb002b24a474bde80ece4031647f3fe05d305c9180226802a4ac565f6d4d9d3d3df06dde4cafc05fcf0f9f1c7d7c2fed6d4c4f7c4ccc8e7dfd7cfe1dcebf7c001f7f2cee6f9eee1e5cdfcd6fecdf8fcdef8e6f6d6f5d104f4fdc2e2e8cad3e6c3e9cbcbf3f8e7dfcff2eff6c7eecdf4f8fac5d7ee03e2fbd4c2efc608cfc9d3ced8e7d2f6f604d7dee1dd00d902f4d908dadfd0f1eef4e2c3f9e8f0f4cdb6cbc230aebddc80dbd0b859ec7ff5d833376810b8561dc18065b1210393b8ec55e7013021815653a143808171c87f9a1aeb2a01d0d8da795a1b36288f08bd808032faa680195a0774faa87f4abb96ee80382754cac02965d5d033830f98219e80d67880df80336138b080ab80e89e7f44b6f9b084fced2f1a80dbf1d6379be5cb05,
      4096'hebd112e1fdde12270a4542322ac633070405c01c109df4550524013203fd01e833d766db341b2bce02adf0effadb36351a05f926ef5715f63905ecfa41d00bef19eea2c92ff42fe3c4513c0df6c3e219293aeae32321ed0e0dd729b44afddafacf24e9c5e7212fee19edc9330b4b3410f0f2e80c07b81bd61c29f6fb2af0e3fbe3ec0edef7e3320f0d0101fceeb612f4bff6f69efec9de45f62ff5fdbaf5d50814ff0fc335fa04ebf0c7c4e2b2dafb15a0b7e30cf228a3fa32f5f0c715e0e20000f5c0a536fee2e9ef0fe002ecf2eae70deee6f1f6e7f206cce70ce22dded5febcefebe8b2d7f4f309e2e4ede9fe0fd702ffdc8f1ae50cea27e2ffd31dc7e6dee2ce09086505f80604d416110514831d77801ce1e634dac704c8ef091027533c25569803b70aa17fc30eee0f32ba4b54afcdc100a6b8d7fa2813ff44beddb07fe9eb00dd967f26342fe8301f136dd5f711cdc10857094222bdf6e2fe26fdeff5018e7a157fef500995d4022afc530315ffd9e0cf36363712376816278a24dd4fd0ddf8dbe2d0eafceff6e7f3c2fbcaf8e7d0c6fae9c8c3f4ceffcde7dee5f7e9effaf1ceea07eef0dbd0edd7f9d4ebf8eeffe0f7d9f1ebfeebfac6faf3d0cbf9cce1d806f7ee00f8d3f3e7fdeae6d1f7f3eff5c8effddeeef8d2fad0f6d1c4f3e5d1f5dff5effadce9cae2f4da00f9e0f6e6e8fbe7f002e3f0f4e8f7dff4e4ed,
      4096'h8b82acd4e2bf2bef07602e7fe31b0df97fce8036e8bf800aba20bddee3e92b7f074a0b80fcf8a54284d770017fac3b7f185aedcbad22e213514af93cca99805ce8cf895348781dcea84b7f061f398d4b6817128113ddda673dedf0d13f0f9c0669ad27b7591d2dd9bbbaf0e2f3723aeaf09cfac8282e16800546957fbb1dc22ce823ec1f1aebf4dde7ec0212f10122f527ebfa3006faf0de011607f5efffcb0ae01bb5fcf0ebeff319e3ee0d38dfced9413ef7ee1901500119f007fdec05d6fb100b0728f7063314e3f710f5fb15e92405f80c03f63a1501ffe502f00f050b0239d2ec1f1529c6f3e3ecddfc17e41012fcfff9120ffed9fe2423e618cbec190bbcd6e8d8dbc10cd09746f47f4f3406ee7f1c09e413918064d66d27ce8c8dc70c0c0da5423874143707b714d60446fc5e3f3824e9f9ec7f53f9e5fdb6beba802f08ecd47f5f4f36efde315f07cf1ad83d5214eed3ebb5b31a091407c3d510c3ec5880cc807f7fe9decfefb40afa34f6e2f234bbfc13e54480fbd2bb3393258ed7f10f00e4eb1ef2f8ddf9d0c905ce03eec6f812e6c0180cd801ce18d807e0c2d0d4ccf3fbfad805daf6e7dedacbebc6ebbdde04e7fef103e1e7e70bbef117ebebeee306b6fae8ce090ff3c8dae6d2ffdb0302d806dcd2f8efdc160f07d01b03ded60bcdfad0d6cff3f7edc60decccf1e6eefdddd5e1e1f1e8cd10eac4f5d8e9da,
      4096'h0b07140f03dcbeb00728f345e86a1bbafacfd17febdcf02be14ad8f441e4d610c81405ad02f8ec13ebf2eb2322a1cc08e535f4df011b497f1cc1e6041acb1316be07fa3015e7e829c96d21db1b190325022f7fb8dc40d71a5ddd10d2d2d5083c6ce52dd23c28a0d7dbfe131804a9de3403fa047d252c59ed301de407133f3230d6d7e8b0d1d2e2f1d1e4d4eddac6effbd5f0e2d5b4cdcee4c6d7dfe5d6cfddbbf3e1e4e3f1f8e4dce4d4eab1dae9d9ebcdd0e5fcd2f2d2cbcae6e6dbdfcdebeae0c0d8ebeed1d9d0d3f7dcefcee0c7edfdf49ed5d1d9d6d5b8cef2d3e4e9d9ccc6f9cbe5e5d1efe5f3dbc0f8dbdef9d607e2d1bed8dc04dbb8ead7daddc2b6cfe8c5e7cee1ce0aeafcf406e7f0a3d524d7d3dfd6c0c5cdf6e2becfdca609f6e80ed2ddd4f80ce1e3d2c6f0c9cdcdeee8ca9ee111d2f4cbd1f4fcc0e2e4cadff8d8e1c6b2fbebd7e2bae9c80dc7fbcbe108f790d3eff9e001bdc91cc4f5cccdc2afcedcceebed0fd7e1d9cfeee4fdeeb707dbd1acf1c71dccb7c2fae3ccb78bd307e3f7ec1ddf06e3f516ff37cf360ded4ac8dc14f7fbbc1edefd0bf5fae60729e126d1e3ffff1a2de21018f6320f10212b1afcf307d042f002fbe02ec3ddbe4904f50739203a0efbf15815ef050fd8f3da2c4ae015e901fc0aee06cd07dae0025ccf22f37a2a12ccdad5fa052929280b0605fb4e0f0ad4fded10042cae1c1809,
      4096'hc2c30dbfceaaf7faecceeae1a3b19c05c3b9b2e6a5aeafdec2b0babfb5e1f3acf9e2d2bfddf5c9d6c7bdf0b9dfbfdcfac0d0d601c7decbc7efedabc8ccb5b5e2c2c9afa8dde1cde1b8ead2edadcca4f8e7fd98beecf7e5e6a8a9f6b3ebceacb8b3c0c1b1e7e8f2c6d0bebffac4fadab401eaa9bfd5dafec2aad0cec7c1b699bbe1db07f6f8dbf60af6e907fad6e0d6fdedd9dafcf4dcd7f2e6edd5fbeefd0cde0607f2d5f100f1f9e2e00be3fed8f9fde3f8ecfae1f1e3fb0106cafbe9dde406db01d5ebfe00f102d9eaef0be1f7d7efeff5e3e30ffdf705e8d6eed302cce3e3f1dcf6dbf90407eadfd5fefce806f0e0f9efede1f7f6f5efd0f5e8f8efe2cfe8b59d1618f51b7fe81dfefa4b033eddf95815bd04fff5ce1afb7fa1e39b04d97f3375508042ddfbe11ec1d7fe9880ae7fb9da2209d53af2db7f42131240eaa740b0f5c403fe79da3ba0022775047fdc2806d9f0b1370ebcf4eb9df5d52012d73911fed6d92e2ad40d82bf14dfe8f3cadf14daf6007f03fa80694fe876581e06cce00a063b6cfd240d32e9220ad036f40915dee110f1f7f5e6f2030220023a2b14163ae0efe7ebdc51e601142230fb36210b00f501e7d419ea2f310328d1eff044ea06262cda3621eef6202df81133fe04f9d4040120f64f0e06dcf6fc21f2142524d555fb292600f004dd0d010cffe10e0303151332f9fff82f09210fcc1e1351,
      4096'h11a52e417b0c4f613dc00411c8f30cde27c4c1f1e213be3fee53c6330e3d0d7f297fe691b4bb0b6ef608f44a11acd4550912d308d13cf9166ae0cf2409f9f17ff6f2b00ac27ff321cbc4bf1dba45ed05f6b0e6037fe36708e1d6e1ea1603fc3c22c67fc764f433e087ffee2a4d30ccd00e0618087f123ed673693c1400d4f019051ff616f20608f518080d15f304fb051c1a0c271affec10040305040715340ffd0a21f4f344e708f514152522012e322b1cfd13fb100f310e2beb14f004fe2c0d0519251239fc24071c3123f41a0c2d180b0e0cfc390f25050b0f0719f1fff924ee17001c3339fff80cf6e21139e30d0709fe082d0efd050b1afd37e805f103f1aaf55e7f0e7fcce2b2f4a2c6cf80bc048fc205fed8f4433217d24cec7f8a52fb444680fdc839d62ff8167fd88c0b129a2f21ddd87f17287f20f7e47f2dbb24e310a6d9182f93fde714be4b081521fc97b632057e127fd2b8a108e9b7121213e7a978fe50aef22680cd1de8efa0fe0a0bdcc7a47f41e3047f7f0ae14ce7393ac2b5d1e904affe00bf361a7399202b0f46c0be21daba80ccdc07bbfac8987d4225658ef2b808f07f9ccaf3ff68df1e4df5e12c1affc4311727a2f434c495806dc6dac267077f3ed6de6f06fd297fbe08282f4ec325bc27cf0a0de2c3eb2bbcfd428014bd7f6804b7abdac903d5471ab509f3d6fbef2b4b97eb48ed558ded0f0b,
      4096'h1b860e317ff7461beaa7e3d433d4a2ecde80e0e68017e20ad931e0dace31b97de21bb480e080a011cd02097f18800a67bdce21fbabc6fddb53323411f311b15ad2f3bbf1d53aabd8d4d4b55e480a048ffcc407ed7fc5731bcbe6ffe1e41c0d38ea807faf3dccddca8006f49d1c28aaf4ead0e6937f9602047f7f0920ebdacd69670d290d0731fad80db8b38053deef0c80d855f80b7f7780428d131d1111f8caa7ccc953be97d7d61753f413801e16a29abb03dbfda7dcb6bfe937dfe45b5c80012c78a5b79d800c1ab980df0fec40d0a6d60c32caf64c218b13e647d03262088043d129aedaaf0aeaff1be20bafe34b032401cdf00f0d56e2ec288af3e7e7cbcda5fda0c5b1e50ed2d9d0e8c99d9afdb8c6a6c88ab0c0caa39dcbdea9d9e3a10fcae5bdd0e9d2cbdeb4e89adac2d8fc99aeecefd4e4c9c4b5cdacb9d9b6c3d5b6d7afa0e6c5b5d0c1f9cbee9fb59aeaf2fa8eb3e9d9cfef9bc3fcaad3d4b1acadc9beafb1e3d6c68fbfbf08bee1e4affdd5bca4b8d6f9b697ecddc0c99d81badfcde4b9bcaadfdac205c804f2c5fdf4eff1c1f2e6b7c805c2f6e6d8cfbfcdd1ead31ee30513f7dee6bfebbddeded4d8e8eafffce611eee8c7d6c7d2fda7e9deedbbc4e602d8f2c8b618f2e3c3ccb10eff0dceaad603c6e1efc60593d2e2adc6ccf4c9d8f4e4ddb2f9efc0d9c5e815dbfee4cfdecddb0fcad4d0d1e1fbd0bfdb,
      4096'h0233f0e40a2eec05c0b103ce5229330009132b3b25373ee00606022334f6b7b93e16d87f0ed47ff369de80ea147fcaa4d6f2ee3b3dc92c49fdbc27a74a083131d50f50f8aff682ff2cd1fcc1cbc5272a04fbfd19fc3d080429691d47db0628001f39d853170480027ffcd14820851ee207790031e5eef965efe424e838d3f7fcd4d2fbe8f0d8f6fef9d5f4f5c6d4baf7cfbbd1ded0cad1eed1dccff3d3f4f6c9ffefe3ccf0d4dbddcfeffbe0eac5f3fecde0daf5cbf9d9f5e3f4b5f3dfddd4fac7f4d0c1f3eed507cee5e40ad7d6cfe1e3f2d3de00ede6fdddc9f0c205bfd1d1d6c1f3d6d6e8f0dcd6c1e106f1f2ebdeffe5f2d3e8e9f7f2deedf1dddde1c1e0294c000be823c233f7fac2b6000a1802182e3fecfe212ce0f1a11e10230234a8fdec0d6ce50200063837bce1fd61fbe8e0d007f520c8ea0dbdd837f1d91f1ed8280645fdf8d3ef0d271fff32ebac1d99090bec2603e6e7d01d1a0d3b27f52ae9fe0f082eb5ed0e1d5d2117e61d33ddeef31c17fae2f90e21d6a7f1d0f80010e3ee18f90af520fb130dfbd9da1cf9c1f0e30c1bec091c0acc27fd36fa170dfee706efff260fb1e6f21525dd05fe0a0292e4f10bed0a01e0f8faef24f7e52a10d81d120ef7fcd5f9fcfad4f8e605e41cd700f7f81905e705eef71d233403fb2107ec12f323dedbde120bea1e0029d60d0605f8fcfa06fde824fbcfedeaf3051e02,
      4096'hf1000df902fb000505f10902f9ecf4fef4fbf6eef7f5fadffae0f8fffe0104f2070202f7f4fa01fff5fd0af3fbef00feeff8f2fef5f8fafdf9fe000107f6f8fafafdfdebef04faf700f20301f006fd00f7fcde04ff010a01eafdf5fe09eff7fcfafafdfef7f9050302fdf9f6ea08fdf1fafefee2f6f2f8f3e311fffb02eaf6f6e5331cdd143e1506eebef8b6330d0b0cad40130908f72bf71a093fd4d8ebc9c913eb2722f9b94df061bfcdfccd05e1c2cf09ff144f15041a0bf3109c320c021c031514dfe1dfbb29dbdfa00aec9205fb08deeb00fc012bfad11902fedd0e00eef224e003d0f7c91305170c1c13c11e08fa57e5df0ed440f02ae52bb3329fd3cc044c150b303be1181cab1c80e5f0dbf3c61622ed126d7fd605dafc067ff5deb405e55113fe80d4b92359e00e35d6e4bcfd16ddf221fef6ffedd6fdf114427f0dd62f0efd95ca9a7f2683e2f910d85e98b7ae2a52332421ec0117ea43f2ea3d13d07f1b7faee1cc32ed035b1c6eb2161101cc4167e33bb277e73d4cbb050142c94a6b5852fc29db68cad03480ec181a809c1e419e25187380bd8032eb3613358026250efab6bfc824c97427f6e5fe6917c0800fd1d980804b88e8434fc0757f25e634fe66d4d1803535b22d75bec07e820cdbfc30dcb2f3da7f7f08705caf4a38283a25378080dd133def7f4916add731fb8d70dbf7419e73ef81e8ffca393307,
      4096'h2880f79ac9195bed80ef016d7f1b33357f6ed819f5c9e8290c7819ffbceb80580cece52926017fe77f93809dff7fb14ac8e70c4c7f3e26ce12b730ab4805b7533fd18711c943ec2ff1c3c3c4edf807f166f81823f480f139a3560b2b855f1cbf1e38bff37fba80e6a22ca83d1b80172c147ff368e4e20bcffb1b06197f98ccf10dc30f01fcb33100fb0f1c7fe60215154ec58b1f2495802ecd7cc9f1c0f60441e801d3bbf906220fe0b31be9faf2fa7f2a49d8f310fc380d2f2bb60f07b1803ef2f09f0a2946f101cd29d705ef20c45544fc04ae130bf8180cd3e2982eebaaef15800b804d4912d7ced5d8fbe73c1ae70be6cc0634f4138024320822c101f1170e0a2a3e7f2e411544e22a12e7430c5830bf2d0b3335f9ba03f31d3b59485e3e3b7fca21b8d40c68cf4848720a1337332114ea18eb0251281c443976c249df7fae1c401b9d66e67624f6d655447f211008ec1c377f0842031105ec1c38fd471e2d9f7fec4d075f25face1bdb54000b0bf8282334643f740b4b332c4cc17f0f7ceaf215f229f342fa55323bc91308bf08b3e5cd3f048059b20718a6270518f510d8db7f9d5eb65bb15892d32f9180eaedc16a4012194dfb11726dfdfe7fe07fcc1136c0952086b21bbdced325e6bbe64f055f32f2287c7f23faaa65c044e0cd23ef7fbbe9801e062fc43bff021ef1132a040a250d5193acef204628f67f1bf7da,
      4096'h250b02446f2301d906d2e0f60bf1e6ec3be8f421fa1a0ce0f8f82d041920ff15082dc015d2e3cb52022a775310e41d151218ec03fcf5f611de4a1537d21a0061fe0416efd76918cf34e0f64e086b15ea0ce41b0033042d0c0d22fe210b05251619d07a1407f70604b6120de32e14d11a00d413fb25f0040d372219f3e019f721ddf7010aeddc44ce9e4e297f162c4fcdf1fc138623bf277f087fd8c980d5807fed2b7fbc727f7f385580f6c18ec480f2df35317fea7f3e077fc828d67fbf3a1436f680a76806bc95997f80eeff6be423ee7f60d9e780cb0c804567a68035a712ec180eea5ac480dd12f5809dfb8031d5f23980512f93f9e1f7110cca7f000d06369d59fb7fa87fba5a3d14bf0a758c7f2ecc90eeb5af7f7f1d7fdb670f4c807f45177f9b7ff67ffe7fa5244bf0d38026807f7f7f717fb3637ff95dcc7f197f06bd2d03807fdc800d150c80214dea63b6147f7f9320a67f7f97ea7ffb8057b76a4d7f00f26713802c807d83ebe6807f0c037f803c7fad7fe07f7f5fd97f80e63d11ecf1cfcb15e8e4dceeadbe0d9cecf5a2100fabc3060fc8eab518d304dcb2d8d8c2e42a00f000ae17c3e5c8ab17b6d18bc6f4f206e8abddc8d30dade2f300d2fe03029affc2d4c9d3e3ced3d4b8ecd601ff90e6c6b9ecdaa316f811c20aef9fbb0cc1f2b1c2d8f0ee05cb070ac6f2d3f10adec9c2cff1f0cdebeabaefc584e0
    }),
    .CHANNEL_BETAS(1024'h782b78a5790b79eb7968777278b5756077ec79d8798f78507645798778d3785478d87933773f76ef799a7732792b76ba765b76c376cc786978587779782c7968783478d678b4767c792378b677b376c7771e78e5770978bc7859791f797476df77cd787c785c797f796d77d077887701770578337725769977cf776374dd78ff),
    .CHANNEL_THRESHOLDS(1024'h0218021e021c021001f301fa0207020a01eb021001f801fc0208020901fd021201fd01ed01f5020e01f501fe0216020702080209020a020e020801f201fe01f601f5020b02160210020c021102080206020e0212020301fe01f501f9020e020f0201021301f501dd021101f7020101fd01fa020e0207020b020001f801f70202),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_project3 (
    .clk,
    .reset,
    .in_valid(e_41_valid),
    .in_ready(e_41_ready),
    .in_payload(e_41_payload),
    .in_completion(e_41_completion),
    .in_bin_tag(e_41_bin_tag),
    .out_valid(n_project3_valid),
    .out_ready(n_project3_ready),
    .out_payload(n_project3_payload),
    .out_completion(n_project3_completion),
    .out_bin_tag(n_project3_bin_tag),
    .actor_error_o(error_actor_project3),
    .initialization_done_o(initialized_actor_project3)
  );
  logic error_actor_decoder2_fuse;
  logic initialized_actor_decoder2_fuse;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(128),
    .OUTPUT_CHANNELS(64),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'h0a0204fff8030cf707f4f701faf70dfff601010b1105060f09fef5fdf8ef0501eb10ff0d08f7fffd0b0801000008ef0a010df71304fa0005ed01f6fd0705eff7fafefd07f00804fefafefaf708ff0803ffedf608f607ff1602fbfcfe00fe0afe0afefe00fe01fdfbff0dfefefaf2fcfdf9fff9fe00fbeeec0306fdea0009f7fe07490ee0d9e913a921182debf8d9ee07e5d5605b0704802007dff8b344cf0b3913421afdd9f8e1fbfbe5e80062c62b50ef2c0b3749440fc47f00e76d8f3a027fdbcced7f06fc80ab85f88013400560b47f28328005b3f780938dbfff80f68020ce1bc62af1f7805680118dd28013ed0b03f7220415d4167fcd9ede80e180911d06010219e2d410f5e81603e1ebed18db2111f46210f30cffffedbef8150703f0d20c14f6f10502f4f809f9042eead1200003f20a2afc03d314efd3faf620b9e4fcfdfd01ff36eced0603010214fff9fde0f9dc01fc00fcd5f5f70605edfd13051cfaff27ff0400090b02110a19fffbf90c0af00b04200de61afd0703f3181812cbd8040510e01bf41ab3aec4e50ad737ecd60fc8d1060143132626c0cb01d5b7e307140205c324f4ef0efac2d9bcafcdf7e8e0bbd8d3fef4abf5d3fb070f291606090be6c080f2e5e40601e69efc04d1bff6fed909e6029de107e806cdc4b101ca06fccb010be2c8d90502c515ef0afbe309d3aef7feccb2d3dcd80ee6abeaf7,
      4096'h0d1af4f4e103f6f009fef30711ea09e9ff11fb1e02fdf90f05fc03e81df918fa0c06fafde109eb1e0d06f81007ff12150bf9030c06faffdf3306fe16f109010603fcfa23150bede2d202c002fc031c071007fdf1ffdefae9e6f50fffdb01bb06e8050afa0003ab27f8f0c4a0cc0efdfd13041412fcfe0b1a0cd2ebeefdeedffe12fc09031c09101815f300d208fee628fafe0feca3fdc9070a0703d91602f8fb0700dd0429f60dfe03ffee0feedf00bcd6240bcae3fa06420305eb04e5f8040cfa04fdecd1e9ed08e0f9e0eed703ef17f6f0f3faedeefde514fff0fbede8f8efd605f3eef4fbf2ececede6cfe2bef704ec03d1da01effef7f2f4f113e4fe10fa03fafffb0306fc000101070101fff6fcfcfe0000000bf8fdfa0001f900fcfbfdfdfd06fcfefbf9fa02fcff07fe00040002020509fe0400ff03fd020202f7010900fe000bfef403f8f900020201ff04ff080201f902fe00f602ff0300fdfafdfefb000200fe0100fffe0400000200fefbfe01030001000105f7fe04f3fef9f2fd07fceed41801f70b04ee0fe805f9e003f2c5021af01bc40cd6090fe912dff5fcee002606fffbcbe221f4ef1e0515051f2a182a1e0c2000fcfaf8e504e9f40b32f8f5fb21fdea05f0d1020b15fdfd15f911090fccf304ffe9f6df0d0103fee501d502f60cf8000402fdecd20aef01f8fc05fa02fefeed0510f0f903d202ebc1fb,
      4096'h1c1f34ddec00d5e609ee092ccca90924c6400ef909cecdde03ed18fe3ef142f321ce1d3dcdd51c10e24e342703b2e3d4e13e0f1a0c3b0a08250bc5ce16df1220fb03f7f6b44bd00ee301ecd3090b80ffd4c8fb3ee402fe4e3d0dfd071cfe5bf62a070225fffff6dfde0cd21ae080ef060dfd01d904dfbb955c20d1dae239eceff83000e81eecea29f1ea2b04fb0ff41f09fef5fad41dc7f5f9f80ce11afcf50202220b002cf9fc2f0508cefe0afc10f8e319fa0dfe0aff1b2aff192fdbfffa19fff4fe19fa06dd07f404ff11eafcfff509110ffde7ce03b8ecebe9fad1fed1040703e9e8f6ffbbfaf804e0d5f800fc06e4fcf506fffa0118f0d8f5f6faf3fcfffefaf603fd0001f7ff00f8000802f9fd09fcf1fb06fc070301fd02fe0504fcf8f1fa05fcfc0802fcfff10203fff7fcfe02fa040000fcfe05f501020302010201010101f3fff80305110004f9feff04faf900f5f600f601f5f7fe0301f8fbee02070001030201010b05f814010b0702fefc01f600fe040b08f6f9080704f201ff01ff02c60feae3f906e711f80101fd0208e813f1f6fbf10cf8010c01f40608e712f71b020d00ffeefb02ee1911f310e7120f1423f30c040d0a0207f410fc150b09060526fbc710ecb1fffc07eeffff1019fdfdf90ffd0301f2fefdfc13000d02d5040bf2050204fffc04f8f5f9fb0a00f800fef205faf3fdef04fee0eae2e500,
      4096'hf0f5f2050501e6cf01e8ef041113fc0905cef7d0db19bef5070519f41007eff9eae503f9ec1afa0107ead908fceb23d6ef06200bed1007eaf6f10d0a01fd280ffaeff5f613b6f7f8e601b716cc040efd2d0af9ca0bf9fedaf2f8ed02f0c8e5fafd03f300fff9f1e0e1fff3d6db0202fef2fff600fffb0a36f2f2e9f5eae8eb0810a300f5f1fab5d0a01c1c48e3f220f4113bf5cf48e329e4e3d3fa24c4e542ebf2aa25d3071cee86f3fe5544e81df0801be543db1c190318ad153db52bed29fff015fcc6ccc7f8241b030ce2d90693d8dcdafc2c03ef07f92a2ad0f7dc21c5fdf7080ad70503efdd0ef519df0ec3fdfd1b0dc6f5fefbe9b00009e020060d17df5226f0b1cece853380d26c0dd0affbc7b92cc9a42dd5cdd6e6e9dfb0cca6070f44fcf1f7a3aa2329d058cabd9aedc8c7d1c7eb22cf0cf3133f0dedf6ca890311e5f5fa15de53f606eef4fbb004fddaefbcbae0000df1040310fee2fb082b17fd0a04f62708f6f9f2f4e2fffbc2b0f00d2f03f6d9faf5f204eadf0e06f93febe8ff0ae80c0cd51724ff08fd21d71013131222da120d0af502f003f7fdfe0b27f4ea46f8021918300205150e0c20150a270be3edf72c0efa0c1cfc0318f918ede5feecfd14fddfebf2ec00cf0e01fb0df60c20fde5f7ee0493e508dd01cdebccffacfdf6f307f7d8dfddf7e8d3e81803f2ebf601010201fa0af9c9def4c9000b17,
      4096'h29d6011132ea0412e10dfc1d01fcfc25f11ae40217d3f5f7fa07fd0a05ec0521f70f09011cf813f1222804162724feddd70fe7fd0f060718d8f21540dbfa09f401fefcf9e8012edefffe40b9730719f0d3dcbed8fb0502b8e0ef3709091513f421fd012df9091d3927f8133c2f0dfecbdf0cc2d6fdf2fbf4de074ccd25e3c8f8ecd9fbfb0efa0c08f8010309100ff9000b0305f906f00f0d1af802ffe0fafceb09fa01f90c0414f9fecef0d6ae29f00809f4f00beed20223f900e3f905feeffbfefdfcd4fc9726ede80002d6f7fc1802e1d3f3dfe701fd23fc0005050bf50cf701ff0df3f705fafa1a06030307e7f7f5e003d40201f2e3e5befa0aed09ada7eef0c3fd14f1d2f69013270732fd3213b7eb21e9ce7f2b7f22ff2909fabb010dd1e80451f50ce9df86e2f423e706f8b7213bbed91f03bf00f8ac121e814f06f3b1271b27d5d7822e05ce03e9d3bd099ae6aad6bcf20e1c05d0b524f50af9c4f2f2a7fc27c6181a290b1bfc15e2f8e215f3c610abdc03ffe3b5ed02b8dad9d610101f58febce5122cf31b3a7548eae313bfddece12135f78d031200c50962e511e0de4e0ef3de0d2d321202e5ef1e094022fcb8c90b030eede37f06bb7f9f12c8f4f1f2e50de7d180b780f380f180093c0c7f21f2d9f5e1f38084dca0f7b6e1801ac5f404f7f2f780e09306a3809c11f9dae6091eea03dff275e188c294e1808020,
      4096'hcc3f0d1cb0b25bd72ef3b7e3f7010187ee063766070e100609f8bfd0df32f680255be0f9e4190e1706d0da8027fba27f2bf2be0d2b9bedb728fc80e41554a5a4fdf0ebd6352ec03424f31722e2feb1f2f23206fcfa13f9801afe2806d20a80feb302f1ee07fb01de2216cfa9d7e4fe1e17f00a0f051710011ede0c43da212d1bfa01fb03e5f805fb0005f504fb0108fafe0afb040c0b040205ffedf8f7fd03fc040704faf4fd02fe0102fe0006fcfb0b02fff50606fbffef0c00ff0202fdeaf9fefcfd020500f2f90200f9fc000007f8ff03f8fafbf6ffeb00fa00fef5f9ef01f600fefb0000fc01030601f8fe03fe000600fdff0004fcf903f903000205fefc19f9fc02f5faf000f60a0717fbfc02fafd16efff11e801f5f802f40afbf6090400fd28ff01f7040300090913150df1f3fb0f0211130400fc07fe0d0b09f2fb02fbff0017ff02f3f4e8ff07fd05fe00fcf803f7ed0301fce1fffc0afdeceed5f6eafffceafefff4fefa1300f0fdfcfb0202ff01fc01f70203fceafcfcf905fcfe2a80eb267f7ff13d7fffba807f65a52de8807f8080e38028c13551924dc78069988080127f014c807922d4f7dc507f8080c019e8de6cfb7f8000380380e77f7f16f6fa808080e102490689fe80f480e48080ecc9b9e1dd806914800b9b0080f4e3f401d6fe04a0bb9bf32b80c7bccd06b3f296b6f7bccd8da0a2e57f032050da,
      4096'hf8f4fd0305fbfcf4040305051012f5fd1ef9ed0502f815f30703030004fbf8fceefafbe50713f4fefdf8fa00fefd0dfe13f207f8f804fd00f1fdfff900020206000103070803fcee0e00fe0609fe03fc010affed04f501f7f5faf9ff030afaff14fe0203000006fffffd0506010dff0206000307010e21140201fc0507f30603030302ff01fafe01ff000202fefe0402fe0300000001fefcfd00ff010101fd01fafc0202ff01fc020002030200fffefefc0bfdfb0100fffffeff010300fdfdfd000000fe000dfcfd04ff02fa0900fe03fefef800fd0400fffefd030003000600feffff03fe0000fe00fefe0402f9fffd0300fdfb0000fcfa0901fff6ff0801fe020cfdecf702fffe01e911edfaf302ebf5d3fceec304fc0aee1ceada07f2fab1f127fefaf902f8fdf804c0a7eff8d118f30604f2f70efe10e0fdaf3bf9e9ea0dfde9f904eac705dad406f7efd90137ecedf4dfafe7f5fad1c3d9f8fee1ced11414fbf510f400dbfdedeffbe00604fce8ec00e9f4fee5fd05d6ccf8d4f5909f0830f6efb238fdc84201e3da0f1b19cf2fdee77f0bf11dedfc0ae00fe3e2cb18d642c51b0036e705edd4ffc4a99a2a43d4061b2206a941f559e204ef1724c20456e6060fcab8d449510406f9e4f6f6df26b9b90b2def1a07404201f90c2dd143e845ffee0701010dfce617d623e9aaf80dccffd2dd00bbced99b05120dee84afc5,
      4096'h10ce258080de23207f8080c76fb4e0b0fd8040dcbde97f01f2393584d07f03a472db95ec479477da8016dd80bdd5c53a56eed9f7b8042dfac80680805d802110fc05e9a48580aa11aa0d8012800380b29a80edd3c2e8018062da80fd93ac80018010f5b9fdf1f38080e58080999c131ab105a4801a0f8080a00a804996fc20f2fe0101fc08fe060703ff01f90201fd0904fafe01f305fffefb0404fa0602fc020106f90204030702fefcfbfd0704fd02fd00fcfefb00ff0b0101010c03020405ff00fe0503f4fcf6fcfff9fff001fefdfffe03f6fffafef1f0fd01fff2f8eafcf1fffef9fdfffafcfffffcf2f600ffff04ff0103fffafffdfff3fafdfbf9f5fa090dfae8fcfbe7f8ddd7f8c3d7fb00efe8db1ce8b914c4e2e8feeff7e7ecf1ff0209e0f800e10218e4e3eedcf0c6d8fabf08d7bbf5fe01fe13fccafbdad8ddf3f306fc04ce00d5050a05e502e4fac903d2d4ebfaebfa00e1e7edc90ad6cde1ead0f7fcd8f804e7c1c9e3badfbbbffa06d5fdebce01d9dacfeae7cde4dce5d1faec9fd5c97b112961fb010be32f28a50cfcf118c5dfb41409fd122df33808fb06eab908c426292ef3e3809d1bda3922bedad10af8f8ef0720eb02ce49f4f6f97edfec0dc4d2c65acbd5f70e801b0b71e8f78d80abd4d30e35baee17f824bd35097ff9f137f3040111ec00fc3f0303f5ded614c2eb0cfbe24e80f838b1068080dc,
      4096'h39bc73e3801e1ac78019808080807f8080028018801d8080e5e680ca80802db0803c8003808080dfcd9f7f0aa82e80be8080807f4680de9a49d5d9ef809e8080f3f3d6fe08527f117ffcc4de1efa801ea7c1d17da6e5f47f223a9cf01934190c7ff4e323f4f5d9e5d345a906ad80c73188d4d74df7d9a01880efbc0bed1880cb000c00f0f8ffe6f605f3f8fb07fbf8f4f8f00a06020fd606f0f309e606f8fefd0dff02fefdfdf0ec0df4fa06fff50a15110b0714fd0cfbfa01fdf6fef807021dfffefd0802f406ffdefffc08e6010d05090307fcfe05fd03ff000afe0904edf901fefbf8fe01f5f7fe07f003fcff00fe07ff0501fffa0204f9fbfd0000edebfc7f52feeb9e28c6f2c51d7ff8c5cb18319dbd1a0957a7aa0129e8df2b03c5e81817e4540de2b315271e6fdf26e80ff6bcab4e011f057ff3fc670b25becdbae1ff00fdfd02196ca7f84dfe04f2f506a1c39ce4dff8dbd2f8affcf803ffdb31040a140bfb44fef7edfbe0e7eef1ebdb04f34606b0ec01e6f6e427fc05f6c4231119207faef0170440d322b7257f49d6f0b6ee35a2477fa69defc9e0ea107fdc2babfc4349becd1680601add0d5d34ad32421622f67f7639f0224ee0947fa02ed27fd78fe57f7ff7bf8080f9155bad027fea7f5c1f80e09de09d80a202f2802b800efae5e27fede380e5df1ca49c2078dba107910fed1bdc387fd880e180f88080fd,
      4096'hf103ff01ef0302fff9fb0306fc0afbfdfefdf60705f102fa08fcfd080300fe08f5f9fbfbf11206fe0503f7fe020b0dfd05010305020901fdf900f203ff00f5fe02fafe08fcf4f4fcf100fcfff3fe08fe08fb01e9fbfb01e2f5f8f1ffebf8f100eefcfff5fe01f4f6f7f6f2dbfdfb03fbfb01fb02fbf7fe01fbf2f9e9f5f0f1ff2a52eeae67fa4912358d08b72ae7ece84902ef09cf7fe83e0326f0da5310e8df527ffa2165e1d40a93fe978bf9360e7f1f0edfee2d1ee51e25fb8040cd19c8fdfaf2e17ff89b0df180fa82fad7f173277f5ce39e0b2ce9808c04bbfd801d80f4ad07efd4f2faa2ebf2f08d80801df4f4e9f312e2fee7036addacdf80f4e4832dfef70200f8fdfc03f4ff0003f2fc03f9f30cf1f70afc02f803fbfefefcef07fdf7fb0001fff2f7eef7050504fafef7fdfef7fb0dfffffcf4f7fefb0704fef9fffc00000206fe070202fe01f3fffff50a0600fd07fc02ff06100002010001fbfbf902fe04fd0004000401ff00fcf3fd01ee00fefa01f4fafeff07fbfb0301faf8153f38fd0820e61be0002d0fe70b29f3f453fe07192a120418e7f018d0f702f82aff274810ef27092128251ae90cde1309e5f5021f01fa0e1afa070328fbfc00f901f9e9b9001b07fe0103b42f008000ddcada39e81f0330140dfe0524f562f620ebfa08fc000204f725e024feb0fc00bf09f1dafbdaa9c9f909fcd5f4f4dff5,
      4096'h8088367f844f7f80cf7f80808080cd808080807f808080184b1f807f7f80a980802a80c98c8080d080807f7fa58080d98080807f7f8003807fee697f80018080ebeae16a2c637f077feb7f0e7febf79efd557f021535cb590a113edc5c8050585c170f1508ef3b7f5e7ffa7f3b8008659b0a425bce65d5ef58157fff4931f13b25fb01080304e3fdd8ef05eb040701ede10222da0508e7da02eff513e0f0f72916c01a0afce7f61a04230002d119f9cfdd08fdc6e1070102fb02ffda1cd707f4fcfd01dee3131df4ec0622d82800ed03cad4b903e30afb21f2ee0bff2b0037fe1cfc0035f404fc1a11fff5210feef8e5f102b8ed02f9ead9d51a18d1fbe7e4fdb380f7b48007fea6f2352b23da334e80587ff2ae7fd46ec01bd5ee3f806117a5a7033fcf80dc80c89b805fe083e380567e805a28a2c30ca280e553807f08f60afc1c0e800ef1cd502711d0138104803a80226c0afc21f78151fad8f1bc228008801312ed070410c3e8481a93f4e911592df246cc093bff8046ccf57fc34f7fe90206fe01fefdf901f803ff01f7fc0afbfa07fcfffffefcfafdfefffdfefc000000090503fcfb02ff0703ff0903040003fe09fd02070201fc00000708ff02fc00fe000000fe04fbfcfe0000fb01000301fbfdfd00fd0200f800ff0000fe03fffdfdfffefeff0100fbfe01feff01fcfffe0502fafe00fdfeffff0200020101fffd,
      4096'h2408f4e9b4e4b2d9bff916edc4daead1bc13f30310ac8cb4f3e7d9ca15d20f1422e01cc3d3ebd5ec122bfa1fface3ab9ca311e19f5050dce1df2e9f7e8dbf634fdd1f33d002a88b6ff0808fc15f82fe40c13dbdce4d5fbf1eee71ef5f1f3f61720fcfc3ce9faf51f11d707111324f1da1afefaf0f80508350dd314ca2ee5d51a05ea1411f7fc03f40a140b09f30a130cf81409160002e7fff7ffd8eefdf40412020702120a0900f7fe1700e60601ef1cfa12f7f3060401fd0e04eeedee01dae201fc0108f606cf1109fd00040201cffce5fef4160301fdf0030ff804f210f604cfff06f302fafeed00ddfdff03ec02ff0bfdfff605fcf8e913fbf90cf82b2d0efd2cff05dafde0cedc0af4b7ffc9e9e8d4e110f9e8de80dec5f3ddc6ecece90537fafe10f5c8f72dfbfb08f9e8d903ffd014fd33edeaf6f062f3d4f58bf0fb25ebf3f5100a4aa8080a00eafe03fa0ddc120a2feef4d0fea215f0bc01e924b3050407f109f1f9e5efe1e6d90fb802ed0f12fe14fd070526fc0ad50422f41bd8fdfce21203fff4060d10fcef0af1030b130420fd1428f60e0ef7f9ec01fdfb07f1f3ea090e04fa0be20f09fb0a0707dc020aec030d04f7fff7ee02fc0313eb00f3fd01fb07080fe80a0800f5fef800ef04f9faf404ee0401e9f8f0fa01f8f8e5f70203f908fff9f8fdff0cf105f2fafbfd15f2fcea03f9fff7fdf3fd1df72105fb,
      4096'he9d6f40ae00ff7bef905e4fe120fecdefeeeeaf6eecffaf007000b08f0f0edf3dfeae1e5e200e9f4f8d6e6e8cf0707f6feea05f0eff5fbffcd0325d914e204f4050206d40b0be7241effde0ea805e9f1f1ef070207e900fff30dcfffe0fdd41719f8fcde05fe0feb0220ffd6e50a060410fdf704030f05ef1808f121e2252afe2680fed86adcf6f31bb3323d0b43fb11f6266fff02f5d21b49001b21f8f9041d1a80c5247f947acc2e2d1b10a21ce08ac3e3551cb220057fe702e2a149a14c26fa1617b484911d09ef06eebcb8f791ed8093c701aef311df4e06e508fbd5e5f0d2f9eeb7f2fd35caf818e8c5baadf00bd40280a8f799e2c5a500c862d1243bec806f2c807f4f1216d3c9218015b4807fc580018080828018853728807fa380fd2635f5200d10ea7f8e298080e6357790802fccdc802bf6297ffda364801e6e7febd4e985c49054f31ffd10310b0c7b64ee1344802e19e280a2ebd818260480e83223e50aee06eff5defedf25e35cfbb90d072b290edc48f7a6e1eec1db80a41bf6e813f20c01f509fefc06f4050c020cf8180bfe0df8fe11f600f9f70406ff08fde70f0210f7f0f7ec0408f6ee0dfbf1fe1909000c1e00f7dd00fafe0bf4fd19fffdff10f0030bf7de0200032801f3fc21faf0fbf401012a000cf5ff1bfe4d081700f9fdfdfa0300f915f62500f0faf7f900e2e9ffeaeefbfd27fad9fcf1d0fe,
      4096'hfefc00f307faf501fef002ef01fbebfdfbf70302f9ffeb05f8f906ed08f8f6f5fc0306f901fdebf6fffbfa00fdfa050809090a070806fffefc02f7fdf8f90311fffffe18fbfffff9f201fc05010115f9150803e703f900faf9fd0200fd08fa040301000afd01f8080105fa02f605fdfbfe000101fffc050ef9fa05eafdded6fe02001103e7f70b1505f9f3faf7fcf4e3faf2e1f90c0f0607f20f03f4fff5fc07f50ff112f9faf90ffaf4f9f1fe02fe1200eecc01efe800f2fa04fefcd9ecfefcfc01fdfbf50c0500fffffaf80bffe005f3f3fe0bfa0b00190e02fb030f0415fb13fefc07fb0108fcfe06fa05f8eafe04f7fffbfafdf5edee020af8f80015fc00ddfe010bcb1b1c0a0ee7df06f01209f101f8143c09043d0324eccf01d30a0eacf3e9d7f4f0f6e8fbedeffec40af0e34a3bfb0b09f7c3edc603f2cecd28f8c3841401facff414b1190404b205cc02e9f8f508361b12cff3ba241eac0698fda712e607fa0206ecdce495cac780a5e8030ffdec08f00813f6fb40b1ec37c4261f33061204fcea0ad2f2e50914f30c00fd100a020df9fef6e1d0dfe60708211500f7fcd7dceed422e11ffce7f3f5f4ff38e501f921e6c81004e30d041bf7e61f0c02fbfcf8e10e358009faffb811cafd000d1cfb28f80bb8f9c10aeba7fba9ffc4fa0207f0f300f9d8ecb10dbac483fefafc10f8f206080a00330bccfa05d4ef02fa,
      4096'h547fb27f80808080807f7f3080807ff5807f7fe8d080808080b780040180f67f16c880e98080807f387f797f7f3ed8eb806b80fb7f7f24e47ff37f8680af8080e2b5d380807f7fde7fef7f807f02803a8080807f807fd37f7fbb5a0f7f7f7fe67fd7d072d3e2632e6880fc7f3180cf4084e48080da808080f67f6f80257f7889fcfa0103ff07040a07fe03fd0110f6fafff21103f700fa000604ff04effffd0610ed03020303f9f300fe00f8ef070802ffff0afdf201fe04f0fffaff16f7010600fe00f8f3e206fbfe02f5f109fffb01fdf3fdf4f8fdff0f01fdfaff050110fc0800ff00ff01f5fd010dfd0102edfffbeb01ecf900f2f4f1e5fffef200e1d6fbb80feaf4100bf74901d415800b15ea1bf2807fd28026d22e040d0017f0fbc7e227eee2eb21ef5821c900bdafcdfe23cc82041ae2de6a033119f9ed032ff50907fdfd00d7d3fb0908f2f8eff70b07ca09c5e2e729f209f72715fff1021bd3f5f8dcfef211fcf6fefaf617f618e9c2f007bcf6f6f1fcfdd1b0c91b02e9ece910f50ce00ecd95ed0edcebedf720e2cefebadc22dd0f420745e50cf2a1ed92d105c3ea1e0efee8e708e819f60be01e16bf5b2e0fc027f9e6019d01f9dbcf10dda5a70e0cfeffea1bfded3efafaf8ea00c809ecea0109f9fdf7e204f2effaf3f4ed04f0fa03dd0302ffcce1f0d5dcd5e50a0df7f8d6b301f1d0d30019d301c50ff301,
      4096'hfcf504000306fe0101fffefe0308f5fd000109fb0004fffc05fe0003fd02fc0809f5fd00fffe010106f0f802fe0a06fc00f702fe01f90000ee0100fd08fe0101fe00fefbf7020401fc00fcf80800f601f3f5f9fdfafd001001fc000003fe0afb07ff0103fe01fd02fc02fb07fceefdfaf101f4fa01faf8f2f601fef1faf9edfae3f6050bebfe04f90efcd5f90602fbf50ef3ea1400f10c0e04fee7ffee0508e9ec1bef060b03f0faeef1f2e20df5e71d08e7e91300e5fff502fccffb000aefd7fdff000105f80d02000207ebe801f9feedefecfdf6f6fdd511ff0901f3fad1fce80100fffdff0500070e04df0cefff070bfd0200fffc08f602faf50a09f601fa0be40bfbfe01021cf6f715f5e50a0413e9f9f7e8020101fbfaf8fb11edfaf300f8e2020d0a0304fffdf6080ae927eed5f206fedc07fd0111ddfd1f100bee03eef9fafdeaeb1816fc12fc1cef1202ed0ad9e5e813ee1a020e090e0cfe081910fa18fefd0ef902130205ff041e11f6ff02e7fce6f7ffe8fce7e60606f60d03fa02ccd7f257cf0941dd2ef2e8e1faf7f1da12f91a3114cd36016205bcfba315d9f107ef07faed11cccaea1606cdfeffc93d200adb24e0db04e4c30ad5c51e18d29e0d0404bef527fd2a22021efcb0ffbddfcf0f0e3214eb0d90061db201df09ca12fa0811ff0ef93bee1c00fed6130305fd0a04d507051c21eb1813d020eb2e3af5
    }),
    .CHANNEL_BETAS(1024'h77a374f17414733176dd78d475eb75f7758b75e474ae76067369736275bc74a27493760b748b74837599765177776f5b769a763b767775496a207849774b74e5750776bb750b74cf76b07513739d77f16c6c76266bd375156eb4721d773d764477c176106e8b773e76ff7567739075087229775f770474d476dd75c17781751e),
    .CHANNEL_THRESHOLDS(1024'h020f020a020b01fe0207020a02160210020e0206020201fb0212020e0204020302110214020302070206020e0213021501fb02140201020e02150209020e020c020c0204020d02110208020e02120212020102110203021202130207020b020b01f90213020e020e020d021301fd020b02140211021202080215020701f401fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_decoder2_fuse (
    .clk,
    .reset,
    .in_valid(e_44_valid),
    .in_ready(e_44_ready),
    .in_payload(e_44_payload),
    .in_completion(e_44_completion),
    .in_bin_tag(e_44_bin_tag),
    .out_valid(n_decoder2_fuse_valid),
    .out_ready(n_decoder2_fuse_ready),
    .out_payload(n_decoder2_fuse_payload),
    .out_completion(n_decoder2_fuse_completion),
    .out_bin_tag(n_decoder2_fuse_bin_tag),
    .actor_error_o(error_actor_decoder2_fuse),
    .initialization_done_o(initialized_actor_decoder2_fuse)
  );
  logic error_actor_project2;
  logic initialized_actor_project2;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(64),
    .OUTPUT_CHANNELS(32),
    .GROUPS(1),
    .KERNEL_WIDTH(1),
    .KERNEL_HEIGHT(1),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(0),
    .PAD_Y(0),
    .OUTPUT_WIDTH(2),
    .OUTPUT_HEIGHT(2),
    .KERNEL_WEIGHTS({
      4096'hee3ffa0219060f2ffe120900fc0c1c000902f913faf317fffff80efcfb070403050f0e150517f3ec17fdfdfe0df620fefaf90af640fff30a0b02f900e5f600f88bcc8038fd0180de80c759dcd823808080133ae9e9ea009e8080ef80f4edf68080e18020c09ec7808080f61b80c6804bb13990b22c809580801c80e7800280230bf30401f206fff81607fdfdfdfd0a030502faf9f7fc0705fc20f708f802010b13f4050002ee0407fc0ef705fb04010af903070cf407f8f2020e09ff16f309fbfdf707ec00021b0b0f06030f04fcfb160ff4f4fdf3100cf7fd4afff8f51102fdf6f8040efbfe04050b01fb081302f603e5f5f40d0df5eeeb0aee00fd01f80af5deac29342d04808099927fe6e2d1fe8003007fbd551ff3f97f80e99c378011e4848dee80e0808cd27f8911cacd7aa0065206db8080a4ee2d0c90a11e80311f290a807f08807f80807dc5a8cc80c6e6c4e980b5805280017fa17f80cff6e608c57f80508080257f987ffdbb358079cb1cc71ba4ee807f80803a807544c9a16cfa8ad980043c0480b280a2cba880a2808080b7cef4de01f0808080c9809af8ec8080b380a0b7b0a8808080a1b2808080e980a98099c180c5ae80fb809980eb8081187f7fd24f19067f7fc59a7fda057f43ee8dbe4059fbed93ae7f4dd7034814807f0f5462707a3bc530f3ddde47534a76efd680f47fff7f150980e31480f3aff5,
      4096'h858380ede50e808080b48083808080b780a291b9f52feb8080808080e9ede48080dd8080b98098808080fbf080e8800fd4d18080b480aa8080a780aa803c80ec988080c780e4808080a58080808080808080808080e4e580808080809c11f48080b1808080808080808080f0808080f480b480808080808080c980ce8012808093c680001808ba0a80ce0c092025809b807b3b22e22a1612d780f68002f0f38080e280edc5e5a380808046e98080802d801595c1eb80d1c2805880ba80583dfb808060f4e7128080a0805ebe96ba8081d7bd12a22a2180b673478080d18e3e800c807f80808080c680d87f6b927f8088d68780808006e28e2c80a62a80e57fcc8f8080ffb40d8080808e9e808080808080a98080f6d4e28080809880c402e380808d80809b80ac808080c0d88080802c900a80808080b58080f880df8001802605c0831434c77f7f9177fd3fe570807f956631c4804913cb80805fd11f7ff6eb807f80b87f4f02fe801328579be8c50d80122e447f80f5d6807f54a3803626d4948080ab80268080808b8081800280808080808080e5d38080808080c504e08080808080bf80b2808080c6db808080c280f980808080808080b8808980ee8086838080948024808080128080802180808080808080b3168080808080f3c8e98080a2808080808b80808060e0808080af80dbac8080808080808080df80808080,
      4096'hf8d219fede06bb80f3c304fbf2d2ead0eaf40de85816e0e805ec15e712040ce880bceffae9a1f2f6dc050bf2d222d6000b0380b295ce20fff2edf10a9b26fc2783a78011501580d580bd44b2be9780808015ec1a13201a8e8080ed809cf7e78080c680d7b1da80808080bcce808080eb80dc8080e280a2a1800e8089803a80f42b02ece81d0d12d069bdb300c7f508c9cdeeb900daf1d5efb053091edeb103d7abf503f7eed9111393f7ed06ee1e8019f2f0f30ee82bc79f175c33037fdfebf880808086cb0b808080f080e2802e80808090808080bcd51e80808080e2d5fd80809f808080808380808048a2808080f1801380808080808080b680c380048080b71c104bf87f808005807f80797f8091382b7fd85422487f7fa829087f802a6b8080c87fcbf04bebb4097fdd7ff7808d5023e7888025b23080645d077ff6ead8f07f731f7fef267f7fdf25423ce6464ce44512797f09f0f336282ed30d17f61880d1e1224f7fd1cebd8812c9f17e7f60f5f0a62413e8567f0880c2128067d332809180d1a024c48d80e280d880a280b68080808084160d8080808080f1fdf48080878080d780bb808080faf380be8cdcb8a48080818085a2808080ca80ae8080808580ccdeff808080f1c0e8c32e80b38080088180d328b5ac808d8009ddf28080f980801e80d48080805a0b808080dbb915e698808080d680a980c380c1dcd6,
      4096'h808080ec9df7808480de808580898080809c80808210d1808080ac809d09198080b08080a280c98080808abf80808002801980808080808080fe808080058080d57f0b0d5cef764b80cec637ebac06f8c52ee94f7f7326b5ea8139fffdae1e2e8054ba182b7fecc91093f9e0d3f357080adfe83a58827f0f4533d401807fb854ba3bb807f603657fe348f7fa1df73d53f111de3ae5031303e1c71918033ffa27f9693621307fedede51b941c19fa7506d0e52d277fd90a15532cf9eca8f6f5cf29844d2e9f1d859b450e3080e1ee180d6afb05e7d0e51450157ffff5e3e2f50c5dc933131580e765f65fa547fe4ee753da1a54b9cc18baa87eb93de87fd85ac8988080e0df0380b980cf80aa80808080808080cc80d20d808080c580b3fcf58080dd80808d808080808080d8808080de80d28080e680808080ef809480fa8080ef212308f7083c7ffc180e0ee3e614321831fb1d2e333bf8e0fc36f8fc18f7220e20e521312607d53edcf20cf2063f16e1f0fbf433d927d7f30601fcc71bf00480e1800bfced83808080add614cd80e1808019c080baef80ba808080fb9a128080048080f098a980808025d9b6f280e5d70abcb3b180e40d808095d880d801dc808080f980328080808784ae8c0780918080bf8080e0f980808080800cf20d8080808080808095808080f0e480de80bad819808080808080808080ad80cf80b5
    }),
    .CHANNEL_BETAS(512'h77757c8077ef7727787077887c5076987bd77c057c8275097c247bf07bcf7a7b77527cc276eb7bd376bd775d7a2e7b617cb577647692772e7cc5768779917af2),
    .CHANNEL_THRESHOLDS(512'h020c021f020b022101e40204021b02050220021c021f01f40222021b0224021d01f902210216020b01e80200021e020c02230208021202080220020d01f70212),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_project2 (
    .clk,
    .reset,
    .in_valid(e_45_valid),
    .in_ready(e_45_ready),
    .in_payload(e_45_payload),
    .in_completion(e_45_completion),
    .in_bin_tag(e_45_bin_tag),
    .out_valid(n_project2_valid),
    .out_ready(n_project2_ready),
    .out_payload(n_project2_payload),
    .out_completion(n_project2_completion),
    .out_bin_tag(n_project2_bin_tag),
    .actor_error_o(error_actor_project2),
    .initialization_done_o(initialized_actor_project2)
  );
  logic error_actor_final_fuse_standard;
  logic initialized_actor_final_fuse_standard;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .USE_PARALLEL_BANKED_STATE(0),
    .STATE_LANE_COUNT(1),
    .STATE_CHANNEL_LANE_COUNT(1),
    .STATE_SPATIAL_LANE_COUNT(1),
    .INPUT_CHANNELS(40),
    .OUTPUT_CHANNELS(16),
    .GROUPS(1),
    .KERNEL_WIDTH(3),
    .KERNEL_HEIGHT(3),
    .STRIDE_X(1),
    .STRIDE_Y(1),
    .DILATION_X(1),
    .DILATION_Y(1),
    .PAD_X(1),
    .PAD_Y(1),
    .OUTPUT_WIDTH(8),
    .OUTPUT_HEIGHT(8),
    .KERNEL_WEIGHTS({
      4096'h7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080807f80807f7f7f7f7f7f7f7f7f7f7f7f8080807f807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f8080808080808680808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080808080808080808080807f7f7f80ae848080807f7f7f7fa07f7f7f7f9a80bd8080808080807f7f7f7f7f7f7f7f7f317f80182f809ca6802980803680807f808080808080808080804d7f7f7f7f7f7f7f7f7f7f6a7f7f577f7f7f7f80b07f80807f809a7f7f80807f80807f7f7f7f717f7f507f7f7f7f8080808080808080808080808080808080803b80fb8080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7fb77fce80e97f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f80807f9a2a7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f227f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f5b087f7f7f7f7f4b7f78807f7f7f7f8080808080808080807f137f7f80807f641e80808080808080808017b947d08f115a9b4fc180809e80808180808080808080808080808080808080808080808080808080808080800e7d7f2a7f7f187f7f80808080808080808094557f077f7f9ab4,
      4096'hd280808080c3b48080807f777f7f807f7f5f7f808080808080808080db7f7f387f7fe62c7f7f7f7f7fc6377ff2267b81807f01800a808080ae83977f0ba21f94808080b8cfa19d80807f397f3de536e880c17f7f7f7f7f7f7f7f7f7f7f7f7f5c7f7f7f7f8080808080808080808080808080808080808080808080998080807f7f7f75035f59586779b618f880833580e58080808080808080808080808080808080809f80808080808080807f507f7f4f747f087f8080807f7fee7f7f807f7afd7f7108d78e807f7f217f7f3f7f128f8080ad808080808080ebde04baeda1b9cba78080808080808080808080808080808080809580808080808080808080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f9c9ba3a9ae99a394bc8c8880b7a197bcc8da808080808080808080253c4943545946575e80808080808080808080809480ce0180d8f68080808080808080807b7521414600f3ec9380808080808080808019044b261c48582e6f46547944737f46707b4a6b7f497f7f085d7f7f7f7f7f7f7f7f7a7faefa1b8082d8808080c0dd08a3a9a8c299a70a0200e5fbfebbd7dbaf8092828092808080808080ac8080d38080305d7f38427a0e255c7f7f7f7f7f7f7f7f7f22112bf41837dfe3ecd28080a580808080807f7f7f7f7f7f7f7f7fc0fe20afdc08c5d800809b92a1a78e80,
      4096'h80807f4d2f222700e3d6dcfdee1d371649685d7a808087808080808080a2b9c680808c808080ed114b99f34085ab068080a880808080808080808080808080808080808080808080808080024c89070880808080808080808080808080baa980cf94808080aebcb78080808080808080808080808080808080808080808080807f727f7f7f7f7f7f7fc8a1b9d8ddd1cfd3bf80af80e6f8c09aaa803b124379426a7f757f80808080808080808080b384bee4b68080807f7f7f7f7f7f7f7f7f0afc0b472f4c7f6a7e7f7f7f6f7f7f0f24277f7f7f7f7f7f7f7f7ff4eee902f2e602f5e8808080b7fda380a8807f7f7f757f7f1245577f7f7f7f5b7f7f7f7f7f7f7f677f7fda3d55a5a2808080808080808cbe80ab05d880808015200902d6fbb9a0bc80808082c3828080808083c2808080808080808080808080808080ebd10111d71226083c7f6b7f3f3846cce825112d510e2d41f6fff6b9b1c4b6bcbe8c9e885a2b5a411b4d6d3b787f7f7f7f407f7f7f7f808080a4c8948084808080808080808080807f7f7f7f627f7f7f7fe8490eab02ed8080807f7f7f1c637f9bf024808080808080808080ae8080e58080fd80807f7f7f7f7f7f7f7f7f8080808080808080800b7f7f7f7f7f7f7f7fd68080428b9a34808880a9d6ab267f497f7f808080808080808080808080808080808080cb988f0ccfcad480807f7f7f7f6b7f,
      4096'h7f7b7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f8091f3bdabfbfbe7597f2eba7f7f157f7f5fc7808020bd914f1d2d46ec6e7f407a7f5f7f8080808080808080804d407f7f7f7f7f7f7f7f677f7f7f7f7f7f7f80808080808080808095be5fa3f77ff1307f7f6e7f61497f7f706f808080a14c228f808022a2ae1098b1de80967f7f7f7f7f7f7f7f7f7f7b7f7f577f7f7f7f8080808080808080808080800101c090a38062b3837fef9f7ff71680927f8080248080497f7f7f7f7f7f7f7f7f8080808c958080808061d5994918a5deb280808080808080808080d58880e3b492ae8080808080808080808080808f7da7d17f80a67f58126415065a08ec5e80802b8080f68080768280d3c1815a5a9c5dcf8080e78da963a4dd80802c808037a7807f80f87fb4ac7f17717f848081a080d846dd688080808080808080808080808080808080808080808080c28096ba1d80270780011883757f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7fcb2c7f08fe7f4b2d7f2bf7d97f7b60753d338b8080e68080e080808c8080a2d54194a91d3380c8f480810980a65d75777f7f7f7f7f7f7f577f7f7f7f7f7f7f808080808080808080a1de7ff3367fcf367f7f7f7f7f7f7f7f7f7f80808080a280808080be830abd8028ee80407f7f7f7f517f7f7f7f7f187f7f1c,
      4096'h7f7f277f1cb04cdd80f612801c808080809c8b80808076da0f7f66297f4e272ba9231a841412abfc38ef7f0ca37b10ce608080808080808080807f7f7f7f7a7f7f7f7f7f7f7f7f7f7f7f7f7f12a857db803a55e67ffb03f7602950e902fd80804d80ac7f80c37f28fe7f41597f7f677f8080808080808080808080808080808080807f7f5380808080808080bd808080808080808f7f8080808080808080808080808080808080808080808080808080b1808080808080808080808080808080808080808080808080807f7f7f7f7f7f6c656651557fdbed1f8080998080808080808080808080858080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7fd18f8080217f80807f8080807f7f7f7f7f7f7f7f7f8080801349808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7fc57f7f8080808080808080807f7f7f80917f8080038080378080808080808080e88080808080808080808080808080807f7f7f7f7f7f7f7f7f801267808080808080808080808082808d94767f7f7f7f7f8080b77f7f7fb97f7f80807f8014248085d28080808080a28080808080807f7f7f7f7f7f7f7f7f808080808080808080d6e40498a9cd8080808080808080808080808080808080808080808080e880808080808080807f80808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080,
      4096'h80808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808680800e8080cb80a17f7f7f7f7f7f7f7f7f7f7f7f7f7f7f6d5c7f7f7f7f7f7f7f7f7f7feb80f5808080808089dde6d02ca3801788877f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f808080d33b938094807f7f7f7f7f7f7f7f7f1180e67fc17b7f6b7f808080808080808080a2802a80fbca80808f8080808080808080807f7f7f7f7f7f7f7f7f80808080808080808080808083808080808080808080808080808073517f4b586566266e7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f80808080808080808004e986062ad980bf807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f80808080809e808080808080808080808080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000010100010101000000000000000000000000010101010001000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000,
      4096'h000000000000000000000000000000000000000000000000fffffffffffffefefe000000000000000000010101010001000000000000000000000000000000000000ffff00000000000000000000000000000000000000000000000000000000000101000001000000000000000000ff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001a1a141317100d0b06f1fbf1f906fff604fbe9efedeffaf6e7f3ec141a111314120b0e08f5fbf5fa03fdeefbf4ff0300ff05fef6faf9dadbd8d7d9d6cdd6d1ebf1f2f3fbfaf3f3f000fdfffbfafbfefdfef9fafa00fe00000201f3f3f400fefdfffbf6faf7f8fdfcfcfd00fdf8fdf8fcfffbfbfbf6f0f3f1e9f4eee1e8e6140e0b140e09261e11eeeef0ecedebf4f2f3f5eae6f3eee7f2f0ecfff8f10800f70b03fb1013140c0f0f0d1012d6d7c7e1e5d5dcdecf0904070a0d070807001711180e0b1415101806040401fe01fafbfafdf8f0f5f6efeae4df0f110e10110b0508030b0a08080606050503bec0bac9cbc5c8ccc5f3fbfdf1f7f6e8ececfe0302020201f3f8f701000301000204030303faf805faf8fff9f7e7eef1ebf0f2ecf0f2f6f9f8f7f8f8f8f5f609050806070509060a09050801ff04050103fafcfb0203fffcfffdf3f4f9f3f5f6f6f8f809090b0301030a070cfefd,
      4096'hf4fc00f5eff1ee090c1305070dfd0407808080808080808080808080808080808080857f7fa67f7f80cfc1808080808080808080ba7f682e7f7f8062c4dffcbb918682808080808080808080808080808080808080808080808080898080bb80aff1f1c32a53422ae7f1012a9b7f7f66025f002b08267f567f7f7f7f8080808080808080807f7f7f127e688080807f7f7f7f7f7f7f7f7f808082e3d0e93ef45b7f7f7f7f7f7f28743b7f7f7f7f7f7f7f7f7fcdd1acbddcc3b6b29c80b780be4cfc8080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f1c7f7f808080808080808080647f7f047f348080807f7f7f7f7f7ffb1c1e8080808080808080808080d9808080808080808080808080808080808080888080a595d17f777f7f6154ecc180ae367f992f7f80c9e37f446448184ae5b7923bf45047267f59577f7f4c7f7f647f7f797f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f9e7f7f8011738080807f7f7f7a7f7f80bc25ca7f7f797f7f7f7f7f7f7f7f7f7f347f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808084cad17f7f7f7f7f7f7f7f7f7f7f809c80807ffc807f487f7f7f7f7f7f097f7cbd7f048026808080808080808080808080808080808080808080807f7f7fbe7f7f80047fec3280aab380f680808080808080808080807f,
      4096'h7f7fa4e468808080808080808080808080da80808080808080808080808080808080807f7f7f7f7f7f7f7f7fba80808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f808080808080808080af3b058085808080807f7f7f7f7f367f7f5280fb7f800b7f7f7f7f7f7f807ffe801e80808080808080808080808080808080808080808080808080808080807f7fc57f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f294349fdf6f1808080808080b780cd808080fe7a7f48747f80abc3d0deeabf02f380808080bbb080df968080808080c08080808080807f7f7f6c7f61809b808080808080808080807f7f7f7f7f7f7f7f7f1afe0c00e30374f32d808080addd8080808054de0f2dcbfa95aecf80808080808080808080808080808080808080ac3a80ef078080827f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7b7f7f98bed1ea1251e8fafd6bfe2723dd46ffafd9808080f715e0d0e9be257f7f287f7fa4415122a77fc480369780327f7f7f427f7ff8757f8089eb80c0d68080808080a110427f4d717fc9800a9780a880808080808080a5808080808080808080808080808080808080808080807f097f3fce6d7f617f7f7f7f407f7f853c7f83e16bf9737f9f3273,
      4096'h8080808080808080807f777f7f497f7f7f7f7f7f7f7f047f7f7d7f808080808080808080e99e0d03b2fbbd80b97f7f7f7f7f7f7f7f7f9ffa16b7457f808ece7e7f7f4d7f7fd1457fd7dbd3ebe9cad8e2c5b8bbbacec1b5c1dbc792809b8b8b808e9c8096aca0b9c69fb2d2a3999d83998b86838c87a0a5bd95919e848c88b8d8b6b3ccafa6cdb785a99dba8380808080090f1409160d0a0e18808080808080808080130400fcececf2eaeef9e6f6e5e1eae8e3de020d040b1412161218654e514c423d4b3d40808080808080808080352e352e22322d2f2b8080808080808080808080808080808080808080808080808080806c624f1913200517258080808080808080808080808080808080808080808080808080808080808080808080801f25373c51603f4e658080808080808080804b3e42211f26220f17808080808080808080dad7d3dce6d8dbd8d5eaefe8eaeff7f4fbf4d1bf80d9c5809b908080808080808080808080808080808080808003f90c02f9030a0610f1edfae9e8f1eff3f9150d1a140515fdfd0a808080808080808080fffe03020600100914c9e1cdcce9c9a2e8ca8080808080808080807f7f7f7f7f7f7f7f7fd7e5f5d7fa04c7d3f3d4ddf2e305fdc4e9dd7f7f7f7f7f7f7f7f7fff2d36034451e40a267f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7fc3b5b9c8c0bea29b8f3c38423140362a3b,
      4096'h3f8080808080808080802d2032190f120c0209100916fd04fbf6f1faadc5bbcaebdfccced6030009f6eafbeae4f08080808080808080802329321c1f27171a1080808080a790809bac8080808080808080808080808080808080809aabb4a5aaaf94a2a4808080808080808080808080808080808080808080808080808080808080808080808080dcd1c6d2d0d0a6af97808080808080808080161008fdf9090b06fd8080808080808080808692979fa0ae8e95a2f6f5f1f1f7fbebfceb80eebc809680808080808080808080808080808080808080808080e6e9e5e9e6dfe9e2de372b2e3b37302b313206030e040002f8f9fa8080808080808080800b0d0f1a19200d1c0d80808080ba8080ea8f8080808080808080807f7f7f7f7f7f7f457f7f487f7f7f7f7f747f8080b18080808080807f7f7f7f5b7feb8078808c7f8080458080807f7f7f7f737f0ae2608080808080808080807f7f7f7f7f7f7f567f6cf77f7f7f7f7f7f7f7f697f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f497f7f277f8080808080808080807f7f7f7f7f7f7f4d7f80016d808080808080808080da808015cb868080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f80808080bf80808080808080808080808080be6fc37f7f7f9d7fd47f7f7f7f7f7f7f,
      1024'h7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f143e3cdb37c59ebd808080ba80bd3ff11c8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f247f7f457f7f7f7f7f7f7f7f7f7f808080808080808080808080808080808080
    }),
    .CHANNEL_BETAS(256'h2bf52e5c70b46f6057d43909620134dd72aa7a8557f7294f59d471266f5a3f9a),
    .CHANNEL_THRESHOLDS(256'h0240023a01e701ef01ed0220015b021b0240023301f1025b020e0125012801f6),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h0000),
    .ADAPTATION_DURATION(16'h0000)
  ) actor_final_fuse_standard (
    .clk,
    .reset,
    .in_valid(e_51_valid),
    .in_ready(e_51_ready),
    .in_payload(e_51_payload),
    .in_completion(e_51_completion),
    .in_bin_tag(e_51_bin_tag),
    .out_valid(n_final_fuse_standard_valid),
    .out_ready(n_final_fuse_standard_ready),
    .out_payload(n_final_fuse_standard_payload),
    .out_completion(n_final_fuse_standard_completion),
    .out_bin_tag(n_final_fuse_standard_bin_tag),
    .actor_error_o(error_actor_final_fuse_standard),
    .initialization_done_o(initialized_actor_final_fuse_standard)
  );
  logic error_tag_detail1_residual_or;
  logic error_union_detail1_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_detail1_residual_or (
    .clk,
    .reset,
    .in0_valid(e_3_valid),
    .in0_ready(e_3_ready),
    .in0_payload(e_3_payload),
    .in0_completion(e_3_completion),
    .in0_bin_tag(e_3_bin_tag),
    .in1_valid(e_4_valid),
    .in1_ready(e_4_ready),
    .in1_payload(e_4_payload),
    .in1_completion(e_4_completion),
    .in1_bin_tag(e_4_bin_tag),
    .out_valid(n_detail1_residual_or_valid),
    .out_ready(n_detail1_residual_or_ready),
    .out_payload(n_detail1_residual_or_payload),
    .out_completion(n_detail1_residual_or_completion),
    .out_bin_tag(n_detail1_residual_or_bin_tag),
    .overflow_o(error_union_detail1_residual_or),
    .tag_mismatch_o(error_tag_detail1_residual_or)
  );
  logic error_tag_enc1_residual_or;
  logic error_union_enc1_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc1_residual_or (
    .clk,
    .reset,
    .in0_valid(e_6_valid),
    .in0_ready(e_6_ready),
    .in0_payload(e_6_payload),
    .in0_completion(e_6_completion),
    .in0_bin_tag(e_6_bin_tag),
    .in1_valid(e_7_valid),
    .in1_ready(e_7_ready),
    .in1_payload(e_7_payload),
    .in1_completion(e_7_completion),
    .in1_bin_tag(e_7_bin_tag),
    .out_valid(n_enc1_residual_or_valid),
    .out_ready(n_enc1_residual_or_ready),
    .out_payload(n_enc1_residual_or_payload),
    .out_completion(n_enc1_residual_or_completion),
    .out_bin_tag(n_enc1_residual_or_bin_tag),
    .overflow_o(error_union_enc1_residual_or),
    .tag_mismatch_o(error_tag_enc1_residual_or)
  );
  logic error_tag_enc1_extra_residual_or;
  logic error_union_enc1_extra_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc1_extra_residual_or (
    .clk,
    .reset,
    .in0_valid(e_9_valid),
    .in0_ready(e_9_ready),
    .in0_payload(e_9_payload),
    .in0_completion(e_9_completion),
    .in0_bin_tag(e_9_bin_tag),
    .in1_valid(e_11_valid),
    .in1_ready(e_11_ready),
    .in1_payload(e_11_payload),
    .in1_completion(e_11_completion),
    .in1_bin_tag(e_11_bin_tag),
    .out_valid(n_enc1_extra_residual_or_valid),
    .out_ready(n_enc1_extra_residual_or_ready),
    .out_payload(n_enc1_extra_residual_or_payload),
    .out_completion(n_enc1_extra_residual_or_completion),
    .out_bin_tag(n_enc1_extra_residual_or_bin_tag),
    .overflow_o(error_union_enc1_extra_residual_or),
    .tag_mismatch_o(error_tag_enc1_extra_residual_or)
  );
  logic error_tag_enc2_residual_or;
  logic error_union_enc2_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc2_residual_or (
    .clk,
    .reset,
    .in0_valid(e_15_valid),
    .in0_ready(e_15_ready),
    .in0_payload(e_15_payload),
    .in0_completion(e_15_completion),
    .in0_bin_tag(e_15_bin_tag),
    .in1_valid(e_17_valid),
    .in1_ready(e_17_ready),
    .in1_payload(e_17_payload),
    .in1_completion(e_17_completion),
    .in1_bin_tag(e_17_bin_tag),
    .out_valid(n_enc2_residual_or_valid),
    .out_ready(n_enc2_residual_or_ready),
    .out_payload(n_enc2_residual_or_payload),
    .out_completion(n_enc2_residual_or_completion),
    .out_bin_tag(n_enc2_residual_or_bin_tag),
    .overflow_o(error_union_enc2_residual_or),
    .tag_mismatch_o(error_tag_enc2_residual_or)
  );
  logic error_tag_enc2_extra_residual_or;
  logic error_union_enc2_extra_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc2_extra_residual_or (
    .clk,
    .reset,
    .in0_valid(e_19_valid),
    .in0_ready(e_19_ready),
    .in0_payload(e_19_payload),
    .in0_completion(e_19_completion),
    .in0_bin_tag(e_19_bin_tag),
    .in1_valid(e_21_valid),
    .in1_ready(e_21_ready),
    .in1_payload(e_21_payload),
    .in1_completion(e_21_completion),
    .in1_bin_tag(e_21_bin_tag),
    .out_valid(n_enc2_extra_residual_or_valid),
    .out_ready(n_enc2_extra_residual_or_ready),
    .out_payload(n_enc2_extra_residual_or_payload),
    .out_completion(n_enc2_extra_residual_or_completion),
    .out_bin_tag(n_enc2_extra_residual_or_bin_tag),
    .overflow_o(error_union_enc2_extra_residual_or),
    .tag_mismatch_o(error_tag_enc2_extra_residual_or)
  );
  logic error_tag_enc3_residual_or;
  logic error_union_enc3_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc3_residual_or (
    .clk,
    .reset,
    .in0_valid(e_26_valid),
    .in0_ready(e_26_ready),
    .in0_payload(e_26_payload),
    .in0_completion(e_26_completion),
    .in0_bin_tag(e_26_bin_tag),
    .in1_valid(e_28_valid),
    .in1_ready(e_28_ready),
    .in1_payload(e_28_payload),
    .in1_completion(e_28_completion),
    .in1_bin_tag(e_28_bin_tag),
    .out_valid(n_enc3_residual_or_valid),
    .out_ready(n_enc3_residual_or_ready),
    .out_payload(n_enc3_residual_or_payload),
    .out_completion(n_enc3_residual_or_completion),
    .out_bin_tag(n_enc3_residual_or_bin_tag),
    .overflow_o(error_union_enc3_residual_or),
    .tag_mismatch_o(error_tag_enc3_residual_or)
  );
  logic error_tag_enc3_extra_residual_or;
  logic error_union_enc3_extra_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_enc3_extra_residual_or (
    .clk,
    .reset,
    .in0_valid(e_30_valid),
    .in0_ready(e_30_ready),
    .in0_payload(e_30_payload),
    .in0_completion(e_30_completion),
    .in0_bin_tag(e_30_bin_tag),
    .in1_valid(e_32_valid),
    .in1_ready(e_32_ready),
    .in1_payload(e_32_payload),
    .in1_completion(e_32_completion),
    .in1_bin_tag(e_32_bin_tag),
    .out_valid(n_enc3_extra_residual_or_valid),
    .out_ready(n_enc3_extra_residual_or_ready),
    .out_payload(n_enc3_extra_residual_or_payload),
    .out_completion(n_enc3_extra_residual_or_completion),
    .out_bin_tag(n_enc3_extra_residual_or_bin_tag),
    .overflow_o(error_union_enc3_extra_residual_or),
    .tag_mismatch_o(error_tag_enc3_extra_residual_or)
  );
  logic error_tag_context1_residual_or;
  logic error_union_context1_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_context1_residual_or (
    .clk,
    .reset,
    .in0_valid(e_34_valid),
    .in0_ready(e_34_ready),
    .in0_payload(e_34_payload),
    .in0_completion(e_34_completion),
    .in0_bin_tag(e_34_bin_tag),
    .in1_valid(e_36_valid),
    .in1_ready(e_36_ready),
    .in1_payload(e_36_payload),
    .in1_completion(e_36_completion),
    .in1_bin_tag(e_36_bin_tag),
    .out_valid(n_context1_residual_or_valid),
    .out_ready(n_context1_residual_or_ready),
    .out_payload(n_context1_residual_or_payload),
    .out_completion(n_context1_residual_or_completion),
    .out_bin_tag(n_context1_residual_or_bin_tag),
    .overflow_o(error_union_context1_residual_or),
    .tag_mismatch_o(error_tag_context1_residual_or)
  );
  logic error_tag_context2_residual_or;
  logic error_union_context2_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS), .USE_STATE_MACRO(USE_STATE_MACRO)) union_context2_residual_or (
    .clk,
    .reset,
    .in0_valid(e_38_valid),
    .in0_ready(e_38_ready),
    .in0_payload(e_38_payload),
    .in0_completion(e_38_completion),
    .in0_bin_tag(e_38_bin_tag),
    .in1_valid(e_40_valid),
    .in1_ready(e_40_ready),
    .in1_payload(e_40_payload),
    .in1_completion(e_40_completion),
    .in1_bin_tag(e_40_bin_tag),
    .out_valid(n_context2_residual_or_valid),
    .out_ready(n_context2_residual_or_ready),
    .out_payload(n_context2_residual_or_payload),
    .out_completion(n_context2_residual_or_completion),
    .out_bin_tag(n_context2_residual_or_bin_tag),
    .overflow_o(error_union_context2_residual_or),
    .tag_mismatch_o(error_tag_context2_residual_or)
  );
  event_upsample2x upsample_project3_upsample2x (
    .clk,
    .reset,
    .in_valid(e_42_valid),
    .in_ready(e_42_ready),
    .in_payload(e_42_payload),
    .in_completion(e_42_completion),
    .in_bin_tag(e_42_bin_tag),
    .out_valid(n_project3_upsample2x_valid),
    .out_ready(n_project3_upsample2x_ready),
    .out_payload(n_project3_upsample2x_payload),
    .out_completion(n_project3_upsample2x_completion),
    .out_bin_tag(n_project3_upsample2x_bin_tag),
    .coordinate_overflow_o()
  );
  logic m_decoder2_concat_0_valid;
  logic m_decoder2_concat_0_ready;
  logic [PAYLOAD_WIDTH-1:0] m_decoder2_concat_0_payload;
  logic m_decoder2_concat_0_completion;
  logic [TAG_WIDTH-1:0] m_decoder2_concat_0_bin_tag;
  logic error_offset_decoder2_concat_0;
  event_channel_offset #(.CHANNEL_OFFSET(64)) offset_decoder2_concat_0 (
    .in_valid(e_23_valid),
    .in_ready(e_23_ready),
    .in_payload(e_23_payload),
    .in_completion(e_23_completion),
    .in_bin_tag(e_23_bin_tag),
    .out_valid(m_decoder2_concat_0_valid),
    .out_ready(m_decoder2_concat_0_ready),
    .out_payload(m_decoder2_concat_0_payload),
    .out_completion(m_decoder2_concat_0_completion),
    .out_bin_tag(m_decoder2_concat_0_bin_tag),
    .channel_overflow_o(error_offset_decoder2_concat_0)
  );
  logic m_decoder2_concat_1_valid;
  logic m_decoder2_concat_1_ready;
  logic [PAYLOAD_WIDTH-1:0] m_decoder2_concat_1_payload;
  logic m_decoder2_concat_1_completion;
  logic [TAG_WIDTH-1:0] m_decoder2_concat_1_bin_tag;
  logic error_offset_decoder2_concat_1;
  event_channel_offset #(.CHANNEL_OFFSET(0)) offset_decoder2_concat_1 (
    .in_valid(e_43_valid),
    .in_ready(e_43_ready),
    .in_payload(e_43_payload),
    .in_completion(e_43_completion),
    .in_bin_tag(e_43_bin_tag),
    .out_valid(m_decoder2_concat_1_valid),
    .out_ready(m_decoder2_concat_1_ready),
    .out_payload(m_decoder2_concat_1_payload),
    .out_completion(m_decoder2_concat_1_completion),
    .out_bin_tag(m_decoder2_concat_1_bin_tag),
    .channel_overflow_o(error_offset_decoder2_concat_1)
  );
  logic error_tag_decoder2_concat;
  event_join2 join_decoder2_concat (
    .clk,
    .reset,
    .in0_valid(m_decoder2_concat_0_valid),
    .in0_ready(m_decoder2_concat_0_ready),
    .in0_payload(m_decoder2_concat_0_payload),
    .in0_completion(m_decoder2_concat_0_completion),
    .in0_bin_tag(m_decoder2_concat_0_bin_tag),
    .in1_valid(m_decoder2_concat_1_valid),
    .in1_ready(m_decoder2_concat_1_ready),
    .in1_payload(m_decoder2_concat_1_payload),
    .in1_completion(m_decoder2_concat_1_completion),
    .in1_bin_tag(m_decoder2_concat_1_bin_tag),
    .out_valid(n_decoder2_concat_valid),
    .out_ready(n_decoder2_concat_ready),
    .out_payload(n_decoder2_concat_payload),
    .out_completion(n_decoder2_concat_completion),
    .out_bin_tag(n_decoder2_concat_bin_tag),
    .tag_mismatch_o(error_tag_decoder2_concat)
  );
  event_upsample2x upsample_project2_upsample2x (
    .clk,
    .reset,
    .in_valid(e_46_valid),
    .in_ready(e_46_ready),
    .in_payload(e_46_payload),
    .in_completion(e_46_completion),
    .in_bin_tag(e_46_bin_tag),
    .out_valid(n_project2_upsample2x_valid),
    .out_ready(n_project2_upsample2x_ready),
    .out_payload(n_project2_upsample2x_payload),
    .out_completion(n_project2_upsample2x_completion),
    .out_bin_tag(n_project2_upsample2x_bin_tag),
    .coordinate_overflow_o()
  );
  logic error_tag_semantic_half_multiplicity_sum;
  event_join2 join_semantic_half_multiplicity_sum (
    .clk,
    .reset,
    .in0_valid(e_13_valid),
    .in0_ready(e_13_ready),
    .in0_payload(e_13_payload),
    .in0_completion(e_13_completion),
    .in0_bin_tag(e_13_bin_tag),
    .in1_valid(e_47_valid),
    .in1_ready(e_47_ready),
    .in1_payload(e_47_payload),
    .in1_completion(e_47_completion),
    .in1_bin_tag(e_47_bin_tag),
    .out_valid(n_semantic_half_multiplicity_sum_valid),
    .out_ready(n_semantic_half_multiplicity_sum_ready),
    .out_payload(n_semantic_half_multiplicity_sum_payload),
    .out_completion(n_semantic_half_multiplicity_sum_completion),
    .out_bin_tag(n_semantic_half_multiplicity_sum_bin_tag),
    .tag_mismatch_o(error_tag_semantic_half_multiplicity_sum)
  );
  event_upsample2x upsample_semantic_native_upsample2x (
    .clk,
    .reset,
    .in_valid(e_48_valid),
    .in_ready(e_48_ready),
    .in_payload(e_48_payload),
    .in_completion(e_48_completion),
    .in_bin_tag(e_48_bin_tag),
    .out_valid(n_semantic_native_upsample2x_valid),
    .out_ready(n_semantic_native_upsample2x_ready),
    .out_payload(n_semantic_native_upsample2x_payload),
    .out_completion(n_semantic_native_upsample2x_completion),
    .out_bin_tag(n_semantic_native_upsample2x_bin_tag),
    .coordinate_overflow_o()
  );
  logic m_final_concat_0_valid;
  logic m_final_concat_0_ready;
  logic [PAYLOAD_WIDTH-1:0] m_final_concat_0_payload;
  logic m_final_concat_0_completion;
  logic [TAG_WIDTH-1:0] m_final_concat_0_bin_tag;
  logic error_offset_final_concat_0;
  event_channel_offset #(.CHANNEL_OFFSET(0)) offset_final_concat_0 (
    .in_valid(e_49_valid),
    .in_ready(e_49_ready),
    .in_payload(e_49_payload),
    .in_completion(e_49_completion),
    .in_bin_tag(e_49_bin_tag),
    .out_valid(m_final_concat_0_valid),
    .out_ready(m_final_concat_0_ready),
    .out_payload(m_final_concat_0_payload),
    .out_completion(m_final_concat_0_completion),
    .out_bin_tag(m_final_concat_0_bin_tag),
    .channel_overflow_o(error_offset_final_concat_0)
  );
  logic m_final_concat_1_valid;
  logic m_final_concat_1_ready;
  logic [PAYLOAD_WIDTH-1:0] m_final_concat_1_payload;
  logic m_final_concat_1_completion;
  logic [TAG_WIDTH-1:0] m_final_concat_1_bin_tag;
  logic error_offset_final_concat_1;
  event_channel_offset #(.CHANNEL_OFFSET(32)) offset_final_concat_1 (
    .in_valid(e_50_valid),
    .in_ready(e_50_ready),
    .in_payload(e_50_payload),
    .in_completion(e_50_completion),
    .in_bin_tag(e_50_bin_tag),
    .out_valid(m_final_concat_1_valid),
    .out_ready(m_final_concat_1_ready),
    .out_payload(m_final_concat_1_payload),
    .out_completion(m_final_concat_1_completion),
    .out_bin_tag(m_final_concat_1_bin_tag),
    .channel_overflow_o(error_offset_final_concat_1)
  );
  logic error_tag_final_concat;
  event_join2 join_final_concat (
    .clk,
    .reset,
    .in0_valid(m_final_concat_0_valid),
    .in0_ready(m_final_concat_0_ready),
    .in0_payload(m_final_concat_0_payload),
    .in0_completion(m_final_concat_0_completion),
    .in0_bin_tag(m_final_concat_0_bin_tag),
    .in1_valid(m_final_concat_1_valid),
    .in1_ready(m_final_concat_1_ready),
    .in1_payload(m_final_concat_1_payload),
    .in1_completion(m_final_concat_1_completion),
    .in1_bin_tag(m_final_concat_1_bin_tag),
    .out_valid(n_final_concat_valid),
    .out_ready(n_final_concat_ready),
    .out_payload(n_final_concat_payload),
    .out_completion(n_final_concat_completion),
    .out_bin_tag(n_final_concat_bin_tag),
    .tag_mismatch_o(error_tag_final_concat)
  );
  logic error_readout;
  logic initialized_readout;
  temporal_class_readout #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
    .INPUT_CHANNELS(16),
    .CLASS_COUNT(6),
    .OUTPUT_WIDTH(8),
    .OUTPUT_HEIGHT(8),
    .PREDICTION_BINS(10),
    .READOUT_WEIGHTS(768'h01f9faf4fcfe0710d3faf1030a04f5fff9fd04f6f4f1f3f2afebec06f9ea80f2051406fe040dfbfaf6fcf7f506fef80df50b00fc0102fcfcfaf7f90b02fdf4f7f701fff909110e0a04f8f700020a090aecf9fd09f1020105e50212f71209070d)
  ) temporal_readout (
    .clk,
    .reset,
    .in_valid(e_52_valid),
    .in_ready(e_52_ready),
    .in_payload(e_52_payload),
    .in_completion(e_52_completion),
    .in_bin_tag(e_52_bin_tag),
    .prediction_valid,
    .prediction_ready,
    .prediction_x_o,
    .prediction_y_o,
    .prediction_class_o,
    .frame_done_valid,
    .frame_done_ready,
    .frame_bin_tag_o,
    .address_error_o(error_readout),
    .initialization_done_o(initialized_readout)
  );
  assign all_memories_initialized = initialized_actor_detail_stem & initialized_actor_detail1_standard & initialized_actor_stem & initialized_actor_enc1_standard & initialized_actor_enc1_extra_depthwise & initialized_actor_enc1_extra_pointwise & initialized_actor_down2_standard & initialized_actor_enc2_depthwise & initialized_actor_enc2_pointwise & initialized_actor_enc2_extra_depthwise & initialized_actor_enc2_extra_pointwise & initialized_actor_down3_depthwise & initialized_actor_down3_pointwise & initialized_actor_enc3_depthwise & initialized_actor_enc3_pointwise & initialized_actor_enc3_extra_depthwise & initialized_actor_enc3_extra_pointwise & initialized_actor_context1_depthwise & initialized_actor_context1_pointwise & initialized_actor_context2_depthwise & initialized_actor_context2_pointwise & initialized_actor_project3 & initialized_actor_decoder2_fuse & initialized_actor_project2 & initialized_actor_final_fuse_standard & initialized_readout;
  assign fault_o = error_actor_detail_stem | error_actor_detail1_standard | error_actor_stem | error_actor_enc1_standard | error_actor_enc1_extra_depthwise | error_actor_enc1_extra_pointwise | error_actor_down2_standard | error_actor_enc2_depthwise | error_actor_enc2_pointwise | error_actor_enc2_extra_depthwise | error_actor_enc2_extra_pointwise | error_actor_down3_depthwise | error_actor_down3_pointwise | error_actor_enc3_depthwise | error_actor_enc3_pointwise | error_actor_enc3_extra_depthwise | error_actor_enc3_extra_pointwise | error_actor_context1_depthwise | error_actor_context1_pointwise | error_actor_context2_depthwise | error_actor_context2_pointwise | error_actor_project3 | error_actor_decoder2_fuse | error_actor_project2 | error_actor_final_fuse_standard | error_tag_detail1_residual_or | error_union_detail1_residual_or | error_tag_enc1_residual_or | error_union_enc1_residual_or | error_tag_enc1_extra_residual_or | error_union_enc1_extra_residual_or | error_tag_enc2_residual_or | error_union_enc2_residual_or | error_tag_enc2_extra_residual_or | error_union_enc2_extra_residual_or | error_tag_enc3_residual_or | error_union_enc3_residual_or | error_tag_enc3_extra_residual_or | error_union_enc3_extra_residual_or | error_tag_context1_residual_or | error_union_context1_residual_or | error_tag_context2_residual_or | error_union_context2_residual_or | error_offset_decoder2_concat_0 | error_offset_decoder2_concat_1 | error_tag_decoder2_concat | error_tag_semantic_half_multiplicity_sum | error_offset_final_concat_0 | error_offset_final_concat_1 | error_tag_final_concat | error_readout;
endmodule
