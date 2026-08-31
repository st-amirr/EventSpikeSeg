`timescale 1ns/1ps
// Generated file: do not hand edit. Source is model_spec.yaml graph + ROM images.
module eventspikeseg140k_dag_top #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer RESIDUAL_MAX_EVENTS = 64,
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
  logic e_0_valid;
  logic e_0_ready;
  logic [PAYLOAD_WIDTH-1:0] e_0_payload;
  logic e_0_completion;
  logic [TAG_WIDTH-1:0] e_0_bin_tag;
  logic e_1_valid;
  logic e_1_ready;
  logic [PAYLOAD_WIDTH-1:0] e_1_payload;
  logic e_1_completion;
  logic [TAG_WIDTH-1:0] e_1_bin_tag;
  logic e_2_valid;
  logic e_2_ready;
  logic [PAYLOAD_WIDTH-1:0] e_2_payload;
  logic e_2_completion;
  logic [TAG_WIDTH-1:0] e_2_bin_tag;
  logic e_3_valid;
  logic e_3_ready;
  logic [PAYLOAD_WIDTH-1:0] e_3_payload;
  logic e_3_completion;
  logic [TAG_WIDTH-1:0] e_3_bin_tag;
  logic e_4_valid;
  logic e_4_ready;
  logic [PAYLOAD_WIDTH-1:0] e_4_payload;
  logic e_4_completion;
  logic [TAG_WIDTH-1:0] e_4_bin_tag;
  logic e_5_valid;
  logic e_5_ready;
  logic [PAYLOAD_WIDTH-1:0] e_5_payload;
  logic e_5_completion;
  logic [TAG_WIDTH-1:0] e_5_bin_tag;
  logic e_6_valid;
  logic e_6_ready;
  logic [PAYLOAD_WIDTH-1:0] e_6_payload;
  logic e_6_completion;
  logic [TAG_WIDTH-1:0] e_6_bin_tag;
  logic e_7_valid;
  logic e_7_ready;
  logic [PAYLOAD_WIDTH-1:0] e_7_payload;
  logic e_7_completion;
  logic [TAG_WIDTH-1:0] e_7_bin_tag;
  logic e_8_valid;
  logic e_8_ready;
  logic [PAYLOAD_WIDTH-1:0] e_8_payload;
  logic e_8_completion;
  logic [TAG_WIDTH-1:0] e_8_bin_tag;
  logic e_9_valid;
  logic e_9_ready;
  logic [PAYLOAD_WIDTH-1:0] e_9_payload;
  logic e_9_completion;
  logic [TAG_WIDTH-1:0] e_9_bin_tag;
  logic e_10_valid;
  logic e_10_ready;
  logic [PAYLOAD_WIDTH-1:0] e_10_payload;
  logic e_10_completion;
  logic [TAG_WIDTH-1:0] e_10_bin_tag;
  logic e_11_valid;
  logic e_11_ready;
  logic [PAYLOAD_WIDTH-1:0] e_11_payload;
  logic e_11_completion;
  logic [TAG_WIDTH-1:0] e_11_bin_tag;
  logic e_12_valid;
  logic e_12_ready;
  logic [PAYLOAD_WIDTH-1:0] e_12_payload;
  logic e_12_completion;
  logic [TAG_WIDTH-1:0] e_12_bin_tag;
  logic e_13_valid;
  logic e_13_ready;
  logic [PAYLOAD_WIDTH-1:0] e_13_payload;
  logic e_13_completion;
  logic [TAG_WIDTH-1:0] e_13_bin_tag;
  logic e_14_valid;
  logic e_14_ready;
  logic [PAYLOAD_WIDTH-1:0] e_14_payload;
  logic e_14_completion;
  logic [TAG_WIDTH-1:0] e_14_bin_tag;
  logic e_15_valid;
  logic e_15_ready;
  logic [PAYLOAD_WIDTH-1:0] e_15_payload;
  logic e_15_completion;
  logic [TAG_WIDTH-1:0] e_15_bin_tag;
  logic e_16_valid;
  logic e_16_ready;
  logic [PAYLOAD_WIDTH-1:0] e_16_payload;
  logic e_16_completion;
  logic [TAG_WIDTH-1:0] e_16_bin_tag;
  logic e_17_valid;
  logic e_17_ready;
  logic [PAYLOAD_WIDTH-1:0] e_17_payload;
  logic e_17_completion;
  logic [TAG_WIDTH-1:0] e_17_bin_tag;
  logic e_18_valid;
  logic e_18_ready;
  logic [PAYLOAD_WIDTH-1:0] e_18_payload;
  logic e_18_completion;
  logic [TAG_WIDTH-1:0] e_18_bin_tag;
  logic e_19_valid;
  logic e_19_ready;
  logic [PAYLOAD_WIDTH-1:0] e_19_payload;
  logic e_19_completion;
  logic [TAG_WIDTH-1:0] e_19_bin_tag;
  logic e_20_valid;
  logic e_20_ready;
  logic [PAYLOAD_WIDTH-1:0] e_20_payload;
  logic e_20_completion;
  logic [TAG_WIDTH-1:0] e_20_bin_tag;
  logic e_21_valid;
  logic e_21_ready;
  logic [PAYLOAD_WIDTH-1:0] e_21_payload;
  logic e_21_completion;
  logic [TAG_WIDTH-1:0] e_21_bin_tag;
  logic e_22_valid;
  logic e_22_ready;
  logic [PAYLOAD_WIDTH-1:0] e_22_payload;
  logic e_22_completion;
  logic [TAG_WIDTH-1:0] e_22_bin_tag;
  logic e_23_valid;
  logic e_23_ready;
  logic [PAYLOAD_WIDTH-1:0] e_23_payload;
  logic e_23_completion;
  logic [TAG_WIDTH-1:0] e_23_bin_tag;
  logic e_24_valid;
  logic e_24_ready;
  logic [PAYLOAD_WIDTH-1:0] e_24_payload;
  logic e_24_completion;
  logic [TAG_WIDTH-1:0] e_24_bin_tag;
  logic e_25_valid;
  logic e_25_ready;
  logic [PAYLOAD_WIDTH-1:0] e_25_payload;
  logic e_25_completion;
  logic [TAG_WIDTH-1:0] e_25_bin_tag;
  logic e_26_valid;
  logic e_26_ready;
  logic [PAYLOAD_WIDTH-1:0] e_26_payload;
  logic e_26_completion;
  logic [TAG_WIDTH-1:0] e_26_bin_tag;
  logic e_27_valid;
  logic e_27_ready;
  logic [PAYLOAD_WIDTH-1:0] e_27_payload;
  logic e_27_completion;
  logic [TAG_WIDTH-1:0] e_27_bin_tag;
  logic e_28_valid;
  logic e_28_ready;
  logic [PAYLOAD_WIDTH-1:0] e_28_payload;
  logic e_28_completion;
  logic [TAG_WIDTH-1:0] e_28_bin_tag;
  logic e_29_valid;
  logic e_29_ready;
  logic [PAYLOAD_WIDTH-1:0] e_29_payload;
  logic e_29_completion;
  logic [TAG_WIDTH-1:0] e_29_bin_tag;
  logic e_30_valid;
  logic e_30_ready;
  logic [PAYLOAD_WIDTH-1:0] e_30_payload;
  logic e_30_completion;
  logic [TAG_WIDTH-1:0] e_30_bin_tag;
  logic e_31_valid;
  logic e_31_ready;
  logic [PAYLOAD_WIDTH-1:0] e_31_payload;
  logic e_31_completion;
  logic [TAG_WIDTH-1:0] e_31_bin_tag;
  logic e_32_valid;
  logic e_32_ready;
  logic [PAYLOAD_WIDTH-1:0] e_32_payload;
  logic e_32_completion;
  logic [TAG_WIDTH-1:0] e_32_bin_tag;
  logic e_33_valid;
  logic e_33_ready;
  logic [PAYLOAD_WIDTH-1:0] e_33_payload;
  logic e_33_completion;
  logic [TAG_WIDTH-1:0] e_33_bin_tag;
  logic e_34_valid;
  logic e_34_ready;
  logic [PAYLOAD_WIDTH-1:0] e_34_payload;
  logic e_34_completion;
  logic [TAG_WIDTH-1:0] e_34_bin_tag;
  logic e_35_valid;
  logic e_35_ready;
  logic [PAYLOAD_WIDTH-1:0] e_35_payload;
  logic e_35_completion;
  logic [TAG_WIDTH-1:0] e_35_bin_tag;
  logic e_36_valid;
  logic e_36_ready;
  logic [PAYLOAD_WIDTH-1:0] e_36_payload;
  logic e_36_completion;
  logic [TAG_WIDTH-1:0] e_36_bin_tag;
  logic e_37_valid;
  logic e_37_ready;
  logic [PAYLOAD_WIDTH-1:0] e_37_payload;
  logic e_37_completion;
  logic [TAG_WIDTH-1:0] e_37_bin_tag;
  logic e_38_valid;
  logic e_38_ready;
  logic [PAYLOAD_WIDTH-1:0] e_38_payload;
  logic e_38_completion;
  logic [TAG_WIDTH-1:0] e_38_bin_tag;
  logic e_39_valid;
  logic e_39_ready;
  logic [PAYLOAD_WIDTH-1:0] e_39_payload;
  logic e_39_completion;
  logic [TAG_WIDTH-1:0] e_39_bin_tag;
  logic e_40_valid;
  logic e_40_ready;
  logic [PAYLOAD_WIDTH-1:0] e_40_payload;
  logic e_40_completion;
  logic [TAG_WIDTH-1:0] e_40_bin_tag;
  logic e_41_valid;
  logic e_41_ready;
  logic [PAYLOAD_WIDTH-1:0] e_41_payload;
  logic e_41_completion;
  logic [TAG_WIDTH-1:0] e_41_bin_tag;
  logic e_42_valid;
  logic e_42_ready;
  logic [PAYLOAD_WIDTH-1:0] e_42_payload;
  logic e_42_completion;
  logic [TAG_WIDTH-1:0] e_42_bin_tag;
  logic e_43_valid;
  logic e_43_ready;
  logic [PAYLOAD_WIDTH-1:0] e_43_payload;
  logic e_43_completion;
  logic [TAG_WIDTH-1:0] e_43_bin_tag;
  logic e_44_valid;
  logic e_44_ready;
  logic [PAYLOAD_WIDTH-1:0] e_44_payload;
  logic e_44_completion;
  logic [TAG_WIDTH-1:0] e_44_bin_tag;
  logic e_45_valid;
  logic e_45_ready;
  logic [PAYLOAD_WIDTH-1:0] e_45_payload;
  logic e_45_completion;
  logic [TAG_WIDTH-1:0] e_45_bin_tag;
  logic e_46_valid;
  logic e_46_ready;
  logic [PAYLOAD_WIDTH-1:0] e_46_payload;
  logic e_46_completion;
  logic [TAG_WIDTH-1:0] e_46_bin_tag;
  logic e_47_valid;
  logic e_47_ready;
  logic [PAYLOAD_WIDTH-1:0] e_47_payload;
  logic e_47_completion;
  logic [TAG_WIDTH-1:0] e_47_bin_tag;
  logic e_48_valid;
  logic e_48_ready;
  logic [PAYLOAD_WIDTH-1:0] e_48_payload;
  logic e_48_completion;
  logic [TAG_WIDTH-1:0] e_48_bin_tag;
  logic e_49_valid;
  logic e_49_ready;
  logic [PAYLOAD_WIDTH-1:0] e_49_payload;
  logic e_49_completion;
  logic [TAG_WIDTH-1:0] e_49_bin_tag;
  logic e_50_valid;
  logic e_50_ready;
  logic [PAYLOAD_WIDTH-1:0] e_50_payload;
  logic e_50_completion;
  logic [TAG_WIDTH-1:0] e_50_bin_tag;
  logic e_51_valid;
  logic e_51_ready;
  logic [PAYLOAD_WIDTH-1:0] e_51_payload;
  logic e_51_completion;
  logic [TAG_WIDTH-1:0] e_51_bin_tag;
  logic e_52_valid;
  logic e_52_ready;
  logic [PAYLOAD_WIDTH-1:0] e_52_payload;
  logic e_52_completion;
  logic [TAG_WIDTH-1:0] e_52_bin_tag;
  event_fork2 fork_input (
    .clk,
    .reset,
    .in_valid(ingress_valid),
    .in_ready(ingress_ready),
    .in_payload(ingress_payload),
    .in_completion(ingress_completion),
    .in_bin_tag(ingress_bin_tag),
    .out0_valid(e_0_valid),
    .out0_ready(e_0_ready),
    .out0_payload(e_0_payload),
    .out0_completion(e_0_completion),
    .out0_bin_tag(e_0_bin_tag),
    .out1_valid(e_1_valid),
    .out1_ready(e_1_ready),
    .out1_payload(e_1_payload),
    .out1_completion(e_1_completion),
    .out1_bin_tag(e_1_bin_tag)
  );
  event_fork2 fork_detail_stem (
    .clk,
    .reset,
    .in_valid(n_detail_stem_valid),
    .in_ready(n_detail_stem_ready),
    .in_payload(n_detail_stem_payload),
    .in_completion(n_detail_stem_completion),
    .in_bin_tag(n_detail_stem_bin_tag),
    .out0_valid(e_2_valid),
    .out0_ready(e_2_ready),
    .out0_payload(e_2_payload),
    .out0_completion(e_2_completion),
    .out0_bin_tag(e_2_bin_tag),
    .out1_valid(e_3_valid),
    .out1_ready(e_3_ready),
    .out1_payload(e_3_payload),
    .out1_completion(e_3_completion),
    .out1_bin_tag(e_3_bin_tag)
  );
  assign e_4_valid = n_detail1_standard_valid;
  assign n_detail1_standard_ready = e_4_ready;
  assign e_4_payload = n_detail1_standard_payload;
  assign e_4_completion = n_detail1_standard_completion;
  assign e_4_bin_tag = n_detail1_standard_bin_tag;
  event_fork2 fork_stem (
    .clk,
    .reset,
    .in_valid(n_stem_valid),
    .in_ready(n_stem_ready),
    .in_payload(n_stem_payload),
    .in_completion(n_stem_completion),
    .in_bin_tag(n_stem_bin_tag),
    .out0_valid(e_5_valid),
    .out0_ready(e_5_ready),
    .out0_payload(e_5_payload),
    .out0_completion(e_5_completion),
    .out0_bin_tag(e_5_bin_tag),
    .out1_valid(e_6_valid),
    .out1_ready(e_6_ready),
    .out1_payload(e_6_payload),
    .out1_completion(e_6_completion),
    .out1_bin_tag(e_6_bin_tag)
  );
  assign e_7_valid = n_enc1_standard_valid;
  assign n_enc1_standard_ready = e_7_ready;
  assign e_7_payload = n_enc1_standard_payload;
  assign e_7_completion = n_enc1_standard_completion;
  assign e_7_bin_tag = n_enc1_standard_bin_tag;
  event_fork2 fork_enc1_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc1_residual_or_valid),
    .in_ready(n_enc1_residual_or_ready),
    .in_payload(n_enc1_residual_or_payload),
    .in_completion(n_enc1_residual_or_completion),
    .in_bin_tag(n_enc1_residual_or_bin_tag),
    .out0_valid(e_8_valid),
    .out0_ready(e_8_ready),
    .out0_payload(e_8_payload),
    .out0_completion(e_8_completion),
    .out0_bin_tag(e_8_bin_tag),
    .out1_valid(e_9_valid),
    .out1_ready(e_9_ready),
    .out1_payload(e_9_payload),
    .out1_completion(e_9_completion),
    .out1_bin_tag(e_9_bin_tag)
  );
  assign e_10_valid = n_enc1_extra_depthwise_valid;
  assign n_enc1_extra_depthwise_ready = e_10_ready;
  assign e_10_payload = n_enc1_extra_depthwise_payload;
  assign e_10_completion = n_enc1_extra_depthwise_completion;
  assign e_10_bin_tag = n_enc1_extra_depthwise_bin_tag;
  assign e_11_valid = n_enc1_extra_pointwise_valid;
  assign n_enc1_extra_pointwise_ready = e_11_ready;
  assign e_11_payload = n_enc1_extra_pointwise_payload;
  assign e_11_completion = n_enc1_extra_pointwise_completion;
  assign e_11_bin_tag = n_enc1_extra_pointwise_bin_tag;
  event_fork2 fork_enc1_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc1_extra_residual_or_valid),
    .in_ready(n_enc1_extra_residual_or_ready),
    .in_payload(n_enc1_extra_residual_or_payload),
    .in_completion(n_enc1_extra_residual_or_completion),
    .in_bin_tag(n_enc1_extra_residual_or_bin_tag),
    .out0_valid(e_12_valid),
    .out0_ready(e_12_ready),
    .out0_payload(e_12_payload),
    .out0_completion(e_12_completion),
    .out0_bin_tag(e_12_bin_tag),
    .out1_valid(e_13_valid),
    .out1_ready(e_13_ready),
    .out1_payload(e_13_payload),
    .out1_completion(e_13_completion),
    .out1_bin_tag(e_13_bin_tag)
  );
  event_fork2 fork_down2_standard (
    .clk,
    .reset,
    .in_valid(n_down2_standard_valid),
    .in_ready(n_down2_standard_ready),
    .in_payload(n_down2_standard_payload),
    .in_completion(n_down2_standard_completion),
    .in_bin_tag(n_down2_standard_bin_tag),
    .out0_valid(e_14_valid),
    .out0_ready(e_14_ready),
    .out0_payload(e_14_payload),
    .out0_completion(e_14_completion),
    .out0_bin_tag(e_14_bin_tag),
    .out1_valid(e_15_valid),
    .out1_ready(e_15_ready),
    .out1_payload(e_15_payload),
    .out1_completion(e_15_completion),
    .out1_bin_tag(e_15_bin_tag)
  );
  assign e_16_valid = n_enc2_depthwise_valid;
  assign n_enc2_depthwise_ready = e_16_ready;
  assign e_16_payload = n_enc2_depthwise_payload;
  assign e_16_completion = n_enc2_depthwise_completion;
  assign e_16_bin_tag = n_enc2_depthwise_bin_tag;
  assign e_17_valid = n_enc2_pointwise_valid;
  assign n_enc2_pointwise_ready = e_17_ready;
  assign e_17_payload = n_enc2_pointwise_payload;
  assign e_17_completion = n_enc2_pointwise_completion;
  assign e_17_bin_tag = n_enc2_pointwise_bin_tag;
  event_fork2 fork_enc2_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc2_residual_or_valid),
    .in_ready(n_enc2_residual_or_ready),
    .in_payload(n_enc2_residual_or_payload),
    .in_completion(n_enc2_residual_or_completion),
    .in_bin_tag(n_enc2_residual_or_bin_tag),
    .out0_valid(e_18_valid),
    .out0_ready(e_18_ready),
    .out0_payload(e_18_payload),
    .out0_completion(e_18_completion),
    .out0_bin_tag(e_18_bin_tag),
    .out1_valid(e_19_valid),
    .out1_ready(e_19_ready),
    .out1_payload(e_19_payload),
    .out1_completion(e_19_completion),
    .out1_bin_tag(e_19_bin_tag)
  );
  assign e_20_valid = n_enc2_extra_depthwise_valid;
  assign n_enc2_extra_depthwise_ready = e_20_ready;
  assign e_20_payload = n_enc2_extra_depthwise_payload;
  assign e_20_completion = n_enc2_extra_depthwise_completion;
  assign e_20_bin_tag = n_enc2_extra_depthwise_bin_tag;
  assign e_21_valid = n_enc2_extra_pointwise_valid;
  assign n_enc2_extra_pointwise_ready = e_21_ready;
  assign e_21_payload = n_enc2_extra_pointwise_payload;
  assign e_21_completion = n_enc2_extra_pointwise_completion;
  assign e_21_bin_tag = n_enc2_extra_pointwise_bin_tag;
  event_fork2 fork_enc2_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc2_extra_residual_or_valid),
    .in_ready(n_enc2_extra_residual_or_ready),
    .in_payload(n_enc2_extra_residual_or_payload),
    .in_completion(n_enc2_extra_residual_or_completion),
    .in_bin_tag(n_enc2_extra_residual_or_bin_tag),
    .out0_valid(e_22_valid),
    .out0_ready(e_22_ready),
    .out0_payload(e_22_payload),
    .out0_completion(e_22_completion),
    .out0_bin_tag(e_22_bin_tag),
    .out1_valid(e_23_valid),
    .out1_ready(e_23_ready),
    .out1_payload(e_23_payload),
    .out1_completion(e_23_completion),
    .out1_bin_tag(e_23_bin_tag)
  );
  assign e_24_valid = n_down3_depthwise_valid;
  assign n_down3_depthwise_ready = e_24_ready;
  assign e_24_payload = n_down3_depthwise_payload;
  assign e_24_completion = n_down3_depthwise_completion;
  assign e_24_bin_tag = n_down3_depthwise_bin_tag;
  event_fork2 fork_down3_pointwise (
    .clk,
    .reset,
    .in_valid(n_down3_pointwise_valid),
    .in_ready(n_down3_pointwise_ready),
    .in_payload(n_down3_pointwise_payload),
    .in_completion(n_down3_pointwise_completion),
    .in_bin_tag(n_down3_pointwise_bin_tag),
    .out0_valid(e_25_valid),
    .out0_ready(e_25_ready),
    .out0_payload(e_25_payload),
    .out0_completion(e_25_completion),
    .out0_bin_tag(e_25_bin_tag),
    .out1_valid(e_26_valid),
    .out1_ready(e_26_ready),
    .out1_payload(e_26_payload),
    .out1_completion(e_26_completion),
    .out1_bin_tag(e_26_bin_tag)
  );
  assign e_27_valid = n_enc3_depthwise_valid;
  assign n_enc3_depthwise_ready = e_27_ready;
  assign e_27_payload = n_enc3_depthwise_payload;
  assign e_27_completion = n_enc3_depthwise_completion;
  assign e_27_bin_tag = n_enc3_depthwise_bin_tag;
  assign e_28_valid = n_enc3_pointwise_valid;
  assign n_enc3_pointwise_ready = e_28_ready;
  assign e_28_payload = n_enc3_pointwise_payload;
  assign e_28_completion = n_enc3_pointwise_completion;
  assign e_28_bin_tag = n_enc3_pointwise_bin_tag;
  event_fork2 fork_enc3_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc3_residual_or_valid),
    .in_ready(n_enc3_residual_or_ready),
    .in_payload(n_enc3_residual_or_payload),
    .in_completion(n_enc3_residual_or_completion),
    .in_bin_tag(n_enc3_residual_or_bin_tag),
    .out0_valid(e_29_valid),
    .out0_ready(e_29_ready),
    .out0_payload(e_29_payload),
    .out0_completion(e_29_completion),
    .out0_bin_tag(e_29_bin_tag),
    .out1_valid(e_30_valid),
    .out1_ready(e_30_ready),
    .out1_payload(e_30_payload),
    .out1_completion(e_30_completion),
    .out1_bin_tag(e_30_bin_tag)
  );
  assign e_31_valid = n_enc3_extra_depthwise_valid;
  assign n_enc3_extra_depthwise_ready = e_31_ready;
  assign e_31_payload = n_enc3_extra_depthwise_payload;
  assign e_31_completion = n_enc3_extra_depthwise_completion;
  assign e_31_bin_tag = n_enc3_extra_depthwise_bin_tag;
  assign e_32_valid = n_enc3_extra_pointwise_valid;
  assign n_enc3_extra_pointwise_ready = e_32_ready;
  assign e_32_payload = n_enc3_extra_pointwise_payload;
  assign e_32_completion = n_enc3_extra_pointwise_completion;
  assign e_32_bin_tag = n_enc3_extra_pointwise_bin_tag;
  event_fork2 fork_enc3_extra_residual_or (
    .clk,
    .reset,
    .in_valid(n_enc3_extra_residual_or_valid),
    .in_ready(n_enc3_extra_residual_or_ready),
    .in_payload(n_enc3_extra_residual_or_payload),
    .in_completion(n_enc3_extra_residual_or_completion),
    .in_bin_tag(n_enc3_extra_residual_or_bin_tag),
    .out0_valid(e_33_valid),
    .out0_ready(e_33_ready),
    .out0_payload(e_33_payload),
    .out0_completion(e_33_completion),
    .out0_bin_tag(e_33_bin_tag),
    .out1_valid(e_34_valid),
    .out1_ready(e_34_ready),
    .out1_payload(e_34_payload),
    .out1_completion(e_34_completion),
    .out1_bin_tag(e_34_bin_tag)
  );
  assign e_35_valid = n_context1_depthwise_valid;
  assign n_context1_depthwise_ready = e_35_ready;
  assign e_35_payload = n_context1_depthwise_payload;
  assign e_35_completion = n_context1_depthwise_completion;
  assign e_35_bin_tag = n_context1_depthwise_bin_tag;
  assign e_36_valid = n_context1_pointwise_valid;
  assign n_context1_pointwise_ready = e_36_ready;
  assign e_36_payload = n_context1_pointwise_payload;
  assign e_36_completion = n_context1_pointwise_completion;
  assign e_36_bin_tag = n_context1_pointwise_bin_tag;
  event_fork2 fork_context1_residual_or (
    .clk,
    .reset,
    .in_valid(n_context1_residual_or_valid),
    .in_ready(n_context1_residual_or_ready),
    .in_payload(n_context1_residual_or_payload),
    .in_completion(n_context1_residual_or_completion),
    .in_bin_tag(n_context1_residual_or_bin_tag),
    .out0_valid(e_37_valid),
    .out0_ready(e_37_ready),
    .out0_payload(e_37_payload),
    .out0_completion(e_37_completion),
    .out0_bin_tag(e_37_bin_tag),
    .out1_valid(e_38_valid),
    .out1_ready(e_38_ready),
    .out1_payload(e_38_payload),
    .out1_completion(e_38_completion),
    .out1_bin_tag(e_38_bin_tag)
  );
  assign e_39_valid = n_context2_depthwise_valid;
  assign n_context2_depthwise_ready = e_39_ready;
  assign e_39_payload = n_context2_depthwise_payload;
  assign e_39_completion = n_context2_depthwise_completion;
  assign e_39_bin_tag = n_context2_depthwise_bin_tag;
  assign e_40_valid = n_context2_pointwise_valid;
  assign n_context2_pointwise_ready = e_40_ready;
  assign e_40_payload = n_context2_pointwise_payload;
  assign e_40_completion = n_context2_pointwise_completion;
  assign e_40_bin_tag = n_context2_pointwise_bin_tag;
  assign e_41_valid = n_context2_residual_or_valid;
  assign n_context2_residual_or_ready = e_41_ready;
  assign e_41_payload = n_context2_residual_or_payload;
  assign e_41_completion = n_context2_residual_or_completion;
  assign e_41_bin_tag = n_context2_residual_or_bin_tag;
  assign e_42_valid = n_project3_valid;
  assign n_project3_ready = e_42_ready;
  assign e_42_payload = n_project3_payload;
  assign e_42_completion = n_project3_completion;
  assign e_42_bin_tag = n_project3_bin_tag;
  assign e_43_valid = n_project3_upsample2x_valid;
  assign n_project3_upsample2x_ready = e_43_ready;
  assign e_43_payload = n_project3_upsample2x_payload;
  assign e_43_completion = n_project3_upsample2x_completion;
  assign e_43_bin_tag = n_project3_upsample2x_bin_tag;
  assign e_44_valid = n_decoder2_concat_valid;
  assign n_decoder2_concat_ready = e_44_ready;
  assign e_44_payload = n_decoder2_concat_payload;
  assign e_44_completion = n_decoder2_concat_completion;
  assign e_44_bin_tag = n_decoder2_concat_bin_tag;
  assign e_45_valid = n_decoder2_fuse_valid;
  assign n_decoder2_fuse_ready = e_45_ready;
  assign e_45_payload = n_decoder2_fuse_payload;
  assign e_45_completion = n_decoder2_fuse_completion;
  assign e_45_bin_tag = n_decoder2_fuse_bin_tag;
  assign e_46_valid = n_project2_valid;
  assign n_project2_ready = e_46_ready;
  assign e_46_payload = n_project2_payload;
  assign e_46_completion = n_project2_completion;
  assign e_46_bin_tag = n_project2_bin_tag;
  assign e_47_valid = n_project2_upsample2x_valid;
  assign n_project2_upsample2x_ready = e_47_ready;
  assign e_47_payload = n_project2_upsample2x_payload;
  assign e_47_completion = n_project2_upsample2x_completion;
  assign e_47_bin_tag = n_project2_upsample2x_bin_tag;
  assign e_48_valid = n_semantic_half_multiplicity_sum_valid;
  assign n_semantic_half_multiplicity_sum_ready = e_48_ready;
  assign e_48_payload = n_semantic_half_multiplicity_sum_payload;
  assign e_48_completion = n_semantic_half_multiplicity_sum_completion;
  assign e_48_bin_tag = n_semantic_half_multiplicity_sum_bin_tag;
  assign e_49_valid = n_semantic_native_upsample2x_valid;
  assign n_semantic_native_upsample2x_ready = e_49_ready;
  assign e_49_payload = n_semantic_native_upsample2x_payload;
  assign e_49_completion = n_semantic_native_upsample2x_completion;
  assign e_49_bin_tag = n_semantic_native_upsample2x_bin_tag;
  assign e_50_valid = n_detail1_residual_or_valid;
  assign n_detail1_residual_or_ready = e_50_ready;
  assign e_50_payload = n_detail1_residual_or_payload;
  assign e_50_completion = n_detail1_residual_or_completion;
  assign e_50_bin_tag = n_detail1_residual_or_bin_tag;
  assign e_51_valid = n_final_concat_valid;
  assign n_final_concat_ready = e_51_ready;
  assign e_51_payload = n_final_concat_payload;
  assign e_51_completion = n_final_concat_completion;
  assign e_51_bin_tag = n_final_concat_bin_tag;
  assign e_52_valid = n_final_fuse_standard_valid;
  assign n_final_fuse_standard_ready = e_52_ready;
  assign e_52_payload = n_final_fuse_standard_payload;
  assign e_52_completion = n_final_fuse_standard_completion;
  assign e_52_bin_tag = n_final_fuse_standard_bin_tag;
  logic error_actor_detail_stem;
  logic initialized_actor_detail_stem;
  streaming_channelized_plif_actor #(
    .USE_STATE_MACRO(USE_STATE_MACRO),
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
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .KERNEL_WEIGHTS(1152'h142ae81a3100182404f50681394a057f5022d280809280809c80807f7f7f36809b808080807f7f807f7f807f7f7f2e877f7f807f1c8002112b240e1817171f1718152d3b281e19117f7f807f7f807f2280807f7f80777f804c7f8080808080802141458080afcb11d428362d07010401fd0206020406030502fe0005020a8080808080ad8080da7f7f7f7f7f7ffe202b),
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
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .KERNEL_WEIGHTS({
      4096'h808080808080808080c1afbe1a0a07461e22727f7f7f5f7f7f7f7f8b808004929500b8aa7f7f7f7f707f7f7f7fa7ce9bfac8bdc2b7e2117f7f9b467f80807fbca7a92dddaa432602808080a0eca1cafcb0eaa19512aeed0b02f77b7f7f7f6a7f7f7f7f8080808a9d9eb9d2dd7f7f7f7f7f7f7f7f7fad86bbc0a792d29395808080808087808080b883adfeddef01334880809380809b9b808058294e36a5eb0eadf77f7f7f7f3b7f7f7f7faf80db8080b8aa95c07f7f7f7f7f7f7f7f7f808ec18080ca8080bd24197f36ff7f00f53f01ea46ea8049c1801c8080808080808080807fbf807f11137f197f7f7f7f7f7f7f7f7f7f878080bb80a1d380457f7f7f7f7f7f7f7f7f80808080dfc280800974577f7f7f7fea517fba808056cb396bd87f8080808080808080807f7fd03fd8803c96807f7f7f7f7f7f7f7f7fdd9b94808080a180807f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7d7f487a166b5ac4c0948080808080f18080908080c423242228c880808080b2807fe0837ff40f3c95fa52a787f6f0d0f97f7f7f7f7f7f7f7f7f808080808080808080466e7f7e7f7f7f7f7f80fc698080bf808080808080808080808080e980b29b8080d29fd57f7f7f7f7f157f7f6b808080808080808080507f7fde7f7fab7f7f8080808080808080807f7f7f7f7f7f7f7f7ffe8e80bc8080808f9a80808598a1948987,
      512'h80da9c91cdd3c115ceee7766587f7f425e715c8080808080808380807f7f7f7f727f7f677ff2f832dceab1ca80928080808080808080bcb2d495ea0dddc4cc0c
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
    .OUTPUT_WIDTH(320),
    .OUTPUT_HEIGHT(220),
    .KERNEL_WEIGHTS({
      4096'h8ba6a9d4b0fef601ededfb090f1000fb151513fc0e132af8dc808080808080968780c3d2d52d3d1418442b4c2afd6400f9ff332ec5140ec180042813809ce61676b4302dddd74b42328d80d5ffab30fa128821fdd4e580e50f58c34005f1cade362ac0b2b5fe021305e20ded1d2deb0df804192007061d172d263e3b45808080808090808f9f80809480808083809497808080808080ab7f7f32cda27f7f4fd98d7f7f7fdd80687f4cbf80d614258070bb80687f5fe79b7f53471f80145475b580fa250380808bc58080808080808080808080809829c28080dd808080808080808080808080808080808080808080808080808080808080808088ab9283919f9da48081fdf10e050df11e1f30151d19272043bcbfd7c290f1dceabdc813040e05f733201e1e11fd0a0a03fa56241518215526072c1f700ce3411246b2a5c6ed8f8080809e07212c3f0c24184f1105c0b7b8c1caa3809d8080808080949728311b1a1addd8bca9cbac80808080e6dbccd4c908182b3b181c46453a0c2b4b4226181236331c0edbdaf5dee59cacb5bda1aec8f5040fcee0ff0304f1f408060c02fd0c0a1dfef5000220261e02f4171715fdf6120407f4ea0a01feeae20a1013f1e70b5637417f7f0e180e5357d4dbf5fb17a4b4b2cbeb808fb6bedbf60b102b248080b2b0d58080809aa5a1c8ede704291940365480dce6f5f19cf319fff6c1f0,
      4096'he7e5eaf00ae2f6d1c8bfdfd6ccf2f605fbf30bda1c1100fc0502f419f722090ef71e0e1f082b4b737f7f7f7f7f7f7f18777f7f7f4a6d7f7f25120fc1a7b7c0f40a8080804a07a180806c451280807f2d0680807f7f308080522805000b251f11081efdf1f8050efcf6fb090bfef2ff0610a4b8fe110abebef3fdffd7cb0b0601cfc4160f16d1d3101e2706e0e5809af1e4dd2d89c78bbfc3bdaf80bf8eab93928d8080373b4b0e1b1618f62906fde9dccfecdce9dcd702d404fabba62e36350780fafdfde980461b2e1d9f7f4229f8a47f1316c3837f36f4cd807f4f04f59b1f12dd8880fd0adeb2801c2d2fcb807f7f7f80803c587f80804b7f7f80807f7f7fd1807f7f7fcb808080317f7fb1a669727fa880667d3f80801bfee980805056148080809a9b958394c4fe0b04040f2333463131103a4e42250939676e5b2cfff808fbf8e4dfe8eacde0cbd7e9eeead0b3e3fc22f40c666b2cf61154573ad9f7441649de083d1856e2f63c7f1db6a7f71937bcbf141e55ce06377f7feafa3f7f6ec3034d628089270609808030e1398091dde62280be132f2580d51c2a5725cf194450d683cb5141a88dcc15338080e8385a8080ba323980807f7f7f8080777f7f8080585f7f80807f7f7f80807f7f7f7f50e980837f5fe080927f462b80807f4ae180807f7f2a8080807f2280edcab08080424f29146c808095511cde80808286,
      4096'h80807f807f807f7f2080dc804b7e782080807fcbab80808080fb160a343674413d682f21fd0d0a2ff1b5a5808080a99f9c8a8080dcb4b0a0bf213af3e8cfb993e2a4e7ceedb7808c80b0c19a80b2032d5480bf092b48808fe9100e80b0fb21289bb5022d3b8080d9111a94b92e323f0d28567777dad731446e8c9fd5020e80807f7f6e8080a77d7f8080a9577f808014667f8080187f7f7f7f6cba807f7f6080807f7f7fc1807f7f4a97807f7f3c8080a4d0b7f0d0a3c81ce0c2b7ddc1f3e4bcb1c7a5ac81b395929e2d7353604f2a44e8fa200af31527fbe8fef505e7d4fc141c298080b8a48fd0ef140b093412160a0c2002f7030191d5cbad928080938080afbf06eda1261e1605011c0d102015dde2d1d2d4f0f6fc03e0faf013faf6fdf420fe0e00f9f3fdffe1fc1f05fea6dad3dea4cde3ebd3d2d2d4060be6d8f2ecfeedafd703e8c78bb5f4dc80a0c76080cd0b808080e667778056cf8080808080807f808080801af7dc806580ada6c880808080808080808080322b29e1331c45941ba2bbfc5dd6e0a4b11510ea01ddcbfa2e0bf9a6ae0a0ee2d6158b801c44e2bce4ce213bf0a600dacf3c8080808080e2daddc3ae111d1b050f0cff080f240404ffff0d80808080808092bcad8095c3e4bfb20ee8ebf700fcf50fecf27f7f7f80807f7ff480807f7f5980807f7fdd80807f7ff980808080686e27808000767f88,
      512'h80066f5480803d4767808a707f68030d03c080f8fc05cfad041418e8c432222ff4de58442204e9edf50d3938fef3172415f8fd131c06dbd6ef05f1e3d0020c06
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
    .OUTPUT_WIDTH(320),
    .OUTPUT_HEIGHT(220),
    .KERNEL_WEIGHTS({
      4096'h7f7f6c7fa08944c4805050d1abf228f8ff7afcec290b1461d4e4809b8e80baae808d92801e09ff151f08080c127f7f7f66366d7f7f7fd6a480f0d4350c7f2a7f7f39462d2e7f7f7fb7eb80c5108680808080801b3a332d77712f7f7f7f7f7f7f7f7f7f8080808080808080808b80ab808b808080802ae3c766e6ca7f7f7f80ed2180dcb3808080fe373abebe1d80aefae102e27f7f360beb03a4c4a4c0c7b88080802b1bf17f08840ba1c9808c808080808080807f7f627a787fdd7f7f7f5067677c7fa5964db820039380a9809e80ca3c8080e1808df080f82d263b4e1d18623d7f6d777f12081100e6808080808080b002a8ab3b63072234f7cb065319637f791d5b75c87f767fd28d8080808a8080a480afbf80cb8a4bfbf0f93f3b9ad42115f3e715d5c66b7f667f59527f5c537f7f313916eb1917c87f34f5f84e61c2fbcdf3c508edfafe10000ff5f212acdf06d025d6197f7c27b58e04d2a4fdd5e02709e805082ae4e6f181a9d9b48080808080b9e5d20bd1a309ce800501691fdd29647f37d08080b58080948080cdb78ddcc384dcf880fc552a487f68ead714808080c18380a28080350ff3dacfaef618fdf9dfcafca9803efc132e367f1cfd3d235d7f151fcc0eecd7140b0d0aedffc8b4b5b0e0057f7a7f6c47507f3734506660463332501ac2c61daca3de859bdf80d21335aec7e980f02cc82922ecabc9a687,
      4096'hac7f22517f77f27f6b7f4ef8ef2f01be5839e22a544e7a6e152b192965727f7f162b7f47fc4ae5217f792a7f7f78484a28fee5dbf9ffdaceb4c980c78a94bbc5686109287f7f80c1a60a08c8ea1680fb159f7f57f2a6dd0493aceea90e0a0ee72bdf80f1f3080b0c1aff022afb4972e81d6b5a8080ae496a5600582f89f7cd4eedf0354a5953437f2cd7f64e351a785b422e4d52444850b1b7e07f5a2d52490ddccdcb8fc4da809f91809b88f426fdad9a80abc48074bf28e699b38080800f5338985e5a800e49c1424bda4c3289062372eef27f7f5cf818fa17f8e330f516a093b2f3c4c980eec880d9dccda3b99c80cd808087cbbc80d60b94b680d31802e6e8b6b19592900600a02a309786d09406ccc70fbef080b49e7fe0ff39290beec2c3d03819e6e2e384ab896a7f2b5161d8f2522ddbcb5404b0111dfae14fd9af2917b68080a2cd3193808080c194808fe6d080f5ec8080b8136f7f4c7f7f097f601e0744d78cf480f15b1df3e324feffd102002aefd9d7e10e80a4dfef1426fa1f18a9fa35070c0c0303f70901ec62393e00ef3ead15784a4e04fd04f6900a7f32231c605c527f637fb9d1808ec98090968c0acb1d411d15472a13cce9e9a7e51312de00e52526bc1e218080bd031d9af50c8280c0b45533547223c23053d8676d31e325e080809aaec1e6a8e0eb80e5ed26370817350291a7c31a1742ff1543c4,
      4096'h195a8eabd1c02850dc2c57e1d5dddae7bea180b0def9970812d54b0fd92adbd8fcc7ecbef00c3e2ec40e1aecd51b1c1ee1abfff99eb280866d5c5d7f46264178742c131232dde1d7c82a27092b0fef33130826bd32c00832ce56f5f528ff0b32e5dad700d02c1ef2e3ee1404100780bcc2a3e0cc80d1beef042af31206a8fbf98080808080808080838080808080808080a0171f7680df242d0f3a48305412d47422e04eecf409e91f0fd9070c7558566d7f7f7f24587faa3155c21858f7c57f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f547f7f7f7f7f7f7f7f7f117f7f7f7f7f7f97ef7f8080048080237f377f7f093d7f8580aca880858cd1a59180f420b0ffaa8e07e9c77f8adb73bb807f28807f2c1be9808b7f7f7fb7968fbddfcbbbb2808080968080b680bf80809ab88080ea80b87594808080808080808049ec62f180607f7f7f218b7f46f27f7f7f7f80361380fb7f80777ff196807f25e0726ec87f7f7f7f747f7f7f7f80911280808080808be09a84de0a80e389808080808f80b780809d808080808080808080d28080b7808009bf807f77477f3a247f7f7f80d98084dac68072ffb79d888080a580b98b9d80019c80fa80808080e73380b92180111f08fdfaf3fdfe09feeebab980deed08207f1780df4d808085808080fadd3a85802b80ae44e9802680805e8b8030c18f269680007f05178080d580960f,
      4096'h80eb1780895380b74b80986df58055c6804b7fda4ae6b51e8080808080809bb15b80808080808080e07b80803f8c3d46c2f14b80802b8080878080bd8096e3800cf6809c5980a47f3fd66f8080ef8080038080bcb28080ae88b092dd98a38007c091979ca2d99e804ced806d733e7f9080d78080ef808080cccb1f80808344bcb8b7fbc4b0cf8784bbbadaa8c1bb80eec28018150fe5d812dedef6d094a780a24a877f69e4f0a48be89588c09d8080a82a809e03a4c21d80fc7f808058809f583d3448ddd9e3e0cd89adf6011f122e3d7f672be53de7da16d18aa0fcf13f18130ba1abfee50cfa0e04f4120bf6e3e902d2c0b415c7ce6442557f4718e8c712273a2f44210ec3c9af6f1dbc1cd787b585803228047f65307c7f7f01deeb8180808880800fe9030de819f5c3063930df6114e605f1efe2dee85655fd9ecd005d7f445c4e40c58082b2c7bdefd2adb288a520423f4855208081d5111feeb9bfeb808080644d287f5e2f7f7662c7c4e0e8f3f5ae8cc5829e80b2c4b9ba1cfcd9d7e24cfde27f76fe7f7f21632404f0000dcbd5add3cce292869de9faef5339f88c9ed2f0f851110acdf9e7cce50106d8e4feb9a7dab0c8d4cde6a81dd6b297cdb80a04dc7f29d07f7f636a37f331c7c09d9aaecbddb1ad90803800eb30d7bb808080337955495d6ef5d71ab8f5dcf97f4fdc104f754b46fee7f2aea2a1a4b5ad9397,
      4096'h8bb8a79d1e110325001b0b11fb4f5e587f7f7f7f7f7f55483314d512d5454858474a2def3d7f7f7fe1059280839ab2f3ff387f702a2b592f3f5cff06f4176a5b235439f314150804e5d60b4f57585fe1f610d8c8c336052e30ea803ef9197f5a6457fc82bb9fd7cba0c6b9bcdab0e7ce3f3b1228a5b5f9fdf616f0b3ffedc7dcded3b6e2a7f014de808080e1d1c5e1df87809dc9acbec9147c150af7f105432a375241677f7f7a7f0d3f42482f1615feffe7f5fe9ea2cf09ffdfea0dd8861b0337ef5b711b2d5c17273e224027010efe22e6fbb3ca9d07f514a0d3eab598c20a4b16591ef52f3d3ed4e7d9a783b4b79bbce6d3e78f8088fdfbf0b6c80ce31b157f7f7f80808080808080808080808095808050dc94809880808080c3800f7f49187f7fffe2feed22f6c0d1dec57f4069127f7fe1ddb9bc7f677f7f7f7f7f7f6ff8047f3f7f7f7f7f7f7f7f7f7f7f7f7f7f68f37f6b407f7f7f7f888080e4ba00b380808fc57f20ca263380537f7f7f7f7f7f7f7f7f808080a7e1c86c7f65833e31507f527f5c7fb5ef1b68487b6a7df17f7f7f7f787f7f7f7f8080808080808080806015ebcf045b0a7f7f02e5c1fb7fabb9271080808080808080808080db809ea68035071f7f7f7f7f7f7f7f7f7fcc95808057e48040218080808080802eafca735f177605f380808051f1abe7f1fbb09e8280b59980808080808080808080,
      4096'h808098260e477e469480cd80808080a1f280265ec16180bae33d557f767f7f7fb104d8808080808080808080808080808980e680809d8080e72280307136ccd5804bf4ec00d9e7da07ed06c7f57f7f7f8080808080803c487f7f2ea97fee70adbc197fee5c7f684b7f7f7f7f7f7f7f7f7f848f7f80447f47a67fea08a480b811808a80800152ca80357f237f7f7f7f7f7f7f7f7f7f808080918080808080ba7f7f1e7f7fef4c49267c43217f7548502f7fe6e27f7f7f1b3b67808080808080808080f8147fa71c7fd67f7cd77f9fa37f48c86141808080808080808080808080808080cdb7807f7f7f7f7f7f7f7f7f801ddc8041be800f268080808080808080808080d48091828080808080af8080808080ed8080808080808080808080808080808080809da79d80ff8080808080f3b8d722d30880cd7f7f7f7f7f74480d7f1d1ddfcd253e83b4dd7f7f7f6c7f7f7f7f7fa083f09380138a80f50a7f02ee7e6ca9cc1feb07f505f00ef0fff480df1b80fbf88091b7c13c3b6d5f2525d1b39010d280d708808080d68080f78080808080bfee09984074a98af819647ab9cd00a980800847466e7b51d3644a922580326e52071180803fbccdfdf97f7f628e8080f68080808080217f4a1a707fcbf8d6fdfddfde9acfc5910ce31a68d9e5183a345c80a5d180023b8080b5654730663042e84d7c7f7f7f7f627f7f7f7f7f7f74,
      4096'h7f7f4522482c8095808093988080807f507f7f657d347f7f9c18a2f7161e1f04657df3082db2d816ded60c17faf20d368080d4303819687f5072387f727f7f7f6f7f7f6c0ce3fadaafe707fbccc2537f7f7f7f7f7f14af8011e78080d5808080ee8080ceebaf88808b8080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f5c7f7f37ce2a152b07cb07f8027fa4071680802980804f7f7007cb9a2cf1b67a7f7f7f33526cf7727f7f7f7f7f7f7f7f7f7f7f7f597f7f7f7f628080d38080808080847f316c52b0e47f800e7f7f7f117f7fcf7f7fd78080764ab21834b97ff3807f97067f1222cc6e97c044b18068f8848016bf80a87d4e038080808080808080807f7f7ff27f7fc87f7fcf80d89b80ccf887ae808080809e80808080f3d411b68080c8adf77f7f7f7f7f27a37f5ae880101aa8e0089bf38b809d19affe80c2f4a0c1e7ebc58e80a680f9e0070e1ce3f55476d8f29680d1d3808080a8808080808087808080808080a380809680cf7f6280662080637b9e7f5168730b427fcc21cbe342ded2a78080808b80ded2807f2f60e98b80b2beaf2a198048841a6780e3529bc8040afaed15fdfafd09fb3e0f7f7f6ef0dbb42e06077f7f5e7e7f181c20217f7f537f7f77367f7f7f7f7f7f7f7f4ff333eeef7f527f7fc6d09780d2b6808080d28725dcdd6ad993ea3b237f4ae07f46ec62808280cd01a87f560046f1,
      4096'h325f23224c7f1c30edc77f5abc7f60967f75466d333d7f6c7f8080808080808080805a54733b617f4d5d7fca99de3f2d6700197f808080cbcf801519ef290f237f566a7f7f7f00fc7f7f727f367f7f94b515ebd46ca4e57f808082b580bc7f0ce57133f23d492717b8b79a80888080808080b4e79edbc89ef88007d09b8e80fcbbec34657ff2d28037f0de19241d731ecff058ae7044801306972913923357f3617f7f08145d7f7f7f7f7f7f7f7f7f7f7f62377f7f4b7f7f9f4a7fcda7b8ea9af4f1dd20f3fad60b16da18dcf42ebaa980c8a392d84480a88e80808080b201166c39e6d8b48080c5808080808080808080803086147fe51e7fe3f5f858808092d4fc76ad5e7f0a7f7f207f7f808080808080808080427f7f7bea7fb3190b807f7f80327f80cb7f95a68580d726808080ad1c3ac54e608080807f7f7f6a7f7f27627f7e7f0c7f7f3b5b7f4c647f577f64d9a6f7807f7f7f7f7f7f7f7f7f80efd580f8c48080800be5801e0e8092c380137f107ffdb7c90ac4117f7f53247f597f7ff64153a1a400352e71a633605a7f69077f7f4f0d66767e7f7f697f7f7f7f7f7c7f300f3d7f7f7f7f7f7f7f7f7fe22cf380262780d4d580808080809a8080804c7f7f453a2a80d08480808080b880baa682571b7f150b7f099e0cdd08807fb8677f1a7fed011cf9eec7c7eee27f7fd2805b04803e80cfa780729280d899bb80,
      4096'h80808080808080807f7f7f7f7f7f7f7f7f808a8080a98080526f1e808096808080e9a8118ce82f805180843d7f7f7f7f7f7f7f7f7f8080807f45467f7f7f7f53667f7f7f7f6d7fb8ccc6fa809e47176980809a26218047d7808080808080808080807f7f7f7f7f7f7f7f7f747f227f7f087f7f64808f80a480807238808080808080808080ad7f7f157f7f5e7f7f7f167aa77f7f717f7f7f8080b1e280802c645e808080808080808080808080809ab1acec7f900c808080ba98128080808086f68084c3807f7f7f7f2203f5cec2333d27e9eccd200e7fefe8864f80807f3d0b8080808080808080808080808080808080805d15907f49807f4c1c7f7f7f7f257f7f7f7ff9c0eb0fd911a8ba108080804780808080807f7fa27f7ffd7f7f698080808080808080807f7f7f7f7f7f7f7f7f8c3e7a8080db80808080808080cb8080ed80c5367f80487f4b7f7f697f7f127f7f7f7f7ffe36797f7f7f7f7f7f7ff27f097f45217f7f7f7f517f7fb37f367f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f357fb2ed52097f7ff080808080808080808080808080b0808080807f7f7f7f7f7f7f7f7f007f7f587f7f7f7f7f80809dbe807f131cff8080808080808080808015e9f66e577c7f7f8080458bf68080a48080808080808e8080808080808080808080807f7f7f7f7f547f7f7f3dc9c95266ea7f7f7f,
      4096'h345b6e5b797f809ce28080808080b4fd04efde9ef68080808080967f7f7f4cf5660784df070b0005f219020df9276c7217445933edf80106e9a8b08d8080861e7f7fe1f3177f7f7fadba0a5345457f7f615e23168080d2193d35262ecced3ae5a595882d1e0f808999cf19501adeee808080cffdcf200ba7d1dbc1808080c0cffae21afc3404f8d5d4f2e0da2ff0c9341312119be9037f7f7f081c019da8ca87b1c08080c192c0f79fdf049ec9a3adc5a827181280930c8dd40b80d8f2ad90cd5667782a617f394464caba3883bbd7b01620bb22dcc5daf2d8ac80e2ada68080805d7f7f717f7fad08eed8d7ce9ca1a0a380b0cfc0d8c4c4f0c8d4bc808080cd808020c4b08096cc2f692fbdceeb0180f9b2980af79815dadfabef281b233947772d1553440464253c58493c7b5c1b533667616d080a07da4a6313ee290cc1f8ffd6fd3cf7fa0e09170c08fafa140ef7e1060efe1b66c2e896da9c80aebb8027fbb1e8f1d7f6bde880bed580a3f186aac0d6ced135fb051dd1c72a43470eff2d0b034a31fcca7113e31beab62a7e31387f6a337f7b12531bfa11e5e0cf9aa1ea05c9c5e9a6a8b6fc05050ef73e0e533a80bb8090cab1d0f7fe135061f5fc61fc28783904cf433b4a5a7f7fe4e25cd3e130b4ce223b506e7f7f7f7f7b4cf421180e2415ece884fe25361d3146dd1c1dd4f865de0355abe81835fbec1100ed3cfb,
      4096'hbc5f45385647075373077b084d65ed3526e90e3cf20b2944305b5c4612542d7f7f7f2c14fa7f495375431e2a513308273d0b0334fa2347cbcfc3d8c3f5b10941bf8980d1b7b88080a46e367f40e728b5d6d1ee217fd5da3392bbc8d6801c0eb5520c995c0e1c38021230150d1dcca5806ef6c4d69fc1bfcd173a577fcdf528d8ff08f00e2192aae7311363471b737f216849055a7bfe470587f30d1013eacc1303c9068093f68080ed8080801aee531cf33d22141c504b7f6a7f7c7f736dadb910dfc617d880c3f1d8ddf1e927b5d129c1bbeedadb81808080eccce2e6bffbd58eb64df54d52f16d73bc7f2eff1042011862d4bb6c3b634702517f59437f7f7f56557f8080f24ae61b52ac440a8903f5dfec2dd60243b5a821385f513556754957bdc9a88680a7a180b346386f2b2b72fabe007f46403c2a375d1442660f284816790abcae09dfaeede1c8b1e7c2cfadf5d6c018d0ce34e92034f33d7bf63b7fc27f7f80407f8021807fd22e809dcd0db0801a86801080801a80807f7f7f31377f7f437fa0e8eec7cbf70100183429e1f17f7f8080803bb380fcfdcc53801080f1bc80808080808080f476bf88547f3334808080808080808080808080fc00d280a88048df808380bbf7804196e98087badb291e80bad43156737f7f7f7f5290237f87007f36594a1f7f40e9277f7f7f80808080808380808080808080808080,
      4096'h80800f7f7f237f7f7f7f323f7f483d3d717f46f1217f7f7f7f7f74e67f7f4440d9f4fcfe2b7f808080813880680e807f7f7f7f7f7f7f7f7f9848ea7f766b7f52308480e98080b2808080808080808080808080297f5de7ce94da041296399380ce8080b3ec84d3808080d18088807f7f7f7f7f7f7f7f7fd2a2403a41cc7f7f1411270cb3b011bb8080142126470c47051552b10d2ad3d399808c9dd6c1e42ca90380a2b3f7fa11ff1505000d10113729e7c5ca928080b5e2b3f5e8db3909fe9b07ea83cce280b1d88080808080888080804a01b9dfc101c89f1a204d342cd8309f948014494fe4f94eeb9c018580809cd980a780800814df264ae5f05c0c8003eb80dbcc8092803c1d2654efdfc6868043493c221302e71814ef2a17e4023aabc903988883b58080808080fe696c900a71c5cf2e142b500221ebf633373c2dc440241735004db88080908080808080f45c559a274886b72d3a280e605915377e03ff2ef738f9de02ebd83c344822e95111ec1d2412f701c321c326181231352bf93f120accba03e5d5f612a9b8c44d121e57fbcc0484800912d82603bfb4c5957f7f7f8080809b809e8089b3f1ee30e67fec0d7f7f147f7de8317dd498807f08458091fc2809b6eb0805f90d007f7f7f357f7f7f727f507f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f441d7f5a205580ead17f697f7f7f7f7f7f7f7f7f7f7f7f7f,
      4096'h7fa943657f7f803d7f8080ea7f7f7f7f7f3be14a439e808080808080808080277f80507f8080ba870bdaa080808080807f7f7f7f7f7f7f7f7f417f7f1b63028080802c8080a080808080808080a089dc808080808080808080808080809203ebe57d7f20627f7f7f067fde80808880808080bcb9808097808080800edc1938e5467f7f7f7f7f7c7f635e7f7f57154a3380415680808020e48080808080a580a9b80009ec837f7f577f7f7f7f3c7f8080808080808080807f7f7f7f7f7f7f3068ed7f3e80857f8080808080808080808080800a44be80329ac71fde7f7f7f7f4f7f7f7fe70add1a4c10f3db02047f4e7f1cb380e580800da70cfa8080775a80a5838083807fb8e37f7f7f7f7f7f7f7f7f7f8280dadd8b4880be7f80808080a103a7860b30287f8080789806c97f7f7f7f7f7f7f7f7f808080d2a6e4dfb4327f7f7f7f7f7f7f7f7f7f264c7fa5a64e8080808080b780808080808080808080808080807f7f7f7fef7f7fee7f7f42e73a0c9557d0808080808080808080808080808080808080807f7f7f7f7f737f7f7f7f4fec4c16d17feafc808080808080808080267f7f80ea18808080808080808080138e808080c28080808080808080808080808080800c7b73d16e7f808080294b2e7f80c01c29b77f7f7f7f7f7f7f45c080c09ed2f2c480cb804e342eca007d081a6222aadb37c2b27f244d7f7f427f7f,
      4096'h7d7f7f7fe7fae404d8db15cce080808080808080aa80d20cb51403b03fcac9c0cf10a280808080800ab52feedd3b260758b2ae808080c9b28080a9809fa7b89f97939dd29ab8b5d3e2c117f2a3801280a611b9ed0c80f7920a237f7f7f7fa900df05e2c7b813cc6641173f28257f7f3d8080808080a4808080808080808080808080fd7f7f7f7f7f7f7f7f7027367f7f197f6e304e7f7f6ff27f7f537f72694bbb6c7fb083d880b8e780ed06dcc19e7f7f7f7f7f7f7f7f7f85e3403a2e7f7fbad580808a80818e808080b594808080cfbd9ca3107f292f7f0779114bfcd17fe8e540661e06c3b50bceae1f8082eb7f7f7f487a777f7f7f80e280a3e7b73648f8451d56342720c9f0e75a6d554a597f64347e1080c78080ef90aa0773e821468e007f9427e4f2d1d6e8dcf7f4f2002b2d587f790b2819cbed80e19f80a180806035707f3b403eadbf82809bbe80e6d080ccd3c5ddebad5b8080b17f7f7f7a357f1d3853d598d59c80878080a280809d8080838080807f7f7f7f7f7f3b5d7f64238f7f48b92504ea20f2d74adee5ff1c28808080a697bb25e0127f727f7f33786c727f58484c2b517f26577f2309652f0f3110d8042d7f7f153f7f7f4971717621f1ddb9e7809d80800b80802980808717407f372e78ea2677427f6d7f7f7f292e7f7b061760150d7f176ccb9beb8080a6808091224625173c1e7f4a506a7f7f7a,
      4096'h7f3e5257281e4135647f7f6f7f7f7f2b136429dd312a0abf8980f6c9be86e6d97f7f7f290c2d7f7f7f8091aa808080808f8044f7c93b581e733b2380a780adc299cff091e4ed0605f305eee7f87f7f7f7f7f7f7f7f7fbdce0e4751431915d17f7f7f3a2c667f7f7f808880904a598031677f7f7f7f7f6b7f7f7f7d7a7f7f7f7f6d7f79757f79766542d91ae57f7f77783b26f9e1d08080804a10f480bab98081b0ee7f3780e1c480b980c31e8b9c9d80fb1d2a3e7f7f50647f80a689f521c1f3fdb2c5d780e5fc8080808080808080ad8080808080b9cfbba0b28082d728663380a4899dfb037f7f086d63d23d2bad80eb948017c480ae80ae96cd272952c82231557f7f2f445f7f7f7f3b4c3f251a0ce809f1e5df1bb2cd80a697caa8bc9f8080808089ae7f5565531c287f7f7fda17b4ee63be9db580ce12e517622afd0cdb7f7f467f7fcf7f2200517ff801c380be808aeb1080695512162bd08480807f938a0156eb1e3a1335f6f0f9faff96e8ca0d10d7f4808080808080f580cde5c7808080bdf6f7c41300808080d50780b38080808080c2808094a6803e7f7f76687f7f7f7f842c705d7f7b317f02c493802e5480c23680c58080327f7f7f7f7f80e26e937f7fea717f8080800d7f93deeb80808080801c808080807f7f7f7f7f7f7f7f7f7f66807f7c157f26e48089bdd23ff5808f80bc7f7f7f7f7f7f7f7080dc80,
      4096'h80808080808043f3807f168073ca8080808003f68083bb809780803b7f7f7f7f51358b80f5c3eca080807330b37f3a0b6e463b274a7f3ce5303b1f32e1f27f082a7ff791a27f7f7f7f7f7f7f7f7fcfbd800e6b801ea980d721947f7f2ae9552ff18fa93f48d09f2dc0297f18c7575f371ba32df95825f22829767ffe807fc3876c96867fee2bf10720e7050df2506eecfd040eacab8cfe8c1d0cea3810b31a4af5807f7f35c4f380808080bd808080808073c2aba9ce8080c3b55bd70c80808080808080862febe23a7f7f7f808080b325a3667f0b7f167f808080bc8083808080ab80cc8080ba1dc7717f7f7feaf872f7f30d558c2080808045445b4cfb3811eb1e80808080800f8080087f7f637f653e7f7a227f4c107f6bb933200e7f7f7f7f587fdad22f808080b3d9808086964e39466c5f40480ed47f685d4014c419bc807fa2821a90bf180ee7a380cfc8f6143a387f7f3b7f07544f7f6b7f7f7f7f7f3b06b9fe7f808080808080092b80bd9fd44f1729c280e2caab42484f7f80802e7f7f7f7f7c7f6e617a3ba5026017434e18fd808089a680aacd80ad7a16ec39b6db25b915f30becf0f7040df610f23620436a7f407f66be80a8d69a80c8a99f7f414c4a244545ecf05780c54080cd09c3fc8fd1d99a88ef8080805bfa6c6bfd0474090dbf80ad488080338080a48081888eb0938080f91ed926e5f99bb70acd80,
      4096'h801b8080c78080fab3a7d3bdb306d797ae80ae1ea804808033702c484c08745d226e808082c29a04c6b52edf80874380ea019bb15f2a4e5ed9764b497f7f3b3354ff7218bf23808080808080808080eaa3353e801eaeaa06182e4914f1b2a293ab7f7f7f7f4c183d7e61808099ca8093b580b62af5054d527f294a27eeef5e7f58107f291be5150e6ff6187f7f7f00b1a3de87a6c9bd80e1caa7d3ecbedcdbd27f14f08091807f3af6327fba7f7fae7f7ff0197f7f7f7f7ff87f7f8080804836808480800759ff335b0a2cfa2b617f7f80cc807f507f80808c857f7f77fd06974c7f757f7f7f7f7f808080fdf78d808080dd7f807f7f457f7f7f7f7f7f7f7f7f7f7f7f807f7f7b7f7f697fdaa388801b7fbb8095807fb9eb80d38080808080727f807f7ff27ff8802b80bf7faf8080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f807f7f808a7f80808080804580808080800580545a80a8c6010f0d04397f80e17f857f7f807f7f80037f8080808080a4808080807fee167f7f7f7f7f217f7f7f7f7f167f7f7fe3680e7f7f417f7f4dcdb2dbed7f80f461f57f7f7f7f7f7ff77fba7f6ef07f7f7f7f7f7f808080803480808080802580667f7fbd8080caf4f1022b7f80a780c980808080800aac808080e180dc50da88807f6b7f7f5e7f7f7f7fa10908b4b6eab9f5df522f897f2a84808080048086309bac7f157880,
      4096'hb9d6808080ad80807f7f7f7f7f7f7f7f7f80563ab4803296e77fc98080358080aa808039f3094180a8d7003a2d7f7fe9c37f7f7f7fde14807f077f57627f7f127f7f647f7ffa7f63564d31677f7f7f7f8080808080ed8080808080808080808080807f7f7f5e7f7f7f7f7f7f7f847f7f807f7f291f8080bd8080c28080a480801380dc7f7fab387f7da47f7f7f7f7f7f7f657f78237f7f7fbc808080800030cb118080c180808080808080808080808080a280808080808080c893a380808080808080a1808080808080808080807f7f7f7f7f7f7f7f7fe280899fd0807f5c7fb780af8088a78080888280808080807f7f7f8080808080809c80807f421958acfc7f7f63d3ebe8d4f5f7f5c6fa80dead530f8980c5fa31808b1580807fe8e4808080808080b7fb4a7f7f7f7f7f7f7f7f7f80808080805f800a71808080b780809985f59f9b0b64dfd336a0442a8079dd80687f7f7f80cb807f5d7b7fe53a7f987f7fa97f7f447f7fc7b06a80807f4051808080cd93aef880808080809680808095807f7f7f287f7f7f7f7f51263a7f7f7f7f7f7f80f69d80809d8080808080808080e85a7f7f80bc7ff42e7f627f7f7f7f7f7f7f7f7f7f7f809280ea8a800731378080808080cf808080808080808b17dee07fb580e980809eadab958080808080be7f73388080de8080808080807ffb007f80a97f3a477fa8877f80807f7f1a
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
    .OUTPUT_WIDTH(320),
    .OUTPUT_HEIGHT(220),
    .KERNEL_WEIGHTS(2304'h3d356e01e8152829537f3e2e65d0277f011a2f013113e4000b05167f7c7f287c4ccf41fa9c4546fe7f24803780480f5425ec2834f4271a0b2c1e01100d1d46140c1d0e0c112c2538014029df2a13f8d48016f51809da0127f43e7f7f7f573ef9537f6230fb24e5d00e32f139cc4ff3c5112b83a080b2019019feea0d183ac47980ec7f21806fa17f7f481f7fc28033804021217dfb2c7f3e43808f90f0f6e05057227f037fc9dde71bfb0f80c0bfe60101333323797f7a5b0bf5f1130a2212620fcae6db05fb59df56fbbad727ed477f2a1632cb1414f42932272df8461780b58042425726030b6c0d503a17360b1409d8dae71d0d17fdda091907128080808080808080ac2d2e3d2318222c26497f1a1444ab0b13f11480808080809580ad7f),
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
    .OUTPUT_WIDTH(320),
    .OUTPUT_HEIGHT(220),
    .KERNEL_WEIGHTS({
      4096'hfff3951806f62913cddd01e2e0d7120e0a0beef92518e3f0d3f5f5c9f8de06f6d67f80124780808f7f802b807f7f7f7f4243b880163f807f1a15256537bf4580333b7f9b7f80e7804934807f7f8d16fe8030c34a7f80ebcc7f806e7ffbbf1e7fe829fd807f808080cf0743ef810f7f8a807f808080c56d80737f7f7f007f807fe88e80e8d07fc97ff8e953c2804236ab7f80c351eb7adc57d217d0802280e2bc539cdb989d7ff87930c0b9098582b7db7f7f80c725e88080f45d7c5d0fec807ffdb380824ef7879a157fae523bb180fb80ff57069fe97fc3b3d01280e2f17780df80a0d593991d43800880d480d082800a1680c580f4fe8083eb4b3a19ccb5c0de9480808082f933a47f8037929cb780ac9680a480205a268070278815805d807480dadf807f7f7fd47f807f80148080f780c244f6037fb0357f8080fe801f8080d4807f7f8080806d807f807f8c7f7f7f8091806ca4807f0a80b66da7805f89509e80a6807f2b67b816abf8ad8980803e80e377b70fce0fc84c0ea20fb9f171c0c5baab8043737f404fe807d217a8554fcf16e41adb06ce51390fe7fee51980c77980fa6180d4b08080228013ce7f7f427f13f87b89807f5d9ce3e1eeac319980e5ff4f805b988080fa80698080808080807f8080807f51808080cfe3807f948080695b807fc08080e68a7f8080808080827f8091807f2d808080802b80be80,
      4096'hdff61fd2e1dbde18f0060616dc2bdbe62addffebeb13e1f3fc0013f00514dad9ed7f80f47f80d5bd3f8629806ee77f7f573effb1652f807f018051bed2e44e800fed1bf7df7fc07f2eb3d4dd35db1d50c67f4eef7fb680b92e801dfb0995d10980ebb1bfb525808080967f7c80bb80d080807f807f80067f809680a9d280138080313280ac80808005b7275b241a5203c280b380696e80807f80ed630dda80857f7f7f808026807f7f7f7f8080357fef7f7f80b3807f0a80807f7f7f087f808020afc3748041b480800e807f80bd8080808ff28080ac7ffb80bf0f7fe0804e80042a800b7ff3808086807fb30d80808080f37f0f7f8acc7f80ae8380d3807f80a97f80de7f80e595f3801a803fd27f7f366b6fb27f3c807f3b80b3cabb8029807f7c96ac807f7f7f7f7fc083124f4d7f7f7f807f807f80807f7f7fe00e7f807f48fb26000a42dfa01def8b00be7f4400607f8044d0d5bd808050e8d6062ca00f80ca360fd0d82d93499d77edfb3d7f1c70c587827f3a80ea1b42b26e07a0f380a27f1080e480808085802c807f0b7f097f6cfba93c5b806e7f0d7f7fe5d41a8053a409804080807f80ecc195807f7f7f7f7f800ad0c58080807f6a0ed07f8080fa80901c807ff0ab80bc8f7f8080808080807f809e80434a8080808019808e80af8e807f8078088080e9807f8080808080807f8073806f7f8080808008804480
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'h32310ef81c030f280d00f9e706e6eededddf08310b4b48060f1d06d8eae2d3e2d5fdedf2d7b9cee6c4d2e2d3e0faf716fafdfd01ece42cfc022ffc0222f5f72705e2fde6c3f7d0b635f7083b031833f6f3200c031f02ec0ddadb11e3dd23e1e807daece3dcd2eeead3edf3f717f8fd28f1df19dcdc07e5dcfef5efedf0d718dfe32701001adff509f9f72c13022a0705f9f6f2d7e3eeecdc01eed2cce5d0d7d2d9ceec0e04090f0cee02f906e2ea2304080df0ef1d08fc1afae4e3e0eb01f2d0e1e0d0e2e0c819eaea1f03fa09f1e519e9d41cffe50ce2ec2cf8f61ae6f8f5f3e2ecddf6bec3e4d0b1d6efebdc01e7d40de5dd2e16f025ebed230ffb1fe8f00ad1db0ed3bfded0ccc3f1ecb6baea27e6e221f9f433fbe117e2e02ceae626e9daec1a1f0a180f2f160ff6eab20bd2ce11dcd61d27f01e05de01e1b209faf009f9ee1d07e918fe170b02f824fdf1240c285641223b252c2e340c1efcf518f1e53c2a383e0f4a4113160de7f3faf7e0f1d6d8493415321aea27fccd02f99f0bfbb32519a825e20809e9effde0fc402b0f3b0fdb1cf6c107e9cdfdd8e0130eea20dee40800cf04c7b0fadee9e8dae00cc3cce2f819afdcf1bef80fdbcfc4f9d8c5feefd31cdec722e4c417adbf21fbd52ad2aa16f0b4ea01041f33fb1e13e804d3f3fdf5e50a09f6320901faffdaf2bcbe390ebf22f2ac2704b407ccb3fdae8d01d6,
      4096'hbd3e14fe3d0c014c0ef6f9d3e1110b1c13120f3003ec14a1d605b0c708e7c212ecbc22f5c3cfe7e4ff06002200ec1ee7edf0cdd308c5c8fdbfecf7b8b0f8b4c5fdfc08f704faf5f9f6ecf203e5f9f5daeefb020c16030c0f05fc1f041609f0fe14e7fd10f5f8f9efeefbeff1f80512f50505fffe0407020105f0fd15e4ec040e110c04050af2f3f901100ff4fa00edf203160a17fa0719f5f905edfe0ee80608e2f2fcff0b08f7030afe020704f402f7f808ecedf9f7f311ecf9f7e1f203ea0003e8f200f1f50601030bfcfcfff9f801fb09f80307fafdf7f5dcf108d7ebf1cfe6f6081210020c04010312f5fe12fafc10f3fd0ff4fdfff0fff2f303f5fb0000030910e3f00c080416fc040d05f304f50814e7ff0fe8f105ed0413eef9ffe2f5fbfff707ecfffcd8f20afafbf9e6f207eef30404fe1204100ffd050febfd03e600f0dcf2f502f6fdfbfefcf5f2fa040a07f1f3f5eaf8fcfaff07f4f5ffebee00c102e4e8efdbd3edfadee7f1e5d6e4e8eaed0917220bf602fded10f6220cea01f3ea4433192d2e190f1b0d1e1cd4deece6e6dffefaf3e9fc08fee0f3e7fb02332839030b1a0c1c184130431d183d1e1c3d1b23380b0f2105ed2ac7ddcbfa10e5fd01e03b3a44190b3af52e4022203e0afb0b06fc19a6cbcfa8d1c8cad7a9121c2a190b050d150e0b034af7073b0ee92e12fbf6e5f0dfffe7e9eef101deefeceb,
      4096'hf4f94534142a042218192a1a462403171f0afa0ff510e0d5f2f500eeeb12fffd09defdffe9e7193f3e10233b22403efb0615e2f111e6ee01e8f1fce3dde1deedec2410f30f00ea04fdfee9dee5d6e3d9cafffa34363513e704fd0302d3e3d6d6f5e5cdc2ded3e6fbadc4ddc1b5c10c2a581b14241c1025fe02130cf3020be904fb0f071c1a08f601faf0eaf2ede5ef07fe0203fe120a0c24110d1ecdd5c1d5d7ddc7efd7ced6d6c7e4e2d3ddc7effdebeb01f9d7f2dce7d7e8e5e5fddacdd1d0d9d7c6e5ddafc3d3f3e901fce60ed9d4f2c8c1bacfcdd7b7afb5f5ebe7f4ecf20fecf9e6f1efd8f2f1c9d2d5dddddbe6e1e3c5bdd0e1f2fbefe7f0fdf6f9e4c9dae6e3fadecdc2f8ddd816e001f5e0def2f7ebebf3e0c8ddb8e5fcf6f4fcfe0b00fcc79fd7e099cef5a2ba06fe0a11020c120407dee2efe806f2f1e4f8cee7ded8dceed1cbd1e2e7e911f1f8f4eaecebd9dbf7dfe300f0f1f4f8fdf9f40210fc09bfb2badcd1cae1d7d908030310fdfa0902fdf8f718293537111717e8eafce5e1eaf4f4e70d1621ff1e1209fd06e1d7d0ded6dedcc3b7e2e0cff4e0d7e1dac7edeedff702ef0afa03f7f5eff1e2e9e3e9e7ebeee3dee9e1e2e0d81019021c141be7e7e00d0806241514f3f9f9f5e5f5f1fbf8f1f2fdf4f2f1111920e1f2ef0f0e0d0d0e06eeecf906171208170de8fd02f5fdf5080f10e9f3e5040407140905,
      4096'hf3fcf511210c142311e4faff0e04000b1004eef6eeead9d708f7efeeedef0d1110160908faf8ebf70808ebfd02f80304fe0201eefc05d1e8de09fe00f9f4f2eae4f3ea0705ebf001e4f507071a170f0c0302fdeaf3ed05ede4e5fd06f70505fe22201bdde7f4eaebf1fd0210edf200e5f8f8fb01ece7f5d7dde5e5efe8f3ebe1f0efe6e8edf1f1e1e0e80908030d14160708000e0b110afb0aedf105e9fbf3f4e8eeebecf2fce6f213171ddcd9eb0308fff2f7e9eff5e317160dfffd02fbf5eb0efffe12fb13050d16f1f2fbecedf9efebf50cf6f905f8ffe2e7d410fe01150a13fbf9fb1c1f18121b25011618fcfe00331717180909fcf8fffc0808e8e6002c2b201c1505050411110a0df3f2f8f5fefa0e0a1c0b1124f3010df7fc1203f707f7fe1d0604fe0804fcf0e0ef02020cf7fc0ef3f9fecfd2c7ccd1decfd4e0faff03ebf908f8fe0901f4ee01e9f611f8fef802fcfdf0ed0e0528f9f5faf4f3030407070a1612131722fc08f8f602e8f8e9f0eff1000a0c150afe0af0fdf4211a1f0c0e0a001511f9effdeff403e2e7f7d4e4e2dbcaeee0e4fef0ef02e6eafcef0003f4eef9ebedf2dadff8100bfc070c0e06020c29262501022005011aeff8f5f2f807f60b05e4d4cbeedecce7e1dcf8f8f9eeeef403faf5050e0bf902020e0108e0dbbfa3a4bd808080273008122742fd0d33e5f1f8fc1fea0e2d06cbc9a4a9e2,
      4096'hcfa8d9cb0c04251b14fc0211ec05f4e0e8ecced5eebbedfcab1becd2e1e4f08080a99ad7c7a5a68e443f21495d46263233cbd9beead9cad2d3ce1d261f2d3e1c1a1014e0d4d2dcfac2f307ccdeecdffe0ddffa02e7ef03f6e2ec05d0cdf5dbd9caf2ecd3f1e2ce09110ef31302dde6fe7e5e154d5d644f7943f90906080506e7eaebbbb094f400c21126ce21170e1b2a2c1d100ce01f220d101e07e30cefd5d0e7eee8d5ac9905090c293e25272f20f0ecd4f8d5dde6f5dbd3c5c9ecdde2e4e2dbebf8edd4f5d4cad8c17f747f5e6e6338431f1236454b4e6c5b544fe9000d0f1c2e1def0efc13fe430dec09dfdbe806e2db00ebe1e2db17281c080e0d1224fcfbf6fcfcfdfd0307fbe7f7e5f7f2f4e6eae9d7edd9f0ecebdfe3d7ebeae6e9eaecddecd4f0eee7eff6f2eff3f5f1f0fdfef4f6fffcebe8ebe5e8f8eaf2f4d800fbfafbff03070009f1f9f2f7fbfaf0fbf5d9e2d8e6efeeecece4e2f0e3eaecefe7eceaf4f6edeaf6f9edf2f8e6e8f1eef0eff3f5e9eaf8e1eaedf2e8ede6e7f5efec04f4fcfcf2f2f9e9fa00edf8f9ed0100060102000305fef4f7e6f600efebf2eae4d9cfedf0e8f7edd5eef0dff802f5f303f805f8f10201f8fcf6f9f6f0eef6f5f5effce8e7f3eff2fcf8f4fcfbe7ebd5f1f2e7e9ebece9f1ddf1f2e7dee8e7e9dbceebebeef0f0df00faf9fafafaeaf5ebe5e8e1f3fef0f3f6feedefdeed,
      4096'hebf0e1e5e6f2edf3f8f5f4f2f7f0f1f1f0fbf6eff7fcf300fcf3fa070003fdf909d9bfced1d6e6e4e0d7e705cae2e6d6d8e92e16f52122fb090f0b0de61c01f20101fd04e9f8f4e8e6f6f5f1f1edd8e0f4d4e1e2d9d2f3e5fdf2db09ecf2f7290e1bf9f6f7ecd6dc0bf6040707fff80c100a07fbfbfdfdfb0801c0cdd6d2ccc5dbebcd08fc1308f4051b0f1904f1f9ede20ae9f3f6e1d0c4e4c2baf5d1bd0f030912fe1a100c1700f502090b23f51827e0d0dbcbd8eaccd00bdce1ebe5dbe1e4e0ec25382d1e1c1d2631190a082502f81c0b133c0c0a06f3f202101bf617ddf1ff01e8f309eff1fbfbf0f2f0eef8fbf2f4f9f3eef303dcfaf6e1f5e8e0f8ecd2e5d6d1b0dabfb7e0c49ee1f1d8e0dbe5f1faf34d342c2c1b0c1c1604d3dfd6e7e6e2d1cfe2dfd9b0d3b1afd6c7c4fad7e9fae411faf719e7e4eadae2f9e2f002fdfaeffb1c07f10604f4ffe5f5e8e2fff2e4301c2a281a30252a240b0af107f4160f1410cec1bcd8c5d2c1ceacd3caabd6eaefdccbe231130a0bf8fa1af8000907df0d01cbe1e8cb2211e81706fc2610e3fdf6ed15f6df14f0d807fce20c0cfc1a28f5e3f4d80b0efc0902f611f6e413fddb22f5cd190dfe1c09f02b08ee2908ff201bf41d0a00380b0e32082e39182ac6daf8e9d2aec4dbcbdfe8d6eceed5f2efdb0de71732d9041ce8022502f13100f91d0b01f80d07dccc16f9f3fdd7c1ab,
      4096'hd2d1a2fbbda7522dfe2e1f042e130b2402f421fefb331c0503e1ec06d6e802eadee6ddd2e7dccaf7d9c702060107f9e52513fef606f9fd08e7ff01e402dce8f2e0f10de1d5110622fb1ff70b10f02404f924fbfa1f00141beee810e3fc0af6efd6b3c3fdebf7bb02ebf0cadaf4f2f4d2dbdc15fb1d1c0b33310e0ae0bdb5ffcec302e1dff5bda2d0ddc3dcd8b6bbb188d2e5c60fbca6f8fe0f0bf2f5fb0a00aebbc1a498a092ba9d26fced2911fe43261e18fd0ef8f70e1e1413f9ddd3edd3ccdbd1ba5b4d21706d25646a2e02f50a171515200d07ded4e2fbd7cccad9c9260e02210b14341a10754946684a456b595114f1d803f8cf010dcfede4e8eeeeeaf7f1f1f216d92a260b02591a3923302d133f4d3544def2d0dbcce0d8d7cecff3e5e303c8f5b5da5f6b1b5a5a335e46403507153713193515251cf9e71216f90513fcc0d7e1b4dfcab7d0b6d1afbacfd5d305fdf9faddcd0804e3fcd9aceecbdeffe4d8e4b8da88998d86a88d8996903c1d39472e2c5b3138120c06240d12251427e9ece2f8f30e07220b111b170cf1020d0c0dbcdecbb7d4dfb0cac21a2df41629e418f4ee2024072e3b2354401201dccbf4f1c202f5e6d1d0c7ebe8cce2ccb9230e263a252b2c2d2a2002fe1e270d201b1fdbbebbfee5eedbe0dd0e0d0ff3dff6f3f9fcdffae40408ec01fe0cf2eee20cfcf7061708e1ff0bf3f102e205120520,
      4096'h08f1392e1936212c300f0b341a0c37230a06ed080805f50826142e1c2a151731312adcf0e21a190bf2f9db0228141a221dfe3a1d06f6040fedf7f9e004e6eaeefbf4dd1104e0e0fee1f712f7fd281b1710060bfd07f71721202c243c2222374f3cc6e1ece1e5def1eed33432243b3526373628ed02eff91e06e2e506f5fc17dfdaf8f0fcf7efedff0814070204100b1bf70c3011083d1d27340d2d522d354c2704fcefe2d8ec00d8e0f8f3fdfe0c0e0101faf1f4f10d12f20301e4ed21e7f30bddf2f4e21208101e101a05fe00f1fddf0d10fadedee1e0c9dbe2f7eddceef7275c304d6562485c55241aff0413020a0ff0e2d0d2f4efe1e7e3d4f501191fec23221712f4f0ccfff4d3e4eddaf602fe000a0df1fffee7daecfde804e5e5efedec04edddf0e7e2e2003a1c042b090d13fcddf3eb0aeffee8ebd6ff00f406f2fbfcf2eb354631443b56443f3d1f0f250b0a120d06eff508faf81c023a081a241403222efd020cf304dcbff3ddb4d9cdb0ffea06fee8f5f0e2e6080b050b0b0e0a04feccc1c7c4cac4c3beba0f1d0d100900170a04392e3c403e44482f5e20141b0dfc0c0c050df0f8e10807e6e6f4da0602fd030df9f900e30f231407030f0d05042008efebf0bc03f7e0f5efdb05e7b4dfb3927f60587f32157f3812349ea0019480eeae80e2f7d9f6e4acedc2bcdf090bbb060dbef0d33fccd334c1d5fab9cd30,
      4096'h0cf5a5c00b9bd4ca0b07ec2be8d521f0bd3bf2fd06b7b30ca0bb83d2bcc5e3ceaccb9f7f384b6f1d3d7ff83e03e4f2f8b1b0e992b4f0c1c7abdbebade3a82e09052b0fdb1aebeb4053617f3b357b3241d2c6e6b4c7ede5eff6a39e8dc5a596a39e927e3d5d3ee23322f7631305f42801f72f0a0a80a69fcfc780b7e0b7100ddbaddbd8eacfb67f4f747e331a7f571c10e7eb1ee6dc15d1e5a1b2cea0bdbf81afab0105eaa3a58e8d8e80d68796c38aaeeda0a747696c0f2834b3c8f1dccad7c7d1c6d9b78aa48b9e9380af92b2801bf7f22309ed2501fc0edaf00eebd2f5c6b7f4f9d3effaffc8c1c21b1c201f180e0f0c26ee220d1a2b380e291d0e18e9e9f4f20015f2d6cbbae0d8d0ccb8baacb7c0d5b8a4b3a4972c40f82100fdea0b161200e4edd1b780a7953106fded22f3f4f9e2d5ebc5d5d6d0b7bfb835201b32150725140ddbe2afb4dbef80b3ce09e9fa0af2eddb00e2281f3322221307291fc6a2e3adc5dfcfdecdeab1f9ccf3ebc8f5fd12e3c9d9dad9f9bbc437251b0f1614080a1920d5ef3bf107fff0b9e5eb0df6fa19ec1411253656433f2f39426dcdf3ded4d2c4c3b9cab9cce4d2dff8c5d4ecfffc03fcfd14f8f6ff0b1726000bfe0b0605dce3e1e5ddc8cdd2d20818341a11250012084047293843343d47500cfe2101fb00e8190edce410eaf617e2f1f3e6cbb4becbd9c6e7d7ebcbf0ddc8f9eefff0,
      4096'h0605d6fb2911161a144f2506610f084c0410bdb4eec7becdc1b3a02936f94c44ee0c37eb2d1b216af5017f0518edbabd18c3cf3811fdd7c28001d39405ce8c102835477a7f51747934efec6118cf3a23d9ccc0a61bdab50eddab3a00e23302ee2dcaf30ad4c75208e87f150806e9b14407dd11e6c92f14185112e827ffe814f6b3661fd42917c5693c097f56fa4034017f71537f7f6d7f66627f371d7f30156e2a0315dff33efbee53f2d7173be86043ff5a3a19eec7cefb04bcf1e0c71bfbe15d4ffd3e27f1e6d6da2214db2422ca3a04ff4211fa29ed084a1c2064fd014cec21eee6d90bfdd3fce19a622ad47b78d23043d7f8e6f85a192068020323390bfae208fee0f208fe104a601149563c240fe26d35e7641fdd401202772f1a48180b3d050003fde713ebe2d0c2e7bfa0afcd8bac7f4442716f177f66250aa1fa20d94ef9ae09d2e6d0dbe3cbdbe3cee5b1ebdfdad303f9b0eddaffeef4010b050f03ce2105e0e728edce38f3070ddcf60efd16eab4c5eacdd8e9fbec8080a18087c78080aa2134e737532c7d5a33d2a8bbcbd4dde5ebf5ed9fd8bddfe3e3bacb2c18ef2910fe202a2f7f7f767f7f7f7f7e7f808080a08084bf85adaba6a3afa59da3a19f1be0d721f4d57f1e362e35f43d2f132142f5c0b7dfa8a08088adb1b6a0fdf0bfddceaf957f7f5b7f77677f6b55dacac4f0e1e4edd7bddcbb07d0e4fbb9cf,
      4096'h179f80808d8080808088e011e0f1f00120f8fe9bc68080e395cae1a4afccabd7cca1e9c0a99e9f808080808080804b4f216b3d16695c2134331b1507fc1a230fd7c8cbbab8e9b6b9c71b1d041d1e0a201c15eee8d4cebeccacc4deb8c1dac4d8d4cddfdfddf7de01feecedeffdd4e6bfeae2b8cdc4d507f9f6f0fdf6eb03f4f1dcea0ad7edfed7e5f9c9f0dfdde2ddf4e5dde4d5dbe1cab0eecd513e343738153126030e01e416030cfcffd8d6f0f0dff1d2e0dcf2141e1f111a0f121820e7ebf7dcdbfad9e3f3f8fefcebf7eee4dfe71e300b3d2ffe21410a141406130c030e0cfbc3d8cbbdfdd8f2f9e0e2e70706f716fd08fbc8b6c6f4cae607d1cee9e7b4e0e5dfded0c8ec1cebe20eecb9d1e2ff0a020efe0b140c08150f0d0606f90b1afff8e5e6eee1d1d6dfda130419f1e8f30afdeb1e4d1714400c10fdf8fe2416061d0eef040400eb03e5d9f8d4e9d3f9f00ef6fff209e9f5fefffff7f8f9f4edf113eb091f1b0bdfedfdfef1f5f4fe07b5ccd83f605932503e273722fc0429e1d00dfcbff1df0d25cdeff0c9e1fbf22318c80923e007161b2220192b0e183a2314c4c8c49cedb2bcd7f2174c040e420936442a352a31574720332f04fffa1126f0dbeed2ed252bfb2230f10a180d1f1c13241e093e26dfcadfc0dbc2c6d0e50a281a0a4c3b1e4029fb1938fc3d40044040bbccdbf9f3ba1bec14edf81eec25edd8,
      4096'hefff3a4033273e0e00fafe1d3029fe34100029121147441f2b21f5fe15add51d8eb0eacbebf0282e462b3f422f53451b3e2f223c1ffc1703d7e2e0ea16f3b8ecd50c02060002ebd1d2e0e4eef8ebc5d2e9d0da16162ff8f71deafb090ce8070618fbdac4eeeddd01e4d5fdfaeaf4311c300c432d142c38160c31072638202635a799a4caadfdc580b7c3b9bed8b7cee0b9db50e89f37edcd4c3ab11198d6c6c0cfd5c398eeabe0e500043f47058080a380808097aa88d7d4d9e6c1fff8f6d42c200cf02a4b25524c5136754c2c5e616970effeed36f2173829239480dd9c96e78a8dc82c3928481b78681454d0cbf0ffe4dafcf9fcbca486ad97c2e3b0a0032c1e0d292938332b6f7f7f7f7f7f7f7f5ad51227c2e4f6ddecd7c7bcdbd0d8bdcad8ee2ffcb70a1fdb3b630c68535965225a6b4e47bd8d1db0c0ca8080c5e5bd98f712b5a7cab27f7f567f7c5a7f7f4f1bfcf521cefc13e0e9c2c6b3acb1bac3c7de8280b7a191bf94ac9405b1d4fe0bce3cf50ac8b492b4abaaa5a1d0ca80bdaaced69ab9028080a78080808087804c6953584c6363786e353d1c221616344b56e5e8e7f6eee7f9f8f6dfe9eae3deedeae6f3b9bdd2d1c102bfbfc0e3e7ebdae1e6e9d9e6e0f1ebebe9f9e3eef5dff0dfd2e0e0e0eaece1e2efe5ecfee1e6edd3cadde4e6effaedeaeceb05d8eaf8dfe0fdd6d8f4e2ec00d5f4f6e6e6e0e5dfec,
      4096'he5dfe7e2e7e1e2e6f4e3eaf4dcd6e7dcf2f7deecfedeebe4f0ebe9eae1f0eaf40cdcedfcddeae6eef1f7e6d8e9ebe7e5f0fefdefeffcf2eef2d9e3eae1e0e6e5dde7dfd3d5c9dad0e1e0c9e0e3edd1eceac8d8ebf1edf2e8eae3f1ede7e4e8eee3eaf2e3f0f2ebef01e7f4fdf3ff03e4f3ede9f6ebe1dbeee3e5e4e2dcdbe2dae7dae0ddcddcece4e6f1e1f4f0ebf503edfff5ecef05d8fdf3eef005e3e6eae0d7f6dde4f2e2e2eeeffbf6f1f5f7ecf1ffe6f3f3e1f1f8e7f3fbf1edf0e8f2ebe7c8d2a4bd80808080afc3eedcf2efe817f3253e432f38261d5a7bd6c08c17e42f1bddd87d6d7f692b526a3b73e50fc41d2b22f20bfa808080808080808080557f7f5d2df51c22ff7f7f7f7f7f7f7f7f7fb580a7b390a8ad80b6ecf8230fe22c091330f0fdffa0a6e2e7da25b788adb0b1a3d3b5e3808080808080808080de8080b78080ebb39c7f7f7f7f7f7f7f7f7f7f776e7f7f7f7f7f7fc7bdcdd1ccb9d4d2e392c9eea5110a1413143839245334537f7f72477f4c7f7f3f7f7f7f376306544c110b472c7f7f667f5f5d7f7f7f84809791839ce7bae4d4d10ec5eeecddcfca8aa8cdb8b4ca8080a0364f65337f5a462507eb4e7f5e627f10427ff3e8e20af1e70ff02c94808098b6808080807670334a7f6d7f7f7f1c13d61728f6685117fc0efe0e0b1fe8f6df0a15f401ee06dbebfaf5291d123d22214123cbb9b8c4a9,
      4096'hd3d5acaa0e01fa0003fbcef6dbd0ebb9cfe193a6d89bc3e0b8c6d2e2becfb2d1c5baddc2c7a4c6a10123e8fb1c0ee6f011c5b3a6c3f0c6a2bfc0344416270e23ff0a26cbd8a4bce1b4abacb4d8d9b7cedeb9b6cfbffe070b05fe1ce4e9f7d5e0dcdb01de9cd9cbe115e8dcfee6dde6f8ec01032227f60128fe1214f20df4f5d3f004a4a1a2c9b3b5d4b6f01f1c1e070606defb0ca1dfadcef4cec6e7b4aaa28bb2d48080b686faceedf02200ddcfe71a250cf8f401d3f8152d1f06171113e10717c0c3c6d3d5dbc0e7db13f6030f0916f0ece9312c2b49256b1f1e630e0b0e0af720eddc0a11e9f00603e6eaefcf02edf5f7e7fec6e3c6eff5eef4ead5d7d8d8e5e9dee5ede6e4e5dbe9e8f2f3eaf0f2ece3e3e3e4dddbe6cae4ceefdce403dce8f6d5cee2f401f0ff08e9faf6e3ebefe7f2fae6e1e9e2ecfcf2ecf3f4e7e4e5ecf8e9f5f6e2eaee06faf3230a0b211009f4de0303eafff5efe20301f700000004eff5ea05f2fe07f9f205f2f0fa02f80203f6f1fcf6e4e9f6e6f102e3d9d8f0e0edf5edf6f8e3de06f8f2fd04e3f1fb1d22181d241916190defdeeaf5e1f3f6e3e9daf6e6ebfdf5e1ffe4e6fffdff0309000d0205fffcfaeff4fadef0f7faf0e5f3f9f0e0e00112ff0e11010604eff2ecf5f1eaf1fcf2f309fcf60e09fc08fef1e0ddf9dcdce5d1c4d2f2fbf9f7f901eaf2e9e40e02ef120df3051407f2fe04,
      4096'hf9fd0bfefde5ded1e3e0dbdcc7c3f207fcf604feeffffaf00200fa09fdf8f8edf2f1f7f5fbf1f1f8e9e1e1d7e9e0e3dbdfd6e1fbedf7fdf601f8f3f0e9e9f0eae4e6d8dce7e8e2e9ede9e0e3e2eaf7e9edf1f0efe9ebe4f1e6f1f2ebefece8f1e9eff1edecf0ede9f0f7fafcf9f7fafdffd4ddd5e9e8e5e1dee4e6eddfeeede3dfdde0fbf5f4f2f5e9eef5f4cee0e3e2e0e1e5e1e1e4e6e2e6e7e5dfddc9dbe1e4ebe4ecedebeeefecedf1fdf80002eefdfffd00faf7fefbf9d9e1d5e9dfe2dbdbd1e4f1e1f6ecdffaf2ece0e9eaf1f7f9f3f8f2fc01fc0304f6fdf6eaf8efe9f8eae7e3dce1eff9f3fdfff6f8f701e2dadbe2e5dbdee0d4dfe7e0e8e7e0e6e4d8cfe2cfdedce6d5cdd5f5f3fafffefaeae4f1ebf9ffff01fb00fc04ecfbf1eff0eae2e3e4f0f1f0f8fbf0e8f0eee6ebedf3f2ebfcf5f1e6ece7f9f6edfbf2f0fbff09050709f3fb04f2efedfbf80401fbfccbe1dad5f7e4c1eacf130b080d0afdf5f9f4f7fa080afd08f9f8fbe9e5f4eff3fdf000e703faf00105fef70102020209fcfd0ef6f3070e0706150e1209040af3f6f5060408fbf8fcfdf0f9f9f2f704f901fd03ed05fb010204f301f2f5fffe09f7f7fef7f5e8fff4ecf9fef3f8fdf003fefd0707030dfbf80e00fe0d020b02010801fbf9060afffdfefcff0807fcfd0de0e6d2f2ffea01f3e9feede7fbf9f6010807dcf6e7f2ecf5ecebeaf3efeb,
      4096'hf2f3f4f3f1edf4fbe8070805040005fbedeffaeff8fefafbe7eaefefedf3f2edf7e2dde4e3f0f2f6f0ea10110e0b0808f8f6f5eafaeafbf8f9fcf8fdf6e8ecfdf8f2fcf8f4faf50704f604f4faf609fdfa13040a16030f05fe010c0702080602d6afc6f1a7cba28080dfdb07e0de11f0e30747375d70524f7f4e53cff7d70dc9a7ecb08faaccf9adbae8c581b0401fe6130cd8a1eac7e6deccddd7e1dce6d2d7b1c0b1abb589988012244d2f04173910360af612edfe0ce1d70ee5f304fef2210de039f8ee13f7cdf0ebc6d4d2e30fdbe701d3e6fe12f8f6eae6da04cadf293037180b1c2400215a6450674c5a7f6d69531f113d0d2a07051feee310d2d6f9dbd6eb22162a19052b1c0b4e3429432e1e424e294799c5d3dab7f19fccb2c3fafbe41cdab6aeaf24381a1f2812353828120d1d270d2a360d3cef0b09dddbfae8de0796a6dd95a3bd80849cf2d1f6f4d0e0d6d1a2ebeb22e3f9f1eef11cd4eefff0ddf5e7cfdfafd6dc80bbf680aaa0352a4d2135243d2d3718181a03fd0b09f20d2030212d3536363e42fafe0df40a04030b10e1cbddfae3e8e3e4e2f40b0804fffe0c0412eefef10805010503f2ff0f0e0f240c0d19fffbeee302f4ffff09fa14211a2b2d2e3a3029dde8e3e7f0ddebeefff3fef6f900edf9f5f70003fc010005fc050ce8f6f3fc01080d0a03ebfb010708fbfcfdf9031410010306070b0dfa00,
      4096'hfd06150afc0b04eaeefbf8070804011afdf7f4edf6f7fcecf5fc0208f6fefdfd0702f8faf91a19120d0e13f7f8f7f6f4f404f7f9060d11f6fdf8f40f0fff071207000b1002fed5e5d4fff7e4010bfc0514090302020616110409fdfe01fe060705fff9fdfbf402090500f0010a06030e00fc16e7e0c0def7d9ebf8eaf5050aee0402fd0303e5f304f1030bf8f302f2fe03f0f605f5faf5fefef80cfc0305050221e0b22362191024b54a3117605c1a663d05ecc689fae889cdac80f815ce2c44e12502cef7d7f230fff028f4eae0e3ede211fb2dfa1c8bc3a4b7b28bbfc389e3fd071b5164574b4af205ec03f5f62dffcbb3c7acf400c9fdffb9da1d0ff2ec28f1e707cdc5c1f0d6d2260496daf2e5efefd91b06d408f5c7310ec73321c6e5beb40ad1d10fc5a203fee40bf3d32908d16a4a12647c2e5e57602015f2512efd3a2af415e0e02e07e03c0a0303f2f01908f42a15e7dcd9d1225056f1eff4c1ddf907200318f7ddb8c0decdd3c502c7adc0dfdeede2f6f7e8c820f6f84c12013324fcf014ff2e31e90e30ef22f9c43a089f21ee91e2edbc5b25fa5646e90e16024831fa5224fa29edec7c372913f7e11df6d94420da4cf3c30fe6df11e0c912f3b7c7be8fe501a9a0ab80c6d8c3a5a9e7aab4c67f7f7f757e7f69757f80a1809cdc9f84ce80f7d400cab8c1d4c0a339f3e8e0ee38f1ebf3d7cdc5c5c9c1afb0cca2,
      4096'ha5cda480808080ba6d574e354a3d362a250e080cfbcdebe1e4e2dc00f89c84cd8c8380352e3f4ce42222102df2f903e5e1bdbbcdbcbc809e8fb087b69c98446c4c4b333a3f250d607f7f75785c7f78513435262b4537375c31b8bbbbb4b8aeadb5a4184b372f2c1262151a7f42667f2d235f4c418689aa808080808080bc97b7c48e808d80805774785a704b556129d5d4c9bbaebecbd9bd10d9e0deccd0c7a9bc80808d808080808080b2f3eaace1cecdbfd1e6cda8d99f91fba3c8d6cec9c09f8ea9808080a9b98080a38080807f7f7f7f74437f665e3661323f19ee380fdde5122fe8220103e5b1f6cbd1e3bbb0f6caa12f31624250292a19203df73c4b14331be905f418d705f6eaeadf9fecfc1400fe351217103def1124eff812f80d4c3e1e1a1bdc0e00e122e3df11d5eb17e90236010928fa093ef910eee7d107f4e5f8e9cd311836311c1d1809fb26fdfc22ebf022d8e02bf8f738f7d307f3b708c7e310dfd60fdfe53fecf532e9f74cfd0057fe1b30d607fcbac8e7cab8febdb6dcb49c042a7eff1c52f4323027f8e226f2e63304fc58001e771357181c3f051a3603f6f9d1d0ad39f40c35fae7470af820f7f12010fb2ef7fd2a1fda35f1e818e8d92708083a20010a09daddaf96cfaf80d6c99211500d2d2edb293dcafbe6cd26e3cdefdfb211c2f2eeadb4c8828024e80014e6f82cf0010de2e507d7e009e6d6,
      4096'h08f5f939172e2836371429052f3928344438c7a2cee0d3eae7e1cef2f5d20205f91bf209f00ff7f2170d32301afe0df91417160a1f12dacfd1eef3b4f3e0cfdfdfededfcff1314f9f1fbf0fd06e3182002c1d6c1e6f2db0605e90e1f011d20091b1b12d0baecfccdea15060bd5ddcf07fcf3f1faeae70cf704010c292c23d6e0ccf2f5e4fee7ebfed1d1fb10eb0b0e21242bf2233939091619ff0ef80f1a19322920c1a0b2edf8e1fb0b05f00cfc0915120d2d14bcc8aa04f8d4fe07d9c6fbf0e116fe0c0b1ad4bfeeed1efffc0f20f9f4edff0eff1e1e19fa1bed1a2e1936381fe6f3e3ed03f1e902eaacc6bbced8b8cfd4d6a6c3bad4e7e7d4fee70d17fe232c0123372dff2008213415122311ea0ee4fd2af50100fedce7df0e14fb1a0a093c1d3c0d034a170f0acac7b9bfb4a9f9e0ecceccf2d30217c6d223100507d0f31dfa043c0a13211bf24c4b5d4a1a2c421914247754463d3e2902281f550927566f49382d1b713867d9ccf8b3cff2b1a5f10b16132204301f105ad405d90c00cffad2df5a5b5e291f1d592d4ffaf00c1f2141293d43c0bfd7e0e2f3f6eff2808080a3a79799d39484808080a88a808087cdc0f20d2a19496365d5dccdecefd906fbfeecbbd2c8cce9afddde808080808e8dc4cac61a0fd1ee3cd42244ec3a2f552c1c4670526a0b2a24ea0c4dcaeb21808080809980b2b5bd808380bfab9b06cf,
      4096'hb11d0f1d5e635f7f6b60d2cecab9bdb7d5c9e43a6b4bfe192005fedcdae8a7e7bdbdfeded549403d64fa6177377fa6c098b1c8a89cbec880808080bb9c80a2b4261f2120182c0fe810040eec1f00f7fef7ece908fe4722302b28f80bf2edf6d5fceabc01d3d0d2dfdbd4b9c7b5e307f7f1e8dfdddad711e7da09dcef01eedffbcfd7ecc2decbb6c4f2f8f9ecebf3ede3edfafed703fcd4eddecb0f09f92a180e2102e60a162c1808090b01f601f7d503d7daeed5da16191430220e140701fcf1edfde2fdf7e3ee20080d070a070b121d1a0be62afac5d7d5bfd9f0d0eddbdbdac9cbf113f7452cee2b0fef25f4fc28ed1d160101cbe4f2e2f8e5bfd5c3cae300ebded4d9fcca1c133e1cfb351a0b1b2418003210091e0c040d04011ff0f20ee4e3e409e5f6f6c9dbd5a303c9f5f3d3f1f1d1dcf1edbd02ffc5f8e6ce2d1b024215fc330bfecad5e5b6a8c7aea0c71e05080aff0d0bf90b1ffd0403f1fcefeaf71f10082a1a15fde5e5efececeae8f0d0dfe0191d1ffefd1afaf31cf1ee0de1eeffdce500090519fcff08e6fc06fc0317f80c20e3151d061117ed02fee3fe0016fffb07f6f7fafff0e2daf2deedf3d8f1ff141f2df70b11f4fc060af7f6eef1fed5e3f9040109e7faf8f502fd271c15fd000bfb04fbf1f9f7edf5efe2dcf7f7ff01dbfb0ad9e901f70b02f90c09f805fcf1e6e6ebe8efddfae7e1def3d9dff2c3,
      4096'hd1dafd0f1af6ff21e8fe27e30403eceb08e4f70e00e4ecf2ebe4f9f6ecf90608f6f500e3fa0cf0ff0af9000df7010800111ef90711ddf617eeecfbedecf6d3dde1100d2bfbe2fce4d503effde2e9fafbfafe05370f15100af91dff04ede6e1d5dceed0d1ddf8f2e5ece1e1ddd9e6f4fef8e6fcf1e1f6f1ebf601f6ed03f2f307f909fa04fefce4f308f6fd05fffbf8fe09ffd0e6ebe7ebf7e7eedcef020002080f00f2f9140b111016130b120dfa02fafa0702f0fae9e6f1f00703fa00f7f401f70602000d01fefe090705150c0a0a00fce4e9e6fcfff3f3eee9fa060f0f080b021206e8f903ff04fbf401f7fcf2f9050300fe0002f607020c08090a1302f906f90afef902fbf8160c091f110b100b0904090a080001080405030bfd0709fd050703e7f0d60a0301fcf7ea09110416161f0c0b0ff705fa011202020610f70a05f70bfbf0f2ecf901f3040b05ff00fb040c08fe0905020f0f0b0a060d030718050ae4e9e4f0efe6f6ecef16172216150e0c0f0dfd050c050e110c0c17f7fc02f9f2f90f05f0fafe06f805fdf7ecef0307fd0f0cff1106fc16150f1c0f0f100b0dd9ff01ddf3f90213021e140750230451270fdeccc4f4d3c6dfd2a95125084e3610584d1712001522f7032d181f19d9e0fae3c004d1bfd0aeadfee1c101d6bff91b340e344c12464bfcf3cd0ff9da0ef5cde9cbd1f5e0cc00ecc9251311290213,
      4096'h3c0f13f5dac604e9cf1afddafcf5e60b03e62308d61824023619ff402a111107d72111de1908d12621e01b16ed2c14f60c243024251315252b342f143e14fe493406cab6d9e7cfd513d7b0331900192e013325061529f744442e4d3a332d12192710303f0d231207e914fee706fbf9190cf32d0ff3490f191a200c280e174b2b110f070f2208131d13f4311203281024302729100bee1e140b0ff2ff10120e0dea1a20050afcf9000ffe1c2a04051801ecfb11d615f7d42e10ef2616fa2d21f3d5f7f7dceae6c2e7d1e5feedf1fae8f8fbdd1efb0f200d041a03db14f8eb1a01e00bf6bdf0e3ea10eef402f5e5ebe5000fe9f1f8e9f1fff9d70508cd1310cbcefae5dd03dfcbe5defafff60b09f31711f0edefd70ffedc0901ddf006fbe1f7e40f08e3e318f0fe0ae4f105daf5f9e8f0f1ce07f6e6fffad6fcf4dce7edd6f50cdf0216dd040fcb111d0b0d2805112bfbf2e3e7f2f2f1eae9f90805e51800eb1500e7d6e511e2e003f00c12f9fdf70e00eb180be70502f5e4e9e3f9e9faf1e8eff4f3fbe3eadffeefdf10fee91200e3f7e8f6ebe9da02efd70604ef08f5e30efddeeff8dd08f5d2f9f6cf221ff8211c071119e907e6f8fbe6d302fce4f2f9dffefeea05fae50600eafe05f2e8edd7ee10e3f218dcf50ae0fa0df80415e80010d8050e0119241e5b4731f1dddcf1e8e104e7f3fdf4e1ebe4e9f9fddd0101ec2823,
      4096'hff051a000d08012f15125a35371d201433241a1c302ca3c4aac6c6b1d1fedf2c28186c583e3a3054919eaac8abbfdfd3eecee9ccfe07e91c160cf0d9cbe9ced21e00f324090b33100a442718bdf8c3d9e8d7e6f7ee07fbfe14faf8353816b6b3c4b0b0c8d4d7cfa4d7d9c7d8f6cfe3d601214a15fb1c364741c8c9cde8c6cfefe7e6b5b2a5dec6c7e0cbccc7bea0e5e0bdd8dec71521f72418e20802fb16091a3114191f2133c8eccae5dbd5e4ebf71ae3da01ecce04fde0d7c9e4fee4f51efa01e6e4fe090e0d13121ef2dce90208fff3f502ddeedefae7d70e07ffebe4eafffef3271b0fe5f1fafbf2150bfd24a3e1cdc7eae6e2dccea1cecdd1ede0f3ece6080009f7f608f4e301e7e5ece9eae105e5f0080621fe0f120d152019fc0620edff11f7fd05fddefffeeefcfcd817fcedeceee0ff0fea090d0e170e12161720030cf30803e202e7e106f7f708f1f80c01f805f5000dfe0c00100c111601160bfa2d1203fb0afc0810fd1605060901ff0bf5fcfdf9f706fc030ff0000ffbf5170714190c182616211611091209171b142306e9d3ee02f5d2daebfaf6f501f1f103ecee0d030ef71af2151d0620030917110e1808fef6f2f8feecf1faf2e2f5f0f3f305eceef8d900fffc02050408130d0b10071a12112b080706fbec0d02ee04fdf5fbfaf1f4e6dfefebe219020917f906100c16f6fe04f607f5f31405e5eff5ec,
      4096'he8e4fdeffef5f3e8f3f0ebebe9f4130108180311140e091705060804070f0a1002c906ecacb1f2dac300d1ec0ff3e91d01e830fa335af1df54f701eedde7f6d1e9e7d1e6cfc2d2eebeb3fce9baa3c617dad108e9d9d328d5e468c4dc4efee4bcb4e3d1be9bccc6cc39eccc43d1c743f2ec2507e442e7dc4801db2c0cf841262140151bd5b6ea13b9e127e2e943dbcb4fdcac3500b9c8e3dee2e5f700f30737e6f161fff145fafb30f1fb4ee7084f01061ee5f3cecab9fac9a9ecb9b8f8c0b6f8cbc395b4ffd5d9baf3bfb634fbf74dedf92f0008bbd5dad0d0bbeaaaa4dfe1dfbd1db6e6b3804aff01560f0f561d113bfefe3cf70228f80323f0f228140e490d1dc7c9faeebaafe0c3800ad3c907ccb301d0c6b7dfc5ccd5e00509c91ddcd823f3d009cce7c9d1eacdd3b5ecc6804bf0d37109ee6b140936ecd545f0d03ff5eff8dee0f3f1d7f7dee2f1cedbe3e1dbd9c9cdeaebf3ecf0f8e8ebf4efe1dbede4e3d1deddcfced1d1c3d0dad0d9e1d6d3cfd3d7ced6d4d7f0f6e7f1fef1f9fadae5e1dfd4d3e1dddbf5e5f708f3f605f501effaf2e9eb02eeeffbdeced7efede3d6d9e2fff6f906fbf5060206e9def1e1e8faebe8eee2dae3ebf0e2d7d9dbfee6f0f9eaf5fef6f60cf3ff01e80210f4051f00ff18fe0514fe00ddd2d7e4d3d3d2c8cc031505ec08f5f1000af5f7fffef1fdfef0fae8e4e1efe6eeebf1e1dcdbdf,
      4096'he3d3e0d2cdd903fb0301f0f407f8f3f7e902f0e9fce9deeeebd8e2ebdfd7e3d6d2c0c0d4c7c9cac6c3cde3dedfeae3e1e1d5ddf2ecf3ede9eaead5e6f0dbe9f3f2e8ebddd8dce1ded9e2d8d7dbcbf6e6f0fde1f4f7ef01edd7f0f1e2eaefe0eef202dce1eee3d5da12c8f807f5f1f5d80bf7ff1220fc171f011d24e5eed3d7d6e1d8c4edbfebe9c8dbe8c6ebeaf90304f310f1e4110406f40af2f80dedea16f2fe0ee6d405e30201e9f014daedf9e6010be1fdf4e0f6fbedeafa0e200d1f3723122d39df0af2da01f1d90418ddf5fde4ed01e4ecfceaceefffeffbf2fde4f00d1d050e2812161e0f2a37112838192d3bdcd1e5c1e6fae0cbd2bbcfcbc8c3d6c3c1cf0e171e232a192e5c34f80a14071500111f1fd3dce6d6c5faf7ded8e5f9ed05fdcdeef1d2fb102907091d100e1eebfe13030c1707170cef0d1cfb041603271dcfb4bad8cdd2cbc9c9ebbfb3e0bfb1dfd5dce11216061436fe3a21f5f4de0ddfedf9f9e9d5d9efe0e3efeee5e9ec0a16f50219fd0a25e50402f80610fd080eef0a15ccd3c1e2fccf0ff30acab1c3d9e1077f7f7f4d39530a384e334f5922fc2e513e3af8fe24b7ace6ccb30a1a490b203163152828735935e8cd08c0e7253f3743f7c3c2bc9ad7f3d503ab9bc5c1acd65c2b61fef6191f214f041fe9dbd4d6f4d9f04a4f4bd7de10b1ba051b0613aebad09ba8cff1fbf0d5d8d2c2ddf00ce7,
      4096'h0fc49fd9ffca14dbcbe197a804ce9c0d2d5559d31e23b3db11e5d2e5b8b2afc4ace255294af408fcf6d9490ef3faf6cdf008cfe72e4b1c253439ff302c484b5f0ae0ff31525e433548d7b115daba3ffbfce9181507081304e5c9dac9abc8d2e0ed7b63383d3147433649c4c3a880808099bdae310522e9d9f3adcef2512f2a2608082d2653d2f0b8859b990f0efd0fdb21f9b7ec08cf15e3cecdccaad6f8cd0af50001f90e0cf3eaeee7eeeff105fcecf2e810090e21170d1a18131901001818000ef8f50c0908100f080c01fb020707fffefff2eceef402f4ff040af4f1f51c1919121d12151606040800070b0c06fd06050d03020207f9fefdfc0603ff00fffefaef0e1b000d0d060b0d0607090aff0106eff7feecf5ee00fe0805fae9fd0afe01020af9ff08fd0efd000f0101160102f8010d1111f7f4f8efeff2f7f0eff9e6e3111a151f18151927130b0d1000fb0607ff0ae4f1f3f0f8e9080bfa0b10190f160d010af9fd0907110e0afe0a08fdf3f7fc000001f1ecfc060a0d12080704f7f9fcfff502fbe8f1f309fff5f8f2f701f9fe08f30a070003150b14e4ecf0f1fc00fce6f2fd0000f908f5e6f5ecf50cfd010900fe0401f0ff03f70207fe0301051006040e120cfd0ef7f2f0eef8e8f5f1f6f1eef600fcf9ff0502080405010503000615feffe0fffcec0203fa03e5e203f4f3fbf7e81d1515231c0522091212,
      4096'h06100e101e13140e050f000101f702fbeb0c10010f09f515fff3f3fcfdfff703fff2f3f4e6ed0af7effefbf80a1f0a1110f70c0afe10fd09f7f703f6fb070a0afe0bfdf4fff0f8edfffef30107eef3f9ef01fbe6f8f4f2f804fe05fb00fdf9fffd02ede9ed020802faf4fe060ef810ffe60bf5f0030dfa180106091a0406fbfb03f3f4f6f5f3f2fe12fc01f6ff02050a090c08f7fdf8fbf802faf7f9f3f1eef2f708050507090d0c0c0c0efaf1fff7ff05f80503fae90b0af91ff1fa01f4f0edf6f5f4ebf005eef5fbf1f6f703fb0205020bfdf8f4f2f00a05fb0802f0faf5f9dcfbf6bd9a950a2e1dccbbc6e2a7b523f8c2f58080b88080898680d7d4e5f0bbde0ff10e4f26512333686d6c7fe1cc06f3d2154b517f220a445809e51e0d264408172a225855747f17040428fdf73102245c204544384e42425a808080808080808080575e5c533c4f57344043275b4b3b6159427fbc99c6c3bde3def100fbddfed3e504cbf815f10baf92d0f4a88deae4ed26f8e72f16245bdfdaddf0cfeefcff0b9ea28b908080808085ace880b7c29fa9eb9fe4f6f780d3bbdeb9eb537f7f7f7f7f7f7f7f6b5f4d39283d2b313998af808dbf9980b9808080808080aeeaadd00c2e472c21465c4441c1b7b680aeaf9bb1b3ae80bf8c80b080808080878e808e80c6e0c523214336353f7f6f750b05eef1e819a9c910c9b8ebcfe4e8c9c1f2,
      4096'hc3a2e1abbfe28e809892d0adabbfee8eb69c213cc05e7632603e1cb7a980bfa5c6ccb1a1f6fd0ab8c218e1c0e1d9ddecec17cedcf6e1f2f734e0ee3dedaf0efc0b6b1d6c00fedcd77f7f7f7f7f7f7f7f7f4c7f7f437f7f604e7f80c1d48fbdd080c1993f332cee267fc5f02f497f7f1b727f1f2c3199cdae9fb4c2808e9d26797f282d7f27434735627e553c6c5f2e413247647f6d5f7f7f70bee9e5beeef6a3d8b99f99e3ffd7daccfcce22431207254ae3103280808080a98097a490d0e8fed0ebe9dbd91a575e7f747f7f7f727fef01f3e8e9dfccebc085d1bd80bfc8809cc2dd060be3f3e7adb2badbcff1deb0c8918080d7de97bab6b298999580999293cca080818cfbed17c1a3eb808097657f7f76667f7875783a4f4dfa1536272128090f16040c211c18fbf802eb04fdf70800e9fee9ef05f816070c150d0c120b050d1c02fdee01eaf002f6f6fbea0501050802f30c15fbf3fefdfeebf4f8faf8fe0bf40002f1091afce6ebf601fafcf8f5fef6eee200f1fbfdfaff0ef9e40c01fd0c0af6fb01fbffedf5fafcfeede1fdf7f2effaeeecf900ee0903ff0103f009f1ec0404f4f901fe08f6ef03faf504fcf5ea00f702fbff06fdf4fef2f104fcf802eeecd3ebcdeafae6071407f1ebe1fffdeffc09f3fc00e9f2e5f3ece5e6f103f7f9f5f709fcebf5f5ebef0807f705fb01efec0bfef60b01fbfff1e8fff7fa00ff,
      4096'hea0904fa09fff90dfbedf4eaf3eee1e7e4e7d4dffbc4f9f2d0ecfcd71302000c070b1308fef3fbe8f9f4fb04f8f2fef6e7fffcf4fefcfa01f4f80407f8fdfff3e31c15f5173216f908060a02050312071603d9d8aefdf2d9f1dfd0383a3627293b360a1ed8cfd70ddee7e0d7c8add2c3a8e5c1ddd9a5f6faff2302f3f4e9d7cc94e9d8b0ddb0cca00c1efc21f3f70df5ddf4e1ce0bfbeffbecd413140a08fd34150f43b891b1d3cfafc8c98febf3001b00eef7feee04f3fbfffa2112ee0511120e392423331808050aeb1929e607020bfcecfad9d7ef9797cc23312a231c1e241d1bf400d71d5a0f3419f54014093f1e00362e0ac1d3d1dbd8d1c3e3ad91a5a0979b839aac85f8febd1ee2b6dbb9ac66514264312571504823271e191828312b1de2e226bcd5fdb4d2ec232a1a1417272016248180808b9a8780869907e9fc1ff7080b02fdbfe3fdaff7f896ade31917341b0d012908fc482f4b5c3729402a1304e8ef0c051c283226c1da02bbe3e5c80105da18f4f5112000091ada0507ed13df052a06b8ce02bfd905acef1001363ccd0c11e2341f102d512c2c562b2f539facbaa8ded6a2d0d3e10802ee021af60822e00238f1083d020a4589c6d5cebfdcaae0d9d00e2ace0a2f020132e20017dbff15ebfd14e7d917e9cf21010efed8fc17df0425fe0504fde42d010d34fd0636b2c1f0c4b102f0e2e49ad8f4b9e4edb1,
      4096'hdbe8b9e6feddec0eeef225c0ec17b602efd6e7f2eae4f8e6f20bcbb9bdcce216cae1e9e3fc0fee0a3cee183605150cd80a29f20412f4061894daf3abe300a5d2eae704f9fe0102f21f3ab9c8bcd2d5b1d8ded6b8bcd0a5c806cac6c9cbde1ad4e619f3effce90800e2dee2f01ffee3fd0fcff70fe90e23cbf217d2fe17d2f40600280b38fd2739211ebfd6ddd2cae1cfe8e96b7f7f4a7f7f537f7feed3f892bcc8a6d8d8efdfc2c0cfe6a7ccdd391c0e2f0e0c0d173c292b510e0d3afb0f1821ff21b4f619d0bdc306112cf0fd10eef1152f413ff31226e80b0a80809ca39da5b6aac3556357194d460d543cf8ff2aebe20fefe905e8dff380d0bebdd4b109071fdb0a22ecfefbf2180cd0f52cdbe80b8084a580808f8091eda7a6cb9289be91aad24f666d31404a17255126fcd2fff8ccdee6d952383782e6ec313efed80b09d6dde0c8c9d60c2c2df30222da0b1b2e051a311b2313371ec5d6f9c1c7e2b59fbb9f9cc898a8b5c9b1f48392d081a4cb80b0d9e60f02e912fde03102e6e7e1d9d107d6f3e3e31c1897f8d5ee03e5ec0708c2df15c7da04c7d7f2bed7e6c6d9ebeae10bfe0301171ff6271a111b120d1bf4f042604561737463794df5f1e1f1e5eed9f2bfa1b2a99ccdc1b3cbc3fa1117e00fef08fd0d11f21939fe2821180dd6c5aebdc6c89887ad10ccfc13f1d433f4faf2d3dce801fbfc0af729110912061a,
      4096'hfbeefdde93ebe995d7dc9fd3edd8edf8eef102e7e81d08ff32110211eceb2306e223110414fa16170f1c15050d09f30dd3adacc9b6b9b1c8de0106ee0b04e7f2e9e7d8d3dcf403de19d3e63010e51efded130aef27f7ef1d0213f704e7dcfab9dbb9afe1c6accfe7f1cadacdf5f7e33f3139423240382a2b3f1c1139180f1c0a0aeff8e1fcf4f8dfc3cdc3a7bbcaadbdcfd2ebd4e4b0e304a5becfb2430c043a05f827f9f3eacbe9fcc606e6c5ea2a14d5201af32d00001d03d71dfee71603f0f5fafbfefcf9ff00f5eaecede7e9f0e2dfe0f5f4f1fe06f50700f7f5f2fdf4f5fbeeedeaecf4eefcf3edf9f0f6f1eff0eff2edf4eaebeffbf9f8f8f2f9fdfffaf9fdfcff0204fd00eef2f7f8f7fcfafff9eef0edf1f8ed00f9f1e6f2e8f2eaf3eaeddeeffaebf1f2edf4f1e8f2fafef4f9fdfefefaedf4f3edf1f6e7eee3e3f4ebf3f3eff800fdf5fcfc0000f9fbf9fcf8f2f0f9f3f1f9fdfef0eeecf2f7fbe7e5e9f6fcf4fb00fd020505e7f5f0f4f7fdf60107f6fbeafbfbfaf6f8f1f3fcf4f7f9f8f1f4e90200f702010000fcfeebeeeff1f6f4e8f5f8edf0eaf4eaf0e5eae5d7e8e1d9dde2dfe3def2fcfafcfdf8fefaeff9fafbf8fefe020005eeeaefe9eff6ece4e9fcfcf5fafbfafbf3f4f9f8fc02fdfb010608f4f7f3f2f6f8fbfaff97d7eca6ce0ce70bccfbfff204ee1012f70014f5310f28501b392dc88ab8c1cf,
      4096'hd0afc8bf1a2d17144e3ef72910010e0a2ffe11a9bfae28db0c2e0d3a38042bcdc201cc90c3808080fb20041c2046d9cf0dfab4b5d093b1b2808819fbfa16f2e308e4f9b2cd05b4c7ffb0c3b21b0b392d0b3a12f22ffde3d5d4d1d1caafc6e0deeee5af0cd2a5dbfefc05ea2428de3e161203a2f9103ecdc0df020df70b080205e9efb7dafcce19dabcbfc43c062f36231c23fb20f9defde6e2e8272330c1d6dddadef1bbc6db9bb905ad9bd49fb0a424140115fffd18ebce2215151a151216f6139db8cbd9c0dad5cad0556a567271597f7f5f7f737f6a627f567f7ff8dedef6c2cd0fe0d9f0f0d3ce22ded5dbd2cadca4b7bac196ddbcf409f0e8fa2de9f5ebead3ec361501606c5fd6b9a9fcebe216f70efe0903240f162df8ee24012e3e0b0f4e3e5095aec012e407291c1905fb3308253a6b274f1eedfc11ff2411310cfcb2d63109f9242906bc9480e19880f7d8eff7f1b1f5c5b213fd080fe4b0300af3032a0fddaaa70ac3b9120e13d4d19ff8b9ac0cd6e805e6d01d0cff241932f6d9be1c0cfe211cfff1c4acddcedf0303e5f8e8e42d2b284f3c56c9d097fff3d5130c1807decc1d01b620d8ec15e9a92702d3281febf4e402f3f502f1def2e7ea09201f42585d6401d1bff7d2c2ebe4c11305c82a0ef12d11fac7ad9500f7dd070e0c0f040e39293074675bada386f3d1bc23f80fc9baa2eac1cedec8acf9d6f11b,
      4096'h290b170f3ce4d1c42808123a3a1f2ae6bd1dfed922f7e0fcd3c113dc0d2c1826fbf7f2f4f9f6f5f6fbe9e5e0e0e2e8dfe7f2f1f2f1f5f4fbf5f3fcf0e9e7efeef9f1e6f7e0e0e7e5e2e6e3e8f0eee5f0ece5f6ece2e8e5ece5f6ebf0ededebf6f6fcf7efeff0f3f6e8e8f3f1f4f6ede6e9dddddce4e1ebe2e2e6e7e3e3ebeaf9e5e5f8e2ecede8ecebebe7f3e8d7e4e8e7ebe5e6f1ebe5e6edeaf3ece402dde8deefe2ebeceee6e9eeeef5eff5f5f4f3faf4f8f9f9f6f3f7f7eae0d9e8e0e5e1e0f3f0e2d4f5f5ecf3f2f4d7e6e0ece5f1eae8eff6f0f0f2fef1f2f2fdf1ece9ecf2f1e7e9e9ebf1eefbf4f2f8f7f4e3dfe0e5e0ece8e9f6e7e4e7dedeebe0dcf5d4cfdeccd4e7d6d1e9f5f4eaf5ebf1f5edfef7edf1f0faf7f8f6fde4e6e8deebede4e201f2eaeaebedf5eaeaebe9e4dff3eae7efefede7e6e0e7eee6e7edecfaf2fdf0f4f3f1f2f2eed4e7e4d2ddcbc2c9f5faeffaedf4f0f007e7ece5e7ece9ded0d9d9d2d4d9ddd7d4cdd0ede6e3e4e5dce1d4deeef2e8eee7e7e7e8ecfaf6f4f5ede6eef0eee3e5dce8eae7e2ebede6e5d7e3dad6d3e0e1f9f0f5e6d6ead2cecff2f6eef4e8f1ede9e7e9dce9e5e3dce4e3e1eee5e7e0e2e7d7dad7eaeff3eedfe1eadee0f8eff8ebedefefeceaf2f3e8fbececf3ede5eedbdee4dce1d5d1ceeff6eaebeee9f7eaf5dae7e6e5d8e5e6e4e7fffbfdf7f9ffece7ede7eee2,
      4096'hebeae5e0d7daeff3e7f2eff0f5e9f6e1dfd3e1d6dfd1d9daf4d5ebe2d7e1cbc5ccd1ccd6d7cbd0c1b3d4f3e9f5efebf0e5dce5f1f8f4f8eaf5f9eff2f8ebe6e8dde6d9cfcde6e7e4e9e4e3e4dbe0ebdce7ebe8e9eff1f3e1dddee6dce1e9e2ef02070508090a11080ff9f9fc00f9fcfbfd02000008fc00fffafef4fdfd0902fe04fb01fb0003fa010a010306fef7f604fe02fff501fffe0403f803f9070a0706050906090b080c05fd0203feff010001fff3fbf1f2fffb0202f4010600fd0302070103040407fe030c0508fefc0502f5feff00fd05fb0308ff05fc040506f7fffdfa01fdfffcfe0104020405fd0201ff0a050701020200fcfffafdfefaf7fdf6f9ff030402090dfb060101fefbfcfa04020201fa0a030c0c060b060b09f7fdfdff0302f802ff0204030001020f0509fd04f8fe0200040802f9fa00f6f8f7fdfbfcfafcfdfa02fdfd02fc050807030402fb0203fffffd0700030907fcfb0200fdfdfcfcf60003ff0500fc02ff07020000fc0902f908fdfcfd00fefe02f6fffefe80808080808080809601060a180c25e5e8ee808080808080858080829280caa78d8c80801105373515041c3105d2aba590bea38080e4808080809a95808680480c1d3812f5fb24dd497f3c7f5d2c7a4a58e2f0f1d4f7fbf9e0c94968576d3c7e525373878380f28ab4e2af8d01f114fae1dcfccfc1d0a9c4e2c7ddfac1bbeafb,
      4096'hf304d9d829fefd2e3d2b78362b7f713c7f787f7f7f7f7f6c1fefe5f902f3edf3d6e94409b97f4df4523a087e687f6a4c537f6a35cdf5d7b9e5f9b6b5dfecfdf714191ee8a4d0ddf50b13ef06f91aec23f80d30f80f1c0bf3e8e21cea0d37fff8fdc9cdc7e4ffeb93ccc3d4dce515fc09e4f30bfbe0003f412e473343d4d607d2f913e6ed058080808080808080803c46165558347f5a284f571f644144746128140efd24fb07e715060c09f4202202151806b7cdc9ea02dbc5fabf1aedef2920041b2a10f0dbf0f3e9eff7fbedf1caba09e6dd150df4e4ecf3f4f6f50e22fa03fb001b1f1338351fb3c5cbf6e0f804f8fafbd9f81101f30e0d00e0ebd0f5efe7f8dbd0efe0cd17fae90eff07f8fcf912090c1a150012fad715220612180ed4d1c4f2ebd11c12f4cee8cee1fbee05fcf0e1bec51418f511340c0b0efb011e02070d03d6c1911cf0d7e6e8d2dbddd0e1e8ecf6fcea1cf8f80efbe3202119fcf0f1fd04f707fbf3dbcfcae6ebd90300e7e5eaddfc04e20af3d4fafad51215f5f0e8f80c03050f1e2b201935e4e6caddd7d1ecf3fefc050f0af9e00805f30602e5ef080406250d09f9eb0c04fa22340ccaf2d5eee7e8fef0e4d1f3da01f8eb0d050de5d2c6dfd7c7fcdad8110b0d02040d03f2ebe4e7d3d0bbb8ddd5b0e9f7f0d8e4e3e8d8d3e4e8e6ecfae0d2cfecbec8c5c6d0d5a0bdd5fff2e6e200c5eceedadc,
      4096'he0f6d90efbf4d1ea0d10f8000bfe03fcf4ecdac9feffe7e6e8cb2527331b101101fef9f0edcbedd6c9dfd6bee5eddef50ef9e5fced0e2323fb131af302effcfdeaf7fcddf500df211d020c14ee0400e61a10e00fe8cc0417ef16060702070affedf307ffd1fd0210ece80e0a1c17121d111111f6020e0b12fb06f3020701f5efe1feffdaebdf0405db07fde7fd06e3151b23060a17f5f8fc0403fc0d040400e9e6d1cbcdced4ebb5bbcbfc06e9f6e5ebf9f0e90eff1103012219f71f1e2314231b080cfa03e3d1d4d0d1ccd0cbd20a10f40e17ecff10da1109fa1407f20307f8070a04080b0b0e080df5fcfcfbf7fd02fbfef1f7f1f0f600faf8f1f308fff702f9f6fdfdfafcfefa0201fd0103080a0b0e0907080d060204030102ff0007f806020c080b0c090b1008ff000800ff0a01f80100f80203fdff01f3ebf9f8f00103f002ff03fff80805010a01faf9fdfafd0304fcfbf5fdfc0403000d050203ff01fcfe04fe0204f70106fd0102fe00fffefdf60401ff02f8f8fdfafefafb00fffbfefff6f3f1fc01fbfefdfb0001fbfefcfbfcfdfa0205ff050a01fd0a07fcf900fd0706fe0703ff00020101060207ff02f7fcfdfc040303010400f8ff0002040402f8fbfbfbfbf8f8f6f8ff0508010602060002fdfcf6fdf7fdfafeff01fbf8fcf7fdfcf6fd0d0f0f0c09110e070e010105fbfd01fefdfa0200fc0101010302f7
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'he52ff9fefa2a1440467f5a7f463e4c55096b3901161a06153d1312411b492fca4125283030f12a20043f22fc2cf6c1f21aff241b093ffcfef7ede8db0a08da6b2143341a450617281ffbf618fc14fbec07e8f3f327052c123c14393ff604f7f34b1813fe11f7f804030121151703151208f5eff2f82f14300dd01222032c303c1c250fe51f03e10deb050712eb52314f09dbe008e3ee0bfacd4d052208ef0917fd0430050d0adff90b2a1c5855446311ff7f661aef20111ffc11e6dee53f1a2e4e2cf4521900381c2c03d51d1fdd1433102bf4e2320002165e403ce1d621b4d61104100ef315f0f9fcf71214f206fcf22824f67012291ffc1a5b2e4b471b471a111a23082c17213f511df45a28341cf321e9c117292942407f7fc4387f7f6e7f13250df7f2fddfdddb7f3f5e7fb9467f4a7fd0d7f9f827f1f5f5eb34122507ea152f0ddf17ecf903f70cfb080f17392e19404300555c213d3cd5f319f5fc214a0c6159f7757f6c3cf2f208f9000a1200134a3778024a6a0c0e502e3c164420fa123028f6edcc1ae2192d2b365f045d3ce1237f7f7f3328282e112e331f3143fc152714013a11e4340834009c1f410d5626342a1ee81a10f70d18fdd2d801f00437170ffa18f0cc0c1e040c3020452ef8f94e3b357f487f61da307f7f7fde0b2af7e41e60ea131413eef40cfb16f41046234431a62c300d38441a7f1bed5bb000,
      512'h39e8010aebf015f202ec091afc11030bfaf800655b2c34e9d7022a441a031708de071e1919461c6339fa4b7f4c7d3506f53dec0938301d1e15f31ef7eb09241a
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'h04fa21dfe6d80aeefbdf372f01e73de10338c51124e5fae5eaf3fc291d0b1d06ff02e211ffe3eceeec0bfe2d12ecf7ea030cf6061c10f7da0b070805fcec120b4e18fcd8d01a271830bc20eff3cfabe302a702edc2ee80f30cf9e6b033f8be14465f01e6f602d239251217e97fd68627dd6ac6d8f7cf0a917efaf368803ed90bfa102ef8f90208db01100e0a08fc1ff7faf7f2051de1f3100a01000911e7020417ecf62afceaee09ef0906112102ef0cf20c0013fb0806fc09f9fff8fdead4fb03f0f35406e234da01fff813ed3904cb0d0e08110d4b1edf09f61404d7ecfc390def24f4eceb011105133a2e4b2923ecebf3dc1f47effe25180404e53befe3fff4d804f509fdec36f5ebf4eb0318e7f00e0e16e80adefb18f1f802f7e6e7fcafe7ca08fffa0006ecf8cbecf2a2d5fbd8d206f90cdae7054cadf70c0311cd0705d18ec80ad97ff8000d0dad341132070c2fdb46d4a225ed1e180338b512fad1e3f480dcb80101d6e42480fd3b84e4fdc8f73974f5b1f6f249800af7e53bd4f617e2eefae4e425c6f1f808ecdae1f114c004ecf2f4fafae7130d02eee9ecced4f9e2d7e30dfadc17d6fdea0d0fc509fcfce2e5130ae9fd07de0a020be2e7c0eb18dfbe00c0e5f6ecf8f3d6efee08e5efcbfef9ead0fdceee09cf0506cce4c1d6c8d4a4f1f30dcde9ba1dee10f9aadee1a3dad0f19889cf0cf7b6f808e63e9cf50c,
      4096'hdae0e31be429f22903f1e2f12d13f9a8f8dde2e0f806280ddef9e8bcbcfe93a5cbd1fcfb09090593f7abe6e98011ff1402e2e98080cefe018003fefa199b14340023f20423f522f6fceb2d03d9fa04bcfb0ed013e505f2f0110401ec01e7ef2518fce9f0dfe029e0fff81ff0051508e4f804d50e07ef02f411fd090700d91e0d1f341ce3e6fbf5fcfff4fb0b12ef04e21409d416f803eae7ddf3f630f0f7022cfb08e9130bf3f5030219211a1618e2eaf2f2f810221dfaf92602fe18e00702fd01f60ae5ea00e6ef02041210f5ff06df101eeeeefc0110e5ef040408f1f4000e02e0e7fbfffbefea0f121bfbf0e0f7c9fefdea0ef40504d31301ffee1adef10ee3daedcd27dcea100df4f3eb070addfcdfc716cfd703e82adcf805e0c0f0f4c2c603fbfb11f8fed8e5c3ff01ddf2d5a9c2dd36cb8ee7f23cb7fef9f5e8aa2513bd98e120cc7fe342004a11f7dd7ff985e7ed0cc7f8f11b05cf12fac4fff4f48f068025e9e309f193d88b34d480c10204e1c360e1abd2085c83fc05bd45dffbf8070905abe3d5f9b607e2e4e7fedde9e6e207dffb01c5cde3eef2e2fdf1c2f20612ede703f1afe2e7e3eb09fa00d6ead6aa27c7eafcf5f1c60df5f9e6c5dad30ce7d5fae9e1f1f5f404ebfb2af4f70decfb12f5d4efedf30fd9f9f311e0eb12cef0b1f007f3faedd60a170029c5e9f7c1e9d90be8afea0812dcfafdfa27c61a09,
      4096'hf8c0f484b2caf88508a8d1b9dcb6cac9ffe4d9b3f4c29ef0fc05ecabb480d8a5d9810ce5e690f89cdecbf807c9b8c1b780eca08c84df0de4b5edfdd9d580c916f2f009c3f2daf280fbf0efe200d7e6edf706defe1ed8d6dfe301e9f3efb1c90904ad0011f7bceaece9e80df800e8f4bfa5fdd4d8e806f8c6f90202eae2bfce02e4c5e6abe0f4dffa06bad3f7e5ebedc7ecfa05bdf6d5df0fde02fedbe9c0cdced080ed05eabcdcb5f3daeef2a4c5f0a2bac7e2a8a2e001d5a7f807e60899e30506fa10e5e9f909e7fcf8fdd4d6e6e8fae405f613ebf6e4ef14fcf40524e3e20b13f5edfeefe11ffcfc1ffd101510e209dc1af7050f120ad615f1fc24c5e3df0719151cece9e7f9c2f8dfe4f507f2f7edff02ef0c02dfe2f8e701ffe2fbd9e80f19c60220ede20df40c070bf01a0901e3e3e701e8e4170cef13f3f7def4d7ee0d0accef84d0e005a519c2e2f7daa7d0b4ece180eff20b80dd2c1906d6d080d0d5e7a623f8e980f5d5f0ce32c8afb0e002912480c8a5e7e59cc31afbfec097cdcfc621f6d3e6e4dff102f518d6dce920b82603ddc206e810e6d5fc0a0be6fc1122dca9dde5f0c2dfec1b1730f6f7b715bbf3f5edc6ab0df210bcfefbdc11bc0911f6cbfad6e4fbdf06f502eefe07fff8b900dee3dfedd70316d501f0bbc1e5ddcde7bbfaf025ed04a6fdc301ffaef2e9f1e0e5f0c996e3fdf594f6f5e6249ff107,
      4096'h8dbcf4dbea7f0e4ef505dd26f773efe8eff61ddc0a0d63faa7ed31e1041addbe3a8020f0f90449f1ccae28d6802a39fa0fe6038080ca00518003030922cd13e7eac4f6cdddcafcf904dddcf1e4eafe8c0ae4d1bf0fe6f5edb8f3f0dab2dcf4cefcb9f3fc11ca01cae7d6ed10bae4d9e5d2e0c9aeabdcfe03a004fce6fbb7ec00b2eedc01e4e3d21bfe0a272709ffddf5eb0009dffffdfe1ab502ee15d0eafee9d9bcf2fb1104ee8303e915e4acac12b6eff83adcbb1cf93c9bffff0c1ede45c5e30c0df2e8fa01e1061a00f3f34402d30613f104feeb32f003f4fc14030af5f812e60a0502fe1609f9f80904fc10e8c2f2f304dafd02f8311205faf727e4e107e880f413779e2509fef8e055098095f9fbdce5f1c5dcbf069f021621091d2d01ee42e6f01374dbf0fc43b20662beb9dd0732071a132bf8e306fbed11801ef80a0196f480eae8edbef7a7d1dff6d0eedff0efeaabd2d19911c3e7d4c1abadd0cff9b9d6f1fea4dfb1e7f8fb0fc4b2c4d797c7c19180f615f5c5f10bb10898f308e3fa1189ccc7f7cd0dc40fefdce003d8fe0ad5e2cedbf8aaeff8effccfecf81acedcdbf7f5d8e0e5ec053af3f9b6dfd7e5c7d1c4cfef0fb8eff9f1e82cd4090f14121a03f80523dcff0e1702f923fcecfb120a1dfc06e6fef8f9f40818e411162efcea030edb0bf8fc08e821190be0fbddfa030d231bfbfb21f9fd0ceff1fa02,
      4096'hf6bcf69fe613f4d9f9ebe3e3def6f1e9edd90fb3d1e6ca0ac1f4f5e3e0ceddf2e8ade8f023d2e7c9f9e712fedcc2d7d1b1dfeda59b270010d5fb07e803d307eafafa03f00db4fae405f00cedc8eefbeeecf8eef708f80b191bf5f108d4fbf311f01616fcf6ea06e4d90a060906e9f407f202a5f6f114f81b04f90608cd1d110e0d19fdeae8ff03e0fde31f0e08e3f5f6110bdbd105fbf4f0fdfcfbf206fb021804e8fdf4f2ebd7e017141c0c05d7faedff05f4fae8ff01effbf903fef1f6f2210202fcdddbffeee5f11bfd0003da03c9f0e7f50505deee0bf70804d3ecd3f908f0d6f818f3b2c7e1f3df11f7f5fde3edfdb5d2ec03e90bdacd0b06ea08a0e20088b0f4b90f2cbe36e3c0d2ccccfcee3bf5c229b3fe9f403cd9ee16f2d6041ba5eff52cf834f236c0d9cfcd1280c40080bf8bd780d11b037d8007eee00bb924120401f5c4e30dd6e70c29d1eb02cb0b06cae0dccce307cecce40fffbfe3b7c4e8f3c611e701fddbb61caf2ff0e1c5a8d3ae57dae4f8d4f992f4f20608dcd3ffceeff4efd6e9dae2ee08eff2effdfaedc703f506f605d0fff2f90afae4e5d9e1ecfdb9f7fef7e004f3fceb0e0ad9e5e3b2e2e5fed1e50cfff1f5fcf4e22ed1defffe031be3d903200ffbf4e8fdfb0af518e0e3020c0809d5defd05f2e21d04f31d1fedf0080d03251eedf4f62226fadb22cc0efaf9f0e000074208fc07d012d405,
      4096'h1d0806f20afdfbf8fdfffc0aff04feeefefcfdfb07fef1fd00fc02f806e304160ff7fdf40af800f20a07030f15fa06f7fffd020d0917fff4f6ff0108fcfd0306e7e805b5e3cfebedefc4f307f5d1fcdef801fcc3f1d4e3fbbbf9f709e7bff1f50edd07fee2bd1d05eef6fcf8f2d3daabcad1c4b8e606f8ed11fdeedce5e20701eafefcd1f3f0079e09def2ecfac6ead101f7d104e9ceb20dff09e6fbebb2d8fb0fcfee09d1a9ebf0f9f11a0cfbdad4bdab19b0d5dbf001dfe306fbdfd2bbfb1300fa09f0fbe2e7d609132c0a2ac2dc03ee0af526f3efbfeefefbe6ecf5cbe5fe11e1f50101db0ed9f5f7150ff411f7d3e5dd1ee4201af50700f3ffecf9dce8f93927fde5f20809cc0f071cef09f4fa070b01e20a0a2dc8fc370905030bd6f5061a0114f1f3e60cfa0510fcfef2e006f8ec0dec07f6040afffe030505eee5160ff209faee04faedfb0205eb10fdc6faaaeae5d314f5ee03e70101fae8e1e7f5eafea1e2ff10d2efdb10d804d5c9f3cdbfed100c12150bfb01bf0a03e90ec0cd0074f5e200ee2613ff063cdf1f09febefcb5ee2af2eb3180f4effdfff71104f13217ef04bbfd11e5e7194ef23a2edad6f0d22f26412544ea9333f8fae7ff1716ea181205e0d3e908b20e0102e4e6ea05e3f6e8cae3e1f8a5e9edf1eadc08b0c523fcc60308eec010cf12ed0d00ddbfdedfaff28d06cbd307b800f1fd04d7cce00f,
      4096'he9e2f080ebe40880ef9df8bcdf99ed9a11d6b8a9cebaa7f3a2f3e997b680bbd9c4a8f7e6e280e79af4f11cf3c4cee6d793c4a180b2e407a8beec10cebe80d1fb141a11d0ff1b23fffd36f60c24ede5fade04e4ee13ebd0002209010a03f2fc1d1501ec210af800f40ded08f60af619f5f1fe18e220fa01de46050202bd15eef4e6dbffe2d115efee04e2f8fee8f8e3f5f4f0e8dcdb01fdecd9fffeedfaebe8dae3dbfcf804f5d5defde215f3edf2f4f204ee06ccbd0801d0d609ffec1fc20a00000a030bf7ed17da09e1071bf6dd16e712f3ee140dfee9fc1c04f7fbefdb010905fe0cfc01ed0713e8130afc0c072230f9e3c603e010fbe41001070cec0de20f32671d09e2c510de20ca03fff5f732ea4924ac1720feb9f54cfffc0adab8fb45440f1d14ead126f4ed24081e36f43012cff4ce103d33fdde33ff001ae0e5dce018de02d403d8e9db06fa130214e0e239f213fbf8f9e2f2fafef6f018ebef03fa06f8f30cf2e9f5e9040ff01402e2f7e304020af5fe14f6fd06f8f2effdf838f7f1da0df103e602cc09e5e106f8f6f3d902f6f3f9f8e2d9e6f6f2e7e5e8e0f2d80ac902fcefdcf0daece4f60dd5f801c8c5c6f8faee09faedf3f0f5e7fac3daf4dcf9fadade12e52afc03fb09e934e9e2db0918ec020a0d35d5fbf8eddff1f5ca1ad9fd0005fa36d81ce70e01a1e41181ceeefc0cccecf44fa0f90218f4e31de1,
      4096'hf5f817f0ee0900fd0110fb11f2fbeafefd04fa031003f0f0fffffc0a20ef12f50df7050bfef71d0df5f7fa1613eafc0fee08f2110d07fdea1301fe10eb110301f1dffc8bf6ede8cd02ebf6e8d8cafe9a0203fec9e9d7ce0addee0dcfd79fdecef3c3fe030aa1ead9efe7ea01b6c6e3b0c0b6b6d7abe6fbc6bafb11dbfacace000f14f9ffedece3c6001b11fb010c2908ebfff634edf9e5f72100f603f5d8e6182eefd90601e9090440ec212a3e10f8dcf228f436380d01202afafdd622dfeb140cfdfdf8f408141304f01200fff5f9fe04fbf913ef00ecf918fefe09eefcf3f7090c01fb0901fd02f7fe0e000c0b0a00f300f416fb0205110600ff11ee05f904fef1f0b7d80de1f3fffcf1e802f1f1c01add0dd4fed7f4ecc7f10ad4d8f1c9dbfd89f7ef12cfe4dd03e011f4bfd3e1bedbd4f5b19105f3e9d400fad44496e9fdec1ff51f07a7f3ef0a3ff10ff8f822eff4c3dcbdf82cdaf8f2f0ec95130ea30ff43c09e2fb132a425a1554e405d20a2bcf229507a7fc0de3000105ffe615f222e2d8e5e60200e401f50ce947fa422213ee2d29efc817204cb5f4f025d40924e9f1a2d2e0e81fb8cd14c8e61080cfe8bfebf825d9ad08f10a89fdf6173ce041a914a0eaf61bdbef02fce530fc03aedd1af3cff70ef5fda829daf6ffe3e40504fae89efffd0507e1d411fce506ceebdf181df7310fc9faf5eed0fced1fd0e5f8f3
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'h312a360fd6f8cec6f21fe50d24def04eed51141522092bfefd01f727141de7b8ec2700137e177f16374c3bf929c2101bc9d9fb19141d1e0d402fdb16170c2fede5dbf2f7d0c5cda30b050d1ff61cfa0b2e2bfd28e5a0ff2411294e1b53f90d123c201c101b1af9e705e3f7ea1a08011d23fdfe3a332ce91cfbbdf62b00222f0541febf01363d3741043bfc8e083f1a4018584f483443053e0c1fed47f1dc003e213b3b0d380bf312120508241b3d08fb14d4ff061afd3dedb50840fd4406f80cf603f8111b1910f418ffb20e2b22134a26542abc2a4f0d35201b0808c4022c062b1109ea02f0ee060d0536253910daf92d15090201f9f3ede8fef20515f8f23207023a2e1bfe053300220e01310cdbc70006dffa3017317f7f7f29d7494b1679260015f4e8fa481f44370d4bfaa316391a4905f8061e15faf4e5d9ebf70de8fdfcf9ecf921d935f8a10730f7373b362d2d1a21160e1220f3f21b05e3200ae102fc0ef2fdf228031dfef20bebde04ef11fe24032800e50d35fe16362e09100e0b15041d6440232af2fe6d2f267f7f7f60fc607f7f7f244e3e12fd4d213c28260631ebcdf11a04123af832f79bfb4e125c0f1bf1162ff70b03e22d093a25fe080f0ef622ff12f5ce02291632693d2b52ec174b1b495810611a9bf959084c380542fae607ddd116fe08010fed010c03eb5e2d6a13b7313822537f7d7f66006e2ee8,
      512'h2010f0e0020b06230e25582a5c4500125b074a0213250ef8262114131f171d25f22f111d156e37264d0d68783165fd060d02e607370c1749123603db0203f510
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'hfaf8060ee604f905f30a090af1f718f5e612dcfd01f6fe03ea030707f1f9f505ff10060319f310fbfe00ff20fbf3eaf10206defbfe2301f207feff07f9ecedfeca7f05c090ae9a3c218003af349e09bd1fb23cec800d80bcdfeda61fdf1112955147cc08ad27c24f24fef00a5d1130743d4edbb7e5c904b3391c80fa8025125ef50e01f4caf8f90505f30002f6ec08f6ed06e4f8fbece6e8f1f8d6081f0beef40ff6df08bbe2f207f601fc0f0bf0f5f1ebf9fb160bfef4cf1bf8fcd7ebf4f0dc11d2fc47fe043f010b29fe0e0d2228f9f20336ee070b470b16f7ed02fa26191e00181fffddc81ff6000f1f0b093edb00d4fce011faf60020070114ff14e717cb2cb8cac347451317fad0c7da161ded54c5d634feacd8d64532f226f704cb29b1e9f53d077ce4dd090ae50b1580c8d780351cf7e9a501077ffceb0739e6ef033eebe70600e50c03eaf20b04bff235fb07e8f200f2e6fb06de0f0732fbe4fdf30ff280e11426f3ebfc1fc602c4aff523c004d7fa1dc3fcf316cdeb0e00fdef1c12ebb4d30c5a143b0a32f431cdef2dea08328df10fc0097f2025e1c1f4c5fdb980c7f70be50500e9f5db8928be8021c62c008ecbf180a4fc2d8b00c8fc1b30fc94c9b8e3f731fbdcdb0ae8ce05e3d9eddcebe5ede7cdd502f615edfdfee3d8d0a8f2d2f6080e98e3e1f4e8f1c7b2d4a2d0f4e2f2c5b9fa02eec0f2c6f1098d0ade,
      4096'hd5b0ccdf1d0ad94108e2bdd61748eefe1ea01ce2bdde4d7ffb0d330bb80aecc9be25e9014427d8d2c3e0e480801fdf401ef039bd80f403ee800fc8ff51db48e412dd0916d4060dfdf21900150107fee4eafc0b0115f707f102fce80ffafd0c25f8fb08fdeffc27f8050615120a20eaf5f1fdd81104f4fcfc39fe0b05f1eb0ddd07ece511daf8e306f5062520f1ee09f5fc1ff0e5f1f1f6fee8fefefafefd1708fadeef011beb18f01017121200fc0cc0f52e16d8062806e12def04ecf7e6f841f8ce0303eb05e408f9030212000406e8f603f1fa070107ef0501ecfe02fee7f5f7e0040ff5ee08f2fcfb0df2eaf6e7da0003f3f9ebedfeeafd08f3de05ec00dfe9dfe0cf43f4cee5e1def60c1706ff04ae900eded0e5f25ee00322ffe5d7061a08abdbfa1ec1c424ede6048fd7db508031f01ff5f8030214ffd714e90dd91e64ea8fe60032052ceb15f9e6dfe80dca0ff3e559dcb206d60b17fc221cba05f31a1a820a0c42f72ad203ecfeb2c7e7d39ce8d8f5bec209ef08c4ffe6f443f0fbad04d304e1ecd3d403eee30615e4d7fdf3c61de8ed0affb7e7d9fb020bf3e707e2020bdcf815c723edf1fefb08f9cab5e0c5e7dad6fcfdf7d61bf0f9daabd9c3d1d5eff2f31627fef504e2eb15f7ff0b26f826f6e40df7101705f8f009f91f1bdfe0f5e6ff13e4fa0011200b0ae721e6de121809f6bee6f81e06f7fa12ea050c0f,
      4096'h9e80b6c9dfddbb100ccedee6a38ffebc80f0f3c7cee281d3e7fbe20580cfcf80c0dfc606dc80f2e2eaed070680b880e0b0b49a9380b806b1ae1e80b4a180dbd3e3e106e8bee1de0ef9fce919dbd424e4cb080af9e3e2b8c6e8fde111f2cfd3eaf7d5f800c7a6f9dcddfafe18fbbdcfe9b5efe6fbd102fed7fc1cd1abc6d4ebd718bbee9c0507bdf2ffcdd0d5d910e345e8a460edc6e1ca2726d942fbdf33f5e300802cf21da81ac7de3ffaf0aeda0b9415291d8f85021f27e100dde90eae5d413a22152cb0c8e207f9f93757e19f1f803be4ed2cfc0a0c80c2f4c3f73d20e92bdd7f250b8ef6f923e80632167fbfd77ff3348f40320efc806ffdd90c1d0abcf7dcc60a12d802f204fa0a0f05f10d09ecf506f0060cf5fce206fef6f80702e9f4f8faf600ffe20efefff6fc05f501dff4e0e9fe0ee200fac2070ae5bbfac005f0eb231fc501edd1f306af1fddeab1e4bbf9e6f1e4c2ebdbcab402a60b20f3d7ad245109fde618f367ead62ce0c888d67de4f284e531b007bd1ae4bf36f5f7aee5cc80e0c3e2ebaef708dfef09ccbcffd4a2ebcacef8e1b8f4fbecddf3b7e1e58ecd89f70af68321b7ea040ee38ec681d6b4d8c3c080f70dc7cdf4a99dba80e6b3b18be8a2e0eaeed7e10798e328e805174fe6dcf0fbb7415ef5f2da00cde5f3800708d6f439cfc7d1cddbfdc280fba1f62be030df80b1025c80d996f52f0bd429,
      4096'h8993ed14160027db0c32dfcb0e41c90b29df230d24f04cf33e0829f0b629c7e3098e10fd1bdcf2ba03911ac58015c6e01ab8fafc8c9ff517a1fcc8c53acbfac6e6caf0120315df0000c7e2e9bfd3fbdddedfcde7e1ecf418f004ff0fd4da07c6e9f30005f1cfdae0f80510eac3d5b6c1dbf6bfb4aad5fbe5bbe6b19fe6b2e0d5b19cf28037ecf000e008ffaf1672a27122061bca10fbf24d0d1456e3cfa8c2054acee103611fbce8e180f6ab80ff338027c95ccec6ccfa2580b1cd07fbd67f7f23d01902e9f2e104ec17fdfe04051bf2db00e3fb040209e50efe0a0afef2e6f7f0fafb1118f10ae9e1ff0414fafeccd2f402fd0020f905fc04f5091b07edfdd3e912ecc6f6eae003f4e3ddff14a1d72f18c3f3fa81d2b203f4f7df22153bce0829e5d701d7fea8d80bf8e32e0fb9372724040342eb21f203e01006d6aedec67eaac1d2d6e4cbab08f3cbb1f6a795059c93f1db96ccdb9de8f303c50f80c2d58094acd7ffcf80d0bdccf31cc39dbc80e6b9b5989880e9fcc7b4f880efaa82b7e2d6ac0cc7c7f9ae2605efe0fbbcc404c195debce0ebddb9e5d610d8f6cbb2ea9bf0bddbfdd98010d9ebebfbd4c5e4a5d8aaedaed8acc7e9d2dc13aeb7c580c5e8d9d3f5f6f619e30800e903f0dae9fee6d516ea0502ebe5ea0208fb0904f9f8e705b0f30306ac050df3eaff01eeedead9eeeaf3eedef9fcdffaf8dad9dbb4fce4,
      4096'hcdbdf7b9d3fcc615fad8aaedc9e7dde48ed506c2afd2de0c08f213fed5e1e380e7b8fffff780fcc301e4fe8e80ef9ab3dbe9059d99ebf7c6b701ac8ff68009f907d1f6dc08d4e6edf7e4f801f6b9e5e7d6e004cab8eacf01e7fcc601e7f409e5dff30000e2e2fef8d60af9ddd6e5d1ebc8efcadfe8f3f703ed00e4d8d5d1d0c7ebcbed01c6edf0fd0f0cf70205041cf00211dafa0af5f2ebfd05d404feffedd6e3f603faf1f003de07fc081ffe04dfe10beefdebcce4fad3f50dfbdffead042511fa100ad2f1e3f0fb0517ffe0bfe3c6b4cfeb21fadad9eceaf5e80dddf6e3f4d3b7e414e091edc610dff121e2f8e9bce4f9da1fefe819d7e8e7f1dddae3ddc6ee9101e43608f7defbecfdf10a1a003a070f04f2f8020c1512011429102510c5ddc0f60f1dd20c0d00e0faf09dcfe1ea23ed00e8b103fe28e1f1eaf425dc08d9bec5d0af03029c0108b0e7f2ccdad9cfb5b416a489e0c8fade0426fdd5ded5abdfb7e4039e03f5db12cce0f6d8cdd0ebc3cd93e4aaee0601f017bceeaeb5efad1acdf1e11a18c50aefe7d404efe1e0facff306f0f1d8ffff16f4e5ecd509e6dbf6cb0ff4112010cfe901060fcde1d8cdf3d5f5dbbf0df9fbf30be3d2ede90bc7f235fc2014fff30bf9e005d1efe005feeeec0a1904f1dff6eaf7da01fe290df0181c1404f6e10b35ff08d60919d806efe2ffe0e3e0cdf3ee44081301faf70206,
      4096'hfe060003fa080e030109070ff60c06feeaf300fffe01eb0210faed01f1f7100604f3fbfeeef5090113040005090d04fb0505f20d1802fffbf4fe080503ffeaedf7ac14d3c700aafcf3d3ef12dca1ffe9cc02ddd1e1e6c9fdc8fd06fcf9f900c2edd7f403048008faf304fafbd4d0a7c6ca03cbb88ceaf1f4fd0cb8ccad90d7f10fc50b24ca20ee11ee15071bdcf142cbea43ddec3cf9f4dbdd01c50721c824f40e011108eee925fe0b1afa371cddde10e8dffed01cf1e4e70d17e8ecfff217ee02c1f93de61d0e01f8051435b7e45bf9e239050d11f4d6d40303f6fa42ee371cd2e1de07b3eb26cb283b2a5f1d050bb7d019f62d4032ffe0230d0a05c2efede319c7e7e9c9bbf822cff51034c9d14a80b712a82b17f2e9a8b7f2cd1a2dde5216014df109acc74bf80767264c7f15fc6ce1f280496635eda16a3926f8acd6e8d718dc100e26280609fa31ef110518160fe40a450dfa02eaeb0bfdfff5d6d81a1af4d4180315ee251416131615fc25f1ccfaf2e307f906051affec3af20cd9030bcc1a0ee8c111cd1e1cc5efe2f2ebc417dfb71ae7c0fda1f9fb05151e05f5fc0227dfbaf4ce2407161ad0ff3102dc571c1107fc1bf13bf4ed0e0211e3a202f702c73818fec6f0341436a6bf34c38ff1802125d731db2be98ba8e481ebf818dbb21c7f020480d8fd2fc322e71066f2da7fe4eb804208f1ed80243d07c82dce80b7,
      4096'h8080d49f9cc6b8fe13c1c1e4aa960b9880ea9aaebacf85d4d4f7a811afb2ea80a280dce99780f4acd3e910df9bbe80d1acd89b8b80c00981b1f887ac8c80a5ec34c8ec000c00c5d8fee7ef0bf1d20cfafc0703e8ede6dfdff5f5cb011004f8ddddbef3f7e40bfed908faeb11ec0acdedfceaf4cbdafc0ae10a04d1f7e3bbe705c2ced29fff00bae5e6ee0fcf0d10d00eec19f3cf04ddd9f7d90d0609fcd8c9f21c80e10602e0e4e51bd90fdfa0f1fbe102f93f04d706fcf4d30ceaf6fa9b076012db0afc06f9f0f911011a0e1600f8e4e5f40226f9e3d2fee2fc050a11e1e60609fe06fbccd215f306261046f2090d14fb15f1180e0c070d22f5fc21c5dafd2f44f90218f8e8d7f8e91ff423bedf5fd9ea27eb11f809ec11dffde91117090708ef3a180ebd1313091419f9f840330425d8c5e7235ff5f8dd08f6fa5dbee7d0f8c9ba0ae1e4e5c1f902e6fcf9e8de1cecd715f1e4e6cfddedd40be5ffec08e1c7def9f9fb1fc1f7ebfbfb09f6ec01ded8fee7f5cacf140201f40cd6fbd2b60027f1c7f3efb208eee9f9faf5e9d4e5f4dadefaf4ffe3f8dff102f8e3feeb01f8e7fdc5f6f8e9bcf4e7010106f1bbfecad0c5fcedf9cdfaefdff9fcd2dad79fead1e9d3ee02601cb5f4e8130300024ceb54000e610bd4ff033033041c01b10a170bf5bd0f0d5c0bc9e616ecfed598f9dc9a0c0a020cba20037f03f7d8f309a821ab,
      4096'hf6f71106d3cee8f8eed31822f00adcebf6f307f9f0fec8ece6fecf08e9f800eff50ffb0402d20b0f01fb050a010ef021ecfbd2f3d9fdfc081207040ed8c0ed01c7a119d106f0c1f0ecded7f3b4e6eedba1ede9e3f3f8b202e201f7fdbfd704a2f3aa02ffde8006ca04f6fbe49bdcacf1bde7c5cd8bcc06c7cdf7b8b1e882d5ef26f6eb28f600f81b092ffe2602032427dc360cec22ed14ec0ffcff0df7f43d36e0e1d41511fb1df71d2c01001fecfcb6d7e0fbf61d15f71b1af73901ecf523c60a07e3d60ef3d304080b051221f41922fff01303c70ee4f1fcf7b1f4031118fdc71dfefa0609fa17f5083df3120601e216dfb506f50604000c000001e101ffebc480fde2bf0cb3e8f1e8c20701fbf0cbd5e101cf2ddf08d90a100903e6d8f8a0e98005ee08a00db5fbf319d680c6b6e9faeb06b980c6f7e2cf03c99f1c800dc79c12ca27ea04f9f41ee9d50014f6f0c423d6eabaddfe16d8fef2f7f5feef03fbd960f8f0ec27fc25e30bfee22ce0025dbef7931a0af2fae80601e3e9be15eba7be8ef88a0feb8bcdece807ba4d01806bcf0e19fe36f2087ff00768edf8ee80dd0e9c8a1856e99388efe1c0b080963e80f2c967e5b3fd0943aaeeb2e033e53022c21ae7a41cf2e9dd0bfa31db08d2fd2710b1fa1207f98033a3f9f7f70fec15d432ecf60cf6ee9ef7fa1cd905bfa4443f5c043207da4d04ddd401001eb7d5ec72
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hfaeafae8f713e7efedf9ff131c020d2e231c1701fa1d201507130605ff14ccd8ebeef9d3e0f80e23262d4c4308e5edeff1e90b060e0104162e1b2b19ff04fc23160f41032d08211f0e092c190015361e3de3d3f40b00fd0003fb29fa18fe1413fff72c1808282f331b211c1e08f6f807faf6ff0cf7d0d1e6f6e5ef04191b1317370ce70e04e6f102ff2ee1f3fb293118fbf6ee0cff14140707f6ebf009ecea04f4f1df07f0f7f40e3a2a0ff11014120c1afbf8fd3d054d152835201114ece8f6fd03f405070ff204041c1703cdf9ed2e4bfe4319134a0e0e000b04efff0dfefef6f412feeb0cf3e900f7f3f00f19e90d18f1f8e90512f9f51cf6051efbfa0afaf702efeb0207ffbe11daea09f4c51f0a01fa1b20341a48080406fe1202020304f10dea0c06fc0d0301413a301116321f1838f1f404f2f6f305fd0d1af9092f161f22fb17f3ec2c061b3e17261512fe15e6cdf8ecedffe6dafdd5e0f1fbfffa0e0e0ff509052e1115dfe5f0f702e00b13ebfcfded2800102214111b150114fef515161117dfed05f9e805f8d7eee10ffceafef3ea150713fefb0a1403f712030f0c10f60e3a181e0e0813f90df4f700f1e7effe0de511140006e00502fce701dc0d1c0df80d0407fd230bf91c1410121a02fc1e03faf0f70af9101c090e1c1f0a042ffe1318280c06fd121113020b052912fafa06172f1934122407010318070d,
      512'h0b100c00f60b04fd10041c0601f6f70df9ddf11af4f506fcfe1015f820f9090d03061d16151b2226fefd1a0d1535fa1b260e0f301d3609133f263b423d200737
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hf1200108fc000e0109fff4f8eeecf6e3fef0fb14f80dfff307eee9dcf6eff20df83301fbebf80e320007ebf003131b19f5f7f60ef3f508fd1cfdf616f427daf900fffcf6f70003f500f9fb02fcfaf80103fc00ff04fe030100fc0300fcfefbfef9fdfeff00f90101fef9fff8fb0604fd0000fefdfe0201ff0400f801000200fcf6ee030600f503f6faf7fbfdeff6faf8f603f0f1fd03eefaf401f208f80300fcfbf30306e802f808f2faf7f8fef5fcf40000f305effff9f9f400fefcfbf0fcf80af0f800f3f3fef4fdf5f31401f70ae9faf8f5ee04f3eb0ffc00f60af8fdef03fbdff6f7f6fc0406ed00ff0f0309e8f7fe0a0af9fde206eeedf70c03141b08f300f4ff0115f60ffef5edf404e8ed0feceff7f0e8ffefeffb06fcfc0c040403eb01f5fdfefae9fbfaf404e90701eedefdde0d03faeff606faf703f0eff9ea05f7fff6f7fefd07f204fafeff01fbf8f3fe0bfffffff9f9fff6fafbfdfb01fff7fbfc08fefafdfb020303f9fffc03f9f6070301fd050aff05fcfefcff06fefefb0111d3fa0feade04fbdffdf0feecee11d2d2ffcbe308ea0dec020f0001e3f3f1f3ebcb0af9f9e901b70101fdf7fcf1b209c5faefe500dcf2d1dafaf8e7dfbeece807e0f8f5f5090fec09000714fb03ecf50603e6fb16fd0104090214fbf0020c0ce7d8fe06f3f1fee3f2eff1e9dc0afb0102da1a16d9ebf6ecf504f2e410f10000,
      4096'hf9fa01f6fcf6fdfc02f4fcf900faf603f301f2ebfb01e304fb01fbf0ecfafc0108eefdf2f7f20202f1fcf2f0efddedfffbfcf9f2e7f705ef0100f4ecffe3fbef06d9e7e1cfe286c99bd8c5bae6e6efc5c700db91c2e2c9c4f701dec8f1eabcddfeaa0df0dbfe03e6ecfdfae0dac1ca01a408afd9dbcc06c1c5efe2b199b6aab906d6fb2c09fd19fbf60a07220dfd1c08f704fbf1431e1409f019fd1ef81314030febf10efb25fff8ff0a12faf81ce9ec09f2091a0dfcf2090002180025e806d901e20fecd0d5e0d0bdc2e9e0e7e914d9ddfee5cde2fdd8ddff2318f8e40fc8eef5b00312cee3efd9e4dfea05f5bfaaf3b800c2e7dccaf7c5def3f7c8dba9d1ebfb13fcfefaf4f8fdebf7eae502f4f7fb02f3fe01e7fff2e2fbf8faf4f0f6f6db0503fc03fffa010c00feffe4f3fbfb11fd01ed000afcfcf312fdf106fc01e8fcfff8070af9f2c8f9dcede8f9fd0404f3e4fce1d709f8ebdb080c04210a06fbebf8dd09fff7f104d1f9fde004f9efd8f4dcfff2f6d5e203d20006f9d4e7d9eacdfdd5faf2d4e6d7cdcde4d9d9e7c1f9c5e007d4c1ecfcf5e9e10bf3dbd806e2fbe09dfc01cef8fbd703f4f2f0e5ebd0fdcc04dfc6ecedfdd7cffde9c4c4b1b2c504e5fee1e0d38ec68ae2efabfdd2fceecd06059acef7b7b1f50ddcd9ce17d3cdfeae0c07bcf5fddbf4f4ebf8dca0c3eca0efa9e2e2c8f9e0d6efdacbc0b0b5d1,
      4096'h0dfe1a0c00fa1cda0306f0fc07052accee12d5fd13f5f70305fb1111180be91ae4d10c14f311fbe50df6184a1404d90dd903e60d1fddf7fff3fa1907eae508ddf80d02e7f7f6e4edd7faf5d7d703e3eef7fdf706c903ecd302e9d3dbe7f5d4e7ee01f002f5ef020af8edecdfe5ecf9e5effbe2f319fbfaf007f8d40ae002e1f9e80c04e7eaeb03effff6f4f0050ee00e06fbf50fda0f01daeafe0be9e710dceb070d01f5f80002f8e6f3e6e7f5ea20fff1f80b0df71503fc14fa0a16ee120b11f8ea10ff03031e13040003f9fbe62feffcf8f5f10cfb130d0000ff1e0cf6e80af9d5ff01f21cffebf70701210d13e200f30ff919de00f604f6f81ffd04ea06c40fdaf6220c0516fc16fd021c18f705dcfdfa0deb15f80c2c04fd15000fff04e2efeafffd0dfd05dd0103f5f3fa05e2e2080918f8e805fb07d41118de15121518ed1af6c2e6f7ebf7faf9fee8e6f4defcfcfe020dcbf8f2e6e3eaf5f411fbfdd1fcf2e6fc0afc060beff3e6f7e9f817fae4f40004f7f501071207e003ea00f70af2fdf8caf5e1fdf6caf3daf1ead3f40b01f7faf8c21cd1e3fdf0efe0fefdf3f6fbe4f6f2f0f51110f4f1f9f3e4ea05cae404dcf0f215ffc718fae10cd5ebece50cd1f300c1b5acb9a4bfe0b6e3ecf6a6c50feca2ccf6c6c5ff0adcece40ac0d201a50200c5fcf9c2e9eee5f9eabea5e893f3bdd9e7caedbfb2f1debdb4b1aeb4,
      4096'hf900f7e8f6f8f2e7e6eaeae2f800f0f9ecef0006cb10edeaf7fefbfbf9f60afaf61609fafbf1f803fff5f3f7f2fa08f901e5ffe2e806fff5fafcf7f8fc0ef2001eb41afedaeabbd280d0c0aefad6048e9efcacd1d2d3dcaefd01f8e217f2a0c805bb0e08f1d701b4e7f8f30be7e180098004aeccdbc0f3a3c5fc2adf80938082f9f1fcfcf301feec06f5fdfcf1f5fa01fefbfbecf9060af5fe01fe02f102f601edf105040100fa030600f403f7f8fefd02fbfdf6fb00030102fa02f8fefbfbfd11ef00fff2f6e6fafdf4ee0400edfbe6f505fbec02fcfa03fc04e90501efdbf9f3dffb08f202f8e5f6fa02e9f9ea06f5f4f9f80ce6f70603f20903d911fd0206f507f7e702f6f6f202f001f4fef7f7fcfefdf8fef5fe0905fb00f6f9f9fff7f102ee04f6f0fffc0e00fcfbf8edf805ebf7e804f806f602ea0a00f302f6f40400fa02faeaeeef04ecfeea0b160aee020cfdfdebd914fbea08fffaeee9da01030afce2080603fffd0bf309f6fbeaecf8f801090e1fed03fdeef700f4ed09e6ed0103f7fbfd03f60200fe06fd04fd0c0307fc0604f4fefe0207f7001107fdfbfffff9f6fdfcfaf601f1fd09fa0afa0cf501fc0bfcf8f3f802fefd0303fd03f8fdf70feafe02f2e0bceee6c9f2e9e1ebffd1d50be7c0ebead1e3fd05e6ece4fcebe601ce07f9eae4fce1ed05dbf705cbccf4bb19dee4e5e604cde301dbe7e3cce1e1,
      4096'h0a010d12fee8f5e70601fc20f4f80e040b1800f123160bebfa0ffe1ef80b05eff7e1fd14f9fffcf8e3f5120407f8e6f70be90bf60b050505dbf611fa24d602fe00fcfb04f501fd02170405fb08f60cfdf803dff811fdff19fd0a080d0a0002edefc9120207fe04fb0000ee1f01e8e4fefd11f8fbf1ed02ef08f617f5f8e5050aff04f8fbd6bca6ddb1f3dfc7d3f3e8e6c8f310a5ca17ebc0f90ee5b7e5edc5f608bb09f4e3fd00c7fbfbf6e0f5b7daedadfabce9f6e807bce506d9e8b6adc5c3fcfafbfff9f901f800fefefcf8fbffff050001fafcff04f8fffbfefff5f8fefdfafafe00fbfeff0301fbfdfbfbfdfafa01fbf9f8fdfd0000fffe01ff01fefcf8ffe2ebdde4f1ace183ecd9c5e5e6e7f3bafaf1a4b9eeddabf201d3cddbfcd1f402bd0ff2dded0bcd0cfc01e7d9c3d0f3aaf4bce80ddf06c5db09f4c5c7dbc0d0f6eb00fef8f9dceadbe0e5f8fbf5fbdaf30200caf1fffae4f80b09dfe70ee2f918d3fff6e6ea0ae6eef7ffe4eaf9ecf6d3eae8daefddf5efe2edf1d0e4c4d9dcffe5f9f5e9ebb3deb5ececc706e0fff5d5fe16b6c9f3eeb6fffddde3e01cc2dc02c50106c502fed201fef9dff3b8c9edb802c4d3e6ec02deed00f1d6b6adc4d302f10d03fd1c1110fe0202f905f708f503fae9f304f1f20804020023141605fae8ed0002f701ffdf040cf0160c07dd02e71501f5f8f0fef3f4f8fe10fdeb03f0,
      4096'h03f3031ce6d4bde7c1ede5e9ccfa03ecfb02fff8ccfed8c2f4f7cbd6ddfdf300edfffcf6e1f7f8f314130deae1e4fb0cdcf8f2e5fb090406fdfffe00fbfccbe607edfaf7fc000605feff01f8f8040008fcf3f706fafb1dff040500fafefbe111fe05fff6051301020bf5f1020412fd0cf0f4f205f0f4020af5000107f5f80000f6dafa0914f70a06fbf901eafe0a0b13060201f0f4f8270a10040308020fdffaf70204ff0bef04f302eaea08efedd303f305f8ebf9f30227ed031afffee700fb04ccf31f211312eb0b090a0df9050d010b100feb10f6061304091d29190d0cf9fcf8fbf514e9efd9fa03ef12ee03eafbea120701f5e2fa1febf312e701e01901faf807fafdf70bfcfef5010008f7fff10400edef07fbf00c00f7180df403eef5f6f60c01f7f000f1ff02f0fe16ebe5000007fffa00e503faf1fefef80ef004fdfa00f5fbdd06f9dbe8f0efebf207f700f8f7fd05dd110bdbf8f9e5eed4f3f0fef310fdf9e40003f5f3fdfce6e0fcccf7fbeeeef4f4fa00dff2f5f4f4fb00e5da10020008f50ff7e2ee0d0afdfe041401f804f907090c030beffe060e0ffc0d08ed020300fe12fdf7071603140311fe0df30ff3fc0c04010103fe0503f6f6fcfe04dafffcfde8fce9e8dcf80904faffe1e3fde8d824f408f000fa1003f105eef7fed10bf8fdedfeddf300defc01eed6e1e614e4f8f4d600e8ecfc08d7f4c501e5,
      4096'h020106090afb01010cedfb05040303fcf7fef700f7ff0105080513030505100300e50807fdfe00fa0101fb150e07fdfdf60ffc01faf1fff8fafafff30cec01fe000dfff20ae1b7d4c3dfe3cf03f401ebe4f7f6c2f2f7d9e4fff0ecf1ecfcd2d800bfff0ad5eb02f9fe0de6ee02e8d8f9c7ffe0f4f3e3fffff0fae4d1d1d3dcdafeb6f2f1dcf0ace2a8fddbd0fadc09f4a8f3e9b4c1faceb5f815e4ede5fce1e420acf104e7ee0ec60cfc02ebf5c6bdffb7ffd7daf8e2f5d7e506ddc5b7a8d9ccf3c9fee1bccf8bb2a4c9d9b0ecdeeccbbf06e791c3e2bdcc0102efc7cfeebce011a8f406c1eefac801f3e2e2e4c58af4920e90c8e8d503b5c506dfb59ba89cbafefbf7fbf5f5e9ecf0fbebe2eef1eef8feffffe9ea04e9e7fff8f4eaf7fbf0ffecf0060705f30407f6f600faebeb04e6f7fbe5f8020304fc0bfbe60500f7e9f4e7e310efccdeb6d3a1d6d8b0d9e8fcd2bc0509a9befaf4b2fb0bddd9c2ebc5dcf3bcf0f7dc05f7e8f8f8e9e7e2c3bbe9adecaeece4d405bddbf6e1e2a7a29fbdfe0413130a020efe05040cf3ffee0f090113e90d14010bf9010c21f90ffcf906fadaf10cefedfd05fa0cf8f5141105fff406f8f9fae6ee09f9f1f5f316e011f203fe02f204e5eae1eef3f3f9f7faf8eaed0bf2ee05fdf8f508fd0df3f4fce9e7ffdc020fe1fb01d600fae4f2f3e2e8f4d405e30400def9ecf901f9caf1f1e4fc,
      4096'h17cf01e9dbdac7bc9de0efc0ebd903b2bbf9d59ec1d8b3bd00f9f1dbda0bccd301b4fa07bfe909a905fad3eee6cc99f299fec9c8e0c3f2c2d8fddfe6b9a9bcbcffe4f4f4eaeaedf104f6f80613e7f7f1fdfbd8d111ebec04f708eafa15f308e9e4e6fbfdebf707edf1f7f10205ddf4020115f702e9e6f8dae1fde4e709e20ced04f4f0fd0ef004d70afdeff90becf416f2e410ddf80bfc0f06ff0ae900e8e7fce3110ff905f2ff02080aedf9080106fff714f6f10ffdfd030df0f700fdfff7ff02f8f80300f4fc0a03f1fdfbf1fefd03ed03fdf3fbfff7060004030600fd0f09f8ed0407020003fbf7f6f10afd03f800fc08fb02f7fa03fdfbff01f9fff7f9fafac8f9f3bed39ad092e1ebb7dafb01d5be08ee96aceac6a6f7f1d0c1b9eab6dd04bf00f7b5f015f4ef07efe0eac1b9ed9bf6b8dbeaccf7bbda07e4c9bc9ac1cbfcfffffefc0000fd020000fffafdfd00fbfd02fffcfefffefefd0200fcfcff01fd00fdfffefeff00fefbfdfefdfefe0001fefdfffc04fffffffffc0103010001e50cf9f8d3dc0b08fef2c8bbfdfbf8ef15f5040ff316f5e300f7dcc3f7ecf5ea0e13ef00e8dd0b04ecdf02e4f5d2eff3fef7cfff07f102de1902ef03edfdbbe101ec09fef703feeffddffa070aeb0ce4f9f9e9fc0ef70d1305020a040bf6f401fbcefc03f30ffef70701ed070ff3db04fafd0bfbecf0f8f9fcf7f9f206e6fde9,
      4096'hf8ebef1c00f9ebfaf0f7ebd6e7f1fb02eaeb1ef3d50607e806ede9ebdcfff5090d0309fdf404f0edfff7fae1f3f5e1f9e9ffe2e0dd19f7f40cf506f1d6f4f9def707f50228f9ecea06f7f0e6ef02fd0f23f019e6f1dd00fdeb0406edf9fdfce9021b10fef3d0ed071bf7ea1000fcfef305ff1806f3fff50e10f4050003140706010bf8f1f001f7f0f9f5f60006fcedfe05f302fcf40503f5f70607fd01f6faf511fcfefbfcfa040602f7f303fefb02fdf008f9f6fd0200f50bfcf907fcfdfdfffef8fbf90cfe09ff01ea0406ea04fdf108efde0b14fa040ef0010dfc0c17f9fe06f800f70200fff7f211e7fef509f5dffb0c11edf8f3fc03f9f701fa11f505e401f0fffad2d3afccb5cddac8e3f2f7cccb01f0a3bce0e3ca01fdead9effcd0cdfab1fd02e4e4f9d4ffeee7d3dda2c5f7adf0c0e4ebd1fabcd1f1e2c59db6acc4f4fe02f901f8fff60fea020df80d00f002fdfee90ef7fa121402090df50704f3feef0b0af8f807f3fcfff2fcfbede004f9010401fef8f8fbfd04fcef02f5fafd0bfdff01030107fe0ee80009ff060c07fafbedff05f80b00f6ff10fe020402f8f3f40102fcf8fd03fb09f20503f9f2f8f404f2ffedeffdfcf9fd07ec00edfd0104e8fe0503ef11080ef70a110e0004fbf9e8ff0a05fc140b060a080710fbf90012f604f41015fe00f5f6f003f203eb030cf8150ceffffdf8f3fe140d0000060d,
      4096'hfc02fcf9fafffaf9f4fbf9fefcf1f20dfff9fdfef0070cf4fdff0bf4f5fdf6fbfc0400fcfef9fc05f7f2fc0200fcf7fcf9fcfef6fe04fef9090302fefefaf3fefb140219dac0f4f1c8f5d5c6d40405d4d406e5e2f129f9c8f0e6f403d4f5f3e3fecd090cd502ebddececf40ffafac817cf1de7e107dbf5ddf1ff10dbceefded103ed0ff4fffb0cfe03f30507eb0205f2f40bde0108041919fc1711090116f002ecfa030de90c06f6f7f6f20eff08fc15f5f6f70df1f6f602fffd1ffdf0eaf7fa08f3f5feeff102f812e30003070301efef08e6e500e9f207fdfd00fe1c00e9f1eefbfa02ecf2f7f9fdf8f41f00f7f602fb0107fff3e701eefdf903f506f1feff0d00060dff060bfae2fb0104f4ff0afef107ff050711fcfdfef6f603130c080ffff6fd00080a00fdfa0d0b040804f90e0208fb0a01fb03fe0403ed04eefaf3000ee9fc09fcfef5f40dee060102fbfdf6f6fdfef611f3f21103010a06100cf9eafdf4fe01f2f0ffe3f90de50f00f8edeafc1f03ebefeafa01ebf1030709ee02eaf4ece9e9ec28f4f5f300f8fddc18e10215e91e0d020305eaf0eafefcefea09fb092df7f6ecedf613fa15f9e916010826f604160af8f6051bfbf4f3020318f2f807e4e9f9e7d5d0e3e4e203e304fc07dfe7f8e1d5f801eeecf0f702e2ea18e4f2f8bf0606dff6fcf4f9f4e4f9ebd6ebecdefcc9fceadbede8d0f4e5deddcccde6,
      4096'h021f00f7e903ede8d4fd00f0f904e8080e0df902f018fde9fd0302f8f1f7e40515f8080af5fcff00fef6edebdffa02f3fd0d03f60ef4fef21dfa0614ecfcfefffdebf9f4abe080de99efc4b4eeed02e0bbf0fa9fb6f4ddbb0211d2bae226bee61c9cf70cd5ef0ac611f003edddc6c2f899f3b9cee3e4f9c2c7f5d4d29799c2baf3dd050dfddbd6cee500f3f6f1ee0cd8d9f0e5d7f2f4f5e9fdfdf4e7fcf2fa091fc70afaea08fbe7061cf6f905fdeaecd323dcfb00eafafafc02f4f3d5e4bfcffaf5f706fbf0f0eb04f3040103f2fef6fb02fefae4fd21fe0000fde202f8f61afef7fbeaeffffff4f905f10b0217f4faf0ed07f6ee05fd01ec06fd0201f30d11f20301ebeff8f0fb02e900fd02f5ffeefe02f4ed08fae806f9ff05f7f70af6ecffedf7f9fdec04fe05faf10f01d6fcf8f4f4fcfffefcfffef8fe09f40bf7f8ff04f00101f4dde1dfe8ea06d40600f6eff002ece0fdf4e805f60f10e1ec18ecf1fae7f703cceb0cfcf608fc0f02f0f0f1f1f9e813d9eef5e6e5000ad5f7cef6dd23f8fcfaf00e00eef3050b05fb0308f5e9faea071d0326f00b08fc081601060af7f40a1bef0afee3131d0ff9010ff902f20af80220ee00f901fdfe01ebedf7e7fdea07fef3e7d9f8e3f7eff3f1f00cf7f40eebe2fc14eeecff03f7f9f014f0fd09d605fae7f8feefedf90102faf3e8f2f1fdf1f1eddbf8e7ebf7e3e8f5e0ddf5,
      4096'h0aee1502f1f610e70b02f6d806d30ef0fa04d71401f412070eec020f1809e31de7e5f102f719fefefdedd902261df8ede2220a08eaeef3fef7f405fbe9040fdd06f402fceff7fcf60008f9eef7fcf4feedf901f7f60709f400f8f7f5fdf6eefafffdfdff010a00fcf8f3faf4f3faf9fa03f7f3f6f70100f7fe010200faf9f1fe01d7ff12d9e4aee89ff3e2b9f1dd12deb7ff05b8cbe6e2c201f5d0b8d009cbf707a90cf9cbf208d5e80efae1f3b4beeeb3059bdee3d300bff905d9d69fb3c4c7fafb00fef607fff606fff812fef5f60204eef80b090a09fbfefa010102ff090d0608fcfff30a04f2ff0800f4f00afdfffdff02070804fdf709ff00040604ffed11e3f6f8f7ed0ffe0ee508e906e3f9effaf7f8110fefddfcf403ff0eecf3f5f1f4d2ef01fdf9ffdfeee5e30ee1f1e6e8e90b04f8e2e8f506defbe0e701e815ed0eee042af5f1f0efeb1512fd01ed1029ebfc0a00e8fb1fd00006f0e7f4efe4f5f1ba08f007ebeded06fc0905fdf6f7f1df17f6f8c8fff5e2f411f3fadfb1fdeffb0cdeeb010f11f80cfffdf513f0df171bfef208e9fa0b09f1e9f1f423f9e7e503eb02ef15fd0906f5f2e90b00ef23f4fb071c000e0b0523f6f7f2100204190f11d4f90ff8f5d2f7e9eafcf1f1020af2cd13f8d0dfecd0d7ff0cf4d1fbf5eaf4efd3fef3f0e2f7ddfef7f70bf7eec4f6bd0bd7ecececf9ddeaf31fdfdad8dfcf,
      4096'h08eaf2ec01faeedde8def8fb05e402dfed05e7e812f0ebf8fb050e06f503dbf100c6f60ee2fffbe4f6fceaf4eaece8ebe6fcfae1e5dff0fdd7ffdedaeed4dee2fdd1f8fdebeeb9eba7ffdfbcc6ddf202d10703ccc3efecd30300cedae5e2cefce6d309fce3fa0dcc02fa01f2e0e7cde9c8e1cad4f0fd08dfd305fce0caccd0cefd00fe00fef406fc0bf4f805fdfb0ff703fcf2fa0000f70cee010305ff0503f5f5f706fdf9fafe05f204f70403fcf002f9fc03faebfa04f7fbfd0f0107f7fe06f808fdf2f00bf3eaf1f1efedf9f9f1fd0af805f9e213ffebf2f8f9f7eefbfbf80ef902fcf202ff05fef8fdf402f90100eafafff701f902020f03f205edfcef00faf4fdf8f7e4f4dce6e3ede8f5f306edf905f4d8feff00f0ff120e00ebfddaee0dd9fe0af0fa06f2fb06e5f7eae8dcf1d4fdecf0f3e500e6f7f3f4dcefc6dfe312fe081f01f308fdf9e80311011afc0806090ff10601fefa04f9143002ff13ee04e6051703fdf1ee14f9f9130804e2ff030cf904fcf30105fe05070111fbff0c03f7f702f9fe06fc0b00fe00fcf2fbeefef6f4f80afb190714fb07f90009fdf4fbee0108fafafbf6f6faeb0b06fcf006f708f808edf9f9fff503feed0203fd07f9d8f403dbf8f0f8f308dce8f5ebf009f3fbfbdff4eddef3fb0701000706e6deefe50d0302f1ffd503f0180303f0e603fcf8eef5f6f703f4fffff6e309e90cf7,
      4096'h03f00d07e3d9eeddd4f1decfdddf03e4e8111a00d80df6f3fef9e9e4d0f4c9f5dfdcfbf7ef000df509171209e8e8fbf2e9f7d7e40bf7fbe1d6fd07e2eaf1dcdcf3fbf4f2f9ed07d6f2e1ebf30ed8f7fa0ff301ebde05e0d4fce5e6e502faf8d8180afee9e3f20901ff04fd03f3ec07f3e7f9f8ef04f409f9fbfaf30be108e9f6fff803fe00fa01f7fa0000fffefff4fffc01fc03f5fafe05fa0104010004f407fd00fe01fcf6fdfefdfef4fffb01fb01fe02fcfef6fe0003fd0104f9fffefd0312f0ff16f2fa02f2f513ff22f3fa2cf9fffef9f60d082af705070409dc120a0efde00a01f10a06020c2b13fb061706de07010bf9100df812eaf9170e11e4f7e60b121622f00cf8ead91912fbf4052101ebf8e711f1ee0deffff6fe1dfb00f710ee1d0406f60dfa101a0c0603fa140b10f51401001d16f6fc17fe03050819f4db06fafcfefdfc0cf403fefe00fe0108eefbfff7fd0cf30809fbf80104030601fa00f20105faf703fe01fff4080af8f7f8f9fe0100eeeefff6fcfffffd00f7fffdf0f2eef5ddeaa5ed8ed4dfacd6f2fad0d407fcb7c1f2e0bdf709d6c1de0fd7dffebef0fdbbf50eeb030bf4f8e2b9ccdbb1efdbdefcdcf6c3e2fae2cdb7b0b2bcfeeff50df705daf4d8f0fc0700ffeeeee5f8f6bffffaf008060af3f9f302fb0300f001ff010b05ce0706e208faf7e8d9d91ad8f1eff8f606dbf406f3eaedfd0d,
      4096'hf2de04fdd300dce4cbf9f0c8eafef6ebd2fff8f0e4f8f5dbfbf5eaf2f402d905f4e209f6e2fcfaf9f6f8f7f8e7d7e3eed5f1d5f1fb06f6dfe8fc01e7dcd1d6ef00e4f9ded7e0dfe0c7e7e8d0fdf8f3eef2f90ccaca0cd2c9f4fed6d9d4f7ecf9f1e0fff9c8f80be7e80adfd0f0dafafed9f8fce5eadefed5fefddcf1e2fdd4d603f6fdff04fb020300fcf904f709f505f9fe0a0701ff0300ff0605fdf90101f3fffe02030501fffdfdfaf800f801f7f6ff0307fff6fdfe05f8fdf5ff0af501f512eff906f1ecedede3e6e9fcf8e705e9e5f9dcf314ebefeefb0100fffb06e1ede7ccfafde6f80ace04ffe400fbeceb08e611e4f1ecc9f6e1e1f9e8d6eccfe2e102e405f5f3dad3e7f1dfeffdebe905d4dfffeecffde8d0eff8fceef7ecfbf1e10cd600f3ecf802dcfcf9e4f0fbdbd5e6da0df9ffdbe2f8e4f100e0daf3d7e7df03fafc0000fc01040400020003fc0503fafd00fe020308fe05ff02090a00ff04f5fefdfffe00fffe0300fafffb01fafcfb06ff0000fd00fdfbff0603fefa00fdf5cc010dd3e0bccdacd9f9a9d8f9f8d2c30ccd95cce4d3bdfed7d5e2e3f4c4ddf0b70ff09fedf8d8edfcdbdef8c5a8fcb3f3a8e0d2bcfbb7ba0002c2bfa7b6c3ff05feefedf0e8f8f205edf801e7f5f7f6f301f6e60c08f9f2fcfaf1f2fdf5fdf5ebfdfcf9090303f1f0fbf8fbfbfdfaf6fefb0603fe02fe05f9faf900ede2f6,
      4096'h13d40c061ffcedf9d9f7f7fc02f204eedd0803c7ffd90901061409f80801f9eafd050dfef8ddfdf0f600db14e8f7e1faca09e9e6d1effa02fff1ecdde5e712e3ffe712f3eee6c4f2d7d6e8eafcea08ece50bedd1e2f0e6f1010cdfedfa16f0ea06d8ff09effdf7e0fbfaecf2efbbcdf3caebf0e7e9e60bdaf102e8eae2cae1e5fded0121e7f7fae3f3110612010efffa1b01eaff1b07d2020700f80dfcf51dfc07340de9c9150501ec100bf9fff9f50417f3ecfefcf0f5f210f417ff1513e1f116e60c23f0010be8ecf709f300fe11ccddfcde191ae8f60dfa08050ffd01f811e1d80403eefffedf030cea1e1112d5ffe1fcfa02ede4f5fad4f20aedf8d6f2d900c8fb10cbcfa0d196cac6b0d0e901d2c607fba2b6dfdca9faeacbcacbf2c4defab806f8bbf721ddf003f3cdeda0b8df9eebb5e9dcd208bae2fff5cb8d98a2b50803fefe01fa05f604f90400f40100fffdf6f0ff01fc0907feff05ff0901fa02fbf6fb01fbfa0405fefcf60105fffef9fe04fdf8fcfa02fa050604f904f8fe01f8dafe0d170cfe0f1a0d0bef160b0f162c100b11f6d8fb1105fcf30b0f0c0c05fb1200e8f6fef9f5fd0bf7fcfb0411ed132413f7fc06f505e4ffec1d051e0e02fd04070400fefafe01e9ff07fcfafff0fff8fdf006f9ed0cf4f7fd00fe0000f304f6030200fbfdfef700f40df5feeffd000305fee8fefffc000707f907fb0103
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'h191227e1ed16d2d1e02530112137f6e8eae8f80ef1f10c0c06051a3f0527071f22180b17f5f2030900f806ee03faeb02e509190e3606e9eefc25fd2b2d2512f20323fee3ffe9f306ed1500fde8030df817fb19250cf710060d0ac7dbb0c4ebb6a6ec0bf0fbecfbef07ef05f302f309080207100f1000e7fd0f0f1509f2eef1ff001713ecfb13f7f1f3131212fafbf2ec1cf90f160cff30011b0c250834311228fc232419d4272cbefd15b6fdf3fd08f8fcee18ef0cf9fd1808eb1a100332112d26ef29383f5d0a022c080a081f0c4a0101070c01faeff1f0401a233c06161912252bf1fb23f51321f60ef7e701050bfd03f6f13124ee16fbe3021dd801fbf411f902fcef1109e8fafa10f6f20cf822fb32172a02ff13f417f50a07151a131c04f1e8fadff1f7010e0d1918040c032616181e16110c021ef7f415ed100cfc0bf42105101c08efeeefeb1508120f01fafffc02f900edf6fbee12faf20cfe0602372542113429061d1908ecf3eee706eaf4ec100f14020f15f31c2c03fef303f8f0050bfc09fc0106f50b1e2231011d0bf8090301f30b4f471206121b0c3d3d122c3c372f2b3e182cf9ef080ce602fd00ebf20bf2f1d71aff0016f6fceff6ea032606f8f906eefd00020efa06f010f60afe101105f01212d61ce9e4fc0ad0000215030afef7f21b1a13f01714f20405ecfa00f8ecf0f4f80ae707010906f8eb161a,
      4096'h0ef4fefff8fdf1f8f7fe010109fcf1fb0c1506e7e6f8081dfcfbfc1df909f60cedfc120d06fe1707060e28f81c09150816091ff20f1812e3d7fefe040914f608fdf423fb040aecf5f2f7d90d17193042444e17f3201c0533342153f500f2f101ef00f4fa15faf81504e70306e8050ee9f0ebe503fef01e0a111a0810e701001d2bfe1a06213f265d08fefc040f1ee70a07190919f6021103f813f11ee612fb30233631f408e60d0e0103f2eb20fffb00fb0707391ffd07f11614001008091e1126d6bee3200ed706f80b12f01604fef907082603e7091b1f19080c1aeffe06faf211ed05edecf6f102fb0f2d051107003818fa18f5e6090a1d20ea01f610210226faf8f8fef014e804f6fd004c0a221c0d0f21f2f50aecf813101ef60e28140406f6ec0604eae9f3ea03fbfbebfa0c110304e90001f1160b1117121117f1fae90105eb0bff0419f9e3fafbfa0606293b4c142017110534fafd0503f0030c0902170e110ef810f5f4f3e7e5ef08fff50e0a03fefff3f902f308f307f7df2805011d241d39fefcebfce6ffefea19ec17fccfe9ede1f0fbe3f30aece020fee00f1bf31718fff7141b23061f07130b15ed0a1804e652051432403647f605f7fd1406f0f519170222f603fbf70c0e160d0dfb0d0a29111e171c07f40009fa1cf50f1105e9ebfd090a01fdec01e9fa0b2a0c03fffbf5fb1711ec0bee14f7f6201de41c,
      1024'h17f90505010a02250d221a16eefd09ef16110d10ef08f814fd030b0206330d210309132305e2040af3f60c030002fe03000e06070108fbece309ff371e243c1b530bea0cea010507fe0d380d26100911e8ef0600ea010efb22031f1802010a0811f4f210f70ef00cf3f4f90a03fcfb111c0dfe160e2b36fe001ede03ede81119
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hfdf9fa1501ececf2f906fafb05f0fd090521f1f6d90416fc0bfdf5fd04fcee11e2e2f311fdfe05f8fdd505d30316f204ffeef8f6e6f5ec01f502fcf407e4eff41f07fb050301fac20305f7f8000d01f90ff7fde5f5f1fb031201fb07f6ebfaeefffcf611fdf5f5e5f42ce9f114fc0103fc06d0f00601f1f80bfb0b09fdf615f307d8ff180705eae9fa08fbfbfcfd0700f6e8d3f9fdf5f6fe0610f6f9fe040a02f7f6fb02fe04fc02f5f9fbe60706f404ff070306f7f7fb04fe03fafcfffd0afcf715fa00fa04fc12f6ecf5fef5fff4f9f70301f305ffd9fef802f80006ecf7f90506f6fa06f4fc0702fdf306e701fc00fdfff3f2fceffbf102000e0cf9f804f3e8fefaf1fbecf5eb00f608fbf5fffefee6f701fa22ebe2fefbfbf809f6e8fb08f80805f7f9fd0aecfe10082af7f2e706f5fdfe06ee06e6feee032317fffc05f7fb0b030801f5011efcfaf50008f0f71ae20e03f6ebfdcb09e0fcfb0d0710fef903f7feec0601ecf205eff11f0307050900fe08fffae7fcfff5ff0aeafbf8fcf7e403f51afc14fbeffe02f2000a03f8fdfb07fb0502f90b01ea1201fa1ef1fbfa0f0400fc08ff05f1f3160610fdd6eafe05020202030702fdfb03fcf20b08e60a11f7fd03f9fbf71effeeee05f9fce908ecff010803faf504f2fbfafafafa070702f6f9f7fdfd05f707ff04facffbfa01fcf20009fe0800fd1206ffeb03f30b00,
      4096'hfa0bfaf705f81f08fefef7fafefbfc010007fe0105f50902e80dfb0cfdfe00fffefbfd03020201f70004f907f9e9f5ffff09feff0302ec000502fd010106e8f803f5ee000404f90602fafc0103fce702f60005f006fd02fd08fefaf9f7f3ebfa04f803ff01fefd0401effb0404fd0001fceffc0200effe0402f9f50e02f9f9fbeadaf40afefdedfbfa1403f70af3f911e2fcc4012efffc01fff80602f0ee0419fcf1f60f0803f8ddf2e7feff1100ebfdf616f403fbfaf7fffcfb06f2f8f10af9f5392600010df00be904e6f3e214f10300fff31dfef5daf3f902f2e100deeef801040926f2f503f9ff01e20811f60626fbf7050508f7050406fc05f6f40928fbd0fd00f1f800f108f2fefcfb00fbf507f5f7e8f9f9eae7fed0f3fbedfa02fdf6f80904fb07fe02f8feedf508f9cde30004ea02faed08f600fffffc040905d6f8fcd7dc03ff00fff5fdf4fa08e6ffb1fce8fc05ff05fcef11e009fafd06eee70affea1103fe09ffeafed9f8e5d7f8fde5f8f109fdfcedff01f0fedae3fa0dba14ea02ff1205e5f70004f409fd02fff9faf4f8e5f82604e3fdfa000021f90c06fc0ffe02fdf905f0f9f121fe1705e81806fdfcfb01fefb0202f907f6f700fdf1fbfecf11fffa03f80f12ff1cff06feee0dd2080317fb00ef0217fb05070a12f301ff000607fdf8071303fa0507f6080401f8f8fafafdeff702eef607020208f400,
      4096'hea02faf8fe020308fc030302fd01fbf9effefa00fd03020103ecfe0601f8fc000dfefef10401fff00101ffed03e7e106f5fcff03faff020100fefd0307fff3fdf4f1f7050501f5090af7fb0606f6ef02010102030505ed05ed00fbf5fefb041400fbfbfd0200020904e801f7f4fafc0e01f7020703f4fc06f8feec04fc06e40dc4d90cd2f0faf9fefaf50cfdfe00f8f2e4fedff798bdc3fad9fdecb401f9f20011c7e512fa0bfcd600ecf4e3f6e39bf90300fbf6dcdcec0b0efae506ecf5cfe8b980cdf8fcf6069701c6e8f6e5ea8100d0e3feb4f2f4d1cbca090beff41b80fafb00f3ed0df4fff5f9a305d4df0a09c808eefbf5f5c9ebf2e30e8011e8ea8400e7f700fbfaf5f503f6f2010500fa0000ff07010c0200e1fee3fcfe09ff06fdfbf5fff9f8fa02f9fc02f9fa05f5cef205fe030604e5f8f7fc00f9fbed04ffebf7f0e7e506fdfcfb0604fdf90008f5ce01eafd06f9f10002f80406f901faf7f0fafcf6f8020c0906fafee90802fdfcf9f6fafaf2fb02f10306e404ebf400fbfa05e11605e5f403ed1f08fd14fcfaf6ff04ff07f104cfe6c506c3fd02fc040de7f9080514eeeb020f10f3e90109f9e5d7fb030afffee50ef5fe0ff8f2f504fcdaff0c9fde05120108e6011efe02e611bf05f315faccfb06ef00f00904080316c408f80402060808050000c005eafb02f8f00cf602fefbf0fd0be2fe9dfcfdfdb5fe,
      4096'hf6ef00f5fafaf8fffbfffdfc04fffefcf6fcf9fdf1f7f500fbfcf8f70000f600f5f502fd05fdfef1fee2efe7fe03f8fe0204fdfdfff8ee030503f5f8fdfbf302f7fcf704fc0104e9fefff805f000f8fb0301ffed0300f804fdfc0203fdfef902030201fcfdfefdeafcfaf7f00101fefe0003f8fdfcfd01fb05fce7fbf9fafdfbdf0ffbf404fbfbfe00f7f8fcfbf4fa01fae8f508e700e005e6f7fefdfeff06fdf8ff090407fa000aef0d0008f7def7fdfa0c07f9f5f7fa07fc0101f90505e6fdfde4f4020801f600faf8fcfa0100d3fefbffffe704fc1900ee06fef803f2dff503fbfd00fb0af9fe0ae608fb06fbf9fdf6fc0608fee9ff08e406cd0b0101ce05eef0f0e806feed0106fcfc02f9030100edfae1feb6bad9fcbaeb0addf2f6f700f1f8f3ff0007f6f803def5e5f4dedcf8fbfaf8fde9f7f8fb09f9e6fd02fee4e802a6e4fffcf60bcff3f9fb01e7f4d8fed2faffe6fef7edefe10100f000f4dbfa0507f9f602fef7eef7e5f9cfe700faedf8eceef603f602fecd07c3e3fff5d7fed4f2f0e4fc03e501f2ecf50af6fbe9f7ecdc11f1afc4c912c7e104cbeff4e1f7cfe0f3e807fdebd6fad81acbedc69e0afafc0500e9f7ee02fcfbf20feaffc1e2f892cd09ed010db615dae410d2dfdbefd2f807b9faf9cb01b008f8d3f1f5a2ea01eefde9f4fef8e2e18f159bc2f5fef401e7fffc0803f304d1feb1dbf3e29703,
      4096'he702fef102f7fa0002f6f8f702f601010805f700f5f7ee08e4fefe0003fef5fef00b0600fd03fafffefbfc1704dde902fff905fceb0501000301060406ffef0afedaef050704f9000409f6fffaf1dffafa0405f1ff040804f70502f50bedeafb05fffe04f9fd02f504e7fef8faf6fcf601f307fafbf2fbfcf2fae0080104eb0402f5fcec02eff8eefdfefdfe0104fefff5e4f1fbd4e0f6fcf5f901ea0201f6ffe7f6f80104fef7f7f2f9f9e7fdfcf108ff020003fef1edfc0402e303f5f7fb00f9edf5fdf80107e103f7fdfef8fbfdf3fffcfedefdf5e1f4f1fd01eafcfdedfc030b03ef06f801faeffafbe6fcfd05eaf9f1faf2fffff9fc0003e603f8eef1f403f2fb16fefff9f9fb08f8fa03f9030408f9eff502eff201ff08f9ff05f7f80202fffc04fefdfbf0fdebf8eb060ffefdfe020001fc01eefd02fd00f5fdf7fffef711e7fe01fbfdf9f2fb0103f309f3fefdfbfcf302ffeef8fbfe03f0fbe6f70601fefb06faf6f5f505efedfafbfdfd01fbfcf4fc04f0fffa06fc0605fffa08f8ea0400fe01fff2fcfaed0206fefdfafdf400f100f1f3f1fef001fefa000106f2f507ff01010205ff05f8fe0df9e1ee050dfffff9040df3020704fe09fdfee408fee6f003fa00fcfd05100e020907ecfe04ff00fafc08010308fdfcfd0bfdfafcfaf8f5fe030701fbfef802f8050dff00fcf805f106f8fcffea01e907f800edfd,
      4096'he30300fff7050b02fb02fbfc06f6f3f7fdf7f7fc10eaf602e807fb07f60302fc0206faf6fe03f4ecf3e0070802eef000f2f508fbfe08fb030afc0c0407f3f00e00fff8fffdf5fb150100f400f0fde9edf303ff0204f7fb12020403fb02eafe00fff900fb0004f601fdf8f4fbff00fbee04f1eb01fdf4f9fcfefbef02fd16020afefb000201fbfffffc0501fe02fdfffffd05f6fffd0102000000fffd0101fbfffc000004010000fdfffbfafa0203feff010101000100000101fffbfd00fb010203040501ff01fffffefdfd01fb00ffff00fefeff00fef403ff00fef5fffefbffff000104fffe000103ff00fdfffeff01fdfef60000fdfe020000fffeff0001fff0f8fdedfdf8f2fa0209f90503fcf907fdf2e2fedddff1faf2f901effcfaf2fef6f500fafb0502ebf3e9f3e80301f303f903fc00fcfceefe00feef01fbf7ecfeede9f9fffffb04e4f8fdfe02ee04f4f9fffb04e90103ecfbeafcfaeb00f9dafa0003f8ef01f602e9f9eefadaf10204f401f8f101fd0000fffbfddbfffbf6ebfdb5f4f7c1f4e6e302f1f60ff8f6f8f9ff02f5eefba1d2bcffb0faf2defc02e106efe0f8f6f60607f2f4e0fce2f1abb604f4f207f7dff8f1020d0aefed04f6cd02f484ccfa03fff7b70904e209caf2a0f7d60300d5fa01f0edd6fdf1f703eca2ef0dfbf7f008ff03e602b9fdafd9f8f1e100f503fdfaf0fefdcdf487f4f805800d,
      4096'hf3f9f5f706fff0f7f1fbf2f60cf0fe07f501e8fd0703fb02ebf402df06f6d80302f502110dfd04e9f4f706cefd010001fb17fefafbf4df06f405eb04fee208fdfb25090800f700e4f3f4e205e708eef10801fcfe0601cffefc00fafaf8e5ee08fd0f04e50afdf0fdfe00fde0e6f9020e0803f51005fef6f411fedcedf6f7e7f7c10809ca01f3fa0df3f5fffdf8fb05030e03ddfbc3d7c2fed306fcdbf901f1f7f3000b06fdfcfbfd01d9f4e8f2b1b6fc08fafef8f4fdee03fc01f4fff309e2010796dff90603f8bf0203f2ffe7eea108e90b03dafdeff40ef80701f3f6ffaef405f4fcfc1609ffef04c5f8d2d501f1f013e70404ffe306f60104abf6050689fbecfc00fbfa10eaeff905fafb03f80303eef5ef0900e0fb08eff107fa0e02fa06eeec0510030404fcf9e3fdf404fbf804fe11fb04eaf9fb03f802eb02fc00e207ec10070404fffee4ef0ef4f9e60300ff06f7feef020dfbf8fa0504e5fbede410fafdf8f1f8f0fff2ece1e8061af9fafcf9faf4f302e5fc050efcedebf9f8faf4faf5010105f9fbf7f714f904f500f405fef0fffefd04fcfcf9f5fef6f60efd0a0ae9fcf0fe01fad4fc0700fcf9e803fd07f70500f905ebfbf5fd01fefe0dd501090bdf01fdfff3fef9e407080402f400f4f5fd0dfffce5fffeff03e6f7f10f0006fcf1e100f2fc02ff0c04effbfdfd06fcf4eafd03f201f9fbfcf4ed010518f0,
      4096'h07f80506040102f8fbf609040901fbfa06f1f4fe03f7ee0100f404f1fef7f101ec07fcfefc03fd03fd02fd14060609fefcfb02fcf900f7fe06010ffe04f80af9ffecf3010201f50ffafe0b0000f408fefaf600f9fbf406fd010302fbfdfa03010203010400f602fbfd03fcf3f80200f30006040100fcfff8ed0208fbfeff0702f5fff5f4fdf405f2f6f105fc0008f3fbf9fff4f102f8fd02e6f1fe050504ee0008fff8fefe01f9ec06f9f0f8ffe9fafd040dfafeef02fa0401ff03fdf5fcddfe04f5f502f804020afbfdfd0cf1fd02f80afa06fe07f2db0df80401e600f4fb1b04fb07fb04fcf707fce806fbebf6fc08fefbfe0005eefe06f9f9f10b08fdeb01e1ed01f0fc0113fd0601fa0105ff02ff0efdec0afeebf300f213fe060407f402f80602fa00fd00fbfd03060805f8f50103fc02fe0001eeff02fdfb0100f5ebfa01f3eafffdfbf322000002fe0607df00f4030a0e03fffa010b01fa09fdf9fd0b01fc01fefb07fb0306ee0b07e501fdf904f600fefd0801ff0cfef70b0300fe08d5fef9dd02fbf0fffbf2fc0704fbf200fd01f101e608e707ccfefaf3fe0004ef01f603ecfcfe01eefaf5fdfe02c5dafafff3fef7f5fbfc050805f7fbf606e0fe15c5eb04fa02f7f6fd06fa00f0fdbdf9f3fd03f20601020503fe00f5f8f6d5f5f9f905ff0005feff04e1fbe7eafdf4fdfb0003fbf8e70002f8ffe6faf702d40a,
      4096'he3fc010003f7ee0cfff3f3fff8faf40505f602f709f5e6fde7f4fdff0509ef04f804faf70303fdf901e3f718fad7f109fc070103e904f7fbfcfb0f04fc00dffaf4eee5030609050b00f4f80205fce7fefb0801fdf5f6f4f9f70303000af8f00200fafaf502ff00fff7d00009fd0004f4fff6effd05fffa03e301f4fffdfefbfffb07fb0503fc0a02fffdf9fe04fefeff04fd07090a01f701f70efdff0400fbfc0407010102fffd0401fdfa0802f2f8fd04fefe01f805fc00fefeff01ff00fd0901fcefff05fdfa03010107030afdf5ff07fefffd01fd000307fffbff00f8fbfffc01fe08ff05030300edfb08fd0000f901f6fa03ffecfd01fd00fa0d0100f5fdcde800c7020302e3fe0305f204fb09f4fef9e9f08ec3c807cef1fdc6f500f602e9e403f2fc08f7f1f8dcfee6f5dfc001f7eaf609df0be2040206e3f70ffdcd00f58ff303fdfd09c105eef706e5e79bf4e5e301d3ee04e4efdd07fcdaf9f6aa0302fefbe50302fbdffae40ec8d50bf7d303e8f2f1f702f9edf0fdbdfbf7f7990e110af7f8ffeefaed00fc1bff0b03f902f907f60905070201fef40301fe05030412fefa0f0500fd0201e90305f906f1010705fefcfefefafc07ff060cfffb04fefaf929fe020108f101ff0503edf705f413f9ffecfefdd5fa0200030cf704fefb0002fd16fbf904effa0507f1fe0006f9f8f9f6fbfcfa0006ef040103ff000400,
      4096'hd0eefedf08f4f3ed06fdfffd03ff03f6f1f8f6f4bbc0ed04cff3fdcef602f005d2e3f706fdf8ffe3f3ccfdbf00f3dc09fbf0f607f1f6fd0605fcf0fafdfbc809fbb3f5fe040504bd06ecedffe101baf2d8f2fad4ffffe8f7d805f8e2fbeeb30004f405e203f5fdecedcefdc2e2f9f4e3f7eff4f7fefeeb030204a6ebf9f5c7eef4f5ffed01f0f00000e6fd03f8fdfef4ee06fff1e1ff0303e0da0decff0309fdea05fb01fbffec0303ecf902f0eaf9f903ee0803eb0ff4030702ef01fefef0f4f5b0fa02f00404fe02f70c02f2ed0505f4faf7ea01f4f9f9f5fafcfafdfcedf50107fbf101fb06f4e9ff03d2edfa03f8eeff000500f5f704da04f5eafffdcf05eeeafde605f2f3fb03e2050706e9ecf1f5ecd4ef95a7e1fec7fd12e7f20804fcefedfe0502fbe8de02c2f9d4eff2be00f4ea09fcf205e7040d08e90906f3ddf7ff95ca03f1f701bd050cffffdfe1e5fdc90207d5f4ebe40af1fdf7cffe02b0e6010b03e9f5f603faf5e7008febf1feebfefce8e401e90303d605c6e004f5b7efff0efbf9fe0010fcfcfef000fdfefcf802fffffc0a0ff9fdf90801fc06ff01000efcfe05fe010308fbf6040005f0f2010a0303fefb090a050200fa000401f8fbfdeef5fd05fafb11f7f3fb0217ffeb000103ff0304fe0e05fc01fe02fff3f8fa0400060a0201f90308eafe020a01fef7fbf700ff03fb04fdf602f5040301f605,
      4096'he1f804dd00dbe4eb0505e9fcfe05f9fcf1ebf6f6c7d8ec00e5f0f6e3f705f901dfe5f505ff02fbdbf0e2fdcfedf5d200f9fffe06fa00e5fc0402ec09feffe3fe00eff1ff0301ffd7f9fcf0f6d604e5f0f0f40ae202f5e3f0e7fb0be3fff8d3f0fb0d00e7fdf4f9e7fde902ebff0305f2fbf3e9f8fef1fafdf1fad808f8fae0fdeffaf7e901f915f8f80602060cf6f8041b14edf7ed0919f9020a03f909fcff06fff70c14f60400f5ff1203080905eaff05f900fdf6fcf4fdfa01fbfffaf5fefb16f3230203ffff06fbf809fcfd07f301fdf50af9fb0108f815ff0506f8ea0202fd03071efc05fce31311f8fa00f9fe03ff07e3fb000500080bfcf71100fb0703ebfc0002041017fc03050204f5f701fbef0efa09ff09f001d9eefb00020104fcfd0ffdfd080203010dfc0e1805dddc01f8050505ef02f9fd07041107fa09e5f9edfae80007fcf21bf6fe1602fafff4fa030202fbfefdf7fa0efafae8fde0f2fb02f922fcfaf3f8fb04e0f7f2effdf6fd01f50901010802fd01fcf3f6020202fcf2fefd0efbf400f9fcffedff02fef900020afafd0c04fe00ef0300f902f90102fdff01fafe0201f8fffaf60cfbf0f90303fffb02fa00fc03fcfe07f500fee5ff05f9e9fe04fbfd120107f70107fbe7fff6f900090000fc020b0302fbf9faedfbfef60303000100fe01fcfbfdf8fcfefe01fbf7fc04f601fff901f5fe0001fcfe,
      4096'heb0a030e02fd071901f7f907fef9f90024f5ef18ee03fe00f40601f30f13010018fd03f50500fc090313f902fae202fe0d0101fb01fe04fd06fbf808fc07f2faf5f8eb01fff9effe08090cfc1607e6ff0d06fef70001fff71105faf910f8f705000201fd0208fcfe0fef0012fd08fdf501fef5fcfd010300e403fc0e03f8f200f1f201f205e7f50001f3f70000fa030ce1e3e104ded6effef50a00e5ecfd0709eaec01010903fdfcf2ebfafcf702eafe0307ff00fff6ecfd05feea0506f1e8fef1eff500f8ff01ebf9f806f9e6130cf0f1f9f5e907f5e7f5f80205f7faf1e1fcfd08f7fbf8faf9e6f1ecf8efe0000def00f0e501fdfefafef7fdf6f8fffefffe0001fc0501fe1a010404fbfefffe040308fd100206fa0101f70efd0110fc00ff04fa03fe04ff030a0501080104f8f0fffafefffd01050204fffd030807fff200fdefffff0202fd03fa020003fcfafefefa01ff070906fe020cfd01f007f7010600fc0606fd0afefb03fbf602fd0001f601f8fc02fcf4000003fe0508ff0bf905f9f500ef05f90707ff01fcfe02fc00020503fc01fbf1fa04da08fbfa0002fdfce705fd0303fe05fffefdfc0205d8f0fc09f2f603f806f5fbfd020b01f6fceb0c0bdff00400ff020b01f50702fbf1daf8f6f6fef400f801090f03f9fefef2e70dfcfa0206010bfe0205e0f508ed09fcf0fce60902f5f0fcfc0b01ea07f9f8e1ff,
      4096'h0809060cfefbf50c0bfb0104ff030004010c07fc02070002fffafc010402f5fafe0308ff01fd0203fdf4ff0cfcedf7000009010300040303fdfff8000708f50502f0fd020001030b00060804fa06ff05070efdfdfb05fb0211fffffefdf5f104fe07f7130604010c0008fbf7fefdfffefd01fa0202ee0501f2fdf508fd02ff0dd4f4f8f9ffeaee0bf600f007fceefdf9ea05effabd08ebfac703effc0505e4f8ecea07f80300f7eb07dfedf0f0d2dcf5f1f800f3fe00e7fefb08fffff9fdd5f3febae0ff00faf5df00fcf9fde5fdbcf7eb0ff8f3f1fd08ece2fff7fafde6bef4fffc03f4ff00fce8feedfee1edeefdfb00f703f801f2f5f5e6f3b3ee01f7c704b917ee18fbf50ff708f9060209f6fa0213d6ed04cec4fdfea40905e0e4f2d9f5040c24f80604fd02eef209f402e6f400090dfdf6dc04eafbf10802f5fcf2d0f2ebc60a05f5070aa5f616e10df218a7ed0103fec903f11602dffbeee3ff23a2f4fbf8fff204f9fe1ff3e2fdd0e4fefcdf04f4f0fcfcf2f8f9ddfdc602f8fec4f9301c061bfcfcec0202fd05fdfefef3ff091e1600f2b200fbed070ae7fcfc080215f7fbfd070602110b1cdfdcfcff0904f7f2fbfa0506e0ff0203dd0503f10001f5d8d2ff0002fec6010dff070510fd02f506fbf2020719f9f8fffe07fdfcdf0401fd08dffcf0030df8e9faf0f513f8f9f9fce1f60afefbfcdbfdee04fbfae603,
      4096'h1fe5fef909f1f0ef02fa08fc01fffefaf9e9f7fd02d8ecfa0aed01fcf503f9ff030afdf9f6fbfa0bf4fa0901eefe01fdfef80302f9fdf2ff06020305f7f9edfbfc09eafeff000d00f80304f4f8f620faf6fa00d900f7f9ffe802f7f804effffafd02fef2fafbfefef8f4f8fd0306fbf4f9ebf2f5ffe8fffdf5f90bf7fcf904ffbff206bbfefcf4fa06e801fd000e01ffe905dff8b7dcb2f6bef5ffe10000f401f0f2f6fdf9f608e500e0f9dbf4d7be08f8e2fb00cff6e5090ff8fef500ffd3faec80d408060afabc01dfea12e4039aeedaeb07d9f319e1efdc03fddb02f9a1fb060203f70bf7fedefda90dbfe504fafcfae6fbfe05faf0f3ce0a9a01f0f4a9fe0d0c0108f206ee0c00000200f407f702f101f60af905fdfdf905fffc050706fa0a0afbfa0304fafb0007f60500ea0a01040e00fd02050003fffcfb0304fcf703f7ebef0505000906010d04fbf30f0301050401f0fb060303f101010cfd0df603f901ff0200030203fee70304f70d040003f306fdffeefff9fa01f401fe11000101f5ff02fefc0003fefb03fef8fb0703f2010700f0f8f0ffe90300f50403fafbf507f6060bfe06000dfbfff807d5f003fbff0102fbf4020402fe08fe08fdf00bf7def005000210f5fc06f1fe0312e6fa04fbfbe4080108f2040503f807f5030003f6020a04f503e6fbdff6e8fcfff6fc08faf60a05f0fdfae500defaf000f9f8,
      4096'hf505f8fa06f7f409faea02fffdfc04f815f90ff2a6e4d9ffb91df6e201f708ffe0ebfbe9fcf9fb04010501f1fbb0c1fc0115fe06fbf9e70402f80df3fb06defceeb8cf050cfdfbc3f718dbfaf7fcb6fae60a07d4fe02ea0b34fdf8daf3eaa4ff04f705e8fd0b03e7f7c2f4d4ce0cfaf906040b0605f5f304c4fa990f00f2a205f8ee00fefd08fbf9f500f602f9fd0302ee09f8f000e2e904dff8f6f00205fa020af601100201fcf50111fefd03deee05f40a0504f3000b0702051ef508fbf1000407fe05fcfcf90af9f9f202edf4f1fa05ff00ff04fbe6fef50304ecfef2f81402f609f800fe0d0303d800e9e3f5f8f800f41809fe02fc00f3fef3fa0109e5fef5f7f200090402deea0500ee04f21301f907f2fcebeb0306ebfbfce308f7f7fffbeffb00fbfaf8fdfee902e706f7e70b0317fffff304ee000c08f5fcfefaf3fcee1b01fe00fefcccf6f4e2fcfd0eeef4e2f4fef305facaffef07fcea04f9e20efa030405fa0007d90c14f1f2e4fff81201fee311f9f408fb24fbe10df0f4edfcf308fcf8fdff1d01fe02fbff05fffefb05f9fafcffff0a02f710fb00000110ff0007fb01fc0004fb0411f8fe06f9ed0001f8000200030403020009fe0001f805fff6f5020303f806fa02f902fdfcedfffd03ff07000109070f0100eefeef0105fefe0701f901fbfe01f806fdf5000003fdf90efefd02fffd0100fb08fd06f802,
      4096'hb8fc06ae0aedede60be5120504f6f501f6fae3fb8eb9c9f8b1e701cfed04ef0be2e8f3fffdf9f4eb01dcf4d4dfceb0f9fcf00900e1fbdb070bfef70e0303bfeef380ca0afbfc0bb5fbfee7f3f5fa99fddaf508c005f8cdfabbfdfed1faeea103f90905e40303f4e5f9b800bace0514e203edeef5fff7f7fbc009a2f901038b06f1fcfc050ceef1ee10faee00080e09fbe309d0f6fafd1807fbf7f4f407fcf607ffe6050a11fdfde8fad004fd00f8ec010105050aee04ff0303fd1215f9f308fefe0e1205fefc01ed0bf4e708f513f4f500fcfa0f02f5d3fefaff04f401e7240502fffc12fdfbe4e006fff0cb02fc0316fb0fed03070a060307fbd4f200f70ff507ecfaee02f0e9daf5e901f9f808f1f4e9eed4efb5b9df01dddf06d4f5fef400e1d7f117f402f1f8edd7fdc0f3f4f305fdf70106d8fbdafc0608da09f9f7c3fef1adf006fc0703c9fd0901f9daf9fcf5dceafac101f8ddf9dcfff8d8fff7c6ea030206de02f9fcead6db07c8d806fee7fbf7f6f9020ffbfaecfcdbf8f7f3ccfbfd04fd030107190a03f5f0fefcfefd05120a0cfcfade01feea18f7fffd03f5f8fefa09ff000100fc0019ff0402e6f5fe06f5fcfcf903f10109fe0102070bf10d11d6e905fc07000d02ff07ff00f7e5f6f807fd140e0415070202010609f3ff01fdfa0310020efa00fbe3ff0e0c0efaecfdf3ebfefc0302fa1af90514fe0cf403,
      4096'hf30401ec040df9f8f908f4f803020606f6f8ddfbe8d7e2fbf5f9fdeffb05fe0502e5fc02f8fcfdf5f6e2feeb0408e9fe0005fe04f1fee6ff06fcfefafbfd040906f6f404f600f8d80303f2fae4feeff8e6f902e2fdffe9fdf8fb04e2fff4dffefa0302fefd01fcf8f5e7f4e9ebfa00f8feedf6fcf901f4faf9fdf203faf6dffcf8f3fbfbfdee01fa00f2fffb000108fcfcf9ed02f2f8f5fefb0dfc00fa03f1fa00faf903fffc04f603eafef0000604020203fc02f1fbf103060306fdfdfbf8f9fdfe01fbfffff5fcff00fa01f8fef3f9030003f0fe00f9090203feeefcf3ff020004fbfffe01ffff03eff9f107fefc0404f901f8fff30107ffffdefe0300eafa0004f9f500ff05fef6fe10fd02fdff03f306ee02fe030efff801f9f900fef6010afbfe110402fff5f5ea03f303f6f70404ff0104fbfcfafeff02f8f701fc00f9f6fd1003030200f409010103f109f8fa06feffea04fcecfff1000209f9f704f800010009fbfaf7f304fefff5fe05fefffc01fcfbff050009fbfff3fffc01faf8f6040505f700fb08fff9fffcf7040304fc07ff050809fffdf908fdff09fafef50e0d0601fd0402f7f8f80206fdeff5fe01f3fd000603f900ff0102f8fe05f40208edfb0003fefe02040afc0009ecf00a0208030500fd0a05fa03fb0106fffb0301fbf6040609fff9fef2fa09f8f7f9f2fffd0509fffd000011fdfdf5fdfff707,
      4096'hcdf3fed40aeef3f403e003f8fdf8f601f402f4fab5dcca02bded0ecef005f601efe5fefbfa0506ebfece01dee8d8d10106050209d1e8e7fb0009f3fff6f9caf8ee9fd909fd0307c3faeae906dc09a9ecd40606cafe00def6d8f700ec02f5aaf80a1000e704f0fde7eeb9f5c5d60901eefef9fdf0ffffe803eaffa0eff8f0b205e9f9fb000003090800fd0206fef6000a060316030b090301f706fcfd040405f81112fcfe0204fa08fffdfc090ae5f2ff030e08fef401fdfdff020aff0201f1ff08eceeff0305fd0f0004f80310f1df08fffffd0f03fc0d1afb05f8fffff8f903fb020b0f0006fcfa04d9fff2e7fcfdf2fdf81504020101fc0c0209020005f400f90c0504fdfb0a00fa000101fbfcfaff0ffc020009060cfeee0afaff000308fcfb0304fd04fe02fa04fa02030be9efff0af4f8fdfefeff0104fd00030500f50b01f400010401010b0000060400f0f5fd0702ff0809ff0009110500fc04f5fe07fdfdff070401fbfd04fafb00f700fef6fef10401fceefffc0cfdf5fefa07f602f01703e80af308e9fe0d06f909f8f7f8e814ef05f016120513e7fbe3f4fd03042af30508fffe07faf60b07fc031ceffefa0502030b040000f7fd0cf5fff622fbe70019fcfe02fcfbf30af7060617f3fe1202fcfd01fbef0409ff0005fce4f5f006f8061afbf903e90b0afbdf0f02ff1a01160501fff10706fdfcf0e906ff1004,
      4096'he7ed01e30dee1be5fb04f7031bfa0c08efeee9f603f430fa03f403edf4ecf80cefe5ff1602ff03e303df11ed0200f905060d06fce2fe0306f403e7f707faf109f8041efe0704f4feef01eefdf1100a060808f73afb0701fef30303dcfcd50717fe040516f2f7ebfe1008f1d10fe80513fcfddf0f04f800f42d07edf5ff0805f6e90108d3e80bf00c07fe0e030306f3f6e30dfd00cbe4e9facde909e3ff04fbff16000605f8fbf712f5f6030cfbe7dd060cfdf800ea05ee05fa010405ff02e6ebffaee707fd0004faec0704fbe9f7de07ef11f5dd06f8f700f10304fd0001d7f5fd10fcf500fffce6f6dcfeeefcff08fafdf5f9f303f2f8f5c501dbf2fbffc5f0f0fe0001fffff3fb0cfb06fb0201f608fcf9ea110ffcf904f6f7020b070516fa040103000205f1fb0fff090e01e2e9ff04fb02fcfbfc05ffff0312f70804f106fdeff9020007f70508f8f506fff6ed01060f08000b02e702f403ffef1705f5fd0405f7ff0807060efc06ff03e9fbfffd02fa1203fcfffcfae902fbf604fdf80fd0e7fb18f2e7fd10f408f5fdfc03fefcebefdefa0feae702e0e9f3fe01120a00f2fdfefdfb05f7f3feeaf81afedcea03fb00fa01eefaff05070511fd0805defafd06e2ff06ef0c1803f8fafbfdfccf05f7f90511f9f500faf603fcf303ecf8f0fffafdf7060dfe04fed6f90cf3fbf9f702fc0cfdfc00fa02e4fef2f1f700ffff,
      4096'h0f07fefc02fb0cf90209f4fc00f7fd0108fbfd00defb1305f20601e0fbfd000a04e1fffcfe0000e0fe0b050afbe7fafefefffbfe030301fe0003fcf2fffcf2f403f9ff050202fbfdf301f900f911fd08f406fe04f9f508f807fefdf602eff30801f90000ff01fe0106ff0af4f2fd0217fbedf4fe05f8fd030efe00f1fd02f50de406fcf906fb120bfaf900f901fffb04ff0b05030b09f802ed06f2fb0ffafcff080afdfe080402fb02f6f60f03ddf80501fefe01f4050004030201020505f9f80ef0fafdfcfd0203fb07fc0af8fade01fffb090d00fcfc110201fefdfdf9f60001fb0807fc0403f9fce0f700fcfcfaf8fdf106fcf8f206fd02fa05fffd00ef070bebfa09fef8fd00f702fe0309fd0302fafb03f80ffafa0108fb02030cf9ef06040100fd030305e600f709f907fa05fefdfd0001fcf802ff00fffa03fcfe0406010cfc02fbfd0711fcfce60308020cfef603fc13f9faf404edfcfefdf3f707ffff00ff0702fafe07fbf8eefe06fc02010002060100ebfc03020406fd00010cf9040a00f3f604f41d0afe0dfafe05fd01e80bf5fbd6eef509dde902fefcfff6fd09fa0702f70406f7020101faf9f5f3fefd00fef7ec03ee0107fef50cfd03e1f306b0eafef10417e6fc0c0209fcfaf105f412f3ea02fef0fe0efe0c050804e6f8fd0208f905fa01ededf401fff2fe01eb0100fff4fcf2fdf9cc0ad8fcff07e6fb,
      4096'h06f6f9f7fb01f6f2fdf30003ff03fdfdf6f7fef6dfe9f1fe00f707fefcfbf0feecf2feff0203fc03fce501e7f1fbf602fcf30801f8f9fc040401f3fcfbf9fdf9feeff3030302fae4f9fd05fde8f805f805fdfff5fff4ecfde3fd02edfcfbf8fb0403fae8f7fcfef1f6fb02e30008fdf0f8f9f400ff01fafff102f3fcfffdfdfecd02fbd5040bdeecfeed0000f90ff5feddedfdf99bdac60bb7e90ac3eefedbf9f2e7f00dfc040ae612dcf9c700ebcb0003fd0208d3f5dffdfc01fb08fef5be03d693cf06fa00ffb0feeafa07d6d9c7fcce0a00bc01fedff2d203ffc3fd07ab0fff0b05ed15ef02e7e2b907c6c508f4e9fffceff7070002f7c108bff3000690f5f8fc0210fcedf700fcf9fefefffcf2fc1bf0f901caf9e102e31affebf405f5fcfff3fff6fcfefef204eceeedfbdafbfc09fc06020ffcf1070602f4fdfd0ae8f4f7efd70102fb07eb0516fb050b0aedfafffd01f5fdf81efafa04f909ffe5eefafaf4fa06fcfff5f6fce9ffeaf60403f202fbfffd0402fff80803da0100fdeb01f7fbf901fe0afefa0503ff020a0000fff010f70002050702f7f7000efc010d030b00fc05fd0202fdeff1070c03f6fefded06fcff09fef700f902fafdff0806f6fc03130104f6ff0cf7fc08fdf509f2fcfaf8061404f4f405ecfefc0dfb0104f7fdfb0402fe0102fe07f9f408faff00f901050601fdf8fafc00000204fc0306f7,
      4096'hef02fcedfdf701f0040203fef7ff01fc01f9120009040d07f004ff0306fa05fb03f902fcff0102f7fdf0f3f3fee6e80002f90303f6ffff0105fc0efd0502ea0e06eefa0404fffd0500f3f7fd09ffe100000401fcfcfc020002010401fffdfa0400020c0a0200000908eefd07040400f605f8faf7fe01ff050102fd03fefaf0fd331f0301fb07fa11f8fd1c0602fbfdf701fad806fdd3dd04fffb0bef0007fe0206fc07f6f7fc0c0e07f4f8f9f205140a03180500d9fcf502f80607f009fe06e508e8f005fcfd0b00fc0a05fc0f0cf50ee20ffbf7fcffed04fbfffe060d14b1f0050400f40c07fe02f8fb0c06fbfc0002fceff7fc0601fbefd4fedd00fc060707000b0403f9f21e01fe0206fdf9fffe0012fefe05f8f601ffef1500fe07fbf7fcf80106020300fefcff0efbf1fdf00102fff7fa000cf9fc00fefc05f303f9f30504eaf200fffcfb0900fee8050afaf4fafa03fcfb040515fc1202fdfefcfef0fefef704040104fef9f7f8f80705f5fe0006f5f5fffdf9fe0407feff0cfd06f4f8fb25f90e0104f507fbfdf906f902f70329ed0c13eaf0f5ffedff0103f2f8e5fff9ff02fe00fb010b0c06f7f301f001050a07fdfc1bfff4fef9fae3ff0402e501f2e0fc05090d02ec0811f90e2416fcfff9f9feccf51502fe11fcfd00f706f20501fb01fc0006fded0ffafe08f703f9f8fe0efff4fc0d0321e6f6ff06feedfc03,
      4096'hf405fef401041208fff90202fffb02ff07f9010100f8fcfd010afc0f100409fbfc02f7fb0002fa06060b020107fdfcfdfe00ff00f8ff080105010802fefdf9010aecebfe0100f304fe0f090101efeefdfe04fd1503fb020b0402fdfd0ef50cfafff9f70007060bfb00ee01f6e80100f602fe0005fff801fe0f00fdff000bfb01fdfc00fc04e5fef9f70c0afa12f80304df05ea02f8fd05fbfafbfae4f5fbf308f502ff07f7fc00fafadae6ecf608e40700fdfcfc04fd02030101f6f2f5fd020dee0420ff020206f1fd0afefde60af601130201f602fcdffef0fd030b06e505f8ff020b07fdfe02e9ed0afce6020605fefa05f006fe0200f706fee109f5fc06fac4f4efd1fdf7f1df0dff0e01f9fafdf3f3fbe80199aad10bbbeb0ecff0fafb0f04e9feff0807f7daf8e8f8c1e6d4a507fa00f600e7dfeafcf506fe18f9f5c0ead289d9f9f3fb10b4eaf2e4f8e4008ef0dffef9cd0deee6fcd507fae5f6fd9607fe15f9e602fd01e4f5b4fbb5e70804f807e0f6f3f5ee0001eb0289eff5ea930ae9f702feff02f9f5fb07f602fefe0605eefae205fce8fe0005fc03f301fb07fcf1f2f9fdfd0302f0f9d6fcf203020602030a0205fafaf8fe0303fc00fa00e9fef3fdfb00fd04fcf3f9f6f3fbfefde9f6fef7f5e803f6f101f90009e3faf5dffd0108f804fffffcf80210f7f6f3feff1401ea01f806f4f8040601eafd00f9f8f5,
      4096'hf803fe0dfb02220401f8f5fc00fd03010dfb05f906e8fffdec0dfd0af9fb10fb060209020203f907ff160b070efced0102010500f205ff030702fd0406f3feff09faee040601fc0a04fb07fdfa05ec01ecfd0c090500000f1702fdfc0cfe06fafefb03fb07020806ffde06efeefb03f3fff7180cfffc0107fdf8f816fa10f506e0f3f2e6fc00f3060bfcf3f8f4f2fe1508f400fbe2ebe705dff70b0e010f0500050100fe0a01fb00f806010104ddcd02fe0cfc0c0d0a12fcfff8fd08f8fff413e5c8f207fa0d0fd90a07fb03f8f7fc09ef0cfe09fc0bc706f1f9f6fcf810cd02f60603e60703fb02f5e90005f91500f8f500fc05f0f6f9fdf9f4da11f6ffd40c0afcf80d04e7fceb0311f7fa0e02050efdf9dc07fa0727fa03f7fcfff1f6ff0cf3e9f5070403fcf500fc061404fee001e9fe040403fef704fffe0ffbfafff2020618130200050206030e05f3e909fe011efa0605fae8e102f9fb01f7fae90ffdfd0cf814feebf4e2fe04f5f917ed0a16f4fdfe070705020108fc0af206f018f2ea0100e6faf914f60108ed03fcfbfe0222fe0bfdecd8ec03e118050606fcfef7f8ed040e04fafde900fa020605e4e002050408faf600fb04ff040a0d07fde105fbdddffe00fefae303f4ec0605f9ca06f5fd06f900f8010efefc00e5f5f1e301fdf3fcf9030805f3fbdafff9f6fef6f300ed0cfafae6ff080affc821f104d403,
      4096'he2f700f9faf6f60700f40105f8fafb08fb05f30805f7de0ed90402f4f503f7fcfc1104f8f901fd0af2fbfc1ef3d5e50d00f50800f306fefbff020108f807ed0912dbf2020a0503fcfdf70707f8efd605f2fffff8fa03fb080404f502fffffcf5f8fd04100a1003f107f5fff0e7fbf2f5f901fe0a03ea0506eafaeef1ff09eb04dff4fec509f7f9eb05e4050101ff0005e4e4d3fcb4a8d906d0ec04e4ec07f706e4ee0409fafdfcef01de00dbe7f4d602fb0002fbefe8e1fc02f9e80b00ffcefbfcb9e8fff80b0ac6f8f801f7f7f6c8f3d60106c105f4e4f3cef5f9da06ebbffe040b07e706fb01e6e8d304cbf305feecfbf1f0f0fc09f3fdeb04c5f4fbfdb8f80404f90300fc160100fbf8fffffd01000802000402fd03fef20ffe090100f8fbf905fc010401fd04fcfbfdff01f5fa0204fbfd0004fffaff000200fa0201f40404f7f2fd05000009fdfb01ff03faf80002ff020109fe05000c00fbf4fbf807030201fb03ff02fb0803f000fe0100fdf901f9f80001f3000403fdfb0efe05fa0104ed01e9fcf1faf301fe02fc01fe0001fcefec02f9ebecfbfdf9fefd06fef106fff9fffdfa01fff5f6f9f4ebfe01f402fe02ff0000fef803fc03ef05fe01faf7f4fdfc02fcfdfff4f905fffff8fbfffdf7fdfcf7fdfcf1fefefbfff6fcfef0fcff04fffe02ff00f5fa00fcfcff040502fb00f9fefffafbf6fe00f8fdfffbf600,
      4096'he814fef705f90321fcf50901fffcf6fa0dfced05f0eecc02c705fcd8fbfbf8fff20407fdfffe011b01f9fc06f0dde90506ec05f9fa08f70300fafaf5f807dbfbfadada01fc0810f90319f8070519e00ef307fde3fc02fb000607fd06f6ffdcfd0709f5030a0a0adafdde02f3f211fef503f8f9feff0ffc04d405d91602fdf7fedd0007f8f9fdea03f8f9f1fafdf406fc090eff0004f5db02e1fdf6ff0000f3f7f8fe08ff06fcfdf207ee091805d5ebfd0bf7fd02ecf60203fa050afdfdfde6fd05f5ecfa0200f10afcef02faf9f6f3fdf9ff00e5fdfcfcff0bfb00010aedf505fdfe05f9fff9fefdfdd9f608f6edf5eefef10af201eafff7e7faf3fc0201f306eff7fd020103fefd0605f6fbfffefafefcfded1b040e0000f4fafb00fd0202f8f40afe05fefb06010105fc1100ebdf07110705fcfe090006fdfdfa050302f401ebfb0a03ff08fd0d03fbf90b02fbec000e0afcfc01fee907ea03fee907f4fafbfcf4fc0f070706fe0203ff02d801f4fbfff10f03fc0efb01fcfee100ff01ec0601f9f9050002fcfb0801f4fe10fc00fdf6ebe4070ffc0707f8f2fd10f30200fd050b01f504fc06fefbfe050bfbf3fd04f40afdffef040400fdfd00f9fc0808f80205f5020101010e02f5fd02f5f7f202f405011205f9f302eafd00070205090ffefdfcf902f8080e00fffaf7fcfdfafdffe60cfefdf203f6ee030dfffd0cfdf6,
      4096'h30f701f7090ae3e2f9efffff070805fbd8e4dc01ddc0eaf401f612e2ee0107fc05e7f507fdfef6e6ed01fecbf501f107fef608fde7f8ee00fc03ebfef6fd17ff13cf0000fefefadafbe30b00e9e50bf0dee9f3d8fa09dd01e3fcfed001fbdcecfaf3ea0203ed001ffb01faf5eb04fdfb01e6e5f1fbfffc0ad4fdf8ed01ffc8f7eff801fa00f0edfcf801f1fffbfafc06f8e9e501fbdaeefb04f5fefafafbf407f4f7eb1105fcfb03f8e1f6fcf3f7d4010602fffaf2f9eb0402fdf205fcfbee00fcfbf603fafffff4edfafcf1e40afdfbfefcf9e400f7ebfefffbf6f0f8dcebfafb0700f003f7fdebf5fff6dcfd040505f806eb000000faf9fbf9ee0afff7f5fffbfbf8edf8f0f9f0f7fbf6fd05fd04fd0519ea08ef0b2007fa0604fafc01ebfce6f6f503fffcffee06070b0a0106e106f4f6fafd0201feffff02f6f1fa0001fcf8f102fc0205fefe00f3ed000407000107f7ff09fffc050bfc00fde300ef1df5fcf7fc16f8fafedcff13f8d90702f716fcffec06fffff5070bfcfa1606f70500e2fdfd050001f11b03f80400fd02fffe0803fb0c07f4eafef401fa0501f9f701fafdff03fe05fdf5090bfa06fbeaff0004fa04feeff7f4fbfc02fff50402eaf6f7e9f1ff02010907fc050a0000f6edffe60cfd07f502f9f6fb04fe09fdf2e5fdff0602f40108f8fbfcf90702f7fdfdfaf5fcf701fef4f9fbf0fde7fb04fdf303,
      4096'heb0aebeff2fe26f4fefcfa07faf000031eff21fee0cef001f22ef5e0ea11f4faeee801e807fdfde50f1103fa0dfdf007f9f3eaf20cf1eefe01010600f8f9fd1707d2f3fd0afd0fe9f407fa06f602e5fe05fbfa0205fff4051503f5f0f106c6fa05f40d0afcff00f3020217f3e301ff0c03feeefbff0306fd2df8e508fa18cefbe6f60600fdfafc0300f9fffc01fcf9f81104f60efd04f6fbf3f8ff0f0a0518fdfbfffcfc030502fc010619130ddbe200fbf601fff6fe000307fb1115fefcf90104f7f008fd0af71703fef40bfcf6dffbf708fb0a0601f302f5fd03ec0ef9f410fcf8f5ff0008f90307eff8fdf4fc01ee05fb15fffafafff9f403e7f60304f30ad2ed00c7f703edee01dc0c00f3fbfeffede1e9f8a0b1d1facbd10bcef304fd0cd0f60316f7f9f2f504db05b7fedcbcfffae50a04e0f2dd040ef9e00d0c05d5f1018ad1fbf70b04a3f7eef108e1f4c0f7d6f3f4c1fbeed9f7c701fdda07f5b7fb080c06e100edfbf2dcb607a9c70009e701e9f7f60a0303fad508ceeafff1a10212fe080600f00d0b08030afa03f70100200af7f3f60c1c05fb04f5f507fbe8f30fed00fe0601fcd31203ff0506fef80307f20000f910f8ff050403f0f90b100006ef10fffd09f5f0fc11f6f107ff06021202f4f2f9f5f01513fefd04f0fe18f5fb03f8f905fefbed120b04fe170bf705fbfff0fa01e9000118f31802f9fa0a00,
      4096'hf50009d805f0e30f02ec0308f700f0f500f7f8fcc1e910f8e9e6fb0ff7fdfe00ede20305fd0706e6f6ff04d2f5e8e9f5fee70508f00be3fef9070400f7ff07f7f4bfef03fb00f6dd0102f1071200f3f7e4fc07da0008edf2f5fdfafafdfde2f10201fff5f10802f1fcf600e3f30500e6fcfff7f604fdf9ffe407defe03fedef6181e00f60411f9e403ee03f5080400f5e5fde9f6d3b9fffae6e0fde0f202f40ae8dcf8fe08fe01e912efe5c4e8f3cef8060bfdf9fe01d6f70102d90cfcf9fd00e1d6f606f00202d2fbf9fa00dc0be3f8e7fb02ce04f8edfafaf7010dfeebdafc070a04f700eefce7f0aef2dad80d11e5f8e9effa03eff6fdd902e206edf8dd05eef80106fff109f603fcfbfd02fefefd0706fafe00fd01ffef04fb0b080502fdfffffcff03ff010afffe0b07fd02fe01f6fbfd00f9fdff0200ff03fafffcf7fa00f00702fd02ff05040cf6fb01fefe01fafc04fffdfd04000d02fe0704fdf6fefefd04fd01f901020800f80c0100fa00010102fefd0cfffafb02fe0e0302fd00e70bfaf7f4fded13fdff0204ffff01070ef8eb0adf000bfbddec0cedf3fef500030506f6fefdfafbfaec0205f9e8e701fee400040801f1040904e7fcfb08ccf500d8fafafffffbf303f8fd12f2f8d500f51cfce102fe04fde403f9f906f5dbf9f9ef02ff070901f5fffe01ffe500fc000a0005fa00fbf7f8f6fbe0e107fce601,
      4096'hc70901ed00f4f7fc0101f6fcfbfefafe0104fff9f505ec02d8fbfdf501f9fe02fdf402fb0800fcfdfbf4fb0f05cad400fa04fff8f1fdf307f9ff00f105fdd6f30cedf0ff090500f2fdffe800f9f2cb03faf5fff80cfffafbea0102fcfbf0effffff0fb06060801f8ffdb00ebe9f50005ffeb0303fcea01faebf7c8ee03f4c8fd0706fef1fefc1300fc0af8ff0400fc01160ef506fc082302f60ffd130209f6fe00fcf500f8010507050efc0004fffe02fff901010cfbfc02fffd03fffdf3070502ef130002020008060512010902fe04060a02fa0000160414ff000601f106fcff02ff1ef906faf8040005fc02010206fdfa03070104031517fdfe030005f9f8da0512c6fc03d90d0afef416fef6eff8daf4e308a5bbc109c3e504cd050efc04f3e60105020307f4faebefececc999fb030a0909edf4d805e109fb0b0802d0f5028cf3fef6f90ed304f6f102e5fc97ffdd03f5d2fff4e5f2e701fbe1fbff9ffef710faf40a0b00e9f8c601cfb80710e1fdebefecfcefecf9c2058be000019102f9f800f400fefaf4fafaf8fcfcfefafdffeced05fafcf503faf901fcfafd0101fff5fff9fefd02fefef2f5e801040803fcfcfffff302f60303fdfbfe030305fcfcfaf6040401fcf00201fffdfbfcfffef9fbfcfd0001f004fafdfaf2fafcf1fcff0001f4fdfbfdfffcf5fd02f3fc0109fb08f7ff02fe00fef002f901fd05f803,
      4096'he60002ec030d0103fcfafcf804fefefc04f811f7f5fa0500f00bf600fbf7f5fb02ff0a0300fcfcec10f80d00fae3e8fa0c0205fffd0600fcfffaf5040e01e602f7f6ee0000f8f51a05fafa0602f8def8ec0805f103fdfb00f804fcf0fff9ef02fbf601f1fe09fcebfcdef5e8e6fdfe030ae7f700f9f402001bfae5fc0313da0de70d02f7fbece6fa01fd0304fd01030207040bfee8f1d607f4f20100000102050dfdf8ff0101ffdf07fa0202fcf1f2fe050d01feffffe703f2fe10040105f2fd11dfdd0003ff04f8f90ff9fa0701f505e5f906f80205280204fe0704fe07d2f202fbfa0802f8fb0c08d909e6f5070212f8fbfffd000bfd0dfa03e302fbf500fdfb10fcf802fef3f10a08fb00f9fbf6fe05f8fffdf1f7fffcfaf1fcfc0003fcfc13f5fc1709fffcf104e702e9faf0e804fb13fb04f2f4f000fdfc0f07fd03daf71bfde400f804fd02f80cff03e5fbf20800ffffe21508ddf6f2f700e9fef1f009fc05fefcfbfc03f4f9daffd9f7fdfef20bf6f5fa09edf203fc06dbfff9fdcb01fc0bfdfcfefd03fe03fe020601fbf5000a0f07110302f900ebfffd06080009f6030b04f80102000001f1fe0903e6ff040f0007fafd030004fefe04fb0304f5ff05e0f90508fe040508fe090804fde60904040306fbfbff0e0406feff0704f10b00fd05110305080205ecfffdf6f6f7fb02f30cfe02f905fef700f20604feec0b,
      4096'hb7e2f7d7f9e6def60dee0e08f5f80105eeecd701a1a3b5f5c7d60cb2fbffdc07f6e5f205f9f9ffeaece903d1ffd2d600fdef0608dbf0e6fb0b04fb16f7fce8f80b80d401f60809a90bf3f7f5fa1ba1fac5fd14af04fbeceac1fd01c6f90682f80201fcde08f106e9e5a3019ed2fe0602fee1ecf4070df2f6e0049fedeefa80f5050400fdfcfd06fb0100fc01fe02fdff02fbf90300fcff01fd0600ff000100fa01020203fc0101fe02fdfe0203f7fa0001fb01fe0201ff0200fffc03fffff90300fa0600ffffff040000fa04fcfffefe020200020300010101010000fff9ff00feff0003ff03020000fd0003fbfcfe0403fef603fcf901000501000100040104ff03fafa0107f70502f70108ff03010707f9f7f901e4f207fa0501fbfb030bfcfcf80bfef802f7f6040d0b020bf5fbff02030100fb05fffd0100fc050702ff0609f6f3fe04fc01f6fa070700fe01fb01f9fffefc04fe040807fcfdf2fffff4fafdfb09020207fefc0c0f00fbfc00fc0207fafa08fef2fcfbf600f607fa04f601ec0204fafe02fa0cfafdfdfc01fbfffd05f703020e05f9fbee17f8060af7fefaf11c0206fcfb020304fdfc02ffe6ee020409fe04fc0b21fc04fd07f502fbfa07fce3f8fc050cf80a04fe080905f5e9fdfd0803f608fc0107fdfb06fc08eef503fc00000f040a03fbf9fef905f4fbf9fa05f801fd050402fbfffe01f9fe01f306
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hf3094126103f28541208fd060e123e3b1f49211e1103071b22230c10f4fd12172f03060bfdf608fe070f0cf6f7faf0d8f9df0a392c31e8f60cfdf70afff8f8f7f6d8d4e9e6df08fbf7121ff50e1afe0ff8e8f507f2f7f7f1230b3026140aff130ee106fae4d40c02f52bf81627e228e2dfff2d1a1d0605e81beaf4feea1f120912f5fa12ee140bf805f7eae9f11315f911e5f410e8061f0e0612f91fe02904e6d7fe160d020611efd6e8d103f219d901ef111b1f100b0108ef08edf8fd4f2004070af4301cf0ffe51f2200f8014249fff5030f1906fc0606f916f3262b0a424a12f5f8f4f5fb0c15fe04f4ebdf2f3214ff0ff0c9d7e300fcff23fd11fc030b051e35f41312dc05e3f0ebee0a10f4170f120f2c2e00132cfe12f5faf3f00df404e1b9c9070cf611151e08fb0b12fefe160eeee2f1e6fefbecf6f327141f26e9c9eddbd6f20c0803fb091000f0f9e0091408f9eefdf8f5f30af000fffd101123330e070105dedf02e521091ee2e3e9fd0ee7250d02130cfe0beeeb1ffd381f12600f17def30911edf608f9181503f60b0ff6e82307024c3a2e1315060ff60a04102000d7ed061d0bf002fd04f601f0fe050b16ece20507e8f5f7ef03e4eef20c1c0f071e0d1d170616f6ee08e8f7e9ed07edddf6f807ed1ef0f6170f0b20fa06170efbf6fa010a21ff14e719ead6f9e30815ee1310f30104221dfb3520191b1d1e,
      4096'hf8f212fbfb0be5f810f42818fc220503450e1e0df5fff50508e00a1806effef7fde6050215021c2823182702e7edf10c36d9f73d1714500608faeae417fefb0110231a07f105e2da00030ee80906143c3544251e0720ea17ff03c9fe0902f701fb04ffec1706ed0cec06faf5f5e7f7f5ec16050ce9effeff0208f6fd000907130227e7e215ff0700230c29eefbf409f2f308f7011f1b2df5ecfafd0af8eef606161a1909200f283bfd2a1d0c13fe0312f41e3710ff0fe902fc0bfd19ff02db0ae5262e260a0b0a12f905fa15fdfcf20bfbef031e0707201b23fa0009150fea0820f3000a28e61107e1e61c18162f080219141f2304eee918d6e4220dea140108e8e1ec2012080de733f8f1f112e5071b0f0705ef01e1dae8ff08fe150515160914050d01041b23f73439e4f107e5e218f7f007080e0014010a1bfc090c03f10cf8ed00f9f908112a02fe1cfeeb0309e901ed1104151b2206e710e314f005feedf0e8efe4f1f816070dda0810110117f6120406e0ef19def2ecfee51dfb1603fe192b2319f3f40d0e04f8f11104fbfc071833fb05ee1017fd131506061c0a2238432808ee17f7f40dea0408fdf5fdf80d0716dff3e905041a112a050ff4f8f40ff5effb140222ea032801050cfceff50bf5dd0d0a0b10ffed1bedf312e704f10aebec1bf606f000faf1eb04f6101209fbf0f3f81aeb130b110ff2eb1807fcfc3a,
      1024'h0712130424fb0113e4ede9f40df90cf50312f50e090305f6ec140a1210dfdbf6e916ebf7f4f5eaf305eef91702e9f9e80dfdf2feeafe00e3fbf5ee0507160c11fa170b1cf4010eef050fefedd6e1c2c92e1919e806e3f9e7f1160f0afcf6f50405fa0605fceaf8eff202f72006091ee4031409091f241d2d061b19ebf50ef204
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'h11f2ececf60ffcfef106e1f418f4f6fdf7f50404dafb1a001404fceb1307e102f7f502e5fd04fdfcf60ae2e00704f6f701f6f4ff06fbf3f80509fced04e31afb0317fcf9fc03fcf7050aed02fcf40d0207fbfdd4f1f0ff0deafb0cdf02f80de9f504fd0afedef9e7f6f9fbf101fa070c000ef7fefafdfe05f20107f8fcf816fbf8e60100fffef606fbfefcfdeffe0400f5e9f5f3fffdff010b02ffed0c01010007f7fffa01f6f7fafaf201f5f605fbfcfc0300fb07ff01ff01f5050201f1f8faf60ef2fafdfd04fe02fa0203ecf8fbf603f700ecfeeee507ff00fbf4fdef0201f4f6f5f5fa09fdf8fef005f6eef1fb01fa09f700fbfd01fef9fe00f6fffb1005d8f80df104f8f801f309f300f4fcec0cf4ee0100fbfae1fef205fef0f1f4e802fff703e8fd0608eff5ffe0fcf9e5f3fbf9f8e8f9e8f7fcfc0107ecfc0bf6fb0b04fdebfa05fbf9e1e80010f7f8fe01f0df0b05ea0400f707f1ec02e2f213e0f0f6080306fffafbef06fd0704ddf7ffee0607dc0003ff05fffef80afefffeedfafcff0803050502fe0002fdfbfbfafe01f9ff060300fd0500fe08fe01fbfe0001f70103f0fff804fbf8040709f8f906ff0002fb00fafefffffd0606fefefdf9f4fbfbf5fe0003fcfbfc06fd04f6fff2fdfafe060403fdf9f7fc00fff608030503fd0101fefb010400fe0803f80009fff9fef900feff09020403fbfcfb01000305,
      4096'he80410f206ef03fcfd0007f5f904020302f8ec060006ecfbebfbf5f3f2fcfb050afc00e300f8faf6e5ecedf602e6f40b06fefcfdfb030407f303eff8fafdee00fbf0f804000601fcf504f5f008faeef6fafa0701090705fd02fb06000006fb03fdfe07f6fdefeff9fffbfdf5030e09f900f9f6fcfc0003fcf7f2eef50006e9f8e9f600f8fe07faf4f7fde8f5fdfe0600e9eef3f800eb23fff7fbf602e8f9f1fd1aee08f7f5f4f805f3e608f70105fcf6f10307fafaffdafafa01e5000af9f8f20423e80100fd01030203f00bfbfc00ff00ff09e8f8f9f1f6faf008dd0bed11f6fff5fcf60414fbd4ff02fedcf0fdf8fffb13ec050500fdf6fdfd0ffbfef70702c1f90dfdfadaf701f701eaeaeef6fb0606efbff7f8e3d7f4c7f5cfdbe5ffe900dc03f1d901fa0603cdd1edf9f0ddfe0606f8f405ceff2300e30ec10100f1d605f6d7dffe070900cddcf2f3ff0404df16eaf8faeb080bf5f105e904faf102d8fff0ff0df4fef6eef9fcfef201fc0a06e2ffdff3ea0505fcf8f5f5d5ff0004cff9e70d0210fafaf303faf71c06f8fd010c00f2021104deecf7f107000bfd0312f70801f7f2f9fd0c0604fcf10400eefffa0c0602090104fdfb0914e2f70af9fcfafdecec02f9f5f4f8f60c1e160afe1900f40700f1030ae200f7f60000f9faeafa04f3f9ee040913090904f502e3f9fafc01f0dd08ffedfb0aefe6f9040611070c,
      4096'hde00fcf102f401fffd0306f4fb040301faf9fefffcfeeb00f6f7ecf50608020606f4fdf4fbfe01eaf4eaeb02f9e9ed04fff5f4faeff9fff7e9ffe6fe02fd01f1fdebf8050201fd02f7f300faf8fefaf5faff01f500f8da07ef060bf8f907e9f7fa0201f802e2fdfbfc08f7eee80ff7f4fef0f601020302fbe1faf003fd05eb0293dad0f0e3a1f9feeeefbb11ecfff00f09f0dbfaeabde8ffbff3dbf3cafdbbfcc4ff10dffeef0202edf9e8eefde7f10108e9df00ec06e207ecf8c708fc00cf040a80e6f6f0f5f3a7f2d8fcd3eff6c7ede5f405b2ee02dae8e0ebedd80dffb3fb0de804f007f5f1cc04d90adadbfbe4dbf7d6e6e9fb08030af1f9de0ef5f39efafcfffceefaf1ff01fe090509f703fefe0602db00fef2f904e700eefef700f2f9fafefaf7fe07f702e100fb01fbe2f204ff02fcfce8fef8fefcfbf0f9f7faef00eee4f904fefafcf9ecf001ff0502edf801f7f6080701f8f5f0fd0a04010ef3fa0003fbf904ecf709fbfcfa06f002ffeff8e9f8f7fa050202f708e802fefcf704d0dee812f2c20002f705e5f9fefafef4ff07dbeb05e6df00d5f7e9eff90cd108db0201e7f6fcff07f6c5fbfbfed8dc050cf5130cdffe00fa0e02d8fbf4f4e7fbeca0fff8f8f0fabde116fcf8ecfed808f7020dee0803f8f4d8e30af90805d7fbfcf70afb07f5fcf4f8e001e9e20ef2f2ffd7fffa03f51df3e4fce5f10203b808,
      4096'hf1f1eefdf201f5ff0a0bd3f612fbfe04f8f1fe05db0c1600e8ebf0070001d5fff3f003fcfefafa0d04dcf1fff8fdf704fdf9f4030af805f70209fdf5fcfc03fd020b10f7fef8010702f7f709dbf3dcf303f9f3f7e9e9f3f103250c0d0af70c01f0f7ef15fedcfed5f9fc00d3f202ff0cf913e7f8fff60de5e1edfef3f6f203fedbff02f10bdf00f705fceefcfe01f901faf7dc020df9eefadf03e5f0efffe9fef1f9fae706f4fbfbe2faea0602d6ef01080ef500ef000f06f100e50900f0eb00f1dbfc03f9fbf7e207fcfef30bffdef2f0f11afb06fe140d09f30a0d06ffed05f6010dfcfee7f4fd00eff7f5f11705f6fdee14fb04f909fef1f8eaff0907d709c3dad6ec01ca10f5ecfad108f502f3f401f7eae9f3bee7f8baede7dbe6f2dff7d9f607d2eef4f91600ebf100f6caecf1f7f6ee07f402f0ffe1f2c0eaf2dfcf13009bdcf204f3fbb9f7e005e3ec01c1f7e3f8fbde09fbd9e0cfe4f6f60f07c4f4f0f6f9fc04ea03d4f7e804dd06fcf80103e30f03f8fa01fcfefbe7f402f7d5ffdbfbeaf3f1f20601fa12f80e09faf80e22092ad6d6fcd9ffefe0f3fed1f4ebfb27fff711eff50218271bf3ea070822f5fd07ebf6cdf7e2f3f00b11e50f00d5e824e52902fdf406f8f3f401ebecf6eaf1d0ffe7f9080d12e2d3f312ebe413effc07f30ad7fde7faf104e807d3d605f5f001f1fefcf8ef0700ea052f0d04f1dafd,
      4096'heaf80a1001d0fe06f7faebe90503fcfd02fee00b02eae1fbd102eb05f40cf6fcf20bfaf3f6fbf918e8f4000d06d9fb0115fb0906d8f70203fa05e709fde7ee0de4c9ef05f800fee6dd0404070804eb07f2f7ff0407f61637eaf808021010db00fdf312fcffeafd02f7fc01ee020af607feda06fdfd010c0800efdbfcfcffec16ecdbebe4fde20dfafe06e3fafc04fdfd03fcf0f5fadcf702e7ed00f8f1f7ecf9e9ef06e2fb01fef103fef2f20603f1fdf9fcf505f302f1fff6faeffe00e201fcffebed03f608fee0f5faf3fcf2fee7f1faf507daf6f2f1fbe5f5f7fafaf1f3f301fcfef7f7f403e1f3fcfce4f3f5eb02fbfffd00fa06f5fbf500ffff0203f5fcfcf6fb030904fbfd00f8f4fd01fcfcfef4020bf9f806f604fdfffffef3fefc010dfafcee06f9fffe0203ffe4f303f105fb09f4fef2fdf20105f8fdfdfafff9fcf80a01fffefa06f603fef8fef5fbff02fefdfdfffbf5f8fdfd01fbf801f0f4faf501070a02f6f9f0f9ef0001fafa0703fc00f0fc00f6fffdfff60c00fcf70206e8f90cfaf6f805faee03f5effef7fffcfefcf403ff07e804ee03f8f3fcfc01fae70bfdf3fafff3faf1e8f504fde7fbfc00000603f002f0f9fbfee9f107fff2fefbe3f8fef9fbfaf3f80507f113fef30003faf9fefdf8ee05f1ee06041308ed0008fb0100030001040702fd02f706f3f4f4ecf9fefcff01f9e9eefcf6f905f808,
      4096'hea1cfb14fd0602f604fb0dfef7f6fefcf6f6f003f90dfbfeecfef4f0f70506ff0809fce9fdeef109f2eafbfffdf1f811f9ee05faee0c01070212f3fdf9ffeffcf5fef0f7fffd100afafef801f604fcfde9f9f70801fc090a0ef80a02ff00050017fa0afd00fffb0ffdf8f0f7f70cfcf6faf3f5f9fa05ff0108f8f4ff010300fc00fcff0201ffff01fe00fdfc0100000001fcfcfffdfd010300010303fd0101ff010001ff00fd00000102fcfdff01fcffff02fd00ff00fcff00ffff0101fe01fefe02fc0100ffffff04ff0003faff01ff01fe0100fdfcfd0001ff01f702fafefe0100000100fefdff0002fffdfcfd0000fffefafd00feff000001000000ff0103d8d1eae8f2d5f50003f4d4faf5fefef400fae2efe5d70801df0bfae7e602dffff6fb08effe0cf9f706ebe2e2fa16f8fe0005f004f6f7e8fc02f6eb030ae701f6e7f4f700030101d5cdfc04f2f005defdfc0301eaeffae1f70de0ffe8e7eed6ff07f5f2fcfcf005d7f6f409eee9fbf9f7f403e0000400010707f80bfff9eef1efa7c5c5e7e898f6ffe5e3e321e504fb19f109bee7efcbc7ffbbf8c8adda0bb6efa1effae5ed0eff13e0a3e8f3fdc9e30cf9fdf002d9f6e6ecd8089df900f1cffcdf8ee3fff4fae3a7c00b0ed4ecf7eae3d3edf5c9edf9dbf6d9dff6f30211b4fc1805f2eb01e2fbd005ddeaefeb05e7e0fed201f103f409fbdefddc14f3fb86e4,
      4096'he302ebe311450404f121d4f010f5fb07ece810f3e8120dfd1ef20ffadceaf8ffffd800dafefee8e3f118efeaebf4effaf508e2faede30ef70bf5f8e1f9d6eff9d92fe8f409f0ffebd701e7fae6e6dcedfaf1fe10f2daf00ee30bf7d0dd111a05fdfaf1ebf1ecfff7ffeee8e503fdf601fc0de00703fff105000b19f8f8eacef2bbdee6dcec9901f4edf8b9fdf1f7f9f708ffc403faddd9fcbc10d3c3d5fbbf07caf3ead3fcf5ff06d7dedbe4f9bef1f90ae903fec3f90df9fafdb0fd02e9d3ffeb9dfaf7ef0402a5ccfafae301fab7ece9e601ccfa0bf0f3f9d6faeb0ffcad090bfb04f304d5f5d9fbd4f4eff7fd0ae9fadbf2f50d0309fa02ecd00efe07a4fb08e90402f60af8fbf5ff0006fffdfc0cf8f9f205ccfe00000bf2f7fff9fade051bf8f9df06f3f4fde6f5def8f4edf603fa0bd7faf801f9f60cf60d09fbdbfbfb0216edfffcf614f701f4f405dff9e2fbf6f3fdf8f0f6f300f90e01e4f9e60303f5f9fdf8fdf102ffff17fcedfbf50305ff05eff6fcf7fcf6ebeafbfa01f6080b12e90003fb10ff05f606f608f2f6020fe8f003eeebe3f2ff19eb1e1ae6ffee0101f9eeea02f60600fe010107d4e810fb02fcf0ffd405ebfcf4eafced02e015f1f9fef503040906130c040202d2f619fceb070eed06e4e9f7f3d8f8e5e8f6100106f8efc7faf008e70bdc0507fbf10d000afae40d04f70b06fffa1a000fdff3ff,
      4096'hf206fdfefc03fafbeff5f9fdfafcf4f7f6eef705ebe6feff00fbf1e9ee04ea00f601f908f6fafefcf3020001f0eff401fa02f7fb06f805020d01fdf4fdeff6ffed09f9fefc01fef9f2fcfdfef400fdfafdf0f9edf6f8f2f4eef6faebf90306f7fc02f7f602f9f7ef0106f9f20dfafbfef9f9e5f801f8f8fef1f7f903fcfefff2eb0c0b04ff12f8f7fefc14fd11fffff7f8f7fcfc06f8fa09eff7f006f7fe02ff0001f7e401f9f6f7f9f4f603e4eafa08f90602fdfd0100fdf8fa1402fb0205f5f30507fcfa000911f3fd070bf7f802fffffe0b0604f9e605f2f5fafdee05f605fcfcfa010913030bf907ff0be501fc00f9f3fdfd03fcfa0209feebfbfc03ffff0606000403f901f3fbfaf8fc0b04fdfef600e803031603fefcff070c0afcfafe0302fe01fffd0502f30ef4f5f3f4000506f9050308ff0c00fd01f000fcff12fe02f0f40403f906fb0f1101f703fb07030302150601050d01081007e8ff040201feff010500f8f705fc12f3fef21105ecfff7ff01fdfd0006fef6fafafff7ff05d7daecf4efbb09f1fb0de9fd0905fef912f0d80bfcdfdaf8cdfde1eff20ddffeee10fcd300f40422d6daf0ff18e0ea0105edfc01e8040510f102d8100ceee9fae7bfe205f6f408dcf6fcf7f5ef0fe8fefcf009e6130b13ed0ae503030ef5d601f7fe1d0002e7f4fdf8e7fcf7001805de01ecebf602fc0711f9e8e5f3fbfec906,
      4096'hdb050f0b01fd0600fcf21707e501fbfd110bf11106fbf6feedf9fde5fc010cfff604fceaf802fbfee8e8fb1ef8d6f8f104ffec09e2f91efef404ede707f0eafcf805ec00fe04ecfcddedf900010204e9fef9fffd0cfaf006eaf2090ff904f9f8edfe03f9fd050b11fefbfe16f101fdeafee80e01fdff0dfbf2faf204f9fd0a020113231afb0afef2010414f3f0fff9020e08fb10f80df302f907e70d13f90009070cfdfefefe0109ddecfb10fdd7040109f3f903ffff1affecfff3000510f0fcf9faf004fb0c04151307fdfc060014ff05fb000e1218070b0e0e000b03021205f8040afcff04f712f802ef07f10e0bfbfef003fdf9fd02f6fdf8ef15fe07fe1ab5cbc4c8f592fbf9fef8aff6fefde9020df3cfcff3bdfffcbff7f8d6b603b7fcbce7fdbd02f0ebfce3dcd1c6fed9e4fff9eeecffe9fcee03f4fed4f1fad4d8ecf3a6f907fa0afeb1cae5eadbfcf8a4efd7ebf5ac00f1d9f1f7cd01d2ec07b3fa01ef05e60ddbf4b7fbe5fad8ecfbfccff9f2f6f3fa080a05fd06d5edf1fdace4ea02f9020703f70eff00fd0c0cf70003ec0210fdeefe0603f5fbecf2f90302fd1111091bfcfdf8000cf8e8040507fd020e00f6fa0bfff0fb0a01f5f509f309eefe0e1803fd0700f30300f2fb06fef900e8f6f9fdf9040205fc03fd07fcfffdff02f9f6170306f0ed00f6fafef6ecf1f800f515feff0afcf8030311fefef7f0ef,
      4096'ha6cecfccfbadf5fefc03c5fef802fffb00fed3ddf1c8faf9c0f6f1e1d10ad3fbc9f204d1fcfbfcfdeedcd8d8f7eeedfbf4faea04c9f8ecf9f205d9f1fce1dbebf4b2f6010400f7c7d9f8f3e6e804adfbe1eafdc5ecf4e0f1f4c8f3e5f9f0cbf80aef02eff7e9f7c5fae101e8e6f7e8ebf3effdfe0104fbfd03fae7fbf5fdbbf6cefbee11e9c6f4010002e92005ebf91805f8f1f2e7f6e7feecf60003ea08f6f2f7f40419f9f0060c11ed0f04fb1002fb0bfef3f7eff1edf706fcf1fd0815e2fe03d0dffbfff9f6f00cf506f5ed00e8f8f2fcd3eef113e4e9eddbf300f3ffd2000ef0f40202fafd0b08effdeddafae6f30cd80507fdf3ed02ee04f60205ffe303cdc9d4cdffb90cf4f701d004e8fbeb0d02fed1d4fbcaf0ffd2e8fde5b9ffcbfcbaebf9cbf8f400f5ecdcf8f1fbf2e2f701ef0bf5daf9f7fff9fcd0fb09c8e205f7aee302fefdf383d2f1f1e9f403cef9d9d7f5affc01efdbd0cdf2db0501c20401f5f1f101ebffc10fd6f7deeb02eeddf9effd0afc08050af1fc01f6f101c7ece6120c1700fcfffdff0104f6f1f9ff000af8fd0c0008f5fbfd08f4ff03fc07020412fceb0800f811e2fd010efce300020ffbf800ec011404f30be80300ffee0ff7f3f4040404ff01080bfe0003fd02f4f3fd07f8fe0605f70b02060104090204f6030203f7f2fe08f8f8fdf6000dfcf2feef10f7f700fbfdfef7f3070008f5fd,
      4096'hd7d7e4ccf9d0f4010911dd0101fb01fdfaf6f3eaefd3fffaedf704e4e1ffe3ffe6f402e2fbf702f906f9ddec0bf9e8fdf2f6f1fde3f8eb03fa01e1f20be2fff506eee302f505ffcce1fef6f1fc0ac8faf8f2fbcb02fae9f3f9e405f7f3f7d9f9f9fdfee600ebfcc9f5ecf6f3f0f8f7ebf804f500fb02fa07f1fb08f4fbfed8f2fef5040000fd00fd01fefbfd01fffbfffb00fb06ff010603fdff01fc05020001fbfffe00fffffd0201fb0209f8fc02fffd02000200ff0002fefdfefeffff04fcfefe000001fe02ffff020101fa02fdff00fa0103fef8000403000102fbfdfd01fdfffeff00feff00fd060400fafe02fdfefff90003fd00030300fffa0008ff03e8f9090600000104fc00fcf4000300f00401f507fa01f603e9fcdf07fcfa0704070bfded00f5f804e8edff08f7e7e10202fcf808f3040dfaf70cf416fc07f1fb05fff00903051303f5f90602f200fcf8f3fef80f02f4fefd080c05f402fc020104030303f80100fcf6f7fbf6f21c0bfbf6e4f306fbfe07ff02fae708fe05f80fe80416faf801020ff4ff0cf7f9fffd0104f6fb08ff03f1fffd02fef3f9f80103010affe7fef7f8f5f3f5f20ff8ee10fe02ff0afdfd01f7f9fbf6fcfbf6efea00eaf7e4020202f30806f905f907fdf8f7fbfc0309fefbf50dfcfbfffffe07fb03f600fcfc0205f50a07fdff01fbf8fffe02f3fb0501f807fdf00207f601fefdfc,
      4096'hdf0709100b0a03f5fe1103f7f20502010f05f10cfaf90001ed06f6f901f80702040afaf90309fa20ecf0fd0c0addfcff110504fef70319020902ec0003f2f70debf8ff0902fc01faef0b08fe08f20cfffcfb00000208fd12fcfd0200040df60203000400fefcff0bfbf2f701ee1004fdffec0cf6fd03fb02f7f9f4fd04fbf61be4f3080702edf6fe05f6f70cf1f6fff5f2e6f9ebf7d60500e603fff6ea0308fe04f303f3fb0007fffffdeef90109f902f504eafafef6e20102f6efff05df01f0f603e0fbffff02bee9fcf7f7f301ecf4e8f7fcf2e9fef9fafaeaf6070beae9ec00f6040001f501f1f0f8f1fcfbeffa0603fe020703f7fbf5020004f9fef600eefafe05faff0604020507fcfaff0301fc07fbf9040701fefd020500fb03fcfc02fb03fff8fcfcfcfcf8fafd03f9f4050104fffe0300001000fd03fc0201f9fb03fcfffafe000101ff0607fcfb0200fd00f9fb06ff03fc0001060105fbfc02fc0103fffe030100fe01020103fcf3fe03fafcfdf9fcfe00ff02fffffcfc0203fe01d0ee0614ffe7f6fc0012f3f40009f40e04f1f7f7f6f3ec05dbfce8e9fa020dfff20403fbfdfb02f6dde3170b06ccebff000ef407cefdfdfce703f6fbf80de0fc09e5f0fd05f7f0e1efeaf6ea08fef3f8e507020518fff7edefdd06fcfcf5ebfafa050af1fee6fa0e11f9f601fd12ffe709ee01f5ff0308faf1ede60804fbde0c,
      4096'h0eff03fafbfa03fdfa02f2f6fffef8fef6040601fd0af4fc0907060b09fcfefb0e0d0000fe03fc00edfbff05f3ee0604010002fefe0205fa0b02f301f70904f9f6f40508f90805050700faf7040203fa09f2fbfc03f3f407f90903f70604fcfefefdfb0b04020802000312fdf1f500f1fef1f607ff0e02fef1f802f803050105ddedfce2ebc8f6f2fa0cdd09f2f70613fb05caeaef06f003d6ebe8ebf001d400d2f6fef00601fffce3cce30705ceef0105fe0800c609eeeee206cbfb0e07e504e7c20502f9fdf2e8f3fcf5e3fbf8e2f3f2eff5def3f6e9f9eef303fef4f0ddf9f90206fdf7e4f5f404f4f4f8f70303e103f5fdf3fe04f8f3e1f6f1fc04ffc2fabed0c7b6e99515f4f7fee0f7ece7f5e7fb01c0d5fdb5f909a80ad7c8d809bafccefb06ebff08fdf2cfc4eafef6dad3f3e7e9e9fef3feeffbdafbbaf60ceae1f3ea9eeb000af8f5b2c5def0fcfe09ae10e007ffb2fcfbef0000b40ce9f1d2baecfff6fefc05f3feca0fecf5cbe7edf5f5faf2e012f5f60915ea00eaeafafabcf7b5c8c8e1008bf300f3ddd409e70df806f704dae505d2b8f7a8ecd4d6d8fec002d1f5eccff8080103d8e7fbe305dae9030c02ee01f2f4dcf2f102c5f417e8c3fb1180f10606e5f199eae500e8faefdcebf6eafab8f325e4ebd5e508e90a0eb90008fffef2f5bcfdb907deefe6d803efd707cff8fb06f806f5e3feee0cfbfd8cfd,
      4096'h13ff02f8040aff05fcfe02fb23f60103faf71301fb0110fc02f0f90c0004f6002d03fd0d00f9f9f91005eff803f70afffe01e3f91700f5f9fff905e605f63b05000a13fff601fc1101fdf4f108fd04fd09f6ebf8f40c0df8efebfdfffbef0bf7f601f80ff3eefbe2f20904fe1bf6f705fbfb19fafef8f703fb0016f2fffa14f197d2d3d0f89503fdfaffd5f9ee05f40a10f9bdd9edcdd7fabbe2fde6c505ca0bb2fbf3caf7fbf7f8dcc0e9fa04d6eb0903ebf20bc5f7f0fef4fec6fbffdfdfeefea20bfafcffeb9cd3e204d904fbbbf6e1ef00b902fed2f0dfddfde6fa08ac050106f7ef0becf8cdf5d8f5e2e4ffece008dff6f40306fd0aedf9d6f5f1fe9ef7fc010406f7f604fb03fffdfefcfefcfffc010004fa02f7fefffefa06fe020300f6fdfff401fbfe02f8f3fb0303f0fefc00fafa05f1fdfe01fd02f8f501070002f9f7f6fe0000f80504ffff0709fe03fc01fcfffc0603fff3f30402fd02f9fbfbfe0301fb01f5f8fbfff4080101fafbfefbf60001020304fbf505fafc00fdfefaed04f0fdf501fff603fffc03f60006fe00f4eff9fd0cf1faf4edf1fc09f9f904e207f9fa02fc00fceadef10407eaf4070706fb07e5f808fff605fafbf90ef1f2f7f303fd0101fefaeff7f1f60ffcfbf00af9fffe10fff2f2f20f060cfe01f7faf9fb01fcfbf3f3fafef3f4fbf202fff3fefefcfafd0508fff703fb0606feedfd,
      4096'ha2c2d9d0fca4e8fcf513cff2e8fefb1e04eae0e7f7f6ccf2b0ffc9c8bffcc4fadcf8eacd00fc02f1b2c7cfd700c3dc0808130001d1faf2fdf0febcf505e6ccf4ffa1f80802ffecc0dce6e6d6f5f7c6fbd608efdb0e02e8f8f6db08f604f0c105f6f900e6efd1f6cdf8d5f1e4de2106e601e4f3fafafcfcfdd1ead209fbec90f4dc111100fef4fa02f511fbf9050204f604f5ebfefe00e400eb05eeecec01f800ef08ffe3fe00f9f3dfe2ebf4eeddf1fbfd03f806e9f60ffbf007f5000206eafbf2edec03fe05ff08f40000ed03f9eff0e4f702fbfefff1fffef308f2fa03f00201fb02e8fbe8f905fb03fef1f20a05e1f7f0f704fa0b08fdf9efe300fd05e800eee8e803020806fb0df5dfeb07fa05fae4f8f3fdfde10606f316eb01ebfce60101eb07fc00eff9f8f1f7f20e08fafefafe0d0e030a00fb090402fcfdfae6f304f211f001ff0908f1f406f9fe05f9d602f20003edf9f4f713edff08e2f2ebfe0e050606e7fff801defa050eea0609ff0eef10e801fc02010c15f5fff9faf7f102fb0af3f4fc02fbf703fc05fe04fef9f404f0fdf9f906f9fff8fef20401faf5fbf6ff01f905f9f7f6f3fdfffc01ecf5fb0505fb06fb04fafff5fdfbfcf6fef6f6f4fa02030401f8fff40901f5fdfc0403fafcfcfefff9fbfbfd01faf6fffc01fe0bfefd00fe00fefbfb02fd03020803f202eef205fc01fc01fe01f101fcfbf3f7,
      4096'h82d2dbc6ed80f2fdfff8c504e4f60003fee9b9d5f0bed703a9f3e3c7c50fd5ffb7f80ed5f8e7f5e9eabcd1daffe0e6f6fc04eefcd1ecf3f0d5f3acf70cd9d4faf686e9f5f3f8009ec9e503cf00fcb2f1dde8edaef905c6e5cfc7fbdef90c9c0015e6fbe7fcd6ebca00cb06cbdf0ee1d0f3d7fbf7fa0d0602edf5f716faf080dffb0200fa0102000004fefdfb03ff01fdfffcfe01fafc01020200f9000000ffff01fc03fb00fc00fbfbfcfbf8fd03fe00fc02fb00fe02f70101fd00ff000200fcfe05fafefffefefafa010001f8fc02fe00fc01fbfcfbf005fc04fff9fdfbfafefd00ff0101ff0001fe02fff6000000000002f8fd0000fefc000203fd00000303b8ded4c6e5bbf3ef050ce60ce4e60408f9eee8def7caf5fcb90514e2d7fdf706c9f50906f4f6f1fa05cbd8d704fef4f7fefee9f7e5f8cef1fbffd00804c2def2f8d5e9fdf413f8a3c803fbd6fbf9b1eee9f3f4d5edfd02efe3c5f8e5dd04afeffcf2edebfafdffc7e8df0de9f3f3f1e7fcfbee07f70bfffa03fad806fcefc4efe3f90917fcf7fcfcfaf2fc04f402fd06fefa01080ffaf0f9e7f9ecf3ff040b040c0cf0e9fdf8090fe5f6f6fffde5fd010bf50602f7fcfb0ff70decf7fdf0e5f7fef5f10501fc1bf80804f2050805fef3f8f10802fcfa021b0603000a0d06e4fb0cfa0603fbf7f9020406f9f60c030b0b01f70001040701fb04f4e41702faea00,
      4096'he9e3e7d802f80906fe03e4fe01f9f90401fcedf4f3daff04ea00f8ede5fedf03f8ef09ecf4fefcf5fef6f3f9050af7f9fdfdf103eaffeffdfffee3f900d6fb0cf1fcd7fffd0002dce5fdf8f5f404effae9f205d3f3ece701fae702f9f6f3ee00fffefdfc06f5f9e903f2fdea02fc00faf7f7f300f902fffefa070bf6fb00eaf7f8ededf50102f10803f902f8f50a04fefbfff6fafafaebfef5fff8dfff03ecfdf4f803ef00fb01fdeef1f1fe0af7e6fffff0f8fff400fbf90cfef1010006f2efffe3ff03fe04070ff1f7f4fef4fce2f6fcfbfaf3fbf5f704031204f1fb0c0d09fc0104eaf9edffeef7f401e1fc0505ff01efeafff8fffbfff1fbf4020102ecf7f3e702f1f7fcf003fa07f6fde3fafcf5ebf3ebf3f6edf301fa00f5e7fb00f8feedf9f9e20301f201f8f5fb04fe0becfef607f4fbfff8edfb10ff0001f8ebfef7f905e6fd080304ff0508fe04f1fafe01e7fd02f2f5f1e00a10e600e2f4dbeaf606f8fff9000201fb00fffef7f6f601f80203f4fefcfcff050104fbf102f308faedf5200907e60803ef050409f8f7f9040dfffe080f08eaf8e610f2f200f00006050cfffaf705fe0aee01f80c01eefd05fff602fff50211130f00f003f309f20feff4f006fe0408f6f50c0307fafb04fbf1030bfc06f502fcf701fcf20b05e2ff06fc0afafa01ff07ff0afa03f20cf8f9fce6fd010502fdfc02f7e9f7fb02f509,
      4096'haedec9e0fbba030801fdd405fe03040605f4e9e6eed2dafbbdeafcdbdc07c701c0fbf5e1fa01fbfee9d5ced905d6d9fc0c02ecfdcdf7d6081003d702fdeadaece6b5e809f6020db2ecf5ece8e2fab7f2d9e1f3d1f7f9cbd4e1d1fdebfc01a7f4f1f4eff602e5f0d3fcd8ece0f1f4f9e0fb01ecf701fcf4fb0efcfb040af5a7efe016150bf8f50206f9fdffecedfafcfe09f5fc050d05effef30201f5fefcf7fb020dfef802f9fffde5e805fe04dcf90203faf701ebf721f9e915e1fe00faf002f0fbed04fc020ff6fd160905fcf7fcf9f7f6fafdffff0411fdf404000009f0fefcfc13f9fbfe0401fb01fa04f00afef5fcf11006001003f7fbf2f20400fff90efa05080d03f901f9fcfefcf801fcfffe06fefa07fe07f7fcf404fb0203fe0300010ff9f2feffff0bf1f9fc01f9f3fc020dff0405f5fe06070506f504fd08f500f8f3f3020007040506ff00040104fc00fffc080106fc020cf80205fe0206f3fc02010504fef2fd03fe0003feff08fbfbfafa0c00ff0bfdfdfd00eb0a02fdf209fb08f602f814fffc08fc10fd08fb00fce8edfa09f805060315fbf4edfbf600fcf8eef8fd04f803f6fa010bf5f70af40003fff6f8f2fd09f8fbf911f7fa020af4f806f2fefef0fb120104040bfef90bfe08fefa1901f5fef5f7f9fc0ae5f8080001fdfb08fbf10c110805f5ffdbfeff0002fdf90000070700f8f311fbfff60607,
      4096'hf7fc04040400fd0205fbf7fa02ff01fefefffe01f80608fdfb00fc060903f2fe08f904fb0600ff01f800fffbfb04f9fffd01fdfe09fbfd0108fffc00fd000efcf8fe03fd0300fffd0003f6fd02fffd020eff01fffdf8f209ef05fd02fef9fafefbfefc1801f7fbf300000aedf2f30107fd02f4ff0002fd08010516fbfffd0004d9eeec04ecc6f5fefbfeeb10faf9f51311f2f7fde6ffd2f9e3ebeced00f7e9faeb0504f0ffee0b25f7ed11f8e5f4fb080df6fafa09fcf0ed0908d6060dfeeb0504c6e603f7f0ffef0de70206fa0603effcfeffebfb14eeebddfe03f20d16d50004ebfdf300f8faebf4e508f6eb01e0eefaf10d05fb0f0105f208000800f7d6fdf003fc0cfdf2010afdf40802f80300ff070cf60904f800fbf0faf2fe11f60000ef08fb07fffffd15f2f8fc0c0af2fcfcfdf307050bfae503010b0406040af0eff7ec0a05ff00fcf50c0213fb0e0205f8ff06fbfcfdec06ff090a05f8fffbf30004010809010f1c09f8020a09020e02f5010206fdfefb0305fd0aeefc0511f7fdf2041801f7ec09f8f9f51ff9f800fa07f70bef280bf5f0f9f503f1f90fff12020c180023fd03f902e7ee010dffdcfdfd00f7fd06fff8dffff702f2060a00faffe8f9f9030203eb08fff4f614140605fafeed060efcf416f0f9e206111306fdfaf30004f0050a122201f3ff02f70010e7fbe0040cfffb14fef9f1e50003010a07,
      4096'hf5dbfbe5fcf104f9fffafafdeaff08f400faf5fe0007f7fdfd0500e5f4fbf5f9f3fdfee3fcf904f7f7dff4f901f5f601fe00ff000304f3fc0af6fdfefff9f7f7fffaf105faf804e7050508f300fcf4fafef9100104f902fe05faf8fcfc00ebfc0000030204f6f6f007f5fef206130df3fd0400fbfefeff05fb01ece8fc01dfffe705110ffef904fb04f6fdf0f1f8fcf6fd00f00dfc03fa03e402f4f7fefde9000a0dfaeffdf6f5f9e0da03000ad7fb060aecfff9efff2404f803f802fcfae1fef5fae604f7000afdeb0bf8fa040100f3f9fafb07fff8fd020b0708000006f9000901ffeff5f9f80700fff5f3f70afeedf6e40600f40108f9ffedebfffe0bef13f60901ff17060100f504e00907f1fe04eff5ef0202f0fffafa06190dfcf4f6f71df911fffefefdf9fee0f7f41dfaee0be908ebfe01f7cefb17e4f8fa09d1efefde1ae903f902f1f3f716dc04ef06ebfd0af001e3f304df0b06f70dfc0adbfceb01070102f7e811d8ec00f3e0fcf4ff0ef203e3020b01fff50c051f050af607efd0eedf0df1e3fefd04f9eefd0106f9020f13eaf5faf9dbfeff08f80104fce20ad2f30503f502f902eedaff16f7d8f9fe0f020e07d9fb06fe25fccb090613f207eac608fff2fc03bfedf1f1f0fbfcf0050deb0ceb000f1e15d6df0ff5112bcf04f40709ef18e705fdfceb08eff0f8ecfbffee0e010805110be91cf6f1fcfedb0f,
      4096'hdbd0efeef4e1fafaf1ead61ff9f2ebfa00f2f6e8f8dde7fee7fb0cf4db05ddf3edf00005fb05fffc13fefdf5f319fafbf502eaf2f6eff8f5fffce7f204eafbf001e1ed00fe00eaeaf00401e1f5f4ebf7eef6f3d704f4e3e9e9edfceff3fbf0000afcf9f000f509e0f30303ebf5f7ecf3fce2f607fdf4fa0a0e0df5fef3ff00ff88d4c1cfdd9b031a0404cd1df6ed02f8f905cfdff6d4f7fcb9f606d3d902aefdbaf30ff9ef07f216fde4d90ae1e6e3fdf70af202ecf7daf2dd07befe12d7e4f9d98eed00ec06ffa1e6f1f6cef4f898efd6f9febaf805ece2d4dc02c50415a5070cf804e600ebfcc0f3dc0dca05dff7e4ff03edffff010b03e60b05f6f805a4eee6efecf207e404fcf9fadbedebfd00ff00f6e505f3fde1f8df07f2f0ea01dcfbe2f501e5fdfbf803eaece5f60de1f6f902f00308d6f3090d0005edf7f7f9daf0e9f7f1fdf6f9fedd11faeaf401f7df01f5fffefcf6f805faf1e3f601fef3e0f7fe01fef90beeece8f5e5faefed04f9f8fbfff9f7fdfd010208f6eafcf6fce3f0fb0a0cf20b0f04fc00faeef20ffffe01f4fafafffc06f1fef2edf2dfe3f40f02f9e809ec02f6f4f2f901f2ebe6f3e9fdf60bf3f9fa0405060905f7edffe505f2ef14f800fdfe07f70a1204faf4f9f605fbfe050cf2e8f30ef2040605f4e80909fa0af70bfdf7fbff00050b01e8f700fcfa17f9fb03f604ef140702f9f6fd0307,
      4096'he808fffa02f404fef503fff8fd0305f708f9fd0400f9f104f600f7ecf5fe0afbfd0404f20200fffaf2e4f9fdffdef503fdf90002f5f707030102f2fbfb08f4fbf2ecfbfe03fe0cf900fc03f8fcfdfbfbf411f2fafdf6f7f909060300f6faf3fdfc02000002edf7fd05f101f7f60d09f2fbeffbfbfdfe00040ef7f1f00401fbf6d6f519f3f0ccf60b06f7fb04eff8fbf91601f3fd0fe5e3faebf2f5e208fe18fff80706fcf3f6fe23ff02100706f611faf00ff705f1ed06fafdfbf1f101e4eb0ef1daeffe09f2fdf1edf10e08110209faebfbe6eef800ee08d6ed00f01224d30706f0fbecff03100002ef1312e109e9e4eefa19fffef70e09e90a0511fb03ef06edf01700fffa00f209f7f8f4f6000003fef8f905f802eef9f8fff702f9fcf7020a07fdf60702fef2ecf1ee0801eff1070bee04060000f408fb02f3fb00eff6fe05f6f902fc0710e508f5fcf602faf5fbebfe031c08f7fb0705fa0411f8fde50004fe0303fc02fb000a05f804f80e02f802f01af1000309ff06fbf602fc09e8f9dbe0f2e3f4ce010af3f1f0f9ee01f907fdfdf50005ebf4fff5f2f6f80503e401f0fa0108fffff4fbffdcef0e01fbf40105eef706e5fb01fbecfee2f50cebe902f4e4f0fd07f8eee2eafcf3f9f401e8f9f806f1e108f2f410e8f104fcfbfce1fdfbf802fbffef00faf6e800eadf0bf7dff9ecfcf9010300fff20310f5faf4d6f6,
      4096'heafffe0c06f7fe000dfafe03fe00fd00060002fff6fff6faf408f8f4fdfafcfde7f8fff40103040df404050400ebf60007fa020004fd0304f70bf6070908fdfbf0f8fd00fffcfbfb0b080602fffd09f7f402fdf501fe0301fe08fff70205f700fef9010902010b0402000cf8fb00fd0800f5f3ff0300070601faf502010e0100fcf0fbf503f8f4fdf404d7fd02effafef1ff05f3fded00ffe60ce9eee3f7e3f60804f40afcff03fe0df3f7f10711ef04f405f202fcfde2f60304f7f00dea07faf716f70105ff0af3f20aee0ded04f2fff0fbfaecebfede070fe602ec02e0f0fa0efafdfcfee7fadefd1405ddf8eb12f6edf3e9ecfcf8fbfff7f6031afeea00ea89e7d2cefaabf9f8fa1eb507fdfaf40fffeed0e2f5c8fafac4e6e7ead204b0ffb7e80ccaf7f1f8e6e5b5dcd3fbc6ed01f5f0e1fdfaf1e10be9fdcd0910d3d6fbe7a1f706fff60685c9e3efd2f0f7a9f2dcf4fbaefffae0e5d7ed04e7ed14a0f203eefafb00d8f7c600eb06d0edfbf3eafc05ecf7010d0d01ff05ef03fdec8ffaf4ed030302f8f8f8fbfff6faecfcfcf70004eff211ec0400effefdf8f6f9fbfc02ef0afa0700fafbf8fde6f0fefffb03f90bf5fffcf2f6fff9f9f30507e402f1fd05effa04fa05f6f5fdf4fd0904ef01f6fd01f7f702f41002f801faf8e9ecf6f8fa0009fff2ecfefdff06fef5f608fff7f9f9f906fd01fffe0707f7010307f9,
      4096'he50f0f0bffed00f600f902fbf900f6fef9f7f9fe05fff403e701ed05fb01fe000711fbf80301fe03e801f7fd00ddfcff06f60801f3ff0806f604f1faf9fbf3f0ffecfe0402fe04f6050c05f8f807fb03f6fb090302f3fdfcff0308fe1609fafc0103100200f2fd0af708f8ff1a0103fffffbfcfff904fdf803fcef040208f907f8fcdcd2eaf91909050be6e40f0606efefe203efe8c1e9f202f8fe0412fbde10ecee19f8fd27eeecf3f1f0f1f6040a020801ff0403fe16f905f5dffafceee50a08fce30903fdfef0e612fdd2f8f8bc07fbeb04edfa03410401da05dafa0ce1060a0cfde90716edef05f50a16f8f8f7eff90f0cf5fffe0ffeeafe18eb0200ed0202f902fffe0efdff0400f4fc030003fdf7f5fa00fe00fdfdff0101f700fe03fd08fc03f7fbf9fffd0201ff07fa01f4fff9f8000209fe000102f7f6f802fbff02fb09eeff0003ff01040af408f9faf40508f9fefef6f6f6fcf9070103f5f601020201fafa010cf2f706f6fdfbf7f10108fe00f8fd01fa01fafafa00f802fe01fbeee4d9c501bd09e80509e0ebe2f407fef9f8d2e508ecee00dff0e9e1df01d1ffcefd05eaf8f1f008eef1cce31ceef4f5fff3ff0a051220ffdb06bcffeec6e715e2dbd9fbfafffbdad108f1df06fcbef8e2e502cf151e203cfcf101ee02f7ccf4f20819eafbe6f7def212fdf4e52116e1ebec04fa00fc07fcfbf4d4fe08f7b916,
      4096'hcdf7fe16fbd50800f8f3e0f2f6f7ff0407fbef0efef2edfae20dd8fefefb0100ef05f1e8f6f90918ebe2f7140fc9ed0012fefefbecf50a001ffee3f7f9fff70df2ccf806fdfb00e2f8f8f0f80e02f8f9f6ef0e00feff0818f3edfafe0f0ef2ff05f7050108f00205ffeef701050208f3fae40cfdfe040501f4efe30102faed06b6c2cccdf0b8010a0202d90bf104f41c01fce5caf1bfe207cef0f3bfc402c0fdf9fc05f5fa09f6f710f4b3f50bf6f6f1fffcda02ebf4d8f3f2f5c80010d9f10bfbcefc03fa09f7a5e908ffe9d2ffb5fcf4e8f4bbebe1dadce8daf3efe8f5c0ea0ef5eaf8ffef02c8faedfcd2deeafbdefa00d804fbfa0d09e400fdfbfdf4c2e9f9050103ffff00fdfefc02f8ff0400ff01f9f80c0503fcfe0002fcfe04fd0300fefbfcf9fdfdfbfff60302fc00f1fd0605fdfe08f8fd05040002f4fcfcfdf601fffbf60201000802fc00fcfc02fd06ff03f909fb00fb0a050606fdf70303fd0004fdf804f8f8fb08f9fd01fe08000302fafa0afbfefcfd00fff7fbff0109f8ff08f1f9fb07f8fffaf200ef00e5f6fcfef1dfebf3f3eb0dfefdf9f7fef2fdf5faf6fd05f403f8eaf803eaefed05f1fafdfe01e5ff0cf9fbfe00fefdfd0cdddafaeb04daf9fb00fedffa1501fbf3fefaf504f3ffe5f2fbe1f5e4f1fdef04d8ebf70002fa06ff0900e7f5fe00f4eefbf80f0010f3fa0301fbfd0a0e0af6fcf30501,
      4096'hcdddf702f5e9fa04fa02f809f5faf70b0505e60a03fad801e6fdf4e7fefeebfbe8f7f3ff01120108e3f2030b06dbf4fdfafdf80ee4faf908e8fbe3f801efe5fcf2e207fdfff9f3ff030700fb0efe0df2f8f5fcf1030fecebe8f1fc0c080af304fe0405fcfaecfbfd01e3f2fdef03f0f2fbeb0204fe0208f8f0fef60cfd04e40feefb020f04f7fdf8f50500f8f8fc060402f7fa09fb07ec04f2feeef8fe04ff00f70ef3fbfe080701dedafb0b01e3f8040201f706e7f801f7f20dec010402de00f6eff7fffc05f4ff00ecf9f609fbf7f8f700fbfe0b0cf7faf5fd060710fbf202f907050200f2f503f7f8f601f11006e600eef904fc0103fffaf7f1f9f900f40ef20703fd020200ff030408f8fdfe03fbeff6fa070302f5fffc04fc000c05fdfbfe05fcf802fc0402f3fa0802f4f50c0203ff0e05f9fc0b060306fd06fb04f9f302f8f0fefc05fff607020cfef6fdf804ee020ff403fe030b060505f9060deafffe0401f702fc14070df9f8fbf50a03fefcff0e04010100fffa10f5f9fc09f10a02e7f4d9f8f1fd09fffc00f4ebfdffeefcf7dbf5efbf08fcefe9e2f4eb00d4fafaf907f3fff5eff011dce2daf8fff5fff6061efbfaf802f8f2ffebfbffe50aedfa05e00002fffcf0e3fbf3fcceffe1f7f3ff01eef6e1e11aec080dd8f7f8f005ed09f3f1f401f9daff00efd7d906fcfafe09e0fefbfe0304fdfb0dedf701e60a,
      4096'he9dfe8d1fbddfafc05f7e61201faf6f702f2ecedfac6fbf6d4f4fbf3ec06e302cfffffde00ed02f3f6dee7e801e60afdfdf400fdf8ffe501edfae9fdffdaf305ffcad90200fef3bbe1f413e2f100ddf9fbeefac902fbf4fce3f8f7e4fdf4eff407faf5f3fdf806e6f5f905e20b02f3eff509f6f80404f7fffd0bdde90405eff31908f2e90715fa0af5fcde080cf7fd00d7ea05f9ddfe0cf7f30308f7f1e40506260b0b0cf1f4f0f306f0eaff00e2eefa0207e3ff16f2e2fe10faf80104f816fdfd241500f60409f20004ef12e40705fd10f3ebf9fef7f60fdff9fafee6ea15fdf8f80afbff0bf7edfb05f9cceef1f50f0017eaf8fdea00f107011ef2f60105f7f70efafd0efdfffd0204fbfdec08fffeff03020a09f7f60309ff0f110b0306fc0afefd010300ffecfef40801fd02f404fbfdfe0109fff00306fafcfcfe03f9f8fbfff204000305fb0000fa00fb0708fffaf703f40dfd05f802f3fb00fdedfcfefe0304020306faf609fff8f103fa021205fff3fbff03000702f6fc02fa01fbfff7ee08f8f403000df5000cf9f90b09020700f80307fcf8fbecfe08ef070f010102f804fb04fafb13f8e6f40cfbe21a0101fbf306f0061904f306f6fd03e6e907f600fc03f7f9f4f6e101f5fb03fd13faef05f9f7f4f20c15dce1000903fdfef6f6f90203fcebdf0efdf7020dfb02f5f8fe09faf5fbf7fe07f007150107f7fef2,
      4096'he4b8edd016fd17eee7ebec01081105ef08090bfae51309080c06f7e22308ec000bf4f8e7fef1faff1911e3e9020c1712f6e416fbe3fafa1830fe1b0dfbacdd0c27fcda0ffffe29c4e3fee3f8e413ed1217ec14c60f1b2d041ee909e61224d504fe0e12ef10defdd4ea0cf4f4490415f1f5f811e8fcff060502e80a0c02fcdfecf3020907fefffdfbff0400fef7fe050303fbfe0d0305ee00ff03fa0705fd00fefbfff7fe0204fe09eef5000304f2fa00fe000707faff1703f804020bfe05fcfd05fd00fd03f7faf7fa090b00f90204ff010501fb0402fe06fd0201f8fb14f0fffbff02fafa04070406fefd04f40f06ee00010402000106f8f8f5fff80306f40195c8c3d6ef8dfb0308f8c81befeff6f8f8e9c9e202c0d607b3f6e9c8c309b703d8fb04f8f4fbf90211e7d4d3fceefaf703f4f1ebd7f3ddf4da00aeee09d9d7fbf09bde03fef9faa1e0f8f7c3d710b2f9ddf0f4b001f2dfd7e4d1f5e3f0f9b6e314e4f6e201f6ffc9e9d0f8c8f0f6e1e2fee0fe0cf20706f2f706ecfdf9e4b3e7c8e10ae503c500f2ff0ef9f3eb0802040004dde9f5f8f702d3060beadffee806fafefbcbf8000ef6eed3ebec00e9d8fffff01bfefe08f90705feed02f7e6e4fe02dbe2f7fcfd04d2e71cf7f00a04de16010308d2f306fa00e5e6fdfa1316e6f9fef308f301f1fb0cfc09fef3fffc0dfdfee3ff05f30df806e3f801f90502d009,
      4096'hbeffd0f0fab90cfcfeffd4f9fbfbfbf7fffcedf1f7eaf8ffd8efffeaf104e201e501f9ebf80afff7f8edf200fdd2f7f713f8f608e6f5ec03f802e2fc0bec0207f4c7fafb02fff6cae3fbf3e9f307deeef3f7fdddfaf1edfbedf2fcf403f7de00f501f20407eafde203f803e8ff06fbf2fbf4f80306f8f7ffea04f7f60003d8fcd1e4f4f008ecf70be406ea040706f30d06f6f6e4e9dc0603f2fc08ecce05d1fb2afa14ea0305060d0ff0d2e301ee0dfff3fff1fd07fbdb01fff7e3fd10e6ebf8faf4f101f711fbcef104f5f0eff2f2f3f4f2fcd6f3fef9fbfbe1f601f7f2e6fa03fbf803ffe4fecbf5ecffe2f1fe00f2f904e8f2fdf6f5fbf70dfc11fcf4eaeef115ff050a09fe07ef032306040cf9f8f801f60616f5070803fe05de04f312f8fbfcebf0f3000b02faf10b0bf000f604faf30cfa04fa05031109f203fcfdebeaf500daf5f5f80ee8eefd000df00bf70613011a0006f20a15060af9f5f504fef903fcee0e0e0efc12f8f7fa1c03f100f3fdfe15fc03f7010b00fef500f6060001e5eaeff9fed505f5fb00e8fde5f5fc010302f3ea02f2fdfed70feceb05fdeb05e5faf6fdfe010af6e5ece21801e2f60410fe050e09fd020fee0ad6fe07e8e70ce8d0fcfcfafcfee5f5f2fce90509daf7f108030600020f2be8ef02fe0c09e90409fd0b0000e6fc00f6f202fee3130dfdfcf414fa050005fdfbf8d1fd0303e4fe,
      4096'hdd021001ffcafff001ffe6e8f6fffc04faf4d1fbf1fde202cdfdd1e1e8f9e6fbe801fde4fefdfb00e3d1ee0909cef0f706e5f7fddefb1704f4fccefefcf9e3f9fce1e3f70205f2f5e8faf5f40304e9fdf7f6fbecff0ff10610ee1004fd01f003e700f8ef00dbf1f106ecf2f4fc0100e5f6ebfffdf10100fdf2f6e3efffffd1f304ff06fb0209fd01fefe02fa02fbfef80f0202f9f7fa0004fc07fcff0306f403060501fdff000005fe02fc0302f8ff00fafdfffffafe09fcf9fafcfffaf40bfbfc04f6040301040601f9fc05050101fe04fc03f70500020ef80403f605ff010300010203ff01ff02fe0803fd03f9fe00fffb01fd00fb01fefcfbfcfffd070105f0f504f106fafb02f8100701f0f00616eaf604f1c4e3c3f9f9f9ec01ed0410fd3b02f53ff80a0b13200aee0906f53306f8f9e5faf7f8dff2e2f8e3ec05fdfcf220f31afcee0402fddbf613fb1508f4eede05eefb082811fee3ef1129f517f00d090a08f9f605fd0201eaf5ffd9f8f10903050a0002f51205fb03242306eae8f7ffecf7f4fef7f707fdfa04fefa00fcfcfaf0fc01efdef5fc05fc0004f903ef02f9f8fdfa03fcf90309ffecef0105fefffdfcfd00fdfa04ff01ff01fdfde3f8f6f701fcfafc02fff2fb06fcfcf102f8fbf7fef9e1fdfbfe05f5effdf0f3f1effb00fafcf9f8f3f9f3f7fff8f307fbfb05f9f6f9f4fefcfd04f8f3fafbfefdfdf8,
      4096'hc6fd0feaf7eb07ef0100eaf6f4f701f409efd204f808e5fddef9ece9e705e806fc03fad700ea0005e3dee8f101d0f7fd0d030700d90112fdee03def8fbf5e7fef7eaeefffbfa03ebfb06eaf20207ee07f2f6feeb03090825fef6fafffe0de80d11fe14f801eaf707faeef5f3f00bffdf00f5fcf90002fcf6f4f6ea0a01fce0f7c3f8e4dbfdb90517f004fbf4f80df1fd03f7d101fcf3de08dff4ede9effbe70fe4fff2e7f1f9f0e9e5cfea0008d3e3f50103f304e9f1e202f2fac6feffe9e503f2c8f102070b07cfeff6fde5fc05c4f5f60000dc04f6e4e8e4e108fefaf6c0fcfcf402fb05d6f6eb08f3f4ebea0404d7fbefef02f902f0ffeff6fef30206cbf2f9eb01f6f012fa050efee1fffbf8f2fef5001610f5d3f3fee5ed00eded08ebf800e9f6e60b050406110df1eefdfa11fa06080904e8f3f2fd0303f20807e5e60c0c03e5f9030cf9f7f50801f70306ed05ebeb12d9f1180a14ebf30dddfd11000afaf605e600f3f7ddfbf10406e7fb07e3f607fa04f70305f5f30b2f0ff9f9d7fde8fe0e08faf3fcef0101f8f1f602f7ff04fff40cfc00e8fdf105edf3fe03fff8fafb00f5f9f30003edeafb03fcd9f3f807f5f5fce3fff7fbf304eaf6f506ecfcece6f5030102f7f908fbfb1500fd00fbf8effd03030efc02eff8fd0104f7f1f4fc0603fafbf7fbfefff70008f505f9ebfbebf7fbfe02fffcedf3f3ff04fae8f4,
      4096'h83cdcec9f280f708f300baf9e605f2ebf9efc3caf6bdccfbc0fee0d9b4ffc10bc4f510c1f5faefe3f7bec4eafeefecf11407f402a2f1d003eb02a5ed16d5d906f38bde02f6fdf196cde2e0e9ee099be8e0e1fbb7fcedd3ddd8c5f5d7d5fdacff07e8fff5fde7fda1feca01d6dbe8e7bafcd6eb080609010bf90ae1f704fd8cf105fefa0307f902ff0704faf9feff00f803fcf504f101fffdfa0200fd020200030802fef90000fd00f3f8fb07fff7fd0606feff0300020e0806ff00fffdffff03f3fef402ff00020209fff700fbfffb02fbfc080606ff0e06fe03fdfcfd03fe0201ff0705f9060204000300fd00fe03f7fbfd0cfcfefffd03fd05fcf901fefdfbf1dafae4faf0fdf8fbfa00feebfcfffefe08f6faf6edf8fc04fff2dbeefae0f804f804effc01f6f409efeeea12f9f4fefef2f2f9ea0001f6f9fa05efffdf000ffc08e4f9f804ffe500fdf6fffd060ef4fbfa04d0fdf8fdee06e3fa0903f7fb00fafdfbfaf7f8fdd901f601f90104fb0bfefff4f1fc02f701ecf9f7ff00faf7fbf6060c05fafefbf7fdff0bf0f5fdfef8fcf3f91cea05f201eefaeb0700fc0afb16fffdedf8fcfe01e6ecf811fde4f2050204f909fa030503f907e8f8f9fae000f2f7ff040409fc0806fb05010202fdf7f6fa0507ff05f401f600f803fffb04fcf70401fdf8f60004fdf0fffce80905f5fdedfef5fc0d04fdf4f5eff502faf301
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'habfc2ae11929a1f31211151102ec09f1e1f00600fef507f30301f5223733f9ea1a090e05de020af6ed07fcfa0d060505ffeb0a221c4cfe0f0ff4fde5f8100d16001fe9e7f7edfdf9fa0f070b0308fd0a0720fb250601f1110b24edd8a81fff0e0a0c1a07030ef5e403fb02051fc725fde001301036d810e7fcfae4272715f8010c12e9f90808fdf6cce2160e23d1f8dc2b241e05fd150d0e2f32242617dc31d9f11cdaf201c72200b41117ee03111eff0311091f381f3b27de11fae4f91ed80224f00f4a1b3603f7f6ecf6f2ee05fef40c080106e9eb06fce6f8e905d114733841fad50b2ffb1de0d8e7f0edf228fce1d9ce08ceb6e20d121f21290721020907dd03f3deeaf2f5080107040802f720e7f407eff315edf720f10120e6e8f7f3f50d1e3ff10a03df0306fef3f71a1e14ecd3e4201a2301032105051e281329f8ff0bbcdcc3faf5fb01e3f91afc0414fbee20f61c12d6f6f8e410151025e6eef7f8e1f707f506f5f807e000b20d25e3feffd7e1f1fa0dfa1dfaff0d4744560fdc3547041bc6ebc90efdf42b2e2131041311e20b1bedea211c1114d02402fe01fdcef329e51d0ddceafd0af5e80207f70ff1270eff08e50efa0310eef5fce80cfdfe0af9181510fd08e2edefeae9fc0e08f7fd08efdc111320bad2deaef6bb101307060afe11ec12021417142b18f5fce4f7f4e80a1212f60ceee9eafff8e414e30b,
      4096'h17eef4ff0d07f102f80ce2ece5d820d5aed09c04f5050700ec1005efeff90617f40e13e5de2d1b2e07d018330c2a2d243f15e7131b2430f1ef0d1203f22a1f34f5010efb0d33f3fd2c0106ea322215e1dfdfc116cfe230f4c020dc1ffbfef800e4100df913ff1c05f41a19f4fef9e5f10cfbf216fb091f111a08e5f2ede2ee16ee0b30e7f74410e715fd15cdde19140653e4f5e4f5ff1a0c09f80cdf060ced083c120526162cf3f8f9f5071617f6da1a00ec11eefee9e2f8100211072809170e08ebe3ff16181535d93bdeda0a00001a290e272bd21b3c091c1101180408faf605e40a06faed00f60403e9f1f8ffe1e3e6f1ede10f12f2edf9f8f9f5f71d171ceecdec37201a03fc2f19ef1929041f16fb0c15e31b2c2716060808ff0d26ef050720073111ec1a25fb230a05fa080dfaf3f5133405241de3001c010d2ef828f4c5fc3d371a1e1b22cfc8ebe705fc0ee7df3a40f8f8dfcc43e7e701e1163efa0af5070cfd00f8f81c00300e1afed5ce01f2d9dfea0bf3ea0600ff1808f6f72f0f48241c1c00efef19eff21f12edd8e7e2e9dee9d4d4e63ded4cf4c6d9f3faef090604fa08f5f6edf512f41a22d0fcf9e6ea0c030bffc5f77a1948171f23fcf408f6e1e0071838f0f71fe6fc06d2ee15c4021ed8e31056255e13e8482d0312130f111cf41afefafb1c1a24f9ef04ecf8e7f10aeaeded060efd0812060dffe607f8,
      1024'hec06440041f0de0beef1ff473a01090b101c241df6f2f2070e0a1212091728f8fae6b71824c72b121c150b1827001ffa0804fcf30f0104f3152424cfddc6e6e5ef14032d08f80ff5e50911e3ea13faeef3e7b0ff27f4eaf71ffed6de07f107ff0009fcfef7282530fcebf018090819061b0af5010e09121511ecfb06fb0606fa
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hdafd04f0f6f6fdfef1f408fc01f6f6ebfff9eee7e4ddf508fdf20115edf0f403ebeef9d5f9091005f0f700fdede6f202eafe00f1e0fcf1f0f5f8f40201e0eff600ec06ecfcfd04d8e009eff7150ee0ebd0e8f7ecf7eb00eb02defbe9e3e3d1fdfdecfb0eedfdf1f1f8fbdeefeeeb03def9feec0c0601eb10f6fd010602f9e8ffb90eef0f011ccfcaf3e4f6e91bf2ffc5d039dad5ff2ef9f928eeef4716daf7feebe70ba5feeff5f7e0d8f9c3e1fbc20703f2dcaed0fe05fef011e7eff61b01f0d807be05f20be42322fbe01fec262def0cd9edf400f8cded062eef9bc2e0d8e9f9e7f815dcfd0e1ae30be8b5d90ef1f2ed00e1ee00bbe206e7ccc2fdf9010e0acd0501e5ede8f8f002eafff9d6f005f1e8e1ecf40ce7fafdeb03fec2ec070b0ae2fef908fde2fdfceadef102fcd703f9f4f9edf9fef80ef4faf20500eceffde7fcc7ebe0fe06f8d9d3f6fcf201f5e9f2efe6f8e9f7fae4f4f8f7ffedf5f5caf30203f6fbf700f7fbf1ede8dfe0f3eecdfef5fefff405ddfdebf2e703f6f6e4f71eecfa25f824f8e0ff14f90bebec00f70ce4f803faea030437f7efdecf0918f30aeb0ce5fb02010b0bfd32fcffe90a0511fa0209d91803f5eb1800f7f41ae5e70ce1eefd19ff01f21bed0e1209ec0a10e51713fb00f6cfcc0a07fa041309f71602f1e9e8fffb24ea0028d200eb10fa0d05e405110718e6f9ed080a14fbf1f9fa,
      4096'h03fffd0601f70a0bf40506fbf1fefcf906f903f4020608fef812ffe0ed01f7ff07f8fcea010001f506030909ffea02fefb02110df703fb0117ff01fa07f6fbfe0af0feff07ff05e3f603f30405f1effcfc0204fffaeaf301ece904f7030fff0200fb0cfefe00faf8fff7ef1215fefcf302fa0905fdf2fdfff709fc09fdeff0f5d4f604d6fffcec04f1f3f8e222fa00ebf309e3e1e8fdf903140411fd03f2f2f3d8ee0cb9f2f4f809e602f20ff3feec010405e2f2e4f4def7f3ee00e5f0f2fde008dce90801f0fb030ff4010fea0414f7fcf30c0601fff8fdf3060ae8e4e9d4fa07eefc17e0faf30afcee35f7f7d0ef0305f5c5f403f0fe07f305ddf4f711070b10052000040f110f061bf104060b061d37e10e1e17dbfb07ee1c0ee7e8062e0d0d08de30f908250725010c0115fa300b0cfa2e3cff0408030b000dffffbd12dc13f82dfcfbf519fbf901f2f9f904f71edc1e1af2090716f8f3d9f2291740ff0e00f7e5ff0dfff80728f7ea2609e40817f6f81a21f92f02f62525341c0c23f0fcefff010efaea03f4020710f9e3fbf9f804f6fc09f9ef00fde5fff203f3fd00eefb08fbf4fdf801f7eee1f80404eae305f102f0020e00fbfe09f8eff4f7e308f8efebfbf0fdf4f9e9ebf200f4e9f308f9f90006f6f8faea0300fafdf5f4f1edf6faf7fef107fe04f4f6e0fa03edf6fafa00fc10fbfe03ea0108f9f9f70106ec03,
      4096'hfe110108010ff7eafe121802a7f3050a05def21423e2f60918ef01eaf7f902f701de05d10a0d02f119fc1b06cae7f6fdfc05feffdc08eefaeb0fe4fefd0cfcc519f615fa12f90603fbf90c16f5e40bf7e1060a15f601dee513f1fed814f80e01fcfaf1f1f5fff1f4fa0103e1080eeaf9ffedefe8faeef6e9f4f51beb02efec02edf9f5dffa9106fbf6f4c4e6ea07eeedeffdeaf1bb02f707c3dff6c1e2ff0004dcf0f1cdfbeff4fee5e2ede2e3d7dd050df7f709d9fff7fcfdfffb050007c0e7f404f1e8fbedfac9adf4f5eeff0296ddea0503fd02efd8f7faee02d0ebcc11e9f5fa06fcfb09daf2ffb9e8ddf9f0f8ad04e0cbfb05e1d90507fffafbf8e6a30407f9f7fd04eefefdf4fee8fcfdf4feeeebff00fb04f6fff9d30e16d90bfe070a1001fee9fe0103fef7f405fb03e6150317fdfffcf5fdfa05f30006fef911dd0c060cf5fffef9f4f0f0ef01060af5e5fefb0405e8ffebf2f1f7f605fe06f8f900fbfcfcfb0efb08fe03e0e2f800e900d9fef2eb05f800f506000408fe05f0e5032cedef0517b005f9fde4e3062b0201fd1a110504ca3505f9c9151fce28ec0131012e01f5fe170bf300f41be233c71efe15f5f006f402f211dbfcf9fa0723bd09e434dc2e13fc1e23c50628e31bebaa5d39f10004ff11090d183deef93827303505fe04f435f6530814b9fff4050bfdd0fae624fcebfb01081c090400000ab507,
      4096'hdc18fceff4fafbfef80210fbf7fcff13f60ef401e9ecfbfd0df6faee1801ebe8ed01030308faf9f1fae2f701e5f5e604f7fdff0001feeff807fcf9fcf5ed29f6fcf6f2f7f9e5fdf6f9fff3f4ee03ff050af40001fcfef6fc040bff03f001d90900f801fbfcff00d9080ef4f005dcfd10fe05e504f10305fe04efe904fdf8f6f30bc9f8cbf7eff6f9f5f31503f7f9f60425f3251f09fd09f7d81007f4ea032afefe0cfc2303ef11ecfdf9fff115d31ffcf70b0e1e19052d05200e15f9f1f5f3220a0f190f04f7f405fc02ef001612e4f8150a03f8010b2e1dfae9083c0a1bfe0904e8fcf0fb04e1f809de221dfceefc0ffe0125121223fd04290f030c000d000816f719f20be3061511f60a16e813080f02f3fafaebeaf201d8db14ee11f005040203e906ec140605f3ebd1e22a131809e108f5011d05f404c60115040de80810f206fe10f7040bede70603f602f6f60101ff01f6fd220610eee8f219f2fa1e11fe1beef20afd13fdfae6e315d5f30a07fc12050cff0d420618f404fafef80406f2ebf6ecef8801f70502b8129cf50befe5fadfe9b6e51b07a8e9e99ae0fb09f9eeebf9ce0d080bf0e3c4e102f6ebd0f1f207eaefdefcebfbe500090016d8d5f1eae1fbe8ff0de3a7a705e7e9e8dba604cefd01fd1218bcfcf8ddfaeefb01fb0ff504eeec2403e1021ab7a1d5e1f2068010ecbb04e5eed0faffeb0a0ff9d39411,
      4096'heffd04100ff208061808c90acefd00ec01051d150cf50807d61211e1100d0ce62a08ffea0203fc000cfc11e806e7150214fd10000d02060511040b06fff1c40517080e0a16fb01d1bdeb29e602f9d718050f07f20c16f81404f605f22e011cfd01f40c1107fb21150dd1f1223413f3eafbee0bf0f606ee070304160c0105d518ecfbf8f1fefdeffc090a0ffe1a05ffebdb07f308d3fee7fef9f3f739020b0102d5f70c1501f4ffeffa04e71af9ffdd00f602f5eb0b01f6fadc0efe0402071e00f1ecf107f10df90df911fefef5fa02ff17f7f50b0213cff3fa17fcf2efdcf7f7ff11e712e300de0ef7f81fdfeae413f1030dd100faf716020bf8eadcfefb0804de0f0202010ff8f500f2d6f51df006e0f704e4f4ed14f8000700ecf60206e2fbdcec08d108eff8fae3fde704ddfdcf020efbf4eaf5fee9f202f00afffcf504e2fbfddcf203f104000efcf300d603fff60cf8070effe2d1ef0b17fad8c4fdd6f4fdf80703ee00f8f6ef0efef0f0e100060200effefcd7e10aebf2f70400f3070b04fae90a04e2070cf5f8ee0fe20405f106fb0500f3f10205e6f420f50c0002040ef9feec09f3070106dbf8fcf3e803fdf9070a12eafd0504fcfc01f4fe0dece2fa0ff3ed06f1f601e0faf2f813f3e8430bf8fbef03f0ef0cd9eefbf207100d010af5fb0507fe1f04100403fc100ff8df06f50e02fbf4e7ff080602fe011af701,
      4096'hff0b030d06f2fdff0700000908ff00fcf7f502000d0bfc03f40e0ef1e80b01ff010101fb07f400000ef8f0eff9e8f406fe0a0ef9fa04fe0203f4fdf4fcfaeb060afff400fff90efcf6160ef1e906e608eefb040d0df7f2eeff0505f20cf1170103f80fff01030ff6faf8fefc0502fef002f31103f500de0107f700fcfef6ed01e4fb040df613f0d506f4b6e918ebfcdbe40cecc4071c00fe0cffe91001f4edfbf9f308ba0deef6e9dff4fdf0f1efd60406fdf2ddf5f700f0fc15ec00f723fdf1f7ffdf020ee6010114f3f91cf3fd09edfcfe01ef06e1cee90b12fee1e900d213fd03080fe5fb0a1aee0600ebf1f901edfe030300fceaf10defece8f9fc010203bce9f3d4feddfdf9fefbe4f1e4f601fdfbf0d3eecbd0faf8edebebd7ecf904efd1f304e606eb04fcf3e1f1fd0004d4fff5fc02e9ee01faf908fef5fe08d509eff0e0f7f9f9faf9c7dc00ec0ff6f9ddf1e3fcf9f0f908f005e8e4f5ecdcf1e9000205ffe2e4faf5f2ffebbec9daecfce005e8da01f6ea00fa03e9ecf3fcfcda01ffe7f3e3f49502f90000c111ea05ffe8ebf4e7faa70002fca7f4f0a9e4f706edf60b01c2f9fafaffe9d5f8e9e9cbfbfc10fa01ffde05f1ff0501f8f3f7e8bef4f30bedfe04fff3cbb5e6f3f3f6e89bf6df02fff102f8ed03fee4fde4eddd1ae902edfa000606d9eff9badbef0afefaaffcdddafbf4e0dafaf3f6f908fecd94ff,
      4096'habf0f6d1f3cfff04f1eeedf2cc0302d5f7f0cbe8c2d5f0fddde6f3c4c704fd0bd5f0fcd80bec01fde6e8ea06f6ddebf6f7f8faf5e6fff504fef9fc02f7afe8ed04c8f4ed00fefdafdc06f3eae902cce3d0f8fafaf2f4ddfff3caf7d6dcecd808ffef00d9f904fd01eed2c8e8d1f3f3b9f906dafd00fff707fdfbebf5f7f1bff610d8e5d2018005f9fbe09efb06feffcddefed2ecb62400f68607f7bbdbebef10e4fbddda0a06eff1e8eaead9dcbef2fb0604fff4c4ecf3f71aeef7e2e3e9ab00d728eafaf2e8f3bbb9e3e1fceeea8a19c8d800f4eef6e5faf6e2f7bbfed8fde6f6f510f60e09eaeef0c4d1f50ff2ec88eef0caefeedcc6f6e9f40612eecacbedecfa0e07fa08f7fb0beaebfd26f309dbdc0c04e7e41b18fc10fff4f10ee4e5f9f2e7fff708f5f8f8effcf6f9eefbdff902f800fdfbfafff7e7fefe12022209cbffe3eef308f2f9f8f404f909f10ff80802fdfc00f400cf01fd19ee00eefcf5dffa010324eefffb1bfb2e07ece618f3f704ebf5e9e70e0cffe3effd02f6f2f7fc1208f2eeeb0aea06e90e3b030903fb1104bfe6f7fbd5e90013e8090be7e8e9f9df0100e7fafb03120d13102cd5ef0c03f108f1ef1506eefaf003ef01fbf3f7eb0efdfbd9ff0bee0a011df1fdee001bebd7e1eaf2ead2fce80ef6f0b9f3e6d6fefbfcf6fae405f7dee0032104f6dbfb0b0418e8ef0c03ef06fbeae8f3fcfc0b04,
      4096'h0e0fea12fcfb08edfdfaf1f834ecf7f415f9fefe0d0dfcf901f7f5e7f2f3ef0605fb10fa04fdf8fdec091522d7dae901fffffafcf1fbe6fbfcffe4eff82a0f04f807e9def6eefa0708f6fbf1f402f2ec17f7fa16faece4f8032efada06e9f4fa03000b08fdfce90004111ced0bdcf6fefef9f6f6fae6f00ee7f000efffe309fc09faf221f0120afdf518f729eb08000cf2de27ef29c6fd1237eae8a8d00109f73cd00dea15070ee909e61e0e03fb00e30a141c21010a00f2da19e7e2fce6dcdeffeb0e0a0f02ee06f3022c10e1cd0d15e40f1407fdd2f80208e302e9051f0e28f300effdd4fa35e92726e81ef4340300f3de4316f202f105073914f609ece6220805000107f801f906fc0afeec03fe131900f6f40105f001fa140908f2ff0a02ebf6fdf20408fe0608f615050401fafcff00ff020104fafe0e05f9f60011f1fbfdf4f3f10404fd0ffffd0505010df7fffdff0506feecf905010505f201ecfe1807020b05fcfd120001f1110b240cfaf500fe0d08fbe200fbfa17f3fb020aff00fcf20708ffb10dfdf0eee0f3f40d08f91b10f110d7050300bd05fbb01001050e04f2f0e3022006fae0eef7f6e4d3f7fd19fe0dfcf204ed0426f70d10f90fc41ff206fbeef8f302d3d2f9f0060be0c2fbf3f4010203e9ebe90ed1eefe0ae1f7f400ff0b0104fcee00feb7e11003f806a70623ea08ebe3eb0208092401fdcdf4f8,
      4096'hf805f909feeffbfef6f7f704edf8feebfdf6f004fffb04ffe7e6f0cff4fb0ef008f2fde102020306ebe6fafcffe8eeff0004f7fbf0feef00f801f0f701fdddfaf4f7f4eb0205f7efecf7f403f7eaf0f0fdf901fdf7faf2f3f9eaff0bf9ebeaf7fef3f3f20605f60afbeee9ffe7fafec600edf7f7fff0ed0200fffb07fbebde0502f1fd0c01f40605ff0c0403f501fdfb19f10b0aff0b03fee60418f10dfb07030d11000bfef800fefffaf9080adf040301080203fd0618fe0e140dfdfd02e8090613fc1a000a1dfeee01170611ffe4080cfefefc040e071105feff070bff0b0303fc0dff03030417fafe010e2a00f7f8fff70709fc02f9fd0102fe0cfb0ef206dfe9f2e4fdb8060bfd1bceefdcfef6f3dae1cbd4adcafcf4bfccfdafdbfae8ebede2fee2010212f0d5b2cbebe4f5c3ff0cf9f9e708f8ee02e5f2dfe003cdc7da03dde4d4f1e9e0b6a8f5d5dff9edbbecccf8070ce7fbddeddfdefacfc615cde2fd07e1d5f807c3d9f7a7bcdeccfc09a5ee0bb201f2f40ef8fb03ece500e9cdf8fcfd0601f9fefa0e0afe02001af8ffeaf00dee0ee207fff9f3f6ebf7020af8fae10307f901fb030cfa08e9010108f001fc00faeff6f81502ff070a0405030716f500f1fff90cf406fa0518fc010afffc0a03f50c030df700f11704fcf1ecfde9f0090722f101eefefaf901f8e8f50ce80411f6ea05e61407faecfffafff0040b,
      4096'hc5f8e7e3ebabfa14f7fccc02f012fcf2dacec2d5c5d0e3fcc1e7dca9edf5e101cbd0e7e6f80207e9e5caaddadceaa30cebf5eaf4f5fb01f0f0f6fd0303c3dcd3e0c1eedae00cedb6baf9f8eaf8fcc5dec3f9f23bf106cad1f3e1fccde0e7d1f3f623f6e3e701e2e80ba8edb9dcfb0ea50418b8e614d806fd1801eee5f0ebbe0a12f8f7fff9dffaeff7fac9ed11f7faf2f40ffdfade040cfaeceffaf904ffe50d08fa02f6f3effcf2ff02f9f0f8d114f8fff800f915f2fe02fefefef9e73bdff3f713ebf8fdecfb04e0fcfdfdf701c9e20cec03f8f60a03fd0a04f9e801d61ffcfbf7fdf90406e315080307e216fbf4f8f9ddecf7f8f9fa01f8f6f8f9f9dae6fc050908eeeff2ed13fdf00b0303f407f3e5010f02edcf0308e3eb11f0fa16edfbfd04ef58f60309fb01f1e3140f00e90aebf0fa1d2901f4f6c80c36ea09e32903f30902eefff4edf808f9e8eacfdf18f2edfffff9f9220910d4f80123dc2c0fedf11be4ec0704eafa07f2f411dde00d18fe1506fbf50e290306f0062002fe11fe0ddd02fb08f3090901fcfef6ea01fe110ef40efe030800f9e3100dff010315050100fefbfffafef51507e6eb13f71c000409f8130c050dfe18050bfd04e4f41d110e1c12020101f909080a032503e8fa08050cfbfd04141ff4f8fe2e000315050000fff9fbfc0225faf4061b1efffaf6fd070bfefe16edfd0712100ffbfff408,
      4096'h053cf6ef16f3f40409ff08030804fef1e000f605d5cf0e0201f7f9fa06f6ecfeff08093604010cf4dce8e62e0914e308f606fa261efd02fbff0016ee06eb5911df04e3f5ed000808000de408edfb1ffb17f7ebf30d0d2f03edff0a2ae10dd5e602fdf6eefeffd9f0fc09ec03e1e20e160410f2eefa091d0b03f6ddf802eb0215f1f207fffc0bf7ee10f2fbf61af60afd2112ea0b0528f20013fef51e051007f1ece6ffbe0704040402092809e7faf2060ff7f0f9e1fe0d01f801ecfefd0a03f30a13f9040efff3fe13060efafa06f0e4fefc02fa0bcff9f91517f9e611e0f6ecf904091401fef00ef00607eb01e0f7e5f903e7ec09e5dcfff3fde6f701fcf000110d1a0df6ef0f050bee0506e508fcf71005e4111304ff10f01d07e9080f0a08070e02f6fb07f91a06fd0d03def5150403fe0df0f5fbf104191b0511fe00fdf9f7f5ff0c0e0707f7cf0a0a16e214f300f605020200f7f1f80d130ced16fb00fffaf1240afffb041b0ff4edf6141ef9e9fdf816f9fbf7e10002f907ffff01e2000e1a1c1e0708ff18f903fb08edfe02100fe0110228100406ff1c14ef030c0bff2506f5f00bf90f0d061c330115ec11f600041b02ea0617f62e18fb07f3e6dc14070ff61400080405fb270a0d041af017f3fe080c07df01320ed30d203011f61906e716e306032ef50800fa2a2926f61001f34a160704eaf71011f2140df90ff7,
      4096'hf8f40803fff500010003fb08f7fdfef700fe0afef70307fdf30107fcfcfbfb0307fd02fb0302ff04fefe00fe0dee100312020403f904fbff0409fe0002fff1ff01f70100040105f6f9fbff010bfdef1502fe04fc03fcf608f0fdfdff08fc0109fc020401030209fe00f501f70106f8f700fbfcfbf90bf3fffe0201fafefdff080a0800e7faf800030b04fdee16fd04e2ebfbeb09e503fa01f1eaf3e20304f503ef0e00080300000000f0e4f6fa00f409f1faeef703faf9ff0002ff0703012e05f001ee0cfc00f901f50d00fc12fefcee2604f310fe090e09ff2401f6f1db0fe5f40a1116f100e7f8f8080a05fced07f1fc21f7e400e81a07f100eedd04ea1908e212fa190b01fdfb09fde4f0fef700ecf7fb02f811000bf4f714fee7fa0c09ef0bf5fde503f8f60a12f711f5060415061102f3f9030106ff21fcebf9ff1ed1fa16f7f0f31af9f6ffff01180aff0eee0eff0c03faf8f40af11912ffea1ffdf10303f51a0e05fd01f6f6fc0dfe2c04f9f406fb19070afddcf4f20007f0ffececfff2fa0deefce40d1af7ff05f9ed0b070f1ffd0dfcff09f4f4da101efcf2f900f50b1ff502090a0ffd1b10fb0005fd1103fa06ff12140400011df912efffecf90e0e132a07fef218f4ea0a03fa0a0fe10507fc121000101e0cfce5fef80d08270b040e1e1b0105001008f219091309f8f303ff1b15090df30208201819fe26eb03,
      4096'h010218f2f1021209fb1ef411e50e03102017fbef08fc0c0cf0ff1007ede9160025ebfde7ff0b0a0e05061ef205062afbf603f009f809fd06fd0aff0cfaffd808faf80715030ee5dde70103fd0bf6e016f413ffe5fbedf41c19e4fe071605070501fbf3edfe030d1210fbf130191609faf7f333f102090200fc1316f60403e90801fcfb0700cb0f05f0e4bc0bea1902f703fbf4f5d4130f0aeff114d6dffbfae711ff01de09010101fdebecebe2f3090004f1fbf1f0f6f106ea080307f9f5e3ec0709f6f6ecfaf1efbcdbe1e7eaf6c51be9e2f9dee902ebf6fdf9ebf003ff14f6f80006100b06e3eb02f9d8fbf900f1c7fde9e5fdf8fae603120f100802cfe2fc1bf5f9d4ffb8f309f9e9badea6f0feceedfad7eaafe810f8b5e2fda0d8f1e1fac2e701ccede0f6f2debbd7f4e2d1e10eeb030cf8d8f9fbfaf4fbf8f7fbd2c3d809c2e0ebf1f2e892e3eeefde0814a5eaadf20c07f3f4ccdaf49fe7f5d5fddb0d0afffae6e201faf00daaafc1f9dbfb8a0601b101fdd5f2071821d4eef6e287f71410eeef13a321e7f4eee202f31000e8f6eadaeeb9d3f803c4061ab1adfd01f0000ff4f408060c0310b7d5dc14de160c020207f31e00e50b03fb101110e7c5fc000713f6f70406b29b01f1e327efb30ebdf0fc0e0d10ebf6eb01faf8f7060a030b04f3eb0709e9f911a7d6f2e9f10092f702de02e3e2e2052f0e120305dfbffc,
      4096'hcbe401ad0ed30001fe16da05e702fdcfda19c3dd91bce602deeaf8f6d303edf6a2f307f3fefb1301e1cad8efdd0bcb0ce108eff4e5e9e3f7df0706f403c905d2ebcce7e8f3e402bccefae6fce3f2d3f8d9e5fa0bfc05d5dbf8d60dc9bed1c7e4ff0af1d8e903dfeae0d5d7cbdade19990517c3010be90d090befe9ef04ded300d3e7f5cd0098fef2fdeba905c70710d2f1faebeb8aedf8fc9edbe892c4f6f6ef0ee1fb9afeeffff4e9ccecf1f4aad90300fafb01c404e3f4f20202f8f5dbbdedf6c0f1f9e6eee7a59c04f5e4f5e78abcd0f507e8f3f3ceedf9bcecb8c0dc011406f4ddf1df06dde0f7baa3f3e0effb8000a9b80effd2d5fcefe1e904f0e0ace422f81afdf9f40618f003ef0ef413f40f17ff010afdea04fbd40717e801f1fb09331106fa0c04090819121005440126f30b0109100902f009f30129090b00d03904181b0f0710f908dff611fb13fde81bf20003f7fc08050303fbf3130e173b18010209fb10fef91406ee051c0f1b020ff814150efc0a0300000e0d1606010f052df207ff0aca13060407021bfaf808f9f6feec14eefdfcfdd4e90c0cfa06fbf60feeed24fd0a0f1207eff01001ecf3f9f607f5052bf802ef091d0bfd0af3ff07ef0b1bf302150ceae6f623f604ffe0eefd0cf712e8ff1225fc14001901100ccd02092df42403fd101a0b010208f115d8fa03f7f4fd0e15fb08050a010a18daf7,
      4096'hdcf0f0cff28a04effbedbaf5e0f3f8e3cff7dae6b0080304970afe9efcfbe90ee3ece2cbfd0debf2e9c5dddee2bbf0f7fc1002f5d2fefef4f5ffecf5f4e8b5eee8ebe2faf8eeffaca1e0e0eee6e798edcdeafae1e9ebd2e5e7cafadaf7cbf0edfa0ae9ee1b08e3ebe9a2c4d6faeaf88000e3c7ece6d6b9f1e2e80a0bf4ca92e10108fa0bfefaf9fd020301f9c8fc0300d6ec030812ec0701f31311d8020807fff604fe0400f7fb01fbe5ff0a06e906fd0f0802fdf7020afe03ee0c0000fefbfa0ef1f503ff04ec08e5f60d06e9faf804ee04ff0b01fdebf3f1f1fc0612f6030a01f60c0500fdfcf312f900f91107f6f306fe0c02f9fe08fe0205f0fffef5ec0217fad2eef33709fef80adce602f60af9e9feedf8d214fcef35f9f8fbebf801e1fdf4f4f90beef6edfaf3d329eeeab5fd08fafef205ef00f3e4f5eaf505fd090711cffb24fb0c0ce61523d6321b151409071cfe11f400fef0f6e40226fd15ddf706ed081411f81cc1ec43f2daeaebefecf6e3da02030911fc06f9fc12024cca01fe03060301fd01fa080efa01f205fbfe0bf005fc03faf5fde5080ee8030a14f701eff6eefe0af80507130cf409f712fbf2020307f407ed091007fc04fa04dc1707f6fdfc02fe040005f50e010a01ee0df304010b00f8081c0aeffafc11fd030805fd0bff110305fd00e90d0c110402effdf41c0bf410f503000307f807fdea02,
      4096'h100ce0fff906fc0eecf3330c1107fe14d7dd11f4d4cf0010e1d2e0f30ce111de0302ed42040c15f6e7e7f217f2eddd0104fefc141501f4f3d804fb0af80302eb0ed6fae6efebd4effdfdd006d5db02e9fffff2f8fbededdfe80af81d01f9caf0001ac8e80bf9f0d201d2f603c8fb0b13f11acceffc360fe308f8f5e701d20201ec11fffad73ae60c151600f2fee00ce6e4df05fc081cd4fb75eedd2cda0d01fd06bf06d51ad3ebddd91a42179af7e4011004e118dbfefae9e6f5e9dbfddcf8ca1cf3e60d0428f62a1efdce09db2437ee02fa00e7fddffdd71506f50fdbdac7e6eff0b019e600faf3ee2eef06dbddea11ffe7ed19fed4060fe3e8ccdd1122fbfcdb10f2dcffdd04f9fefed9e9fc09f7f0fcf3eef2c6c30501f8e0ebeae0eff8f4e3d803d9f2fe00d303d7d3f3f9f2e401fe11edeff1f6f202f7f711faf6d304e9f5dee3dbeae20ebdc601e8d6ebe3d5f9daf3010d0df0f30ef0dffcf5d103d9e8f4edf2f2e9f9eef0ffdfbee5d5e7fee704faca0aee01f70423f20203f6fde1f4f7ee0ce008ed150106f8e2010202fc0d26f6041407f916f7ed100be8fc0bf8f62b01f9e4fcfcfbf9160701f615fe10fbfc0b0414ed07ef0720010b0604eceb1c19041a0d01070bf9ea0bf9021d0bed0712fe060b0bfc071e03e1f71c1b22110b05f718f81604010b0600e22c18f5f3f903f22f0908f7e5010bf91a11050fe603,
      4096'hdfdaefe4f52be6070cef00f4fffb0102f404dcf6d70806080af80418e6fafb0de8ebfee40a110a08e9f3d0ddd80dc00df9f9eafdedfafdf7ddf7f1e400f907de09d9e100fb00f3e1fcefe2f3f10f02e4fa07fcecfcf3e4efdbf3fcf1def7ccff0903f9d6f000cade0d1afdd1efea0706f6fad804f4f0f4ea0a03e5fc01e4e5f5f50cf82b0d03f8ea04f40a11ebf500f91ef7fa042ff2fe06fd19f8b707110d0011f0fafb04f302ede9da1d2acbd8f7fc0dff19fdf9f604030e04ef100a022501f7eaf501060c00f2f407070afd0500f3c20d07f908e6f3b302f2f9dfffd5f5fd02f6f6f6fd061700f30800faf9f7ffedf9f70ef2fa0eea0afe09df0cfcf60d0ffd0cfcfcf1fff9fcef02f0ef18f8fcf2d70decfaf61a09fbfaffe8f626f0f9f3e30803f904f4eefaf8f6060de601e2fe08fbe9f5f6f305ff01faf2f807071d100506e4f901f607171101f5f8fdf802fc1400f6fff3f8ed05042209e3f0e2eaf3f706ff0ffa020bfdf4fe07f2f6ef09f9fc08e8f8f4ea1514f3fafefa0604040224fc07fe16cf12f610f6e6f21c1b02161710fbfc23fef9f7932b220123ea27fe3b04fcf8fb13f6052d2524f41b0c3308e1fa070b16000b0e32191e09fff8e77f274d291106f71feefb0e10e13719e007081302fc09ff132ff417fa081fec2ee308d927153702f84009e32d4036f5010b03161d001110f2ff01103c04fcf80afd,
      4096'he4fdfdf0ffa9f4020703deffd50303eaf6f2dcedbfe9f7fbdae904b8fbfcfae1eaf6ebed0c0607f9dfcdf0f6e3ead702f4ffdf020ce2e105e9fa10021715e7dbdbf7eaeef8f9fc9da2f6f2fef4fcc3f1e9eefd1afe06e7e6f9fcfddde0f4ffe4fe16f3ddfb02d5f112b6d3d8fbf409b10215d7f8f3dbf90514fb16f50be4af01f9fb060602f5fb09000b01fce3f6fafd2501fd110202f2fbed170bf601fb04fe061401f902fcf805f20210001ceb1f020a04fa06f602eaf9030c0913fbf4ed0603050012fcfb13fcf6f00cfa19fce4f9fb0501f1000e030302e8fb000afeff11fcfe0f0502fe011801d3fb090201f9eb02ed0217020afffb06fe0f06fd07fd0c0401f31903e3fb03fcf3e2f500fcfe0a12f4fb0ffbfaf3f4da170aef11030b0a080402fc07f004070af60df40ae31bfc11f1fdf9e1f9f606fff80706fa08d50cfa09fa0f07f00e0af1f30a122e0bcf05fbf6fe0103eefd09fb02ffe014f508100900050304040dfcecc812fa3407ed08ff04eb0b050fe7f406040605f500f70505fa0107f309fcf50005080007f9f8f7ef05fff9fd0ffe0205fefef5fdf705faf8f9f00f01fc0500fdecf416fefcfdf90f0401060efefffcf7fbe003ff1d1d080aebeefc01f7010607fb08f7e903f7ed08070306f3d9faee041402f305dce506ffedfbf9f90422ef090310f9f107f908fefef107fb020dfdfee8f6ffff0400f6,
      4096'he8180fecf308f700070602fb15ecf9e4f3fcf2f8f31c050902fe00eaff01050105f208edfefbf6f5fe09f1f7f0fbf0040b0af802e9fc03eef5f3effe05fa01e210f9f700f9fe050d04faee0a0204fbf3fa070a0200fffcedfc0603f1e501d20afffdf010fa00f605ed0128f9f406f80304f9e905f9f20af5f507fd01fd16071136e7083bfac714fb03f2f2f8ec1a0bfb2318f807e0f8fef3aadf00ba0901f105052a06ebf1ea0412f003f9f4ffed1fff0901efebfefa0503e2fc0ffe0e27ffea002b04f1eb02f5e2fdf6fe04f5f6b6f716f403fa0310eff40505fbfffff21f180605e2eafcfddc05f3f6fa061a080b1a0af8fc1800f6dcfb19f21111f2ebe60b07fa17f9000205ed091b000ee803ff0c0de908fcfef60000f807f4edfef80c0215f8ff03f80f04fff6fbfc001203f2fffe0b020702ff0001f502faf306ff0ce002ef0c0c1509fae7f3001303f2e8f80e0a0802f30cfbf6eaec14f5fa1af004fcfcffee0505ff03ff0be8f61e180cff0502fc03100a07010101f5ffec00eedffaf8eb0d10000209e3ec290619c40ff8093efb20000dd8ef0007fcf1eeda060c0a17f3f8ecfe07fe1001eb16fc000100040bf81f00e508e305060ae80700ecd8030fdb2f1e040620fd00f0f9fb0507f92d0a100f0907f200e318de01f916030a330be5fbea0f0334f60dfe0115250c00ee04e42720ee13e2fb14fc190afc09d60e,
      4096'hf1e7e8ec04e6fdf5f202fa01e20d0ade22eff7f0090200fefd0cfbffe203effcdce1f2fc00fbf910f5eae912e9ee120ee7f50ff9faf81a031aeb05fdf7beed320ecdee1aee0c19f0f9f4e4e80a1efef9fcf70b09fff85e1306f909f20712fffc04faeff81a0311d508e4fa0206fdef17f7ed1c0001ef040d1bf9fceafa16f90016ef01f4f2040419f113fc07e3fb02180bf3f2f70908f6f6f11b010403031804140e07fc030f0302f8f7edff0ada1afef4061bff1705ff0208ffef0103f0f9010ffa1b1203fc14cff9fc10061cfff70cfdff0800fb070b05f9f9fe0202f0f82401f61bf8feff1fef08e4ea1b1f02f718fbe90f13050d01fffdfff703fc11e80ce8f8ddf0f925e10408ef320208eef813e3f6df0c1f25edf757dcf62af901ece10ddbf9fd05fef5e9ec04f212d7f0daf535040a12f2fd1ce5ed04dee505ccf2c910ede3e5fe12041022fcd327e30e1ad71609effcdbd7fad90bfc0fe4dc06eaf0f8ede1f7d0020df3f21a07f7ea00fa28f12001fe02ce1e03deefccebfbfb18fc2df6eb0a0ae21e1309edd502ef07fb0703f22d0af615fbf4d4e421ece4f3da0630f2f703f2fe11eef4fae6e12bebf7fbe713fa0f35fceff9d1eb30ea0040e6e4f8051cf9f6f817c60b05ebf80aeede2612eff6021249ee10ec0405020b262725fff7f3cafe09e80c31d3f3160cec06fe0303ee26f61e130604071b15fd2fcdfe,
      4096'hedfbe700eee6fb1708ea1403fb09fcf5f1fe01f7fbf70107fef6011b30f601f818f2f23700070605f0f1df18f503e109f9fef9f01cf3f6f7e7f519d9fe190c04e4f7eff7ff12f50107e10701f4f8eff31f03f9180722f112f1f4fafbf200ecfefa1cfef3fe05d20902d8f71be1e81306fe060cf502082909f0fd0b08fff00b05e2eaf0f4f79efdfb08ebe405d50a0bf1e4e0eae7c0ebeb09c5c7d3b6e408fee8ecebfbec04100700e7cedbf6dfe2dc070302ee03e900f200edf409e509f2d7dee2e0eae7fa06dbbdbbf3fdd8dceab2f2d307f41b0511c4ed00cc00c0fbdfefee061fe4cff108d2f813b2d2dbd5e910a6f614ccfdfcecfc021ef7f708f6ebb6fffcf900fbf2d2f6ff02facffce7fafde6ecfaf301ef1eea05e601f8ecf40405081ddcfdd4fef6e9fedbe8e310e0ee0f03fffde005ce09f3f201fd00f1f907e8fbf70cdf01f7f0eddfdcf9e9fd05e5e4fde8effdeefcdefa08ebd0f4f1e5fbf9f900fef7f4f605fff4fdf6c8fefedcebd10a03ebfbf300e2f908f318f701e3dffbea16ffee0212f502ff02eef115f1f900f1ed03ec000e0a071f0d09f90ef30704fcf510f4fef8f501ec06f60beb13f1fe0801eaf0f5fdf7f0f7e500eff0eefaf70ee706f50608fe1ffe08f316e6fffdedf30208f1f308d4daf609fadfcaf6f3fa02f3ed1ee5fd0d10f8f8f5f8f7fbf40004f7e50001e5f0fa04e4e2fb00eeee0e,
      4096'h06fe0b0d04ecf10dfb090007e8f805e805e2fe0e1afa0903d30c03d7e80801f50702f8fb06edf60ce90feef401de09ff0d0400fff1fef10407f9eaf300eecd21f3f5fdf8f7f407feeaf2fd04fdf4e8ee02fffdf1ffea0e1d0fe0fc0d1ce3f90001ff190303060afaf8efda1c18eaf7ebf6ff0904f9f9fdf811f2fa0803f205092317f226ebcf0cff10e9eafd0706ef09e806f20810d70600d1e6f0e80eeb13dd10e7f806fe0b1601ffe12a0601fcf5020d09e408e5fdda03e20ffcf7000a04d8f1f8ea01f903db0eebf2fc09efffdc0ff504fa0c02deede9e70507ec3814eaedf9f300fa0bfe06fc25b00401042811cbf5121ce6f713f800f0020108f7fc18f81b04051efe05f6fcfb00f90e0006020b13e310e732ecf801f81407dbf5fd3a0232faece302f1f9070ff10607f9fa0c010e032117f8fe0afe09ea140701f802040e0407f901f81e020103eaf6fef8f51403080a010ee92f12e4ea0a1e0841dc150501eaf0050305f52321ef1a3be7f7f205f85211f42eeefef6152d0bf82d03fad4f903ec02c009f6f4fae216e20909f7fbfde5f1e3e60d04deea0ad1fffbffee0aedfee2000cfcfcffe0e5fef0f10800eefcf908db060bf9f30ce8ed0ff5e0ddfaf001f2fc12e4e4d5f2e6e7efe3d801eff506f9f9e7e4feebf8f5e9f2ebeff8010af8f514fae90ffcdce8dfe3ff02defefaf5f7f7f2eef6ebfe0b14fedeebfa,
      4096'hf0faf911fffe04fd03f5dc0116f101d500f9faf90e2ff300fd0bfa02fcf9f10601f9fc11f70afb05f3ff29fefc0022fffafcf7f11101060305fdfb09ff17e8f4010ae6e1f7fe0a05faed02040afef0171bfc09fd1deff0f80112f3042b010af2fb020b22fc060c0809fbf7ff2217f814011512fbf10c0912fbfa0afc04fe10face09040ef8fef301f4f8eee82bef05cdd3020ccee44ff4060af70326fbe4eb180904ffcaf213ff07e205f8f5f0fefaf80302f3f7fd02fbec0b0106e5f4000002e02604fef82403232b02e70f0a0906ee07edf805fdc71723f507ffdeb3d6fde5f5f8ec00f6061218e9ef290feef300080102f7fe15e9020ef9fbf1d4f2ff19f5e0dd01bbfdaf020202eeb6f3caf402def9eacbe387cc0304a1fdeec1d3f4f2fcf0f3f1c11cf5f209d0a1dbe5ead5c702fafaecf6daf6f2f1de19ffdc07e8c8d8d2c0f2dd03f7ea8687f2e0e9e0f1c5e5b5eb03fef1f6d2f5efc0f7c2cceb09dbfb0df0d4f9fddbfc14a3b9dcdcf3058009efac0b03e1ec0d1fdedbfa07d78307df1205f7f220f40802ee30e416f0fbe7edece9ecd107f7011804f31609090302eaff01e1f3e8f911f3f1ea18c0e9dd030209f3f3d8f6e90af80301f9fe0311f50703de0308f9fa063705d81adb0618d307e1061112e6feec102d04d1eec2c8ed03fcf31c00fd0000f5162ff6dffbe70808f7dff20de81403de0acbe9f9f21909,
      4096'h17fd0a1f000affe3050d1bfcfd11fd2b1fe6eb0b23d8f1f8f116f60fe7f708fb0af7f72cfff1110c28042405f1eb35f7170afff13304e60e12f302f30007cbd718e80efefdfeea08fcfe0f0feefaf305ac110e08fbd5fae41be8f4ef1fd1eb30ffff1dfb070504ec0ac71c231d10f800fa0c00ffffe6f3ee07080cf604f2fa07ecd0fff11707041404f416241a0012df20c4f7ffcf2711f63ff91e01fffdfc05f10d094a00e7231f12b6b80ef9f2dc19f20ef722f81001fe0fea00e91dd009e52de9f3e0f9f210e010020e0a1811277aed09f61d051d291618faf3eade47d721030708c8e9057fd7f536d5fafc2f03030817e4f80a340af60afbe525fa7ff916cdfdfce0fd12f2f60af6ebf31af9f6e5f1fbe4f4ecf5f7060afbe6fc0002fbfde5eb01cefa0700fde7fcf00ae6ecf1fe04fdf5fed2fd00effce4eeedff0aeee404e1f1fdfc04fd0b0cf9e010f20cfeecfd0103fd01e8f9ff0009fbe3eefcb9ec0320e701fcfce3fdf10818f901fa02f6f903f10300f8ebfde0f1ea00fb03000616f9fff1f700f60cfa1410f50000feff18de08050bd810fe012a0ecbe6001204eb14f41ff9fa0e04050a080c11fd23021ef40a1613ff04000c121e0f00f9faf312091915ffeefcf312ff130a0cfbfdfddf1107f4f3ea19f800f5fc181a13fc09fefb0af3020414051003faff0717060d01041011fe19ffecf8121e060113ee07,
      4096'h2be9eef9ecaafa08e31ecbf9fbeafbfded1e0606cc1cf4ffa40912deefe515fa0c09ea02fc06fdfc05e7f9e508da1ef2f9f9dc02290505fb09f805fcf90ac91ff2442b0401000c07d3e6f9f309f1b51c0eeafaed04e5fc30ea0cffed04ec15e50808de2606fcdefd07e0f60017ecf907fd2ef7eceae4e8f8f6fb0401f8d13de01310fc18f705ff1608f514fdf107fe12eafd0a180ae2f2faf4e6d9e3140b14f2fd03f035fa090303f4e6e522f3efe9070dfbf8f20dfdfdffe5f303fc00f81efff5ddfbf1020af104ea020805e0fd0ef4fa04fd0ffa10ddd9fe140012eaffebf3ff20e4f4ef00ecea010910e4f5ef0d09ff02da05fffc230cfbfcfcf407ee020806e80f020a000af90f07f800fdf800fc1501150308fe0dfaee170e10feff0b030a04fdfd04f6ff080100e6f30def10fdfe0703030ffe05071b07fff9fff9f4191500040504f214020ef910051e03f40ef90203f507ff131908ff0320070609f802fb0f040004fe00f8faed1b0bfffcf2fefd1506fb23feff0203000bfc0bf00b0d05e519f10cede213fb12fd19fc03e6e10600dff40b07010df3f5f6020bf2fffbfe04fffaeffbf1d6f7ea1ee8ffe2060103ffede9fcf1fdf9fff106000d1bebf7dfe6f0edf300241309f81cefee13e305fffceefcf9d6e2fb16fdc5f1e6d8f5fa0ef717f5050d01ef09fef0e607020401fcfd0407f2fffefcf0ed0702f51e0c,
      4096'h12fdf90c06e404fc03f5f3fcfb0800e9f7fdfc04e70ff400dcf029d90000f500190ffff208fe0cf304ec05ef02e8240003040b030101f10ff80013050013def0190e04f901080af4dd0a02050ef0df00f4fbf90e08f9f1f5fcf400070a030bfdfdf9effb03fefa05fce2f507f3e80cdef4f7effff5f6e7011700050a02e8ef1020e7ff14f2e9f8f2fdf5f4fadb02f80405030b020711020ce60500e703f9fa0d031c01fd05f9f7090ae2fbea01ef16fe0203fffc12ff0f0313fe05f00214f3fe040f0907f40303fef7fa05fa08f0eff509f4fbfafe0bf7050300e9fb01f5120b06f9fc00fbfbf9fcf8f7ff0219f1f10dfeea01fa04f8f3fcfa08f90c01e0ebf90af91514f7fb070c0c13020cd6fd0105f4eaf00610e9070207080ae3000e15f70eeeff06fc120709fe03100809ff1706f905080af402f308f504f50df926e3f10bf514fe0b02f203fef407f80b02f720fc1209e90102f009120afdeb1d03061ffef40901fdfe12f41ae4f3fd132208fbfbf91a040204f8fcea0b1ff901e9dbf152f30916ef2a040d15181ae91df5ff05d3e841f01cd80c0610f7eaee22eb0bfbdef30720071b03efef050a25f5f4c7fcfd16edef12f126fbeb07f7d6fbf114d708db20e4f2e3e8ee54080516e1e527fffa1c05e1fe05edcbf11f01f2e1f2bf2105f9f902fff91edf0efe01a7f912fb0e01ecd7f7f2e40319f509d906fcf8e514,
      4096'hf6f60d00fafafe080be81e051ae906efe215f302f30300fbfafddfe52bf7fdf514060222fb120107faefe600fa08fd0810f803f329f009f7f80f0005051b1309f3e1eceff611f7fcf7f9fc0bea01030b0af9fb14061df8e3e725f7f7dfebfef0f81bf3170203e61dfcd42713ecf20d03ec0cf306fa0624010ffcece700ef0714cfff09d9ffcee6f70008deed170bf8cde8fedcf3c0c6e5fce3fff80ce2f5f5f2e1f305f7f7f909f5f1f9ee02e2f0ca07f1fff2ee0f00f8f1e7160de502b8eb03e6bef0dfeffcf9b7c501f0ede8f7e2ebe2f1f6f6f8f6d4fbe5cc0ed2d1f0dff4f703f303f7fddae1eeb9e6d4bff30bbe0312bdfa10e30bf4f0fb10f400f8ddfafe29053e0217dbe5e8e9fdf43edefaf1edf3f0071331f20c1c180915f601fd0d000604cbf807040804174c35e9f40af4310223ecea11f5081300f401070ce705f3e4d9f9fb07f6162b11060f0414f6cbe1f31e0c14d806ea1f18fdbb10ebe90dfde3f11305fcf70ff21bf4fa06edfceffce3f8ebe9e7e5fae5feecc3f5fc28fd02f4fc0f02ff0607fef5f90af2f3fbf404010b00edec0505ee03fce6f9fa00070ef307e7f90606f5f2f2ee0202f0faf80e01ffffecfe03fbf6fe020404e9f0eafdf805fafef11ff7f6f0e900fdf1f205e0fbfbff0a0ef8f403f1fd0d1403ea1703f8f1f7f5fc06ff09fcf1fee6fe01e6faf90013f9f5f7fffe090d00fffbf909,
      4096'hdcddfde418c00d00feeceff7ddf2020c270ae6db04f2e9fe180ff7effc07f40cf606eef9010df418f90705050105e400060a1912ec02f7070a050af8f6a3f905f5fe100b09fb13e0d604cef4e515ee11e601010000030902edd8e9d7eb0fd51a05eff7fa0301ffebf3f0d404070e04bdf606120918fc130ce7f7f2110506e0eeecf30b0cf7faf8040b03ee01daf8fa0107fe0b0209e903fcf30afd04ef0701fb05fcfcfb05f6fc05f50314ee0cde22fd0803fafefb04e8030111fb0aff13d1f8fdeefbfcfb05e900d9fe100615faea0bfaff02fef8f9e80722ee00fa1ef1f81204fd03ecfcfd090c0be007f90e14fbe703f10cfd0005f902fa03100701f7f0ef0509f4f5f8f3f7fd0cf611fa0608070eda0122d5e7d70ff9f5d7e7e7fb0206ddf2e9f03cf7050a11e9dcd8e2dcf8e606f9f4ecfe13fee501e5eef7e506e927eb01d514dff8fee5eaec0400f3f2f703f2da00ed0ff517e3ddda06f7efd3f9e8e8fd0befea0bfbd406fdde1bf0faf10ceafd05f1edfc0d2afd07f807edfedbfe01ef09f5df08d210fe0ce5fcff0102fa081508d9fbddea0b01e40ffc1b13f5f614d5fcf7fff209ee06f22b0f07e9f4100301fcf611f9fe070519140606f7dcf30df004f10614fafadbfa00f1030cfdde04e6f80206f7e10a0401fafde7e8f6f00c030b06e50c05f4e1f8dc0002f3f702d9ffefee10f2fbecf904ef1213fcfee8f6,
      4096'hc6f6faddf9aa0afdfbfdccf9f305efef09f5ebf2d8e6f700caededceedfaf1f0dde5ffeaf5ebf2f9e5ece0e200dfdafeff03fdf7f0f1ebf601f8e8fbeceae6f8f9def8f0f6e606cbc4f0f1e8f7f6bed9d7f6feeaf1eccefbe4e5fae6efdbf3ecf4f3ef04f4fbeaf0f9dfeedadcf202c5f8d0e6f9f2e3e504f3f9f1fbf7f1bef7f514fdf001ff0501f7f9260714e5fd0af4eff30ad2040ef9fce8fafc18e7ffedf81a081efeff0df90315dff51432ed00ea10ee241afe0700ea01f6f711ed7918fefce5030910f000f006fafdeaf816f94403fc08fc26eff3f2080f15f907f7e5f314021af902deff00f80004e0e9130a041ff9eef9fb21ef0404fae308fafc05eb2706fe16faffee06ddde08160ae9bd0408f3f805feebf523f7ce0df60ef9121bdf08be04e7fb10c828121ad2f605f5070426ece601f0e6270cecf4ea1903040909e8fd0c1d0ffbeffa2de7f10902e01df80437ffd7f904072b08d206f203e201f31f35fcf70017ec27c5cfef0100c9fffdf2fbfaaee315d207fc0c02f10ffc1514f3f009e40302f6fdf702f303fef31509fe0e07e307ffcd080df2fa030b011608f6f205fbf601060eeeed11fc19030a05071a04ff120c17f90c0afde0f22d111a0c0efe0810f3ff15fe0722fce302e90102fb00f52115f8e406201d0419eff80c080d25030f3603ef0d1c1403fbe7fe050e0bff0d03f70a1f100c01140105,
      4096'h02effffffbe50408f30eed06cff8ffeaf5f5ebfbfbfb110adf0105bbe8fefa0d02f504e2fcedf90b07dcf402fecdff0209040605e80d0afc05010afcf8ffdafb01ecf901060c11f2eefe000c06ebd8fef4fb07f302e4fbe9fdddfe130bfcf408f8f606fe0802efffead1d7f70806f8c0ffe6fb04fbefec01f9fff40ffde8e1f9f6f604fff70dfbfd030303040a02fcfc06f9f9fdfa1204f916fc0e0b0a0b0ffafeeef90a04fc020afc0c0f03060015fefd00fefd0804f2fd0b01f6040005f40100f4f3faff05ee080dfd0d0207f6010212120105fdfffff70005f9f304fc000004060f050cfeff0301020700fa1309f4fd0e08f1000f030bf10804f30305fbff04f3f0fa09b0040000e7ddf7e0fd08e7ecf5d707f7fbf3f9d3f1fbbfd2f606db18e000e80302fa05f2c9cdf7eaeef101f704f000e401f0fee010ffe6f9fbe9d7f706e3eded08eed6bf06faf4e1f0c719e6f3fc030302d7f0fc01f802060bf6eef606f3f9fb04fbff16c8c6f0f9f1fe900af5e2eef2d9e4fd0df015faeee4cc02d501f9eaf10adcf704f307ed33eb00ecd604fdd2f3fbf5f915f5f71a0eecf6eedfe104cc00e6f40ee107ce0ce2dbff080dff16de05f3eaeedff90519f503e3b9f0e9dff105fce7ff05edc82cfbf6f0ec02fcfb1100d9dfec091900c6d7e8d4e7fb04f639eb0018f7e50f0dd7e514e90f0102c60402dd0e0ff8f0f1d8f6061307,
      4096'h1beb13e4030b0b0eef0d13fff3f2053831e116fe0cea110206102ec7eff51eff071afe1a05f1f6042303ff1016032bfe0bff182b090c08081cfcf404fcc1ebf02feb350207f8120219f9fbff120af204ed0a1802fdea3a1ceb9f03151f3afdf402f106051304dee01907e81e2d05f93502eaef17f61b02e92a16170f0606f702c7f0fde1fcaffdfdfff4d3f9cf01fedeebfdec00edf4f0febdfdf3a0e602f8f207f5fac5fbeef500d4cfe8f8ebdfdefdfb03ebfedbfee9fc1a04fdf80ededaf8e9ecf20504f5fad9c2f9f2fb02eed1d9e2effced04e2e3f2f7d4fce6eed5eaf80709f4faf2fce8fff7b2cfea02ddfda6fddaf10303eadf0704f3eff0fce2c1f5bbf0f0c107a40a07f9f9b2eba5f6fee2f9dec6eac4c5faf8a1d9e993cbee10e3e0dd01b502e106f1cec7d7ec05b8d5ff00faf408c407ecff07fffafdfeb1c9e0edcadffa0b070093a5fddfdafbe997e9ba02f8f5f4fadbfaf2abf9dbdec6d0fcf9fefae2e9f7efff04c6a8c8bbf4ed80ffcfd3f500e6dcf9e6f1f5de01c480fd2af00a0d09f1fe0cf609ef07eb10fbfd00f51009fd07fe07f200fbe91afc19f3160dff09f90402fef40807fffee208040305f0fb1effdafd0314ebfbfd0ed3f5e70e140d0301ee0af1030305eff3e00613150cf1f6fef60bfcf406fa09f20afdfff80c0018fcf30406f3e51c220b08eefff80903f8f0f8ffe7040bfafbf8dcf2,
      4096'hdb0cfae200b5f919fef7f8f8f6110807f90cccc4c0c2ee06ccd9d9d3d4f209d5eadad416f7091801dde5a709e704a1f800f8fe0d40f6eaf3dbf6050000dbedd5fbc2dbe301fafdc1bafde9deeee9d8d0c6fefc23fb15cce3d8f400d7dce8dadf0306e9ebf7fec5e5109bf8d7d6ec0aaf0424b3eefd1542043106f0f6fac9c30403f101f502fb02000a0307fafd0700090d0514f6f9000900ec0c150004fb0ef5fdf5fcfc03fafd01f40c12fb07f71e0602010308fe01f6051cf7fe04fc0ee9120a021005f9fbfdf30b0809f8230eee0bfe00020801f70614020301fc0efe060a02fa0e050103030305f40ffb1efaf407030d07090108f50501190002ff02f40118f0e9060416ff00fc030d110803f7fa02ec161adef90ffdf5f5fffffffc0122ee16ef110501fc07ff00e5144fe017fa0ffefaf71d07f8010ff10e11f914eb480120fb1d12180102070c1003e3eefe21f2fc06ec0a2b1cfdf0f2feed140ff615000401e31afe19eb0804ef19fdf9faf60dedf2f4f5180afbfe020907fbff040a17f00ef2fee7f6fcf00d0c08d9fd040f1cfdfbf015f517fffc130cebfd05fefa150701eefbf702030afc11fc1be40808fc0a07ff0602100111071206f4ebdb02040307090f0911defe03ee0203f0de1d02fb02f207f7f816f7f0fd1801140f1b0af80df701fd00f403f5fd143006fc2105f32309f20b04f805fcfd140504ee02
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'hfbfa0421162e35103b3d19073013344c407f0a13062e0adf2510f3b5c0a0ed1ef820033406f616fbf81600f6fa2320f1212905c5f0b023101a02e8f601f1fefff402f0fcfbf3f91be3bfc9f1e9f8d70510231a16040f1d04fa0719ff1305da060afe045b22672cef2f26f632f630e7e03ad7c101cada06ff0811f70224e81dfc3833cf08141e1cedec11f0c8e013051b13fb300de5fff0ef1a150323ffd4fa340523050bf727db1a3d112c1b223fdce52101edf40afe0608ed071f1b20fced0d05dd092a1620f3f6dcf422dff907def0fcf5f9f00919eefbe11e03d9ffe4deffeb16f806f9e7f40a01fde1e1ea04fc04342b2725391ef903051c0e0e312032ff180d09f406bdaf98051906171c260fe70a1f0d0b0a17e90203f5e8f402060ae94f074d41ec351df70506f9040603fbf8fe02111d15d214e1e10df51f13180d01fcd8e1e0fe06e7e9f501150e0c103016102bfd2218e7231d34f8d2e5eb0aee2c08e8dc0cf73b1610070b1517fe181a1a0d050eeef412eee7f4d22dff4429d818381c2f46fd3df6e210f7da0a3f062f0cf0f506f6f5191632fcf3ffd6e2c806e31ff7d61504f60a121226e0e00f1efb28c8dbbd1120120b1f26f0ecdcfdecea0a1a052cf4fb11e7f816dde405ff16d9b9e113f5011a032611f916011d35e8e3f4f4170ef5111ffbe0e9e6f91bf7e01a0f0702ee01fffd08ff10edea05f6f92a0b,
      4096'h1df90eedf316f4e9031b580638040f09ef8da01407250f181c0c0707ecfef8f308ef30083aefdde1f009eb4b353c231d312ef12f2a3154181649ffcf06dff819d7d1e2f5da252a346005ec060af50afbf7f5261923f8f8f9d5e3ef23112921ea1f1c0f45e0fe06fb01f13e02fa1f0913400efc1c03f72ff8fb1afc08371059dcff22fcfe01f6ee1902f2020ae6f90d1822fefa2006f31e2d100c0ffd000addf0190204231823fcdc03f1e4ed01ec1fffe211edf2183a3a020700f91beff90f4306de41019edbef43113a3c060633faf7faedf8e7110bfbfc000a0ef8f20212fff00cf9e10bf7f20bdae10b41145626262fbdddff18101ef3070cf3f500020dead3d4f3182116353c3e07edf706e20a19134310e3203df825f21d24ebfcffe9dbf203020ef505020efaebf6dce1fceef4171a20060904fcdf0026032d08ec0af7000bf3f80847367037f228a9aab4fff80402ed16250434f7ff0e140b0f1400131a182c4b040a2d2c2f30023015e0faed01d23b09220aed0b05fcd6f508000b39fce3f5c2f80512eef612070e0b0a221502fae3210b0a0a1217ffee0ef9faf91d0adf1efcec1206d02e002906f721faf1f5e5e5e30b0d160f041af02529da2c10cae7fa27101805e2ef04f8fe14200835181d301c39fe030bfbf30215ec101a1b2015ea0517f60f01eff606f3000de20907f0090cf3fe0fea1229192e16ef062b,
      1024'h1333170d150efdf302faec221c2631ec114717381bf9f70ef9171af4eb290721e3f7d7cfefdd1e052ef7ea28bbeff52f0d055106e4daab03f202f9f1fe08f1f6fe15d81212082b081df9e30be2090af505ee26faf90c16fc2b16182737224a14ca11edf4ff10f1f70ce7e32dfc072529fa0de8dbdfd4d910f5d7f802030b0ae0
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'he3e50224f2e5e302e103bbdbef00ccf5dd0c06ced5030706edfc25faca18df0cdb02fcfaf6e2dfeaf9f2d5dff2ffedea0004f6f3da04f807fe00a5cbeff9e3eb13edd8a20adfda04fed600e3fcf6d7f2ddfce896e4f1deeb0209fb000cacf7f2dfe0f5d90dfefdd1ddd6d4f3e7f2e2faf7e5ecc3f8dff7ccfbeddbfdf4d2e0f80e18123e022ba417fbfee9dec2181ffccc4119e91421c9ffebef4f19e42a39f7dd1efc1307dff71819e3e5f7f506ccdc1cf602eb1cfe0ff6f80921f8662516ae04df2ab319fc0808d1ece1c4d5dae40e0d0bf20eef3cc0e9e3102025dcfb0f030413ff10fd0e3cd81604e5cc14fc0cf6f8310000eff7daf6ff0a00f0e0d0e8f4d7c1f3f512e8dbf7f9dc08e6f0f5d8fbe9e3caf8ebfcf7fbf605c2e0cce6e4f7f2fbf8f105e7e0eae3f4e5ddf8f2e6f5f90bf4f9e100f3f708f6cddff5c004ddebf7d5d2fceab4e5e80805e2f1e3dfcef8fc08d4e4fdcf06daef02eafaaddcf3ebe2eee6f8f2ecdde3cce1ffd6faecfaf907ebc6f1dffef1f801eef9e7daf0e91b04e8fc38fa1ffaef100818f026c4fe04b50403f51402041301f717f2e2f611e904f2e6fe0318cdd5f438401bef240313f40904e4faecf60bdffa14d1e4ebe9fa0be3e8eefde30e10e40c43182703f5f40549fae8ed34e7f80eecde2d14e6e9f2de09f50f14220ec4dce80d03ffd3020dd6fbe41207f70c101305eadce40d08,
      4096'h0b050bd6181962fa011c23f81f09d9fa1b9cfe0e0bf80908f808d008ffbadd0c0e0f0bebe90108fdf82ceb1d26e74632e1fcfa10fe02fefc3403fce9ddf5e9680c13f53c17f90602f4dd05223e14fbcf190327f705e35c51eff2c6fd0a0903fbf9ea17f7ff0fd63ed6e10c350cfbd3ff07d2d11e140b0108fd15ebfcdf06e4f70b070b11ebe8eefbeb06b9eddafdc4271a2004de0838e40d020a4c17fa13f5f9d3f2f50114f8ded619df0aed0519c7dc0e1ccbef0801de06e516c3fd172d1dc14b06c2da393004f93a02be1c3021ccee07ffe2e11609dbe1e60d400cfdc70dd5e2d500d1e31029d7dffcc8c01507df0fff16fbd6fef300df07e5fb08f0fdeefbbcabf2b022e1cfedd4faf800f100e3dffcafc20ae8fd170a1d0bd8c4e995d508f0032cde151ae4f5a81c1613fdc50f08d6f81803a9fce1102001cacde6a6f2dbe5f6d420f2f6fb01ebf626320503e612feff1dcbf4e9ce01f9f1e9b707d4b0ab0fe6eb08060d18e7ddf4e804c2f7f300ffbaf9a206e2ee02110ed7f50105f9e0f5ee05fcf0e614fd010b00e3fcffe4f6f7e4fef80df902fbf509d6eaeff8f20514fcfbf903f011f605f8eff804dc001dfffef7fadd020b02f8f8f3f2f1da00fae8e7ececdefcf0f0f5fa02eb02f8d1e6f9fcf8fff709f103f6f7f9ed04d5f0e2f6f6f503ff08fbe6eceeef03e809e40705f604fb01ece0f504f70ce7e4f2a0f1,
      4096'hf3e715f8062210e910062ee6f9fa060c20ede8f116c705f712fde1181df333060cf51613fc080aebecf03cfee80dedd8f6fb0408fbffe61ad8091e20d500efdfe51426ed030bf0fcfa050efe10e6eeeee0081709faeefacd120e0cfdfaed01f3d216f91807f90c1a06e0f4fbe3ed0d16ff05130e10fae50dfb00fa0411dfe70cbfc3e1ecd3d6d121ff0cbf1605fe1adffe01b1e3bcd8fb07f1fde49a03020303e70c02fdf31d1df3d016e3c4dd19cdef05e3f7fce10b000af206c7c6debfdde9e4e21fa8eadeef21ed2709eedced1d31070deabbf3f1c4c024fcf7a6eed8c6e7f524e6fd15da0eee2fe8facad4fd21ed07040acb001a01f4f3f1b60d38f30cf0d2f9d7a5ef0ff103f3f9ec3e0cff49ed1ae7bc23dcd512f91800dcb2e4bad318c50cf30008fd5015c7faf0031df70435d5db0704bcef0a1a09f11d02018005f9adfff304f2ffef2fcb273508380d1632f0e412daf5030bf5160bf4be1539b5c5272cf0eb15ed061b2cdc16eeb2ff0af9fdef0cdb00ecfc400e08e50209e9f4d6d2bbedf73005362c270821563e15431019d7c327e99e21081d03d4a6c9ed0a0703efe3f6e41635fcdd31f4292efe1248e3f707ffdb0812180827e7eddcc30668c4f8c3eeeeec0dfffa362123191b2a371208fec6060932355325ddd12210b4e619c12a3911f63a470e203a31c710eff302d00a2f0def3c070bf1f32b2f580349,
      4096'hdfd4f405d2debaef0302f2c1d5faf3f8d63eded2bca8db0909faeeccc0fd10e9ecedecf9fd0212bbeae7dbb4f20feeba281b0701eb0efbedf5f59a05f116daae04020a802df3dcc903f2ecc5d1ccc4d8faf4f08deee6aecce6111be2bfadc4eeb30df0cf03d2e1dedde0d5f3d8d212f2f10debc0efe5dad4d5f4cafce4e1f3ef0e112aa828292d1bc5fb233336da390e19c6d94b07a3f2090011f3dffcbc1bf816dbf7f4e0f42011ed1ad9283de90a2ac0dded1cf1eef7ebe906662cc5cdd757e949f07f16240738ee3009f650f35b2b07fc1020ecf82f31e80cc1bbe366f3f04812341904c4c16d1206034a0d19f2e1fb0fdb2d00f73351f524f2f11d451b3208e910f6f0ceecf5e0f7b33715f31e1b3c2a0320cefffcfff2e325de110bec10e516eceae9f7e5151ceee3e548edfa0cf1ef281a06f606050bf328f210fb3b45e4f9ec22f421280f11110dfff92d2919e8f3fd1c0cfff006030efc0fe34605ee1d172f12fcedf0e0f01d170416090114f60e1728040b10f2f1fb0cf31903210d86a5debdea10acfbe1ffb8e1f2f1c500e4adb3d9aec9fdfb0efdd080cf94cf00aff3edd0fafec9ed9efed8dee0a2d5c9cfecdf04a40403f40c0ac7c6fa80efbb9dfcda9405ede6f4f2f41ed2e0dbf6f7fc06f0e2fafde7eeeff9f7a1f89da7a3fccce7ea05e8efdbbd99e8caa107d6fd0ba0f4c2fde2eeefedf8c4ede5e8cbde,
      4096'hf3d707d011193600f10f161c30081a122cd2df35d0932b032502c6d5fae5f316db01f7d4f5263bf8cf2a122e11d02f32cd0b2b09d0f21afceff642fedab9e45bdb2dc243eff6130cc92d14152b272f203cfe3b2308ff053a3218d5c7264dd9f710d10b0f09efee33e10aff4fdf05e80803d30a441408190810101aed0c35f4efddfb011ef1f0cbec0901e8ebf9f811ecf1410ff1170f070deefb220f16351004eff1ed2311d3e8fe18fb07d6ef2aede515f8f20c050af60cf20ded2327ff09c4f8f622d6efffe7dcf4fdf9cfdde2d0fdfa09e500edf8bfb3f60ffa10ecf31015e413c6e402f2fae02903fcdefc0d0efa001906f6fe00fefcf6ee08110cf70205010f26350f14cf03fa09ddd0e104cc11fe153abe2e64f9e7fc034a0d0b2730d2db3301eb0627d6afcee00debfeccf7daf61812d0e4f3bb00e921c01c0741fce64bd4c6c42746140a450f8402f615bfcf2ae9e9f728cce1c1fae823040a9ffdfbdebef4b3e52b21d7d6f6c8ade9e60b07f8fa0dd81ff9d8c0edda08d2eec8f2dc1502f4dd031d04220dfe110207ff48200300ee39ef8c1efe3010e419f4defff005070b00fc00482012ffe809081735ed131709f107fd1cde2b0a461917cf0514cfed19defceefd15ecee2ed30bf621eeeef11932ec013808f713e9edf932e40a0a120c25ff18df2522e5231a0905ffee0b22f934fbfef92def1a04020117ef01,
      4096'hfaffcf1218f8e70929f8e33916f824e63414d02d08e712f534fb0dd21229faf3e620f30de514220bf91916fa2c28ff33f2ef0ffcf9f806fe1efd3beef1cfe614f701f678e500040103070eeb13ff0404e2f21238ea2ee915080bdbe7f04bcef51611ea0dfad807fdeeb6f7000311070cee25f32e17f2d83118f7e3f2120935fc1a20e010f1f8ca060110dfced7e6c136001319070d3ae6fde7f22b1ffa1b07f9cc0decea1c16f0b10cdce9e3101be8b91308c9e2fef1f4f3e90ae0f1201f31b557fecdbb2f18f1ce2404defbf109b0c00a05eae2f8fdcae4f0e23418f1fd11f3ceefe1ead110fcd2dcececca15fcf203fd21ddeaf1d9dbe3efe81806dcd3f6df150f0874e7f2f2d113dafabac92ff2f6f6270204fb7fcc0af4ee6928231522ec031fff28f8c123dc6bd520df011fd8c03e03eefe350401fb08f1f60afa6857d426110dba1bfbe9f60cd7eb00cab4ebd90efbf3f1f901cbabdff23d2dbbd40716b64ae4d6f7e8fff52028d4f426df08df0047efebf4e5d7d9f922eafbe0ced70ae5abfce608f23e2b0aff135b47e65011130ba96b0bd0030e2310faa203fbd90b17e5f71cfb393c24145ae504231e2234ddf00a4508022345fa08fafbc6cbee2ad30846c2f01300fee8652e0bfd29284df51610f4180aea221fd4f0e006efdb02e81421191f170d371b150a12002224ea00ec142bfa1d63f3fa3ba32721de090b,
      4096'hcf9fe2b0f8f7e7ffd7f1f2eff6e5a80bcbc6cddcbbcde3ff11e7df93a2d4c0fcdd090df901fba3dcdeead6c908a8d7cbee0de801e2feede5ff1ea3ea07b8ecd4d20eaeac13eec6dae407dfcccfd7c5d50f09dd97eefebef2e3f0269af580b7a8d8d9d7d8ee0605bf9fefd6f1bef1e9f406acd4cfeeddfee1eee1e705d0b4e200e0a1cdcf2108590e03f320501c0f2d0a4007c66ae1e007070f1d96afb5eeb8ff16061424cc1c1729062dd41f2afc192ce21a2562fcf7423312142603c5b41229d800ee08e8eafbe300362603da2a5727150df33ff808171703d8c1b91f3bd4ff17030d202dff0531ed1b2b1edefc30e7fbe2fe4e100b3f01fa42d1132d2f1cf8f118182be0f9e210240b0ee9eb20111ed72400ee16befafe04fee203e026e9fc15f7102fdff0f4ec2f03f6ee0d22f9c213fdef182df80ef5ec21f4c33a4407ef14ff05db16eee8f3fee90bdf04e2e2e6f613dbcdf108f6d4021d2b2dc5f304e6ff17f6fcf700e8ed1ed20cf9140b190d0d0020d8ecea04f3ffe51d07f3eeec0ac484e4c9f2f0b8f6d5f4caa4f5f4dfe7d194d695d5d4fdfaf7fadea5bfb5e4f2c0fcfce9f801a5dcb7edb3b8dfd1ddede8fcc7e7d5fde5fdf40296d6c5a7eed8e4dfcec6a2dbbae6d3e3f6ebe9ceb3b7fef308a6f7d6c207e302d89ff480c7c0dcbde8cff0e5f1bebdc9c9dbacf2ee01f5cfdec1e9dcf4d102edf5e8f1de80f1,
      4096'h0c16ff2bfd22d9fe0fffb00be4c1e6ef0e1a3feb12fef0f3f00325ee1312fa050015e4e905e811db11eb05dad1f3d9da05f7c4f2f6ff03ebff0eccf40533ffc827f7f3e2c0dadfcdc6e9cca40fbbcbf5f6f1f9efdae5efd5fcefe50feddd2afbeae5c5e3ea15f9d7f9e009c737e8f312f900f1ebfde6e9fd04e12317dd06aeefb9e0f5d0e51ad902dbff0ed61eecd301ebe2f5f9fe00f4fef40acdd7dfc8ddef0004fb0810e6e5e8e1efe7d6feceede5dd0800f2f2f5fd07d9fbd1d7f2ceedced8f8f7dbd302d3e8e5eae3eafae3bcc30e0702d5f1f7e3f2f6eeeaecf4aad9d4e6ecf90dfdf6fbdf01e1c80cd8fd050f00eef8db13f50ee0f9fdf4f4f4e4ecf2e3140f0c0ffc0cec2a08193802f200f02adafbfb200f11fb0ffdd9f9fc261cfc0afe1101ef0ab2dcb5053929e8f409f3eff812c5c0fb03041cf201e3f5fecbe4f302011301241dcef3f6171a31f5e90bf8132e0de2e101db0ae7d8000c1602f10bd3fb100e110712ea04f9d3cf0fdc1c06a8f8f3060cf10dfb0f120406d70efd10d4dcc524f17b161538fc1c1e0116d02ec8aa23dc800df22d11c7eb04c0fb0812e024f6de383bfbec5e0d1223f2567705fc030cfff10fe30906eefdd7b8c96ff823d248c5181519f62e10294c374509120101daff17072f2325d3bf2726dcd503e10f2817e5201fc61a122dfc0ae63701ef162415100e1d141609de18192120,
      4096'hb2bdf9ed11f2dffaf7e6e0f4e803eef1eed2c505ded915090ff8d1aecef8f105f5e402f007e3da02c905e7d5f8cef6ddf200eb06c60aff03f407c4d5e8acf703b8f5e6d8e907cf06f9120edefce3f6c803fd07d0ed08d106e3e3f0c3faa1c2c7ecf0e5fb00f7fcfeccd2eee8b302e4ff05e200c3ebf717fef9fede03e2ece8ee01fcfec4131e57e8ed0e372631f7dbf810c30818f7f222fb2d13d8e9fbc3f90a101412d7ed08e402ca1bfb3712cc3c2de1041d22e6fa08fb0e132a02d9e3df7f0407fc6004f4050b01061913331b340aee01341d1ae121551d05e4ef192c00eb1cd72625fc2b0523e40d4037e70ae51f0ca7112a11fe050308250ee901100ddcc9de10fde4ce150f030118d9ede335dbe208f20104bffb03e905d602121002ff20f50c28fdda18fcfcd6e9c8d12cd8e91af0f5fe020df50a9f0ccb1ce9ebe6f707f240eef5e3cae4e00602e2fcb2bce2b8fce5e6eaf6f7b80727f610bfd1ee2bc84aea0302e5eef9439edbe4f80c33f2031eeaecfa220ad2f1f617fd1907cf092916ec32fefaacf6e7e49fc2a9209fe510402ee8d850ae03f3e558260a120cfbdf16cd16f0f7e4e00ce20428fe07d9a011fed197eb01fcef0004cd11e52d2d9c1421d7ee30470c1221e9e33dd2f7dcfd15eae8d41211e6f2f2212e2201f9161b0fba01bce88516bbc605c8c514f8db3ff81d0909ebf0d406ffe1ee0cc7f6ecf5,
      4096'hd2eaf5e7cbdbfdff02f009eaebfd22e9d019d2f8f3dd130300f8f7eefa14f905f7ee0507fff406ed02f2e8c9cb190de80ee803110603fa1bd6e4e0e5fdf4d3f6e30213e7ebefd9eef60ce0c1f0c4d9dce50fefd1e605c4dad7fe0300eac9e216d73bd7e8fbdde7e313c2d6f9f4001d04060ce5cbe5fc11c5fce2edf52a00f1ffdbe0fbff18fb06fdedfbc2401a0aeced45fcf817c405090600fcf7bd19ebf704ca0cf2dbfd000616c61113072cfcf326fef4d102d7060df916234409c5daf1f1c4f4e92cca0b28fd0607181d132c162e03f3f22b130602fc04fccdbbfb47f2d437f92019fdefedf815fe0b0efc1ffd0503d41623f80b070c0d05e12c1528d419caa0e0f0ebb6bffcdbef9eefececa1dfefb4cfc7abe103ffef05f580ccbab901acf7e8b6f4ffa7e6ab03bfe5e7a2eee3e4f0e6e8a2fbeff2fbf7e006d6aedbd4e2f0a8d6cde7dfffd2f7ee06e4e8d9e6f9fa02b7f1dce4070006f4acfeb9bbccd6c0e8c405ebefc4a2e0ddd9e205bbf6ffaff2ecffdbdce808f9d305d202b8fe0d0cfeb227221df8dad1223834140e1319cf060be3d331041e0df9fafbc7d40116ff1206f635b921db171e4415a34c60daf13a0eebfdf70645023a0df5e4b87aeb08047ff10d190c2004ff1e342f162119f44a14fd0b434d1bfeeae5211aebfe41c459240a350340c4173038eb2df94afcdb2a271821f92e1b3834f302131a29,
      4096'hddb7c900e6c9def5fd04ceddeb0ae900d2e1cecfb4c5fe03f7f3ebb7ab02c305c2f7ff09f4dad4bfccf0b8a0e5eac7d2eaffec24d117fb15d40fa3ceccd3f1e2e402d8841aedcde1f1fbeac6d4e0bddeedffe780fae1b9f3e1f82ecded99bedfb7e7d2cd0dede4d2b1acbae4d4f2fed801c3e396f5dee9bd18e7c008edcdf1f01a0bf7210b10d303fa06c3dbc124ad10201338df0946f50213fd1d33071f1efaf4fdf2fb01fdeb0aedc73e09ec18eee11bfce5c1f8fcd3d7fbfef7efed0520f930f5d80bea110cec20e20a203cf3f5000cfe07c8ffde0105d0081727ede908e4f4ebeae8d6db0de5d1e2f9def4e9ce0dfdec22f9fcd9fde0eefd1701daf4f5ebbc3422ec01ea00f8d4f82a2733d002f71cc5e20032d41206f907be2f12cb1c06effd08dcfc13fbd8ceec200a13ec1ef7e4f2e9fbcc020ff8f4011b0ee7f4d301e6fbfaf7061e3beb1f04fcfb10fce83709fc0600f704fdfa06fddcfefd220e0a09ddfaf705000725edd5050afa23030205f1ff25131910010bfaecf4240315f1001008d21d1f2de7ed12411628f0f4fe369fef0f06de13f70bfdc1081df0f9091508071aef08160ef9fc1c2d270e332402fd17f7f9fa030611d5151cf3eddc4bf7f11852090325edfede090c4520fa0cd2f01110f9d02b3f0013f8181d23061204fa2418050ddf13f3c01f280bf0edfa07070d3c11181d190307ec02080b0004,
      4096'h191113bd0d5c260bdaf621473e180b2432d1082d20cc0ff41a13060139d90cf6070b06f4fd12fbfac91e17432db9220be9020dfe1bf41816270d4cff12ede154f11a177ff62c1014052c31272f2a491421fd3e681e2d733f0edbf5fa3628f5f140d5232e0c370023c5f92f35f10ec70702e9065b122f1c3a1af0ee12f4041004ffef0f27160addf0fbe3d9dae802daef042c13e10e2dfd00f2ec2b030b2920f902f8d1270edfc108eff41014efcdeed50f14d8c7e307fb11ff16d622e11223bc0c08f7f7041d01e919faf00ee0f5fadc12f7e3fa0701cce8fc1210f1f0f0fd09fbb0eee8eaca1ffdbe1203d003f2d033f7061d11e8e8efe8fbea04fedff908e6e40405e108f323f5dcf525311cf5d5f540d8f30623f6150bfbf904fa2de73e0605fefefcf40abb1bcf22492d02d818f9f30320e2c8f5fdf719083407efe4ddedf80d112e12092de205060ff335020804e4f83e1feafa0213dcf8ece73819fbf723f6f4fc020b191a0bfc09f1d5060418ffb0f6221c0b051ef20e041514db3611fbe118e618152d13f21119180aec0e0b0cbedf0fe8972cf31efdc10900cc1000fc0c1f18fd010e38f31f041828ff3a38eff90af9e6eb091034fae507dacaee39e11fdd0f150a2a160c0731321b253d320c1627ecf600fd15e32ae1d405e6dad10af0162df90cf81cf6032051fbff071b08e30c1a17090920ff0602031e24fc20,
      4096'hd9f01a2c1902effa0407f3501df90de741f2e941d4db1e0318e5f5e31ac8f50cfa11fab911290520a6221af03ad5d700d60d07efc7e9fcec040651bd03a904efa60be90ce03a3be5f10e0f2e2b301734f002024104fe0ee6edd1dfa33852fcd31acbf6310de22037df232800cb160e12f3d9324311f0fd38fcf5f0f44bf624e4e7ed04d700281dee0a081a24f7f12eef04e2e3310a851006e20ddccf08d7ef040efc100ffde11301032003180216160516e80f1e1b0901eceddc6ddd0db7054befd4ff05f7fcf004f30f14b62d1722edf5fd1522d9f91a39000ccae61e34da32121c06220a0dcd340f1bec3c021117ebff18ec22e6fc11e7000316114e69000fc8d2e9cb04aaf603eef1d8d7f9f0020cd3fbb5e4a3efe502f8e70fe8b6dfd5f6e8fd0b14ffe80fedec16dce9d81adcdeecfef70de41212e2ecdeb1d1fcc4d9e0f705f28324edd5eff611efd8f9d4dfeaf3f6d3a3ebeccec3ef1117e4faeac6e3be12edb909ffebe8e5c8e2ebeee607e805ebd3b8fd1515da0307b6f812e6ea109dabdcc0f7c1edfecbfd9f04e8ee9bd3fcaba207a2e2000bedf9a2a1f180daf4c605f3bd001dd2f58af60910edb20010d3f6e2ef8b0b12ecf10555efd380e4eaa5f7bbf0a1f00c04d307fa13daf00d0ef7faf9f6ffe21cea06fac080fa1a88a2fead02e6f4eaea9fb8d615bfd8f5bef804a0f412f6e5cc16fff5c2fcd4039be3,
      4096'he6d0d4d3efafe1faec0fdbd0d0fff904df17f6bddee7ff05d7fbd7d5d2f1df01dcfefc0d12e5ebdfd5fdc2c7f2f7c0f7f7fe00fad10df507cbf1cac9ead215d9f3ebfaa9f1e4dcd7e1eff6c0dde0c7d8ea03dab3f3dcbbc7010411e0f8ace9d8c5ecced5fdc4ebddeeb2dcd2eff909e404f3f8c116edfbcfed01c0f40df9f91cd8cce824f8ee2a02ff0300e503ee1cf2f6fde9e8fce8fc13e2f1f0dd091501000b07d328e9fb09f50e090fcecc2303dd0ff4f3f1fc05fd09c4e8d9e5a5e2d1e10bf017bbdef0c5ede4020ce2cbd3ddd9e205dcc1eed8ccc208f1d1e80ad0ef12cf2bd9fe03e4f3f629afc0f418f824eb06f700c9fe1613da1609ca0514eaf9f20309fe03f30010faf8f1f049240524e90e08dd34bde4fb050c00e30011ef800edb14e910ec422a2d0104e1e22ff1492ddcf218f20af5080aec024ce1e2cfc737e7d9de31f208fc06050830f1382c2310faf5112bf2f7132c0ae1efee126c061b4eee2c3500d6d619df29064c0cfdfe02f61beb42f12e031bf315f90e372b1ce4bb23f7cdff165305eaef331f28df500d01e0f9fdd3d221f605fea4f22fd812fb2509f006f1f23d00f9effb302615fd0ee8eeebe6eff4dee5f4ea441301d7db36bffc1cccf4d4f8fbe10d01e6161c2a1ed1fd011dfbed4c03f8e9dfe8073fe8ea151a122a04e3db1c2fdb343ee015140d05f4e11a0042f927ea0ce8ea331af1e6,
      4096'hebdce6e413e35416151cfbfc31e818020cd1c31ceeac15f3232ac5d8f703e1fd0604fb1bde211debed06fef9050d0229f4041017edf614fc2c060e08c5eaef1dee040b13f5fb0015f21c06101512f6ffe5fa2cf5eff7db150af913e60cf1deea0b26f0150fdc242c11ecdafee1021212ffd9ec1c071a14080513eee41316e10af1f6eef134fc0304f0fb2f1e0bf005f219dcea3a1fbaf7f3130ce7ff10f40bfb0bf72209fb1838ecce0546010c0404fe0e051409e0fb0408040e05efc8f1dfe5f90de81d0c100e0104083018ddebfa19f710faf3f3eee0c802ece1e8010efdee0b13e62413ea1c0911c017cde20e07fe07e0eaf61af9f805ed12fa0d17e5fafdddd4e615fbcfe9f001f8cfcce9e9d402d7fae6ddebe505f9fd121ff5d5e8defedbf700000cfef1ecfffce2e902f5f0e0f10511ececf106f80f19caf3f6eceaff0ee9dcc2280be7e5edfbf7ece90ac5e10df4ffa7f9f2d0dee50f25fafbe5c7d8bce0f3daedef02e6e806d6dfdbf8ea01f712e5d506e0f0d3fb06f5f8e7d5f5161b2608ee0b1923e6efff1b273202c8e928aa121240fe30fc02f4031ef7b5f2fa2105f1f6e829c713e1252a501bd1240ef70128d0f5f2f00c1d0c2412f0efd62601f1fa5cf90c171a1c13133434253a1e20f71a5613f337071501c00f332906df31cf15f1f7370e25e1310c19fb0fd71a0bd51b2c0cfc0006150420e500fb171c,
      4096'hf0db04f5e01739e604f62cbd0d0e3b17ebead6fee1c11f040aeddcdeeffd01ff09fe0c34efe55507111bfefeca3cfaf62bf7f03e13121516dedfe210d005f1f4e5f432c8fbfddce205fbfad6d9f803c710f9d7c4220bf1fffce20809d6e4fc36d257d50b0acc021c2ad1e0f3fcf932f6fb25e301ef09fbf6f3fcc8092810e40eff1713fcf9fedaf70dfdc4f0b302c9e4011824d30e41d0fa07e9291bf72910e5e2fc010206fcf1e2fc0908fb1817f0ec050de3e8de000cedf303cf0b08361beb0d07deea1534f9f533f2df1a1025c1e6f6fcf5d60a12e6dfe405260ffacff0f2dff70ac5e6eb1dcde0fac9ece80cd519080a0df0e8e0d9dc01f4f1ebdfe2edd40f040845e50ebbfdf60400c8ecfc0a00e5171c111119ff0bebf329163d1d1f04f8f0110e03df1f030ceb04e7f52deae1350df2000a0d0e1bf105fe12f62245cf12231ad4efee01f808de14e3d6c4ecda0204dcfd11f8d7d9fef01922d7e52640db74b9fb01dd16ef2df1d4eb0fef050600260207ef06f0d7f4f9f810f7ebceeff8efec0911102a181e05241a2303fffa06f9db1bedd542f0371002e3f2d3dc14f81018f8eb3ad219eef7d50715b13d7fcdff2a0505f2e10c0901fe03f0c2d64dd412df3dfaf61bfed32619f2322f05fa1bfc3a04f8334d69e810f4f61a09edd822c4300b13fcf727b919024dfd31fbfa05f2001c1f34f01602251efeec260b13,
      4096'hc6e3e008d2d2bf00cefdc2f3daf0d808e205f1cdc5ebe9fee3ebfceac8ddc700ae0bd8e306e6c9f6f4c8daf3f2d9dbc6e21cf1eff9fdeef8f3efb7a508e818e50302bad818e2ddeef5fad1c6d8eecce7eaf5f1bce811bdf5ee0924cdd6a8bedbe8dceeccfde8cecbc10bdddeeff9dc01f7d0f3d8ddd3d2d6fbeaf6fed6ddfbf8afb5f7ace3fad4fcdee700eefee7f6d1d6c4d7d7faf30209f8fbddbdb0a7cbede5f5010500def7ebd1e8e0ed07c9efeccfe7eafbd2e5f8f1ee06dacce4d7e6f9defbcbd6e403cedef7ff07ededf9bed0050611b5e2ead6f1d604eddbf6a3c4c9d1dfe9ddfd04e9d8cecfbaebe504ebf7f8c0ece1f9daf7d400ede001dbddde120228221effff9918f511ccced8c9c7efdb5027d9de39e6fe13d15c3b0715fa05c4f6de001ae3ede61ed3fcfdeaf4dc90d30fa9e42af8f60108fed7c1473d34be3605cfdb362211e614eff4f4e9fce0f102f3f1f10af8e2d1ec1f2e31e9d921f8d2f207d9d7d8cea9d61b00cb1603f80a051b27f3d9d6cceaede32edacfe1f5d3d8f8e4ccf22d220315e70e651a1716172bdcbb3eedc438132418aee610d60c12eb1331d3d6ff2c3db328214df7c7254005ff25f8d7f31007121e401cecbfb41de6efd84ceeed2aeff92c283d0e4e5d30fcf6155b021937291dfbddcd146ff50440ee253a12fde038b7f950269c22e622f4f3e01f0f2c3f3a0e1fe7fa221f3d10,
      4096'hbcc0d9e5f99a01f609ffe9faf6f21710effdc0e3b7f0060ef90bf0b4e6fa0d0104f8ea0ef8f631e9d4fbc8adc019ece022f3de04e4071613de0d99e3b9cae4e2d90628c3cbd0f32aec0fede5b2e4001fe4fff4ac05f1e5a400fc03c8fcc1c607f54ce3ecf9bf031332afbbd5e9fc2ec3fbeffdb7104008e9ff05aa1a6413faef0c12301a17ff36ede3f92e492bf5f81f2edae81cdcf61bf41f1aff0812fee7fa42020508ec39f21efb24e6f738da193ec1042e161ff7fffe1ffffa0bf9fbf97ff0e9f679e505142e3d1d45233f3d1d410a0807fc100c42740909e9ee300701d328d6550efc25f32fce03024afd01ebf6fedc2c2f0e3b3b26f318070b1d2dfd0dbecfe9ed18d51914120611633ced262d2ed1b6251c862e001005c0f708a4f604010237dee10f03229329403d19da0e3cc20627f28d0f094c032824def3c1b817b104047f021ef807f52e0c1234202c4100030df2e6cff85df428e3b91936bfc84eb32d310e35312ac7123c12ca3cea4708ba12180cff003f10102a0b263027350cf2fff3f7f200eb1c09ddd200f3fedfebeaf4e6f30101f2f1f8ecd5e209e404f5090610fdf1e5ef11eeefe2dae9f5eaf100ddffecfef4f7fbf5d8f4ec05070a09f0e2f1bbe6dbebdcde10f9fee8d2d9f9eafedbe5eff7fd03f8d5e90285eee0e5fdf5f1f0fffbf307f3f303edefe8eefaf7f2f3eeecfcea01f7f8eedbd3d6e8,
      4096'h2b19231bfa17b8d811fed4efc4f5d61ee1032ad3fd50dcfcf7d41428242808eac3f018f91b0e0518fcf3150ffdefedc402fecbdafdfe01f423ede2f4211d11b0262cd1bc132ffb16f9e3d610fdf3f1030beff3ffdeefe1e7fae61e1e16e417d7eddadecee8f00dbef615f3db0ee6d527ff2f03c5e3e2b0f2fde80de1d3e8d7d9ceedcbe706052f051deeef2d3a1647f2061cfa0aea01f7092605eacb041ed4f506e80b08fd023827f621c808d4360304f7f70be913083215ef0b05d6deca1303b2d532ece9f40d3b173e02ddc1052a46eff8f5d40720ecdd1501f2cbe1f0d3f62d480d0b09ffdb3833033ff0090e1ce7f91127d2e64e2705f217f021451910eeb01f15d0ea0638dde02b2f5f3207f4014df1c62f33a3060a0c10c2cdede62cef0a100fce1a06fef5c50d373e19f41742edf9facdc8f7fc06f6163afce9ebb64eded6f76ab31f53100703293c16334d43fdfd0d23f5f909e136e7d5ee071001e446c9251506fe093d06f701caf123e8f105a755122d2103df2602e5192e0a48fed5fd05eee6f5140edaf2130214f6fdf8f8fcd3f212cd04010605cbfa0ed520f614f70501feec15fee8f40e00defc0cf10af6f4dfd7fd02f7fdfbf619ddd7e50edee705fb02fef6f4eaecf6ea00d0f7fcf4f2fb12d7ef08d605ffeff3eaf0e402fb10f104f5eff7f30dd5cef2c8ff02ed04f7fd17f501ff0002fcf0e913f8eefc,
      4096'hf8fa11c624e305efce1d01fc10f7f5f8f7cefbf5ffacfef7fa12f010f290dcf916141df2062815e4f00cfbec0ce916392402070a2009f1ea23fb0f01f104e22738eff32fe8041cd009d316ed431de4e1f0f90eeedd05f8470ff70ced12550cf0eef5ffe2e412061bc7ffd80200e7e0f8f71bf90407ebcbf107131916dc35022bdef501bc2c0843fab802192d4cf702011db50111f8d219f82613cee4fad1deff24090df20124d205e727ed0827d04f4fceeb3305fcf5f4fc0ff90ee5ebe2d46c0909d43609f2f22616121f0c43381d1c000e15e405f4212f172005fa4436ffdd0ca137fb031a1b4ae10c373de504d8fa01a8001304fe160b021221f9fc1c33102a07f605e0dee505dcf9c6d1d3ecedfaf11b21e50a36f707f3f0181ef8f7fa01d1f90303120104f00be0f7c8f802dbd1f91feae4e7fadae4061abc103a18fdb61d08dfc32efdf40c10eac8c5e8f2cdd10cfcf6c703e2c202f814161103cf030fddfddfeee30a04cce7d1e5de00f3e9f20814f8e9e6f5e2e5f80f17ecd5cbfa11d7cdead2001c16fee8e6062516183720f0e9e23fdfad05111efad5c70beffc08fcf4ed0203fc303af816e8e90c12160712ee1518e409330d00fc2d14f1cc0316c0dbf608fffce210ed1f00fced083c2c05ffdf47ff13190510efedcb0604df0a17f900221aecfd6002dd1724e5ee1901fcfbf43e08152203eff40a081635f622,
      4096'h10ffef16f1fae70508f8d8fef006eafbf9f216ece40efef9000504f31a1610fed7fcf4defb02cd14e3f2e8e0faf1eee2fbf9e5f3e00209f809030f04f6f3e5e0eddf0003e1f419fef10404eceef71214eff4fc0e0dfce2e7f7f9f3f2f501fded0eebfd0b04f6f0e4e91e11defdf4e804f9010502010adc0603f2f10df312ccf794a5d3ecedb3f512edf5f3eaf5f52ceecaee8fe0bab7f813150bf0b3f6dce80cf6f0faeaf8c310e3d401a2a8e0efcad2ce01f8ebda0eff08ea1ea0b513c5eec7d7b40496ebd6c20f061ff7d2c5d2eb11ec06e1a9e4fcbbd001f40fcfddcca9e6e22eeee616f5fbe605d8f0d9dc0c01ec05f3e8b6f72d1aec01fddc0335f5f113112425e00ef060f9b90c1759db035607cee2d33706800300fa0caa07fbd1bb2009edfd09e1e93c48e5f7dd110f222e1f34f22f3910fb06cfede74bf4e6b8db7fc6031a7fccd5f901a100f4b5d9214111c1dc1c49d35721363ae9c3f2227faf06531c362527d2e1310fc4f552250aead4fe0ddf690ffcf93cc716fe003232f50f1621ee1c0314e5ecddf8e9f6ee0babdc102206e2fd7fdffd0d061e0c1816fefdeb17f9f8ec17f0d3f2e401fe07e9dbf6fb11f0d9ddf7e7fef9fdeb24fd2b1ddaf901c1f53317f00411f4e71ff2fbddf21601f3eff8d8f921ecdb2614fbd8f9f0f8e9febceec21ec9e103e6d5edfdd6ff04fffb0507d5e7ee13e1fc13d2b911b5,
      4096'hf6f0f1ee2d0525100afd1df21904e8f52dc7ea0611cb0bf60306df030de9090335f9fdf7f6fb0a05f3120d2f1dfd133007101b1bf5fa0a08e2f5140eecf8ef68fc04eb48edf11a04eb081d1f1213f9f80d0c242efdf02f111eddedf60605fce6020e181301ebfb1cf1ea141df608d8e604ea0d121efb1ef216fb0511e928e020e103f3d3fc3bfe0400ee251100221a25fa10e71f0abf3cff18fcd5f006e110f9dfe7141c00f814eef4f9400de305d1ed0cfd1bd7ec030dffecdb49e8ecd8f3dfb8e20915020cdfe71bef17e5eec9f6ede605fa32df0aedd2ebc5fcf1d21afaeafb23043f1ded004525bbf6bfcb0af41af315ff42e5f20027e8fad61a13000edff8fcf5e112ff1df217f424ee20dafc072f91010fe5ce0cfb1a0ccdfd04efe4080f060a09ece8061e040fe51f17eb1c3fdce923fcf6fb0dfff310fc19d5f6e673030ddd34fe07fdfa11e106111a11d3e2e80227e006ee2f33f5feddf61bf5e610ca001c210c18d825f5e1ff2307fbe8fbfd01e42312091feaf006e8f3f1fee3dff1c0f7f0ec0b30d608f40bee0be7fbe7d9c2d1f9128ff6f3e6feabf01ca60e00fbf5fe01f3030518f805fd20ddfa1d0d2008e1fbf9f704d9e5100b1bfacae91be9fd1107d5edcbede3000f1419e525f416e7f221f3e2231b15f4efd8efc60016feeb25e2ebfed90026081324f30df7d906f2eb42fdde0100edece6f4ec1a80f6,
      4096'heebe38add8f408eef1f1db22f4040af57ec4c32105a012fafaf9b8c9d8ceee1ef5f9f3eefedce9f6ac2a1ff00fdf131dacd91808b5fbf5e918fe360a1396d0f0b546c158e013f5dddae627030d0a330112034144fae21b22f7e4d8d3304ed7e30caa103ff5d51126f5df21dbd30c061d08a3ff651fcdd91d09dd0c0b1be724cd13f7f23afa0ac719f81bb3b7d7f5fbf6e84011c40a0af1120205600ff743ec01de0ff0130cffeb122ee7b2cacb3718df0106f0f817e0dae30cffe3fe693b11d641091dc819fef5f51800aaf2080aefda1cfb07f0fd23cdd2f82a373efbe30319e9140fdbd2eadfb90d0af7f229f603f7012afaf7d9e9fef0e11601dceff4ee10a7abe7e3dfc6e60904f8ecfde7ffe5eddbebadd1c3bde3090000f3b6c1e6ce02e7f104f5fbf8fbf0bf14afaee6e1ebe2f4f4eaffd415f70ae507b3d1ddc7f1cad9e802bfedf2cfd2f50af4e6c6e8e9f2e701e68aeae4dbd9f4f50ac4e8b9bee0e1f4d7e502befadaf8d1d0e1d909fdfcf8dafea4eef3f5f1ff07bb0f050501f52b1b244120fcbbe5050680bbe500f82ef9294da2fe43031af1042dfc2e3719f598110d0d1108bff92bcbd4dd02f3d9bee50bd5d623ffe8ef08fba31a595123de520cd8b41635e3d62afae2f4f1d5b7e10ef8cbd215f0dcfdf60d172a00b1410ed8e6e4b5e41923bbd50ff1ba29f50315112217f8d1c0cbf90ae51ee4dddde8cd,
      4096'hf9f6f70303cefff2df050e15f60afd1228cbff0718e6f9f20b01e2e9f6ef1202f4070cea0806e5d8acf42ef003d5e4f3ddf712fcc6f4d2f51803e1e7e4ebccdb061807120100f10ff00c12f71305041aeefe13ecece6e8ecfd09e2fb26e3f4d907f2f1f3f703ef1bf0e7fdcde1f413fe04c1edf1150af7fffef4080109fb0af5dda5e2d3ffacb2dce001dacad6f6b7fd9aeebeb1b8e618fd0bf5ffdac1cbc8f7d8ecefdd0bd7bce6c6f5d6ebdedaecebd0e81adcf00108d904dca5e601fe0ce3ecbfd0ce3ce1f8e722eaede0e6bbd1c21cffef80e908d014ec0c28bcdfae8dc9cce40dc3eddde9c795d2a6f5ca03dfd50cc5e5bcc4ed08f206f2f709dd12db05302119130df50b0edffecbd9cd0b8ee5f20a30c92f1f2008f1f133431a0a38e9f1f5f9e50d09e8da27eb1f26c3f1e4ca161bccc816ffd1e7fbeccf16175726df3f11d2bc660fe1f3e109fafc19d6e9da22fee9bdfeee10cb100a350b21e00f11dfd705daed240bc7eee014e5230002fef413fae6f8e0db0a0afa17f1e1c5f0d9f31200d30ffe1cf7d50411ed0ee104fd1db9e30a17ca0409e606d811ffc011f7fb1009f0fcff11f7e91911021102e3cbfc0700faeefa12f526ef2c040edef40303100f21080c0805e7f103f611e50cedf90a0908001f12e0f5e3f4ee0634fb060305eb09f809040c06fd06f4fb00e5db03f4e70c19fae904eeece3f9fbfd04f5,
      4096'h3be508d518402b03fd1c58562b1404f931e5e023fde8220a060dc9cc21ba0005280ae9f7e9191037eb081d552ffb2f2dd8f108fd1fedf4f8edd87f271cd40a5ae0f6e27f02fe1426e5181a51231d531e16e72f4210fc614a0f0ecbf5ef5b0e114ce73360f71bdb5fdfdd3f140723e1f8e8e0f15928180f5c0a202a270e4f311ae9f1000ec6fa08ff00f3efd4cf0a341bdb21f0100ada0408f7fd1de01210220112f10103f9e511f50bfc29f8f628d1d63208f10cfb0d07f2daee0a233a17039300e41ed532e9ddf4caea01c3e9ccd8f7e203ed06f108c3a6f2fe3411e5e5fc2acc42e0eb0503dfed1402f4ebf6f310da0800f2f0f7f901e4f3e01dff0ddfffea060918f20e193ff3f9033b2951fcd00c22a1f5382d00daf213fcac1c34bffb0c3e1316dcf108f9170c1e25352dd61d38eefb28fb0bfedd103efa4919e00dd75c12ee1a62eb0a2c250211344135230c0d030c2c220700572ee7e8ed1d0d2e170106de2f1f06250f35f31b163d061db71a0401023b19e3f60d08fbf102dff9fbfb030aee170906c5e2cffae5e2b4f7dedafe182bd9d94ee5fad7f024fef82e1907aefbe9f9ffe3cffaf1e61a34e9f7f6ca0dfff1c1eb01f60bf0ecd324e8141be6f80aedd305030a0008e4e627ebeefef6e8f4e9ecec0bf4ff1ee2301514c3140cfbd1cec0f4c30cc3d4fce8ceec0adf33010aeae9edd2dcebfcead400d9c60de5,
      4096'h25eff5d3190d0ff519f209395113020910cacf26b3b818f92d25eef926e9e111e21928eaf105fd32ed33c60f1fc44943baf0201ef7fcf6f1281d16f0d8d7ea6fdd0bd107e60e090b062339ff2d1c47ff18ff17060e1c295154e1efe8292eec0437c8393419f3ef27bc01072ffa20fcfafbf4032d0f131119041bec1cfd2605ebb8f6f3bb29321ef8f801eb430adc51ee0ad9c04804822af4191abfde07b1f610f818feecf92744f3e80ffb130bf50e36e7fbf208c1eb24100b1224c8f49aa917abf5ec28fdfcf921d6250ded1628550723f2073d09080e163116dfe517fdbffe27f1371e15f8145f211e5a3bd9091226fadef530080b3533fb062ef6161217f5e20936f716ff12fdcffb292a3afcdb1116e6f02222b328f1fbfcf21c1d121df010fd11d809f3edf0aee3402f0bc90bfc04031cf1d2f5120902fb0bf0f3f895090af00715020c25f91e1e28220ef1060a0f180cdde010f3dc0800f3ec1922eee2e6fbf4370309ff0feff210dfd619ea1300b6e8cd040d0a0d0c1614f82802f701f3c1e9e708c3a9faeddedadbdae5ce26cddef4e0be01e5fc0904fed1c1b3a3e6ceef1c0110e5f7ecf8c8cbc604d0bbd7da0be2f9d505f505dbfa83f418d7f5a503f2f388350dc2e122fadfcaf8fab1dc140cdea0e0eeb3dde8032acedf8ec3adcfe402e0f518cdd9c1ebb4e3bdfdf2f7f8f2d5f6eff3eccbeae7f1e5e699dcfd,
      4096'h1501e626e4dfc0e9eaf1bde3d61cbdbef1142ce7f831eff5e9f426fa211f1606f003e1ff1af6b8edf3fcf811efdfeaf10401edd8e003d7f50811f63bc70f1ac8fff4c610de0fff091ffef516cde203ea0af2f11613d7dfef08eef5fcfce01315fadd08e6fccf20c3d50af9d601facd26f9fb0b0ff2fbebf1fff0e60ac5d50304d3c5c516cdbcb0090b0ea7d9c810e502dc13fbb8d8f6e311e1130cb0a0f2e203bd00dbfe22c0e7f8eaefd1c6edfdbbcdf011e7f5c109060ed003b3eafbdffdc2eedfdc84eeefcae7cefff59dd3e5d6d2f9f0c5b1e8f6a7da0a0e07edeaa9faf0b9e9d8c308bceec4f0bacbb6e6f415ee06d7e5a908e406adefe1d5f900eb01f40618fd060509eafaf10ce5fa0c140aeefa1614dbfa50f800fb0618020df6fafdfb02f915fdeeeb02fe050714fafd0feee305e0ebfefaccf80bf018f0de0f0df90e150615e6effb110ce3fd0f03e0ece1edf5f91edfdf0dfaf610e70cf0ee0fedfaf60113f10101fafff9f4dcf9f9f718fb0204e9f3efeb130bf7f9fe05ffdb08f8d50df9f3e4e904f4faf0e2fa07c6fceeebf3f80103ff07ed08fee2e8ebef05eefbf9ed01fce803ecf0f2e6facbf8df03f1e6fff204f5f3fcf2ddedfbf9fb00d2fcebd8e204ddfdf6f102f5fef7f1dafffd04db08ffecf2fef3eafd03dbf5e2defe0704fa01eee9dcf2e9f9f3fae900fae505d4fceaebf3fafb02fde3efdbf8,
      4096'hfff2eaf7180822e92bfa04eb210e01ec1ad506350408fff2f802c5ef08d224163503f7e8ffdb061d041e0b1e28011a0708fc010cf8fa110c12f4fe1cd60feb4f0c1f041fd80dddfef407180e0f17e2f0efe007321308231e2af3e60a09f70d10f6e71e0809e61a0ffa00e7280f08f1fcfff6001d21da0ae7eef8dee4ef0eeaedd609fc0707001b0306021e3026f50d323cebe40b09bd2cf41a09c5fe1ce024fb0bf603e30f220fc9c31c4bf8f8db0b24c7f722e8d2fcf6f232f001f703d5be08d50e151102073d0de20a350d19100d3a1b0f1ce5e202083cfbeb00cf270fe0c71ec6001b0a042246d6020fffc729fc2005af0108f81332321bfb27fd10f6f4f8b38fddc8f2c5c600e3f8caf7e109b7fce4e2b3cdb4c9fb11e803de90cdb9d106c0ffe4d00ce7b7efae07ccd1e3c5cfd5f9f806f9c506f3fce5ffabb5e890fbdfcce3c49b01e5e2fbec02ffdcd6e1f2eaff04f2a7eaf0ddd31de8138af2b2ceb2e4d1e0e904dcede9c3cdd3e1b9f9e8f0f6a5edadfddf00f801f3c704f7f5ede801ebd2d0110819faef04181f00f8ea112bbccb1805ad0ff9dc12e2f4e4cb0d0f18f602e807dd02fef1fd0d1e07e70d28f3ff0dfcfbf4e8fa2c00110a06f602171e19f31ef518000cdef9182326fb0af1f1fa0721f402260bfc17f7df09ef0f0ed1e803edf9e8d5071700f71d0f0ae9f7f0dee01e25f805f50f190ef7cc280908,
      4096'hd5bdedf9e5dbddfbe800bfcbf6f6b9d9f0aee4b7d3e7fffcec06e893dcddf408d4f2ebd9f602bfe9d909d1d6fbbcf1e2fb00cdf1b804d8f8fe09beedcfd0ecdcc2f6e4d0b5dfd708d2f6eaf5e9dbe2eff2e8f3befae7dafbfffbd8b8f982cfcbe3c3e8f9edf6f3c7c2d7e8feca07e0f00ac2f5e1f3f0e3def5f7e9f3d7e980f1d58de1c804d2bd0ad7fb9fd2d8f29806d5b9b8c1acbc0003f103e9bebbb7c5fd90fdeaba02e0a0dbbaf4cfdde49cebcbdd03dbe3acfffedbfedf95e6e5c6eaf4cffdabb42df7e0ecf2f2d400dce5d0cef3f3038bf1dee5ffe0fc25adfa8eb7cfcdb8eda6e8e9fce380b7bfdbbff7baedf2c4edd2e7d2d9cf08eedcecd7f9d1e610061417082bf7fffc09facb05fbe8deea072602175ae4fd12f66bd614231af71bfa09f20df5dfeef8d5120cd518efcf3a05e5de0301e3ef05f0f71abf1512e021f4f0efd0ff0be8f7db04100be9ed09e703fcfcebe915efc7f5e5090bfd1c0901dbfaf8f8fb09e8050808df020de7f306f504f50800de04f702f9f2d5e7d10200edf5f0150d2806f1e51534180b1b090203ce46e1b30ffcf80708000ac3ea10fe030814e52c1007fa1bf71a1a144c1dcbd814331efae6e424de451f319af13ddb31d17f0ee70626fe1f27f420415b35f909483503f30c3e2d09c9f4f57fe8ea38f4243106ecf5311307172af71000fdfd11014814feee1ef214fd25180725e5,
      4096'hf8def8ee1bdd7f100f124b0b20dffa2626dce3230fcc35fa2420e4cff8e8fe0b3b0013f8d90f5d07f712130bf91b3239e610090ceff4161027f501f3bceb064dfffee32ffb08fb0b08192c360d0e16fb1f001606dbef2615edecc4da1a1efae6ec0f321d00f8e2360bfa1038ef16f3f507dce02f1fe21e041e06f0e4241df7050e24f5c30d1d22f2eafd143324faffec10c10d0dfe0818f50f12f40110e1e8060d0104e4fd00c306ea030f3e1bce0022f30512f4faf8ee08f70419f4fdffe42b08fffd4201032f13082612442f170525f6041e250a162029fe0cf103100afade34f01c1efb00130ed4ea0323f2fdec1401d61d1b041913160408080503150d14cbeaf8d6f705e107e9eed208f2fd06e0fcdedbe7d6dae8fb0ff3dadf05c70a03e8f7f8ddf018ec06b000f7e7e4e9f5e4100210f2ce0301f3f4fb15ebf8b6f9e59deeefe5f5f8fc0aef0315fbedfd16160401fc1a00f2f4dc11fa00c4f9e2c5df16fb030a04f10ae811cd07eecafeedf500d314dc0101f9150701ce0d07fef7f42a17fbf40ff3d5fdc905daefdb19dddc151b27dcfd62ebf8ebf621160ee41302dc0aeff504f6d1f610ea0d29f5faf8c4fdf5d7ce05f5fffc06151605fb1923ea091af4f8ee0a08f9f8edf830defcee010dfef60408ec08ee1b02fb13ffda1803f8f5f4cef4e30bcbf3d0decd0510dd0e011e12fefaf1f2f8fbeaf20de6daefde,
      4096'he4e5ebaa131bedfbcf0af8f010e5fbd3e6f5bcf9e40d1bf6f8f4e7cc02abcb12eb0909e30ced22e3c626e703ffeaead5c0ddf6dac8e7f50fed01feedc0c5ebfdda0fde19da0eef090af30e1af30803ebf90223020404f3f10ce2ddd5f83dccb7f0f9f5e6fcd209020e1ee3f9dbe60d10fde9f000030ef90320e0d4d716def20d05ec05dffa084c021c03ff0810fbfefaf1b9f603e0ad14fbe3fdf40010c5f7071bef1205ec1c2efb0b1afaf618f41d0018060c110802fc1410ff0105ebf1e860e519e9140f13db00ee1101ef14e4d7d7070af1e4f3ea200d1a04f6ff04d8f011d81021e3f509e12af5d30d3206f300e4fce8e10c192804f9fc1cfefa1a310f2a9092e3e0f4f4c20eefe6e8ee0106b0f2e4adc8f7acd0f20306eaceacaaa9c1f4d5f2efc0ff04b8efbbf8bbe0fa88d5d0f01ceffbaf0c14f5fbfbbfde058af9f184f29db3f1eec5f0f50afad5dfdbb8cb210a0acbf803d6fdd1d20e9fef8091afd9b5e7d9f3f4e4c8a5c5b9f19a09bf0d06bef6bbeed1f8e1f408d401dfc9def3e9d6f0c4272445d8040824453e180c0221d3ee1ef1ab2bfa1909ae0916cef008242c14f0e31f17fbd833244b07e22609c6fb3229f5eafcfb2b021e0df2d9d93eddede44bd20a0439e21a3625183748320f06fd1e15fa393f0b17ebc20d23e4c71fc52a25fe050a3fe8330d4fe4fd06f406ca232b1c00031113f9f1041e100607,
      4096'h1cd8f300d6f44929030f03b90c011518c701e3ea26b42a01ca01d3eae8fc0b04ee20f23914de3df5331aede8f242ebef2bfcfb2f170d0233cbfee90a18faecf7f4f73fd9f3fdd2f9f100fccee5f005db1408dfe10b1004c328ff0007d4cced46d648d80903ecf7084ec9f50d1dfa5fe1031d09fd06410acc050bfc023a02ddf70a24f90b182a2efa06fd2b470ef734ea3dd7f94f57082afa0a0f211e17f7301201f918e9f015ff20dd26474439ff1126020108e8e70212fd24fc681d08f3123afc11077f29152d150f002e3d3e3b2f45ff06466a02037ffef20cdd05177f04054cf6291cfa232a32072423ee031bf000ff0b17412b1cfc5309063eeb243622151008e4cff8254c0b1fee1a3820ef11ea17d4e16728ba1bfdef03d8070cf2dd0212ff0e1b0ae5ff14d90cf01e08133252e9e00f0b08f0f5003c0c3b37d3b4c938e20d027ff8230202ea132bf91a1a30f5f2e2206f11fa5e20ff18c207e86c04ee05e8da360af9ee44c400f21712ffecf60a05125413e6d53bdb0df3f9f02e0928171afbd4123533eade16382c4af3dffc2fa5df3d25d831f9120aef1e31dbe30127140af9e9291134040a323323ef4a2fdce529fe0af10a102e0e5311ebf8f64a030eff7fed26340c090608264b251116f3f82a2d181c553b130fe0061b5b210313f91d32fb2d0618f00611370b14d404ff04f226191117291a2e170ef10a110b
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
    .OUTPUT_WIDTH(80),
    .OUTPUT_HEIGHT(55),
    .KERNEL_WEIGHTS({
      4096'h93aee0b6cea0f3fbcee4cdd3cab687f9c9acbdd7b49ea7cfc9acd2c9a7e1e2c2f7d6bdd7c6f6e3cbccb3f5a8d7d1d2eab9c4c503b4dcc1beddd398b5c2b59df5b5bdabafead2b1ecc7e3c7fea2c68fe6fce9abd8e9ddd7e2b899f8afe8bbbbaca3b5b5c2d8eec9bcb0adaffbc9e4ddbf03d3bea4c6c1f9caa5d2d5b0bab580b3a6abecc5c6a9e2f9d9eef006a3c8c3fb02b6b7dbc69ea104d2ebbac6c8caece704ebdeb5d811ebe7bb9eecb5fdb5e507d7e1cb09bee9d7d9f4e49bd3eeaab0fcb0c0b8e6e1fae1bcb0faecdfa3e1a70803fdd2b6e404bd01e8a4ef94f8a89ac8d1b9d3c0f0fdedb5e1c3acf5c20306c103dbb6cdc5ce00d3ccebcdecd8cab5d9c8b20fcbddadf40af6f0e0e7a4a39ff6c1c4b8d8bfa2b2e0c5cbade4c5f0e5ba02d3eebae7e2ded2ccb0f7c8edb2c9e5c1c6d905c3edbdeae6e6b0e2ddb8c3eface0afc1e3fcb9ddbceacedf97d7ade8eceaa3bdfae0e301d59fe3abf0bfb1c5cbbbdcc3c6e0edc0d2bfc6f3d9eae8c400d1e0bad6de07c5adeae0e6ccaca2ce0106030c0116fd3bdbf101f10ec004e803f153a102270ce513c9e2f0fd1c00ac3c17c22ad83dd716dc3f12f2fc2104c4028df7f7e9d1fae0e1040411b905f127f5ee03c9ee23e9060c09ee0afc0f08e9f4f5ab1bf7ee0af2c01ef0f819f208fbe0d5fc0fec050df938eb1d13fe22e0f000df1acef7e70f2ed81303009fd2da04,
      4096'h2d20e7f1fd340912d0ede2c756ee190dd2f869dafd0242f04aea41f61803e3c808d6f42a1ca00ef73206acd3e71de6afe0d0171622deedd4e9c15cf3ef1d19b5321f22e1e7dce511e6e6eef419d226c31d11c818daa1f7d4eb36012de04b44f8ed10ed20d2e8aa260b2cfc0f07bcf40bf9260adaedf60c28f4d052dff1dcf8d205febac409decd8c802fec63056e79ef1eedcbe2e5e2ea0bdf53e6eaeeb28023d33bf727d3fa3f331f8083263e29dc35183f202d4a127f49ae8030f61cb9d2fc1fe6124c151305f8f673a7b3180dce511e167facf1a2f222034132e08008deb375f721d87ef280861c18dd03e2c431ce0623bc65eceffbcb071efa0f03272d1396ef020d32cc5f0254f4de0a8003806c2c80c51bedffadf6dddf01b2d9097f2ee764d380045c803c80224c071a805f6232f9f0bd80e6ba312264d828b9e2b03509d0931b38007f39010c125d161aa821f517faf3fd1fe4edd080dcc66cd6d72f03bdddb8bafa7ff280e1b2dfe57f01def280a5b57f0c149a38c9ed098e170614e9f0f3d5c50b1e0f0135f7ef2ce50b21c623eefae2db17381a0ceed7ecede2c5f0c32ffe5ef5298026ddcae4c008d5f0d20ef1431c5eb3121bf3f48050dc2499f4f7e1c32bc3d3fcce03e904a3c5f2fbf945efeaad15dfe2c7ea31d7dee3e9fab82780e7ebd1d2033f07c5f3bfcf41f2061dd6af04bd2be0f21714e951d507d4,
      4096'hbb91a9614ca87f80f75c7f7f047f9d7f0df180582a80807fa77fbafb80a8817fd2017f80592b70675dc3aa347780b57fb67f657f3c7f07167fbd27b17ff0217f0f42807f7f733a30d209c0b46ce4d419f2327f0be9497f3d08fe45d0237511217b10b7d47f69ccd187054724df80f771f205806a7fdf7f807f7f00387f397f58e2d408d0efc6f4f4f205efe4c7cbe1eff1e2d6ecd7ddd0f0d4c3def3daf5f4cbf4ede7e8e9f8ece5d4def8d6e1ddecf6e1f4da01cbf7e1e3edf1aff6ead6d502e4dce5bbfaecbbebd2f8f202cadccfede9edb8e2f9dedbedd3e0ffd7e9c4ddd9d0e5ded5e5f5eed6f8d8db00d302eacffcdfe8dff1d505e3dae9f2e7e2b5afeef5d0e9144bda4ff809dbdb11fe2c89087f80f15ae0e1cee0cbdf2206d73f0e6bff7fd380c097a674b4100c1f5e83e926735c0005daca17034c1b31d8effea263eb05bc0ed27347c1d90dfc1af87fcac0a6baf9f069f70906f6d3fbcb3f21d72c2d9a39fc4c0a4bd58004ea0f5a679be3eedee3ff7f0908e4613ae83fce37023f1107d6a28007dbf2dbc0f7b33bba50f0a43df0aff4161bdcffcef7d9f9aca8b70ea32b7f25ef5eb03fe5c580d07fd5b2b9fff71722dfbefcc6c421901cfb2ad412d218b6e796a1d8e1cd1c03fa8011fcfee3ddf1acda800cb9531c0be110f7d60649800790deaeff7f0ac02205af35fe1159be0c80e5ebd1a4cfece228e8da8c,
      4096'hf2ccc1fc22bff70d9109f326e4235c012dfbc705dbb28029a5eb0cc7f7b4d13fee1f8934cd7f6a6404aa23fc0642ee1e3937f7332fff567f0b86cdf383ad807eeac5c51e267bf7e5224009f61b48cdc626105ba90c80fc0eeb5acdd8c11ab2cf7f8002c97fc8bb8649d50a3b1bde2ee6f424085b124c54dbf346be1fa6c82319e6e5f4dcebc6f5fdfbf4d8d6c9c3cff0d8e9ddf3ddd1dbe5c4bbc5f0d8eeead8eaf8e8dbeef8e7e7d8d9f4e1f3eee9f4e7e7c8f2ddf2d7fbf9f4badff3d8e3ded1e5dfb4f5f1e1efd8e7e3fadddde0e7fce9ecc8f2e7e7f1dbc900d6deaed2ebdde4f5eee2e8f4d4f7dcecf0daf8ebd108efe7d6dde6faebdbfceeddedd8c6d7fd4af8563428b00f289ffe802ef0c9af80042784fe7f1d920f8003c64e32449e0c49c47bcea9a625fd610f242445178007d9e3c7059cacd2800a334c914812cd0d1c7feda805eb2c53c2c3edf0443380d6a7f534f7f21b14c257cc7f0c4138d99ae2275e80f505107f083f2d52dac90edb146191eb3cac57e0ffe4cfc246153b06de1e0526ea1f120010132fe904f30a2d02d10e18d1e70cf317e7ffc6fb312b14270de5e72303280ae41df418d7301c111f1403f404e6392308e82619f0e31afbfeda07151a1906e4221515fd1be81efe0303df1a47f00d17ce01d926e6eb2ffde80500092c1201eaf2fbdefe17060b05db03011b1615072124f9310404fafb,
      4096'h23375bdec23d8ab933d7cf9afeb1e0ced71b5f80f16341b136802d296e275baa023ad676ba8a80f2217400a7be5e7fe7238003caf18080f180510db1803dfe80d6f57f1ba1e4f67f7fba1e55c8412ec9e601be5080cbb5e45949127f77e551f0b62a807f89ad1947411834c60b6af7fb0c0e45cdec1d807f9880faaf8f11ef80285df8eeb62ab92d80cef1f240af460280414acec21759de2ec707bad5bc158b24a7ef7f0be17fbf7f0abfc5807f14bad8e127105ee69a99d7872e800d35419c341224c4da8080113ae4b68010803da7e418c6358ce313e7b750db5b803e42b9c428804c80e480237f38211cdadc35090762fc1980df1e14bccbf99224a238eb3cfe98e380dce61acde9cdd212e53af1ca3409e1bbea04e1e3d3f8c3f5a9e8c7e392263a111a2aae14f19280c62fd1ac3cebfb0d3315da01d1cdfcf301c31e80fc07d7b609abbdf1f2fcd0d6ff9cf51d200e03d8a5188dc2d823fefd04c0ecc4142480f5b7cddccf13271bb9edc22013010af1f18cc8da15a2d8ede725ce0bbf1bdbe7bbead31702d22ff23b0dd34d230bf5f30115d0fb7f0b7af90dd4daf737f7ef03042e1e3e0435b30ae7120f1533e903f5430e3c071826f0f70a4bd6fc3b0306d01521062ddcce28481bfc00f04e3f2be3d01f1cff0cd5ef24c604eed1f7f50c0ecd220bf3e9e81dbbee170d1ce4072ddff32f0431cdd8330b1a4ddaf6db,
      4096'h1111f6e0dd1ce10e0ed104f230add306ce0d18e0df0625f413e60137f4f7d2b7f7a5ff1110dbf6b913ffd7d3a114e3e8a4dd041402facdd7efdc05d5142b27d119f619a40cd4c3d819cec5cde4a527f2f9fcb616badf00e6ddf9fe1daa02fcf98530c50caffcc621fbf2effbcce4fbca0318fdaecad20a11dc1616be13c6bbd81695d1172ae83bd91c25ed7f03eb1eeb6680c9f2e5e6d50ef447fcfa9d1dfc6702f1d0d7f03aeeff00c5f5df08e3007ffbde062230fbd823062cdf0206f693250edec5fd265b0cd1ee2204381414d128b41de6c411fb1613cfe611daff05e3f3cdb1ffb0454148dd80e9e2011342f3fb05cf03c615fe22802a47c661f6d1d7d1d4df06dee4cafc06fdf0f9f2c8d8c3fed7d4c4f8c5ccc9e8dfd8d0e2ddecf8c102f8f2cfe6f9eee2e5cefcd7fecdf9fcdff8e7f6d7f5d205f4fec2e3e8cbd3e6c3e9cbccf3f8e7e0d0f2eff6c8efcef5f9fac6d8ee03e3fbd4c3efc609d0c9d3ced9e8d2f7f605d8dee1de00d903f4d908dadfd0f2eff4e2c4f9e8f1f4ceb7ccc12db1bede80ddd1b955ee7ff3d93335670bb8551cbf8065b1210191b7ee52e803301f845451a84284826fca7f9d1aed2a01d0d6de75591b37268e08c1808031f8a88019560873faa87f4abe9bef80382752ccbf2a63d7d333840e9921a180d87680e080336036b280ab80eaa27f41b9f9b286fcef2f1b80dff3d737a0e6cc05,
      4096'hebd313e2ffdf13280b43443129c934070505c01d119ff6560425023104ff02ea34d965db331b2cd103aef1f1fcdb37361c06f924f05616f83605eefc41d30df119efa4cb2ef62fe5c5513c0ff8c6e41b2939ece42422ef0f0ed928b74afddbfbd125ebc7e9222fef1bedcc350c4b3312f0f2ea0d09bb1dd81c2af8fd2bf2e5fde4ed0edef7e4320f0d0102fceeb712f4c0f6f69ffec9df45f62ff5febbf5d60815000fc435fb04ecf0c8c5e3b3dbfc15a1b8e30cf328a4fa31f5f0c815e1e30100f5c0a636ffe2eaef0fe103edf2eae70deee7f1f7e7f306cde80ce22ddfd6febdefece8b2d8f4f309e3e5eeeafe0fd80200dd911ae50ceb27e2ffd41ec8e7dfe3cd09086404f60304d414110514821e75801ce1e633d9c404c5ef080f26543d23559602b709a07fc40dee0e31b94b52b0cec102a6b8d6fa2710fe43bcdcb07fe9e900dc967f27332fe62f1e126cd4f411cdc10756084121bcf6e3fd26fbeef5018e79147fee500895d60128fb510316ffdadfce34353512366617258a23dc4dd0ddf8dbe2d0eafceff5e7f3c2fbc9f8e6d0c6fae9c8c3f3cefecde7dee5f7e9effaf1ceea07eef0dbd0edd7f8d4ebf8eefee0f7d9f1ebfdebfac6faf3d0cbf9cce1d806f7ee00f8d3f3e6fdeae6d1f6f2eff5c8effddeeef8d2fad0f6d1c4f3e5d1f5dff5effadce9cae2f4db00f9e0f6e6e9fbe7f002e3f0f4e8f7dff4e4ed,
      4096'h8c83add4e2bf29f0075e2d7fe31a0bf97fcc8034e7be8007ba1abcdee5e82b7f06480780fcf6a44084d86f007fae3a7f1656edccab20e110504af93ac79a8058e8cf8a51467620ceac477d051c368d466417108112ded9663bebf0d23f0d9c0566ad25b8571c2dd9bdb8f0dff2733ae9f09bf9c7242c13800342977fba1cc22ae925ed211becf5dfe8ed0312f20123f528ecfb2f07fcf2df021708f5f001cd0ce31db6fdf0ebf0f419e4ef0e39e2d0d9433ff7ee1a01520119f108feed07d7fb110d092bf8083416e4f812f7fb15eb2406f90b05f73c180101e602f210070d023ad1ed21162bc9f5e5ecdffc18e71013fcfffb111000daff2422e619cbee1b0cbbd5e7d7dac10bd09843f37f4e3204ee7f1c09e312928062d56825cd8c8dc60a0b0ca4413671143507b711d50245fb5a3c3523e9f9ea7f50f7e4feb6beba802d08ebd37f5c4c34eedd2f5c06ce18d7395113edd1eab4b319071007c3d40ec2ec5680cb807f7fe7ded0efb409f831f6e1f333bbfb12e54480fad1be3094238fd6f10e00e4eb1ef2f8def9d0ca05cf03eec7f912e7c1180cd901ce17d807e1c3d1d5cdf4fbfbd905daf6e7dfdacbebc6ebbede04e8fef103e2e7e80bbef217ebeceee306b6fae8cf090ff4c8dae6d3ffdb0302d806dcd3f8efdc160f07d01a03ded70bcefad0d7cff4f7edc60debcdf1e6effdddd5e1e1f1e8cd10eac4f6d8e9da,
      4096'h0b07141005dcbfb20627f246ea6a1cbbfacdd27febdef02ae34ad8f440e5d711c81404af02f8eb13eaf3eb2221a5ce09e731f4e0001b497c1bc0e70419cc1315c007fa3115e7e829ca6c23dc1a1a0425022e7fbadd40d9195cde10d3d2d608396ae12dd33b26a3d8ddfc131605a9de3303fb047d272c57ee2b1de409103e3130d6d7e8b0d1d2e2f1d1e5d5eedac7effbd5f0e2d6b4cdcee4c6d7dfe5d6cfddbbf3e1e4e3f1f8e4dce4d4eab1dae9d9ebcdd0e5fcd2f2d2cbcae6e6dbdfcdebeae0c0d8ebeed1d9d0d3f7dcefcee0c7edfef49ed5d2d9d6d6b8cff2d4e4e9d9ccc6f9cbe5e5d1efe5f4dbc0f8dbdef9d607e2d1bed8dc04dbb8ead7daddc2b7d0e9c6e7cfe2ce0beafcf406e7f1a4d624d7d3dfd6c1c5cef6e2bfd0dda709f6e80ed2ddd4f80ce2e3d2c7f1cacdceeee9cb9fe211d3f4ccd1f4fcc0e3e5cbe0f9d8e1c7b3fbecd8e2bbeac90dc8fccbe108f791d3eff9e001bdc91cc4f5cdcdc2b0cfdcceebed0fd7e1d9d0efe5fdeeb807dcd2adf2c81dcdb8c3fae3ccb88cd408e2f5ec1ce005e2f215fc35d3340ced4ac6de13f5fdbb1be3fa0af3f9e50829df24cfe2fffe182be01018f5300f10212a18fcf306d040ee02fae22dc1dcbd4703f5063620380efaf25514ed040fd7f0d92b48e013e800fc09ed06cc05d9dfff5ace20f2792711cbd9d7f8022728280a0603f94c0d08d2fdeb10052bad1a1607,
      4096'hc2c40dc0cfabf7faecceeae2a3b29d05c4bab3e6a6afb0dec2b1babfb6e2f3adf9e2d3c0ddf6c9d7c8bdf0bae0c0ddfac1d1d601c8deccc8f0eeacc9ccb6b6e3c2c9b0a9dde2cee2b9ead2edadcda5f9e8fd99beedf7e6e7a9aaf6b4ebceadb9b4c1c2b2e8e9f2c7d1bfbffac5fadab501eaaac0d6dbfec3abd1cfc7c2b79bbce1da07f5f8daf60af6e906fad6e0d5fdecd9dafcf4dcd7f1e6ecd5faeefd0bdd0607f2d4f1fff1f8e2df0be2fdd7f8fde2f7ecfae1f1e3fa0006c9fbe8dde405db01d4eafefff002d8eaef0be1f6d7efeff4e2e20ffdf705e7d5eed202cce3e2f1dcf5dbf80307eadfd5fefce805f0e0f9efece1f6f6f5efd0f5e8f8efe1cee7b19b1416f4187fe71bfef94a013bdaf95713bc01fdf3cb18fb7f9fe09a01d97f31724e8042ddf8df1ac1d6fc9680ad7fb9d72209d33aefd87f42110f3de7a43db0f3c301fd76de38a1012472017fda2603d9edb0340cbaf1e99bf5d31e10d5360efbd3d82c29d50b82bd12dfe6f3cadd14d7f3fd7f00fb80664be574531b03cae20c083c6bfe240d32ea220bd236f50916dfe310f1f8f6e7f3030421033b2d15153bdff1e8eddd52e702152130fc36210d00f501e9d519eb30310428d0f0f145e907272ddb3622f0f7202cf91134ff04fad504021ff74e0e07ddf6fd20f3152524d754fd2a2600f205df0e010dffe2100305171332fbfff92e0a210fcc1f1551,
      4096'h11a52d41780b4f613cc20411c7f20bdf28c4c3f1e213be3eee52c5310d3c0c7f287fe391b6bb0a6df607f34810aed5540813d409d03cf8156be0cf2307f8f07ff6f2b00ac47ff220cac4c01dbb44ec05f6b2e5037fe26508e0d6e2e91502fb3b20c67fc661f332e087feed294b32cdcf0e0517087f113dd671683d14fed3ef18061ef615f20608f517080c14f303fb051a190c2518ffed0e040205040614320efd0a20f4f342e807f614142321012c312a1bfd12fc100e2f0d29eb13f104ff2a0d0419231138fa24071b2f23f4180c2b170b0d0bfc370f23040b0f0718f2fff922ee16001a3137fef80cf6e31136e30d0709fd072c0dfd050b1afd35e804f002f1a9f45b7f0c7fcbe0b8f2a7c5cf80bd088dc303fcd7f241331ad04bec7e8a56f9424180fecb39d72ef7157fd7900b159c2e21dfd77f16267f20f6e37f2aba24e40fa5d91a2e96fbe513bf4808171ffd98b82e047b117fd2b7a008e8b6111112e6a776fc50adf22480ce1ce7eda2ff0a0bdbc6a47f3fe3037f7f08e448e63838c1b4d2e903adfcffbf341872991e290e43bcbd1ed9b780cada04bbf7c898783f23618af2b805ee7f9dcaf2fd64df1d48f2df2b19fdc42e1426a2f332c3958069c7d9c163067f3dd4dd6a04fc257fbd05232e4bc222bc24d00809e3c3eb27bbfd3f8012bd7f6401b7acd8c802d4431ab509efd5f9ed284898ea46ed528deb0d09,
      4096'h18830b2f7ff44219e9a9e0d430d09eecdd80dfe28014df08d830dfd9ce2db67be018b480e080a00ecbff087f14800864baca21fda8c7f9d75230310ef20dae54d3f0b8eed636aad5d3d3b35a4405018df9c504eb7fc36e18c7e2ffdfe21a0a36e7807fad37caddc98002f19d1928abefeacde38f7f9303007f7f061dead7ca65660d280d0830fcd90cbab48051deef0c80d655f80b7f7580428f111c0f11f8cda9cccb52be9ad5d61552f412801c14a69bba03dcfca8dcb8c0e936dfe5595a80022b77a5b89d800b19bb80de10f13fcfa6d70b30cbf54c1f8c13e645d13360068040d127b3dbaf08e8fe1ae10bb1e249032301cdf50e0b55e1f0258cf2e7e7cbcea6fda1c6b2e60ed3d9d1e8ca9e9cfdb8c7a7c98cb1c1cba39eccdfaadae4a20fcbe5bed1ead2ccdfb5e89cdbc3d9fc9aafedefd5e4cac5b6cdacbadab7c4d6b7d8b0a1e7c6b6d1c1facceea0b69beaf2fa8fb3eadad0ef9cc4fcabd4d5b2adaecabfb0b2e4d7c790c0c009bfe2e4b0fdd6bda6b9d7f9b798edddc1c99e83bce0cee5babdabdfdac306c905f2c6fef4f0f2c1f3e7b7c906c3f6e7d9d0c0ced2ead41ee30514f7dfe7c0ebbfdfded5d9e9ebfffce711eee8c8d7c7d3fda8eadfedbcc5e702daf3c9b619f3e4c4cdb20eff0dcfabd704c7e2efc70595d3e2aec7cdf4cbd9f4e5deb3faefc1d9c6e915dcfee4d0dfcedb0fcad5d0d1e2fbd1c0dc,
      4096'h0036f1e7092ded07c4b505cf522933000a182a3b26373ee10906032435f8bbbb3e17dd7f0fd77ff465df80ec157fcea6d9f3ee3c3ccd2c48fcc227ab490a3230d70f50fab4f7860029d1fec3cec7272904fcff1afd3f080429661c47dd0627011f3ada54170580047fffd54720901fe307750231e6effc65f0e424ea35d5f9fdd5d3fbe8f1d9f7fefad6f5f5c6d5bbf7d0bcd2dfd1cbd2eed1dcd0f3d4f4f7cafff0e3ccf0d5dcded0effbe1ebc6f4ffcee1dbf5ccf9daf5e3f4b6f3dfded4fbc7f5d1c3f3eed508cfe5e40ad8d7d0e2e3f2d4de01eee6fddecaf0c306c0d2d1d7c2f4d7d7e9f1dcd6c2e106f1f2ebdeffe6f3d4e8eaf7f3dfedf1dedde2c2e12a4c000ce823c532f8fbc3b9000b19011a313deeff202ce5f1a7200f230233aafeed106ae60202073935bee2fd5efbeae2d207f620c9eb0ebed835f1dd1f1eda270745fdf9d5ee0e27210032ecae1d9d0b0bed2604e8e8d21d1b0d3a27f62aebff10082cb6ee0e1d5c2117e81d33deeef31e17fbe4fa0f20d8a8f2d1fa0110e4f019fa0bf622fd130ffcdbdb1dfbc4f0e60e1eee0b1d0ccf280038fe180dffeb07f102280fb4e8f51724dd07000b0398e8f40bed0c02e2fbfaef26f9e82b11dc1d1210f9fdd7f8fffbd7f9e807e61ddb02f7fb1a07e907eef91f223503fe2209ef13f524dfddde130ced1f022ad70d0705fbfefc09ffec24fed1eeebf5071f04,
      4096'hf1000df902fcff0505f10902f9ecf4fef3fbf7eef7f5fadffadff8fffe0104f1060202f8f4f901fef5fd09f2faeffffeeef7f2fef6f8fafdf9fe000007f6f8fafafdfdeaef03f9f701f10301ef05fdfff7fcdd04ff000a01eafef5fe09eff7fbf9fafcfef6f9040303fdf9f6ea07fdf1fafefee2f5f1f8f3e311fffa02eaf5f5e7331cdd133f1505eebff7b7360c0b0cae40150808f92bf81b0a3fd6d9eacbca12ec2723faba4cf060c1cbfbcd07e2c2d109ff145016041a0cf4119c320d021c041515dfe3dfbb29dce1a009ec9305fc09dfeb01fc022afad21902fedd0f00eef123e004cff6c91406180c1c13c21d09fa56e6df0fd441f029e52ab431a0d3cc064e160d303be3191eae1d80e6f1dcf4c81a21ef136e7fd807dcfe077ff6e1b606e751130080d4bb215be20f35d6e5bdff17ddf21f00f700eed8fdf313447f0ed8300ffe98cc9d7f2583e4fa11da5e99b8af2b53342622ec0218ea43f3ec3e14d17f1c7fb1e3cf33ed055c1c6eb6161201cd4268e53cb178e73e4abd060243ca4c6d5852fd27db68cad13580eb1a1c809f2040a026197080bf8033ed3813368026270ffdb7c2c925c97429f7e7ff6918c2800fd3da81804c89e94250c1737f27e9350167d5d4803535b62e75c0c27e830fdbfe31ddb5f4da7f7f08705cb14a372a3826368080de133ef07f4a16b0d732fb8f70ddf8429d74ef83e501cb3a3409,
      4096'h2480f79dc71559ef80f0026a7f1930347f6cd517f4c5e8280c7416fdbceb80540cebe62625ff7fe57f92809dfe7fb247c6e60c4c7f3e23cd13b92dac4702b94e3fd28710cc40ed2df0c4c3c5ebf605f160f91621f284f039a2500b298b5c1ac31c38bff17dbb80e7a329a93c18801629147ff264e3e10ecefd1806167f99cbf00bc20dfffab22ffff90d1a7fe500121448c28d1c2093802acd74caf0c0f4023ce7ffd2bbf902210ce1b417e7f8f2f87f2745d9f30efb340a2e29b50c06b0803aefef9f082742eeffce25d603ec1dc3503ffc02ae1008f61709d1e2992ceaaaee1280098048440fd7cfd3d7f9e63819e60ae4cb0330f21180232e081fc3ffef140f0a2a3e7f2e411444e22b13e7440d5832c02d0c3435f9bb03f41e3b5a485f403a7fcb21b8d60c69cf4849730c1338342315ea18ec02532a1c453a77c249df7fad1c401c9e67e77725f8d855457f211109ec1e377f0942031205ec1c37fd471e2e9e7fed4f086025face1bdb55010b0cf72823366540740b4b332d4ec17f107ee9f414f228f23ffa53323bcd1108be07b4e7cf3e038058b30618a8270617f60fd9dc7fa05db759b25694d42e9380eaedc2673f13174dfb106f6bfdfe7fdf7fcc1234c1962288b31ac0ced424e7bbe54f055e31f227797c21f9ab63c142dfcd23ef7fbcea801f062ec739fe031df11329040a240c4e95acec1f4424f67f1af7da,
      4096'h260c0145712401d907d2e1f80bf3e7ec3ce8f522fb1b0ce1f9f92e041a210117072fc115d3e4cb54022b785411e51f171419ec03fdf5f712df4b163ad21b0164ff0417f0d76b1ad034e1f84e096d16eb0de51c0034052e0d0f22fe210b0626161ad07c140af80704b7130ee32f17d01b00d513fc26f1040e372319f6e11af822ddf7020befdc44d1a04b2a7f182c4ecef1fd148923c0297f087fd8c880d8807fef2a7fbc707f7f375580fac290c480f2e034307fea7f3e077fc927d77fc03c1436f680a96606bd989c7f80ef006ae422ec7f5fdbe880cc0e804165a98033a814ed170ee959c480de10f680a1fb8031d7f23680502f96fce6f91211cc7f000d06329b56f97fa97fbb574112bc0872897f2cca90ebb4aa7f7f1b7fd9680d49807f44157f977ff47ffc7fa12248eed28024807f7f7f6a7fb25f7ffb5bca7f117f02bd2a00807fda800a120d801e48e75eb7107f7f961da67f7f96e37ff58055b5694a7ffdf26113802c807982e9e3807f09037f80397fac7fdc7f7f5cd77f80e43a11ecf2d0cc14e8e4ddeeafc00d9eedf5a4100fadc4060fc9eab617d404ddb4d9d9c3e52900f100b017c4e6caad17b8d28dc7f5f206e9acdec9d40dafe2f300d3fe03029cffc4d5cad4e3cfd4d5b9edd701ff92e7c7bbeddba515f811c30aefa0bc0cc3f2b3c4d9f1ee05cd070ac7f3d4f10adfcac3d0f1f1ceebebbcefc686e1
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'h0a0204fff7020bf606f6f801f9f60dfef502000b1105050e08fef4fdf8ee0602eb10ff0d07f7fffd0b0902020107ef0a020df61405fc0005ef01f6fd0705eef7fafefd07f00903fdfafefaf707ff080300ecf607f606ff1501fbfcfe00fe09fe0afefe00fe01fdfbff0dfefef9f1fcfdf9fff9fe00fbefec0406fdea0009f8fe074811e1dbeb13ab21182deaf9dcf009e6d560590606802008e0fbb743d00b3913411c00dbf9e2fdfce6e7ff61c92b4fef2c0c3649440fc77f00e96c9238047fdccded7f08fd80ad89f88012400560b67f26318004b9f780978fc0ff80f78020d11bc729f1f7805580128fd88014ee0b04f8230515d5177fcfa3df80e380951d04000216e2d60ef4e81501e1ebee16dc1e0ff45a0df30a00feeec2f8130602f1d40b12f7f10402f5f707f9042bead41eff03f20926fb03d513f0d5f8f61dbce5fcfdfd01fe30efee0503010111fff9fde2f9defffd00fcdaf5f80604edfd120419fbff24ff03ff080a010f0817fffcf90909f10a031c0ce716fc0602f3121511ced9040510e019f319b5b1c8e509d737edd80dcbd4070440132626c1cd00d7b9e406140205c423f4f20efac3dabeb0cefae9e3bcd8d4fef5acf5d5fb090d281705090be7c080f3e6e50602e7a2fc04d3bff6fedd0ae7029ee407e906d0c6b401cc06fccd010be5cadb0603c816ef09fbe409d3aef700ceb4d6deda0fe7aeecf7,
      4096'h0c1af6f5e302f7f108fef40610ec09ebff10fb1d01fef90e05fc03e91cfa17fc0b07fbfee209ec1d0c07f90f080012140afa030c07faffe03006fe16f10a000703fdfb20140bede4d502c302fe031b070f06fdf300e1faebe8f50effde01bf06ea0409fa0003b125f9f1c8a8d10efdfd12041311fcfe0a190cd6ecf0fdf0e1ff10fb09021b08101714f2ffce06fee626f8fa0eea9ffcc80a080701d81401f6fb0600dd0528f40dfd01ffee0feddeffbbd4220ac9e3fa06410205ea02e6f8030bfa04fdecd1e9ec08def9e0eed603ec16f4f0f2faeceffde715ffeffbede7f9eed405f3eef4fbf2ebeaece5cee1bdf704eb03ced801effcf5f2f5ef10e2ff0ffa04f9fffa0307fb000101090201fff4fbfbfd0000000df7fcf90002f801fcfafdfdfc07fbfefaf7f903fcff08fd0106ff0203060afd0400ff03fd030203f6020a00fe000dfef204f7f9ff030101ff05ff0a0201f802fe00f503ff0400fcf9fdfdfaff0200fd010100fe0501000300fdfafe01040101000206f6fe05f1fef7f0fd07fdeed51901f60a05ef10e806fae003f3c5031bf01cc40cd60910ea13e0f5fcef01260501fccae323f5ef1f051706212b192c1f0e2200fdfaf8e604eaf50c33f8f5fb22fdea06f0d2020d14fdfd16fb12080fccf304ffeaf6df0f0103ffe501d702f60df8000403ffeed40aef02f8fc06f903fffeed0612f0f904d203eac2fb,
      4096'h1d1b32ddeb01d4e60aed092ccda90a23c7410cf80ad0cfdb03ee18fe3cef43f320cf1b3ccdd51b0de34f342703b4e4d6e23a0f190b3a0a08240ac6cd15df131efb02f8f5b548d20de301ecd3090a80ffd4c9fb3ce401fe4d3c0dfd071bfe59f629070224fffff6dfdf0bd319e180ef060afd00d904dfbf9a591fd1dbe235ebeff72f01e91eedeb27f2eb2a03fb0ff51e08fff5fad51ec8f7f9f80ce318fcf70201210b012af9fc2e0508cffe0afc0ff9e319fa0dff09ff1a29ff172edb00fa18fff4fe17fb07dc07f4040010ecfcfff509110fffe8d203bceeeceafad1fed4040703eae8f7ffc0faf804e1d9fa02fd06e6fcf506fffa0117f2dbf5f5faf4fdfffefaf603fd0102f70000f6000903f8fe0afbf0fa06fc080502fd03fe0505fbf8eff906fcfc0902fcfff00203fff7fcfe02fa050000fcfe06f401030403010301020102f200f70406120004f9feff05f9f800f4f600f501f4f6fe0302f7fbed03080002030201010c05f816010d0802fdfc01f500fe040c09f5f9090805f001ffffff02c410e9e0f907e611f60202fd0209e914eff4fcf00af8010d02f4070ae614f71c020e01ffeefa02ed1310f311e50d10151cf10d040e0a0207f212fc160b09060527fac511ebaefffc07eeff00111bfdfdf810fd0300f2fdfdfc14000d02d5040cf1050203fffc05f8f4f9fb0a00f800fef205faf3feee04ffdeeadfe500,
      4096'hf0f4f2040400e6d001e8ef030f13fc0804cff6d0db19c0f5060518f50e06eff8eae402f8eb18faff06ead908fbeb20d5ed051f06ed0f07e9f4f10b0801fc260dfaf0f6f611b5f7f8e601b715cd040dfd2b09f8cd0afbfedcf2f8ec02f2c7e7fafc03f4fefffaf1e0e0fdf1d9db0002fef1fff5fefffb0934f2f4e9f5e9e8ea0710a600f5f2f9b6d4a11c1d48e4f220f6113af6cf47e429e6e3d3fb23c7e540ecf3ab25d4071bee88f3ff5544e81cf0801be742dc1b1a0318b0153cbb2bed29fff115fcc7cdc8f6241b030ce3d90694d9dcdbfc2c04ed07f32a29d1f7dd20c2fdf7080ad80503efde0ef518de0dc5fdfd1c0dc6f4fefbebb20008e122050f18df5226efadcccd843380cf6c0dcdabfac4b52bc5a12cd4ccd4e6e8dfadcaa2050d42fbeff69fa62429cd57cab896ebc6c5cfc5e820cc0af312400debf5c8870212e4f5fa16db55fa07eff4fcae06fdd8f0b9b7df030cf3050814fee3fb0a2d1afd0b04f62808f6faf3f5e300fdc2acef0d3003f5d7faf6f103ede21006fa43ece7ff0aec0d0ad41722000bff21d71112121322da130e0bf602ef03f5fdff0a26f6ea48f80319192f0205150d0c23160b290ce3ecf92e0efa0a1dfc0318f71aece5feecfd14fee2e9f2ed00cf0c03fb0df40c22fde4f7ee0494e308dd01cceccdffacfdf6f507f7d8dfdef8ead3e81903f2ecf601010303fb0bfcc9dff4ca000c17,
      4096'h29d7061031ea0410e00efd1b00fcfd23f01ae30216d4f5f8f907fb0a03ed0423f71209051bf713f1212805162a23ffded610e6ff12060716d9f2143fdafc08f301fefcfae9012fdffffe41ba740719efd4debed7fa0602bae0ef38090a1515f420fd012ef9091c3927f7133e300efecbdf0cc2d6fdf1faf4df084bcc25e3c8f8ecd8fbfa0ffa0b09f8020309100ffa010b0307f906f00f0c1af802ffdffbfceb09fa01f90c0415fafecff1d7b029f00708f3f00aefd40223f900e5fa04fdf0fcfefdfcd5fc9826ede80002d8f7fc1802e1d4f3dfe802fd22fc0005050bf50cf701ff0df3f705fafa1a06030307e7f7f6e003d40101f1e3e5c0fa0aed09afa9eeedc4fd14f5d3f89514270531fd3313baeb1debce7f2b7f23ff2809fabd0209d1ea0350f50ce9e089e2f425e906f8b5213bbfd91f03c100f9ae121d854f05f3b3271b27d6d7862e05d003ead4be089ce7abd7bcf30e1d05d3b623f50afac5f3f2a9fc27c8181a2a0c1cfd16e3f8e215f3c910addd0301e3b6ef03badadbdb10101e55fcbbe10d2af219377247e9e111bedcecdd2035f892010f00c2075fe310dedd4d0cf0dd0b2d2e1100e5ee190a3b22feb9cb09010cede07f06ba7ba211c5f6f2f2e60ae3cf80b980f380f18109370b7f1df2dbf5e5f3808bdda1f7b9df801ac3f404f4f2f880dd9303a0839f0df9dbe3091ae703dfef70df8dbf95de808020,
      4096'hce3d0b1bb3b259d92df3b9e5f700008dee0735640810100409f8c1d0e02ff7822358e1f7e4180e1607d1db8026fba57f2bf2bf0c2c9dedb927fc80e71450a6a9fdf1ebd6332dc23423f41521e2feb2f2f13106fdfa12f9801cfe2606d30980feb502f1ee06fb02de2116cfaad7e3fe1d16f00a0f051610001ddf0b42db212c1bf901fb04e3f805fb0005f504fb0208fafe0afb040c0c040305ffecf7f7fd03fd040804faf4fd02fe0102fe0006fcfb0c02fff40707fbffee0d00ff0301fde9f8fefcfd020500f2f90200f9fc000007f80003f8f9faf6ffeafffa00fdf4f9ee01f600fefb0000fc01040701f8fe04fe000700fdff0004fcf804f903ff0305fffc18fafd01f6faf100f6090716fbfc01fbfd15f0ff11e901f6f802f50afbf6080400fe270000f6050400090912150cf0f4fa100111120400fd07fe0c0c08f3fa01fb000017ff02f2f5e8ff06fd04fefffbf804f8ed0301fce2fefc0afeedeed6f6eafffceafefff4fef912fff0fcfcfb0202ff00fb01f60202fceafbfcf805fbfe2880e7217f7ff13e7fffb8807f62a42ee8807f8080e48028c3344f9051c780639b8080107f014b80771ed6fadc48778080ca18efdc64fb7f8000340680e97f7f15f6fa808080e40246068afd80f480e38080ecc3badedd806214800b9b0180f5e2f401d7fe049cbb9cf22a80c8bfcd05b1f298b8f7bfcc8da4a0e47f021c45db,
      4096'hf7f4fc0305fdfef3050305041013f5fc1df8ee0501f815f50703040103faf7fcedfafbe50612f3fefcf7f900fefd0dfe12f107f8f803fd00f0fd00f901020307000103070803fbee0e00fe0709fe03fb010affec04f501f6f4faf9ff030afaff14fe0203000006fffffd0506010dff0206000407010e20140300fc0407f30603020202ff01fafe01ff000201fefe0402fe0200000001fefcfd00ff010101fe00fafc0102ff01fc020002030200fffefefc0afdfb0100fffffeff010200fdfefe000000fe000cfcfd04ff02fa0800fe03fefef900fd040000fefd030003000600feffff03fe0000fe00fefe0402f9fffd0300fcfb0000fcfa0801fff7ff0701fe030cfdecf701fefc01e912edfbf302eaf5d2fdeec205fa08ed1ceada08f1f9b1f028fefafa03f8fef805c0a8f0f9d119f30703f3f80efe0fe0fdaf3bf8e9e90dfde9f905ecc805dad406f7f0da0138edeef5e0b2e8f7fad4c7daf9fee2ced31415fbf511f400ddfeeef1fbe10605fce9ee00eaf5fee5fe06d7cef9d5f6919f082cfaf0b635fdca40ffe5dd0d1917d32ddfe87f09f11bedfb09e20de4e5cf16d740c91a0132e805efd6fec8aea3253fd6041c2006b03ef552e504ef1622c60350e8060ed0bdd8434b0305f9e6f5f6e223c1be0a28f017073c3c01f90b29d33fea3fffef05010109fbe715d81fe9b1f90cd0ffd7e200c2d0daa303100bee91b2c8,
      4096'h18cf258280e022247f8080d272b3e1b7018040e3c7ea7ffbf5383989d57f07a672db96ec4b9877dc8018de80bddac63b5cf0def6b9052dfeca0680805f802513fc05eaa68680ad11b00d8013800380b89b80edd9c3ea018069da80fd99b180018010f6befdf1f98280ea80809b9b131ab705a9801a138080a40c80509b0126f2fe01fffc07fe050602ff00fa0100fd0903fafe00f405fffefb0303fa0502fd010006f90103020702fefcfbfd0604fd01fcfffcfdfb00ff0a0101010b02010403ff00fe0403f4fbf7fcfff9fff101fefdfffe03f7fffbfff2f1fd01fff2f9ebfcf1fffef9fdfffafbfffffcf3f700ffff03ff000200fafffdfff4fafcfaf9f6fa0a0dfae8fbfbe7f7ddd8f8c4d7fa00efe8dc1be8ba14c4e2e8feeff6e7ebf1ff020ae0f800e10218e4e4eedcf1c6d9fac008d8bcf5ff01fd13fccafbdbd8ddf3f306fc04ce01d5050a05e602e5fac903d1d4ebfaebfb00e1e8edca0ad7cde2ead0f7fcd8f804e8c1c9e3bae0bcbffa06d5fdebce01d9dacfebe7cee4dde5d2fbeaa5d9c9760f285efa000ae32c25a709faf117c5e0b81209fb122bf13608fc05eabc09c823272df6e2809f18dc3620c0dad508f9faee071dec02cd46f3f8f87de0ed0dc6d4c755cdd5f70c801a0b6fe7f89180abd5d20e35b9ee15f821be32087ff9f135f304ff0fecfffb3c0205f5dfd813c4ec0bfce24c80f536b2058080dd,
      4096'h39bc72e1801e18c38016808080807f8080048016801b8080e3e680ca80802fb1803b8004808080dfcca07f09a72e80bd8080807f4480df9a4ad5d8eb809d8080f4f3d6fd06517f107ffcc4da1efa801ea7c0d07da3e5f47f213a9df01a341a0c7ff4e323f4f5d9e5d245a906ad80c73189d4d74cf7d8a01780eebc08ed1780ca010c00eff8ffe5f705f3f9fa08fbf8f5f8f00b07020fd606f0f30ae706f8fefd0dfe02fdfdfeefed0df4fa06fff60b15110c0714fc0dfbfa01fdf6fdf807031dfffefd0802f406ffdefffd08e6010e050a0207fcfe05fd03ff000bfe0904edf902fefbf9fe01f5f8fe08f103fcff00fe07ff0501fffa0304f8fbfe0000edebfc7f51ffec9d27c8f1c71c7ff9c6ca192f9fbe170957a8ac0028e9df2b04c5e91715e4530fe3b415271e6dde26e90ff7bcad4d011f067ff3fb650b24bfccbbe1fe00fdfd02196aa9f94cfe04f2f506a1c39de6dff9dbd3f8b0fdf803ffdc30040a140bfb43fef7eefbe0e7eef1ecdb04f34406b0eb01e5f6e427fc04f5c52210191f7fb6f1180642d424b7277f47d9f1b8ee35a4477faa9ff4cbe1eb117fdb2bb1f94048c4cf15805d1bdd0d5834b335401423f87f7339f0224be0987fa22fd37fd892e67f7ff8bc8080f91857b2027fec7f591f80e0a9e0a286a403f2802b800efbe5e37fede380e7e21da9a22176dca40b940fef1bda387fd880e480fa8080fd,
      4096'hf103ff01ee0201fef8fb0307fc0afbfdfefdf60705f102fa08fcfc080200fe08f5f8fbfbf01106fe0503f7fe020a0dfc05010305020901fdf900f103ff00f5fe02fafe08fcf4f4fcf000fcfff3fe08fe08fb01e9fbfb01e2f6f8f0ffebf8f100edfcfff5fe01f5f5f6f6f2dbfdfb03fbfb01fb02fbf7fd01fbf2f9e9f4eff1ff2a4deeb164fb4711359206b929e8ede74703f20ad17fe73d0225efdb4f0eeae04e7ff91f62e1d20798fd9a8efb360e7f1f0be2f12f1ee51c22fb803ecf19cafdfaf3e27efaa108f280fa82fadef270257f5ae4a20a2cea809004b9fd801b80f5af07f0d2f2faa6ebf2f08e85801df4f4eaf311e2feea0367e1b1df80f4e68b2cfef60300f7fcfb03f4ff0004f3fc03f9f40cf3f70afc02f902fbfefffdf107fef8fa0001fff2f8eff8050505fbfef8fcfff7fc0cff00fdf4f7fefc0705fdf9fffc00000205ff060202fe01f3fffff6090600fd07fc02ff06100002010001fbfbf902fe04fd0004000401ff00fcf4fd01ef00fefb01f4fafeff07fcfc0301fbf8103d32fa061ce616dd00270ae50926f0f14bfe0413290d0313e8ec12d1f7fef628ff25430ced24071b242319ea07dd1205e4f1031efffa091bfa030023fbf701f901faeabcfe1706fb0100b72c0080fde2cddb34e91c032d0f0cfb051ff25cf61bebfa04fc00ff01f420de21fcb4fc00bf09f0ddfcdbaac8f806f9d3f1f2ddf5,
      4096'h80873b7f81517f80ce7f80808080cd808080807f80808017471e807f7f80ab80802a80cb8c8080d180807f7fa38080dc8080807f7f8003807fee647f80048080ebeae16b2a5f7f097feb7f0d7fec009ffd4e7ff9162dcb5402113edc568047585b170f1308ef367e5e7ffb7f398008649e0a4861cf64d7f2540b7f03482df13a23fc01060102e4fdd9f005ec030401ede2031fdc0409e8dd01f1f410e3f0f82414c61708fce8f51703200103d616f9d3df09fdcbe5050101fc02fddc19d905f5fcfd01e1e5111af4ec061fda2500ed02ced8be02e409fc1df2f009ff27ff33fe19fc0031f503fb170ffef51f0deff8e7f101bced02faeadad91816d3faeae5fdb780f5b88008fcaaf3352e26de344c805b7ff4b27fd36ebc1dd5f342806018a5a9023fd080df80c99f805cdf81e680577f805d27a3c60ca680e558807f03fa0bfc1c0e8010f2cd4f2a11d2148004803d80236b0dfd1ef78155fad8f1bd258008801312f0070414c6eb4b1d90f3ea115930f249cc0941038048caf87fc6507fe90206ff01fdfdf901f703ff01f7fd0afbfa07fbfffffdfcfafdfdfffdfdfb000000090604fcfb02ff0803fe0903050003fe09fd02080201fc000007080002fbfffeff0001fe04fcfbfe0000fa01000401fcfefd00fd0300f800ff0000fe03fffdfdfffefeff0100fbfe01feff01fcfffd0502fafe00fdfeffff0200030100fffd,
      4096'h220cf9ebb3e4b6dabffc17ecc6ddead2be13f30510af8fb6f4e7d8cd17d50e1924e41dc6d5edd7f1122bf81efdd03cbcca331e19f7060dcf20f2eaf9e9dff632fdd2f43d022a8db7ff0808fc16f831e40e15dbdbe3d5fbf1ece71ef5f1f4f51721fcfc3ce9faf52012d808121427f2db1afefbf2f80509370cd214c82ee4d61a03e7110ff6fc04f30a110808f1081108f7110514fe02e6fff7ffd8eafbf2010fff0600100807fef3fd14fce404ffef1df90df5f3040101fb0a04ecebec01d7e001fc0108f604d01107fdfe030101cffbe6fef4140300fdee020ff704f10ef404cdff06f102fafcecfedbfbfe01ed02ff09fdfff705fbf9e911f9f70df7292b0efd2cfe05dafde0d2de09f5b900c7e8e9d5e20ffae8e080dec6f3ddc7edede90437f9fe0df6caf82dfcfb07f8e8d80400d014fd32eceaf6f061f3d5f58ef1fa25ecf3f5110a49ac070a00ecff04fa0ddd110a2eeef4d4fea614f1bf01ea24b6050407f209f1f9e7f0e2e7db10be03ed0f12fe14fd070526fc0bd80421f51ad8fdfbe31203fef4060c0ffcee08f0030a12031efd1226f60c10f7f9eb00fbfc06f1f3ea090f03f90ae30d07fb0b0806dd0209ed020e04f6fff6ef02fb0110edfef3fd01fb08080fe8090700f5fef800f003fbfbf503ef0301eaf7f0fa01f7f7e6f70203fa07fff9f7fdfe0bf104f2fcfcfe14f2fceb03f9fff6fdf3fc1bf71f04fb,
      4096'head5f40be00ff7c0f906e600130febe0ffefe9f7efcffbef08000c09f2f0eef3dfe9e1e5e302e9f4fad6e6e9ce0807f700ea07f0f0f5fb00ce0327dc15e106f5050206d30a0de7251fffdf0ea705eaf2efee070408e800fef40dceffe1fed3171bf7fbdf05fe11eb042100d6e409070411fdf804031106f01a08f222e2282bfe2280feda6cddf9f51cb5313a0c45fa15f7246efffff5d61f4b001c22f9fb011c1e80c6237f967acf2d291a0fa41cde8bc2e3531bb320057fe802e2a447a34c25fa1617b485951e08f106efbdbaf793ee8095c802aff511d94d06e708fdd7e5f0d4f9eeb9f2fd36ccf919e9c7bdadf00bd40280a7f799e7c9a601ca63d3223bec807126807f450d12cecd228010ad807fc280f88080888015813620807f9f80f92436f420090cea7f8d298080e42e73958032cbdd8027f6227ffd9f628021637febd4e98ac39350f31afd0c340a0c765ee71244802e15e3869debd61724ff80e92b22e505ee06eff0daf9dc24e359fbba090726230ede43f3a9dbe9bdd780a21bf6e913f20c01f508fefc06f3050b020bf9170bfe0df9fd11f600f9f70406fe07fee70e0210f7eff7ec0308f6ef0dfbf1fe1909000c1d00f7df00fafe0bf4fd19fffdff0ff0030bf7df0200022701f3fc20faf1fbf4010128000cf5ff1afe4b081700f9fdfdfa0300f914f62500f0faf7f900e2e9ffeaeefbfd26fadafcf1d1fe,
      4096'hfefc00f407faf501fef102ef01fcecfcfbf70302fa00ec05f8f906ed08f8f6f5fc0406f901fdebf6fffcfafffefa05090a080a070906fffefc02f7fcf8fa0311fffffe17fb00fff9f301fc04030115f9150803e802fa00fafafd0200fe08fb040301000afd01f9090105fa03f705fdfbff000101fffc050efafb05eafddfd7fe02001002e8f70a1404f9f3faf7fcf4e5f9f3e1f90b0e0606f20e02f4fef5fc06f50ef211f9faf90efaf5faf2fe01fd10ffeece01efea00f3fa04fefcdcedfefafc01fdfcf60c05fffffffaf80affe204f4f3fe0afa0a00170d02fa020e0413fb11fefc06fb0107fcfe05fa04f8ebfe04f7fffbfafdf5eeee0209f8f8ff14fc00deff000dcb1b1d0c0fe6df08f11109f402fa143d0b063e0426eccf01d50b0fabf3e9d6f3f2f7e8fbeeeffec408f1e44c3cfb0b09f7c3edc503f2cdcf27f8c2841401fad1f514b31a0504b207cd02eafaf608361c12d0f3bb251eac069afea612e607fa0406ecdce596cbc680a4ea030fffec0af10814f7fc41b2ee38c6262033091404fdec0ad3f5e50916f50e01fc130d030efb00f7e2cfe0e5090a231701f8fdd7ddedd624e121fee8f3f5f3013ae403fa23e5c71104e50e041dfae7200d03fbfcf8e10f35800afbffb813cafd010f1efb29f90bb8f8c20beaa6fbaa00c3fa0307f0f300f9d8eeb20fbac482fffafc11f8f407080b01350cccfb07d5f004fa,
      4096'h477fb87f80808080807f7f1e80807ffd807f7fddbf80808080b880fdf780de7f18bc80e98080807f2e7f7a7f7f36d0e2806d80fc7f7f23e07ff37f8880af8080e3b7d480807f7fdf7fef7f807f0280318080807f807fd47f7fbd500f7f7f7fe67fd8d168d4e258265e80f37f2680d03f8ce58080db808080fe7466801d7f618afcfa01020006030906fe03fd010ef7fbfff30f02f700fb000503ff04f0fffd050eee03020303faf400fe00f8f1060601ffff09fdf300fe04f0fffaff14f7000500fe00f8f4e506fcfe02f6f308fffb00fdf4fdf5f9fdff0d00fefbff04010efc070000ffff01f6fd010cfd0102effffced01edfa00f4f5f2e8fefef4ffe4dbfbbe0febf50f0af84501d816800b13eb1af4807cd78025d82b040c0015f3fbcfe325f1e5ed20f1511fcd01c1b5d0fe21d18b0419e4e264032e18faee032df60806fdfd00d8d7fd0806f3f8f0f70b06ce09c8e5e827f309f72213fff20219d6f6f9defef310fdf7fefaf715f717ebc7f107c1f6f7f2fc00d4b5d11b02ebedef10f50bdf0ccd98ef0edfececf51fe3cffebbdc21de0f410744e50df2a2ed92d203c2ea1d0efee8e708e819f60be01c15bf592d0ec126f9e6019f01f9dbd111dba6a80e0cfeffea1afeed3dfaf9f8e800c808ecea0108f9fcf7e105f2edfaf2f4ec04f0fa03dc0302fecce1efd5dbd4e40a0df6f8d6b401f3d0d3ff18d302c40ff201,
      4096'hfdf604000305fe0101fffefe0207f7fd000108fb0003fffd04fe0003fd02fd0708f6fe01fffe010105f2f902fe0905fc00f802fe00fa0000f00100fe07fe0101fe00fefbf8010401fc00fcf90700f701f4f6fafdfbfd000e01fd000003fe09fb06000102fe01fd02fd02fb06fcf0fdfaf301f5fa01fbf8f3f701fef2fbfaeefae5f6040becfd03f90efcd6f90502fbf50df4eb1401f10c0d04fee7feee0409eaeb1af0060a03f2faeff2f3e30cf5e81d08e7e91201e6fff401fcd0fb0009efd9fdff000105f80d02000206ece801f9ffedf0edfef6f7fdd712ff0801f4fad3fce90100fffdff0500070d03e00beeff070bfd0200fffc08f602fbf50a09f701fb09e409fbfe00031af7f712f5e7090411eaf9f6e901ff01fcfbf8fb10edfbf3fdf9e3010b090303fefdf50709ea24edd7f303fede06fb0110dffd1c0d0bef02eef9fafeeceb1615fc10fc19ef1102ed08dce7e911ef18020e070e0bfe07170dfa16fefd0df902100104fe031c0ff6ff02e8fce7f7ffe8fce8e70505f60c01fa02ced7f156d0093fde2df2eae3faf6f1dd11fb193115cf36fd6005bdfca514daf006ee06f8ed10cecceb1705cffdfec83b200adb22e0db04e4c30ad7c61d16d3a10d0404bef527fd2922021dffafffbddfce0f0e3315ea0d8f081db101df08cb12fa0711ff0df93aee1b00fed6110105fd0a04d607051d21eb1912d020eb2f3af5
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
    .OUTPUT_WIDTH(160),
    .OUTPUT_HEIGHT(110),
    .KERNEL_WEIGHTS({
      4096'hed40fa021a061030fd120a00fc0e1d000a01f913faf418ff00f90efbfb08040306100f170518f4ec18fdfefe0ef621fffafa09f543fff20a0b02f800e4f600f98ecd8038fe0180df80c857dcda23808080133aebe9eb009e8080ef80f4eef68080e1801fc0a1ca808080f61b80c7804ab13990b62d809680801b80e7800280220af40301f405fff91306fcfdfdfc09040402fbfaf7fc0704fc1cf807f902010911f6030001f00306fc0cf704fb030007f902070af506f8f4020c08ff14f407fbfef707ec00021b0b1005031004fbfc160ff4f4fdf3110cf7fc4afff7f51102fdf7f8030efbfe03050a01fa091301f602e4f5f40d0df6eeea0bee00fd02f909f5e1ad23332a0480809c947fe7e0d3fb8000007fbe4f18f6fe7f80ea9f368011e28592ee80e1808fd27f8c10c8c879a5064e0ad98080aaed2e0694a81d80291d2807807f08807f808078b6a5ce80c7ecc8e380b6804c80047f9d7f80cbf6ea08c57f80488080257f9a7ffcbb308075cf18bf15a6ec807f808037807542d0a263f68bd880043b0480b180a0caa780a1808080b6cef3dd00ef808080c9809af5ec8080b2809fb7afaa8080809fb2808080e680a7809ac080c4ab80fb809880ea8080167f7fd548170a7f7fc7a37fda097f3cef93c23452fcf19cb27f49d5034113807f0d4b5b6a7236c62cf1dfde3f4e446fefd480f27ffc76130780dc1380f3b2f6,
      4096'h888380ede60e808080b38083808080b580a492b9f52dea8080808080e9eae58080dd8080b9809a808080fbf180e88010d4d38080b380aa8080a980ab803a80ed998080c780e5808080a68080808080808080808080e3e580808080809d10f48080b0808080808080808080f0808080f480b580808080808080ca80ce8012808095c480001608ba0a80cd09092021809a80783b22e12a1611d580f68002f1f38080e280ebc5e3a680808044ea8080802b801194c2ea80d1c0805680ba80573afa80805af4e9128080968064bf98be8086d6be11a7211884b6703f8080d1913d8012807f80808080c680d97f4f8d7f8083d89680808002e09426809b2980da7fcc918080ffb80d80808092a1808080808080a98080f8d4e28080809980c502e380808e80809b80af808080bfd88080802b910880808080b68080f880df80028024fbc3871437c77f7f8f77ff42e868807f956331c4804914c580805ecf1f7ff6ea807f80bb7f5102fb800f28589ceac20f800c2f417f80f5d5807f53a4803923d2978080ab80268080808b8082800280808080808080e5d38080808080c503e08080808080bf80b4808080c7dc808080c380f980808080808080b9808980ee8088888080948023808080138080802280808080808080b5178080808080f3cbe98080a2808080808e80808061e0808080b280ddac8080808080808080df80808080,
      4096'hf9d117fede05bb80f3c403fbf2d4eccfeaf30de85714e0e804ec15e711050be680bdf0f9e9a0f4f5db040bf2d125d6000c0480b594d01f00f2edf10a9b25fb2786a580114d1580d480bb41b2bd9780808014ec19121f1a8d8080ed809cf6e78080c580d5b1d880808080bccf808080ea80db8080e180a29f800c808a803880f32901eee91c0c11d265bfb800cff706d0d1f0bc02dbf3d9ecb451081fe0bf03d9adf504f4efdc111498f8ee0aee1d8019f1f2f10fe629caa3175834037fdcedf980808086cd0b808080f280e2802f80808093808080bed61e80808080e2d7fd80809f808080808680808048a3808080f3801480808080808080b880c480058080bc18144af47f808011807f80747f809c362e7fe352274c7f7faf28047f80295c8080d17fceec4df1ae127fdf7f0180975024df918023b536806065077ff3f0d3f27f701e7fef277f7fd627413ce83e48e64111737f09f4f536252cd50c15f71880d3d81f4d7fcecfb98c13c3f0707f55f8f3a62411ea547f0580be128061d434849280d1a224c48d80e180d880a480b58080808085150d8080808080f1fbf48080878080d780be808080faf380be8edcb9a88080818086a3808080ca80ae8080808680ccdeff808080f1c1e8c42e80b38080088280d428b6af808e8009ddf28080f880801e80d88080805a0c808080dcbb15e69e808080d780aa80c480c2e2d7,
      4096'h808080ec9ef7808480de808680898080809d80808310d2808080ac809e0a188080b08080a380cb8080808ac080808002801980808080818080fe808080058080d97f0d0d5af06f4680cfc935efb004f7c92aea4b7f6e21bcec873700fdaf1d2c8052bb192a7feecc0f97fae1d4f7530d09e1e939548a7f134333d701807fba53bb3cbb07f603647fe44bf7fa1df63c53f10ede3ae8051206e2ca1a17033ffa28f9683827307feeede81b91231c007509cee830277fd60a11562af8eca6f9f6d028894b2da21c8b9f420d2d82deef190f670005ead3e8184a147ffff3e4ebf50b5cca33131580e85ff85ca845fe4cea4fda1950bcce17bdac79b837e97fdc5aca9c8080e0e00380b980d080ab80808080808080ce80d30d808080c680b3fef58080dd80808d808180808080d8808080df80d28080e780808080ef809480fa8080f2222208f5083b7fff170c0ee5e514301730fb1c2e3239f8e0fe35f8fc17f7220e20e622302609d63edef00df4083d12e0f1fcf335dc26d7f50701fcca1bf00380e3800bfeed87808080b2d716d380e2808119c383bbf280bf808080fb9e128080068080f09bad80808029dab9f280eddc0ebdb9b480e50f808099d980d906e0808080f980328080808987af8e0880938080bf8080e1f980808080800cf20d8080808080808099808080f1e580df80bcda1a808080808080808080ae80d080b8
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
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .KERNEL_WEIGHTS({
      4096'h7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080807f80807f7f7f7f7f7f7f7f7f7f7f7f8080807f807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080808080808080808080807f7f7f80b48b8080807f7f7f7fb27f7f7f7fa580d38080808080807f7f7f7f7f7f7f7f7f337f821a31809da8802580803580807f80808080808080808080557f7f7f7f7f7f7f7f7f7f6e7f7f5c7f7f7f7f80be7f80807f80a87f7f80807f80807f7f7f7f6f7f7f507f7f7f7f8080808080808080808080808080808080803e80088080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7fb97fd080eb7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f80807fa4367f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f3a7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7a2c7f7f7f7f7f7f7f7fad7f7f7f7f8080808080808080807f177f7f80807f6f258080808080808080800bac3bc685094e9047bf80809b80808080808080808080808080808080808080808080808080808080808080800a797f247f7f117f7f808080808080808080874477fa7f7f8ea6,
      4096'hc380808080bbab8080807f797f7f807f7f627f808080808080808080de7f7f3d7f7fea317f7f7f7c7fb4207fdd0f7f8b807f0a800d808080b78ea07f16ac29a2808080b6c9969f808079317e35de2edf80b97f7f7f7f7f7f7f7f7f7f7f7f7f777f7f7f7f80808080808080808080808080808080808080808080809d8080807f7f7f7f1d77726f7d7ab719f980843580e58080808080808080808080808080808080809c80808080808080807f3d7f7f3f667ffb7f8080807f7fe07f7f807f7f1b7f7f28f2ab847f7f207f7f3d7f0f8d8080ac808080808080e8db01b8ea9fb7c9a48080808080808080808080808080808080809580808080808080808080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f9898a0a5ab969e90b88b8780b5a096bbc7d88080808080808080802a424f485a5e4b5d6480808080808080808080809480cbfe80d4f3808080808080808080776d1a3c3ef9f0e68d80808080808080808018044a251b47552c6c414e733e6c7f40697342637f407f7fff537f7f7f7f7f7b7f7f6d76aef8168081d4808080bfdb06a2a8a7c098a6120909ed0206c3dee3ae8090808091808080808080ae8080d38080315e7f3943790f265b7f7f7f7f7f7f7f7f7f24142df61a38e1e6eed28080a680808080807f7f7f7f7f7f7f7f7fbffc1eaedb06c3d6fe80978f9da28a80,
      4096'h80807945261a1ff8dccfd5ffef1e38174a685d7a808085808080808080a2b8c580808b808080ed10499af23d86ab048080a780808080808080808080808080808080808080808080808080014a8a050780808080808080808080808080bfae80d298808080acbbb78080808080808080808080808080808080808080808080807f747f7f7f7f7f7f7fc9a2bad7dcd2ced2c099c780fb0dd7b2c1803d15457a446b7f767f80808080808080808080c79ad2f8cb808b807f7f7f7f7f7f7f7f7f06f806422a477f65787f7f7f637f7f041a1d7f7f7f7f7f7f7f7f7ff5efea03f3e803f6ea808080b4f7a080a3807f7f7f707f7f0e40527f7f7f7f587f7f7f7f7f7f7f637f7fd8384ea2a0808080808080808dbf80a801d580808017220b04d9fdbda5c080808083c2838080808085c2808080808080808080808080808080ead1000fd61024073a7f717f443e4cd2ee2b132d510f2d41f900f8b9b0c4b6bbbe8e9f8a5628563d18496838747f7f7f7f447f7f7f7f808080add09d808d808080808080808080807f7f7f7f637f7f7f7fec4a10b002ed8080807f7f7f1d617f9ff1248080808080808080808e8080c38080ce80807f7f7f7f7f7f7f7f7f808080808080808080fc7f7f7f7f7f7f7f7fcb80803292b51f809d80c1efc23c7f5d7f7f808080808080808080808080808080808080f1b4a832ebe1f780807f7f7f7f657f,
      4096'h7f747f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f8088ecb4a5f7eedd50751ba97f7f027f7948c2808015b58b41102234dd607f2f6b7f4c7f80808080808080808044347f7f7f7f7f7f7f7f597f7f7d7f7f7f7f808080a980809480808eb24e9ae97fe61f7f7f687f56427f7f6568808080943d0a8080801b9ca80993abd780907f7f7f7f7f7f7f7f7f7f687f7f457f7f7f7f808080808080808080808080fefebf8c9e804ba1807fd98e7fdd0180887f8080138080377f7f7f7f7f7f7f7f7f80808089928080808054c88f3c0b9bd3a680808080808080808080fba79109d3add1808080808084808080808080846f98c37f8096734a045506f74af9dd4d80801d8080e98080678080b6a2803a33803cba8080d1808d498abf80801d80802898807f80d77f8d8a7feb497f8080808580d628ca638080808080808080808080808080808080808080808080c08093b81e802a0880051785767f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7fb31378ede46f2d107f27f4d77f775d723a30808080cc8080c7808080808081b21c808afd2a80c1eb8080fd809c4057587f7f7f737f7a7f397f7f7f7f6f767f80808080808080808084bf75d6177fb4197f7f7f7f7f7f7f7f7f7f808080808b80808080ad80f9ad8016dd802e7f7f7f7f3c7f7f7f7f7ff8757ffd,
      4096'h6f7f07780ea33ed080e903800d80808080968580808057bdf27a460a7f2e090b87fdfa80eef189d62ae27bfd966dffbf518080808080808080807f7f7f7f767f7f7f7f7f7f7f7f7f7f7f7f7f16ae5de1804159ec7ff5fef25b244be5fefa80802880887f80a1760ae17f233c7f754a7f8080808080808080808080808080808080807f7f6a80808080808080ec80808080808080b77f8080808080808080808080808080808080808080808080808080db808080808080808080808080808080808080808080808080807f7f7f7f7f7f68626354587fdff22380809d8080808080808080808080888080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7fcb8b80802d7f80807f8080807f7f7f7f7f7f7f7f7f8080801b4a808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7fcd7f7f8080808080808080807f7f7f80a07f80800f80804a8080808080808080dd8080808080808080808080808080807f7f7f7f7f7f7f7f7f801f73808080808080808080808386808f96517f7f5b7f7f8080937f7f7fc57f7f80807f80182b8083d38080808080b08080808080807f7f7f7f7f7f7f7f7f808080808080808080d3e00097a7c980808080808080808080808080808080808080808080800780808080808080807f80808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080,
      4096'h80808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808d8080138080d480a07f7f7f7f7f7f7f7f7f7f7f7f7f7f7f6a5b7f7f7f7f7f7f7f7f7f7fd880e5808080808080eaf2dc38af8a2394937f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f808080d1358d808f807f7f7f7f7f7f7f7f7f2480fb7fd17f7f767f808080808080808080ab802b80fdc980808f8080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808680809080808080808080808080808080806b487f43505c5e1e667f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f808080808080808080fee3810024d480bb807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f80808080808980808080808080808080808000000000000000000000000000000000000000000000000000ff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000ff0000010100010101000000000000000000000000010101010101010000000000000000000000000000000001000001000000000000000000000000000000000000000000000000000000000000,
      4096'h000000000000000000000000000000000000000000000000fffffffffffffefefe00000000000000ff00010101010001000001000000000000000000ff00ffffff00ffffff000000000000000000000000000000000000000000000000000000010101000001000000000000000000ffff000000000000000000000000000000000000000100000100000000000000000000000000000000000000000000000000000000000000001d1c151519110d0c06eff9eef704fdf402f9e7edebedf9f5e5f1ea161c121415130c0f08f4fbf4fa03fdecfbf2fe02fefe04fcf4f8f8d6d8d5d3d6d3c9d2cde9eff1f1faf9f1f1ef00fdfffbfafbfefdfef7f8f8fefcfefe0000f1f2f3fffdfcfffaf5faf8f9fefdfcfe01fef7fcf7fbfffafafbf4edf1eee5f2ebdde5e217110d18110c2b2314ececefebebeaf2f1f1f4e8e4f1ebe4f0ede9fef7f008fff60b02fa1013150c0f100d1013d2d3c2dfe3d1d9dbcb0a04070b0e070807ff1812190f0c1517111a07040401fd00f9faf8fdf7eff4f4eee7e1dc10130f11120b0508030c0b09090607050503b6b9b2c3c5bec1c5bef2fafcf0f6f5e6eaeafe0402020201f2f8f601ff0300000204030405fbf907fbf900faf7e4eceee8eef0e9edf0f4f8f6f6f7f6f6f3f40a06090607060a070b0a060801ff04060103fafbfb0203fffbfffdf0f2f8f0f2f4f4f6f709090c0401030a070dfffd,
      4096'hf3fc00f4eef0ec0a0d1505070efd0407808080808080808080808080808080808080807f7f967f7f80c3b5808080808080808080bf7f69347f7f8067c9e2ffbe918782808080808080808080808080808080808080808080808080868080b780aceae9bc1f48381edce8e00780687f43e23ce01bf8167f457f7f787f8080808080808080807f7f7f227f778080807f7f7f7f7f7f7f7f7f808080dbc8e134eb517f7f7f7f7f7f2671387f7f7f7f7f7f7f7f7fbdc09badcbb2a7a38e80b180b943f28080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f247f7f8080808080808080805a7f7ffb7f2a8080807f7f7f7f767ff213158080808080808080808080d68080808080808080808080808080808080808080809c8dc87f7f7f7f6b5ff8cd80ba407fa6397f80d5ef7f37583c0b3ddaac8834ee49401f7c52507e7f447f7f5c7f7f717f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7fb47f7f80257f8080807f7f7f787f7f80ba22c87f7f767f7f7f7f7f7f7f7f7f7f2d7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080aed47f7f7f7f7f7f7f7f7f7f7f80a780807f02917f4f7f7f7f7f7f7f0c7f7ebf7ff7802c808080808080808080808080808080808080808080807f7f7fef7f7f8e307ffb4280bac5800380808080808080808080807f,
      4096'h7f7fcd0e7f809180808080808080808080f99b808080808080808080808080808080807f7f7f7f7f7f7f7f7fdc8f808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f808080808080808080d25e2680a9808080807f7f7f7f7f537f7f6f802f7f81407f7f7f7f7f7f807f16803d80808080808080808080808080808080808080808080808080808080807f7faf7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f253f46f8f2ee808080808080b780c8808080f8737f426d7f80a7c0ccd9e7bafdef80808080b6a680dc8e8080808080b38080808080807f7f7f6b7f62809e808080808080808080807f7f7f7f7f7f7f7f7f02e6f8e7caee5adb18808080b1de8080808056e11132d0fe9db4d580808080808080808080808080808080808080a63280eb018080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f6e757792b7cae10846deeff151e30d0ac42be797c0808080f412decee5bc1d7f7f1d7f7f993344088c66ac801a808017777f7f327f7fe7617f8083e580b9ce8080808080a510427f486d7fbd80fc8b809b80808080808080a3808080808080808080808080808080808080808080807fff7f36c7627f587f7c7f7f3e7f7f84377f80c955df5777851559,
      4096'h8080808080808080807f6d7f7f407f7f7f7f7f7f7f7ffc7f7f747f808080808080808080d388f7ec9ae5a780a57f7f7f7f7f7f7f7f7f96eb06ab337f8080bb747f7f427f7fc5387fd6dad2eae7cad7e0c4b9bdbbcfc2b7c1dbc892809c8c8c808f9d8097aca1b8c69fb2d1a39b9e859a8c88848c89a2a6be97929f858e8ab9d9b8b4cdb0a8ceb986aa9eba8480808080060b10061209070a148080808080808080800afcf8f4e4e5ebe2e6f4e1f1e1dce6e4dfdafd07ff060e0d100d135b4447423833413437808080808080808080322b322b1f2f2a2c28808080808080808080808080808080808080808080808080808080615845100a17fc0e1c8080808080808080808080808080808080808080808080808080808080808080808080801d24363a4e5d3c4b62808080808080808080483c401f1e24200d15808080808080808080d6d3cfd8e2d4d7d4d2e9ede6e8edf4f2f9f2d2c180dac8809d928080808080808080808080808080808080808002f80a01f80209050ff0ebf8e8e6efedf1f70d05110cfd0df5f502808080808080808080fcfb00ff03fd0d0611cce4d2ceeccda5e7cc8080808080808080807f7f7f7f7f7f7f7f7fd6e3f4d6f802c6d2f1ced7ecddfff7bfe3d77f7f7f7f7f7f7f7f7ff92730fe3d4be004207f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7fbeafb4c2bab89d968a3c38423140362a3b,
      4096'h3f8080808080808080802b1f31180e110b0108100a17fe05fcf7f2fbaec5bccaebdfccced601fe06f4e8f9e8e2ee8080808080808080802127301b1e2616190f80808080a38d8097a68080808080808080808080808080808080809cabb5a6a9af96a3a5808080808080808080808080808080808080808080808080808080808080808080808080dcd2c7d1d0d1a6af98808080808080808080120e06fbf7070702fa808080808080808080899499a1a2b09198a4f8f6f2f2f8fcecfded80efbc809680808080808080808080808080808080808080808080e7eae6ebe7e0eae3df372b2d3a362f2a303107040f050104f9fbfb8080808080808080800a0c0f19191f0d1c0d80808080b28080e0888080808080808080807f7f7f7f7f7f7f307f7f397f7f7f7f7f607f80808d8080808080807f7f7f7f427fd2805d8080548080228080807f7f7f7f5f7fdecc518080808080808080807f7f7f7f7f7f7f407f45d17f7f5d7f7f7f7f7f4f7f7f6f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f2d7f7f087f8080808080808080807f7f7f7f7f7f602a7f80ce3e808080808080808080c3808001b8808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f767f7f7f7f808080808880808080808080808080808080a653ab737f7f837fb87f7f7f7f7f7f7f,
      1024'h7f7f7f7f7f7f7f7f7f7f7f80808080808080808066e40e0bab0795808d8080809c809f22d3ff8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7c7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f037f7f277f7f7f7f7f7f7f7f7f7f808080808080808080808080808080808080
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
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .PREDICTION_BINS(10),
    .READOUT_WEIGHTS(768'h02fbfbf3faff0511d0f9f1030a05f6fe020008fbf8faf6fab0eeee0a01ed80fa031305fd030bfbf9f6fbf6f30500f90bf80c05ff0509fd02fdfafb0c0801f6fdf601fcfa08100e0902f9f8fd0109070be8f7fe09ef010304e50112f3110b080c)
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
