`timescale 1ns/1ps
// Generated file: do not hand edit. Source is model_spec.yaml graph + ROM images.
module eventspikeseg140k_dag_top #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer RESIDUAL_MAX_EVENTS = 64
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
    .in_valid(input_valid),
    .in_ready(input_ready),
    .in_payload(input_payload),
    .in_completion(input_completion),
    .in_bin_tag(input_bin_tag),
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
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(1152'h1313f71d1a0a1227160409bf2932fe44391548ab805ae9807fe6807f7f7f7fac178085c480682a804f7f8042737fe9df7f2e807fae800c16102f1b32282a2f191718324c2d2d342c7945807f3f807ffa80806e4e804b61801955808080838080074235a7d50c122d2538404304000100fe0407050602040502020103040a8080808080f48080d87f7f7f7f7f7fecaabf),
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
    .actor_error_o(error_actor_detail_stem)
  );
  logic error_actor_detail1_standard;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(4608'h808090978086b2888ff4b2d642fc084006267f49577f44797f4f61d5a9b435d2db1dd9d67f527f7f5e7f7f7f7fd5c39202dbd6cea0c0c0307fb5287f808b65eeb0ee25daef15fd199a9995ddf2b8dbda99deb3c422cc0504f2fb6a697f785d7b7f617ca680c7cdc1cdc9c4e17f747f7f7f7f7f7f6ebb9acbd9b2acbe88a48080c08086da8080c3cba8f81ce608f80331bac6e3bf89d0d1bac124fe1915c6f3edba017f7f7f7f2d7f7f617fe5c6fbc58ed8d7ccd97f7f7f7f7f7f717f7fe0c7e0bed7e2baadec0ff77ffdf242d1e00d01f82ae3a91fcda2008080808080808080804cc6dc701c496b295f7f7f7f7f7f7f7f7f7fb08098feb7e40fb6327f7f7f7f7f7f7f7f7f9880b3bacad38680021113540e517fb91c7fb7c0e532056232ec7d8f80808080808080807f42c717c28821cabe7f7f7f7f7f7f7f7f7feccbbcad8293cbd9b37f7f7f7f7f7f7f7f7f9680808080809189af7f7f7f7f7f7d7f7f7aff311dd4e8c691bdba80bbeebdeff2b9d4ea033735464222f42b38c5d27f13227f19797fad030cfdfc20100a087f7f7f7f7f7f7f7f7fa5ef2deff41f97aaba2021464747737f7f7fa62959d1113cb7e8058080808080808080803bb29fface92e706e07f7f7f7f7f7f7f7f7ff38680b4999b98b9807f677f487f7f367f7f80808080808d8091977f7f7f7f7f7f7f7f7f59f0953aeaa2ed17fab99290edbdb1d69b8031d3df0ccfa324c4c27f4b597f4e39514958c1809ec38c80c0808e7f7f7f7f587f7f5c64cbcdd6cdbfb5d885a3808080948ac18790e50feada0acacce19fde),
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
    .actor_error_o(error_actor_detail1_standard)
  );
  logic error_actor_stem;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(12800'ha3adaec0b70d06fbfa06150f130e080a0e0b0f06121716fe04808080998080b7ac8fbeacc5081cf911401e211a004aff06103214e81910d8b209270bb4b3fef93fc130fecfd4241c24aaadbdf5d42f092fc515fccee8aae10510c42110d2cfd31c1bd0ddece50cfde90101f30d06fafc020c130bfe091903160c202d19afcbc8d9d8d0cbc9d8cfa1ccb5cfc8abbfb7cfc3a6b7a4b2b6b7497215bfb22d62f4a3992f604fa68142610aa9860e1825804cc4a9497733e3ca6b5637f398135c4da8841b46188080e106808080808080808080808080b3d7808080c88099808080808080808080808080808080808080808080808080808080808080a4aba09ca7b8cbb49aa7edf4fae6fddd0d1226f3061420212dd3d1d6cda6edebeee2e71c07251a1627151a111906fd0611033c221310053d280a0f05611dff1d1249f3e2f107edcec7caf108141a200906012a1c03d0c9e9d7d7b0aac4acaba38bb6cab71f2022160ce3e2c0bcc6a48a808080d7aeabaa90fdf91a170d1d291414f4243c1a1b1b23382222100c0f14f507d9eddbddc8cbe5f5040ed9f0f9fc06eef9fd030efd01030615fc0106091b1510fef9140d12ff00120407fbf2110400f1ee090b0df8f20b20203e5f6ffefc0d4140d5d5fa0521d0d1e4f6fcafc4eef50305161e2736a59dc1e0f3808aa9cde694abc9ef02bfe4191442a7f1f706f8b6091a1404d4fef0f2eaf106dcfcdbd8caf9e6d8f607fbf3f30fe713f8fef80af6e607f52a02fcf51e1115011e20334a4d3d304c4976211936263b2113494b110deee2e9dce128048080804900c48080382bd780804b02da80804e47da8d80261701fd02121506000a01fdfd0008fcfbffff03ff01ff0506d2dcfa0807e0def705fce9ee0cff0ae8e60a130fe4eb0d0e1a01f7e681b0f4f8ce258fbca5dddaf3ae80c6a6bb92a9bb8080303b48212f1815063018dbd7c4d0e1c0c3c6c8f5c4edf6bab2141002f780fef6f2e2831bf9070ab373241efbd366f3fbd1b07f21fddeaf6743120be12015d4b580060ee2b180172a14e49753692480802732299d8035482f99807f5621be807f5329b280919a236857d6f3424b3dd0a4443616a3a30e08e3a4ab353927b395adbcd1d3ccc8e4f109fe00000d1c2e18231a26232b17181b2c2c2c2500050101fef2f1f7efe0e8e1e4e8edede2d9effa1f060b33601bfffe2b3128e5fc331538f3ec3e1353f40a3e5704d4c8031034d9e9292a3bf1223f4b3ff9f8204f3fe41940348dde1fff159ece1702169bd6f5f7228bed0c222588f106193debb8f22126e5a3d02e18dfaddd071bc8b4dd2423b197c71d1d80bc57524f80ab3b434a8080172a5e80904f4d6f80c844637f532bf2c3c45e4cecbce0422a21b7b56532f2ab8e514611b694803fe480109c96808d29fd06214b8a809f1400bc808080ac8080759b4a80717f2c80cf80275451e080806fc1808080808094210a221a4423243a2218181318fcf7c3cabaaaa6bca7b2869d80eab8b7a5e3282af4e0e8f2bfebc8170817d085bba1d6e4b5fef9f51a2cefebf70c26d1dcf1010ee6ecfc091cecf3030e1e8099e20b10b0c50c2120fcfb273030dfd7092329cdc5f9041f80803a462c8080e73e4d8080f73d6c808011317f8080166d764c663ac7af4b6636af8d6d7f2cd78068762ec680705b0f8080c2ebc8fbe2bfd102e4dec3f8d8fee0c1c0cabfd0b0bec2c5cf2859485b53172f0bfa1d00fe0921ededf7fe0ce8dbf70b1a15809dc2b3b2c5eae0fd0130272d0f1a210e000301ccdfd5c0c68781b093a6b3c7f4e5b0f91d06fde21507090d13f2f2ede5f4060a1a17ed0c12320c020cfd3d191b0406111407e9012d1102c2e8e0efb7dadff4d8e3d6df0516edd3e9f701efb1cdf2eed18bcbf4e18bb1cadd97cbbf808080a9170a8231c080808080808057ae808080cad58d80d6a080a8848080808080808080808018142cec11fc23ae09d7d7e935def6b3c9010fe807ecdbef0b1b09afcaf209dde303a6a91a2bf5c401e50f2502bff5ebe021958999958cdeded9d8d41d0512071806fcff0e120901fa0208808082808098a6bfa5809cd5e0c8b806ece9f8f2eefdfdedeb7f722480807f53e380807e661480807f4cdc80806b57f78080a4a7321f1aa0a423512bab9618471f91bb2d3610b0c74641210e0ee9a980faf3f9b19f1411ffd3b6401a19e3d34e2b18f8efd8ff1e323cf00d2e391ae9fd21170ccdf0fc01f0d4e1180b03),
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
    .actor_error_o(error_actor_stem)
  );
  logic error_actor_enc1_standard;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(73728'h7f6d377ac5a933e1b9400dbfdc03c9081f40d2ccd8e4dad2bba180b79380d4dd80a6d380150402101805030c0d7f7f7f7f687f7f7f7f808080e7ef10ce601d7172174225247f6268c1048fc009b68080808689e31416e133455558687f7f707f7f7f7f80a99380809a808294ffc3c6959b88808080f7b2c92efc00194b6280c9058623ff80f0b8043b25dfdc1980b807ec20f57f7f5c29121bcecbafe9d7bba1a6a96539ed78fea1c48ebe80a2808084808080807a401e694b40147f7f51202e2f1c42bec25ef917f6ddbcd5808080a40e8080df8080a680cadcd12d38ede3202d75624b671317e0d6aa808080808080c6edb7e025f5fe1d1201173030ece82d63ff3736277f7d6fe0abae82808580949aadcace80adca3a0f320d4441c6d516250c033f0f113d432037323138491b432f1a211516df08f9eceefbd8172fc4f3edfeee20f9f70903f705f3f507ef1b26f84516057a43cf99bdbfa79fe9cec7f7e1ddfafae70d060bbad909ccbfbeb0c2caa9e4dbe8d5cdf9dfd11415375d1b36707c4ec79399d49aadc792a3cca5a4e1cabceae9c6dc231b10012cffe2099bbfb8e0d18ad6b7af1dfa01f3c8c004fae7e8e7f2e6cbc80cee05202c6a3c204d2d617f1c1af611fcfe0b192e01fe1fdfeff1d7f61919125430191d651305213c37131d211504d6f2f6ccf2f2b6d7ecbbcc1a44dc0e15bc1e3cc80e1aefc2d3fccbd549292b525b06725c6423fc07190af42c07eedb102f012906101a0e2660402f0710282c0b2c07326a3d1c5e403b26213005dfeffdf5ece8d4edabb4bbc6c3af3e3207fc362187bfa9f202eaeffbb0f30edcf9ecefc0e6e9bce40ccb061bf8e116c488e7010508060a03060d041947f01f3a3bc8cef7031016ec2526c102e330fe120316240ae71d1bed0a01f604120d18100d2f202021b2d1ed5c3214282707faf5fbabe7f080cce380e7f9050200eed5bdf6dfb616b9feeacde580808020372dee494dc91939fe303d0f2d26e4001434ef0366473fe800e611f6ee13f103c7bcd1fbccd1bcd7dd97e4ddf0e5debfd3fbb1ddfae7d7a0e7fccae6c8e301fbf6d3c2cdd7cdd007fae10303b7caf7dff7e3e5eceb04a6d7d955f3011114f7d4b7a8d314e0dbeee7beecc91d3c031727cbfc3911e5fc200cdc020a01e01cdbd0ff0bd6ca9bd8d10fc5c7bcc6d7cb85daf7efe0f7f39bb9d9224a58417d7d0d4c2a22063dffd508defa3821f50216f708f6f5fbe9f9e3d5ededa1becaef0a0de7ec06b2dc18ff0b05020afe0508fc222928111d310d1b57051204ef090cc609531f15251a253f2f1436dac39f80a4a3919fd000da0215f40431151bd4e2fdd9e7f6fcec04dd010ce30a04bcd4050df1b41105a6d9e2ea4b3e4b452c00014916463f25f209eda8d6ede6edf5d8f4e8cdebff27400ff420fd95caddfbf817e7eb09defb1ae3bff1e70b1ee8f22af4def5d9e6dcc5bddd141fe1fa0dee10fb0bfef603e7eb05deef102c1fddfc05ead8fbf701d5e7dee0d1aeb9c2445146491c17ff182f04021cf6dbdcd7e2f903ed101af704130700da19f708210214fd0622fb0a04f3e6db0afd28211200fa05f4f203dff4eee9f3d6c2e7fded0616d3f5f6aee0ebc4d0c4808088a79c0bc780aba38cd180cfd8dace1b9cabfb09ea0afb0633d8c15a03e629fa0303ef0a04e5fdfd7f7f7f7f7f7f7f667f42f50cd5c1e20405ad7f7f7f7f7f7f7f7f7f7f7f7f747f7f7f7f7f6b4d7f597f7f7f797f7f7b417f7f7f7f7f5dd1187f9e9875d7c17f6e0d7543f92f4fb1dcdce1b780b306dcc499ea14ecf8c3f8e9f1017fbc0752d3ae6512ac7f7f7f7f51607f7f7fb1c6d6ade1e8c1c8d280aefe8080f7809b99b4ed4f80bd4d80e76da8809999808080b2803e1f7f47fa7f7f7f7f2ffa7f1f357f473b7f80295f80f07f80f17febe19d20f6c5e9ff807f7f7f7f3c7f7f7f7f808ede808080808096eb02a8d50ee8f7deb9809cccdbe808968002808080808080cc8080e080a5ca8083cdb7807f33454f11287f57359ce7a5a8ddfa80fe00d8959dab97b1b4bcc798da149ef31f8ee8d980b32c80962980e528080004f6fe040cff05c3cf84f40f27be6d1493f01c80b9bd80a3bac7e9fe9bc01d800541b8802080806980804dbeaf2ab18017e3e2198080a88080df80e5e580dc4780d34b80b265f58032b4802dbd8056cb8df48080888080a180a31680809080808080946480803e80c52fa8da6380805b8080da8080e08080f680bddc808e7880807f80ad7f8080008080358080f9ae84b7b8aef9b7f0ebcfa2feccd6c8c3c10ad38044d58072d6de7f8086ea8080258080c6b49a0b8080a794af9cb3ffbcc8e1b4a8f1c1d0c2fad68d1adc932ef8f3fce8f5e6f5f9e298cd80c000b3dc7fe0f2f2dfecf7c4cae1a480802980800380881a9bcc5f80803380803e564e5af30620c1c8a8bfe80c031c331057253412500cf20ce1b1ca07ed2af3060ec2b6fcfb0601fe02010802fae3f0fee8e8d9feccf0412a46311616d0adea0c15060ef6f6e0e0da5315e4edd7bcc3bcb84b2810655b3c586a5bd7d9d4998396b394891702160ffb1fe6dd0f3c2bfe3f1a0ff4e31114fcf84d4619c1f1084b5e48162e2abb97c8d1d6e4e5daeec0acf1304f440e1e20809edf04f7d8afbac98080897b4c2b7f662b7f5c56e9d2dde5f4dbc3b6bdd4ccc4d7ecefda0500d1e40104f8e54336f36e6323482f10fe0d1dd1ddaec6d5c5adaba7f9eae9371a03b6bee5fdf921f8fad9bccebce3f5fcd6e109c0b9dbf4f3f70cedfc1cf600afc0d4f8f5e0500ef47f7f6a390ff3fdcab4d0c6eecfd7e9a999c31bf9fbfbddd99c89b936533813191801e523d9ebdff3391102f433421e32eef609ced3c1abcbb390a180a7aa8a1006fc0805fe1110fa413f3b6c414a7f7f7f222a0dfcb0edbdf4f734200705d8fd7c6c7fef00d280b9d3acf1ee42665927091826153ddee2dff516fd092910f81a35f2f4f0ccee1737424cf8f60af3ece610f9ed22df801fd5d1635a5e30ef9ebfb4cbf0ead9dececdc0dfd64e4905149782eee6ee11fecde8d3afe3d8d2ddfaf1cad7e4b3809af1dcfddcd39d88acccdbd4e7fd48ea18fbfb072d2b180c1730647c64623c070f3416fc08fcfc05e9c9979fb5d903e6e305e0801a0002124c5d01fe13eff7010804fb01efef16000be900ea270a00f2eaf4f1d6e71028ee3cfb07303a43f701efe5dd0ae0e9dce7d5edbabeb701f9d8c0bcdfd9eef8424e7fbb80808080a78080b0888080e5c0a908e6dba8cdb7a59ba20baa017f331d7f7f3503fe051011e3fbf3f07f5c7f5c7c77f5f8d8001e2a7f604a7f7a64641d187f4a5e7f33267f7f7f7f7f7f7f7f7f6de07237397f7f7f7f858a80becbfe808791befd7f00bc2c2c994f7f7f7f7f7f7f7f7f7f958380d809eb416e52c9284f70663a7f6043290b377f17617f54247f6c7f7f517f7d5b6b8080808080808080807f3e435c657c727f7f54683e3d7f392a5c4e808080808080808080809480a1b38cb580a87f7f7f7f7f7f7f7f7fe3ddd680381f882c15a18080c8b7971ee3ea5c503b21ccf48080a0f7f3b8f3e3dfa79cbea8e0c9a992da84be87808080a48080c30507407f23a888f98080808eb703b9ff30114a9d00ec4c7f77607f7f70aaddd980968080808080808080808080f08001b801c498c8cc0fe4761a3001c9b17815f103f0ecebf2fce9e0d87f7f7fd1bf808480807f1c327f7d2055ef60e9ec0664fd527a2f437f7f7f7f7f7f7f7f7fe2b37fd05f7f600a7fcfac80ada9a2808b80221f6642c44f7f266a7f7f7f7f7f7f7f7f7f808080dc80a13accd6657f7f557f7f67034e7b6c4a4d68787d364b7931347f7f7f7b261f8080808080808080807f6c7b214e7f767f7f7f7f0d6f7f307f7f15808080808080808080808080808080b4ae807f7f7f7f7f7f7f7f7f047febde4bedb103c880809480808004e4af80809580ccc6808080809aa6809ab58089c080baa0899cad80f6a880808080809290a9ce97c5fd94f4a280808014e3f5f9f50a3b92357f7f68797f607f0f7fdce7b5d518f8d2e7e9315e663b597f337751d8db12e4a803d7bce9fb6f0cd64d49d0dd06eff3fbf9f303f000f680d7f084d9f595b295ee4a3f361826deb5cce21804a4d403808c80ddf499dcc8c2a4a3b9f706f7ad02408080f605f715e7bf06dda6cfe3331b11362cc72239c311ad0cee1bdaa380be3efcc91200254344c58080098080818080ed3cf10afe12cfccb5b6b0a1c69db58080c9dd0019e7e4fc2a17308095a880ccf68080c5332b2334123206175055357f7232787f7f7f75753c636e4206252280b18085aec4808080652f69562e6039527cc3edbad4eb09fcf24419c7e9f18ad10ff9ee20130c190c1cbf8ef2f11afce51b1323ed3426403e7f3b384d0412f8ecccb1b8d2d5a5b1225f3b5c293d3efccf99e0cfbd84c7808080d180a8b5e8e4c9ce219180808099998084803869644b27650d135d7f7f7f7f7f7f7f7f6af01a0d0ff5f0f9f90049d62c17d08b318fda267f7fd5fbfff6e8b3657f7f67615d7f207f7f7f7f7f3c627f476e7f7f7f7e7f7f7f7f7f9180d2a980a78780a87f537f3602fa44c3077f7f7f767f7f5c7f7fa480a13461a9f3f391710ef579de3c7f2207e95617dc49e69d31f2e7b87f0dc1007046208080808080808080807f7f7f677f5c417f7ffeb00fec80e722d5d680808080808880f780eddf060e89ce0ea5477f7f7f677f54ea7f67e6ac2ff89ee1fac8b5ef9cb96cfc0614eae1c42b0cd7c7d992b28fd7bbd8fcd6ae06edf9ff0ee4a9d3bb80beb0d68080808080b9b0cf80808094a7868ad18cdb7f6683480880132ae47f7f215b36e73ef007fbd940db169a808080aa8001c5983f2a344018b4eff0c144f6807fce3877a0df71d1dc000df3fd08f3fffbff134a3b7f7f7fb3d3923bfbfd7b7e3f576c0d25f20f7f7f5b70573e7f7f7f7f7f7f7f7f7f4a0839fafe7f7f7f7fafc0aca5dfdea9ac8032a5154cdc4e5ed2077f647f7f5f7f7f607faf88890b02eb7f4f0b7ff13e7f0b307f644a271dc77f44fe7f66da7f58257b4d587f757f8080808080808080807f7f7f577f7f4a7f7f33a5ef7ffb603ef77f8080abb7be8001dd071beaf27f02037f557f34257f7f7f7f7f7f7ffd99fc31a642e8c85a8080beb780be3df4167d3e1a223a3018b5e7f8b7a08ab78880c1bed806ede7ccfdfa07db81b780e2e3f711374a090db01dede4e2cbd35b4c030452eb5f56a4353abd5037e2566c1f7a7f7a3e5e7f63437f7f7f7f7f7f7f7f60222e6e7f3c7f7fdc2374c8abb8f78ff90cc4f6ebf8e60907fe11eae9febbbfcbcde5e20a6c80a28080c2d180cecc1852292d1bc19eadd08080808080808080809bcd800c2fe0effadf400f15e5bada09d83dd9407f067f7f26757f8080809695808080801e7f567f317ff2221a807f7f805f7f800f739f918580bcfd84a09786bfeaa4cbd18080807f7f7f6e5b7f424a7f7f7fc37f6d0d3b44f547693c62411b9aedc27f7f7f7f7f7f7f7f7f8f22088f26f3808098b3ae800caa80c7c1802179167f231fcb27290c687f78307f746e7a116c7f0dd4e931377f205c537f7f794a7f7d1f16203d6f4b68547f7f7f7f7f7f7f54032b7f7f7f7f7f7f7f7f7ff11aed80fe1680ddde808080808095808080217f7f1f1e218bb79780808080bd80f7e31813ee22ebe534dc80ed5a45bf7f467f7f7f7ff9050dfff5dff4f9fb4b3ffc8016d180fe94ddd3ac5ad9f32ba62d9680808f8080b080807f7f7f7f7f7f7f7f7f80b58080d400d17b7e138280e28080b2da80c79be725d131aba3eb7f7f7f7f7f7f607f7f80b4867f3d4d7f7f7f7f38717f7f7f7f2f7fd5031517a32a7fe47a8080ecfafec5f79096808e80b7b7808080807f7f7f7f7f7f7f7f7f7f7f207f7f027f7f49808080bc80954328a980808088948a8099d07f7f7f6b7f7a6f7f7f6b7fee7f7f4c7f7f7f8085ec4deeea7f767f8d9dcc808080808080808080808da880b5fef1f49bd3db96e702b1808080aa9080f2c9ed10296406dbef849489072e2bfb000b2ecc7f0702d34dbcd27fd30e808080808080808080808080808080808080be9d8006ec80d7bbc97f7f7f7f727f7f7f7fe7d7e9fee115fed7198095802a82808080804f5f183f40217f7f7f80808e8080808080807f7f087f7f7f7f7f7fc618768085b4f8e48080808080918080c380d4122ff87f7f7f7f7f7f7f7f5a7f7f7f7f7fceb8d96e7a7f7f7f7f54f07f237f7f147f7f7f7f7f7f7f6b7f477f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f6d7ff87f7f327f7f4980808080808080808080808080a6808080807f7f7f617f5d7f7f7f2f7f686e7f7f7f7f7f91ad042cab397b7f7f80808080808080808080988980dde3d11cfb80802cc6848082b6808080808080b98080ba8080808080808080807f7f7a7f7a4277527ffa14091e521f7f3d7ffc0e15496165bad0018ba3bf999cb40301dc08cfeec7c0d0beb8e53e0c4a37e94365ed1305001102f90a0202fefb22281c2b360dd5e8dcefc4959d80d7cec9043863d9f1197f7f7fd6a3e52bf30e7f645a34233acfd2fafe0913dbe6afea04e2dfcdae462719d0b199c2c8e1442421e5badecdd7ccdde79dc9c9dcd7a7ddb9a0ddc3b4c500d3e4e1d6e0eef00c0b0334301c07d4ed017f6b7cfe1306d8e5f0d4eef28094d293a9ef94cffebcc7bbbfa6b41de9f680b32395e7f7b5e6f7c0aaec39403a2b5052413f40050c3ae0140ab5d50dc3eeddefe3fcbdb089ccb4c3928f9c2869595e797fcf14fa10f3eacec5c9d0c3d0f3f4e6f8faec01f7f9808889d88ca407cab994c5cc18441f92c0dffd9ce0d0c5ecf7d3fee2ceb0e20c0822504747281d5c381a442c2f53422e585e29232954213d0207efd3133304fb2c1adaf71e011555f9fb03070b08fefd00130d17fd1a1a16315cf809c32ae5cefe01b93c0cf301021011064996dbdd9fc2f59ec2f7e6eabf3428f416d6e6123d5c1f207b141c730deccb1cd9d8eccab6073af7fa3b1105390e1b37151d150c0ffae6bdedffd7ceedc4d4cb09ecf218e821163b1288c8a8bfebecddf2021038370004410714553115d11c4021485467ccf04ac8e133cec83240243e6e646d6b5532111426422f1c2b25d2001712fe1a0aee1807cd035be0075eccf13a06eaf803ecf619edcf4b34283114003164154e0e3c42013422ec130eeaf6fe1d0b28241f32591f7f7268240d1a66253d412a17153424171d1c140e1d092834dec9cf07d5fbe21521cfc1c3cbd3c59899c24b2b5214f91dd4d8d5ee022ac6d6e8aaad9aeeaf21f2bd1c07c34307081c02090f100c0bd6bbb710d6d7f0d8dee0ee14f01529d0f605191a1904fa09cbcdde2bff4528f040490243340b382bf014d293dc150c0312f21c2b0514baab02a493f6a180b407f52ef9e51f09ff183217514e58534a2f2cd9e711f4ed08f4bfd5efe4eff1f30dd6e212e1dffae7ead2c695a5f2e0f2f1d6f5e7bed01cda1d15f02531d74521fd0924f61b32e8f0492d232d0125323320445767fd1036cdd10c1ff11222dc0b04e20607e5f522da0022d1cd22203544201d59321ecccbbaa7bbd0aa84bd102438071841d9d30919f7051e1501090120341a242a1f37fee6d209e4daf8f3ffd4e2f0c3c2fcc4cbfac9d905ea0a29ed1b3afd1e3b9d2857802a3e80e08071221580aaabe4e9a3e08b80ca808007a7807f7f7f7f7f7f7f7f7fe4ff0ef7d9f20cfd101ae1bde7645980808052ff8df222997fde1480c49b80808080808096f917e9d545623b5c8e9581808080808080808080b2a6c1a5f5801b02bdf4872225b53906279b4244137f7fd8d701ef7c667f66627f2fad2969dc487d5470522f5b642e4f7f7f6a808080808dc780808080808080858080a780a27f7fdf617f7f77102054265761547f3d194f6d6821645d05e17f6f4433b1ece8bbfc7f80ac80c327807fdf807f7f7f7f7f7f7f7f7f9b0fdf7f6c497f7f518080a38080f280808080878080808080808a09081fcf92db18fce796e2d480b78080a30daa09808080d28089807c7e7f497f7f7f7f7f0ec4f53d54c97f7f0305221bcacdf29a80800c3f22260d15ebf719acd8f394cd93808086e0d4dff2af9f808086fb050eff0b08f90a0513fefac8aca5808080e909feeff2dad5eac5ca07f989b8d48080868080808080808080804c12ebeab7d0a59de1052234e7d1fdbe9087143419b0d1e6cc9dc8b2bc80b1be808080801410082031dedb06da8006e380cea08080801d181d18ddba838080151b161601f3abcadb053416d2dbee9b8bce838080918080808080034752a4db30d593eb142e380bfbddda00015230d619e7e50c0518b58680808080808080084240c0f0119780dd38302b4422f8060eea052c041dfcdfead7c1564b4710f541f4e307fcf1de10f2f1da090f1941320a2008e2ebd9eeedebdcf8feb8c1b32816051df0adb68080031101ebe6d48580807f7f4fb8edefe480c19fe7f9290528317ff60c5267fb474edee5298580801493e58080b510f1ebf007fafcf4047f7f7f627f7f7f515d327f357f7f7f5d657f6d757f767e7f7f7f7f2632781e142c88d2fd621b447f7f7f7f7f7f7f7f7f4a7f7f4edb2e20617f87127f8080e77f7f4a4c37f99ed71b929bc0a4b1c1808f86804c7f80507c90a9c01c51212ed4a98080807f7f7f7f7f7f7f7f7f414e52263810878b9a5bdc80e4028080de808eb9d588e9a1808080a9bd98ab908092b794f61ceb1864560028217f67377f1bf79a03fa80a784c8ca8c809080b991a3fe0707eff0e07f7f7a7f65711ffa1c272733f7192380fb09e5fba63036bdcdb804badca7ddf8060c04107f77477f477e5f387f808d80ad90808080807f7f7f7f7f7f7f667ff47f7080df54808080808080808080808e801265f1c922e0e3c8c37f7f7f7f7f357f7fee0ee701fdf7f1f8f70f7932772afd802980804f537b5ceebf7f24bebebfd498805a09ff327f7f7f7f7f7f7f7f7f5b39577f7f740f7f7f80808083808080808024497f84d47fff10fb7f7f7f7f7f7f7f7f7fb280801d392ae4efeb6d697f7f7f7f787f7f68fe7f7fe3292cb015808090a5c407809e808080808080808080807f7f7f7f7f7f7f777f7f4f081644cd6748ce8080808080808080808080868080a48080807f7f7f7f7f447f7f7f583d10d238ff5e34d7808280a38080808080367f7f80f85a80808080808f8080808080809ef8f7bebdcf80808080808080808080aaaad25a698010588080820b14401e80e0d2dc0366537f684c4f7f030e86c796ebfa10b9b0802d312fdcdc5bbcd72dbfb880c2808012b8967f7f5b7f7f7f7f7f7ff2f9f0f8f7ea0ae5f580808080b09080aa80dd06e73bffad2718fb06bcf5cd8080808080dfd30b13fe3b420c20aad0d58080ac969d88af91a9ffc6d0c6cafcceab93aab5b4f7f9df01b107b6e403251bffbd1ecb5b647f7f7f7f00bca828afb707e6b335031945e50f78692a8080808080b3808080808082808080808080f3647f6e7f7f7f7f7f6a1f27657c3b7f7c1c556b6243e77e49317f49512aaf257f8b80f198e4ddc40303dffcaa7f7f7f7f7f7f7f7f7faee842645676691b108085809690d4808080a280808080ad8080b4077e2012e60ef2f91eecc86000bd3029eeebe4dbf8f2ef0e80a4ad79664b5023367f7f7a9cc9a408f0bb56450b391a3c562726291e2c34472945394535f15110b8cccbb4cfd3e4194efa1d57002977115bfae8e4ecf5eaf3eff909202340795f151c3aa6c88ce0b8b9c3b1ea382a505f27315cef04ae80a8f880e6f580dbb0cacf06d028cab8e3767f7f7f537c7f5875d1b005c995f0b687f68080d38880c58080a039545e27787f343b7ffff5be4f300414001efcc6df2fcefeedec238f8098140f3b3bfd303e2d517b285245527f290400350c512a044900ed342f080a05ee0314567f0a2e4c581442312e0afde7d9f2b70cbc80f18080e18080a1071e7f4a344c2234550349164d4c201c206d7e203937ff0c792974d1c9f0bd9edbb7afef0a2211ef0e1c262003447f7f405a31302b00292c3a567b7f54607f6a0409510e19261a2fd9a89200d2f9b9d8db7f7b71270e3a577f71cfcbd885b180959bc509f6e5232e1a3b040487a480b5c7afd1f4aff8f801fdf602fbf2fa7f7f7f7e63607f5e77c7dae1423e1b10f7f7443d7af4eb03324e1a81c4b0b6131592f714584037465f3b7f7f64f1ff1026455e25311741414f584c440f31175556094234241b0efe8080802b02f7bfe5ed8091d3e94a298de9f3a5aac1c6f5cab9aea71643484f7f6e3154618caea4de07d9ddf4ccd80380e6e98c9cd48080aa8080c4b080a480acdd01fce4d5b5ac0c0f272f0d0afa072114455cf92131f00f15d280d1a88ae2c480aca18080bbeff901a8dff0597f76351f2651587ff4edf2f7dfccd9f2bd0aea0ff801d1e0e2ecd2d5bbb4a4bf80afc57f675a59360c7f7f7fccd9cef127e1c2c0a1fa1c2a123d35eef915742b077f7c1b5b35242403d8ebd9c3eac3f30310eb214b49f60b0cab808023bdb7bb33c50b12080103f102f903a6c9c1c1e8e15215ec80c1810c29dc06f30e808380ebd6c607f7ce99d780b50280adab80808080e2de8001e7d0584b3b7f4f7f7f4b4fdcfaf9597f3a2d5fdd9aa780f41180c70eb203a99d5a7f6e7f7f3e80343e007f7f1c333ca0ba80056bf1ff0aa880808080c4808091807f7f7f7f7f7f7f7f7e7f53807f71476b430a80b8a9bf17be80af80127f627f7f7d7f7f6780c3a480998080808005f680381e80fd0c8080d28000ee82c4c28005d5d6617f6c7f3e09ece38e25fd07c7d79c3d0bd07f410d4840ee04fe5418e21b0d0010c2e265000e5f2cfff57f7f7f7f7f7f687d7ffbd4800f2bd526f1fefb3215477f48f21963e79ea91c07d7fe1809065b0bf93d40140fc941f3f642001c372f5deab77fb1cb5580983ef50aff0509ef0c00f94037f2db021881af94ef9dfcf30434b586125a03c54b6133a2b8808080a39b80ab8080b9eaa99ecee49b9dabdbe9b7f4808ba4808080b1c0fb11021a7c557f9580cad1e1e349470677196ed08082ad809cf280891097bb8880be1ddd4a7c225b06e029d4f11913a8168080802f121d25f42408ea188080a68080098080153e3032502f33713e367f2c12562ee30aeb0c30787f46497ffcdd168084a5b5d8b2d7ff12320d212c172b1dff187f3f4506d4bad6808002a3bfe3bbcf08daa6dddbf7f0143644327743202ccee90244462f7e5d7f462538df147f808096a59eac1328b8dbb8ff30e2190cabfbdac9302df62bc18eec7f7f7f7c6160715a77340c064f4c51332a0bcdcac6dfdeed2aeffbf809d7e2e810f5bd44fa06f5eff80006f9f908504e3551572b7f2cae9c9abbbd9dc1dcc53223254d0b3d3eec1fc195c5d492cba69de09db2bbc4a2ecc1858d474167722530712f429b8993da9980c380809480aca095ab9980800326e92b0e13ccd816b5aaa8dbac80c6a280ffe1e7e3f5e60fdcb8ddd9e705f01f859d3430252f19034b250e45d0c0b2cfb320ada812bb94a504a2eed5b3b765465a334d7f475d777e553223215edbfb14a08da1b99db5a0808fd6d7191ec21eade50af511311303f7d0dede7f7f7f7f522b4c7a68bca4c600def8d1e0d114f2012a3e362539152a3b7f7f63407f38147f7f7f7f7f7f7f7f7f04edebd3d0d3d5d19ef0e4bfddf5c7dedac77f642ae6e9807f6934f1349b7f7fb37f7ff4d17f7f4b7f7fe5607f808080c5ad80808080f225000e18f41a1024747f7fb1eaa57f647f80aa99e27f7f27ecfdb41a6e407d587f7f7f808080b4c2808080808fa0807f7f7d7f7f7f7f7f7f7f7f7f7f7f7f867f7f2b7f7fee6afc80808095c0808080806994c6a2f0f4cdb280804f7f807f7f177feb8041c2dd56cd8080807f7f7f7f7f7f7f7f7f7f7f557f7f7f7547347f7f807f7f80147f80808080800f80808080a75e803250a0ec1302db2d9a787fd6317fe96b65807f7f80ea3a8080808080a78080808065d7e9647f7d7f42ef7f7f7f7f69077f7f7ff13dd9497f14235bf2e4f4e2de5cd51726de3a7f77567f7d4460dd7f7f2d7f7f7f7f7f7f80808080fd80808080be4ff73f7f7fdea5a18caaa5a6a516808080bf8086af80800a9d858080ce0ed4c1fed4a47f7f7f7f7f7f7f7f7f0010ef02fffdf4fbf84f288078c28080808012f4b72ecd9c7f375cc1c4b58080950f32807f7f197f75167f7f7faa3553fd8d080c435ceb80802d8080bf80804730617f18ea482a4558587f521c7f7f7f7f00dd807ff87f7f7f6e7f1f7f7f7f697f237f4c49056e7f297f6a7fa28080b180caca80808080808080808080804b7f7ff07f7f7f7f7f7f7fd77f7fa57f7f09e18080b18080fa80801a80802a80c626a580313044003a47517f7f7f7f207f7f147f7f71228380d880e55f222d80808580808080808080808080808080c8a9d2b586b980822013d3878080808080b8f2c8808080808080808080777f49447f7f7f7f7feccb8b01e0807f3477cdc51288bfbf808080bc008080a8b7597f52bf80838080bfc680cc7f44567f0c3c7f7f7fecfaf0fcf5ff07f2f9f52e003449c386cbd727afdd3e86f17f344680869b93be80f206667f7f7f7f7f7f7f7f7f8080b680a45be37f6d978080f39d80b684ccc5b8344b38103bc43567fe7f48d37f7f7f7fcab8807f25ff7322487f85687fbe7f7f2f7f28daf01e89da7f0a6e838087e2c4e5dd80808080808f83808386807f7f7f7f7f7f7f7f7f7f2c137f7f207f7f7f80a5d084b5c2808dac80808080ac0824687f1e217f2e4d7f797f7f7f7f767f7f727f7f7f808080ee80ae47335380808080b2ed808080809ad182b70c17fe4fd5ca17c6d3d5f8d08e8080809a80f3474c558096ca8080808080807812183c80f47f283933b6b858bdc27f3f20),
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
    .actor_error_o(error_actor_enc1_standard)
  );
  logic error_actor_enc1_extra_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(2304'h282542e5ef10211a576a17134dbc0574f50b2c0e321be8091204137f397f114938bb0aea912933de75038008804e144930021d47072c130b1714080d160c4a332015311b2a424648072a19db0304fce2b210f61e12d30a26ee2f384d381b1af0244a2c3ae917f6cb0536dd28e41efbdaef01c2d7dbc7fb9d22efe817113ad96080f66b0b80449869734a1f62cf802280581c0e7ffc217f542f80aeaff5eddd202e1a7f097fd4e3e22406029ccccae7ea0033201939521a2b1beeca10e31e074f0cc5e3e7e2ea35034302e3f50fe1217f1e0a5fdaff17f90f20fd2dfe300280aa8033284f13f8fc430347360c2d070cfad3c4cd170f0800e0071701118080808080808080d72c03261a0115321a3f7f3e3e7fdf4524092a80808080808080884f),
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
    .actor_error_o(error_actor_enc1_extra_depthwise)
  );
  logic error_actor_enc1_extra_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(8192'hf9d9bf1dff08251cd1ddfbd8f2e51f060decdfe62118eef3e703f3c6f7e608fd087fb7205d80bfb12780bc80357f7f7f2772c59d1c26807f69412b2629a827800f2e1c983480e4800b36807f41c4fb3680fb1d5d7f810bfa7f80277ffcba017f207f24803680b89a801fdfdd0bf46fee807f80fdb6bc12bd7f45097f007fb95b03b3800b037fc540d90026efbc3148e13b80d739eb65f119c2490baf16b1e9e725bfe8cb8065c97ff80004efa4b1d1ff7f698c274beaaf971a7a5ff10bfe8026faaf8080c94b00eed37f80590eb280e880f67ffdffb765e41eea0080e2b95b80f6e3d3db86051255b004b6cbc3e1ca9c0b0fb7dde0f9eea1c9f21efa12d9c1c7c7dfd59f80c31bf7b87f802cdaa1a480accee591d03039028810358e118028802980bdf7807f5d7f097f807fb7cc80afbd80fd5bc4d37fe5f27fba95fe8020808514807e7f8080a52f807f800cc47f7f7f80ab9a5080807fa580cb4bbf8059c81085b8d08f7ffb53d6fab9fdf2cea89819b0e02ce712dcf4da4718e10ce0eceff18cabb4804e4a7f1f629b54e5f8943b1dd429000de233e1244849b1fec62986ce7280f32880e1c19a80f0801fdb7f7b3658c0f92a87804e5195ede5f0952bdea3eea4348021dc80b210804cffba80808080758085804d1c80808022ed8065c280809c5a8064f08080d7b1689a80808080fa7f80be803601808080a51f80cc80c30b08e4ebe5da03f5051011f30de6ed0f00eaffed0cffe6f4f605f40417d9f2fe7f94e05c92f7a30ec2dd80431d7f4c126df5d53905803e70b93abfdba81780efe21ffcf142dd5417d4cdf306e11e43da4a49f477e29bcc6db4250c07c0e62980c899300628808dc8ca3335ebde83af919f7f842889fa4a80ab80dfdf801989942e0480e1a8808007dcf33314226721b1f7d79f5057a98b7f80f0450bdb84ae7f7f12808020a37f63663a8080167f80697f9ed98a498080807b5820067f80f2fc07be18801a0d9f80308047f3de808080b9448d80e3550b80c5d82aed80038e05f8803472299095a7b46ed003b7cc80b8ab5d0307d7e97f80aaa995df807f80db7980d27b80e08ac980e88011ea7f6e444715a77fe480731980e8c2c48015807f7f63afb274327f5035d1c925433b7f7f58927f857fb3807f7f7faf097fa67f23f51be5e3360ee8dfe4ebd8c94d2d05fd61c32a0ef7d7eec912d9f604fbf21193ef020bf3cc07d317df35f8f610282a21f3d7c63b19c6fada11d33c04d6fdc2cf7f96803f80af858ea3c080654a7f407f7afcb61849802e64e17f07e9db01803dfbf980e9a1c27f8803f0b1c87f7f177f7f8002d8d08080807f1d13e27f80eaf5809979807f059297e09f7fdf80808080807f80b4802d0e809180801580bd808d91807d807d0b808011b27fbf80808080807f80f9806b2f809480b506803090),
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
    .actor_error_o(error_actor_enc1_extra_pointwise)
  );
  logic error_actor_down2_standard;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(147456'h0302eff7f5f50d04fafaf7ee01f3f7e5e4e3f002fb1d0ef60004fce6f2eceefdeef9feefdedde3efedeeededeaeaecf5fbf9f0f4efe10deef810fbfc0deff812ede703eff2f1e6d821f90323fa0518ede908fcfa0bf8f904eaec10f2f11ef5f80cf1f7f5f3e901f9e6f7f3f305f2f617f2f10eeaeb07e8e609f0f4f2eae815f2f019fffd0eedfc06fe002305fc1e01fffcff04f8f403f9f309fff1f0f3f3f6edede9dfefebf900f5fafbf50df1fe1d050b0bf9fb0df8ee0bfff6faf0f802f8f1fdfffefcf7e50bf0f410fbfeffeff309ebec0ff9ef05ecf118fdfd10f400f6f0efe4e5f9d3dff6e0cbe6fafbf701f6f305eff607f1ed12f5fa1505fb0ef0f408e3eb05eae1ede8e8dff8f4d5dff41cf6ee2000f724f6ec18fbf51ef7f51bf6eaf904070a0b0c2f0f10e0d2cbe4d0dcf0e5d31013ec0cffe104edccf9e0e2efeef614fdf007fafc0b0bfd2301040df91446282031222c0b10e801ede101ecdc34211e441e3e423e2e08decc07e7d502dee31f10e81e05dc1df2e3f7f5d2ef04d8070fd60beff700fff607fef72311f61ef9e018f6e3f9d3d7f1e0f30808fc12f7dc08f8cffde1def6e6eff5e8eaf2e2e6daebfac0dcecd3f81ad9cdcbe5d1d6f4f0dc15d6de0aded0eac0cd1206e610f0ddf7f2d9eff80e0b24081a10eef8dae9f1f4ee0810fa1df4f2f2e8e4f2dae60f05dffb00e101f9ccebcabae7d7d8f6f4d61cfaf217faf82604f6f5eced0301170201fc26f8f6fccae9f0c9ddeacfc9f1dfdd0bf5dddff0f901fa041402040aece6ddddecefdaf2eddcdfebd8cbe6d8e3fdfdff0200fbfb00fdecedf1f2f0f0f0eaeff5f7f5fefdf9fcf602f7f9f9f5f7fdf0f7f8eef2ebf4f2f3f1f5f5faf4effaf6f0f0f8f5f7fbf0f6f9f3eef2f60100fdfe0203fdfefdf501fbfafbf9f60000f2f9f0ebf6f4f0f4f5f1f4f5f4f3f9eeeff0f5fffbf701fefd0101f3f2f1eff1f2f1faf6f3f2f6f5f5f2efedf1ecf6efeef1f3f4f1f5f0f6f0f9f9f3f6f7f904f9f304fff203fbf7edeef4eaf2f3e7eef1fdfff0fdfef3fbf9f9eceff5f4f1f7f6f1faf9fcfaf8fffcfbfdf502f5f9fdfdf7f4f3f5f9f7f6fafcfefef6fef1f7f5ecf9f6efedf7ebf0f4eaf4f1eff1edf6eaece9eae7e3ecebfbfcf3f5f2f7f4f2f0f7f8fafdfdfef9fdfcf5f4faf5f8f3f0ebf3fbf3f3fdf6f7fcf2eef4f8fbf5f5f4f5fdfbedf6f1f0f7f0eff0f7e7fdf2ecfce2dffbfbeae4f2e4d6d8e3e0e61b193008f70d01f80df0130cdfe6e5dc1b0e08121909f607010805e2e4f4fdf7f5fdf6f904111c00f6fffaeffb3426220309101817113822242511221f19181d1a1f0d070904f914e1dbd0f9ecd702f3d4342d3a17082f0b1f35191b2406000206fd0dd3dfe4d0dbcae6e1c8141721160efe15150e0af529f0f91b05e82201eafbebefe300f4ebe8dfecd8dbdae2dce9341f241ffa1a0800201f361404131809010f0b1404e5f8f50ff6fc04f3edfbdbddfaded3212a3212121e222d2d080412f2fa17f5faffececfde9d7e7d8dfeb12fdec03f3e5fff2fae5e4dedee7d8e605f61f2730fff809fcfd0edde3f4d2dfe4dad4ede7e5eac8cbd2e5d6cf0a1837120513130f17f6f70802f1fa07e700000a04191503f5fffbf3ecfcefeeedf0f7f82412281c26351d132bd9d9d8dee5e8c7ecd7d0d6e2c4dfe8d2d5ccf702f7ec09fee2f4eeebd9f3e0e3fcd9d3d5cbd8d1c0dcd4aabfcce6d9f9ecd903cec7ead2cccccccadeb8b2bdf6f3edf5f4f3fdedf3e5e6eed9eaf0c9ced5e1dfe2e7dce8c9bad3ebf302eaeff3ebf4f3f6c8dcf0def1d9c6c9fddadc0cdcf5eedbd8f0f3ebeaf4e4cdddc1edfa03ebfdfefbfdf1d7afebe9a9dceba0cc03fa0d06f8ff00f803ece7f8fc10fdf9e4fdd1ededdee5ecd9d4ddebecf216edf9f7e5ecf5dceeefdeddeedfebf4f80cf1f300f8f403d6cfd8e6e2e2e2dcdc0906071208fb0d0e000c1223394239181a19efeb04e4f0eeeff5e4111a2604291f0e0e0ae3d3cbdad6ddd5bdb9e8dbd3f2dcccdfd1c80700f70103fb04f804f6f4f0fcf5f5efefedeef0e9f5f7f3f6f6f40200fb090004fdfaf10b07010e0407f6f8fb09fdfcff01fdf9fcfefd01fc010409f6fdfa140c0b140c00fff8fafb0300fa0400eaf3fa0101fffefcfeeff7effdf9fe060002f9fdf108110d030904f1f8fa0e0904080a03f9fdfafbf3f400fef8f7fbf2060909030007f1f4fbfc0109fcfe09f6fc02faf3f7f3fdfee5f3f001f8f8faf7f6ece7ee03100b01080ef70205080c10fe0204fcf8f5fdfa04fef9ef0507fb0501fd100c07f7f0faf0eefbf7f703f4f800fc02fbff03fef2f6f1faf9fbfef7f9f8eef4fff7f8f9f8f8efeef0110f0b10100e02060007040800fdfcf80003f5faf9fdfcfcf8f8fa02f701090c0df4f3fa010004fa01fff6faff08050200fb04f3f3f21110130c031804121105fd05f3f1f805fffcfdf605fdf205e1f2e907efff0bf601f8fbfb17201512181a03111010120f2e1c180aff07f7fa08f20510eef20f33261e19140019120e0d0a0cf6f900fd03fe120f1c17162dff0c140c0c190cfe0c090c20060c0c0c070df4ee0208060bfcfe0ff7f3fdeae7e2dfe8efe6f0f4000a12f5011304030e00fdfc01ee0512fc08fe0afe01fdfe12041cfcf6fdf5f1ff000203081310130f1f0805030214fffe000afaf80c120b15050100f4f9f11a1212fdfffb020902fefd09f4fd07eeeffbf10303f7f20df7010a01fb08f1f5fdf904fe03fb04faf7fce7e9ff0701fdfe050800fe001f1a15f4fe0bfffc08f8f5fbfaf802f90600e3dedbede0ddeae6e204080cf8fd08060909050e0f01060f0e030affe3a7cebfc180918b040101fe02fcedf3eed5e5eff316e3073001a9b88aa4b9b197b6b20f061c1205f6f606e411f7e7fdeddaeaeec3d1dbb2fadacaeaecdf92adafb7f0dbc0b0a53b2b1b4a5346343d3ad0daccf4dbd2f1ecde241c171f250305f6f1e7e9e2e60adb0c12eceae9e80609e5ff06f7d4e2f2e7d5edd2c1d7dde4d9f5fde4f1ece3f703f0fb00f1edeef07f7f2b7b725d5b6145f808000908ffebebe5bfa5a0ecf9c80a11ce120812092124140810dfebf9ebf5efe2d1d9ebe8e1f2e6d3d5b8a1f0f7031d3527265131fde3def1dae6eae3d6ddcfd3e7dde1d0ceceedf8eee2f8d8dde8cf6e5e6d515e49273411fa1422282339231d15dad6f5f7fef6efd9c91f11093e070115f3dfe908f8ee1404f5fff723201a15160f1b2606fdfdfffe01000508fdeefdf1fcfcf8ebf1eaf1fcf1f5faf2f4f4f1f2eff0f0f2eef0f5e5fafbf7f801fdfdfafbfafa0303f9fd0301f8f3fbf7f500f4fdfeea00fffcfe010208020afa01fbfe0201f7fffaf0faf0f3fbfefdf9f4e5f2eaeff7f2edf5ea0000f8faffff03fc00f1f9fff8fafaf9fcf4f2f8ecf0f5f7eff5ebfbfffdf60afd010400f901f6ff07f8fc02f80204070404ff060703fafbf3fb05f5f0fcedf0edeef4fcf3fbf5e9f4f8f0fe09fdf90aff02faf80202fb00fcfbfffcf6fefef8fe04f4f5fff9fb0603fd0403eff2e9f6f9f2f3f5f1edf6edf6faede4efebfcf3f0f8f6f501fced0905050606ff0103faf6f8eff902f700ff01f1f3ecf2f5f4ebf0e4fef9fd01fefc03fefafafbfb0200fa0107000601ffff0c06060305ffd7d1e3d8d1dfe2d4eaf201e6f0f1ede8ee2c210933240922211b0ef41906f709080101e9f9faf1f8fdf902fde5eadff1e1e1ecdee205081711f31e07fe0f220218f20f0fede8e51903120f0c0bff0c171c110c0f0f0c091312dbe5fcf0e6ebedfcef1c1b201412171c1f281e020907fb13010601f7ddddf0d8ccfad6d31d151a190b241d0f1f0e0e1620162d0a1f32f4eaf0dcd3e6ced111f1f5fdf5eef3f0f2f62e4336322a302a3c3b181f331716311625450c05fd03ffed1816fd0bdaef0106f3fb17ff0d070b0bfe00fdfc0608091008fe150ffb1bfcf903f9f9fff1efeee5dbb6ebd0bdf0d4abf1eee7f1e5e9f9fcf857463b403224292420d9e7dee2d6e3d5cce4d9dbc5d9bab7d5cbc30bf7080a011c090528fdf900f2f80df5f80e02fcf8fd0905f20007e9e1dcf9ebea01f0ea200a0a240c1a201c17fc000407f5050f1113dec4cee6d4dbccdec0bdc6c5d2dee9d8e7ea0bf9f202f9f30ef9f9f6f1ebe6f4ead9f5ed19ffe61c01f8220aeaf8f2e30cefdf02efdcfef0e80900fa1912fef4edeb06fafc07ea0006f4e403f8df12f2df0f00fe15fcfb1900f60df8f41108f30afcf823f3f722fa182c0819e1e3f0f0e6d0c6e4e9e6e2daf5e9dcf6f7e9fcdfef1ee5fd17e8fd22fae927fbee2204f8f3f4f6e7d802f2f5f1d9d9c6d3cdc1f6c7cc3f15f2230efb1f01fe17efeb1dfbf9271501fadde603dfea00e9e4d1cecfd6cbcce5d3d00805fa01fbed0e0e05eef800eb04edeff9e7f5dde4f6e0f30ff0e705fe040101f002f7e813fcf013f3f012f80d0be9e403e4fb00f7f4d2bfd5f9f301c400e0e0d8e2dfdce7dbd4e70904091b0c1e1e100ae2d1cc00cedb08cceaecb3a9d5c7c0ddccb3b5a7a6d6d2d3f0b8a8f6f1f700fbeefc0aec9fa0b1a9ad9f90bbb129fd012e0e0046151605eef6fcf2f512fffbe8e1dad9cfdecfccbc402e114e461b4e3a23f4e4f10702f30bf9f7e6eeebf4ded9d4e7d7180b070f06092609005527284c341a56362d0a0dfe1607e00f21e6f0e4ecefecebf3ecf4fbf5b81607d91429e322131c21011c2d1521dbeacac5bcd0e2d2d3e7fbe4fa07d7f2d1eb494c1c40422b4a4c3120f1fc27fe02220811fde1e4f5f1e7ebe5e5ccdadeb7dbd4b6cfc4e6d0dbd8e5e5fe00faf9f0e702feedf1ddd4dfd9e4eec6d9e9c4d8b9ada2a2baba91beae330e1d37141646151310080216040a1a061200fefa000402040a03fd0d060a0503040e0febf6ebef02fbf4f8f60209f8000dee0900f9060d070a0c0b140a0204f9f9fcfef300fdf3f3f9f6f9fdfbf702ff09fa000aff0a05070709fb0105100c0b0a0bf5eff0fff5fff4f3f5ff00f9fef7fafb02fef101faf2fef7faf8fff7faf6fdfbfef702fbebf2fcf2f7f4f1030907110106100d08170910130c09120e06120f01080401010af4010efc0c0a0aff040a100eeaf6f3010908fa06ff020902090a07001607f8fcfe05fef403fef9f6f7f8f9f6ee0801effe06f9030403010f020304fe060401050f0f090e091305080e1a11ebf802f7f9f2f9faf00e100a1a17051c1609f7faef030b0503fb02fa010603fcfa031105fbf30109070308ffff0c0e030c1709071a0f0f1b05141c1415170e14130bfef40f14f9fdf6fbf7f70301f702f9f7f3f1ff03eefdf9ebe000ddebf5dcf4e6e301fcfa060900fbfaf4fb0801041311f5fff703fcf6ff0702f9030414331c2f3b3e222c2d111403fd0801fc05f401fdf9020303fafafa010b151dfd1c171814090af50c07f2fafcfc0103fa000604f2fffaf7f0fafefa02edf7f7fafd02f6f1fef5f4f003291a001d1503100bfafff8070007fefef7fbfcf8fff6f8f6faf11b211827252b2e242813091a01071003fffdeaf9fdf0000319f8011007fa0911eff2f8ed0e05ef0108edf7fceb0cfe110bfe0804f701fdfdfdfbfa00f5fcf1ded7dcd7dbd6d5d6d4f900fdfa00f3fefef92d221d24212026192802020300f80701fcfdf1ede7f5f8e6eaf4e4141408061711040cfc09150b020308030504e5f0d8d8e9d10df1e1c2c1b9ccd1c1c5ccb447150847170a4c210dfdcdd9f2cdc5efe3bae5f3f8f2f5e4fadfebd3e3c8d7dde0d0e2bc05d1d300d7e2efd6ed111c02f5051ee912f6fe04eafcebde03eed0e6cecddfcbcbf0d5da9acbceb7dfd4a9c8cf69333b68282f7e091ff0eedaf4eadbf7dbded7ccd4bcccd4ceddc50dfff40c05e6fef9f13f3f32672620482b2607f4ed0bfcfa131d0bc2bfb6d9c7c5c1c9bc21e10610e90937f8051e0ef91d0efe1a0b0aa4cdbbc0bf89ccdfccffe7dceef5e41408ed432c3c49290d4b4816f3e9edfef3e1fbe9edc0b5c4ccccc3c4c0c5bdd1bbbfc9acbcb8bacca0b6bea4bad2c3c9bfe2f8c8f10bbbd0e2d4c5d1cfd2d9c6cdc6bea4a7b988a0c1bc972810fe2511fb24110202e2eafdf8e0e8e8d4e200d3f3efe7c2bcc01e1f1d221d12101223e61408172434f922230c16dbedf9f0f811fdb6b8b9c8c5d5c3b3bfbbd0cec8b9aaa8b8aa0e16f718f7f6ea040bdfdaafd0b8b480959c08f905f808f5eff4f3c2c3b9bdc5c6b0c5bb3b2721391b10281c14e1d4a9c4d0da80a7c3f7d5f4fdecedd0ebe432272b251f150f2626deb8ddc2c9ddd0bec2ddc8e4c3f6e4b4d6e7f1e6cdc8d0d7d1d1cf382f211c1c2010132610c6d823e1fbfde4b1f2ee07fefb13eefd0214122830292d332c57cccdd5c8dcb8c7bbbdc5c3d0bcd8efaacae1030103f9fa10f9fa030c101cfe0906150f0ddfeeede0e4dcd3d8df1f3042141123f30c07313d212b3a322630301c070af5f5f6eb0003f4f70beffc14eaf204efdfbdd5e0d2cad2d1f1d6f0ebd2f0eee1e012ecd7050f020afbeb270802430b063c060ec1c102e0db02e9dbe70812012526060b27f816050f43f6f548fb0fefe3d00df4ff1d11fad9cd9405e4ce13eec60209001e40541d2d371df5ec5219f13427f5c4c7b705e3c413efb81907f52707fd24f10901dbcf22fee74e03fdf3e4c2330be213f9da24001135150a15fe161108c74d26e51f0ada4121fa5d28f4251bf65b3f346f53465b403e5a1d18551a0f411701f9d1e01af9f036f5de0e24ea4033ff3c260fe8bad3e4debcdcc8bd0df2dc3237ff1509ecebe5e21a12ed1c19e3230d0d3e1afa260609370e103e06fa36f616e0ede6fe02e706f6c12a12e5464ce90c22d0f2e7f44006103a080b030601ecdefa0ee8fc0f010f34361f1621221c0be95622f0471feb2c1b025e211430130714cfc2e2f1d71af8e9adbaa5b9bbc8c1abc23404ef3a32ed5b3df812d4070cea2bf7de00e2e1e7eedee8e7e4e2c99da8ccbdbef9d5c0c9c2e8c5d1e3dde3e3eddd1b03e3e301efd70eeaf0f5e6f6f40203bda5b3c7bcced2dcde80808380809a8095b41814d71d3912412920c0abb7c7cacfd5dadbb5b0ba99bac0b6a7c2fcf8db02fdeb0211187f7f597d7f71676277939ac1d2abc2dde3dca9a8b6b0b1b3a7a5b5dcecc50206dd502a331c08ed1a09030115f1b8a1c08b97808caf94e1e7f0f2e3fcc1cacc7f4d2d775047624846c2c0bee9d7d6e2dac4bcaec8c0c0cab3b9d3a59f8098a49e8490a6d9fae5deecff04f200a9d9bdb6e8c5e5f3e69abfa2bbc4afcbd5bcacbaa28d808c96a09924290c3f270c393019061105f6fff9ff0c15dacfc7cbcbebbdd3da1d170f17130d1e171200f0e5e2ded5d1e4fad8e7dcd7dfdcd5eadff001f4000b00e8ea04dbead2fbefd7dad8ea08f7f3e9f7e2e8eef4ede1f204e8e9f1e0eeead8f6efdeeaeff0e2dbd8e8d8e2dcc7e4e241302d34331a2c1f0b06f1ed130900f8f8efea06f3e8f9dfebeef91a161710180c0d150fe8ebfae7e6fef1f3f9ede3eff0e6ed01e3ec221f0a3830132c3b151a170e1a180f161206d2ebdbd0f8dffc01e8f0e7fa00f90fff0afcddbfe10fd8ecf8daf8f8ebc4e4e5e1ddd8cbe808f7e0f1f1d8dceef910000104090906ff1813130e0eff0b170002f1f5faf4e0dfeaec0bfa08fdf3f30203ed112c02fb21040010f419200b15170f060a0809ebf4ede8ecd8f8dceceb0bfaeef50bf2f502fb01fd0003fffbfdf4eaf8fd0800eaf3f5fbf601ddeaf6cbd3e117352efc1210fe09fbe2e2fdd7ceeae0c5eae4ff12ceedf0cad9f1e2fb1bbce00ce1e30bfcfefeea04f2fb08f3f8e0dbdad0f1c8daeae5f013e5e70be8030bfa1406ff1a08f102fa0502fd0109fbe5f5e9e0f208e1f909d8da02edfbfbf305f2f00dfce0d7dcd3ddcdd2e1edfb04f9f31409f9120af00011f70e0af70f0eb4c1eee2e2cff6e3f7e1ef04e102e2d4e1e3283732081e0aedebff02fe06e40a02f10a04051a20061606fc0602c6dc0aaac9e7cee6f102000cf70507f71206050e0cf90a06e805fbd0e1ded1f0e9c2e6e200fd01e3f0e0d5d3cfe2e8e9e2dcd6e4dae8160e2befee11f4f416fcf707fb05fae1e8eee8e5f6edf5ecebeaf506f403ee0b01f50010feec09ee0016fe0311c29aacceb400c988c5cecbc9dfd5d1e7def35500b44d0cf1575ee735bad0ebe6cfede59dfbbef4fbee054c28f99380b68080869699a5dde7cff3d5f4f3fef30b1c02d716200428fd662f644a1a4e5e4b5f00f8f124ee01232208a591ceb6acde88bde23d2f10571a417f2240eec5ff0ce9ec06fef1cac398cdb1cee9c2b423372328292d432e2b7f7f7f7f7f7f7f6476c9110fe91802d1d8d8ded4efeaebcbdfebf724edc302f9e23a3b1956405361203f57433fb09cf0a0bce19392c8dcc6a0e4f3c2bcd3c47f7f5e7f75687f7f5809f2fc0edaf910e2f2d3c4d1c7b1cdd9ccdbaaa6d0c4b8deaac29d21dad90d1adb34f808f5c9b7e6b4e6e7cb00ce9cc7bfc8dab4c8f880a09d80808e808e805d6652554268656a7b47432d32272738504df1f4f3fef7f2fffefbf1f901f4f1fcfcfc01d7d6e4e4dd03dbdce2f6f7fdf1f6f6f9ecf5f504fffbfd07fc0304eefbede3eeecf3f3f7f2f2f9f3f704f0f3fce3dceaefeff7fff5f3f7f80ce9f702eeef04ebeef6effa04edff01f9f7fdf7f3faf8f5faf5f7f4f3f6fef8fbfeeeeefaef0103f2fc08f3fb0000fcfdfef700faff0aeffc08f2fbfafcfbfef6edf9faf8f4f90303fafa03fcf8fcf2f904f6f6fcfcf7fdf2edebe0efe4f1efe4f6f5fee7fcf9e5effcfaf7fff3f5eff8f5eef6f9fef7fdfdf800fdf7fc00f4ff09fe080af80104f903fef8f400f9fafef5f2f4f9f4fbeefbf5eaf5f9fcfbfff200fffa050a000901f8ff11ec0604fe0011f5f702f2ee04f5f800f4f3fdff0705010001fd0008f70201f40105f8ff05fdff01fa02fdd1a7cca7e295808080c0c1efc5e0e5dedec9637d7f6d7f7f627f7fdb94ae10db070dccc8444640351e1f1f1d1d183aed18362007f4048480808080809c8080345f50401edcdad3db7f7f7f7f7f7f7f7f7fbb8090b094b3b780a210073d14ff3c12253fe60a029acc03ecc21e9a84a3a294a3cba3d09580b8a18bc58f99b0dc9facc2808bf7b6a37f7f777f7f7f7f7f777f7f757f7f7f7f7f7fbeb1ddc9becac8bddda7c507a6121f011a272329213f33577f7f5f367f236778487f7f7f2c34f92c15e2f107fb7f7f7e7f7f7f7f7f7f9896b09d9caaddbadfb3add7ccccc9c9a4a2b3d3efdbded59b9cb930224212452b250b1404617f4a7f7f24617fddb0d4d2cfcae9ded3c1bb99cdcc969a808077653066655f7f7f7f1614e01f1ef95b350ef8ff060d0914f1f6e4f701f5f6f4eee7f0e3fa33270a372723442dd8d9cfd5d1d7d6c7c3ff01fbfe0efbd8f4d8d6ead1d5f4b3afd2b1d0e8c8d0e5d3c3d0b9d1cac6dcc9cfb3ceb10b17ff16180ff6f4e8d3d9c0d2ecd6b8c6c11b2e1b18111f070d14bbe2c8c6e8c2bbbab2efdac7e2e8cbcad3c0f6fdfff1f809eaebeddb02e3eb0fe1c0e6c5c702f4e005f3dfefeffdff01102cff1813f2ff00f3f7f1e8e4f0f2a4bac6c3bbcad3b4ee0e1311000f0cf4effa9dcdb3cbf5babee5afb6bf9bbfdf9e96c194f5fadef7100ddee9eb06120beef803d9fb06140802fb0c08e90903c9d9dcc7e7dad7e1e10cf903080e0301e5e72d2d2c3d36551e1e49f6fbfdfbf407f2eaed00eeda07ffe4eae3cdf6f806f8f803daf0cae6fdf9f4faf6e7e5e5eaefe3e8f0ecede6e0f1e6e703efee02f8e8e4e2eae8e5e8eff6dfedd9e605dcdb05ddd2e1f508f3f808f8f1f4e4eaf1e5f0f6dce2ecf7f801fdfaf6fff6f9e7e9f3e7f3f1e0e8eb09f3f0210308250c07fee90005ebfb06f1ec0dfbf01201fe12f8f2ec02ee0302f10103ecf4f6fef2faf7ede8f5f9e1e401e9ee0feed8e0eee7f4f8f8fffbece1fbeeeefb0ee0edfc1e22131a211613180df0dee400e4edffeaebd3ece4e9f9ede0ffe1e6f3fafffd0f050c0302fbf6f5eceff6ddf0f6fbede9f3f0f5e4e1090e030e13040b0afaf4e7f600ecf90bf8f509f8f5180bfd1402f0ebeafbe8e7e2e0d3daf80204fb0000f2fdf6dd03feef0800fb000705eef60dfaf61505f9e9e7d8e6e5dcddcfcff802f8f70402ef00fcfdfc01010904fdf9f5f8f6faf9fdf6f6faeff1eee7f4eeece7ece30103fdff03fb09fffdf9f3f4f8f4ecefe7e8f4f3f1f4f6f1f0eeebf1fbf0f0f5f4f3f1f3eff9f0f7f8f2f4f3f0f8f2f5f6f3f2f5f3eff8fdff0000fcfe0202eeedebf3f3f0f0ededf0f6e9f8f8ebeaeae701fcf9fafdf2fbfdf7e2eeedeeeceaebebeaeeeceeeef1eeeae9d9f2eff3f6f2f7f3f5f8fbf5f6f802fd0305f4ff010002fefbfffdfdeceee9f5efefe7ece2fbfcf500f6effff9f5eff3f6f8fcfdf7fcf50303ff0406f9fef9eefcf9f5fef5f0eeeceefb01fd0304fbfffd05eee8eceef1e9ebeadfeff0edf3f3eaf0efe4edf9f1eeeff3e7e7e7fafb020303fcf9f5fafd01fe0303fd02fe01f6fef9f4f9f1e9efecf6f8f7fbfef6f2fafbf5f5f5fbfbf401fcfaf7f8f7ff00f801faf805040b0d0b0a00050bf2fbf8fe0303f7fef9dfece0e1fce0d4f4dd0106020308f9f6fef9faf9050a040cfdfafbf4f200fd01fffefff6f6f3eefdfdfffafb00fd000402030bfcf9040700030f070e050107f3f6f906080bfbfa00f8f4f9f3f0f9fdfe02f804f605000c050905fdf0f3fefd0bf8fa00f9f6f401fcfafafcfbf7faf702000005090b0efafe0b01030d001007070a040406090e08fbfbfcfe0605f9fd0be7e8e7fcf9ee05f6f4faf2f2fefffa060a06eaf4f3faf8fdf2efeef7ebe7f7f9f6f8f4f0ecf5ea01020501fe07faeff3fcf000fdfb03f1f5f5fcf8f8f8f7faebe6efeef8faf9f5ef100f0c0d0d07f9fafcf3fef0fd02fcfbfefcfbf2f5fcfcf9f9fbf606030b0f0504fd010105fe0011050d11041403fd050b0704080608b8a3d7cc92a0b18080e2e602edeb01edef07403840544f3d774036d3d4b8febaabddb39fc5d9d3cacac9d69ca212e8caf5dacbaac3b4eee4cfe6dedfe5e7dcc7a7d294a6ce808b99151e3f28001e290235f7ec04e9f401e3dd03e5f5fdfdec030cec18fae4faecd2dbd6c1b6d0e7f1d3e6efd4e5fae2e3f2d9d9dcd9d1e81a1b2409000a1ffd105444394a383d65664c3e0b07190d1b140512fae8fee2e0f3eae2eb09ff00fefeee0a06172c0b292407243f1e28a8bebec4c0d8b1b3b6d1e8e5d8f6d2b6b3c310270d0c17071e2e1b0c031023080f2b0325f8fffff8e2e9fde504a7acb8a3a3b28099a1fad4ebeacddfcdd0aceaddeeeadbc5e6ddd4d7f2edf5d0ebdbcae2a3e3d784cce780adbf2c1b3117240a3c29210d051001f8fc0af801061313111a1f222827faf9fef9fd01020309dfdde4eeeaead8dedcf3000800fafe06f905edfbf1fb00ff0108fefeff0cff0401071204f4f4edfdf2fd0300fb090708150a0d211b12dee8ebecf5e9f1f0f9eff5f2f303f3f7fcfcfcfbf601fd0607060ff2fcf6ff0701050cffe9f5f80302fd0204fe030b05020303080706f6f9fa060e00fc0a01eef4f4fc000005010cf4f4fbeeecede7e5f1f9fafef7fefefd0402f2f1fa0d0d06fbf90ff2efedf7f8f100f7fbf5f702ebe8e7f50003fdfd05faf4fefcfcfed6e3e2f3f1e6fa00fa050f03030301061110fbfff7fe02fd050404faf3f6faf601050404f1f90105fdfdfff906ebe2c8e1f1e0ece9eef8fefff4fefefc0001eaebf9ecf4f7eef2fdeffff4f7fefff7fff6f6fdf40900faff05030aebca3b4cfc1c20dd2119054d3a1a624418edb68806eba404d280082af1263fe9240beafdebf42f0ff82cfcfbcee5e8e4221121f920bacfbfedcca0f6ecb9dbf91c13435a404b4d1914f72c14fa3615d7e0d8cc1114e31c15d2de0509f7f31feff21adde0c5efd8d22b09a9edf0df0703f01d07f8f5f2eb2c15ff361ff700d3c923fcf11beacb1a01f41e04f93b0ff2604c1e7b7f4a706065251f035438114c3d14f1c6ba14e3d63df7fc0f02eb26180d271ffcbdd1b6072833dcecfbeaef011d2710381ffce7e7ea0af6dc14f5cacfe2e7fef204fff8eb0ef2fa3e1418301f11012d1e363a122c51232919eb472dd93318cdbabe9b3701dc301fd7fef4ec37210b3712ff380af87f493b2e34091d0de23f32fd47f7e824fff32c06f3290ddfd9c4a2aee9aaa5b191c5bbb7b1b8b2a8aaa2656a6f6055744b556b80bf80a2e79d8cd288f4c0f1e0afbbc8bab01ad2bbc9b8ccd3a9aad9c8c4c3c6bdabb4b9dedeefd6b3a28b9de45e522f354730342d23f9f7f4f0c5e3d6dedcdbf5dfba98aea6848027202b33f40a130b12e5e1ecdad5bdc1cab7c69ab2acbeacb598a92f4f2b331d1e2816f8406675655b467f532a53483861623f503a1eb9bcb5b9b8aeafb0a0f22df6112ff2320bfd7f334b5c120b392b238a8695808080808080bbacaacecab48080803c5d504a563847471adac9b3c2a4a5b8ba9e02bec9c9afb7b99caa80808d808080808080a3dbec9fd6d1c1b0c3d1bc95e9bfaff7c6b9dcd0e2c4baa4ad9d93989ab19180b08080807e7f707758347e423d2049142808dd2803ceeef00eea05e8f3eedaffe2e4f5d5d3f4d9cc2b1b442f2a1a1114162f002b2b191e18ff11f609df00efe7efe5c1dcf6faf804fe06feee21ec1214eef40aeefd0502fd00f6d3fadfd115f0e912ecf111f7fa26fdfe21f4f121f7fc04f6ea0d03f6f8fce51914210f0c0b0505f412f1fe1de7ec1aeae817f7e726f7df0dfbd40de0ee14f1e915eef61bf2001bed0127fe021dd0f9fddbefeacad5f8e7dc01ddd7f6e5cff70e4bf6041bf505f424fef31af4f02902f84500295310460b0124ea0a14f4ede3e4d9bd21f70c21f7ed23fcf11ffdfa1a01f920fbf61508dc22e8e010fbdc1205021c13f40c06e6e8cacae8e0bde5e4ce222b021d11e51c1ae009f1ff1cf1fc00f1e709d0d9f9c6bfe8beab14f20d0eeffd22fc0909edee07e4e90ff5ec0cf9f112080bfe1108fc10ea16240820291cebb1cbfee2dcefdddcf2edd4fe0fec0e10ffec13faf40bfd1d1a0f04fd020c0d06f810f5e1dce9e9e8cee8f6e7ebebf9f5effbf9f5faf0f7fa000efe0d2618d5dee6e8f3eb0011f7000fef241cfe18140adcc9f4fdddee13f9f7c8dbd8f4e9f1edf3f1e4fcd7021101222909cbd5ccf1eddffbf0ebf7d4def204f4020514172f0c2a2b330b2015f808ed0e1209251d10ac9398d5d6d5f50105e800f40606fd0b2012abc5b0fee9cfe8fbddd6f1e4db04e70e0a07ddd9f4000d01f9101beee9dcfe03f218140ef00add19240527290adff0e2dffde6dcf7d8b3b9a9b7ba99b7bbb697a58cd4e0c2ede7e0f4fde41b1af722230f1210f60b19fffe11f3edfbf30017f6fef703e9e4dc0400e90cfaf6210916fc0535f7ff06e2d5e7f3edea030af1efeb0edef519dcf51df6f3ffd9f0f7f102161c1c392a1345364839242d332f1e27614b31060a070808122314113e5145363e255d3e4de7e309def4fce7defcff080e0e0417160833c1d2bde3eac8d3bfc31d1a2a08181025101ff3f2fb070d26122526adaebac5d4cbdcd4d4c2c0cbe1d6d5d8f2c9c5c5c5b8d3cca4b5b7dacde6021101373a2ce5e9e6f9f8ebfcfdfb1cf72500fb14f10707bacfbbc7d1c8d6e4d1fefad8fe18dd0f24f91113361b08284a303bf30608eb0527e1d9fca79c9fa7bda5bfbbbbd6d0ceeee5e5f6e3d0130817393d394e3f35e9e7f1e3ebe9f0ef02152318f1f204f5f3e8d0d9cbe8e5d5fee5e627283450104f58345cd1d6c5d4d6c7c4d0e3b4bfb6b8dbcecbd0d0ffff0b0f181df1e902efe7eaefe8e4eaefea04160a3b29302a2c0f05fdf9fae50904d506dae2e7dfeae2ced6d8dcfc02ec01f2eedee00df6ec0eeef71406f7e7d1eaeedfefeddbd615000814ff0210f4050f05eb1d0ef00ef9e6fbeffffbf60105f4ea1a27281f1d141a0f020500e70df2f00bf1ef0afbfd0c06f1ff05fb0807f00f01fe0ffdfe281b0a191f0f2923141102ee25f4ccf7e2d0eaf1e3f1e7e8e9e8e1f2fff91a11fb26130526020e31ff2526110cc8d2dbd9f1e2d2c6d1d7f404f4f1e1ebfede2c24392c142e30182327140c220d0e1c1811ffff0407f1f2fff2f0def9f3f4eeefeee0d3f8dbfbf5e5f7e2dad8edd8d5f8f1e7efe9e11b0a021805fa1a0affd1ced3c8bac8bfabb21911061c160f1a110d1f0e051304090502fdf6fc02f8fc00fffdf7e4ece2edeeeae5e5dbf4faeff7fdfcf3fbf1f7f3faeff8eeebede7f2f3f7f0f8f3edeef1f2f3f8f4f5f9eaf2f1edf0f2f3f6f8edf0f300f7f6fcfcf4f7fdf5eeeaf0ebefedeff1f3e2ede7e9f2eee4ece8f1f2e5edf0f1e1efe7eff3f0effaebf3f5ece5efeae7edf5eaeef0f2f6f7f9fbf3f4f2f0efecebe8ebf0e5ebeceff4f1f1fbf9f4f8eff8f7f6f6f9f4f7f9f3eeebebeceeebe8ede5f1f7eff9f9f5f1f4f0e1f0e6eaebf1eaeaf1fbfaf5f9f6f7faf5f4f6fafcf6f6fbf5f7f8f1f7f5f4f8f5eef7f1eff6f2f2f8f4e8efede6e8dce5eae4dae2d8dceaf2e9dde3dedae3fcfbeef2f7f8fbf2f000f5f5f7f6f5fefbf7f0f0e4e5eaede4e7e4fff6f6f8f8f4f8f2f3eef6ecedf9f4eaf8f7ebebecf3ecf7f3ecf4f7faf3f7faf4f5f3faedf0f7f5f5f0eff4f7e2ebecedf1f2f6f6e8f4f3f3f8fdfafcf3eefdf7fbfd02ff00fc00f3f5faf600fbf1faf3eef4f5fffbf5fff4f5f3f0f7f5f4f9f1eff701f8fd0d030003f8f6ece7eefcfaf9f8f2f0eff9fffefbfff9fcfde3ebf4f3fcf1f4f6f2f4eef0faf9f7f8faf7eef1f8f9f6faf9fcf4f6f6ed01f3f3fef7f302f9f907fdfd03fc00030606040104040507f1f7f3f6fcf3f7fbfadfe0dff3f2eeeeefe4fdfaf8fcfb02fffcfcfcfdfdff04fb01fd02f2faf9f2fcf8f4f8f2f8f8f1fffcfafefbf7eff3f8f7f9fbfbfe00eff0f4f1f3eefbf5f6e0e8f0ebede9f1ecee020409040500030303f8fffaff010303ff04f0f2f3f2f2f4f8f7eef1eff8f4f5f4f3f0fbfaf8f500fef802fbf508fbff0cff0305fb02f7f802fff6fcfffcf4110c031910f91b1401f1edecfdf2e9faf7e221140a180c051d22060700ff0dfcfa120e080df1eafffae907f7effbefea05feee0ffcf2001618000d0e05140d06fff007fef60901f3fef5f501f9e81103f31208ff0d03fe12fffdf9f0ea00f9ef0afdf105fdee0e06f6120cf40c12031604f9130b070a08ef1110f9130cf40c13f80b0d001705fefa04090d08070102031513071007f81b15fddaddebf5ecf70dfbeb2111020f1d031f14080b1dff0e16061d1a160c02fe05faff0802fb0d0bfb0c00f40202041915021f120a3112120a0cfc12fffa1b0afc0a04000e0403140af81704020c0f0e181a18f9fde00206f60000f40300fd05f5fa05f9f8fcfb0004fb030bff000d09fafe0af508fcf71408f9100901171403edf6f7e7ebe7dfecd3fc03ecfdfcea0a00e51714141d1d111d08f610fff61afcf105f5dff1dedd10f0e207eeddf5f2f406f8ea04f9f4fef6e40202db120aded6fde2e801ded8dfd9fdf8f50704f11704f2f4f3d708fcdf0b02e4fc09faf1f6f10509f0e813ea0507dffa03dafaf9defaf6d10bfae50302e5f6fbe8eff6e0f104e1040ee00a0cd70621fd0428f90d28f404fae9fcfff2fe02f50507ed0f02ef1002ece8eb09fbed020f160bf7fceb0a03e81305ee070cf3fdeee5fef5f5f7f0eef0f3f6efede6fcf9e00e04ec0fffecfaeef8f3f0e2fdf1e20704ea0afae41301e1f4fce103f8e1fcf7e21618fc191b06171df802e6e301e7d50108de08fee50bfdef0800e30908f3fd0efaf1f7ebf00ae0f412def408e5ff0bf50413ec0312e20016071921175b443cece3e9fef5f70b0004f2f5dfe5f6f1fd00d6010cf51d26070d1d0a2124204f2b2d603f4d161712302128262c35bebfb4ceb3bdcee5e7192021735d54442e5bb1bbd6e1cfd8f8eefce5fbef1812002c231fe3daddf2e2e91a0b06151216201111463429d601e1f5fbf2000a0a0efafb16fcf6313c1dc6bfd3c5c9dcf5f2f2bbe8e0c9e2f7d4eadc022a4d150022324249d8dee1f6dee405fb00c2cecdeed5d4f4e4ddd0cdb7e6e5e1e1f2dffc11e2fe00f7f9f2f824142239201e2b2a40dadfd7ebe3dcf6f20404eef607fde71616fee4d9f606f90a291920fdfd161f24242d2935f7e1e90a170c041314f4f7e204f1eefffbf6ecdffbfff501180f1ff5fff7fdfb191f1631b2ebe8d7f8f6eaf7eac4e9e1e505f90c0307010404f6f808f5ed01f1e8ebf3ebebf9ebeaf9f70bf50306f7fc0909f90214f0fc0af6fdfdf5e8f9fbf0f8fadb0903fdf7f7f20d1cf4fe03081306100700110700f812fae5fde8e806f6f603f1f705f7f606fb010bfc070407080afcec11fdfc1907f7060cfd090c0017040502f9fa06f8fb02fdf806f6ee07ebf301f7ef0bf70110fd0c12080f0706010c0313120618fee4dfeaf6f2e7ecf3f4eaf0fae9ebfae7ea0809110015fb0b150910fa010e030115fdf500f7f908f8f1fffdf3fef1f9f7fdfcf4fff2fef6fdf9fdfff8fe070909ff120b08190003fdf0e903faec01f7ecf0ebe8ecddd9e6e3df05effa08f1f602f6fdf5edf5f8f2e8f307faf4ecf2faf2effcf3efe4e9e9e4e3e9e1e9f00dfdfb0afc0605030207f9fdfcf4fa03fd06f0e9ede6e1d2fdf2dffaf2f302fafafe04f4fee00a17e1e20fd9e507f70b0bf8fdfff2fddef0eef6ebe2fbf6dfdde8fdfbe8ec0400dc07ddef2ae6f21f00f5ebecf7f4eedde5f6e81efdea27f0f021fffa09fde917eee823fcec0af9f4120c0a0904ffe4e5f103e5ed0ef9f111f4ee1df1db1801e5eefbf6f8f8fa01f6f313f0f227f7ec1ef8f311fdf725fa011f05011f1005fe00f912ffebfdecf100f8ef00f5eec8e3ebebf7dd0008dc19fff52704f91501faf5feeef2f6dd02ebe5fef4fdf206e6fce7c71a02fb1b01031b0c0118f6f414f6f80af3f409f5f90f0a001b00fcd6e509f3e8e6f1e1c8f6eff4f6e9e9f9ecebcadbdedeeff7f304e408edf10afae805f9f6dde6f3e9eee3faedc22603e4360df3340ffd10faf021fde717fcf4f9e4e7f8f6ddfbe5e8f2dcdae9e8e2f2e0dde6ece7f0f3f1eff2ebf2eae7f7eeeae4eee4dcd9d5ddd4d8e3e0dee6dad8d4d7d7d2ded2e5f5f2f0f9f9f7fdf7e3ece8e8dfdfe8e5e302f1fe12fdfd0ffe07eef5e9f4f3f9f1f5f8e4e0def2f5e8e7eaea02fdfa09fff7080603f4e9f2eef3faf4f3f2e3e6e8f0f6e8ecebe201f0f304f5fd0bfffb10f4fb09f10316fb032004031b0307180303e5e5ddf0e5e4ece3e30508f4f40af2fa060301f9ee07fafd08f9fcedece6ede9eeebf5e4e8e5e8efe1e9e4e0e103fc0005f8f90bfff6f8edf3faf5fafbf1f3f1e5def4ece2f6e8e0c6c5ccd3d8cdd9dbd4ede9e9f3ede4ebe5e0edecebecedeceedce9f3e9edf7f6edf9ece6e6eae7e1eae2e5e8d602edf406eaf801f700f7e4f0fff0f4fef2f6f2ead9e9f0e1eae3f0daecf8ede3f2e2edf1001b1ef51119021d10f4fee6eaf4ede2e7f9d1e4eadedff5d8e9f6ebdfedeaeddee2ebeefa000cf30711f7fa0cf7e905eadde9ede6f1000215f9ff06fe0d0fed0300f3fffef7f90303f8f103040303ff12ee07f7ec0700ec0a15eefc06f4f806ebf204f5dee3f7ebebf5e5d4fa0b0f07071d0d1218051f2d022637072432eaeef6e3f2fef4f4e3d7dfe2e0d7edd8d5e30e151a18211e253227070e140c1407111522f4e3e7d8e6eceee4e9e1f5e90609e7f3f5e7041a250e101c11101ff6fe09030b13000b08eaf5faf2f0faf6fcf5dbcab9e5dccae5d0bbead9d7e1dbdbe2e2f0f2fa04f60b13f3020400f0dd02e4f6f9edf0e6e5d9e0f2e5e3d4d8f30511fa0218010922f00401fd020cfe090fe9e3f0c7c0cafb010710fe09dad2d1dde2fa40344c021027e9fb1423322d19f6122b1717f8f80dd8c9e3d0d7f20c0afb04fd1cfaf9fa3b331ef2df03dedbf424261ff1ddd0d3cfe603f906d5c3cad3c4d446213113f20713f81e101cfaeceaed00e6f838453af30014e0e80b30101ee3dee7cfd2e1fa00fce5e4d6e8f1f716fe0ed8cdf7ffe70ffce0ffd7da03f6cf11030d11d3d3f0bdd7def9e9f1d8d4c4dabfe33c1721040cf8eee3160cfe03e7e1ff06ebf82a27f9141e18072022392f4d03e1f5051e1c1f1f1ceccef1e7cdfd03fe01160d07130d0ffce6e8edd5d0e4eeee463613191121220712d1dbba908194b1c8cf30211debf6fedddfef2817250af7f30c0e2cfdf7e6ac9cadf2f5e907f215facff2fae607fbe7efdac0e9e9d805040800050c0ffcf2e9e9eceff90602eee8dc0a0e0d15190b05080a12f9021412fd07edef0b08040d0e0709fff806080b0101fdeaecf0f806fd010e11f4f9f71010100a0d0c060900ff04fa03050902f301040afffffe00f7f8f5040807fefafaf8f0e8151d0212120a0a0f06010906f9ff00edf2f8e7f4ee04fd04feebddfb06fcfdfb07f4f5fffc09fbfe0706fe0afc08010a0b0d0afbfbf4e7e6edeee6e6eddbd3191a101c170d0f1c07080e0ef7f205f6f7fbe1f0f0fbfbe20f0af61112231213100709ffff080a191215fd0a0afef1f1fbfafbfdeadffc02060c1006fdf1ebf8fafef102fcdfecf0f3f0e6dedfe1e3e6ec07f40b0803ff100704ebdceef7f004fdd4e1eaf4fee0eff1d5dfe4f40b0501070c03fe02e7f7fff0f801f2f7f40a150e02080f01051403faf5f4f6ecedf4fafce6ea06f0ecfffaf311020e08ff050afe1202ffe402fef10505fb0af2f608fbf90f0b011703081409f013fa010f010b100f1f181d190e0efa02fbf304f7e61311fd15feeb13f8eefaf7f6fef3ff05f9f9f5eee608f9f7fafffb0e14041307e80e02f60bfb03f2f704f7fe09100afd0bfceefbedf3edfefaeff9fde6f3f7f4fb08e5edfaf3fc0afe00f6faf8f1fbfafbeedae101fefe01e9f80d12f70afae406f1eb0102fb0c02001110030f00fc0af2f409fefdfcfd0b01feeff5fbfc1609050bf3fcf9faf906fef3f8f2f2eff1f406ff010201050e080408f4ebfaecf4f6eafc0bfcf00f04f31ef4f71500fd02f8f501f5f803ebeffaecf5fc01fa0d070405f9f5f2f0f01103f808fae8f4eff3fc0f08bea698ed07fadad4e2d8dbe507f1f80ed0d2e7b8aebfda96e7fce6e6dde00803ea49203b262c4c49435502f021fae9161a244c351d3743160f35232d3a2525120d3717497a2009112509fd23fe164b1d393f3a413a373f8080808080808080803b544f372a49322b2c3a1e3f30183d311f46c0b3bcbcb2d7d6d4d106eb05eef900ef0719fff2c1afd5f1c0b8edefd00fedda07ed01f9f1edf0f9def7ff050cbdcfbf9cba9c999fbee2e890d6eeb5d8f6cde1050693f3cbf0dede3a43653b3c465d41485750502a2b43273133bdb6a7adcea8b6be9180808e8080b2de9ac716233723102d2f291edcd9eeced6dad1eeebf5d2fea69ef0dda0bcb2b4ca9eb9a6c9d7e10cfe22220e13241f2006fadbf1e210c9d006f1d8f9f4f5f3e5e302dae4feadd1cb9592a8afdcd0b9d4f3bdcec33a3cdd49472f5a4e31b99195baa5adeab9a0faf426cede1dd8d1e8f2f005da06ced8f7e0100d29faf24bf4f313ff1a37265002ffcdd87f7f7f7f7f7f7f7f7f617f7f4b777f653f6594c6d691d1cf8ac5a334293df33976db0b225c777f316a77153038b0bba9a8bab980a3a13b6b7f46417f2f5841767f7d7f706d7e685b4f5e697f6d4f7f7f6ebde7e5c3e9f0a7d9c404edf236eff91c2bfe40602c36344b16293980878080ce8099bca8e6ed03d1f2edebecfd7f6b767f7c7f7f5a76f300e2f7ecd5d6f9c8abd3ca91c3d880b0c1dc0507d8f4f0aab4b3dfd4ddecbbcda68084c5d9cabdabbfa9a5c7a0ccc3b6e9c38dabbafdec04e0bdeb8d82a27e7f7f7f797f7f7f7543493120262a2e1f1902fb0cfd0415120c03fdfefdfbf9ff00fbf2f4ecf6f7ed12fbff080d040d0cfa0a14f9f9eef7f1ecf4f5f6f7eefff50307f5eb0904f9e8fcf7fbe6edfff4eefa00f8fcfcf8fa0dfcf2eaf4fcf3f8f9f3f6f5f6e402ebeefef7ef0bfef9060108060800fafefb00eef401fdfcf0ecf4fdefeef7f5ef0600fe05fd02fffcf80afbf206f9f2fefffd07f9f509faf703ff01ebeffafcf5fbfcf4f202f50002f900fff2f9e8efdcf1f2e40611fdfef8f703f7fcff04fdfef8f9f4eef4f6edeaf3f7eef8ebf0fce8e4f3f4eef4f701f5fbf806fb0709fd0401030503fefcfaf900fbfef608fe0207fdf70cf8f4f6e6f0e9e0e6e2e2dde1ece0efeee7eaf4e51303070b03080d0401f7f5e1fef3ec02f3eefbfbf102fdf800f90005f8ff0700fafd00fce21f19fe152d030d10141c0817141d1c0dfcf1fcd313f9ef08eedd231e23242223321b20ccd5dbf8e1dfdcc5aeb5dae7b3e3ccbce6bef506ff0d040d0501fdbd99ead1aec1c2dba6091c0b1d020d0c07ffebe7e600f5f7fdfce72102ff17031f1b051cb3a5c1c7bbb5bdaa95f1f10b1607fff9fcf01afc1006042422faf80b070732150c300c020205f7161ffe17050de9e000e7d2ddc2b8cb102419161210110f02ebf0db0d37093311f64618074e23033e2d02c5d4c9d5dccedaf9bcb8c9b1a8ba9eb1d38efff3be28e3caf6d3c7623e3069252067402c2d20271e101e231208dae51fbbcff8acd6e3291f180e0c23130c15b48880b2aa8cb29f9916040e1b00151bfdfac2c4f6b3e0e691aeda2119281e170329120739262a4b2f0e2f170106eefefe0b15061c2dcaef0bd4f503c7f60ff11d08ff19270c1c22002418162afb0c3001dcec18deee16cdfa24fe1821de0f1ee928110e16361b1c370e1d35ddd4d9cbe6f2ceece6fc1212010e26020b2ef00736fd044104104bafdef7d2d40cc4e401dc1426e30e3b1a0d3af80724ef0227f70020ecdb1bebd61cf40500f2091ff914310c121615fd36151b39181433c5d3efd8db14f5e7fac5f00addfb03d0edffcffb17ecf92f08012fe6f928df0a07f6fe0af4eef7f20207dcc0d4f1fb1de6eeffe5f4130014310119301a231fe10133f90522fa0e24c8eeffd6fc17c0e5fcf70609040c0def1330f0f9e2f900e7f2f7ecd8e2f4d2ee0be1f0f9dcf71edff81eebfa0eec02f7e2ececea0ff6fe0d16ed0d19041b25eafd1aed061ee9fd18ec0aff01e8fc160d07ccdde8d3d7dcbccce2437979175a700d565f24f310e2d6f6eee6edf8e4d1e0dff1cdddf21901f709e6ffeef40923183307ff1cf90307fefa10b3dbf2dbd8dcfc010cf0f3f6eaebfb212825f50614eb02fc8897c0a3a8c3a6a5d83740410f2c2e072d2804ff17efe702f1f0fadcd7e3a2d3b2c4e3be0c0612e70813f0fbf7f5110ad8f117d5e4ff91acb78280988da4c6d7d4eabfb3dbbbcee23b4c4a0b1f1ffa0f301d0de503f2d9eae1e3402a31a1d4cb102cf4f203ede7efdaf1fbd7031a10f2fb11e8fe0d2b07161d070c09220bd4d602b8c1e6c1b4d7b6c8d0b0c3d6cfc3f0b5cbe6b4c4f39fdaf0eb1118d301eabbeee9e3e5f1e6d9fbcedef0f0f9f6c5eecdebf9dbf0000cd1ed11dae8ffd9e4f8d5dee8d8e0f4e9cee2f2fafcf704ec1c0a010706fefeeff0303e313d54424d5e2afd0a0805fb16f0f6e3bbd1bbb7dcd0b8ddcdf4edfde7fbebe4f5ef11f3162df4191f1304e2dcc0d5caceb3a6cf23fe082e18e8400e010cfaf3090dfb1c11f81606fd06000ceaedfdeed0f9fac5eefac6e70eed0712fcfb1cf8e915fd012006030aedeb2404df2110f213fbfc1e222c21200a1d0c01cecccce5e0e3d5d5e50904f408fdecebeaeeffdbe90c06e220e5db300dee23fdf21b07ed1b01fd230c13fd10e1f409dbe3d3c6eed7c4ec0701e9fce00c06ef2e191c2819202717112b0d042402fa06f6fae8f1dcf0e5e8cdc0bac2abc1b7b1c2c5c9d700f8d2071ad6f502e133f9ff2dfdf011fb08e2d5e0e7c2fbd2d0d82a0ee32422f72c04f81e02e11a00e80f02e7f6f9fbfdfcfb00fff5eff1edecebefeae3e6fbfbfc0407f80203fefcf500faf8fff2f2f1eff5edfcf3edf3f0f6f3f0f1f1f2eff3eceef3fcfdf9f9f5fafe00fcfbfefcff0203fd00f0f3f7f8f7fbfafff9f3f2f1f5f9f0fafcf2eff6e9f8ecf1f2f0e3f0faedf1f3f2eef4eef8fafdf6f8fcfffdf8eff7f5f0f2f6edf1e8ebf3edf5f5f2f9fffbfcfafb0001fafdfafbf9f3f2faf5f3f9fdfdf4f3eff8f9f9eee8ecfcfff8fe00ff050409eef4f0f5f6f9f7fe02f7fdeffcfcf9f7f9f2f6fef8f9f9fbf5f9f405fefc03020002fdfff0f1eef6f6f2eef4f6f5f5eff8edefecece7e0edebe0e1e5e0e9e8f5fefdfdfffaf9fff7fffffefd00fd030202f1eef2eef0f4f1e8edfdfdf7fcfcfbfcf6fafff9fb03fdfa000307fbf6f3f6f8f9fbf9fdb7ebf7d1e805f005de03f5f4f8f00000f3e90d05250e283f0c3620e0c5d2daf8d2c8e1d1f70bf5f61cfcd909ea111308170217dde7e71e0b171c0c43100a24e7e902e6dbf498a182eaf9fbf2e807e3c5d3e4c6d0e0bdc5d8a5b20df7fc14fced0ef5e4cfd50ddbd704d7ded607031813fc1d06e10f02fbf3ebe7f6ecdad5f4e4f2fcd5fbf2b7dbf4f1f7eeff05e2fd082d23d21534450ffe090004f904fdf7fee9e0c7e0efd902decaccc611f60c1b000b0bf2f806f207fe04f62f1a1febecf606070aeb010fbbdb0bf0d3e8cfe7ce0203ef09fcf408f6d208fdf404fdeb03e0e4c9ddf7fee9eff7e8ed353b2c45422955553671516f504d684a7d7600e8e107e3d805e8cb0604eef030f4081601dbe5c6ddc6c9dad6c9f9fcecf2ec14ecd1d500eeed2a160f404734e5dfd1fdf3ea17fb0cfc05f80e030b15fff716081f24fe133a2632cbe2da0ffd0c1f150efdf116181c263a163007ebe20cfdeb0e11ff02e7e9220f07212611ebd0aef0d8b6f1f9eff8e9d301e9e60ffff402f8de2b0cf8071d12dfcdd0ffe3d9f9fe03ebd7c003ded213ebec00f4f1120a0d201624fdf4d90b01fb0f0dfbfef3d0f8eaf70404f0f6eeea180b09201026dbe4c9fff7e80b0208feebe21dffdb17f1ee0cfbd41c02e91b16fdf2e7f7f5f805ede7edeef0040e182a38394109decaf6e3d1f2f3e50a07e6130ffd1b0efee0ddd106fcf7050707fbfb0615101c433730cac5b5e8ddd80cf101ede0cc09e2ddfcdbd503ef031412101d1528e5e4dd060000241f0812e6d310f1e714f3e1f9dfd907e1f611010efefaf6f8fcf9f8f9feefefebedededeaf0f4f2f8f5fdf9fafef8faf5f0eef8f6fbf9f0f6ebecf0efebeeeff0f0f0eaf4f0eaf5ede8ebecf2ebfbf1f3f2f2effbfafffbf4f4f5f7f9eeeef8f6f7f9f2ebefe2e5dfece9edebe9ebecedecf7f4faf1edf9ebf4f2f1f2f0f4edf2efe3eceff0f1eceef6f4edf0f9f4f8f4edfeebf2e9f7ebf2f4f5eef0f5f4f9f5f9f9f8f7fdf8fcfcfcf9f7fbfbf4ede9f8eeeeefecf7f4ece1fafcf0f7f9f7e5efe7f4edf6f1eff2f7f5f3f700f5f4f6fdf8f4eff7f9f4f0f4edf2f8f3fff9f7fcfbf9ebeaeaf2ecf3f4f1f7eff1f2ecebf3e9e7f6dce0e9e0e5ede5e2eafbfaf1fdf3f2fcf4fbf5f3f2f9fffbfcf9fcecf0f2ebf4f1eceafff8f2f2f1f4f9f1f1f1f2ede8f9f2eef7f6f4f2f0ebf0f7eff1f6f4fdf801f5f9f9f8f6f5f2dde9efe0e5dbd5d8f4f7e9fbf0f2faf505ecf3eeeef4f0e8dee0e3ddd9e5e8dde7dbd9f0eae5e5e8dee2dde3f3f7e9f1ebeae6eaef02fefbfcf5f0f6f8f5e8eae1ecede9e5eef0e7e7dbe5dfd8e0e3e3fafaf7f1e2f1dddcd9f8fcf2f7edf4f8efefede6efebe9e1e6e9e5efebe9eceeede5e7dfeff1f8f1e7e8efe4e8fdf0f9f0f2f2f4efedf7f9ee01f3f2faf4eef3e4e3efeaeae4e0ddf3f1edf2f3ecfef4f9e6ececede1e9edece90100fcfdfd01efeef2f0f8ecf5f6eeeceae9f0f1eaf3f2f2f8ebf9dde2d0eae2e4dae2def9e1ebf0e6ecdad5daded5dfe2d9d8d3c9dcf9f0fcf3f3f3f3ecefeffbf2fdf2f9fcf4f4faefe6f0e6ece3dad8edefeeeeedecf1e9eff2e2ecf2eeedf2f4f7ede3e6f0e6ebf2ecf5ff0602070508100610f1f4f9f0f3effdff0007060cf70301f4fffbfaf70503ff06040904fefcf2fd07f6000902fdf203fe0a01000507fd0608f303f7080e0af9ff02000605030d00f5fffdf2faf5fafcf7e9f4eee4f9f00005fbf5f9f5e3f1f30401f9fdfffffc0107030603f1fafbe4f2f2fdf704ecf9fbecf7f1020808eefdf8f2faf3f4f6f9f9fdfcf7f5f1f7f9fa00fdfff8faf7f9f4f4f4f5f5f2edf5f9f9ff0604fe0b0ff90b0006f6f5f3eafdfaf601f404f80802f6fffc080ef4f9f9fe0501020705f9ff00fbff0004fd09f8fbf1edfaf8010703eeeef6e5edeafafafff7f6faf6fff9030c02070b08020802030c0ffbfbf8fcf8fc0303f7f3f8faf1f2f1faf70103fc0501ff020b1109f8fbf1fdfaecfbf3edf7fbf7f6fbeef6fbfb8080808080a2a580c601f8f806000ff0f7ee808080808080ba8080858e8094a09580898011f91f1f10001823f9cbbdc99ec8b880d1f780a0b3a3b0cbb7b7982ce7041a0af4e70dce446a37645d2e5c5142ed07e9e704fcfff5f0313d474e29523e313f988998e29bbfe3c1aefef408f6e7e4f3dad3ddbdd3dbdbeaecd7d5e301f801faff2b1c15111f2e5c222c7466457f547c7f7f7f7f6c5cece8fff6f6e6f6e1ee02f4c52c21e5331c0a47465349473c6b5d3cc1eac6c9e7e7cfb3e8e7fceb031bffecc5ddef0d1a0a04fe081e0615071027111c1b1004e2db16ea022403faf9e3e4deed09f5b3f0e5080cf31d1d0bfe171cc6afaed4f7d4f8f3ffcdc5fed1e8f6ddf2ec808080808080808080283719474637765b3e404b2c604c4b68663823150325040bfd130819110b2e1c12251d19d1e8e8f406dee10bde290b13322f24303a20f9e9f005fbfb130e0716f3df1cfaf62c12fde5eef4fcfffb121e05ffff07292011363f1bd3dce402fd060c110d00faf91d0d011d1e06efe4e3fff7e803eff1fbf0e32509023719120711fb22210c272f171404fe1f1d16202827fde9da120cf51f2709dfefe0f807fa181204ece8cc0008eb1619111e1c1824291b252722f6e7c42af6e31301f1f3ecedfc07f60f140625f5ee1103ef14210d06f5fcfbfc0817f709f6f4e3f6f7fe171d01f900f7100cf81d12000e0afa22190b110a11181308203338413146080afc00f5f100050f02fefe1204e91107f10e05fc0506090f1f1221fc041a170b2c301fe5f5e1f7fcf70c03fcf206f91616081e1c24e7e6cce7e8d7f7e7dcff08f50304fbfefbece4e5cdeddac7ede2c6fbf5f6f4f1faf4e5eaecf2f0f202f5edf0f1cdd9ded8ede8bed9d9fbfdeef1f2dbf0dde2e6e4f8e308fdebdff0110f010d1003090afdf2ece0fcfcecf6e4e21c1f1b2211020a06f9e4f9ddeceee8e2e7e0f8fcf00304f8fafef408170a03110af309f20c05f20706f203ffef21190a0b15fc0709fc0603f30efddefa0bfc0e05fb060a0001fdf60801dc090005f6f3ff090c031818100f0bfefb0d0d110201f2f7faf3f3e4f300f7dde7df1300eb0604f806fefd1113120d0b0601fbfd00fef01101f900f5eddcded7d8d8e8c4cecd090af80e05f607f9ed0802080706161208180e18041b15f90600f9ece8e5dde7dae1dcd60d11ff0b15fc0411f1160a01170c021008fb0506010503050b0806fafffafbfcfdfcf9fcfe02f90000fffffbfaf600fbf6fef8f3fefffafdfffd0102ff02050101050402040606030000fbff00feff02f804ff0404070306050706fefc0700ff0800fb0000f802fff90000f5f0fbf6f401fff0fefd0400fa0604020901fefefefc00030102fffafdfdfffc0003feff000001fa0003fd0103fa0105fe020100020000f8f202fef8fffbf8fdf9fcf9fafdfcf8fbfef4f4f8f6fcfcf9f9000101fe02fefc00fbf9fdfefc0200fcfb0304faf9fef900fffc030203030502020702040005fc0001fe050500fd0300f802fefe02fefdf9fafdf9f8f7f7f5fafffefe0001fd03ff0201fff902fefefe0102fef9f9fffcfdfbfafd03060106020207ff030405060000040000fe0100fd0200ff03fff8),
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
    .actor_error_o(error_actor_down2_standard)
  );
  logic error_actor_enc2_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(4608'hd52fe203011318202572317f4e394d5a0c5617f3fefb0713170c0d4a3c6821e35a2e44132bf52c26044228fb27fed8fee9e512370b4107f8eff0eccf1406d64012121f1e26f80c001ffbf618fc15fbec07dfeee720051d0e3d082436ef0505dd460a180a1ff0f9170ef920200efc1309ffefe7eff327061617dafc16f51103130a04fcf002f5eaf2e5fd0417003d15340bd9e501e0ee02fdc43a000906ecf40cf9fb320d190dde09f11a1229311a4204fe6246fdf01f0e20ff0bf5dce5421f32512df4541aff2b0d1501e91215e10e270815faf40f01070d613f39ecd91eb5d71504100ef315f0f9fcf7161cf6000c002526fd37041d19ec133323344009390df91016ff3b1c1c184626e63c180c1ef60808d6102c2c2a204665df2c454c3d561c2f1802fa03ead7ed5c222855dc2d56245fdee4f2fa1aeffbf7e814060eedf1140ef3e816f1fd05f80bfd0e0ffc2d2c06363df14b4b173831c9ff0fdffe181afc4823f55e50421ef2f90ff50a141604143b3b51f6453afd082c2e3c164420fa123028e7f2e109e90c0a0f2612d30f19ed045161543710102c2c323a23414d02133119023204e24a1f2d0cc53d541060342a2b0bea0512f31315f7d6f2fbed0d33180f0125eddb1718010842184b33ef03511f436b28583ef00c4a736cf90e250dfd0b34f1001413eef40cfb16f411391e200be40f2c1d10121f620bfa52cf0a30e8010aebf016f102ec091afc11030bfaf8005a572934f9eb0e213d2604030fedec160e004c23604705467a4c573316fe31f50427200d1611ea1ff5f1032725),
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
    .actor_error_o(error_actor_enc2_depthwise)
  );
  logic error_actor_enc2_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(32768'h00ec03e1e3df15fbfbe61f200c030beff61de10b1ae708f2e9f4fd05080f0f0405f1edf9f9edf6f6e4f4fe0e07ffe1fb03f9f0d206f9f8dc050607f704e812fe2502f9e4d3f919e725ca27e5f2d9b8e721c1f208def280ee10faedbc29f4d517353501eded04f22a1e0f120043d5ab17e351ecdef9d608b754fbf6558319e507e6f204e2f2ea09c002f0fff5fde6eff1fcf1f8fafddbd9080801f7fe06dae1f00acff10ae8dcf001eff7070802f4ecf2d9f5e8fcd8fb07f6eef8fee0eec1d80b0dfffa4605fc26e401050e12fb1105d61efdf81c0f3f02f206f80a01e5e40133f9f229fffaf2f3f820113126221f3e0af400f2393a00fe15090303f020f406feeef0fff306def503f8f309f4fc01f1db0008faf9ffe6ff10f4faf7fee0e5fed4e6e30302f9faf1dff9e7f103cde9efe0e2fff300f9f20415cdf9090209de0606f7e8fc01f028f2ef0603e517f502fef916f002fce311f10b0b0111f904f7f2f5fbc5ebf6fbf6ef000de7fe20ee01fae1f9190c19ff00fa05db05fcf5fee9f4feebfcf9eee416c4e5f80701e5ebea0bcafb02edfc04fbeb110c02f1f9ecd1d8ffeaf0e20afbe209e207f30d0fd21a00fbe9e71c10f30107e615020bdfd4ccee1debd506c0e8e5f2d4f4dff9ed06e1edd303fce2de09d3e210d40400d4e0cce0eae4dff2f705d5f8e312fb0e03d2e2ddbbdbd9e9c0aee10bf1ddf907e81ec7060ff5ebff09eeeef3060204faf70c0502d4fb08f9ecf9040904ecfceaece404e5dee7e4fa08fffeffd3fcf1f0f6d801edf4f6f5f2e3e7fffff5cd02fff80bda0e0a0f1e060a250511ecfcf13107010109d20b0eee16f406ec061a0405fa03ebfc2a19e5f6fef5ec13d10eff1ffefe0a04f0fe09f320100c021a14fd091006d525fa040d00e9e8f307f0fff0f2110f04fdf10401e4fdee0203e9e0f5f604f4fff90702e6f80502fdfbfa07041c0400fcf8f402ec03faee05fbed1502ff07fdecf90bf7fa06d6e4f3d4fc02f5020bf208fced0212fbd4f8010be5e50400f8e8f4fb15e6d8f4f4f8f8fce41f1821fcf4dbf7d4eef2e3fdec0904e31b02ffea14dcef0fe8fcfaed19e8f0030904f3030509f505f2f613f1f702fd18e8faffe9eb01fceee5fefe020003fae3f8eb0007eaefddd8eddf35e4d7ebf62ae5fffbfcf2cf0909ecf8fe08e61af20f00181af5051cf6c3f9eef8dafdf90102ea09f8e7fefdf1efe3c80802020ae3d0f0e41bebcfeb04eaf9e3210bf1fb040ee7fe03d80bfa15ed0205fbc5e6e1f8c307e1f1f10fe4eae3f4f3e9fff5c9e0e9f0f3e7ecf5cfe5feffe9ec01fcbedadeefee08fdfae9fff1cc20daedf3f7f2d905f6f9f1eeced211f2ec05e2e2f2f9f604e9f71afeed08e7fe00f4dcf9eef110daf9f5ffddf300e3fbd2f504fcf8e4e9ff080008cfeef1dae8e103e2bfe9080fddfafdfd20d51709f7d907bcbfcffaa707c5efd7f8d4ded906f3e8e104cdc7f1fd04f1cde5aae6ceecbc0af9eac3f2d7efdbf90deedbd4d3a0f7d8c4b9ec0af9e2f0fdeddf9de314ece200c3f3dff395fbe200e709cde2e1fdeee0f80ad8d5e7e301e5e7f8b1c5f9f7a8050c03bde0e8f7ec0dece7f104dab8f8dfd2d7f7f8ddf20202eeeab5d70af2e7f4c0e5f0e5f205cdeafef1f9f2e3f8fa03ddfadbe918e301f9e9efd7e6fdf1c7f50dfbd3fce2f5f4f108e6e9f5d1c4dee2cccefc01e1defa06e8f4c2f807f10503f2e7ee09e1fcf7f6e0eee6f2f8fb05f601f1f8e9f415fcf50224f3f50b1ffcee04f6f51c130711fd0c0f16fd0ee91efcf7eb040ae01ef1fc13e4ebd50e05f40cd2e5ddfed1f8d0e4f0ffe0e9df0204eff8e6dcd0f8e602f8ddf9cce7f509bf000ae8d1f6f40af50cf00201f1ddd6dfefdfd1fd0df609f2f6e4ecc9ee1411eefcc8dde605d312e5fa0b05ecdfdef3f0a7190208b7f2201203eef8cbe40101da1b02f7d2ff0505e524e6e0e4f403c721c4f1d80aecdbf312fc04e9d0efe4bf1108dbe9d6dbeb02e419e3e9e714b41b0ce2d5fdea06f2defd0b04eef80814edc0dcf901cbd6f412122ef1f2d30ed2f9f4f0e0b6f9f21bd5fefbe302c20b05f1d502dee6ebe2fcf613fb0a01fff5c0fe03eeeffbd90604d801f4d8cef0eddbf7d1faf911f3fbc6fec90111c8e6dbd1e8e4f8dfbbecfdefb7f6f6e922baed0becfe03d3f019ee29f902f107081303fd070e00da120831f2cdf510101214ffed05c704fff5051802fdf218fdc2f506e30ee8fcd5c5d40012cc02020e03fa1fe0fddcfcf1e5d0fcf803f0f30103f5ffb306f7dfea1bec00efc7f6f6f4cbf8fce604e1f4ff0df2f6dff3dff112d7f9e7f2f0e7ecd8d4f5fefccb03fdeafdd6f0ffbdebf8ffe5ebe308fe0d191f0d1bf7faedfe1edd07fd0bfbbb02f214d80b0ff6e8d2fcfe000afebb010213fbd1bf04baeeee2dedd61ef930b5ffff081cde2ddff7fc02e6e5e7f9dd06ff12f6f604f6c7fd08e7f4fbeb0ff706f4f6faf0fbfbe0f9d704fd020005edfbeb0904e8faf0dbf2e801f1f3fef81bfc05faf20fe3f5f2f4affa1b51f9091bfe09e83906deea1404f8fdffdde6ccf3bf01161917141df80007f0f4fa42e8f8041bca0846d2bedff2120feffe12fa11e8fdf31ca312010c02b6feabede9eed2f8c1f2f508d7fae1fbfae6dbead9c00acfebdbdbe2cee3e7ffe5d901fcc9dad5fa07fc08ddd7dfeccad4e3c4a9f71201ddf409ca08ca010be0020baad1cff1f70cce1ef5f5f60ddc0e09e5e6d2de0dc0eef9f20ae2fb0510d6d5e4fbfdedd3e8000c35f6ffd702e3fed0f3d8d3fa0eeaf5faf2f437dd1614f2090b16f90b34d6fe112409080403d2fb09073a0809e7f0eff7f6ff1fe50b083707fef8fae718f7f501df172f17f122eff3030d1f14f8e31ef6fc0becd90001ffe3fad6ebfbfae3faeff8f7fbf7fae4fdf007d6ffebf205cef7f3f4efeaf105ffe2f3f90eedfbe80ef90ef9f7dde6f0e4eae3dccf190003f5fc06eff7e107f602f903f803c907ec05f50bf6f4f900faf4fde7f911f81a091ef4f307e403e113f41a15fc02f915e8dd09070cf0f7f8f9ff02b600f51df832fef8070fe128100c000701d8e9e2fcf3fce51d0907ff06ec0e0cefdbf8fafdf2fffbf2fbfdfbfa0804dff9fff7efe1dc140e1f0010daf0fbfd03f6f0dcf301e9fdf904f201e5e91ffae9efbfdaeff0e3f00cf1f402d3e8d4ede0f4ea00dcdf0af708fcc7eadaecf7f5d70000fcb2d0e7f0df13fadbf8d9ecefb5c8c8e2ed0cced70c06e6f998e4ffa2c800da0c15cf10e7d0cbcee7ecf3390cd02ccffdae4c27e2f11703dd231cbff5161b030e1516e7e4ced50082baec82fc9ff880d40f03658d06f0e11de23510091604e7e70bdcf60a39e6ff10db170edaf5edeaf606e2d2e90d05dd0ad7d7fbfced10f60014dbdf29c427fefcd4c3e2cf54fb020eecfaaf0cf40512e9f806d9f1eef5c5e7d1dfbf09e5f8dbf7dde2ca02e7eaf602cce3eef80bf9dad8c2daedefc4f5fdf5caf0e4e7e910fde0ede0c0d3e0e4cde901ffefedfbf2e101c3e300fd0104f2d7f10df7fbdfe1f2eee7ea03fad702080409cbd7fe05f3d811fde9191ef9eafafc021510f5fdf60a1008f038df111800e9e800ec3808fc0aea07e2061a0903f70cfa01f9fc0b010f0008fde7ff07ff000bfdf6fdfefa02f4fee00e240cf803f907fffde80f02050b23f9fffa07f907280f18feeff4fe02ffff03040bddde01bfe5ddebe1f0bbf90706dcfedf02e8fccfe5d6e501bef9fef5f0c7edeeffc70cfef0c40bfdf4fbfcf8efd5eebdd3ddd1b2df01f8ef0cfdeee5fdc80cfde5ebf6e3f4f609b808d7f7ef0ecae7ce03f2db09e9d1cb090008e8ecf6c0cff3ffc7f1fcd7bce8ea02ed1901e8ece6d7ca0ec2ced5e601ece505fce5e7abfd12fdf2ffd5fbf7f6cd091311f00ac4e1ebf609db05e1efb5effffbe4e9e8c0e3f812d6eafefeb80dd7d7f9150cf2f4f3d5dddce9dc24f9f5efeaf3ffebf0d5d5fd3f2d03f0edff10d6111424f80efdfeff0bf7e7161532d3f1410a05050bd6ed041af80f04f5ec16f31b0efc07f2d2f7eafb04fd1101070b02fa0305fefbe41b13f609f2db06f5f5dd02f6edfafacaedc4eaddd40bf5eff5f20001f6dfdbe9f5f901c8e8f513cd01eafee904dbdefbd6ccda07fa031111fbf9dd0a03e5f3d1d4ff4ffd020cf72c08fb0537c919fa02f4dbd0de04f8f02e80e9fafd0906ee03e9502100faf1f90ae3041847f32052efcae4db23ef3f2d1eeba72cf9fa07fe0c06ee12180409dcf10cdd0b0d0d10fdfe03eb01fae704f5fadaf3f0f4f7fa14d8dd2108ecfc07f8e908f427f10a0eecddefe9dfffc917e6e706dc09f5fd0503e7ea0dedf901adefe708bdf3c710e4facefbb013eededae8c8d7fcb5f6f0c6e4b5d5f8ead8f9f7e9b6ebdb0e001706e7ecf1d7c7d7d9bfe3fd05d5f0f00de1ec98eaff03fff4de00170df0fe27080307f4e3f5f4fbeffef5efe2f71a07ff02f8e0ed0e01f2fb0cfce811e6f8f307f601e503f5f10205d016f900ea1b0401fdebe5f8f9eef609e1d704fa0203f103f7ea04f8fbfe02f2e8f001fee0dffffafafef9f4f5f0f1fc01fffeeb00fcf412fe02edefebfdf807e3df0a01def108fffa19e008030404090ef6f504e407f90a1c04f908ef0007fa15fffbf9f41203040f04e6050207d9f9ff02f2fa04010e081009030b14faf5e509f411fce90501060100f2ee0b22400116e3f40feb1acefb13110622e7371dc90d07ffe7ef3cff08fef8d3ff3440091efee4f025fffc0f07f421d8372decfde9122d28fde524ff000005e3f7f010d8f6d103e2f0e406ff0afc09ebed20fa08eee4f4e3f8defdf7f004f6effdf4fc00e603f3e803e8e9f9f106fbdffbdef3f7fed6f600f7ed06f9f2f1f4e206f9f8e50fef03ed03df08ddfc0006eaf6de05fff00004e2d9ebf6f3f1f7e0dff7e406d202fef7e0ebe0eae6f70be0fa02e0cec3f7f9f0fbfa01eef0f5e9f3c7ebffe9fc05e1e914e80cfd00fb07f00d02e6f2090802fd080f1ae2fcf1fde2fffbe307ee0802f90601e60ff30bfcb4efefbbddf2ff0bfafcf736cdfb0108f4f517f0f8f700f9e9fb09fa01fefa14fbfaf2f702edf900ff03f3edfcfef90427f20ffb1be10900f4fc180c05faf9fe0aebfa15ef03fdebf30efdea1a01fe08fbf5fb09f7ebffb9f8f1ede302f706f2f5e1fdb30205f8e7fadfed05e4f20addedcee8e300e6fe050bd2f1f0fcefee00d9ecf5d4e7c7d1ebc2f6fcd9e5fc0de3f4e2d7050c15f8f4f120e3e2000f1af805041304f5fff92d03fcdc031e00fc0dfad1f31511e7e4fef7e40ae832041f212805fcf1ef1fed2c1a1f012f1afafddd0ad8011a140102fcf41e100105ed0cfd01f3fef802f9fb15f200eef617fdfe01edf6ecfc05ff06fd00f8fafff6fb0efcfc09fffeedfffa0a02fd050cef00ff13f6020305fbf7f8b6d8efe0dbffff07edfce3fbc018f1ece5ffd7e7edc8f1ffe7d9e7d9f1f6affcf808c5f7eb07f111fbd4e5eed4e0d5e1c1b6fcf3e1e600fad41ba8f1fb0d35fb1205e0f411093cfe07fefe2dee0ae9d5c30d29d5f9fbf1f1b30808bc1aee2806f5fe0b0c2957114edbfdeef920cf24b9fcef0b0ce4eb010529f8140008edd801e1ff17eb07f70cee2afc27081cea092ce4e8121b28c8f6f819d51210fdf4d1def9fa13d4edfeebeb06bbd4e0cde9f205f0c80ef407bafef80e21e31bc9f9c7fed014eff506fcf61ceaf7edf81403f60ffbeffece15e0f8fde7e01205f8f8b0fe02f709d7e4faf5e9fff9fadfdfffe733c0db09f7d8effcf009e6ddf0f3),
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
    .actor_error_o(error_actor_enc2_pointwise)
  );
  logic error_actor_enc2_extra_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(4608'h271b1bfbdcecc8d5eb15f6031ce5e83df636fe0f19fc2101f402f6190a07e6cbef1efe101e113d0c262718eff4cb0604c5deec130c101c1c3c21e61716ff24f1f3e7e8f8f3d4d8d1ff020616f517f4161b20ff2afdb60d290b294b3244f0161329330a000b10f8effff2f9fb452923383c0c1f483f24e40f00d3f31efa120b050decd6f119120f2dfe2f03a90928112fff404e2c25330f422202de22eadef631012f1b02270ef31bdceffa271d250ff81ae70302250a2cf6c3fd3d082e06f80df603f8111b1910fc180ed71420211e290f3204bb0823081c1a0de80dda001f0a231109ea02f0ee060d052a2d1e19e80134100efbfbf4ede5e9fcf1fdf4e5dd250cfe212e15080023ff0bf9ff1ffcdfd2eefae5ea1b102367697f1af2474328501e061504f6014d203d0efd1bfac6fc23082501ff031717eafbebe0ecff0cf00101ffea0826df3105a10622d8163142372c1f21110d0521ece819ffd718fed2f7fe13f100fd1ffd15fae502dfec05f221fb13f20e06ebff2a040b372e09100e0b15041d3222ff160efb4132057d4e6a1d08307f577f0a3f4207f1541c3b38321437fee604100a072ff41ff19dea3c0d49161cef1428ef0afedc2003171503fdf9f6f41cfaff0ae3ff1d0b2066492445fd2652284045013a0dacc832f61a3b0f2df9f401e7dc21fe09010fed010c03eb452a5119c81c2e103461536939fd4616fc1e10f0e0020b06240e2639153e340a073c1932051221200535322c191e0c0f1ff529051900532e2654145d532c4c091d0a06fa100f060c39092404dafa0d0e19),
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
    .actor_error_o(error_actor_enc2_extra_depthwise)
  );
  logic error_actor_enc2_extra_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(32768'he2efff08f406f107fff10ff6fcff0800f00cd9f703f40afcf504ff03eafdf2fe020afe0122ff0afcfaebff04fef5e10b09ffd8f1ea0a01ea0afdfff102e500f2dd57f5e9d1c4b529058d06df10aefbc603c51dfbc40990c6e0f3e10fc9f601c03713e9fccd09ed2a2210f5152ffb1c44002bd9c3eeea03eb28138002bc0c1837eef6f9e7d1eeee0507e3f1fce7e102f1e405ecf4edece0e5f9f8e5000501f0e4fbdfe407cdd7f6f3ee01fc0bf8e4e5efe0f7e7fff7fef4d4fdf8f1cce8ddfce113e6fd2101101c010526070806181df5f00a1bef0b081d1205fafa04070e1911fd0c19ffe8d215fb001d16181032f4fbe809ee231c05001306001d0c09e10eee16d5f3fb1514040c02f3eeee1104f71ee8e71a01eaebfa2622f91501f1ee0bdfee0616022cf9fbf7fbfd0606b6f0ed911ffbfef8df05033ff5f51009fcf0060911ff0405ef00fef4fd0e03fef50306f7f0f70506f1fdfeec080406feec0cf30ff4e2fa031bf6fe0d0bf901f2fc030cec00f7f712fb0af9fff5f40707f1f8fe0809ebed0a251e10060cf22df8f80dfd031ce301f8d10532200deef401df02eeaff81206f70a000400e5eb17df9d05ec120ad8eee0b6dafe1fd300e40e1e0ffcdfcfddf0f41bf7e9e102efed03e9d5f2edf2f2eee6d4dcf50001f0e6fefde3dbccfa01fb0606aae8fbf6f2f3d5d6d8bbe0e6eeeadbe10002f7e5f4da04efb7f1e3ffead6e8180ed535fe05c9f3143dfb101cd111e3cce43c59f80b2112ff1ef9dbc324f2f33923f006d305e9a28c02ec0e261021a194140208880cd60d3011300313df0a07f9fdfefdfc0e0c0b060e12eaee00040b11f800fd04fcf10c00f8091ff8ef0508f50022000f0c14160c21f9fcfe00e6220905fcff2afe0d07f1dd10e8e9d4f307e7fbf606fc010404fc02f1ef070ce1fff8f208f1fafef2fff701f9fce5ccf3ff13f70aeb03f71004ed05f9fd000c00f0ea0705e305f1f9f1faf1fe16f0ca07fffd00de0903ff0905020905e8f605f5fa020106ef0701f0fe04fdeaeef4d7040d02ec0bfa08fd0fe8dbf6e6de00fdf3f6e4e0fefcfd09f1e905ea03e0ece5f9c612ece1ecefeee1051e0b071ad0bc0af4e9ec0543ef022109f7f3f8f6fde0e2f71eded102f3f303b8e8e022a41ef712eaf6ff0121f1e2fe04fffa153aeae2fb0df1ff23f4fe0dfafa00f7edec07ef1debfb03f60012fe0d01e105e8fcf1d6fbfc0a090edbfbfbffe2eb07f0eff9fa05efe8f3f6fed900e1fd1b00fee8fbd8fff404dade03fbec0cfbefedf7efd906edff0900d0ebfffb0f0af0eeffebf5f3def916d81fedf101fc00f4decbf1ebe4e8db02f4f8dd16f207e0d6d9eadde1e7ef050a12f2f5fff0f30cf7030f00f81002fe04f71317fcf8ef04f21214e1dfe0f20008e3000316180b03d90ad5e513ff11f2a9ebf80a05f705f8f3ea050ed0b8dcf6ecead90b0af103f1dece05eaa7fa0bf7e8eab9defcfdf203d5fce0d0e8ffdc05f09cf502f2f3050fb1dfb6f0ddd8d1cea6df04dae416bcd5caa2efe6dee406fbd2dedb0e00f9ed0be4e124d9d5020406e8e3c4cbfffded10f5d1daeaeec7ffffd9b0f8e4e2ffff0deecae000cceee9facdf1fee1f71bd6afd5d4fbdcf3d8ebaec9f4caf504f1d5e8d3f3e408dedc16f0f2e8de0b01e2f8f3e312fbced8cf00f4eaad00cef71afbefd3fde4dff31203bcbbdb18f1db00dfe9e8b4131d1e08f707eeeee004eaff1f21e3e30eaa1af0fc0bfa06fbbde0f9eb042207f91e073720fcc3f00c0af7ec1e0f56b7eb51f31aca19170afeb53cfee7fa1800dee1d3bf040ae9e8e505fafe11f5e20309e4e70cee0200f4efdf00fef5f5fcf3e4eeecf1f30106cf1000fcfbfc06e8f3e1ebd4e5f004dbf7f9d5050bdfbfebb9fced03fe18d50b00eef7fedd07efddecf1eceeef09ebf0f2f7e5e901de08fee6eed5f50803fdf203f238f4e61ef7dbb9dc36e9d4c1df13df05ef07edd9090bdeeee3e5a9f5efe3e9c3f90cf00606ebdd07e7caf7d5f6fee7d0f60cefe1f5ecfaf0c2e2b5fa08f9b019dbf5010beab1edbce2d9e9e0d9b1fa0adae4f7d7bbd29aedd8ccbdebcff712f0ddf308bfef20e50734421afde0f4c32d26fcf4f006e7f3f99d0ff1ecf539d5e1e2e5ebfdda8004c9df1af629e793d00257a8dfc5fc1d12e420e5e7fff9f30bebecf7111207f3f500e60207de0512f804ff010403fef800fee3f9dbf806f8d7fce602fb0ee9d700e7d704f4fc03e5ecfaf2edfee6ee03dbf5e8f3fcf61dfc17f10003e3f8f2e3eafef2fceedffdf4f10012f603040b05f509e9ff0cff04f9f0e3fef9020cf0dcefdfd4f8ffe1d1d3e8fcecddedd8c8f8e8e8f6dfe603a624f4ff0003feffec0726d94c0ff81ee306fd022d010c18fcf0c5dbf425fcf30d430edafae6dafacfbc0915c51fec33def303fd25bdd0def7f4f32b4118cd11f003e4d805ea2204fe11091ef1df05e3fa01030be50cfe1b0401f5fbe5f1f2f20918f60df5e407050cf7f3bce1fcf903fd140606f301f3091405e8fae2ea16ecedf4f00103fef3e0f610c7f03313cff2f7acdde9e703f9e3150639e6060fffe102ecfec80403d6e9f0fdcd31150101fa2eeb11f522ea0c04f1c804db3bdffcef07eedfd106fbf5e7fde3d70acdd7fcf3deebe6d4ef0f02e00acaf3e6d1cde0eb00e7b4dde9ddf914dddaeacef8eedad5d6a800fdeae8fac803d8d2d5fbddc409efe5fcc6200cf8f7f9e9eb08cac8e6ccfe01e3e1e9f90df1f8e7d3edb3f5bee3fdeca10ddef1f0fcd5c6f9c8e7ddebd3eebbceede6e710c7c9ed92eff0d0d7eef4e801e00802e503f3d0d9fde4ce07e503f3ead3f3f509e10901f2f1e904b5f201ffa30a10e9f4fffaede9e0f1e0e8e7e6ddf8fcdaf9f7dce5c9b6e5e8e8e8ffd3cff9d21200f4e603d9d9e7f6abe7fddfc5dadc10fcf4edfef9f1ebbd02e70afff090ffdc07f4feacb5f6c0d6e0fefed8e3f7f8ceec00e1c4dfb5e3000fe5fdf01feeefeff9f0f6f903d4eee9e6e60ce3d4ede7f8fbfcee01f2fc06eeeff8fd01f2f0fcf8e203fae2d9f4e3f0e9f1def3f1f1f806f200eedaf3e1efd3e9ddf7f8dde9f8fe050502f7fe0419fcfb0df401fef6ecebff04e604f6f7f5e7eaf601fcfae905e708f70718feeef0e2f8f2fef8e1edfbecfc0c01e4fcca1014f5faf3ebd3ebd6ee00d7f300deb1dec2acccef02ded7c5f4e6f4e00be4fde5ced7aade0ff085eac8f6e7f01ccceccfbfd9ead2ecbfe51bdfcce5cbddc6d5dfc6f1bd01e90ff8e7e6faf7fafe0005fbfdfcece3f3030203020001fc0f0a08fdd6f6e9f405f8d3fff601f3fbe3d2dddb0205f501f1dbe7feffedf4dfeb11d2f9f2e6faebd2feffba0102d207f9ea00e8f0d9cc2ad1b1e7dbf6eb032ffe01fae5e4fbdff503b316f7fb12dde706fce500f8eae8ca08db0705100f12ec03ccf0f2ca06dcf3d916fab90bedd8db05edd1e2ffcce9fae7dad6eafe10f3cfe9da0ae4daefe40df2052210dce70207ffd6eccddce6d8dbd0c909f9fcf00ce7e5cbf1fceae047ef2204f5f60cfddefdccf3d908edf3ee141906edcff8ebf6e3fdff34f9f51f1d0b00eae40c30030bcef420da0efaeffbe2e9e5c2f1e6410a14fe02ec02290a01fd15f720220600160f16f0fdf8fadaf00c0df902dd041bf5e503fefa201907e3f801e1f106091ff100171b1915fbfe07eb2b2c08fffb09fd200bf202eaddefb512eddafeb8fd04dff500eab5fddfd9f2d5f0e3e8dbf6eefd07fdf6fdfbdce7bff9020a8d04fdf501faedd1dcbddce3f8dac99fddf2eef80bd5ccce9de5ef04ce0122e812e40ff4070307e80039d2f334eafc3dfafae1f701d9051ace18fb01e700fbfaf81dff0313fb3010e3f114f1e4ffd316e2e8f70514f4f2fbf617f007c9f823f20f1c0007010d1fdb0b2604f92b040318f7f0e71202fc002ffb2525f4eeedfdc2fe19e40d171e290e0a0deaea08fb2e1919fff51a0904f8e2fafff10fc1f503e0cbfc18e7110e1fed0927c2e0f7d82828f606aae6f6f5fc2ee13129fc000700d0ef2c12f2231c396d0c074ffee5b4494619f3d72a2926e3e8e40dd71dd90cf8170df209f336f0230e091202eb002f120702e701fbfcfaf3e5d81215dbe81401f0f71efc1524171bfd2af4f103f9e319fe0706120ceb3edfffccfa03e5f80befe307f41605ebf6fafaf1dc07efc900f7dbfee1f30104f40cf201f50612e5e2fdde2307fc18cdff160aff3b0710faee1ff428f7ea0e0108ffba0cdd04001bff01fdf4fe0d03cbecfbd2e1eeb40f06ee15e31bf5c1e5eed2fb0821ecd614370cfdb7e3d910df09f0113ff0e66bd40daa061110f480182711e626f0cdecb99deedfc6e7dffe10eef2f1e6db0ccbbdf7cfe8e8dac6e103f9dc0df1ebf5c9d9b2edefc59af6dbe4f00cf6d0e3a5dde3f1dccda4e407c4effacbc8cb80e2f525d3f3ee1affc3d9f4e5eceaded106fae9f511f2e2e6d6def0f5e401f8ecf5eeddb2f9f7f3f700d7fef2ec0ce0edd4f4ebe7e9cfecff0aedfc04e1ece1c8f4fbc9e9e8cdee02d9ecf4fd02e30f05f6f9f902ecdf0ee600fbf509ec01fbf9dff921b3000201eff7edf4fe0bf7d519f5e5fa03200af304fddce509e9f9fed4012304eb0af804fafbfb070013f80e0a13ebee1405100eecf50202fd030508ea010400e412fcdfe311f5f70b0b28f2040109fb0bf40c040105fd13f9f4f1ebdc08fe16e4000a14edc8fafaece804ccec23ebe3fdeaec0207eb0800feef110df20b04fcfdf205e10603050cfcfae12d12f71fc8d6e80d2ee1fadcf8f90010dbe1fbd4cbc80fed00eec7f907e8fef9edf11cf2dd04f8f4dcd2e7e6ec0ae800ed0cdeddeff7fcfc2ac9f802f8f608f3e9f4dfe1fae5f9dcdf130100000bdcf7e2cd080bf9ddfaf0be04eaea05f706efd3e3f5dedefdf1fce3f9dbf303f9edfef0faf9f7f8cdf9f8efbcf5f0ff0205f2c1fed3dbc8ffeafcdaf6efe9f1fcdfe6d1b2e3deefe902f90d0de9fafe0b071e0210ff17010a29fbed00fc131b020507e40900fbfdf30a062b06ebf50a06ffdfd4fce4e7050cfc0ef00f012bfefbe8f7f8d808e5fbf91113f8e2e6f8fbe11510f60ee7dbf8f20704f7fedae7f5fee110dff6f5f1010bfe02fed2090e03fc0504f104f61efcf5daf3d7effcfe0907010bf1c202f8d9c813f208f3d8f3f7eef4faddfbf2ebcff3f4f6fefacf02f301f3fdecf906cc02cc05ffeba905df06fafcebc1f9d300dceedfe4b4d805dbecf8dbcaf2ace0fb0af8f318160501160f23031708071c0ee61308081cf010050bfcfc0ff9f0262bede0e30707ff19fc101901130f0309e8ece4fa0e172cf90e19f92c04f8f013f40b03fbd50af1de04010a07041ff01516feeefcf4cf0ce4f6f7f8c5f5fd0b02fece170a01f0070407071837f9f70e03ed0fead010ea1304f8fd0003fdf303f7ecc78c0ae2ad02b6eaf5e1f408fceef9dad5f4e7e10de2f3d9020fdf02fedbfed0eba507f0faa311d9030217e0a4d7d600e4faefd0bcd6f8e8ef03ebc2f4b2eaddd915f115fa18e4f613faecf7020206d60cf8ffc6ccfff6e500f50afdf8ea160ce63206fdd910fe12010bfee618d2fe1bd7fbc60711f9fbe9f901effedc13f8c3e1d211ca34e9c2d9f7f70bff37feaf54d90713f828f60a61fe0636fd0910aace10e0c0063aedcbc8f203cfd5c0bd0aadfadc3ef0f00b0756c8f2a50010071421d90ff0e60f05f8e9fff52cf5080017210eec0317fcfcbe0ae2fbf7030a030aed25c80205fdf9bff8ee09e6f9e6d62602240520fdd51c03eaea010f16dbf1043a),
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
    .actor_error_o(error_actor_enc2_extra_pointwise)
  );
  logic error_actor_down3_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(4608'hf5ef00e6f414e0eae9f2ff060ef802301b1712fa010f1307f8fdf705fe15d3d8e6eef8d5effd0d0d1f2531350feefef7eeec100b1103030b2312250ff901f40e04ff19f70af605080c08210bf809200d2be9dd021107050507ff17f90bf20909f6f61b0df8141c20100b121911fbfd0f01fc0515ffdeddebfdeff0001819f70d1ff2d9fff8f1e6fffa1de4e4ec171704fcf6ef0cff140f0404e7e4d906d7e205e7dfe313f8fcf514352914f3181514052301f6ff27fb32f91923040409f3ec01fb09f3080a13f101060e1102d2f5e61c2ceb230b002909f80004fdf0fd0800fef8f412feeb0cf2e800f7f1e50e15e90611eaf3e8ff0af3f311f7051501031df3fc0eece60beefaaffec9dbf4e8b7050af7fd181620102f10070a0512fe050401ec1eeb1809031209083f292a162633140a13fbfe01f8f6fa04fa0715f2fa13070711ef03f90023031229021b0111fe18e1cdf9eef301eee1f7dce4f3fb03f7060710f40d0d331823f1fbfafb03f10610f4f2fadd13040417140e14100213fef60e0f0817eefc01f4edfff7dcedeb13f8eef8edf10e0a1803fa0a1201f61803140c1a00123d1d230afe0cf706f3f4fbe3f3f80412e9171f090be1f9f6ffe9fbe1ff160dfc12050dff1a0ffa25170e141cfff41704f6f0f404f80b1301040b14030320ff0d12220c06fc121113020b0517fffcf2fd0823111b17270b0f0423fd0403110c00f60b04fd10041d03fae9ea05f1dcea2503080b00051a15fe12eefe0800fe1613151f1c2601f80e0d0e33f3091608071f102000043715342225220430),
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
    .actor_error_o(error_actor_down3_depthwise)
  );
  logic error_actor_down3_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(65536'hf40efb06fffffefc00f4f7f7f2ebf7edf4f80302f70af5f9fff3f2f1f401f9fcfb1203fff4f30a16fd0af1f9f9080c0df9fbf6feedf5060503fefa0af80ce9f3fffffaf1fa0502f8faf6f202fcf8f40102fa07fd09fe010101fa00feff02fefffbfaff00fff702fffefafcf6f70604f701fef9f8010302fd0600f003fd00fcf6f9ef0409fef30dfcfdf7fc05effcfffffe02f1f60702f002fa01f80afa0404fbfff70405ec01f704f100f7fd03f7fbfa06fdf609f0fff8fdf700fbfefff6fefc05f30201eaf5f6fef3f4f91408ec13e5fff9ebf407f5f70ef100fd05fdfff90ef6e2fcf7ef040503f302000f050ce1f4fe0810f8fde806eef4f610ff131804df04ebff0804fb14f3f1ecf603e8ec10e3f2f6eaed02ecf4f803fc010f0203fbeff3f7fc03e3ebfaeff5fce705fcf1d702df0cf7f1f3ef06f2ec03f2edf2e1fdf1fff5fcfefe09f902fefd0200f9faf4030aff0100fbf8fdfafefbfbfafdfbf700fe05fffe03fd020005fdfefdfff9f60901fcfc020a010500fafcfb04fffbfffd0ee2fa10e2e60ffbe602fbfbf0f906dfe4ffd9f601e91bf3000d0dffe2f5effeebe408f8f8ed01d201fbfcfd0104c815cefaf6eff9e6f4d6e7fbfdf2ded9eef204ecf8faf6fbf9f401f7fc08eff7f6f5fb06f4e908fcf0fe05020cfa0110080affdd0107f6f7feeaf505effaf3f7ecfbf3e40dfee6f5f6ee0504eefa08e9f9f9fbfe05faf7f90af90df5040800fcf5fcff01eef60900eb0bff0102fafbfa050805ed06faedf30306f205f5faf5e4e702fdfffdfaecf705f3020008f903e900f804e5eef1dcedc4d5d1e2eee1f2eff2dff500ebcee7e7edddf900f3e5f6efd00102c50af4f1fd03fcf3fcfbf7efe7f307d209dbe9e7ef04eadff3f7c9cbd7dcdb02e3ff1311f21b07fc0b061910081d0e0307fcf732070f0b0418f41ffe110c050feef7060724fef3fa0911f5fe10eb060cf00b240cfef20703020e111cea04e901e10ff4cedae9d1c7caf6e2f3e413e5eafeecdee7f8e6e3fe2113fbe80dce01ecbc030ed6ebf1e6e8d9ef15f9cdb8f8c702d4f3e1ddf7d1eef40dd0e0b9dbf3fc12f902f8f7f8faedf2f1f5fdf6f8fefef4fe07f000f7e7f9f9f8f8f2f6fde30204fe01fafd010d04faffedf1f400060000f1fa05f9fcf80dfdf507ff02f0fdffeefe0deff4e1f9efeffafd05fe03effafcdfe711f8fae6060b0d1b0e05fbf4f4e307fcf6ed03defbfae20100f1e1fbe201f8ece2e603dafc05f5e4f6e2f9d5feecfcfae4eae5dfe7e9efe3f5d2fbdbf206ead8f1fbf6f9e609f4eadd05e907eabffdfce503fcec03fcf8f7ecf5effcde02f5ddf1fdfef3e8fef9dbe1cdd6db03e6fef0e2d8c6cfc0e503d903dffcf3f30505cfedf7dfcff80bf5efd213dcedfcc20a08d9f1fde8f7f9f2fdf2d1e5f7c9f5cdedebe0faf8e9f2efdde1cbdede0cfa0513ef0114ddf512f0eafefa2dd3f20acffe0fedeaf3f6fa0e071313e40ddecf0702e4fdfadf0ff01d3a2609d70ac3fee31412e2f6e9fbf92e0bdaf7f9d0f706ffeefff0ebf6e7f6f8efdd0ae9fcfcfefc06e1f9f0e2fdede3e7edf9ecedf402f601faf4020afef4f4edecf1f9eff8f9f0f50dfafbf70af9defdf1fff1faf50a02faf7fbfdf6ffeff9f8000bed09fff8fb04ea0801e300fe06f5ec03eded0b0308fa08fd01f8fafbebf0faf311fcfbff0302f90602fe0ffb080af5080200f5e4fe0feffa1bfe0500fff9fee41fe7f8fbeef90bf40805f9000a1012feed06f5e000fbe4f8fff0fbfd06120f10e415f30cf820e508f5eafff82405faf8fcdf1cd0fb0e10fb180206f5051f280a11e0f7fa0be017f8002d04fd100520fc10f8edeb07fb10f705de0710fbfef103dfe1060c20f9e907fb03dd1216e50a0e1419f716ffd8eefaeb0202f6fafceaf7e503f9fd0808e201fbef01ecf1fc11fcfed801f1f3fc0bfe0507f4fbeef9f2f71200e2f70208fdf3010c0c06e8fdf8fdfb08f506fcdafef309f9e6f6e904f1e6f90e06f80406e009e0f3faf3ffecf801f7f602f3fafbf7f70d13f6fff5f4f3f60bdaf400ecfa0110ffe615fbef0beff3faf20ad8f702cfc6d8c8cdcefcd8f0f2f7c0eb0df1cce6f7e3dc0008edfde708caf5f8b902fdd6fcfadaeef2ee08f6d4c7f2bef7deeae9e1f0decaf3f7cad2ccd1cffa0ef9f5fffcfaf5ece7f2ecfd07f006ecee090bd40af5f3fffdfbfefafa0e01fc1f090203f6f809fc04f0f7f4ff0ef304f505ebf80cfffdfbfcf4fe0516fa0a1ac01608dfedebd9abdbeed104dc04a8d0fcbaf4f1d7fec4fe0108f714f4b0eafbc90c05fbdc00d4ebf8f621f5f4a410ac04d7e5dadbf5c6d7fc35e9a2b3a9a3f9ef01f9f9fbf6f403f1fcfff5f9f8fefcfafeecfa0600f70001f803ed04f2fdf3fa0804fffffa0305fdf103f6f4fd0005fafe00f7fc04fe03f9fff200fdfafa13f600f2f4f7ef0901f7f7110aeef7e6020909fa0ffdf50cfa05f90afff7f2fb01def80bf40bf6defa03fef7f8fc11f9fff5081bec090809f50bfbe5200b0c24010ff9ec03fbf9f3fdef07fbf6f9fafdfffe03fcf8ff0b060500fdfffe01f9f009ec0303f7fbfa140400faf9f9f807f3ebf303f714f602ea0500f306f6f10602fef9fce9f1ef05f8ffea030d01fcfa0cf8fee3dc0bf7ed0606f9f0fde90204fefdf20506fcf9fd07f602fcfbf7f2edfaf8050213eefafdeaf200f3f306e7ee0009f2ff0008f305f000070308010f080afe0903ef09fd020afd001507fffa0304f7f700fef3f501f1fe0bf713fd0df707fd0ffdfdf3fd02070104050008fa05f50ee6fd04eee8d7edf6d103f1e8e8fdd8ea0ae6d1f0eae4ebfc04f3f1e5fbe9fbefd206f8e7e8fce9f101e60910d5d6ffc816e4e2ebef03d1e300eee7e5d6e5e41105051bf7f1f3f60604f512f6ff05ff0a13faf4201500f8000eff22fa0a0cebf1f10009eefafcf4dbf7140102fde0ff0cea0bf80f0605fcdcf60bfd1de8fafc02f0fcf6ecfffff815f9080207ed0cf40204d0fe1af90216fe0b0e1506f4fbf1f1d50afd01f604ee03f2ef1a06ede3040009fd08f5e502e0fcf513f8fce904feff08f801e7dde2ece7f8fcf5e7fef1f7f6f712e3f6130fe6fd0a04e3eef2df0707df07fcfcfa00e7fefbfbf0fde0fefce1fee7f4fef805eaf604f3f9e7d4f1e8fbfcfe00f6fbfaf5fbfefbf7f6fbfcff03ff03f9f9ff02f000f9fafdf1f700fbfefdfefffbfeff0402fdfbfbfffbfafafbfbf6fa01fc00ff04fe00000000f7f9fff4f2eef000e5edc5f4faf3f3f4ef03ecfcfee7e7f404d4f700f4efe8fde60904e00bf8f6f008ee0a0104f6eff2faffdcfbe7fa0ff405f4f60606dcf2f7edf3f6e803f9f3f8daefd3e5f0f309effae6f502fdd8effcfae5f90a02e6e60ce20814d6fff1edf209f2f2fa02f1f6f3f2f3d9eff3e2eaf0f6f0f6eef0d9e5d1dfe5fff7fe02edfce9efeaf109f008f7fbf9fafe14ebf3f509dbfffefafaea15e0fa02ec0107e302ffeb0102fcf7ffe7f6fce406eaf1f5f502fffe00f6f0e3d9eaef05f30501001815f6000604fa07fb07f208fcddf203eaf600ff02021c190903f7efedfefbf003ffeb0a01f10f0708d903eb1301f8edeffeeff7f7050800ee04e802fb0217f2e7d8efe3f4f2f9dc0103ef0302fe06e504f0dcf9f9e6eae2ff0007ff0400fdf4fbfa000d1706f5f3f20608f4fafaf10307030b01fffffc0405e0f30dfa00fa06030a05fc0201fff5030709f8effc0304f929090907f9fb0300eb160605fbfe0715010305f9f60a080ef60aeff2f006f9f5020bf700070ceefc0209f6ddf90a13fb09fff8fa02f501fd0d0c0508faeff9f619050d0401100600edf5ed0805000dfc04ed02f4ed03f4f2d80df5fafbf7faf20225f50315fafce9fff2fbdbfa17150e10f7fd0b050bfe020d060c0d07ee0ff9070e08081429100b0efff30801f80af8f1d8fd07f10deeffe804f00a01fef3edfb0dfaf408eefaf311fefeef04f5f2f104f5f3edfbf5ffebfde7fbfed8e1fdf7e804f8f51808f0f9e6f2ebed05fee0f000ea0100f5f804edd7ffff07f9f7fbe703e8e5fdfef208eaf9f1f811fbffe90be8e9e1eff0e8ee0cf205fcf6040dd61601dafaf9deead5f3fcf6fd1ffdfae5f50302ef08fae7e6fcda04fbf9f6fa07f900ecfff4effaf509e5ea15f7fc0cf70afeecf6110bfffe0715fdff06f9050e100510fbfd040a1103040bf3fb01fd0318fcf10708fb120111fe15f610f101090102fd02fe0e06f7f8000105d8fcfdebe5f9dfe1de01f404e8fde5e2fde8d20df009e9fdfa04f6ee02e5fff4cd0bf7f8effee4f2f1df0003e6d7f2dc13ddf1f7e000ddf0fc0cdce3cef9db05fa010af6fefdfa04f0f50204f508f7f8f5eff5fdfaf20500060bff05fbff00f8e00602f80000f2f9fef90b0005effff80dfd00f8ecfef0fcf800f50feeffeb00fafbf7fce9dadadfe5fee105f5fef2fdf9fae3fdf6f5ee01f3fa00ecfcd5f1f3c8fe05def202fc0006eefa0af9e701de02f3f4ebefff0af2fbf6dce4ddece5ffd6f8fee8f9e6ece1ff02f401ea07fddcf7f0ededfbf3dbfb0ff801effdf00018d0f504f8f10ae409f9fffd01eaeb07e100f6ea01f1f8f7f404f3dfe3d6fdebf6d5f9f2cdddc9c1dbd6f9e1f7e6efd7ee05eccdece9e3e50102ffdfd7f1d0f807c1f601dcf1fbe202f6e9f2f3e2bdfcc20cc1daeaea03ddd505efc3cec3ced3fe01fcfcf4f8ebeff3fef7e5eef8f0f601fffaf6f309f1ea00f8f6eef8fdf200f9f0040605f0040bf9f6fd04eeef09e8fdfde6fb070104fc0cfcf10701fce6eeecec0bf8d8efece0d7e1f5e2e8f0fce3eb040fdfe8fa15d6fd09fdf3cef0d9f9f0d3f3f8f002f9f7fbfbf4f6efe6e3f7dcf2d8f5e9eb04e6edf8f8efd8c0ced80209110bfb0209e9f80706e703010802f711dfff0900fcfcfb0d1cfe13f9de06e5dbfc07dff6fdfff8f8f9f8150efd02f8fdee04ede9edfff5f0f1ed11dd09f703effefbe8dde5dbe3f2f3eaf801f9ebed0bf2e7f4f7f6ed07fd09f0f1fae6e9f9d10209e5fc02d001f7e4f6f5e1daf5c801d9f9f6def8ebec01fdcde3ebdef613d700f6e2e9f7cacce9fdeaf6e203c8e8faddd0e3dddbd900fa07f4df09d3ebf7c3fb05d3ed07c705f7df00eae0c000c3ffead3e4daf4e0e5fefaecdfc0ddd5fff5fef9f1f1f5f700f5f70305f3fefefeffe0db05ebfafaf608fb0017f300efede10106eefc07f3f8f7f40708f4ea06f515f2faedeff9e7effdf9eefce103f609f6fd0913fb06f30bfefdff0bf0fe14f6e713e20108081109ff0ef906eeec0bee1207060eebfefc0b08ea0905080bfcf51700f90bfcfd1016eff8ff07f8fffe02f1f9fefff9010310f20506f3f4fff9ef03f6ee04fdf7070605ff08f9f80600fae40105f90203fbf8edea07ff0df5fffe06ff08f8f504f8f6ff01fc09f3fdf1fcdafaf9cee8d9dfd1eb0beae90101e6ef06f6d4e3eff5d3fef5f2e8cbf0d2f703e100fdd7f010fcf405f5eefce4e5fed1fae1e9f2e2f9e6ea06fbe0e9c1eee9f9fd01ffff0501fe0302fe01f9fbff00f7f905fffffffdfbfefb0300fafb01fffc01fd01fefdfeff01f9fa01f8fbfafe02fbfb00f706fe01fefefc0108020100f113fe03e4e30d03feebe8e003fd00ff12f70b12fa0afde800f8ebe0f3f7fcf50d10f904f5ec0907f8eaffeafbd7f9f4feffecfa0ff802e71601f4000201d9ec05e10300e500f8dceee0faf903e20ae5f9f7d8f407f20809ff03040d04f2e2f9f6cdfc01e406fef103f8e50311f6cd03effe01fce5ecf6ebfaf501f0fee2ecd6faf4f3120300fafcfff7f4ece9f4fb02f7ef12fcea0606ef03f1f4f2e600f702070109fcfefff4fb00fdf9ecfafbeefaf8fff2f0e80df9ff09f807f2ecfc00ed0a0dfd001d07fb061201f1eef60a091828eb0ef2fbe414fbf10412f6fdf903ef080e0bfeeee2eb0916feeb1405f507ea05ff21020406f41614f20f07071a0e160008fbf6f600f7f8f9fbf50106fbef0103f306fdf70501f5fa0505fcfff8fdfc0dfbfffdfcfd030402fcf400ffff01fff604fafa010000f50afcf907fffcfefe0debfa01f7f605ee05ed06f5edfd04d90bfadf090fee0a09f602fef40f10e9f1f1ef01f3f801ffe9f407e1fe0102e5e6ea0811f6f6f0fbf5eff6faf80deef8d501f70205dde3e1dae0dafceaf0f8f9e8f501fbd8dfe601e402fefef4f4fddef3f9cbfd02f6ebfaed02efedeaedd0ea00d8f5e6f5eeebfbe2e7f4f8dbcad7d6e3f6f2fefbf0eaf0f204e4f405f5f4f9dff3fbebdc05f0f2000603fc05ed03fcf3ede80705e7f309eaf9f5f2faf8e6d2feec01f8fbf3f1f6e6fc06f9e3f4e7e8e810e80103f0ee00ea04dcf2fdf8fb0efaecf4dae9f8f1fdedf5fefaeb0702eff7ede8fdf9def7fcf80305ef0b00f5dcf5e008eef7eae8fce3f3fc08e4e7e2efed09ed03fe00f5110e06f90a0906fb06fefaf2080804fb100dff0a04071206fa030cfefa000a11fefcfefeef01ef02e9fa0af41607f0fffdfcf3fe0b07ffff070d020501fcfbfffdfcf400fa01fcf9f20900f90002fb0706f3ffff05fbf7fefdfdfb0400fc00f9fc04fdf5fbfc02fdf8fefefdfcfa0102fefb080304ff03fdf4fefb08001bdac4f9f1cbf5dec3df0406d7db06eceaf023fccaf3e7f0fdd6f5efeef5cb0906d905ece1f0e8f61801f4cc16d71de9e401e9f5dff5ff1adfd7ede4d5ffeffb03fae90df904f707fef0f0fff2fd0febee0bff0a16051914060b0df6faf8f805fdebf806f5f7f9f10e1001f511edf2000fedf7f5f804fd07fdf4e603f30ceff9fbe4f3f9fc05ddfffa01fd06f1e40ae6e205e9ea04fdfc06fa16fee9f5e8f2f806edf6f6f4f8f8f41afaf6ebfdeefefafcebea02dcf0f8fcf404eef2ee14effe0e01090bf7e7020a07f80008fbf4ff020d0a1200fafcf4020f190a071600f0fbf8040500fdfe01ff000f0dfa12fe0a060efef704fc0203fd04f4fcfffe12dfff0eebffe6e7fff002f0fee501f1e9fcedec09eee60dfb0100fa0c06ebe7edf0fcffdaf8fed6fd06e413f5fbd8e6eb27f2e9dfe0f9ede6ee0f08fae7eed0fdf1f2eefb1af0faf009f7f4d910fbff02ef1503fc0001e7faea02fde9ee00fbf7240101ebf7f60ef41bf7fd0ffb0409f7040e03fef20520fff4f8fff419f3f106eeeefeebdcd9e8ebe608ed08000bedfbf9f9e202fbfdecf3f800eeee16ea05f9cc0504ed00fd02fdf5f1ffede3f3f3e5ffdd01ebfceff8e4f5f0eaebd7e4ed021cf8ece1fce4e2dbfcffff03fded081208ff05ed15fce9f70303f0f5f9ee0215ef0400f2f7ff0008fbf0e9eaf205f3f60609ef09f9fef71bfafc10f5fb0101fefafc01cbf2c6e9dbf4f4eafcf901f9f1f405e6e9f603e1030df0e1eb1cd80618c6f90bf5f007eb10f502fdf3eff502d1f9e9eaf101fbf3e5f8efead7cdf9e8f4d40010fce2f0d4fb010cfaf8f007dcf0f2e3e3fcf40bf6fdfd00f1fdf2fc1110cd09f8f109fbea0716f8030300f0f9de1fe7f0faebfa04f502f7f9e6ead1d7fef6fe09fdf2faff04f6f9ff07f80507010307f3f0ff2502fd0003f606fcfd120102fbf804fbfff20201f20cff0ef1faeff606f1ee03fd0bf406000400f80a0cf4f603ede5f4f0ea0ce300fffbf2fde2ff05eae105f7e802f3ff0305f004ecefebe2f9fcf6f005eb03f8f411fad6eaf8eeeff7f4f6f8fff4e9fe0ce508def2ec05f90005ebe6f0e3eae7fee3f602f9f30002f3e103f0e9f9fd0f0debef16eff800dcf801cefc0b09f702f80400f9eefcf0faef0fe6f6f6ecea00fde2facff7e61ff3faf8f31201f7fb100a00fd0303f9eefae80c1df522f5080906051cf70907fbfa0508f107fee50f1209010216f80ced00fa031cf300f7fffd0906ecfbf6eefdf30a04f6eeedfff3fdfcfaf2f709fa000df1eeff0df5f8fd02fd01f110ed0306e105fef3f4fffaf2f900060301f3faf600f4f5f7e7f9f0f1f8f4f1faeae60010ea0e08e7fe04d6f7fcf1e2f6e40edfe904d8150bf612fbf9ea000a180aec19eee2f2fbe405fefcf9f3e70c321ff8f4e3200e0fefe6f2ecfdf40cfeeffd05d705fd03fefafbf9fb0006f9f4f9fdf3feeff904fbfc0a02f602f8f5f5fdf8f3fb0200ff03060500fffaf8faf9f8fcfef903faf4fcfa0000fa0101fe01fdfdf60200ebff16eef3e9f2dbf703e9fcee0ef0ebff09f2f9ed05e401f8eedfdf07e30906ce09fce8f206f2f009fcf1fedde9fae305cff0f1e700ec0204f5e9d8dbf5ecf9fffff9fe0ffbf807fbf70ffbf5f30204f0fd07020d0af901fa000901ff06110503ff00fb0804f80207fdfbf405fe00f30004020c08fdfb0fff080103fdfff00ee803f6f5f50ff90bf30af310ea02e4fd00f31115ece8fe030306fe02fbf8f9f7d9fa06f1feffdef6ffe80ef4f1dbf4f2040207f2f3f4f9e9fbedf7fefa16e606f20b0ef6eafbf9fb0b110c02e80c17f8fd04fa020123e2fd05f2eeeff0f3f9efd308f912e1efdd08ff0212fcf0f3fcf018f304d7f2f6eaf70ff3fbebce01f2fd12f9ee081510f203fafdf30ff6ee150905fdffe90301fef8ebf6f41f00e7f6fff107f9140d0800fdfaf211f4f122f6fd0413fe15080416fcf8f411fb02080b0ee1fb0b02fcf5fd06f10c0bfb0709fcf10efdecfaf1f2f40009ffedf9f8f9faf4edfffa02edf9f0fff7f704fb00dffee206f3f3f2f5faf7f1f612e8f5e5fbe908e7f2f4e7eaddd6dcdefbec05dbfedee505e0dcffe8e4ebf605fcfbf904d9eef2c0f605d7fbfae3f7f4eff7f0e3dbecd201eddfe6e2f0e8d6ffe7e6e1d7d4d6feeffd02fefde9f7e1fffbeae2f8f603f5050bfaedf602ea0300f5f5efeee801fdf30603fbf909f100fd00f9f1f9f5f8eceef0effffe0505f103fff1f2f1f5f60801fefff00205fe0ff4f802fefa09ee03f7ebf001fbe904f602fd05f6fcfcf3f0f40607f3fefcf8f9fff308f7fadc03f3fd00fde7f906e7f5fb15fa06f1f600fa0afbf4f704f5f3eff2f2f6f2fdf20107f701fbf305ffecf8f7f3f3eb00fcf601f70000f803fe07fefcfdf4fffa02faecfbfefc07f303fc0e03f401f6f9ee01f9e8f8f9ecdae7d4d3e4f2dbfbe702e5f205e7d1f5fbfaeaff1401f9e9fcd6f5f9d2fe02e7fb07f0fa02e802f2ded4eccafce3ececdd00d6f2f2f9d9e0c3d6d811fb001dfdec09f5f6e7ff070110fd09040801e60200f8fe04f8052904f713f5fbe70d080000efeb09faf00c0903dc090310f204fdf50100ff05070707fcfb0d07f2fef5f7fb04030900fef9f6f0fef1fdf3edf00bf60d070bf903fc0003f3fa01dd0005e800f9f8f9ffe8ff06f9dffaf406f70df1fef6edf80401f300fcff00fcf4ffffebfafffefb03f3f7faf6f80bfefd02f6fff5f7fefe0506050603f6f6fbfa070307faffee03fb0e05fd01fc0404fa00fdfefe02fb0500fbf70af80f0102fa0b06f5e5f4f2e7f4ece7eaef06eff60e1a06e90cfbfafefaefeed9f8dcf7faecfdfcfaff0b02090d0d07e9eb06f2f5fcf1f212f7fcf6ecfe03effbfaeff2f503f7edf6f310e3fee8fcf318dff2f90ef306f9e804dfd1ffe3e9e40200f9e61911fdf2e5f50a0b0b17f70efbea14f1ee02fefa00fc09ff02f9f009e712e9f702fe03fb04fd02fffafcfe0105fdf804fd03fd02f7fbfa07fc0100090606f709fb04000300f9fdfdfefcf305fc02f701fb06fd01f9fc0009fe0105fdfffeff020bf3000dea0206f2f90cf818f6f91bfd0100f8f30dfe17ff07060003e8170c1504e90601f311050202160c04071606e007020109160df902eef911120af0f0eb05120321fb15ffefe91b16fef5fc1804f0f8fc0df5f90df700f6081b050cfc0bfd0a0500fa11fa0d0cfc0503f7121308fc160600100df70714fe00ff150b02e903effbf4eefb09e4f6f9faf8f4f60bdced00e7e607e7f7ff03f3f603060df102fbe4fd04e7fd04ef02fdf20705f3df02e5fbf702e6e6fed8faff01f8f3e3ebeaf4f5f202edf6dcf4cee4fddce8fffbeafc0501eeeaf8ffe2fb07f0e4ea0be8f800e2f5fee0f70af9030bf9fef7e4f4ebddf6faf4fcf0f8eff4fbf7e7e8d6e3e3fff4f5060105f8fbf0f3ff15060bf1ebf9f9f6d70bf9040d0a09fd05f800070106ff02050b0705de0602e30bfe00efe9eb18def7f9f3f70de0f50900f4f40014f5f00103e9fcede8ecfbffe4eb02f7f9ec00fc02fafaffedfcf7f2f9f802e7fbf8ed07f9f5f9fb06f9fbfafaf1ebfdf3eaf4eff6fc0ef8faeefdffeaf9dcf8f700f0fce6eaf6f1e7e8ecfbeb01fff4f703fa0de7e50debdff7fef0f0dbfafdfdfaed01fbe2fc09f4ef0ee6dc02e80802effb0decf8e9fef405feebf0f706efea04fcfeff08fb01fc00fffd04f101fa02f8010306fffeff01040709fcfb0000fbfc05fb03fe07fffdfdf9f903f4fcf8f703fb0408fefdfe0300fcfd0105fbfefa0ffbfa06f4f4f5e8eaedf7f0fee805eeedfae0ff06e8f6f6f80109010306e3efeadbfbf8ebfa09e403fbeafffefcf606e512eaf7f8d8f7edebfafde5f4e4e8ea02e004fae8e0eae6fae4f7faeee907d8f1ffe9dbfde6e2f2f5fcf9fde9fae4effed7fff7ebfb02e0fef2e8f800e8d7f3df0af8f2dee2f9e5ed00f0d9f3dce6de02f6fd0001fc00fe050006fd07f80303f8fb03fc0405040003ff020e1300ff0bf201fd00fd02ffffff01f6fff807f7f8f80bff04f6fe00fcf7ff0809fbfa01f9f6d6040fd9e7e3ddd4e00ad2e501f7dbe70ad9c9edeaf0d3fedee9f3e6f7ddf1f7d20cf3c1f2f9ecf001e1ec01e1c900d3f9cde6dad6fcd5d20006d1dfbbdcd7000f01f0f3f5edf8f707f00507ecf6f8fef305fdf50b07fff5fcfcf5eafefdf9fef9fdffff000306f5faf8f8fef701fbfafaff0a05fb02010af9fbfe07f6eafa11d609070eff00f5eaf7040504f401ebef07f9dc06db1b00001205020900f9f7f2020b00ede3fdf7f7f9df17eff9ea05d708eedfdbf0fb0200f3fbe4ecea11e4ffde0dfde9ecddefecddf8f3ffea07eff60aeee3ebf0f9fcfe0beef7f914e9f7f8dcff08ecfff8defdf6f3f9f3cdd7fed9eef6e1e8eb0ae7e902f8eeeacae8e707ed061bf6faf9f5fa0a0914040e090b1703f6fc1c07e7080a00fb1f00fb2605071c0900e61304fcfb0e170602faf2fc09f4f8f6faf9f60108f511011708ecf20edc031be2060ce9dcf607f102e80bcbd8fdd70817e7faf1f309fe0dfefbe50adbdd04f4dff2fed802fef5210e07c501d7fff4fde7e3f4ecd7f106f8e5dde2d300ddfc12e0e7e0e1d6daf3e7e3f601e3f50501e2eae705d7fdf0f1edd9f6def8fade05fdddf619f1f504fae1fbd1e8f2d5f3e2f3e9e406eaf10008e1cac6d8db0d0200fc01f90efc06fb06fefa000600fff2e5f709fa100905fe02041103f603fcf2fc03f3fa060101f7ee020803f7fef907f9fbfcf203ee050b02f502effb0009d7010b1603f00d1e0b0ef51210090b210e040cf6f1fa16fefdf6100a0302fcfa05fff6f5faf9edfd0afb0402ff0bed0e2210f3f6fcf606e3fff2150b190fff04f90702fcf7f0f0fae1fb03fdeefae2f6f5f0e200f6e704f8f202fefcf7f6f2f8e50704f2f9fcf5f6faf015ecfbdafdf40100efe1f3ffedf70a02f401ebf6f3),
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
    .actor_error_o(error_actor_down3_pointwise)
  );
  logic error_actor_enc3_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(9216'h121121e6f710e6dfea182a0d1323f4dfe6e0f90af0f10c0a0304193a0b1c04261c1e081bf3f5020b02f809ed06faf803ef02190c2c06e9eefe23fc2c2b260ef3fc1dfbed01eef30fea11ffffe70013f816fb19250cf710060d0adef3cee4fad2ce0504f0fbecfbef07ef05f200f707f6fbf9fcf90100e7fd0f0f1509f2eef1ff001813ecfb13f7f1f3131212fafbf1ec200412180b023103280629fe20211c1bec111711d71d24c0fe13c4f3e9fe0bf0fbf116e60b050b2316f31e140e270a2226f5203742520e073500ff001af9420101070c01faeff1f038171339ff0c171f2333f3fb2afa162dfb16f7e5fe050f00fef5f32925ee1502e8061de701ffec0afbf5feea04fffa07f61305eb0cf712f826121afaff0bef17f50a07141a131c04f8ee07e2f904fc1a150e0efe07f4090c0a1116110c021ef7f415ed0e0cfb0df421050f1d07efeeefeb1508110f01fafffc02f900edf6fbee12faf20cfe0602240c2c1218180913130af1f5f0ea05eafaeb0b1612ef0f0ff316280c06f406f9f00c0dff100c070af410110e23ff2206f301fc02f00047360b0a0f18094144082e3628322e372316f9ef080ce602fd00ebf400eaf7e61207fd0ff6fceff6ea032606f8f906eefd00020efa06f010f60afe101105ef1e1bd920eae0fb07cd000216030afef7f21b1417e70c10eeea03e6fa00f8eceff4f80ae707010906f8eb161a0ef0ff00f1fbecf4f2fc0d101611fe07091f0de9eceffe0ff9f0f113f90af60cecfc120d06f41606fe1025f5130a17100c0a19ef151afde3d7ff0003060ff50500f527000a0be8f3f4f9e118122d3b4149512bfe250ced221f0145f5feecf004ec07f8f515faf81604e70306e80411f3f1eee903fff214fd06170216effc0022280014001d302452fef9eaff0616ec0bfc1a0b19f7051005f80eee02ebf7eb0fff0b12f306e608100100f3ea270b02feff12043323fc07f2171709150d051c0e26e1d6ec1c13e006f80b12f01704fef9080c2114f50f1c1a26080c1beffe06faf211ed06ececf7f103fb0e3efb0306083a2af81ef8e801080e16effcf7030e0313f8fbf5f9f502e4eff2f8ff3502181c0d0f21f2f50aecf7262230f71d390f07fef5ec0604eae8f3ea03fbfbeafa0c120303e90b12fc200e2a1d1c1910ed06eb0207e607fc0715fee0f902f60c07242f371019131c1044fcfe0103ef070e0aff170e110ef810f5f4f3e7e5ef08fff50e0a030b08ea0408f411ed0cf5ef18f6ef031c041efefcebfce6ffefea19e407f5d4e9eaeaf1f9e7f709eee50f02ee081cf1111bfdf5171e220a2705150a12f00e130be64bfd14314a3641f5fdf7fb0c05f2f11016031ff307fff5060afef8eefb12060d060d1e1a0bf0fc100316f30f1105e9ebfd090a01ffe803ebff15320600fffbf4fb1710ec0bed14f7f6201de41d17f9fa00fa12121f081b1316eefd09ef16110d10ef08f814fd030b020621fc1af3fafb1305e9040af3f60c020002fe05fc0a080a0208fbece703fb3121184221590bea0cea010507fe0d3d0c2a100409e2f40606ecfd13fb1f071a2302010a0811f4f210f70af30beff2fb060501f80e1c12f91e0f2f38f1f711d8fdece71115),
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
    .actor_error_o(error_actor_enc3_depthwise)
  );
  logic error_actor_enc3_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(131072'h05f7fa0a01e3edeff806f2fa08effd09fd23e4fce70817fc04fdf5f30cf7f611e1f7f312fdfe05fffdcffed6fd15fd0408edf8f5ecf5f601f502f4f807e0ecf41d0804060303f6c00c08fcf8fb1008f8fef6fde6f5f201031001fb03fff0feeefffcf800fdf2fae4f42defe914f901fbfc06e2ef0613f0f713fb0f08fdf61bf107d4ff080806e7eff50af1faf7fc0800f2edd2fefdf7fbfe100df3fafbfe0402eaf5fa03fd05fcfdf3f1ffda07fffb05fd090407f5f5f205fe04fa01ff02effbf5170301f9030111fde8f5fff000f8f8f60301effdfadafdf503f6fb08e8f3f80508ff0807f8fc040200f407e104fb00fcfff7f0fbf6faeffeff080bf7f801eee4f6f8f4f9f9f40001f608fbfafefdfef6fcf30131f1ddfe05f5f5120f030808ff1205f6f8fd0bf5fd12131ffceaf80604fcfe07e906eafeed031b09ff00faf50001ff0601fffe16fdfcfafe14f5f61bea0e03f3ffffdd0af3fbfb020508f2f903f7fbf90607faf008ea062af803050700fe09fff9e1fcfee8fe0405fb01f1f8edfaf91afd0afcfb0001f1000703f9fd04070807fef30a01ed0c00fa14faf8fb0ffa00fd07ff04eff406000effdef7fe03020202020602fdfc02fbfc0a09ff080cf40500f9fdfc1805effa04fdfbeb07edff010602fdfa03effbfbfffff7020702f7ff04fd0803f806010601e1f9fb04fdf3fe08fe0800fe1106fff803f70602fe12f8fa06fa2908fffdf4f801fafb020b08f70004ed0902e515f90dfeff08fffcfcfc04030302fa0008fb06fde4f5ff050cfefe0403f9ff0602ff000107ecf503edf4000503f90503f9040205fadf03f10007f307fb02fd0efdf8f3f9eddefc05f6ffff0102ff0402eef60cfdfcff03fbeb0103ffeafe0600f7f11502f7f1fbe9e2f3f5feefeef5f7130af704f4f910e116c70325000301fcef07f6ecee0518fdeff60e0703f9dff5e708f60cfef4fdfc15f402fcfadefffcfb0f01f8f3f8fbf42818fe0108fdfdf802f6f6de14f503fbfff411fdfce7f4f702f3d401ece6fd01040a22f3f702f506faf5f803f50526fbf7f70507ff05020cfc00edf5fc1efee7ff00f8f901f20bf3fefdfc02fbf606f7f1f6fef0efeaffddf7fcec0102f8f7fa0604fb07fe02fcfe00f707fcd2f60003ec02fbee07f900fffffa060805e9f9fce1e603ff00fffdfef60207eeffc6fcf5fc05ff0600f210f808fbfd05efef09ffec0f07ff0803eafedcf9efe5f8fde8f8f301fdfdecff01f0feddf0fb0cc612f200ff0904e9f80704f602fdfffffafbf0f8f7061801e9fe04fc00140206fffc060001fdfa05f2fdf3050c0dfee9040600fcfc01fefbfb02fa06fb0100fc03fafdd503fbfb0700000afefd010500010be5070209fe00f402fcfb0406010af002ff000003feff021102fd0d02f8fd04fdf9f902fbfdf3f802f0f8fffb0202e803e8fcf9fcfd010312fc03fe020001fbf8effbff00fb0b050104eefe0b06f9f9000a03fef00501fef7010402f704e8e906f7fbff03fbfe070100feff0308fff0fdf3f203050601fa0b06f6fc0707f5ef02040102ff0401f405f100fafa02fb0a1700fbfb010200020803e9fffbf9f8fb1002f6040804f9fc07f6feea03fc06e80df5e00ae5f2fbfb01fbf70afefe00faf5eef6f3fcc6caccfbea00f0c804faf60012dcea0ffb09fde50005f600f9e8c7fa0200fcf8e2e2f7090cfbf405f0f7e2edc5b1d8fafdf805d401d0f8f7f9eebb00e8e8fecaf5fadad4e4070904f616b7fbfc00f5f60bf7fff7fbba04fef70807d107f1f9f7f7d3eff5e70bb00feceec200e5f5ff02f9f6f603f6f1040503fa0000f5f80903f9f1dafee2fbfe0a0408fafaf7faf8f7fa02f90303f4fff8f6ccf606ff030705e3f8fbfc00f9faee04fef4f6efdcef06fdfefbff06fef700fdf4cb01f0fd07eff30200f80707f906f7f8e5f9fcf6f5030d0907f8feea07f5f6fbf9f3f9faf8fa02f10307e404ebf000faef04f31805eff403ee1b08fd14fcf9f6000403f20109ced2c406c80702f7040deaf90a0f13efec020f0cf4fb0102fce9e9fc030afffee60ef8fe0ff9faf503fce2ff0cabe205110108f3021d0301f511ca05f214fad8fc08f900f709040a0114cc07f90403050708050001c705fcf902f9f20bf6fafffbf2fd0be1feab00fdfdc1fefdf200f8fbfcfb02fcfffcfd03fffefdfcfafdfffcfcf600fdfaf9fa0202fb00f7fb02fd04fefef9fee9f5ef0004feff0203fefe00f9f5030402fdfafdfcf602f900fa03fd0103f500fffc04f800fefc0501fff60200fa0300fd0205fffe0102030101fdfefefeeffdfaf9fa0601fffc0002fffefdfc00fc04fdf3fbfafb03fce90ffcfa03fcfbfbfff8f9fcfcf5fb0107ebf904ecf8e305e9f9fefbfc0005fdf602090406fb0009f007000cfbe3f9fdfb0b06faf6f80007fc0104f80404f1fdfde8fb020700f607fcf900fb0200ddfefcfffff304011a00f805fffd03f2e8f602fcfd03fb0afafe0af007fd06fcf9fcf7fd0107feedff07e605dc0a0101d805f9f4f2f305fef0ff05fcfd02fb030100faf7eb00dbd6e1fcd1f508e4f7f7fa00f605f5ff0006f80103f0f7fcf5e3e9f9fcfbfafdecf8fffb08fafafd02fff0ec03c5e6fffcf709eaf5fbfb01f6f5e3ffe8fafff2fffbf9f2f10100fdfdf6effb0406fbfa02fef8f1f9effae2f801fbedf9eff6f702fb01ffd606daf1fff6ecfe06f4f3f0fc03ea08f4f0f708f8fcedf9f4df14f8dcd1d30fd3e503dffaf6e8f9dbf0f6ec06feefecfbea14edf4d4d708fcfd0400edf9fa01fcfcfb0ceeffd8e8f9c3dc08f0010beb12e1f80de9e5fff2e8f906cbfc00d701d806f9f2f6f7d9ee01f1fdf7f6fffbe8e7ac11cadaf7fef601ebfefd0601f503d7ffd6e5f5e7cf03eb08fee802f8faf901f5f7f603f601010afdf7fddfede809e204fefc04fdf0fef1fc0700fc03faf6fdfdf70603dae802fcf805fce906fd000401fd0407ffef0afdcdf1050805f6fc040af9fffef0def9f70406f1ff070405fa0603f405eae2fa05ffff00f9fd02f404e5fff8f7f6fcf702f200fafaf2fbfcf0fad7080105df0404f7fdef02f2f9f3fefffdfe0003fffff4f0fa00ebf1f9fdfbfa01f10201fbfff200fa0103fff9f9f6fcfcf6fffefa0600020002fff4f1fd0302f004f8f9f500fcfaf9fdfa0105f203f901fefafc06f600fdffecfef4f1f7f5fe01f6fefdfbfd020802f804fbfefbf3fbfdf001fd04effaf500f6fffdfbfdfe02fa01faf200f7fbf7f910fefdf7f9fa0af4f901f804060204ec030af1f701ff04f7fffffd0402f5f6fc05fefdfaf3fbe904ed060a00fd04030001ff01f1fc03fd0600fdfcfefdf41cefff02fefcf9f0f80004ef0df9fd02fafbf505faf5f6f7fe04f0fde4fc0702fefb0af9fafcf20bedecf6fff9fc04fafafefb05f5fff910fb0f02fffe11f2f30600020102effdfaec010604fcfafdfefbf705edeeedfef002fdf3010105f1fc01ff01010205000502fd07f8dbed050dfefff9040ef5030704f808fcfded0900e7f203f900ff01041208020707eafd02ff00f6fd05f8030ffdfbfa06fcfdfefaf7f702030801fafef301fb080cfffffbf700f007fdfcffe601e912f800eafcee06ff08f9020b05f70100fc04f7f4f701faf6fc0eecf402f208fb00ff0300fc06fffaf7fe03f5f2f4ee060500ee0200fff607fb020800030afd090106f9e90dfb00ff00fefaf9150000fafef8fee4eef903fffd06fc0111080403fdfff1fe00fffa00000004fcfffdf8f40204fffbee04f1f101fefdf9fc00fbf501fd17020bfef7000101fafefcfc07fefefffbfefffa02f0fffe0300fffefdfffcfe01fbfffb010106010100fafef8fff80104feff01010100ff00020101fefefc00fb000303060701fe02ff0102fbfe01fc00feff01fdfd01fffcf504fdfffdf401fcf9fffe000003feff000105fb01fa00fdff04fcfdfe01fffcfe05010002fcfe0002fefefafef8fefbf8ff0205fc0302fefc04fe00f500f8f8f9fc00f901f9fffdf8fff80000fcfd0301f9f8f3f9fc0203fe02fd02fd00fefef9ff00fffa01fdfbfbfff5fefdff00fd03f9fcfe0001f50202fc06fd02fa0201f8fdf4fdfcf802fdf5fc0002fbfa01f903f2fcf7fcf0fc0103f801fbfd01feff00fffefef4fefdfa01fedcf5f8d0f6eae608f3f70df9f7f9faff06e8fdfec2cfc3ffc201f4e80202e705f3f2f9f7f70606f9f5f9fdf8f5b8d504f6f306f8e3f9f5020b09fcef03f7e002f6abd6fb02fff9e40804f108e3f4cdf8e90200e4fc01f1efeafdf20602eec5f10bfcf8f7070004e902c9fed5ecf9f3e500f602fdfaf2fefdd2f5a5f6f904ac0bfcf5f5f90605f3faf5fbf2f604f1fe07f007f1fc1b0c0402f7ee02e607f9d90301fa02110dfd04fef4fb07dfff0a0801ff16fefaf6f5f006f405f7fbfee004fdfc360e0800f702f9fef4f105e90800f20a01fc0f0700dcfef700fa0000e50308fd0f08fe09fdf4fb0003fdeeebf802100803fe1005fef6fa16fef0e9f6f5fff7e80608dc01f6fb0ef5f7fffdf9fc04020efaebffe2d6ccffe00bfce1ff01f5f9f70b0905fefdfc0401f1f7fbf7c0d3fd07fbfef9f6fefb03fd01fcfff507f20106bbe8fa0502fae80203ff00fbf1cc07f80903e9fef5f30b02060104f8ffcff604f6fd01120800f203d5f9f2e801f3f410eb0103ffe805f80003c7f80405b6fcecfe00fcfa15e8f7f905fafb07f80303ebfcfa0602e0fb08f3f206fc0a02fa06e6f10510030404f7f9df00f203f4f404fe11fb04ebf8f603f802ee01fc00e307ee1302040500fee6f20ff2f9e00308ff04f7fef00209f9f8f80604e4f9ede410fafdf8f8f8edfff0ecdbeaf814fafafef9fafbf302e2fc0517fcf5f0f9f8fcf4fcef020907f9fbf60314fd04f700f405faf2f701fa02f9fcf9f302f7f702000a06edfcf0fe01faf0fb070bf9ffe9fdfd03f70500f405edfbf4fdf7fcfe0be101050bdf01fd01fbfcfce40a070d02f300fdf4fd00fafef0fffaff04ea03f10b0006fcf6f200f9fe01050dfff8f9fcfd0afbf4fefd03fb01fdfbfcfeee010317f7fdfe060403f70201fdf305040502f9f90ef5faf5f7f3ed01fff604f20101f801e700fbfefb04fd06fcfcfd0bff030afd04f902fcf900f8fe08020cf806fb01f8ffe1f7020202fe0af4fd07020bf508fe05f4fff5fefb0bfd000402fb03f8fc010303fa0300ff05fbfb0504fffe0600f300080402fffffff9ea0209fbfdfafe04ed00f3f6fcf404f9f1ee06fbff09f1fbf0fcfcf6fcfcfc02e5ebfe0d0b02f200f0f5f6fdfe01f8ec07fbf3f901e900fd040ff9feec02fe0501fe05faf3fcebfe04f8fe00f7050513fdfcfb0ef5fcfcf613f9060305f3e40ff80501f804f2ff1f05fb07ff05fbfd05fbe40404ecf4fb0afdfafd0005e9fd07f6f8f60909fcef02edf402f4fc0313040301ff0106ff03ff14fbf00802e8f500f412fe0b00fff602ee0602f900fc0006fd05090f03f9fb0103fc02fe0001faff02fe060101f2ebfc03f5f1fefcfcfa2a040003fe000cec00f0030b0e06fe09010801f90efbf7030802fb0001fa07ff0307ee0a0dee00fdfa05f50cfefd0701ff09fe001103fc0206e7fff9e502fcf101fbf2fc0605fbf30002f6f501e7fbe907d003faf2ff0005effefc03edfcfe01f4fafbfdfb05cae7fbfff3fef7f6fb02040805fbfbf606ecfe14cbf004fa02f800fe050200f9fdd4f9f6fd03f50604fc0509fe00f3f8f6daf6f9f905ff000500ff04e9fbf1edfdf5fffb00fffbf8e70002f6ffedfdf801db0ae4fa01fd02fbeb0afdf0f7fefbf9f20508fafd0101e8dffce5e8fdf60702fc05f8fdf9f50403fdf602eefb0ffdd2e70a03080103e505eefafbfa0608fbffeaf9f1dfe203070a0503fff2f20302fee3fef10901faf4fdeff7010403fcfff8dd0100f9f9f402ff0400f6ccfefcf7fd05f6fef5f7fd06fef903df01e502fcfeedfbf40ef90805fc0ffdfffbf3fd05fdfcff0dfaff0308f6ee01eb15fc0002fff8fafb02020203fefc0901fb000702e9f3fc04fdfe02f408fe00fdfdff02ff00f80c01f0f3fe0800f5fe0200020516fde9fffffdfff001fe040508fef8ff01f3eefefa01fe08ff06050500e2fb0bf9fb00f601effc05ffe4fc02fd00f3110202e3fcfaee00e0010302f3ff0203f604fc07f7fffdfbf9cbe2d805e4f0fedffd00fb01f1f802f6fd05f903faf30009fbede701fbf0f907e808f6030204f5fa0bfde800f8cefd02fefe07f604f30604f2eedaf7fdeb01ecf503f2f3f105fd01fdf9e50201fefcf70202fee9fbf70af3f208fadf02eef9f5f900fbf3f3fee4f8faf9de0a1013f8eefdebf8f000fc0fff0003f802fb00f5080801ff01fdef020403000c050afbf9100600fdfffef10600f400f5010305fdfcfafef8fc08ff0505fffb05fdfafc1cfd030506f306ff0402eef900f310f8feecfffed8fafe00030fff0002fa0002f90bfbf700f0fffa07ee00ff07fbf8f8fcfafcf80006f3040803ffff09fbfdf3fef005f8f7f704fefffe02ff02f9f8f902fbe9e4f203e8f4fee5ff01f704e1f7fa04fefbfff7f7edfee903fb0206fdf5f905f6f9060404fdfcfcfefde406fce5fdff030303f004f2fffff401edf6f4f6fcee0102f6f9f103fa00fef3ea0003f803f402f9fff3f3e5feeefefbf8ebfaf4f9fafefcf2020003d6f1fbf8faf3fbfaffef01f1f0fd00e7fd03f9fdfef4f3f605f4ddee0203e4e20dedfe030afdf105fb01fbffec0203effaf9efebfcfa00ee0803eb0ff0030702f502fefef4f4f5b8fc02f00404fe02f70e02fded0404f2faf7e800f3f7faf7fafcfbfbfbedf50107fcf101fc06f5e90305daf4fb03f8efff010500f5f704da04eff1fffed1050ef0fef403f7f7fe02ea040504eff2f5f6f2f6f8d4d0e9fee6f90df3fc0507fdfa03ff0401fceff301e5fcfaf6f9f200f8f007fdf604f8030a06fc0704f7f6faffcde102f5f901f303080affefea0bfeef0205f2f8f0f60705fefaf4ff01e9ed010802f9f8f905fbf8f700cd05f5feeffffdf5eb00ef0203e204efef03f8f1f3fa0dfaf9ff0012fef9fdf10001fdfbf60701fbfc0504f6fdf40b02fc02fa01ff03fafe06fd010309faf700f804edee01070404fdfb0b08060301fc0405fef6f6fce2fcfc06fcfb0ff4f0fd020c02e700f503fefc02000906fe01fd01fdf0f0fa050005020307fe030ae9fd020402fef6f9f5fafe03f704fdf302eb0c0305eb00fbf903ed00e5ebf70404effd0004fbfdf3f0fbfdebf0f300f4f4f9efff04fe00e9faf804ff01fcf2f4f5feedf2faed00fc00fe04fc00f4fd0301f507fffff2fe01fefdff0201fff2fbfdfcf9e403fbf5fdf708f603f9edf4f1fc08f502fbedf4fc0a00f7fef7fceefef902fc030204f5fcf6f7fafff4fbfdf6fbf003fafcf8feeef8f6ec00f816fffb07000606f5f7041811eafaf50a18f8ff0802fd09f7f907fef40e16f40400f0fe160c0c0afae4fe05f8fffcf4fbf1fdf9011502f9f7f9fb1bf612040402ff0ff9f603fa000ae301fff40b06f90509f710ff0502f7e90504fd040108fb03f7df1609f8f404f8fe06fe08f7fb0002000612fcfc0c00000a00eafbfcff030e13f704050204fbf801fbf108f0faf3faed01d9f4fc020303fdfdfc06fdfe080203060cfbff0b07dfeb01fa050505f002f7fd07040403fa01f2fcf2f4ef0207fdfb13fafd03fffc02f0fafe0102f204f8f9fa02fafaf503e5ecfc02fa10fefafbf8f904e5fbf0f8fff70201f6fc0101ff02fe00fcf3000206fbfdf702fd0ffcf601f9fffff1ff04fdf800fc03fc0008fdfc00f40701f504fd010204f502f9fe0301f8fffafd03fff0f40303fefa03f9000003fbfd04faff00effe04f5effd05fbfc110107fa0103fbecfff9f801fffc00f7020403020000f7e4fbfdf50601fffa01fd00fdf9fbf101fefd01fbf5fc04fa02fff602f6f90003f7fef414031302f6070205f5fa08fdf7f80030f0ee0df7f8f501f30f01fb030dfd00130203f30600fb0b041af805f5d906fdfc0102fafffe05fc08faf7fdfc08f0faf3eeec01fffcf506ff0e0afc1b09eaffff07fdf8fa0201f51506f9020df3fe05000204fc0306fcfd0fe5fc180208fcf501fdf4fbfdf903ffe404fb1003f5f303fbf601ed05e9f6fa01f5f80000fb020beaf0ec04ebebf0fefb0100e8f5fd0b08f3f201000703fefdf4e8fdfef702f4fe0206ff00fff7ecfd04feed0405f3eafff4f7f600f9ff00eef9f8fffae61008f2fbfaf7ee08f5f6f7fc0204fafcf3f0fcfe07f8fff9f9fbe9f4e8faeeed000bef00f2f301fefffbfefafef7fffffe09fefd00fc0500001f020105fefdfdfe05040901120208fb0201f60ffd050cf805ff01f603fe05fe040c06fd030205f2edfff9fefffd02060605fffc0c0909ffed01ffecf8ff0203fc06fb000504faf8f9fef501ff020a05080209fd01f103f4030600fb0703fc08fefc03f9f7fcfdfe01f001f60103fbfa000107fe050dff0cf608f6f801ef05fa0704fe01fcfe04fc00030aff0103eee9f705d60bfbf20001f8fbe600fc0304fe05fbfefffcf608d7eefc07f1f503f806f5fbfc020904f5fbf30d0bdcf105ffff020602f40102fff1d8f7f6f6fef000fbfe0a1503f9f8fcf2e10ffcf90303010cfe0306dff406f00bfceffbe40102f4edfbfb0901dd09f9f8d8ff000c0817fdfaf11108fafd05fe040005fa0201fbfefffe03f9fefcfe01fef4f8fefb0aff01fc0207fcf9000d00e3f000010c020400050304fbff03040908ea0403eafe030002070cff080a03f406f9070112fcfdfb05fa0305fefe0100f6e506fd0afc080804030dfffd00f8f601fff8fc01010303f30602effcf805fc04fa06f1f5f8feffedf10ef800f106fdf0fefaf3fbf5fed3feecfbcf04f1f70604eaf9f3f506f90300f8f706f2f0fdf6d9e9f7f3f900f4fe00f4fefb070300f9fde6f5fdcee8ff00faf7f900fc06fdf0fdddf8ec0df9fdf3feffeff3fff8fffde9d4f5fffc02f8ff01ffeafef4fefdf5f0fefb00f801f901f6f6f7e8f4cdf101f8df04e611f31afcf80cfc06fb040107f8fc020ee2fc07f7dffdffc20604edf1f6e4f804151bfa0403fe0bf304061103ee0f00080afef9e503f7fcf5060bf8fdf6e7f6f0f00c04f70507dbf910f70af912dbf21102fee104f51102fbfcf2ff001adaf7fdfafffe03fb0017f7f3fef7fcfffde703f7f8fdfdf5fafbe5fee704fafff7fb341e051cfcfcef0903fd03fdfefef5fffe1a1b0508c3fdfbf40a09ec01ff09011701fbfd0706021c0a09e4f000040f03faf3fbfb0505eeff0203e70202f30b01f4eed9ff0001ffe0020c0407fa0f0e02fb06fbf703060efafbfffe01fcfffa0301fd06e8fdf5050cf9f2f6fbff10f9fbfafce7f70904fcfbdefdf200fbfafd0316e7fdf205e7f2f601f9fffc01fffefaf3eef304f9e2ebfa0def00f8f901feff0703fdf9f6fbf9fef4f1f7f7f002fafdf9f80302fcfdf3ff0602fd04f7fae7f9fcffeefefffe05f7f902fdf6fdf70dfaf7fa00e3fdf7fcfff102f7eefef3fbf7fd02fbf1f9ff01fff8f9f8f60004fbf1f9eaedf5fff5fffbf6f909fefcfcfffdebf405d2fefdf70305ed01fe000b01fff1feefffe6e7c1f8d4f3ffec0600f701f603f8fefbf806f700f4fbfbfae4e006fbe8fc00d9f8f7080cfa06f800ffeafcefb0e2060508fcef01e6fd0ff703d4f2f4ef05eff714e7f3ec02feff03fad6fc0502020009fa00e5fec10aecfa03fbfefbebfcfe04faf3f6d708c6fef3f7dfff080e010bee02ea05fe0003000008f503fdfcf60df3f7f5fcee07fff20509fff80612faf90405f909000702fefbe50802081101fc04060703fefbfeff04f9fb02f4e1f8060600090105120afaf00ef801fe0402f0f9040404fa0201050507ea05f801fe010002ff04fee50304f609040404f004fdfffefff8fe01e205fe0ff7fe0cf8fe05fefc0001fdfa03fef9fa0904f4fe0407e9dfe8ffd50500f30802fffaf708f4070efd070c100afbf708cdf204faff0102faf2ff0502fd040009fdf10df5ceed05000210f6fa07f8fd0016dff9f4faf9e3090500f0120603f205f2f60003f5000404f607e1fbd8f5e7f8fff4fb09f8fa0c06ebfdf9df00c802ec00edf7ff04f90705f8f50bfbec01fffefc04f80ded11f7c6e0dcffc218f7e905f808ffe5fafcebfcf9fb05010f0307ffbcdefc0213ff06fbfaf80302f912f5fb05effcf0d5da050bfefce8f815edfbfdfce7fbf20906e4ff04eb0a33fef9f0f5ecc30004f804f1fe0a04eaf8d1f5e9dc0bfbfc0503080605f2f404c9fab90e00f3c104f7f60003fc02fafef700f702fdfd0303effdfcf800f6ee04dffbf9fb0103f50201f6010f0201fcf20106fafefdddf605010a0504f100ff0702050cfd08f8f3000800f405fcfbfe02fbf9f402fff4fefafbff000405fceefefa0304f2feeef01402f502fe000003ff03d700f6e7f4f80100f4fe09fef6fc00f2feedfe0108ddfef6f9f40a080501ecf105fff003f41000f610fdfbf8f40505f4fcfceb09f902fff8fbfc00fcfbf905ffe407e908fef60a041500fff704f3000b07fafdfffbfbfdf2200dfe00fefbe6fdf4f0fc020cfdf6f3f5fff805fed8ffe206fdf905fbf90cfa02030cfbff05de0a18f3f1f0fff91301fef50ff9f507fa24fcf102f2f601fcf20afcfbfffd1e04f802fcff03fffefb09fafa00fafc0803f313fa0002ff09fffdfefb01fcff04fd0405fdf902f6f30002f7000300030303020001ff00fdf80500f9f9020300ff09fe03fc0202fce9fffe03fe03fe000f07130100f802ee0404fefe0401f902fe0001f6050301fb0002fdf9fdfefdf6fffd0400fe10fd03fa04ecfc05c808f2f2f509eb0e0403f8f801f9f9f703c9d3d4f9ccec01e5f803f709e8fcf6fffefbf70001f3f7f9eadde1fafff40700e8fcf20609fe010b0202ddf2f5a3dc08fcfd0aebfcff01f6fbfbd9fdf2f807e006f7ddfcdbfefffafef2de02fa0703f40203f9ebfbd2ffeceb030fe902f1f8f8fff7f9fccd07cef90002d105f202fbff0bf1f3f704fbf100030d08fced0cd6f6fe031906fffcf6fa02fdf90704eb050a0ffefdf2fbd90ffbfff1f301fe040409f203fa0302fe150df9fdffff020e0904feff02f20ef4f607f913f7f607fcfafdfff3e3fefbff04fb00e9200401ff050afdfdf4e603fbfbd902fc0213fb0ef9030604050700fce6f100f90dfa0feffcf801f4efeaf8ef01fbfa06f5f7eafde8f7e5dee901f3e304e6fcfff600ebf1f511f701f505f2e6feecf7fa0004fff90105e2fceefd0406f108fbf9defef5dffb05fd0502edfe0706fbe4fb0cf8f4f0fbde02f7e6fbe3fffaee01faefef020104f002fafff0e1f205e1ef04feeefcfafcfb0108fcfcf1fdfbf8f9f6f6fcf906fbfe00091d06f9f4eefefdfefd06130c0efcfed6fcfeec1af700f904f5f7f0010aff00010004001df5fd06e8f1fd03f4fcfbf803fb020afefe000705fd0c11d8eb04fc03fe12ff01fe0002f9e5f5ed08fd0807fb0e080a02010900eb0101fdf90501020b0400fde6fa0d0307f9e9fdf1f3fefb0203fb1ff80415fe0af6fdfa0201f30309fbfdfb06f7fa02010405fafaeefefceaedfdfcfdfef5ff04000400f6fd01fafdfefcf9eafefd0307f6ff0003fe03f5fff2ff04fd06fcfdfe02070403f903f900faf00202f9fceffffbfaf8fb02f0ff00f5fefafc03ee00f8f9fffc020203fe00fdfaf8eff7f6f3fc00f9fff2fbfdfb01f7fbfcfe0101fbf8f8fdf5f2fcfefdf1040300f2fffcfe0107fcf4fcecfcf4fefefef807fc06f904f6fbf902f903fffc03f503ee00f2010005020403fc02f2fbfa030603fcfdfefbfdf9fafe01fcfffff50002fffe01fafffcfa040002f8fefff409ff03fef200f500010004fb01fe03fefe03f5f8f304fefc0704fa03f8fff5010701ffedf90300effaff04f9f9ff0104fff6fe0efd04fdff03f50aee02040510fffdfcf9ff01fff70107f9fe110402fffbf5ee07fc01fafb0402ff0104fafcfdfeff0204fb01fbfef9f5030d030302fffc05010103ee09f8fa07feffec03fcf2fff700020b00f90df900010109fbfbfbf306fa00fb0204fefefc0106fbff04000afefffa01fc0103f7ef040500f502fa0dfcf700fbfb0504050207fa050105f9fcf70dfdfc09fbf8f2050d0701fc0403f8f6f9fd02ffe9f4fe00f0fcff0804f700fe0000fbfe04f2040ae2fd0003fdfafb050dfbff0be7e80dff0a03fc02fd0f06fa04fa0206fdf50302f9f602070701f7fdf1fb09f6faf7f0fffd060bff01000014fcf6f8fdfeee08f3f6ffe308f1f6f902e602f9fdfaf801f9f70200d8e3d302d0f60cdcf805fb01f4f4fefcfb0405f6ffed02f8efe2f30105040207daecf3fc0007fc00f8fae0f9f1cae307fe0206f0fbeefa05f207d8f0e70405de0000e5f8f0f9000001f7d4fa080d00f203f4feecf2cdf7eef00800f1fffafaf3ffffed02edffc4f3faf3e104e4fbf90a02020afafdfdfc0703f4000c0bf404fcfaf30001f50bf9f90605faf70704fafe0205f8fdfffefaf710dde9ff04110afef201fcfcff0301fa0200f4ff09d8f2ff0406f805ff04f40300ecd30af4fffc0e02fbfd20f907f601fbf7e704fa02080a0002fef905d2fbf1ddf5fcf0fcf7010502ee01fb0b0204050006defbed0d0804fcfa0ffbf101f801fcf9f6fe18effff6fdf713fcd817f7fbfffefef9f2fa06fb06fd04f406fd01f907dae3fe06ecf4fbfdfdfe0107fcfa050801ed1002dffc010604fe0401ff0606fde7dbfbfc04ff040ffe020f160800fb04ecf30bfbfcfe0406fefdfb06ecf9f9f1fefdf2fde8f901fae7fff912fce0fef60ce0fff41103e90bf40a03fe0e0df905f8f6f8e61aec07f118110510e3fbe900fb01042cf00508fffe08f4f6100707011df4fef90502030e05f700f6fdfcfeff0019fae6fc23fcfe03fdfbf009fb060619f3fe1002fbfe04fcfb0404fe000700ebf5f006f80212fbfd00e80cfffee30d00ff1f0117ff01fff90704f7fcf2e807031104e6e9fef20eef1ceb01050103fff90d09ecf1e4f019f524fa08ef00f404f9160dfcf8ff1802ff03ed06cc10f605ff0a06060e06fbe1fef807f303fafc08feea0afb1814fe0807f615f900f4fbf6110f070809f725070609fef00304f406d51619fe050804f1fff6061501f7ee19e9051dfcfd031005ed00ee2d0715f0ff0519f7ed0408dce70bef0d07fe0e040206f2f6e500fb01cdcde5facaef09e60004feff1a050605f8fbf70ef5f70406fde7de060afdf800e905e905fa010e04ff02edebffaee507fd0005fbec07fdfbf2f7df08ec11f4d805f8f500f10304fbfe01d3f4fd11fdf50000fbe5f6e2fef7fc0008f9fdf5fbf303f3f8f4c401d4f3fbffc6f0f50100fd00fcf0fc04fa0cfaff01f50904fdebfc08f7f904f3fe0205020306f9f9f303000305effa10fff805ffdcfffffffa03fcfafb00ffff0309f309fef306fce6f403010af9fd06f6f70701f2fc02031109fb0b02f002f403ffff02fff1fc0406fbfd0906fc0cfb010305f4fdfefb02fa0103fcf4fbf9e402f9f404ffee0bddf8fe09f7f8ff08f908f4fd0003fefdf5fbee0404f3e902f3ebf8fffe00f400f1fafefdfb05f8fdfdf40200fddce503fc00fb01eefbf204070508000706edfafdf6f4fd05010407fdf9fafc07f6df0500fa04fdfaf8f9fbf903fcf30aece9f2fffb03080502fd03fedffd0af2fffaf702fc05fdfcf1fa02ecfef0f3f8f9f1fa1605fe0202fa0d01ff0af4fcfff7fd0111fafdfee8ff1505f60a01e1fbfffb0a03f1fffcfe0000ebfe0d0d14fee9fdfe00fffbfe030307fe000308f1fffdf6f4000005040202fb08f3010200f50ffb08f306fe0ff9f706f80ffefdf803f2fd0801f9fd05ff01030006010bfcf3fd0215fbed00fe05fefd0209fe08f7fdfc010bdc0dfbfb08fe1700f8f700f705fefa0505fe06fa00fff303e80aeef50cfbf9fe0afffcfe0a0602ec03fcf40300d5fa0702fefd01f00700050403fbff0607fcf612defbfdfbfc02fafb08f90cfdf9cf01f8f90b0dfefd0415fc01fe0003f6e70101fa1001fb0106f7fbdcf6fbfbfcf8f8fced05faf6ef08fdfff90507fdffdf07fcf0fb06ff00fffe0002030304fd0302f5fdf6fd0bfcfa0104f9010203fbfd06080000fd030305f200010cf608fb03fe00fd0001fcf8fefe0000fdfdfcfffd02010bf501fbfe070bfcfcf703020707fef003fc0efffcef04ecfcfef6f8f802ffff00fdff02fb000400fafbfbff0202050002080100fcfc0405050001000307fd0d0c00fbf604f51d0afe0dfafe05fe01eef90202d9e1f308dcf602fbfafff5fd08000602f70405f7020603f3faf5f8fefd00fef7ed02f10107fefd0efe03e9f306bcf2fef10517f5fc0c070901faf405f012f3ef0100f7fe12fe0c090704ecf8fd0209fc05fb03eeedf40006eefe01ec0100fcf4fcf3fefacb0ae2ffff07eafb0cf8faf2fcfef8f6fdf40103fe02fefefbfc03f9eef0f8fefef40600fffbf8feeef8feff0103fdfcfcedfff7f4fcff02fff40701f9fafd030301f7fefcf9f7fafcf5f8020202faeefcfdfffdf4f907fa01fefffa00f8f6fef1fe02f7fcfbfffc0303fbf1f8fdfef3f7fc02f00207fef3f9fafb00ff02fbfff302f4fbfffd01fffb01fdec0308e7f5fff20000fb0bf8feeaec0bffd6ead408d4ee08def9ffe9fbf7f9f50afd0307f80df4faf502f3f80002fe0205dff8f2fefd010906fff8db02e2d1df04fc0000ebfff00705f0e4f7fdee0700d90202edf6f302ffeefe05e60bff0804f910f403eeead605f8ec06f8eefffdf6fa050002f9d106e4f70004d7f808fc0218fcedf7fbfcfafefe02fcf3fc18ebfd02d6efe102e517ffedf806fcfcfbfefff7fcfefefd04eeeff400df01fc09fc06020efcfc060602fafcfd09f6f5f7f4e30102fb07f6051403050708fafbfefe01fcfef917fa0104f908fde6f6fbfbf5f908fc01f8f6fcf100f2f50303f102fc07fd0401fff80703e50200fdf501f4fcfafcfd03fdfcff030503fb0000ffef0ff10303090903f6f4ff09fe0007030dfffc05fc0202f9ebfe0d0bfef2fdfdfb07fbff08fdfb00f8030b00ff0601f7fc02140204fb020afbfb00fef60bf8fb08f6071107f7f606ebfefc02fdfe02fafcfa0204fefd02fc09eefcfffb0000f701060901fcfef9fc0301fafdfb0802faf002fbeffcf601f1050303fdfcff01fb02f00cfb11f70f09e809ff0105fa09fa07fa03faff0102f9fcf1f4f8fcdce90000f60403f3ff100207fa12fd0600e91306de010605fdfc0900eefdfc09ffdc00f6050100fafc02000e0105fa06fbf10600020f060202ff0b0be9fc16fa0400f606f5fbf4fd08ff06ff02fd0cfdf8e4fd2e2102f7fd0cfa0df9fd1a0707fafdf704fddc0304dfe404fcff0bed06fcf6021d0508f6f6fc0d1e0702f2faf107100a01190600d7fcf802f70606f80afe0fe408e7fa05fcff0200fe0b06000c0cfe0eeb10fbfa040df004fbfffe060303b9ef050401fa0c0bff03f7f303fffcfc00fdfceffefc0601fbeed0fed4fdfb0700080b0c0311f9f12bf8fd03fdfcfdfefd011d020100fbf5f7ffe8210000050004faf80209030400fd06ff1304f600ea060307f4f80114f605fffefc03fb05f3f90604e8f301fffdfa14f500fc050cf8f5f8f704fb01080427fb2203fcfefff5eefdfdf4060101fefcf9f3f3f50e0afafefc08f1fcfffcf4fe0909fd0319fc0ff6fc062df80d02fff5fafafdfc070002f70328ee0e09e0f5eafff10701fdebfaf4ffecf702fd00fb010d0d13faf308ef07060207fdfc1afff4fef9faf0000402ec02f1e50804090906edfc11030c2411fbfffbf9fdd9f50b00fe1afcfd01000af60101fbfefa000400ed0c02fa0efb05f9f6fe0e03f4fc07031fe4f6f310fef1fffffafffef50105110bf7f8020200fb02ff09fb03f801fdfcfd060efc11050405fbf702f6fb0002fa030604fefc05fbf6fdfe00ff00f8ff0501050108fefefcfe040bededfe0100fa04fe11010106f1f3fdf904fd0601fafe0cfd02fdff02f00dfafff9f9020703fff900ed06f8f00100f302feff05feff01fe0e0007030006fa06f70400f703e8fffbf80cfcfafef80304e406df08f9ff08fbfaf9fae900fdf408f3ffff07f7fc00fefaebf1f5f501e70704fdfcfc00fd0b030101f6f4f5fefa0df0051bff020303f00209fefde80bf401110201f701fae6fef4fd030701e307f8ff0205fefdfdfce8f005fde4ff0505fefa05fc06fefe00f611fee20af5fb08fbf3f7f3e8fdf9f4ea0aff0b01fbfbfef6f8faf903d3c8da09d6ed0be5f6fbff0c03fbfeff0606f9effafcf9f2eee1d806fc00f800ede6fbfdf7050813fbf8dbefddc6e5fbf6fc0cf1eff5f9faf300cff3f1fefbe40bf6f1fdf306fb03f9fdd505ff10fbf401fe01ebf7cffce8fd0603f905e7fcf6f8f20000ef02bcf2f8efd807f9f80201ff01fafafc06f80200fe0504f1fcf004fff3fd0006fb02f3fffb07fdf1f8fafefd0201f7faedfef90103050103080204fbfbf9fe0203fd00fb00f1fef602ff00fd04fefafaf8f9fcfdfef6f800f8f7f304f7f401fa0007f0fef6edfe0106f904fffefff9020bf8f9fbfeff0f01ee0cf905f6fa030301f5ff00fa00f8ff04fe0df802240302f7f6fb03fc030111fa0dff02effefdef12fc11fdfe0dfa0b000a020203f80aff1b0d020afaf701ff010600f005fe030702ffff07f4000309f7eb040600fc0903fafffe0803ee01e9fc0d0205010b101203fdfb06f805f7fefa04fe07030508fed904ef00fc04f1fff60a0efff50108fef8f81efa0ff007dff5f4effc01f40e0bfcf5f9f8f4fe1300f202faf2e9eb05e70a0a0e08110300fc0900ff0901fc06f9fa010808e4d702fe0afc0a0c0914fcfff80006f9ff0111eadafc06fb0c0df00a04ff03faf8f508f50bfefcfd0adb05f5faf704fd11d402f70602f90600f901f6f2010cfd1300f9f6000304f2fafafefbf5ed09f7ffe60bf7fcf70e03e6fef6ff11f7fa0a02050e00fcde04fa0427fa01f9fcf7fe010b0cf5eef5070503fcfdfffe03150401df01fafe04040bfef404ffff10fdfa03eb03061014020008f90a060d02f1ef13f20120fa060307f2ec02f5fb01fb04e80e03fd0cf909fefbf9e1020301f616ed0a18f4fc0007080102000efc04f906ef1af8fd0100f5fcfb10020306f102fffdff0217000efb00eaf202eb10030502fcfef904fe030b03fbfeff00f7ff1005ecf001050306fbf8000503ff03090805fdee04fdf3ecff00fffcfa03f6f90502fce604fafe04fb01fd040b00fd00f3fbf5f701fef6fc02020606f6fdeaff08fdfff8f700f203fbfbe8ff060700e416f402ee02e20100f2f9f6f400fff20105faf9fb09fd02f409f0e9d60fd20702eff302f9fb000b05f7f901fd01f1f5f610f9cee10efdf40900f207f4fbff020107f707f10912d0f0030b0400f4fcf70308f5eccd06f0fffef3f805fa090405f4fff7feeef4f7fc030c0b1304f008f3ffeee3f9f1f4f901fb0b03eb0606e6f9dff2ff0ad90404f6fee306fafbf704ed040001ff0004ebf5f9fee8e1eb04f2eb03f7f805fb04f0010306fcfefd0400f301fef0fcf202fe0001fdf4f0f3fd01fbfb0900ffedfdfde9f700fb0707f5fbfa07fafbfaf7f7f50004e505f5f2f7e7f8fbf205f2f2ff030704fb04fd02eef0eb02ef0303fff1fdf6f9f5fd04f7fef103edfcfcfeeffbfd05f50601ff2501fef7f3fefffc0201090703fe00f101feee16fe11fffffbf8ff05fa020701fc00f9f1fdfd06edf90308f7fbff06fefcfe000406fc0400f50506eaf0fc08fefd0cfff8ffff00f6e90100ff020b070209000600f8f2faf505040302fdffff04010b02e201fd0101fcfb02f5fe0002e6ff0606fcf815fd0af10104ee01f1fdf2fbfb01ff02fc00fe0001f9f7f20201f3f0fc04f7fefe01fff50502fdfffdfb01fff9f7f5faf1fd04f5010001ff0000fefb03fd03f404ff01fdf9f603fc02fcfefefafa0300fffbfc00fefdfdfdfafdfbf5fefbfcfff8fefff8fcff03ff0002fe00f7fb00fdfd01030404fc0002fefffbfcf7000003fefffcfefff31ffdfb05fc031bfcf30a0101fcf4f914efe301e2d6c203be09fcd2fcfafafff40408fdfffe011a0101fdf8f0d8f00505e906f8fa09ed0300f901f0f707dffaf8c4d801fb080ef2031cfb080c1bdb10f207fde0fb06ed000808fcfff5fecafd080bf5ff0c0c0bd5fddd04f2ef14fef503f7fffdff12fb05ce06cb1603fce9fee2fe08f8f801e8fdf6f8f0f900f307fc0a0501f9f2eed702dc00f5f701fdeff6f9f809fe06fcfded08f8ff0a09d1e6fd09f6fd02eaf5fb03f90511fefdfdf0fd04eceefa0200ef01fced01f900f3f2fdf3ff00e1fafbfbff0ffa01fa03eae705fdfe06fbfffa02fdfdd8f403f7eef5ecfdeffdf001eefff6e6faf2ff0201e406f8fefe08fffffe050005f9fbfdfefafefcf5f7040405ff00ecfffa02fffaf6f8f302fe04fefb05fe01fc000cfde7f706080604fcfe080205fdfdff040300f2ffed00f901ff04000e03fb010902fcf1000609fcf801fdf706f802fef808f9fefbfdf5f9080601fa0201f90001ecfdf6fefff30203fdf8fc00f7fee9fefffff0070200fbfa0201fafb0501fefe05fc00fd00f0e8030b000e0700f0ff12fe00fcfdfa0301f404fc06f5fd0504fdfaf4fb04010bfdfff204fa00fdfe09fbfc08f7fa0304ee010103010c03f7fc02f5f8f402fd05011005ffee02f1fd00fafe050711fefdfffc02fb050c02f6fef100fcfa01ffe605fefdf903f5f0030204fd07fb021ef901fb0707e8ecfaf20000050704fce6f1eefef4ddf0f707ef0ee7f70005fd0bf0f706fefef8f2f10101eef501ee05fff807feecfaf500fd02f3fef8fe0dff10e9ff00fffffbf0fce90100efeb0df3efeef6e4fc01f001ebfdffe301fdf3f0fcf6ef0602f20018fc00fcfcf703fefa01ebf5f4fc02fd08e0fe02f301ffe4f9f6f401fd00eeeffbf901f2fff9fafc06fcf5e800ffedf1fc07f4fefafbfbf806f1f9ec1005fcfbfbf9e8f7f4f2fae0010602fffaf3f9ed0302fdf204fcfbf400fefdf902fafffef3eef900f2e70a07fc02fcf9e800f8f2fefdfbf7f4fddef2fafc07fffb03f700ebf608f7df03030503f806f40000fdfaf9fbfaf80afff8f9fff8fdf8f6f9f6f9fcf6fbf6fd0cfd03fd0e13ec02f20b1f07f90103f901feeafceff2f503fffcfff10404070303f8ed05faf7fafdfb01ffffff02f6f7fa04f8fdfaf101fc020405fbfdf3f300040bfa010cf7ff00fbfd140b0300fedefff41bf7fcf7fc0ef8f902dd0410fcea0001f81cfcfff706ff10f5020cfc010e06f804fee9fcfdfd00fcef1804f60400fd02fefd1006f304f7f4e4fdf8fcf8fb03fcf80101fbff03fe06fc010b0cfaf6fde5fc0003f905feebf6f4fafb02fefc0504eef4f7d9f7ff020405fbfc070a0100f8e7feed0efdfaf306f9f4f205fe05fcf4d4faff0703f2010502fcfcf106fdf1fffcf5f3fbfa01fdf3f8faedfce2000501e7030008eef8f4fe20fa00fdfb06fbf3000315081503f8e1f101f02bf7e8f312fbfbeff601ec05fefeee0d12040e0801f406fcf5edf40af4f8ff01010efef9faf31305ecf7fe08fd0dfaf6050205f502fbfe07fcfb0904fefe041d02f7f8fa04e3fb04f60b02fdff02f501fc1403ed01ff0a03fefbfc000005fe2cf9f808fb14e9fbe3f904fa00fbfb03f9f8f8fcfefcf9f80cf7f6ffeff8f8fbf3fbf8010001f7fdf2fffcfc030602fa0102fb0909d4e80000f501fff7fe020308fbf805fefcf8fe06e9ea05fd06fc0e03fdfe0a04f5defbff09fa0008000203fcfd030506efed0ffbf8f6000000fd0407e8f9fef4fd01f205fbfffffafafff9f603e80303fde70909f200dff902f2f801e50900f6fcfffff4e900fddad8dbfce5db08e5fd030309e2030210f9fbf60403f204eb01e9eefffcec0703e8f6f1030bfbf2090903ecf501c7e2fcfa0803e2f9f30206eff7fafaf1f6f7dffef4ecfaea01fefb06f8f0fc060904ee00f2fef5e6d105ddee0006ec01effff9070202fce006efeefff5e202fef5080202f1100e04040afa05f70100290cf2f8f00d1c05f500f4fa0608f6f105f300fe0701fcf417fcfa0cfeffed03fdf10001fb11ffff05040afaf80c0f0006ec0f00fd03fdf0f914eef105faff020702f3fdf6f7fd1716fefdf7fcfe1bf3fa03f6fb050801ee12100afc0907f609fbffeef90103000517f21b09f9fb0bfaf90007e404f3e80d02f00306fa00f3f7fbf804fde5f90bfaf8eafc10fbfdff00f3f20304fe0605f1f8ff03f4f7eaf5f7ffec0406f309f1fffb060600f9ff01f9f6daf802fc00f8f80102fb060a0003f9fafc05e80108f4f5fafdfb05fefd01f40201fff7f40602f4fdf300f9ff0400ebfdfffbf803fefaffe905f1ff03fef4f8261700fa030dfcf203f203f7060300f7e303f3faf1e0fdfcf3e8feecfc01fd08f4f0faff07fe01fe0efeece7eefbecfa0509fefafe00e8f90001e908fdfaff00e9f0ff05f40202eefcfb0200e50801faf9fc01e605faf5fbfff9011b01f0f9fd0608020500f2faedf4c7f5eeea090eebfaeef4fb03f0f8fee301f601f1fafb03f1ff0105feed0afb00fbfbfd02fdfefd0908ff000002fffef105f90c0402fffdfbfdfcfe04fe0108ff000908ff000401fdfbfcfff9fdf902ff0006fefefbfefbfff30701fd010208040dfafc0803040100fc04fefe0010000f03fd0901fef900fdfd07ff02fd040207fefc0d04fff9ff010103fefd07fffafa02030e04fefffffd09fafbf5feef0dfdff020301ff01061101fa06e30805fbecf80beff9fef700000705f7fefdfb00fbf8ff09fcebf201fee800030701f1030804effcfc07ddf700e7fefbfffffcfe03fb000ff9f9e7000118fded020207fdf403fafc04f7ecfafaf101fe060804f7ff020102f300fcfd090001fb00fdf8f9f7fbebee06fcf401db0801f500f5f7fd0101f5fbfdfefafe02f5f9f6f0f7ec02d800fdf1fafafb02f8f302fb0800fcfefbfafd0609ccde00fa04fff8f1fdfa07f9fffdf205fce3f30ce8f6ff090503f7fefff70001f2da03f6f5fff90c00f4faf40102f9fbefeaffffeffa07070903f8ffe300f7e7f50008ffebfd03fce601fae8f7cbf203f3c8fe0b09fef900021302fb0a02fe0400fb011211fdfefb032402fa0ffd17fc02f9fe06fcf400f80105020504ff04fcfff90200f9010112fb0102fffd0b03fdf6070504f210000205010bfe0506010402fe04060a02fc00fc15050dff0004fbf308fdff02050ff80afaf705fd03fd00fe0206fdf9fe070106031516fdfe000007fafdf30510d7fc03df1108fff612fef7f2f9eaeef50bcac7ca07cee703d8080cff03f9f9010402020607fb00f102f0d3befc03080808f0f6ed05e508fe0a0602e8f702b6f8fef7fa0df103f80002f4fcc2fff102f7e300faeff4fe01fbfb01ffcafef80dfbf9080902edfad501f1d5060ee6feeef8effcf1effaca04aee10001c002fbf800f700fcfbfafcfbf9fcfdfffbfdfaf6ee020301f90201f901fffbfe0001fdfbfff9fefd0200feebf8f000030903fefcfffff502fc0203fefbff030303fcfb03f9030401fdf90200fffefdfcfffe01fcfc010001f304f9fdfbfcfefdf8fdff0001f9fdfbff00fcf6fd06f6fc0109fb0703ff02fe00fef30204fefe050202f2fe02f4030d0109fefafdf806fefefc08ef16fef9fa0400f40ff7fffcf8fafb0b050a0300fcfcf10ffc0a04ffe6f1fb0b0205fffd060bfcfffaf5050efff402f6fbf70000f8f72705fb0706fef8edf8f00805fd03fef600fa04fcf5fff9f602fcf600f4fe0afbecfde4f6fce5fcfe040ae8f900f9fb02001bfaeffc0312e50df70b02fefcefe8fe02fd0304fe01030201000a01eef1d806f8f601fd030204050d06f9ff0101ffe906ff070b00f3fafe060c01fefffff602f2fe11040104fdfd0ee5e60003fe0402f90e05fa01010305e8f906ff03051f0213ff0703ff06daf202fbf90a02fafe0b08e107f1f3050213f9fc06fe000cfe0cf903ec04fcf507fef80dfcf902fff2f40b08fb00fcfbf6fe02fafcfbf7fa00fcfbecfc020203fefc0afcfc1709fffcf104ea05f7fdf9eb04fc13fb04f1f4f800fdfc1508fd03e6f71afbec00f804fefef90dff03e5fbf608fbffffe81607e6f6f0f700f104f1f409fc05fd00fbfc05f3f9e0ffe2f2fdfef30bf600fa09eef203fe06dffbfafdd001f116fdf7fdfd04fe02fd020903f9f2ff07070811fbf4f301de00fcfb09030ff3050a06f50103010502fdf90304dbf9050b000af8fc03fd05fefd05010507f4fe07cdfa060bfe06050cfc050a02fcdb0df90505fdf7fd02130108fd030602e50800fb07120406070307e3fffdecf4f4fb03ef05fe03fb06fef200e90706ffda0ee9e9f9ecfbede7ff0af30b06f8fa0104f1f1ee06dcc8c7f8e0dd09ce0300e706f9fbf604fafaff00f1fa03fc02e2ff00fff30506e4f4fafc09030611f9fdfdfa08bfe501f90607e509f70af8ff15e1fbe7fe0fd405fff6f0dcfd01f3fd05c8fa0101fdef06f507eeebc501d7f1ff0501fee8f7f70507f6f8e703ceeff3fbcaf7070300fffafb09fa0000f901fe04fbfe07fbfa00fefa0001ff0e00fffcfcfbf6ffff0305f90201fc03f9fd0702f1f70002f802fc0301ff0300fefe07fefefc05fff40500fe00ff040001ff06f8fffafd0104000904fd0702040200fd02f3fc01fdfe0003ff02fffefffb0006f8fbfd0705fcfb05f9f902ff080101020007fd09ff03fafc0106f70601f70108ff03010704fcf6fb0ce8f207fe0301fefb0307fcf8ff0bfef802f7fb0404080b0bf4fbff01030100fb05fffd0100fd040702fa0609fbf2fe04fc01fefa070500fe00fc01f6fffef905000008fefcfdf901fef7fafdfb08020207fefd0b0ffffcf901fc0307fafd08fef3fcfbf900fc02fa04fb01ed0505f9fafbf9fff7fcfdfb01fafffd04f7fffe0403f3fae61af5fa05fbfcf9f80d0207fbfa03f205f602f704dee602070bfd05fc0d13fa05fd080003fd0209fad6fefb0703f60405fffb0907edcffcfd0a04f505faf209fefa07f803ede705fb000009040401f8f7fdf6fdecfbf7fb06f7fcfc06fc02faf9fdedf5fe03e40e),
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
    .actor_error_o(error_actor_enc3_pointwise)
  );
  logic error_actor_enc3_extra_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(9216'hf514323019412a600bfbf7f41b0a342a1a35101206070c141d200c17f7fc10091700010302fe09050d1411f7f80d04dc08f4183a2c30e7f50cfcf70cfff7f70af9dbdcf8f4ec1f10ef0c15f1110ffb0ef3e8f507f2f7f7f1230b1c12090efb1213e50afae4d40c02f62af8161cf321e1defe27130c0506e718e9f4fceb1c120912f5fa13ee140bf805f6eae9f11315f915eef60dec09080dff0bf21fd91a00eee60326100b0c19dddfe5c600e60ddbffe90b15200b08fe04f304eefcff3f1e00fc0ffd291df402e52326040415394afff5030f1906fc0606012504363d04444311f9ffeffafc1321fcfff2ecdf303412fa0fefd5e5ee03f9f71efa09fc08fcf31220ef0c09eb04e9eff5ea001afa110510092527000d2bfe12f5faf3f00df404d6d3d3040ef2150c250cfe0c12f6f91c0be6e2f1e6fefbecf6f3271b222ff8d7f2d8d2f50c0903fb091001f0f9df091408f9eefdf8f4f20af000fffd101224240f04ff09e1e906e71d071cdee3eafc11e6291d10201b090bf0ee17fb2f1b1448111ff2ff1c0bfb010ffe221a05f4120ff8f51c09fc4939311d1dfb1207150e151bfbd4ed082514f203fd03f501f1ff050e1af2e60f06e8faf6ef03e4eef20c1c0f071f0914150512f6ed04f003ece702eddef5fb00e419fbf40f0d071cfa06170efbf6fa010a230112f11ff5e3eee20815ee120ef301032117f52a1917180d16f7ef0af7fc0aebfb0af42719fd200b0636131412f9fafd0c09e7091106eefef7fde6050215f5202419192206effdf20618e702401904430009f7e9ef13f1f5fc0e1c1805f303e3dc04fd03ea03fe163c3a4c2e1efe21eb1b1110cef801fbf4fff405ffe51806ed0cec06faf5f5f1fbf5ee0bfe09ebf1ff060b0df6fa060a13180222f2ef1f0a1605150220edf9ec02f0e605f8001f192ff5e9fbfe15f7f2fcf70a1111fd120a1917f90e06fb1306fa03f517260ff60ee409f509fc10fd0ae107de1e2d190aff0e17f807f915fbfbf20dfbe9f316120e132319fa0009150fea0820f3010923e60b04e0ea1a060725fef51a0b091800f3e510dee61807f1120720eedaf5240c0518f13c0903031ff60f1d07ff02f7fce4e2ecf601f810f9140b0410160ef805191ef72f2ae4f107e5e218f8f107fe0efc0d0611170207130df40bf3ee04f3f603052af1f31af5e60c0bec0cf01718161b2c07e80be011ebffffecefe6eee6f2f8150a0bda0810120117f6120409e7fa1bebeffbf8e51cf91409ff102c15fff4f40e0e03f8f0130503030218250002f81001ec0f0700010dff092b3d2303f417fdfa0ee7ff06fdf6fdf8120713eefce8090c0f051f0706e5e8ec0af0e9f20afb17e7f613faf702fff1f70efde70609000cece713f0e20be5fff10aebec1bf606f000f6f0e007ed14160af9f0f3f819eb120b1110f3ed1706fcfb3a0811070019fa0412ecf5f4f40df90cf50312f50e090305f6ec140a1210efe7fef60deff8fef6eaf204eef91702eaf9eb0c00f1ffe8fbfee0f7f9f1030c110c18fd16081ff20011ee0b0febf6e7e7dccc240b16f606e9faebef0e0809fcf6f50405fa0605fcf0fbf2fb02fc14fb0916defe1108131c2c2618f90d0ee9f60cee07),
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
    .actor_error_o(error_actor_enc3_extra_depthwise)
  );
  logic error_actor_enc3_extra_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(131072'h0bf9f1f6f80afcf9fb05eef60af8f8fefaf501fcf6ec0f000e02fff10f07ef02f7fd02f1fe03fdfcf701e4e30504f5f800f8f5000afcf7f9020300f203e30ff40111f4fdfc01fcfaff08f207fcfa0a0200fcfce4f8e9fc11f1ee0aeff9f40aeff70300fcfef7fbf2f7fcfff402fe0602000cfcfefbfefe04f70104f4fdfb0ffef7ebfdfc02fcf409f7fe00fceefd0400f7ededf5fefcfd011102feea0a03ff0002f6fff702f4f5fdf7f300eefb09fcfcfd0300fa0afffdff03fe070102eff6fbf50cf3fdfc000afe07f8fdfef0f6faf401f5fee9feeee008fe02faf6f7ea0001f1f4f6f5f90afdf8feea05f9edf4fa03f90a02fffafe01fdf9fd08f9fffa1006eefd0e030300fafff908ff00fdfdef0af7f40507fc03e9feff04fef4f6f5f602030103f5fd0507fdf502f5ff02e9f6fcfbf9ebfaf2f8fffd0106f1fc0a02ff0903feeefb04fdfaf1f200120003ff0ef3eb0900fa04fdfa05f1fb01f6f90cedf3f8070508fffffcfb06ff050ae2f7fffd0506ed00020004fffdf9fff8fffef60203fe0dfe08030300ff0201faf4f9fd020002010708f80900010b000002fe0301f70804eefff605f9f605020c03fa08ff0202f900f9fe01fffa0404fafdf8fbf8f9f9f0010005fefbfd06fbfd0302f0fcfbfd050308fe060006fffffd0a040503fd0102fcfa03ff02fd0601010302fffbfef806fefe08030602fbfbff01040505e5020ef406f003fb0000fdf4fa04030301f7f1030003e9faebfbf5f6f4faf70502fc00ec00f7f9f9e1f5f0f602e5f50c06fefcfcfb030a08f602effaf9f0f802fbe8f505000701f9f506f8ed05f9e8f4f7f908fe0a0404fdfefb07fc0306f304fdfe09f8fdf4f2f1fffdfdf1050d0af900f8f6fbfb0103fcf8f0e6f40007e002ebeffff6fe02fafef7fceaf401fe0700f0f3ee01f9f125fef7faf603ecfef3fd0df309f0f4f3f704f6e206f406fffbf6ef0309faf6fed5faeeffe90b0bf5faed0420e502000103030103000804fc01ff01fe08eff8f7e6f2fdf309e705eb10f5fef400fb050b01d8fffcfee3f104f807fb13f1050601fdf6ff0016fcfef50703d9fd07fefbe4f800fd01eeeceef7fb0504eed3f6fae8dcf5d4f7d6e8f5feee00e3fff2e701fb0608d0e4f7faf9e0060604f9f505e0002200ed09cb0600f1e70bf7e4e7fe060900d8f5f4f4fb0104e914f6f8fce907100afd06ef04f8f300dbfff1ff0bfcfef6f5f7fdfdf2feff0905efffe2ffeb0405fcf8f6f6d6050004da00e9fafb02f3eef207f4f6110706fc010dfef5f40bfcf8ebf6f807f916f8030cf70c06f6f7f8fd0e0d06e9fcfcfaeafefa0406020a020401fa0609ebf90bfff5f7fee3f600f8fcf9eafa0a100b07fd1500f90801ea0602e0f3ea0100fefb01defd04f2fafc040404030af9fcfee8fdf90501eeeb09fef8fa0be8e3f6f607fffa09e8fcfef700f9020100030bf3fc040402f9f2020101fdf200f6f7eff50803000703fafdfafbfe01f1f1e5f60affe8ef0500f5f3faf1f9fef6ebffe9f803f9fff6fce4fc050204fd07f3f1f9fffdfffbf4fdfefef802fcd808f7030c04fbfff1f7fa03020402ecfcf9fc0df7f4e70cf602feefff01020502fbe0faf501fd04ee06a9f4f209e8cafafef1f1db0febfff30d08f0f10bf1cfeeffcaf6e2feeafddbfddd030eebfff20205f203fb0200eaf80107ede400f905eb06f6f9d606fcfce40408aae9f8f2f6f5cdf4de05eef4f7e7f0f7f505d2f206fbf2e8eff0ee0dffcefc0beb04f60600f7e603e309f2e2fbe8e0f8dcefedfc070309f4fae20df6f5d0fdeb00fbf1fae7fe00fb0a010af404fefe04ffde01f9ebf405e0feeff3f6fff5f7f6fff9f5fd09f605dbf7f501fbdef104ff02fbfce7fdfbfefefbedfff6f2f0feebdafb05fefbfbf3e7ec04fc0201e2f7fff6f5020800faf6eaf60c04020ae8f90003fff705e8fe04fafdfb00e90bfeebf7e5fcf6f9060203f309e602fdfdf111c5e4ef0bf2c50002fd05f3f9f9fafef40102e1ee0ddcde00cbf9ede2000dde08dc0501ebf6fcff0cf9cceefd06d7e90609f5110de6fd07fa0e02d5f8f3e1f702ecaa01f8f8f0fabcd71800fbf2fed708fc020feb09060600dfdb0afc0903cefafcf706fd07f701f1f8e3fff3e30ef2efffd601fa03f51df3e3fee4f60203c103fbf5f205f3fef6ff050adef60efcff04f7eb04ffdf0f1100f0edf30ffdffe7fff8f602fdfefbfa0a03deeefcfaf8fd0402f9f40301f804f70507f7f2fcf801f8050a0efbfeff010afff7f809ddf4e7f408f9f7f7eaf3f6f3031e0c1011f80e01f1f8f70cfee5faddf8f3f6dcf1fdfffefa13f0f8fff80ce5e6ed00ebf7f005fbde0003fb0be000f704fceffc0101f901fef6e80312fbeffadc04eaeef3fff6fef0fefaf005f5fbfce5faef0b00d7f301070ef400ef001206f701e30900eef900f2e3fa03fafaf7e903fd00fb02ffe9f3f1f215ff05fa11ff05ee0a0907fee905f7010c00feeefbfe00f3f7f6f61505f4fdef04fb04f909fef3f9e6f90907e50ed7ebf4f601df0ef6f3faef07f902f5f602fbf1f1f8cde8f9ccf1ece4f7f4f9f8e60207dcf0f5fa1602f3f80bf9cff9f2f7f7f106f501f7ffeaf5d3f0f4e9e31500b9e4f403f5fbd4fce307f8f601dcf8f4f9fcea0704f3e3def2f7ff0d08e0f6f2f7fbf904f008ebf8ee04ed07fef9fa03e60f03f9fb01fcfcfcf3f902f8e8fff204f704f203050cfe10000c0ffaf90c160832ecea09e3fffbe5f70ef500fefb2603f815f1f60214291bfbf8020b28f60106edf7e1f8eef4f30710ee0d00eafa20f12a02fdf40104faf705fdf5f6fcf2e2ffee0a090e12f0e80210f5e412fbf806f5fde2fdfffbf804f003e6e703f6fb01f410fcf9f506fcee022a0b03f4f102e6ebfffd01c0fe07fbf9e8e60701fcfdfefce407fde5ddfbcf05ed00f30ff3fbe403f9ebf5faf80ee8f8ed06f8d5fe0113fa0807e2f60104fe04dd03fde1f30de1bfeb06f701fdddd40503fa0804de07f0f600f007fc1d2aedf309030d12cd00fcf108fcffe302f1f6fc01eb0705f505fdd5f8fcfc010e0901ebd4f9fcfeeb04f9eef8f6fef40afdfc04f3fbfc03fefe0303f8f9ffebfb01f2f00003faf9fafbf6fb05eefc01fef6040302fa0406f8fdfbfdf704f301f6fff9fef60100f5fcfb00f9f202f806fef703fafb01f9fefaf400f703f1faf6f8fcf1fbf903fbf8fdf601fcfffcf9fc00f6f5fcfef5faf9ef03fc000000fb04f7fcf8ff01fd0102030000f701050b09fbfffdf7fefdfcfbfcfef40706fdfc06ff0501fefffff2ff030111f9fcf806f8fff9020702dff207f505f60af3feecfcef0108fc0004fa03f9fffa0c00fefefb07fc02fdf601f6fb050200fdfb00fff6fbfefb02fafd02eef6faf401060602f9f7f8f9edfe0500fe0806fc03f9fc00fbfefffff509fffbf80701e8f60ff4f6f805fbf303f3ef02f7fffc02f7f20906fee905e805f5f8fefa01f9f20bfdfbfafff3f8efeaf507f8e6f9fcfe000703f802f6f9fdfbe6fe07f8f8f9fbe3f4fef901fbedf20600f40bfeefff03fafcfafcfbf609f1eb06fd0b0aeb0009fa0000030504050701fbfdfb09f2fef4ecf5fefcff01f9e7ef00f5f906f807e408fb0cfdff02f502fb07fefff6fefcf7f3f303fc0afafdeb00f7eff80302ff010afcebfdedf004f4ecf7f703ea051201ee06faf20d0907020eeef8f8f5ecfdf5fbf7fbffff1904f6fdfbf7fa06f7fdf0f9f5fb02fb0e1507fe0bff01ffff0018fa09fe00f9f608fdf4eef80a0dfcfdfaf2f7f8fa0aff0109f7f6080104faf2fff9ff0302fdff02fd01fdfaff0100ff02fbf700fbfa0405ff010505fb0103ff0300020100fbffff0101fbfa0102fafefe03fb0100fff8feff0101ff02fe01fafd04fb010102ff0005ff0005faff02ff01fd0001fcf8fb00fffd02f902f5fdfd010102000000fb010001fffdfdfd0003fffdf9fa00fffe000103000100fe0200f1ecfa02f6f3f80001f7eefcfafefff70200f2ffeff00900f206fdfbf801f3ff03030605ff08fb0103f400f6fe10fbff0004f503fbfaf0fd01fafb0407fb07faed03fd00020101f5eefd0401fa03fafe0502ff04f4feebf708f1fff8f3f1f4ff05f8f6fffdfc03f3f9fb07fdf1fdfbfdf802f1000300000506fb0ffdfbf404f9addbe103eabff700eae5ef1fe303fb18f005d1f7f5cfccffc0f9d0bdf90ad4f0b9f5faf1ee0dff17e5bbf004fccded0bf9fdf102e4f6eeede408aaf700e7e500e2b0e3fff5fce5bec50b14eaeff8fce5e3eef7dff0fbf5fcdce8f7ff040fc5fc1604f3f301ebffe305e3ecf7f004e9e4fed503f202f508fbe1fedf11f4fbaee7ed1afe05134e0403f622e2f0faf4fb07fbef1df2f51411fd29f308f7f8eefcff08e800d8fdfee8f0ed20f7e7e8fffffaee09e1f9f9e20df710000bf5f8effc02dc42faf809fb0405e2ffe70bf7e409ec04f1f71bfbd2eb0ced12f7eeeb0c2906fdfaf5edf1f60512ffffedfaf3fbf6f9fc0e00070306f10504071ef5f7e3e6f2c3f1fcf8eebf01f6f3f9d0fef1f8faf805fdd81000e3dffdc310dad4f4fcde06defaece0fcf6ff0adeeeebf6fac5fdfa09eb03fed9fa11fa03febcfc02e3e802eebff7f8f10502c2d2fb00f800fbd1eef8e902e4fc1307fdfadefbf80ffec1080afb03f903e4fcecfbddf5fafafd09eefadff8f60b0308fb03eed50bfe06cafd03ea0100f505f8fef7ff020600fdfc0bf9fef7feddfdff0005f3fafef700df0413f8f9e805f3f4ffe4eee3f1f7eaf303fd0bd8faf101f1f610fa0ff7fbdef7fdff16f700fcf614f702f5f806e8f9e6fbf3f3fef5eff6f2fafb0a01f8f7e3fc03f5f9f8f4fdf8fc03ff09f9ecf1fe030bff06f3f6fcfffcf8edebf8f901f308060df00011fa12ff0e0006f708e6f8030ff1f009fdf4e9f7ff1cec1d19f1fffb010d00eee502f60607fcf0140ee6f315fbfbfcf002e805eafcfef8f8f902e914fcf701ff0304060e150d040602e0f721fcfa0709f6fae9e1fc0ae2f8fcf8f00f0204f8f5d9faf709ed0be6010afbfd0d010bfce30d04030b08fefa1e040fedf6fdfc070006fa07fafaf7f4fefd03fcf3f7faf7f007f8f200ff02fbf6faf900f200f701f809f6fafe01effbfffbf8eef102fb02f6fb07f8030206ff03f8fdf6eefeee08fafefc030000fcfb0afcf70002f9fdeff9f3f9f9f6f2e7fcfaf4fbff0df6fb03f9fa02fffaf70001f2f80afcfaf9f8f7f4f801f7f7fdf2f6fcfffc0101f6dd0806fafd05f7f401fc11fd07fffff6faf7fb010ef6fb0af1f6ee03f105fffff402f7e501f9f5f0f6f4f701f0ecfe09fa0603fdf801fcfdf6fe09f9fafd00fdf2fc0a04faff0c08f2fc020100fafbfffcfe0bfd00fbe905f1f6f903f600e809fcfb01050a0ef7fef805fe08f107fb05f9f204fd0300f9030affeafcfc01f40000fe07ff01f401f2fcfafdfdff03fdfef9fcf405060b02fef7fe010e07fefefe0a0afef7fffd05faf30af9fefef2fe0507f904030dff0c01f9030104fcfcff0003f4f805030301f7050e00f803fe0203f6021102ff040d04020506f20905fd03ffff05ff00fbff0afc03f601f10d05fcfff70601fd010006fdf9fbf9fffafa04dadeeffbefca09f2ff0deafd0605fef90ceee80e00dddcf8cffee4f5010cf1feee13fcda00f40422d9e5f50316e2f30106edfc01f6040c10f701da0e0ce5f6fae8c7dc05f6f507e1f3fefcfaed0feafe03f00ae8131724ec08eb03ff0ef6d501f7fe160502f0faf9f8ebfdf7031505dc01ececf702fd0710fbe8e6f2fbfed208d600fbfafaea07fdfaf00208f700fafc020be703ffeef4feeef8fbe9f2f4fbfef0fafbf1f802fa03e7e8f20fffd3edef04ffe907e6f807fdf8fbdcf808e9f702f6f4effffe04e8e8dcebfef6fd01f1e6f9f8fbe60901e900e9ed0b06f908e3f8ebfefef6fc0200fefefb0004e9fdfdf0fee50201fdfd0ffaecf7effcf8fdf7fdeb050e09f9f4fef40304fff4fcfefa0104fdf60101fdf202f005e8f30001f708fe01fdecfefe0101e2e6ed07f9daff0108f4f901f8ff11fff003eefc04f8f301fbe8ee04fb0303fefc07fcf301fffafffcfc03f50e08070a01fe00fb0405f802f90309fbfff7fdfdf900f7fdf70c0af2fef2f7fdfafe02f7fdf8ea05fe03e80ed7f0eafef7d0fcfb00fad5f8fffeee0209f4eff1fbdc04fdd5f8fcf4e902e0fce3f4fde402f3ef06ecf0f6effee2edfffcf2f0fff5fcf502fffee9f5fbe8eef0f5d8fc05fb08ffe5e8eaf6fffefadbf2eff0f7df00f6eefaf3e201f6f302defb01f204f40af2fae3fcf0fbf4f5fcfde0fbf501f5fc070804fd05e6edf4fee7f2f3fcf6f80705f5120100f70e0cf60004ef0a0efbeafd0704eef9e8fa030000fc1d0b0b28fbfcf7060bf3f2080106f3020500f4f60fffeffb0cfcf1fe0bfa06f7f7141403fd0401f506fef8fe11ff0000f0f4f8fff70600fcfafefc07f7fb040302f8ed120405fbe500ebf9f3faf3eef000f20ffdff02fcf402021d01fdfdf2edceeff4fafce0f8ffff03e8fef80200fdfefdf2f9f8e7fffbd9f8f6f9fb07f4fce8fb03eefdfcfd05f4f3f9f7faf4f6fcf8fcf003e1faf4fafd03ecf4fdf3f1f1f6dff8010300f9f1f2fafd02f003ddfcf9efffebf1fbf8fbf7def6fefdf4ebfa08f302faf9fbfdebfbec01feeff9eef3f6f304ff0103fcfe04fbf1faf7fef0fdc0fbf003e9c3f4030002ed2101ebf91803f1f8f0e8ece5fee7f70303f009fbf2faf00412f9ef060c14f005fffb0f05fb0bfef3f7f1f1e8f703fdecfc0808ecfe03d8e0fbfff8f6ea08f50bf0ea00e8f8fcfcd5dff311f1ecebd5f3fff402cf000ef0f40302f1030108f2fde6d8f9e6f50cd7fd07fdf3ed02ea03f70705ffe7ffeaebf9fd00e509f6f901eb03f2fdf00a04feeaf7fde6f200dfed02f3e1fff3fddcfafbeafaf700f8eff20b0bfdf5f2f902f307f8e9fbf9ff05fde5ff07e4f904f9d9ef02fffef6c0eef4ff03f802f6fbf5e1f7e0fc0603e5dde5f5f50501e50300f8f4fb01fa04e70be3f9ecf202f3e9fbf3fd08fd070408f6fe03f5f501f5f6e8ff090b03f1fff60101fcf5f9f8ff0003f5f90102ffeefaed0cf2f4fcfb0202fc08fcea0900f709def7f40205df020309fbf701f1011205f403e5fd00f4f401f7e8f504040500f9fe0ef4fafefaf8f2edfc0cf1ff0602fc07fc07f60104f605f403fd04f6ebf9fff6faf7ee0110fcf4feec01f6f6fffafdfbf5e9020006ec09ecf5fbf5fbebf702040df20102fc01fefcfa0200f6eb01fbf6f903fbfafffc00fa0002f4fcf902ff0401f80405fdf5fef7f8f4fef4faf6020202eff809f408f804fbea01f704ffeaf7ff0002fe08e6fbfff5fbf102fdf6f9fbf20402fafaedfafbfe00f000fdffecf7f6f8fef6faf9fafa040000fc02fc06f7fc08f3fcfef0fb02f808fcfffb00fc02fcf8fb03fff7fffe00fa0900080a06fffe020407000103fcfdfc04fefefbfa02fe0612f8fafefefe03ff0201fe0003fcff05fcfd0303fefcff020103fe01ff03040601fb02fcff00f60106fef1fc0a07040104f9f9fb02fafeff00fffd0003fb0609fff8fe04fefcfef7ff05fe0106050200f6ff06fe02dff502f302f60106fb00f4f2fd0400ec03f9f609f7efe804e1fddcfafbfdfd050405fcf500f3f607e4ecfbfc00ddec0307fbf60af70511f9fb08e904fbf9f2ff05f9eb0a030213f9e7f6f4f0fdfef2f7eefef60602fa0d070c0306f202f7f90107030bfdf6f7f5f0f4f5fbe6f9190dfff3defb08f90009fffdf8dd0cfe04ee07e90813f7f6ff0204f8ff02f7f6fffd0106f5fefbfa07f0fffe0201f1f8fcfa04030effebfef6f7f5f0f1f10900f001fe00ff0bfcf20100fafc04f4fbf5f5f4fbe9f3ec010200f90306f7fbfcfa00f6f6f6fcfe05fefff30c05f3fff8ff0af504f500fef90209ff0507fafffafafeffff02f30405010007fded0002f70101fafde3fd0805020004f3f913f9f7f90503010a00f303fefcfc01e708f1e8f9f80802f206fafb030afa0fecf1ee09fbd9f8ff070504fdf5030b020e08eefd03f3fd02e7ea010102fd05f4f40dfff403f80500f9fb09f4030c010dfffb02fe0801ed0204000300fef30004fbe8fdfdf31104fcffe9f8f5fcfefa02f4f7f8fb05fbed0cf6f500ff01f4f7fb01f8ef0bf7f7fff6f7eefde8f2e6fe00eb02fbffea04fbfe01f10302fc0006fdfefdf5f50205f802f503ecfbfef7e3010cfaf20004f1fdf3f5ffe9fbffff02d3f8fcf7f7fb01f6f5f3f8fef4ecf7fef7fbfaf70308f3f3ef00f705fd01f301edf2f4f3f3f9f3fb0503fefe0603f8fcf604ff0ef9fef804f5f3fd0ef6fe0606ff060cfcf7fc0401f908f8f7080702fcfb0307fff901fdff04f307fff1fafafafdf2f4fb08ffeb0f0205fffe0405001500fa04fffe01f4f304f9fff8feff02ff01060bfef80302fd00f2f807020afe05030aff09feff01fa0105ff000301feff05040101fbef0504faf9fbf9f9fdfffe04fefff8030304fe05c9df0003ffe5f6fc0213edf3f90af30f05f2faf7f8eceb05d8fdebecfa0202ffee0003fcfdfa03f3d8eb0b0006cbeffffc10f308d4fdf6fbe600f0f9f7faeafa0be1effc05f8eed4dfe9ede504fde9f7e90702f519fa00f2f2da07eefbf4e3faf90507f2fee6fc0712faf8f8fd15ffe80aed05f4ff0309f9eeebea0904fad706fdf903fbf7f404fcf503fef3fbfef6feff05f9f709fef0fbfb0a000a0dfe07f9000e01fbfd03fbfdebeff400fde60705000003fef00309f802fdf200f500f9fdf6edfd08f702f901fcfffdf40204f8f8f8eefbf4fefcfb0f02fe04fd0304f6fdfffcff0505fd090500f50307f5f900f6feecf308ff0703feeff6fa000407fc05e1f907f9ede2f7f4fb0be308eef80511f8ffdffaf902f403d6eeeef10400ee00dffbffff0600ff01e8daf511fed2f70105fe0700d708fbf0e905cffc0dfcf606ead70101fafcf3f5f4fefbf8f5f8eff5f8f0f9ebf4f9fd03f1f60300f7f5e5faf9020503f8f1fff603f8f602fc0203e603f604f4fe05f9f4e3f6effb04ffda03dbece7e9edc611f7fafef5f8efebf7ebfdffdcf2ffd5fc07bb08e1ddfd07dffce50205feff07fdf9d6e30613fae1ddf5ebededff00fef7fbe7fbd0f70aeff8f8edcbee0009f9f7e3e7e4fe14fe07de0eef0600dbfe03050403ca0afdf5d9dbeffff8ff03040203eb0cf4f7e5ecf0f7fbfbf5ea0ff7f80811ef00eeebfbfbf2fecce5ea0b00bcf501f6e2e808eb0bf906fa02f1f706e0c3f8b8efdbe5f9fee802e6fcefe9f9070107e0f105fd05e0f0020b01f001fbf6e8f4fc01d2f614ebddfd0fa2f00505e9f3c5ebe90407f8f1f5eefdedfcdbf51cf9f2d7ec07fa0b0ed20007fffdf8f7d303db06e6f1f2df02f1e106d6fcfc05fa06f6e8feef05fbfdba06fe03fefd0304fffefefefbfb17f90103f4fa11f5f0fd0dfdfdf0f80803fcfe001cfcfe0400faf9fd0d00f0f5fafe04fffc01e7fa1900f3fa01fdfdf805fc29fdfd0208fff8fb060901fdfdfa09fffdfdfff7f4fafffe08f4f3edfdfafaf503fef701fd06f5fd00e3f30803fb08faf8f4fbfe02fbfefcf803020003f2fffc0efcb5f1f8fbfaca03fdfdffeefaed04f6080bf8dcf4f5dee0fbcbe600f8f204ed09d303f5e5f9fcf8ffe4d7021302ddf30804eef40adbf8f7fefcfed7fcffe3f4f3fecb07fbfc00eec9dde70af804fce1f7f6f100de03feeaf9e3ebfd01fd07ce040005f8f809fefeeff7e0f7f4ebfeefe907e4fef60305fd09f0fadff5f3fed2fef5f308fff3e607f902fff6fdf3fdf9ff00fdf50100f9eefcf4fef3f70203fdffecf9feee02f7fc08f5f0f60101ddfcfa00f6f509ebfb0501f3fbebf40200fd0af5e7f6fe0002f000f4fffe090ffc02faf6f903f306f8faf2ee0004fa00fdeff6fe04fcf902f5f9f6feed06fc03fdf7f2f7ef0001040007f7ee09f003fff8f4f6d2fceef5f2e8fff605fff003f1ff08feffecf1f9f9fce7f9dfe9f3f1fef9f405dd04f7f603fb00f6e6dff40408e2f9090807f909e1f510ffff06ebfff7fff4f5f4e502fd01fffee2e8f5f7f30bfbeaebfbf700f71301f6f3f1fb0808fa05daf8f7f9fdfafaeffdeefdf0f1fced06ffe8fdfdfbf9fd050afff303f00907feda04b6daf5f2fdcfeafefb11dff4e9fefb1b01e9f5fbfcf9d4f4c000d1dae5fce5fbedffecde00fd01f8bcdae4f000cbeb0709110001e2fbfdfef1fdc9f605e6e4f700c1f50802ffeed9ddeaf0eaf5f8ddfbe607f1f10d0af704f9e707fe07f0d505f7f900f0f1e2fee2f9dff2efe51d05ef01e7fafbfbfdfdfdd6ecd805fbeeb7fce30a11fafdf0fa01f812fcf9020204f503f2f204fb04ec00ef07eef1f7fef500f708ffeffe00f9f5dfe7eff9f6ddfcfbff03f706eef60ffbef08ef0102fdeefff1ebf203fe060005f6fff8f409f9e8efeff601f602fef70707f308fcfa01ee0201fb05f4fbf6fcfdfa06fffaee0605f2f6effd05fa0b09fdfaf1ec04fd04e5fdf8eeeb03020d05ff08f6e9ed0bfb05faedfcf0fffdf30a06f213effcf1fef5010df7060000f0faf8f5f7fb0b06fc02fafc0b0b030c00f4080003fd02faf70403f21af901000707fef605020609fae901f80002f9faf5f30eef0307eef4ea0b0d040503f7fffe00e9fb080af30808ff15f10eed01fc02010b13f507f8fafa0506fb07f7eefa06f9f702fa07fe03fcf7f006f3f6f8fc08f5fef6ffed00fdfaf8f9f9fd01f707f7f5fbf0f6fbfe03e5f2fa0306f908fe05fafff6fdfafcf301f2f5f1fa0a040500f705f50bfbf502fa0305f8fbf80101f80208ff04f9fbfffb04fe0ffe01fcfdf7fbfcf900fb00020f040403e9f206fbfbfb02fc01eb05fbfbf000b2f0fbfef1bbf4fe02fae003e9f80002fdece0f6fadfe202c1f5ebe5f50cf4ffdb020bf4f9ecf7faedd4f7ffffe7f3f8fe04f1fce7f0f9f3ebf5c5f90ae6edfdf8b9edf7f5fa00d7e2eb0ff7fefce2f4efedf0ddfb02e7f1d7d9fcfdfe0ac80011ebfdf4fdeff4ed00d905e8ea0be6e0f5df05f9fb0b0501f2f7f90dfbf3bdf0f80103fb0102ffff05fd00f905fe02fc01fdf902f9fa020201fff5fdfdff00fefffc04f901fa00fcf7f8fff40103fd00fb02f800fa02f30200ff0000000100fbfe07f9feff01fef7f501fe03fbfb02fd02fb02fafbfcf206fe03fef9fff5f6fdfb00ff0101fefd05fe0200f7fe020001ff03fefc0104fefa000404faffff0500ddfbf8f4ece8f6f4fd09f909f1ed0306fcf4f5fcfde2fbfdd50210faf2fd0404ee030712f7f9f40002dcfcf60103fbf900feeff9eefae0f5f701ec0703e7f2f2faf8f3fdf70efad2ec01fef0fcfbe1f3f9f6f6faf2fa01ede5e4faf5e900e0f3fdf6f2f7fc0700f2eef108f8f4f7f5f2fdfdfb05f909fffc03fbeb01fdf3e9fcd9ea020efdebfcf7fdeff604f804fc0705fdf5050bf6e5f7dffae9eff90506050807ede1fdf60b09e1f9eff4fbe4fd010ef30602fdfbfe12fcfee3f7fce3ed04fee4f00701fd1ae90407f3fefe06f1f1f3ef0cf603040217090200000fffd2f90df90502faf601f80503f9f3060c0d0201f5fd01050302fa02f3e12302fddc02f4f7f7f202fb0704fd02f4fe02fafa030200ef00f9e70303f400f9f5f3fef50201fb07f4f6fefdfcfdfb0001030afbfafffef402f2fff2fe0400f1fb00e9fb0af505e1fffeff02eef5fdfb03f904fffbf6f504eef7f6effdfef502fffaf7f300fffffe0005fdf8f803f6fdf501fd00fcf8f9f700fb02fffefe060dfafc00fbf9f7fbfb020100f3fef7fa0cf9fa0904feff02fa00f802fcfef800fbee0401f2fdf3f902f800fc01f8f1f5f70404f5f0fffff2faff020001fa03fef4ff00fef8ee01ee0202feff0709f2f7f8fffffcfcf7fcfcfafefbf5f401010903fbfb030608fd0102fdf9f3f9fbf803feee0407040401eefbfff901fbfef0fbf9010104f6fc01ea02f4f604f003f707f8fde5fafcf5f1f6e9f3f3f0f20100fff5eef9fef6feecf7f9f10301f200f7f0fb03fe0debfef607f3fbfaf8eefb0b030601f8f9fff6f50bebfd0803080a0407fc06f6fa0b01f1fd00f4f5f7dc090cf000e4f7d9f5f606f800ff000505fc00fe01f9f7f801f80203f9fefcfeff040105fbf102f411f9e4eb1ffd08db0a01f006000bfef3f70506f9f6060601def6dc18f0e505f20007fc0efff6f506fe0cecfee50903e8030606f403fef703101711fdea03effbf20eece9f108fe0705f1f0110804f9faf9fbe80315ef01f30702f601fbf30c02d9fd08fa0efaf8fb01f7ff08fb05f10bf6f5fae0fe010703fcfb01f8ddfef901f1febef7e9fbfce0030704fde804f903030503f2fefaf4dce1fbc8edffebfb06e401dafff7f2fb01fc02efebe7ef05dbe6fd0b02effddef8e3071602e301fdeaeef0eadaeb08f7010bd3f0f7f6fee9fbdaf4eae5f6ebf9fde9dee9dcfdfefe00c3f6f3f6f1fd01f1f7e7fce0eef3f4f5fae6fc01f3f801fcf5fc0cfdfb0408f7d4f2da0a18fdf8e403fdfdfcf6e6f2f9fbfe06f1f2fb09fde1fee904fde3fc00f2faf205feec02f7fef4dfe1f4fafdd2f40302f8f402edf51cf8e40cd7fd00eff5ffedf4e501fb0004eef91b0100f6f8f4f7eff3f9f1ff00010bf8f205fefa09e2fcfbfa0bf9f90300f9fafef7fdec15fdf1faecfc07ff0704f5f6ece50300faf010f6fb12050be402fa01fbf9f103f9fffc09f2ed0d0002ecf8e30bf4f90e010d01f215f3eafdfefd12e804ecfbfae4fc040dfe0a06eafc100e0600e508fbf9f407f1daec03000804080100f3050e09f301fbf810f9110a1a1803fd090a0401e5f905020403fcebf5fdfbfa0500000cf7f4f5f31a01fd08fafaf900d90a03ffe509fb07f600fe0afffe05fc0afd08fe00fcfff3f507ff0202030ffaf3f4f5fafdfc05faf8fa03f903fef9fe07f6f905f100fefff7fafafd04f9fe010dfdfa0604fef8ffee03fefbfa07fa02030307fdfffefdfffd0efffaeefff3f7fc07f5f9030101fdff01fbf8050e0702f7fbee08ff0302fdfb0000030700f7f406fefffffcfcf7fe030104fcfd0102fafffafdff01fe01030000ff060afdf801fc080b00f3fe03fa04fa0600fffdf8fe05f9ff01fdfefd01fdfe06fbfc0105fffdfffdfd08fbf7fdfefc03ff01fefc02fc01fe00fc020fff0100fcfbf109f701fdfffcf7f9fefbfefd1401fdfdfa00fc07f7f4fe0105fd02fcff0002fd0701060cfefffc0101bfedf4feebc2f400fefeec11f4f8f41512e9f9f7ebebcef8d3eaede307f7eff9ed0204e6ffec0b2bf9f007fbe7f3fc090ef5fafa08fcf5eb0d0acf030ee9f70204c7e403f6f1ffe800e5020af90602eefffe00e3fd12fdf2d6f003ee0f10cb0004e9faf100f5fdeaf3e80bf0ec01dee8faf00505fb0f0205ee08fc09fff6d6fef500fa0801ed0102fcef0803ff0600fe090dfa0205f9fff9e9faeaf208fe00ffe905f907fefefc12eeeef203fbe9fffaf9ee09080bf8e904f90907ff050af5f4f5e806fdfefef7ed04030dff120105f50609fcf505f5fd07fc0407f604f4eafa06020c02010efe0ef4fb0a0efa0b03f30200fbfcfefe0408fa0cf9fa0702f2fbec060ff1fae108f8f7f604fafd00fa06fe08ea0d0afaeefaf202f2f7fcf9f802fe0700fffd03faf9edf1f700f8e4f5fdfef8fd06fef9defff902f10109f9fafef0ecf20602ffeff6f8f7f8fcff07f5fbf5ef01fcf7f202f8fbea06f908fceefff40006fb05f305080204fef2f6f90ef0fce3fd0bfffb12fff5f5e90003fff902f8e701f7fcf703f7fffafbfdf2ff08f506f800020108f9fdfc0400f1f7fb00f9f206fff0fdf904fef6e3fc0401f9f1010000ff000204f8fc0af80001fff3fbf9fffdf005faf904ea0f0405fbfefcfdfaf7fa0e0b04fd03fc06faf80500feedfd0000020204fefbfd07f8fdff04120cf7fd0407fbfeff0005fd00f1edfc00e906dcfd0f0400ed04f60af5f9edf2f7fbf5fbfcecff03fcf304e004f4edf9feea00fefff9e4fdf4f2f8dcdbf6fa07d403070ce9fef9efff1f04f706ee03fce4e7fcf3f1df03f50306f9e80cf9f50702f8f1edf9fbfcfa0205100c070900000df2020a0101f0f3f5f8030100edeff806fdeff4dfff00f2050af801eae600fe07e707f7130206180a01fdf903eb0807f2fe04fff8ef0102f609fb0007200efef7fef81f0011f5fefefdfcffe4fdfd0cfeef0bf607ecfdfbf7d8fb0ff5ff0909d7f3fae61bea03f900fffdf515f202f00401fd04f1fdedf7f4e01002f50dfd06daffec01070802f7ef09e0ed09f0effa04ff11f206f6020bfffff60d081a070aff0bfacbf2e90aefe0fefffef9fafdf807f8020909e5f9ffefdcfeee0af7f70afcee0adef605fff502f905f0df0115f7d605fe0c020c07e3fb02fe24f9c7000601fb0bebd60bfff2fb04bfe3eff7f202fcf9040deb0be8041c2412d8d70fff0d2cc904f40703f519e80ef9fced06fbf0fdecfcffec10010805120be81cfcf3fc00e404e8e202fef6edfbfff2edee1bf9f4edfb05fafdf3fcebf1ffe8fc0d02eb05f1f5f6f50011fc04fffe13fd0604fc1200fbf902ecf4fbf1f5f700fceff403fcf7f400eeef00feffecf4f90302edf9f5fbf8f4f8f7ed04f5f5eff2ecfcfff5fdfb0008fcfbf300f906f0f50003fbf5fbeef9fde5fe06fdf5fb08070bfefbf4ff0a02aff5eefde4d303160303ed17f3f001faf902edf8fce7fafdcbf807e60201dafddbf90c0bf206f51600f5f421eaebeffefa08f502f9f9e7f4eb05d4fe0fe5f9fde0c7f000f005ffd5ecf401f3f8f9cef2f0faffe4fb0904efdfe802e90511cd060afa03ef00fd01ebf5e80be805e5f9ea0003f7ffff010903ea0905f6fa04e2f7e6f3f20407ef04fefdfbd9eef0fd00fffff4f204f9f6e1f8dc07f6f1f500edfbe6fb01eefdfbf802e9f0f10005e3f7f902f10308e3f4110d0b06ebfaf7f4e7f1e9fdeefdf6f9fee50ffbf5fefaf7e601f1fffe01f6f906fde8e2f7fd02f4e1f7fe01fefb0bf4f5ebf5eafaf4ef04f9f5fcfffcf8fdfe010208f6e8f9f7fceefcf5050eec0b0f04fafdfaf1f20900fe01fef5f7010bfdf3fef6ebefe5ecf00f02f8e709f202f6f4f1f7030b02ecefecfdfd0bf2fa0204ff0707070bf6ffecfa00f210f404fd0006f70a120306fcf9f905f3fe0a0df5f2ec07f30a0700fae4070af90a0309fdf603fe00fa0a07f500000bfa1912fb03fd04ee1309fe00f5050008de0403f701ec05fff30400f6fb0406f408f8fc0206ebec05ef01f4e8f7fd0ffaf00605f20200fffcf0e2faf8fcd5f503fdf70002fdf4110304ffe2f8f9f7f400efd9f4fe03000de8f3fc05f9f8fde9fae816f0f5fdfefdf90efd03fcf5fee1fdfb02030003f6f7fc06ee01f6f1110ceffaeafefafcfe000611f4e5f10502edffdaf308f6f8dbf60904f7f504ecf9fcf905faf2fd02f6ecfaf9f4f5f1000403fffafd0600f4f7fe15fdf90c01fdf507fafd0ef804e3ee00faf9fae6f101ede605f2defcfc08f3fce5e6f404050503fbfbfcfbece8fd00ea01daf600f40816e00304f107f8ff0005f302f11103e805ebf4effb10fffefb0d09e70d0909fb02e708f5f513fcfefd00f008f7f5f5fa000003fbf8ff03f106ecfafdfffb02f9f8f6010804fdf10702fef5eef7f607fbf1f1060aef03060500fa08fb02f2ff00f2fbfe05f9f702fc0812e709f6fefcfbf8f2fbeefe041506f7020502000406fdfee9ff04fe0303fc02fdfb0903f705fa0602fb02f20bf1000209ff08f9f206fc07ea01ebeef9fcf6e00107f4f3f3fafa01fa06feffffff05f6f4fffdf5fdfd0b02f201f6ff010bfffff6fffde8f911fefdf60105f1f705f1fb01fcf3ffedf60af3f603f5f1f2fd06faf0edf3fdf901f701f4fafd06f7e807f3fd10f0fa04fffc01f0fefcf904fefffd04f9f7ec01f5e609f8eafaf0fcfa010300fff2030cf8fbf6e5fcf0fb010505f3fdfefef70204fd00fc000b00fffef902f1f9f20bf3eaf8fcfffce6fbfefb01040512f1fbfe01fce5f5000bf8030005fd0605fb03f2fc0c010201eefaff01fef9fefdff0a0bfc05fe0ef5f703fef105070802f5fefe05fc02f6fffdf7fcff0203020803fe0cfefcfffc01fff000fe05040909fdf8f6ff0102040502f6f9f503fdf6faf103e2fd00f1fbfef908fef4f7f900ffe70aedf9e7f9eef70504f505fcff02fc0af1f7ec060aee03f705f302f8fde2f70306fff50cf703fbfb17f60105ff09faf609f30af304fafff6fcf9f6f002e3050cf102f7fde1f9fb0cfbfefbfee8f2e9fd0e02e3f5f110f9eff4f0eefcfafcfffaf70a14ffec07f1b103f800fbdffafafa18da05fcfbf60dfff0eafdfae2fdfbd1eaedf8f903ddffd9f20ae3f9f4f9f1ecd1f8f5fdd1f701f7f3e6fd03f3ee09f5fee0070ddfedfeebd3f905fff705c0dde8fbf7f3f9daf4edf6fcde0003f8efdff60300f20fcaf403f1fb0100eefcf000f205eff2fcf5effd04f5f9000a0b00ff04f300feefce01fef5000702fdfafffafff9fbf6fdfdf9fe00fdfd0af80100f7fdfd00f9fc00fc09f608fd0600fbfef9fef3f6ff02fe02fa09f70005f5f4ff03fbfa0206f204f4fc07f8fb03fc05fcfefdf9010403fa01fbfd01fafb00f30cfffa01fbfff1f4f8fafb020d00faf6fcfdfb03fff8fe07fff9faf8fa05fe01ff02050afe010409fee3000ffefde100f201f7fbfafb00f4fefcf1f60104fef304e404e502f8faf600070df9fb0401fe03e106f2fd01d6fdff02f40901f8ff0707ee05f1fef7f8f0f400e1020402ff09f0ff0dffeffd09f603eefa0cfa00ff06030d010af81109f7fe0103160500f40304f501f902160b04fffff9fbfff804fdf605fce403020af1feec02f2e2eb061904060bfce4180606efeeeaf9eee8c3f0f2fff602fd0bf9ee0ff5f719fbfd27eff7f2e9fa01f6050a020d01fe03fbfe28f904f5edfafce7f0090a0ae80903fdfdf6ed1103dcf7f7cb07efec01f7f4f63d02f9dd05ddf903de050a0cf6fa0721f4fe05fa081c02f7f7f4f90f09f5ffff0ffef2ff10e402fff206fef8fc00ff02fe020300f5fcfe0003fdfcf7feff000102fe0202fcfd02ff00fe000103f8fbfafffe02040205ff02f7fffaf9010200fef701fffef90402faf901fc09f0ff0001fefe0108ff03fefcf70501fafefcfaf3f1fd00010106f7f4fc0302010000010500fb06fa04fbfcfa01fdfe00fcfd01fe01fafcfa03fc02fefffcfbfef4ef00dd08f00407f2eeeef606fff8f8e3fb10f6f400ebf4eefcf201ecffe90b05f5faf4f305eff1f0fe0ef5f3f700f5fd08030e21ffe306d0fef1dcf800e7f0e1fcfb00fcf5e208fbf702fce1faeaeafff81002151efdf701f905f5e2f6f40719f3fcf4fdf9f517feffee1a12f1eeeff1fb00fd06fcfbf6dffa07f8da15c8eafdfffacc0900f9f2dcf1fef6ff0402f9e81003eee8f9d50fdbeff8fcfc00e701f0e7f6f90a15ece2e70d0ac4f30010fefffbf1f50e0018fdd1faf9f0f912f1c8f606fcfe00d0edf9eff10902edf9f4ee13effc070b0ef0e8faff0c0be3fe05f700fd09f108f7ffeaf6fb020608f1fae2fdfdfe040501f3efdc0802fae50ae8ebf3f9f5eb010aff02f108fd03f71403fdfff6fbe8ef05edf4f7e7eb01e8fe0f050313fc06f9ff0907e30b09fafdf501fde602faf8e7f7f9faec010b000109fcf30602fc06fae5ff050000eaffe8fd07eff8eef1f1eae8f4f3f704f2f5f1f10af8f102ff0004f0fcf6fdecebf1fdeefc01ec03fcfc0906ee0005fefef7f1f7e70000fafef400f8f8f9fcf3fd0500fffef8ec09fdf9f4fdf204f8f1fcff0101fdfbf9f7fcfbf8f9f1fef7fc04e6fe0b0afbfc0af1fb0e08ff03e9f8faeeee00fef0f90302020bfaf9fef4fdfff901fdfdf40bf302000c040207faf50703f4fe06fbf900f2f5f202f4fcfffd110505fff6f402f7fdfafc01fcf2f1fa02feea020ef8f80506fdfffcf300f900f0f7fcfef4e8f0f7f7f510fe01f8fbfef6fcfafbfa0005f703f9edfd04e9f4ed07f8f7fefd01e8ff02f9fafe00fffbfd0bebe9f7ed07e0fafb02fff0041201faf7fe00f60cf4fdeef5fee4f4e8f6fdf602dbf1f80001fd07ff08ffeef7fbfff7f4fef909000dfbfa0300fcfd090b0afcfcf40a05bed7f0f6f4d8f906fe02e90beffaf60d0503e80502f2ce01dbfef6ddf8ffe9fad6f4f1f501150103e1faf00902d5f2fdf9fdf710e3fafb09ebfad8f902dbeefef0cf00fefff7f1f3fd0902f106fdfef0f1f4feda030cf6ebe2e9fb06070ede04fe0404faf9ea00ee01e0f1f5ec02edecfbe8fb05fd030af7eefeee0cfd04d90ce6f5feff04e5fdfaf506f7f7f4fc0705fff0f60105fbea05ec00eaf1fc05f300ee08f1f2fe0a0900d9d8f006fedefa050402f507e9f708f5ef0de5fc04f5e8fcf4edf800fb02f1f2f2e7f7eb06fbebf6f600fdef0b0bf501fef207000a00e303f709050500f5f6f7f5fcf4fdf21508e401eaf705fb0204fff5f4eafdf8fee909fa010efd010701f9070612f4fdfd05f8feecee0f0d09f1fefc0df506100500f7fb0cf9f903f907f9f6f3f604f3e9140302fe1708fcf9200a04020007f8faf6fb05fcf2fcf902fbf5fd030cf8f6fefb08ef0315eb0c0e1319040808f9080be3fefd0709f70403061316f7f90beb0b05f9fafd1907010600fef61eeefff90cf00c16eefeebf904fd0500fd10f7fbfefff100f8e401fddf0afd06ede9f8fcffe8fbff0106fdfff7f2f60ceaf9ecff00fdfffa0519fc02faf8faf700f8fcfff918f5fd0fee0002fffd03f8fcfafcdffffdf9020000fffbe8ed18f1050bebfaf30404f007f2f4f601fcf6ff03f4efe404fdfdfe05e9fefc000305fcfc07f7f901fe0afaf4fbeefcf0fbfefff9f20e04fcf8f903f5f0f9fde3f9f8e9f6f8fcf305f402e805fff500f102f9fae7fbf402ea04fefff6fffef9ffeb01f4fff7fefffff500fee3ec0200fef6e2f8f608f1f600f6fb06f2f9e903fefbfae909f9f4fef906f705fcf9f9fdfa05fbf7f905f30604f6f9f707f8fa0303f9fffd08f4f1030400fd100aefe10712fa04f8fce70705f7fe00ebf603f8dffa18f7f7030d02fbf80c060c010bf9f1f4f0f805efe4fc06e5e7faf807e3ff12f3e4fe0ffef50404fb15f6f9230900f60807f80b04f80bfa0807fd10f3ebf8fbf4f711ebfcfa04e1e31200faf805f8ff0df9f2fc04fbd8f2f6f5120016f5f8fdf100f4080201eff6fb09f6f71afaf914ffff000105fdfde60bfefd090500110bf9f60410fe130d0d050bfa0d06fc020500fee8fbed10040405f005fcfcfd0109fee80408fcfe00fd05faf4fafef102000105000700fc04ff0b10ff00f305f112f90af60ffbfa03ffe4fe01fd0509010405fbfe0cfbf7f3fefe031407fef7f9ff05000903f5fdfef806fbfcedf2f6f5eff60005f300f3f8fa0a0a020bfbe6fbfcf7effbecfe00e3ff0cf902ea0004f805f9fa12f9e8ef05fee0fd01fcfaf204f3070f03f0fcf3fe04ebef02f3eaff02f6fcf4eae500f8f904fb01f9ec05fde6fdfcf009ece600fd0003e7f6f4f80a00fce6fefdfcf203fdf70bf3eefe0bf7f4fafffe08e707040207ffea0bf1d7fbf7150812f4f1eff001030d04f30b07fd01f50507060600f6fd1907f8001401faf2fff5fbff0d02f6f0fb0d050efeea10fdeafbff132bff180dfddce0031f01e20bff0120e4fffef005ea0ffb0e04f010e70a081f0012f207f40d1cf004fe0b0cf00ce9faebef00f5f33b0210f7f7fc0cedfdfe040402ef060101fef0f9e4f90e04faf1fbfcff07f9fcf6fc090607f0fa1109ffde00f308f2060afb06fdf003f0ee0308fbfee1e6f00604e4fb00ff010c0ef9fd1e04ef01f507fdf2f2000cee01fc05f3f3e9e40f02f8000002fffd0903ee0607080a02f90104f51adafff6fe01f5f50204020cfbf509ee0e0cea01010004ff000cf1f2ebfaf70501dc03caeaed03f3c8fc0308fae516eff3f8faf9ededf604dedf05ccf8efe2ec06e103f102030cf7fcfb080df3f6f3fef3fff903f7f4efe9f6e8f7ee00c9f207f2edfdf3cce702fefbfbdbeffaffebe10de0fbeff4f7df01faf8e5ece0f7faf5fbddea10eaf8ec010704f0eedcfae6f7f8e8eaffe7050af50605f5f905effcfbeae9f2e4f90e0202d700f5030cfef4f90701040405eafafe02f502da0506fdfbfdf8050a06fbe0f9000cf8f3d9f5f506ede4ff02f217feff07f7070000e303f8eef4f900e4f1f8fdfb04e7f717fd010904f013fe0309ecf604f702f2f5fe011117f4fafef50dfa01f8000dfc0bfef500fe0cfbfee7fc04f40cf905e9f805000502e607dd0cf10cfbe20afcff00f1fafbfcfbf900fef002f9f6f8ffe3f2fff7fd03fa01f306fbf2f909fffbf9f1000e00d9f5f80ff9f806f0f7f203fb02eefd09040006f6e2fcfc0200f8ecf2fbfbfbf706f7f104f8fdf7fbf8f1fbeff6fc0202faf100f701f40206f600ff02fa02fcff06fcf6fcf6fc0305faf9ffef03fbf80002f5feeaf4ff0607fef90ceb05f9030805f60a02f901f9f1f20602fefd080af003effc2b010f010203040b0af9f0fafef50cfff9fff4fe0dfcea0107fef1000cf9fcf8fc01f701f90bfce90003ff00f4f503f6fbf5fcf3f6fffdfdf9f0f905fcf7f7fb02fcfa0afff901e7f8f600f4f9fe00fcfa05f5f6fefaf8fcfc080307fdf7fcf8f51501fe0c0bfe04f3042507fd0ef8f709ffee0414f8fc0901ff04e707021cf7fbfee8fcf1000dfbf6ec0f0dfafff005f6f10cfc0bf900031303f7fbfc01ebf3f400e6f8f3f70fe9e7fafdfb0509f5061001140103f3131a1406f8f4f70dfbf706fcf60c100aff12f7f6f61f0bf800fefdfc16fb03f6010d0602f00af50b02fef7f6f8f3ffe704f6ff00f0fdf3f7fd010903f6f305fef9fee60df5f409fdf404ebfcf804fe0108feebf5ed11ffe7fe030dfe030c04fd080df805e3ff06f8f604ece2fdfdfbfefff6fdf6fbed0607e9f9fa070402fe041217f2fa02010a06f40307fd08ff00edfffef8f30205e70e0b00fdf5fefb050004fefbfae0030203f3fdde00110400d1fff106ffe2e8f7fefc04f6f1ddfff5f8e302d0ffd4e9f8f8f1fbe802fdedfefdfb05e1e3f20a0dcffbf707e5f6fdedfb1f04fafad0fcfcecf201fce2def70205f2f5e6fbfef40304e8fef4f6fdecff1bfb0f12f110fcff04eb03e700f8f500e6f6ef06eef2f8fffe00e8f6eb06fdf10100fdf3f6daeefffed1fc00fc08f80208fcfe01fefff8fcf9fef506fffff9fdf9f805f908fafafb03f804020801faff000102fe03f601fff3f8fffbfcfefef8fe0bfbf8fbfefef8f205fefb03fc0404030a0600f6ff040002fefd00fb03f704fb0709fbff04f60603fe0400010501fffefd00fdfefefc04fbfdfbfff9fdfc00ff02fdfbfb0101fc06ff04ea00030301fefb0eff0f0501fef10615f6f212fbd7e7cbfaf8fdf20cf5f90ffd3cfbf628f90a0b161e13f80107fa1d06f7fae7f7eff9e9f3e7f9ecf6051102021cf00df7ef0103ffe3f90d010906f8f1f205f7fefe250ff6e7f7101ff318f40c060afcf9f60cfc0401f2fdffd4fef20f0307010002f41103f903270a05ebedf603f4fbfcfefcf806fdfb09fefb00fdfdfcf5f901f4ecfafc06fcfe07fe03f401fcfffefe03fcfa0507fcf5f50003fcfffefdfd00fdfb03ff010000fffdedfbf6f804fdfbfd02fffcfe05fd02f40201fcfcfef8effefafb00f8f7fef8f8f3f8fc00fbfdfbfaf7f9fef9fdf9fa00fdfc04faf7fdf6fffdfe03faf501fefefe03fccffd14f8f8f706ef0400eff7f6f701f506efdf07ff08e8fde1faf1f6fa03f706fb08fae700eb000de7eaf2f8f8d4fafd0c030700e70114fdef03dff7fceaf7f9f8eeeb00fbfc03effd07f5f8fc06f607f5f6fff502010716fcfafa00000eeb0c10ff0dff01f8ff07faf2f5fcf508ffe500f6f8f90003fcf6f8f6e50701fcea02cbfff2f1fdce0517f504fbf5f60cf2fd03f5e50400f5e008e1f5f2f2fdfbf80ee604f3f5f1f9f0ede4dcfd0e03d6ebf50103f304f5f1ee02fafbca00ffe2f206f3d1ed02060b07d6f2f8ffeff504c9f6f50001e504faedefe5e308f8fcf6c6fdfcf502ff05e2feed08f7f4ebee0404ddfbf0f302fa03f1fff0f7fef30206d5fbfbf8fbfef113fa0a09fee6fffbf8f2fef2ff170bfaddf9fee8ec01f3f707f3f902ebf6ed0b05040a100ff4ebf4ff13fa07070804e7f4fbfd0503f80b07e7e8040c01f1fa030bf9f7f50601fc0507ed05f0eb0fe9f411020aeff40dea010cfe0afaf604f100f6f7e3fcf30205e9ff07ecf707f903f70405f5f60b2e0df9fad904d8ed0af7f7d6fbed0201e7edf503f4ff08f9ed0603f2e0fde508e6e9f905f2f6ebf900e3f7f00005e9e4e9fa01cff8f608f2f3fbe6fef4f9ec01dbf7f2f4eff6e8d5f1040101f7e3f8faf50f00fcf0faf5ea00ee040dfc03f0ecfdf804f4dbf1fb0801f6f9f4feedfff3ff04f40cf8e4fae5f3f9fd02fffbe7efe80205f8d4f1b1f0f502f5bcf806f700dbfaed04f4effcf2e5edfddfd9fcd5fdebf4e9ffea09e7010ce8f7fbf3f6f8daed0dfff3f3f41106f602c0f4de02fa02c2f212e5f206f6c0e301f8fff4d1e8e8f10bf007d2edf4e7fce8fdf1e9e7deddf7f8e1fcd7ff05edfffefdfd02d3ffd901f0e6ececd0fddff70605080009fd08f0f404fecffe08f8f30209f004f90406f8f400fe00f3fff9f306f306fefbf404fffefd0402050304fdf60000fc04f1f1f50701f001090bfcff06ff04110d0901fafbfbf30103ecfaf505ff0202020afcf9f9ff01f603f4fa0c0903fd1b03ff03fb000206fb0001fe0306f50300060006fe0006fe05f0f8fc0ffafcfffb05fd07f7fa0105fafcf8e904fbfbf9fdf9f9fbfbfeeefc00fefc06f100fcedf7fd01fdf4edf3fbf0f805fd03f0fc01f7f209edfdff08f7f9fefdf4f3faed00fef7f9fc01f1ffecf408fc01e2faf902ffedfdfef805fd060ef5f6fb02e6fffbf9f204e8fb0705f8ff01fbfefdfaf7fcfbf001f401fc0004fc0dff00f5f2fd02f801f1f9f7f900faf9fbed00fffdfaf0fbf8fdfffbeef1fbfef6fffff1fef503eb01e3fbeffcf6fd02fafe02fce6f7fbfe00e3eaf10200defb060205f80af2040604f107e4f9f8f0e002f0e9f5030500faff04fbfb00f903eff6eef900fb01000503f8f6f70108f6f5faf50409fff6f8f3f2fdf1fcf4eb0905f5fdeaf8f3fb0204fdf1f3e9f502f6e3ff),
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
    .actor_error_o(error_actor_enc3_extra_pointwise)
  );
  logic error_actor_context1_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(9216'hc6ff24db141da7e6090f0e0600e6fcf8f3f41108f9f00fe50804effd2b1fe8ef05fc150be30508f3f209f4fb0d0403fefef81311184aff1015f0f8e2f40910fdf80bf2edf0f50aff010a02080205f2010420fb250601f1110b24ead8c714050901081106020df5e403fb02061ad31ce7d4f4290c2fdb05e7fdfde911190af8010c12e9f90808fd07dae0190e1cd8f8d72b211b140d19131330260b1a14e31ce7ff14e7ff11d72004c01e14def60d1107f906141e261a321fe313f6ec0325d8040bf710220e2a0bf0f8eaf5edee0400f40c080106e9eb06fcf6f8e612df105f3029fedc0829f61aeadae8dde7ea1dfddfd7da08c6b4df0f11151328033c181909ea15f8e2faf5ed0afd010305f9fe1be4fb0cf9f515f3032cec0023e2eaf4efee011923e90afadc060a00eaf90d0412fae1eb201a2301032105051e300c29f3ff0fcee1c3faf5fb01e3f91afc040ffdf31cf11c0ed8f2f7e310151025e5eef7f5e5f00dff04fdf300e60bb70828eafb00d1e5f3f912fa1ef8ff0b3a262f2c032f4200ffdae8e50ff7f11a1a0d2902f826ea0225fae41f22161cce1d17100ff3d5ee20ec250fe2e1fe0bf1e60103f411f01dfffa09ee1303f704eef5fce80cfdfe0af91a150cfd05e2eceeebf20013150305fdf4e30d0e11cee6ddc000ca101407060afe11ec12effb06071212ebf9dcf7f5e90e120ef50bedece206ebdd10e4141df0f0fd0e0def040112e4f2efe60bd4c9ddb81dfd070301ec170be3eff90617f30e13e5de1c192608e00c240f181e242e12fbfe0c151ae6d8f80ff3e1262628ef0609fb0f35f003290209f0371f11e5cad2cc15e6ee2d09d611ef22f5e70101de1a14e514ff1c05f41a19f4fe01f4010efbf91803122c031016e2e4e9ede913ec0836effc4514e609030be4f220181845e1f3e7f3ff220f0cf11cedfe1000072b0af3230c19f4f0f5ef011611f3d61305ea0beb15f1e7fb160112072915190704f1e9011c1f1c47e648e1da0ff1f51f26011c1edd2030ff201101180408faf605e40c05faeefcfa0401ebfe0205e8ebeff4f8e90e0df0ea02f7f8f0fb130b0bebd4ed152716f6f41e1df9212d1128fff7f21dee1d2e301af5fef801051cef080c17fc30f1ed0822fb0d0a05fa080dfaf3f51236f42416e8f313fd0129071df3d4e9251a06131712dadae7f203fcf7dde1161fecf2cdd137eef008def91adeeff501fe04fff6f207f5310f1bfed5ce01f2d9eeea020601150afd2c0dfef60b0817fffefa01efee17f0ef1c0de9d1dde3e8e8ead9dae940094e06e6e5ecfff1060405fb08f6fbe2f315f72121cffff6ebed0203fa14e7fa711342050f14f6f9fbeedadafb1a2df2ff11e7fd07cee519bbee17d6dc1b330e37f5e9270cf70f130f111cf41afefafb201e1f08f808f6f1ecf00aeaeded050efd0818090e03e606fbed0a380439f2e612e9fb08341cf8fe03120717fef3f1f2050b0419140a1824f0fbf4c9201bcf36071b20080d24070ff80200faf30d0104f30c1b21d7e0cbe8e8f11504230cf608f6e70b19e1e312f7dde3df9a041efcf7f91802deea07f107ff0009fcfef726292cfbf4f42a18071d0a1e11f00d1705140e0ee4f0fff6fd04f9),
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
    .actor_error_o(error_actor_context1_depthwise)
  );
  logic error_actor_context1_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(131072'hf0ff06fff8f6fdfff4f60dfdfff8f8f4fe04feeff0e9f707f9f50519f7f2f703f9fcfae1fa090e05f2fb03f9f0ebf901f0fe00f2f0fdf5f2f4fcf50001f8ebfbfff908f0fcf903e7ec08f804140ceaebe2ebf8eef8f0ffe901ecfcefe6e4f2fefeeefa11effef0f8f8f5f9f9faf402f2fafef2080501f00ef6fd080402f4f302c605fbf9030fd4dff6e6f9eb16f6ffc8da20e3ebf71ff7f91dfcef3a12def8fadbfe0ab5fef0f6f9e6edf0d4d5ebd107eff3dfbfc3fef7feef07f5e1f708f4deebf1c5fdf3fff21a0ef9ee0d011e21e713dceef6fef0d2f0fe1df0b8cce5e2dcfbe9e8f9defde104ed09f4ccebecf2f6ef00cff201c8fc04f1d1d1f7f90005fde904fcf7f1f6f9f706ee05fbe3f304f7f2ed010310f9fbfeef0203e9f5070808f903fa0bfde8fefdefecfaff04df0afaf9fbf1fafdfa0ef7f9f904faf003faf2fde3f3effe03f7f2eaf802fa05fcf2fafdebfaeef802f3f600fbfff601f2eaf80102f902f800fcfdf5f7fff6f7f6f2e4fef70afff604ecfdedf4f703f8f6effc15fcfb15fe18f9f5fd13f60addf000f30becf504fbe4030424f8f5d6e7f31af813fd0be1fb05010f0c032bf300e6080209fa0202e2170cf7ef0ffb07f511e8fa0deff70618fe0aec0ff006020decfe0be21511f900f5e1d70702fa0a0607f41400f2f7fc01fb18f4011cd7100217fa0c05e604090806edfaea08f61afbe9f4010409051303fd0c00f90600faedfefbf90ef901070c000afdfb16fce3ef0004fd1201fbea02ff01fd090a1a0d0be412fd03031512f90307011c03fcff09f5f8020cf0fd06090a06ebf30403080ff7f002f8020500fbf0f305f9e605fd0f0c130600fa15f9feff07fffff1fa222106fbf803f81701fef7fafff30bf30dfcebf2fee1f300ecfffced02fff3f2e41afa00e4ec0ee9e8ee01fa020afb0a07f3faf2ede5ef0bc0f3f3f807ea05f60fe2fbeb01f404e4fcdef4f4f7f1fe02e9f1fef1e305e6ea0c01f1fa0110f5fd0df4fb12f1f7f40a0302f8f3f3fc0109e8e1ede4f406eff701e1faeefbf8f827f201d8f0fe05f5d6f303f3f304f404e8eef80004fa0c15010c02100f000618ff04ff07051229ed061810effc06f0150ce7ee040a09180be223fa03210e220a0e0a1604320811fa29290e040c050a051903ffda18f212021e06fbfb1101fe00020d000af425e21b17f3fc001f0503edf313242c1010fff808070fff2d0524f5f71d090f070ef7fa1f0df81ffbf614242b0f0b19f4fef7fe0205fae403f50307fef9ecfbf9f9fcfb0302f70000fddbfef3f9faff05ec0cfefbf0fdf701f7edeaf9fdfde6ea05f802f0000600f8fe07ffeff7f7f1faf9eeecfff8fdf4f5e7f1f1fcfcf8f300eaf90006f5f8fbeef7faf9fdf9f6e502f3faf7fef506fefbfbf8de00fefbf6fae500fc07f8fefbeb0108f800f901f8e80300f70e0b0413f7f802121602adf3050c00e4fd0d28fff4091bf302faf2f606fb15eb05d00a0b02fa1b082201d6f10301fd05fe03ec08fffaee0aecf9fd0cf5da190514061305020803fc0c0a01e81007fb060a11000ceff30cfdfee405fdff11fcfaf70bf5fffd00f60e0801220ae906ffed02f1fa0af3eafef81dfa02eaf106ebfff5f9fbbc0500f7f6dceae206f0f0f7f5e8fed7e8f806e1e4f6cff2ff0303ececf3defbf1f5fee9ec01f9f9dee50502f8f807e7ff02fcff00fc0400f7dcf1f600f1f1fcf5fbd4c2f6f6f9ff01c3f0f10402fe02efec08fee902eff7dcfdedf7fb05fafc07eaf9fed5e2f3ebf4f9d304e4e2fd04ecec0409fffcfaf9f7cf0701f6f9f804e5fefbf1feedfcfbf3fdebf6fafdfaf8f3fff9cf0b14d90fff0a0a0a19feebfe0103fef7f803fe0cdf130317fcfffbf9fdf906f4010500f809e60e0612fa08fefff3e9eced02fe09f2db01f90405e6fff2f6f9f6f305fe10fbfb09fafc00020efa0e0300e3ebf700f8ffe7fef0ef07f7fffa07050307fa06f4db090403f5fc0ebb04fffce7e505270601ec030bec00bc0704fac30a0fc210f1fe30ec1a01fbff1209f402eafdf117d304f809f7f302db02f20fe6f6060606f4d0fae720e11610fdfee8c2000be201e5b95912f30004000c0109020df1f52311091501fefbf231f8460609b9d5f4ea01fec9fbea0b01e507e2071207020000fab501e51306ebf701fbf9f40209fcfcfcff11f9110400f1fafafd09faf9f91301f4e8fbf5030108f7f9f6f6e5fcfde801ec04f9fdfffa05fef4f906fcfc01f6f121f3f9fafafbfaeefff907fdf600f00807030ff40005fa05f4ff0111ff0af5fcfe0000f90206fdfff7ee0910f3f706e7fd0cfe05f1faf2060bff04f0f5fefdfafafb01e8f8e6f6e9f8fd00f70102f5f9f9f7140b050af70704f9e50c08f0e80910ff0309fd0802f60cf7fe02fdf702e814fdfc080a0e16040e03170009fcf5fdf4090409fd0903f8fafbf002fdfd180edefd050802fcff030f12fcf5060c0703070303effcf8fe03f5ff0adc040ffdf4fdf9fe0114070dfcef02130b030700fcf4031706020008f2080403f71614f9110816fffef8faf7f5f401e3e312f114fe1102f203ea1aee1306f9f4daecf0190cf909fb07f6f72b050504cd000b090cf9170eeffcfa08f70703f7f1ff0800fdf900fd07ff01fcfe15050af5f4f30e06060b13fe19f0ee0afd05f1faebf205d4fe090afd12f80200182e0a19f308fafefe0df8f7f3f807f2bb01fd0402db0fb8f709faf3f7eafdd4e91606c7edeec5f4fc09fbfaf3fade0b0709f2e8d7f71003efe6f4f106eef2ecfdfbfceafe07ff12ebf0fbeee9fef2ff08e7c9c305f5f8efe5d116f4fd01fe0e1ad80b02ebfb0a0c10f911f703f1ec1e02f20217debaf5dff905c00ef0dc04e900e6fb00ef060cfbe9c311fcfffd0f0aef07000508db0ac9f400ea03f9fdf606f20807db0e11de090a05e8180cfff60203fcf60ded09ef00e7080409fd110a07020906150009f9ff09ee031706070717f6fecee0e90eeff6fdd927020f07f51003f70503f006ee171013fe00f4000007fb37fe10e9dc16141bf3eafbee05fff4fbe608070507ff01ffd109f2fd00f10000eefcff0a06fd1606ffe8e50aef02e505ebfef5f5fc3dff06f9fcdbf10c1501f3fff7fafce800ee02d900f402f4e80e01e9fad80904f7020a15f9f6eff700f103fa10f612070ffbf902f717f7f406020dc2f5fa0dfcfcf2de07f0ff12f0fee100eb05f7fc1ad7e3e814ee030ed7f9f9f2090006f8f1e1fef40b05e30602000112f8f6fcf1d7f51cf006e6f202e4f8f61bfaff0203eefefefeebf9e5fb09d808f0f8fde5faee06daf4ce0203fbf3eaf5fef0f101f7faf8fcf501d3fff9e80203eb04070efdfb01e10004f30ff8070ffee5cbe7060df9e2c600def0fdf8fffced00eff7ed0d01f8f8e500070200f7fdfcebe408e7f2f10200ea11fd02fafb1403e40809f2f7ef10e20606ef0cf9fe03eee80205e8ef16f30bfb0b010d07fef409f3080006e800f5fbe21cfd04080b0ffffcfc04000500f9fefbf0f5f9f7f8f507ef02f6daf900f806f0e84cfcf7fbecfd00f712ece6fafd0914fb060af4030609fe29041304f8070e20f7e507f41b06fa01eeff06050408011cfb020706051104fafdfd0500010908fe00fbfff20a001408fd03f10e08efeb0807fd0409010007f400ff11fbf6f0fbe6f306fe0a0ffafb04010304fcfcf9fcf7e9080df9f80bffff13fdfa170300ef0df00bf6fb040e0ff401fefffe050011fa140003f80e0c010305fdfcf8f6070afffeef03f21401f4f7ea0108f706fdfd02f203f7fe0af4f710f1f505f4cae917ecfce0e111f0e6041cfffefc02f704fbfdedf7e8fa08cb0deff7f7e202ef07e2e6e203fcfdf3deeef7faf0f9f5f7f9f712f6e7fefaeb060ee2fefb08f3e811050306f006fe01f003e5ceeaf911fef1e5f6d8fcfd03f707e6fbf009f10803f306d301fffe030103fcf8fc0debeceaf5fdef02f8e2f3f6f5fffbfefd00fdfaf6f3f9010600faf6ffecf3fbfbfbf2f8f903fb00f5f3fd02fa04f203fdf7f104030403ee00fafd01eff80000fc0300f9fd05fa06faf6f4fd00fcfefaf4fd01fc11fffef6f6fcfdfbf6fc06f801f9f8f9faeef404020103fef1edfcfafd00fdeeedfdf6fdfa03f0ef00f9f500fc01f1f7f8fdfcf802f3eef5f2f5b502fa0000d30fe805ffebeeedeafdb7e502fcc1f5f2baedf802eff40101d2f9fbfaffebdbfaf5f6d1f7fd04fb01fee605faff0600f9f4f7dad9f7f409eb020401f4ccbfe9efeff3e9bb05e702fff201f6f611fce4fdf9f3e6fdea02eef9f90605e6f5f9ced9f7fa01fbc8fce0e7fcf5e9ebfbf5f7f503feddb500daf7f7f6f7f7ff02f6f3fef6e20202e9fbf9f0feedf3f5fef1eefaece703fd08f4fdfdf508f201feeef1030bf9e9f7f9fbfafcf8f8fffd0300fdfe00fae4f1f802e5fbf900fefee4fb04fc01f504ecf2f2fafcfcf6f9eefcfeeafaeff0f3f908fff4fee9fb03ff05f4e9ef03f2f9f7e8fb04f0fe0007fd05fdfcf2f9faf7eafbfee0e7e9019a04f8fbe2b5fbfefeffcfe6f4d3f1c4ff00f7a60bf6cbe5ecf40ee6f7dfea0905f0f1eaeff3efecc2effbfe04fff4d9ee01f81aeff8e4e5d7cc03da1be5fef3edf4bbbfe5e3f8ebebaf23d6da00f5eff9f904f9e0f7d809eae4eaf6f60aed0e08f9f7f1dfd0faf8fbedb7eff1ddf1efecd8f6ebf5ff0eefdae4f2e2f2fbedfa01f6ed01e7edfc19f20ad4d20509ebdb0d1cfc0ffffce402e7d7f6edebfff009f6f7e9ecf8e3e5d5efd9f8f6f700f702f9f8f6e1fafcfd022d05c6fee4ebee09e8f8f3f708ef04f404f50cf8fdfc00f3ffbdf6fa03eb08daffeedefa0101ffedfee5f8fa2e04eaee00f2f704e9eaefe301f700e1ecf705f5e4f4f7fc0600fbe70fe9fff50f2f030405fa1806cce80a0ed7e60014ed0b1cdf0200f8f0f300d3fafb031316161925d8fb1902f809f0f40f06e7faf0f4ed03fbf1e1f1000501f3ff13f617fe1ef708050d23eee4dfe8f2e5e501f213eaefdcfedfe600fcfc0203e005f1fbe0ff2612fde8fb0a041afef80cfffa00f3ecf2ecfcfb100504f4080d02fb0a01fcfaecf721eef7e919fcf60b1415fdf9f6fceef3e8fcfd0612fa12f605faf7f9ee141c19d8d0ff03fffffa020afaf7fafffbeffaf719e40a0014faedf5faf70c03f6fcf8ff03f1f519f7f916f5fee7090f0efaeb00f307fe040017fcfcfcdf1009060a0611eaf5fefef904fefbf1fb0ef2f000fdffe70cfc13ed121bfa0c09000819072ae305001eeedf2bfe2dc7fe1334e9f1b7dcff09f844ed0def160a0ef50b07341d12f60ee812151c17fe0afcf2d51df7dbfceae8e50bf819000f01f60cf2022906f1d40921f50f150c01ef00030ce602e408191d22f500f90dd3fa1e122e24e62b0f260309f3de3c11f610fb04003809f509f2e9110903fe000cf602fc03fc0cfdf603fe1516fd03f904fdef01f413fef6f1fe07feee05fcf50407fe0106fd1201fffb03feff00ff080404fffe10fff9fd0009ef1008fcfbfa04ff0210fffb01fe0d09f8fcf6ff0501fafe080705fd05fef8f9011005020809fcfd020303ec09112406fa0000fe0d03faed01fafe19f306020404fef9fb040400b50df6f1eee5f3f60c08f91b09e70ecbf10300cc07f3c00d020a11f6f7f0ee022005fae2f4edfaf1d6fafd12fe0dfc0304f20426f40c0ef9fdde1df30ff6edf8f804cecdfaf6f902e9c912faf5010203f2f7fb08d6ee010bf1ecfb00ff0ff806fcf9fa00c7e50df8f706c40622f40bebf0f70208090e00fddaf4feed04f900fee1fa00f3f6f605f5f7feecf9fcf201f5f504ffe4e1f8ceeafb05eff8f4fde402020406e8e6fffa03e3f2ff0104f6fbf4fdef00f6ffeff701f5ddf7f3f4faf2020af6e1e2f5effafae8e0f501f901fcf5fdf0f6fbedff07faebedf4fef2f8f50606f701f9e3f300e2fefdcf00ebf5f6fef7f002fffef70afbf2cf07f6f3000bfef806fdfc0e0004eafffdeb13eeff0bfefa04fde10511d9fbfbfeff000dff02fef7000000ecf7fd01db0301fe090202fa0707fe0f0809f8fcf8eaff0503f205000511fde2ff060609fddd10fbfdfdfc0202fd03f8f6fef70bf6fe0003fb03fd0503fd03f9f6f2071204f5e5fff5070bf8f7f3fc0100ec07fa07effef5f7f709feec0406fd13f8f4f0fff9fcebebebf8e2ebfdf8e3dc04ebfdfceff302f5fefd01010df5e2d6f801fdfae2ff05fbfbee0afafe01edf6e9e702f2e8f203f6ede8f5f3e9e9d7f8eef6fdf7edfdf5fa0508ee01f5f7f9f4fcf7ee0fe5edfe05eaeafa05e1effadbe900e10206ebf308e102f6ff15fbfd03f7ed00f7fffffdfdfc00f702f90902fd010017feffedef11e90de001f8f8f0efe9050a0cf5f9e205080901fa030af7f5e3fef501eaff0100f9e3fcf7fc0000fe03f50603070af3fde9f9f8fdf80fff080afaf80b02ff0f04f40d050ee0fbf51f04f9f1f4fdebf50afe1bed01e4f2f9f70af5ecf10ee40414eef205f11405ffec00f9ffe70901dc01ee03f1e2fc11f9fdf401fc0dfdfeebdadff4f0ecebfde5eeead808f8ec02e9e4eefdfa0105efede2dbf6f5f2c808eef8f1f704fc0bf4f5f9fe0102e6f7ebeae1f4ebe909f2e5e1fb01fdfc00f1f5edfbf62af506e7e802f3fdf4f8f8e0f6f919f9edee01eff708db04e9e5ff0ae70311ddee0eed0efe1201f5ecf5fbf40af6f9f9f1f9d9fafbf8fbd0f0f5f7fbeff502e8fcdeeb0bfbecf2ece3fa01f310f7f402eef4f4fdf7fcf0f9fc01d8f8fa02f900fef2f4010200f9f9fdea0be7f3f80becf8fef1ffecd1fcf4fef3fcd5eaf5ee02f9f9fc0309fae8fae6ffdefbf5fbf800f80506f20102f4e7e9fefdf6e9fae1eef9f9f30401f8f8f4fcfaebeb020f140af1eef8ec04fff1020319f606f2d90c0f05f1e40307f5ed0bf401fd0800fc05f049f706080804f6f10f1617f70afbf1fb052501fafaca001ef109e83901edea04f0ff02e6fb08f3f9fae3e514fbf1ffffff041c0bfbf1ff0121f61316fefb19e4130a04f2f40fecf710e8eb0c0bfe161104fa0f2b06fdf60afc02f710fa0df3fc0503f3090800fcf3f6ec00fe0c03fc06fdfd0302f9dd1605e9fffc0b060203fef8fff9fefd1509e9f70cf612ff0709f70bff0504fe190206fb04ec011911fb0a10020200f6fb0c00021803e2fcfd050cf9ff001221fa03fe230803120e000002fdfcfb000df8f201111cfcfaf1fd0606fcfe06eefe05130d0bfa00f003f52cfdf802f9f9fc02ff00031805fef9df05f7fbd8e30a0205f8fe0f03f4fe00f605082c03010b00dfece720fa1cea08f905fb111ffdfcfcfb0107f706f547f8ddf0dfefeffdff08fb0fee0df3001dfa10f8edff060427fc03040912f004e3ec04fef60bfe00e2ff06fee703f1f90dfe0310fcf3fa0b180706f8f3f902f0fe05fbfb0902fc12f7fb0df0f9f402f70bfa2a14ea17161ef4000200fe28ff150af1e6f4febe08050502fb073101e7faef0800f5eefcdefe0a01f70cf106fd02f00a0b1a03021105feff1809fe15ed0af6e401fb03f708e8f4f61f06f8e60febf6f1fa0511fa00fef51ff30605fa14e6f6eaf801f7f20bdfdafcf6fde0f601f6f50214150904f5e7100202e9f207e40bfbee1ffeec0c1502ff14f72508effd091c0d06fe03eafa0bf71c07eafa0feaf00407fdfd10f1fcfa04051f0c080cfee30d0df5f6001911040ff1ce0e0615f912f610f006020000fc020000150e010f04f408f7ed1e09fffa121208f0dfff1e0ff8ebfcf62a02fc06ee0005f9fe06ff0cde040511111508faff13fc020307ecfe021213f20a080e000605f81b12f4000cfd010c12f6f50af90dfe0c1029ff1be812f807041805f2050ef82805fdfbf5e6eb12050af312000804faff1f06051014df18f0fe070605f70c2800ea0b1d1a0df61705ea19f50403210407fc021f2419f80401f5380f06f8f5fb040ef8070b0301ff03ed080bfcf0ff02f905f70dedfcfdf008fa0700f3000cfceb0306f3f9f70b06080003f60503fef9fbf600fe0ce20a0717030607fa0705fe0d05fbfa03f4f4fc02fafa0c060413f3f0f906fcfff7e62901fd06fa02f7f7fff4f4fbff0c03f519fa0307000503200200eeeffc050af3ef00f80703f607f7ff0201e902fd0401060b0801e5faf900fe0904feeb1b0004e7e806ebf7db0af401f1e6fb01f805eefde1fd001204030105fbf1e6f7f7feea06eefaecec00f902fd0105fcf4030e35f3ee06f409fbfcf205011401020cfd00ef2305f211fd080603061901f2eeeb13f5010c070ef200e1f9fd020afef1f708e7fb24fcf1f8e91708f404f0e105f21c04f618091b0800fe05fefde8f0f8fa00ef02ec0cfb16f40df5ea11fddb0206fff30809fdf702f8f70615ff08fa04f71c040002f3fc0a0106fe1ffb01ffff04e5091202fb101901f800fb0302fffe08f507f80c03f5f20520021008fff7130dff0604f5100603fdf300fafd0a0229f5f9fb06fa19050805e4f7fafc0d01ffeef2faf8f7f1fff8e810fef2fe08f6f50b0a1520f7000a0b05f1f0d81421efddf106f6150df10f0d0c14fb250e040808fa1d020209fe131e0602002ef914eeffe4fd2411121410fdfb25ffe70c0e040b10e3070bfa17100113350904d8fef92709110901131402050712010cf520122202f5fd05ff2f120c0df20209261510fd2bf4fe06011302f9061306fb20fe12ef0c030b220104fb0ff30d0df20118faf3fa05ff29f0fdefff0d0a0905012ef00dfd1efc0803ef0ffb090007fb030404fa00eb0cfd070f100408f0e5ef0403fb05f9e524f013fee600f8fc1212f1fe0e22090d08fefbfcf6fd031a091909f81b041e0901f7f324ff03120001ff140cfe040bf4080302fa1500e10e04f0e6d00be91702f60bf8f2fdd7fb0e09fff30be7e9fcfeeb0cff01e409010100fcf3f7f9f3f60b0006f2fcf2f8f6fd06ed080307faeaf7f20701f3f7ed01f5edc6deececddfdda25f1e4f9e0eb08fa08fff7ecfa0f1004fdf800030d0a06f3f20209de04f50df2e6fdebf200f8fef1020e0e070802def1021afaf9f600e5f606faede1e5bcf3fedcf9fdee03d3f00dfad6e904cef4f4edfdd9f200e7f1e6f8f5e5d3f706fcdbf40ced020af9f0fa07fbf5fcf9f6fce8e2e907e2e6f5f4f7edc7f8f2f9ed0512d300dbf50a06f502ebec00bbec0eef0af00b08fff9ede80102f80bd9d5e2f8e4fcd80500d402fde7f706141bdcf1f8f3c3fa0c11f00910cd1eeef6f0f902fb0e00f400ede7fbd2daf902dc0615d0c8fe07f50b17f50507050b020fcdedef1ae1230afb0206f41e00f10902fc0d0e0ee9e200000f0d02f80a06d0b50101ee1cf4d520e1f2fc0c0b0efefbfc02fb1109060d070a03f7e90708f6010fccef08e6ff00d3f802f405e7e9f8052d0d0e0204f2e7fef0f3ffde0af300fffe100104fb02fee6e019e3fac0eded01eff3fd18f502fef9cb04050bfffd0e01e9e2f300f108e709ec06f3f604eff1fae80705f602fa14e7f0e8eff5f6f101f0edfcfd0ae7fdf60304ecfc08fd07e4e400f80ae1dcdf04edff07f1e6ef02ecfcebf404e7f3ec12dc0411d5ff08f5170705f3f1f303ebf805e1f3f5f600d0fef3fdefd504dc060de1fdf5f506b8ecf9fcc9e2efc8e3f8f5f213ecfcbefef2fff5eddf030a05bbea03fcfbfc00d903f7f6f60102f9f7e4e0fbf9d7f301eaf5eccebe0304f2f7f0c3daf1f706ecf5f7eefe08d2efe7deecf61605f6e4f0e505f2effae9c409dcf9fcb600b8da0effe5f0fcf3e7eb02f3f5e3ee2cff0df6faf4070bfb02f10df813f41413050001fbfd08fbe50811e70fed080d101706040c0409031600031039f821f30d01090bf302f009f70219070a0ff31c08130c0e0707090beaf609f80cf9e424ec0003f8fd0502000210f3070e1d281c0102fc060ffe04fa08f9fe0d000c02f8f9130b0efd03f706070d0716060b11082906fe0a08d11203f308f41c00f909f6f7ffe80ef5f5fcfddbeb0df9f70208f60cffec1afd0a101502e8f8fb03eaf7f80007f40614f808ee0c1303fd0ae406fbec0202fb021600e9ddf61001ef03e300e70df710e402070dfdfbff0f0e040ae0fe091ff1260312001801fa02060816c1f903ff02fef703fb0003090a0afed8fbe3f7f3eaf4b704effcf0d2f6ebf5f9ebe0f2e0f8c5fa0304b908fdc307fcf30ce8f5e6e0fd0ceef3edd6f2f0f4c4f6f8f80e02f6e9ff0af6f8ffeff6f5e2d7f9ecfde300f9f6fec4b6e4e9efeaf1bf03e4edfbe5ecfce3f9f1d8fbf305dce9f3fb09ebeb1807f4f4edcadae9eff4f9bd00e6dff0e9e6d4f3e6eb0008f5d9bbe8f200fefefaebf7030304f9f8d1fd04ffe6f1f6fb0a030a01eb1511d30803fcfef303fdfe00f4fa00fae5fc0004e50c010a0a03ff01020efc05f006fe00f4f0f61102fefbff00f9fbedf6050604f5de0afc05ff0a06fde600f3f2fb0802fb020e01f3070f01fcf2f817f504030d03f3e908fd0904f603fefe0704f805feecdc010efae1e4f5380609000aeae605000af9f202fdfadf00fcf02ff7ff0eeef7ffe1f8f5f4000beef600fefbc91aecfed7fafffafee9f9efecf3ddf302f805ff0e0513e1f22cfb0300ea2026e51e0a18140ffe1bfe11eefefef1f0f9021e020ee2fd0aed100f0ef810cef046f3dbfdf8f0f6f6e6db0202fd0401fbf8e402022ccef90605000d04030300ff130102ef02fa0410ef0e040efaf1fce10a0fdf081022f50405f3f4fe0df4fc092414fb0bf61afaef03040ffb09f40d19fb070bf8f9dc20080303060307030a06f209001806f20af206020903f9182d11eef70513fd0c0603fb0aff19040509ffeb151b20f903fafcf02a08f119fb03000205f60af6ee04090ff20e010bfc0af7f3270b0807fe22dcee0a00eddd0110eed3f1f306e800e21103ee36040c14f0eaf4e809fe02e80102fffc112b01fef3d9fe0d0df8fcfeea0bdff4e3ef02e7f5f6fdeafde8e805f8f6fff2fdf80beadefbf8f81e1401f7f20119e00809fa04f00edadc18ddfe0b11f219e7ee04271eea12fb09f801e80704df2607fde017e9041714fef4fbeb0bd8fceefefa142edafb4ee9ed1dd30ff80119ef05d117d9edf7dd2233f7bbf9f505ef04e40cd9feeceee3eff8f6fdd4e6da1a0afffa040d0a141408e4010f201ddffcfb01e9f6ecf4e02402f6fee4e5dbf1f6f1dc21e700fa13f619e809e800ecf7ffeaf51a01e2fa16eaeae4e410fceefbee0ff5fffffb03fd00fff4ee0407f9fefffefb06eae60301fee7f504f5f3fbf606ec02e6f5fe00dd02e6f6f901f5f801000df2f1fcf8fe02f5fc0ef9f9f300f8f8eeedecefeb08e4e801f8f4f8edf2fcf2f6010a0af0f905fff4fdfce502f7edf7f1f500edfbf6fefff2e4fbf1f0fefd03fbe506f201fc031df50e03f8fdfcfa00f201f106f519f504f6e6010002fc0e26fdf91910f818f5e9120bd40810fbf83309f7fafcfcfafe1e0a1bfc1bf610fa030d05100708f4082700021a05fbf4331a031906010b0f03f20cfd011013ef0c0ffe070b0ffd192209eaf61e281b051205f515001c0521090405f12d25fbf1fa03ef3dfe08f9eafc0bf71f100610ec00e6e1f3f5f621ea070af109f6f8fb0101fefeea01ee01060702fa0412f2fffb0bfceffeeb080f0906ecf6e3f2e508d20bf5faedfef9fbfff8e1fef7e900f8fbe304e9ed03fc05f3e704f1f1fff60b0ce90106fceffcf4ecefe9f3fdf1ebfdea020802f2dff300d3e40810f9e6f4f30601f8faeb02f6f0f7f20903f1fc01e9f1f8edf6010e0af5faf9fbf5010fe5fb00fd2003f9f71900fe05f31600f4f908fe001809fbf504f302feeaf11610e3dbfffe04ff1605faf705020a07ff0a08000af4f7fdff03050504e2ee0607001508f301e20c06fd00f6eef300e8faf202e1fa0b02f715f9fd051102f8f401081105fff1faf81bfafcff0009000df405fdf8fb07fc0504fbf303fbfcf301f3f00cfafcf3e613ec01f81509fb00fdf1021cf5fdf5e90803f904f6effdfbfb0707ec02eaff01fbeaf4faf404ff0101f30006050c0c0802eef401f8011a0fff0200fcfa07fd1200f7fffc00e70a011109e8f1f0f1f4f8050307f90202f7f401fcf7fcee08fffc07f202f5ef1513f8fb02f6060107f927060e091cd90ef805f7e7f31f17011420fcf1031ffaf4f7ae241cf9130329012608fc01fb0ff7fe2a1010ee17043806fbfb060f0600190c34fd18ffffe9fc5e1f3e161805fe22eefe0e01dd210aeb09041202faff051825f711fa0d130017f206dc2a103502073a0beb15212eea01010214090e0d08f407fc0c2902fc0b07efe404ff03ffd0f6030502f5ffde0303f0ffefdffbd6e2f8fcf1ee06d106fdfee8f2f8effa0a0506fae4de0108f9f0e402f2ffe5010de7f004edfa0e01130bfeebe1feecf4fafefdb9bbf8f600f7fde501f8f1fd16fe0af5f9faf7fefbeefdf6e8ff12f6e5fd02e6f90fd9d9ecf2f808d80112eafaf5ea050412fc11f509f3d70302f4fbf6fbe2f9fafb0ef5fbd9f0f8ee1deeee0efdf6eefad41d06e5f7f205fdf705010203faf5fbeef4f9f711e511010405f903f002f9f807f60403faebe50704ecfa10fafa13eae6e904f5fd00d5f7f30701ea0710faf2fbe8fafd06f8ed11fafe0cf504fdfa0101d4e7f4f3f7f7e203e8fd170200f6fa04fcfd05fc03f2040602eb0701d9fc00f6f2e8f505e9fef711e6f405f9fdf5f4d01505e804f7ff0af916020507ef04fc0cf3f7fbfae1050007f1fc01f6f9fa0605f608fff9f1e007fcfcf40708f01ef9f4f4fa170dffc902f4f6fdfefef504fefcfffff20efbfb06ff00050a070402f3e8d600fa1007edf4ff05f4090503ebf4fc09f304f405f10afbf90afdf506fd0103040400fcfef9fafe08fdf6fc10fd02fdfff901f6fbfa0000fff20501fb04fc00faf60c04f701fb050301050afefefcf7fff301ff10030308fefe0501fd0804fafa0502fb03fa0107060304faf5f5f5090202f704f0fc0600f005f9f8030cfb0efd0c10f70afa06fefd001002fd0afb07ebf705ff05fffdf11406f0f300f6000606fffb03ecf9e8eff8fcfaf81b0509f900fef2fcfffd000ef008e3fefbf6f4fc02f1f1ecfcf404fc0af801e4fc02eef4faee0205f7e8e70f04f603f9fc030bfdfbf3020504f4f2fd070a01fff9ffeffff803ede6fde40900fdf20bfa00ee02ebf621f6fb05f8fa04f9f208f9f50af5f407fcfdfd09020628eb0018faca12ff01f3e6f9da0e09f615fce906c8ddfef4bce4fbc1f700f002e8fe05dbf3ef030bf1efef04fbeff600fe01f1ede2fbf601e6f707fa0dfbfbe8001df8eeed02f0d3f0f6fdf6e4f3d0fff7f503fb02fef403f4e0fcf302e80109ff04eaeafdfdf3f5eee8ccfb0e050afa09f9e90200f2e6fc0ef10b08f4fae80207fc0b00ff0807fc08200010f202ff0c0af617f607ff0000fd09fded00f90b0216fbfe06f613050cf5f0fa011300ebfe0c0e020dfafefd01f5f8fcfa070104e804e5190c190c0de6f3fe15fbf6e40110050902ed0af3f0ebeb17f3fb18faf402fcfdea0306fe0e070ff1ea0e0e0ffffd02fb07180711f9ff02f5ffef00f6e1fefee7f91204fe06eefb250117d807f8033ff912080ef6ef0003fdf3e7ef03040b0ffff9f3fe06fe0d01f31df70301030403f91c06ea08fd0505fdf10900edea110efa2315040417fef9f0faf7f805fd2b070e0d020cfb05f418f501fb14060d2607e802f60d0333010a000c17210c00fa04e71911f105e5fa16fc0a13fc04dc05fbfafbf808f4fdf7fe020201dc0a0aee1df1fdf416fa00fefe110001ee04fcfaebfcf20300faf914f6fc090af1ee1c11eff60ff3fbf9120213f514fff7caf0200ceaef14ee070cfcfef7fff514260403f8f70a0d02075f0e14f909f71014010903fa0e01190327f602e1080a1716ef1cf7ed240201f8030f1cf9faeefa1b040018ef00f6f70006fcf415f207def4020715f0f1100c02f5f5ee1602fbfb001501140407f3031104f9f9fef8021ad7160209061d02050606030b03f20304e9060b0ff90d0a03021bdbf3fd0c090dfcef0debff090501070ffef2ebfe0612f20520fcf60cf7ffff2ef00ae9df0b1104f60efbe70f150514fbfefcfce80bfb0be40ae2fdf4eef911e70304f22502fdf3f913ea0cf2060f15edf920e7fa16fdfff3e516eefae50401f7f3f003fb08dff1e3f50a0308fdf2fd08e9ec07f2f304dcf4de0aefebfffe06eafc1906ea17f70a00e40a07f303e7f6eeea06010cddf3f70101fdf1ecfed8020dfcf8fb16fcfc12fb1df419f50105e01503dff7dff1fcfa07f832f7fa0f0af1170d08f10502ef03fcfe03ea250efc08fef6e3e708f3f7f3eb0a1cf8f913f5020ef6f901fb071fedfeffff0ffbfa20fdfcfbe3fa0f12001dfce8fb071303f8ff1bda0604fe04fbf6f11c10f3f8061131fb030503040a23201510fcf8e6e2ff07050523e5ee13080505f50203ec1df51201020603080cfe14e608eff8effbeedffc060eeb0303f504fcfde201f5f100f20007fafcfa081f0001ff00eef22400080603f0e6dc14f809e408f9fefaf21af402f7e7f815ebfe0e0aeae4dee0f1ff12f2f9ffe20702f3faeefa0803f816070ae8f3f8e8fafaf6fedff7fd1cf1f10105dbf505d6f105ddfd13f4fe0807fa02001c0af2fc06effff0040be8f5f30df9d5fe0106f10203de0708f9f3e3f400e8eff007e5d6e0d8fb06feeffff4fcfd030c0500ece2fb09f9eaea05fd02f202f9000000f2f807eb07f8f2f0eaf1eff4fb09e4e3ddf606f2e5f1e503f105f714040fe2fd09db00ec0af0eaf30418ebddf506e7000dd9e3fedcf30cdff80feefefdfb0b0219f9fc05f9fbeb03fcfdfefff3d9f7fe03fadcfce4fafde5f8f9f404e40beb04ef04f8fdf403040911e8fdd9fff7eafedceee60fefed110301fde204dd09fcf202ff00f2f9fbf9fef708dcfff7f8eee1e0fafaf3f5ecea0af0effdeffceef310efd3f5f3ee04ff0000fef3f0f50406f8ffffd7fff8f1ecea0a03f0fbf302e7f906f412f701e9e4f9e40bfcec021df3f9f703f7ee12eff8fdf2e905ee050a0d081f1101fefff0fe03030012f8fef8f400e4140600eb0afdfeeb01e7f4eafcfceef4fdf6f4ede7f1e915e201f107080125050afc0fe90100ecea0209f0f90bd0d1f600f9e1d5fef0fa02f1f50fe0fc0a08fb09ebf3fb12f3f305f6f2ff01e5f4fa06e1d7fb00f4f0f6f8f9091404ebf1fdf509f207e7f805f100ecfcfd16ff0a03da0cfee6f20301f9fb08f8f906edf601ebf5edebf4dff4ff09040000edfefa0508f5ee0300f0d712f3f7f8eef7f610fbe8f3f6fefff3ebfa00fffdf2fdfbfb0803e6fcfd12e4f00901ff050604060cf3f8f0ec1308faf6e4f6ff0f03fff9eff811f6f70403f201091902f7fdf5b70cf104ebf0fd0a0af00209f9f700f7040500d3ecf1e317f30be708f5f9fffe0915ef01dd0908fdfdf006fa08e60300fdf502e702faea00f4efdff308fff7fa00dff7edf6f6fef5f2ce180803fa04fefff2f2eb0d0602062afd09fbf4f6010bfe04021dce06090a0c10d7f51111fafb19f900fc0406fef80d0705170efc1b01fef6040800050d0206010811ef16e923e6f901fb1000d9f90a2e0a2905eeea02f2f9030ef30a01f6fb070208031e0f04fe0ffe05f00c1201f9ff111009070901f71bfdff02f1f802fcec20fb070a0511f03010faf6090f102eef190501fef906030ffa2518fb143909f7ee04f9440bf414f402f614230cf827ff02f0f800fe02d708fdf7fbf513ee0808fc0401f4f9e3f00b03f0ef09e804fc01f407f8feef000afcfdfeefef0002f50e00f3fcfa06f3050cfaf60aebed0d00f2eefcfb02f6fc10ebf0e5f4f5f2f2ede70cfcf705fafafcf309f1fef7f601faffff0109fcf612fbfa08fdeff3f3f10602f7fefbfffbf8fff8f8f0fe0811fef1f8fc04f9f60901f80403fef6eb010e0301e505fbfef30b10f600f40a07fd05fced100408fc16f809fc04f1ff1d05fcf31aff00fcf8fc0801030205fffef7ff13eeec0211f3f6f7f30902fbf4fdf914f8f50f0cfc08fc0cf9fc01fe09f408140701ff0402f913fd060cf909fefd090e01f9110113110df5090d0901fc0a0703ff0dfde10a0603fffef610faf9f5ec26fa04e0e1030befeb25f305fafa030fece4f011fdffffdff40cff13e400fbfdfef4f5f70002f5f4f80106f1040dfeecf6eff6eaea0004fef911f91816faf711041503e8f8f0fa0907df080c04fdffe5c2e205f8fbf9f2f8f805fb07edef221aefee00020100ff0012f40709f5fa03e4f4f511f0e8e800eefee5020101f2e1f6d9f702e805f0e1ffc3db0203c7fef6e2f3f7f2fd07fff4db16f8f507dabe02fc06e0db02f7fbf0f8f1f800f4e415ffe205fae9eedcdff3ec03fbefc0b6f5f2fbe6f7f1fbe0ef02fef4fef302fdd7f9eeeafb04e5fc0af4e1fbfded0310d1daffe0f804c807f3da0902f1f70a1be6e4fa05edc708e71613fff91bf70dfdef20e604f4fbe7fa03eff0e5f9f3010e05011cf20b08fef10401dff4ecf90ef400fd0ac4eff204fd08f4f7e4f7f509f40406fcfeeeefe70af6f30807f6ff061d07e311fe0c14cff8e405100ce5f7f7180f04ddefcff2e304fdf715fefde8f7f90f18f7eee7e9fc08f6f6f60ce10bffe50bdcebfaf317ff13fb0e10ff0101fafe0a16fdfe08fd1e2deded091aeef7f9f215f8feedf900ff0b10f81ffff20e12220513fcf1f328ffff09fff22b04040b100506f400f4e8f016021207fdf50affff00f810fafef002c30f0b0103ea02f317e0f6f610ea071601ff0ef807040afa0add0e1a1a04f905fb09ff00f5eefaf10e0aff0404f9f804e4ea05de110b031c08f50423080112ea06e406f8d11d05f73dfe320b0af9030cf305091f00ee221409d8b9fbfc13e915030ef701fb1014ff0efa0c041cda0ee81dfb03e0f90009e40e080af81f201572ee08f61fff18fdfe05faf3e3dd44da23050701e4e9057eedf435e6eefa3403eb0717e10b0e1509fc0800dc18fb6c0209cc020cf4fc16f1f506f5dff210f9f5dfecfff5fbfbfff90703f8e90cfdff01faf7ed02cbf90b0000e5fe060be1eae8fef1fcf405dbfd02edf9fdecf9ff0ce9e709e7fffdfcfbf9170bf8ed0bf817ffe7090103f803ededfb0105fbe1e900d8eb0324e307fbfbedf4ec0c1ef6040202f1f803fb0100f8e5fce2eff0f4faf60dfd0feef0f3fc00f60d01140df5f300fef80fed130414e810feff2a0bd8e4f209ff0810f411f9f90e020301030312ff28050af30a1414ff0e00050312fd00f8eefe11041010fff305f307fe010c1600fd05e81207f301ef1a0103eefc0a0f11fa09fffb0dfe00040b0d11fc0006041a060e01041708fd0ffaeffc111cff0104ec0539f3f900eeb4faf8f61cd9f90ceefbfcf40af808c211f1ffb10104dd01f51105fa08eb11fc07fdf20aee0c000cdc11fa18f9df042e0503fa12f7ec09f9fccf09ed260efe010cf9fbd9eae90410eeba1e0cebfbf9fa040621f106fff01ef11fef0108f2160bfdfc0206e6d8f002fff902fd2ce0fbebf6f7faf0fb0bf9f9e036f2f5010106f8fbff0a02f60cfdf105fe0df6090603f6ecf3fafce7e6f4140502f309f9f221fb070203f8f8e10cf206e507f6fcf9f308fdf5fce6fc03fa00fb08fbfbf0faf40203f7fcf60207fee8fe02fc0203fd0ef818d2f9ff1b0008fbfa08f9ff1df901f000f1fb07fa08f6ecf60cfeff02f10000ee190e030007f706f0f80408f404110bff0a070707f700fef900fe13040b0406fd10fae6160bfd09050903070bfdfc04f7ff030303f3f910e813fc000803fd06fe00072001ff04ff05fb1814fd000804f21603fffa0d0b1508e70bf50304fa04fa0d12070503190bfe070302fb0f0500040b04fcedfb0f1a02fbf7fefd1508fb12fd000102fe07fb02ec08fcffec04ef04f0f405fc09fd0efe03eee70bfaebf3fd05010bf4f501f2fcf9fbf50103fffbf2fcfdd9f2e70ce602e306fa02fff205fcf4fefbfef30500fb01defee7f1f1eff6f81c0f0af009f1fa09e7fd00fcf600fcdfe0f800fddaeff4e9e4fb0df20cf604f8f2f308f3f9e3f002ff00fcf80706fa03fd06f1f80302f016001500f60307cf05fc03f3ecfbed0900e7f7fbeffccfecf200daef2ac5f9fbf503030cfff109fd0ef405e8f8ef05e41cff09050d04fc01fe12f8ff0e0700fbedec1d05fdf701060bdbc60bfcf4efead10beefbf8100af9f2fefce800fc0d0cfffbfdf8f1ec05fd04fffcd7db02e2000ed6f2f6eb01f3f6ec011901f90802f0db1104e5020ceed9f603fdf3eef9d608f7fffefcf4f3f404030fe40c05d4f2fdfc10f50c01e806f8f6080cd8f6f0feeb0dfb0c03fffbffff050419f607ea02f7f3fd07020803f20404e1e8f9f9fd05eee8fdf2f2f8f9fe00ee03fff0e5ee0af3fb0d06f8f9fcfcfa04f1f5f1e6f602fbeeeffee7020204f3eefbfd09fb0901e9d9fb09ff090ff3f6070d0511f90be7ff01f7faf3fffe0ff90a02fa0706e9030ffef715feff0afc0f0604fbf8fafcf7ff09070005070bf6020809fbfbfffcfa0407fa100318ff0afa04fafcf301f8f8fef610031008ed0203f400f205fdf40509fc06fdf6ff00fdfe0dfe15f8eb090e1007edfcfa1303ff00f0fef40b070501f2dcfd22f20802f91c01080d1306ee07f8ff0ce1ec2df60fed0c050cf9f8fd0bf302fce5f90500061303f6ecfaff18ee02dbfcf211f1f502f40afcf10e0aecfcecf9df08e01ef1f5f3f1ed3102fffce6f31703f71604e80000e5d5fa0c01f0eefed71c04faf6ecfefafcd00ffff0c90d08fcf801efe208f5edfd0dff07e3fafdfae306eff40cfcfbfdff05fde71c050ffb06f7ed0dfd02fc04fffbf5f5e1f42bf8ebf613030227fa150100f5dce8fbf003f60609f804ea1deff8f7f70e04fe052210fff6d9f3edf506ef00fef8050bdc0607fd01f9fa150518e7f5ec1ef7faefeef2f7011ce9fe0703dc12fedb100ae8ee0efbeb0df907fa0010051102fae900ed0e0be90004fafff5effc000501f41607fbe6f404f504e6f1effef8ff0019fdf9f8f7f8ff0307fafc06f8f8fe0308f2f8e204fbfff7f41100fcf6ef0d09ec01eaf905efe0f7f3f5fefceaef01fb00f4fcfdf803f6fafafbfce9f9f8ed09f1ecf4f8fbfa02f70af9feeaf1f6e7fff5e3f807ea020ce3fd0af209f8f6fd0ef800fd01fe13130b130603dff8e7ec0cf52cedfaf002f4f2ff0a1ff10a030e0f1de704fc0dfa1e04c4f906040d061d3220f4ed1dfb18011ff4f410f60914f8fdfb07fdc814f6f8f8fdfbfd020115140f100122e8d9dff51c0a0ef616fc13f7fdc3fff7000c00e6030406fdf822fe0ff60214e9fdebfde6f2eef0eef3f9e7fcf6e8f7fe19fc0cedf70f04f60707fff1f40cedf6f9fd05010703d6f20706e002fde4f5ffff0a0f0409ecf70808f7ebf5e9f907eafff71802ffffe8fdf7f9f4ff070605e3f6ebfbf20900fdf722f1f2ebf3fe00eedc0ee0f9f9fe0b14f4ee08f3fd061804012306f6f2fcf1fa13010cf4f403df0a02e8f8f70020f7f4f4fff70c0f05fefced05f1ea02f715d60cffffefeff9e3f4010c1513fff6120cecfe1810fc050a02fe0b0609f002010cf615fd080b0c0004f4000508160ff202030608040afdf7caf11ff7060f0b080212fbea04ebfbf314050cfe0101fdff091007ffeaececf80df81805f2fcff0201f806f5f5f00e0d0a04dbf705110015ff000aeaf8fd0f0403f5f7fff606fcfaf0f8fc0103ed01ed00f9ef03f600fb03fa03fcee0affe8f5ffff000500fcf805f6fc01f5eb05f5fbdc0bf80903f900ed04010205fe00fdfffbe80701f3fd00faf9faf9e9f9ff0703f3e102fcff03ecf8fceffcfded00050ffff8fd03fcfdfdfefdfaff0ae6f502ff00fbdc03f003060200f3010001f11102f9e9fe020afdfdf9fdf80402f810fb0907060de20619e5f0e70cfafbe1eff4fc0109e5fdf2f334f9070811ececedeee606f105f9f6eff91dfef501e9fbfee805ec20f001de08e9fa03e9f2f3040903f0f80603e900f00df812edeaecfdf800e8fffef6fd09f5f509fce703fee411fd02f50af6fd04f9f0fe092f010bfa0bedfee30504fa14020008e50ef608e800ff0a01fa071b0df007fa020901f00dfc191df9fc14f8fcf808f408f005f3191300f6f61c0300fcf70f03fe12041603020ef8f4fb29f215fb081102fef30800090c0efcec0901f90206f8ed1a0d0708fe00f4f60816030a0eed0b04faf7f7ee0b1804f302f9fff1040df402fcf701f21213fd07f9fcd9f6fafefad608fcfcfee1fb0004f2f606faf7fbfdf4f900ddf1f2e3fbfbfaf3f6efffeff7eff5fbeaf1fbf601e5e8feff02fdf9faf4f5f801fbedfcf008effefae7faf4f8ed05f6d9f3fc04f9f9e0e6f6f8feeef4f0e1f8f1f2fbf6fbe306f2f7f5f200f6fcf2f5fbf3fdece4f501f6fad9f5faf5f1ee03f6fbf6fcf8f7e4fbef1f0ffeff030607f6fa180615f1fd0fe508f707da1309fa04edf51820f003f2fa01081efe020c01fdfcecf4f428f601f40fef1117fe0001e50400fd10fd42f9f6f5eaf50902ed06fb07f3fdde0218043503fd07f90ee1e106100e0407fc0df6fa12f60bf602eeff07f609fddffb11ff041efcfa00fc24f00308f7ef08f5fdfaf703fdf511fdff02fee1e5070709ecbb1d06f8070cf5edf60ef5e11601fcfb1322f707da04eafc0ed8170622e3de05fa040421eae20106e92413f8f7ed25ef000c0708ff0a19ff0106f719f1f40813e220f9032cf8eef90d022407f0fbfd08ec02f51210fef8de00ec21d9f0fdfb00e0fffc01f3fccde410e804060502fa11f8251900f405ea03fef2fc0003fe04fdf61c0d01120aea06ffd50f0fedf60d0f030f00f4f605faf5090b09f1f716fa16021705081702ff0d0d1df5fd1ffdf0f62e0f25fc12fd0b13fc0d14030b1cfee10cf10102fbfcf2291e04ef07232a0718fcf70e08072b031524fff615201c04faedfe06100afd10f9f50c22051301170b0302f2fd00fae10407f40fef06d1f8ffea04f4e5faf1eb110ae50306cbe8feff0df70404e4fcecf90a09e0f6fc09cd080206040606f40d16fc06ff09f7f8eee80301f8f607061210ebe7ff070303f7d10df3fb07f302f6fff801ddfe0d0f07f80df8f606fc0902fdfeebd8e8f60109f8d9ffe60005fbf8ee01faffec0ffcefd8fffffb02fffb04fdff03030403fe03fdfc01f9fcfff80304fb01ff0705000209fcfe01fa0a03ff0104fa040204fffd0bff0200fefe0a03fefe0705fefc00f8fe02fff7fdfcfffffcfeffff030303fbfd04060f0101fffc03fbfafffaf7fe010400030509070aff03ff03fc0202010a07f6fe0c06fcff050508f70406000301f8ff04f4f0f709af040400e7ecf7d9fd09edeef1d705efe7f3f9e0f000c4dbf605dc0ddf00ef0302fa04f2cdc902f7eefd01f704ef01e401f4fee10ffee6f9eafedff706e0eded06edcfbd06f9efdff0cf25f0f2fc030303dffffff3f8080a0defeef606f6f3fb0400fc18d6bdf6eef9fea90af5eeeef1e0edfd0fee0ff9edf3d101e3f5f8ebf10ee0fa0bf40bef2bed00e5dd0704e0fdf7f6fa11eefc1c0501ebf0f4ec04e800e8f509e7fde111e2ebfc07ffff16ec10f4f5efde05fc0df605d8bc00f2e2f004fef10511efe711f8f703e8fefdfc1001dfdfde080400d6e6f2e8f6fc04ee11ec00f3ebf10d10e3fa06eb0d0102d90602f40a05f8eff5e1f7011a0617f90403040e0a09fd0c04ffeef2052722f91a040bed1002071114d0fcf813fe1712fe0405f2f70c20050b0f260e29ff0dff1621060b09071afaf705fccffafe19e62d1007060f0216fa050a1505f409f009150b05f32f1900bf0301252d030301f3151012041df31a00021d251efa2602ed0c0bf710f3ee2216140a0505f903ddf4fdf4fcbbfdfdfff5e1fad601fee4f7fcf104e6e6f1fecdfef2c2ec02fff40103fad7fbeff600d8daeff8f5e0e9fdfc03ecfeeefef4fd1a02fdf90ddbed03ebe7f00904fdfadfc9f902fbfbf7daf1eff0fdee04f4eff604dffcedf3e3f0ff0609f4f4f3fcf401f8c4eaed02e9fdd7fdddfe0403f1f20706f4e5f1fcf2c5fae0f5f1ed06da0803fbfadaefbdf8ffeefde8ebfcf0edfbf9c5e2eecbecf208eafded00d402e805f4d8d8f7fb03c7e1fffefbf606dc06faff0601fcfcfeede0eef1e3e7ff0907ffd7d1fef6f7fcf2c700eb01faf7f701e7f7fdd5faf5f4d6ee00fbfef8ecedf9f50501e5dae8d5faf1c9ffdaecf800f3ebfaeaf4f6e501daa80012f1fe0708e0fe01f40afa08ea10fbf1f5f10103f1f9fe07ec03f3d607000cf60900ff01f90303f7f2fefc05fae1f3000305effc0ffffdfc0800ecf8fcffecfbe601ff0703fdfff6e3fffb03eaf5d910fc160bf3f9f6f9fcf4eb06fb07fffdfd00f708fd1bfcf8f508ead40cf8fa08d9fff8fc03f5f1f7ffefff08fcfbfdd700f414fe0600e8fb12fffa16fa020c05110009f0eeede9f204ebe6e9faf1f702e4fcf1e21bfa071101e9f8da0ef805cbfbfafaff0830f9fcf7e6f904fa00f802f0fde3e8f301fefcf0e1ff03f7f4f5fcebf4fefd18fc0eeaf5f00000fffaf1f6ee0204f0f6f9ffe3f90dd20cfeeffc07f30319def6fe1524031f05f9fafce1f60507fb03ff07ff0404060309f8f904ff0c1901120008ff0c00ee0e1bfd00020ff50609fb0203f8fcfff2091afe06f617040001040c0701000625f5fd07fa07e62b0c060712f7fa04fe030b03fd1f14ed0afc00020bfffd181a0100010a1408060bfff80c060004fb0b07ef0b071af6f1040310140b03030205011ff7fdfe0bfd060cfdf7050406fffbfc03f4100605f7f306000d08e4fc0ffde7fb08f5fb040c21fb14ef000401fc03ff0ae3fa36da0dfa14fefaf9190604010bfe0a13fa17eb2dff200712120c04fb060c0ff4faf0ef20edfc06f3090e03f204f1fef10913fb1d0004faf719fe1c0308f8f110f2fefaef0ceef0f9f50cfefbfe030b03fbfc000311f90108feebf6fcfc0e1808d4fd04110dfaf6f717ee18fffc110ae6010e11fd070601fafbf7020107f914021ae301090b0b0709ff03020112050702f4f4f30202fefc10101612e2fd05040df6f1e11bf1fb02f40800eb05f0f0fc160d0b081b0bf80dfa00fd09ff06f40311250ffc1706f42604f2ff07f8fefcee0c05fdf205),
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
    .actor_error_o(error_actor_context1_pointwise)
  );
  logic error_actor_context2_depthwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(9216'hf7e8e91d100f2a05312b1701321a29372b63f80cfb1702e01205ecd0ccbaf61ffc27082800f417fcf619f8ee041d1dee1a2204bcddab291b2009f7fb07f40bf3fd00edf3f004f924e8d5d4fcef0ae3111b231a16040f1d04fa0723091e09e20a0d040a3afd4309df0805e60be128d5e42edcc2fdcae61b02f711f10722ed2e1e363cf00f071d12f8f218f3cbeb1e122612fa351aedfef3ee2b15011cfbdefd290d22fe09fa1fdb0b2f0b2317264ee3e02b01f0f80bfc0b08ed0e240d2201f00a06e507261126fbf6dcf526dcf607e1f0fcf5f9ef0819eefbd30af4cae9dbd0fbe51cf60affe5f50cfffae0e7e6fdfdf03e2f24353b270cf907181101121312001f070af9fdccbdbc08110210191a09ea031a1614091af90205f6e9f4050a08eb2ff8352ff02b08fb080afb01fefef2e8f0f8121c11d313e1e10df518120d0403fde6e1eefe06e7e9f501150e0c042708051ced0c0ce11d0f2bf0cbd9f60af117fae6e1110521140d02111b1cf217201d0b0307e2ee0be8e1f4d02bfc3127fa1d28131e2efe34efea10f4e10d380e312203f31005f6150d1a01f4ffe6dfde0ceb21fee21d02f20c211728e4e1111ff81bd0e3d7091700051922ece5e100f1f20d1e0525f5fa11eafb14dfe6140813e9cce917000c12f7140cfb08081d24e8e3f4f4170ef5111f02e2eadbf71dfbde1a1a130be6fb06f3070810ecf101fffc26111ff803eff509eef2fc1455033a0b150ef59ba32416291b1d2811131bf601fffd0bed330b3af4dde4f009ed4b354102030d16e609161a331714420ce105eafd13f5f1f404f12426224709ee090cf40cfaf5f11f191df3f2f6ddeaf608f32c0de517271e45dffd06fb01f13f04fa03fe102206ed0a05f51df1030ef70214042ecdf110f1f0edece50c08f905fce5f6030812eef223e7db080bf3ee2d121314e4f523fcfb21172706e610feecf7ffe82203e307d8f522281bfa19fbfb21fafdfd35fae23afeb1e5f2320c1929f70218fef0f1e8ebe70a06f2fb050a0ef8f20212fff00cfadb14f6f00fdcde0d2ffe3816171cb4d2e90a030ef3000bf8f0fe0712e4e1dff301180e2835210bf6fc01ed0716223819f2293af22dea181be6edf3dcdbf004fe0af803020bf9f0f6dce0fcedf3181c21090a0502e10020fe2600ed02f5ff09f2f3ff40296127e618b8a9bb01f80b0af01d28ff34f7061a18171c14fe1d19141232fa001b2a143a0f3733fd10e006c51ef40b07ed0d0108e2051a0a0730fad4e9bff80213edee0f0202fb09221600f1d92f080d0f1819fae009fcfcea1d0be01dfaee0ff8ca1f012901ee1502f3f5e3e4e4060d0e0b0319f01923db220bd9eb052e13160feff008fc08fb13ec260e0f1efe20ee01fdfaf3ed12e215211b2418ec1612f40e08e9fa02f30611df0807f0080cf3fe0fea11190f2716e6fb200e3303010500faf8fbfbf42d0a2837f61e50293b17f9f80dfa1214f5ea310d1decf9d3df00e00efd28ecf231c0f7f51f03fe35eed4dbb0f5e4f8f0e0f005e8e8f81bd80f130b270821fde208e4080af20af02500f10509f00c100f23201a2c10d80cf5f4f20efcfe0edeec27020f1310e0f2d3c3dfc8d700f0cff20507110dee),
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
    .actor_error_o(error_actor_context2_depthwise)
  );
  logic error_actor_context2_pointwise;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(131072'hf9fa081ff5f8ec02e703d5f3f108e9f5ef0b0be9ee110504f4fd2409ee15f709fb02fdfaf8f4e6fbfaf5f0f1f609f9eb0c03f9f7f603fb05fe03d0dffa00f0f210f1f8c308edfa0b0be901f400fef608e6fdedd2f7fafaea0609fc0609cb0203f9f302f30a04ffe7f4eef8fefbfaeffbf9f8fcd0faf4fce5fcf1e90102e9eefa0c07061f001ac40ff9fee8e3cf0511fae0170fe8fc1ed7fffdf23a0ed90b0ef9da0dfdfc06effbfc00eecff5f3f8e3e5fafa04ee07ff09f9fd0dfadd4d0709df00f70cb014e5fc05e5f7eac8d7e0fe0b0909f4f6fc17d0f8ed041a0be4f2fef0040001fffc0302db0515eedcfdf212f7fa1500e6f5f3e5e8fe0708ebfcd7eeebeaf6fff30d08f4faf7e60f03fc00fbfcfaf5e807fd02fefdfe04d80cfdeefbfa0afcfaf504fbf2fcebf7fc00fb07faf90d07f8faf400fefa07fdfaf6f5e404f7eaf704f5fdf9e9fafa0909f7fffa07fafcfd060afb08f603eaf401fafccefc0408fcfe00fafbf5fbfae10305e7fdf6fcfb12fde8f5fc070cfa01f703f6f602ed19010601340c2cfeff111a21f417da0222bdfc230fff04041201e91d0cee08120e0bf100fe1c20f9f6ed443d26f724200ff10b0cf4f9fd0d0ef01b2fd9f2f901f10cef0fed1909070cfc18362e2e1207fd054e1909f93a0df821eaf8331efa0001e204f80a282c0ecfcde51f1503de170eecfe0d120c070f0c1608fdd7ef0d060c09fbe4130c48fc001825161a02ebfa13cf000a11eb11070406cf0601d7fe0b12030907ec10ff070023072020f52e3705fdf90c0402efff2e031b09e6fef74a0613ff4c140f1bf50dfe07263415fce41102210b00f7412eec02ce040f1a0909fdf30a14fe140a2ae3db0e230e09dc1006e0ff35110401120312f904e615f9110f110d0feaf4f7fef305c5f5dff2d727fc0d04e71024e80cfc09351e0710ecfae3eff6ff12fadfdc15d9f4dd011bd8c4ef1bd2ee0d01ea06e800b0db282c0ece38f4e3bd3404fdeb1efed2f2250cdbf2fdffe5de03f6dbdfeb153a0df7c114edeeeb04e6e615e1e9f207ddcd1701e9feff16f4c0fe0b03f306e70106feeeeef2d9c900d41cf7f1f1e6fb0a05fb06f1e505c9d00efaef15091b0ad5e2f8c6e506040325f5120e0b03db1915160de90f15eef91201ccfcec121c00e3ecefcf00f9edf5ea2cf5000605effc271d0412fb13ffff19e4fbfed711fff5ecd408eecfcb1200fb1b050c19faedfdff13dff8f702ffda03d805e8f60e0e0ce8f8f80d01e3f1f606e7f1f60dfbfe0af9f0fbfdf3f8ffe5fafb090002fbf609dcecf2e5ff040cfcfbf303fe0305f6f7faff00df0412f8fff9fce20108fef7fefbf8ecdd00f8eff1f4f1e1f8fefcf80004f403fde801fcfdf80600ff00fefafbf9e805dcf0e903f5fb00ff0401f0edf8fb00ea05ec0405f805f401f6f0fb04f8fbf4f5f5aff3eff411f40b3216fb050623faf7f50c101feff8ef05d909f61efde72215f72b0707f61713fc1309eae7014503eb04f3eef7f9020df9ffee0fe1061a17d5f4edf9e61e22ec0303f204ff1a0d0a23080a0df3081904fdff01f505160df906eef8e7f700001bfd09131b01f0f5fdebfb0d17ff08030911060012fe020a0d07e9f211dcd2f801dde3ec1a0409e0fc080705e6000ed0f4e2ddfc05f7fee8bdf215fe03fe090203f6fe1001f010f1e0f009e0fb09eaf9fbf609fe08f504c9dfe5edf0f9eee60dbaefedeb0afa0c0bf6e7f2040b050aefdaf501d7d618fff9d0f4e1e6f6eb03ed0510e00af30cf1eeece8ff12f205fd03ea000805f3f6f4d30120f3fdf3dbeaf7cfeaffedfaf8fa040b03013ced09f1cc15f0dd0ffa1500ddcee5e0d514e205f60306f6330bd007f4f9fffcfe15dbe308ffcaf2030204f6f701eeb60befc4f6f4f5f5faec16db0319eb18f5130df6e90ef4f9fdf7f61002f7d80717ccd90a0cfc140efa04172cf107fabdf30bfffef806dbffe2ff260c06f0f500e9ece8e7e6f60017012d0b0f07282b09072e081cf8d22301de0a060d02f2cae4f715050f00e9faebf33903f21b022f2112082217f505f9f10711050702f903d7e4023ce306eafff2fc13f40b15212cfa04161c0d0600e3fdf4291028fee5ea041ad5f9edf115170cd4242206f8261ce10ffeee02e5012d07fe290a06f3e5110d22fb2af9f50416d9eed4000902ffe1dffc05f8e152fce7dcd6de0813fa05f0eb1117ec05f6ee01fe0a2ed403e9eddaf31df2c12d190602070c0af5faffbd09fe30f7c00306169a27fff4e618f5f7d7dce5f1fcf9f6f2bffcffc4d3f40d18fdd1d8eafff02410dd03e7eef50001f501f7e81901f32afbcdf106f3e5dbf5e50b06ea03f3090a06c61d292916defb24282ee3310011cff13a0ad0fd08f310f8dffec61df80cfdf8ffe2fe0e0ce918e82f24e51d34d6e2f116f2ef01faf401622ef2d0f031e329df7f141d0c17f924f1074c02350b02fc0f25f1ed2c17f517c5cdf369f6ed1c07131606c911490705f6420a12f7f6fb080b3700f022450422f3f80241172afff204fbe7c3d302e6f8c50e0bfa0d1b16290c12e5f7f5ffe8e616e9080bd60be415eef4ececdd0505f4d9da20e6f9e5fbf3281601f712ed00f819ea12ff2512f1f2e006f60d160e09f80ff8f30808f2eaf5fc12f4f7def9150ffd06ec35fef40c110b0dffecf7e20312fde90c07080df708fb1706030201e6fbfde915f90d03aec2f6d7ee1cd8fdecffd7f2f8f8d8feeecdc9fdd3d4fefc0efed3abe2bdda00d7f5f0e0fbfbea00d0ffe8f7f3c4e3e2e0efe302cd0405f80b08e9dffbacfbe1b3fae6c704f9f2fd00fc1ce9edf00201fc05f3f8010bf9f6f6fcf8cdfacecfc80deaff0004f7f4f0d8b5fbe3c606e3fe09c100f1feebf4f8f0f9daf5e6efdce2fee6fbc7041228f3ed0e211723fe0d1835e8e52ce1cd20021302dce20bfbfd14e60bf7cff6141af2e622133b0ce52023e7072504ebf30ef8f1eb5513f7cd1f3beb1bc853f00706ffe01b2b16160d0e1227fe3726fef7133327fed8e8264bee000bdb061706e80121e905f025f106d81103e6fe50110d0610100f28f0fc26f5e0eaf9f81ff2e5c9f90801e4f6fd0512e7f02414f305110c0cf5fb24090518f804e8f6ee0e10daf60201ecfcdce811e8e8fefaf309f909fffff00cd2042bf30ed2f9fb0cc6f0f7def2f802f9d6dbf2e0f80209e7e9fdfbced7fa0bfb05f1e203fbf003e7e404ebe1f6191001e0f8ff0fec000bffdeff05ffe8f3ee01081ef70bfe03121b160a06dc09fb08ead9ebfdea1cd7152fc6222004ea03032e0b0c2219d8e80401090524f7b1f8d7f1da0811f2bef21613d7fdf5d3ede5f2b4f42332eae636d8fe9b221513fa1c0995e6f21fdfdf11ecece7fcefd5ccfe031f0bf7cafbf9fb0403e5e522dfde0904e1cffdf20afbf9190dd01b19e9f3e1e01fd802d6fdfb100c02ec003503ff09fe160bfdfe38141706f431f2d11dfe1d0ee714fde503f10b060af7fd033811fa00fb1f04fd1afd191707f3f3fd05022508492804d61d1de4fd08f7fdfaf717fdf92dfb11ef16fff5f21630fa063a0407f9ebf30923e8030a01110fff0f032209e31511fef604fc0a110850fbf80b37fb1803fb03050deefbecebfa1fff000016f8f4291ff61ef141feea320adf13f521fbf8d51208fef3ed19f4f5e61f3422f00c1e112707053205f210f9f7f910f1170423f9f0d0df1cedf8f170e60419f5fa11240512130006eff31132f616f61b0a0bdcdc0134d4fa0e07fef5f9dcf71bece3f905f9150a1aee19fe3015e8fb0d19f9f1fb081722061219f411eff2e005080fe7e1dee0d234060b1704170deffdf7f2282f0e1516f9d501ec001b1af2cd08d404e3031ef6ae1f0accde02f2ecf1e50bcafa29280ad43ffce3c02e1803d80401d800fdfad8c80205ebea0c07ded4f6f73416e9f11f04e9f50ce8d322d4e2ebfe04c919feed02fd26f6d8f1e8d9daeee926f4ebd8f8d7f90b0959efebebe31ae1f9e7dc1e00fbde2d08fcef46de0801f13f1813181bf1fb08ff14f9db1bec33f205daf723f9e21b07f403130305fb0502dfef01402de00fff12a516f6e3fafbe7e6fdd6eff3fc07fcf2edf701caccf0073124ebd8f703e716e8e101f3f5fd1b20ea020ffb18ed0033fcdaf8f40ae7ff19f3f605e7fb15f1cdfaf4f3ed191411ff0e1e2eeb2107df0cd5370ae8070a190b03bff707d50719edf90cfc0b27110635ecf10407120ef8f6062ffd021a1afdfcf5e0d6e9fc04e7f932c5f4f1e0ecf5271dfff102fd1afa100cf0f514df1407dbf4e6fce1eff2e316fd291107011d1203fe0efd0d1ceb00e1fc0bff0243f5fc2bca0217d4f9fdece4f6d6fb080000e6f50604fbf2d507e5ecedfee3f1ecff11eef1d7e4f4e8fd040709000103ccf6f2f0f6ed08d8edda020aef00fbfef6ed0018defc09e7f4ebdc08e6d60dfdf3f0ff0cebebe4f0f4fe0b06e6e30004e6eff1f61bcef8a3e9d30003f1f6f30a05e2defdff00def7faf805d9ece8f3fa04fbf3eaf70ce8d0f400f0c6dce61f145a0d0ff4273a35101e0e340fe06af400fe06101bc6cdcd08c8ff21fb132dcfff252e0c24da3325082623fa1621550cf8282d0d0c3a04dbd72621f3050414eadbf8e1ff143c18f91d3b1f150cf449f9fa20151dedc4d40848e90b0a16ff3727f823290f082d2fee002c01fbf4fa4e0f1c470dfe3ddd0b300d210ad5fc0421e5f0e902170907efed0b0918e803f5ea01d0f2fe01fefbefcd17ecfc08f10e19e3fdece611f4f1f6fc10e6dd05fef20f13f9fef9ec17d3d61a29fefd0b05f9d313f6eefe00fdf3e5f5e9f2f4f511dfc4f509e6d00002260bdae1eedbfb15f0e5f8fce9f011def8edfcf618010ced06ceeeea00e8fae70b0a06f2f607e0c8f8ddf502e0f8dff6e7c8f900f8eae8b7e4c6f9e8fffbfefbe0e5f6d202f5f6fdfdebfa0bc6fad3f1e4e3e9f7f4f701fed1ebedfdf0fdf705d8efccd3f0f3e4e1f8e8b2f2eef8edeffbfefae9dff500f507f00eeaf5fcf002dfc7f780eddd00e8fff0f2f6f8dde6e1f7eec4f7f502f7e9f5e6edf7fdea02f0fef1fcef80f319120922f91afcf304ffc813f1e0f3dc07fb2ff813f2eef4ec031f03130d08051a08e6f204fb10fc0def05f7d2fad3da09fbc8e500fffcf901ffde03f633f0ed1ce1f1f6c3e9e1dcd6f6e3d609b7e6f3edf1f900fbf110d30302e610efda2c1c05dbf5eaeb17e4f1ea0822e545eff70df9fef8f1fe02eee9fce31f0bef0cb2e4d001fddaea1ef601e2ff0af917f9f80001eaf40c01fcfafefa08d1f6fbd7f6f30c04fc080cf8f7fee8f3faf5ffe9fef1ef0600f4f8f70306e30000f0f4def3f0ddf50804dd0afe00f1fcf00007f9f0fd0b0501fa06ff01f502f3eff2f6c8ede403fd060dfefe00f008eef708e202050c00fc04000f030df1fafef703fafb01f5f50903db040a16f01107141503f406f21cb607011af40ffc11fdd1fdfff40efd0bfb0ffcf10cbfe3ce112e2beaef03f7fcf710dedbfcfe0912f809efe9f6e9e9f602051b011314f3fc010f0732000704ef10290b00eb01e60aebde020b1804fd04e8041df80c1814ec080adfe90be21c05bf09ff0303f006fc0f02fff6df090510f6e8d92cfe7c1406320625040303df1fe5c52bfa9904f41e0fe0fd23dd120719012000e12a37fff93d1d1b1efe365900fa00f603f30a0412f8151dc2dedc5f0c1bf152cb351a0a0111214740251d02070102fb0110031911f4d7df1635faea06ea0f270fea3e2de50908170e1be63c01f7032c14170b2f141502eafe181113c0d2ffe20ffeedfbf6e9e9fdec07f5f2f1dbd907ece512080ef9ddc9dff8f504fbe802ef06e9e406db05f5ebfddafbe7fb01ee05d709ff03f506d5dcf0c1fb07c3f6efedec01d90701120aed00ecf8e803fd06def307f108eae7f2d7fcb9ced9f8f7f1fa00fbfe05dddff3efca00ebff04f101d6edf31600f9ffe507e4eef3effffa0bca18344cf2e50e44203507e2fe16e307210ad81dfb0913d9e507d8120a101613eced03d70ade170c371bed4529f7021d20f1fa07031409441cf5ecfb540205187104070ffc0006221e2d161107fc013527f9ed1251141ae3f9154a09fc0fea1b39fd2a161efe033130ef18db290cc10a4612fffd0e02260df8f217fee6dfea0f1de5d60ef60c0108f5ec0526e2de06f5f7fdf10202f004fa070921fb001bfc0b1ffde218fef3faeed4dc1be2fa15f5f90dff0b0010b002ce09f2efebf703ea28e9f7f6ef07f3fdfeebf1e9e300e0fdeae5f1fef9d61613f70ce3def116ec2cf6f606ebfa0126d1ebf3f80b2af9021303e6fa280fdefaf8fd051904f80d1705e217fcf2cae9ece9bdcbba15bfddff1c13d3d81ec202f3ea3d19faf7eafcd2f7d6fbf3fbe6e308dbe20fea09dfa2d901dcaaf20008e801eebfedf3131eba1412dcc52700fe03f9ebd40cd4efeef4f1edecd1fefff2f2fe1f2612f6e70910fbce0bcbee93e5d4d501e6d30efae204fa1c05edf1e7d4f1f2e6f800d7f2f0f4defe07f6d1e9fd0c07f307f4000b1becec1bdbf7f9f1140202f909f9011610040afa0405fff20a0105faf2e9e40d0cef13ee02130d02fb13ddf6e9e504fed6f4eaf914f4effff0fbf500f1e1f0e6f2f4f50df2e1f90cdce0effe0303f0d6ef0eee2aebf0fce6f0f30cf6e5fdf60312fe050df9d3ea0d16d5fde7f7f826030202e6dcf909f2eef9fcedfdc7060106dae70fe3f50be1020304edfdf6c408f0f000e700f5e4fefcdffedd01050505eefafc00f5df00de04fbfe0a0627fadfebf6f5e0f2e702d9f3fafae9fc040bf6fcfefb04f7f70efdf801f70004dbd4ff13ebeb04ec04fcfef4f9def0f00dfaf702f5fa02d80014f8f6f2ff0002f6fdeffcc5fbecd1020bf0dbe5feedf3c9ecf8fbcae7fcdaede9e1f402fffa04f9afefefe201e1f9eed9f7fcd9fcdd04e4f4fad1fbf5fdf5eceed0fcfbf7fdfbf116ebe6f0ebeaf0d8f1d8f6f803ebf3f801f1f6f0eafbfb01effef8f006fd09f7db00e0eaf0eff6fdef04f9f8e6dcf6f6ef0008ddf9ffd9050cfff1effa06fbf107e708c8ff08f9f5b31b210f02ded61e1e2bfd0a151ad4f003e6d42604060ceef8f7d7d60108001013f729c713e50d1a3414c43b55e4ef3401ecfdfd073a08451dfcdbd84cf40e087ff20013030e0e0b1019030a151bf5421202f5314314faece51927ebf91fdd12260a280727dbf40e1df413f738fde7093c150e0721123320f8eb07fc04fae9ed16edebfef90803edecf51102ffe5ffedf0e2e5ff0200f6f4e8df21e703f1f9ff18f7e804e1f1f5e0c8f30ce0e50300f11bf5110510e00dd7e8e5fdfff3eaff02ba13fcf2f407fef4dee6f6e9f8f2ffeec707fbd3f3ec0022f2f3d5eb01ea0feef70afbedf5f3d0e4f9f2f912e300f1f9c0f800f8ea12ede30c00e0fcf50f0d00f706f2e003f305d5f0c904c704150023ee080df50214fefb2a091415faeff5f3ff010bf603f1cd3203ed0ff3d00efbe8c402fce4e3fe06e7eafe0614fe1fffdbf1ec0a04f21a01f5052a03fe01f1fe06cbfce807fee911151de2db0af1f4f1ebf5e2f6efe7d7fbf8def5eece12fdf106ddfbd3d7eaeffd1502e60ddaf3dd110dea040602ffe5fa180b17e403e210cee20214d10e05f205db1d01cf0203f10206e1fd04fcecdbf6140c12f00909ecf2f101d70101fff0fe15ffeeefe307eafef709050922f912040bfa0c0afa2012fd02fd0a03fdfffbfde3f8f40dfffb02e5fafb01fffe0eede2000a0401ebfe04f4ff260d06080204faf202fe0b04f9091905f11c1c20fbfb113b1f23fbea0426ae031600f11bf70bfddd081ff3030912090611f00e0810fbfd152c1a022b3006fc15f8fffaf70c12f12e25fff6f437fcff096a090c1f0a20f20b3a3d22110ffaf11022faed2a300517f81a182e0d0308ec0518051b0d0af3c2232410fdf30f07070749101508170b07fffa010d0b0702fa02bb0d4c1911e1f71f251a0a041620e3f02815c50bf61910e6ee22d609f8f90205f5fe06e0efce1f15261cd70d0ce50208fa07f612142201500417e5ed29ee150f60f8170808f92128152707260c13fe34450216412affeff7f32124e9f61edcfb260a240516d9ee101ee40dd00602dffb440d24092b11f4fc08ee030204f2f4ff1714f9d4edf7e3cfdedff3cee9ed180ad9ff25f600f1ec2a0e152504f8deeed0360ed9bf04fcdff1ffe7f5eeb2ff16d9c3ea07fcf1fefbb909e71710be0b060fd4040afce500f5d0f2caee03d1fbf7e2e6f7eecde8fd1110f2dbfafd1300c8f2e5e9c3e2efe2110fd305f4da05f7110de7e7f0e1f4fde900f6e9fa02dff7fc04c808fa2ff9e7f51f251df7e7f71fd4f90b1ff6070b08f904f92bc62303fd11fee2f518d315d21534330bd501fff00020ebd3f500ff1503320602e5f0f3f813053611040ff206140e0430141e0ce5f83918fafc081ae9ffedf22516fffd18f1fcff010f0d1d00ff0affee00f40affb907241a13040dfa0d080df7dd2007f5f918e11a102200ed0f1a0407f00dfd0ed5f01800e721f508fed30f0dde0f000a0f1c1ffdf6081aff0e101b18172913f7f709edededfc092cfb0412eade041ee80efa1a130c150b07fe3234fd0e1a1f081422fcf4fa0611ec05e5e3f4f8ebd8fc050027fc02181004ed122b0400fe1907eb011113fffa3801050402010ef4faf2f004190415fb1a1506f52b13fb20e119f4ed45d5ea01030ae6f4e920e0f307f628faea10151a20da11000a30efe3fcfe0905f7efea0bf4fe0b75c8f5b707ebbe04f31de24023f2eb132c341c452618f302004904e910f3f0e9e0c4116203ef1301fc330ce31f1dfb212303ebff0718f40e124d0ee30225f4f4d5f62addfde7eafdfbf6fb3815eb03081a1ef50c28ea0400f62312cc0d06ef0adee512faf60423050e16fde114fefc21121d170dfe1532e90e140e08f9f3f5f56deffbcef738f9edfd39f707f6f3f50e0fca1b0a1bff00fe132be6fe1232f9f0ceea1138e8271c12ec1406ec012909efea2801051dfeff190135e9050cf505030a0a3b2efe02e8f4fceb03cc1003f8f4f1ec02020d09e30bd3fccdfbed02feec0806e0fee8f803fd091affeb1ffb0d12f702eb27edf104fff90a000e14e9f2e6d8e703edeef5f7000bb31cf7effd050df7ec02e7fef7f5f8ddd7f801e7d4f6121200fd05ebf8e31cfcdf0705f1fbf9dcf5fd04ef0fee0407eadefe1917f80306d6f811f1f50dc2bafadff3daf6ffdbfdc6e3f2f7c0dcf6c9c306d0e20009f5faaac8f2b2eaf6ed04f5d70005eafac1f9f5f3fdd4f90ae8f9e6f2b5090af2f4041af8ddb7f6f1bbf5d6f0b2f9faf8e3f802ece1f402f5fbfbfb0d04f503f6fbfcccb5fa0ab7c2f5dffdfff6f0eebedfe606dfeefbdafb03c1f918f8e8e1fbfff7daf0e506a3e7fbecf0eff2d2f8fdf60cefe9dd0a0c03ee2007dffcf9ff04e8fce3f6f50bf701fffefd150ef106f7f0fee2e3fa0cd6000e0000fdef0afe05d5f7eedbf8f216e9f8ee11cef4f1f9eefaf9fadbe7f4ecf2ef03e2e2fef8d8cf05090dfafbd504f9f40de8f5fddcf1f610ccf4e805ff16eb030d05d8110206f0f101db001e000517e4dbeb2afaf220060403fdee080719f9f806f5e809fa0311edf2fce6151d08001affd622ebf80c010cfb23dfd91511ed0ef6f3f4ff05000fc8fbe0e5b0ede4f10be719c7e0f9e1fcd6f818f4ccf1f8ebfa05dfc8f7f1e4be0ff0d4eafed8f814eb21e8f703f003f727d9d5031df91cf205fa05d4fd2419e90b09e5071af3fdfd0808f7faf3060708fcf2f63512f019f01710da31c7dbfc0504fff0000dec950edc0eea06ed2e310b03f7f9e940fc2414dcf517f4fef5080ef2fe46f601d1d52ae7daf029f2000b02f90b3def171028fef0f5122dfde914101beaeff6fa650520220b033303d8e9ff03080429fc070205f719fb39f2240513f61300f11f1a1eefd51706e400112402e8f3120e1a0129080afc1404d8e916f906ffdaf625d20cfc1404f4fdf4f6340f05f0182f18000010fef4f2f2f2f7f4f4fa0c321d05e5f920cdf81b0af7fefcfd000308ef1317170efbfe0120ffff2914fcfce7f50a1deef50d030f1904f70b1c22e6152be807100704f3072b001ef605f409f7f41b0cf1ef00f3f0f70cf06825191e00083efb220a1de5d92e03e312f2232ec1e91017fafd2306fa24dc1133fc030d0e1f1a161e3cfc030f11fdf500012f152823c403ed30ec061a2cf5090b110a12290b2124eb07fafa30120ef3ec24f8fb15f81007f4f2152e012108eb333017f5e80ceb1a0a1effe402440836221c0712ffff0d05f10af504f9ef2f1915fbeffb2e2311f510f71fdb002b1bcd04f3180cf40e11f30bfa13f82307fb1325f7d51147171ffb0b2717011218e9fa05100d001af6d5ebdd03ff0aee2e0c1616070d142d29f21814260510faf7fa08fbe6ef07e0e7040901f01e01f73909fa142301cb23edee09f50f08e1f9001800ef06f614ff0b04fe07ffecf5f218fce4f7f402fae5e7f4f7f202eb09f5f7fef505fb020e1d0cf5fdf8fff3f90008090501f906fdf8f70408ffea01040df1f9f507fa0e14e9fa01fff4030cedfae01e1006f8fafffbfaf411f2fb0af7ffd906fee8e4f30f1c0afcfde3f3eaffffeef2f703f5070bf4eaebfefa02f921fde405f7f9f2fc0501fef9e70312040d05d4081b1feedfff181319f9d3eb25bafa1034d42afcf6f5ec0af4c9f8fb190df3f9eb28c501e3222b220cde070600ff23dbeef3f1091c022b12fdedd307fbfb014ffa071a11030b181a3412120a14f8174400f227fc060bc80d1b25ffec11d90905f9300622ed0bfd0901ffd40a0ad700290bf80016140524f3f2020710fcf10511ee0923fb16f81beb0913240dfb02efece4e4230310f1f7e8f218fd000a02091af3f34604031dfb00e61bff0415fbf428050e060ae2fce1fbd8060c01edf623bcfcf8e3ee11f8fde9edf303ea12fadfc20408f9f9fce706fee9f8fe1fec22eefe01f7fd241ce7f4f9f8fe2efdfc1604f1f51407fefbf8df022608fb0f05260fe9f7f8d0f80cfdc3fab7f3d5edf0fb17d40822d1fa04e91827011ff3e5e2fb01ec0602eae2f903f7df0b0bf6cbf10ee7e9e000ffeff5f8bdd3203608e20bf8d8d4161108fe1cfcd5f20c0dedf2e6fbf5d207ffe7d9e9f82609eac0f8e6f1e80cd5e6e4dad5d6fee4eae4fbd6fe091400d5e800c7df04f3e9ebf1edf9defc0a0654e900b7fe1503f3e5f4020e01df211ffbff140609faf5251425210e05f3f20f1803ef201005faf0dbef0ef7e5130ef5f7f80c060bf300e3f2f11219e7090f0cb3f1fb02f003eaf8e2dfde00fcfd04def20af5d9e3040a150be8ef13230025ef0700e3fafc1900f0f9fcf809fc001601f8f50e08f0f5f9f3050507f1f2fbf1efe80a202f070c0533152cfcf40521e4e6210de52ef12d0ffef60acdf4130f0716fbec2acf12faf1f61e28cd264cde002af90ff3f10c110a1b1a0fe00037e113f757fa051cfaf21a20091a21f6fc16fc361e031347550505f500140c00ef05ef07120cfa151bda0efa280407fd0705fc0d2a1c2bfb1300221a02e71101feddfaf30fdae7ce00dafdd8eae4f3eb08ea0c04e1df02ebffebef070aedf0e000d309dff105e6e0fffcd2e602f9ece7cbf216f3f209fef0f9f4f3c3ba0a0118ec0403d7e113eceef900f3dcd9dff0e6eeeef7f4dff212d4f4f30b1de4dec6e1f303f9fae3feefd7d8e50eedf100fceb01f8eafbdae4e8e1ecfceefc06e7e2fbfbcef200d2eb0af0fdeaee080401f515ddefeae9fb06000206fffce5f2e7d5eef203f8010c00f212ffe7ef010607f7fcf3eaeef1fde8edfff6f30704e6eff5f005e2fbfdf4ec0dfbf301050902ff0aeefd05040cf4f9faf7efe907f2f6f9d5e8e5fe07fbfbfe0af1edfce4eef7f204fffafaebfff3fbf901fb00f3ee09f5f0f40e051e1303fd0bc5f3e80ee1e2d5d8d1fae0191df4df16edfe00d943380cfaf604d7f6e4f316ffd9f30fd7f4f6dff1d597cf0eb9e922f903ec0401cbc4292217d915f8d4d62d1202f20b01defcf4ecfaeef8f5f3fd07f2f2d5ee192621f1e11d00eaec03dedfe0d5cfdd280be81504f5fd051709e9e1e1eae2ece819dde1f6eddbeaf0f3d3f81711f5f9eb0a390ef710fd30e6c430f5e216101115dfde0fdc0a0fe81529dddd01190fce11152402dd031bf4fc21f5e1f6fb0b0f01422b06d0cbfef3e8df49f1fc0def012a251f0417370ff8f8123df3ff2a1418fae3cdf54af80d0ce9002c1103f927c5033a0eb80edb0ff600ee280dfc232d0f1ae90b040a1cf1e1dbf2fefab915fa12ff02f2fd050306f40bdef8ddfd070bfb08f6d3e8140a0118faef16fae11efdf3fddfcdde09f7f022f6e504fa050f11e609b1efcff6faf3e40110d0d6dff212fcfbf3f0c5eaf701e9fff7d40504ebc2fe0103efffd0ec09f122ee02fbcd021314cdc9eefdfe1bd1fcee01d80d260df1ff04cd08450fefefffff03e614f62a09d6fb252e09f1f51d28d7dc14f0e614f61015e3f307d9f6fb2c0304f6f027f50cf80cfaf921e7082fd101220e08f902021c09091af8f7fd41f6f3f462eb0a09211616401b121b041d1306050000f71c4d02f0edeb1b04f7db06e1ff04fd1f1204dbf6fe1cf202e4f8ffe20a2c0904081af8130102040ff303e6db03de11ff2011f7051c2c33ff0f2129e2e72920d51800fc04de0911cff4020d072bfbe8fefe01c50f373d14e0fc06de011bffc30c141d070e36f704e2e712e1fc007c011600191424211e23131b2df60209fef8d6052c0717e9dafd30dce416ec182b07182723e70e20f8f1fee51707d7fc230509ea2b060c1c0df70b100c05fcfcf6f7fa02f11008e7e7fcf316def6f2f6f2fa0600f2fbf8eae4f400f60403080603fdfceff805eff9ecd9f1fce8f200dfffe7fefdfdfbfff4f5e800f90afaecfdfabdecf3fae6f50afd04f2f3fbfdebfeebf9ec03f109f9d6e50094f1e8f910fdfbf102fdfd1df809ffecf3feeffa02f8e7ee03fef501f80601f1e0e7eb16030f10f4fec0f4feffdcfed0fbde10d7f61feafb1ce4fdf8ddf9181a0f0befdaef13fc161efb0a00eb0104fff5e7cef600d9e0fefff9f81bf9c7f4110b0ce21419d9c80f06f40af6f7ddf4faeff2fa09f3f6eef2ebf0f6eff1180a04d80ceef5e9eadbedf9efc4fb1600f002efe40dff1effcfead7c8e9f5ecfff2e3efe7f0cfdce2f900ea190519f303f11a0f19e0e80ff7fdeffbfa071504f9cee91adbf903ef0807feeb140ffe0fd0f2ec08f7deeff708f600061afcf1fee9dddfea1af8d4de12cceff2dc0a11fbfde5d5e9fdffe8faf5defc0adee1f4f5f6e4dfdadbf5f218ee0f01f3e0130fec09f2f00c04e3faf8fde0ec111cfbf50af30415faf2f6da1308d7ee0e20f2ea211f2a2ffaf1fe33eee63428dbff080b0debd3eeda13f308000ce61402f8f6e3ff232517ec0222f3f6fdf2e9f90b0ff5fe3eedf9f0e130f3f9fe61c4031aff05fc301ff61d1d24effe0b14ee0400d621e3df00ed1e04ee17e3051805eb002f0805f0d20909f1ff04cf15162009f7f41203fa0d06081ef9eb0f0ddef1211800dff219ff060304f7f500eaf018ea09010305cdff19d515f61d0005f8fefd1501f1fb0f15f5f9070e05f3f6f3eafd03faf903181cf4df0124e3ff03140200fc00f0f901f409e90709faf2fb28fff917fb070aef00f3eef10c0303ff12f7fdfef50ce5fc05e807fafa04010220f611f412fbff06fd0100ecfaef0308d924f1fdf5e51d120e07f605f112ddf01007b60bf70312e014f9bdfbfb181c1df6062105f7eb01fefa03e82243120206021b0901011ff81811fc0fe8392cf7f13ee80b2fe317e311113c2003fbf6f90e000d11ff4406070cf4125312f907f00c00ee04151bd0faef05fef7ea01f710071005fcd70606150d14d8310126f302fac3211c3bfdcb02281f36f1fa0326c402220dd817f91512caee0dd701ff29030cfa0117d30af81c101921e63e3ff3ea2c0f07f6fafc13fd3415f1eee92d0f01f64e080a0919140b1919271e14040d0d1405fef71e25170605082b440ef60dd2150602241b3bebff231af203e81201be0c1f0304080f0411160ae60b120b311dfa09ede7fbfae6f9d8e5cdee0002e81c32f41617f807f5f0203409fcfc01edff0307120b12f916e1f9dffd04eec90220ede9fafae7e7020cc00a2e26ffd512fef5bc2d02040b16efcecbf4fbe9c91bfcf6e00defd8fafd1e15180ed8121ef206f5f9e302f4e7fceff8e90be9e909081ffbe9e700edf3f20f1de7e6e2010ff1d5eae1f530070ff2e8f213221a3625f503ef1ce1e404101bfaf0d213eef207fa01ee0e02eb26250119fdfc14150ffc01ef1115f408320efc0035040cda1617d6dff60cfffaed07f8101f05e90921270dffe147fa0f1cfb10efefe6020aee0e1400001a13e9183f0edb1221fbf51800fc09fd3d08131017ecf601020514f913fbde0214f2e9f5fe03f9d6e9f505d5f6fce60af2e605fcf9fd0501e0040af7fee8fff4e0fbf9d604f102ecf1fee0f6e4fef8e6f6d60201fc03fdf90af0eef4eeeff1eaeee202f0fdeff9fffafafff7faeef4fcf807faeff9f701f4eef7e5f3f5fbf405f902eff1dfec02fcf3f7fdeb01f9f2fa0401f4e8f204f303fcf106d2fac4cbf403f1d51310f7f70ee1fd0615f1db09bffaead2fb0f1408f7dd0300f40914f3fbfffac008fcff01cad3f6f5e2e4ed02faf0fe0b0108ee18bcd513f701e4e2c10ebeefe7d406130ffdebd7e2edf8f105e7dbf20cdce200fc0bf5e6e4d9ffe615000411f9fef7feecf7f7f90cfef104fdf6e0f9231afa01fdf7ff1dfbed0f0334040e1eec3900da0b1f39ec342ff40e0fec360eadf4000a0ac80f05f7ec1d1920fdf9e5f33f5ddceff93014073a4355f32737fcfc1be6f5eb623dd5cb0f7fc3f8127fd230f70cd3f608ebda1e2507e0e0187fff590e2418f3cb01207fc500250d071221e4f20c0bcde71d1d1bf208ff0bf9710df9fd27e411ef130e3915031214f802030ceb12f1f9f0fbeef9c1eafb0c02fcfe4ce6fe1305110f10f8fcfeeb11faf1ef16fbdff7f1f1f502f2ebddfc10f4e5ebf909f5f801db0ffc1e08d7f9fcc7c92afcfafa0d00d005fcf7f2ec1001f5e8feeef916f7f31f1306dcfaeefaf60de2efe1ffecdb0feff1edf9d8f70308fcfc07f5e6eb06e51301e7d502d504f6efe83006190ff9fd13090bf6e9f32dcdf4080fc90df50306ea010ff105042e01fcf5f608eb0df617102518fb1b3709101a1bfaf90506e9f92b11f7fc01510314ec58ec00240e021224310e08feff1c0d2637fd01300e1af4ecf80e07fee4fc00061401f5160eeeea04170311e4f904ef0d2e1f0221fc13fc0616ed16e613eb08f5e90845fe0d03f01b1203282c21f80aed1e01f535ff12fddcf0fdf3f7f9d5e0121800060b06f1182f0bf1ffe31c08ff1501fa031e08f0f735e7f4ce0cecb5edfc140202e0fcfd071ee908f9120bf804022efc0af0e4f1d2fcf7db1afde5101108270ef4f83814cffebdeffefe0df411fe41e9fcff18f8fce409110f0aeffe0706f016ff0cfb14f4271216e707032fbe0923eed913fb210bd50a0ef8ff081a080a0dedf9f7150a0af62918f72644eaeb1dfb01fbfffbf604102ee100e14e08fdf24ffe0714fe0d0c0b262a1dee13f30224f407f72a28f011df041502f115eef90f2c0b2b091ef5e20c2413fff012fd0c082c112320fef706f1fbff1201e9ffe0030df0111ff3f6f4feeb09f7fcf5f8e2f0de1cc3fff3e7ffc5022dba25fc12fafe0bf4fbeefbfff91027eb041f072806e0f0fef71deeeb09333b0cdbf411f3ea1711d6f7e5effbf50c1919ec0bfa07e7f235fdff2d281503eff700df0d1a0df7fbfcf0f80ff21bf52617ff0206f00605f955fcf1ee17fdedf4f9f01080fa00d912c3d11510efdff0e54906fe15fa6afadc3c15af08f908f8d6d5e2e6e61e02fef2eefefc180cc2220e071902081ec6db1c1cc7fb08f915f56b121ba0e1e9bc38df6bdf09e500e5fc2c03112559180f034641e5ea29301100d7d32d70e7e91ddffe46f6d1062404df1dfce701f41709d0fa7322ede83a0ae0fc1bfef334d807edf007f9fadbfff719b1c4d7dcf4f6ea2407c9f5f9ee11fa04550cec25f002dffff2000b04e1f114e6b2dee61b16d8f807f3f90ae2d9db07f3cffc67220deb26fe02b717fb02e91901ace9f6e7ead80dfb06d6050ce1ea050b3323f2d8f304ed1318e6d4ecbbc40416eef510ed16f10119fed2dde501e3ec14f7ee1200e903cfd2fefde7e3060708fa05f4f40bfef1eb02d2f2edd8eb070400f8e3e707e60206f50308fcf41604ea10d7d4f800faf10af7f0fef410fd08ec06d4edeaf300e5e2eb12dff2fde7e00204faf7d9f6f9fced01edc7faf7f3e5fcfb08e9efdce8fbf813ed0101d3fdf110e5e7f7f10a0cfdfafb09d1f3ffff01ff05d90a100700f81d10112f19f1d2dcf905a4d3d1def41be2fa38bffc250016f8031eff2c1b0bf7c00b0bfa0e0ecefd0ce2d9e1f1f1cbd7f00bdfe60fffdedf0202af092336ffea2fffe3a21204fbef17f9defa00cddcdcfcf9d4e203f0ebf215091315f6c4331bf0f1f7c8e90ce0dadb1d06c319f0f8ec0e17f9dfddcad0e903ea17e4edf0f3d608ff0ced02e819f7d4061c10f80b091233b711222feafaf11701d7fb0ae31a0207050ee50913d9edbbfd550b04dbe6f1f1f214fed5f2e80c19fbe2faf8f6dedff710143c0207f50c06140b05151f0422f2fe16f4fdeffde9f719deff21f407f010f2070ef421f935e4e800ddf900030604c5ff0c18fdfd0603f5ff0bfd05190ef2dbf1f4ffc6cbe3eb01eedee4fbdbfeb301d5d2d8f014fd0ef7fcfbecf0e4f9f7eff2f009dfe4f5e7f7e7f2e7fbf7f5e0ed15e304010ae105e3c7ef0c1b12eaf1c8fee231ed09f526f0f2e7f5d2f1e016fff29ff213d70df20e21dee5dcbbe7f00b11e2f0eaecdecbe4cffce305f2de0aeaf7d6cf040b0405f5050bed14e505201510001ef60512e9fedefecd03a9f0011c19e62b0c17070ef21e3a120b34ebf9fcfaf40c14e5f615f62c1fdefffbd50c1cd4d50afff2eafc03df161a40faf22604ddba5c06f3f3f105ef0d1cf603df1afeebc5000804d6060630092ae70619e8e913e6ee17f8dde4ea18041af1e90bf513f8e4faf0e500f6fc29e9f2eaf4dcfd14f7d00f0e23fdd90416040cfb1af71eb9f30e1bed0b0af507d61200b405f7f30f0aeefb0409f8e0161f0b1707fef4f90901eeebf90dee2cf636090edbf00efc0a0b350a07130400ff0cfc240e1200010c0b1cfc101de7f105f2f60344fc0118ef080dfa131b2308fa08fb01fcf3ef03edfc221f00f40df5ebeff5010d0a032cd6fadc14301707f519303a1efeecf225e4d519e6e21e09070be2be06c4fd040002ebe9ec05021ad80e012c1af31b3adef305ff0eef00f6f9f8601406c11b47d609cd7f02110015f1131b2c201939fc1aea2a34020b324203f5d1ece944f8eb27d41241f80ee638d0ee3a0a0108e000ebc9f64e240bfd41011d1f19f2411604f601fb32c1f703030bf4e9eae81e2e26e430fefcffff010801fd38eb102a1601fff40103faf423ec0b001900ea14f1e2200bf315fe0c0004ddfdf31225170ec8fcea03c230f5e1feeeede9cffae8f50bf403ee02ff1dcdcbf8f6320eeee0fe18f628f5ec04f5e2f11e110bf9ff0023e208000be4f80508ea04e2180716e414f103030aed0d0a24f9f402272423fcd7141aaef0180efdf0f40cfcc30422cbfd0a1f1413d4f410ef0dfc1d201b20ce0d38f0fa20fdf8fee80434f73225edfee83a11f7005bee081d290a152432380c090b090a251d04f7321ff8edf012081f070202db131f051f221cf7141726fc09cf0f04f3043615e3050a07fb06fbe00500030108030e0409c1e9d6fae0f0b3f1f2e3e90e2ce7da33e8fbe0f12f04f91d0d06aff2eaf0ffe8e500f9ea071ff204fbc0f802f4c9fa0104f5ef00c40af20d04e2ed01efcc05faecf604e5d508f8e2f8f3e8f5ebdefd06f6f60ceb2c140bd5140003d3eed9f4cfeae2d414eff5f509e8120110fae4efe6efef05ebf805ebd60def0cf0fbc51bfe09fd03f41227350c020414dacd26d1d011fa0f20e0f22de9fc0ff31722f2f3f7fa24fa1ae2121ae1342ae3f3190cf5fdf4002eff3b0af3e40041e70ae90fea0b0c0df8172b051c0628f618ff14160b051f3039e8f1f81d26f5111bed0e2312f4180ae5f3fc220003e6f5fcf9ff3b0b0b0f20fe18eb0efa03fbeae40804cd1d3b24ffe701fb230de738f11df9e13916d026f61516d5f317c9fa0d0418fef7fa0d2aeeff0312281205092201faf203e1ee201607013be907c5d81acef7f938fd070000f50d1e0f1a1d230214f40741000a1d0b2915e4f90007de0613ff1c1b0ff3163e200f3a16f8010b1afbecfc450606172d040504fcf90308e2fdfe14da0e1816fedefc1a1823eee10210d2ea2015c71cf405fde00f15f711f30efe0edb08f7eef4d0fc262a05e504f502ff13fee7f71323010212feeaf8c5fe0e01071e02081a0a1417140f17fe08ff16130adafb0cf1e9fc00f5f9fc1beef0f2fdf62cfc071303f3f00fe4f1fcef0800c6fee502030603081012fa0ffa08040fff01fd06e7d1fcf5e7f9f3ecf7ef1ce10913fce723f8fd0b03130a01dbd7edfbf415030cf9fe0312daebef04f5d9daf409eafbfe04fc03e4ffca031f080dc2fef812b42714f0fd2a02e4f0f90be9001309e7e2f9fae6e1fa041ffee7c4f9d5f60e0beef819dcf5ff08e8fbebff00f8fa18f7fef309f8ecf0ed05f6fabef7fe1101f416f5d9b1f6faf3bceedf02c9c1df071feff31be4f7f2f522f51b150107d7fce40417fed9f9fbf7e6edf0f9dbdbfa02f2d8ec02f9ea0600ee18d707fdbefee2d5fbe2f9f3f5f8f9f5dad8ea05f6f8f3f301ffeaddec05eaf6fae8ef0d0ef5f7fde9fcdcf1d9ed0dfbe205fbd8fcfa0000fef5faedf103f1f500d6f0f6fef4eee41adae1d4070c0ad1f2d71bfb01ef1a0ce1fb04ec0df00e0ce1dc0afd02eb00e50419d8010f00f4f6ebf314d9dc0b0deef9e807090add05e3f8000002def7e606b7f2fdf600f001f9c9e2f9f8f4fbf4d4eaff05d2df12120506f2db160cf006f3e906d6f3e812dcf3d702fb1cf504fafcc706fe0de1f4e9ea0411f80cfa02fff9fa080df4f6f40aee0914040ff0f6080af0f719fc00ff05fcfa07f20200fa02fa12fd06fc06fb02fc0cfb001501eb03e6edfbfbef080cfd1bf5dd01fefa060d041ae9fefe110c07feff0ff50cefeef6fb1df6ec05f9fdfeebfdf3e908f5fdfe0b13f501f5fe01fdf9f4fbfaf403fc0300f6f6fdff0a08fa01020515e407ecd40bfef5eae704f0fae2f3fc04dafaf7eee5f7f8f4fd06f307fce9e8edf705ebfbfae90107f4ffe6f1f8e8f7d8f2edfbf3e9fee403f6f4fcf6ecf5f8ebf300d6fbefe9e501ef00f1fcfff6fffe06f701fe03e10502faef05f2ecf102e9ebe6f7fe0205fb02f2ebe7f0f3f2effbf700fbe605ddfcf3f1fbfafbf501f1efe7fa04fdf0ff1a0b1bf016faf80d21080de81ad90930fa09f9f30502beef07d61f162500f8f4ffeaf6090714040b14fc170710fe010bf6fa121010ec1c15e807f137ff10032cd90df209081906101619f705fce107300d0b1e172402e6060a02091011e32b1409e81b0ffe09ff1c19fdf8fcfff6071a20f301f0f0f8e9f30815fcffeef4f2000d0521f10702190811f9fa1834d7db040bde1bf61b09d9081ce419fb0a0a03ec0d0d13e6dd0e3109fddff914d1f419f3f5fd030227fe060508e7db0cf1fd00210207130603141f1b0e25180e080c13e607070d37f8e800dd13ffeed900f0ff10fe010d1ee404f80ee70cfb1804c5031af700132210ff0ffbf7fbf2f9d7bff8e7f5e5eb01edfae9f6ec12d2fcf3f9d3efe2e1fd0ef102ebc9e8e4e504ebffeae509e7d405dc06ece9f5e1e3ea0afa04fbe905f9feeb00d0d2f5ce06f5dae7e5c701f2f4fffc0102ece4f102f1ff03f5e2f600f3de17f10fc0f6d7f5d8f4f3f40103ebf4fde9e2edf4dffdf6f4f8cafddcfeee040100f6e106fafbf2ecf6fcf2f316181ff1fc04162c0e150bff36d5dc240ad618f9f213e30bede429102afb02f108f1f80ef2f91b1d0ff9091e0bfd11f900f3f40e2c0b2613fd06070b0b1efc3af41e0e11fa111019230a140efaf907350a0d1d13fc16f7df0f071818f8f3fe06fcf8070917fb0d24150df105f0e7ff232905fd04181b1c09db322608e6cf0200e9ecf3fcec00d4d8fbf9cfdef7c1f3cdf4f3fffcf206f1bdf2e80407f4f4eee0f707d0f8e408efeefcd1fbec0500d4f3d104e2f9ff09dffed3eaececc8f7eeeac0ebef09e3fdef03f2e7effcf4ebf5eb02f0fef700fdddd4faa8f4e3fcdffb05effaf7dde9e0f003e109eaf308d3fcf1f5fde9f0f6f9f1fbe2f081f2efc7fce803efe309e5fcc4e4e6fec204e7e2dae7dcdb0002fa02f6efe9e7e8fecbfeefd602eccff1e0f8edf4f4cafce0f503e2e9d3ff05e4ffe7c7f7f6f2f404ddfae0db2300fdfa05f7e10bedf7f5e5f6f602d000f6f5fbe9011ddbfcc6e5f6f4ee02d1edfbfefec2d4e4f1e1fdd8f2f5e901f0edf2eaed06f2f5faeb01dfeb10fd16f60419f201f008f3ea07f5fbf5fdec19fc0f33ebfdfff63fc90efd10f90b0108df0c06eeeff8eb02f8e10ef1e22408e9eb0301e8f507fcf404cd07fbd410e4eee5d3f30306e4fefbff0ff4fe130403f9f000f41ef1ea03e7fafdff0a0b01cb02fcfdfd07e6f91112f4fe06e5f606f9fbf001f9deeffc030200e5efd40df3f202f5120735fee8e51c2d0f090dfd1ffbd240ebc00cfc0107050706c6fd1116100813e41e0607ef1709312a173a27e9da132c0af9e4ec33ea4f2f1b9ffa2cdc33d17f0f0e1314101520201c43421e0209494b00fb193c2605c9f6fa7fe9e822ec052f08f42833021f113ffc0e0201fd0b0f4c1407fa23fb14ec2710181be401efffe219f65f060c123a1d19fcfa2727ebef380cdd2cfa151ff0d6fcdf000b331613ffdb143e00f2190d1e0f113337f20d0709f3f4fc1027012706d8ef113c030be144fb0b18060e2c343e13160f071500150cfc062d11eb01c5e51323fde002fc171c03ff2827fcf1102df514f0fe07e2f4481dee0c0f1f06f7f91319f3120313fccd090f16fcecfe0f1d1ef3f3f012beff0901e10ef60211f3f50dd9ef05090503f2fe04c808f0fb13290ddafb1efa0310f4f8f8fe0efbff2300f9f7ee1bfe04003c010c191501231125280d0007f6041c1ffc151826fc07f2fc080bf9e715f60d17fb08160ee6e9fb0af603e70401da0f1e0406110cff090b04f211f90acdd500e0f7fbee09ededd6fbf5fdf2def2ddd6f2d7c5e8fb0cf3cfd2ecdcf403e9f7f8def008f601c402f6eaefe3f1ee09010ff0cf03fcf4f5f6fbf4f2be00efa5ebdae8f5f7eafeeff916f6f3fd050a0301fc02fafdf1eb10f800cdfae8c1e602ed050704ee0ae7f6cdf8f9cbfee8f600d0fff501eff9ff0701d104f4f7f0f20c0e0df70afad7f0d704e9fddc02ede7ff0e1e03fb2cfaf9f4f8161008f30601dffef2f80403edfb03e90309f2f9f2d4f5f8e0d303f702f90501fef1e60bfdddf905f2e1f1fc02fdfbf4ea16f0f8f505fffef8f204f3f9ec09fefc0603e90efb01fafde0f6ed02f3f8d9e9f8f804ecfb011307ebfdfaf1eb07eef302f6f3faeaeef602c51f3308fecd0b072213ee1acc0de6c122eb0621f4eff3cddb29b6d314fcfc0afd0efe2bfac320011a13f9eaffb0d5f2d2c6e4fc0ef4041f05c9cefc1cdd21eb3ed422161a100d1a2d07191b0b060229251a1012fb16e9d9db0c55d2bd0c0320f6fde216101f2309efe8ef1109fdf80e2c0717fe1a1fdbe3ed1ce50b08f9f6f2f1f60f31071f03fc191700f6f5fccaf803ebd515fcfdfdf60618dc0f0622f71008ee0f1cff09240a07150518101a0406fd020201100b051d17e9fbe839e70bff270d14fe08f700121910e4e2e90309f3f5feed11021af8f702fee8f912ed0e09e6fa0d0a1203c5011d070100effdeef721172305090118fc00102b1128b3d3f8f7f706e60bf8ec00f50408d8f3f8d4e314d8e4f60308efd8e5e1d7e8f6fbf5f3d90006e102dafae0f701bfe7de0616f2fcd00916f8fcfee8f607c201019ff2d4d4f401ecfb000900e9eff2e3e91a080809080bf1f7dede0bccf2b3c7d9f8e8faf8f5feebe3e0d8e8fdb909da0b05e706dff1ec01fbf706e808f2dce9f5eed903df202634e407071e243214060626f1f71e04d224fb0608cd001ee0f7071b201103e71113fee9252c3610f81115daf92916f9ed070b28ff30220ae7031ef40bf555d90e0c0df70d30300f1314190e05fd19fbfd28391920eedb0c22f0da0edf0217fe1121280421fb25f302070705e90e3816f4fa2215fcfbfd0213f41404e3090dd7f43319130c00ef06061b10d50fe6eb1de52b00e0fff2efe81605020510f52b10e628e61a18f1f7f331f2ff25fffc25060b070cd604e5f9fdfcf8fcf4fc35cef6ffec0af9f4f6e4f5e2fae60d07e4e7fd0602e71bfc00fdfae1ec27f022e6eb01fcfe1a2ce2f60f090544eb030c08f0093c1ae0060af8fb3409ef070010eff514260af702fe1d240ff021f029d1f52732fb17fb040d0a0e0ae9110f00fd13f6f314ee18dc1a2d2f20f30117f4ff07eae2020ffd19f8431002e9fe28fa0ef67d220d1600fffc24232f221524fd053a3ef5fe5c02ef0de3fd0f63f8fc1fed140bfb1b1826f11216ecfc10e302fff8012d240c053806052cee0527100e0a0afce7f8261cfe14ef132c1eff2beb17e2e34e25d315fdee03e3ff07ecf40203000e130af70a15da0dfc0c050a2c4df7df0f0e00f1e9033b0b442fe5aef220d603fd7cf8210905f21728011f1326f2fee41f790c0b45181117c503ee7700ea15ebe2320a060f57d1f6080b0dfdf6f50907224812ece63aea0cf3f0fd30211e0507eecd102223fcd112221d1ff2ec041fb0d6210ae132fa0008f30316dcf0010a0c09f6ec22f523f90f14121ae43938e0e722fcfbf3fb0b28073916ecebf52efc00f16ff00f1b141906001b3c190c0bf8f9231d070e362e1708e5fc1e3f08f603e80d23fc1a0d13ebfd1426fa00df07fff305361606fa1a16280ff9eb0a0401),
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
    .actor_error_o(error_actor_context2_pointwise)
  );
  logic error_actor_project3;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(65536'hb6d7f0e0e9c80003eaecebebdfe4b6fbe8d3d9fde4c7d1e0ddd3e7e3d3f4f7e101f3d9e9d904f0eaded410ddf6e8f1fee4ecd502d1ecebf0f8f3bcdcdfd8c903cad9d1dbf2f1d802e3f2ec13c6e3bf0102f0e4f1fefef0fbe1c2fad3fcd5e0d6d8d8e0dff40ae7ddd0cbd802e8fae7e302e8dfdae7ecfce4d0e9e7d9dbeabde4bdc9f5dbd4c4ee01e9f1fa05bcdcd1fc02d2caefdabcc403deefcddadfdcecec0bf2ebc8e109f6eecfb5f3cdffcce805def0d407d6f2e9ecfbefb5ddfcc7cdffbdd7d3ede7fde3d6c8fbf1edb6e8c60b06ffeacced0bd008f5c1f1b4fbc0bbd6e5d3e2d7f501f1ceedd7c6ffd7ff07d702edcee4d6e100e6dcf5d9f2ece1cfebd8ce0adfe9c1f809faf5ecf6bdc6c0f8d9ddcbf3dbbecbebd1e1c4eedbf2eed203e4f6cdeef1eae7dbc405e2fdcaddf4dce0e104d6f5df01f5f7c5f3e9cdd8fabce7cbdcea09d4ebd0f6e6ebb2e7c6fbf5efcbce03f5eb08ebbbe9c3f5d3cadbe6d1f0d4dff7f7d2e2d2dbf8e9f8eed900e3eddae6f405d7c5f2e5f7ded1c5e8fcfefc04f805fcfef7f8fbf8f9e3e9f2f9f605f80205fdf102ebfc03f90afce603fdf703f20bef03f506fcfafcf8f2fdeeeefaf6faf4ecfff8fafd02f1fdf90601f8fddcf406ea04fdf6ef04faf7ff00f3f9e6fefef6fd00d608f7fffbf7fffeeafafbfff307fdfdfaff09fefafff2f800f404e4fcf4fa07f40003ffeddfedfd2c2cfe1e1b49160102fdf209440e1bfe11044802153238fe46193318261a101c1201052b21f4040c2530fcfd070d10f714f7190619f412ff14064416fe1c15ee332d2709f90f141a0f00121227132bf90311f12d00f80ff21a380227152c3e200b190e221203ff350c2a12fd21000a20fb101afb0f13fa1e19062812f0061afa00fae7e005e2e8dbb016f842f74f3c030cfbe7f1f5e1f81ee030f4e4f9d6af0ce5220f11ec15211e05c1b21f2310e4171135160819044336d2c00fff15ceeefefcf5fd2d0d03fb01e936b9db0efbde3f091167daffd3fe1e100721eab706ecd752ff19ea38f4abc71502f70cf4e50de00601d84dfe0105e40d1b02fb0c1f2612c3ee061732de57ef40caf40bcc03cd3f1ac4f819f804dd00dff1d9d1ee0c6d0df856d6b3f71d80338416230f22e33b341cfce3f7aad3f62d0e43f12acff1d424e6ecce0ff7fb6e3ad8e6074e1315ca1cfbfb0304f81ff8fbe5abe4da4fdaed1d06deecc4b8077cfaacbabee7ed36ebf3f5c4bfd45e1037c733d9f5fdb81b0e12f8e9f5dcd9051405fb34f0f821e6161ddf1af1ede4d8123b0e1903dce9ebe6eee9cd1c0041011c8e1ed8d2d9d109eafef7fffb362441c9030ffcf4ad3cd81cadf9f4e1da31e3e0fad919edfbc4d5edfcfc47ecf3bb0de4e1dfef2cd2e6f1e5f9e41fa1eb0ae3f9023211c6f6d0f83ff00516d5ba0abe2de5ea1f09fb3dcc03e1efaec33f24b73ee4dd372f7219630b7e3217e5000b80a16eec7fc6f386e0a97f03fb66800b05282428e1e70a2fb0df401a654572286c07e47fdc25b156e7f8641f228d7f5f3d2f1ad31313cd4424d4f5ec207ff8e1263f06fff12fcb3d57fa014b03afe96b1706c9c1fa2b04e1e8f94ef6fa873b7fe5718049362d2e7f1e5b24efe707e2f6d9f8f7f904f7edd7dfeff2f8f2e4faeaebe2f3dfd4ecfcebfaf8d9f6f7f0f3effef3f0e2ea00ebefebf5fcefffe201ddfaf3f5f6fac5fef5e6e905e9e8f4cffcf7cef7e4fcfc09d8e5e1f8f4f1d1ecffeee7f5e6efffe7efd4eee7e4f3efe6f001f4e301e6eb03e204eee0fdedf4f0f7e904f2e8eff3f1efd2cbfdddcef71c49e9550505f3fa17f225c50457a8e65c05f0e4fbf502f401ea381142097ff8a3e5dcdc64e405f12b3ec10e22605600fdc4e12a114c2d30df0e08c63d0011dc10f33247dce40afb2b137fe3e7aeda0ef94111181811d7f8d62f09ee3628d335dd121f40f090d8f5014b41d1fff1f1f71c711f05d65322072fe7401338200bd1caab03e2ddd9e3f2cc1dc13ae5c031f3b1eb131cf7f1e81ae5faca99ddfcbd247f110750a32ae6e082c47ff1c6cdef040c2be6ca08daea1b9f1bff28f91acd14d708c4bbd7feeb14fdf68510ec0bf8dbf6b3eda00dd64f1e13d70ef9d4fd3b8015c8e4dcfc6f14d51209cc39f80f48c805a7e4f3e9b0edefd319ebdaace4cfe8f11dd80b0ad2ecfffbd71f2ef52cf2cb09f7a4aef2c2f9cfdcfcdefa21f51dd817002e3d41f9d522060afb06103a31ed250df0376d1ad7c8f7c8cbc340dbe1bf37f32b0ef8cdfe270c0623e6e216fc48cc0de30d0efffdddcef5d2d4f478ca07d571f2f7be23c31b131c0718f9faf4114d163619e3fd2fde22e1e22117eeecf6e5f3cefafdfcf6e0ddd3d0daf2e3efe5fde5dbe5ebccc7ccf5e2f2ede2edfde9e1f0fdedf0dfe0f7eaf9f5eefbeef0cdf3e4f5e202fef9c6eaf5e2eae8d5ede8c0f6f7e7f7e0eee8fce4e7eaef00ecf6d0faeceef7e5d200e0e2baddf0e7e8fcf3edeef6dbf8e5f3f3e5fceedd08f4eee3e8f1faefe300f3e7f0e3d4e20616f9370c21d60514c3f4af14f7d7bbadf31caafd3d06aa0a8011ee36153001fe0fc93ee2cec00cf10f0512e605029df6ebedb8f5bbbbd1a108281ea828fde71a133dd5c6fd101620dacff714241e8edbc4f11ce6d61d09d029dc3c04131ee9a5dc14249ddf0810610122e331e9d006e7ed3badfd20b211e5faf0d7c7270721fff106f001eeff03f7050600f7efe907f808ecf5fef3fafcfcf3f4f5e5ee07f609fdfe03f108000205f501effcf307f2f8fb0c03fa03e014fbfbecfa09f6f6f9faf9f9f007f9f7fefb07fdfc00f3f300ff00f4eef71ceaf2f8f202f003e5f4fdf4f1f803e80cfaf901fffceff3fd01fe03ed00eff505070200fff9f801faf3f3fc0b28e0c318bfcc12e4d9c3f8ddbbc4aff9fdabe41416e3fab10304330806e60603d621c4cbb2db052cd2b69f0706e1d98002c2df9e80cba70ee395b112eab6e3dc47e2bbf1cd5131fd00ece5fa05e5d603c41985d2ced817040d4219fb1dd4bd138d32c4c5c41bdc020fd1e8f4c6d308f525c9ef059a14bd92fba6b6f5da801442f0f9e61fa919baf0f3f821c21701802b0ee5c90343ec22e01fdfd7e4fbcc0eb30d7227ed59be5305d7ce8a5e14bfdeec26fa450fbfbdf2b229801c2d2cd430fe21ebfbd183072209f5a0e9ac2be7f71cd332baef15fbca34e743803030dab91981399eeb801f591c181fd6d21c010645ff0487e8f109cc020eae22b025df2804b6f1a7e9f91ed80ef2ef04f733ffda36ffedcee90d07dc03f8dafcc4e0e7f4a52b24141c38cd1fe1b289a52bf5c811ee0e112926db09d9d80bc415d02480f011ebf42ab2edfaf716dbeff6c6fe10262101dfc108b4c6ef2905040703f8de012e8800d0d4ebdc121a1ff0f9e1300d010df5e7c3d3f519c3f1f20125da11cb0be4f7dbcfea10fef921e41609c7211ae307f2eef8db0953073dfdffd8f1f5fdfbdeff0426f616e10ddd04daed0bf001d5e5fe2f0837f0fb2100f4ed2ae2030ef80bedf315e9f1e7ea1e080ad8dff4251827d3f6fefeeaf1d2f21de0fdf3e0e2ef05f7edfdec07fbe704dff508fb15d90613ede407f21becd2190ff235d0e8d51b1403edf81de6230fe00a0037bce402e40c1cede80726050ce70b2ff700e5d003bf041c13f3facb1c05eddcca13efecc8e00a080a00dadef3e30fdd122a25df1c0618c71ae9d9e122eedaefedbb23f7ec03c023d2e9fdf6eb06001cbd14fd02982bde0ad503dc26f506f703e0e4f0da031f02b3dfdb1419e61416d813cccde000eff10104f312fc1604f81203f401f8fff2f5f8fb02fa00f7fef5f7e70d03f802fafcfb020dfaf905fbf7f7fcf3021afcedfd070103ef0df914edfd03ffea01faf7f6fc0102f8f3f0fa040f00faf405f704f7f403010101f7f406f70cf7f9f9f4f4fbf0ec0a1df4edf303f80411f4fc02f005effc0101f208faee01fff2f4f3dce801dfe5cffb03f9f2fbf6d1ddcffededecbfecdd7d1ece1ddd8e5e2eaf6c8fff9f3d7e8fef2e7ead4ffdb00d9fafee5fce9f7dff8dd08f501c9e6e8d1d9eac8e6d5d4f4fcede2d6f8f6f3cdf2d5fafbfbd1daef06e2fadaccf0cd05d8d1d6d6dfead9fdfb04dae5e5e200dc04f5de08e2e3d8f3f5f4e7c9f9e8f4f7d8c0d3ce00deee00b9f9f0f00b0524d2fdff264dd7e24516d28101c800dfc5e7072cf0083301bbfef3df2fc8c146f4719f15f90c05cf11e5063623292bc11aeeb8b11ee6e09b0b04082c0dc12a32e7b5fac10f0d17f2cd2d2efefa24d305c623c7c1f75ebf01c7063220e3d2c7a1f7db381fe7fce0cb0c0a311cc2eb06da2ce004f618efdc07ece8e40709092712fd0ec61906fbf4eb03f5ccfa1fff0f0321f0fde1e41bc62cef1cf012ce06ced5eee8ed041105f0f614f82e02ea0de5fbde1ae901e203f4c3d612ed0be9e01e06f8e6d6eef91324e3e400fbe5fdf9ec1cd21afae0f3d709e9f2ffff04ee1202d817f10f27fef5f7e9fcfbcb0cfef711fdf00be6e5f4eff615ebfef13915120f0a14f6c81af6d3fffdb209dbef48fa2cff06ca02de0d1e0b13d2350504f5f5d4e0efc2ef021cc0c4ef0d0828ca023308f8d61aeff00c0000d1bf3a0cedf8fa1df70ff1fef7f406f9f6f9fdfbfe0cdaf50eef31eee707d7f8fbf1d0e900ff08eff7f8f5080be80206ecad1ef208f62cef04e720daf4f1dbe60f0b430108091ed81a0bf9229b28458df3f60808e9cefdcff4fd14343a2d2147afd5bc09be7fdffaf11b2da62e34cef2c40db0bce70d2d19ee3bcee7c366f9f5f8f8a54c313b17df21370a63e10b14d6d90a42274129d2dde5f827e6fb1a0dab68fc2101290daac804290133e224fef2f002294430e848541434a22ded4ed7e5fae2e7d6eefff2f6e7f7cb00d1f9ebd9cc01eed3d0f4d400d2eae6e8f7eef3fcf4d5ee06f4f3e2d7f1e0fadbeefaf303e3f7dff4f203ed01cdfaf5d7d4fcd1e5e008f7f103fadbf2eb00f0eadafaf6f1fecef1ffe5f4f9d9fadaf7d9cff7ebdbf9e3f9f4fbe1eed1e9f7e100fbe9f7eced00ecf402e7f5f9edfae6fbebf3dacfcbe4ebc114e80c1d1a10fc1412f34deeb022f4cb97f1c707dddeeaef110ef12f04c5fbf5e03bd2e22e097bd8112f0932e1dfe10a000b2325f324cacaa711eae9b736002c1bebd1fb420308febd2950f811bc07fef44a2ddff4dd26edc6f654cf20d7160824e1efd8fcccfd2d1cf4f5c3fded0f241ae10508d048c51bdf27fd36031915f6f6f2ee040b0610142afc2606073313fe05f40f2b1807f4fbe412df27d11708eef81312f2f41b3cf8f5d84349fdfa0e0355021d021104f511ec040b162321141a2f22ed22110b181eef281d031012fb4a191715f601ff0c06140f4adefe2b2622efff0707ed011c070521fc1000201b0eea0b3014fa1fd1f82622fae7fcf8fde90be9e7f9f9081025ec015ce206fc0aded705f528fff0d4dceaf90613e301f103fd1309f210f90e020a1d191e03fc01e73b34ff00fee7ebe9ba18ee02e347fe1b2302f3f5350fe909f81829eb04e504f6eb190f04fde1faf5f10137c6f5cc2b4508fde4e8f8ef0b1dfdfdf9f8ef0c17fe11e604efe61be120d7fae8080aecf614f8ffeefce5dc01dbfff1daf209eedb0c03e302e20ce001eadfe2e3ddf8f2faebffe7f0e7f9e7dee3e3f9d9ea04eaf8f804f2f6f907d5f50be7f3efecfdcffdf6e60c04fee0ecebe3f7e90002e501eaebfafbeb0b0dfee811faf1e203def5dfefe9fff0eacc09efe7f3eaf1f9dfdeedeef4e6db12f3d9f8e1f5e60a05171004dfdce00315f433f54f53cc17cceb5b01e6eefbe526cdf431e61b14db1ee5cffb08e925e812120c33d9180b2d13f5ecfe125d44fff3e010f0d30c07c70dff51ff050a21d43535021a0dfe1ff8227fdaf957e9f657dd0dd0fadb031660cf12dd1d15f6d6f2f1140b0105f12103fd155809222ef80b09ee18dc2e2b0fe5edf5d6ece9f2faeaededf8e6e9fbfdeaf9f0f3dbe3e5eedbebeaf6ece6f1d6fbf7f2edf702edf2efe8fedcf5f2f1f9eaedecfee5f8eeeee3f9f3f5efe6fbf8e8daecfff4eaeeebe7fdf201e3f1e1fc03f8cbe9ebf2eeefdce3f6e7f4f1eee8e9ffedf4f7ecfef5fceadefdf2f0fcef05eee9e3eef803edd9f7e8f0eee7def0f1e0ede9f1df0ef404f913fdfad2f01cf3eaeaf9e9dbe6ffeae0e3e9c70a00fe0febf1e3fe17f0fce2d70bedebe103fff0ccea0de600f2fa0912d3f9f9def306e3eadeddff04f6f1d2f8ef1ade0ae1ff0afacae30011f010dedf16da03dfe3e2dae7f6e0040c17e8f0e7e5f8f60af5d605ede4da05eb16dfdbdafdfeeae5bdf6faf00af11af311e901f9080bf13d1aec2ae2dd210ce8c901f005fdf705ec090ae936e5e803f62b32f9fc12033f200f19332be9f005d94d0210fcf325dcebd038ee01161306101709f22c17f504fce504f31c54f010fc13121ef202e509e7ec0f52ea17fb492505e1edd4090f32002317041a035c0b16cdf4fb0c0b2cc4282416d5e213e1e6cd0303fedafeeebdd7bd05dcd6cd02ced0d3e8d5cdd0d9d7f300c905f7e3d5e7fed9ecd7d703dff5d7f206e0ece001ddeaeaeb00ffc7e5e0d5d6f2d0e0cfcbe6f5e1f9d4f3e901c7e1ca06f0fec9dbfe0af7facdcaf8d3f9dfd0d7dadae2cffafe01e2e4d4de02e105e3d501f7cce6eef9ffdbcbe5e1e2d9dec7e1e8e5fcf2f1d9ee02f0eafff7dee1dcfeeae2ddfdf3e5e1f0e9e9dcf9f0f502dafdfef4dcf301f6f5e9e109e4fbe1f4f8e3f7edfaeaf4e7fcfc05d2f6ebdeebffddfae0eafffdeffde3eef204e1f0d8f1f4f6e6e007faf1ffe5ddefd6fad4e4def3e1f4e0f70200e3e5ddfdf9e4fcf2dff9f8ebe4f0f8f4f6d2eee4f4f6e8d2eadbc70707330946100701e938cc32d9eb3fd6e7fcf3f1d216e53accd8b5feef7f1464fb93dde0cceff4e7fbfb03a4054d08ca190ef1dbfcd9792ff545f0e2b654caf4db1400551522e6f8156a1b71def6fde8ecbd2e05e7fb00b7fad83adfda1c1cdf08eb23082804ade719dffd24ece80fc0fafb7f0dfacc2326f572021402eded16fe343f0a1ff93eec1afeec21fc0726e4ea17fd03fbe709ecfb250d2b371a0b1fdff3eefada4fec0c0a2127022c22110ffb07e8d31df7252ffd35cef3f63deb182d13df1c21f9051e21fd052205090add190313073c150deaf50112f81c2133de4a092314050312e611f01408e213020f14231d01eb052507140ecc242246ecbe1c385300222722eb0117df08f2f327cbdff3e713cd34fe18d724123907790855d3b9bafdf73eec05f4391bcb022d2715e60fd7fd150b44f4d731f3f8f25d02fec819eb501c18d9ebf610ec24f0f8f1d4f0fd54e54505e8f3e8f3ffecfb2315d073db401519e6b7e0f3263734d0d80b010f135e1000f83e4a3410f0e0f31a0a170113f9070ffa1e030d00f002f405ff13061f0dfcf0f906eb000c021b21fc020219f1f112ec00fa10072215ff12130a13fc0e03080717fe17f30df305fd210b0913050827e02407ff1a1cf3090c1916080507ff19141f000c0f0818f601f51bec1301080e1dfdf20bf7f61207e30f06090005270701070d20041fe9ffef0004ce1d547f0c75070cf50bf7fcfabc0b25c0060004f2024e322bfd32036fea7f005e0c8edee2041f1826257f22cd2544f5091a07fc4a08e37f34fc334123d513010cd0f9347c0b0811200a6a32432124a7d91c267ff16de7e9ce07fd2f0f184016c65f075223502583f339ed0831dc1908e6f7c97f38f5157f69251b23f03638d9e1f20114ce140bf000291cb02f1b1921e0d731fdc4a8cde510c000f3cf4c193754bce8c9010266d6dbee1962de1b1800020814fdc3252a30ccf837ddcac641d1fde343d75713fce327f4100d2fea240d0a52dd23f034f619d5e9db02e9e61a51c129ec4d4d01e2d6d0f3fff91fffdf07fbf918fe3428c909241737cc0b2524ffc72b327f095519fa00061b07e0d2e90da213ebbe1ff920f938f6f6f625e272013cd997d8e9df2cf511257f1d8e2b4913e22730d1e009ec4b5626100319d540f404dc111b492df5e50d166a393a15bd02ec0f0b6dfb5016e3f101ec150a1d451db67fcd12080cf180e507cf183dce09efe8faea7fd6f00a7f590c3102ffee5f14062b110c3209ec0ee0dcda27f203f09e003905215e2bb326c90a1a090c10f7e1e2d236e3ebedeb14230b14ad1b12ebeee205d7f8c9ecdadff933eff44319b8152d4bd2e0d8a31029e1abf6020134e9c9ea1333e7092c1bc929ef39f41849119910e80bf6f0d215d70e16e710e0fe36022808e50f14050fee101abef6f7f7e4e0d005cce0d4f411ece4ecf6decdc2fed7e5c7efc0d5e4ddc0c3e2f3d2edf6c414e7f5d6e0f9e1e7ead401cdf5dcf308c8d7f2f3e9f1edf0d6e9caddedd9e5e9caebd4cbefe4d5ecde03e903c0d3c5fef9fcc9d5fdf7e702c8e1fdcee8e6d7d1dbe5e4d0d3feeee3b6d8e20cdef5ecd4fee9ded6d9f9fbd5c1faece0e3d2bbe5f1edfcdfdcd4f4f0e303e604fade00f7f9ffdc03fcdae902dafaf0f7eee5e0e200eb1bf4050cfceef2e0fbe3eeefe8e8f2f9fcfdfa0cfcfdd9eae3e907d202eef1e4e1f3ffeaf7efd70dfbfdd5deda0bfe07ecd1ec0de5f508e402bde7f0d6e1ed01e8f6ffecf3da0201e4eee7f512f5fff6f0fce8f60de8e8e4eaf103ebe4f70714fbf3ff15f801f40102fe0a0f0bfe0a0c05190a08140e0efd0d0710fff5ef0c07f926140025f914f7c8f40429f6e4f1fd040f1801011802f809d914041014020a1cfc0100e2fc0d04fce7f7f10806050ffb0cfc1f00ff140e0b15fb020e030316ef160bffb7052c07fc150bf622f10315fe0af5f4f00efdfd09f508ebf9fdd8daf2e8eed1f4f9f4d9f2fbcfdfccf8dec6d0eadcd0d4f4d1e7d5efd5edf6d6f9f2e7cff3e5e3e7d5ee01e7f1cefa07dcecdef6d0fceaffeafbb9f8e3dad4ffccead7d5f5f7e300cff0f107dedfceede7f4e4d902f8e4fee3cef1c301cad1d9e1c8f7d6e6f6f4d9d9c5e102effaeddfffebede0ecf2f5f2e4ebebe9e4eccde9121bf3f2f10bea06f505e4e807fd05f7fb0e11f0f1110df705ee0efd04f8eff6eee80818ef0407f915ffe5e7f217e9f8e2e804f80beaef01f3e00ff0f00806e511f61cf500e6e2fc0a0af3010de704e0050aee0efbe6ebebf5140813fa010ceaf9fa000bf4e0f802151105fafff0ffeff901f7feeef3f6fdf6e2ffecf8f5fdea1c08f61509250e080310f40b271001fe151126041f21121d25301c07140d072900fe0c2420ff0a0c2213f7160a0e17f80f0f140328f60608150827070e1e100121100d1317f8160413060ff8220d16070e0513120afb15020f201e27111f1e22fe11020f0e0000131514110129fd1113051802141c0e0005230814100511290dfd0705f301fdf9fffff302f6ffeff9fdeb0000eceafd04e3f8ddf9fc02faf7e600fbfe02f4f9fdfef601fbeef8f9f5f5ebf7f3fefbfbfefbf2f304fc02fc00f9f9f706e3f1ffecf408faf5f5e8fc02fafafddb07fbfb03fae602f502feeefbf3f7fbf900f4f8f1ff0907fcf6eef5fdf0faff02e2f1eefaf8e20dfef1fee7f3f200220be9fe3b02e4e2e5e1eb3df50818da321fefff0e2001120725ddddebd8f3fae40c35f8e532d93decddf0c919effdd2f00a04440ae8ff06e60dbd1707fa0f0b0e14cd06edc81c02f4c001ecd9ffe709f9de01f3ef16f1cf1e05ffe106fae0dd16e114f1e1cd0b1319030a01eb17fefa39e9cdf7d8290611f60dca1ca4cebcf91804f60b23e9fbf5f508bff5ecf1f5ec1216ec011f28f804e70a0b3bf3f0f0fde8121afccbebdcfb25fafa0ff3f2ed0d04fef10804ecf3f2de10f0fd102901071301f7e7e8dd3927f3f1f802ed1fc4e0ed09280efa03e9f60df813f2f91604dc13012cebf6e214f610130f29de05ff01e91427e514de0de9161fdef5f414d92524281ffa0edd14d1f313ceff0eeb99bd080dc9fc1605a2ec9c04ee12fb10aeed02eafdd5ecdefbcc3605eaeaec221bc5aa07ccf2b68522a8e2171dc8272a05010c041cf3ebba071ce0f5200be630e002edea01dcc0e5d04f5a05331bed1203effbfe05cbd2e7fb03072f15eed3e802fdb92cd6de0ba8f7f4c8f4f9ce0806f119c3f7bbc81326f3b931fd277f13f63a3b6fec0700f6033d222c12e6d3f1a30bffe3154856017fec7fddc0c1ee65e00cdbe829447f4df0da0fdd1bc5420ee03131e5ce0a2523f22121e9e8ddf5ec0cde37261221e3b5f121cb420913dd2b14d90b4bd11e2cb8a5f4fb30e52b12173a1b107f0940e1e11401f7fbfaf776c1e5f4fcda0b00fecf170a07f20f2ed6ffee040ce1dc1112c2b401db21d4f3edf912f0000cf5d7eb0c0b06e6e90cf80fe10c1a091be20bf9ee190b0b18c90df8d8c213e8efd200f91c0704ec010507ec0be32007f407df110d010f0bf9f1cf21e4d4f711c90ce1071716eae6dcfa08f521f3f906edf3071702fff30c0e0215dd06fd12f3ed130e64032afd23df1e23dc31fb4746ae070f310fd7cef606ee162f1a514f1c7fd6f2bff20d5ece27485a05ed29472a14e516d20c3523293c1c56c91fc67faff91629a5610f4e1005fb3e367ff616fce91b0e7f0c230002e0ecf126ec181818927fcb511b4e02dec4f2c93416fd03f8170127552b60e53f221953cb7c005708f701f402eb13fb0e421e2424edfa0ac814f107ffbf1c2c121c0f09fb09f6100ce265ee2c0628eb2cbdda06ace2f1f2f217241c1b33e7ed3b25efef60ea3de81912d4be3bc3e601fa32dc00f2d5e7101e3e0af00c1b38fb00ed3cd42007d705e636c8fab309e308fa22e90302051700000711f31aa90218091c1cfd3401ecdbfeec03315c090cdd14e7ea03fdf1cfee42daee1bfb06fdf4f90405fa061507230b29d3e4d5f3d243f70f634317d7100e1420efffe5f4f910ee4afd33d904f45af9f6f8feec461bc70decf346125e01fdf6f21bef2d072610f6f600fd07f6100c04d158faea070ff8b7f602f61c23e30a00cd090429e702f334271403e508ee1d0ce8020b07f92b0ebe1d216415243ffafaf201b81def2b7ff972f7c6c7f1bd63f7275dd33841633822ad0cdcc6efaa01ea211e49094f1f097fd31bff6be3311f11f9c3d44314c3ccda53a3f7044bff1ef75b47fcf59ef21aaa0544e4ae11db0dfc0c21043ce88df6130db6e40aaa29faf620be452bc10f14001326e97f09121818e11ee14fc97fe21c3805230825f27f1ef5d3c2cbc6257f10450b30fd148c581a027ff37f317e072cd51812eb1a8b2d993b587f4e7f9f1c7f0636cf7ff22311f0ffed94650ccef70e2280fc1a041faf0b7e3ddb05d12720c5ee5a00c640ca2d1a14e3085801bb05d641b812e59b7ff8005ca71342cd6dfd3e5443f47f9ce30800ebfbdfe20bf4f1edf5ced804cbf6f7c90105d1e9ff08ddebdb0bd4ffe8d8f2e6ddf3150307f8d100ca07e2d105e0ecc3eaf9f4f6f1cf05e8efffd0ebeff6e9fff8feca04e1f2cdd0f9f0ebe7d7ecf3fd01c2e8e0e3f6f3bd0cfa03ddfcedc9d7fddbe9d6edf5f3e9f3d70107e7f6dcf4f7e2e8e1e2f4ece5f9f0dff7e3a5f6),
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
    .actor_error_o(error_actor_project3)
  );
  logic error_actor_decoder2_fuse;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(65536'h00fe01020808fffafafafef6fcfffa05fafd140d0dfdfd0006fdfc00fcf6fa00f105010103f8fc01fefe00fe02f8e806f905fe13fafd0013f201f901fcf9f400f8fdfc06ebfbfcf7f9fdf6f107fe06fdfbf0e8f7f406ff07f7f5fbfdfefa01fd10fdfd00fd02fbfbfd15fffdf7f8fafc02fef2f6fff6fbeff604fef402f8f1fdfb26fdf3e5f4fce6ee2218e504ed02e9f6ef0b310b03cbf304efebea1bf2062c07fffdfffcfff00c00ecfaf924ce161d040cfb151b0308e14600fb18d50bf323ede5f6fe02179aebd5fcc60f0c032cf2341118d403f8fbd1ecc5be00c9f0e512ed0ee211f8fcce07990bb4e28005f60602fc0bfd0bf80d36f8eaead5cfe3e50ff90c0308f1f1fbf3f30503eef4f90af10c03f7290009fbfcfbf7e6fdf6fcfffced090200fbfefffefdfbf70215fcf20ffb05f7000bf902ef0af8f1fcf60de5ecfefffeff001000f8020101040e00f901f701fcfd0100fe05fffd0202fe0113010efdff12000201050603060809fffefcfc04fd04020b03fc050105fbfbff0207e5e0001c320d2b0631d2e3df041be1360bf414d2ea07213e221e3af4f015f2caff0d1a031aeb14f1f10bfadef5d5c7e20ff202d702e1ff1bc6f8f31317183a220407090ce2d110f201051dedd6fd13f2f9faf5f406ff02d5fa060c05efece402f205fdee010909f404221ff32a0207fc0107f0d5f9fce9f1f200fe1407dbfcf90d0bfe00f40900040904fc011101fff50501011303f8ff0c09fe0af60a01050109fe0002fb0bf50a0bfffc02060c0e0e0e010f07070600f51a0404010206070702fefcf80c01eafeef01e90bff020f04040c01f80902fc01f3f9fcffeb02ed04f70306f60002d815f5faded6e509fefe10030a0dfe090a0d0bfcf701fdfaf70001fb05060c0713f90df4fbf708f3ea0afaf602f2d3faf2010507fdda08f9f9f6fd03e80314f505fcf701f0fff4eafee5f61d05e2effd0631ff05ebf9f5fbfe0cfa04fd00e9f1ef08e1f9e3f0e503f405f9f8fb0cef00fdf20801f8fbf6f4fcf0da04f4fff5fbf5f0f3f3eadde7dcf804ef02f8f001f6fff6f4fdf505ea0605fa0af702fbff03fffb01080808ff0501fcfc04fcf30500fdfffd0000fdf80100fefef80300fbf8fefc00fb0103f702fdf4fc000300f70200fdfffb03fe01f60200fffc0002f9effef7f7ff01f5f9fe03fc00fcfcf6fdf500f6fffe0300faf602fbf9ff0400fb02fefdfb0800ff0103fcf5fc01f7fd01fb00fbf10007f2faf2f3fdfc01fcef0708fffd06fa0af70506fbffffe7010ff204e907f10509f40bf6f904fcf50e03fc05ecfb0bfbf60e0407080c11051b01070900fcfdfbef01f8fe0716fbf9fdfc000101eee8010300f2fe0eff0a05fee8fbfffffcf9eb0501fefdf5ffef01fa06fb00fb01fef8e606f204fbfe0afc0402fffa060bfcff08ed04efdafffefc03f5f601e2f7f9f2f60fead8eb11ea0f1dff08e5e9f30ff40e0219f802fa19e70d00fde70c13ecff1518fce3ecf3f00af711ea0106021006dcdcfdec040dfd02fb01d921fbf7fd01ffdb0906ca03f2ddfb07e600ff1304fd0a04130025f928040222ffff06faf816f318f7c5f604f7fef7ef02f6edea070ff20afc0aeef5fb25fbe80ee8e8fff5ee14f703fcf40d09f7f5fce410d7f5f5f904f01100edf60413f5fb1bfcf623fb00d7eaf6f50cfae404fd0bf3faff0e14ff0217e3fdf61500f6fe010011eb0b0403f606fdfdfdfd020c0800f8e802e3f8efdcfbe80af0030e03edf4f8ffd8f9fa05efedf902fd05ebfcf10200fd010a00f5fbf7f6fd0701f0f105fc03ff080014feecfd0f0df9050afef8ee0f06081107fb08f30d0deeeee1f70107000cfafdfbf30703f0f5faf2010204eff2fefd1ae7010403150a0cff03020301fcf601011100060001fe0afa0608fff808ed01faf9010203f8f6f00701ff03010401fe0a02ec1901110c04fcfd02f9fbfc040506fdf7070801fb01fefffcff9d06c3d51406d0f8ebfef1fb06140910e0faf501080b010f0ef31716c81bfa10f91d0808ecd4e2ebebf9dd02e607020e00dd0c0505f703f5fa0c121a0c0d090714f0c7fcf4aafee70be5fef90c11f3ffeb18f205f1f1fce4fa08040207d20611db070204f8ee0af5f5e9fa0fffef00f2dc0700f0f8fd0500f3e4e70303ef09f901fbf5f9ec05e9f1000a0c020703d8f0e1e20cd3fc090409fc0804f1fbfbfc01fef614fd090df6ddfaf3ec0d06f0050ff5f4fc06f5f7f3fafef4fe1400fbf2f7000ae0f1efee01d90ce4030808190b01dafe09feebf2f9ec01f1d5f9fc0403f5fdfffbecece4fbf2f1e5ff01fef1fff1fdfffd0424f9fce8f5edecf108f6db13f8fbead8fcb417163de6f23ded0e2af4e04cef1ef8e4d8fa1aeaf11bdffade1bf6121bfaccf7fd5c3efd0eec9f1c0a2b06261a030bd41327e3180c0e0df213fd02d2c8f3231a0306ef0606a3eaeae0f23304e407eb372addf8f519f0fdf90709df0503f5e00af818e80bd4fdfd170cd2fdfeebe4c20412e61304fe0de37b28fcbbadcaabf8b0e37f11cab31fc4b70dd9b52fb4dcdfffe6d4d5929e04131900f804f09c1927e277f6bbc012b2d7ddc3ea4ded1bf21c2f0ef9d8f9801816e2f3f90ee952fbebd9f303a90dfdebececc6b2ecf5ff050df7edf6fa0e271bfb0405f52809f502f1f9d7f301f4aeed0e1f03e5e1fae5d2e013de08eafe570addfe03fa00e7e806fefa0c0606ddf90af1060ed309f902f2f4ec03e9fbfafe050aec1ef302fa0b06fe0305070b02170210f9e2f4e81604fbec0cfc05f8ea0aebeefeeffd00fee8fbf7f700eb07ebfb0d0d0a1bf5f1ff0c04e4fb07e900ecedff01cafdf8f606f9ebe7e2fbebe0f31202f4f0f803fa0206fd0b00f7ebf0e40d0c1613f4010e12f9faefe9fdfc0d0100f304f101fcf203f6ecf9fa06010d06f4f414080aff060af70ffa0c19fe04071f0cdcd806f000000d0604def40c13ea02070000fffc09fafa0cdb00fe1ed6320614f4ddfacde7fefa01fbe5f328080a0911f620fe011afa0710381dfe162a2411fed3e90adfe5fdf60000ebff45d91bead4f8faf0fffd0b010a08010206040a0bff01060608ff04030c0e0ffc0501f60400f2f8fbfbff0f0206fbfeeafaf3e402edfa02eefc03f4dd0116ee00f7fe07fb04f9fffffe0207d713f8f10000f2f7fe0e08f9f9f9f6f5fffe06f900020305fc01fb00ff07f7fb03fdfd0e0402fb02fbfbfaf802f9fd00fbf7f4edf907fb05e5e1f6f1e8010f16f90ffa191f0b180a2607f2091b0900350f57180f151004fc070ae5f3092b021809f9cff0f71b060610ed1121f4f91f0ef60009df0a21e923120afe150e150bf3d42204ef020bf1fe05e814f3f7eb0a0c150306f31611050ff706fae3fe15fb0d0e2216201621fe0df90bf9f509effc0206fffdfd10f0f103eb1209123af1ebe8211a04033261290afa05e5fcf1ea311d04ccfaf800e40f2efefe06001c0903f7190e2413e6ecfa0e20441814e3ff051101f4f95c04f227e710ef06f7f8f0f307f79ae2bef8b807cc052e023924fff1f909f8c2caeac5fae7f2e110f1f9030af8fba9f4cb1bddd6df22fbe908061707020c0e3507f1f3e4fbd5d216e719fb0be9e01cff07fff4f4f9fb00e0f5061230071201f6f7fcebeaf70bf9d80418f1f6f00a04fe03ebedcb13fdeb31110af3ee11d3f7dd0efecd010b11e1dcfff9f6f41a1bee1513fa0c14e7ffdefffb1c0709f8fdfdf014020b03db00d7ffdf01f9f303fefeef0a0ee9c8e7efff0e11f90b0b020a090f0cdd081af212130afa0efc05e4f607f9f9fdfb05fcfb03f8fffef005120c05fcf5ffe9f7fbfdfefaff0203fef7fffd0405f7fbfd0401f70c01fded0305f8fee80200fe0300fbedf4fcf9fcfdfdfcf9fafe0006fffa000201fb00fefcfcfdfef700f8fefcfdf7f801ee00fdfc00fffefd0009fefdfa00fd0004ff02fc00f8f5f4fbff03fffffdfafb12f7ff03f007f101f607121cfeff0cf3ff16edf714fbfff7f803fe10f6f905fcfbf22201fcf90207fd020904fc0aeff0fb0f030b020a0007fefe0c040af40408faffff05fdfbe7f1e3fff7fefbfe01fefffdfef40204fbfcf7fc06fdf1f1e8f4e2fefbe4feffe9fbf71700ecfafafa0202ff03fc02f50306f9fcf8fcfefffafe2918fd297f7f21f67f07be80713fd428fe80628080eb8055f4262ca67ff68565e6fe80ed6d1639db4719f7efca396480802ffd2a2b3dfc7f97000248ac28557810f9fcef92ab13db3104dfdaf9f7b6068096ed0fb112e702380ef608d334e8f8e5f7013bff0300e2defd20e71bd9db04d2f6e3d5f9bbc6dbd7f5f3362e140be5f417020703f60b09100e0aef16f0fafd0ef80011f6010b0d0c0604fe1016f8f7080c0ef507100a000205070009fd0cfe0815080efffefb0a05fb01110a23fe12ff0105faff0e08f31800fb0d12fdfbfafb0c0be809f00208f8feeffe0513fdff22fd0403000009fafaf6050a0007fd03fc00070a020d22030cfff4f909fb1103090401fffdfcfbfcfe010304ffff02ff000201040000fdf9fdfffe02fefbff03fb020301ff02fc020302030503020004fc0afefe0203fefe00ff0203feffff0100000001ff0dfdf908ff02f80900fa0301fcf8faf902ff00f8fb03000300050000fffe04fd0001000200ff0501f7fffc01fffdfb00fefbfa070201f6000800fc0905fafded09130814f302f0ffff02ebfcd2fdf0d204ff0f031cefe4faf2f3cdf126f6fff706fdfe03f9c6a6e302f517020106f3ec05fe0be9fdc33311f6e8fffdeaf9f5efe402e0e905ff06f10134f2fd06f4d002fcfafee7db01fef1d6ef1427fbf50cf500f107000305fa0c17fce90100f807fefc0e12efe30cec02aab10a0c06f8e61a00f8110c00f2f6170eee0efce632f8f2ff040809f10cfaf9f608db03ed0bfc1b0005fce3fee2cedcfe06ef030c0bfff0fcfb1ff802fc0611f0010ef4030704f50020030a03fdf2f9fbf20af6f30104f70c030707fb030610f519f527fff80a01010607fc13f50afaedfc06f90003fa00e3f5f4d905100d00cfe1e52bd11f8009ee297f4a8794055ca2e61001a111c832f17f23e7344e8e357f35bf57cbb0ef58ac42f49717d9c8d7bc9bc6580aefdac90d2a0be006808347805618fc04eb01aab4ae29ba0ca3128702c0bcf2a6f7f0daf901b542dea7fdc8e2e002870ff6fffdf202b880299a83c6bd1218f904c8ae18e0a29eb30c80fdcd0804f3faf5fcf707f505040cf9f8f7fc01fb0302fbf9fbf1fefb02f40705fcfc00fcf6f908f500060106f0f8f6fcf5fafff503f9f6f4fcf8f9ff17f802fb02fe0003fffe01fb0205f3eff301fef6f5f301fafdfef800f5fcfefdf7effafbffebf4eef7ebfefcebfafdf6f601fdfaeef3fffefe04fdfd03fff9fcf7fcfbf3f6f9f7f1f50e0cfbfa0104f6faeef002eeea0101f1f4ea0efbee10eceef9fffefaf2ecfd05fc11ebfa00ed0308fcecf2e8fbddec0def08eadafeff00030dfddff7e8e3f0fbf605fd05e00aeb041404f103f5fbdfffe9e3f4fef40500efeff1e207eae1f2efebf9fdf1fa03ffe1e7fadcf1d7dafc05f0fef8ea00eaf4eafafde9fbf8fbf2fcefdbfbf021060a0b0dfef9ef0c10ef07f9ec0fedeaf50408020712f5fcf9fdf5f2f9f0fd0f0905ebeecfd2e9ec140be9f5f8faedf2f0030fef01ed1106fd0119f3f905fbecf71bdef2fc07d8fe0418f6feeed6dff1f70503e0f90dfd0dea040342fdfa1cfb020007f901ff170600fcf3f508f6fb04f9f913c50517ef05b9bbf2f1e50f17c535fe80802bbba380f3338080ef8105c3e58080bbf180db9580c1f2851a800aa2809a43f6c80721e227b8f880cc80642880edaf0ce70e1080c78080f9f8e7001c3211dd7ffedcc20ffdb8f6d1dfe2e4bafff901fe04cdf7061b000370f9ef13f9fae4efe227c7fce2cddf1bfae70333fbe3c5f991ecd8f8f215a9d60304fef2fbfde1ff09f3f9010801fdf9f6fa17fcf708eb05faeb0ff002f6fd040fe6f70000fff4eafef8f9f6f80406fe04110703f918f9fcf5fcfa09f505031ffefdfbfb000107fecdffee03d101120511fffd00fc06fb15f6ff0afc0805faf609fcf9eefe02f0f7fe0dea04f7fffffe11ff0500fef80303f8f8ff0002e6e2fd7f2ef5e6bcf2e2d0e4047f0cdfc20b1dbadc22143cc9bff822ede511f1dc031917f12b0aedca1314055ee706fa0601f5c53df022107ff50a60090cd1d9cae6f100fefe04083bebef36fffaf1ea05b7d8dae1efeceecefa030df5f7ffe31918070c09fc2cfff9f3faece8f0f5f2e503f51b05c1e301e1f6e3f5ea01f3d30f0a131233fef4f90707e70cd1121a1ffe06f5ed0ad80d16f6c8f9f0f3f3161cebf7e400fa05fbfdfde52200e6faf1f3ec21f3ee09082801fdf914f7f3e133ecfdf228efd2f5092ef8deb9bdfdfc2cd801570b161605c3f7eff3e6dfd9f3fabf08d405fbf5f42bf8f4c7f3eb0ddde9f622f1d90fd2fff20b00174bffe7f4a8fb99c9fff807fcffdf00f1f8f3f40009f1fe00eff4fef10c06fbf0f2fffaf40a02f8ff08fbf601fae71305fc0b08f20006f919fafd01030b070c01fa0000e9040206f4fa04f6fd04ffe7f5efe800f903f3fc12ff10fd02e800ff01ebf6f3eaffe8f30001e1fafeedfc02edf2f0f7eec9fffe04f7fd01fa09f8f80103fbf9fbe6e6eff301190e09df13f701f4f5e10cf506f008de1a0ff204f80fedede813e8081af90dfb000e0b0705e8e2fbe50bdbdcfa1f0c2200fdef070410f207fdfec205eaf2e400fdf9f00400f4d3f3cefdc20e06f938092b34f6d60706f5f8ef02d2ffbc05e8f9e903f8dcf9fdc6d6dbf8b0ddab08fafaf6f904efff03022bffeef6b4d7fbd017faed0501fbfafb05f2fd0200f60bfdf9f80a02f710fc08fa08f80004f7fc01f902f8000005f3fff7f1f907faf1fef5f201f20205eff7fbf5f1fdf4fc11ecfc00fa00ff050ffafd0305fe00f2f9fff90602feff07fc00fffc05ff0101fcfdeef8f703fd05fc000601040300fef7f2fc01f700000302f503fb0207fb010503fdf4130b05060617f015e3072021f5081df901410d161afe08031ae9f305d3f51dfcf3ef1df907fa070702132817e500db1608d5032028fdfa141afafe1515e6f7fcf901fafdd5e81aea060101d11700c1f9e3e2de12e20c0300fcff020517f033f725ecfa07fd00070cfd2aea1b00d6fd00e608edeffcdac3cbde0104edfcf0e0f58080477f80387f80e67f808080802b80808e807f808180b2d418807f80809d80804e8007808080e380807f7fdf22801f8080807f70800280cdf2296180dd8080efefe71d2131660e7fef7fbc66f0eaa5d8f54508d428d63afd0c6ee3548c443b67120c2106f34a7b6f5f1b7f69a0074f9208dd51d8e6becf12f97fe959261d270c07fc0a0807f1f1eefdff00060706f9f2060ef00801f5ed06f6fb03ecf0fd0afce902fefaf4f912020ffb00f608fdf2f202fff8fcf300060e01fff208ec05fcfdfe0100f5130df4f7040de71400f604f6f0def5f1f9fd06f7f406ff11fe0ffe16fe001ef902fe150d04fe0f06f5fbf0fd01e8f801fef6f8e90814f101f7f0feec9ffead80e3d71ed4223a46c7144fb32e7fdbea7f164be6f9dee419a7373ea2d3e047f2b4d0cbd9bfb75afccfd280ff49e53511e8fc09beb8eb34de52f8fa04fd160b03ec0ae4630b0dd91af1038023db096b10ff23f9fc49fce9f4cf02be0a800f0ef1060308c2f02201d8ebd10e451ff52fd4061ae2c535e5dd64c93e6bed00f6ff06fd00f402f407fe09f60406f5fe07f7fd04fa02f201fa0002fdfa030100ff0c02f9fdfffb0c01010d050e030200f60104070102f9f401100406fdfafcfcffff02f90bf9f7000100f903000b03f9fafafefe0700fb07fdff00fd08fef9fffffcfbfd0201f9fe0801fc01f7fefb0805f8fdfffafd00fb04050906fbfdfa24070c02d1f6ddcddd0f12fae2fb08e5dd0df50a16f0cbcd10f0e7f608e3fe301ee60ffbe7fbf2fc1d18041116011ee2ef180f1d0f0a08e9fff7fbeff7e9ed0efee2f80c0013dfd7060504fc1bfb00f40006f0eceff5fd0df6f00bf905001a0c1dfefd1ff1fc09110ceb090d0811f7e809fff3fafb05fd130bf412e41cf0e71003ee0212ebfa05e30710010cf20204f7f811f51e01fbe9fff6ffd4ecf6f30114fa17f80cf30901000211f7ea0afef326fb04e7ef0efa01f81a05ebf9ec07dbde01fc0101ff07e4110dfd00050501d7fbf101fd1801fafdf11311f905f213e806cdff07f602f908ed07dffe0002f102ff0ffd02fc05fc01ff17fdfc11fb31360eff1afd08edf804dbf203ebe405e9fbffeef20f00fae3e2f1e5f7e6e9f1f8f50809f907fdf9e5fd2af704fae4ecf7f705ed01f827f3f2f9082ef7d713c7e8f20ef1f7f8fd053af00204000200fffc07f204091beff5f3fff001f6db00f419f002ff05f507f5fbd6fbede8de01f4fdf20b08fe0bf905fe16f50af7010bfb09dffcf6e80a00f0ebfff805fceffbefff00010411f7111cf80507f0f8edf7eb01f6f0f4f3fefefaf9f6e700f102f4f1f6d60503e8f908feecffebeb02fdff0ef4faebfd01fb040a06fbff0900fef80500ed03f3fcf7fcf6080100f8f0fb01f8f8f4f60404f907fff8fcfefc0eef09f4e5fbfd01f1fae504fbf2f8f6fafd0bf60afafafcf1fbf9e001fff2eefefffdfef8f4fcf5fbf6fbe9f1f9f1f200fd0405f502e6f7feeff8fef9fafdf3f0f9e4f50005f8ed0800db05fafbff010313f8faf3f9fc0502060402020405fefffa0ad105e9f90407090c010000f8e60ce3fffde9fe1600f8fbe405fe03d7fa07f0e1f4020704f9fd05f803ffedfb0b08d9fae30f0cfd10bff9f126d908f90ff61417021b04fefd0621ee18f3110822000709f6fe08f100cbfb000bc603d809010e03f0f7ccfa01001123ecfd031cf201dbe51ee61401fd0c0d00c4fd0610f203f3ddeffbc7f8f7d8f010e5030a070dfdf20412f3f8f7eafcf6f6f8fe0ee3f112f6f8dbccf706ef01eed0fbeaefdee50ae41ad91609f59c3af09d7f2ffcc0ffd1eeb230d4803ce280178080e8800bae2b1ab953c780f62141db08211ef37fc5128085f2217fad8024f8eea314f82d49fdb023ab0b3a7ff0ddeee4d0a11fb102fdedece70a383bf6fee4980b01e920baeee61301f1f6fb1d1bebe3f205ef09f9fef70adc42fcc91405ecf80bd72ce0c7fdf4cefcaabc19fef402fe08fdff0006fef9fc0b0efe01030804060ff9020a030000fc000303fefff5fefc08fff8fbf5f608f8f701fd060701080c07070000f400fefc04ff000dfffdfffffb0207f8ee01fd0a100103fa1206fcf500ff010bfb08f9ff0d031c051b00fb01fefc0308fd1800100204fcf9fe00f1f600fefefa010705f801f4e2fe02fd02fe01fff6fa00f803fa00fffbfdfbfe04fefdfff303fdfa05f603fbfbfcfff701fefffdf3fc02fefcfcfefc020507060906050400fb0002fefafafa040afffffe01fb0900faf601fd0100010dfe0c0801f703fc00fdf9fd0000fd08fc0305010009fe01fc070205fb04f802fefb010001ffffff0208fefb05f1fdf2e5000afbf603f9ea070a00eef9fcf2fbe5fbf8f1f1f10705faf7f213fc05f9fcfafef805f5fdf9f6f120dff6f4e1eff80106eddbdafadeff00fb0d05f2feece6f7fdfb01fc02ff0f02f701fff9fd0efef6fdfcf501fbf6020011fcfdf8030d020af91bfdfb0bfa020afcfb09fa06f5eafd05f8fef2f1fcf1effff608f8fe0111fd00f1110bf7e0090a0bfad9eee8ed0008fffbfb0827e21713f505f0d6f9de0e09bb0e04e908ecf3fb0fdb0605e00af7ef22160c09f70be3f1d314f5dce312ffdcbe1001fb0cf303e614f504da04d802e7fff10c251108fef5fc191acf05e2f9f010e206fb0005f0e8ddc8d2bcb0c6f3030cfaf00af00609f4ff2cf8e224da121828020307f6f601fefbf7fefffa0303fdf501fdecfe07f9edf3f1eef9000c0703fbeff4fffdf212eb0306faf7f805fe16fa09fa10f0f30003e1f2030605f513fb00fcfdfaf80419c30cf800da0ef1fef3030a05130801f8fbfa09f2ddfce3f7fbfdef05f5f300fbe7eccfffcceabffafcfe01faf9010502f51bfff7eafbdcf8f7fcf8c2fe4580dfe39b8041473980f737ac80293c060eb48080f3e080299880f77ff0a8ea019ba9cc0c4e7f327ff550000499ef81452e6c0f0c14fa2eaf80828980f3e0ec05ac54fde16ef83c804101d7f3ba8ba9068009ed2e33ca0707073c14f451eeeb0bedf3fa010a99eb56e9d3eb1b10f4f0ccf0bbb0d1c1f61fbcff49ffc7f602000304020907010103fcfd09fd00fefc06fdf9fffe040704fefaeffdfafa01f70000ff03faf601fb02f7fe01fffbfdfb04f6fff7fe05eafff70308fdfa0200fe0002fbf507f5ff02f4f607ffff0102f6fbf8fafeff02fcfdfbff060109fc0a00ff01ff01f5ff020fff0103fcfffbfd01fcfb00f8fdfbf20000fd01ebeafbef00fa02080208fdfe00fae40508000e00df21fed9feff0d0605030af8f502e7f80301000cff1007f506e5e3ecf7f4eff20305fd010e0115f5fdfa060bfd02f2ffff0002f0f308f5fffdfef90203f6fdfdf3fb06f205fc0dfcfdff010cf4fcfdf6fffa0afffcff00fe0f020afbf3f903edfcfbfcfef3f3ebf10506f6fafb04fbf6e908d0d40dfa00e9f00df4e6ebffd9e110f40806030aea00f4c801c7f3fcccf5f80ffceaef01ff0afd09fe0e0ec506010ae4f7ecfa01cf0bfaf9f40ad1d1ce0c0afe03f408000136fbf4f9e500ebf903ed070cfcf2f8f1f8f6f3faebf4e904fcfb03db0302f9d6e2f7e6d7d8f3090b01f9e9d101f5e0defe01df0ad505f700fefc0000040300010101fe010103ff00000204fd010100ff05ff0100ffffff03fefcff0201ff010003feffffff0501fd000001fe01fc0002f80100ff030000ffff00ff01fb0103fdff00fffe0500fd01fcfbfdfefd000004fffe020003ff04fd06000103ff01ff03ff03ff05fff7fefcfe01fcfe01fdfffbf90200fcfefdf7fcf1fb0104fb09f60304fbfbfb040701fd09f8fa08f5f8040201fef7fff30204f3f20a01010c0102f7f4fcf7f1f7f3e50503f6f903fafcff01f0fdebfdfefffeeefdff00fd04020008000202faf201f100f5f1fd0bf7fffef50901fb01f9f6f7fde80100f5fdfffdf9fc09fde9fef3ff0609fd0404fff902f4ff01f30903fdfefc01eefbfeff0700fefdf814f4ed080703f1fb00ef03ff00f7f8f9ff09f3fbf8fdfefafafdfa04fcfa02fdfc07fb1cfaeff704faf207fa0108f8fd160c07fdfbf7fafbfefcf6200bf90dfc03f71501fc01f0eff209ef040204070c06fe091b08fb1afefd12fa0205060904080f0bfdff02edfcf9fefff701f4fb010afb0c02f601f2f60331ecec0cf703f5f4f3f3ebfbf701091018150315f72c03c8f0e103fb00fb031006f500f9d80525070315f1dc0b0e08e90cfeff02dbec07f3f70a09edba090303f7fd11ed1d0e010004cc00ccf2f80f072812eb09eeff15c200e1faeb0df4050cee09fb0beefaf9f7d7fb0503fe0503ecfe030c10e70ffbd70aee2022f9),
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
    .actor_error_o(error_actor_decoder2_fuse)
  );
  logic error_actor_project2;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(16384'hf84ef0ff23fc0435ed2901fe03f81b1408f4e811f9fb11fef4f114fcf706061107121227091df5fe1bfef8f013f134f9f1f518f54fedf90c09fc0301e40600fbf7db8021fd0381df80d416e3d9f880b080fa1bf3c5ebf2808080f280f602f78080e480fdc7cff9d68080d00d80ba800a8e06b41e26daa69080f8ebeb80ea920803f209fee90410ed15fefafcf5f915fb0801f2ffef011006f935fa15f0fc011311f607fb04f3ff051414f3080a010b05f7fd0c00f201ebe6131e02fe20f70cf9fffa10e2faff1400180bfcebfaf700fc0ff2e8f9f00b11ebf54b0101effa03f801eb050afd01040a1907eb1327f802fceffdea0e17f5e7f629f7fcfb0afa0cf1dff50d132a11ec81d2204c2de5f3e111ebea51152b3bf0f06380e1a624cf0bddd8f9faa607d6dbed45b904d6e65af52e1d1cf9bda2e12d2bbe08ff1486121406dda146fec613edecf6e7f5f5a104fefaf980eca22ee5010ded7fd1f5fc1a03d57fee2880bd0726e75905fa27e339eefae9fcd8e7f7f71cfb1abe111a00101c06ecea80002d0380d480ba8baf80a48c808087c5fad8ee05808080e780a7e4ee8080df809cb7b6d7cf808093d7808080f980d68004f1ddc4b380f4eba580d7808d00354de61b0f04201ee7f313f21f2a0307c7e4112905fed5ee1f02f102ff09a80b003b223b01f7fc191afae02120280813f0d20b2a0a10250ebcf00ac001ea11f4cb80e5f50b97b980d180a8b1ac80d280c5b8e9030f03808080a380ede7ea8080fe8080c3a8c9e78080c4f480dc801296f9a5fbf1d0b99980e1fdbb800580e6f5a480d7beeb80a49acd80b180a38080809980b4bcec118080809880b50ef78080eb8080809eb7d580808cfc808080f780d880ebe2d2a59180f6e6da8007808e06c580f9000ba9fb80d6dbfffd1280aa80372710af0b0fe1b180fc8002fbf48080ee80b2c4e4dbf0808025ec8080800e8002acfde2d8c7bc8005f9bf803027e0faac4ff922030280a7af3afa2014f11af5fa1edb12f6ddf136ffcfdee3d2258061b67fa8b0c080ff97156e52c07f25fcc40da4b4800a29d8459edf198d1073ecfeb080fe120ca0b281c5b79ea0b980b1809cb3e206dd0e808080ce80d307ea8080dd80ccb4b9e2f980809501808d8003850a9cf6e9d3d3b580eaf2e780e180eaf4f2b70444f5015aaf21111cf333b1149e1e1edfa5fdf4caa5802bb7160ff9df804f80e72d2313eb80d420279be9c0f8cef01c2b7fe0df09802c12bf80000eed0d9680d0d71b8ec880bb8db4ab06808080b092c080f2fd808080a080d6fee98080cc8080d09be6e88080070580a080ef80ff94dbf7d1b4b980f3e6ac80f982d712a880c4bd17cf9b8002d6c4b50580b2809094908002178080809080f7faef8080db80869980cce18080710580d080f38adcd8d8bce6879780bf0de880e7b9cefcfcfdfce411dc89fbdc0308f4eaf9f2e8d915e44219eeef05f110da11030cdcacf9f0eaf1db01e6cffc10ebd224db11160b9addbfec25facffcf10ab71ffa0e03b080fa0e1480e390cdc3b1a48d808080cbc600ce050f808080f880a7f1ea8080e5809db0d7aed5808089eb808080e080cf80f6f9c49b9980e90297800a88c910e500faf4080cf220ecf204eb011aeaf505e4eeebfafafbe722ff1eeff702fbd70902f2f9f4070dfa07f70dfe0aadf7fa01f40ef819ecda221912014ce802f400b480b6040891b480ee8008c8ed808080f6dbb38ff0e920e6808080eb01fe8080d18080a58bcaed808038d38080800880dfb5eec7f4959e80f3fcd5802cfd8016f50334b13e2580c9d1782e366ead2ef9f67fd81c0c18177ac304c6471516fb80a1cd1508f115c9c8fe59d4330f9cebf92efec0932df318804de204022ceb090c6445005dfa076d1afb070015fc0917e810f92778fe03e909f80ce80703fbf388eaf5132e17ebe5f8d2fbef1b2c2a18fdfebf1d080d284c0cccf10ad606f0040ade9ee7e715fde68af1b7f2c6c681df848cb7cbf41a218080a0be80f6faf88080c980c7e395eee680800e05c2e0c509d9f08fe1e1ead9da80b0ebdb80deb7e30aca80c7d801a3c280eacfffee1b80dd80d709cc810c23e0bf80c6800703f580800a808018800cf880804504808080fcd70feefecbd588e880d507d080ec0ff9e8c080ecd8f980c985ef80a8a1a1808080b19ec1bc15e6808080cc80b30e138080de8080b8a1f9cc8080b8ec80808003800580f8cdccb48080fdf788800a8090083700fd2603e80cd1f1e714f5f0fb03d906f6214b0104e8fcdf0802fee911228722effb151803f6d5c20bf0deff22fa0004f03701f5341b1211f101a90aef1c030bde0703f60b44e42cfbf20ff50c00edffe62103f704fdf0e802090212fc06dd180a2f1a2def02e40ed40e0fef42ecfbf401164cfbf4191b160df3c803f8daf6d12928ce0312cf240323e5eaf70c114410090ae5de172311430a07ecfef8ef3afb1d1d18f4f2150d4bc9220719fc02f2fb26d4f004e2ca2e130cf049ec31f80d8a80dbf30381d68dd380c2808080808095a1eea7e20b808080dd80c20af78080ed80a2a688bcca808094eb808080e880dd87e404cb809280ecf7a9800680800720190309fe0f44f01f0cf6f9e904111018f12e200822f0e3f62bfffc16f71ff80cfe272224fded38f0f6050a063d05f3faf9f426e60cf3f3f9fffcd4fcf3070107bc0d0bf6e1bb99ade10820ce8213a5de23efc4f20185e7b7af80fddf0ebd8020a3ab08f2dfd480aa26e3dbfd8010e0f3f1f804d1021780def1e280ee1ce9f7b480fee41eb5b180c4eee1e11180d291eefac880010494e180b6800704088080d68080acd0e0ee809f141680ee80f1fdf8c8e0e5ead4ad80c8f8cf80f60af5),
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
    .actor_error_o(error_actor_project2)
  );
  logic error_actor_final_fuse_standard;
  streaming_channelized_plif_actor #(
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
    .KERNEL_WEIGHTS(46080'h7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f887f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f80808080808080808025077206e65061077f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080808080808080808080803421188080808080807f7f7f7f4c7f7f7f7f0d0f7d8080fb98b0177f617f7f737f7f7f7f808080808080808080808080808080cd80808080808080808080807f7f7f7f7f7f7f7f7fa0803ce4801c4c007080807f80807f8080687f757f7f727f7f7f7f4beb7212e66c68fb6e808080808080808080808080808080808080e780628080fd4bcb7f7f3c7f61247f7f7f7f8080808080808080808080808080808080807f7f7f7f767f58055b0a94d74d41397f7f7f8080808080808080807f7f7f7f387f7f7f7ff780806980c07f757f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f69e6427f0b597f7f7f7f7f7f7f7f7f7f7f7f3f167f7f7f7f7f7f7f7f7f7f7f7f7f1abfadea9388e3e79a7f7f7f7f46557f7f7f808080808080808080fceff9cddbddc399b10f9c95f68180da8080808080808080808080808080808080808080808080808080808080245b51d6402580caca80808080808080808080dfb980bfdd80808080b79780ecc2808d807f7f7f7f7f7f7f7f7f8080808080808080800c7f7f697f7f245b7f1afbff0c9ef0faa3c8068080ed8e8080808080808080e38080b080ba80808a8080808080040202f1e2e4caaaa77f7f7f7f7f7f7f7f7f765bff792e02384cecdec193fbd394d9ae838080808080808080808080808080808080807f12f52fb7a906e09b71021728cdba30b2d2808080808080808080808080808b808085800c92bda7808081808030f7210f10f222d1ea8080808080808080807f7fea7f7fe95013935e0e80670c801cab8080809a808081808080a89fca9fb29eaaa3a8808080808080808080969ba98480a38080808e83988b8089988d8380819980809580808080809d80859a80808da5b9c093b6cb93a7b94c5454605b665e564edfe5e2cfd7c3c3c0ccced2c4ebdcd9fc0205b2baceb0b7c0a29bb3091c201e2a261a2726acadbc9fb8b2a8aaaad6d8ceece7e7f5eae380a0ad8097ab8086a2cde1ddc9e3e6bfd2d3a2bacec1c2cdbfcbbd3b2c3f2d2229311c37f1edf5fa0609020701c2bbc0c4d7cdb0bfc33e2448171b28170413ed090be9f314e1ecf1ccc9d0cdc2b6eecdb9ece3ead6e2e3c8ced0edd8e3d5c5dbc9c3c2d1c7c8e6d7e1efdcf02b365433374c131d3b66736978737a6c7178dcd7efb6ceecb5b9c6a498b1a9aabe949c9f6d7c7f656d764a516524382c141e1d0b0b1394a6aca1a5a1849690ffded3d9dccfd6cddc4f4b5c695c6e767377efdef2d6cecfbfb1c2e4f80acfd8f4cfc1dafff002e6fc0adad9ecd6d6e2d2c8e2b4bbd5cfcfccc8bfb5948c88b2b8a7a5b4a58e8b81ea1e29092a18dff9ebc2c4c7bfbdb7988a8fd6f5e0e3fedfc3d4c7edf2eed5dbdebdbdc2808080808080808080ccd8d5d3d6d6b9bab62d222c402b3a4d4a4f0cfb0a00fdfdf7f6f2e7fbda0b15fceef6d2f0e0ea06f2f810040cbfc1b5c8d4c8afc2b9c1dbcfe1e9e0bebdb3493822514732373e2005fdff160b142c1b211b2c2c091514ebefee10152421262d212821d8d7d1e2ddd8e9ebe7a8afa9ccd5c2b9d0b84c4e5829383b0e1b175349535c435768505f506b6c415f60123532c7c49fbbb49a858080ced6cacaddda92aca40409fa07f3fff3e9f1a6a796cad1bdbdbab6b4dfedacc6db80a6ab808d8088ab85808080fcf0fb0ff60616091635292e2a1c150206150d161e08181cfd05fdf3edf7f2f2f4e8ede51a08121508142311214c3948352136373844a9bda7cfd7c3b8c1b9edebede7d7e3e0dbd73b2935381f364c3e4b06250ff9140ecdeee1364a64192e45f81221808080808080808080808080a480808080801c3a7f4f327f69507f9a8080ab98979d809b80a1fab8c92fb1bb2b8e8091ab80d08c80bc8080af80b725bad337808080808080808080808080808080808080d48dadce81c3bf808d7f7f7f7f5e7f7f607f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7fb2c3e5f1d80601e727b38f80fcf2b301d6cff9b7cd0de9d40ef7102a02517a2c477f2f5f8e80808080a280808016f12f5e2e4f7f617f6c196c75236b573159d899ba1eafe4e1b9b3dcd52ee1ef49f9f73a7d5d7f5d4b7f7f4c5d808080808080808080f0a6bddb9ebcbf80b37f7f7f7f7f7f7f7f7f74143d7ff945652c38808080808080808080808080bcc5d280808029e0e318dacc12b4ecded20fdfbbddd7aee57f6d7f7f5c7a4f3d508080808080808080801eccd004efdbb6a197b280c8ab95c39080b0fab4a0f8c2aef58b9f958080a4a080808080c4de59e4f764c3d2380ed70ae3cdfedebcfaac80fca881f6e7b0289580c59280c7be80e6bd8080c6829ce89bbac080e1be80f8f4c02b9e9023a78f4beeee7dcc9ddde7c00a38e7378080808080808080b1808080808080808080c4c9e0eedf19eef4ffeca5fdf2a0e9e5a3017f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080809b8080808080533f35737556777c7fe51d602a2e7f42337f3d242670636b55415dbc8080cf8099d38eb7ecc1cee8e11cf6e11d0784c5e980a9ec80aa150d0c43443b3d413314cd113c0635120422c09ef0d7b1d1ce83cdcec3fde5d706bdcc03797f7f7f7f7f7f7f7f808080808080808080d1a9d7d19aedea9dfa7f7f7f7f7f7f7f7f7f66153b6d0d28680e2922e83207d20a24d11f80808082a4ab80809725c9f6290efa53110139cc0325b90914d4f910e11afeab15e5b0f98080808080808080803f33343c2c4f2f2e447f7f7f7f7f7f7f7f7fe0a9e2d397ecf7ace5fbf9e9330a1c08161294cd0ee4e651b7f23822f85723216649266e808080808080808080808080808080808080ff5f80808080808080808080808080808080808080808080808080808080808080808080808080808080808080cbfc808080808080808080808080808080808080c78080808080805c4e711d164f0d030b585679273350e6e7038080808080808080807f6f7d4d29445010367f7f7f7f7f7f347f7f7f7f7f4c3a30d8bdad9a217f8080478080807f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f19687f7f7f7f597f7fb1197f808ae98080808080807f7f7f80f47f8080348080788080a18080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7fde337f8080ea8080809480818281818080808080808080808080805c7f7f831a7f80807f80a3f280809c8080808080ef8080808080807f7f7f7f7f7f144d14808080808080808080c5bfcfa7a2b380808080808080808080808080808080808080808080805b80809980808080927f80808c8080808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f808080808080808080808080808080808080808080c88080bc808e597f7f5c7f7f234f5809377f2a2f7f1a0e487f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7d7f372e7f373c7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f527f7f397f7f547f808080808080808080ce8cfcadecc38080aa8080808080808080807f7f7f7f7f7f7f7f7f8080808080809f80809080808480808080808080808080808080807f7f7f7f7f7f7f7a7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f80808080808080808080808099b59c80b685171612040904052d127f7f7f7f7f7f7f7f7f808080808080808080808080808080808081000000fefd00fe00ff010002000101000003fdfcfafcfcfbfcfafb040504050504030504fdfd00ffff00fefffd02ff0201ff01000102fefdfcfefdfbfdfcfa010103ff0101ff0203f8faf7fbfaf9fafcf9fdfefdfefcfefdfcfd00feff0000fefeff01f9f9f9f9fbf9fafafafdfefcff00fdfdfdfdeff1edf2f3f2f3f2f0f8f7f8f8f8f6f6f8f7f5f5f2f2f3f3f3f1f0f9fbfafbfaf7fbf9f9f8f8f7f9f8faf9f9f9030303050103040404fafbf8fafbfafafaf7f9fbfafaf9f9fbfaf9040102040204030301fefffdfdfefefdfcfbfcfcfafafafafdfafaf9f8f8f5f6f7f3f4f6fffdfcfdfdfdfefbfefdfffefefefefdfdfefffdfafffbfcfdfdfcfbfdfcfcfbfcfcfbfcf6faf9f9fafbf6f9f9f9f8f7f9f9f9faf7f8fbf8f8f8faf8f9f8f7030402020204040203fefefdfcfc00fcfdfeff00fe0000ffff010000fefefdfefefcfffc0302040003040003030100000102020001fff9f9fbf8fafaf9faf9fefefefbfcfcfafcfb191a0e0a19070e0cfcf807ecff1102fe02f1c1cec8e0e7dfe0edd80419010b0c0a0c1601f3fbe5070d02fb060114130b19200d11120fccc8c1cbc7c8c1d5cbc7d2ccdeeee9e7e2de0c0506fcfcfafefffcf4f9f8fdf5fcf0f9fadadee90b070809fdf0d6cecfdbd9d7d1dfd7ecfaf3f0f9f7f5f3e9858280808f80808480dfe2e100fdf91c1c0fc5c6cbb9beb3cbc7c683808a80838683878b9da0a6bcb5acc5bab5070f15000509050918808080808080808080d6d1e5c7d7d7c5cacd47393d36363c3b3236e8eeffede5fddee3f0beb9bfb8b9beaf9ca309110519160f0a0d0c100d080e070b080b05818884989a949aa6a4e9f408e1edf9dce3f32c3e3932312efe100e1b141b191818231e18d2b5b8d7bab4ccbfb5cce0edd8e8f5dceaf6f50b0f030c120b030f271b2120261c2a212b362b281f1d26291d19060b0a1d1c1108110ae0dbf0d6d5e0dbe2ee292f3018181423202b0a0d100a1713fbf90aeefa1bebf617e3fa14808080808080808080808080808080808080b3557fdf7f7f8002f5808080808080808080084e363b73549f13c799c2ae80808780808080808080808080808080808080a280808080808080b0808acfa3ce6e634d5567723a0425819b80d0fed480bf9bfef3f244172d432d42808080808080808080f53e66b2e2e78080807f7f7f7f7f7f7f7f7fa4a9afe5dbe714e3277f7f7f7f7f7fb406ef767c7f7f7f7f667f6b8080808080808080808080808080808080807f7f7f7f7f7f697f707f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f576c6b4d66032220808080fb9a80dd80808080a78080868080808080808080808080809990acdba1baede0037f7f7f7f7f7f4a4b20fc3661e5255280e4d57f547962467b3c1f163a12494336704b566e7f617f7f747f7f7f7f8080808080808080800fde1eefe6eebeabc77f61787f64697f7f7fdd7c7fa92e7f8080ca547f7f2a737f85d113917feae17f1efa7f77809e80805280d064807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f80f680a811c5cb7f067f7f7f7f7f7f7f7f7f80808080d580804b807f7f7f257f438080808080808080808080808080808080808080808080808080808080807f7f7fe07b7fa9457fa2c580808080af80808080808080808080802e561a968cb9808080808080808080e480800aefa0a58080b780808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7fc9627e09287f6a7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f80808080808080808080d2988080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7ff1e580ceae80e7cf80808080808080808080808080809880808c80808080808080808080808080bb1a801b52808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7fabb0d8a6acb18080808080809980ab808080090d7f312a7db3d8e184809e94a5aa808080bacf9cb4f0a380808090b9c6818f8c8080808080808091808080808080c78b86c08080807f7f7f7f7f7f7f7f7fcfc0d2aaaac1c794cde8db942021eededeaac680b3c58ac3839abe80808080808080808080808080808080808065617f7f7f795762397f7f7f7f7f7f7f7f7f7f7f7f6e66540204f7aed8ddc2e206bad3d6b780808c808d808080808080a49e82938d80577f7f576c7f0530334b074e2cdc3a02f0367f7f7f7f7f7f657f7f9586b8859fa980808080808080a0c98082a9e7a7f9cdb1c4ae85ad80808095d0808080808080d38080b480808080808080808080808038f24223ea2a6b357f35797f3f6b7fe7346be60c75074462bb0936958dc8ac80bda580ae4f27533d0b652c355f7f7f7f7f7f7f7f7f7f808080808080808080b780cb9e809e8080807f7f7f7f7f7f7f7f7fbedcfbe9074797a8c5597f7f407f7fec2c6adbead5edecdae6e4d8cdcec9d7d1becedbc2c49fd7c1b4a9c6c1a1adc3b3c7d6b8cde0c0c9ceb8c6b4b0bbb9b2c8cbe0beb9c1b3b7bacae2c5bec9b4b8d4b9a0c5b2d09d9789898eedeff3edf5ecebeaf4808080808080808080e9e1ddd9d1d1cfcdd1e6dcead7dbe2d9dcd7060f090b12121611191d11150b0b080e0b1180858c808080808080150f1311071414160f8080988080a68080808096878080808080808080808080808080806c625416101ffd0f20a5a08e808080808080808080808080808080808089808080808080a7bec1808e978080802f394c4b60704f5e75808080808080808080fdf6f4e8ededf0e2e3808080808080808080c7c2c2c4cac2c4bfc1e8ece7e7ebf4f1f7f12321d90f08c4c8a28a8080808080808080808080808080808080800c03130a01090e0912e7e7f2e4e9efe5eef3e7e0eaeaddead9d9e4808080808080808080e0e0e6e4e9e4f3ecf729363b1a2823ee14158080808080808080805d5c6a5257584e554fff060cfb110ff2f5059d93a9b6beb3b2baaf333a4125342b221d19f20204031a1dfd070c2a291e3b4647273333201a23384c40242c26ccc9d0d0d2d4bdc1b9332d362531261b2a2b8080808080808080803025331f1616140a0f18131c070e03fffa00c7d2cdc9dcd5d2c8d305030af8effeece9f4808080808080808080090e1107080a0204f6808080808080808080808080808080808080808080808080808080b3bccdb4b1bdb0b7c0808080808080808080808080808080808080808080808080808080808080808080808080d0d3c8c4c8bea2a59a80808080808080808018180a090a12111202808080808080808080e2e8f2ece7fadbdcee0e0a0605090d000dfeaafff880958c808080808080808080808080808080808080808080d7dad5dad6ced6ceca312627343028212625110e160e0a0a0504028080808080808080801d1d1e2522281824158081888080808080808080808080808080807f7f7f7f7f7f7f31617f7f7f7f7f7f7f597f8080f08080808080807f7f7f7f357f3ecb37950e2880d20e8080807f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f3e7f62186d7f76797f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f808080808080808080e5f2d30b1517edcc34808080808080808080948580c3a7c7d6dad08080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f59657f3b6b5526286904e97f415f7f7f7f8080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f797f7f7d7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f808080808080808080808080808080808080),
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
    .actor_error_o(error_actor_final_fuse_standard)
  );
  logic error_tag_detail1_residual_or;
  logic error_union_detail1_residual_or;
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_detail1_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc1_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc1_extra_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc2_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc2_extra_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc3_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_enc3_extra_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_context1_residual_or (
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
  binary_event_union2 #(.MAX_EVENTS(RESIDUAL_MAX_EVENTS)) union_context2_residual_or (
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
  temporal_class_readout #(
    .INPUT_CHANNELS(16),
    .CLASS_COUNT(6),
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .PREDICTION_BINS(10),
    .READOUT_WEIGHTS(768'h00fcf8f6f5faf90ef7f6f70106fff0fefc0400f9f5fae2f7f6f6fb0afef280f6021004fc030afef909f8f6f6050b0208f70800fe070800fe03fafa090500fbfaf403f9f60a0e150607f9f9feff05030ae7f5ff0af7010103fe0110f8110d0c0c)
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
    .address_error_o(error_readout)
  );
  assign fault_o = error_actor_detail_stem | error_actor_detail1_standard | error_actor_stem | error_actor_enc1_standard | error_actor_enc1_extra_depthwise | error_actor_enc1_extra_pointwise | error_actor_down2_standard | error_actor_enc2_depthwise | error_actor_enc2_pointwise | error_actor_enc2_extra_depthwise | error_actor_enc2_extra_pointwise | error_actor_down3_depthwise | error_actor_down3_pointwise | error_actor_enc3_depthwise | error_actor_enc3_pointwise | error_actor_enc3_extra_depthwise | error_actor_enc3_extra_pointwise | error_actor_context1_depthwise | error_actor_context1_pointwise | error_actor_context2_depthwise | error_actor_context2_pointwise | error_actor_project3 | error_actor_decoder2_fuse | error_actor_project2 | error_actor_final_fuse_standard | error_tag_detail1_residual_or | error_union_detail1_residual_or | error_tag_enc1_residual_or | error_union_enc1_residual_or | error_tag_enc1_extra_residual_or | error_union_enc1_extra_residual_or | error_tag_enc2_residual_or | error_union_enc2_residual_or | error_tag_enc2_extra_residual_or | error_union_enc2_extra_residual_or | error_tag_enc3_residual_or | error_union_enc3_residual_or | error_tag_enc3_extra_residual_or | error_union_enc3_extra_residual_or | error_tag_context1_residual_or | error_union_context1_residual_or | error_tag_context2_residual_or | error_union_context2_residual_or | error_offset_decoder2_concat_0 | error_offset_decoder2_concat_1 | error_tag_decoder2_concat | error_tag_semantic_half_multiplicity_sum | error_offset_final_concat_0 | error_offset_final_concat_1 | error_tag_final_concat | error_readout;
endmodule
