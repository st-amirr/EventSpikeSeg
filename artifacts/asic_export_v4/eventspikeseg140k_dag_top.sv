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
  output logic [3:0] prediction_class_o,
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
    .KERNEL_WEIGHTS(1152'h707f7f7f7f7f767f7f307f6c7f7f7f237f717f7f757f7f7f707f5e6e7f4d7f7f7f177f7f4d4e61656e62667c582e593e495e5f3d4c595c6968797a6065776050775f6a7f75446d5f7f7f7f7f7f7f7f7f7f297f44727f72296a55637f707f7f79687f7c20694763777f366f68757f7f7f7f7f7f7c7f1f7f7f7f7f7f016c7f7f7f7f7f7f7f7f7f5a647f5b7f7f7f337f7f),
    .CHANNEL_BETAS(128'h7b2f7bb57a707b177b007ae97aee7b95),
    .CHANNEL_THRESHOLDS(128'h0171016601a101940165018d015b015a),
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
    .KERNEL_WEIGHTS(4608'h342d1c280110f8ecf57e5744681933100507493000360101e7f1da4b200734e604edf5d2673f334f0e2106fcfc463911300813fafe017f6d5e7931411a283a7f66687f2c4f13232637261238141c0a21147f594f7f364a4a34274425014802151f1106371c195bff15121d0e73583f7f1c293a3b104b340157f20b200cfa7f7f657f4b557f64497f7f6a7f476b5a574e483a1254062041160d7751145f21285830087a624f7f4873684d437f7b7d7f3c7f7f595c7f68577f375f73575358493c6d1f50513e375e521f6b33274c390b62400d74f908381002342522ef0a1204050f4a40490a1320f3040f49262f03001cfe01ff3b30390a091dfbf60b4f3b3d0d1a25020103463a3ffd1d29ef0512545146192b2604181e484752050f2c0302092b200c30150b250f185e3f367f0c2e4020484f2d2e660828343225493a355f123e432f4471584a79254359242a5e564b7f3b5e553f567c727f7f547f7f67717a6f5e7f24567f406044272a4715201d24096f473c6721394131235c51437f295040483e7f51577f314e343d3c7f554d7f355f634f4358504a781b45283b3453413752053938281863482e5d152d322931401f1f2e121f121d257f5b3b7e2d302f26215e3a0b5a1418262f2a5b2913530f1a1f142b7c56397f264544472c693c185d0e2f221d187f77657f3e6965623c7f67487f2c5351454e0c3a055c141243050b1151277f3141753c33f5390c6c0b1d3b1f16003713680c2b431023062a0066ff133ffefafc491b5e0b053cf8fc3073447f3e427e3c4f2f7a337f3c587f523c),
    .CHANNEL_BETAS(128'h7a437b54799c7a4b7b587a467b4f7aa4),
    .CHANNEL_THRESHOLDS(128'h01c301ed021301bb01ee01f701f001bb),
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
    .KERNEL_WEIGHTS(12800'he4bfc3d0e2fceeccf7e4ccf8e5dec816e110dfde043005d8df15250d3422e9e9f9f90dcfdbd4da0a1de6d9ccf6f600fdf4e19fc3bfb8b3e1efdcf3f11408f1f0f7eefef301e4eefdfef2d5c0aceea68edcfdd3dad0090bfbfa14e0f30f12061701fa0304383247371beef9e8eefac2ccbabcf7e7d3ddd0e5f0f1ddc5d3402d222835f002f006fae2ccd1fcf1c5dddbe200c3cde70d05dba8dbdf12ef9cdceff6de9db9ceedee8498a4df23ebee10fd313c0fd1d07f7f7fe5d77f7f7f0f16797f6c11c77f7f6e16fbd8c8b8d4c5aed0a9e6bb89d693b7b0b9ee9ed0bdcbf2a9b098342bc1889be5bac7c5b9809fe5b1eec3d4e3ebe8fbcd26c0cecfc6bbb2a5f1fdecedf5070b05150eeefcf7011505fdf30e20ad8da48d80a5decac28fbed902e7f8d6e7f31427edf0e9fcf1a4aa9c9f8bc3b0bcb79e100403e8b716251e1cf9142f16240ec1c8bbc4bd0a070605111609191e201116110a17f3f808f8fd1b09fbf5d11501f7f2df1cfdfff4e417fcfcf5e3210000f4ea180a00fcfb130e04f2f90701fef3ea0f07fbefe90205f7f3e180ae80809d808080ac80808080808080809c8080808080808080808baee88080808ae68080808080808080809c8f8080808dc7be80958094d9969b96a89faec79bb6e0e2cbc9c7fee61ae080ba98a7808de9eddacd01b706c5c91223ef0e1800091b261d0b04fe040806fcf9030306fdf9fa0810fcfd0106150a060511f3e6ef0319f4ecf00613f3e5f40612e7e7ec0511ede7f307128080808f80809491c2bb80acae969c96b9d1bee3a1c0d2b7c88080808091808080808580809aa2be8ea5b29abde180b1bfb480808088848085809193808f80808080908980808080828080809f94809580a1b3b0858080a68080ccb7d588808083808080e5f409252dd6e4132433b9e2fa1c32bdebff1c1da8e00a28251c0d05e8f92111ebdef5080df5e2e5190dfce7f80e06eacbf084b7a0b0b4b6c7d0cf0016ff17130a0e1d0c15142913141b038084978084aeb4c2afbaf5d8f2b5d30905db01f1e8fefae0c00ff7f802130bf1f1fc0c02edeff80707eff8f90707fcfefd0b050803ff0206030409fa08010302fb0b08fe0903180511100354121c081a421a14100f39e7fa0df51c020105fe1b12101222b7b1f21e1ce5b0da182880cac91815f5e8e45726defc0862736f7c4f4b3550535e352b0d1509050105f9eacba5dbe7ceb7a8fae303fdffb0bac1d202a0858bc2caa0c0cdacd3d7d7e4e8d80be9f307090fe2ec060b19dfec15121fdcf10e121ce3f21815f4020bf2f4f9061500fdf00f12f7f3eb061106f3e90313fef92013f3ddde2605fce9f326fef4efe516f8f9e6ec16f9eedcecd8e9071a29d4fd050b0cdd00060d0ce9ff071715e6f80a2216f502070409f2fc010002f0fd01fe01f500020003ff0a0a060c05f4f6fc030bfe00040a0cfffd070b03f4f70008fff3f8ff090bfaecfd0a0dfbf0001014fcf3040f1d0afb091b2113001521f908201e0aea021c17f7d3f20607e7c6ef07fedec2e306f9e00a0409ff0afbf9fe0100d0d8e3efead1cdd1def2eae8f0effb0a0d0509060a090f07fe1c0e0e12081510120b081e050e0d11dbff0805f5daf907fc00d901020ef2f713292c2d081a35391e171cf9e51e1521e609201819dae7210ff7ada3eefcce8080db30febacce12b05bcbef94403cde0f0461ccbc6da3916cdbcc5d814261be6d315270ee1bf162b08c3bf1a2911d3bc13291edcae8082ab80808080c58680808080b88091a583c1808080808080808080118080809925808480881a808280da2c808080b43a463907e6bcfeedccdef3bebabac8c1b7c5ebcfda9cadd51b18e7f293b48d01f9ffb4fcf2b0d4ee1696bcf119f8070320250275645f7b74604b60745750435f5e4f4c3b444118fe090ce2fce2d9c8c2ca879b808084808080808280808082bcabbe87b59c7f572b29166360251514695312151843411a0a1e5030231608808080808080808080a68087a4b7decbb9e012261b0f212a2ee62e401b91c11d360e80d434561480cb35532480e32b4d038023cfb6f41e2b00b2f9352ae09e173639e0a7273b25e7a32021200dfeef0310fedbd8d300f2dac1e60dffe2edf51b05000415190d09fafc14191c0b06131418080d0a1008fffef702f9f5fb6737e6a52d612fc28d0f753cc180146d2caf8b1e45078080ebd9e1051effb6ca1d3126b5b139382f9cdf3338299ed618301a),
    .CHANNEL_BETAS(512'h7a3a79947a7c77e27abc77a7784b741c7c357add73417c5f7bcf747c78db756176747a02774f766d74f47527758177907805771b7ab2781f74e87430751f7686),
    .CHANNEL_THRESHOLDS(512'h01df021e01fb018f02a8023f02350254027101ce027c0235028701fe0204022e019c0243020c020f028a023c019402250263026101f70211029b01b301fc01cf),
    .ENABLE_INHIBITION(1),
    .ENABLE_ADAPTATION(0),
    .INHIBITION_STRENGTH(16'h00e0),
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
    .KERNEL_WEIGHTS(73728'h2b1c09324c5d3e3d5518f216feec0e2a13e7433418391f2d230c2938292c061207fff703f101161b17071622fc06f40b0ee7f814edf01b1517ebde0b06fa18e3ebccd9cab39ca39cfdfc06fe090500030620201111141d0505ffeadef3d0c7c9c4c0c5f9ffff02000000fc0006070605ff04fdfcff2024f9e9f20ec9dd241206250e1d14191b1309fcfcdad6d7dcd0f1060116cad4e3c4afd848260706ded9d2d2fce9efe8f222fed200f9edea0ccbbf04dcd40302ecf6f2ea02d2ceedd9d5cdcef8e6c1dbf31e131fe6cfe2fc07fee7e1f0ebd600c9a2da0b07cf0009f9e907001731681d357e15256af80a1927f5d22603f05d27050aeeffefdd0d09120dcdbebefbf4050106f401e9fac7c7ec261415f1fbf7b397c9020017020414d8e1082bd8be11ea2d41304142174a2436f252305b808080f6e2c4f11dc9bdc22ef4fe311f0011160913232a280a0c62657f7f7b56345f5631e3db0540d4ff331039809dd6f7483015faf30a03120203fb00010afdf8e52914cd64195990a380dbfad0b2d0c301050403040dfd0908fbf90a0c0f0b02f7088080808080808891947f31347f3c263b297a9dfc0efcf4120010148190b908fb16f8f513cee204e2ead6ecddcd988a82c0fbca8094bbd3095102354f08ec22acc480afd6aca1cf9e9fae84fd2af3b5f5f346797f66586e7f7f7f809eda91e608a2c3ea98e10915250af1e8bec7cee1eef9c6d31ad730f84323fa386c6719e0d80a0c3125f2fc2462667f7f7f7d64747c8b848080b1a5a9a3b4a1d824fe5f7f3e6f438080808db2c0969da8e4d9e6060b0815190b0e112a1c000b284439fde7d4130e01262525f3fef1fa040302fefcf6d4e0e3eefaf3eef3141b280bfb02260afa0e1215ff0c141c1f23e6f3f1ece8ece5d0edfefd0102fbfe02fe04ea060aff081434231ef704fce3f6deeaf1daffff01fcfcfdfe00000100fb030304fdfe02f6f5f400030c01f6f5050a04fbf6081e25290401f6edf9020c0209edf6eae9edf7f0f3f00c01f2f6f5f7110803ebf0f3f1fdedd9e7d702fff8ee0f14f5f9fbeaf4e6f4fef5d7e6f7eef000f7f0eef4f3ddf0faf4ecfd0c080a00d1e7dbe5e9ebeadad9fdf8f4e1e2faedfe03020ce5fc18fc0a09f00e0c041617101e1414fdf2ece9ecfbecf400fb080cf00500ff01fdf1f3e8eaf1f9fee8faebf4f2f0f7fff0ecf5edf5ecf2fa00ebf5fac48d80414c287f7f73f4aefabcc7d0808095cc1621e430f222644780d996d824eb99fdce808085808481a7b3feb3c480c1e6cd80808093d2f1cbe7d4808080c380a7a2b5c880caa4f503030204f7eb0207e0c7b8f7f5d8e9e1a03a04cc4721f74a3ef107fbfe0a0ffa0803edf30ae7000809e105f07f7f586e2e387e3c1a969e8080808880808016c6f2592d51b6d9ad808080808e808080809bace6da8ce8c8b9be7f333a7f67507f7733436b38795a1d7f7f3e7960fd7f7f1f7f7f0a21b7f62d09cd2d03c4d380801e06d8fddf81b52ff40260303b7f237f196e7f7f577f7f580530ddea5030504533dac71fb6a61322080a4c02bedbbea5fcc581ecc980e8df80dfe1807f7f397f7f5e7f7f7f8d80a397e4dc961ed47f7f7f7f7f487f7f7f130b17f1fa05f1abc3fbf2fc101417ece5e7050f0efef51add98a81a1b1713fdf6cfd7d71e12071eec29fc1efde0f813eb0404d6ebd8060e33f8f431d9e8281514140bf9fce9e8d7030a090004fffc06050bec07ff2114f80007010c0ed4e8f3bae9f7fc09070302fcfe0004000405fa06fdfdfc03fa05e702f3dfccba9ce4fe01d3cabae0bbbb040a08e9f0f6dddfeb151e15030f0fceeaeb1f2311331c17fdf8e10ff60de0f2ecdfbcd50a0f46fefc2abcd735f0f409c4bbc0a2daf300fef0e600e9b9acdb191323fdfd17f2e518161617f5f9e3bcbaa3fcfd2cec0d27b3b9dcd7187fc6e666d8f23face9d5e3f6e1d2dbe1f0e5f6f708fbbbc4ca0f0e04eeece38f98a0dae5ffeee608b3e6ef2a4251270830d3ddfcf7f406ddfd04aebcf9e3bf9727f70b180ebb606c533f26387f7c7f808080e6dea6b3b796ec541e443d227f2f042712da03297f2414377f7f7f2f2e4012555dae8fc08087d97ff5f0807f7f807f7fd45d73f5ebfff1f806f10bf910f8ccf8234d7f216e8f80808186808080800000f20b08f70e00f30708f908f60c0a050bc7be85e5deb7c38c817f7f5ef3d74840447f8097a2a3c5dce98e8d7f7f7f7f7f7f7f607f8180808cf4b79bb09052a78038aba3829780b8da8380e29b809680d18080a38080808080faefeaeeea0cc5d722808081a5ba9cf509bb9084b0cbdecec2b2c780919b80cd9f80948819e9803a2d8021f1bf0fefe3d8db0a27ddfc03fc06fef603e6d7e27f7f7f62707f524a70c1fa80e3ca94f2c39a80ce11804c5c80160480808080ad80808080eec7d440553035f320f4240122ff0740370f1206fa7d47736c527ffe01f8bad0e0b4aad89ce0e657feab1f02d52101141311ef0914004211314c0928386865f90c31f7ee29e8e325f3faf1eefffffb0607f0360719353c34311c17f90adfd5eecabbeefff6f4fcfefa04f7f40101f9fbfff505f4085209dd63f7ba5c06bb4d46617f5c2b35263af0edecddc9cb00c0c81a0320f6eef6d5b9d219301f577f457f7f71d71beded07f5c5ea04dd41762f297f454b7f6306001d0f0c1411de0f331b355b2b0e28030c0706fd10170ff6123be5ce6601c047e2bfd0003bf51838c00a4a185239424c7f30487fd4b503ecf31e241919647f5e7f7f667f7f7f575c437f7f7f7f7f7f21f9e907e1e902c6ce071d1312253bf2d40cc6f030b6da0ba8d743b89f802050d33fe8a6c9d9b9f1b001d7fa0889a2936b7f7f7f7f7f93adaabd16c8808d8003dea416361e411e1144493632616b2ac9ea26e623b312d553f7c67f757f7f597f7f4f7fef01efe1e8d801f6f6e72049f8523f7f7d182d2d0d0f110d3c052903e5fbf609e7fbf3f5fdf9e2e50400f2fa0a7f7f7f7f7f7f7f7f7ff915fdd7d5c5f5262b4307ec54efdb0bd3a7808b808080808080805924010a7f71092f177f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f527f7f7f7f277f7f4d7f7f36463c3e14337f193d67254023df14fe0c0b7f7f7f347f7f3e7f6f7f3d7f7feb7f7f083567cbdb644cd87816c4d9cf2577564d7f084480808d808080808080a1808adb8080aa80807f7f7f7f7f7f7f7f477f0b287fca3979f02a7f7f7f7f7f7f7f7f7f231d16ff121926111f1f1c14ecf903f6fcf4000706ffee0a2ffc0e0a0e05fd04e8e6dbd31300ec04f9fd001e0af8030703fbdff6e9cf220e02fbfb1307ef0d10272ef41129fbfef1fd04fffb0005f903fe0f020c06fc0deaf405f40eeebeebe0e2efc6fffe0001ff020201fbf90504f90301f8fe00f3f40acfbdb8f0ddb6fcfeffc6ced2c4cecc14111ae2f2f0cbd6be050108ece7fcd5bbd00d0cec17160827070d0b0f23eada09cfdfece60c12e00f14d8f805c8f0dbdee8dbdce0cce8f1eff500f0f30502050d060af2fbe3d1e70606f1f1f7e400deb70e2b2cfc281601f61b181527f50524e9f2ef0bfc04e1f7fb09fae0c6ced6e0e7bbcfc8a9f0f2d5dee4d4a3c2c4e4edfceff501cfc3ed0d191f120f2010febec7fd0cb2d812b3a1db431300543ff74c686dafc611fc02007f7f279580805cf5967f7f7f7f7f7f7f7f7f7f687f07e0e42b1af5f0e226b0d8d4d0e49ff9b5abe75948ff291f7f7f6580bca480edbb80958505f9ecebe9fcfafdf3021cf156560d32f230fef3c7e7cbd3d1f295fa06ecf30b0e0214f603edf10cf808f1ecfd8080808080809b8080f101e9d8051aeca7d5a0c6fed3d506dae7f36f5f7f7f7f6d533b421801a67f7f4e7f7f7ff5fb9dff03c38eb09e80b1168000f68094b7b38080ae8080938080dbe194212521ed1fece2357f197f7f7f7f7f8080808080808080808080e78082b48080985919177f7d1e203ddb360fec3235671e0a0280808002f580040b808080809cdc80e7ba80808080808c879b93a4b95c7f88366aaa2c7f80808480aad98084b159742aee14a0d6c1d1c5bfbb80af008080ab80a99280808b80808b808080808c8080808080db8599af0d58f60380971496a201808080443ee620e8b580f2d47f7f4b7f7f537f7f53050a06f205e8e808fe37b320c41ddbba2a167f7f7f7f7f7f7f7f7f07e9f601090af906e6fdf2fe0bede9f30a137f7f7f7f7f7f7f7f7f80808080808080808036241d101171687f5d808080808080808080ec1c43809a578080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7e7f7f315a7f26091c2f15a22aeb95247f7f7f2438780a70017f5b557f3af47f4b0f7870ad525cd57f751480808080808080808093af808080808080809cf4bf8099a18080807f7ffe7f7f167f533d6e18d03780806fd98f7f7f667f7f487f7f51d6d9cd1cedea111627d50019f0de0bfbfd0fada9cffbbde0e9dafec8cad500fb1930113ef8f0ead4f7fbdcc7f42c2f5a1a0b1436f2fa1c23591038471d163e80d4f7cb1a0dca15e8fb070c0bff0c0a0709ebea37fb153605fc0cf414040702e42339ed0800faf7040705fff90cf7fd0dfcfc12040288a58092bc98809e804b37362218071dfcfcd2f7e0214155383651b9b2bd00fd100d132a000e211f1112272719ae8080b6c280b70080d2b7f832ed2df5070ac9b8b4dcd0bf2c2d19fb1315253216fa3df7e408ef3853726e7f7fa2e1c3a4d3bbd7caa3bed6ecc01dfbd80819b4d2f4ffeee7171af8fa08131811fceb102518151d1e181514211d716c7f5d4d5235143780808ea095b3d0abb6809bb7c1fa02043b6a8080b2b7ebe08ab8d8020b0eee1e1cc8bf030deafff60506f40117ff0710151b1cd8c3f10302fff9f405d6bbf423090f05eafa0006fd08eaebea02fdd7ead90d170eca0b24e012224226190a0005eaf4e70d070108070306fcfefa0c08f206fb0a1415fcf0f5cbdafbd5ee1901fcfcf800fdfffbfd07fc0702fafcfbfa04fc13ffe3e9f8fdecb9f0f0e9d6ccecc8d2ce09edffe5b3f2b797f3f8ebe8e4e8ef85c5f627210d25281006080cf40620dcf90dbbe113fcff19092031cb1728f0ec01d0b3e3d8e20de4f5eaefe9f7cebd0b1c2f3cecdd27a2d6240e14160901f4ffb9ac0c091007030cbdb51ff3253ddc3334d83729f2fcf90ae4ebf70403ddd9dde7d4dfbcb8b4060feff9f9f2e5e6f9e0e401ebed06c2f0f5382c141a0518d8dafbecfcfacd01128ff015fb1526052b2eedee1ef50be5ece6cfc6dfcc1f6d661c484ce51225202037f60f15031b29e8021e0cf4e8fb1c260afe18a6d3d7d3d8c7adc7efa190ccb7e6ee83a08080868080808000f704fd01f50a050301f030bdee18c3f1fef8da13bcaf06aaa2eefa01f600f8f103fff7030b02fffc0708f8f5a1b12b92800c989cfd1deacdc8a395e0c5f7e4cae4e3bcc5efdbbb203660f82937f3236105f0152eda0c12171abc92f39584f09488c5b380a3bc80a6dc90d4d2cf0ac8bb10cecf04efe80cc2cef6c2d1c6cca7aac38589ba908ad6e84303f5271d316195b68a9fa980a58082d4f83adb1040e5275e1e52695c4b001bdd043b066a33f56042185215ea07e389b9f8d9c3b90249c2bf0d1b2e5ae4d2b2a4bc938384801d092608f9070d233dffefa8f4c5c3f6c4d618fde11dcae416f1df261bf31afea706c9930ee7e1cca6f8bab20f4033305209de0cf5ff0cece705c6e9e0dff90df83309e412e2f80c003eee0008fff0c8d9fafa03fe00fffdfdfbf4f808f9e2f5dc0903f7f0e5d5e0ead9d8da03fafaf9f90600fdfcfffd0100020007f7fef5ecedd5e7f2bff4fa24f92244ea091800250109ceec06ddc0dffafce2d6dcc5f8c2cc142328092e36010afcf509e513edd212f1b721fa040fd5df06d6ed31f5dad3a2afeea7caeeea00e7e8dacffae3e42dd9ee17c2fdcbd91df9e702eed60cc1f443f814df02fdee11c2d1d9c12df1cf4efeee3a181e40302e022d150202e0fdf4e3fbdfc7061b2c350dfe18f4e729efc6ebe0cefce0cf0b0c3134f6dc0801b30917eee904d60f0acb2af6fad6eadef9151e192b2318efd4ebaea0ce233546d9de03011c13aad1f9d4e308d6ed1fc7d7d5ecf7f1b9e0fde404fedff816ceda0c04192d070517b7c7e8fcd9f6e0dcf4e5def3040b03fa060a0603090302fee5c2cfd9e4e9fdb5b71addaf1cddce02f8fdfb04fdf9f9f80304fd06feff0605fefcf10a16de2a0bf32b1a0625e71712c0d0c9404a2325370ffc1bffd0dbbac4bdd4f8fc08350e2900b9cc17ceebd6e6a7eacfea2f020b0d03de00bcc909caba341b1a6c2e1a400d1affbbbdfed6da2305194e36113a0df606e8d1dabd29fbeb48341d570be4f1e9dbf1fe0b1909d5f607e91015e7233e302302e42715fa0e352a33f1db0430f80a21cee9ea88b5febb811612241ff51b32365a0dfd042106e60ae1e42113122d092648124d7f6325395c54fe17fd1dff211f2d337f3c7f02e8ea13cbe0cceaaf76115258e22a7f7f7f7ffe13395324353f391644436326597f7f7feee6e3cff5d1704f389eadb780a79680c080fe03f20c0c0e00f9f5e5feb5fbd9e4e201fa808080808080808080e90c02080bfa0cf9faf6f1000202f5fdf90580808a8080808080807f307f7f7f7f7f7f7f808080808b808080806b4f777f385e7f5a7f04ea07f5c2c1f1d78080808080808080808080808080808080808c80808080808080808080808080b6808991a78080808087a1a883d1808082b18f8007fc47f5fc9e0207c3eaa19002230353143ed7dd2b7e7f7f7f777c3732ff29fa6a05fc48212f546a2e356df47f6a7f7fd79af91c80f4ebf22a0904a3a99b94dde49e5ceec34d0de830fa03f5cfd7cef1dbf5f809081c110a1417ebfdfaffe6bfdfdcd6f80413d8c0af0a08040b07070cdbefe1e3f6e8d8eef30e1fd9e0c59cab9d1f1f322a2c1e01301a21a3d90dc1cc07bbce00ff01fffffa04f8fd120724eefa0befe6e71e00f61d04062316f0fb07fd03010605fbfdfbfd04fe01fffe00001fbeb70ce8e613f801253431eb090fb8c4b3e5d5d80a0b15170116f3eae910fcf60af0e91619150b02ecf3e800d4bfb7efe6d71b09f0ff082111192503e4ff01dbe10afdea3924242308ee04fdf11e04032a0c2757495f3f313cfbc9d1e6c7d40efafdd9d0f0cbe4ffd5f802d1e8d4f6ebc81eecc5f3ea0af0d6e8dccbe61f1cff10ff02eaeee24a422f2b1917e5dfede7b5adfdbfc4f3e1e1d0b2b904dfe929151ed3d5e8fcebf800eff8b404c6f611e44e38ee134e1fd3d6e9a480808dbcac0403c71f030a1ff0f026031ced000680aefc13d9c81c1a27eabdaa9eebed8080d3b0c310d5c7e580808961f1fd6cea0f1ec805fefafb090ef81211f8172f1e2e1aeeeef7bdbda1b6baa6c9dfc9d7fa01f0f900f3f0f702fb0dfef6ffff0802f97f68fc7f7f227f7959cffee4adb9188097cee4b0cae288d3d691cc80828086abe080aed4d2f0f2d3c5c1d7ecc07f02357f10487f366c7f775979527f68707b41ded329e7151f0620158ee818b30f46d0062ee2cbf9c2c8b380807f3d1e6f71457f7f6d4b10187fcfd93edcc82317012f09632d417f334c5115000721510c3120220df1f9d6f1d9532d2310e611e0f2107f7f5847487f6c727f159ab926c3f80cb0ba7f7a7f7f4e7f7f7f7fefd50105141451537fce160eb80413b6c2fb0626f31e2a637f7f7fcdc6d2cad5e98f8f838093a980d1afadb6039caffd91f31788809804f1d1c1e1dc949ededf12b6f21fdfed04ab080c02f60bf907fa00dcc3cfda04f4c70eda1d1742093b29f9121d04fbf801f4f100f7f5000afb0504f8fb03020bfe10f3ed2cf2eb00fae1c3babdac80808007f8eff1ff04cedaeb80808080aca0809180cdb1cfb2a0d9231d1209f4360f0c51331126ecf30eff23f10bf4f3397f7f2d6c7f05486ce6f2100b35261a11130cf1d500f3f9b7b8f3ca030c162143f329154902cc0ee2a505facde72d5fc1bd6efa017f211009efde42d7de17e09dbdf5d7ec1d2908d8c0abf3d0c6f9e3ba090be71001fe1f2911c6fac3ef08cadaeccf2c45fe221d254e2837bdacc480cd9d80808048f88fc6beb28080808080808080808080808080808080cb8080808080888080a1918091e2b9b78080a183808026eada14a891f1f4db7f7f7f7f7f7f7f7f7ffdf3eb04ebfe01eeefc8d2bbaacc8f9d80807f7f7f7f7f7f7f7f7f020005e7eee403f602030bf10910ed1705f97f7f7f7f7f7f7f7f7f8080aa808080afa2ce49e53a74187f7f467f8080808080808080805839508ff4fb8080c67f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f5740ff53fa807f7f1886c6a3d6ab14e7e53c7f52087fe9b17f7f467f7f7f7f134f7f7f627fe0df1f80d47fc3f0e6b0a4d380b2e28205b80aa5808080808080ed09c680c990aba8807f7f45507f557f7f7f27901a74dc1e7f2a7f7f7f7f7f7f4c7f7f7f98b6afa892808080ba80808080808080808080a0ec80808e8b80e78080808080ad80809a8080b18080809f9c258085b1808085808080e112dc86ebfb8080807f7f5b7f7f437f7f3cff04020d161a08ff124bdee4d88080f680197f4b667f7f367f7f3cefeafd020804eb09f4fcf3f6f0ec0e0606077f7f777f5b2c7f472980809580809e8080807d49594a35154d2838808080808080808080bf0f0f808e92a094807f7f7f7f7f7f7f7f7f6e7f5b667f547f7f2d7f7f7f7f7f7f7f7f7f7f7f5f7d741c6508f9fdad16e3250ba4e0ed7359587f7f1a617dc7744f407c6e785227673cd0db02961a17074d80b7d08080158094802aff93b48080c6a28091a29ca1ae958a8080597f19717f407f7f7fb388ecfb80b8d2b630227f693060794a7f6df41eee1d0903f9fb17f00018defbd0808280f71f13f10547040d2b030620ff0306252132b8ddc2b7dfb6eae0d1cdbee3c8cde0d5edfcd0fe300d0e3ff0181fbd8080cc8580a682800c0cff07030303000cfbdb30f3fbe2a7a8b7ce8dbdb680acd5b4bd050505fd02f8f5fd010afa06f703ff05f7fc12cbf8eaa5f9f6baead7f2fada130bb5f1ec07d0e115fb0001f0f9bbcac3c1c2cafbedf00203f6f1d605f5e11221071002df0f02f0181d0af64d12fb4c18030dd7130aed22f0e30613cddbf1d9c6ebb8e328cbcd5a11f114e2dc04fc1309f9222b09130d16f0f6f5f5f1e7e311174d10d675082177f3d7fbf9c9f9da00f0473b31301a32473945d6edf6f6e4fd1aecfb19081d14e62629071adba58ed38b80ca8b803c375d23275a30495a4c152bd1b1d89a90d0a2b2addeb8c68196803c0f43b2ea1bb4bedac8bbeeac9fe7c49102cfd6b49ecdd1cbfdff99bfaa95dee798b0a4d8d515e4c811dbf31724b4e7159dea1ac1e5050607fe0303050801f6f9e6cef701c8f8cec40d60b71850b81745f5f6fef8fb0000f602f100010206fb02fc0256fbf53a01cb4512ead8d8f4899ef1b2808810b30904992227b624d7e2debed5e4b3cad5cec09edacfcba8bab9d51a32a7f24cc1084ce60e46012a7f004b5910e97ffdbf5ff2f9590e082fc4e134b2013ff6c52f00a54235d73e520b1d34f0f14af9f4c3e72aaeb425bbff07ccf774cbd169b3d220bbe8e6a7c0db93ceccdfd8c9e2f7e0dff0ea00f2e31608f103e6cf1dd2280adc3219e216fddb65e3b14fe6aa32d5083bbcf43bc217382508f606100898aaa5cfd4c0eed9cedac2ccf6e9ddd7ecdd8080a9fdeff2f0dc02bfcfff06182911200f1dbcccb5c2b4d4cdc5aaa8abcbdde8cfd6d4edd5f216e90301f5f7e9f6f3f9000804ff060005051103db08fce5080b05f3eef3f502ea1026190402fcfe050401fd01f6fc050003fef902fc5f2a033735ff481401a6a8b6a9a0b39ba780f9f7ed13fa0716000fe8e0efd2e9f4c0e1e3e003dfcacdc3cfe4c82b2f080e2a082435230433540f34491453431f0fd61c07de4227fc00f0fce805f2f70c0a01f001e0cddee6dd043526f224fdea2af7dd191413171616052313f30a42cdcb28c50220d0c3b5c2d2aac2cfd0e51008d308f4dcf4d4fb2621f40e0fcefaee1b1e0c12110c1509020d1410e9e304cdd1fb0a1b32081726051933f20618bec0bcb3c5bde3f6ecf1eeeddedece18fc1494af80a3b983c4a9a8909189af808033f1fefef5edf4eff6d5cdbbd8beb2bbc099d7edefdbe1d0dec69bdfc1d080a6e5cac7c8fffcfc05f0fb01fff6fdfcf2efede5e7f1d5daf0efcaddeacec8d7f605f8f4f8fcf601f6f5faf90002fef6f2fec4809780889ac6ae80e5d6e7d1c9c1dba9c08395b7808bb5b098a78c8080808080808080d9cca4a1aeb4a8bebe9ba4af8a90a8bfa288bcacad8585918085aacaccca9fbec193b6abcae3dbabc6cdb4b19a9987a280808ad08990e7b4acab9585a2869292abd8a492b4c99ea1c6b4b7ceb6a1bbc7ace1d7e6e1dfdec4d4d4beb89c838a9b9bb19ebeae9180809c968080b18382808084d48180f2b6a780809cb9819caa888d918a80af9780c2c6b6f9093580809a23234a5e545f422e29ba9e836f66406f7f7f1916fe27401e17180decdbfb060429d312243a41532a26f130e9e57f6c6145503205cfd1e55044fb7f4de73220fe030d13fffd0bf7110406dcd6f71307e63139375a33343a050b04f9000afb02f8f5f2eef50ef80a00fa00f8058080808bad8795c8a07f7f557f07244f4c43e70d18dd231be8ffec7f71657f7f5c6455531e3cff787f097f794eb7838098b080808080bcbbb9cbd4aeacacb6e8ed1fefe60db2e30f2e30574f5148182915ff1d49180e5c18284a8baccdcdf6b3b0badb8cc3f4b4fc0080a9a0d3cc88edb88898e9d01701375ef90b31e2eacff60f011a1a03395536687e3c506b36596c85ac82a3b986aa8095db4045f269530d4b268080808db39f8080809b9780491c054df019636b536e6329cb2afb0b018b6c3e417f7f7f8ca1acaadaf8a9abe980809480a5b0ab91b37f7f7f7f7f7f30743c5a587e20457f2334637f7f287f39217f4713eff6f9f6eff5f1f70dfddb15c0d903c2f9c00cf2fb320526730d1df6f1fe0c0900f1010007fef000fb020bf40b7fe8a27fef957feaab636b5e5e4e38cbf02d220afc23eb414aed17808080c9e6bee8e8de17080c6104dd7f7f7f4d391767417f6367457f7f7f7f7f7f7f7f7f7f12066072da7f6dea7f7f2c6c6b6e7a7f7f34427b5a454d650c7f4320a77f1ad97f3fe27f7f7f597f7f29727f0aafd612e32cbaed1a80b5c29b8edeb4959b7f7f047f7f027f7f7f7f7f7f7f7f7f7f7f7fdeccb8bcddb901f8e103396829207f421c77f0f1f709cf06e13227fee2443338121af0444628091558fc1e333d10d3fe7f68237f7f7f8080b8809fd78085fc06f6c2c0bbc8f0ec047f7f777f717c655b7f726d5c18e70d06ecce7f7f7f7f7f7f7f7f7f0e0c150f0f0fff0c0819213ae806007a1433777fd21b60aad031a004f503f809f103060403030f060efcfe01fa7f7f307f7f127f7b447f4e0fd62918ea0871b3b4f9a8a8f690b9098080808082808080804c3a22d7c6a1d001f7747f535c7f411d7f1a7f7f7f567f7f7f7f7f7f60ee7f71d17f7e116e7f4b397f02607f3bef022ac1bdf5d1e319582cfe2f29e626451b7f7f7f7f757f7f597f643ac5733497423680aa89809194c498a60c9ac28099808082c091403c0d297b08fd16182e33011238c6272bd1acdb66d2f342ccdc30c7452ba91fe4c90feed4f9b5281e29fbf1fdefc9ceab9cc2808089b6f5c780bcaf808094fdd8c230fbda2109fa9bc917f315f1140ef493aecacfed06c5dd2980a8a28de2d7808094ea8980079b88129caafff5f303000503f9fa201808ddd1e1dbc2aabfb0d6ddb9d6ecc5e000fffb02fe00f708fbfd04fe02fc0bf5f5fa0cdb4b0308520df84c80819fa2c5d580becf160410fa02120be9f6b6a6d1b1b8e7a7e20cc3c4aa9184d280808015d037220f4e4a34603b07f702f417191621af8e07d6ab25d3c71be8cad804dde5d8d3c9baa482d49480c180804b227f5f327f677e7f6004ec4104f66f040924e1f2251c414e2f56001c27abe617d2f50a012128faf417e6c3d6d7c1d8ddcff1cdbbda7e717f5a6b7f7f7f7fe0bb80fbbc9feab6ab7f7f7f7f707f7f7f7f36be80e480992e460d2516c9f6e904809d8d7f66857f7f027f7f7fa39580808080808080b9fef51900e726fd20527f4c1e423bb5cec049e1c404f7e4808f807f647f7f117f7f0d7f151d130e0e06fa090f5de90cf821c6beadbc4a1e7f27077f1a3960f2f013fb04f50bf309ff190d16f8f624f01d7f7f7f7f7f7f7f7f7f140f7c8096c8d5f9ac7f43141afcf6e8ddca8080808080808080805b17520f0bfc4ced317f7f7f7f7f7f7f7f497f737f7f547f7f7f7f7f7f7f7f7f7f7f7f7f572d191a16db615dd17fc2d850e4c359ddfc7f7f7f7f7f7f7f7f7f7f757f7fb5397f295070161fb88d4a0ae4da330f041111193c07b7a69f95cb80dfc097cf36fe76c4ce61dcc6e57f7f7f7f567f777f7f7f437364a66a7fa5357f7f7f7f5d7f7f7f7f8080808080808080808f8080ad80808080808086808080808080808080808080808080808080afa8839ec9d4e48080809a8080808080be11de9694808080807f287f7f3a7f7f3b7f0bf3f9f1edf2f103efde178001d580db8b8021554071391d68463c0cfa00f80ae4faf1f90c0d02fbfd080ef1f67f7f657f7f317f7f4b809da78081ab8080807ff1e67f1f397c0c57808080808080808080ce809280bed680adb47f7f4d7f7f647f4c7f747a7f6e3d7f68757f7f7f7f7f7f6d7f7f7f46be0923f4fc3df3f8a996802ce8bf4b28017f7f5c7f7d297f7f5277e6297fe10b7fede215b1fafa99102cc6f3a3bee38080808080d2ccb8db80be918ccf91e1f7e9a9beb982e9c27f7f7f7f7f7f7f7f7f9a80b9d7a3f24db4177f7c7f7f7f7f7f7f7f),
    .CHANNEL_BETAS(512'h777474257a5572b3772d759f77406fc67b0370b16afd771479c6789477e374d674f6777177ab7435658b6d7679cc754976e07974737e74876fae75c96bf36c0b),
    .CHANNEL_THRESHOLDS(512'h01e901e8020701a402e501f4021a01ca02ad01e30280022502bc017a01b101b001690217018f0187022f01d5019a0242029b022c01f00220025c01a101c901c9),
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
    .KERNEL_WEIGHTS(2304'h4c254305ddf163f5333d152b1ce8ea40021e131b252e0308612c4e4823f77f0507604d150c1218090afaf1fb021b0b3c0a120e24372e80f1ee83d51cb613448092808039bee1504e3edd3b06f607240b2516f51f00efec3fe962fc0af70009f30a2911421559f1f901200a3335ff2105f20a412536011b1c02192af927096b2f5b18d91f2de61b7f4f767f71584d7e7f12fd23d8ecab8086802520200803f721e5f3800de4b86ff4e235d68880d78e94cbb8acbfee15f80b1c12fb05fa7f026611fc093b0c17b9df12eb1613c514d27f26f3341b16680e572e3147fde10720ee2c3a25263a18452a2d1b1113e81d01ff2508ff001a1cef00e9cdfaf2eef0fc03160524150444cb978080808080802a114af2bd12e0f8f218ea1f3bc4247fe24b),
    .CHANNEL_BETAS(512'h79467a1577ab7a1b76d4792179af7a8577cb7a2476df798d787a7424796b7a4e7c3678087ac7790b76b779717a757ac07822794177637890778f7c5077f97b33),
    .CHANNEL_THRESHOLDS(512'h0254025f024301ff020f0259019a01e3020b01fd023e023b023101df025e01d601df026301cf02530215023801970255022a025501fc0218024d01d802060245),
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
    .KERNEL_WEIGHTS(8192'h35f1021530d4f207d6050df400100afeebff000e21991fcfd63ed009f9f8d7b7bb151000c61b4f7fcb02aa0103ee4ff73bc63e0b8e803080b4562280182c809f04f62bfe07080c28efeef404fc12dcf716f7fb07dcc602d6c5250a15f712ecb105a52a1de0ea0dbfaed3f5daa5f7034fb1f3bff4fd03cd0c187fb012e6c0f315dba98080f6d3f9941d809e95cdb6a980059fdff9a19e089be0d3e7fd80e887a2e109edee1afa4a55d5ffacfffcffd7f41bd401fcc980cf8080030ad1ed23f3807f1d7ffae604ba708a03d93604ecfdd21b1f0106c0cfcaeeb1680ff736b5f3b4ed8ea0fc11b4d022debb0cbb1bd71f0920fdbae70d06f3180505aefff840f31623080396541d102061c7050e56c038a53943f8fef40509f01d37f436dd2b17f50bf14f05ebfb0f6a043688f5f1c206ed42e564f3da8bf7a6caee0bf6e4f9f9ee160040f8eefeddda0fbe1414fbd611fde528bdfcf004d9f60e0ff6feebd8e715ff7f7f36db7f80372a725a7f2b2638801c7f77fb23d313e1809e48245f528a80c2da80f320b61914528c0f290bd3fccd22e7da01283700e20cf4fbe7e6312614de06330f06ef0d08ebf2f4d9d5f4f301060b44ff1101fb03d8ed0af7f919ffefea18c3dfed030020d0dfe212fafe0bf00de101f7c8efdadcb1e31206e70aedb506f60107f5f3f3e9fde3e4fae300090af0e9f8040003f4f90cfc05f5fbe8fe011314016e0ee02d66e931a29701314c305cb846feb280e180e920d9e8ed2725fff5f8fdef10e9feff02f8fd0514f0fefedf0af407fb0deff1130708f1fd1bf0f87faeb61c91974a22800fc2ee92ba7f21a0e480f9b63ddd20eb7f80ccb5801176fa002aedebfe1dd780af0be1a7a647f980fde1fa1334ef2de337cded7c80fa2ae39dfc0bfbb6c3bf848804d41de6ff22bb158bfefa11d117087fc4f31bc9f408f9e747e9efe9e0cdb5d4ebfe89ce2e138004b404de07da141a2feed2e5c5e5012f18230811fc09cfd108e912dff9f125be1acd0bd6fbf9091120011402ba040429ed2bd13cfae5d20ffad51c30e6f6f10503e6ffd60cca20fe2b1414f0ddecf6d7e0dfa6dcbbfaef1485f40313c0f4b61ed1da02ede8f3f8171ecbe9e206e3efdc0b80cfeea91f0f02dbf91709f858e1d0d50303cae9c5e710c11517ac59e0ececfc53e8e822f602f719b8fec9f7d0e714fe1deede8014a090faedf7c703da800a3c7ff5fe07dcd9ede30957f0e030eedb06e9f5f20dfb16f029faee02a7e8f407172beeec09f61208e011073de42cf4070ce407f602f4fae835f7f50f2ff7f97f80801091a35e1a80faa3d1b3cc4e598080c8ff8dd7e415172aa403b180d57f3d8b0117c9a019d68080eeb3ffc97f438a0f80efda24ee2b107fbcd802800734df80fcfcdcb5e1ce80afcec0d7ad7f1781cf800cb611d5094745edd105800542),
    .CHANNEL_BETAS(512'h75ac786d7927746879d17a75760a7670782078747822741076f475dd7706770273ec77a7740f74c87697728b791d75d9787978547841778676cb748f73ff7241),
    .CHANNEL_THRESHOLDS(512'h01f301bc01fa01e0023701c702260200022d01c9025301f2021001e801d601de01c2023f01aa01c9021801f401f802400250021301ef0229023e01b801df01e8),
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
    .KERNEL_WEIGHTS(147456'h0e1efbff1417e3e7f4fffbe4060b080b3332fe070b0705fdf2f8e5f60e02fa0500fa09040e0ef20f05130dff09f30c00ee0809050d04ebf703e5e0f3eaede202ff0cfbf604f5fc011109f72912f918f7e4191f1b1c15332f2940c5d7f0d5d4fdcedce3fe1303f0f4f4ff020aee04fb021f09050401081c12fb0505fd050c03fc0f0405ff10ff0cddfe02d9f6f8effd0c0f0706070c0710110cf0ecece8e9ddeffee7fc0c01000709050e00ee02f0fefffe0610fbb4cfe6b9d7dccbd9d2c4dfe8c6e8f1ced1df03fd08f9fb040800fcd7eafed3ddecd2d1dae5f3e6e600fad2e4ec03deeff1efedf2d1d5f4f2ece9fdf40607f7f5f1f5f9eef9f8fae8d0def3ddecffecfc080706040b0f0e131b18e1f1ebd1dae8e1dde5e3f1f1e0f0e7fbf4efebebe8f4efeef3f3ec03fef8160b01fffbf0050809000402faf2f9e8e6ede9e4f0ebefe8000302080207040a07fef8f6fdf9fcf5f2eff7f6fbf7f3fcedf3efedf0f1f8edf4f8eeebe8ed0cf2ff08fb030af9f4fafbf6faf2e9e800faf803f8fdfff9f3f4e6edf8f3e9efe5e0f1eafcf6f10100f6fef2f3f2f7f5f6f6f4f601031105f6f1efeceaebe7f5ebeceef0efeae8f2f1e7edede4e8efefebeef9f4f801f908f0000af7f005f3f1fef7f50cfcfb06fbf903fbf3fafdf802f9eefafffd04fdf6f900eff0f1f1f9f3f3f9f7f6f1f6f9f900f9fefcfbf9f2f3f9fafe02f9f4fffbfafdf4f702f4f8f102fd0008f8f9f9fafafdf6f503f8fbf2f9f4fa00fc01faf6f7f1ffeffb05f5f403f7ee00f0f6fffef5fff4f1f6f5fb0cfff70afdee0beddff2f2eae7feefefe6f4f10604ef0cf2e5f0e9f9eaf5f0efdae4ede5f7fdf0e9f8f0def9f909ecebee06f3f00c01f802f0f30de8f1f7e8e5f8eff0f7f6ea02f7f80203fd03fefa0d0d0806fbf80e02fddef4eafaf9ebf3f6e30e10070402000b10fdf1d4e0fce4ee05e6e3fff904fcfefef1faf504e9e100f0dd13edd8fffbfefff7f2f5dff10206eafa0cf30a02e8e8d7d9f0d5d2e7cdd3f3efe7f801f5fe02f20ff7f00efaf204f4e71f00fd1503fd08fdf508fb03ff05090e00fc07feef0404000f04fe0c00ed0e05dd1df8e707ffee0807e50c10f210f30303f00405ee05daf4eedeecfcdcf5f80af7fef8ebebf0ede5fdeddef8eae712f2ea0a03f106fbf40503f31300fb0ff9f504f9ec05f4e903eff207f1ee18fa0007ff0014f6f0dcf2e9ccc9c3f2e2f0a7dbb5b8d1cea6c4c5e5fdf5cbc0eac8e3d97f7e7f73607050595c0deedfe2dbd30ae506edede9f5ecede805ffd2e5ebbfe1dcceceee36103e46fe1f38ed1bb9e3c9c0ded3dbc4edf505e8d6e7d4c8e9eb7f7f757f737073696998a99894a9a280988f07f8dc1c121f250807fff5d8fff6e3f5eaf4d4d4bedec0c6e8e7e27b2d4c4f311a4d023bcfd3ced0e2cbd6e8ed351d0407200116f8f82b1718051e13220c105c4346383a3e1af4137f7f7f7f4f53641a4d7f7d7f7f5b5e786476081a14f70608e4e8ee664546593f575c3c2633042d1145111f0f10eb03edbff0eecadfc91320172d36142b24272e493d112115000c012a163c1d1f0a050a1cf1fff11e260429f5f97947567e53565b38377c495f3f35456c3637f9fce8e60c08bed7c0b0d7d2bc9eb89eb9d2e6e2bfd80ffaccd5c64f5c39475235362b2ae9e0dbe7fdf1bbd6efc5f4d0d0d4cdb9eacddbd9d3ccd5cdc5d7c8f40fee050df2161cfad0bea2fbfccfc8c2a713011c070813fc10054d462e4b4b3d3c5028b3bcbdc4c2c499b8ade0ba8ce2f3bad7e4aee20111e60511e80301c7e4ddc1c9e7cdcecf7f7f7b7f7f65625d6f262b241b1d1c2b351ff8f8ecedfee6f1eac6bdd9d2d2f5e4d8ebd0e7f0cdf702efeff4d8daede00cfdf604fce0f108090a1901050dee0d1e0e18111b0a1cf8bfe200d5fefed7e3e8baf8b3e700b6f503d2c0ded2eaf7f2e5c6e1000719020f22190b1cd3e9c1e7e3c9dad0a59d9b97cbb8a0bccbabf908eb0b0ef503ff04010ef8ed0aedfc05f8eeecc902f9e8f6feddf8f4e8f6faf8faf5f5fbfbf6f0f7f7e1e4dbfffdf8f8fbfcfbfcf4f3f3e4fdf3f0f1ebe7f8fcf701f9fefafefdf9f5f5fef8f9f5f1ede8eee0ece4e5d9dadae8e9e7e7e0e8ebdce1f5e5e6e7eee1eeebf0f0f0f4eff0ede4e4ecf6f8f401f8f502f5f7e3dbdbdfd9e4bdc6c5fcf7f3faefebf6f5fae0ddd5dcdedfe6d6ddf2faf400fff7fbf8ecfbf6f7f9f7f1fcf2fad1e3dddcdbddcdc3c3fd04fefffffaf8fcf8eadce0e9e0e6dcdedcf1e5eaede7f1e5dbd5fdf8f3fef6f900f6fafff1fefffafbfff2f2e9e5dbeddedddbcdcceef8f4eff3f9eceafd00f1f0fff5f4fdf7f1f903f400f7f8f90000f2f0edf3f9ebeaecf2e7e0e1eae8edd6d6daf6f6f4eff0ece8f2e7e7e2ebebe0e9d7d7d5e1e7ebe7eae3e5dde2ede4e8f1e6e4e1e4e309fcf9eddef600e9f65b70696b626374627c060714ffde0ff5faf1e0f7dfe3f4fa071a24292e2b1f1c1d310a23fbed060ff50904ee0114fe10200d1d383339aac6c0abccccd9f0fb190bee2f210825020e2d192b3b34173d442cc4cdcde7fddddbe7e84a3a4949443465505824230afcf7f61115ded8dafdf7fd081514200a091109e9fa351b36c7dac6d6d8d0e0d5e6d8ebf2f9fe040b0c1432173d2e284a212a1fc9efd3f301ee141504ef03f5160cf92d3c1fadc2b7bdf0cde3ead4bed5d3cfdfd7e3000404f50f0f141b37252ed4d40205ff1d130a22c0c6cfc9f3d3ddded61435080df3e3170dde474f6d5a435d4b4a4c3b1d23393030474837def9fbf6f3f3e2fc0b94b1af9ec5c3d5e4e8cce3e5d0efe8fae9e4bcb0b4f2e8d50d02fbf2ded2e5d2e8e2eedf05ec0dfce8f5faf7fefae3e5ecde07f2ed04ffedeb05f0e804efe317050405f414fff3fd150f0d020402fefe1001f6e3f3e9eefbf70112f6e414fce91805f11302001b01fd01eff405fd04ecd8fd01f4f718f9fd1811f71904000dfaf715f0fc0d091b28111b2f2500432f1acfbbc0e2ced3f6dde7e6d0f809e20702f2f2eae5e2f4dde0ecfdd9dae2cfe3d3d3ded4d52b1e02161f0b0c030522fce820feef1507f333130330190c2d20130efef41908ef1a020219f9fa0bf9f511030af3e5e2fde5dc07f5e419fdef05eff401f2eafbfff9f508f7f804f8fcfeeb040df41bfb15faf7e0fd00e4170afd1efaf717fe031c180c1a0c16121a071516040f01f11201fa0806f715f7dc15fbe20ff4ec2304ee2603f520fef2f4fb0100000504100decebf1f200f9151d0d12130e21161e242428050302fbfa01fa0202020002fdfdfb010204090505070a0711050cf6f201f8fbf900ff04f3f3fbf6f6f8f4ff00080aff05180e1c170cf0f0f5f4fd02f202050c070a10110b0b0d0af7f9fafaf902010502e7f4e9effdfbf9f9fcfafc00f7f900f3f1f8060c15fafb0b1e1117fffb03fbfa01fcfcfff8fa00ff0504030c0bfafaf8fefc00070dfeeffbf7f3fbfc030afcebf2ffeef7fdf5fcfaf2f6ecf0fceff0f8f4efebedf1f4eeebeff3f6fcfcfbfdfef90105eef6f0f2f7f7f1f6f4f4f5f1f9faf7f6f9f5fb00f6070208070afa0c090d0c0b0a0a0a0aedf1f9eef0faf8f5fdf3f9f9fe03090d0a19f4f3faf8fcfd010804eae6edf3f5fafcfaf6ecf7f6f5fbf8f503001b1715170d0e0f171d15191427292d2e2a2c0a1b13fc050107070ad5cabbdcd3d0dce2da19060d1b130d14101c05fdf60b0bf909050a05fef8fcfcfb150a08ddded8dcded9e3e4e7100af40e00fa120a0e0101fc0c13151c2823dbdce7e4e1dadfe7de1d1c1113100b1c281d0402f8fffae0fafaf0fdf6f3f5f0ecefeded05f7e406f90c020202dfefe6fcf5e6f3f3e9e8e7dbdee2e0e5e1e9ff0a04110f03040d0ddad6eee3ecd3e5e1dbdecec7f0e3d2e0e3ede5dff3efe9f9eeecf1e6efe4efeee1e9e9e0e9efe4f2f6f3f9ff0005100e0c0f080b0615fcf5f9fc00ee04042205fcfdf900eff8edf11019180f18171a1122f0f7eefa0101000afdfe01f7060807fa09fde0cde0d6e4d6dee1e8e0e3e3e2eaede0eb04e5dbdfeff1e2ecef02fef2f70a0d0805100904030504000011f5f40606051115091e181ae5e7e6eae1ece8f2eafef003faf9f5f7f8f3fbfffd05080d130406fafffefefcfb0700f2f4f8f1fbfcf8eaf4f115121a100a110b0302f1f90004fffe100201fbf5ffe4ede6e6e9e1eef7f3f9f9f00efae9121719191514190814efebfbfaf8ef0c08f71e190f0901fd0bfe01f1f5f9f7f2f4fcf7f7f2faf402fdf90c01f6000707110b07130e13dbdcd6ede8edeef1eaf5f2f3f1f5fa09fceeeef2faf0f1f0e0ebf5eaebf8e6f4faf2f5f2e9e8f7f0eff4fbebe301050d040f15ff0404fdf8fcf8f3f002f3f3020afb0303ff0cfffff5f7f30007f80907fafbf1f5f8f7f40bf0f10f0f16040503120400e0e3e7f0eff2edf7e4dde7eaedeae2e1f4ebe4e7e9e5f4f1f7f1e9fe04030e090f0c0e13fffef0160a0b070912f70b02100e0711170f00f9f9090601110e10f4fbf0f8fefafc04faf0f4eff7ffed01fc01f8e9eff7f9f6efece6f002edfc02e4090602e6f7e30803f7edf7e9fffefe1012fd080200e8f2f0eaf3fbebfbeaf3f2f0fe01fcfd00f6ebf6f0fc01f6070407f9efeff6f9f9fefffaf3f8f904fff9f4eeedf6fbf00bfdfc07fd0df0e8e704f9f9070000edeaf00400f8202011f8f6f30e0cfa0d1304e1e8ecf6f5fffb0601e5f0e4eff2f8f60d03e9eff9f4fbf206fff5fbf9effe0803060a07e8e8dff5e2eaf7eef3f5fff1fdfcf10af207f802eef503fafef3eef6f9ee02f4f0f6f6fdf9fcf5fe0502f904f7eff4ebfc0d01fafbf1f7fcf301fdf7fe0703eefaebf3f4f5fffcf9d9e8e3f4f2ee02070a03f4f605fef600fef4f0f5f3f0fef6dde9e7f9f8fbfefffbf7f9fbfef9f9fefff7fafcefeef5f1fbfcfcf60200eef9f1f4f9fbf6f3f3fefaf004fef800f4e4fffdf4fff7faf8f5f0d5e0dee8eeeef2f0faf1f0eceff4eee6dfe90dfdfeff030201fcf8efe8eae9e9e6c2cfdcdee2e0e5edf7ddf6f3f9fbf301f5f8f6f3ecf8f2f501f6f601f7f2fdf8ef00fbf702fcf1f1f1e801fcedefe9e0f2f7f1faf6faf4f6f9fef0e302f9f1fdeeec0af8f405fffbf8f1eb0500fd05fe00fd01fb1405ff1601fb0f05f5fdf1e702f2f3f8f0e6e1e8e6f2f3f6eaf3f104fcf80200f60201f8eaefe8eef2fbe1f4f4eaeae9efece4e4e6e1fef2f5f1faf6edefeefafbf502f8f702f7e7f8f5ef05f9f1fdf1e8f9f0ec0bf9f600f3ee00f5e80904edfcf5edbf8fbdd5ccc3a0b9b1c8e4e7c3def2112e12f9fd0e502939524d2f7f7f76606b492f5646b980b0ecd1e5e0ecf9b4bf8ea0bba28f9e80ddd9decce4e8adf9d1312f4024fd190ef51587bfa4d634f8bcf5eafaefe2f8ebfaf5fe1e7f7f7f7f7f6c6c655383848691bb88a8ba96809bc7dcdce5d3f9edf5e8ced8d3d0b1c9b387818080c18b95bf807f7f7f7f7f7f7f7f7f432c0f321a0e081007f9e8e1e0f6fcf60ffde1dfdef5efd3f2e6dbc8cedcdeb7adceae843a553c3424171809033f341652350e2209fcf709fceaf2dbdfe6dc14041a31130d0834f352f4ca4227dc4d1de5d88987cd9cba9fc580c8e8afd6dfe3cd00eee6dfd0f8ecceeee9b1f3e6c916dde1f8d2d6e9f4f0fee9dddaf7cf1203f81001ed04f9f5ea13f8fbfbf6f2ebe203010203000007fe02fef8fd0c110506030efd06fdffff1102000604000a06000b0c0005fe07fb0502fd030304f0f8f5f1f1f4fff3f8fbf3f302f9fa03f0f70cfaf408faf407fafbe6f5f4e8efecfcf2ebef08fff8f4fdee04f90400020bf9f80afbfb00fefa04070903fdfe01fe070efbf60d01f80efaf80efcf710fd03f3f5e701f9e9f4f4df00fdff0801f80703fceef4f9efeff3f6f4fb170809160d0d1a130c06fdf606f7f506f7fc13ffff0cfcfa0af8f70bfc0307fdfe10010413050511020411fe09fff8f70200f5fc00fafffef7fdfdf20f04fefbf5f200fcf401f9f7f50308effb04eff803f9f3ecf8f7f1fbf6f5f3e9ea00eef007f4f6f5f5effafceefdfbf402f7f807f9f800f4f802fefa07f6fd0ff6fd0f04ff11fff811fd03fdfafdede70bede2f6fefb05f1f9f6ebe9e9eee6e9e4dfe5fbfbdcef010bddf314d5fb040afafddadcfce0ceffe5e8e8e9edebebe5f4fa0b1afa0b14f2df09f408fde3edf6d9d5ef2a292b1f1a35f1fe22000006e7fcfeeeece303e608c6bfe7c9bfeb110affe7eefcd8e9fe0fff0f06e704e7eb01e9dff0d0ddf3bfc8e80cfe1000f204e1f70bf20001d901feeef9010b0908fd030cebfc06190f150f1722fd06f9010f1600100fe5fafee9f9f8eef806dff5eaf4fefdeaebf4dbecf0e2d4e0e4dcd5dcd6e00afd19e4f2fcc4d7f51d3135141b23e8fb1a06fb0ec9e7ebe1d0e4fa07f5051704f307ece9f10cfefa06faecf8edf707f8dffce8db04fcfde9d0ece3dacce50f1c1ef60d1adff306050814effb0ce5eb02090d07fd05f5ecf3f0eff4f30607f90c07fd0afaff11fff802fcf202fcfa0706fe0305f8f9e7e40af8f314f9eafaf5f200fbfd03f7f9f9eef708fefc0e0406f7e8e9fef1f601f4f4f4e3e603f6f300e9ebf4f5e8ebf8fce9f3fb01fafc1602ff0e070010f5f814fd0a0f021913f5ef17fbfb1500f9ecfaf6f9f8f404fef5f8eddffdeceb06f8e6f1f3f8efe8f0f3f4e9f1e9eefffaf50300fb08fbee08fefc100aff03fcf808f2fc221112f7ece103f2ee09f9edf6f7e203f4fa0f05f800f8f115050708040ffcf9e90502f41306f606ebe806fbf21500f0fcfaecf40101f4ffffeff0ee03ebec04eaf304fff6ebf7f6f5fbf1f9eff805f8f70701f908f0ed13fbf50d01f40bf7f918030008f70006fee31203ee0e08f6e4e2dbf0eae7f1e6eaeceaeffef8e506f701ead6e3e5cbd4c8bbe7f81afc04f803faf9f7cac9e9dce3f0d7ddf9f9dae214e9e2f6fae5fff61dd9dbedecedef08fe16fa0b17e5080c06f0e607e6ededd2e20cfff31dead716fae2181b2e0606211bf817e805eed4cfdcd6cee50fe6f30ceae211eeffd3dcefd9f5fdd7d8ef1a111f15f5f5fcf707dde1ebdae4e8eecef100eafb0af1e4e5d7d1f5f7f5fdeaff01d9ebaa9cabb8b6b0babfad15f2fe1e0211150c1917f1df21fbe30b00e124f8021e17fa1d0fea1dfde420fbf72509ef06fad818fee1f8fee51512100a1214230ff908f10b0bed0ef5e007091121f2eafcfaf52021312eea1e36d0de1ffbef14fb0910dff6060ff2e40b03ee12080626ff031003000c10ff06ecee06f9f8f5e3d907f2de0ae1dc09edcf1cfaff1bfede0fffdbfcff04fdfe04f902fffefdfefffcfaf5f2f4fcfefcfffd010202fcfaff03fc04fdf8fef8fb03fffafa020103fbf9fffaf800fc01fd01fafbfbfdfe02f8f9faf7fcfdf6fcfbf4fbf9e2f8f1f7fefbfb00f3f7f6fffef7fcf8f4f8fbfafdfffd01fffffbe4eef2e7ebf3dcefe4f0f7f3fafa02fd01f8f5f7fef9f9f9f7f3f402ff01fff9fefafbfbfe02fb00fe00030002f0fef5f3fdfbf5f6f5fdf9f6ff04fafc00faf0f4fcf7fbfef3faf5f5f9f6f702f8f1f9f40002ff010401fffb01ff0501ff0001f903fcfcfd03f601f7f8faf8eff5fafcfc00fbfbf70805fe020007ff0804fefffa03ff00fffcfaf5f4f9f8f3f7f8fafcfb00fefefefff1f7fbfa05faff0103f801f6edf4f2f6fafaeff1f3effaf8f9fdfdf8fdfbf3fff5fc02faf2fbeeff0b0910f9f5ecc7d10c08f5f5f4fbe7f0010604f8e0ded6ebdef40cecf8ededf8ecd3e315231909fbf9f8d1eafafe0df7fa06fae0f40a0d040afe00ece3d916fffafff6f0f0cddb0c121b0c150a240400e6f3eaf2e5ffe8edfa0b0c050ceffbf2c9e9eefae8f9e6e0eaeaf5211d1612110639201001f5f7fceb02d6beea0b1f221f131a07df03edf4eee5ebfdd3d2e3f1e4f9dcd8f3d6d2c200f515e8eff60201020f03f212fc02f8ede428100d0a04020ceaf31b11080bfa05f9d3e706030df9f3f4e8d4cf04000401eaffe7d2fb080a100308020ff6fc070f19fefb06c0c1e210122eff010a090b021a0a120c130dfde7f61f131315030cf5e0ed1a111710040b06dbd3070af607f4fbf3dde4100cfc04fa0afbe5e1140d040f060d01eff005f1eb03f1f503040c0008fa0607efeef4e5ececf0f8f00de1f5fafbf6f5fdf9ef03f8ee0dfa041af1f4faee0508faf81102ec0904fafd0cedecf8f1e6f7f0fdfffcfdfafbf9fffc18fae21b08ec040b02010ef81204edf405e9eff602e5f3f3e4ede607f6d11cf7e706ead42707f91a0502160e18f3e803ecedfefaf8f0f6f7e6cee5f1e4d9def3fe0d0106fd0817ff1c150c0a02fc0603f0e6f3f6e0fbfdf102f62e211e1bff0216021b1f090315f1e91cf7fdfde2effce6edf7fef0cad8ead3cfeaededeb080a0110f9f11bfef8ecf1e3f201e5d5dbe7ff08f2f503f6f602fcfaf7e9f3fdf6faf3e702f1f0f6faf9edf7e81103f21cfff31802fc07f3dcf8eeebeee0ee27141a13050511ff0011fef107f8ef1007102a04ff14e8f31a0606f9fbefeaedf0f5fcf7e1eee8f8fbe420170eee1308eef0e9e7e8da0b161225220819091416150d151a0f1c200e120d0c0e08ff0f0c0cfd0b0eedf3fde2ede7b2d1adafc3b2acbebff1fdfeedfb0bdcecea19180e1a110f1d0f1cf3f7ed01fff8f7fd01f4fae7f0f1f3ecf8fdf3fb0cf4061101f908ece7f2ebe5ebecf1f4d7e9f2f8f8f014131002f20102f7fefdfef6fdf6effc01f1fd0208e7e9ebe2cbe9d5cec5d5d5d3dfd8d7d5dddaccddcaf2fbf3e6fef2b3c7b6c9c0c3babfd0c9c5bdcdcabbd1ccd0f2f3f0edf0f3f907f9b9e6d2ced8dbc2d1d6d1e4d4ddfbd7c1dfd7f7ff08fcfa03f0ec0c190d06140f080c1508d6f1f6caeaf2dceff5d7e2d1d9ebc2c6f9e9dad6d9ddf1eee7e2f0e0e2e6edeee6e7e3e2c9d8c9d4eed8e9ece3f4fafefafaf9f7f6fdfef5fdf9f700f8f9f4fcfdf9f801faf9f701f7f2eff3fcf9f0f8f902fafc00f904ff05fefdf8fbf902fefefcfdeaf2f1f7f6feeff8f2e8eef3f6f5f3eef2e7eaf6f0f7f4f4fbefeefbfafaf80000f9f9fefdf90301fbfa0001feeaeff0f1f4f3ebebe6ecf3f6f9fbf4f2f1f5e9e4e3e5e2e0e3dfd402fff8fefbfc04f9fbfbf8fd02fdfffc03fbf3f1eef8f5f5f4f8f7fef6f500f9f8fdfbfaedf0e9f1f0e9e8e7dceef0f0ecf4e6e0e9e400fbf7fefafcf6faf3f3f5fcfcf7f8fd01f7e3e1e2e3ebebdde5dfdfebeae8ebebe8ebeefcfdf8fff9fff900f4f0f8f4fbfdf9fbfef8f3efeff4f8f6ebf3eee8ebe9eef2e9dde2dcfafaf6fbf7fdf7f5f6f3eff1f6f3f7e9faf3e1f2f1f1f6f7eff2ebeaf5e8fdfaebeaf8eadeefdac9c2cb96a193fefae6fcfbf7f7f0f6ede4d5d7ded8dbe6c51f2a1b15261a091c16dbebc6f50213d9cbc9312b3f434b55433a49070702251709120ae3ec00eafb00e3e2e7ced1e0e1fffd07e1e805fbf4eaf2dfdee0daea0210ea0c19f9f004fcbec2b7b6abab9eb19bf0fcee0c1502f8fadb26272d202615131e00d0bcc1cbd7ced3d2bb10f51efe0916fdf02824170106030b0714ffbfa9c0b89c8dada7afd0e5c9e7fbdff0ffe3fc0ade1214feec09fbc9d9bfd9e9c2dacfc200f8ed0dfb0df0f5f1eef5f0f7f6f0eefdf0c0cdd6d9d7cdd7b5d580d4b784d4b59cf3c4e4d9edf106ff0bf8131c1a35172e2e1b1e2504fdf6f200faf2fde7cac0c4fcf5d216eee3ee15f7fd06effef8dac1d5c2cff6cbcbddc2c8d1accdd7c1d0deb5c5dadfe5f6f8cfdcdaeee2ffd8d2e6c4e3e00bff1716f20e0cf401130c0f18070b110906edfbf6fdee0bd7e4ebe2dde1eaf2d6ded2d5f2ecd2e8e5dfdedfd11103f80af4f8fb05fad0dacbe2f7dfeff4f6c5d2c6d8d8ebdedeea382427353114342318cbdec4b2cbb1c0e5c2b2c0aeeed9dfcad7c4dad2d1d1c4cadcdbdac9c9e7d1e3edc8bdd90d1b052120181c21fce0ded4e7ebd7ebefe2dfd2dafbc6c401dfdd0b03e301edf1feeee9fcf3f40203ee050a0334181434250f401e053f3f1838381f3e2e19e9e9efe2e7e5d4d7e31519e31616f71320f32809c81fffd918f7d5e3e9d204fae313fde5cbe3d9e7ebecdbf2e4fb0deff9f6e9ece5df2a22f516f9e900ecdfe7edd5f5eedef8fff90df9f916fdf00c0afe1001ff1a130b22151df002e5f4f7eed9d1cdefecd8e4cfb2d3d3bd081915e9ebfdf1e5dd2f2b051313f10704f805f8d61f1bf10805e7f906f30208ede6e9cef6fce9f9fcf1e3e2c62a02df07dacd0a01f0b4c6d0dae4cfdedec4eedfdce1dadbe4e2db3f2cf32513fc09160cd5e6dbdae4e1cfddccb5d3b8e9eadf11e4d81a260c1d150a061700f209f7dee8f6e7f3d9382f223825080d1218faefdff5e9dee3e4dee9faf0d9e8e1f1e7e0f8f4d9f0cad4e5e9d9050c060ce5e5ede0de4a17e81cf2eb16faf54c230b2914e92b0d062116010a0efd05fffd1120011006fc250ef601f7b721f1e80ee9cedccaccdceee0eafbf60b06fb0c10f70c04fb0f07fbfbfeecdfe5db1616050b0dfcf7fbede5defae8d8daf5f3e5300ef12ffae70ce6e8eef4d014ede1f8f8f94a0f2d2f2b1c351d256f5a3e7f7f7f7f7f7f02ceec10fcf6f1e41b8080809c94a5f5d5ee3b373a201a27130d1d1002ff1c150b060201342b423f1e283f2428808ccb97d9d2e3e5eb3418160f0c1027050d1a0ff8351af5442027a98fa2b3d2d1c1d8da3833193d2c2349292ef3fadff6efff1a05f9c49fb6c5c0b4ef02e10af3fd00fc15f9d2d380adb1adcac6cde7fca2b6aad4d8c9d6dabffffd202e12fb3b371594b6daa8d4bedb03f5ffe8e91601ea2713268091c9a3d5dd040f1fcc97bbd5c2e3def2f8dff4ec16efec2d0b05203b26223434252a19c9cdd8dfdd1dfdee1623253d09fa1f170e0919fe041409f41c140b43252d4d282d7f705f13292148222d44382780808080869f9abdbaa1d8fdd4c9d8ff111d8080bda9c4f3e2e810dedadef0dedfbbc6bebbd1c097bdb79fb4a8f3f0cdebdad8e1efefece90c00ed13ede510011a0ceafaf5e1edf6d5dfcfc8e3e3c0d6d4e8eff5e0e1f0e2e3efdbedfae8ed00ece805f4f805efff14f1f603cbcebabedbd6bac7c60af4fd0dfc160e000de0c2beccbaa091858004fc320d102b0b2023f0f2f1e1e2f4d4daef20061810ed10fdfe05e5f4f7e8df0bebf0f6cfd9ded1deedd4dfe213fd00f71411090f09e2e7fbecf201f1f305deebfae8ef07eff1061a162b141823171f2c1d161320131f231d1ff7f4ffeffc1bed051d000701090a03060a0d212428171827272236f7001f111431021f26e8e9d0e1e7f2dde9e6e6e0edefe1f8e7e1ec2b2a3631162a362725dceef9e4f6fce4f20000080b03ff0f080c11fc0619090820030c17f6f0ecf3f3ebf0e9e9f5f4ecf3f5eae3e3e7f8fbfcfffdfdfff9fdf2eeeef8f3e8f6ebeffffffe020100ff03fafcf4fc00f8fdfaf4f7e1ebdbe8e5eae3e7e6f3edf6f3f5f3f4f8f4f1eaf7f3f9ecf7fbf8faf8f2f5f9f6edeaf1f7fcf1fcf9f6fdfcfaeddedfe8e9e1e0d1d9faf7000302fa0804fdf6f6f2ecebeaefeae6f5f4f4faf5f5f4fef1fef4f5f6f7f9f4f7f1e7ece4ecede0e0dfe0eef4eef2f1f6f3f5edf2f2e7ede9ebf1e1ddfbf4f8eff0e8f4e7e5fff6fefbfcf9fc05f7f4fbf602f500f4f6f3f8f8f0efece8f2e7e3f0efe9f7f5f2fff8f4fbf6eef9fef8fef8f3f0ecdff8fae90200f7f5eeeaf2edf0f0ece9e3e7e9edece2ede2ecf3f3eef8fbf2faf6efeaefeaeeeee5eedfe0f3f3f3fbf1eff6f3f1fef701fdfbf5fef8f2dbdee1e8d3dffbf0f6c6cfc7cedad9c2becbfc291e3732291806f8201f2128220f1c2024d6c0cf09fae61e0d0ddfeaddedf6eab6d7bf100c080bfd0cf3f9edd4d5cccac6d8cfd1dcb3bec1dfe1cfeaf5e0f2dfe2f8ebedfbedf15b4f47434450464c49e0ddd9d3ded9caded69cc3a5bededcec03f20b260a080f0c0000fc02f1e9cce2f1f5e1f64945522618403a1c2af3e6e1fbf7f6fceef0201017323f27390f17cbecc0cfd0c8f4ed09f0f30be0c3f9ecf70b1f382e2c0e2e0ff71a56414c504f3e43323d080f03ff0314f50a10403d2d413a1e46363c06f8c10d06012a2c06e6cac6d7c7c5dfdcbff505e6fd0aecea03e51512070a1111ebe7022d1606ef0d071502edc2b4dec2ced4d3f8d7fdfefefdfafff503fbede3e3ebfef6fd1422e8e8e503eefa0c0bf9383c3657444c43374403f5e1eef9f61603f8d1d1d1f7f4fe0a0e11f7edf1f5fe07010a11140902200b1709fe0714070529171d2226259fb6b2bcd2cdeff3ef08f5fe090313f0fc0dfff0e90c0d101f1110cbe0e1e6e6d4f2e2ed0bfdfa0c06011009fff3e8e2fffbf9f6fa01bdc8ccd2d7cfe2f3ddffedf8110b150aef23e6f3f1f5f1f9111709e5dadffef3eb04f5f90b0af6151b15101c20ade0d1cfe2e4e8fcefdbdaedebdee5f300f3d0e4e7ebfafb111001c5e8decdead2f3faeceefbfc05f9020d0b0ccec8c7c3e0d6e1e5f1ddcfcfe3e2eef806f124010105102c1b092904f9fc01f6f5f9f8f91b1f2c29213030261bfbf2fdf4fb1c0c1104b0bad3d5e0f0d1d1e4b0e3e9c7e8e5ec0c01bcd0c4cddcd6e4e2d9d2fff11537184a4d2dcfeedeaac0ba96c8db4d57475b6f4e503f471d0c142d18110e1708d3eee7263e20393521c7b299bcb495d8c1e1dcc2bdf2e1d5fff6020b18052d351324251ea9b0c2b8cdddf9edeebfdacabdd1b78bb7a0337d645f674b667f56e1efcfee01e9e6f7e9d4fcf4e20d0d0a2a15e5d4dff2eef10205fac6b7b8dfd6bf01ccc021283c20f60a1202ed0300e302040108eef9233a0e253319413e2ce3e3c5effee406fef3c4d6d4f7eae10bebef707f4c7f795f7f7b7c4c662a7d5e267c6437cbc7b8d9d6dacadeea3619ff322be537330210e1bb2ffbcc5d41ee0bfad9dcdad306fcf59d9e9bafb1a8a7bfb3fee1d7fae8e2ff08fa272bfb2b562848332bb0b5bdb6d1c1dadbd0f5f6ed070af9331329fdf0dafe03e624181894b4b094b2a7a3c0c1e7e6fad4b7ebbcd3d30d08f2bec0fefac7fa12090e0f171d0916fcc4acc2adcad3b2b5c1ffe2e2f8f0260bd50bbdc9eaf3dd1f1f060e0af7f81808030f0e0ba5a69fac98ebc2c2d394b8959eb4ae8d8080060b0200daf406e4f08087809dce8c8c8196bfc7c6d3decbdaf5dcb58580a680a5ac90abcdabbfc7c2bae4dafc3f252f0f14241c2024d0bbc3ebd3bfdab9cadacde0fbb4f31a06fa16f2ee18faf411e9f5f0e5ecf2dbe2fdc6e42d3128234b34304b1b57442c4a372f452d2900dee104dbf8d5f2ea23dde026e5d53214e16935fd7f0d1c7f431fdbb4c2e7e8dcfbbfcb808080808080808080f0ea08f9f807d5041a5337115e18fe603f1be5cee1e6e0d5f8e4f0130200211411241a0c290e1424051c1c1e29191e2c1304f9f61f134e464d5b54557e717f190e10292e1ff9faf81a03e73a200a3c3007f7f2f80af2fad6d5fa4d33423b274a686061e6e011e8ec2cfa0b37dde1e3d0f6f4ebf1fbd3dfe9daf0e9c6bede2326416b40305e5269fded05ec00f1def205473659464c4f3b5751bbfff1d2eceecadbe40e041fef1727fe1b2bc9ebf0d3d1fc08110d311b1c3226295636424d3c53544559645767ff01f4ded217e5e3f8f0ebf1f6f600fc010ad8e1dbcfdcf2daf607cab79fbac3bfabd8c9afc4cedacfdedecdf5ece705f70411fb1816aebef8a7baddacb5dea49bb8b7aeb4edcbde16f6e70d09f60bf8c6202c3a142024302f3d09f304040a121019239fa5b5c8abd3aaafe40002001101061d2a1bc9a6c1bec0ccc4d501b0b1bec0b4c3e6dad7010204fb0202f3f903fef7f4fcf4f100fcf7f7f9fef9f6fbf5e3ef0a11080b1209121212fe09fef2fcf5f2f900f8f4f5fff7f803fbfc05000203010500020a080704040d0a070908edf1edfafdf2f1f2ea0c10060709020d0f0b0605080707030b0b080507060005fdfd0503e2e5e5f3f1f6e9e2ea0c0b0c0f0c100d0c0df9fff2eafafaf8f7fb050aff0f09050e0a030c06fd0a02feff01fe00f4effbf7fcf9ebeafe010aff0006040408f80003f90305fe0806f9fd0200000000fffe00fc0100fb01fff9050e0a0a090606080b0f020703feff02fdfefcfcfef9fdf6faf4f6f7eeeff7e8e8eee3e3e70702ff0b0709090b0b070407000306fd04070302fc040302fb01000a0e0f0d060f101113fd0107ff040601020900fffefffffd030205808084ccb2b5d6d0d010230b809c9c8080803d2d1b37466e5c15e5506434201d1f1724fdb080990ef5b508ecf380a880ce8880808080e3c09bd1d4a5edce9b39321f3e531e362f0e808380cccbd71b1301bbe9c1aab8808080807f7f607f7f66697d279bc2b1bbc489809180918080f4cfd115ebaebcb6a9d7ca93c7ba9dd39880e3d6e7dc15cf612f177f2036663e1dc2e2cbdcefbdb6d1b0211af92a2f18ff4118e0dbbfe7d2bbf7d5d8acb7a3bab4becfd2a97f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f78dcd9dfe7e9dfd1c9b9404bfe7f7f377f7f44733ae77f680c7f7f238c8080ed12335108a7bea89de1c7999fa3860ef7de20ffe5f0dcd4607d51737f6d6e7f78dac7a5b6c3c7cdc7a7444c2d535e18597942665a1221223947484100fbecfafdfbf8f8f9faf9f7eff4f4e8eef7fffcfb02f9fe01fdfdf8f0f1f0f2ede9f0f101f501fafefefcf7fafafefcf8f6fefaf5f9f4ece6f1f5f2f7e8f9f1f4f6f8ececf4f5efeaeaf8f3eff9f9edfff7fff9f6f7f7ebf5fd01f7fdfcf900fdfa01e6ecdfe8e4ebe2e4e5eef5f7f6fffbf900fde7f1e5eaececede2e0fef9faf600fdf8f9fbf7fbf9f6f400fdf800e5e9e3edeae7e3ece9f9fefbfc0100fefafbe6e5e6eee6ede9f1f2eaece6f0eae7e8ededfefefcf6f7fcf8fef9f6faf7f8fcfff5f9fcecead7e7eae1e4e4ecf0ebe1fbf6f0fbf7fff9fdfcfdfa01f8fff8f6fbfbff0002fc0101eff1f7f1f1faedeff4ebeeecf1eef4f2e9f5f9f7fefdf8f6fefbf6e3ebe6f2ecf0e8f0f3f1f0f2f0f2edf1f2f3e7e9e7f8f6eaefedf7eefbf9fcfafbfc02f3fafdfd00fbfbf9ebeefdfdfffd02040102faf9f2f5f8ecf3eae8eef8fafefefe00fc04020104f9fffcfbf6f9f5e9ebf0f0eef2f3ede9ecf3f3ebeeeaebe3e7eff0e8eafaf0f6f2f0f7f50d03fefbfaf0effef9faf6f6fcf4f4fce8f301f3f0eef1ebdcf9f8f0f8fdf7fbfcfce5edefeceeebeef0effafef9f7fefafdf4ecf5eef2f8f7efeff5f7e9e8f2ebe2e8dbdee0fbfbf7fffff6f7f9fee1e4e5e8dfe4dcdbd6edede9eef1ebe5eae6f4f9fdf5eff1faeefaf8f0faf6f6f6f0f4ece9e9fef1e6efe7e3ddecf0fdecf4faebf1f9fdfdf7fdfafb000001fafef800f9f7fd00f404050801fbff00fbfde8f3eaeaf4f1f2ece3f5edf3f3ecf6f1e1e8e4e4f2e1e6eee4e2e5e7e6e5e6e2ebe4e5e7eeeaefece9f0e8dce80f000bebf1f9e7ead9020dee17230e1e3a34fb00eaedf2faf3fff6f402effa0bf60e10020c0e08f40c0502f9f22d191a2b2523323d20170c13061205070d03e8f0f1f3f5eceffcf6000df5f202f70205f711150d0d1a132f362bd5d5d3d6e6d4d3dce5121c11eef5ecfa0a12ee00eae200ffe5faecd30803eaf5f8e0f2ef140509120b2d0f0815f9f8fdf8faf9fc12fb1a11081a16072e302cf2edee08ff0e06ff10edf2e1e8fbee070cf2d5eee8d9eaf2eb02f8c5cac8cbe0dacbdcd2e0dae1e0e4eb04e7f0eae7effa01fafb1003f600fbed05f6e2ebe6f6f9c9f004deeffcf0e4f8d6f5070005e9ee0c100d121915112021f7fcf1fc07fbed0afbf8e3df02f6f9f0f1eefa01f50b080b111410eeeae6fb02f5fd09f0f3fdddf5ffebfa0f06f9f5f5f8fbfbf1fbfffefa02fff8f1fdf3f2000800f802fe00fafffdf3faeef7f4e8ececf8f6ebfc01f8fdf9f9f9f6f3fefbfbebf4ededeceef5f4eee8e9e9fb03f9f5f3fbf0f1f2ebfae20400f10204fff4f3f0f2f3f2f1e9e7f4e9f6f4eceeeeeaece7e5e1e9ede0e4e5d4f6f1f50d09ff0e0402f1e8eaeee7e9e8e8e6fdf5f706fcfaf8fbfafaf7f8fff8f7f4f7fc04040eff02fbf8f5fbf6fa03f5f702f3fa02e7eae3e5eeead9dfdcf1ede4efedeee4e7df0200f509f7fbfdf5f50004fefdfdfff0eef6eaefe3eaeeece8efe40101fcfa04faf101fdf702f4fefefa04fcfbedf0f4fbfffe04fcfaeff6f1fafdf7f9fa0304fceefceee9f3ebe8f1f2e6efe8e8f0eee5eff8eff3f4f2e8e7e5f4f1ebf2f8f3e6e3e2f5f8fbf2fb01e7e5e4f1020e110815021414f6faddcdf9e9b3cdc8162d22fc1c1d1d16101e121a140815290f18fff2f3fe050606091cbdbebcc7dad6c0c9c3030a1bf90218021d1bebed05e9f6faf0ff08a1adbdb7bec1dccfe1eae9fbd7fcf6edede64f38284b243244563cf70005fffe0af80eeed6d9dad7e1e0f4eae6f6090af1fe0200fa01a289c0b7a5d5d1d8d7512c36511b243e2839e4fb00f8f000ecedef503f204437383e2510cdc9e0d2cfd7ccd0ded1c9d9d5d3d7c4d6d436383a1a1a1d46413957503442382a42423f01081c08080901051027223c2f2f3a3f2b2d412d273f1e045d4518baeeadbdd2c6f0eeeafffa000d12f90f14091515170803fef50702211a102201002a1e12c8c8d7c3c8d6c7bec31810111309141c0f180c0afdf60421fbfd080f0b11110d1c1e14162b23162d271b3e44490d01f8fffa031c1cf8d8e8e90bf7f3191412f2fcf10303f70500f9fcfb0913000702fefa04fef6090501090113bec8d5deeceeeffdfddacfcf060ef6f5f4f31608030c0c09111019dcd8d0defcd9f40bed0302fa1008080a0e15dcdbe70c0dff0c03f2d5dad8dbdfe8f5e4ee12f9fe0b02fa060b13cfcfdff602e4f3ef06fdfefe110402100902f1e7cf0a0cf42a19f9cce3e0f911fa0a1510cddce9f70707ef1104aec2bfc5ece7e30603b6b9d0d9d6d9f512f6fbf3f60c07000b1712d3dfe4e8fbed0802f7d5f9edeafdf803f919efe9e5f7e8d4f0f7e5e4f1dcf7f6edfdfaf1f1fef8090d09080e1cf001011b1a05012220d8edfbf203f6fffeffb0b4c8e0e0e3e3f10bbcc6dfdbf9f200f2f503e5e8fdf2e3feebda01e5f5ededfaebe808e0d9e5fcf907fbf6fb05e5d7fee2d90cede52bf8eb0be5e5fedfe80af6fb15f5ee0af7f609f7f709fd0d07fb0904e1ea02efef16fae70bf7f00b0e13161c1efde8e6dbe4e9dfdbd50d24190b0d0a24181622140a150a0c100d1a2e2d2726372632291b01f0f6efea06f2fbf9f8f00402082416162afde3e4fce0f1faf0f1dee3efe7dfe5fbe1f912f30f0e02063504001afef813fbe714f9f02613193f060235111504f6ed17fe0412f70006f7f012f30215ff061bf6ec0bf6f100f6f2040bf706ee0f07fd19f8dbf2e8e0f703ebdf02fa0bff20370f0a1113f9031300fc01fef801eee70ef8080c040dfee0f606ecfa02f7140cf2e113edd70ce7ed0ff5fe10fde616fcfb15ec0020eff023fbfb182e29cef70209fd1de0dacbddf1eac6d1d110243780b7c4b4dbf6aef51b80b50c97b40e596a7bfd0e2b09063af6f6e9f5e6faf1e8eb1d332ecef908c4f8fee40818a8de1280cffa201520eedce6f4e4df09060d023d2bf42f1fe20511baff1a8ee21508fcf8050b0ce3050f2e45740dfb38e9df1aef314cbe022fb40131332a1921360dfa02edbde7f8bacbe0adbad1c0d3f8acd2f4b6e6041b3447cdd401b1e121e6172ac1f312aef416082248e3042ce60f2df24c65c71f57a31548de152ba5dd2696da1709052ed2eb0daeed01301029f7ff1df3ff1f32577b012f67e11152f13445cc032fd8020d08384dfb2a42f42c41f10a33b6d711a3d1f2f90af99ce7f885dbf1e30516bbf40ecaf70ff7081dc0e8fda8cd02101f4aef0745e30e47050f18f5f300fb0007fbfcf0fd02f5f2e8dbfe0f040805fafd0415eafa0be6000cfafd0bfc071000f90df8fe100b0805f80000f3f802ff0a12effb01eff909f1f70ce7edfce5f2fdfaf302050afbfa160af80700010aff02f0eef5fa1af40012ed0612ed0709fbf2f7f2f6e404080df9f8fd001013fd050ae6f605eff707010d060f1108fc0201fd0911fdf9fef7f9fee8f20ce1f3fbe2f2fbe0ebfbe1ea02ee01fbf90407fffdf7fb03f7f50801f5fff2f3f3f0f10923020516f00f11ebfef6e4eaf4e6f4fd020314f3000cf5f403f9060bfb0510ecfe0d0816270c1f180e2122faffebe9f9daf9feeff400f5fafcfaedeef0eefe02ecefece4f2fcedf2f4daeffed2f1ff07010b010b08f701f9e60708ecfdfde8fdfcfb090afc0c0bff0f0cf9011cf30f14e9d9eddef6f8f3f2ee19fefebdd0e2daf2f8e5ddd03735292c3b2f2b263fe9e7defcff1ddce1e5140d1c151d2e233236c5d8e0d2f3e0d3ced1fc0c0cf6150ee50e0bec04e50c1710090104fdfa03f9e408f0e404d6e0ede2eafbd0e4e6c8cebed2ccd1d0c5d7d9dad9f9eaf0f704fa16191d101b35162b25f5eaf1d0e6e3e30df9102804081c290d362408050e0b070e120e15bea1cbcfbcccc3b8cd080d12011707fd0e12fdfa0a040b010e08fdded6dde1e6dbe2d8dee6f4f2f0fb08e8ebe7f60bfe01060af5130ebae4e1cbb8dba8a4facec9d5dbeddbe4d0df121a13082727192715d6dbd3d1dfdde9e5e2dedfece703e8dee6d4b2c5cbcfd4dae0d8ca15262b1f2426232f2cf70801f90308e2f9f2f1f6f9f805eff505f103f7f2f5fdf1f3f5f7f9f7f5edeaf2e3f4f2faf7f4f8f8f4fafffbf702f5eef6f3eaf4f6f8f8f6f3f2f3f4faf4f7f2f2f5f1ececf1f3f2f6edf3f8fbf5f7f4fefaf5fbfdfa0006f9eeeded07f8f7fbf1f8eaf1dbe8eff1d8ece6f8ff02f70000fff9feeaeae0e4f5e2d1d7d0ecece3fff804fcfcf5f1f0ecf0ecf8f8efea0003fffffffbfb00010605fd0606fc0701fdf1f8f2f7f7ecf0f7f7eaf1e8f9fcf7f5fbfaf9fdf0f6f8f3fafbfcf5f7f4f6f6fcf2eff3f601f5f400fffafb00fcfffb0001fffcfdf9f4f5e3f2f2eae5ecebed00f3000001f5f606fefcf8fd01f5f905f7eef3eaf0f8f2f3f8f1e9e2e7eee7eaece7e7dce2ece5e7e6d3e3e2edfaf7f9fffaf8fafbf8faf70101fafb0501fffdfb02fd0606fe09fdf2ee01f1f5fff3eff60efe0305f7f8fefb050906f7020900010b000c0b04040104fe03110e09050c080d080a0506040a01fbfbfe05010c04030300ff03ff00090805080c05070c07080805050b03070dedf1eef3edf5fd0706010709f7030ff9ff03f5f7f7f7f7f9fcf7f6050f0ffc050ef80610f1f40008ff07fbfd0213120e080f080f1312fc040504fbfd050809f8fffffaf5f5f5f9fefe0700ff000cfa0307fffbf4fe0105fafdf30c061d01081808030eff081d04090d010605f7fb07f9f803feff0501fa02fcff0502fbfcfe0303fc0600f30d1600fef50002fa04fcfff5fcf00102fa090a01fbf5f6f8ece70206fe060d08050a06fcfcfbfb0307fd0805f6010df3f901fefb02feff04fa000bfffa06fbfa0703081407040e050204fc001404ff08090908f6f1f4f80903ebe9e51009f20004e3f7f7f0030a04070a070e1210211a1c211e221a1e180c04071c241501f5f2eee7e00601ebfe07080200f00506fc09fdf8f4fdf7f7fdfbed02f9f2f7f2041004fdf2e71711140f131917151b1d1e1f181e150a121ceaf1deeeefebeeeae4fc0bea0c0dfef7fe030002070709fb060707eef4eadbf2f2dcedf5292f291919251a252115120f0b15090b16100e0b0d1b18120b0500e3e4e1dde2e3dae4dbf0f3f8f603f9eaf9f2fa1202ff050ef50605fd10010f0706010cfbeaf3f4f2f8fcfafdfbf6f9fdfd0805faf004f9f2d30801e3fff5e7f1e7edfdeaf9ffecf30c0c061006001c0e0efafdfbfcfcf0fb00f8ecf3e3f801e8fdfff0ecf5e9efece5eeefeafdf9f3fcf9f5f6fbf6f0f3ecf4fce8e9f9f3f5eee7f0f2e0f8d9df26252e222b452937500a0623040912eeecfeecf403f2eef9e7f4f91301ee15fae5ff04fb17ff1604fd120d101a0e0ef70d08fe09fa0a0c02fdf6f2edf8f4f2140bff3627142f2111e3f3e3ebf500f4110619080a0e07040502fe0cfff2040608fb061c1b140528160e320c0bded9c1d8cfc4cfdbd02d0c16110217ff0519ff040b15f807fe000ce7e1e3e4dbe2d9dbe802fff60805fa17ff01fa02f5f6efe8edf3df141c10050a00070507171a1e0b09150613160b15120b140df90809e0dcdbdee5e8d8dcf20d06d6120ce01207f7271f003a1b03250b03ede5f12a1d0e233108f2eef1f5e9e9f5e9f6131417111b0e040c1b33291327291e1f1a1bfce8dadfefdadce7d50d07f903fdeaf4edf00f120a060107fe03f416070323280e343dfe0405e1ff01e60ce6cc29100b40361d1f0202222a0d3e260a3f3d12f502f7122b0a3b2f0b0deee30e0bfc0a0705040df42209eb300ee5e807e91e1f02111dffe4e4dcf3f1e0f4dcdb220ff80c16f5241df61227083426253a31203118f91a03f11811ece7f3f102170ef6120e262b0346451340431b0703e80b0ee91bf5e2211d0c2b1c04371617291ced250df32b0df4fdf4f3f4f8f2fcf0e4f2f7ef01f9f4070febf719fa120800140c04ee100713181311210d2026113f290f2c280a0b03e42008f1432101fbfaf4fef8f70305f7e7f1e7240af21e12e5f0eedcdce8e4ffda020e0df72117fd18190d071f0a2e19fb3709f8ff0806292c0a2018fbfd0ef80b03f12020fcff08fc12190d121d04e9f9e6fdf9ee060df1ff0700e0edf9e9efebfd110c02070800070eeef105f4f9f2f4fdfefa0203040108f506fff90805e9f3fce6e9f0e9f8dddff0e0dde5e7f60102ecf7fcedf3f4160c1c10080f12ff0b0512f4ef1110e8f806eef1f7f8f6fafafbfaf3f9fefc0205f9fd0bdfece5ecf0e8eae8f1021d16f60b1af7f20fece9fdf3ebf9ebeefc1a1a21060722030717020404010a0f0b030bedebe6e8f1f3eceff41f472f0d191d183230111a2200070dfc05130a111605fe05f3f5f41e1e201b1e2a101b21fcff01f10000fb000002120c020d11ff0d11e2fee7e3ecf1dedcdb151c310730260f2827213228141c2a0c0115dfdfdde4e5d6dee6e3091816fb040df3ff0a14161501030d01fcfa080d1afb0b0cf8fe080c1f2200101b05070c1b1d21211b1105141213211a0c1421e3fa06cdcac2a5aa9cdccfbce7dee8d0e1e8c6d8dbfdf709e8ecfaeee9f3f8e6f0150606fa02eb201130230242550f2f150d04f7130eefe2de071516032121041a11f7ffe0f502e4ddeee3091f07ddecede2dde6d2d3e3e5e7e4f9e2f4dce0d0eadcdfd0cccc05f7f703120a23fb21313f44283f4b29443dffef03e2ed0bdacce8ed090103f0e8040302301d3b22302d14231dcdd5dccec3dbedeafafef5fffaf803f6f2fde2f2e4faf300d8dcf2a2b4cabfc7d1ccbae2cccde1fbeaf7ebddf1050c0d0f161e0d130dc8eb07e0fafec5ecfacbd5ffd2de03d9e500e607e6ddefeef4daed1f1d1a1b1b2a041827e4fdd4edf4f6f0e3efebd3fee9ecfce0ef01332a2b2b2c292d2c27dfd5e2e7def2e5d1e3dde4e7d2eaf0cfe204fbf2fbf7fef6f5fcfffbf4fbfcfaf7e6e6e7faf7fafdf7fefef9faf2f4f3f9edf6f1e7e704fef903fefdfffffdf6f6fef3fff8f1f2f3efece5eaf1f0f1eae5edeee4f7edf3eceae3fafaf1e9f9f6f8f4f0f4fdf5f9fbfdebe7e7fdfaf6fcfcfcfdfcf5edede9f2e7ebe5e6e4fbfbf0f6fdf6fbf5f2edebe6edf0e1ebf0e8faf7fffbf8f8f9faf0f600fbfdfff800faf4e8e3dce4e3e3d9d7d00200fefbf9fdf6fc02eaecddf5e3ede7e5dcfdf1f0f9f3ecf4f2e903fdfcfafbfbf8fcfcf7f3fbf9fdf7fcfaf2f2eeeaebe7e4eae6e1f9f1eff1f7f2fcecf5f9fef702fe00f8f8f8f9fcf201f8f5fdfffef2fbf1f6faf6f8f3f7f1e9e8f7f2f4f5e6e6f9f9f8fcfaf9f7f8eff0e7e8f3edebebe3e5f3ece5f9f0ecf4ececf6f1e4fce9e6f4e5ebf8e8d7cce3e9ccdaddd7e6edeadfe5ebe6dee3f3e4e7e4d3bce1d40d130a1c15150b101ae7edd9eeebdfd6cbc8f4e7e9eff4e40206e8c9d5d8c7ddddb7c6dffb090d110608060001e3edf0fd05f4fcfcfffceff9f0f1dededee7ea03f40b1311140e21eee6cee7f2dcd6e4ece6ebfaeff41500fb07f0e3edffe8f7efe2f205fffde0fb16020b0904000d161b02092019fbf906ee0100eff503dcf0dfdee2e6cdd1e3100f14130f0e080710fefc160d070203f506f80d0e202320332d28f0e9eafefaff0a0304090d0d0d1d15f6f911e0ccb4e7cbd5f3f3e403f808010b0b062213fe0cee1a0cf9fe1903bdbec7c3c0dfc8becfe3f0f3e1dee6d7d2e70bfa000f0a1b1a10150d0c1b1306161c0f1800f1090b0303ff05070f1710080d1907142107fef10af0e00ff3effcfcf6f6fdf3e7e5def2d9e1e6e1ecf8fff4fff9edf7f0f5e9f1ef14ffff06ede417f2e605fbf803fff9f5f8f407fbe4efeddd04e8db0a06ef0cf9f7ff01f408f6ef05ffe41900f5fbfafafd01fdeff4ebfefd01f7f5edf3f0eaf7e7ebede8eaf5e4e80d07f80504fd18fcfc09f4f3ffeeec01ebe606fc0fe9e5f9eff1fb0906ec04fbfb01fdf2ffebf0f8ebe8f6f2def0faf5e600f6f7f4e41011fc1208f8fbf7f20e1402070500f9f9f7130bf90e05f3fdf5ee0405fdf3fd00e9f6ef0c01f006fff9faefec1105ed0a09f42515f31004ea0cf9dffff5edf0fff6f10ff9fbf1eef1e2f2e6e4f3e9f6ec0d06eaf8f7e7f5ecd70701eff0ede6f8efea150efc0406fcfaf3f30009f50b08fcfe01f51419fc0912ff06f8f70105fcfe0601fbfafdf9f8f5fcfafbf2fb030a03feff00fa05080afe03f9fb03fcfd00fb07030103ff04fdfdfaf5f9fdfcfaf701fffafffdfffffd00fe0002000200010803ff0708eaf3f2f4fbf6f2f0f0fc000400fcfb0001fdfd00f8fa02faf7f9fefefdfaf8f6fbf5f4fbe6ebe9eff3fbeef4effb03fef901fff9f3f7010804030d08ffff070408050007030202010605fb07050005090300fffcfcfcfcfc0200fdfefe0003fe020601f2faf9f9f5f7f5f5f502fefb0101fbfb03fe0400ff030703050703fbfff3f9fcf5f0f5fb010a07080606070a08f8fdfcf90002fbfef8fbf4f5fdfafafdf8f9fafdfff8f6fefcfbf7fefeff02fefcf6f7fcfaff00ff01fef806ff0602ff040701090905fbf901fcfbfb0001fcf9fdf70600000700fef2fe19f4f904faf8fbfe00fcfef2f5f3eee5fdfd09000107faf9fae8e5eef7eaf0eedfde02ff01fe02fffbf9fcf4f7f5f6faf5f8f2efeff706e8f2fdebeee6ebe4e8efe9eceaebddebf40ce8f302f5f1eff7ebfff9f705f3f4f4fcfbf3fbf0f2fbf9f8e3eef3f2e501e3e5d6f60207f3fdfef9f9f1edebe7eaece5ebeedff1f2f5f3f4f5f5f3edfdf8f9f7f1f1fef2edebebf8eee7f6efe5dbf20713fa010ffdf90af3eeefebe2ebe0d9ddf6f2eeefefebeee1e7f8f3f4fcf3eef7f3f6fdf0edfcf5f7fff6f0e9ef19f1edf8e6e5d9edf311f1ff02fafdf503000701fd05fafaf1ed0006fc0200fefcfbfcfaf1f8f7f8f9f8f8eee9e4efe8f0e5e8e1edebeaf0ecf5ebebe4f1edf4f3e9efece2d8eaf0ededede7eae5e1f8f7f4f6edf7efe4e1170b10231215100f0a1f181c1b11120f18181e0b0f150109f409071215080d06031a0b00f5fdf7fbfcf7f2eef2fdf0f4fc06feff080ef9fd00fa0108fa05fef802f7fc04f8fc03f8e8eaff09fb1002f906070cf9080a08010f0deaf3eef1efeaecebed0600ff0400f6020109e8fceef30c0ce90607f9faebf3ececf4f4e4060c080f0e0fed0408f703fefdfbf8fc0efefcf8f9fafff9fd0500fd05f704f9f7061008051b0803090d161f0ad6e8dff1e2e2e8f6f1dde4e0f1ece7f8f3f1e2d9e1e3e2e7e6ebe9fa0103fefef8fbfcf9cad4d1e1d3dee4e0c9fcf7f0f5f5e6f1f0f20eebeaf60207fa12fbebefe4e8ecebf4e9f1f6f5eb06f6f501f7ffe7f3ebff0305f7f900fe1301f8fe03071b11e6edeff4f7e7f801f8ccebe5fcf4f200fc0c11f5ea101d0f0d1bfdf5e5edf3f308f4fefb171a1a12070a040c17f0f7f2ecf8f6fbeffcf0eadc030b0c0efc03f2f500eceff6f2f0f2f3ebe600e1ebfffd0c03efee0702f70e0e09bac8a0c1e9ced5fad5edf4eae8f2f3ed00eafb14050916121f361c1a0e071a1915130616e6ece204fff602f8f3f3ddeef7eff3ff04f3fae311efe6ef1e1e1f010feefe01f502e6dffafff8fbeee90902f6eaf5dae9e9dceefffd0110fc0a0a100e1919ebe6e9eef0f0fff8f30914fa160efe1a1d12f714f8060b090f0d0fede2e0f5e7edfef9f4d6dfd9f202e4ff0ff804e8e712f4ff31191514f8e5350b0f2c2b18c4cbcbcdcececedacfeffde903e1e3fcf9000401f90dfc01180bff04fbeafffde50e16fbf1eae2ff07fb0c1203030ef00e0a03181416848094efe6db0ac1d2a88b8080808080808015f1cc121116192e0a7f7f7f7f7f7c7f713b8f80801cdee9e3c2e99ee8d3a703df80b796becd90f9c19ce8bdc37f7f527f7f587f7b37809580c5bea0efafa5e4ecfda5c2f7a2b6ba7f7f7f7f7f7f7f7f7f808080809680808080a880ae1417e07f4717c503b1f8e9d1e3f1c5ccb6cea2a280dfa1cc7f7f557f6d475e6c1ff3eed5e500d0e6dbc8fd1209252331613f141205c411f0d002e5bc6314266222252314c47f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7013f4c708e6cfefe3c3090ed87435046f4ae87449cd7f25f67f2a12808080d8b7aa26e6cba2a28fd4abc193958b311504400ddbefd8ba64383f7f5a605a4e63f3cfaad2cbac1fe7b27f79297f7f3d7f7f297f6a0d7f530264621acedac7ddf007f3fd2013393b2e2f4a3f2c24cdf11200f317dc0a158097b9bce10700161bdeebfee52f0bfc1a24c2e500141624f9060ad3d6fbe5eb0de9fc20a6beedd3f10c05111ef90701111438152f2acae1f4fffe111f110eb6d00de0ea13e5080ee0e6f00204fd0d1417ece5fdff3f20f3363f85bfe7bdcef2d00b14272a3527133c041f2780bedaadcfe6dcffed9cbab8d8e9e2f60506e7f0ed050e1a232611b3ccf3ecfa13081c21e0fb080c1e3b24263fbedffad60cf5def10d91afd8d2ec04f3fc15d2d1e0eae4000e0e22c4cfe4c4e7ffdef227deeef6fd0204fa0f183f200e42050b2b3215c7f80f041a222c251aeafc0910131a222124e5edf6fc04e51b00f0b3e7fde6020c0a2523cdcaede3f5fff3050bcce710e017190a2946c3cccacbd2d9dcd2d309081c28382e1d303debecdeff13feed020f1d250e090af61104f8b4c5c2dbd0dadfd6cee3edfae9f1e9d7f6fdfa0af8152211fd14fc2d25193d2e203b282bcdbdcbd5dfd6f4fcf8dbeae0d4ebdbc4e0e8293d0f262035353011e6ebfbe9e7fdd0e4f2acccd2e7f5ee0afffccce3ced2c9d0c2d8d81aefe6fe00f1f50e0910240b0b02ea0af901f0f1f1f9fbedf5f1efede4e60dec14071b22080a0c2b300d563f30fa03f4291215273029626c43697f5d747c6625452449331b3f3c34f5edf70509f3f3fefcd5e5d400f5091b0ede130acd1600e73425f2f1f70ef4fe2203051dbebccdcfcfc9ccc3c511fe191717271f1f170a03f7181c1c1e0b180112ef0909f41f150c0004022412152b381d04f6f41c0e0733231c1f151c07040b37223b351d421d141004eaee3a444b395259384966aeb8d3c9cbdcd7e4e7081b1ef9fe1d0405251a0bfb1801f616030505040bf8030a08150fcad2dcc6d4d6e1d9f1fb1310e6f101051411e1e8effdf3f5dcfcfcebeffbd3f601f2070f1b122b3327273f332c080cf7faf909ee0b19e7ee06ebf1ff180d1a2c2b11132907132c31909bf0bfc9fbd0c6f5c6ddd2d0d9dec8dbdc39253d2a1724323142dde6fadedbeedae70bf41325182132141d33f20112e2e91e00171aeee426e7f21ff8fb23d5d9fce3dcfbf4e602140c130f0712191f25e60b18e4fc03e5fd151d1615e30c15edf81b423b36503f31504c39201b2c3f223a3141491f28422a3031262724bbccd8b1c7d7b7d3e4f8f903f4e60af8111bf1f10ce3f205e80a16),
    .CHANNEL_BETAS(1024'h770d770b7810758b72e07834752f77a777f276f878c4779877e7734c76ab771d794b78a97997789e793a765f7934736e76c6772075e076d077f877ac7563741b7535779077826d737912789877ac79697591777d779875d277db759977e0789176b1779178467803763f78b3766f79a0784b784d781476d96e3d774e76657655),
    .CHANNEL_THRESHOLDS(1024'h020902510230021c01f2023c020001f701f201fa01fd01f902280219021d020001e601f5023801e701d1020c020d020301ef020b01f00259023b020301f30205020201cb01e9021e022e022801e80205023101e501e10258022001eb02020222022001fb020801ef0204023601f501fa01fc021b01ec01dc022901d901e701f0),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d6),
    .ADAPTATION_DURATION(16'h1340)
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
    .KERNEL_WEIGHTS(4608'hee10f200fb021610233a1a28321d1e2c180f0ffc2cd8112c10253b21231f08f11dfa13f416ebf417f70005e9030ee9eefef51623f81842120c19ff212cff112c0cfcea0616042a1a0de2f003d60bf2e01bf6ff050ee906f10607f2fef2f701f415f3fefe14fcfa1142152a471bfe0a1efcd4f8f3e220182f28f222120a15000d18f0fb0800e90510fcdc0e24c245fdf83222231b0e2b2522ff491b3f08f2321b213a0b0ff80c000cec12f72328300fd41d353940fd2017182229d5f80f25041c06e8f42af9111210fb03141114ed0347032314cd132f233252260720cec90bf1c40d1f22ee20e9e2eada63161e22e91e3615340ff816f8fc0711221909fb10f3ff0c0c090f32245b39090a280c1e0ee00d46ef23311c50f70020fcf4190e00251f0a1a06dbfb1ef422ab00cd1d2c0beb0508eef4030c1c1404ff081ff92decb61333041214edf502fa0cf70e10ebfdfcf90102e8120d361f2ae9f7071c0d1cf8ec0df8f408131bf0f7e3effd01e70eeef8250d35e5ee030bdf091e2d390bf22bcc11234afc353fd6337f50610f04ed2201e50e1511fde9ddf605f70f081b0fea06f805100d0b0c261003f8dcfe01c7092d3ffe0f07fff7f4f3170616f5f012fa00230f0630fbeb1a371a06ecee05fae9ebff0512e0f7040f46eaac1de6f1021708020b0decfa2d1509f7eefb1efc23211b1f0d1f28385333f6e3f90cf6fef6f710333c541f115a0c252b17210e10f21914172714f9ecf3f4f4defa0737012a1fec0d451a1a17ebfe36f53c67154c120ded210600ff0af61305fc08d6f2df0421),
    .CHANNEL_BETAS(1024'h77e2788c78b876ff785f781277f378427800777d77c27849784179cc774278637920796d77fd7912787979c47801793e77fa78e979b9784477d279a27906781a78b3797e78277980780177f3789d781978a9783d78427aa677d47767780077ca785a77e7788277b679917801782f78a6775f78be78be77f9787a79747708788a),
    .CHANNEL_THRESHOLDS(1024'h01d301f601f5020101b801f30212020001de021a020301d801ee026901e8020601d2020901fe0204020301f102070202021001ea021d020801d2022201f201ee020001da0203022901fa021501ef0211020001f701d5023e01f7020601de01fb020d01e001f1022601d1020101ec01d401f301ff020001ef0241020601e50219),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c6),
    .ADAPTATION_DURATION(16'h13f6)
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
    .KERNEL_WEIGHTS(32768'h08eaf414eaf6050bf215011af006130dd7e2fde1e822ff5ef323e3effb17e2f0c5dad8a604fb10fefffbe6cfea1504c70408ee04e70dfb0f09fd1b09fef50ef8d9ff0401ecfae3ebf41103f40af4fa0703dbfc00f0e107e00908e81906f7e5f80a13f2f3fefbf3fce0f0f51f10e7fde20402f10b1dfbdefff7cde4f1dfeaf1daccf9faca0403c3f8f70100e800d4eafeecdbf3f0ebdcf5ede8ded3ecf3cdcddfefe0e2e4f206dc0304f4efe8ebf4e7e8ffefcfeef206e2eff4f3eff8d7bddad508e2fafd010e030105f0fdf90708ec00f8f804eefecbfa1a0bd5e0fc02f8ef0c09fff21000fbf701d8eaf1e9f0f809f722e7f7fb08faf4e00cf9f9fa0bd4e2f20ff9f6f2f8f8db19f8f20107fc0afae3f0e002e204eb040c05fed9e100fdf2e1f0f309fd02fc09f6fde8d9d6e9fafaec16edf5fcf6fb00eef6fe0c01200705eeedf9f7e101f8bef604fb02eaf8e5ebf2ecfa04d1edbcfad9f1dbcde401e5e5f6fafdebf4f904d102e5efe5e1e605f7fbfcffd3eaf603f1daf207e5fee2b5e8fbee10fde4e0fa2114ea08132306ea020ffddeff10081600fb141018da00e8fdf40bf8cde7ffff0cff32fb190be30801f7f1f2fe1aeffd000e07d80b0eeb370500e80803f9fd11fee5f805fffa0403ec19e801fc0105e900f6f00504f002fbdae3ddf6dee20803030b16e4f4101df4fb1cfc1506eeedfae4030af6fd0201ecf5001b01c91f11f5f2ea1a010404fdf4fafcf6da06dc0d2cf920f3d8e6e203fcf8e5efe60edb060128efecfcf2b0d9fb081708fc17f9fd07edf1030405f6f7be1d00000ff4f3f9040d10f20ffe160bfcf6f8df0a01010b01fcf00807fa0cf3fa0904f8fdebeb010203fa06ebfe07f5f8fe12fdfbf8fcee07ff090ed004f8f91cfa0d061a12e508030603f900f6f4eff7fb2c3102faf309f7faecd8ecea0ef7f300f4fdfd0bf303f9ee2231f7170e2406fcf7fbfffbfb06f601f7f22a0f09f509e50ffce70300eefd12e0fcf20f03fdf8df0f28d30ac906060511ffefe5fdfaeff3e902c91d80020228fb230afbf211fdeaecc70c06f9f8fe04f1fdfd28e5c405160e19f5d81d1002f5fd0aeef5f50c10cafbf50d05b3d4bbfd2011adf408040eec26302ad648fd04f200de00f3e1f02300ea40e4fff413f50ac6fbe5d9f304800cffedf0f9edfafeea05fcf104090af8faf8faf2faec07daf71010f2e601fff5faf7f7fcfb030708ff07ecff07f7f20d090107ee00f5fe0105f200fe00f407fcf8deef05fbdef6ff03eafbf1f600fcf8f2f5f60102f6f0e303eaf4eafdfafaee03faf108e7f8050adef6f9f200fbfae702fffb03e8fbf102f1f40dfaf000f7fef2f2eefc11f9ebfee5fa04fefc08f8f8f8f8efeafce900f7f8f6ede9eef806fafa01edfaf9fefafbee03fffbfc00ea1204fe020bf3fbfffbfee3f706f7e7fce4f30600d7f4caeaf8e3e8f7f007f7fef5d60a0dd30ae7080501eff2e7e111fbc70be5e5fef6cbf6010817ec07e80a0df4eeefca05d7f6e6fadceb05fb0f0bc8f3e312f6f91bdc05fe0a02fafa0de8f3e714fd0914fd1d25be05e9fffdeef8fbda08fee70cf90408fbf70a11f100e4ebeffc1ae309fbd2f003e830f915f60713c2faebefdef8ebf503c6ea03f4f602fbf8e2fff9e604e3f4d0030607e9dbfb05f7f303f1faf2fc01fbf509edfef5f50dfe00fbf5f7e5fffb07ffec05ff02e8efdfefedff25fbed05f60b040615fcef02e1dd1b1a0d0000fdfb01e3f6e1fe1304e319fff91a0eedfefd08111b0015f32701f7e3f41eeefeeb05ecfe0609050fd819f8f72df9081706f3eb140a0311fef8ecf10521f008021cfaf54adef3d8dbf9e9c5ecfbd022e2f8f90013160ff89f1df8fb01f0eaf8ffe8020a150aec0f2001fe16f2f60bfbfff9fe02f807030bfffd07f303f7f0fbf6f511fe11ec0c0807fe06e1f0f0e705d50103100502fde3dbf20f00d7070d00fbda03eef50001f9dffcf50603d0f2f9de02fac5e1faf4fbeffad2e9fff5d3fde1f4fc01f7ffe2df0801dffcdfeefde2d60600f1f4f6effacaedeffee8edf0cbf5ebffd6eef504edebd2cedffff9edf000f708e20ffafd02120608fdf0fae4fcf00dfe05220e0ef3e10301ec06f3f4fff106011cfc0de6fbe600ee04ec00fafb03edfff203fefa0ef20af201f2f3fb09e5ff01cdfefbe902f303ffeff6f6f1fde1f5d006defdf2e4fb05f4eee403fef908f904ecf2eff105efe3f608fe05e4de01f6fdf5ee0103f0f7e9faf4f9ffe4e6ff0bf7020809fcf70c05f1fdf4f6f7feecf8e4fe1cfce2fcedfff7e7f4f900f60401000cf3defbecedf4160bfe02f7fbfff9fff9f2fb00f1f50ff7f3faee03f506ec03fcfbf0f5fcebeef7f707f70c04111407fbdaf91213edffe913f90810edfe01fc070efe120b1c14f1f700e4f8f4fd2406e517fbe6f6f9ed1eff0be60c06f60f10f8f4020201f30005ede5ec1d012cf2de04ec1aed1a1f03fbf905222e04120108f7ffff0c0612effdf6fc00fbe7f9220007f90701fdf308eff315fbe507f3fffcc82af904f6e4f003e3fef0d5f8f707bffcf700fceaeef80106000203fe05020202e3e7e2fad6050c03ecebe80a08fbfa18fbfa04f8ec13d4f6e5f7eaeef1f6f5ea08fff506030cfcf401f6fafcf2f4f2f80f0feef101fefff4f4f9fbf106fcfeebf9f5f902f4f508fe0309fdfe03f8f9fbee09faf2f503f805f8fdf9fdcbed09f607030a10fcfff8db0307c905e5fd0204060ae4fa05f7ed15fcfe171300010321fef00d0df0fbeefb18f81fecf11507fbf005fc250aeb10fbf1ede90ef5fef1d1fa02f4f6f613f1f1fcf9f106eaf7e4fae6fff4db090000faeefd03e3fb03fbeff8f50001f2faf3fe1404f0e90ef708eef7f3f4f6fefaf3fbf3f4ea04e6ee02ff19f7f6fb0afbfdeef0dee506bc09f207cae1d70725fad8fd080d06fb0e080bfffcef130cfbf114eb17de09d20a070809e6fff5f22ce6f70137fae91101f0fe00fbfc060706fb0ef9fee7f300ea0bfa00ef120818eef9fcfaf7f3fdf6f1050009f6e108eaeef90ef9e117ecf707ea05fdf1faf7f9dc01fdf705ddf9d40002faeaea090cfe37f52213dbc406f5d6f117fa143008eceefc13ecfff8ced9f606fdf5f203ecd1c7e31bf91b00e031f8d5070efa11e001f704fe02d7eed6e9d40f01d6f8f4f30ae9fdf0d4f6e6d705c701b304dbf1dbdcfdfce1f1edf6faf5fffd03d7f2ede402dbdb0afd0502e9d604f3fff7df0306ec0200bcdbeaffe9d90f06f4cdf1fcfbf7f8fb01e803fcf102befab2fdf40fe1e8f3f1fef1f50e16fa16fbf2feedd6f9dfc50003fb07fddd0709fd0407f0fc0407cbfeb308dee70618fbfd02f809ea0ffef4efef06180921011c0bef05fdea02f10ffff2f004fffc00fdff04f2070602070a19f9ffedfcfeef0df8fff90cf606f4f902eafbf0faf9e90907fffffa0af8f7fefdf90105efd30508e207080ffa230edbf403f3e5ddd304e0f8fd09feffe4f5f9e913fd190fd90beadc08eada06e0e2ecf9efffd9dde3fec7f704ebe5f8f6fcf5fee7d4f5eadbfbe311e900eaf1dcdd02f2e5e9f705e9ddda01fdf202f9f7f5da04f500f4fc03d2e5effae7ef0306f6e9cec9b9e6e5e306f00df5d6f4f5f3fa000ff4e5fff0050aec01cef9f512e7f4ff09eee602f206e9ff0905f4f3de0509f4070efc0e17fcf6fb08fefdf0fcfbf4ebe6eff3f0fdc321f9b4fcdd21ecfa1f39dbe7f3142b9e0ee500cd0c17ef3f08edfd0b14edbad2e480f2ef3204171a14eac3f0e4b2f51517f8f706e90c14d80c0cbd2d1ef6f5e3f8e1fb05eff413fdfb0905e5eff303e602fcf0ff070ceb01e70efcd608faffdf02e7f904090fbbfb0210f71dfa1400fbe3eee7fbe1f4fe12ec0af4090436f1f2e9d2f704d7e4020306eb02bffffcead9f9fdf8fdf7f2dcd6def3f5bec1e6ded1dcc9f9f8eef0f9ebe7e3f7dd01d7fdefc2e6f6f9c4ec0bf8d31fc1dad2b6ef0cf2010803fafdec100e0e0efb102527dcf7e5f1fdfaf9fa14f2fe00f8071cfaf7fcebfd08110109e6fe363002f5f6f9e6f1fd17f8ffee0517f9e3ddebe2050109d30813ff011107defef6f902f3f8e0c9fae210e60826fafcc8e6f3f9d70c04e7fdea07fa16060ee4dfa50403f8e4d7dd0e0cf00410f01101f2f414cc04ef0bd9d5e40c0302e902eafbf6080dea09e9c106db07d9f8de340fe10cf900f0010d3de32afaf9eefefbf7dbd2bc0ceeec0bf2f3f11f0814f20cfd06e00fbbf6f7e8fffae70a07b6fe04f4000821f8eefce5cd010ae6ef02f703f9120af7f5ed00081bda17f9f305fefdecf305ffddfafcf1fcf204d600e1f70aa6d3faeb29decff303f1090e01fbedfdf002050c011000e9f1fe01f0f8061c0806faf6f9f3cce1fc0011fafbfa1afbe4fff700e219fa0623e50607f90408f8fdf1f70403fd02eb02f814ea2008f713ed0300041bebf9fa0711030f1ccbff021107fc0affd9fae1ece9010b04fdedf80ee30cdee7f3fa26fbe0ebfd03f8f73402ebfde4fadf0218fffff501f3ff07fbf9f7fff2f10afdefe2f404e70715fe00f8f400fdf2fdf4fcdffc0004fffc0603d602f2e0ea0702e12af2fa01f604fef209ffe8f3f0f6fe06f7f8f10509faf7f9f209050dfef4fe0ff300fc1bfcff04030613f501fbe109fef5fe0a0104fe020301070005ddfd0011fc00f80afb04f6f3f9d3fd0cf312f217de00fa0000fe10fe07eaf715040815eae7e3fbf4010d040bfb10d6e3f8f4c5fceeed02cef8ff11eefaeaefe3f900fef80bdefc05f0f907fa06f5eee6ffd30bf5e3f7edcd03e8b80404f802e7ffd3f302e4fd09e2edb30a04decdc8fd00c0eddeedcfeae4f8f9ecf4e9d3fdddd9e5e9e2fb02b7e6f4fecfef09f4d91fddc8ebde1ffaf7000702cdf927fdf8ed02f6f80a00e2070607effaff0df9d3f1f0fbeaf107fceefdffff03fdf2f4dc07f2f50401e3040a2700fe160904d3fe090f1303f5fcf420f407f9f90e01fdfafdeefa19eb090dff152de3f71604fff0f006ebfd03f1edf9f8fa01000c11f515d1e4f300000c01e3fee7fbf91e0909ff0cfcf60c14fcf3f819f5fa04090deef9ffed11f3f5e6d004d5130606f8f8fef4f103011206eef40b03fbfbf9ffeffad3c5ecfefe10f9f3fafa1100f5ff05fa01030be91007c90301dce10000f2fefef4e3f9eb09fe0609040ff8e708e700fdf61e02e90b0ae8ec09f60406e90505f8e31015f905f90cf9e2191309db07f721f1e400dde3fcfbf802e9f8fdf407f00e0bfbefecfae601e5ffe40e02fafeed1a000603f014dc08f7f5d7fc041004ff2109e10313f3f1f717050cf306fb04fbf61ef89f200ffa16ed0dc1fb00e60f0fea010cfddce01409f1fae10208f8e9e2fe0ef0f8e50ef9ed061ae704ff05f41c020af7f823f211e411ca070dfffceff6fc2232e71ffd38fbe3ce0b0bf8e004fef0f7d00912e7ede4d605d014d500edff9dba1decfbdcf33a04da3305fbd1e5c6ced680df0c0cf5ecf1e8f024060bedf203f9ec14a3f2ec00f20dfa0e04fd1df6f110ec12c2f7090101fd1af8e3040100fce7eaf7e10b02fa0132e8fe05f70ce8e816ff0be805e1eb100107eef90b28f8e5061de9220916f9f1f60c0812ef0e0ff10af2100b00dcf80304e401cc060a20e10608fdfe14070206120df90c14f3dc050ec9d40f0d010df808f6fb03fef706f2fd131ffe0720e7f0eee40203ef02f7fcfff2fdeae8fef3e6fef611ee00edf9e4fbfdfef7ed0afdfef90507fbfffedb02f1f8f8fbfaf812f3f8f406fef1edfefae802eff9fa00),
    .CHANNEL_BETAS(1024'h777e7822793e779a7717785776be78f7779c778279277848775977957880785379f978a47990781a78df77ca7901787f786c76af784c777b785b779e784e782d7886770e78cc778777d877ac780779e37763770e78ae7900781777dd7745776a781979f377aa77d577fa7959786479e677e378dd783379bf76e476cf78d27900),
    .CHANNEL_THRESHOLDS(1024'h01f40249022f020901f202390207020801f80219020501f801f40227024202260202020f02430212020101f8022901ea020e020c021302180210021802110225020b01f701e0022f0204022601d00236025b01d402180238021301ee01f50202021001e6020b0218020302310202020c01ec023501f301e30202021c01eb022e),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d9),
    .ADAPTATION_DURATION(16'h13de)
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
    .KERNEL_WEIGHTS(4608'h223e1cfff0081cfa12352a582d21f53a07301a0855e2f620271644060b0203f0d3140bf1230b12eabc071c01fe0a0702fa07f7effb042313fff7f3ecf1f3eaedf0cf1aedd41ff5ed16020b17e52324350a1c103805f82c120a2022073311d91d24e0f3d612de093dfa03f6f124140a14cf0c06140001fb0213ebf81dfe0123e3051ad6f2341dfd1f10cb14f4f11309e627062b0f032ace1226fb0a2ff1eb0c20063a14f9fd0ef3020401f10fce2316f4e712deea0906130df3f74c20160112f6f1361fe1fdfefb0c121012f2ec0ff220122918d90d31fe23f5dcf2fdf7031a0604fe0adaf221e0fc0af745123f0ab80a12061c2d1b2a18d4ff15eb191c04fa0f14fb06f4031100240c2dfdf2f8042e4c2610df11f1ef0c010201020709f6faf315e7f407db0c1200221bfa2003d707210318e6232af319fac9e00114072208c90b19092a10f90cf2f5fe04f2faeacbeaf5ea032e1b33d3f6f7e90112eb0f1301f00d16fbfdfafd150506ef0a1bf5ec17e03deb1f23d30049fc0f4d281309e01726553143256112cb19710d330ee6f20301f663360ae3efe51624fbfc0a0cf00be6df0601e9fd05012129281b12666d1aeaf1f90414eb0ae7f617032106d30c1be62f28182f15f1f111302608003cfe0b03fa01f1d2e4db2b3819ee19def1f8061c0010fef2f1e5fb0adaea0ee0ece92a2745080e30173a36fef3f03020071f1a0d302e1e27e91802280ae0f1effc211819202407fc0bf6090a100f16400e2716e4090df11310f71220052d4ded4cf9f90c09e3fb13f00b2df80c11d711200722),
    .CHANNEL_BETAS(1024'h798c798878ec77c477f777f1784b786c788f78c278c47882788377037859780879407840780977e078c4796a780378e7784b77af7a1979a377c878497878778478517958776579d2775a794d789877f07874793d78a479cb78ab78c5787278c277e9783c78ec78cc785577ec7829791b78387876786077e17a0d78c1770978c6),
    .CHANNEL_THRESHOLDS(1024'h020301ff020201fd020e01f5021e01ee01ec01eb020b01f10205021b020101f801d801fe01f20201023501f101f9020a020c01f302140217020202200207021001e1021801fa023201f701d201dc01e201ee020101e9023f021801f601dc01e4021001f101ff020c01d401ed021401e401f201bc01f3020c020f020902200226),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c8),
    .ADAPTATION_DURATION(16'h13dc)
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
    .KERNEL_WEIGHTS(32768'h28ffdb10fb01e8170017e609f705ee01e3ea01dff7f7f814f919f3cf0203d50bf51012bdf3d8f00f1723e614e2ea04f7e6effc19f30a11d7ddf8020bf00ef2f1ce120311eef8fa03d402020e15f109000efb03e7e119fef913e21c14130a0001eadf2610ff08eef3f40005722f13fbf808f8fd0a14f3f5e412f5f50df9fa0231fe1b2505ed09f9e8070514fcece9012b1e1d000ff915040ce21b0925fcfaf0fa12e6f210f41af9070dd8163f27f9f8ebf002000314061f1b021dddfcffdf04f5f0e5f6ef07fff104faedea0506030cf303f901e2f611faf0fbeddd12f1f5f5fcf5fcf6fb05e9feeef0f4f7f3f9f6ffeef9ffec07fafc05daebfd04f5fdec07d3fce9e5052cf7f909f3fde70df616fe04f3e2f6e701f4fdfaf2fbb1f70be1ee0df0f5faffefeceaf12df7e4d9efef07000becf608e7fc07d2faf4f608f9fbf3ebe4f7dcf002f917f104d915d4311c0ad8e0f5fb0b180501ee0ef6ef4f05cad60021df11231f1606f1fbd9d10112f3dfe01721f7112e00e5bde605f40d1ac907ccfe22ebf7eafd020fe4ffe6ef06db0de1fafff9eddaeaffe00ef11a040c02f7e3f20e24e5f7f4e4eee51d0125e4ff10fb07d50018fdfcfcb30ce7ea20e701e7f7ea071804d1f225f7f4031405e905132420f9021be8e9ffea180520fff904eef807e901d5eefaee0904ec1637f21df4ee0112eb13ecfc3b0a1221d610e12cf32604fcfe00020109fbfcece605f201fc05fafcf9eef7030101ef05f4f3fff4f7fe04ee00f404f904f903f9f4faeef606fcfb0404ff070105fee9f20c04ff06faf804f50e07d6f132fcd01fd9e60de34d0df9def3e7d9c0fbfa0a16eef2f50fd817e906f6d505f41b05fa0f3926d8160d0c1c050af2db03ea0809c7ed06ea14e424ed041f01fafaf311f9e71efe01fbf00c2924081417f3fb06ef09f704fa080bf9f2f6e50bf303f81305e51ae5020901fffcea0109090b14360dfcf9130912f30400091109f30715070df02bdaed0beffd2119fdfa06ee143bfe0f0ab7f133f0f5e8f5f397ffffea13132bf1dc41fd020312f3fe1d0c00d710fbe92202d600f8f3c9f9e9f8e901d6fcebc700e704ebe6f3031dfcece20207c0efe9a219f9d3e70ef5f7f723150ffff8efd9fcb0fbedf0faec00fac6fb03e1dd0bfbebfc0ec403cdfbe8051d15fee6f4f7ecdc0ef7fcfafce8edfdef0503fa15e90bd8dee71adefce8ff01f6fae7e8031efcedd9ef0df3eafde8f412cff30de4fceff9fcf4f80df6152103f0e90608fee9ee0afbf2eb050f03faf4f2e70c01fbfaecfd01f80bd3fbf3f305fb16fbfefde70cf9222a0de5f504f4f506fff9f2e309f20aed01f2ea0dfbeef51d0bfd08fcfe18e8ef09f8fdee0cd802f9f60a020cf919e50d01ee08f2f4f4000203ffef000fe8eafdf206fbebffe6fdf9eaf9100c14fffc0cefe5f30aee0f340fe401fc04f0021bf5e613fb2a3520f515f5f506f6e515ff09f20d0af608df00fff601f910f9ed21103b1306eff600f309090206160bfce8fafa20f113c8f4ed0005f8feedf6ddebfcf7fff9f00103f8e6f1f0fed40204e016f0f102f9e3daeaf0fc04e4f7ddcec8eefff1f4c6ff0ad7ece9faf40cfce3e8efdcdaf8ede9e7f7f7fafef9f3fdf6ed04f00cfb04080304e4edf703f2f6efe4feebe601f500f3f6f507e3f4ea02f3e2e7fafbfbf3fbe2f404f7fd06e504f2f30204eaf9cfefee08f2d9f9eefbf8010ffde3e3e7fb08fe09fbe9ebfef6130003ef02080cf202fc07eaf8f9f6fcecff050513f1f5f7faefea0307050904fdf0f007ece9eaf70ff7efed18faf91802f6f1fa10040203f40501182b07010c12f7d3f51fdbf9080007ec090b2007fb120d20f7f403100ef80701030af5fff5f9fef1fd0117fed910f9f100160507e9140ebce4f81601e3c0daf5ce14cdf80fe6100bbd091dec04c609fecc04d90ef517e0fde4c802031cf5de23ebef04091e12e6d3eae5c6da02e0f7fdfe05fc0409f6e9e4f1f8fdeaeefde2fcdf04f0f9f60d10e50015d30d10ebeadb0b19ff0febe0d5d6d6e6f7f8e3ff0ce8d8f5ef0cf8efe4eff1f6e4fccb13eced130a05fa13f6ebf8fdfb0ad9ff02f307ff14fdfd1bebf2eef101edf80bdb1505e300e8f1f929110ad0f4eb1904f6eb040cd300f5e1ecf707f8eaf601ffe9f8f5020ffbf611dee6e4fdfb0b0bf9f4ddf9e8e9f302fd00ffacfdf4f8f8f8f5f7e301f9fbeffcf6e2f2e9e1f7f9f700ee03f9e4f5fbdffdeff20404f1fcebecd6ddf82ff2e6fef4f7e704f01d0802fcf002e6f20afcef04f4a408edeef506f9f8e705f7e1e4fcf9f3e2d7d7f203fff7f603faf1f60ff4f8f40103fbe7fddbe502fdf9fa01fbf6f10202f3fdec0bf40306fbfded0000f6e505f6fffa0109faf4f3fafafb04ff04f2fefdfcee0aeafbfcfdfef4f9fefdf8fff2f6f4f903030ceb020dfdeb03fcf8e3ff2f03210407fff10b011df912fce20ef3fa4c0b1316ee0ec1ed290015fb0300f30c1de213e5e51c08ed201d01f80d0de9fa0a0dec0efae5dfe90b0ef6f8e9020dcde4edf5fb10f5e7fbd501f5fbf6fb04aa2108e6eef0e0c21ae6f2e7e6f0e1dcdae9d3fa00cce4e9decef2f804b7f3dcd5dbeef5e2c0f900070a14060815f3f4e6fd030618f6f1ec01dfff0703feeaede6050ce8f6e90fe7f70bfcf2d103faf810eeeefa08f6f9f3f810e00016e000eceef10be90cebe4fdfae9e0fe0df5eefaf0f5f8eeffebede0fdff05dd03eaec0a0401ecff0af2f8f50e0106f1fdfaf20806fcfdee02fbfc16f6ecf6fffdda17ec2009f00cf004e1f8090cfdfdfb15e4f3e4f2070811fcfad705f2fff001dc09f4c709eeeaffe7f9eefafd0feafcf1e70508eee4fdf4e401f0ea11de0609ebefee06f9eee5f6ead3ebfd09eef1e2fdfddbeaede3e3f0f2faedfbed00ecf5e7f012a6e6fbd9ebefe5cddef4f6f1f30bfce505cde2f6febd03f6d1ede3f60fe9f8e9f7ffdfe303c801fcfb0108fffb06faffedfdfd090702efff00ec04e5fe09ec0703f9fefd0501f900fef0fbf6f1fdfaf6f2f0e6f904fffbfd06ecedfffaeef7fa03fcfdfcfdf706ee07fd02fbff0e03f0eefefa0517e8e1ee04d90a04fd0e02f5f7daf90be30f110ef5f7e9e20405f5fae4dde5f7fb07f2fdfaf0e10401ed02f2f0ed03edfd09bdda010806f1edf7d8f2e4f4f5f601f6f7e802dce0f2fecbf5eaa6e7fcd4f5e6e6b4eff505dfeef7fae1e6b5eef305e009ebd5fdd6fff9d9f3e5e4fde1c5ecb7dbe8fafeed00ec10e8cfeafb09f5081707f8ffe7f007f8f1fa00b5e1f4e8e0f9e8d0f9f507e4dfeff5d7f4cae9fcfcc905e5dce3e3f0f8e0fdf7e8fbdec805d0f1eff1f3f809e1fde6db02eeeaf1f6eff2fdf912ebfe001dff07dcebf4e0defbe2eb0be8ff0bfa0beaedecf202f4f7caf1cfc4d6ff0909ddeef8fbf0dbd5e2ef10fdcd000eff10060ae9cae3f4f5f5eae1e403f50be7f50e0515e4bdebe7140fe718f7f3fcc3e606e8f3b9dccdf4e210f5ea2c0ad305e3e21000e9f501f9071be3dbfdf3d9f0f8fbe3d3edf7efd8fcfcf5df01f3eae4fce10104bfd8fad6fde4f3e8e9e4e8e7e906fae9d7e8ee00f0daff04cec6d4f9ffeee9f6f1f8dbc5f1d9e901f80609f8fe01ecf9f2f104030dfd000901ebf9f3fbea07f600fb00e602f7ebed0c03fdf6f6f3dd02faf8f4fdfbe703edf304ec01f3e3fcf2f5f1f6fbfef6fa03cae3c9e9d2e00332cea7c2f2c3e7fa21f1c718e70357c2350d80e8eb0c28ba21ed80f59be4f2325002a212f20e2ef5c32c1f1ef0bce7f0fee3fea607cc29d709040300feecf7edecf1f7ec110206f7e6fdf811e9f71fdb04d3f700f40efdfae0edf9f8eaf900fb030df2f6e9f0faf8f5d8d8fafefae8e2f1f9f7ef0ee5e6d8fceeeedae9f9d6cf1d07dde2e7ece8f5e90403eef80806f7fc1aedd9d9e2e0e3dbf7c9fafbe9efcee8deebd1f6f6d5ebddbfdde70115eadff1f3eac0e0ded6f728e002f0fefcd5f113fdf1dfeded0e1dbcfff3fe2002ee07172af1f113eee8eefb2fd8f2eaeaf0e41dd63b4d07edf006c8e6f0ff080adbff160be1d9f6e907fbfd0705fbfb03fb07fbf408f4040204f8fefbfdf4fafc08f908eff801f3f6fd05f7f3f501fbf40105fef9f7ebfefc02000302f601fc02f5fdedf60ffb06fee2dfefdfe90605e9faf4f0f0030cfff509faecfcdd1813f2f4fbfaee091c0e1a0015ee0f0c09ef0a000008dec2d709fbf9f324eb0500f205e2fdedf1fdfcdc01d9dd23ed0a1ffef515e206d8eff50146e0c1d1f7240c12fe310c2e1f33f4e405e70bdefe0cfb2a0217c2d7d339c0f1e1f5df2de20d04fef80203efe1f9fdee0727f5f8f6f506fae90100dee0e5ee0b01f1e6d402e001e1fc16ee01c6d4fcfbcefcf8060907fdebf5fa030bedeae8dbff0f06f6fdf2f10303faebf322ecf702060ef5f7e5eec8f60f14eb0602ffcad5ecfef419063af8e1f8d315061decf1df07f2e9e0e5e2f7fe16f8e921eb00140de8ecf6e8e4e3e6fbd30906c70310d4fc19fefefbf3fd0cfdf30509f8f1fef6fb03fbf3e603e012edf8f1f213fcf509ea0201f50c00fffdf3fbfb06dce7daeaf404fbef0208f0ebfa05f0effd02f4f4ecfffeda08fff5fcfde803f1de03f5fef80500f90502fbfff8f9f0f6e9d702f809f6faede9f8f9f70cf505f1f30ee9e5fcf5f8f4ebf7efe6f803f0eff1f4f9f0f1fdfdfeef08fe1401fefbf00e0411effefcf5fb14fff704fffb18fdfcee04fbf2f5f6fb060000fc010cf8fdeef40d05ec01eb04f1f6fd01fc0ceefaf700f2f9ea0100e3ebfaf0f2f7f606e0e0f6f0fbe3fcf0f7e6f0eceafa04ff1ff1d4e5fbbcd6f7e9daf8e80f02e2f3f4cadee1f5f0f7b400d7cbe3e7fd0be0e2f5edf3cbc9fdd8e10002040301f906f713e5f3f519fd19fae8f8fbf4eff6f50309be01fbf2edf40adedff105e5ebfe02f216e2e5fc00f7fafdedd7eafc12edf7e0e6ecf404eff30f0425110200f50511f620fde60c0324311e0000fdfbf726fb0f1bedf80e19fc15efc1f3f3f0e90233fa1aea0615f2db101bf0f503fd033a0322f517f4f8e2f508ddee0e180707090dc9f3fefbfee9eeec0903d80eff05e1f810faf508e110e5f01513fa0ef1eefcf9e8e0b8d8ed0cf9eeedfc12f7fd07cc00ea02fb100411d9f72207f1f008ffdfeff60f01080406090ff70105e90b08fef90b11100c0cea0207ea11050504f1f3eef4f23635050cef01f1edfc10040fe4f40cfdeef2dbfb0503ebf5e4ebf8eef9e6e20edaf1e3ef05f0edf7001d060807ff021be703040bf7dd0105ea07e30a04081001fa0bf2f80cf2f10b03f906f6f2f6f80020e71ff6eee9e611e6f1f4f9fb08cde6fae7e7f808f7f306eff3f302d409f9bfdff5dae1fc00d3eff003e1dd02f2e4edfcfbf404d6f6eef1d9dffcf9f7e0edf3f6e8f4faddd4e4050aea05f5f503d5fff3000009fef3dbf8edeff5f6d4f8e7cafc06de01efe9e604fb0acfe20207dcf3e8e0040be206e8e300eff112e0f9fbebf8eee7fbccf5e4f8ebde04f91df91a0ffdd6ddf3f702db040efd010206080a02e406d20de60eecebfcee0dfcf3f50d37ece90d0bf20b07f1f81806170ffde71f25ca10fceee2edf9fd06f7f203f3e8f4fe03f31f0aea01f9e702f2fed4f6e4cff5f0fafef3ffe9eff904e3f3f2fefc12f2fe06f7fefaf2f5f0f0f9fef6fff7f70af8f80bf4e0f1040706f90c14dff70afaf2fd240dfaeafaf9fa02fff408fff00f0904fcf1fce9df07f00cf6efedf40912e807f5fe0b1b05feef06000113ebf0f5fd18f61b),
    .CHANNEL_BETAS(1024'h77ee76f8782976da76c077457805766c784177807838773477067717786277f7781079a47921797c78ef76b878f377bc788876d3784476e778ee7706777c776b789f76cd7789771e78cb78bc77ed79e876d375ad78a4786c7798772c773d78eb77307a0a777878527832795f785679c47725780177d77977775e792f784c7780),
    .CHANNEL_THRESHOLDS(1024'h01ed0214020a020a01ff01f901f3021f01fd01fe0219020d01f8021402090214020801f2023f01db01fa01ff022002020209020e0226020d021b021402150213021501fd01fa02420224022401ed023f024201eb021502310206020d02070208021601c6020a02130200021e021101f801f4021c01e802020228020202170213),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00da),
    .ADAPTATION_DURATION(16'h13a8)
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
    .KERNEL_WEIGHTS(4608'h060b09fb0e0dd6efe9eae4ec0defdd1a09f50dfc000e0f09fdfaf70c091df2f8050b15fb04f2f9fbfd010a05edece9e0e0e1080afeed060f1e21340bf3fbf61a100422fa15001613faf010f5e302f1ed1ff9ec151a14192d3222100708fd0d04f7f401e8e2f5010df60d1109f7d1c4d7cfd1bfedc8ebeee408fbf808170d173c371006f9102bf814fd20fef5fa1107fcfff1f306f61507f2f3e9f0e900e6ee03f2e6ea09f6f6f60c100efdf11a1f0f011901f30021f61fea1c12fd05fcf9f014fa12f7181a1af2f80407070aeefbf41318dc0cf80b0ff506f705f5f3fe0a0209fffe1ff80119e4f700e706f4373502314a1514c0ee02d5de13dc0209e5f116ddf203e3f11c0419d413f1f70706d20a0afd05211e2b0934070502ff14f4fc07e4d50fe1fafaf2f0e4f90e120debfd0af5e3ede7f2ede9f0f1fee4f826dfce11fee001becaecf905000517f915f813fc17faf203070e09fbe903f4f3f80f1b0900fe03f40f0d1e0e0cf4ebe20a02f11a24fbe3e4df07e7071617210f00fe040efa0c141323edde10fbdf171af0ecef16fff608dee000f104ecf0f5f3f1e5fcecf2f3fbebed2b0f0b2bfb110809e7ead6c1dbe8f70ae71a190918f8dc000ce401fe0022faeffc0303ec1606da02fc1000f91dda06f7f0dee1f6d9f411ebf00801fa0814f702fa0f0e0dfd1a1410000b00300cf202f108280e1f111f0a1a092bece701160d0d050d0d060c060bfbe5fcf5081af40e0ddedff6f7e90503ec17f70801030012141a0afc17e0c8edd6c9fdc9fb0ed4f117d1eed9eb1af12b1308330d28),
    .CHANNEL_BETAS(1024'h784277a07948774477687765784a77a077df769d7843770b783a776477a2786677d6778277e778a3782377f177fc783a77ea784377b677ee782578a8782877f777bd783f781d77d5781f788d77fd780777f877c377e8780b788f77e2782277ac782177e177c477c67854780a781378a177d47974784677e178c0783a77f377da),
    .CHANNEL_THRESHOLDS(1024'h020d02010205020801f30223020601f7020d01f601fb0219021d01ff01e00203020d021d01fe0202020c01ef0202020c01ef01f401fa01f301f901f101f90209022801f5020d01f6020d01f601f601df020a020201ec01fa0212020801fc01fb01fa01de01f901f30214020201f801f601f7020001e8020b020c020502020203),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00ca),
    .ADAPTATION_DURATION(16'h1416)
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
    .KERNEL_WEIGHTS(65536'h1710f406f9f40103f718f118f90afff2fcfb04fe070ffa0cfaf8fbecfaf81b08f20400f1f5f213ff022007f9f5ff0af102f8fdfa02fc04fe15f90e0c05ffee0cfbfafbf4f2fdfdfb02fcf70503f7f1f9f80504fafbf4f9f2fdf20315f200f7fcf6fe0303f9fb0602fffbf40a050403f907fdfbecfafe01f9f7fdfb05fbffffebf8f7010308f504f60305f9fffa0bff08f50000f6fd09fefb0010fb01fc17f703060c00fbf9fcfdfc04f4fa05f601090003f908040203fc07fefaf9ff0204f60bf9fbeee5f309d3e2f7dbf0010be9f3f400eefee5e1f50d00f9efd5fafef2e3f10ae905e8fff601fdebdefde609edf6f100fff9e60906eef1eadc02fef907f6dceff2e2db081005f20de2e6effb13e6f400f7ffff04ec00fcffecf605faf4edf20cfef9f0eae204fd04ffebf700f3040ae40afeff1514f4e0dcf2f8f9e32ef1d300f1fffff7fbf303f7fd050201f006fb000100fbf9fbfbfaff0000eeff00fffc02020001fa05fafe0003fafdf4fcfa00fb04f8f506ff0304f5f7020001f9ff01ff01fafdfaf8fcfcf801f9fd0104fcfc03000002f6fc02f4fb0001f201fb01ffff0201f801f501ff00fefffcf701fdf400faff0004fdff0107fc02fffcfffc0202f403f0f801fe080108f317fdfcfbf204ff0202ff02fef900fd0dfdfcf90af9fe0201f9f9fa0af5fe0cfa0bf3fffaf305fb0003edfced0afbf8fafff502e414fcfb07fc05000108fefbfe0403f8fa020a05fe10f7fcf8f7f9f90c00f8f11001fefc03f5f0f20400f504f6fafd080cf30804eb06f7f801fafdf908fafd0a02fdfb0cf3eff505f0f900e2f5ed08f4ed04fbf9f6eef6f3fffb05fbf300fef6eefb03ea07f6fbfef406faeef5f804fa01f4f8fb04f004fefcedeee8010aecfa09ed09fc030502fc0afbf2f5fb08fc0d0906f502f6f7ee0202f9fdf404fafee1f4f502fdfff80705ef0be80bfde505f50ceb00f5f80cf2f5f4e90502f2060508ef11f2170bf4f0f60afde602eb0202fc06f802f10210f2f3f8faff091400f70509fe070d0413f4eef60205010916f807edf0eff001f805f902f8f500fdfafaeffa150006fdc7e6fc14f9f1def80202dcdef0eaf2f7fcf2ebf3e8f2f6f8f8f0dff5e2ece4f302f6f8e9ecfedeef18feee0e2af7ed03ebff07c7f4d506edf9dfdd04ddf60decfa0005d1fa14f6f5ec02ece504f408f8fe09ed05f8fe04e017150aeb01fef301e402edf5f5f8e9fde311f7f8e9eaf2030b0502fd000ff7fbf5fc01fbda101010f91bf7fcf8d50606f606f8f701f6fbf7f6fbebfcfaf50f06ed0512fb0a0bddff0df2fffff7fff40d0bfaf6eefbfcf41be8fa030407fd15f81401ed09e404100ff201f3f2fcf7ffff0705f0fd0400fd05fcfeeffaf4f6f4fdf0f2eb0dfef4f502fefefe02f6fc0614fafaf5fef60202ee0300faf70505ea01fff7edf103030cfbf0ede30913fe0af0f709fc0bfffa06002001dcf203061408ea14140000e6100b01f6dc0c0111fd091a04fcef25d704eefe0605f10c02080f0ac6ec29fdf801f0ce03f902f303dcf9f802ebe102ecf60cf3df0204f803e5edf203e7e7eaf4e9f8f100e7f0f6f5f3fee9f4edfa02edf7fef5fafad9dbd8f4f3f5d201f6dbf4fdff00f504edfa02f3faf90202f7ff01fdfbf8f7f700e9fef1fcfdfaf1f4f6fcf4fff4f90201fafcf9faeaff04f9e304f8f2fe04fd00f6faf002070000f0f700fa03f5000807fc09f6f9f00513f8fd05fb0500fef704ebf5f2020a00eef8fe05fb0602f9ff0bf603faf3e5080604031900ff01f406eff4f30400020517eded01fefcfd0503fd02fa00fb030406fffd00fa02fff90103fb00fdfaf9fd0206fdfdfefffefefd00fe0102fafa01f808fe03fcfcfdf4fdfcfdfc0503feff03f9fdfbfdf2eb0400f2f5ffe4eaeffcfae602f906fdf2f1fb01fafde4e100fef0f6e901ecfaf5f7fafef1f0e9f2e7fbf800fa01fdef0003fbe8e4e6eff5fdf2f803eafef7f6f60818fc09f805fb0f04fe010103ff01fcf7fdf9f2f9f702fefaf30dfe02ff08fdf4f10d040618fcf7f9020cf90afff5f9fc050013f9f0fefbfa00f4fd0607f1f9f1f9f3eff4f901f107f2ecfafefe05eee9e7fbe40002ecf2f4f9f8ff03f3fef805fceffdf1f1fcfbfd02fdee01eff7f5ef06f3f4fee7fff7faf2f0ec08fcfa120cf8fdf4e5050e00fd0005e60708f9ebf2f807d60b1becdbf916151f00040c02000310fc0b0204f3d1f00dfbf80503fa11ff1b171a0bf3081500ececfcf40bfd0c00edfaf404ea0103f1fef5f7f903ed08f90008fc0703f4050ae90806110517ffee0004f708fcf2ef09f90bf3f2f108040603f506fb05f300f7f1f6ecfefff6fd01e9edfde2fcfb03f1ebf7fefa07e1fcf600f5f9f8eb01f2ffe8fcfd00080600faed01e8eefce7fff4e9f6fb04f6f4f707fa00f3e0fcf5fbfff1ecfcffefdd0909ebf202e6010303f7d6fb0109fee8e2f9f6010404effa0be5fef0f6e30009effbf1f0f4f9f3dd0009090cee09f8f3fcfce4dcebf5fbf9e7fb0de80704fdfdfb05fcfdfdf70108fbfbfefbf5fbfdf9ffeffffb00eff501f8f404f8fafc00fd01fef305fa0106f2f5f700f3fef8fff5f6fafff8fcf6faf9f9f6ff0afbf308fefd03f0eefbfe02fc050f05040103fdf5f7fbfb0afbfa0900fefd01fff9170306fbfd12fefe0af4fb01f800f808fffa02f6f603ff08f8fef50204f615fbfafefbfff8fcfdfcfcfe06fc0300fe05fefdfafbfe02f9fd03fcf9f80004fc050301fffcf805fefe05f8fcf3fefbf607faf5fd06030206ff02f9fffd0cfa02fc00fff6fb01e803f6e800eefdfbe8f9f50300e5ecfbf8fffff8f407f6eeedf8f9e404f7f8f4f709eff4f7f808f7ffecf404f8f70709f9efede2fcfff4fe07f5faeff401f4fd00060afbfc00fef9faf60402fbfffa01f8f301fefef4f80c050002f504edfd00f1faf902fdf3f5fc00fcfc02f5f7f9060211fced0803f9eff1020cfbf8d8e30109edfcd30bfd00ff011dd50ff50ff7d0f8e7f4fff919f6e2e400f7fa07ee0df0ea05feebdf0e17fc0c2eecf4fa1e0a06e7030802f7f5cb1315dc00e9f708fafef3f707fcfe05030deff5fcfc05e913090306faf8ee0308f2e3f803f70bfcfc0604fae9f4ffeffaf8f4f20ef1f804fe0310fef0ec040a09fc00ea03fd0100fefffdfcfffa030004fc02f602f8fef0fcedfefc02fb0efcf5eefafdf10e00fcf9020806130afbfe0a0410f00104f5f70601fefef4fefefcfc05f00013f7fef302050208f4fbf60604f6fe08f9fbf8f1eaeefeeafafa0005f1fefd0afcf103f7f9000b06ff0701ea09f50e1400f403f4ecf9f9f7ef0e07f6fd05f201fee6fce2fdfb0ff30dddf617fad3e904f503f5e92013fc1604ded8f9e9f6eefcfed5fee2f6dff7e8d5defff9ebf3eefc01e0f6d302ffd9ecfef704efcb00ebd3fffcfb03f213e9f00c050cfdfef900fefa0505fbf6f803f6fff2f6fcf8f8fbfdf701fff9f90c01010201faf6fafcf8ed0bfff20406ff070bfbfafa000601f1f5e901eae50802d6e20ce6f9f308eddffefff9f4ded7e8faf402e6d7fef3f1f8f4ececfbeeedecf1efeee5e4d500f4f4f1e302fade0507e9e4f5d407fcf0fdeed7ebfdeae9f6f8d8effbdfeaecf8f9dffdfbf905e8f6eef7fb0105d3f303f4ef05fbeb0aebfff6f200dff300daf600f4efe5ffefeffe07eafaf4db02fef3fde8ef0702fcfff805f5fa03fffcf9ff0601f6fe03f9ff07fdfdfd040bf3fceb01f7f8fef500f0fe01010e050001f0f205ff01030609f907f80600ecfcfdf5f004eefaef06000a140ef4f10a07feeb0002eef3fd06feedebfdfffe05e2dc0eebecf7000bdc04ee0ffd02fadde500e40aeff8ee211ceee3f50a14faf705fff513eef8110207ecfbf9040002f40ce702fd1f0400fbea03f602eefef300082ae5e0eb1bffde00fbdfebeafeefff0d01e9e8f404f5e9e605f8fafef5f6e4fa08edf3ece025e0f8f9e605f9f2f6e8f6fd0006eef4ef0cf7fbe9f4ebfb0ffa0eeef9fe0900faf90403f8f6f4fef8f80f0eeafa00efed01f5e5fa0200ff08f9fffbfff3fcfcf8edfdf3e60703edf00ddbe6f6ffefe402f805fffbf00412f902f5dd2801efd9ef07f601e805f1e1ece6ee05e21f06eafef7fe01f8170ce5dfebf607fce71307e10bfbf3f8f105040dfe02f50cfc00fe04f607fb06fdfdfe06f9f91508fdf512f5fb05fffc0207fd020d0c04f400fa020204fff90105fc02fa01fdfa00f9f4f00d0204f5fffef7ffeef4fe09fd050403fe03f902f5ff0005fff9ed01f2f7f200fcf50703eb00fa0af90ff9f20a00010af206f5f904fa0402f9070e08060003faf9040af5e3f6fe05f706dde3fb0cdfdaf4ee030af6f3f1fcf700e6f5eafbe2f2f400f30afbf2ecede9e7e0f8fef9040308f8f4f7f90c03ecebebeef6f1e4f709cd01f804fc0ef8f9f302fb0002040704fafef90301ffff04f30301fd0101ff01fdfe05000402020700fc06fffbf702f901fffefc0102020109fcfafdfdfbfcfa01efe1ddccf6f8f2e1fae0f9fd0df3e901ecf703ebd5dff5eef605e2f2f2dce0e906f2f4f601d4fe03fee6ef04def8ef13e9e8f2f10605d6dbdffcfbf1cce110d2ec06eddf030de5d809d8f7fa09ecdbfb0007fcfcf3eaff0efe03f7fef6ede00307f3f7e6f3edf000f3edf3d71600eaffdf03efe30716ecf4d60600eee6fcfad8fa0200fcfa03fbf7f6fef6fafef9fb01f6f9fc00f5f200f602f4fcfbf8f8fcf9f9fc00f902010000fafafbfbf5f90af2fdf9f9f9fa01fffdfff6fbfe02f40005edfdfef4f70ff3fbfdecefe3f8fcf0fdfbfe06e8f8fcfef00df4fd0ef5f2eef8fae5f8f40002f4fcf0f1f5f40203fcd40005fbf6f70701f6f1ddf9fff901fbf7fcf9000100f8ff01f6fbfcfafd010ef1fffdfef6fcfa01f9fffd00f4fdfafef7f803020001fb07fefdff02fbf503faf6f0fff6fefdf8fe09fcf3fcf80301f4fcfa05efdff2e9f7e003e7e4fe02edeafbf810faf5f1ea06fb06eefaf9f8e6ecf501e7fffff1f1f5f2fdeae6e9f7f3fb01ebf3ed000b06e0f7effe05f3de00f3e6141f00f6f80e08f8e0f5fefe010910f60207fcf5f4f8fc0301f5fef5fff7f6fa0212faf90605f8fe19fdfa00f9f80101f5010ee70dfffe06080bf705010dfd0bff01fffdf2eff3020203f3060003f0fafff5f9f3feeefe0bfefef4f8040109fcfc03fe040ef605fdf3040de6f708f909ff0bf100ee0301fb14f0f8fefafefafdf6faf7f10a01ebf5f3ed0ffc03f6f7fcf6fc04eceffd01fb00f6fcfff5fef2f6ff000700f4fbf9f9e6f6eff80500e8f7fcf2f5f302fcf7eceaf6f703f5ef11e4f2eef8f8fdf9eb0105fd09fa0007fe03fd0306fdf7f501f9ff10f7fdfa08fa0803fb02fdf909fc0105f9fdfff6ff08f9f80cfaf702fcf9f801070104f2fc01f6f7fbfbeef703e2eff7f011fcf7f7ff0c0408faf0f3f6fef4f8f0f702f0f7f2f903fa01fdf3f2f7f7e4fcfbf6f703f605fbf9f5f30102f2e3eaedfcfafbef09ef00f10c261bfff911e61718f6fb1217fbf3e9f9011724fee70ccc0cf6f8d9fe00f50101f80313061009fdfff903fb00f906eede0ce40d0af901eff5dc20f1f713eef9f1f70106ede6fefbf8ee0901fbfc02f802f0effa02fd09ede5eceff4f2fa02dbf8fefeeff5f2eff3f7f2fbef08effaf9ecf2effcf3e0e5f1fffaf8f903f5e801f4ea00fadbe5fbdceeee05f8f2f801fb00f7e4e2f7f2fbfced0500f3e305ffe0fb01f2fbf1f9f2f4f80000fefaef04f50000f907e7f3f3e60501edfae9e913fdfefdff00fa04fcfefefbfbf7f80201f605eef30100ed000706f8f000effb02f6ffe6fbfd0af9f40500f1f7fc09f30c0503f6f401f9fb04ff03feff08f4fe04f308070505f7f5fbfd0501fa08faec02010601e80603f8fbfcfcf2fefaff09050f02f30802fafbfefef801f6fafeef0102fdf80afe07fc00f50503fcffe80d0903d7d7d4f5f5fdecef01f704f704e9fb01f7f0f7fcfaf6080cf5e7fde0e706f50509f1fcdde8fdf8ebe620d5f6f426deeae6f9fc0bd3e4f20e07e0d3e20bcf01f7efeaf0fbf1eb19eaf4f3f8e0e5ffff07f2eff7f505f4ee0ecdf30215dcf60ae203fa05ece3f4e1ffe7ed0ef6eaeae8dd06e40102e5e4e2f50506eb050cd408fcfe05f500f0f6fcf5f0fa00f71400f7f7fff605f307f701f70aec00fb03f9f4f2fff402f803fef8fcfbf3f3f4fff3f8eff404f4fcfafaf6eefaff01eded0ae008f4e907eddaf710d7e6f6fde3e3ef02fc0be8dae103f804f8c72cf2f4e601f5e80500f9e7f4dde4cce8d01b10f5daeef9f9e20e06ebf40201fefdddf8ede1f4f2f3e2fdfae1f306d0e9fb04e4ea0dfbf3f6dde5f507f1f0f3d8f0fffde1f9f8e7fcebf7ebe3f8e6df01d70cf3f7d4ecf7f4f50102e700f0e30df9d9fefae416f203f80104fef807f6feef05f5060000100101f8f60304fe0a01090206fdfe0021fef9ecff05f404fcfd05050bed1cf8f8020403fdfc0209060dfffd0b0202fcf1f7f5f8f2e2f507f4e9fefaf9e406fdf803f3eaf903eb00eff5ebefeaeafdfce3ffe7f1fcee05e8ea08e8f8f1f3def7f7f4fb0205f2e7f0f401f700ede9ebf40de1e502f00b15fafef20bf8f70af4fd0001270dfc05050c060dfa0ffe04f2fa0406ff0ffbf0f711eb011add0ce515f0ee1c031903f81002fe0005d6ed0002fbdaef0ff6f9240404170516f8f1fef004f901ff06110aff060e1f04e0fc25f9fa0400f4e9ef1e18fc1b050c0cf910f1f612fa0ffd06070b0af509f3f5f2dd0af9eaf3f9f6f3f70508f4f70903f313ec040501eceef3f6eafffe00dd050b16f1fafeff0407fef401e10e0c04f204f300faf5ebf607f40802f5d80a0afcfbde090b0004000405ea02fff7e208f612f70303fc01f508110209f3fdfd05f6f6eef4f7faffe9ef15ff01130ef3ebfefc01f103f909ff06fff901f409f6f9f10ce30e0f0bfbf90a1efcf6f9fc010b02f5080a0c1bfa06fceaf3f2f909f8f4fff4ecf5fe1cfe0402f60b080902f21308041139f6f3f9f40706f4070c09f8f7d6f11b0107fc06fcf207fe05fafbfaf9fd06f703f704fde9eef7fdedfffffc02f8fdf805fa0601ee00ff04020004ed0406fd0cf6f2030203f6fb04f502fffd0006f8f503fdfafcf302f6da0600e305fa04fcfbfd00f1fce2f1f3f9f802f3f500fdfdf6f2f1e80404f8f2f3fce9ecfbeeff0df5e7fffafa0804fbe3f4e7e20afff3f8f6e51e1301ff0ffa0100f0000207ff07080b04f9fc0af103050507f005e505f5f304fcf007effffffef427eaf20803091ef7fae4fc03f802fd01030b03f6f80015fde402e5c6ed08c801ffdeebf90cf2e804fbfafbd9f9e706f709f2d0e5faf4db0602e0f4fcf9e5f50afad806dd01fbebf2f9feffddf509d7fadfdafaf2c5e1fcd300fa02fffe04f7faf9ff00fffcf7fa00fdf8fdfef4f404e9fbf0fbeff9f3fffafcf200ef0409f9f9f6f601f9faf9f8eefef8f3fffafdfef602f7010002f5f2f1eaf4ece0f509f0d701d7e8e801dcde07f40cffeeedea0eff04e6e8f1edecdcfcf7d4f5e0f8ebddf8f6e1eae7f7fbe4e4ddeb03ee030ef0f7eaec0600e8eaf9e1fdf1fff3fbf4071001fb070afa13ecf5fd000102f606fd07f5f60d04fcec00fbfe0cf7f1f7e705f8f60b01ebf306f5e61003e506f80100fff7ed15fef712f208f70de8f20701eeee03dcece606f6f0fe01fb05e5ebe9f9f502e9f1f1f9eff7e800f3fcf3faf5f1fcffe4f7eefcf204d2f7e8f6fdfa0eeafbefe5faf6e8f7fbeb1209e7e3020afcf1eefaef010c07f0fe0806fd03fde708f8fef402f104fdf5fbfef4030bfaeb0af80dedf3fcf5f20304e9e606030bfefaf002f700f6eff905ed04ff01faf5f702fff805fefafff60801fd02fd02f8fbfdf9ffff08010608fe05030a03fefff6030108f90a0af1000300fe0508f5fffcff01f40afef9fff6fb01f5f508fcfc0dfefdf8fc080503f30d08fcf6010409f9fefc020a040a0603000403fd0106ff130601fe05f304f103060600fb00f4f907f90bf70ffe08f8fefff6f4fdfcf30efaf4f20ff9f7eb02f6e7f7f2f9fcdc1109fcf6ff0addffef0affff06f0faf9f8ebfafffdf9fbf400fefaf509fffcfc00fdfefae9f80b0cf2fbeceffcf1f600ff080201fa05fb14fc13fbf3020103f3eaf0fe02fef000ebf0eb03fdf7fa00f704f110fbfe12faeefaee08ff0afdf2f40600fae4f808fefd0104fbfbfaf107f2fe05e7f305f0f70503f8f9f100f2fff6fdfd05ef0501f4fff703fbfd02ee03fdfdeefff6e5fefdea0003fffaf4f901edf902edecf2f605fdf4faf7e4080f12e104f712fcffe915f006e8fa18090d021702e9fc0307fffc1af7edd409ffe8fe13fd0ce3f7ebe6f2100efefa08f2f3fcee1500e714d71bfef6e6020ce30bf0fef0e8e615f504dc0c0007dd090c0406fe13fddb00fbfb02f1f3f8e6dcfff31603fa1106db03e3dee9040ef1e621df02f40208fadd0ff308ec02ce1416d5fbf8f6fb05ffff05fc02fa04fa0a180206fdfa06fb04fef40009f7ebf3fef3fff609feecf8ff09f812f40201f60207f5f0f106040bfaff03fa00fbf7fa000102f6f8e8ed03fdd70307d7f6f900edfb07f4f905ecd8dffdf9ffe8f1f4f2e7fa01f507faf309fbf700e9e6f5e2fefeeeeff5f502f3ff0de5f4ecde0afbeeeef8e102fdf4f7ff00ff03ecfe050108f701fef705030204f0fbfd0006f8fd02fcfdfe010afc00fcff010306ff0203f104fc00fafb04f3fd03fb040500fd05fefb03fe0902f5fffc07f8f500fbfc03fcf701fcf1f602f9f8fa0002fef4fffcf4edf903fb0001f806f40a000602fcf4f0fd0bf5fcf6f8f8fbfb01f604ff030202fbff0b06ff00f7fe05f8fefdf2f80eff02fe00fbf800f1f5f6f9f3fafdf300f0f708f6faf604fdfb00fbfafc01f9eaff02f8ee00f4fcfff0fefef9feeb0bf1faf2ed06fae21214fd08f5f603fc03f8010104050b10040501f6fd01f807eafe0412ff00fdfefe14041116f3f404fffe080200ea06040e0700fd0a18f90e0d021dfae204f4f5fef9070301ecf0fdee0a10f2fd08fdf60009080504fb091415efe3fa16f90111ffeef8060a0c1a0e01f900f20dfaf40210ff08fc030aeef3fa06e9e8d90a130d03cae0fbf9ea0bd2feebfceff605f2040509e7e9fcf90608e415fce9c107eefd03010202ce08fad5dee5240fea0a03fddb050dffe60af908fd01c917fbd8edf2e7c8f903fee8f6e0f0dffee1dafdf5030bf1ede806ff08e8dd28f7ebdaf103d9fefff7f2d9f4e9dfd9ef1d00e501e8efe8eb010ad3f0e4f8fdfacffbeecef5fff10200f8f0f4feeaf4fefdf3ed07fc00fef3f5fafbfe0611e402f107ea00f9f10908f7f806ff06efffed020ef4ecfdfb0bf512f4fdf5f7f000fffef6f1fcf2ed031f0ffc10010f0001faf004faedf7040400081203f0f4de0b06fbdc09fb1300fee3fe00051c010a01ff11fa06d91b09f700e5f7fe0ceb060ddc1c09d219f4fbffe9f708eceaf8e701f50df4f2f5050503e1defcfde70402e7f3f3fde8ee02db05f2fff401fefff3f6f5f5fd04f6f5f507ebf504f3eaead8fd02f4f2f9e6fc0400fff7f5fd0af601000904f4fcff080c02f8fae4f907ff03fdf0fffce3fa000a010df0f8fefe090af71df500fcfef90ff300f30204fc010a00eff1fd0e14f1fa03f9fb09eb0302fd0203fe04edf9fb0102fffff905faff04fef6f30a0d01fa0a0603efff02f9f40e08f2f301ebee08f8f008fa050e0809f8fcfefdeeee0104faffff020800fbfafe0302fe000005fafcfdfdf9fd02f6fff703fdf6fff706fdfb01f8fefb01fcfb00fa02f8ff09f8fdfcfafafafffefbfff9fcfb03f801fef2ffeed30300fcfaf8f8230b08020dff0bf50bfbe2dc02130b14db131507ed0a0a080315fffef6071aebfdf4f70c08fef7f9f9f407f9f80705f1f5ffe30b1ed9fa03fcfeff01fdff010104fcfe04fa0310fc0206f7ff01fcfefc0ff5fdfc0ef9fe0bfb03faeeff0609f70bfd03fc01e80d02050102fdf5f309f9ff01020ffc07f80afb04f8fa05fa05edfd08010ef501fcff05ed1707000a09f8e9f8f5fef90ff9f9040502f905fa09fffdeaf8f4fbe604fefc0304faf7030ce115fe00ecf604e2f5f5f2fd02e7e3fbed04e8f9f6e3f9f104f9f7efea09fa0ce9e6ff13f7dbf4f6ec03f7f3ece9f4e9e4faeb05020ddaf3fff3e80604e7fbd9f107f1f7f9eeecf3f8e9d9eefa19fff8070802fad5f6ebf0f20808ffe6f40af81cf802f9ecf2060202f80c02fbe8faef0b0105e10bec14fb23effffafdf81906e50ffeeaf402e8ff00fb010500fbfdfe00f50a0006f7f7fafefe09fb05fdf600fd02f4f8f60600fc03fbf4fbfd0208fe03fafef6f808ed14f50101f8fe090800f90cfa0003eefffdfcf602fc04fa02f601000501f909fb07ff01eff9f700fdfd01f8effb0502fb00fbfdfa040006fe03fcf902f0fcfe00f909f90200fd04fc010702fc02f6fc0104f9eadaecebfdfa0df8f00f0308f3fb12ff0a0d02e1f816f5de040aeee4d9e10af804f3efea040521f4dcfa09fe0bf9eae703fb25fce3e1fcf704e8e002fef7f5fefbf1fbfbfe03f801fe03fe00f2fcfe0104060102fcfe040905f901021f01f50300f503ec04fd0d05fffaed0501f4030c000306010207fbf40709f60bfa08e501fdf10e07e4f9fcecf6ecf9faf1fdfcfdfee0f5ef060002dee3f903e9f3e704e406ecf6f8f6f2dff0f2e2fc02f8d508f9e5fcf9faf3deeae70400eef6fcece7f6fcec01f4f8f304fb01f009f9f30106f801fafaf3fcfaf50ee904e9fc06ff02eefd04f30cfffde90003ea02fcf0eb0c03f107f6fafe0cf3e8fcfcea02e0fdfcf2e6cefaf70ee1f1e8f400fee3f4fdf8ff08efeedf0bedf4f8e9fdf2f6eaedf5050cf003dfedfdf1f9e105fafeea0aebfdf1eafd03deecf9f3faefcb0bfbdff9f6fc00f6f8f8f1f4ff010204f90dfcf60002fefffcfffefe04fff1fe04fcfcf500ffff080005fefe05fefeeefb02fefbf900f4fbfe0801f9ef070101f3fd0b010cf3fbfefff2f9f4fc000004f6f80003fbfff8fffefcf7fbe90deff7e7fe00f7fcfff5fa0601041106f0f7f6fcfde4f7f3f3040205f8fefbf4fc04f6f5fa0c1efafbebe803fcfa02e5fe0100e3f0f3010204f9ecf1f70ded16efffebe8d813f22805f4f0faebf5edf1f3e315fffd26e3eedc0ef7ffe0f122eff5f9d80c04d9ff05f1f802e7d6e1ffd1eaec06fcea06fd04feeaf0f0ff0407efdd07f9f0e4fffaea14f9f2feeee8d3edffd306fafcd3f301f8f800ffe9dedae70af7e8f3e9d001ecedf0fe0706f606eaf4ee07f1ee0d0805f5020ad4040a08e2fd0409f2e5ff12f70302e70f09fe1909eb0c0e05fff9fdf3010e19090204f10701faf7fc03f908fd09f901f9f7fe01fd07ff0303fdff0c05030900f900f7faf403fc01f0fd05fdfcfcff080dfe01f1f402f108fcff01f801f802f804fafaf30d04000203f9f9fdfcfad704fff3ddfccee3fdf7ddd7f3fef906f0e2f0f204f1e3e2f7efede2eaf7ea06f7f5e3e4fbede0eaf0f401fefdf0ed02e30702e1daf9fb08fae0ebffd4),
    .CHANNEL_BETAS(2048'h77fc77ef7832778577a47839782d778078e2779477a477f6775677be782d785678cd775b787377c1781d77d6786477bf77f7789d77e377aa77ce787878bf77f477c8778c7863776e77f077d57839780377a4784a785f76f978d1772877ad7800777d78a577c9779177fc7834779777727807786b779c78b777bf774c77e2783577f87846780b7770786f779a7805782a7819781b7771782077d07864780b77d177eb78107836784077ce7856784b78b378ab780077bc775a7798785777e77800789977cc7776784c774377d377c2787377a77794783a787677a8787b78e377ed77d17851783877d577df783577d27822779e780d77b577d3778077b3780b77c9),
    .CHANNEL_THRESHOLDS(2048'h01fd01ff0211021c021401f50213021d01fb0227020701ee01fb021b0203021c01d502140222021d0203022a02040213020101f5020e020e020a01fc02110224021c01fc02040215020d0221020e023a02220206020b020101fb021b020f0201021201f60219021e0213022502010221021d0206020b01f1021001f702160229021e01fd01f9020b01fc022402300208022601fd01ff01ee020b01fe020b021201eb022b021302330209022f01fd01ec01d4020e0207020c01fd020901f8022801ed0207021102040214021a02170218020a021f02010206020601f202070208022601ef020b01fb020b021402290229021001fa021002210224021c021b0222),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d3),
    .ADAPTATION_DURATION(16'h137e)
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
    .KERNEL_WEIGHTS(9216'h310f35f1fd2de5fd140c2605052ffbf6fd1ff7090c0b0a1f10fc280ff3fefc0c0d150314e8f51a1f171022f61205fa08eae8fdfa04f0f6ea06feea100406ec0d2d1eed08e7d4f3e5fe32fffcefedebedfbec070d00f1fef9fefd0404fb03120a100c14f900f905cf27fe11f9fded1104f90007041a0aebfd16160e03efe6130e122e22f70d23f6d8d9fe2322f9d4e0f408e30d2d1009431e14ef160109020c17f0010f00f40811eeed02f6f2dfedf6f003e115e7fbfa000e00e422171204fbf90ef2fa090b0b05193a0a1106ecde2809090f2608fcfeeae31f061621fe16061f1e26ea1f22e6091bfd1704eb00060f0401edf20e1ae807feebfa12ed06f4ee0afcf1f5f400070b1614331f0523011e030c0203f7fafeec09ee00020e090a12fbedf30df3100e0c151213211524f43024141e1f0a050b11e61218e6281d12e6dff0e8ee1915f4f1fadb1c151b101f1b1f19201c30161402e81108f71201070b0a060e0b09ff05feef13e6fbf9f112eb11fdf1fafbf00e01f510101111ef1308f8090efe341c0a29f112370e230c2206f9fcf9f7edf2171ef9ff0f06ea1711dcfe03f30b0e0ee9eaf0e90e05e40d07f3eef0fdddf3ea1010fe19f1f6f5f3eafe2306fcf7fef2f8000119fe11f10df507fa0b0afeed200ced23fdf41718eefcfb10030efaf5f5151c1ae8211af4f008edfd02f9f2f5f8fa07ec02f2f611f4e834180c00080ae9feeae8e2ecea0c0411f2f8fe02f1ebefeff60ef1e6e90ef708f509e4f3130c06f508ffe20a0fdf05000200f3fb03f2030af1fcee0709110e0ef301fdf72df2f40bf206fedae110e706fc0ff6ec0d140d0de6f30afe16e5e6d2ea03e81207fe1d05f51c03e6fd05d10c14faf2ecf40200f508f2040efa14edf90300f5cfe8cae61105250f07f0fd0b0cf30b030d0608eefd0cf7eaf506010523f73a3c3a4fd10eef0b0d2400f6edf7efe3faf8090a211900edf32315212f291f2d1126fff70e1317fe05fe040bf3120102f7220f2820f82b14343e06081dec0401fdfa1ceb03ebebf8e904f80b13efeef30d120bec03f7dde7202c11eef7ee030cf918fcfdfb05fe0cf804eff4f91408f12722333511261e0f1d1f0e23e5ff1df9eb0407e70600e5f3f5ee100306fe01101d1000f4fc05f2fefd110207f947f01e19233afc0bf10af4eafc0431273d1f042619f2fbf1eaef02fafcf809f10b1412011a21211c1825cad6d0f5f4ff1504e71e0c072933fb1520ea31d50ecdfa16badaf4b6b2fc0cf5f100ee15faff42ef0d18def0fa0d011ae5f612f3e30a1cfd2019e30413e7e30c160cf90d0706fd13040c13eae332ec001711e70620181519190f22101c210a12f21506f5f8090815f4fb3b28292e2f221c21d7f209f319df1c231eecd9061610fb02f3f7e1fa051feee30e0907ff2421f213f10ee5ff201e19220b1efff7f00308230a1a0a08ef0cf7e314170e1ee5f6e7270d0b110e14f5dc1bf4f117262d150504f2f40dff03fffafc0b0c080df71af4f2f61ae20e02ff0e101925f519e9fe0f26122e13e00301f6fee5071b15f2fd1d081c0908110804100611f6ee0cf81ef613fc100afd080ef2fa2a19f30f0c2423efef0ce4fbeefb1a1b),
    .CHANNEL_BETAS(2048'h780c780e781677f978317817781e7842783e781e77a577b7783577ba78a9788a786b780c77e27832783d77da788777e37847786077f9781b77f178d177ea7808782279ad78e07874786a788678297818782e77e477dc77f27822782c77f978397839780e77f077f57844780c7841780877fc780e7812783b780777fc77e078147821782f7871788e7857780977fa77d277f377a5774e783777c878b578a977eb7838780f782577ec7886781277da78a5788f783f77de781078b678f7783377f1788a782878cb76db784e7861780a782e7788781e78bc785378ab7809786b78337828785f77e1781d782f786977ca77e57831782178117851780e77ee783f7828),
    .CHANNEL_THRESHOLDS(2048'h01f701f501f401e3020501f801f10208020301f601eb020301fa01e301e801f401f001e30202021001f301ed01df021d01ec01f7020101fe02230204020401d501ec01fe02060205021601e401f201e501f201f101ef01f701ea01ed02130211021701f201ed01e9020301f901fe0218021701f401f702090208020601ed01f201f901fc01fd021f01fb020b01fc020d01f601f301e101ec01f001f301f3020902060201020201fb020c01fc020301e9023601ea01ff0203022101e801e801f901e901f301f9022501ea01d901e701d901f4020001f1021201ed01de01df01fd01fc01f201f501e601ff01fb01fc01f101d901f5020001dd01ea01db01da01f5),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c6),
    .ADAPTATION_DURATION(16'h1415)
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
    .KERNEL_WEIGHTS(131072'hf60202040500f8fbf50503fa00f9071dee06fdf9fdfffdff0cfbfb0102ff01fdf3f5fbfbf8fafdfc0008f902000000f00bfbfefcf7faf8000cfafafe02f5fefe0bfb02090bfafdee0204fe0304eafdfbfcfe03ff07fb05fbf2f70904f4f409f908fdf1eeeaf8fefbeffff4f9f80c04fdfef6fef80e16fdf6fdfcfc08f5fef6fdf102fcf8fafc05f10101030217fe0cfff1fefef6edfe030efaecf7030405fff8ec0dfcf11c0000f6fa0af5000012ff040e0b0d00f6fef705050c02070d1bfefffa02f003e8ff02f308f7ebe60af6f3fb0eff0401ff05040216f7f8020d0300f3f80bf81bf4021202f0030df5f50c0100fcf7fa0502f5fcf2f3e9eeeff6030e040005f9fcfef405f4f6fbf603fd09fa09f603f6f4020000fdf60d000203f2f4ff0af601f9f90bfdfcfffdf00300f7fcfe050f050403fff1ff03f6070306f50101f602060300040301fa04fff6fe03fffd16fa04fd0602fbfdf600f5fdfbdb05fc07eff4f3fdfcf9eef40300f6f308080f060403f9f31500f8fef50af8f505fcf70202e902f400f0060907f6ea06f90bfde3fef904fa02f3fb050504fd0308fb02fa00e509fbff05f700f6f40403fd03f900f201050bff00fc1103030005060204fe0700fdedf500fc01edad0501eaef06f8fa04fe02f603f4f9e5f9feeff2ff08f711fdf8eceb01fb09f3fefc02fa0004fbebf9fcfef903fb020c0a06fe040efaf3fa0dfe03fef514fefdf8f109f1eb0ff7f7fcfaf2020d05e1edf2f1f9110b04fcfee80cf505fff4fbfaf603fdfc00f613fffcfeeff700ff001df804f8eef6fbfbfe0d1b09f3fe09f802d7fddeef0005e90bf30320f500f50605fefffef6f5030a01f207eb0efaf7d603e907f7fb02f6f4fcfe02050001ff04030a04f7ebef01f203fcfef80006eff702effffff9fef602fdfd00f7fcfdfbff07fefbf9060000fff6fdf6f604000002fbf6fd00fb03fcfcfffd01fd0102fff1000002fdfa03fdf8f9f80102ffff03fffffd01f8f8f90004060403e80207f7fa0cfa00fbf9f9faf6fafdef07f200fb03faf800fefefc03fe07faf600f703ff00f7faf4fd05faff0007f0fdfe02fbfef901fd0b00f7fb0604fcfffbf800f9fef6f801f506f5fbff03f2fcf7f60cfe0201fdf7fffcf900ff04050000f9fdfc00030402020a0aff00ef070303ff0001fbfcfbfffe0200f4020c02ff00fe01fef1ecfbfe01fcef08ff01f5f9f305fa01f1faff01faee04fd0af3fc0bf5fe0902fffe0005fafdf5f0020204f9fa07fd03020b00ff00fff6f9f6f800fe0002ff03fcf9f303fb060afbff04ebed11f40ef6fb01f7f907fdf404f80611fdfd02fce80103fd0502060e0701f90004fdf90b00f6040ffef603fb070309fdfffa0efefaeef80708ff00eaf3020808f3f700fe01fdfcfb04f8001106f7f70407f3fd100002f9ed0206fcf9f7fef3fbeefb06ff06eaf209f505fdf1f2f40bfef8ff0003e8f80301000409ecf8000de2f7ebf806f700fdf9f4000701fafffcfcfafaf1fc050102fdfe0600fcf107f4f6fefd04f8f605fef704f60fe7ff03150001020505fe0301feeffbedf921010fececf11cee03f9f1fafb00f21601f5f8ebf9110d06fafe08f10003fbf1e502eff4010df004ed1cfe03e9f3020507f3e501051a09fefe03ff05faff0816fc05f5e9e41dfd08f5fcfbfff1f00904f6fd07f801fa0afefb0511f0fafff50904fd01f9fe00eff7fafaf607e5fbf2def0f6e9f9fe0311fd0eea00f6fb06eef5daf6ee0af4f9ebef0207f6f902f502e70700f8f2fd00fdff01f6f9fbfa17f4120004eff6eff90dfaf70aea00ecf6ff0009fbe109ff0300ff01f70ff3fc0803faf400f8ecfafbfc01f60206feffeefd01f3000802fb04f3fbf7ff12f904f8050c01fe07f504050405fef402f0f30204f00107ec0a02f607f6fef604ff0402e8e906fd0cf5eafaebf90404f615f8f0fb01f8faededfa00030efefb03f7f0fdf9f2e8f60dfdfefbfbff030103ffeb13fcf5f30202f8fffb03fb01fdf4f7fef8fcf905fcf8f7fdfaf8000200fbfdfc0102f8f4f7fe0300fc00ffef0005fe00fffcfff6fcf4f9000104f4fc06fbfbfdfaf40ef402fc0002fcf5fa020600fe0003ff07fdfef8f8ebf31dfa02f4f3ff0503fc080106fa01f4effdffff0700fa0ef700fcf8fd00fd03eaedf9e319fdfc05001afc02fb01ea020b00f5ee02d9e4f1010505fafbff35ede520f3f4f8fcf6e7f4ff03f6ecfbf203f7fcf9f506fe0ef6f300f3f7fdfbfb111dfcf909170602bb27e4eef9fd1f01f9f6fd0115dd0deb0b042608e9f605f8f301d10909ece4fcfb0105fbf3f7fee8fdefebf60208f2e6e1e1edf8fff000fcfe02e6fefce80300edf2faf4e003eaff0d19ee04f00d001802f60504f8fdfdd4fef2fbff0104fa02f4e7fef80c0ef9f6fef815fa0206f9ec00fbfcfb0302f701ed000402fc0bf9e0f8dff0f00f00fef6fefd16ff06f7fc09ecfd01f2f6f80b000329fcfcfcfe05ff080900e7fc09f90ded0800db01050619fa0d040806fff6fb00f6f8fef5f1ff0bdd020a14ff010200fc01f8fbf4fceb070306f90109fb001ef7fd040a08f6f507f2f50007f0f8f4f1effbf9fe02fcf908fb010ffd06fb00fc0403faf9fbf8f8f5d5fefee6f7fe0300feff01fffefc11f300fd260108f107f9ed10e60801fcef03f002e904ff05efe2fef702f206fcf801f80bfb07f202fcf8f6fffffc03effdfff8f9fff6fd09f301fef7fbffe2030c06fa01fcfafcfbf6f1fbe6fe0af102f9fc06fcfa02f608fc0007fcf2fbec0112fbfc02fd02ff03f801f30002f9050d03e604f7f6e8fbfd000506f906010403f4fdfefee8f400fa0af4f4fdf3f8fcf501fefb07eafdfa00fe00f9010209fd01fff3f804fef5f2021301f6faf0faf601fbfd030503ffe7f027fff9f8f0fc0003ee04fa030ef001f90015030509f4fffafe02f80708fc02fbf6fd03f9ffff02fff701000804fefa08effefe0802fe00070216f3f1f520fef91704ff00f10403fb09000ffb201be706f3faf1ff090500eae5071017f501ff0efe0e14fbe304000211f0faf8ff000d0ced05fbf6fcfaf7f7f504e90509fbf2f9f9f9fff7f7fc04f9ddf9fbf40206fef9fcfff2f5fb00f6fcfaffe9d90cf8ff0603fef20c02fef0fff0fbfb05fcdc01fcf407f905f0ff0600fffed0f5deddfe06f00b040105fbf9fcfc0202fc0103ee0108fdfbede110fdfdc80ee5fafee406fafef404fae8f8faf9fe04f302f5eaeaf5f4faf6f6fb01f9e9fdfeedfa04fffbf6fbfffdfbf7fef500f6f305fb02f5f9fdf9eff7f3fe06f5ff02fbf3fc03fcf402fe06ff03fefffefb0afbfe0102fcfafde7f8fbfef4fffdfbfaf2fbf8ecebfcfa09fafefe09f4fafaf2f4fafee4d8fcfd0bf7edffe6fffefefafa01f3faf9f9f8faf7f6f9090003fd04f205f4f9f802fd0502ff0b1e08f03a1cfef9f808f6f811de03080bfe01100602f5fffdf4fa10f7fc12fd1cf8ef0503fcfcf10ef703f7011f01fe0a02feec030bf9f70afcdbfe00ff07fe13f602fef4090eeb01f9e9fef4effa05fc22faf6f904f2f2ff06e1e9080bfe0002e8f7ff0406fa0410fa0cef02f10afc1217fc02040809050af904f6fc2c0506fafcf9fe0ff403fb0606fe040004fd06fefd0103f80a0506f3f70307fc0fec18e6f20e0303fc0a140b0d01f2f2fb0408faecf8ec030dfafb050cf9fa04f806fb0fedeff905fd0ffefbe9f9f2f72910fdfef307fd02f9f10afddeec0df7fd0cde01f8f6f6ea09fd0d12040e1009fce8ff08f10efde9fff7fffff11bf103f4f3fdfb1001fd16f502e3fcfefefff7dbfbfd02f50001fcfaedfffcff01fef7f900e908f80107f9f5f109f202fc02f909f909fdf502f6040b00f7f9fdfafcff0df50403eff100f9f804e007f7d004fdedf606f9f4fc08fd07f8faf7dbe6f402ffefe9fcd7f50505f1020efd01e9f400e8f001080202020401ebf201f60af6000c0403ff0c0209e80601061bf9fdfe030004fd13fb05fff8faed06fffde006f40405eaf8f616f7fcfb00f10900f90d08fafefafefbfffbfe1700fd0204040200fc0505fd04fffcfef90a0004ffeffafe0c0503fd0303fff6f5fffe0400ea0f03f9f3f0e20be6f8fefbffef0cfcfdf10af9f702f40626040200ebfff0faf2f2fbfaf7fdfc08fff5130c03d1e7fafd0df4ebf50408fefc0301fa01f5f9020300ff0300fb12f203fcfaf506fb00fd05fe00f90203f3edfff6011c00fbfa0404fc06f2fafdff0af6f9e9020be8f5fbde05fede0700fbff03fcebfceeedffe2ddfeff11f4e4fef4ff03eff900f8fcf60cf0faf7fa0c02f30604f908eef404ed09e8fbf907fa0104ff01f5ef01f60e04fbff06f6fbfd0503fffefe00f603fb04f4f7fd03e903fcf3fffffffefb0801fbf9f8fbfbfa02fdf8fbfe0408fe0501060b01fdfd01fc0500f9ff05fcf1fcf2fa04fe0006020002f8fff5f7f9f70204eff0f5f8fffbf7fbfb01fcf801ff0bf0020e0501fef706f8fffefef5080a03fa00fefdfd0401f4fe0a06ffc9ea04fffdef00fbe9f2020104f8fff1fa0d0600f805e1faff06f410ef0e1005faff04fdf2fcf6fc0bfffefcf6ff000101f6100606faf50702f2f8ecff03f9fafc03fc05ff0101f905fc08ff01defef8e3fb070e05f101fbf5fe0012f31af9fefbfffff80ffbf7f5fcfffcfbf20b0d020bfdf81406fd03f6f9f306ea03f000f208fc01ede903f80af7e3fc04fef5fdfffd05f904030504f7f9fb04eefeef04ff02fef5f8ddfffa01fafbfd0103fefee80004fc0101fe0904020603ff01fff907f9f5fbe2fbf8f3ef01f0f505f3fa0201fef503fafee907e511f600f2f9e8e9fefef10500f90af300f9f50000fefaf2fdfcfef60404fef6f8faf50707fdfaeff0170905f8f7fdf6f8faf3f3fe08fbfe0801ed0bfefc041007fa09f602fcfdfd05f8fc04fce4f9f5fcfd02ee01fc0803fbfbfae9f7fa06f8050208fdfc05f2fd01f800fef408fdeffefffefff9fe03f80507ef08fc01fc0a07f6fb00040dfa0205fafe08f00505fff702fcf6040af3fa03fbf504fbf6f6edfd00f201fdf90101fef6fd03f2fa03010008fcff02f8f9fbf602fafb00fc04fffafff1f7f8fcf907fbfcfafcf8fe000005fa040001fef7fef9fd06fc00ffff0301fcfafffa00030af9fdfcf7fdf6fdf3f9fbfffefbf909fa0004f7fcf401f1fdf9fe08fbf7f8f3fa0204fc0303fef5fffffafcf3ff000207000001f2f101fbf3fafb0106f6f9ff0506effbfefa0502fcfd09fdfcfdf8f6000003fbfe04fa09ee080205e1fbfbfc08f40304f50c0400f5f901fe08fbfcf3ff03020205fbff0509fbfef60701fdfdf701fe00f1000e02f4fe02f90306fcfef9faf0f4fb1304fcdef804f9fcfff116f500fd0501f6fff4fb0805fc03f5fe0503fcfdfb0a0b0f00f3e7fb140207fbf40105fd0005ff0ef8fafffffffd02080c02fbfdf8f201f803f5fe00fa0008fcf908f3fbfaffef05fdff1200040500fcf40201ffe8fe030705fd00fcf70ff4fdf7000109fefcfa0c0b03fdff00030402fffdfbeff1fe1404fdf3f9fef2f7fde811eefbf5fbfcf606f1fa0802fd0707f2031d000001f3ff1001fff4fde8f7040001fefc0a1401f5f60cfd0117f4fdfb0ffdfdeefeff130301fd0cf7ffeefee10af4fb0103fafbfefa03ff0bf8f8f9fdf9effdeb030904f7fcfc06fdfe09e90201fa0d0503fcfff40afcf6f9faec0205fa1ef803f900fe0cfff6e500fa09e7f0f7ee05fb01000a08f9f6000101f3f103fdfbf3010003fd04fcf90f030201fffd0208fbfdecf0fde806f9fcf1060b0002ff0d01f10209f9fffc04ecf901fefd04f4fe1004fb03fbfc05fff9ff060a0b0104fc02f6fcf3f8000001fff8fceceaf7fefb01020102fa04fdff02fe0312040201f0fa00f7faff05fef0f4f404f9f9f8ec0cfa01f50504f0fdf60019fb000806f50e0ffefc03f50407fbfefbfbfd0510020101ff0e0efc03ff0a00e70806f9070c07090a19e6f600030919040108fdf90300fcfcfefdf6f8fb04fcfaf7fe01060109040501ff01fe03fbf70305fcfd090a0afbfd1e05f9d805e2080006f6f7090217fe09f70efbfdfcffff0116eb010c01ff0d06ffc8f2ec06ffe6fff80307f90402ecfeff1810ff0404f5e9fafffcfefe0209f5000606fbee0204fbfee7ff06f7fcf9f90bfef9faf3fc0706fdf7f4f0f1fe03f6f70000faf90208f4f30705fc01f400eb02f00bfe0104f6f90317f8fcf6ee030f0102fde702fde9fd02f000080104fb09080a05fffcf7eff8f909f7f7f9f800fdf6ee14f903f00509fcfcf9fc01000402fa0202fcfffe03f503ff0000fc01fb03f6fa00070dfcfe070902fe0003fd04f2fee8fcfa0208f5f204edeceefe0509ee01f8f2fe01fcf8faf8fe08fff4ff01f1fc0dfd0701fffefd01fb0104f901000001fef8fbfef802fd020f040600fc06fe04fe02e803fce106f80509f408fcfd00f5f8ff0aee01020302fbe6ef00fc08fffafcf90beffbf7f4fbf0f7e7fd090402e8fb04eb0508f7f5f904fb04f7f7fef5fa00f2fff309fefbfdedfdedfaf8fd07f9fdfde6f601010df8f6fcfb02f203e00404eefcfd0214f9fc01f3f6f8fafb02f5fd02f3f106e4f4f8eb0dfbfe0c01f9fbfd03ecfef1eefafc0bf4e5f9e4edfcf9f312fafff4fdf7faf0f906ec04f6fbfefafa08fbfb01e5f100fe07fc0a09f10106fa040bf4eee1f7ff0101fffb01f118f50a09f60b12fcfafffd0618fdfef0ff0602f9f7f9f90b0609000701020805020300fe03f7fa00fc0a01090400f9fd2a0a0ed903f10e12040bf9fbff05fb1102edf9f7fef102f20609fc121bef020cf0e1f3060307e50305fa050207f300ff082208042afffdf50904fbf00c090004e4fdfb09f704fce8f4de02fcfbf802e8fb02faff0505f9fb00fff304f8f4f7ee0204ff01eaf80400fc0504fe00f9f9f0020cf8030602010301eaf6f0fdf6f7fffdfff9fa020be812020d070bf900f90a00eefffcfce2d303fc01f6fefeecff02ef09f808e808f3f5fe0cf4edf604fe0105fbf8fe0805f6f6f3fdf4f1fe0700fef902fe09e904effdf4cdf9f90dff04db0102fd04fd02050101fafcf306e60104f9faeefaccff0105fa00020502fb03fa05fdf3f705fc0702fc13f4fb00ecf607f4fbfcdcef06f6fcffedfa0204fdfc07f9f4fbfdfee8e8fcff0e10fdfcf4fafa0006fefef70ef2fefef4f6f7f70ae003f90003f9fc030209fde3fbf606f9fdf0e802ffe4de0afbe4fcbdf50508f6ffe60de5fefbf80102f702fbeeeff0f402f9f1020eecd4fc00f8faf9fa0809f9fdf2fdfbfef6ff04eb09fdfa00f8010103feeffcf5ddeef7c9f9f9ebf20ffefaf60a05fcf90b04dfe6f00300f6f9e9e0f3f9f5ebfff5fd0dee01f7f7fbfe0202e802f603f4f407fafef5f4fd04f6fc020907f3fa09f7f600fff7faf9f9fefff7fc18f7fef202fefde9fc00fbf1f7fbf903f2fa0505fc0201fffe020400fafafdfbf9fdf60402fd00f30500090501070405070ffcfcff000e03fdfd070407faea06fe05f5070804faf60404f4edf8f806f3f9fff80307fc07f9fc010bf4fbf2fb0e02fbfcf604fcfff1f8fdf0fef003fa00f90c0802faf4fcf609f8d601fe01ef0aef0001ed06ff0a00fffdf905ec040600000602fbfbf50209fcfffdf406080003f5fc00fffb03f7f700fe05fdfc06fef5fffcf9fcebf9fff9f6feecf709fd08f6fff7f5f3f601e6f4f10ded0100f7eef5f8fdfc01edfc11eef9faf7faf508fffa00fb01fefe0601f9faf6fefefcfc03fefef70100f60100f9f7010000fffbffff00fdfdfbfeff01fb0300fd01fafe0008fafefefcf904fffff3fd0201fc00fe01ff010501fd000304fe03ff02fb0101fdfffcff02fefefc00fc00050300ff0001fc02f3fcfa02fafdfdfd0101f801fffbfefe01fefffff4ff04fcfffdfafd13fe01fafcfaf8fcfcfcf9fdfc0b0402f20201dcfefbeb15f6ef03e5e7f4000bfcf9f9fe0406fe040af401fd0fde18e2fa000607fefe01f3ff000e0c010001010dfff5fbe103fd04fee900030019f503f0f7f5f408eb02f4edeb01feed090500e9fdfae90610fb0405f9f7ffe30f16ec180a01fc0800fa0d00ebfe0e0b12fa14ecf6020b07100901fcef0704e9f4eefffaf7fae5f6fefaf2070ee906f400fc00f1f8df00ef210402f8f900fbfd0011fefa0502fdfdfe03d5fcfb04fa00f5f603fffc05fe0801fcfd00eb04f6e9f20303f508fbf605f7bffbe5d9faf2e8f6f90901fa12f20405fc03e403ecf6eaf7f50bcdfcf900f1f6f3f113e301030becfd0ff0e1f80408f2e206fa090602fefff1ff04fff8fc0804fafbfaf404fafdfb01f51205fc05fcf1fffc03f3fefdf304f10407f5f1020302f8030305f6fefc01fbf806fff304fe01fefe04fcf8fcfdfc07fefb0203f8fc0cfdee01ee11fd0f0efb020a0504ecfcf40afafbef00ff0cf7ee0ceb07fcfefc0203f6fa05ff07f8fef2f61302fdf6fbfd0e06ff09f90204fe05f9fffcfceffc05f10f040af7fd04fefff2f2fefcfbfef408fe01fdfaffec04faff0d1001fbf6f4f1f50506f804fb00fa05fbfdfffcfef5ff060902020405faf903f6fe040801f6fdeafefff1ff0f0efe04f6fffb0e02f9f7000b01f901eefff60cf3ff0003fc0410fdfa0f0705f3e9f8faeafefdfafbf3f8f6f9f5f7fa06060107f9010319fffe020205fce9fae903090610fdfa14fc0afa0afd0800f705fa1bf8e1fcf9fbfcfa00d7ffff0002fffafd0718000f0506f4060703f5fc0002f008030604021807f6cdf9e9f10407ea05fe04070c06f716f8e4010303ed09f5010e14fa19fe05ede9f30510e8fbfffffc030bf2e903010b0df9f2f8fd0609f701f100f90703edfd01fe09f60300f804fefc09fcfafe00fc05fbf902f706fc08f4faeffd0df7fd07fdf70306fd060300f601fdf70201ffe9fe0603010501fef902f20401fafa0afbfe0408fafcf0fded06fc06ecfd01eaef181404f5f802f9f0f718e40ff4feeefaf7fffcf8fe0b01001614fafb03020100f30a0a0102e502f30be8fff6fef80500ff07000af7f207e7f900060505fc13f6030909fcf5fefa0df509f0f503f7fafff9e6e10300ebfdfffbfdfafc0701fb000bf6fc03e503feedf90e0bf8fc060a02edc8faebf1ef01e905fe0607fcfbf307fff702ff02ee07f0fe0309f10302fce0f2f3fe08e6fcf5faf1f1f5f0e4fefefef5f5fdf8fa0701ec02fd0002f2f304fc01f3e80602e9ffe2fffd0a0e00e807f00c02ff03f9f50100f508fef40700fffe00f5d4fbf7f802f5f8f2060c04f6fdf6fb0302f6effb0108f6f9fafcfdfbfb03f3d0fbebe60802eafbfe000400fff008f0f6fd0109f0feefff0104ec03fdfef4feeefd0ae8f00702e4fefdf7e900fafafbfff8fbf41404f8ff09fd04fb02f70004f901020201fd00fffd01fb04fefb06f301fdfbfc03fef0f9fcfcfc02fffffd04ee01ff01fffefcfc0301f500f40008fa00ff040a02040201f90000f503f9fdfefdffffecfb00f90b01fc00fbff02f5fcf503f4effffffefaf304eef401fafa0600fdf4fdfafbfbfa00f803f703f7fbf7fa05fdf6f5fce3f7110116f7fc211300e6d901f7ee29c303f7fa0f09edf702f5fe0306f3e9f8ecf9eb110bfcf6f40005f109f6fbf0fd0d0ff2f6f7f5e20413e8fef9fd0afc0302000205eefcf906000bf0fe06f609fa00010a022105f2eefffc10fcece7f0fd10090612dff808f906fbeb0cf903fc04ecf9ff04ff0dfcf2fcedec16f1f9f7ff04f006fe070800ddf6ff09fdf8fbf5fa00fef300f802f5f90f0afeff02f2fcff0efffbf0fe15e9fffc03f405f6f505020410fbfbf102ff030a01050203fa03fdf00c010705000211fefb140003f400fbef050702ed0402f2ea0e0a0003f5fc02f1f2f2db15e2f1fa07ffecf1f20bf405fd0b09080b1f0206f800fdfcfe0cdcfc04ff05f50202fb1206fd0402f1f4eefb0301feff02fce60cf3fc0ef6071000fef808f31204f3effc0308fbf90404ff0302fcfe02fcfa0a0508ef0004fefaf900fefefd01f708002f0006d7f8e614220304f7fefd0b0410f40403fb00f60cf50315f40220f80904f5def6fff908daf1040313fd0501f003fa1100002af6eef7ff04ff070109fcfff80efd01040005e909f8000602f80d08f6e1fffefd0304ff07f6cdfbf9030005fef8ffe7f5fffafd0603070108fc01f50108f104fc00f90304fc03f41b06fa0705f7f8e4fff0faf80c090bfb0600fefefff8f9f9fdf8f8f70404f9f008eef0fef9dbfdf603f9fa0808fd0206fcfbf3f8050afc0de8feeff60701f70300f7fbfbf6eb0003e5fd062001e70002fdf8fdd1030f0e0000fe11f8fc02fc0dfaf20807f600ef14e8f2f6f50701fd0606fb05f6070d18fef905dafb05fd040204fcf205fdf5ecf40cfbffecff05000201f4fb0008fcfb05f7f2010e04fd16effaf8fd01060bffe408edf4ecf7f801080cf6f6fbfb0604f40efb0bfaf1e70bf2fef403f5f109fffcf910fd02f9fcf604f806fc0001eaeefafc06ec04f6fa0ff0fb15f9fcfe01f2f5defa07fefc000201fbfc05f9fd0209fa060d0806ffed03fc090c10fa05fcfbf2edfaff00fc03fafefdfff903fb09fefffe0b070cf9fc02fc26f3151300f7fa0e02f509f6fbf9fcf90ae7d8feefeefaf2f6f20d1201ec0501fdf0fbfdfcfa00ef00fc0701f30000020bf604f3050302ff0500f8000204ee0deff6040afd0206fe00f9f8f40801f8fcfdfb05fc03f800050100f2fd04fafcfb0600ff0102fdfbfcf3ef00f9feef03fbfff0fc0df50509fa03f4fdfbfafef4faf105f800fff809f5f8fffef705fa08fa02f7f500f8fbfd0513fafa00ffea0106f60c0604020304efea06f8010df20500faf2feebfdfa0504fdfd040102f8fdebeef0f700fdfef3f9effa00eef400f002feef02f80310fd03020108f9fe0a02f004fe0dfffefaef05e40de0f102fbfd00fcfb00f9f6f8feeafaf0f205f2f1ef0210e6f6fe0c0109fffeeefb00f1fb07ecf8f1f4ffeff2f8ec090216f4fef702fcfe0001f6f2fc00f3ef0505f4f5fdfefef60400fafdf9fafcfcfefc03fa05f9f004f7fcfff9f901f6ff00fdf2fcfa0afc00f2fffc020b00fc0201ff01fefdfaf908fcfc00f401f5fbf6faef0303ef0a00fcf900fff8f9f7f002fbea06f900f2f102f5fefaf905fcf305e80b03fafff9fffe06f506fefef1f003f801f8f5fa00fffbfbf6fdf80206fdeb23ff010be405010804fadcfd022afc00f622eaf8e30fe90afff50602f90af2e4fb09060a06ff0305fd04e9fdf8f9f802fc11f60305fd11020820faf9fef0ebf907e4ff0701fdf7021a050f241cedfd0511fb04f70903f2f4f50e070cfffcfdfcfaeff3faf600080d08e605fb09faf40ff60509f9f0fff5fcfd06f302f7fcfdf4fef0f902c8070404efffe009eff5f602fc00ee00fcf6faf3fa0304090103e3e0fcfef6fb04f5fa040402f403f9ebfd02fdf503ff0ff4fbfe02f305fbfdf0e0fafbedfffdf10bfa0703f6f904f50109f7e9ebea10f0f4f9f3f5ea0302e410e5fb15eef3f9f9f9f604feef07fd0402f90303f8ebfcecfc010010040700f403f60a010e0307f100fbfff800f5060e0102fcfffa01fff2f4f40105fd0d020408060800ffe6ff14f6ff04f8fde8ff18f50aff000efb0719fffb08fafef8f804efef05fbf5fafbf90100fa02040209fafd0c02e5e20ffffe04ffeaedf800fff10ef50cf70703f000f10200fe06f8f0faf7fafef901f9030e04fcfd02f604f0fcfffd0ef701f90310f900f8fffd11000af901f7fdf8fcf8faf5fcfff610f2f7fdf6060804fafbf408fffb04f8fbf202fc020003fd05f803f903050101f3f807fcfe0b05fd0404001403fbfdf101fdf7e3040302f2eb0608f404ecf614e9fcf81bfbf606ec09fd0dfb0a0af9fd0902fa00f905fcfb09ecfaf6fae7f9e5010104fbf9effc07feebfb0cf301fd0504000ff2fbfc06fef605f6f9171bfe030005fcf8fd00e501f0f91302f402030ffa0efcf50d030401f400f9fa01f50b0404f20207f2c3f3ee02fd02f3ff0500fbfd0fee1b10ebfaff08fb08f8f0fe0fee0a05f2e708fa0402eef9fb0005f7f1ede502f400f1fa00f6f90d06f1fb1206ec06f7fbf902fa0301041afae8fe06090304e40b15040101040bf4ff07060dfef3080d03fcf213cefb06f203f8f701fd02000e02fb14fafb0106fbfd1afdf2020b0f020905e4f808eaf40104f703ff040bfd0c030e04160000040404faf5060ef4f81006fc0805000dfefef401f9090d05e801ff0017f0ff03f4ff03fb00f5f807fffefafafef7f900f90000ef06fffbf903ffffff02ff00fdfcfbfdf3eefdeeff0bfd02fcf9fffdfdfff5fc00ff03fff9fefffe0503fbfffbffff0001fcfd0606feff08fdf9fd02f9e8f2ff010b01f9f9fcfb02f0f9fffeecf601fd04faf7f7f6fb000602fbf7fff00401fcfbfdfdf80201fcfc01eeef03fcfcfcfbeafcf805ff03f5def9f701fb04fae004c505010ff8f7dd12f9030d07fd05f1fb11e5f4faf906fe1702fbf3d0fe00f6fcfdfcfd03fbfd1bfa11ff02f600f0fa09fc01fa0be61dfe0207e4c5f4ebf3fa09f5f7fc0af6f9fc06fd07f7fbdbeb080ffef80e10ef0efc0efa04e6050fdef3fa03ed010700dcf9fd0a11f9f806f3fc0bfbf81c0c01ff0502fcff06f7fef5ec0fbdff060400f9d2fff7f9fc0401f7f80713f104e6effffbfe0df6eccafcfefb0213f7f8fb09ff0102f1f2fa000009fc0317edfefd0503050303f9db0000e304fce0050505f3f9060cf4030704f3fde702fe05010eebf8fb010b0b01f112f5ef04fbf9edfffcd703fd0a00f400faf80a01f6020bfbfdfe0702f9fef5f3fef707fdfa04ff01f601f309fdf600fdfaf4fe04fe000203fcfffc020002f6fafc03f711fe08ff010501f101f100fd02fc04fcff0e03f7fbf603040afff8f709f705f7fbf90800faf8fc04fff00f0403f7ff02f805f6fffaf7f50201050df6eefdf8fa030401040af8fb01fb0400031005fbfa02ecef0208fc08ef04fafb02edffedfffcc305010bf3fbf6f702ecfbfcff04fffdfef5edf8fefffe0dfbf3f0e0f900060100fb04fee9fcf906f1edfc000119fdff0202ff06f3fb02fefcfcdf00f6e8fe02e0000406fcfc0903e4f6fc02dee9fa05fb01030adfeefaff000d00f60bf908fcf8ffff00fef0fffafffefef4f80309fc2801faf8ff09070516ffec24f011e8e8130006feea082c03f31a000602e12205041d1c02f7fb03feff0cf4f90ef0040c14fb14fa04030a07fe030d07fefafe01f102041c10feee110af4f6f3e121ddf4f600fa01dd0d0be2ecf3f4011015f306ebf8f8fffb1005f1effbf01b0804f707ef0bedf2e7f2fffd090c0afdfa0cebfc0bf1ef0000f709dff7fde9eeecf6e3fae808fa01f9fcfdfb150604fa0202f3fc13eef7fd010af6000610ff16fcef0c010c1001f9f802f2fd0e08000206fd000403fbfa05f80cf9e603f816ec1ef2fcfe04fd02fb0306efe7dd0602060a0100fb18e6f8ec0dfcf60a01fae30900f4070b0a110afb0b1cfb02020312f5fbfff20500f8f9fbff1004e6f704eaf8f900fff507ff040b01fcf101f70302f4fc0dff03faecf1e8f704f30205fd00f9f5f8f80200f8f901eff9f903fc0e050300f5fdfb00faea0505fbfbfcfe07030afcf1ed0408fd0101e7fd01e6fd1201ffe6f6f9f8f202ffde08ebfef2faf7f202f605010af1150ff1fd08fa0705f00306f2f6f2f800040f010c0cfbfdfd0a02f0fb030411ec03fb0104fdfefbe10909fd04fdf706fcd2ebe1fb10fdfdf406faf701ebf7fb0f0af80208070afefe00fbf50501f8fe0208fd0a0f0a061af7f5fbf5fff804020300fffc1505f5f7f1060503ecc8e9f60e07fa03f7fb0500f20607f9f509fe01fcea04f80f02fff9f1f3fcfdf3e2f0090b1019f6fc0b06010201f8110c04fe00080306f30c03f3ffebfc08fd0f00ee00f8fff7050e1505fefafefa07fdf3ec0601fd08fd0202070506fafcfcff030102fa05fff7fcf60d1bf9f4ee06f526f5071b160002fe0afb011a00f000150af101f8ffee0ee02006f0e50316fb0806080bf3e100e6f2ff04fd04f815f5fdf2fb09fffdf5f6fef5f7ecf701f10212f8fefdfffd00fe01fef70204f900fefe06f8fff60fec030b0b00f90002f8f80201f3f6fcff09fcf5fbf800f602ff050201fc04fbf10a02fef9ffe8f805e606eee706fe0a08fffd14010916f8f809fcfc0617fdfef1e5040105fffcfafc14f2ef03f6f0f9f602f10307fd0406f7fc01f90a04fff0fbf9fefcfdf6e901fcedf0fff60efbdafefa02f8fbfaf9f7fcf9fdff03ff01fee6f5edf002fef7fb07f3dffc01fdeefdf100f6f300fb00fafafa03f91afa0207f903f9f104f9f2fafcd5f6f9d6fefde9f8f705f90702f6fff3fa03eaf4f2fbfaf7f8f8dfea02fef207fcf5fd02fe00f3f1f80501f1fe02f2f9e700fbfefdfe0906faf6f5fafbef0200050614ff02fd000002fd00fa0c06f8f0fe0705fc06f9f907fafb13fb0dfcfcfcf6f40108f9fffaf90bfffd0203020107f8030203f90004fffe030100fffffdfff1fcf8f702031004fd050b0504f704f7fcfd0e0cf2f8f304e80ee81006fff5fb0304f4040efafd01fe0301f5ff04f5f9f7fbfcfe08fadafde40c0601f50ff403eaeffcf5feedc0ff0803f707edfaf9ecfbfdf4e0fff70408e5fcfc04fdf602fce7f40208f7f708f60603eff4fcfe0a070300fcf50509f3fbf70cfaeefa08f4e9ccedf1f0fafbe70407f2f5f3fbfaecf2eef7ede1ed11e6050603eff100f1e8f8f80904f0ef02f5e3f20700f805fcfcf10c0704fdfafcf4faeff803fbf1fdfdfffcef02f9f2fde6fafd09f3fbf404fafafefcf9fdf6f600fafbfa0b0bf9f801f9fded01000af602ff0600f1fced05fdf9f6fcfd1cfa00f6fff8fffefefff70003fe0103ddfcf9f70304fefcf709f5e5fffa04e0e6ebf804f4eefbf8f6f90008fb0afffafa02fefd01f9f10dfd03f402f2f219fe0502fdea0001f303fdf8fd04fefefdfffaddf4ef02fe05fe08f0fdda0404f0fcf60302f6def7f9ea040b00f407e8f1fafe0500fffcea010608fc00f7fa030801f5feff01f4f00efaedf804f305d2f0eefefc01fbfb08fc0e02fef6f0faf302e4e8e9f906f2fdf8ef02fff9db00fc13faed0405fffb070300e7f7fc0508f8f5f7f1e6fafafbeefcf7fb00f1fe01f2edfafbf805e901fa0403fff906efefffef01e1fffb02e4e6eeeb10e6f805f0e311f8fcfa0208010501fbfceb030df404f905f0fb06f50dee01f10909f2f704f8fb05f4f100fbf9fe01f3fefff3e2f6ff0502ddeb00f9ea00e20afb04f50e00fdf5ea020000000608e7fe1e040e02e9f100f4f1e4fdf603050610fbfc070a00fbfb06f2fb0bea0100080a04ef03e8f304f6f914f2fcfdf4f31100fefd02fe03f0edfcfef80b0809f7fe0102f40102f500fe00f605fcfe06fe02f1f00604fa01ddfbfdf20b0bfbfc0bfb0bff04ff07fff503ded3e8ff02fff8fbe504fbfdf8faf6fcfaf5f906f9f504f904f6fffa02f7fbf5f9fefdff1a0f14f00ff40b150afeff0bff04e70c0dfcff03ebfc17ffeffbfdfe08080901eeffff1808ff0b02f4ea050e0efefafefff70003030410000efcffff0205fdfbfa0cf90502ff0120f816e2f6f717fe0b0e01fbfe030f0f0b19fb0100fb0d08fefd04f214f50404f9f6010d1108fa100902fafff705f8fef2100014f300090efa060bfe02f10604f1f205031bf909fbe90ffb04fdf403fafaf701fcfcf7f101fff504fff90c0605fffffe02f905fff5000005fefefffafaffeeee010209fdfd02ffff050900f8fd0405fbf00dfb06f40214fcfd05f80301fafa03f9fb2011fe02f7e5ec00060afdfbf9f908fff60a0204f8ff02f9f8f40100f7ff02eefaf2fafc020af9f8fb0505f3f403fb0700fb0af502fe02f10000fdf8010bfc0201f9f8fe011003ff180906fd01f710f304fd030004020207f9fc0200e8070609f8f1000700fdf2010bf900070ee8eff4f4fae7fd03050103e9fa0b151c0c010312010201e6f3f2fd0b0a08f702f3f8000dfdf6fd02f4fcfaedec0209fbfcfef901f71105f511ff04f9000100fb0bedf5f9fcfefdd5fcfa0beb00ed0d0a16f9fd050bf602f6fd05eee2ff0501030cfbf5f20200140b0d0200fc04fd03e5fdf8f905fa000213fcf004fb000bf7e80905e505efeffff10703fef200fff80607f9010d06f7f9ff0902f6edef01070809fd0105f3f1f3fbff0401f6e50008fd10f800f50e00fe00fffffd03fafbfa01fff304fdf9f7fd09fafcfffcfdf302f9fd00fffd010201f00200f4010bfefdf801fafcfe06f7fefafd0202f9fffcff0000fe03010bfb01fcfb01fff9f70006f908f9f801ecfa010504fdfc05fb0303fe02fa01eafffdff0305f1fefef8fe0500fc01fef700fcfdfef6fcf7080003fe01f1f907fafdfd03f303f5000101f00ef3fdefedfefafbfddffcfe0000fafb01f9fa0b03020206f9f905ea00f102f90001faeafdfefafff904fc04fffafef9fd0801ff03f8fbfe00fef5fe040500fef2f901d500f6efe9f5f20101fd03f804f7f1f90bfa06f70008fef6e7fdf5fc030101f6010700fcfafefff7fff8f9fffc0100ecfa0b00f9f7f90205fcfdf003f0160bfb02170cf50b0b1205051400fc0b05eb00f9fcf9190302ef10e90e07e5fdfa00f7f5f301050d08f70201fbff01fc0208f00705f90afdf6ff0713fb0107fd270205cf05ea1efe02f5fff6fa20030ff51802f504090f03fd1bfdfe14f3200f06dcfeff0409f306f0f813fd05f8e7ff050d051112f70c170f09f51cf0ec0ef10c01fe080306edfe13110104fef000fa12ea190b03071205ff0417e80c0ceff600f306feed0303060606f004ff16f916fd0900fafff2f8fc0603fd090ce7050c3104e6ce09dd221004f204fb030e0c13f41ef4e9fe0f1bea0b06f7fb01f21702efe3fc13f800ed06050615030fe4e0faf61608fb13eff1190fff02f6fc010004f5fc03fdf90006ff06030000fa04ff01f8f9f3fdfb01fbfbfffbff01ff0807f801fdfc07fffbfafeffff030200f5fd0302fdfffafdfe070102ff02fdfe0207fdf10008f7f7ff01f9030800010008fef805f3fafb01fcfa06fd00fef0ed06f8fcfbfafb09f5f5030006f8fd09fa0c1c02fe0200fafcf8f3f400f6fe2d020f00ef2c0607fff702fff124e5ff050702fdfb0001f209fd030af9f9fafdeb13fdfcf9fc0005f812ee0af4fc0b19fdfbfdf90a0310f3fcfc02e9f701f9060cfcf4f6f817fa0708f300de0b03fb0a00042903031114fcfe01efdae5f618eae611f4110010faf90d0bf900fef6f3f8060dfff0fefef7fcedf7f00904fc050301f7fb0508ff04fff61b0b03edf50801fd02f3fefe0906fb0204fafbfeff02fffdf605fc050100f90101fbf7fa02fb0009fc05fe03fd000205fffc03fe02010210010efffe2bfb0aed0fee0c020008fcff03eb030dfcf70000010b080706f0fdf3f704fd02ee0200fafcf904f913f5fbfefdf8fe04020ef5fafefdfafc02eff9eefefffcfbf2f3fefbfa0602fd0deffa01edfb04fc05f9f0fe0500fffcfe0004fdf703030801fcfdeffbfa0af4fff8f901f9fbfafcfeff04fb04030afe00ee01fe00fb0002fefa08fdef05e7ed00010900ff03fc04f910eefdfa0205fcf90afaf402ee0b07f8f7fe08f5ee09ff02fbf0faf2f7fffdfffdf2f907ff050ffbe1fae4fa0310fcf705f8fcebffe5e603dc0101e6effbfafcef23ff04f709fbfeeafaf1e1f803ecfcef0800f2fb03e6f803f6fcf7fafc0afdf005fe04000c02fbf3feecfc12fef816fbf60ef712e6eb04f904fcfbfffaf6fdecfbf0f8d3f808fb19f7f7dbeefeff03ff02fae3fb05f7f1f7fafafffdfa01fb00ece113fbfefcfff5fb0605f3faf5e604fdf1f501fbf7f6d30b010f00faeff6f4f9fcff070af102fef001f8ef02f9f40afef3e10108070208fcfe09f908eb06f2f3f906f9fc09f6f807f70bfafaf7fdfdfcd8faefc40104ebfef904fef7f9ea02f5fe03dcdcf3f6f8f5feeae5f7000101fe02010aea050bf9f70107f8effafcfffdf7f7ff01e8fe01fbf5fd14fb0beffdfdf9f5fffb04fceffdf5fc01faf9f8fbec01f801f0f106f9f8f5f20505ecfbfafbfb03f0fdfb06070902faf9fbf303140800f6f80cfe00fdfe03050e040205f8fdffea040104fe08faffffef02f7f1fdfd03fdf3e3f8f80c01f3f2fdf800fff5f903fbed060401fdebfbf5031100fd00010bfa06fef9fbf9030af9f10ceaf403f9f1ff03f5ecefeaff07fa0cf7eb1be7f308fe0dfcfaf40f0c08e2f7fbf6fdff00f7c700fa130901fc0af90afd0c03fdfa0205f8fafcf80a03fbfc0203fd190900bef2d3f90e040d030101fbff10fc21f601031401fb0f0cf91906e21d0ffae6f8fefb0ee7e8f6fcffec07eee1ff0519f6f9fdfef80f1506f609fcfe06fd0e030400f0fef6e8f8eaff03070cfff203f0f50504f40e02f400e7e00dfbf9ff0102f5f3f3f907050dfdfd01f711050605fcf4fd0803f2f8fcff01f3ff0207031407fdcdf9e60100f9e8fcf808070607f307fdfe060b00f0fdf900040bf40bfdf9d806f80303e00009fbfdfffbebf0f60215f7fe0bf9eee707f803f9fb0e0402f0ff0108f605fcf409d107f70cfefbf500f2010301fbfaeafb12e300f3fcfb02fafe04e9eaf9fb090504fbfcf9090ae0fff3f608fff9fe00fff8faf6fef80805fcf9f9f3fafde205faf1060500fc0504fdf606f801e8e9fdfef4f8f706f7f906fffc0501fffce7f700fffc08fb060c0404fffcf5f6ff060006e2fcfafe15fffbf80a03f6de01f7fd0ee800fd04fcfcee0cfd17f6f8fc0df4feecfee60b0600fefb0006f0fefdf901fa0f0d0200e5ffed000afbfc02fb0d0403f9f4f5ff0404f91001f402eb0ff4f5ffeb0109fd1eff09fcf0edfd01fcecf3fd08f2e5fcf7fb02f80203f9eff6f708f508fc06fc0d03fcfa01fb020ffb0ff4fe08f80003f505ee18fd06eeecfcfafa02dbf80409f9ff0efffbf101f5f9080600ff13e00905f9f80003f30fecfc00f4ef10f20bfbf2f8ec0400f800fef719fdfbfdf5071503edfdf5f7f7d7fafedb0ffff402fef7f201fcf6e0f4e6fdd9e6f304f9fff801e5eb02f5f103e00dfffa0a06ebf5f5f902fb02f0fdf10c01030405fd05fff4fdf70b0afefdfc1319f8fb05f60001fe0aebf80606ebfa020006f300f9fe00f503fbf5ff0003fef000fdf70c02fb05fc0106fb02ffff080100fff500fffa05f7fd08f6fe0cfdf2f700f712f301e8ff02faf2ff00feff110bfe0606f9fcf0f50ef3fe0005ecfa0011fef9fd07fff907020ef1f0fefa07150afa00f9f702fcfc0201fd0800ef0202fd11fbf507fcfffb0000fdfaf40103fdfff704f200fd0fef06f70313fcfefefff703fdfbfffd04fe02fc01faedfcef01010202f3f7feef01fc03f6f9fd08fb00fc09fdfdf4fce903fffbec0202f0f5020301f7eee9f8f5fe12f20bfd00f60100f2fffaf4fc00f7fd09fdee09fb0001f60503fe07f6fee701edfe08fffbf2fbfffdfb04e3160a0f0200f206020ef200fb01fe03eaf8fbf504ebf31114ea02fcf3eb10fbf7da01ff0ef6f6fbf7ecff170dfcff0513f9fdfef9fffdf704faf4fc0101edfc040101220dfdfc12f8f60ffeec0201f4f506ff07fcf400ff0201f5fef507edf0071804effbfdff131603f1f3e407f2e7f3fa02f4fbf8f7fc0107f6f600fb1200f8f9ef04f6fc02f7fb0502f008fbfefffa01fbfb01f9fd050205fe04fbfef800f1080800fdfafc00fafd03ecfffb07f9f1fe05f4fffb0c00fcfbff04ede207ef0df3f9f406fb09e9fb05faf3fcfd050c020102ec01f1fe0ffefbf2f9f7f20a04ebfafafdfcf9f8f0f401f903fe09f301faf2fe08fffef8edfd0ff8fbfe0e20f20cfa0011f80007f5fb08fde9fa050011f71205f8f2e70c10effaf8f8fdfe1010e608f3f105020101f40904fefd01000a07fbfdf1fce1000702fcf4fd090107080a0c03fd02f803eb000409fbec0dfef4e60bfdfa0402fcfffef4f6f0f63007ff0afd0bf3fd10f8ee1f050a050722d2fff607fde2e12ffd04f5e7100208ddfaf6fb23de02fe08fef6f7eaef260a04f70110f0fbf1fff5120b01f1f6070ff602f607e306f1f3f0fcf106dafd0bf8f3f8fbebed020fe4e4fce00103edf3ece505e3ecf0eede0dfc03f1fcedf0f4fbf9f4d6d50f0013f9eef8dafc0608030af8fcf715e9fadefdf3f7020efff4f7e5fcf2eff911f1e804040102fbefe5fafefef6fef8ebf6c000010af304ea0bf5fa03fffe04f101fdf000f9f90609fd04fefbdcfb0604fdffeffe0b0208fbffefff0303f3ff0400030107faf004f70404fccbf6ecdffafdeff305ff0803feedf1f1f8feddf3f0fefe000800d8f00200f2f9f9fe05ee01fdfcebfcf4f0e1fcf70409f6fffef80d04f6fbf7fdf60201f4f5fff600fdfffef306fdfffd0afd0204faf7fe0001f505010100fd01fdfdfbfd00f4ed01faf4f9fbfdfff8f60600f7fcf403f803faf600fff4fffe0302060101fdf3f508f901f401fd070402f90201f0f7fbff00060502faebfe08ef0ffffbf900fdf5fbfbfcfb01f501fc05fef300f4f90015f3f9fbf702fafbf4fc0304f9ecf8ff02f202f0ebffef0201f2fd040103fbf501f6fdf702fdf6f2f0f90408f4fdfaff0302fcfff9f6fa0afefef5fafd020000fd01fc02fa05ffff010000fcfe000001f7fd01fafd070101fe01080000fdf5fafbfdf1ec07fefbf2f3e7fbf203f307f90104e905f40af9f802f2010efff9faf2000bfff0f9fd0602f001fe01f7eced02f806fdfef2fb0c0004f8fc02fbfaf90304fa00f3f90003f50cf2fc11f90306090c04f901fbf7fef5fe02fafcf901ef06ff00fef9fdfcf9f9f106f2f8fb0802020103f6f9ff050005ffffed000de5ef08ffffeefcfbfbeffaf5f30ffa00f405f9fcf8f109060bff0c0df60308fc04f9fc0e00050ae4fa17010df90005fb101307f906fefaf2fc0dfd06fdfcf61809def7fdf7f8071106fdfff810ffff07fafffe01030bf2fdf903ff02f9060105060000f8f909f4f3f6fe05f81904fafc020106bfefee08f60807f6f5030d0900ebea010105000003fe03f0f60cf21605f6c604fe0bf3f40a00f9f6fc04fcff04f30007ffebf7f2ecf70a03f901f7ffffebf4fd0808f503f300fdfd0006fd050402f7f703fe06eb0afd020101edf108fc01fb03f506faf606fe060002fef9fef901f2f3ff00fff7fc03f804f803fafaff11f913faf204f9f4020104fcfdfa02fcf0f20c0dfdf8fff3f709f907dd02f0fe01fd00f807f6fefefdf40bfdf3f4120006fff40702f50becfefdfb17fef9feed150f00f6fb02ff06f8e8fd000100fd04fe0df100fb06110202ebfdf60300f903fcf609f1080000f2fc0cf20b0805fa0a01f6fcfd02fe09f60611060206f2fd04f30df9d6fc03e3fe02ebfcf60201fefa1101f1f2fbd7ef06faf7f6f5f3e2e8010af5100d0702f110f0f8edf6f7fb0bfaf2f200f2fafc0e07fff304fdfb07fc05f4fa0303fafdf6fef2defffa05f607ed08f10502fefaf8fc01f1eef0edfdfb03fb08fff5f3fcf401ff0312ffff01fef70400f5fe0204fefdfd0104f202f403fefafdfdf8fafce4ecf7fdfb04feed00fdf8f6fdfa04fee0f4f810f706f5f2000104fa02fffaf6edfff2021700f904f203fc00fff1f8fe10fefe0af8fd000003f9160dfe0c00f9f7ecf902fd06fe0bfe0914eefdfdfb050111fef500fe14f5ed04f707f8f50004f3160706faf302fe0604fc06f3fe010002f6fe05000107f9fcfa350007e407e00df6fff60309ff14000bf4fa0303fe0302e80200fc0d0ffe10fff6de09fd1e05de00fc050dfa00ebf901fa0afdfe16fefaed05f6fff4fd00fdfd02feffe8fe03fe05010bfafd010bfffffefff5fffc01f0020002f3fffffc09f9fdfffbf902fff9faf3000501fef6fdfb02fffefcff0200fe01fff9f5ff02fcfffbff0600fefffbf405fcfd000001fa0502ffff0afbfdfc01fb03fef9fe11f4f9fbf8fe0004f1040606f90419ef020a02ff03fc0001fcf7f5fe01f5f5fd0c0503ff05ff0208f000030f05f4fbf4f80bf8f1f3ebfcfc0df7fafcfdef000f11fef5fef5fd0514fafdfc02010bfcfd0400f2ff1af3fdfb0112fe020f05f900f3f9fbfcfe06f7eaff0b03061c0a05fdf50bf3f8f4f5fc01fbec12fbf505f9fef7f2f7f6f8070b08ea070c0d01dff90109edfdf5ecf9fbecfbf603f7f102fe01fc030604f8faf7fb05f3daf9f109081f0404fe0cff02fdfd06fc01fb01f50604f201f8020befe8e800fc080005fe06f8fc02fc0508fd0005fe07fef4f3edf50dfffc070209e8e1f2f2f0030beffd00ff09f9fdf6fbffee00f7f6da07f8000719fcfd00f8f5f4f50208d6ee090bfcfbfcf6f600fd08f502fa02fafe06eafaf0fcf1fdf70906fdf1f2faf10f00c30bfc0afa03e8fefdfe12040312ec010becf9eee8fa03090303eddf00060bff02f006ff0407f5fdfbfa0303fa0501ff170cfafef010fb0300faceefefe2f007d7fc05000701ff0bf2f9f2f9e8eeebfd01010aede3f40709ef00fefc0bf1f8040de6fa09fff3f9f0fe02ed01fcf3f804f80307feec03fd0104fe15fbfcfce6f9faf7f90913f8ec15ec0a05f1fbfff4fbf7e9faffef0303fd0300f9f201f20a0303f3faf90405f10601ecff06f2f0faf807f8fa0ef7f902f911f9cafdf00901fef70000061dfd01f8fef8f601e2f4f205f5ff05fff013fcfce2fcf6f20dddef080bf7fe00ffe703080dfbfc04fb05040df90502020b02f2f50100e9f1fc02f20bf0f903fffbfefe0100f8f7040102ff00fdeaf6f4f304030005fa05e80afbfa070efa0006f6fefffd04fdff0007f903fdfcfbf8f900f8fb06fcf6ddf9f1d8fafdf1fe03fdf0f2fbfefbecf8fce7f501fb02f8f4fed8fbfff7f20501fffff2fc03fee6fc0bfdfcfaf801f8eefdf5f4ed00f0040ef6f4f2f4f0f4f7f6fb1cf70dfce7f503ff1702f8fcdaf5f70702e4fcf6fe08fffafdf7fdf404f3eed50101faff0800f505020909fcebf1fa01f5e80101f9f51208010ffc000619c4fee7f6f1041b0408fbfbf7011a1fec12051c05ff07fbfa031fdf2404f3de0307f601ddf1fe00f3ff00fbef03fafe07e404f90a0bfd),
    .CHANNEL_BETAS(2048'h780c7804781577f277377855784478bc789e77b277d8784b77c977d177d0787b77c7775d786d783e781c782a77fa7809787f77f877b3779877c078ca788977eb78eb771e7822782077f0775f78c177da77da77da77c87824781b7795780e783b779077ec779977f67844780877fa77b0784878da77ec781e77e879847842787377ee789f778078337924780b783d778578457881781a7839785e780377cd77c0776d77e87898781a78117829779e77f377ec7821789e77aa77fc786277ca7888785b7826784378da7819778e777078b4786c7778787a786b781778137836786e780b7828786b784d777f77fa77e97845773a78bd77fa77a2783877ba77fc77c9),
    .CHANNEL_THRESHOLDS(2048'h020601fe0214020b021801fd0206020a01f8020e020b01f70206021001fb020701ed02190223020a01f4021f020c02080205020902110218020301fd0210020c0206020c02170215020c02190201021902210210021d020202070212021601f1020b01ff021c02180205021702000217022101fb020301ff020301fc020d0226021801ee020001f6020002100215021e021601ee020002050213020a0215020c01f00220020d022e02030226020301f301f2020702050209020702010201020401f7020301f70216021c021b021f021a0216021a01fe020001fa0201020301fb021b020701ff01fe0205021002130223020801fc02060212021a022302150215),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d6),
    .ADAPTATION_DURATION(16'h138c)
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
    .KERNEL_WEIGHTS(9216'hfcf523e7eb1bfce2f9f4f205f106f2fd06012521ef0110d62c18e5fb10061315fe0b0c0af601f80ffd040d2420f9e0d91cf11c1815f1301c10290608f3fa150ef20c16040dfef7f10a01f40804f10ffbf4f4f8000afef9050d073121222b0e1b100503fa10fb1ff3f62b0b122b07420d231f401d19f5f703e5f51514e4120301f3fdf2fc160e09ee11f9f7f40bf50d030ff0df0df3070f1a15f1fcec19fbf61eeceff9f7e0fefd0008fc16f70f00f8000313ff1e04100de6e613f309ff1f24f2f50fdfff04e30accfbdee50ffee534f4f6fbfcfdf9ebf60efc0a102a0f0d28f3ecff12faedf2fef3fff6f712ed0617fcf11d021b040e110b16f7edf7fa060ee910ff17ff04e308d415f5f90e2112f2e8e9e60df7031d1ae90f12f2ec26eae81bf300f1f7f10309ee0208f20908130f031f0cf9f2f1e9efe11620150cfbee160a050b10221707ff0f060715fb0619f41c251428101e27ff06ef05fee612fed9fcfb01010df00efaeff9f2f700eff6f0ea021a08f4091edc02e5fffc12020c12f5010c0edaeb270be001110c25ff190822f5321d22011912070413e9f61805ece914121f224b2f1af0130c2019f4222812e80d0ff5fd07fd10f705fd080ee305fef41917040009fcfa0df50af4f2f6161b0505f00af61015fe0602fbfd19ffffe7efe2041e0410fafde7ebe31bf9f21419102a09161c11192404020107ecf303170403f403050d0f140b0f1ceeed1b0ce21eff061305fdfa040c0c0b13181a11251bf501fbede81000e4080ded0b0bfb0ee1e2e2f9deeae1ed0afe070c0207fb0720ff080dfeec0100f819fb1deae206f6dcfe1ff3f70a03dc1df6f2ffef1b1c131df4fc13db1306e2fee5f0f7fb08fbed03f3f409e41df5fdff01ec22f402fdeae8e30ff612161ee61cf4f62ae00900ffe303f10f1c05fe46132bec0417fd0408d3f7fb0b01e9e6e213ed1007e10715e9dfdd0a1807f7ed1af3f71129453b101609e9fdf408140b13e4f908edf22006f6e9f8f0e6eef5f6fbf615f716fc10eee30510e9060beb22e8e800edf913f506ecfff204160bfe29172dff1812ed22f81210f7f9260eef1a10111afa0020f8082804de0ff9f01bffe5e0e3161afe0906ddfceed51cf5f214e9ea0915f6faeb06160bfef502edf0f900f9ff192518232e2124fa1131ffedf5df10fa0ddaeeeb09120513000f130a04f3f3e009071617161f0028ebe3260af40df4e4120cfafb0f09f0e80bfdf00f1c0cec04e6100f10172b210febf51a2b28072615221e260303131206f70a1510e80a0aedfaf0e8ec05210e130cee0112f615f8f305111afeff0f01dbeafbfdea0cebf6f7f10a2afb052f1c0c0dfd050919e502e90cefd7e3e2fd0cdb2b170ddee20cfce309eaecf51419f5e215f5f310e9071b05120adf28220a1e060a13f4faf51518fe15291aee1a050505dee61dd90218201f1f16021c0219110c1d2d07e8121006ee0b0c0c05fe100703080ef9fde9f91efde1ebedeef7190e1c1e200316fa151c18e91215101b2108100af22508da13ec00edeef812f607202f10fce9edf1080206eaf2f50a16fffc0cf0ef130b09ed00ec0df804f4f8f4f2ecf8fc211220191518282406111112),
    .CHANNEL_BETAS(2048'h788f778d785477da780777df785c77c3780777b0786278297975787a781a783178487802783a7732787077d478ed783277d677fe7809780977f3780b77b8788d77f7780e78b377c97833786177ea77ef780f78217789785d786277f877e678a7780b77b777e277f7782b786377f678cc77e577d3784c77e0787277b8781d77e07834784b77d17850783a77d977ea77e5784e776077a477f677f1796c7830780377ea7837782c77f878027866786f78537838783477dd782578647849784577f6785a784f783177a4782e7869783a781f77ee77fd777877dd7880785f77fc77ec78387836784c78d877cf78257872787c787b782c77f47819784e7789784c7843),
    .CHANNEL_THRESHOLDS(2048'h01fb01ff01f401dc022601fa01f101fc0207020501e901ef021701f701e001e701f101f401e3021801f601fa01ed01dc01fd01f2020301fa01fc01e301f70203020f01d701f501f101fd01c80223020e01fc01fb020001fc01f2020501f3020901ff01fa0204020601e7020a01ed01d601fa01f201f501ed0201020b023001e4020b01f8020201e6021901de020001f4020e01f301fb01eb01eb01e90215020a020701fb021401ea01e601f5020a020802030205020e01ee01df020501f4021201d8021401fb01ec01da01dc020301e901eb021101fb01fc01fc021101e5020f01ec01f201e90205020801df01d401d301e602010200020301f201f901db01da),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c6),
    .ADAPTATION_DURATION(16'h1414)
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
    .KERNEL_WEIGHTS(131072'hfafe0bf6f9fb06fdf4ff020305fcf40900fe05fb04f7fc00fa01000003fd12fdfbef1e01051702fdfcfefc05f2010509faf30203f60aeefdfb01f604fa0601fd07fb01effdfc04fffcfaf9fb0c0b05fb00f8fbf7fd01fff5fdfa07f5fa08fe09fbfaf8eefff3fffafa00fefd1701fef3fef80905ffee03fdfcfb00000005ecfcf802fa00fa02fc01f9fef2f5090604fcfa00fff9f6f6f101f9fc0002faf9f6f6fdfc03f607f803fdfcf7fbf9f6fdf90003f80efe0004f4f9f6f7f9fbfa04fcfcf50003fffffffc02fffa02ff00f90804ff02fbf9f9fb02050bf70005fef7fdf70013fcf4f203fbf9f90202fdf401f7f7f8f4fdf7f9f101fefdfaf8f7f9fafa130bfe09090000f405fdf80d0ef7f5f7fc00fe0109faf80707030102fd010d0a0404f802fd0c0b010002f1030dfdfe1deefc03fbfbfa0a0a05fb00fbfcfcf8fe0304010301f3fc040aff06f40704f80cfefbfef3fd05f901f0f4f708fc03ef0afff1faf9080102fdf502080afe1402ff0bf9fd0703f506fcf504f40c02f3f902fff0f7f3f9f9fc0ee7fe06e1d9ebf80607f107f4ddfefceaf7eb0204f5edeceff90001f4f0ed01fef5fbfefce3ed01e0f407f8f3fa02f4edf003f3ebfefbea070208fde4f8070501eef2dee4edfdcef8fc0604fe0cdee7ff0005fbfafaf3fc04ecfaf504d7e0f70000f5fbea03ebf9fce30af6030a04eaf005030cd6f4fcfcfd01fcfaf601fffe04fe050cf2ee0c06faf3fefef603f902f6fafafff80104f60609fffdfbe60a080002ff08eff2e7f9e7eff80605f7fc01f20103f9fd03f9f409f80602f8fafc050af8f7f6f7f7fdf006f7000efcfbef05fa0903130201f5fff506e4f5f4e9f4f2f8fbff03e800ff15fffffaf8ea0afffbfbfc05fbe4fefef9f5eefefc0df2f4f9f0f102effdfd00fc09030bf9faf2fefe00feff00fe00f3f500fb03fcfff5ebf906fb010003f5f7fd04edf3fafbfc0005fbfef1f7010503f9ff0cf9f4f900f8fdfeedf8f9f507fafc03fff6f8f8fff7f60107f6f4f0f9fbf6ff03ffeff9ff03fffce9f5faf202eafef804f8fffdebfeeafefcedfffaf4fefaf30dfe03edf90700fafbf6f9e301ffeff0f40cfb0df9fbf40f05fb04faf4fa0d0ff103fbf8f8dd04f9fafc0efb15f40102eaf606f308f70806eff7f50000f607f7ffee0af6f603fbf8e6f70ff503fdf20005fe07f501fdf4f5f1ebeff4fcf6fcf4f409fcf10802f302f6fd010efefaf6f7fcf400f3f7060002f1fdf507faf9fcef0cfc0007ff04f9030af8fcf713f4f5fa07f3031005ffe808fff2fafcfafe0409fb0601fbf72000faf2fe07e902ecf609ebf20ffe0a06020201f702fc03faf802fff403fceef1f6fc01f808f80b01eef306f7f604f9fb0906f1faf9fb03fcfbec08fcf2f2f3fbfd0e08da02f40301fb0301f50610ecff08fc01fcfe0ffbebfe0a0201fbf2f7f5f4f4f3f9fffcf5f3f4fdfffb0003faff0afb0201f9fcf3f505fa05fcea0bfff601fa03fc04fa01f9fbfbf7f5020604f60c07eff5fafbfefa0702fc07fe02f101fef9f9fdfcfefafd04fbfe03f6f001f4fdf2fbfcfbfef9fc03f5ecfef1fe02eefcfff9fdfbf0f3f503fe01f506fafd01fe03fcf5fafcff01f5f6fdf8f103f1f1ff01f3f609ecf4f604fefae6f803effcfad7f9f004f8f8f704fcf802f2f4f7f7f109fb04faf9f5f1fff0e70bfe01fff700e9eef8eff402f7fd01f2fd00f2f60301f8f8f8ecf6f602d4f6070609f703f4fffd04fdf6fcf4f6f4fff1f7fefaece9f20106fdfa03f5fcfb02e20502f5f6fff3f4fbf100cfeefefceef4f600ec00feff0106effbf3eadc0609fdf500f9faf3e8f2fd0300fe0f0109ed0102f1fdf109f5ff0003fcf0f5f1f7f8f9edf1ebf709eaefe1f9fbfd00f7f501f7fc010001080400eb03eeedfd01f3100504fb05fd00fff3f4f5fbf8f5e4f8f5f3ef04f7f0efebf8f5f0f2e101ee0def06fbec05eeff0202f3fa07f8fa04eef3f415fbf9ff0719f603f70100081ff6f0ee11fbf50b07fbfd0b0308fae0fb04fafd0501fb08fdf7fa0005f9fa25eff3f00208fbf6f8f2f10c13fdee1ae50400f5f7fbe302fe0101ef03031008f9fd150801faf6fbfdf0eef604fcfdf01700fcfcfa000efaf6f90301f5f9f70ef5020afffef3e5edf50ff90dfe02ff0307f60009080efefafdf7f1faf9ff04edf81105fd00fcecfcf3fafaea00ecf802f7f7e8020c03faf1f5fefcfc1705fcf9f0ee02f9f4faeef3f900fded0203fdecfcfbf4fc000c0403f40ffdf7f800f7f2eef003fafc0202fe08010300f0fb0505f7f901e608fc06fde6f509fffdf1fff2fcf30bfce905f4fffefce5f90100f5ef06f606f6f9eef60beef1f1fcf0ff08dcf0dff6ff03e1f6fad9edf8e9ffe5fa0d0af8fceff8fbe8e5edf7f20bfb00fbfce5effaf003f4030df5fd01fbd7f8f0e903fcdbfbf6f9f2f0e503fbfdfd00d7f7edf5e2fd0502fdfcfdee01f8fdfefaf7efdb0401f5fb00f7d6e1ed01ff0209ebfdfcfef2df05ef07fdfce9f709f5fddf08fcf4f6f8f900f2fcfbed10fe0102ebf51a03faf80bfef4ee071ad503e6fd0508f511f7effafd0801f50402fd02ee0607ec03ee02fbdd07fd02e5e4fbfdfe12fde00803f6e70e11ed02fcfbe4fc080ce1030d0fff0009f6f0d90ffa01ef0bf7ff05fe09f2fb05f2e4fbedff02fc0505ee020a09fcfff2f509fffe03fa04f2effff9ffed1100fbeaf6f7f8f1ebfffaefeefafbf408f7faf9f7ffeefffe040403f1fae7f3e702ea0cff05f9f8fe02fa0301e2fbf4f1f8f0fa03f1030be8eff4f207f90bfefcfafde2fe020dfd0601f3f20001def7010505fbf9fa0104ececf9f2fae801f6df1309f50ff0eafdf60205f303ec05fc06fdfb02f4fde8faf6f4f706fef7f9f8fa19f8e8f60ef504f7f0ebf81e14f9fcfe1ef4fff111141b070304fdedf701f8fb0b00f31009e0040504f60c18f3e907f4ebfdf0e516f80707f40c09f705f61002ecfe1cf90d0206f7ee1d1207ef24f903f101120a07f10e29fa1a0704f9ecf9cef805fbed021107eefffa10fbfeff09ccf1f9f2f61b0b07f2f00b0df9dffd11fa00f5e1faf60cf3f4ea03dcfafef2f2080903f8e2f701df0ade03030b0103f20106fbf4d9ede9040c03faf3e6d8f3e9eefcf506fd07eedaf7f207f50004e30405ee04fff101f5f8f1fee3f5f2dc0af4f6f3fa08fff50afdfef1070200fefae9fafcfef1c7dbf503f8ea03f9f9f704e8d9fbf1fcfff0ef08f7f2f4ec0becf3edebef0ff7dc13f1030502030608eef903f2fa030318fd0308f80b03fef708061a02f9f100081bf3f7effeea0202eff30ffd0103050aed08fefe0cfaf4faf41202f20cf105eef9f4f9f510e6f9fb14fd051802f7040be9ee0fccf5e40819fdf8031011f2fdfef7010401e7f001f222f6071310e9fbe1fff30ee2fce91bf0fafe1ff4fff5e5ef04f4fef701fcebe0f1fc03fcd304f8f50000f0fef1fc03fd00f5f5fe06feede9f80b08f50507faf4fb08e4f2f70f0403f9f90506f9ef03fffdfdfdf30e03daf00104ff00f4eafff5f0d002fc0e05fe05f3f4fcf0fd0006e6fffd0001fefc03e5e5f2f9fd0404f8fc050505e600eaf40dfef7f7edf4fedffff710fefdfefef601080806fcf104f401f3f3fef802fcff0610fafd02fefdfefef702050102f50afbf80305fcfefff90cf403fcfdf4f9f706f0fdf9f80105010bec0efa02fcfaf6f905f809f4fcfe0efe0203eef7fff0fafef0fbf6f9f1ecfc0cf5f6f904f8fbfefb02ef02f004060401fcfd0806fb02f7fc09faf9f2fdf8fdf7f2f903fcf4fde2f7040910ec0626f8ebfaf801ece409f006f504e1f4f3ecf90de403dde5f4f007e0e6fef10501fdfae31bffcefcf6f3fdfcfafdf6f1ea00fe09fbf1f8f2e2f6f5fc0bfdfbfcfaf906f7edd0e1ff09f9fefe0d02d5d913edf31aecefef1608f108d60afe0302f7f905ededfdf810faec0dfaf7f0f6fa00faedf5fcfbdcf0eef8de070ff012fe010906f4e9f9e7f5fe02ee0efcfb140afaf7f806f1fefcec0efceff004e6f50b01ece808f10113e9fbf4f900f914f6ea0cfbf504f400f9f50503f5f90200f9f700ff050efff10cfbfe04e3fef7f215e2f4f00609f5030007fce5ea0301f305f7da010aff0402f8fbf8eefee80d0505fdf3eb07f7f1f5f202f504fafc06eae9e4f9fdfaf6f8000702f6fbfff3f0ffed0ae7fafdefe9eaf2f006ed06f0f1f3f2f905f4faf6eeffe20ff8ebf208f8fcec00fcf8f7fbe201fa0000fc03f40e0500ffffe400f003e807fc0902f9f4e703f5eb02fcfb02eb0102fe03faf6eaf2fefceff3f7ea020d11ff03f3e4f808fef2f2fdfaf9f4f5f8f6efec09ff08f413ecfa12f5fd0502f7f6f3fffb02091500e9fc03fd05f804f81e0500fa021f0310fef4f900060c07030c0bedfceef10dfefcf7df01160513ea04fb0300fdea00f2f205fbf6eaf407fcfa0101fe08fe00f70412fde2fc0210ef001211fbf803070df0fcfb090507f7f7fe030607fb03f8020e09f8f7f912ff0108000206f4e2e3fbeafb02fceee50fe0edfb120b04fffded05270107f302eaefea17f50203070af809fb0cfcfe11071bf9f9f2ec03000cf70a0fee0afaf806e7050509010f110ef603f0ebf1edfa0af9e60405fdf7f8f6e7f2e9f40a1203faf000e7f60cebe206e6f9fdee15fcf20bf5f9effa09fdf607e8dafcfb000709fef5f70101f302fcf9f9f012f602ffece8f30301feed05f9f2fbf2e7fcf3fd02fbfef1f9fefb0a00f90509fc06fb0202e50105f7f20004fffcf506e8ff0200e90010ed03040007e9f7f7f3f6f70ff7f2ff00eef5fafb05f80000f60002fffbfdf6fbfcf4f003fdf8faf5f7f800f5f7f5fffe04ffeafbf4fc0200edf7ff09f4e8f200fbf9fbf600eaecf908f90001f8def5fe0012fef7fc01e50107f204daf4fcfcf0f9fdf90101eef1e9f1fb0bfcfb00ecf503ecfdf0faf804f7f40417f402fef7edef07fdf803f2f20af800d8f5070602f807fe04fe0afaf8faf005faf304fdf30ff6e4f908fff7d2f1f509f7feff00f8fe08eee4fcf1fceffbf703f7fbffe5f702faf302f6fff8f10200fdfef2fafaf0f402fa00ecfb00f701f2e6faf5f900fff8f7edf8faf4fee900fdfd0204faf7fcf8f5f5f7f8edfbfe05f8fae900f1ec00f70c04f4fcfb02fb000909fbf4f5fc06f5edfcfd00fafffbf109fafcf1fdfc05f2f6f6e3fd0501faecf304fdfbf7fcf7f608fd01f8fcf90205f3f9f9f60af6f4fefcf7f30401eff2fbf6f4eafefceff9f7f9f3f4fa02fb07f9f10effff00f8f1f9f5faf104f7f7e9ea08effafdf8f2fd01eefc14f603fe0202feefef06f606fffcf704fff5fee8f404fcfcfb02fbf307fef5f4030701fe030bf0e7f1f9fc02f700fdf2f205f50405f4ee02f0fb07f9ff0300e70bf604f3f5fd0d1309f30a04fef6fbf70602fdf6fdfdfafa080303fffef7edf6fa0204f70107f3fb0405f8fe0002ebfcf309f2f5f8fff3fdf802ff0600f1ff00f4f8fffb00f9f801eefe0e04fefcf90201fff6e700fff6fa03fcfcf5fcf7eb0900000a00f90e05fef8f8fa0005f4fd02fcfbf8fdfbf5fa04f8f1050700f0fefcf9f4f9fdf9ff02fffcfa000500fcf804fdf106fbf904fbeffef3ffeaebeef5f7f5e403fee60c0ee6fdfffefcedf1f8f1f4ff0df5eaea16ff00fffa03ffe308eded02eef510f3f9eb1604fbf502ed0105f2fd040af00afffff801f408fc07d70a000a0aef01e10b09f00cf7ff04060404e81201fce5f5fff1fcf2060ef70408f3fef00af1f303f6f6f60606e8f3fc09f3ea0605f60707fcf7f7fd02fff800f000ff0202fcf6f7eafe011202f3fbfffef5fcfe09fdf6fd080802ff0c0905f20601f903fcfafd02fbfcf5f1fb0efbfd06030202fdf2f8fffffbf0fe02f7f4fdfe0509fffc0a01fef5fffffdfe07fdfbfcf1f40400f7fdfaf6fc0202fefcfd02ff00fefc0001f801faf5f6ef08fdfff7fbf501010bf6f602f4f7f100faddf3fb06fc000906f905f8fd0103e102feedfedf030403f8f7ffeaf7020b020bfce6f202ff01fbf206fef603f2fafdffe7f9f0eefc01fbfafdef1201f500fff4f502eb090300060201060e0402000305f6fbf4f3f000edf8fee1eb0203fcfaf3e8f9e701e1eefaf0f1f9f4f604fe0df9f616fbfff3f3fcfff8f0fe0100fafff3f1f9e5e8faf8e701fa01f0faef04ee010103f7f201fafdf5f4f005f101060503fbf7f900faf7eef802f7f6fafafaf9f8f8fdfd02fb00fef6f8e705fb01f100e0e9fbfbe701fbfdfcfd000b01f904f3fff9f6f4f8feff08f1f8e3f4ee05f50006f504fef8f4fffff4fffff9fcfdf308f9e6fff8fbf8f9f9fcf9fd15f8fbfd01080c08f8effdf8fdfd160effec0209f20804fffc13050c04e20d0df704fbfd03ddfd12f2fb0cf905effa0aff0feaf90cfef2faf80703fdfd0900f801f2f40bfef0fff501090cfff8f7fdf6f40103ee02ea0112ecf4fe04effffafcf6f7fcf4ddf811fd1706fd00fddefcfaf7f218f1fcf51f01effd09f8f7fcf8f6fafdfefcf600ebfaf401f5fcf4fbfdf8faf7e800fdf500fbfaf4eff500edfcedfbfef7fd00f302f2eefbeff7f4fc00fbf9f7fef4f5fff901f20a02f7f9fbf8fdfd0a03f301ef0500f9f0fdff02f90404f5fcfcedf7f6f603eafafeea04f901ffecf1fbf8fa03f7f9e70cfffffffdfefbfef8f6fcf700faf7fdfbf2f904f4f7f2f404f1f7fdf5da01eef5f3ffeefbf7ee00fee9fcdaf007f5f9e6defe05ebe5e8f3ee07fb03f8fce1e1ffe90407fbfdf2fafae5f4f8f6effdf3e808fff30309ddfe0401fdebfcf1f4e6fafffaf6fbfefbe9f6fff2fd04f4fdea05ebfdf0f8eedcdeef01faf601f4fc03f2f0ea0402fdf2fff604fee104e9fff6f9f6e801fa000006f6fefdfe01fb01efeaf807f90105f6fbebf30104f3fcf2faeb0bf101ed01fcff0006fdffeff7fcf3fc08f4f6fcfefefd0703e40cfafb01f10901fcfafdf8fefbfff602feefe90b06df04f3fa07f7fdf904fefdf2fe00ffef00f5eff8fc0407fbf9fdf9fdfcf60104feffe7fef5fef9fff603faf4fbf50001f7f1efeefcfc03050003e7fe0112e0d7eef8fadafef0f9e6dad9f7edfb0ef700e6e0f4f5fdffdff2e808020500f9ef0ce9d4fcfe0403fae8f405df07ebeef7030c0705f5fdd60a13f4e902f6e7e9f2e4d4ee090b06f8fefdfef2eff6f8f70be8f80300f4f6f6e2f703fbf30902fbf200efe3f414ec020f01fdeef40af5ddeb05e8fd01eefe08fbfaf107ef0600efe6e4faf907d900fde4f2eee6f5ea0404f5eef7f0ee05f6e3f2f8fe01f802fb02f1f008e505fd04fff8f8faebf102f2eb03f5ed08fc04fbeaf7fdfdfdf5fbd7e3f4edbaf30808ff0400f108f5f3fcfcfbfeddfef9e4f8030ae3e1d901f8030af1fdf8f5ebecfe020802faecf101fbf7d5f7f5f7f2f40cfaf8f9fefd090efaef0d0fe8f6010806f70009fbe50f0afb0a011803fde7f50affeb1306f9fef700fbfd16f70518dcf90803fdee000300fb0becf6ff01fcfcfc05f3f10df8f407ef15f800feee0aff01f9ee0003f503f007fc05fef800fd1103fefe09fbde070002fb110e0706fdf2faf605f001fc0efc09050b000000edff06f8fe03fffdfcf7f801f3f3eb00f100f3fef5edf7f7fafaff05fdfcf9fcf8fafffafb06f4fb0cfcfb080405fc0cecf60005f5fafc02fde4fa08f4f6fbe9fafdfdfdda0d0701fbfa05ea00f6f5edfe0e000809fde6010d01030c00fceefdfc04fbf105f7f1fdfb00050bec08f5f2e3e008ebfc03fee3fd020704e6f90ceffcf900fdf0fe05f805fff9f7fbf607fe0001fcfffc0106fdf6fb02fcfa01f9fdf6f2f7f305f9fbfff1fb01fbf90ff5fefefef7f9fc01f804fcf206fdfcfff80dfcfbf600f1fcf8fdfdf8f80004f908f9f4fcfd00fbfcf701fcfbf7fffc04fdfdfa04f6fbfa0200f3fdfafd00fff9fa020bfff8f7f4f7fc0bfefaf9f9fefffcff01fd070400f9ecf7f5f709ece7e4e6ff00edf9fb0c01eaea1d2100fa090df9f402e00001f2f6f61afc07051cfce72c0a0203f414f5f705072214ed0d0100e6f8f10e09ea080efcf10bef0bfce81bf8e8f908fdff0a09fde1e0f10505f002ef07efedf0fcfe08fdf700f60ef6ea0ee1f700f1fd04fdfced1c091beffde706f402fe08fdfff502fbf90e05000500feeffdfe07f105f6f2ebfae9fff5051afdf5fbe5fa00ececef01f20c0bfd00fae008fcdf08060002f30408fdf1f4ffedf9070d09fbfdeff6f6fdfff4fa1fea0afce6fbfc0ffd0210fe02fcf606fefc0cf7e8fd0105ebf9fcebf7f5fefffdfce6f80602f0df01f9fa0cfdedff0002fdf508fdfef1f8f505fd01ff0af1fffaf9e7fae0f2fbfaeefafa0af4eceff9fa07f6ed01fb02f407f016f5f2f616f8fc03f7e8defd01eaf7fefcfdf703ebddf8f7f7fcf80401ff0ff1e5edfff6f0f9fff7f5f7fed2f60300fb0301f900fd0000f9fb15dcf9fff3f80101f7f6edfdfdf2f4ecfdfefe01fffef0fffdf3fcfce9f709f5f6fdfe01f81401dfecf6edecef14fbfeff12f202f7130dfee6f8eee5ffec14fafbf5f4e9f2fef810f1f6f70d0c00fbee20f5ee020ef5e508f2f9ecedecffee29f8f3070ff4e60f03ecf8f00ae4fe1018fb090efa00fdeff6f3f8f4f103ed0705f3fcee07df070802f20a0b05f8e9ea05f3ed0403f402f3ecf709e009fcfb170502f6f1e8071c0601f9fa1909fbfdfcfc030907faf1effd09e20218dbf70ef4fefcfeeeec0cfffae3ee01150cfa0308fce7f2f5e20012f007f9ff0de21ffa15de060feb01071effed0208e9060000e210f8f3f4ff13fbfbfafee4f816ff0704f9fc03f90cede31ef3e7ed09f9e9f9fefc07d901fbf203fcfcf6f3f4f3f90f0ad5fc0406e71500fcedfbeeeff4fc06fbf4e9fcfb0200fc00f8fdf1ff17fe02f5fc01faf916eb0b07f601ff0bfcfe03f90f08090bf806ebf7fb0af2050ef8fc09fb00f7f2fc01f6f3f708fb04fcf4f309f00ffff6fe04fdf8effcf3f0eafcfbf1ff0000f2f0f002f7080cf70cfce90300fc06f800fcfefefcf6fcf6f9f7fbf002f00a0102f505f805ebfbf603f1f2fa00e0f307f501fbff04f8e3f4eff100e4fff7fef6d8edf909eff0ddf1e9060efaecf1daea06ddf6e8f6fefaf9f9e0e9f8fef6fdf3e6f804f9fbe8ec05ff03ef02ebfcebdd010004fdf7f0fbebf7ebfeec0b03fafaf9f1f4f2fbeec9dffb01fcec0cedf1ec14e2dafaf6f7f4f3f5f902f702e00be80301e9fbf905f1f8f5fee2fd00e1e6ee02080bf302f6eb02f7e1fdd9f7fefefaf7e60a02ffe4dffce10afffbf8ecd407f9d901f808f900fcf0f6eb00f9f603fcea06f5f2f6ffea08f302fcfed0f1f0f50802f708f80df4f7fafb06f5fdf502effaf4f8ff09f3d0deee03fef200fff110f5edddf9f8fffa02e8f602f0feeeffffeeeeeffd01f7f7040901fcfbf6f6faf605fa00fd06fd0400f3f10006fdfc06f508f6fc01f1fffefcfcfbfafef4fcf8fcfcf7f9f8f8fe00fafbeff5ff00f903f504fff901f8f50506fefff5fbf0fdfbfdeffe0204fdfaffef0500f5fcfa0608f503fcfb05fd04fef7f5fbf7f303f3fcf604fafef4f5f8f8fffb0000fa0202fafffd03f9f3080dff06010bfe0406fa02f10208fdf70516fc0601f0fb00fff909fb0e1a0702fd2ffd0efcf40501f4ecea02fef51cf0040e05f51ef2f6fbf401ffe9fdfffc0a0e00f205f8020c28cb07f813f10d100a0204f1fa1111dff2f5f0050012141a070103effc0106f8ed0803f22403151702eef605f8fff1fcfdfc15f7ff050af707f9f40315edfb02f609fb0ef3f1f4fdeefc040dfbf3fb03faf3fbfb0300fe03040408f606f8f60a02fdfc03f70109fff8010103060df7f305000107f2f1fbff03f8f300fcfe02f505f9fbfcfbff02fb02fefc01f2fc03f2f9f7ff0cfbf20011fef1f7fdf7f1fbf601fbfd07f6ff02fb03fd02ef0903fbfaf300020500fbfd07060309eaf605edf609ffe7fdf105f9fef8fc0c02fbf5fcf6e5f6feef07f1ec0604f3f1f609e9faf805fa06f7f0fce7fa01fd02fff5fd06e7fcfbf9faf2f10500f4fdfae9f8fb010102eff2f6f6040af303f90efff6f7fbf0fc04fce8f007f7f6f6fbf8dfe7fc04fc04fbf0fb1501fbd9f5e8fbfcf5f7f7f5eefbe806fffdefe9f902f5f60301f1fafcf8e6efdaf8fcfef808f8f1f7fef4f9f304010005eff0fe04e7f0fd0df6fcf005fcfff2e0feeaf2e7f5f20415eee5edf4f5ecfae4f7f90decfdecf0f9f9faf6f4e2edf3f4eef1fcf9ff0001ebfae4ecfd0af5fce8f5f8f6fbf1f3e2e9ee04fa06f9f0fdf40be509f8eceeeff2ee00ece7fdf602f800fefae9fbef00f9eef6f1fcff0adf131903fdf0f7f6f8f5e80b0118fbf8f7f1f713f80b110df7fe16e0f004fb08f315f7ee0ff606f706fafbf61304100106f3dbfcf3f2ffe20e130703f6f50fe90cedf8ebff08fff901fef4f6f5f7fa03f80600e8f61c10f906eafa08fffb05f002fe06f00afc04f509f3fbf9f110f7f7fcf809f40af701efe6fdeffbf2fb0001e6010304faecfcf8e2fafbeb05f0f9f5fb02f3f6ff0002efdefbfef9feff00f7f00201db04ee0106ff03fa03f1f3f8fdfcfef103f7f00df4eb0bfcfbedf3f1f3e9f6eeed03fcfefcfff5f8fcf2ecfffaf4fbf8f3e608f7f7e0e407fc05f6fb0f00e6fff7f4fee5fdef01f8f9f7fd01f3fdf8fb00fb0a0bff02f8fdf10807feea06f60a06f90207f707f8f21e0215ff000eecf2f600fd03eef0f308f9f9fdf60b0812070df1fc01f002000001f9e5220c1b05e8fbf8fceff81cf4fd07f1f205fdfc00eeecfef8f6f3f7fef7ecfe0016f0f905fff5f0faedf61107fcf501fc03ee09f7000200f5080afbf709ff07e406edf5020409fc01f9f8eafcfaf1f6ff00eee4f7060105ed05f7ed0104e3fdf4f7f90404e7eefdf8f7eff20af7f901fdeff0def2feecfef800f4070ef8e1faf6f9fefaeef3fcf6e315dff6fe0b01f7feeaf5f3fcdc0c040dfefbfdf6fafef7ec01faeffaf7eef2001202faeef9fe06f602fb02f11603fb0be8f9f1fdf3f205fd0cf3fdfb06fc09f903f1fc01f7f7f2f406e8f8fef802fdf200ff0300efebfffd04fffef8f4ebed02f204fffbfcfafd04fafa03f9fef7f5f0f800f9f301fff403fafd00f600fdfaf6f4f8ff03fffbfaf6ffeffcf6eaf804fff5ff00f108f9f7f2faf401fb03f1f7fdf70005000102f90405ecf6f90b0203fcf7f9f8fcf800f700fafc02fbf60103f300f4f1f4f90be7edfceff1f5f904efd604feedf5ece604e4f5fdfa01f5f2f705e3f3e9fdf4060b0301f1e2f8fbebf9fd0500fef8edefeff5f5e6fcf8ec06f702fde8e20805fff6efe0eaf4e1d5f50303f9f8faf5fffa05fbff0af7ebfcf9f3f201f7d9dfeefaf5f4f8eaf7ebf7f6e5ffe8ed00f9eff8fa0d07db04f6f5faeffe04fcf707fe00f804fe01e8de07f5030802edfef805050211f8f904f9f2f40704040cf3f013fff7ff09fe0a0006f51901fff502f7eef007f70beb0002fd02faf30904fa11f0f6f8fa01f8fc02f4030505fbfd08f3f6f2e50809faf90208f7e70805fe0aec03fd03f410fa07ff17fdfff9f0020700ef020b0615f4fdfefcf8fdf7fa02fbfb03f6fffefc030efb03fc06e1060007f2eee904f107fbf7f80ffbfefdec17f40200fff902f4ff00faf8f000faeef605fd0800e4ffedf10bff0100fcf6f8effe0502fb05f9e5f9f702e4fe0001f9fffdf410fde8ebee07faea0306ecfe0102fef5f2fb09f2040af6f2fc03ffff00fcf9f803fcfb03f811ff03eaf9fcff00faf4f6f4fbf7f5f3f9f2fef9fdf7fbfbf901fff8fcfffdf7fa03fc0005fbfdf706f6f8fafbfafbf8040afdf901f3f9fd01fcf4f9faea05fcff14ef0101faf4fdf002fdfdf206f909f5f704fcfd00fcfefdf8f8f4faf6fcf900fbf9f7f4f7fd03fb0bfc00f7f5fbfbf309fdfefff2fb01faeeff03fdf8f0ff07f9fc02fe09130bf7fdf702f2fdf7f4fe130cfd08f703f4fafaf900f205e6fffcf9f2f5ee020103f0e3f9f8fb09fb0604e2f7f1e9fc14f505f5f1feec05f306eff202f40c04f0f9eef7f8fd08eff908f8f6fc11f9fd01f4f402f3fa00fb08fcf508fbf7f9feef1cf8ecf30501edf5f90109ee12f1f2f90cfbf2faf40dfafc00f3fffcf9100b00f8f8eeefef0efe08f5f8fe042305fd08fffff0faf0f202f7ff09e6d8f3ee15f8ebf0fc00fe02f806ff06f10b0bea1004f303f5f5fb01fbf81311121601fefefcdcf01201070b0d1df305ede8fa0efefd011c050b090327041208f70cfe02f30b19ecfbeaf2fc10e00af707001602f406f9f10aefeffdf9fb11f3031104f5ec0002f3fef8f411f9faf6e609fc02f8f7ee03fcec07f2010403fefbf7edecfef7f9f20aff02fdf405fbf7fc12e0fc0b05f4f50006f6edf2e9fceefc02f41a05fcf806e7f70203f2f2fdff03f607fbeb05fff801fdef03f7f5eefefaf9f2f7fbe8f801fb00faf1fb02ff0307f8000f0cf4fbfb02fafcf701f1fc02f3f2f0f2f101f6f1f3e7f4ebfae3fafbd2eed101f7f6e3f8fad6ed0ef100e407041406e5e600fef8e6ee01ecfdf2fbfff7e4e6fed40fff01f7f404f800edfd01f3f909ecfb09e8f7e8ebf70502fd05daf1e5f1e8fdfd08ef0006e006f7f5fd06fdf4e909efed080311ece3f7fa03f40df8fce905ecedf5f0f8f404e0e4fcf904d7f5fdebf201f1040cf90000f7e812f5f2fdd9fe00fecb01fcf5eef5e7f2f8fb0eeafbf4eef00df2eaf5ffe9030c0104fd00f3fbfc01f000f2f30706e4d5f8f4fff603fd02f901f5f6f1070503060fdae9f5f7d901060afbfe01dbfef3080506f5e9eaf802ebf21100e7e6fcfef9fc04f100edf0f5f40cf1f107fbedf6f300fceeff0df6fe08fb090ffc03fef6080ffdfdfbe7f50803e901fbfef7040301f51100050100f60a02fbfcf9fffbf8f4fefbfa07fbf1fb00ef0afa0006fff9fff6f30e03fef401fc03f9e4f3f507ff03e8e7f1fe0700fc010206fcfcf5fef9f5f5f20307f2faf9fe020b04f9f5fc07f303fffe02fe05f80af9fa00f5fdfe08fafefcfefafaf2eb03e5ff06fd00fcf6fcfe01e7efedf900fbe2ff11e7f9fce300f103fffae701f2f7fbfdf0f4f4f90af4fef8f304e7fdeffdf9f6f4fcf9fbfedff6f2ef02f605f9f4fdf3f3fe08f9fc05f7e3eff6f7bffdfe060af7faee02f0ed00fafc01e8fafde60606fbd9ecf704fffc0ff3f5f6f9feed0cef01fb08f0effced03f2f6fefaf8f61afafdfb0df2eb0900eff1f720f8030716f1fff602fe1005f8fdf703e906f9fb03f803dfe700f809fe1813fef5ec01f102fb04fffef7f80407f701f606fb0b01f5011413f50c0be005110207fc1eda02f5fdfc0cff0202fbf30bf80811fde80cebf20804ec0807e506f9e302dbfbf6e3fdfb00f502141af206feef13f00d02fceeff09f700f81b0a0df10cfcf3fcfb01f10a050efbe317fb0af3ee0c01f301050e03fc0d1103040203fff40509f50bf6fb0e0204fe0c09fcfffffbf1eb0503fb04fdfef7fefbfc010204031701f5fd07f7fdf5050009def6fcfbfbf0fefbfe0cfd01fae802020403f40aff091cfc0bf4f4f30efe0301fd00f60f15f1fbfdfb04f6fff1fcfbf4f6f6f8ff01fff3f3fef4fe00f8fdf6ff01fdf5fbffff0400fdf5fc06f801f8fb00fefefc03f6f80305eeff0dfbfefafbfff6f200ff01f700000101f8f1fcf4f801f3f608f0fbeeeff10305fdfd0103f7fd00f904f0fdf8f9edf7f4f4f3fffbff00fc06fa0d0207faf9f6fd0cfbf7ef06ff02fd0605f9f7f7f20405fd02f90c01fffff1070700f3f6f201e3fb0404fff10cfcfa0efc00fcfc09fd05ec05f80ef1020702f5f51105f201ef0408fef40510f8e7f90a02edee0908f9ff03fdf70afafdf911f7f7f502e6f213fc01f5f4f2faf8fbfa060001f801fb01f9fcf7fdf8ef03fceb09090d150bfbf6fdea0df7f6f0fdf0edfd01fc0afff1fb06fdf2010812fc04fbfc080310f7f406fdf7f0f4fc00d707f31003fdf70ceafd080cf1fbea12040902fffef9f8fff3f200f60c0901f2eb180000f40b02fffb07f4f907f609fe020300fb0205e90708fff7f50408ec03f6f60bf9f50806f5f8f60418fdfbf116fcfbef01fc08ef13f7faee03f908fdfb04022108f1fcf4f6fd07fef3f8f9fef3f6f0fdf5f6f60bf7f601f8fb02f0f8e9e803f205090ef5f2eff1faed09e4ecfa02ff03f101f30101f6fe0a00ee06faf9eeecf3f8fefdf201fdf2f2fe12f60afdfa01edecf8fbf8e2f303000401f6efff01f8f4f8fdf2e7f8feed03fcf6f1e7f8fdfcf8f303020209f100f9f7f4fd08f6f6f5f007f1f5f6f1ed01e9fefbf4fc02feeef6f7e6dd02000500f1fc09e4fdfce3fce9fbf4fbfbf8f1f5f9ede7fb05f2ee010403f9fbf602f1fd02f4fdfbfcedeff2fcf7fe04ecf204f8f501fcec050405fef2ed00f6f7cb12fcfff3f9faf5f8fa03fef701f805f4fde30d0ffcdfdf06fdfff5fd0908f8070bfd00f3fafd04fcfffdf8fddff6fdfbfa0a03fefbf4f9faf6f803eef8f22203fef30afff7e80f04dbf8e701030301ecde0cf5090ffc10f60208fbe6f40af8f8f11b07e90afef403ebf2020014e3f105faf4fa020dee0503f604051a0bf8010404f5faf7f6f4f5f9fb12fa18f5f4fff601fbec1cfbf4ec15fe04ea031300030dfff603effb0705f3f1f9f0fef8f7f3f4010007f6ecfbf8edfee3ff06e7dfebfd0003dafafaeff6f8f601e2fc07f8ffdeecebf9feeff1fdf602f6fdf9f8cbf4ffe9e503fff5f1f9fae2f305f7eafef4e1040406fdddf60bf3edf0fae1cef2f7d502f9fc03fe07eee7eaeafcfc0304dc09f1f4fd1002d0e2eb01fcf9f7ebf4ebf6eadc0bfdfbfcf4e5f7fce9ffde00f9f30803f001f0f6f9fceb04f805daf4e1f70303defdf5f10500e6fd03f0f7ffffe3e6f2f7ef03f6edfef5f700fb00f9f406ee01e7f10000eff7eee600ff0afbe713faf4f800fdf5020202f9fddee7faf7ebee0507fefdfeef0afcecf0f5ed03ef05f9f405fa0503f5e300f1eff6fdf2e80b040bef0602effdfbf3f6ff09fbf4f607ee03fdfd01faf709fcff00f0ed07e9fa02effb000405fff60afcec06f6fbfdfbe508faecf2f9f9ee0304fa03eefcfcf4e7fc07040501fcfbfedcf6f4f401f5f6fefef8030beaf7fffbf9fde1fff1fcfefa070000fef9f600fafbf004f8f8e205fdf5f50efbe2e5f601fef106f601f7fff1e3fff704f8f8e709fae6f8ff04f7f711fdfffbfcff03fbfdf70305feff0000fc09fb0501fa06f5f7fdfffd00f90200fff5fef500fdf8fcf8fb02f6fffcf8fd01f6f600fbfef9f8fef3f6f402fceb02fffdfd03effb0708fbf6f9fcff0202edf7fefbfafdfc080500f7f3fef4fbf6fbf7f8f7f9f802fcfffefef7fefcf9fcf90004faf8f9f4ff01fdfbf3f5fb00fcfef604e805ed020811fffdfa02e3e8e304f706e2fff3040f05f301f802fd02f8f503fe04f8fcecf2fd10f4ff00ee0200f4cffdeef0fd07f303fceaf702f0fcf10604fef1fa00f416f8f9faf4e71df7f9eb03ff07fe0ef8e8fafef2f1fcfd00e603f305f50afaf0f2f509f9f005fd01f903f604f906f208010cf6f401f8fcf2f3fff6f3030502f8f7feeefdf6f4fafe080ff2fb01f503f301fdea08f70901f201f3f600fefaeff0f8ef0313040ef706ea03ef0708ee01ffedf302fafcfafef70c0309f7020a100100fe0bf3fd00f2fbf20ffa02f6fe0d00ee00f6f80607130be5f905ecf9f3f1ebfff90501fef8f601ee14fcf10504effd07f00902fcf6f109fd02fef30f08f5f8f9e6e30217f405f332f60a0b2905fdf30a0001090a0cfe1af0edf9ee03fbf901fbfcf902050bec0ee2ec0104f706fc11f7e8f7fefdfd200ff5e1f907fd041910f50902e4e613fc080242ed00f2f9f6f5ebe300170502f9080ff3ecf701e3e401f81bfdf8fc03f7fef9060dfbfdf4cce30a0013e4eaf5f0070af9030506fce3effefde7edfff8def819e9f8f90600fcf80c030cf807f2f1f5fcef08f6030ee7eb09e0f60f01f114ef0b02f00b010c02fb05fe07fb02f00c040ef0fffbf7011706f80000fef602f605f104f700f2fcf201faf3fa250017fbfe09ecf7e805fb07ffed0d00f60fff04fbf4f903f6fb1bf0000403fdfee50bfc02eb0b0015000409f801fefdeefcf4feeb0f0f0cf7d9fe00e7e5f8fffdf403fd04f8effdfef6fceaeff005f3fefae7f8fbf612f5f5fbf3f506fcf50a15ee040b0dfbef00f802f3f7f0f507fff900eafdff01d7f80afcf60bfaeff81105f906fbf40a06faf4ff0316f3e2edf9f7f9f5fefaf9f7fc030b04fe0af401ecf9f8f801fe17f8f01bf9fef9fe0500fa0000fcf4fff704fb01fafafff803fdf50104fefefef4f7fbf001f40e05f9fdfdff03fa0003f9fef8fdf7f80003fc02f1effbfdfb09f104fefaf700f1fc0304fff302f1fbfdfbeefbfffffc03fb000707fdf7fb00fffbfdf702f802fd00fbf40101f507f300f6090603fdf2ffff02f7fffefdfffd0004fbfefff0fe01faf3f2f5f500fff1eb0c02fe09e5f8f9e8fef9f501f5f50705f2fb05f90119f4f0f10cf7fa00ee00ecf804f50ef40a000a06fafc100104fffef3ecfff307f4f4f60802ff03fbf0f8efecdce80106fb00fbfcfe09f1ef00f7f305f701000cfa08e8f2f0fcf800fe08fbf3fafbf002fffe01fdf5f30009faebf3f4faf70005f50001f0fcf7fa0f02fa0205f90403fcf3f904fcfef706000cfef601f0f10c06f3f5e810e0f8f402f1f8e7f603ee0efafa09f812faffeafff7fafe0afc01fef2fe01e3f5f504000dfdfef206001005000a0efdf604f8280906ee01f10ff0fceff1f5e9f0f907f2070de3000f0601eef7eeeb0ef8f0f4e8e7f1e3ff0402f7ee1a08dbf602f1e3fcf709001724fe030c17fd07f002fbc8fdfd0100f80bf6db080c02dbffed120f03fa0200e6ee05ea000df90afefff2ee28040cea0111f30409fdfa0cf701fff7170f0b09f0e9271700fef80e01ea1007081317f7f10dfe03061111fcf1f11d07fe1903f5ffec0900f701e4f3e202fc08083105f907f9f7020afafff0f3fef1fcf2fe03fa0500f9f9f4f9fcf9f80bff0006f3fbf5ff08fb04fbf5ef0e0809ecf0fcfdfafb0ff0fc06fff4e9f90307fc00f10706f1f5f103fef9fbfef4fe00fdfdebfb12fbf10909f902f8f5f6f905fbeffcdce8f5fa03eefbf5f9e10cf2f9f4fdf6fe0109f9fdf103f1f906ebee03f7f7f8e6ee0bfcf5fde7f9ee01f7150701081ae5fafefdf1fc0d0ad7f903260ddd040b0504f0ed0705f52206ef2eedfed8f2ff050304ff0103f2fa03f6f60b02250aeffa0afcfbf5fcf9f2f905f114f7f6f3ff08db0d14fed4f908fe04f5011dfd0106fdf0f004db120217191602faf9e3f9f10afc060f000d080004f50308fd0c0801f0fbf003fafef1ed2300f206060de8faedf7fb1313f610101602f9fc09f7fa12f8f507edf609f3ff0a0409e5fe0ff90205030508f0f303fffe1407fb02e7f614fcf60206fd05000dfa160b0109fc0906f70a1009f116fb00f4f90501f6faf7170314fb04fd05eaed08fbf406fa1b02f1fd04f5fbe6f9f5f5f10afbfa000304fa22fffbfaeb00f71a06f3fbe90606fefff8fe00e515f8faf8fffc000c0afcecfde3fcfb07f80ffaedf30217f704f6eff4fefb01fdf301fb00f0ea05fbf803f4f0fff11407fd0e00fd080008f9030502f3f6f402fd0bff04fcfdf9f5f9f3fbfffcf8f608f403fe020305fe0606fe0efbfcedff05f3fc070dfcfef9fcef08faf4020a07fe00f5020409f4fded01f7fff9f00305f0f8f1ff05fae3fa01f4f7f3e8fef3fb0af2f3f9faf701f9f6f0fd06fefc00fafde9fbfaf40008e5f9fc05f9f4effdf50004f010ff01fbf6eef40d0409fbf9f101fefae2eefc00f906f8f800f5eeeafef100ee02f2e70dff01f2f6e3fefc04f9fefeecff0efe03f6f70000fe02f401fa07f90405f9fce8fe0bfefbeef6f0f7fedcf2def504e9e20100eff1e8de00eef50a01fefcf3fcffe8f2e2e3ec0af50001f7f0f8f7f3f500fcf8f1fcf8f3e8f4fbf3ffefdd04ebf4f9ccfafdedfeeadbeee0f9eeb6fb05f904f3f7ef08fdeff3f5f6f1d8f1f4f0ee06f2f1deebfdfc00fff3f2f1f1f4ebfce3f6f200edfef3f001d3ffffe9f9f71905eee9f5faf0f5f5f4fe14f0ddf9f202f6040df3e51100fd04f9f907ea06f501e0f510fbf8fffaffeeff0bebf41fe503f0fe17f211fcdd02f0dbf709190ef8100ffbf60600fffcfef0fdfd0d010bfcf7f9f6ecebf909f1f3ee02f8e1f4f8f9f5faf20af4fdfbf7dbfa0f0411f3f4fcf4f106f7f5ee06e9f1fb33fbf006fcf90900f7ecfafdf5eff3fbd9f90bf7f500ecfb01e01002e2fae9ebfdfbffebde12fdedeceaf3fb050003fff8efe6f7e40c0ffdfd0100f5dc0af7f6f2f205dd00fff7fcffef03fffef400e9eee9d5fb23f6f8f50afbeafbf6fb0c07f8eef3fff307ef29f8c0d20706ffe802f0f0f00de0d9faf3eb0bedf307fef8f5dffbfbf0f80f04f5f5f9ec03f4ecf6fce00304fcfa08ea090bfaf4f706fcea0702ff0ce6e21309f5e8f7fcdffcfa04f8efe5e303eeff07fa01fb03f5f4ecfc00f0f9ede007f9f6f3f3e4f405fe03f4dfeaefeefa0702f40005ffe8f0f70df402f8fcfbfcefe902fbf8d5dcf10e03f403f9f9ee00e1e1f8f004f3f9f307faf800e002f9f7f0edfdfdfbf2fbfbf2ef04f3e5fde8fb0507eb07fcf1f2dcf6f3e906fcf401e8f1f702e6ecf1f6f2fff504f8fefcf1f7fef50cfcfbf40802f2e2f2f901f7f8f901f0f6f8e9fafa03fdf4f7edeeeefeccf50103f7fa02f6fef5f4fd02f1f3daf4f8fdeff2f8eee8f4fc001109fa0603f0f5ef01fffbf2fff702f7f6f7f8f5f9ff00faf10909fefff106edf608f11207030300e4040302feff00fdfef801f7fc0413f6fa0a00060717f9fc03eff900000b03060306fe02fd0bf0fffbfcf902fb0bfffd0f0709f606fefd1214edf8ef0ce800050107ff05ef0c01f50207ff090711ff01090407f202fefafbf3ff04f7090802fcfefb0303fbed00fd0dfb0b12f601f2f6e8fce8f8fcfb0cf50103dbe4f4fe09f3d603f7fbfdfee8f3ee040705e9f0eee8fe02f8edf90b04fffbf2f1e1eb01e002f0f10502fc03f1f1faf5f1ff01f4fff5fb0dfcf31609fc00f1ebfdf1f2d7f1000001ed04ee0200fffe010002f605030b01fdffedf6f202f4f202f3f7e7fb12f8fdf20005fdebfdfc00feebfcfd07f8ec2efdf7f4e3faf904fd01070d15e2ecec2801f5f7f6fa0f0eec0cfd07fff2f4e90301e60ef300ffedfff50cfdf6f51ae0e70afaf9f7edf8eff6f70a08f9efeffa030216f00afdfafdf40ef90ae00713fcf8f5edfd0de0fd040516fbf6f8eeebe70404fb0b091104ef09fa0a0de8f5f5c7010e0c19e11a12f5f0f002f9dd0eee0dfffbfd02f9fdeff909fff5f3f2f2f9fdf10101fdfbf30300fcfffb0003f8fdf0ff08fafcf6fbfa0100fb0afbf70303f4fdfbfffafdf80c04f8fa05fef4f8ff00fcfef400f600f9f5f601f506f4e8f1040703ff0107f6fbfffd050305f6f8faf502ecfcfffc02fcfafdfc0604f4f2f6f900fffcfaf7f90000fbfdff00f5fcfa0bf1fe0af6f6fe17f7e9ecf40a08ecf4f20ffe03f6fbedf206f2fdfefafcfd19f2f40814100c02f1f905f0f30beef60805fdecf6f9effdf6fef50007f9ebfb06f6ffec0bfafbf102eaf502f3ed0203f50000f9f3f7faf8f3f1f6f1fce505eff2f90fed02e6ed03fdf2effef9f81703f9fc01f9f3e806e4fbf4fce90afdf6010cf3030809ffe207f5f803f8e4fff3fcfcfafdf90000eaff3206030c0efbf5f504020ff4ec00faf91307fb010b0b1a14e70307fdf100fe080cf8eb02fb0eebe1080101f10807fe000ffff2fbf71c090eec0501fcfb00e8f3fcfbf10ef0faddfcecf4f5f7f912f001ffef04faf40fe1f0efe9fefdf703f4fd0701f3f8e810ed0803eb0304000007f4f7000e02070ff5fc02ff0dfc01fdf9fd0b0d06fdfc00030e0bfe00f3f90704fdfe07fdf60714f4f40ceef6fe03f6ff0ff9fe08f908ffeef4ff020c00fcfcf503fc07090cf703fa10ffff07ff00fcfbfe0f0300f51c07eceaf700fafffafceffb0502f7fb0cf628eef6f902fc08f907ff0404fe0407fbf70514e1f6fcfff1fdf9f9f900fffff6f6fe0502f301f8e90301f203fefafc04effaf2f601fb01f0fffdf8fc0107fdf8fe00f108f2f60300f9faf4eb0702fd02fa0cfcf8fffb00f9fc02000005f3fdfbf4f305060101fafcf8f8faf9f5ff02fcf6fbffed04fa03f9fbef04faf9fcfffafffb02fcf8faf9fefef7fbfefbff0000fd00fbfff104f3fd09ea01e00d01f0d4d10df9f6d8f8faedd1e7cdefe8021001efefeb0ef9f5e8f70cf009fefd03f1f0edf1dded01f4fbf3fb08feeff3eef6fa0a0f01fff604e2f703f2feec1fc30202edcf03f602fd17f2effef1f1ee0001e8dffaeeecf3050ce8ef04fa0904fee203e4f706e506e8f50ff6eae40af1fef4ef09f6f4eb030001f60910efe4fcf9deff010608f80f04fe02fc000e0704ff030900e6030804f4ebe106fef2fafef604e3140afd0e0005f5fb0bfd0ffcf201fd0ff7ea0100f2f20302ff00fd00fdfe0607000ceff1fdfffefd090201f6eb0fec030606f6e6f7f5f2fff5fa07fdff05040af7f60b06fe02ee0a020804f7edf4f0fcfa0b060506f7fbfafa03f703f8f7f40508f1f6e9f3fe01ee00ecf503f80100f004ea01edfaef11f2f40bfe00fb05f505e90afbf0eef0f901f30af3ecf2f8feffe90afd050703f4fbfc03fc00fbf6f9fcf9e7010404f8f704f6f9f2efe6eef1fde603f2f0f9f7021205f4fff6f908f0f8f5fffbfefbedf4edfbfa01fbf9fa02fcf1fde8101102fbf4f5f6eaeef5fc01fafffaf30800f7fef5faf206fc0800ff00f4f8fbee0504fbf6fafc02ff0101fb0cf50203e8fa0000f9f9fdfcf7f8fafffdef000b0100faecfe00f804fbf310f7fefceef502fff9fafe0000ec03fdeffb04fcffe9fcffffec0704f605f801f403fef7fbf4f4f9fc06f5f20608f4f9fd0a07faf6ee08fcf3f2011a110f00fff8e7fe1cf4fbfbf100f610eb00e700e106faebff03fb06fa0302ede6fff4f906f2eef5ebf4e9fb030500fee808faf1fbf1ee05fee105f1060fe0eb0bf8ffeff0f9fafaf7fd08fa0303fbfc0708f706f00f041402f7ff0ff20006c7ede9fcf8f2f60005f60af7f7eff1fbf1f90c08fb0002dcf5f2faf9e90a03f7091105fc010105f702faf8fb08f9fe03fffefc020508fa01f70104fef901fa01fffffefefeff000000fbf8fef8fdfdfb0803fdfcfa09fcfdfe0201fd02fcfcf502f9fd0203f6f5fb00fc06f904ff0302fd0506f4fe01fefdfdfafcf9fe00f2f4fefc07fefff1fd02fcf5fbfdfff2fdfbf8fbfffdfffc02fcfdfaf40c02e800fcf3001108fa0ff5eeede60105fbd70205f206fde502ecf6f7fafbf1e3fa02e2fee8fff9f90801fcf2edfbfedf05f4e4f8fcf5f1ea00f8f80708f40505f508fbf7e1120000fe0ad7eef5f0d6fcfc02f0fcfbef00e7f600f7f7f8e508f5f0f210fbeee6e101f4f1fbfdf7e505f402feeef9f002ef01f903fcedf70303fdfb04f6fdfcfbf6ecfef5f2f2e9f2fffcfbf1fff9fa03e7f404f1fbfcf4f3efe4f504f9f5e70c01f7fffbf400f0f2fb05fd00fcfc0b03ee08dceb16faf8eeed0000fef1eff9f0fd03fbf8e2f6fff1d1fa07fe0afd0603ebf1f3fb03f6fae107f4f201fdfef3f4f405f90b02ea05f6f0efedf9f1fdf5f702f8f8f0fceffc0bfc0efa03feecedfdfcf301fcf5e4fd03f5faf5f9faedf3fef4f2ffdbf3faecf9edfa0804f2e7daf5eafaf3fcf8fceef6fced0007fcfaf5f601effff9f8f9f8f1e208f5eafdf8e1f6f0f1ebf8f8f3f2f0fff2f7f9fa0701eceff1040007f8eaedf6eaf6f401f9d8e8fdfff9fcfbfbf7fdf9eddef2f800f4f7fb03f9edfcf502fffff0fce9fff8f9f501fe04f6f6e9f4f9f6fffbf4fef5f8fbff01fff7f7f703fa0001f9fefb08fdfafe070800fcf909eb0501fdf6fbfffcf40105f9f2f70901f20dfdfdf6f7f0f304fff9f3fb0302fdfffef9fb03ff00fe0209f6f6f8f802f80100f9f9fff5f9fcf9fbfff206fff6f5fb000109f90106ee01f90208000402f6fbf5f8f80600ee02eefeeefe0502e5ebe8f4fb13eef806fb09dff100f103f405eff4f0ee03f213eff8f7f501fffd0cf6f501fbf4fe0402fcfdfdede7f9fc11faed0efd02f20df80004fef7ebf7f2fb05fbf0ed0af7ff00fafff2f5f3f6fef5f5f4fc04fdf7f3f006f7fffd03fe00f2ffed03f6fefc0400e3fa0101edf003eaf6f5edf50e050efef4f40dfdfe0a03e5f3e7000200edfdf9f8fff2f3fae8fd06e6ffe3ed06fdf3eef002f202000101fbe9f7fceff604fcfcf7f0f8f6eafb07f9f1f6f2fcf903f3f5f1fbf9fef203edeef7f4f30101fefc07ffe9f8eff9fc0205f8effbf9ebebfc00e9deec00fcf9fffb04e800f7eb04f5fbfafefefb01f5fbebfcfdfcfaf1ee00fe03f1f9f602fefcfae3eb0e07f6e006f3fcfcffe6f9eefb051a02f8ed01fee9f1e800eaf00bfff8f3060a0eee050202fdff121007f0f8ff09f6f100ffff0407edf0fdff030616eafff3e7e3140106080afe0d0af2effa03faf1fa02fd0620180efbfcf900080113eefcfa08eefc1dec070bf7ef03fbf3fbf2fe06f8fe09f9fcef01f701fcf5f803e5f0e3f304faef01fff2fbedf802dbf70ff500e9e31202e8efeb07e613fd05faecd6f6f8e1fd0f0b02eafffff2d3ed05fbfcf7e100040bf108e9fbf201ef00dfedf8edf4fdf4f6020801f4fbe9f0ff00fc0be807ecf8ef05f2d8d9e9fbfafcfbfffc10fde5dbfaf9fa0200e405f5e3f9dcfafbf701f5f2fcf5fa00fe04f5fbfeece9e0faf7f9df05feecf8e9e0faf60000f7f4f6f0f500ec0adfff0405fafd03f7f3f1f7edf6ecf0f307f9f8ffe0f3f7ec01f1faff0103f8fafc13fcf7f5f8e3ebfffdd9f4fafcff0105eefef6ebf4f7f8feeb02fbe802fbfef4daf3fcf1fc00de01ee0bf2f5faf70116f7f8f5fcfb09effef3f8eefefbf709ed1207f7effe11f3fcebfa0ef7eb020b01f404f9f8e2fd07f90debde11fbebf5ed08e307f902ffebea00fef0f20bf60cfd05fdfdeef406fa00fcea0bfaefff00eaf60108f6f9e4f4f9ecfdfcff07fe0b01f4fef7ff0701ff12f409e000f5effadadff0f801fc07eefdfd01f5f0f7f2f5faf7f80fec01fcea07f803f8f8),
    .CHANNEL_BETAS(2048'h790c780f7898774e76d778ba78b57830795c77df788777c9773a777077ff794978c1773d7850779178d3786c786d77f278c6784177ae777b783a791d7907780278db770f77ee780b785f772278d3780f7784785777a679307856776d78a678b477807832777e775d786e780f78f5772d785578a37733783477a5798177f677bf78a978f5780877c778e9777177ed783e788f781e788a788d782e78b8785677ab77e577b8794c77dc790177c377e4789877fe77a27862771b77057861781877f578b9785f785978d0784f77b6776678f8786b771b7850784977cd786c7761780478277806794d78bb772678d877d3788e775878a278b2777677cc777878817768),
    .CHANNEL_THRESHOLDS(2048'h020001fe01fb021e021c01f401f9021001ee0218020b01f6020c022801f7020401d602170218022c01f502100201020a01fd0204020a020e020201f902040211020c02160222020c02060220020c0218022101fd022701f501fb0218021301f0021101f6021b021f020302160203021a022601f7020201f002090200021c0215020e01f501f60201020b021e0228020e022201e901fe01fc021102030215021601e5022c020c022b01f90225020101e101e5021a01ff020a021c020301f6020801f001fe02030222020f021b0220021b021a021a01ed020201fc01fe020b0205022501ff01f301f4020601fe02220222020f01fc01f602230216022702130220),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d4),
    .ADAPTATION_DURATION(16'h1398)
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
    .KERNEL_WEIGHTS(9216'he4efe5ff0b190911eb28012b22ef1cfffe07dcfc03e0151ed8f50814dd1cec14f5ecdcf422001f11f718db0106fc09f9f7f508f0eef51afcece4e42423f115202914edfedbeaf3e3f9ff1eccffe6bdfc0a1bf3fb0408f92b3220230e0d1bea1efef3f1fae1f0e7f5fb040d0ff1f505f4fcdb0bfa0b272e48200710f61bebe6d208f9fd25eae60a0a210c08eb1b241a2d191130e7d106dee3daf20d14eb02eb15e509ebf5fbfbf4e40b111329ff1c110216f6cdd020fd2414f606f0091fedf5e4f3fdfcfc081d20031fc5e8d8d702e50cf1050502f505fe0cfb04d3ef07f7161dec1ff30efbd511dcf121190d08ffece51af8f0e9110de5e701e2ec19fa16130df91a1004fc0af6e312f5de140cef11eeedf3ff0b11f323eae9e2ef0c0510fb0afc06f7fa16faf1100af102feebe215f9e2ee190611eeeb1215081cf9fb0b061a0abeeedb10fe04faf1f11c09fcebf3f40afffb09040c291c2f180c0b031018f400e816eb02fae01007f001e5eb05f4fd09e9fc0ae20c11c0010dd7d3e0f810f82b0d2229fc082afb2a162b11f41624edf700eae5e1ddec0eea011fffe3eee6e6fefef5f7201d181002020cffe70bf9f416da2113ed100bfa0af0f80b21e4242a11140cf816f5060811eeeb22d5fef90aebef02f8fee8f5edfdcc031f03f5f70cf2dce92b2311eac8fb0cf6ed0adfded3e9e7fd1d220f260f1f12f7eb0805e1ddf4082c120b1f2d190d240b0e1dc8e5ef05061ff9000af7f3f4fe0afbf3142805f620eef307def3de0e0f070a050ae8fc0f12ee1afde2ec24032109c0e2170010de191ee9f912dfed11f0f3fc15e5060102f61cdb2bf2f118f9010720123bfcf61c18db0f12110d08fafcfcfaec422d201d17200c0a06110f0eebee09f4e309f3ea12f5d414fc050ef61703ee061b0bf7e61d1d2ef3f8050502010af61c3bf11011363007151b07d8ebe3e8f6ecfffee0001a0b16f5f5f605f7e20e2bf21d46273403d50f17f709ede3e7f9f6e92206f1e3fe2df9d51bd0e7f9fb0ef60d00edf9e4e9f0f714f1e30e12151113020b08e9fafdeaef1cf81b27d72033fc24f51113ed0312020df1fdfd010ef4e70503f4e7dbf7080722cfe70d19011726e51efcf2f70bfff6fff3ff15d91a13fe0105fe050cf0050af2ee04f0061c1c29cfe4ecffdeea1b0510eeee16d7e0030c011b200100fbfe202f03190815f7eaefcf10170a18f9e8fdf5e01bfe0a21121b0de7ea13e6f803f1fadd0df200f10218f9150bd8040eed16ebebe91407fdeb040a0c0cea16eafc1ffb10161b1bf2f60ee817f605110504070af60ef017101107141920332703eef5050a0bf2ecdcc219c6ea1aece309d404e001fbf708100d1ae1edef0bf6f0131017df36eaf4f40cdae6f7db01e909dd14360efef1e20ef6f81feff208e4f9d419fc090e190518040901e91320fa2208e7f302f8f6121022221ff4f41f11000ece280227e1d4eb12fff01f0526dde5f9d7e5dcf2110defece11a11fefbf1edf20b0306100fe2f5ea0ae2e110110004ffe703f30407eefe2f011be2e00201faf029fb1520050bfbfbfcd2fff1faf6041714100d05e0f8fb0be4ed06362138eeef1e2120210bfcdc13e8f528151d),
    .CHANNEL_BETAS(2048'h782e78cb785c7830784f77a6787178b7786e786c786b77be784f792c77f978427827782277d1781c77847851783d77fb7790787777fb782877cb783578b07864781b77b178d6783e780977a678dc7857780877d478ef772b7853783b783277cd78e7784177f377d9782277e8778f792e782077fc78e0772f77f2778e77fc78ce7847780c781b78ec77f478b07864780077ef761076d8784b782578b8789d782e77ca77e0783477ea77e577d377ee76f0780977fb77477800789877b9780b7867789478bd77f57961781c78a5786477dc77027841786f77917790784078a1780e78d677d97861782b78307839784d782877f777c37802787a782677e77909782c),
    .CHANNEL_THRESHOLDS(2048'h01f601f6020302000204021701f501ed020d0200020801f601fc01e3020701e601e401f901f401ff0206021601e0020301fe01f9020b020e01f5020a01e502090206022a0202020c01eb01cb01f002070200020801df020301e901fe01f301fc01e901f80203021a022e01fc021901c801fe020d01e6020f01fd0206021b020c020d01f901ef01f501fd01c80203022401ef020701f301e401fc01e501f80201021602130200021302000201020e01fb01ef020701f8020301d101e301e6021901ec020e0200021801fb01ca020a01fb021a020701f40203020901f501e5022801e501f401fb01fc01dd01cd0209020101e302060201020401f3020301e401e8),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00be),
    .ADAPTATION_DURATION(16'h14b7)
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
    .KERNEL_WEIGHTS(131072'hfaf706f50702ecff0f1302fc0001fef40c070d0a042213f60bfaff00ee10fe0bfdf70c0febfff908fdf908fd0af9fbf803f100f0fd0909fc01ffee1bfcf70403fafaf1f207f50501f503f20defebfaef0801fe0004090aeae9f501faf2f1f91bf801faf60aef05ecf101f9f7eb0be0ed1108fd0819110d08010803fd140aee0df90dfcfefc01f701fafd110bfcfdf7fb09041000fdfb010107f806fcfc0e06fe070bf0070e01fa00ff00f4fdfa030beb04ed03ff10f303fcf7f80303f9f204fef9f60a01fafff30cf309f2f0f305000e17fffefd04f8fff5ff03eefdf3edf907031001f8070c03f1f7fdfd0e15fbf7fd03f1fbf6180b0efd08f4fdfcfc10ff1211f407fee10101e5f807030409e9e8faf0ff13040905f50a1211f20e03fd150df8e1e40afc0d01e5f30a080e0f01ffff0c01fdeaf2fefcf9ff03fd02f4faf4f9eff301e217f210f5f511142306ee0210f9ef00070a08f1f9060310fbfdd810f6f2e10af809eafeff0deafe00f70f1df00004f41004040b07ed1911fcfa08f2f8fff1fa0e1902fe1cf6e9f5d902132af3d3fb0e0812061202e30f02e6e70ae6f9f90a0902fe0b1cfafef7e7f02505df030aeff905fffb011bfd14e506faece613040cf11404fd06f9fdfdfe2bfdf3f1f8ecebf8fce905f004f5e90c02fefde106fe090236eef5fbfa0209130908f3defb1709e721fc20f2f8f5f70a1e01f3d910ecf0f8f1dc04fe02f9f2fbfafcf80af72006ebedf90505f2dfebfe05ffffe4fef5f6e8f708feebfd06e906e413fbe7fcecf6fd010fee0307fcf5fbf504eefbfcf0f700f6f7f8fdf00405d2fdebf5fdfb1afbf507e3f40511ebf606f7fbf7fa01f6ee00cbecf4faf8c705f9f2fc1008f916fbfbf00e00fef3ff02f7fbf9fafaf60ae7ddf5eff805fbdc10edfef90c0617ebfcfcec0411e6f2fe22fdec0cf302f2fcf8faf9eff0f5fc02f7f8010afef3fff20c01fff4e806fcdfffeeff1704ed02f4fa09f0effef6e9f80a02fff803edf6d8f8f30106f7fffa0e190608f6f40ce707e806d802e80b0d03f8fa0efd020cf5081ffd0bf7fdf009efedf408f5f8e5fdfcea05ddea0318e809fc060c05e3f001ff0d04e50308f505fbfaebedff0526000001e3fbee04eeecfefff80af3f216f7ebfaf8f503fdfcfd0b0afd0811f6e3edeffe07f105f0e1f4f50d0ff4fffbec0b08f507fd1103f7f0eff7fff6f3f40aff01fb06c208f001ff05f1fd151a0813e9ee0cfbf007fbef080702f3f2f90ae8fcf2d3f9ef080505f61a0ffa1002ebdeefecfa18fe0300fffe0c06fcf9f9ed2b06e3f7df0308fefdf406f4051ae7e1f4e3f8070af0fa0fecf0f2de0704efeee9f0f3f200f5f3f807f2f4fc18020bef01fceafa0305200efef5f8ffecf403ca0d06e4e9fff905ebfef51bfe090b140104020a1404e9110308fcf50803fb0cfb04e6f6f5f3ff0af9fc04f101f103f3e4ffeffcf9050304020dfc09f5f0f7fafc0e09f1f6f1f1ede6eefe02e117e8fdeef4feeafcf4f2f4f7f7efed02edf6e4f90ff4fb02f8e8f3f2ecfff6f603f5080102fefe04f9fcfa04f9f7f8090afaf1effafef7ebfdfc00e0fbe80004f300110a090c13f7f1e6fb03fefefcf302ef0cf3e9f6ebe4eafefafbf2f6f6fa01f6fef7e6ede809f601ee07fbf2eae609efef0be507070102f9f9eff0fffbf7f9efe3feee06e8e50af902fb0ff401faf70809e4fbe1fbf115fe06f102fdf0f8d6eff7dbf70209f5fa04ecf3feedddfdf0f2e8e2f7fdfaf6f6f001eaf404f009f402fb08f3f2f8e9feff05ecfe05f0f8e105effbfcf3fde4fb0103fd042401010213f6eafef806f6031af7f91f1a05f40df2f10cfc0a07f9f2fef4f70c0bfcff100cfcffe7dc0be50ae5fbf30aff12f4f3fcfff7f8fefd16f3f20ffd06fc0305f9fefe0a09f502fb09fbf1fef5f7ea0603f6fe0506f6fff3ff080afd18fcf80ceefafffafe0d1202f0f80e0b14fa1bea0c00fa0e18fbe10c14ecf701fce311f7fc05ffede11f0f0606fd15ee030ceaf2eaf405001ff3edffdbef0f01d5ed020a3815effe00ef0af205f5081507ecf9f20bf3eaf702dbf5fb16e50efafdf4120c0718eb200e0c10f8fdf50c060cfc1f0403080f0201f60e002abf01f6ffe3fef105151a1d0df3f1f41ae1100418fbf70426f9f20f0e06ef1afa170000e8f9e3f2f9db030d3af52102e8f9ccea00efffe00c0efb28e6f01249f5f611e8150c07ed15ce1821e7fe0af8191601f5f7f7e80e081ffdeb020ee8042206eff402e0f02cddd2df0a0aec31eef701cff1161f050a1018e2181effeffff7e5e7f430edc2eae30ee21be8f5ede0280834f70b12fd0000e215f91f23f201e7ffeafae2ea04f607f2f70feeffddfefef6e4fef6f5e3090403070de005f00502e4f302f501fdf1e7dcf9f8ed07eff9091efefe09f503f51bf508de02fd0105f407fbf8f70809dec7f7f3eaeffcf50301efdbf4f8fefc0400f0ea13e9faffe40803ffedd5fae7ff02f6f9ede8f2dff501edebe5fceffcf6e601f3030aedfcd901eef801fcf91500fa1ffae50af7240200ebfff504fdfedafeece20ce105f4f5ecfef90f0cf3fdf814fae3f8fff4f6d8f3ef03f3eb00fbf70702f7e9fceef802f3d8f7f0f205e3fddcfbfdf1f3070e09fffdf70be4f7dd0bff0b09f7f6f9f9fdfcecedf5f8f1f900f3fb0601dbf8f3f501ef09fc08f5ec0204f7f9f5050d05f5eafc02fd09ff08fb0b070a01f40600fa060807fdf201fef8020bf9010807f8030afa00050907fcf609fcfcfa13f9f9fe04f80305fdfd000500fff4f9fe08fcfbf3fafdf403030bfff4f0f6f0f702f20206fb050407f6eafe07ff07e00407f905faf8fafb0ff5ff0003121dfcfb00fdfd1bf602effb01fef906f9fffcf9f70c15fd03fa0004fff00115080bfd0b0718070905110606fafaf70507ec17150516160efbfd0cfef507f40a0104fef2050dfe0701ffdffd10f0f50b050cf506f7fd100a0416fafd050d18ff02fc0f13001207fffff8f3040c18f7090dfe1cfb030007f9eceffcfbf5eb02e8f8f7010218fd1109f70a05fcfa09e8f8f6f9f51716f119060c04fffa0006edfbffedf610130d0ff1f9f401ff09fdf5fff3021cff32061c090306270803fcfe04f01010f60c06f802fbfaf50015fafaee0d120220fc1e0b0202f3fb080811f9e3f5fd0cf4fd0c0501f9fb08fd0e04f502041711edef181600f2fa0bfc01defb00ffed1612fc04f4100af1f804f61ffefdfffbfff70cf7fae5f1e905f0e8f108fbecfee9e4f7d002f1fce5ffe2ed03d7fd02f4fef1fd04fef5edf6ecf8f6f9efeef8e0efeaf607e9fcea10ec00ededf5f3f8dbe50ce4eaf0e002f5f200e5f3eae8f0f1eceaf8d6f3fbf5e00a03e9e6f6f3f8faebddf006ee0018f8f1f2f10ef8ff07f3edfaff01f3f2f3edf2fdf8f8fce8f9fcf9fb0afde60307ff00e9e102f1fcf8f6eb0a00fcfd08f5ff05e0faf2fe00fbfb06ee0ffcfdfc14fdf6090005f4010af4eff606f50dfcfc06050df3fb160ffef0ecf20ef40ff300eef80904fbe9f801fb000bfc00fc0003e104ff120706fcf7fdf9020cf403fa1f06f602fafdf905ff0e03ecfd00ed000cfee60bf9000de0fbf6f616fd03f407eefe05fa08ff0603fd02ee01fa10fe0f01060906fefeeffe0efc05fb04fafafef6f407ef00fdfb01ff07f307f6f6fafafbf7fef4e60605f500f106f601ea02f4edfdf4feff050af30a02fd04f5f4fbff05070df5f4fafcff0b0cf4ff0ef2f909e1f7f102f3f8fef60a0608eaf4f70400f2100afd01fbfe00fc0b09f0f7f1eeee091bfdf613f5f2fde700e80bed0cfae010f6fe21ff18f1fceef117eb05f8f7fffb12eeeff7fdef0f05f7eeeaff0afafbfbece7040c030eef06f8faf4f90efdddf0fafc07edf6f1eb06e60e0efce304fe08f8f8f5f4f1ff02dfd8f0e602dd07fa140ef50ff6fbff09f7fef4e0fd0aedf414161408f303030afeff05f8f404ea0ae5effff304f1080efc13e5e0f5f7fa02e8ff0c00fc15f0f9ee0cfe0409fafcfcf7f202f7f8f9f50b07e5fd1311f00f0204f9f7f8effc0afef5f8f0f9e2fbfbfce9180003f6f604fefd02f3fa06f1fffdff07f60febe7f2f502fdd801fffefafdf301f6f6fc05f80501ef0804ed09fafcf3f8f605070705f00205f8ef0308f7ed010df9f71efdf4e3f4f5ee1006e301101efc0414fe02f3030f0307eaf6f1fa0514fae2f8f7fe0b23fe0bfce3ddfedbfff5031208d4f4df01e5f3dc0006ee08edf7f605fc0af9e1efddeef004f001000707f8fcdcffe4f0f500f3e5f904e512f21be9f312eef2f213f5fffce6100bf1ef010d1303f7fe030bfb1d04d7f004f30efbfc0601ff010302f2f7ebfd0203fbfbf70304fa020afcfe06fd01031305fdfffef600ecf8fd04fdfefcfc19f8fcf7fdfff7fb07fc0706fb01f3f7feeef0fcf9fbf202ebf8ff04fef203ebff07020712ff0d08fbfaf2fef6f900f0060bf3f502e8fff2f801fdfefa04010eeaf802fc0afe06f908fef7f80002fd08fbf402f1061301fb02e9fcfcecf90103ee10e7fff5fcf6f9ec040b07fcf106081c05f9060e0f00fff903fee7fbf6fdf4f805ee0af7f3faeef6ef03ffeef2ff29fcf3fc04f505faf707f903f8fa0cffeef503e703090701fdfdfbfd100bf7f2fd01ec03ea05e604dff600f9fe03fef8f3f9f8fc0e00fded05fbfef2fbe50f0af8f2f6f4edf0fcfafef204f3f7ff0106f51103e704fcf4ea0ef9f0ec0c0df3f3f5e4f3070407ebfd0e07f706f8f7ea10f0ee02f9e8ff010106f00dfbfb03fb04e506fafd06dc03f7effef704eed9f4f6e7ebf0effd0006de06fd03eff7f5fffae8fa0b08fb000df5fbfef3fb01ff03fe0bef05f6ea03f6f3f4f7f8fb03d90806f0f9f5eef90d090602ece707eb0e02f2f416070c01f1fd00030101fa04fcfaf80cf404180bfe04ff0c1000fef901f20606f60500f2010302fbf3110c04effc04fa0213160c07fc00030508fbf2fbeffb11e80812fbf7fef9ee0a00f901ed04111becfb12f8f7fbf006fbf9e5f9fafcdd1a130f02f8100bfdf5f6eb0f0501e7f90afaff02e2f1f704f901f10e0503f4e7dee7d0f5f806ecef2feefa00fefe05ff0af0ec0a08fa19ef07efeffc0e0dd7f3e8f2ebe7dbfbf60000fa04fb01f9f200ea01fe07f001e804ecf90df609f8effaedeb0702fefcf8ccf5e8e5d1efea01f8ecf11d0ad6e50405e903fa11f7edeb0b02e6e5e903f1fef6e40e05fdf4d80b0bf2ea0501d4fae9e70210e6e9031af70c03ebf3f6f50ae3f4eff2ef04ffe9ec01f02308e5f8fbf7fefccdfe0af10717dc0818f7e9fefdf10afc01ee07fefff802fadce6f0f205f51be5e5e2fc172018000bfef3eef70def1401f1e7e2ff10fd0fe708f5f9e1f5f808e1f0031f02f014281621fbf6171611ebf40f04f5ff0d0a0cf8f6f40adbf8e0e10102ddf80801faeff5eef2edf50de105f8e90c0401ea0a0eef1c00f0f1d6f8fae4ece300020614e9f92c1eeb1002effefd00f306fce1fb1b09fcf1f3f807f2fc020be1f20c0903f8f0e70511fe13ff0d0502fc06f8f202e7ecfef5fbed0ddf00e9fdff08e6fc0c000e15e6ed0902f3fdf2faf9f510ea03eefbdceef1f2f904f6fcebfd0bfaf0fdf6f7efe3e2fe03e7effe01e3f8ecffeff909db060104060500f9fff1f509e7f2fef5ef0ff4d700f1f3f600f9fcf30dfa06dffdeefdfc00f908fff9fff6f1ddfdf9dcfb03fcfe0ffdea01f9eadeedf2f2f8e9f1feeafeed05fbecfb09f903f7fcfafed3fc01f3ef07ebfe05fcf5fedaf3fdf9f7fbf0f5030e070211e102f307f8fff90d0607f605f7e404ea0e1401fb0106e40dfd0107f6e6ff1af3fc05e7fb00fffc0cf4040bfffe0df90719fef8fb0303f3fdf503fdfc09f0f708defc03ff0b0601e302ddf5f00f07fd02fe00f5fd090be3000103ee0fd6f8f1fefd00faf70f060d06ebf00b12f9feefeffc0402fd0bef01faffeb1efdfdec06fff20ae1f605fff5040f1007e8ece4fb0ffc00f511fbf6ffec020d19f60bee170d0cfd1509f4050af530fd02010705de1805fff810f40b130b1901130f060be90cf217fffdf0000bfd0605fc02f9dbfa0618110c0ddf0e20fafd0c0b0cfb031416f2de0812eee4f500090df511fdece4f3fb0ffe09fafb0117fdf60400f9f203fae6f7fcf9f605f7f1ebedfdfce9f0ffe8f9e9f203f5f5fdf001fff1f5e5050500fa07f3f5e802fcfef9f2ef0708fcfe04f4ef03fafdf5f5f70ef806ecf2f3effd05f7f7e2faf2e7e403f9050afbf6fff5f7eefcf6faf9f800fdf204fffcf2ebfff0e3fb02fbf5edfaf904f5f7f3e8f1030300fdecf70403fa00ed030ef809030b050013230a03f204f405f7f01622101fff0ce3f503010af40ae808ef0410f7e8fd02022317dee609fc04d5040111fc0ef80dfb1404eaf6fcefffef06ed03eefaf8f802fd08fff91f150e03f30701070d07f0eff81812eff71bfb06fe05070300fa020ef9f101fe050bfcf0f80d12040d080dff1d07fd0511f3ecfaf3fa08060215fa01f008fdec06ec0b01f310feff07fd06ff01f7f4f6fd02fefde8e7feda08fefce906f807fae8f4fcf8ff05f2f8fae7f703ea07fef90400f305e9fbfafffdff010bf115f7f8fcf9f409fef3fb0ef5faeb0408feedfbf5f701f70501fdeb0cfcf706f40afe04eb010cfbf7ff161df309f8fd0dee0bf8f3f3f501fe0b0101180c0dfb020c0f10ff0b05fde1edf1f10dfe0313fd040f0fe20bf806f71004220b02f9050b0715050618f603ef0710fb0710f5f60a08fbde100f0207fdef15fefd0cfdedee12f818f204e800f6faf5080a12ee0308e91024f8fb120c00fff109fdfbde17ee08f70d191b03f4ff09ede904e52d06f5f114f91efff803fbeafaf61bee0011ff03f2ebfdf1e8fd12de010bd917f7dcf8f3020008000007f4db02edeeedfcf1e007fde7270b05ed04f3fb1a02f8fe0df7040206f905f9fa03f4f6fe0506effef7fa01f5f00602fbfc0610f804f9f8fbf706f5e10a2aee0801fff9f4fef106f9021d16010be600f62ae5fefcea0bf6edf80b0801f1eeecc90cfd03f5f9f50717ea0efc0b10fbf8f908f9fffbdd06f1fefbf8e811f7f707f91bfefb1119f105fdf4f6f0f7f1eb000aecf91818000dee221b0004c5fe120b0ce3190d040621f5e503f112f80900fdf2ecfdcc04fa0efd0be4fc0dfd1215f90af248f9d5e7fc07fb1bec06f2fef7f8e3ea0ae3dcf3ef04050a12f9fa131a0df90503fdff05e301fef5e3ee130600e8fdfbfa000ef1f2060c0aecfd03f20b0d061f15fc1a0afcfb00fcf7fce3030a17feef091317021f0213f310f7d4f3160815eb07f30c080cfaf20000fcfceb01e9fffb00d901f9f90515f005fcf50608fd01ff2400f4ea0d03051d01f5f5f7fffffeef0ff6ed07f0080bf41df9fef60b15020c03f50801daf913fafff8ffececf90204f40af6f405f8e5f80401fa1405fdf7e8fd02e301eefc01070ef8ec28f5f903f50300f30ff70404f8f2f718f6ebf703f3ee12fffdfff7f3ff141809ec00f6050c0afa02fc07fbfcf6fef0fb07ff04f805e60be5fa03f9030a00080b07fe04fc0dfa01f5f91a04080cfe020c00f7f9f70202f20702ea010400f602ea04fddbfafde90003f1fee9ea04f6faf9e6fef9fa00e2faf8fff501f90bf701f4fcf5f8eefdf705f8f8eff602050107f008190afddaf8f3f80a04f5ececf9fee2ebf7f00608fdf0f001f8f5fc02fff8f6f7f8e606f7f9f6f5fdfaf3fcf9f6f5fbe604f9e40207eaebfffff506e601faf6fbfefdf40c01fcff01f90408f5fb04f3fcfd0201050cfe0d0efafbf40400fefcfe00fbfd0001f1f9080102ff0df20700eff0fef502f2fd00ec020bfff7fbf4f1ff07f301f3f7fbf7fd040606ec0af9f9fafa05faf5fdff03f6f9fa02ff07fbf8fa09f4f6fbf9fdf114f8f6fffb06fb0ef9080c020000021cff00fc0807f60bf5ef03f21500f8f6f9fe03f5f1edf0fbf50f2905f8fceef2fbe2fde709fb0d07fb2ef4fcee08edf0f8e90608edf1f80103ec00f611fd06e8ef00f1e6ff02fb02fd02ee12f5f3fefa0def07f9eee4fae5ff06000b14fdf30def08f8081201f1fbf7e8eef2fc06e6ddeafd04f0effffff5e2ef02f8fef5eef311f8fb01f8f204fd0205ec021d0908f500e8000500050d25ff1d0bfe0cf00806eced0cfe10060a0701e325140cff000d03ee070901040cf50d120111f50b0c0f020af904fb130002f30bfe12f91407f90ef3120ef5fbef031e14ebfa0800fbf2fb170113fa0efd1c23fd031c0df023071b06fdf20111f1ff07fe1701e70e03f2ec01ef24fdf806f506311a04f00efcf701f5fafc040c0ffee304f0f10204ed1802f504f7020302f7f809fdff03ea040eecf9fdff0a04010afb19f8eceefefff80101fe000001f701e9f6eef3f700f9fefafc0802fbf6fef4f605f80a00fe07eefcfcfa06f7fffa06f3080a0107010ef7f4f6fbfa00f4f80201f70df8fcf50406f30cfb06f80f01fdfd0e01f3f11feaf7ffedfc0809111a0fe9f904200013f706f105ff09e0f5f204fef108ef02e7070108fa01fb0e0c0903ea0e00faea00fd0e05fe0c16f1ea0ceaf306f0f90521cf03e1ee01030cf4f8fd12020912f50b00100303f7e6f9f70116ee0909f7020adaf6f200f1040d07f51b100300eaee01db0d140d02030efeee0c05f20404140c00eb05f709fee0fdfdee05160f0707e1fdee0502fdf8000a03071bd30c0a28ee14ef0d0a05120200e60528ea1805fefd130fdb03fff70c08000eff0723f3040e09f909ff03f9f8d0f8f710f2f328f5f3eeecf20a320e0810f5fd3ff6151c0202e0e30ded0edbfbfcf2f00fed03f5f61dfb03feecf5051904eef80701000ae3f1f40301090af8f9edff0404110feff5eff6f403fdfffa25f3fc09f6200b04090ff6ee0302fe03f70ff6ecf80708ed0408f6f0f3f4fb000ef4f7f529effffb02fef806f1f4fc03fe0512fbfc01f6edfefcfb0c07fefe0f070404fce8fef8f4dffcde17e8130305f2f00603eef8f1160007f5f6f20401ef00f80816f6dbf80a15fd140007fe0e02def60b140600250501e80fe8f00211160708fe0c00ea08181800fd13f7070cfb1beff1e800e914fd04012312e30dfa11e711f0070010001be20fee01e3ec0810f00906f92411fd190dfc0d000019111e0fe8031835fc042226011dfc290507dc040beffb0505faf7e4f6f704f9e8f6060019f5ef1e4213011a0211fefe12fcf4f4fc01f8031d10f30bfffdf1f4defd12091e0ff911e5fb0fff0af606e31ce80b09e900e7fcf50010f5ff1116fd01fb0a0d1ff00cdd16220ffd061c11211d13feeb00e60cfb19000b06f00fe0e2fef41204e2fe0002060a1434064f0210f205fefd1cf803f90d0d04e0f107f6c0f9f60104090ef7fc231401f90ff603f9fb080d080205fdde08ea09fd081c09040c040be1fc03edfee002faf2fc0f03ebf7fffc0014fb12f2f7e7eeedfafeff17f9fa0a0207f6f5f005fbe5ffdefbf704f21cf30beefbf7faf0050bff03fb0607faffea09f907f8e4051dfa0603f3ede808fbf6f9e7f80af4f6080703ff09121b0a0d02f40ff20404f4ff04f9ed0910feee13030afc000ce9fdfedfee221010f207070ee5f408f7f4f9f012f90c09f2dffd0201f6f00a000502ed0df7f7f8f41bfef8f60119f9f5dd00faf200cafa03040b0cee06eafd0c06f1f7fc001201fa06f6f4f702f20910e1030b0007f03b05f9eff9f9000f0209f103fd0cecf2f710f90a080ff10bfbf3f40cea03f10eff00ff0ce7fd0207fc05fdf500f90717ffe412e60304fff6fa0ceb27f9fdf9ed03f303e6fd01070400f8040ff3f2fc12f41108fcee0609f3fcf70bf8f30c0402ef0dfb0aebf80210f612f7f7fd03faff0608fe05fa0500fc0200e60407f9f40ce31dfb0f0607f8070d0a0014f1f71108ef05faf315e3f9ef03f400f8f7fee20b08f9fafb04eee70e1b0ef80320f101faf6f4eb0e06f73005ea05e5ee11fef3fefc0bfef8fa09021815ec0af5fef405ff0a02e509fb01e50dec13f70d1413e6e5f21402041317e1faf2f733070eef02030210011f1ef4fdf7eb2a3108f71c01fa13fa02f405f2111ded01f7f12deaecf901e5e0f5ee12f302f8effa26f0e50b16fff007fcec0413152a11fcfbf1e50b2b050efe0508fdef0d25fe20f1000806f5fe0c1b00f7fd1df10cfd0b1cf4f7e60bf7f71101fb0af910dff4f20d0213ffea160e050514080305f7fa1013f1ef06f9f400080d0514fe0dfe16090915150df60a042413fe03f005e725251301f1e5fa0dfd140afc041b050feb132205f5e6f3fd0b040814fdfe03f802f50d03fc060c11fe000bfefb050702f6f000f90bfdfff2e8f00f0804fefae011fef70803f0fff7f5f5010cf8faf4ef0704ff0bfd07ebfef7ff03ef0c00fc0febfffaee10ff0302fc03eee6fa150000e801ebffe6f1fb0112e914f0f002fd0001fce901050ef2030b08f8fef9060301fff3e90df820090202f9f100ecf705fc05140bf0ff05ed01f704f2fa01fe0a12030be0f3040713f8120015f4000107ecf504fa0f01070cfb01f505e903210dea12fe1110f9f51304f015e8feff0ef2e8ee0aeb0d1100eafddffe020c1815f714fa0fe90b0806f10c05101209f9f5fdfe060bfaf70500fa0e0707efe30007040bf5fc0b120fefeffaf9f702f8e90502f2f8f40918f3f8ebf1e50df9f20a1cf2fe23ee0dfe07fcff0ae80b031605e411fdea040511e9fffa05f8091a0ff011e9ebf341fbe30ff6f8f20af0fcf1fbf2010f0e17edfdd9ecf6030ff6fffc0a08180bfdfb12e501d2f5d30bf8fc22fef0fa0904f20fff1d0701fcd9f8040fe9ffe801fe01fd0cf50fe8050502f102fe00efe7f6f40df5ec09f7040fec12f5f8fc07f0f6f2ebf102f9f2e3f8dd0102f8ede8de150cdef6f3f0f406ebeefce0f9ebf2f7ffeaf6faee0bf5e90203f8faf3f9f9fe03ffebf90f06e8f4f907f6dfebfcf7f3e9fde2f3f0fdf9fdddf91300f2f40006e70fe9fa0dfbf806122ae0f4f40808f2fd0cf8fcf8f1fcf4f2fdecfcfffb07fb02e8f4f7fafe11fafd0bf5fe0df004fbee0201eff2f802f6efedfa00fbfe0902f3f4faf2feebf70405fff4ff0005ef00f5fef9f8fcfdf8fafbf9fa05f9fffbfb02f403f908fc0003ff01fdf2f5fbfc0602e7f110fa00fd0306fd06f604fdf2040708f5f8fafef4f203ff04fff7f2f4fcfff8fdfef8e30bf811f6def81605edf3ec0116f6fcfef81202100ffc08f5f801f625f80a05f20c0a02f0f212f6020ff90e06ecdb0bf1fcfcf5040d05f2f2100604f90c24160cff0705ee0114f806f6f801edfbf9ff00e812ec03fadcec07f604edfae90807fffc180ef817ecef0d1701eaf3e40508f7fa0b0d09fa0cfe050705fe08f2f400f1eef9ef01faf9f9000805fa0dfc03e901eff3f708f0fe02f4fefef403f90203fbfcfdfbfff9fc04fcfe02fcfaf9fc0006fbf5fef108f903fef8f8f40b0303fefffd00f5fcfbf2f8f6eff300f8e600edfdf9fbf4f3f0fffcfcf9f40605ee02faf2f80103010101f4fd0500f7f20300fbf3fefaf7f705fb01fb030002f708fd07fe09f60b00f31303020d10faf5f8f8ff0319150bfc20e908f701feeb12110afc00e316010c060402f9fe1100ff0dfafff505ef0419000d0305e803f9da03fb00ffebfa01f80706f7fefb10fbf3070c1201f700f80ef0f9f3f50be5f6e6f519eef4fa1910e710f7fa02050206f1f2020dfbeff615121804fef1160606f6f8f9ff0cf6f211f6edfd07ef07f0f6090bf000fefbf9031904f7ff1df2f305f5050afffbe6f4e6f1e0ecfeff05f91ffc02f202fd0af9f8e205eeff11f304f900edf4fd0e140409f7fcf3f30f0807faf3ebf9eb030dfe0e0305fdf8f1f70df0f5f500efddf4d2ffe704fffd02f7fa04faf8f3e9070ee8f3080506dc05f2f7030bf7f6f9340813ecf4ee0301ed0c281cff0718060cf9f9f5e611f4040f06f0fbfdfa0e101ef60a181f0008f61dfe001419f13c0cf2120c14deeeffefef2b0906060b0008fd2b0beaf9f60a0501f806ec3c0c011afff7ed05ee230a27100bf31962f7fb3f0d0de8ef0902efd7fffef305050b1ff4fcf718fd14ffeb1302f7f8fdf9171cfa260b09f6fb0efefaf0edebf2292201020ae708f801010efbf5f3110c1eea000e170df908fdff050f0423e5040dec300f0f080608ef02f60a11f9fb05f6030317021714f40a0813f7faedf1050f120a1ff500f5dbf01f091405f0fcef1505fa121af1020302f7fbe60c05fa02faf3fef1f006fafe07f9ecea0107f40a06111cf5eafbf209fdf7070c07ff04f4f8ecf606080c0d06110e0409f80304f0030dfdebfb01f9f6db050503ecf8fa12f202e804ff05f50a08f3d5f90d01120205ff1ef6fde1f8f9f105fd0212f111f3fc0203fd0afe0003f70fddf9fc08fcecf20217f1f7fdf104e309f1faf8fa1c07070ef10a1106fd1a1d000cf9030cf712f8f3f6f91df7160e0b0909fdf4fff4191a10fdef08f509f5f5fc011008191ff917f3f00f0a15f90cf311f70412e6f3fb0afa091a100e0f070803ef090020f70ee70e1c1203fc1d08261b0603ea06f7fb021902fcf9ef03eb0afb09031cfce90610fe14ff1bf9310916160801f523f200f8fe1ff701e80bfdee0401fffe0414f4fe1d0df1e219fdf3fe05ec0908f1fbf60404f1fc04f9ebf502ecfbfa210d08fffffe0501f60700fa080dfc0801ebf5000d02ed110bf70cf4f80d1200ff160116fa02090307ec0810000bfd00f8f305fe0af2fed9fff704e0f70505ea12f604090e04fbf9f9fe18f5fbf0ffef02fdfffbf700f900fafd01e5d7f3fe050afe10fdf70fec0204eff5ec04f9eefbfbfcf4fdfc01f8e3f9fbfbfdfef7010b00fdf7faf9f8f80600fd00fe07effe02effbf6e7f8ecfefc0109f809fcf9f4eff8f500f306fef60501f400f9fbeff302ecf6fa0aebf0fceaf30cffe80200eef7fdfcfffce5f1fe03f201fa08f2f90ff9fb02fae6eafbf3f7f104f9f6ec08f802f1f5fef9f3fdf512da14080407f80ffb150cfdfd15e9e4dc0519010a06f2f60f040df5ea0df7030e02010d08fe15fff819edeb13fdfedb16e301fc1817f502f9010a1afed415fdfbf6fa0e14ff0714f3ebfc1403dbe5fdf4f702faeb0bffe7f9ea0bf6fbdc0317fdf4f115f8e0fbfb06fa11fa0803f60417e0ea1bfaf802fef711e411fdeb03f6f1110af806030ffa09fa03f50a02070b1f01f60c080801f90217f8f8f1fd11022006fb06fe2a18f9feff1701070ae1211302f2fe01f1f925e0eef50ef70502fd03141cf60af5fbf8f708081be8f81d0a0cf707051805fe112b1304110312f8d913f9faeaf8f9fdeaeb0b081601f2feeef716f10bef0af9eb1a04f7f80a0a1bfe12fb11fefe0312d91604e7fcf502e006def61af8fc08e4f5040609f1060f23ec05f40b09fee2eff80403f1fedbf7fee2fd0ef8f8f00402f6fa0726f7f0f9fb0cfe0eea0b101103fcfae5220018e90117e0f902ffffead9edf510f7050aecfffcf0e60c3018dddb0920fb060606ee0507f9060cfee9f60719ebfcfffe04ed1aed06f200f505fcf9f9f202f201fd16080ffa00f4f6eaf1ecf8fd10f60b170a0afffbf602fcf5050709fffe12fefc060a0df41000fcf6f90906f40ffc011d2108f1f900fe0303f4fd03ffff030ef8f8f20af1070bfd04060404010004fd00f6fef109dc02f0ffffee0302fbf80308fafdf2f20d0f07f1010503fd08eb020c01da0004fc2402e40419db140efa1300ebfbd6f6040bf30af200fbf7f4080b0004f80bff12e40916f6e0f1fb200609efef1e07fc00fdf50c1508e80e010dfcdec60af9f6eb02ff04fbf808dfff03ee0eeb070011fe02fefffefbfd16ebee0800f30a10e009f812e4ef03f00af705fc08140f090eeef7f10705f7fe07000908f9050204e61912ecf700f40f030d031005f9fa03290113f60b01140dfcd7fc09060700f9fb0403090105ff06f9101f121600120b08f601f70604fe0202ffff0508fd0af3080c02f6f2e0f5030810f4fbfc1e06f317020aed12070e0b04e9170a221612061f0a12edf21704fef81bde0e211e0c0ffef811fc001101fc1dfc14ee12ff120afce31604fff8fb120e05fdfff6e7fdee09fe141912091804f5e806f5f404ea05fff6fe1c07e605fff5101cf715e708e5eef2f5f50616eeee02fbe40afae1f5faf201e5eaf9f1fd0ef509ee08e9e601f704050502f902f6f9dfeef7fff3e1fa27f20ffefe07e10eeef701f8ff0612eb0014fe05eb0f1a0d1500fa0af00d08ee00f5ecde150f06fcebe7f7f0edf50702ede7fefb09f604f80302f5000203f5dffafa0dfcf204f1fcf902f5d1e3000dfafcf2eaf5fef701f8edf9f2ef06fbebfae3f1f7f30115f2fc06e9f8e201f0e4eb0103ee07f7e801fbe0f901fdf0ececeaec09fffbffeeecfdfbe9f709faf700ee0701f5fe040cfa04f4fffdedfaeff4fcf9df03ef0707f4ea0406f7f305fdf9ee0bffffec1503f020fe0dfcf6fcf1f5f102f208fbe6eae616fff5090aef1401eb0303e6fd06f4e803d004f70dfdff04fefee60305f6f00613f1f402e715f303faf5080700fc06fe06fa030406f9e5eaf3f1040afafadbfe10f2ef04ed08f125ddfc0908fa041c2afcf2fd050cfefa0ce50bfdedf6f5f10201e3fdf402f4faefe2efdbfafcd7e7fde3fadee9f704fbf4f1f7fe02fccf09effc06fbefefd2f3ebe9eceae1f903f9e5f6ddf1eef4f709e40501f5f9dcf6fbf40bf704dab3f1f7ccdb08dff5f903e3f2f4f1fbf6f7f9ecf4e102eadcfddef0f6f7fabef9fffde9f5e6fb0ae8fafddfeaf8ee01f8d902f4fffef604e9fff70400f40cf3f802fb0ce5f8d9dffef5130b02fbf405f30301ed0ae008fb0209e6f41115fafdf0f0f303f2eaf1ffdcfcf8fc0def080f130ffc06ebeb08ecfeede6fcf605f8fefeed0efcfc06f6f9090e0cf5f6e8f7e3f1f0eafcf8fc0f09fdfd0fe5f316070e00fb080e00f0ee0cfbe91020f9f5f9ee09100704e2f200fc09180cee0a10f20d020b0909edf60101020beb12fa0309eff60cf203f1fc06f8fbf40900e301fa060e020610fe0c1402fb0b0a140d0aff090818f703e90e08f4f5f8eb0ef60403ffe1fa060b141a0c0301fc0d06ff020cfcee09fb15060a090b0f010cf9faecf5fe0c160402090610e6d5fd05f8f9fafe0bfa0401edff13ee09f5eef1ff02f90d0bf500ecf609effaf0f4f7fef405feed20faf8f2060002fc07fef7f3f60401ed00f1feeef2fb0707fff2fbfefff8f7f3f0fd00fffcf0ededf50beafcf50aeff2eff8fbff0ef9fd03e605fafb05e4f7e3f107effefaf4fa16f4fcfb0b00f2fff609f50207fef8fdf4f2f0f8ebf4fafe10f3f8ec0201f6efeeecedfd04070bfe100f080c0806ff110b16f3031d0c00071410eb0218f518040c01070109f80c0e09fe001d07f7f400ec13fbf8f91305070704e30dffeeeb1904060103f20502111f10f4f8ede80610df2010fd06f9050512f203fe040e0afd1bf71bfc2112f411f1f30b11eef904f50e06f5fc0b0c0322fb0204111a020734eaff031afce8f9ff0013f722080df4fbf31f06f0f711eefd11edd1f9e5010ae7eff705e2fcfa18f5fbf32406fd031a040b15e902fb2a00fd0304dcf900fff4ffd9050217e9fce9f10400fafffaf721f20b1f05f3ff04fc1cff01f3f1fe2712ffe525221bc80818f4f3e3faf80013222007ebe00f0105ff00090e01f7f8f5f911fb000f0407ee03f5f3edeee2fc05f3fb10040a10fff5fef3fff70dfde7fff60c0801f2f5eb0105e41c0109081301eeee08f009f10ee208f001f411eff7031af7e9fdf816f4fde904f3040c180f03170001f1f20ffc1af8f6fd12050dee0aed13f400ec19940c02ee0906fdd416f4ec11fff20bff03e90903edfa1500fff403e000fc07e6fc09f7fb04f9f4f011fffc0a16fc01fffc160500fbea23eef80ef20cf1f4ee04f0f1ff000300ed0404fefef80d1106fbfcf105fbef0708fef70410f6fe050413ff14f9f4faff0f060e020006080efef5fe0ef3fbfe140c0d03fdf000fafd01fef001fb090604fffd06f40701f7fe12f90ff80beafced0cf7fc0205000a0c04f3f4f1f0f1e2ed10e7e7f41206fcf002dbf40002e9121601f5fc04feef0e130d0b06e816180505e80df9fee8ea0f0b00fae7fefb001bdd1afa050128ff1003ffdef9ed05fdfef8f6fcda01f6f5fef004f1fdf100f2121a04fc01f401e4ff02f5f6f913e3f40607fbf503e3f4fb0214f4f60fe800e7fdf407fb1501f10208fbf114ef06f9f10c03101f02fcdd01ef0efe091005110a050cee0009e90f01fafa02f91afe03f300f8050b05fdf408fffaecf7fa03f910fd0bf9f203f3f701f6ee05f7effcf90107000ef405ede0fefa0d0602060311fcf6eff6fa04f3fb0312ee01fbf008db13f7f9fdfb040112f3fe11060cf91e0a050c00ef19fc0903e2f8f6f1fa0718fde71a04f6f2fe06fafc01f2fbf914fcf309f60216f5efecf0deea03ef16f3f8ee02fa00f0d8f208f7f303fcf6f5fafaeb05e400ff05010bf3f4141310ed0a070103100102f700eff2faf6160303f7f3fff306f70300edfa01dd0ef108ef12fffefb0afb0f05f7f9f1e2121209ec1705fed3fcfe130d05f9f6ea0bf622fd0ee60307f1fdf10f02fbff11161109f0eeeeeaf902fff71107032ae6f61017e802e61d01fbfaf810f5f907f609ff00110f0eec1303fef0220d0fff0d1b080c1e04f70008f908f9e9e90016f5001d0900f4f7fb0d070508faf1102ff80113fc12fff702ff0ee51603f706f80b14f204fd03ece8f7ef1103f5fbfee9f702f223fd0ae306fa01e9f7222a00f01e1428f9ebf803ff1202f2d204080621de071415f2ffed0c04ff02ea13f0f8ff0129eefc011604f609fe09fa1606fce80f0efbfe23f9f50a0af2fe19d8d404202a064d000200f304132d100f06f91333fded1d1afef0f11eeaf6e408fbf1ebf9f613ebe60d0b12fcfd14070a0105f8f0f9fd09fdf100ff05f8ff04060201fff1fe060cfd06fff3050ff803fdfef60005050100f4fafcfd0cf80003f905fd0201fdfa01fb00000008fe0901f8fd01fb01f9f3ffff06f808fbfaf90007fe0afe0a070609fd02fe050200fa03fcfb0302ee0008fcf3fff6f90401fffefaf500fefb00fbf50201ff000e000400ff03f60306fb03faecf1fdf403f3e302faf5faf6f1e0f6edffec05effee404ebd506fc00f4fc00fbfaf600f8e5f0f807f3ebf6e0faf2e8edd8f80600eefce6fef3f5f6f8defcf6f5fce6f1f9f0f7f1f1e4dceceae4e4f9f405f9fff1fcfae8e602f1e9f1f2e6fcfde7fafcf3f203eeec00f4fff3f8ef0800dff701eeedf3fbfbf5dc02fdfcf1f91f0901fdebfe0bf50502f20805df0e04fefe04ed0409ef0cfb13ffed19ec0d0ff9eff606f91efae801e01c1408fa0ff9de03fd0301e102140212f005f81be4e5ff0b13f707ed03eeff0b101f000ef704fcf704f302fcfd0314050c100f070ef0f9de04b3f7eef9faf7fdfb110cf803faf2160414f40efbfaf114eff1f60e01f9f8e921f80600ecf60f06f70a01e9fbee2b020b0a090c04fbfbfbf000ee00d8ff09030610dcfff101fa20fdf1f6eefdf5efdfeafbff07e8f108f2e613fcf20aecd100ecd705f4fafef408d40a12f0d709150905f8f703eaeee1eff40709ecff2ee0f105e911f815fc09fbda0b0828d606f0f7e700110e04ff05f80a0b0821f00b02fae9faf903f8fbf8fff1f3fa04f7fde9040502f501f5f501f702fef905f5f706fafcf1fff8fdfeffeff2f40003f8fbfdf105feff0204f6fcf7fb00fbf0fdedf900f2fc0501faf8fcf2ec03f6f2fd04f4fff7fef7effeecf604faf503f3f8fa0102f8040000f9fe00f508fb0501f6f8f906fb05f7f7fd05f9fff803f7f5f5fb04e403010601f010f913eef0f40af6dedff9f600fd07f7e2021f12000014f1f205f80ff0f7f1e9f7fbfcf706f2f5f40b0e01ff0df6050d14ed0111050dd4fcf8f20ff813f7f3fdfce9000af804ed0b01ecf2ea05e118e0f904e6f1fb05d6fefbdb0def7307ebf50d0b0f0e01eede01ff03e9f6f101fdfe09f70cfc15f6f600ebf2fff6ece8fd0ee005111b1003f4f8e5f9f61cfb1105e000fcf308fbfeef07fbf802ec01faeaf1f9f606ef0efef520fcfaf104f8fc1b0fe408030603e4dafbfcfef2f1f7fffafefe05fcf2f50b06fc0a0af6000403050af6f6faf11011f50113ed0e070cffdcfd0200f00008051a14ff0bec0b0608030f08f6f404ee0b0207ecec1e0513e608f80618f50c2401f5030c0303fbef01fde60800180a01050fe60b021a0405faf710fd021beb04f409fb17ff11fe1404f810fd04fe12f90dee351615f2040813020f0412dbf9f304161b030b03fe02f5000c0a0f06fff909210106222e02210213fb03fc0c18f408f9f61705e90c02e8d10bf00f070bfbf4fb2e04f7150d0deb0707e00505f2fdef0af5fefe05fae6f400e10cfd220408ff0af10e0812f5fa05f711070020faf2f50910120a04001f08f305fc0f0211fd15eb160b0bfc0bfa07140a060de6fdfafb08010603ff03f9fc06fe0217fcf603fc04f2fc04fffc0efa07fe02f6fb0ffb02fcf518efe808f7e0dc0df70f09feedff011708efeb070503fc1be80e030912fdf9eafdf3f30fed0003ef01f10a050007f10003f602f2f9fbffedeb03faef03ec0518ecfbfefefc0b1900070a110bff01e4fefafbfcfa03060c0801f7ec06fb00050505e1f401090308fc06fdf606051a00fd01edeb0005ff04ed0a08ff0a0d11010e03ed07fff3faf1010007fb03f5f0f012f10beef5fd0efae8f20d1a01f9eef3fbe2defc04fafe01f1ee02f8090ce60201ff0c02061708e7fbf1fe0bf4f504f50a0215e2fbe8fefa08ffedf5fa07f8ebeef20f02ed0f0c021010f400faf810d7f41defffeb01eaf3f6e0f300fcfeecdffc27dbf3ff2622d4f8fcfffa12fc04f7051d16fef60d020b04fcfb09dff80cf00508efedf70a11f9f5100f01f8fafbedffeaf6f50908fe0403fbfbe4fffcf803d8f409f4020a04daf9f7fcf813edf0f0f506fbd2f6f91df7f6f9fbe91d0406f6fdf7fa0debf70dec0109f2fee8fef2f5fafb0c01040ce6faf4fef4f6ecf4f1e1eb10fb0df601e6fd04f6ec1009f502fbe2fe1ae7f203070505000701fff904f5f408ff20fc0bf30811dee9eaf00503fc0604e901f8f718e2faffde12fafd0dd623070ff3eb0bed05021706ef13eedef9f921ea260507e3eefbfef4252cf2072107faf6fe0508ff02fee70bf625250c2418f6f7fb020509070b001e0117fd10380fd22ef114f2f615061608faedfeeceb0b06ecfef7f6dff3ef071700e1f0f30504e70cf5f6fcf7040df4fefde6f405000408eafe05f4ff03e6f30c1af7f6fffc19120bff0104f71105f505eb06f300f60a06f50805f805f91504fb0bf1feea1df6f7030004f7fbeff9f4f408fbf80bf0e802e5fefb0afc0203010c05ff0afdf700f5fbdc0aea0bff0af7f2fcef12fee90af6170c1eede7feef04faf7de030100eafd00fe05e3f703f7f901fb0a0d06f6050001f723faf202f00515eff0f3f411fbf1faf8fef1ef13ebf803f4fafafdf00eeaf7f8fbf60126f601f9fafdfa02f6f9e4fbf90adcebfff104f1fcf4fe04f4f7f4fa080cf9f4f5fdfd01e4fefcf7e30b1afbf0fd0503fdfdec03fb080110070306060209f404e9f101fefd0a0df6fcf8f4131ae2f3edf9010fdeee07ffebef0629e404e2f8f70efbef0622000004f812f7fc05ff13ee14f104fdf91ffa08fcec10151b0907e1ddf8f7ec1ff0f00d2afe000fec0b0810e8fdeeeff00307f50f0504dcf9fbfe04f617fa060f0b0cfc1902e8120401e4030bfe00ea04ebfd04ddef04ff0c00f4e41ce60cfc09f6060aff040805f40ef1f20711fe0f00171408f60c0307fb10ff07000b1102f900fc03fc060cfaffdbf20202e4f4fa000e0b01f71cfcf90007f206120f0614fffe03030afeedf8f003ea01ecfbe7fe090b0b0d0e0a0afef7f90704fe050505e503f80cf90dfdff0011e80a0304fc01ff0303130f17fcf9041006f808faf5f8070b06eb08fbfaf9f503fa00fde6fcef05f204f7f5f9fe01021205fc05f4f007f804f4fdfdeded0aee0a04f60408fcfb02e8eb08f1f4f8ffe6fe040217ecf6ff0c02f3f6e1fd03e6f5f0f5fbf000fdf9f3fa05fdf2dcf8f3ecfbf7ea07f3f1f9f7f40002eef90cf8f9fb05eff502f908fe05fff807f2eef9f3f201f6f3f5fbfdfcf30403ffee030aeb0d1009f9fc14fd01eefef7f9ffe4ecf1f8f6f6f820f6f90a13f8e6f7f9fd0901f815f4f302fb0cf9ffedff0df3fd12f3fd040400fbfb03fdf607fdede7f41205e6fcf80c0a1bdbfae61a06fbf8fcd203ee0af2f910fef1fb17ebfceb0013f2ed003109fc0af6ef1018edfbf3ee100dfbf8110702f9f31703e012f50702f60503d81e060bfef5e9eef9f7eb00191adf04ecf6f2efebff001609f20e04f6030205fef3fb0ff7fb05f5fff9fa13f1100316f8f7f1fe0c09fa0a0b09092804e505020cf513f1fcec03e70403081825fa0ffdfcfe0afa0508000823040d2cf3de2b1302edf4fef10ef4fe02fce9e7120ef0f9f5ffea08d8e80602eef50d0b2804ffeff9e9f7fbf80d0618fdfbfbdfe6ec0a0306060b11fbfb0ee9e4eeec0b0502fdede5f4f420e9f9fcedff10f9edfef6e7edf1fdf20a05f5070ce80af100f0e3eb03e4e80cecf600f91204040eecf4f40306fc0009fc05eaee07ff08edc8fe0efbfff2c10fe106f709f1fc150dfeecd9161110e20e15fd0cfcf303f105efdaff0bf204fdf6fffff4f313f7ef0cf00a04f6fcfaf6ef09ed00021301fe07fafe03fff204000819eeff07f70afbeef60dfe010402fbfbf90dfaf51200e3f4240ee8fff8ebecf0f502f80206fd06fcf7f402edff0206ff080804f200fe16faed00f9f5ef09e70dfefa0d09fcfc071204fbf70bfb16eb0502f6f5fd04e9f61b01eafee63605f9e703fef3fce1f1fe02f7fb311d0beaf6dcfd08fef9f40803f806e9060211e90df80ffcfc0a04f7f50610f842f50807040dd908fdf6fd0df6fc061e010afe13fbe60401eb0101fadae41c2efe1209f7f7edf41724170ef3eafd1cdbff1d1406f9e70c07f0c0041701fe00ef11fdf5160af7020be908051ff6f4050d12f6d304e4f6fdfb05ef21f903f513ea1005fc11df0204051503fff3fb00f03c0c0bf8f0eef60d11f7f9080915fafd0b08dd0dfc00fa02f105fa09e8f80011f0eaf0f209e7ef0605e9e91d1006fff5ea13f5f314f12de4dffa1413fe0bf2f0effcfae416c210e6f4f800edeaf90a0403ddf60a02f4fa16f1fb02e3f6f31e03edf6fef213080afee5fa1cef04e8f5f106ff09ff0009fd0e1cf20cee04fc0200ff040a0b001303e9ebf7f2ec090aee0a00ddf7f7f3fe03f013080100040bf5ecff000e06f1ed04f70718f307fff8f3e10211f3fef50cf4fcf1ebe9f6f9f7eed4fa0ce615f51d16e6fdeef1ff11fcf7fafd0203ebf8101c150f07f605f6fa05fb08fe1907f0f20cfd05e5f812ebf4fe12f4f9f1f712e0e8f6f1fafc0cff04f2f709fe08fffe08060004eefaf0ec0ded00f8f5122002f403f406f8f10a1103ecd403f5ea09db020b050e07e6ea0b00ffefd6ffddf7f511fcfcf8031412fc09f1ec0708f3e7011dfa02f102ffedfd03fdedfcfdfc03f8f0ebf3fd12fbf10102fb00e9f9fd01fd02ed01f0faffe90bfd0400161b1f07eaf3e5f61bfdebeb120af1f307210914eaf4f315f8ef01040eee0a12d42307041d041ae5fbf0fde610fdf0f40509f5121ff2e5fef317fdecedf2f417ff05200509fcf3d603260df704ea1f18edf40efa0ee1f21cf9fed625f601d7011206dbda0cf1f00ef6f902f7f9f2ef08fc0814eee6e006f9ee0efa0f0504f6e5eae404fefff203170bf620f7ecfefbecfdf1150bfcfe0ee7fc020303f6fffbf810fce40d04f602fdfff2f501dbf1f20beefcf803f8de00ebf004fb14050207f9ebf1f7f50807140c05efebe8fe0bfddf0e0af3e4efd1fce912f0fffdff1d02060fec0411f9fa06ffff0e070104060f08d6f4e9ec0ff5f208f0e203ff1309fd0cecfe08fa18f800fef4fa0206f7f80408fefa05fdf90ffc14fff2f805ff0c0ae8fd02e4fbf4fb071200effbfdef09f9e7f0f5f806fc040f02f8fdfaf2f8f9fdf109030306faf2fc0ae9f0e7f6f6f9fcee0f17f9f60605feeeff000af60205151007f8eff1f20100060cfef80511f5ec00f904faeefdedf401eb0707f3fb0808fbf606f103dcf107ff0704e90dfa0efc04ef0807fe0703f00509f50817ecf8fd0cf606f5f9f2040ae1fc1eff1501fa04dffbf6f5e8f7fff20e0bfafbdcf60be529f0f1e4fffceff8f90d1cf40207fa1c5deeea25f805f5fd13ebffe61310f50fef16f4f8eceb15e8f7fdef100cf6fddbf513dbf90b0d1112011e0113ea1002110303f60508e41cfaf2fb0e031b1607fd1a0af1fd0508f4e9e52d02f500d904f30fe4f72c0801efff0b09f71a0c131910da23050ef617320c4f28ffdceefa02040356f10303eef5e0eb07ff0710e8e8f8f11107fb25f43902f50b04fafa29fa0ff7e029e8f3f90908f4f901f701071beaf71417e7fceefadeffe7e3fafc0bf7fef002fbf903f3eaf8f5e400ebe0fd04f7eee105f6fe01e9e40af5fcf5f505d9f1fc02e7e2d6040318e708d9eef10ff705e8f1120a09edf3f1f00214fbedc7f0f6f2ef06f9f9f902dbf804fbe3f5ece7040cdff8fce401e7f30cf7f9dc02f5f7eaf9ea11fee3f6f5ede8f6000ffbe2fcf3e1fdf6ffedf4ef11f1fd1d07090ee8fbea05010ffaf33c000a22f80cfd0802ef12f6060cfd050bf50a051402e80afe04fae30514effbf9e7d4130cfef9eef801f9fe0cfb0ce6f7f7f107180b0cf6fef2edf203e4fef90bfe04fbf5eff40ae3d5f4fb0decfff00e10eb19fdf4fffcf1ecf3dc0715fffc0416180e09eff905090b05f305ee100d09e903f1e30b05fb01fef5fb02fa00e6e5fc00ed08f703090cfbfce80a030f00fded041a08f90ef7e7fc06030a080b0919f4fe0806ffeffbf402f601140afeff0107f60701fbf0eb01fb141e0501fb11ffeffd040305f309ef0725eaff03fe05f9ef0df007e30ef9fee2070717f8df02f3ede902011308f1f2f2f817f6),
    .CHANNEL_BETAS(2048'h77c87730779177cb76ae7806779f770978a377cc784177e177397820773e78db77ac76d879417796780377b4787377a5781f78cf7770779677f676f57734781077b9782d788277fa77a67792786278ac78ec779f7865783178927838779c78147706781c7818783e772777f37845783677ee77cd77f4784a77a179087796787477b177df7807776677e879437836787a78c37821786f786678ae78317729780e776f786678da77eb798c7771783b77dd78267852774e777977a776f577d077c9785e77c4784b78b6780d789d77f277d4790a76fa783e788077e3784277ac781f77f3784b778a790677a2779077e8789e774f786f785b77c078a4777b780a77a8),
    .CHANNEL_THRESHOLDS(2048'h02190206020a020001f601fd0201020c02060220020701ec01f1022701fc020d01da0207021b021702040216020b020a021402040201020e020101f90202021c0215020b021c0200020d0217021002060205020e021d020a020a01fd021901fd020901fe01fd01ff021102130202020c020f021501f201f70206020e0216022a0213020301de01f1020f01ff0215021e020701ec01fd01fd020b01fe020e021401f80230020b0211020c021c01e701f001dd020c020e0206020a01eb01ef022501f00201020c020602190202020d02160216021801f6021301fe01f30203020c021f0201020501f901fc02030217020d01f701fa020302180204022602110219),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00d2),
    .ADAPTATION_DURATION(16'h13d7)
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
    .KERNEL_WEIGHTS(9216'hf5fefc020f0f222227f8fa3008fdfbccef260d0100f710dde4fbdcead200fcf5f32316032100f8eaf1eefe08070612050ef5010f0a19f3010d21f92520210cff080904ecf31c271ee9161ace0a0ec5020cef1b100b120ee5faf429f72cffecf7fcfbf7f8ee07fae90a121a2b06ee351e1d2b160739e1e307eeedd8ef09d7180a1bfddfe71c0df9fef2fafe0207370d0ffbe30011ef241f1e0f08fff91b0219190f33eff0eefcdfddfae6e7141000e6fddc0511fc22102f0efc1502e9022ef90a19ee0ff4e8ee1609f7fcf0ebeffdee01ff15fbeee31d081201f00ddaf3f8d3e9021b0b19fff6fffbff09f11127fd1314e6e5000711dcd4e7d11e0d18fbde02fae6de13fe0a15eb0a18deed5817360ef9efefe714331603fb0befea06f41ffbf7dafef60b2d12d905ee0b0d1017fb1108ff15120e1a0cf10304eced1ef82c06ea09fa0315faf80e07f1fa210f1f181b0733111f26252fe9eeec05fce5131a12190f0e12da0efff311212a1807fbedf8f801dadee0210221eaff06edfcf7150e082e20082d011512ddfcf701f3f40e120fd6fae1daefeeeef603f5ed1e14250ff5f71df50cfcdff004ef03fcf6f9eef10ef2f308fb00200c151ae6f4f418fc160cf20902ff0009ef021604ffd1eac30e040a2129122a02281ed204f6f80ae906d4ddcdcfefe3cbf9ea081602f1362c351b130c18060f320c1a10f6ff05e5ee121f2417f313fcecebe0faf911fcfb05f1ec1a0f11dce9e811051df80df60e0c04fffce7fcfaef17fe1302fb003029340e1cf82106fa0b1215f4e10b0efc0ef7d7faf7f8f715f703fceadde7ef18da0f09d70a07e2e6fbf20215181920f6fff6ff040bfbdbe204fe1f190423dfd7ee191919f5ee130a02fa21073011f915f1de0a15f5fcf401e521f80e16fe19ea0606e6fc0d27d5df0903e705eafe24f3260bf80e02d0cc1ffd170aeb0afa040006e6ee05091506e92e18dcf405f7f108f9fbfc051b12d71520fe17f6fdf1e0ece9220af31dfff51b0a08e8f0df070701ec0a11e014fdffedf208ebf821050704100bfdf311fe131ff6ece2120af9fa01111513030fec13230b12fbf4f712ecf21a1b08deeaf02a0cfde202df0103ef1600f60607ec210d11fe08f9f5fcfa2a163108f404faf3c80909050e091ff0f2f703130a10ed14e7051f42254331153e321856030df4fb03e5f910fe041810f1fc1dfe02031b122212e60f09232b05f31b0fe92524220df9fde70e030607030af6e9f00c0c18163031effefd04fbeb1616291b151dfde60100fe0130232610e6fa05f0ff250c2212fbfee1e8e511f6e30f05e41c00e11bfa0dfadbf9020bffd6fdf4eacdfaf3101eff132c0dfb1d08032627e32830fa0af0f707fc0c1ef7eefed90fd8ee04efef17e1ee15dfddf8f41eeaef01fde619dee0fcd3e002f3eecdf9f8d6dfffde09e225042205de01072008201912fcfb120ae8f7f4f704f9f40209fcf7fe171b07d70416fc2c0a0e0021eb0d130307e3eed30b24110a080f22194218ec2d0d0122fafaffef0206eee8e71503fee6e6161a05e70b01110de70823212f30073e03f01903fff8fd0014f8f50be9ddf32f1931f1de17f2dffd2d151f0efffefde9f7),
    .CHANNEL_BETAS(2048'h77cd77b877ee787277f8772a784c77227864788477dc76e179ba785a786f78487887782d77d37842779e78817870783077fb785a785d787f788b76fa77da77d3783c792077f1785078467a1f783978b4792c78bc788176f5785e787d77ec771178a97831779478027812778577747909789f785d786677b1780a76ca78d4781677e578167898784c7898791e788c77fe77db76b17883781578767709780578567819788377d277fb7805780b77cd77437818780878d377e478397a35779778407831785a7856773c7829788078ae783f77f0781476f5784c781577f4780f77bd782e77d7776578497723773f78a678a079cf77a4781378b1785f784478807831),
    .CHANNEL_THRESHOLDS(2048'h01ff0205020501e8022e02140201021701f101eb01ea01fd01e7022201f2020201f701d4021702180202020001f301e40217020e01ee01f6020b020e02100218021001eb020401e9020901d1020a0231020b01ec01f801fd01ec020401f8020b01f901fa01f5020201ff0218021f01f401fe020601fb01f801f002310212020a0220020101e201f801f802120201020001f601f301e101f501f30201020201ed01ef020a020202140202021701f50200020501f901e60204020201f9020c021001f8020a020d01fc0201020e01ec01ed0204021101fa020201eb01e70213020d020e0217020a020c020a01f9020f01f401d901f0021101f101fe0207020201ed),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00c5),
    .ADAPTATION_DURATION(16'h1462)
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
    .KERNEL_WEIGHTS(131072'hf6010a0404f7f3fe02f7f6f4edfdf9f401f900f0f707e8ee08fefb02f6edfe010d04fbfef8f3011705dbffe401f9f70dfaf9040ff0ec01030b080ee5f623f9edf9fcf5f6ecf1fc10ecfd06021fefed01e202fdf2ee02f6e8ecf9e3e8f9e90109e70d0b1008f5c8f9040307fdff0b06ecfc06f6ff01ea0302dbfaf4ebde1015f40cfcef1108eae6f015fe14eeecfd1c0ce8fdfdfc191ae11d04e9f4f505e701fffffd07f907ea180702d6170feafdf806f406060818fbe7e8fd05fdf0060d14f8f5f1d0f2f202ff0cf3ff0cededf9150e06060c07fd0d03edfde623f9f0f0fff5da0dff0401f5e40d000b0ddef7e9f600fefb0ae300f60513ecf90ef1fbff18ef12f10b0d0610fd1befebf60bef03eef6f9d5fa02080913eff509e6f1f70911fc0af7eb1c0ff000210015ed14f1f2fc01d10dfc15f70d09f9000d0815f723f2010ce90409fb09120c04e9f31118eb0806ef0108fc0e06db090f010511e5ecdf0bfffbe93018eff8030100db0c0ae41414fef20f2601111a02e1fb08fcdef8effae8eff8f20002d6e5e6f918e20600f6f2f0fd070cf417fff301f70201f3e9eef8050108d2e8e904ecfff0ec05f7f7f2ed0ff3f10d0e04f2f5e510f1ee09df0205fde6faf204f800fb0bf4f7f7edfdfafa1b08f2f3f404f0f201ff1c0d05fd11efea0106eff9f7eff4080bede7e30209f20803f6effaee0300e5f2edef010623fdec1600fbf2fae0d0071d16f8181615f304300afc0402290913060b1bfbebddfb0efb04fb163cf3fef9d9f0091823112124ef3ff0ee10d83033f120fafce1e83a0cf8340211f6fcf716361ff4dc1b05fd0bf20ffdebfe280ffb020d11080d06161e120aeaf80a02fef7f62bdafd15060fef0de0e40ef7edde0616fb6105070cfccce303ebf9280304d2d6eb01fbffed1208dbfb020cfc0101f61308ecf5171ee5c7ebeed4f80702140e1b09fa13da09f9f1221105ef080ef2e70ce611f7f9e40613f4fe15201209f20403e82903f5d9f9f1ffe4f1f4d60ee70332fa1cf7f2fae114d400020ad8eff1daf0051ae40efa190bfe0931f407f1f0ca0004fce7effce514f4f32e06fee1000903f300edf4102217e0f8f905eafff4f307f50710fe06fff5f0d5f7fee727eebc1e0cf6010d0d10e8fc071504ecfa03fd06020b0819ff00f4fd05ea03c7d31700f4ef021c0e19110015070d0906ee0f061a00e7fef2f9f0111af31508d0ebfa01efec040707dd0afcf31408ee0aea01f2ef15f7a6f5f10605080601f8fa12090af4f704ed0bfe0df9e600f0f4fcf8f9f40cfb0607fe1dff07f6041c22fc230205cef41510021dfedb01fc01f5ebf7fa0e06cefffe1aec0e0a041316f2fdf20dfbfff91211f7ff16e1fc171812e6faf40206f9e9efda09f7fbf9001543d9dc050bfe031800ff18040b021321fc0608fad4f308fac7feed05f9f9ed03f7060b07f2eb16fadbf2fc0dfdcdfaf9070007fcfcf40ae9f61114ee11dcfd08e0ce13f90e16f50af7eae9e0e8f7f9280dea14f2f3f4eaf3f4140c01ed02cefd24def8ecedef02f614ed0df803f4ee08f5f600f404060716e4edf1e000eb11181ce3e3d2ea14f107ebfbfc0f06f80a00f607051bf8070fe7eaee12e90c03f9fb12f7f9f20c040cece8fe160ae5f3f603140cf41b05f407f31edafbf820d812f9f2b202ed07e1f5f9eefae902fa15edf30bfffcd8f10fedfc01fa1801f007f3f62a1505f2fde2d914f9f4fee81606f4060a06f1130ef71506fdeff800f1e8f6fcee00f400080bf7d0f8110afc000501c7f5ef14180f03f1d0120f1218f1fcff0c06efe9e50c00f8d2f0f5f5edf0ebf80deefbfe070ffd09f807d4f8fbeff6fcf1eae3f80c03f001f70005fbf0e7fa01f3edfbfae5f30600f5fb13f7fa00f7e2ea07ff0102fbfc061af4f9e9fddff8f6fcf1f101f4f8fddaf5f9cf00f0f2e807f6fde3f8f9050afde8ff0bfc0b0602e106f8f102f1e10fefc8f80102ee0cfded11f7e011ec11f5f3fb0af9ff20f5edf3e1f1f517faf6eefafc00fef8f7dd04f3fcf6f9f001f61a1bfb03f303fff7fdff02ef02f4f2e8ebfff4f601f8eef604fcf306e2f600f8ef05ec21ec0415defc14edfbf6e902eb01f70000fc01f50108fffe02dde2f609f512fe04f4fcffecfaf4f4f9dd09e0dd040813d7ffed00d400ede50bfef1effeff14ed1d0a03e607170106140aeff703fe0905f2f6f0ff030df3e7f320f908ecf1fc100927fe0a2efb08120cf8e51316051fe503e1fc030cf400e823f9fbf304150cedea0606061d11ea07f5fe0502fef91d1207200209f40806fcf310ffd6ed0207f7ef000d0308f606fbfdf5f6ff0a09f039f11e1ef2e7efff01f022ff0c0906010ede0cf7e10be90312f60ff3030614f704fb0e04fb06f813efff02f21025f6ebf20bf6f4fd0601fb06f50e0af7100c0ff7f6fa0f04fe0e29f8fb2b2f0c1cfaf9f6f208f3f6fc04f402f5030f0d01000b02f0f3fefdfdefff05f42e16f602020cd8ef091fff05fdfae804fa0800e5fb051826ed0e02170ffe22f2d3e0e825fb44f612f81be110f701000509ec231ededfe3f2b0d90a4409ea141b200c13dfeff42df3fbe20de8f0f6091c0edc1e0507f5c708f41d23f826f417100bf4160d0a3b04ed0835f60bf202eb211bf31417ee1bdaf710fe00fa2af407080021f82a1af1d900f80af61ce8edef13ef181b3014fee91b0917eb05e4f21717f9f40f05f703e9f203ef14ded9fb02fd27060decef03d5040bfafe0af8f7e7eec02303efdf090adfffeef2fcf0e537070a0be303ff0108ff0d0cfadff6c7eafaf5eb0ee5e5e8d8ed0014ec0d0b07fdec01faf2f6db1904efea011ef6fafe1affdec1eb1f06f4efe4e5060b0bfb05f7fffafcf3040c21c1f50011f60d20f9cdde2831e407e8141c30152212000214bd0107e80d0df7140be533fd06e606f3120903f6b2d224f80804c6fa28e9f9f8b5fefcf7f0f70ff51416cfd4ea002af50905c5d9d7de3d21070033ffff1bf5d9dcf6c42a24f6dc07071e3a08091822ffacf9f60cf131e621092d16160011eafefced11f80733f1fa0c19f4f010e11d2004f0c4d3c90a0821d0221a1b020b1d0410e4020ed7fcf70d2c04c1d0fdf42cf71bf437ef000ee90bf40c0cfe13340250e611f9df280d0715f2eed4fffa041e0feff5ec0903170832f5e10cfb09fc192afbe5190c21f3fb1b00242e2cfffdfceee0fd090a09ec1004e102f71c17dbeadde715e3f8f43002ed513bf7052a0bf3fc00fdecf7130ff11605ec01f909fedf1003050c040b09ebf0ed0e0305040a01f60501eb2806f5dbeb07f6fcf708d4e6ec1508fa08e60afae8e60410fefa12040ef003f9f7e50afde7e1f2021f0af7f5f811020600f9edf208e4f2eb00f8fc06fd0323f8fc000e01f6daf7f90d04fb0202ccee001703f20712e805f317f1e601f8f0fffff6deff0fe0e90809eff2daf1fb01e9f001f407e9fcfaf8ccdefaf3fbfbd2efe8f6efece7fae3f8fb0103fefcf8f0f805e6e5ec0000f202d500fb06f4fe0003f0fef60801f6e5e3feedfff1ff05fdf5ece8fceeffe5e8f0f1fceff6fdfbebeff6f0eff2fce1eee8e7f6fb010addfef6f0e7f8de02f8d9e9f0e9fc1b0cfffa04ff09fe0607fb03fe02ef100af202ff08fdf915efeffe050d0301fbf6fbf717fadb11d1cc0c0403faf6f2ffe1fbf90f05f9f8f2e5ffd714fc11eef400e2f40100d1d0fff4fef8fffff91303fdfe12fc0909fcf20002faf7f6fcff08050a0e021de0dcdbf3ffef05030cebfafeff0f0e0606fb0e0dfe03e3d1fdfee4ebf90af402f8dce1fbf2f1d4ee0df600f40508faef04fb02fcedfaf9fae2e1f7f6ecfaf8f1f2e90df9f206fdf4fdecfbf607fa0503f8e6daf7fc0eeaf6f705ecfdfb04fb04fffbf5f6f602f9dc03f9f7070e0af3fa08f6fdfaf8fe19f5f5fdece6eb0000fdf2f2f1fd0ee7efe4ff0808f00af3e303ec00fde8eaf7faf5f9fcee0beff8ff0b11121b0b15fe05efeffc1bfcc8fc021cf4f6faf7f903ea11141df7fae4fc1313d90e0508182601f2160509e9f1ee1302de15f20e00010bf93405ebe9ef0e051503faf8fffbebfd24f313fdeaf8fa170cf4e406fe00fce9d3e70711f603142524e6daf5f510de220f0be009eff20e24ee17ff13ff0e05f1e8f509fdeefffaf60209ecedfefdfef10bfd01eaf7010af80708fefd01f5fa00fee1f3f6f8fdffedf7e9f6f904ee02fc01fef3f9fdfbf808fc04eae8eef3e0f8f5f6fefc05fdf9f308ecf4f7fcff06fae6f3fbf600120bf8ff02f803f5f30106f00001eae8f704fe04f1e5ff0404eef0f006f60101fbf0fef6fefe04f2f5e8e4fc0301f3250cfd28080d1d0f0cfdf405eef6061af7d0f90308eff80bf2e81d09e80909ff150204f619ec32ede90a120011f80903d6f9fde2fde7fbf3fffae6f51028f500ecfceb03dfd6e604031aeae70cf61b17f2ed041f16edf705dbfe01e0fdf507ed070bfb0219c8e7060d0a1314190efdf100f90dfb0106f4f501f712d7d70efdf8d5e8f9f2f21fef07f4ea020c0306d91604ddeef2f90013f3021ef4d5ef2d13fdd4f90aeffbfc05f60808e6080ed9faff00fa08e4ec0f1407f9fcf1f11cfad905e8f60719fdf30c0914edf318f2fad912f6f2d8fcc4c314ef0725dc18f9e818e90ce50fdf02e70ee7e5ea1c2fe5210cecfe110f23fe00c4e7fa08fd0ded03f2e7ece80ef114f5e7edf70217f0ea0707e4edec070e0c1910f30cf904e2eefefdfafe02f7fecce8f3050ffbef0ce612faf8eefbfc3a14fa0ae7f206fad8ebf90f0d15f5f5f81819fef2000bd30dd304fddd0506faf60707fae610022422ebfb0918edf7030dfbeaeadd0817fd0cdfe20b040a0b17051108f42be8fd07f2fbfd27e113fef9fcef0710ece9fefcfd260402f117fc08e8f8fef9faf0d2fdf5fce2e3f1fb09fee1000405d6f2120801fadff4fa122605e600fef50ceaeff90ff6eaebeef8f700f911cce2f7022413f3ee1ff7040ef5f8f611f5ff20fcf60aeef911f6df2317fec7ffef0409dbe7162714f1fc01e607ff0b0106f3f5fefcfdf2d6faeb17f8e4101011d9e802eaf920c6f40003fee4e1fe04191e12e4f3f609ec06dcee01f8f3f81814ef0506e8040c1df20eefeb0412093e2e0de7faf722e8def81610ef0107e1fd2116fbfffceef608f8f82af219030904fa19f0da0bde3906d1dffd02ecfaf42100ddd208102ef3e8f5d7fdec16fe0de5f3fc0e10e3ff06e206ef20e114f7f00cf9110c00ffeadd07f3fa031cfada05f404f50c0df1f6f102ff010df4ff09f30e1df81d0bfc182eeb13fd18e5e804fdedfdf2fcf9060df2080318e802f301e9f6e2ddedf309fff90e09eaf40bfbeafef607e70aeff509e50b09f2fee009f3f30afee2f2ede001fc130f12e707f804032c0210fbf207070ae5dcfcecff14070118fb25fdf7e6f2f106f6f3f9f0f4f8feebfadd100cf3fc020bf609fd03e816fd032deaf40ff81b1cf8f80717fef8ef0501efececf2ea040107f70df2f201fbf5f8dce0ff13f708f7fa08edf809ed0104dff0edf8fdfb0cfa0fe7ed02e8f5000118fbd1df0bdbf7ef1b1214eb07f7f6041f04fbfddcedf215f6caf3f0e9f4effa0205def10005f9ffd9b9021cf6ecf30608191703f7fd03ead70decfdf62fe7e603f7d7ff08ffecee12f0fee813fcfd001e26faef00f81600d7ed0c1aeffefdfadb1b0a0004fbd9e9e0f6ee1cf5020ff417132cdc0711fd23fae0fdfcfeedfa001b040e02f10b27e9deede60416fff409d6fbe61f0deaed00e816fd2c05f8f5fbdff635fd0eedf2db0e0004fa0217fff7f0f8f111f5e60218f50b0b1102dcf70cecece714fa09fcef080dd9f5f3fdf2fcf8f5020cff0b1210fefb09f70100f60702fbe90c08e8edfc0800eaf2f5fcfdeefaede212fef30bf4180a07f0eb05f2fbdb0df5f0f6f8f9161af90ff8fcf907080b12feededff1f07faf40401efe5140e06f1f4d3d7182c02f62ff720e9fc1a03dbe0e421f00925040deffb04f1fd120a0d044fe60e10daedfd2a03fffe3c0506cde00ce72729f213ea07d4f00d03fa48fbec033009331418fff52cfb1004eefbf606ed17f71800ff001b1d1912000df5d7da18221be1f50ce4fb10f419ff03dcfc14ee01cb0702134a0e1dec2b07fafbfbfc07f6ecf8fbddf1f6fcf3f5ebfa03f8f2f007fff2e2ec06f8e5f202fa00f7ebfee707eae90100edfefe04fdfc04fdf0f2f7e8e50af8ff0100e9eb0301f4ef01f1eef8f1f405e3f7f6fde8fbedfff9fdfaecf503eb00d8f3fcdcfafbeef8fbfbf8e3def4f6f8f2fcf2f3fffef3fdf700fef1f4f2da0105ecd505ede7f90afcf60ef1e9fff7fad8e5e40aeffceb05fc06edee04e509eef308fcecf8fff8f202e6f3e508f7feece7fffbff03f7e2de00fadff7edfcf4f005f9fd0a03fdfcedecf8d5fafb05f4fb0202ed05e8ffe5f8f3ecf50204f1f0f7cef5f4ddfdfddefd0002fde1eee810f4ebfef00009fcfaec0bf7fbf0fcf1d9fafde0cc060af503ef0c0b0bfee8f40bf51ed9dff608f9eb0509fc181cf01706f8e9e800f8050112f10609efe50bf3efee0614f403fefafcf6011e22fdfa0b0117f4f1fcfc08f5f8fee9010300faf0effdfef8f8fd19f90400f700020f0b0a0ee723fde0e20ff2d505031af8f6f1e6130bfbe4f9fb01f80b120cee01f31215ff070cfd0ff62df0e60210e8fbea080c0107f507fbfcfaf908150107e80303fb0305030607fc06ff060702030310ff1b0ff108fa030e020913fbfeecf3060f2211fd13eff900070b14061a0efc20070c070802f2f814fa030df60308fd0d14050a06f5ff04fb0f0afaff0702072a1ff4faff0eeef805180f010ff7f2f9000af5f70f0b1c13fdf600f4f4ee0cf4f7f60de4e1f5fffd0dfb1ae4f800f9f2030af4eeebf6fe0d0b050bf403f1fbf9e31d03fee0040500f3fd02e6f10106fef9fef804fc03ebf508f1fcf0f7faf9e7fef60df9f7faec0503f3fcfdfaf904feeafff7e803f601f9f3f7fdf5f9fcfd0701f709fd040feaf1f3f3f4f5f304dc05ffeaebfdf2ffd7f8ebee02effafdebf4f8e9e4f7fff2db0407f7fde1f006f4e9e8ebf70bdff902efdfe3f8f30406ebf4d7f2f2f3e8f5f4f2f2f001fcf5fdffe60ceddff307f1e907f1fcfffff2eef1dff0fef206f2f3f1e9f0e805e8090bfefbedf3f200f3f7dde1cff4fdd9e6fce2dfff01f5fd07def0e4eefef90806eae8f8cdf0f4c9faf2d8ecedfcf0dff7eef2f9fbf2d2f2f1c6a8f20be1e1cffefdf0e6e6f2fdf4c801fef9a2d402f9f300c1ebd8f9dbe3eef5d006f4fff8fafbfb02e902bfcde3e909e3f5d2e70dfbe3eaf1e8cfeeea000ad4f3d106c903e8fffbf7eee6e7f2e9fdb6e3f7c0f5f6c2d7f3dfcfe0caf2e4ffe1ebdaf6f4fdf10bd7f5f5e6d7feaafeeed8ab03d6dbf500f3f7fdf6e4fbfdfdf1f8dc06f501e2f7f703ecf80002fff7faf1f0f507f3eaf902fcfdddf904f3ff050c05f905f601eef9eedcfaf7f0f8f500f7ff0dfc01fde6f4f3e3f4f2f6f7e90700fafefdfaeff6fae4ffddf0f5efefd7f6fccef80aedfaff17fce6deeb03f304efedf2fdfafdf703e7fe0604e6d80703f6d608f4f0f8e0f3edfafaf6f0fd0f00edfeff07f9ebf910f7e9f5f0fcfbddfc08ffe0f1f7fef303d9faecf9fff7f4feedf302f6f6fc000301ec00f0eb0af8f7f2fee6f007f7f4faf5f0f306fb06f7e9f7ff0de4fcf8010d07fcf1fb05fff5fcfaf9e8fb03eef906f0effbfefbf4f8f1fcf1eafd01fcfdeaf800e5e6f9cb06f7eaebe8f7ea1ff8f4090cfff5f7140f0fece8fc010ef4e6eef81716fa2404edeee51de7e7f107f6f61c01e703f1f9ecf300f108eaf4edee0d1514fdf8e901fe0cfdf90e04010cf9f6fe1df1edf5ecfae7f2f60729fe01fc0ffb0805fdf0f7fd15fcedf90a02e71cee25f8f2dff4ef0ff9dd05edeaf1fff80ff2f7f90206060107dcf2fa0dfc07f2f70fff150bfccaeee7f81806ce07f2fcf501f3f51e0d152212f3dc1b20e1e41e2efbf7faea182c1110ed09f313031c15f327d1f80c02dafaf721e9f4e31400df1f020d0a10051702fb0b01f6daf4df0cf8ee02e1e3080522de1805efefe9fdd7ff0ffd060b0bebe5e929fa07f616101b073a06ffe705f5fd0407dbf8e531f41bfbf2fef0dbc6fe11e6db0017fbe9f003f0e3e6e7fee702f70b02fab7cd141afbffcde50ddbf708e6ecf6f3f4d302f3fde8ccdf1ad1ed06f8e8dd01d0fd0af11ce101ee011afffb01f409d4eed600ecfe1000fed0041b01edf4fd10eaefd2cee8f8cafe120212e501f3e1ddf0f303200ddfdef5d8f6fffafaef0816feddf0e5ff00fafdf9dde702f1cfd8d004f30ad7f0f7fee7f9f2fd00dbf80aefd4e9f8fff806d3f8eafbf707f0f0ec07f20009fcf3faf0e703dedaf1f3fbeaf00103f5f7e3ebf8ede9f0fc0102f6f302ffe107dd01f6f5efe5f3e4fbedcdf104cc0600d9e0fcfee1eee1f1fbfbe0fbedf1f6fbfaf8eff0fddee9ffbaf9f5dcc603f0e21b24f410fef9f2fb282b030f19022b120dfefbf3120114270cd1f80d0cfafa03fd0dec1b14f631e6d2eb1a20fb0e0b0cf8dff5f50ee9fe0709fe05f1fb2001f8f405f115fcd7d9eefa2710e6ebe6341610031304070702fae6e70ff3280a120a021d0d1124ecfc0f04ff09da2600ee02080303e615040708340217fe00080f04f42dfc21fa0df6b3090ffcee2ffc08ec333cf80cfcdc2b2a1e1a0c2ff4d1da05230a1411282aeff1f2f11ce5432d0f26490023f1f301e13000e72bf8f5ebf91d0af21a18170900fb1e440d06df410305050014e7fcff1e1b070efcec17301922fe211ad1d91b1227eaeb062820140efd18fce2092a02ee040935d7402121e912fbe5e3ebfd281d18e5eb0c1907fbee0512bbf1ddf4eef2f4e70cfedbf82e11d6ec001a03e7f5f6040e33f8fb06cc00f7f713e607d7101cfbd909f1250a13e6fed7fe0205e8e2000311ebfa1c1eebe20f03fbdedbf3cc06ecfc120510f7e2f1e11eecf10709d9e9e3faeb132afd28f2dc01170f17ef1dd2f0e6031300dee2dfe1e220140efff7e6da19110f06150b05f6162b040cef0430fd1af9170409dad703090cf0ff0941eef513fd10ff0a152efc35f524e5070bde1b1efd2de1f8e2e60e11e80b0610040707362a2410d223020203e915eb00fd430603001011042f14070efbf3c4d9f7090cecf505d51813f3121e05e4fd08f2f6df031a026e0a13f7f7f40c04eaeefcfdca0800dddff804f3f401f30bf1dcdbfef8f1fa0724e8c9d5070b1616ebeb08eb020ee5f3e40be2ed00ff0f01d2dd10be030107e2fcf7ccfc14f81bd705fe0818fcf9f5f612ddfae005e6fb07e906dff21d031aeefa14f8f713dcf508dbe71e0619f6f6dd03d4fff9e7f607e4f007fde8e0f2fde3cf0a0ee4100cf5fb0d0aeadfed06f60ef1d2020befe7f6f4fa130e080603eb06f314f2eefbe6fa0c020adde2e6efcf0214e81cfb06f4fefe1e13f9f10601fc09fc10070811f3f7ede807eaf4fefdfaf300f60821fcf2f5f801f00808fa01f41e0cebec0107de0bff09fff4d9f8080c00e9f2f8f8f8ffee0bf50ef40611fa08f8f501fc16f8eefdf8f2f101e3deece8c0c9e9fbedeaddfcfc03e9f1f3f1f4d9ef0af9a6cefffbf5f9d2f2d4eee7e1eaf4e5f9fafdfdf7f800ebd7ffdce0e6fe04e2ffe8f30906e9ee00f2f6f4f6fe0be6f8defece01d50600fbf1d4f2eef8f6c6ebfbd7fdfed3e0fce4e1e3cbeaeef5dcebf0e7ed01f702dcf6f6e2dffca0fef0ddb9ffe0cefdfded090616131a1718e812d9ef010ce1cc03fcf4f2020cf4fc03f008292807ebe6f70cf6d51c1204121cf5fde80114d504ebfef9f521d802f6e813fd37f9fd050fdbebf9f6021d16faf60b2502150f07eff6190b0006fbfb02f2f7f5f4ecf2feeef13424f901dceefa0c1ffafffc06e9f41507e605fd1f1af61eccfcfcf9dde50df6e7fbdffcfe0b13fafff406fdfdf40f0500e9fe05fc0d09f91401010ffff80a05f1f616ff0a20d805ece6f903060311f8e2f203031101f804f2f8ecfd060609170ff71b1a1f0e00fdf6f503f3f4f0000701ff000a0b04fcfbfa0afc0417e90510f2fc1a1deff50407dbf0f80bfe0200f2e602eb01fdf30302fc0d07f3151100040709e80b0f0af2f2f7e5031c0efdfffb080f00f20506f0f9fef9f9ff0e07ca07ff0ce1f0e7f6f10a10f1011309f3f609fa0cedf3f3fc08e6eb12040be30110f7f908eae8fcfc16fdf7f4f20e01fc01051412f9f90be7f000fff5db22f0ea0ef005fdefe8fc1804edd715ec0501fb1116f40608feeffcfcefebf301f9f1f4e5f9fdf5320e08abe8ee040700c319f8f710f2faf6f8f9f71507ded610f9c8e91102f3ff03ef0dfe291e000ae90fecf80efd13e9ef03f5fb07011ef5fbdb010ce50ff30feaf8edf91bd41a06feea09050bf3fc0ce1030d0717ed120cf402ed1acc0a0102e5e606beeff3410d01e606fd09f82af810df0ee604f403e5e8e5ebdfedfaf90315f9f6def81af1f0fefaef00fbf5fa0407f807f50bfcf3f8fcedfaf2fa08ddef09fff0fef9ec14ec10ed040ff4f91710f1fd0ff80ef10104ed050106ee08f8fbfdf5e8f00bfdf5e3f400fd0b09f803f901fce3f20614faeb1708f3f1faf3f9f6f0f5d4f906f7fbedfe060b060702f601f8fc0309fce504f7ff17e8e5f1f4f3e32312fbd1e2db0d0d0de205eee5fffefefb1edfdc281cfcff3907f8e1010804010ff60723491af0effe0d072521100fdefb13120107f42b20e3f10d1203272a08de16131803fa231fe4cc01ee08e9e9f6ba0806f628e61aebe0ecd81bcd0c1410d7effce0eaf942e301f0eef3170a38fa09e607e9fffc35dfece7eae7eaf3fef70bfe05fbf61de1f70ff9eaf0f008092a1509fdf80c13ebfff909f1f7f8fa04dcee0204dd01021d0a25f4f60502fe2916fe00f6ff100ffe16f908ef0504eeff2912f8e70002f5fbefff01fd1300e6fae20b1efe04f52811f5fafff4f7f9040509f9ebb8040af7ebe50d0b13fe01ffe8fbfb111a14050213070224e60af517180efef5f812ed18f0e802171ffdf80006160b061902ecf7eb03f9ff060706e5f702ea15f3ecfc0b11f0f9fc0b04f1fb1d1107fceff207f9f7f313fdfaeefbd0eb04ead1f7f6f2f0ea02ff0e000afdf1f3131211f3fee607fdfcf500fcf405fb18e7faf5fa1509f5e3f3020bfbfbf60cd9020103f9040209dafbf3ffeef404f7fd01fdfce602f7eaeb0704f1f0140004f7feee07fcfdf201fef5d4f601fa0803d6fd07fee9f9f3f8f901f9faf713f1fb00f60ae306f4000df105f00103fa03fe0cfdf9f3f6fe1901f8f401ed04f0fe04ecf4fc030bfeffecf10112fcf6fef2f9e6e6f8f313fb00e7eb08f8f4ffff00e0f20303ecfc05fafae7e5f4f7f2fdf7f1fcef02fcf7f00fd5daf014eeeee6f705fcebf0fefaf9f2f805fbcdf5faf705f3effdf602f3fafc00eb02fe050408f7f5fbe4fae2f40201ff08f1fcfc05f9edf5fcf7faf3e9fffee703ec01f900f00002f8feeb02fa0405d4ea05da02fcd9f50203f4fceef50af2fdf7f1f2f807fb02e5fbfbedf2fbe3f8feeef1faeaefe50000fdfdfedef60ef8cee3dcfbebffd6000803edf2f1fa06f4fdfdf0daf2fd050411daf3d9ebf90dddf5edfef8fffceeedf7f0ebf1f2eae70610f1fb130101fcf4f903e4f5fd07f5f5fff7ef05e008e2020601f7dffae4fcecc3f504dc05fee0f903f0eef1ceeb00f7e1fee3e5ee04fd07eaecf9edeff7bdf8efefba0bf6e107e4f8e3f82b0718f4dfe00b05faf2311cbeebe6eff00703e601fae7fe201cf802f2f8f7eeed3401fc2af91200bef7e1ecf6cffbe6f417ea0000eb13f115df08fdeaf608e3d605f0ede9f51623c6e61705f6f104f0c9f800fc27dd110bf709dd11f6020a02e4f2e8faf71a3d010cedd8fefb0034ed08e4f00b021cfee908e0ffe4fa1507da0bf7d90b081a0219eff8ec140fefeff2010d15f404190a0301e4f4eafffefe063ec3f0facdf91a141116071cfa12fa0b13e125321637eb0ae7ef14f509371ef3fffe0c23201f19d42512ef0fe0f6dcf0eb082ce9fe32ee162702230afe00cce3fa0702fdf23602f415ed17fe0a02190df500ef2216e66110170fffb524fff1fdf8e6d9f9050ff3382215fff5300a0b1bf70ff206221e0df6dabbfff4290ee5b8ede20526d9131dee25061520fc20060b1df416fc30f9ee13e7021bff05f40cf91e04fbec0fe5e1d81d0c012feb1b04de0bf6f3eb1a37060c05e9f9e50ff5f9de2836c0fcfc12d9f4fa12070b05f80508dd06fc2ef6d3172a20062d0e10001414e9f8011202ef03d80f0911e9f9f706291d10fdfae9f6f4f1f5fb051103f00cf9c427febfcbf00211f5fa06fbe2f6080cfafee0fb08e3e8f806faf9fbeddfff1ae7d3ebecfbe4f306e90c0006eff6081209de01ec071612f4effcfe00120e0a0debd0eb120004d5140407fff3ea10e408060a1cec0707e8bc0301ecf10607ef000bf7fff20503e6f501f8f6eae9f80ce7f4eee3fd1a020700ecf30e30edf3f5f31602ff11ef06f6ece6fcfa02f309eff7f30aedfd03f6eb08f70f16fe1bea09fc21130c0ee9d1eb02f0f6f4e80bfa0cedf8ff0f08f7f513e1ebf912afef02ed001406ecf804fceef2ff12fb14f6d8f5f2e00b08df0cedfd07060eeee9f8fafff3f2ff10fcfa0802f804f1f6edf5f2f9e3faf801fe130601f8141112fc0412f4fefe041b2df0f6f4eefc0701f50f01fcf90009f10219f20401f60f0dfc0007f8ec201c140a04e6fb1410ea0ef4060c0816fff01108fc0500f2e9eff6ddeef30600341801fc0506ef02f106f81308ffe0f507f901dffcf80012fd12ffeafdf6fdfdf8edefe4f2e1f1e200e201dd000201e3e9f904fbedfa03f8ecf9f8f9fcfbf1ebeb08f0fef1fbe6faf603fbeff8f6f7e108ece1f1f703f9f3f7f601fbf8fcfbdeeaf605f2f7e4eeec05eb00edf9f0ef01daf2f5f3f2d4faf5d504eae8f9f401f8dddde30ef0fc08f3f6ff03f0fbfc020601f700d20709e8c805f4ebf0f800fa08ea100ef5f3effee8fbf9f4f0f20903fbfeeaf4071efffd10040c07130202f9f2d8fc1019eaedf8cef2ed16ef0f0409fefa0ffff202f4e3030c07f8f502efe9f11e1bfb10f7f1e808fa02f602031002f60cf9fa0ffcfff1dfebf408f4f7e813031f08120d0ce6d3f700000f030703d2f6f708fbeff500de22fd06effc0afb03f82b0af7fcf9e70d2a13fd05361614f6f9de010efa0b0c18e80802fef91f0cf5ee31e703182f15fc2015fe00371906fcd30df52502f9274d04f4f6110005130905f31b13052902241d00e20ddff10b05fde32b0b0034f807f71c0502ffeff403e310fbfcefe00c1d04f5e70e0aefec540a04eeedfbeef948eefde62307cdeaf4f6120d17f8dfef09e4fef01cf7e307f9e1f5fcdffd01fc03070a1dfd06dff501fdf81a0c131d10020e000cf5e9f207eef1fa10fc0afb010d000df5f7f8031604ec080efbff05f1061fe5edfcf5fbf70b05ee1902f80beceaf1eff4eeffeefd010bf9f909ecfd0701f208edfcfe05fb1af40df4fafff51617031bee0ff4f4f6f6051b0818dbfa0f18fefcff0004d6fadff9db0edff2fc08e0f5311b00cee2fdf3e0040df5faf8fe0c12b604f6e3f6f0efef051de4d805dcfb1500caebf1fafb0beae304f50cf6081004f2f0fef609dceee6d20af2e923f814fee40dec14f4dfdd13e0eaf5f2ec0c2b0417f3d803ff1f49ff14e8eff3f3dfffda0bf1d1ff01f90401f9f0eef6f8cfdad3faff14d9fafa0aeaf9f60704e2f707fbe9f405fcec04ddeccaf5f9faeaf301fcfefe09edf9fefae500efdcebffffeb0007f4fbf9eaebf9deebf50703e9f4f6e7ffd7fbc9f9eff9f5ecede4d6fdbbebf6bcfa05cedafaebfceff3ef1cf3d6ec01ec00f9effc11d612e5f9f3c60706cfccfae7e8f2251809f200daeb09f6fd132dfcffe7021310faf4e5ee1e32ea1d16f1d3e6f9fb19e7e922fb02f5d300ebedeafa06ff1cf019f3f5f0e12f01f923e0e3e9e20e0e30f103e7e5e9eafe2322c7fb2e0ff321ebf4e8faec22eb03ca12f4233bf80bf40d02ebe61a14d4f0e1fdde0c1108e304fce20717ecdf032efb071c1803f6e412f00f0d01ecfdfe1cfb1a00effd131c0ce60af917020e0d00ddf7ea14ec0ff807f7eefafddb1decebc2fa0cf20ffafcecf00a090804f2f10e05edf8050cf4fa0003ebff1de8e3dcf8fcceeafff822fb14f61f02190cf7e9010411fe01fd11effd15f7060ce7e0e815fff8de050c1fff14040dd3f4f4080e07fdf7dcf5fa0eeb07f20ae507f6eb0002eb0f03e9f9edfde9e4fcfbeb04f40412061cfb01e413fa2c0ef7ecffcefa0c07eed8e7f9dbe7e8ebf1f613fcff03edcf0decf7f5f519fd030601fef31209e6fdf2e5130105f500fa11ed00ec09fef7f2080313fceffdf8fbeb14f3ef03ddf01d15ead2dcfa1bf50cf4ecd4fbca1e08fbebe3c2120115ef000bfe0d05f2f5eb0101fee9f7ff03e9f6080bec090cfb1104dff70608ddfafcfd08e5fff5ebf6f4d4e4f100f509e6f9f2e60217fdfdebeefe0ee80604f70aeff30fd4f313f5d1ffeb0ef7f5f60804fe0efa07f2fd04f0fee6fe12fc0403fafdf6111503f9fdfee60d12f0f1f902060c09eff5dd00defc092c05f1e9fff6fd09f3ece5f7f9ffdec5ebfbc5d4fc0decf3c8fc00f9eee0f6f4efd7ef03ebd8dbf1ebf1fec8f3d6f4e9e2e8f0d5f7f5fef8eb01fcf7ecfcd7d5eef30706f5d8e5fafedcfaf300edebfcf7f3e7e1d6f5e105d7fb19f6f0ddeb10f8eec5f5ecd0fcf3e7ebf2c9e6d1dfd9e9f6dfe7d3f8ef08f6fef6ec04ded5f7b6feede6d4fce0dc15cf0cfb12e0fe11f5f9fceade07f50502ecf8e51609effbe212e4ff1c030ffae7cf02ffedc217171bf00b0ed1edf507d9f4da1409020abde606efebf72b13e4f8ecccf2ec000ef702d0e608f1d0eb010a0203020f0dcef11c0309f8eaf9dbdaecf3e5110cf2fff6f720ea0bf1000b08080912faf206020f06dceed1feedfcf60411f801f0d70610101002fcedfdf7f6ee0e0009e8fb0c00fe08f9130503010e14fefe0a0102071710e107f2f809f60bfbfd02e7eb02040e16f4ffdffcf203110c17f306fe1d0d111209f9f4070f0903f2f6040cfa0df30011f5f4f009ed0811fe0405f01534240207f8fee1fc020315010af2d8050013ecf805fd041316f2030de30cf50be51a14f80500f6f2edf431e6e1f80206feea0cf2f9f50811ff191512e301ef06e11e0ef3100a0310e3e5f9eaf0e01921f903cfe30cd2160bfc0e03f4f4ddf61c01e90200efe00105f80ef5f81412102111d5fd0e0e09f6e9dfe312f4f3010c1fe4c3f8f619d917f60bfbfdefdf22fceb00190beaf906cede0321e0f405feeafe1beceef50ef5e2d70decf2e70518f5ebf9ea00010a0402fedfeffdfde7fee5f6ffe701fee9feeafcf4f90b0bfcf5e9e5faeaf6fbf91af2f1f9ee03ff0806f2eeed0414fbf3f3fbed04e5fee102ffef01e90202f8f4df02fbeffaf6dbe700ecdc04fef4f9f3eff5eefb04050514eefc02edebeaea01f2fff6fff4f4f912f60fe413f1d7fb0c0f09220e09ec1c0803eefde6162002f3150fe7c9c4f706080727173bdff4f8dc0809242f0f0021e41ad1f119d03315e915dffeefe1fcf509061ded080df80f281afdf22dfa0508ecf9f8feff2232fafe1cfdf52ffc1bfe15f4f002200ffdfcec24eceb0ef7080b02d5e30fe1eaf71310f461380df92dfde817e9f91f0eff00f3dfff0505ea0526d0fbf7e9ed1f02e209fee3f20707f6eadc13e5f5f7f90ff62c0dfc11f00efb04fa1001ee050f13fb03ea1509faf50202020302f6df0df80804f8151dfcd700ef04f7100cd61409f43df91a0fe911e708e8f8ec1ae7f3f705ecf923f7f8fef90705062f09f0e3efdbfb0f16dcdaf4f507ed06e9f93528eef1ff09171dfed21421b303eee7ea0504ec2006d2e22f09f6d1e415f00214051c0c6b0a0a04be0cf3ed0c08fcda0e0efffbece43dfefadbd40002f616fedd0d0716e3f62020e6d6100df1f1f508cb09fdf924dd48e2fff7f032d2f6ee16f6e8e5f6e70d3af21c0700110af857f712e305f6070225e4d3c50210f8f41b04021313dafdc9f3f5fbd20bcc0101eef1e9eefdfcf5f5f4fb010defe9f7fcda2acb26ebf42afcd904f5020bfa32ee02d1fc0a01eaf60b22f4eaf603f9f4eefdf6e3ee040ff1dfed0c05e30aec0008eb0ef3e71408f6cde2ffe0fcfaebc408fb01cfc8f603ff000d1adafd0702f408f4fbfdfa0ccf00ffe5d5fdddfa190411150cf3eced11f6fdfedc0804ec06f900ef0d0b16f0f7fce9fd00daf505fff5011211db101602ef1208f2fafe02e2fff20915fc08ca0c04faf1f91e0d02f911e0e7f2fef5f8f61409120d11fdfafa0316ff0f0efb0412f101fa07ee0506f013fe151e14cf031807eebd13dd0dfc0200f9ecf6f60ffee403e0dbfde906e5ec0af7e303ebded9d7f4fff339f503f11204ef0df601e8ecf3fbfc0efcfcfe07fe041fd6ea10fd030ce2f30605f6e11010f6f01113fdf7f6ed1407d000e509fc05ed1deb090618fb011df60ff207e901270f0308fc00f30518fc221b173402f3fcf40ef0f005faf00607f4e9ed04fffcf11204f1e8f9fcfdf8f6f4f502f91bf9ff18fe03fcf1f4f10506f8f40403feccd303ff1fe5f8e6e60a0dff35f7e5f8080f110def0317f11723e710e30000f912000003dfd913090410031fe4e9e7121407080007092117121302f202fd17ef04ee00f615f4fb140d01e4ef0f06ff0bdff4050ed6f62424fcfd0516e601ec14fd0e15dadc15cd09ffe6fde00e2ff6ec20f413f806f8f2eff30503efff2d110cecfb28faf4f5eff9fc0705f01907e8f5f4041aeefe1337eaf60eeff8f607100a081a1700bfe904f91711f41aeff8f7fa190df734fefc110efd1c22fbee030500fffb0904eff0fb200afaeadefa2a1f0a06f9fefbe8061d3505ed000bfcf7f90619e60bc0ed14e2f0e90603052d0218fa1c01d402050105190c11f4151af3fe122926cb0006040216f800f907e4ec0904fb08edf237fdfcfddec31fff21dc13180cd311e1ef0cf104090bf0f9f5f612f0080a051d0a06d5e3d10b0809f103fe1003f203111609feeffdf5f60400def7fc041a03fb1414d7d8f3fbfbfbfdfb03f8f7ffe0200eeb18fe0105fa15efe4f521fef5ffeef40cfaeae71000e0ddfc00f7e9ee0000fde7f5fcf4fdeaf904fededbfbeaf601defce8ea00ecebecea00f7eef600edf7efe702d2e3f606e4f0fcf0f6fdf7f3f2f3f8f801f20afd02f9f405e5fcdc0df3faf8eeedfefcf0deeeede700f4f4e9f9f5f1f0f0f1effbf808fbeaf4fe0bfcefe5fb06eeedd3fdf5e5e7f3f3ecfe03e408f034fbf50f08e30712fefb2d1c0009fb04df17ebecfef5f3ec190ffbe416fb02142305eafd231108090d1c0635fe0dfaf40df12213ff18120affe902f3f91ef403e4ff08f6181cf1010806fee5f81205faf41cfbfa17f1f10526fdf72506f4ffff05f8f1eef529150d09fd0bfef8fd370d0bf5e10e152b23f2fade0a24f41b080ad7f4fefdfcf4f0e0f40e11eef3f4f81300210803e5f9f10bfc07fe0ef3e80b17cd13f0eddc110d0d04ffe8f2ea030d09fefdfbeb00e5eafc0d01eb03f3ece608dfd9f4f014f4f8f2fa17f600fa0ef80b05e80bfbf3f909030908fdf81c060e00d5ecfb2e0bece20e0d13f9200803de02fe06010903feeeef01f7f305fafe1111d7f2f81df50adac1e60cedece4f1fe0c0af1fd0bfa08d509f8eff9f60c05f702eaf005f9e70509f812e819fefa102019fefcf0f8070cf7fef714f81000e6f01f10fcf50303f0f4f6f006000900f2fbfe0afaec1bf42a05d9f305e5e1ff0725f6fae4fb161af8edf6ef0302090412ebfbfa2110eaf8fc0003ea17eee6fbfbe502f4ded7e9f0adb9e613f3ecc7fd0bfee8def8ef05d1060a018fdd07f1fb08caece5f9e3e8e2fad806f3f201f9fff5e2e405d2ddfffa0addf7e0e902fcececfceaecf3fa08eee0f8dff7b7ffcafcf7f5feeaf4eaeff1b2e600b8f6fad4cb02e3d2eeecebff05eaebe1eaedf9fa0dd7e7faccd500a4fdebd9ccffe1d2121e00f9020bee0504fbcee9ef0df803e80605f605f7f70a06e1fefeffdb04fb08f307f90cd5fa0efc04f1f7fc090c07ebdef2fffafce8f009f709e2f51005f3f3ff1002e9ecfd04fef201ff04f6feffe3fbe7171af8fbe5e5e9d40510cc06fae0f8061800e2c3f40ef4e5daf1ee0c0e01fff8f1f0eefa0bbe00fdfaac07fee3fc120cfae30c06ec1d1511de070409f7e839ff02dbeff2031102f83af2e0f20e020d04041d1ccb0108f211e4081f12051cf223d7eb0edcf90aff130908d4fa21090e14f9fefb1800fc22f7f70314f5e8f51111f10ff92a1009e2edfd1dff12fded0006dbfd0e10ecf0ee03f7fa0013080b04d7e10cf6e9021003ed2ef920f90df117f80804eb0901160be2f9090dfeeb011cfa23fbf2fcec0020f6fe18f6161013fc07ff1325f3162fec14faf7ecf824070b00cfe212020117f317ebe5f1082311f9f518101f2814100afdfefe02f7edfcfd111a09f5f003fb09ee0621f3f910f6fd03f20a3537f8f1f719ee08ee1a1a0e00e0f510ee02ecef0a0a112911f21b01fbeefc05ed0a1607faf4ffe7fffd0deaea020ef6fdf5edf209f5f9fd07110d03e5010305e20d0910ee04edf3f002f8e9ecf6e6eaff09f6f70cf0df050013fefa0300fde61c15feff0befeffc09f1fef7f1020a13f819fffd06f503efe20605f90106f404140bfd050203fbf2070600000dfaf0060504eceefffdde18ecf5ffeb06f8f308eae8ea05ece3dddaf9f4f1edf9fd09f200faf312f0f6f1f2cfebfbf301eeeae5d3f8eaf5e601f701f6e802edf9e7fffc03e8d5f4fbe7eb01f302e706fdeaf4f9fbe6e7f5f0e003e802ec04ebf8fdfc05f8f3f6f8e9f10cfeca05f5e0d202f2e6e9e1d2050bd7e5dce7fc00eb0ff0eceeedf5f0d809e5d1e701f7daed0108dd06e1f4dfe30003e60c08f5f9f90700010f1604f205eafefdfee9e800f4f8f702fbebeff4f6e5f503f4f9f9faf0fbfa0707fdf1e6ee0ce6d903e30cfbfbe8fcec1cf6fff0fb0f1b0ed014ece712fd07e8ef07fcfc08f52114e515fd02fa06ffede9eeeb0bf40de4e8e5fdfd00fafde9f3e30108f9f7ee03f9ffde14f4f8f303f3f609000ef9f4cb130700dd18190bf6fde7fbfdeefd10f117f01efcf1edf9070bf020fc110c24270afb0a050016fb1010d415052dfe011716f1fae60311fcf004e606060311fa071316ffd711e102080cf9d716f6ed0fe903f8f70df60be3fa04f7010409efebff16ebf6f0fe030d1237120ef001e9f61f31ebece4e8f6f2effefc2e0105e6fbe6f7fc06e5fbeff90e04ece6f9dfe811fb07fb0d1aeedae80a01fff7f70e0b0f00eff8e615f9fcfaf112e70dfcffd8120a14ff00f60106f5f5e8ec0e17171004f412fbfad210e4fceeeffbdaf4f8f8120003e9e6fe0108ebff0309ef01f7d8faf42aeceafff2f8ef0e20f1fdf0efddf304f400e5e40912e2f9130dfde9e40dfc1801e7051412f1f2fbf21803f82503fdf4f305feeefbeee8ee0a06d405f9ecf30d1002130804fde5f61415fbe1db05fd0cfdf70e03ed0700f4f310f3e8ebf100faf5e9ea1e04030114f6e80a02f102e80f12e2fafe07f90df217f2e8dc10060cf5eaffe9e9f106ff05cafefa0507000af9f2f6fe02fe0307e9fff233fbfff2ece707230acc14020f05efe6e900fa060e0301e81600e0e30a2ee7fd15cd0502141adc071410062a08f912cff8022bf6f4fe16f1f5f6fff9f91404f8eb090a0ce7f20423f5f611dd01f30011f31300f11ce50d05fffdfa05e0f70df8081300c2ea1840020adcf7e602f045fdeee7e8fa01f636f3d5de10f7fbf315f50807fd0600f2fffcfbf510fbfcf8fdf8f4fc0208f502fa06f608e9f0f7fef6f0faf40df81c13e9fc02f4fef2eefdffe8f4faf2f3ed0009f2ffed02f202f4fd00effffa03f5f8010708fe00ecffedf9f2f20202f9fef3fafcf7fee6f9f809f90af8f1e0f5f70307ecfffcffecfef10c04f2f406dd091704e2eefbf8f6ebf20305fa0005e2f80bf3e8f1fcff05f3f800f50ae9ff0ae1fb05f90cf8fafeed01e3e6d4030404fdec04ee01f4f1e10bf211030908eb030604e90106fef6fef5f307e30dfff3f3fe04f6f8fff601f7fd0b0e01f4ececf2e20903e8e201ecede204f409e1ef02160e04f2d5ebfef40bf0fef9fce8fb00ec05e8d8141405fde6fc0dfb04e2e4fc10fe10e6eaedfde7f9fa050bff18fcf70813e80703f2f7091d0a0804e60ffb1221eee107e60fe0e707eef61bfb030bf70e1aeee602fa2bfd11171df1173613f412fac9fcfe19fcef14070701fa0aeb040ff5fffcf5f5fb08e4f8030df923f4edfd02eed0e0eb0e090a08fbe4faee050cfbfcf90c0b1b1707f00eeae5e73530f8e60ae2092ffdfef91d36fdf9f2f23bf10d130101d21a1d10f91409fdd852061219132ef6210a04033c14fbf9d702fe3513e6121712ebe91815010618060f160901302b25122de0f6e2fc0515e4e63f06f834d404fcfe0cda2d02fce40b122906e5d40d3dff1ffc06fc0b02450a0fe1f0f90be736effcc8080eeff31308fb220f10f50006f70407f201e8fe0001effc2405ef02f1f00c1cf9ecfb040bf4d31003dcff0d070e100507f30aea1c0dfc06ce1106060bff10f5edfa08e2fe12f1f501ffe4f50802fc0afcfa07f5e8f8f804001f081a0cf1f603010ffdf41713f3ccf1f301ec0503f704f0f2f01203f409fd13e0fa07dbc0fe0d011af7e2f7050a1c1ae302e212f7f9fe1c0bcdf5e500dafe02fdfefc0e17241804e8ef07d81a051dfd080a13fdfcde2517e9f6fff7ee0007efe6e6e6100d0af0ecfd02e9fce8e9f9fb15eeef1b1ee2ea15f0f3f5100cec0dfaff21e60ae7fdf4f6180303ee17d6ed0cf105041d0e1af2e4fd091a0f150ef9f7f20111f6e2f0d5fae42511ffe9fdf3cd25090bfa390b0afc1e4000f8030c19301603063bfccecf08112a07101a2ae3e809f902fb0a2c12042a090eebfc09e81718f61c0207f4fd150d1a191a0a02ff0a102614f5e541f3ff0c0805fdf7ff001c07fdfc1409270f2116161ecde9fbf40519e71cf6121bf905f907e004feeff9011f1e1537fe15f82719e0edf4fe061b07f7e8e601f001eff10feafb11fe0afc0b0aec00f5f7180e08f8f511180214f521015f0402ff100dedfd041017f1fffe0403e6f41ae818f101020018e8eeeb061505eef30d23e6f70fe0fcf5f10cecfaf90d370f1aedee03fc07f6fa210ddcbfedee00081c0d00ec0208f71851e9fe10e7e4e7091fc4fa10fdf00003f3f001f0e4f0f0d5dcec01e5f2dcfe09f4e7edf5f504e7fafdeec0ddfefefcffd8f7e400eaf3e4f2da0301f907f8f5f5fae3f2dbf1e0f908e4f4f5f40303eaf302f4f2eef5fd03f4fde706e0f7e3fdf7fdfaefedf0f3fbbef3fad407fee9dcffede5dee0eef3efddf7f2eaf9fbfb0bf5ee01eae400c0f8eed2cf01ededf0f7e9fdf8ffd5dfe0e7aad8dc09eee8c4f3fb03d6d2e602f4dbfffff0b3e9f1e0fcf9c9f0d3f5d5e2f5fee3faf00209fe0201e7c1ecdbe1e6fa03fce9e0ecf3f9defdffe0ccf3f406d2dfeee002d90aca0401f8fee3e9e7fef4baecf89ef6f8bfc9fdf0ead4c3e5e7ececefe0d7fb04d3fbe9f504d9ecefad0af0ef9e0ad4d7ee13fbfbfcedeefa19050cef1111f5e4061c0408f011fffcfd04020c03080d030110f7110226f31f21fd02f4f20d030615fa0bdee6fcf81d1af513ff07ed031f0bfe281507151017092010000429ed0cfff7f1fff5ff1618110101f7171e0915f006fdfef92520ff05edfef003011004fc0cd5f206fd04e905070c2d120afc15fef9f7040afef8eff405faf602f9f10f03f7fafb08030605f4f2f5f4f8faf3feee010109f9f206f7e5f80e091400f7fbf600fc1afffeeeedee030e050807f8f706f1edf9f9e5def5f608f2fbf9f604040e06100305f9f3fcfa12fd11f1fbf00205ff0609f3f1edf9ef09f416fd0bee04f4ff0918fe03f808fc0302f9e4f4fcef02fdf115f9d20100170eff03d70b0c13ece7f7fd21fb1509fadcf3eefe0df1faf7e7ea2f16f4f810d5dc1e100d1c0805ede709fd14f6f9ee23fdfdf007270d1400150605fcf0f907eefe04e4f7f21c13ede90b18072b00100deafaeffefaf713f909fa280feaddef0804f1cf0d12f70906ff0ef2050410df1001220a08f819feeaf9ffeff600fc060a0bf803fa12f4edf60af308ef06efed11190513080906f2f90d0f04f30ef71f2ce1efec0c13001b0c11f7f6fa050a0915f90eeef2ef0204011220faf03429141501000af20fe803f0010902fc0a0d0d07fffd140bfd16fff8f9f5fa042f19efebff0adee9fe1a0b210afadbf90108f8f7050a2d27fff901d9f4f6e20dede4c9eaf7c4c3e6fae9dfd407fef1dfdffaf4ffd4faf8f483ca07efe5f5d4e6e1f5e8f4dde7eaf7f7f2f8f6f0f6fad9edc4cdf90505e2fadde9fffcf0e6f702e6e7defdfcdce4c203de03ca0408f9eae3f0eaf2f7cddef2cbf2eebfd2f7e1d4e9d3f703f1d5eef9d9f2fef904e4e905e3ebeac0f5eadccbffdbe6ed03f2e0fce20603180c0401fffbf9e3f31c1107e403fff20e07001c06020d0608120614ff19ec1513dff3deff02f4120df701e9ee020c0f0dee07e3eaf60912071613fef9220ffc1202f8fcfaffeff5e5f1010d0014fc080002ee0307ef1d19e506f60e0f3212fff0fa04d7e7fa091b061006e2fffd00faeef1030520070107effff9f2f802dae30df0d3ddeaf6e0eef8010600e7effef70feceff9f2c3ebfff20103e4f0ddfefef9eaf0d6f4f1eefe01effa09e3fef8f7e9f202e1eb1102faf5f7eefee8f8f504fcfeee01e003db02e2040bf7f3f5ece7f408c9f802df0007d9f2f610e5e3ccebf5f6dffe01f5edfe0108f0feffe3ecfdc605f0ddd7fb00e7f1180813f8eafffd2411e5f9f7fd02ebf52dfe05f4f0fdef18180b2f0008eb1007050c03ff1dea1927f416d1040afb08060905f0c90cff120fff20e50cf3031018150409002a0e1a0b15f0f6f017eff8f10d0e09fe082012fe0fbe0513f2ff13ecfdf7f6e1292bfdfcfd12cbeb0f210d0915f0e019ee09f2f401f01a180bdb24),
    .CHANNEL_BETAS(2048'h7a0777017887776c78e178b278d27a31787f78957934788a78787864788478bc78e578a578ab783677f177fd782a772979787928776f77b677ba7a3b7a3977ec786b78c2792d794c7767781c79bc784b799179fb78a9784978967867799877fd792e78d6793b782b778d79cd792e781e78fe78e1773278827786786b781e78ef7a547931799a786e798a786078e479ea78d878ef78db792e79f177bd778b7849770078a6786d782678f8783379407811784678b7799a76ee786777ed77bb7843788c7827780379f67ab677e677fd78997a017704784679b277aa783c793c7850789a78d2793878c0782979fa79457a9f7847781f7820787e79b177f779de783d),
    .CHANNEL_THRESHOLDS(2048'h01fc02000202020c01f701ff01f8020f01fa0208020001ee01fe020d01e5020801c301ed0214021801f9021e01fc020601fe01fe020601fb01f4020402030208021d01fd021b02070206020d0214022902250208022001fd01fa01f4022001ea01ed01eb01f402000209022901f50218020d020501f901ea01fd02090209022a021001f301df01eb0209021802160221020901f0021101f3021601e70207020101ed022201fc020f020f022a01d701eb01dd0205020101f801fe020e01e9021901ed01fe020902360209020b020a02140237020401f5020501fd01f5020c0205020d01f301fe01f901f101f20221022f0205020401fa0207022b020802070200),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .INHIBITION_STRENGTH(16'h0000),
    .ADAPTATION_STRENGTH(16'h00cf),
    .ADAPTATION_DURATION(16'h13ac)
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
    .KERNEL_WEIGHTS(65536'h08e402fcf5f4f607041202eff503ea03e3f80c05f5fd01eddad5ef0afdfff711ebeb0306ea04fefbfefcfffce60afbe0fefde402f30c000204fcdae9e4f206f9fc06e60008ffef0b10d205f902def307f3f5fffd0f0bf5e3c30d06ff16f8f501deef0510f4f9fa020201f102f1def00112f00fe704f7fef4e8f60bfefb1205fae6e907eaf933fbfe0ed6e101f6f5cf04fcdae2f6eb0cf0ffe30814fce40304ea201617c5e8f406f6e10200e632d4eebaff12f4f0dfdaf6facc1804190ef3f316e01b0b0ef3071a09011af70bdfcbd504fb0cf7f4fdeacc0f2513dd14ffedf2dbfac2020be0eff4f8ed010d2bf921fe15f50c0217e511f509fd01c5e1f6e80b04fafbf5f7faf1faf80406000402fef306f90cf1f4f8f6f004ed030006f9f9f8ef08ecf501faeef8f1f701fcfef501faf8fbeb03fffbf0f104ebfa0000f8f60e01edf2fcfaf6fff0f3fafcebfdecfc010e0401f5fafb010dfef9f7f3f6fef1f5f302f8f7e7fcfcfffcef08fc01f7f8fef3f7f5f9f702f0fbeef2f3fc01f8f6f800d5eafff804d70002f20d1003e51df3e1f0140c1fef10f404f2efdd1feb14f8ffe914f41aeb39e211fe1406de101409f30ee9140de20e013b14e2dfe8f3e5f2f90bdbfe0ce1141a1717ec00e71cf7ed18ea07f63000120df4c704f5f5130dee0ff5fceb19f31b1f15ffff16e6d1fb05f12312eef70de3121e3eca073e1636f52909fa15c8e1ff0e08f0eee20ad0e1de0106af13de03f30df63922ccfce0161dd82ef51917e8d927d3e411fdee13cbfb01f501f5b804f117ea1adce710c7f8d400f2220dd4fccae001f4f9103a0619f2cce8eceef0f9f80bfc2ee803f7f6f101020e19dadc11dbeb0bebddf91003020bf28de1f947de2110f4dd0ffed8c8d0e9e113051813fd0d0606050e01111b0417fa1c20f50700030913031514f80afcfc040616020900fa08141305fa0e2310e8000e181b0a02f60cfbf50d12120afe05021512341d04130a11fb290310fd0306fd0b0600f2030c0615152b1014010612f8140e031303f60bef07021312f71409fe150f0309151604fd071408e40ff9140bebe7f20033f9edf6fee90510fb03f706fbfcea0bdc06eb0bddf7e901d8f706f0ff27f503eb130503e8fb0ff3f40112f618ff1805f8f5f822f0f4ccd5f3e600df04dbf0f9fafb07f7fe05e909fbecebfbe315e60fcf2000eccceefbec0931e42116f5cdf3f30d000cec0807fee5f823e7f905f7e513e719164807fb0df71012132e1326c6d6ec271715041b29d5e3161209e319c617f716f72429dace2e0918f21ee4fa3a14da2aaeb811ed03e2cf142ae606d3a624f517f205f8dfe1f8fd0e06210ae7f428a2c90cec0e011c133b18d502d3fa050a1c09050af931d5ddee13f31f2b0be81cb3c2f205e8f9f115032201ddc30b19f61018f0d62018d5d0d320dafff1f2f7faf0e6edf1f2feeae9fdddeec8e7f6fef5f6dcf4f7d2f404f4e5f2f1efeefffef208faf3f2faf8effcf9fbe8efdaeffcfef8e8f9fcf6eeebedec07fdfae2e3f5edf8f1fc03eadfd502e3f9fbecf8f807eafadfdbeafef2f3fdfee5f7d3f0ecf0f3f806fef2f3f4faf1f3f804f4f2efe1f0fcfdfcf1edebfdfc0afe051f061eeffc1d20091f03352013e5fcf7460ced3c122703fdfe33451422191acefd121a0114dce5d0fa1a181d09cf2bfd102efaed17db0ce70656f044500e1900ef06350118dfe9febd4a1b32eb05fcfa08e7eed11acbe516630f1f37c70e1e240d06fade07facad5effb0c1c0f3e15cabd12232e03210b040524f9df00dd1cf9f6ebdf18fbe3d7e3d90fece20529eef5d900e20aeffce4efc809fcf7d7eeecfff00a01bbf60dec1c24ed10d5040df4b404fe0c2dd4f3e824f00024fdebf7040febf7ec07ff132ce70bf4fdeb09d9ed08f903121dd3e8fbd5eceff3151d1bb3fae4f8ff0def322c1afc080912e900cf091819e4fc03c9070424ebda210825f2220d0e0d07eb1c0b010b00f1eef1f6011ee3d702171411150f070e0b0c03f8040414f6040207fa10120001000f10d9f515d50ee5f2080f0ef1100cfffffb0803fef60fe6e91af3eefbfee9070909f0fd08f90009fa22ece3fdef0d03f4e4e91215f924010806f6f1f806edf7f71bf8f61cfd01030cea11f61de50a10f7fef7fbfbf901f4e9ec2e070618f3f8c9daf2e81fdee3fdfa0bf03aec12420aea0d0b0c12f9ca1eda24f926f70105eef616dcdde5e233dae506f92ef4ebfe0019201a0002fb01ecf735e4fa04fdee0f28f0e50ce106fc1c012edae5f7030808f5f0e4faf314fc210105d8ee020af204260c06ed0705012532d7fee213de290a00f9f6fce3fb17f90feece07fd0d06f20209f40709e0f624f011fe181214f704db2603f411e7e9ec322af5fef70105d527e5fb21fdf4da00f1220415f329db0fd5321d03ed16dbfaea2b01ea0102e7fae6000336fefbf914f80b0ef2fcf1f91a03d5fa0de700281cfe01f8fb06fe0afdd124e9fcef09fafadfe6f802e4df0719f8faecf1e707e80aee130e0e10f9ed000bdcfbf2f9f3f4fff305eb0cf51e10d6e6ed2017ec1205f309e7f205e8ea210101f7000807f20efaf9f90407fe0d02cc0ad6fed402000a09dff7e6f001ec030f180b0cefe0ec030109fef8060ffbedf7eef20d12151705f5f322ff0b12fbf01a07ff0c13ebe40c062a0e16ee0210fc020df705ec0012fa03da06f617ff11020917eeee02f40eec06e20e0608f60bf6e9ecf70f12fa03f9ed1ef3fe07f2f622fc0dd4fd2808f7f8f7fdfcf2f60d1b08e5edebfdf4df00f5f8ec01e5fb03ebf5fc0e1e0b19ec0c05f5fe03040a1103df01f4e6fe08fc07fd02fd14f4ea06fdf8f7e615ff17eef2190f1605080ef1010807e5e9f2f4edf8fbdb18300bf9f0e8f6e4f817f7e5002a0fe9ecfdd3edd9fdfe0312f9f3dfc2fa2814e5f104f4edfae304d81a1606213e0927f9e4e0e1f5f802f409f5f00b15ddff2409fa01e8f1e716f615e224e0e71112ccf4cd0f1e1f10f6e9fdf914fafd13f7cffac80d06e8e0f6ffebe810f8e9f614f7fb3c02ebed100bf0fbf5030100ebf5f10239f2f0fcf207fa041a0a0be60335f9f3ece4f7fde8e00b1709e3e6fef63ae0f90818fef9e809f406fbfcf1040feb21fffef3e61908f907fe1af3f8f2fefb1318fc0808faef0be4f5f105f81b0cffdc09e2fd1ee9f2ffe7f61531fbf109e9fff8eb0f1504ee1900fa0205f3ff081204d923eefb0429fbf91df90cf81e06020e1b4004eb04d9e6181c2bf81ddd2f2b0f0ef8fbd805eff60cff1bf0f0e50c1ffc1e001afffae4101cf9f51f051033f421f9f10ade1925d6fc3a0ee80204f5fb330dd400eb1ee426f103091cf2f919fbb3f7b4ee2211faf6ef0af71e03f21effd7f0ff16f9d4ee1c18ca0a0e1c00f414c7f03cf4ede717f2fe08fc0a07032d23ea15f3c2fde1003006dc04ea121cc9d4ec0f0e16f21b05f116f32cf2f813ececd40225d215f7ffe2f603c2ff0fffd1ec05e7210702e91212f5d2fdf40e0e1703cbccfefae7dff3bef0eaf1f4101b16010eeb04fbd5cfe2f825f3fae0e801df0f1cea17fae5e9f800c0e822c20622089f01e4ddfd21febafdf8e4e9cb1506e6f809dbbe2006091ae1ee0ee80de00efaa111c700d909e40031ff06d70317f32db9f8e8ee0124f4f4123bee2ff300edd33edf11e3d71e07f9f5e227fd00bf0ff727dc050400240116b90a2915c5ee18feff16150acaef1418f7f3e6dee512c0f8cfed0b0805092dfddf0d1cf5091bf5fd280c15cd07e20beaf40c20060dcf02ecf1080810fef90203fd0909fa11fffcf20202fef6f50bf20506f104f0000102090df90df7150a14090af105060e030c15ff081ef20d050708eefa0607fff7fe0705fa0505200ffe110a06fa0bf6f9fcf9040b1b071308f90709fc0111070e0dfd03ea0c062420120a051b07060b0dff080efe070311fe060af708081d15fb04ebce08033ad8e91306e2f908230ff4efec14131d01020e02ebece3f999f3f803d84ce61ed21d0307f00d2be510130afd3eeb2d13f80b00101ae107d9ec01fcf9f7df2af2d9130df9f42310c41520f5cce00aed1d041b18ecb7fcf101161fe51d1ae3bd12113f240b05150e05def602edfc1816e73afb050338e7062212220a170c1f0601fdebfbf1160a1af310e90317d20bf1fc1110fd09fbf52af419f5f10be4fffc0b15d8eefe17efff0212fdeff8eff801fc1004fde4e42719f227fe1d1612e6f7221006f105f7eee8e7f409041c1f0700ce090ee4e7e31d1002e3ec0618d7061dfde1f9d8d6fef2e1d917ebe9050cdd0bc5dd01040ee00dfdf309e52bf8010c0e010a09060904f5ff0c0efa0afd150b0302010305040009fc0d020e0d090b0bf6090e100efffc0ffb000b02070e091e060604fe0ffbf80a0d1607fc04fb0619110d04fefefcf71509020a0803fc0100f901050b100f14fe091007090a05150102fb0f00fff7ff010c0a0e150efbf70e06120a0705030a06fc01050401fd040a0aecdff70b0604f8f103f5edf708f3ee08f305fff7170302f9f906fb00fd0ce0fe0c02fa02ece9f9f3feefdcfd04e707e2eb0203f9fa1209f102eff7fffd0ffbe6e70ff6f40bf9ddfe0408fe0ffaf3fcffef0af8e6fe01e413f8f9e3fc03f108fbfbfde4e5f20400f2f306f0f200fde90304f30b00f4dc2003f4e7eb0af0fff30710ffdfde10fc051ce8091003f8d81a2116f019f80bfd0904f0f40413140011ff08f725090e070dffeef2031ceaebe00118f00bfb2afb0be8d9f5fafae61802e8f6ed101a051df115f805f9f904cb160d300f18dfd6dfeb14f50408e313eedf00091a260b281b090ef4f9f10cf10f01eff3ecfbff071fe0082c1f350304efedd1111a0df5dfe7efd6f430fd170e1211c5180ee2ec0505232d2c1df5fbe5261f0fc8dffa191028e823d72206e80729241206d5e106ffe0161a220edb0b1bd4093335eff1f60ddd0af32ef71c0515f8f1caeacdf90eee2335d904fe04cc210b02efeadafa09e9e5fb10fbf21ed2f6f012132a1cf503fe0e15da0303e5ee0b06f2ffdcd222f5ee08deec16d2dad8f119c8e8d3ffdbf0ea012fe104da0211c6340917efe9f207f6f60bf2ee02b708f3f527e3d8eedcf501e702ff13d0ed07e90611f0e7ede6e1ffdf04f236f9e7e8f7fdf2eeecefd0f4154cfbf810f3f9ecbb0af9e5ee00f002edf2e9040d00192aebbb05fa1eec0aea07f003dde2e1d3e4eeede31f0dd127e9f70bb8f3fbee16c6f1c0c80007eacd02f5111eeaf6cefc10d10e0110d7d6f63c090e0707f444f2e3c8ef2bd5fecbfe0c01dcf51617e30af302e007e42901fe21edf80ef715f3d3d8f0e1f9fdfb03e4d6f40830e2f103c9f60c0bdce60cebf80afff6e40435f728e6ed0318fc1af2fce61ddefff4e1fdeaf8eaf0080110fd14e404f70ee30dfc4ff6f9f3fa0ffdb806f3f1f0f91106fe080a0cf201e71cfd25f9250e23e8f8181f1eda20eb1a19f10a0c3dfcca011807ff000003d30b0af0235a0e37f320020cdcf818e609fe360bf90e0cd205e9112922f311ead405211f313d2a1012140ff0fa0d202111f00722f10d2039cee0430858d931fc1d12f3c5122312f60bf711b8f208110dd51604120826e7383ef7e002272e042ae30617f0ed200d03130c0b1fd0133ac720e0f00aec37ed14e3f021ca1ee9f0ea2af7d6fdc6fdf91ffe121e211301e6f6f10a0d0a0e13210bfa1bd9d4ebfb27031bf7f81dc4f31813f20140f8faf712d9e6024fd037fa09f30c35fb040cebe1f0e612151845e8e8f6e1e50fe00caee5cdf7b8f2ee0cd6efd924d85cb70c14e2013532cdc6ece50c210527fd7fe4029a111e1302c4e50606b850f95ab2f60400d10f2c44f0e21f15fa59f116f0cccd121408ffe1e201c802393fce0a2819dfd005b0060ec4f018d4ee030d52e428bce6f616e209082e1be71b22ba04fe041f21e7f4fbf6f208f9f9ff03fb01fd07f8fefcfb01f8fd01fb0202f7f9f9f4fd03f5fff3fafef80dfef6f200f8f402f6faf9f301fb03fffffc02fef401fc02fdf1fbfb01f3fbfcfa04fc06fcfb010303fe01f9fe050cfbf703fef6f9f4faf9f7fefff5f3fb0006fc0708fefc0400fefa09fb03fcfb01fffefe020600ff02f904f606f31dd40f0cf5f7e4ee09dcfb2eec17e64819e0e8fd0df603ea111913fdf3ec14ff16dcc701eafdeae8efe3eeeccce713f9faebd5f7ec07fad7eb022c03e4f9ece0f12efe07da03cad500f719d01aeeeaf1efd6e4facd15f7f3e80621ff0021f00ff406d3fbf5feedd71906e4ececdbdbf911f53125f0efec0cdae8ddc4f5ddebf980e3f3c739fd0f0dcee2d9b7278e1bf9edd4e3eec016d7d67f2f10f304edbd18e9049fa4f00be125f0e5e666c6b3bce446fcebc0aa040ff816f265e604f824ab38eaf00d0f13ebeb0d3572dda0b611de2511e016bfdb0a4d2df0e917e7f3d201e12ae9dafe0b02c8f9265f0067b607fa3a1133defba925f8f2ff2d01eab00afe210cd219e517fc0bee1e4a13ecfa0610eb20f424f709070efcf3dfff14f7e727171d350efdf8e3ce1edf09d300ee36ede31cf910fc10ec2cd6e6e1f6ffee06160313dc18e3eb01df1fedd31a3612e20c02f0fdee284b17d4e310d0eaf32105130bf2e909fdfcf6fafaf6cf160924c3e80100e609e409f2fdfe1fe2f4fe0cd4efc4f3fe3e32e204dfdc0ef40d09e1ec0017e7f5f41e03f4104eeff3a61107d8262d12e2d4190502fb06feda130510f73119210fdbec150bfc26092cde0cedf9f5151a18e3040b1df3300229f21bd6d0f00beefbf11026230f03e4f80d0efde23bcde702ef160806f2ec2637de4d1ff0e753e5252b0eed022909dc0d0319e510d40cf6f80fcdebb107fee50a08031fd96206cbf01f01e10ee606161b07e6d424b60bfecf34edfad3e8f4ea150c3401371fe01609fde5eeed08dc092a08fcd8eeb9de2705efe1dcc7d0f2d602011316e520f0f2f9f9d4250d13e3fb0922fe2531fc192ed1f5fd08cbc014fbfa10290b1fe700c7f116cfdbed08e5050ee7fec4ed19b3ff04551a12f3e0c80bf02af7d3d50332ce00e903f7fc0828eb1da20b23d82619e300bbf7f5efe20deef52a0efaf23c154901def0e7fff432093303f9f704e3e932f7ddf70205d160f219e518c4e50305e2f1c4150a0e1e3aec0b060ffd1e36e3d7f3020f0fe6f4f22a40bc5106c2f938e80e312cee0f2a0df6f4e9effdfffa0a04df1ffe00e6fed3f52c08010cf42707e8ebfefcf016dedd0bf7e809fbfbff1e0e10f408c2c4df01070ae8fe072f12f714e91ad40b0e13ee00f00cfcf2cde8192507f9e4c5dcbb19dbfdee14ffe329f1defad1ef1a2427cafd03f41005071ef0f1eafdfbefd6000c23d10d230ffde80af3fe26f514d80b12090ae7ff06f30701dc0905fac9dbedfee4ee1eef0ae2301fcafbf8eee612fff5f218fee9f4f6130517f8f6f5fbf8f5fe120f021302ff2a0315fbf1e8d4fee51215000ded0e04f1e71711ecf1f10cd217da0aee27fae90af3d3fbd5f02003130e05f50508e4060ff9f5e9f70e04daf100fff8e809f4f3f70cc60c34e5fb1205fae6f8fe000102f9f91dfdd90d1a0810d1fd11d7effc0cfeb918ff24f30114282ae3f302171bf21cecec02020b23ecec061b0b14f2ff1dc929ede5faf71df916f21323fa11d3f7f71715f70ce8e121dc23092bf7220dd8e80e0d0bf4f6ff3817ed06edcbf2110a23f8fa0af9f5ed1004e120000e030207ef190a32e428f8faf21d09e6fbf2f1f6f7de0ec82e260df8fddafc311cede8c145d9fad81bc0fcf7f33ddf0992fb13992327ed05b702e6b8c71606dc38f0e700222424e200d004041112051bf6f9fa20e80c0927f6dff4dcd332e924f415da080900f904e1b80c2656fddc12032800d913ebd9f1f801faeaefd61322d733f2eaa122fb162323d2e62d20f50ad611e5080a06050403e3fe05f40b1c12dceb0bee21030bfb051d09fb02d8e6dfff130ffcf2fdfb18070df1e9ea0d0f03b30aff18d9eaf2dff8fb11fd0df8dee1e30be6f608ffebdb14d8f1f6fa0604f5061b06e8fdf40a08f60e26f5f0e9fddfe6090e01020c000619eeedffff02e3c3ffe82df3f0ee01010e001ce60cf805f1ed020dfaf507eefc02fbf2ebfa01f9db1ff409f70b05f9fb0509ee06defc0a1503f0f208f804f2e810e5eff4faf2fb07f3f2ec030d0611ef01f2edf4ef07191312fff00af6ef0d0afef7f1f2ee0ae80de10a07fe02fff8ebfdfb070219f80316f40cf7f1f310fcf8f3f9eeeaf50af1ef02fbf6080611fffb06fcf8f10c08f8e9efdf05fdf903fff93dfbf703fdeef311100afee91c2af8faf000f6fdecf3f40bee0200faf41ff602fd0beff7f10df4f9020505fe16f015faf402f508f2f907fbfff8f9fcfa00120af7f10600f916f7f3000af7fa0300e600f8fe1af7e3feebf31629050702eb07fcfe030b03f0f9fa00fd02fa04070cf7f80c00050617fff5110211fa0c191e0f053ef8101509e5ff1d28f901ee3e26f3ec14fb0702da01f7fb0bf8fef8fb491015150ef7fdfd11fe09f50a080708fb430af5fdfb17f101f8fe0ef5fefd10f8660cf3fce9f0e726110f091b0bf31407e402fe061e0b1a0605f2061a131707040d08031c12d40afa0e0c05030ae8e610040c1211fff81c050e1d00160e05f705150e0aedf515fb05f50703090703e21506f7f31501feffde09eb0500fd13f6050115100bf11203f2f8000816fc04eeee0f15fe05f81406edf7f90206f8130cf4fc18052d060a1bef05de12fbfd10fc00170cfd1ce9e9e9fd05f70d0f0b05f0fd091dfc1e0902160002fafdff02fc1f0001e309060b0010ec0c0716050e060bfe070ce41ffb0a28020af1ff12fb20f00a200204251b0b082b16db130e1328050006fd26fcea1513060415140729efd514fa08fa131b0ff30f070b111ff9310f05eefff8081e221cf72100fcee0d10f5fe2c071e10ef0805faff1a04fcfeec02f5231e0df5fe1e1eeefd1f20ff070c1c07180ee201f20507080f05fd100bf3fdfbe0161be7a4e5eb1bfe12172c06e81813ec05d906da0bf9f7fc0a0cd0df1dd4380ce0fb3ee20d0afe01ea2d2400e62cf8372ff20bed2bea0af401fc0808e9fef01017cf1819fb1d21e9e306f8e21b0c0af72be41d231d1e1a08fd441fe5010dcbee0e021c212510f4270adf14f0132616cfd631dd13e229f30a291a410929fb00ef04fd0201fbfc0405ed01f7f308f2edf6020100fcfafef8fe0208f2effef7f1fffe01fc03fafcfcfe0008fc02f902faf9f9fb02f9f5fa0a03fafffd01ff08f905fd04fcf70303eff8f2f7f1f70800f9fcf400f5f9fefb0100fff7f4fc0ceb00fb08fbf6fdf4020103fb04fbfb0406f8f7f400fa05fffc0bfff6fdfa07fbfafc333929c7fb0cf81c460d482b3116f6360e370b1c103909defd0615edd43bb420ef2c220cf7212006ec051036e9f218bf2c291339f7110d0d0efd30012cda13d2112e021b13f736ec10a90803130718331b0dfe361ac3d015f9d5fdf0083301ee1228fa0cfee31421e5d5061611f740d511b515cd33fffbf50f1d10295205efcb0500025feee81399f6fee6dcdb01f1e7e5f503eb07dbfd3a3de3ebfc15d222dbc4f9e8daf4c7180ae1f61180f8eaf830d1d6f7bf07e9c2452645e901ee1ad72deaea0bf5f104cde5fc56c5a3da14d919fbce0c8eca26631ade19f9b8e3cd0fe4d707ebb401fbf5042b32fd27e529f520e624e3fcd20ed922d3d3cbc9fdff271ce9e9d9ff05f1000418f601cb1d270adff40e02f20401f0d407f92efefefcf2d30d0031c9f2ef0105e926dff60618e1e5d4df2ceef5c80bfb1bf90bfd12090e11dbff0adac410f8f6eafeed0c240f3ce90ccb0b061809cd0a1eded1cc0c06003c1bf402c4c0d603f0eced20ea08f4e9d21bf0d9f30de7d10e05cbe1ca25baec1cfa22080fe7f90d0b08f850130120dbe50d1b0210f00ae0fb48fe1ff6ce0efbf302f826fc051820f5111ff20808e3f91d14230f08edfcfb0c3afb39070e0bfeedfb2208250e021205f5e2d0c0061b092005dc050bf2da0a100403fdf3fe0af2ec2c130212e9ef0a14fefd1e06de1219ec10c5e6c50e1aed1df1121ff20dd8f90de40f0114ebe9fa0c0101030423f50c16e2f9f616e50ddfe201150cf0e201f2f3e4091109faf409f2f4ffdaf8030c0ee608fa0bf9dd02f30e03ef1af807ff00c807fc03fdfc01f507efeeed030b042103010900e518fdfefd081011f8f0e4fd060febf50405f3e914f3e2fefc08fd0312fdf508f60afd0a01f10ff80408fd18e5f50728f0ede8e3edfdff17ff04eb3225df0411efde0510ff252cebdff7f5231f05eaf505f9ff18fc1ef2ff100a1d2cf52314e3f70308e222110deeec0b1f100a2025e900fe23ec21f412011cf9effc07e80adf0b180af11c0a080405d52f16e8f7fdf21615eff8ee0cf4e105fcfa0a1ee0002f1108fe08ddf5060a0e11231d46dec12df01605fbec1c2c0cd60ff02b22faed21e6f90000b5e902f8cbf9ddd301ff17ffef03c9bf24db11cd1c09340df015eb0dedc8d61dd607c4fbf901d202dbf30815e29906d609d1ca103022c92cf4d601da0229180cf80fea03012dee181bf8b7f9feebcedcf3fd9439e1edf2dffa20112ff7f2c5f9183bd6d4fc15fce504d0fce30bf3f7071207ef04060b0ee300ddf2f4fb05f5e3ee14101901d80bf4f2f6020b060d0d03e7050be4e906ece6eff40003fb02fee9f107ce31030af8010d0104020805fc12e8ff06f4f70219010201eb05f2faf8d5e8f911fff5fdefddff130bf3eef2ffff05f5f203d6f4020ee507f8ebe4fceb07ffff05020704f62c310a0ef5df150517fb130922df1430f3020201291b0a3f12d234ef3ef6fd18e4edf1fe5ce0071a12f6fc2bdeea0c32efd8f6043820f7eaed200ecc1b24080114d2f4e412ebef0e07e8efd0ee002af009120fd9f82615dac9fa26fde1e20f16f9312e06fff2e5cb0400d4ca26d6f61406ae20e2e9fc1006d61819eff1e534d50e05041ce6edfef51211f6f0fb050708e9f6fa020806060506f6fc0a0307fa09e4ec0cf7070bfa141cf8fc01fdf2f8f800ecef07f912fd10fb0407f7f7080601fcf3e6020609ff0108f2f8e7ffed0308060210fffef2f0eaed1a161016f0f30be70d110e020400fe0efadc0a08fef01905e4ffebeefa0715f7fc05f7ff08011d12e813ed5bacf502d5f2f8071909eeeb191bed1dec0805fecadcf715f9ee0106e8470215e50309efce10fae1fb2d160d21fb24ffecf8e00c0ed7e01b0be5e5ec08d53feabef80a14fc2be09a0d39ede8fa0fce08eb1629fce5dc07f7012f061e28ebc8f91f19060cf5f41b1ff4071ada0315e3bb2f1322eb46eb2015fd15f40de518c81a32fdcdbcca0604042eff44fb381cea0a1d06e9fc19f20d06e6c8d221002900d32905011210db0900f62d01111af12f1df9eebd13f7f54a0003f70100d2ea2533f1fff1e5f915e1b9d11d101b1feee50becec2f11f6f6f6182622f4ff04060208e00d2ef4f50503f6f9220215ff18bded1af300ff05f3ef001006f929),
    .CHANNEL_BETAS(1024'h77fa77c578af76e77752778f76dd761578b9785a7770787077277759759b788f78bf783c77ea767b775e784976957637789577b77697778077bc7726772276f376617749767d774d7777769877f97785777a771a78337734770c75d477fd77c3784c77c179577801774a780676fe767777b2777a769977897614787d77037820),
    .CHANNEL_THRESHOLDS(1024'h020901fc020c0205020001ea020f0203021b01df020a01fa01f801ff020d02000208020501f4020c01fa01fe020701ff01eb0212020d01f2020e01fe020101fa01ff020c01f801ef020c020301e8020201fb01fd01f301f3020101fc01f701e6020401f301ed020401fd01fd0203020201fe01fd01f301fb0204020b020901f3),
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
    .KERNEL_WEIGHTS(65536'hfe0702fefe000202fd0400fefffd040203030002fc0000fe00fe0404ff000400fefe00feff01ff0001fe060c01fcff03fe010000fd00fefffd02fefefdffff0603fd01040100020000fffdff00020503fe0102ff030101feffff04fbfcfd0301fc02fdfb0501fcff04fe000105ff0003020100fe02fbffff02fe020101ff02fef5020af6fd020a0dfe020f0301fe000c1112030d15f203f903fafd0402fb010207fcf9fe0411f600fe010b0f02f900f8ff03f80df1fd000ef600fcfefa03f604fafaff0c03f2fffdfff8fd0cf2f90113d70bf6f5fb05fef606f90df80df7f8ff00ffefec02f8e3fde4e4f6fc0bfa02f8f8f7e1fffafdf9ee01f6d301f50103012006ed2c25f8100a080ef3f8f62802d2e6fffad8d50ff2fef722fcfaf436e951ec3e310aedf010ff3a079edfe633160f20f768432fef08b311dc010d28f31ae61ffe14fd051c0415fafa0b2c2215f405cff2d610091af81afb1810f1fc130d0e2717e211f907cbe901f115f8dadb1e18fc2b121d0bf91a06031adc0a1108eeeefff900fbfefb0101ffff0501fdfd01fa050800030600000102fefffb06f905fcfefffffb07ffff00f703fffffb00fbfefe05fd010300010201fe0203fc0700fcfd06fffe0102fefeff0603fefcfcfefeff01fc0100fffcfe07fefd0302fffdfe06000003ff03f60001ff0104ff02fcfffefdfdfef902fefffa02f804fefef6fbf5fef6fcf3fd0318080214fffef5f8f307feff070efb0000f501090af8f50901fbfae809e816f40906ee0d0409f6fcfffd01faf0fd01fb1ae5010310fd01fa03f8ed0401edeb08f50101f0e4efff1707010a2ef9e9ff1e0009e1fefbefe2fd02fa0403e80b021a202f0c0505fdfbff1cf2ee18f903e7e8f912ff11fdf5051e0ef3fc07fdf801fbf6f8fa07fefe0002070906fffc03f5fdf804fcfdfffbfd03ff02f1f604f800f100faf8f80a01fdfff7f80bfbfbff010b12f802010901fafcf1f906fcfa02feff03fe09fc02faf9f6010afb0bf6f9fbfffb04fafa0a06fef50103f809fefcfe13030f0a05fe020aff05fbef0001f506faf805010dfff900fe02fd0006fefefdfd01fffc0202fefd03fe09fd01ff00fd03fe04fefefe02ff010001fbfd01fe03fc00fefe040602fefdfdfe03fcf9ffff0105fa08ff02ff01fefffc03fefdfefe00ffff04fffbfaffff03020104fc01fefefd01fdfe0306fdfcfe03ff020002020101040100020100000001fbfffdfd02fffcfd030803fcffff0701fc01fefeff01010200ff02fbfe01fffeff00010301010000fefefe01fe00fdff0101fb01ff0000f9020002ff0100fdfffe01010301030400fb0305fb01feff00feffff0003010100fdfe04fe000200ffffff02fefe0000030301fb00000002fe0000fdfdfffdfffe0001fb00ff03fc03ff0100fefd0003fc00ff0302010103f5e915e3e7f5f9e600ecf7f4dad015f905fc02f1daf405f3e9e50ee9fbdb07efe1e9b8cff307d9faeaeff0f817dddef3fa00dcf7d905d20ed52f08f8d7eccdf0db0502f8fc04faf6fb1cf3dbefdae6eb0f1b1302ebfbf4fb1602e40e03eef5ee00fb4304f90628040e1ef70bf01c0601e5f6edffef0aee151202eb23fc110726f4f9f9fefe04fbf5fdf7fe050601fe02eff302fb07ea05f902fe02020cfbfefe02f6f50204efe90200eafbf8f10a08fff500fd03f50006f504f7f50e02f7ffeef9fcf900f9f9fffe01f202fbfafef6f7ff0708fcfc07fe0407fafae1fc000002f700e8f4f5fee9fcf400fbf6f50002f508f8f6f9fee6ffff01020a02fbf90502fe01ff010002fffcfdfffffb03010001fc0000fbfffe00ffff00ff0202010101ff00000302ff000003fefbfafc00030100fe01ffff00fffe0101ffff02fc0102ff010000fd00fffe00ff0100ff01fdfefffefc000002fe02ffff00fefefe01fd0100fe00fffeffff02fdfffefe0201fefe0101010200010300feff020200ff00bfb7fd87bcebb2cb07a317d29880824d0937091dc0ce0dc58f8020d4f780ad80a2bf8080cd0992fa80a5f1f1f9c1bccb9ca580f5fff9cc38d00bb09380ec80ffccf7f3d3e323faf60116d00dd0dde3d90e183ae5ee0fdc2625d0ed2718eadcfbd4dc2affc8e927c92b400430ff2a09fc16cbfa04daf7fb0606027402f3e2f546fff4f7fef5f802f80ffb04050efbf9fcf6ff02f2f9010101f702fcf5f901eafefe04fcff06fafafd0600f5f90100fbfb05fafd0405fef5f800f7fbe202f7fe0404f3f9fd0504fbf8fe0a01fafaf8f705f903fafafefdfdf5f5fafefa0701f8fdfb03ee02f6fac8fff0fd04fefbf6ff0401fbeffcef03f7f7f1f8e4f3f9fcfcf00701feecf80f050108f8e20107fbfff9faf2fe01fbfcfcfbfd01fef809f8f5df03f9fadf01fff901fe00f30512f5faf7f2fcf500fb00050a040a0a0cec06efeefa23f7f3fdfcfcf2fefa0deffbf4fdfe05f5fe00fd03fafb0007f9f001fafa0408f0f108f211f906f6fdfa020403f6fdfefb00fef10ef8f700f3faf9f20003f8db0825faed0aea12f30713e8fe030df7070afceedef2fdf1fa03e90c0905e50808d5f709f009e4fd12e80b120edbfa03fa2400f005fbf519e117fafd0a01f501fff60304f2ff06e8fcfafdf8f103f6f90c0e21fcffff0ef203ebfc13fbfffff30cfbf7ee03021612190ff2fd0101091810f010f9fff6ebfa051405fbeb031319fbfffdfdf8fffbfff9fb0605fdfa01f80c0300fc03fd02fef9fefe00fdfd00fd01fefcfd0002f803fd0000fa02fefbfcf802fafff7fff906fefd02fe00010001fd05fefe02fc07fe0104fd09fd03fe0303fd04f9fff8feff09fefd03fefafbfefdfdfb000000f4030a0105030407fe0701fcfe00fa02fefcfffefd00000001fef5fc10f4fd0600fdfef50f00f8ee07040e0e00010e01fffe04f300fc05fc000306f8f9f6ff05f602f7fafe120efff7f400f6f4ee00000009f1140000fb01f2fdfbff01fcfd05fefc0200f904f8f400ff01fd00f700fbfcfd04fbf3f70206fcf9fbf80101fcfb0dfe0101fe03060eff0bfdf6fffff709f8fb08f90a01f20001ff000101fe000102010000ffff01fefeffff00000201fefeff00fe020200fe00ff0000fffe01ffff00fd000204ff000001ff00fe0000000100fffffe00fe04000101ff0203fd0202ff00000000feff0000fe01fe01000101ff000103fefd00010001ffff02ff01fb00fcfe0001010001ff0001000000fffc0100ffff00ff0001fd070309fd08fdfdfc0700000bf6010905fffb01000101fc03f8fa04f0fbfc03f5fafcfcef0202fcff030601090ffffdfdfcf8fc0904ff02f3010c03fffc04fcf8f8fcffff10fcf803fffdf902fefa0308fdff03f70505fef80103fff30a04f803f0fbf906080104ff07fd04080201fefefdfcfcfef100fdedfdf607fefe03fbf5020001fffdf804fe0b010103f8ff040001fd010afd06fe0500fe0af5fc0506fffe01fffcff040400010501f902fdf9ff000300fe00fffb02000602fcff020202f70afcf309fef608ff04f5fefffb070404f7f4fd01fff7fafc01f40406fff30a08fd01020201fd06faf9000a03fdfdf6fcfbf4fef90102f6fc0003fbfdfefaf1b6c80080bad9aee6cac1c3d3e080a73112470526b8f00ddeb480f2e6e480b8808ab9be80e906b70780a5d7e6f8c9d1a8c9b980b5d2f7d72edde9dfa480cb80e513fef11adbfd15cef6da1302040df30d4b18602307dd073c12211923ea151cf4dd041d101d1522df3751fc080711224223fbecf2f808f623076020f00b22405def0023f8fb24f700f4ed07020af505f40d08fff713eeffecfef7fe140ff3f9f512f7f90206f8edfefbf70510110a0506ddfdf2f7ec031506fe191001010102f203f70a05eff6f9fd03eb09fe0c03f3f8f3140bfe070f03040d0307f7f0f70a0508fef403020efcfffff6fe0ff10402fe200a0efd0cf8060d03fc0d0600f3fd0df0ff0ff5f4fffafdffeaf0ebdceffc0b09010204f9e0fdeeeafd05f9edf5f40001f0f2f5f607e500fdeefd111bfaf4f5f30fede9e205e503db10eaf3f9faebffea0600fd0502fefbfcfb06eef4fef501050706edf9f603f512eceb170fe8fbf2fbfc23f2f0f912050e10e710fb28fbfbfde4e8fdf315fa03170808140ee3f806fbf804f205fffe0106fc140a04fe05111b0602180cfefefff2f2080e01f009f8faf6f3f00d00f9fdeef806010306f5f90210f00ef5ff080f08010916fe0d02f3f4fe00f805f7f7000012060003f9020cfefc0af6020c03f60808f90b0809f40406fef813fa11f0120808050e0204ff0906fef9fff204f5f6fe07edfdf4f2ff08f1ff08faf6f7fb07f80512fefcf90203100c000ffdf3fff101fc05fafbfe00fefbeef504f00bf50200f6ff0804f5f6fa00fef9fdf101fd11e306f504fefef601f4fdfef8f2f8fcf902fbfc01f902f51106fb00f3ef0d07f909f3fb0bf8fbfaf7f60801f100fe0b00110cf708f803ff0608f8020400fd030508fe060904fe040aebd8f5bfe8e3efe8fbf7f404ecd1effd03f0f6f1fe05f8f4e0c7f8f3f6bdf7d7eeedd8a0eaefe9fca7f40c02f9f8e2f3fcf5e6e6ebf9e3eee9f8f8e39603d8fae315fce907f2e7f5fa19e906eef3f5fc02120efbfaf1e6fffbdfdd1a0df7dffd03011609ebf90f09fd060403040ef706fff9e2fcee09faf1100f1d05fbf6f918fefd00fe0302feff020006fefd03010b050100030000ff0203fd010202ff02fefffefe00050000ff00fc0301fefffffd03fffd030002010603fdfb010001fefb00fafffefd03fffa00ff02fbfafdfffb040304fdfaff02fa00030007fbfffffa06fe00fd000100030007f7fff50201ff00fdfffffe02fcfd0307fb05fc000106e6fff1e9f9fcdff404e508fdecf702fe0211fb01fae1fdfe02f905e8f6ede1fc0debe4eefe06e5faf3ede911f0e2ebecf006eaf9ed05fe09ddf4f821f6fbf1e5f70bf8e803f7f0020000f3eefcfdeffbf6f30304f8fff41005f1e304fbfce801eeeff10cfbf70b0b07f6040a040efe08e1f8fd00f4080508fcfef8020b02fe0a0301fbf8f7faf4f0f800e6f40df5f603e400ffe8eff604f3f5f4fbfcf900f7fbf900fbf2f8f3f300fcedeffefafb06f6f8fef7ef0804fbf1fafff6f1fee7faf300f808fdee0100e6010af9f5fbfefb03fefb1c07f8eefe0d05fafc04ebf4f9fc02feeeea02fc06030f04f515fa02000f07fefdf9fef70808f90d19ff04f80d07fefcfcfefdfe000302020401fbfc00fc0305000500ffff00fffc02fcfffb0600fffefeff03fe0000fa0200fdffff00fffd07fd01feff020202ff0202010701fffc05fff90003feff000603fefffcfe00040102010200fcfe0202fb080403f8ff0b000202000101090201ff06ff0000fbfdfefafef606ff02fb03f7fefcfef7fef3f9fbf2edfbfbf900f10602e8ecf509fd060005fd0002fdeeef0ef5f6e9fde0f406f4d7f7fcf500eaf6f501f6f9eeeaffffe5f7fd00ea16f8fbfbf7e101ef00ed0903edfafef8fefe09f30af9f3f705fefd00fef400f709fcfdf60c0df6e90003fc0804f7fb00f6070501fdfcfefffb03f4f703f810f901f7ff070301fefb03fef8fcecf9effb0af3f90906f0f20bfd1cf8fc0900f6fd07e5ecffe1fd02f5fffafbf4d9f50a01fff302080705fdfaf4e8f7fd06fe00f7fff910010de90efaf4fa14fff601fafef0fd0ff608f4f6faf7fcf70f050517fafaf8feeff91a0dfaf809000b01fdfeed0c05f5060603fa03f7eefdf603f008fbfdeff7effcf10002f0fef7f9fc0001ff01fefffffffdf9fefffe08000304feff0001fe01fa01f703fe05fffffc02ff00fff303fcfa010202fcf907ff030200070306fd0305ff0600f9ff06fefeff0401ffff020005fffdfffe0401fc020200fe020900ff020303fefe05000305f902f800ff01ff00fa03fffc0500ff00fc06fe05fa04f5ff0201f907f802f1fdfdf806fe00f9040300fdf4f5f2f8ff00fa08fb03f7fb0afdfb05faf7ef01fced06effe01fff9f7ecf5fefdf805f3ff03fe03ed07fff2fef5ee00fc0cf10cfceef8e5f2f100fef4fefdf800fafde2fdfc0103f6fef600f2f20703eaf801f9e501ebff030303ff04fd02f90004eff9f805ee0702fafdf700fd00fcfcf702fd00f701f607f903fa00fbf7fdfbfdfd0400fe0105fb08fafcf9f3f4fafcfef4fd06f6fb03fbfef907fbfefb0df7fd01f9fbfe07fff707f8ff0408f1fbf0f8f7fcfdfcfc09fcfffff8f609f9f9f704fc0502fefefcfbfb07faf604fef9fdfbf7fb1700fefe0303fc01f8f8f502f9fc02f9f500f9fcfcfb05f601fcfcfaf8fdedf9f6ede1f2fa02f5f3edf8f2ea07f9eef7ff02ecf0fff2f9f00ce7fdef06fafdf0e704f8eef8f9fc06fdeeffe7fdeee601e9fee6f5f7e3f7fc0af0f400fd06f2effdfafaeaedf1fdfe06f1f7f80003ebdcedf1fdfdf1dcf0ed08e1f9f9fcf901e7e9fbe5eae1f5e0dbf5fae7f7ecd2f5f5dcfdf1fcebe4edf006ffe8ede0eefd0205f6f8fcfd00f5fffd0100ed010705fffe0005fd04fcf4f6feff05f608f800fbf6e4faf8f701eafa04040300fefaeb08f6fbfbfe0002f7080208f70803f7fd0000f900fbfcfffe0ffa01fdfbfb0202fefd07fe0b03fe010af7fc0405fdff0600fe040301ea0503f8040305f8fff5fdfbf304f3070101f4fe08fdf5fdf2ff08270fdeea0f1327f31c1f0cddfa022232f6f3561cff072802dd23df19e92bf408edf29df4170f10c922206323f6f700c023d8f908032114d4292830b2230100c2dbf51127cc0b4cfc13cce4f7f223192df651e7edfd11edeef1d6095fe7e312dcf7e0064f2f473638140d0c0c10fc2edbe449ecdb12f2ad25044dded6f3375cf30301fcf70e0300fcfbf9090002f50607fcfff8f3fdfbe306fb060cfafc040309fafe0801f4f0fc01f701faf3effbf6fc08f701e1f90306fffe090602fbfcfd03f9f7fe0c0400f5fa03faf1ebed07f9f904f2010307fcecfff3faf00dfff902f5ff000a02ed06f0faf1020808fcf2fb05f808f8f30aeff7f7f3ee03f200fcf6f4ea11f7fefdeb16e5032206f6022afb451006f9fbf5f50716f3f4050803030010d9ef06e01ee7fbfcd93a3a39fce7faff15edf615010039df25dffe0201f908f6f60204be0409da00fafbe2e5060403110929eed1120af606e403f4ebdf03e0ddec03df030221081612e20506fc0ffb1cc7130e0ed5e907ed0b06f8000d130ef90308fef402fb05fe01fcfe00fe03ef0b03fefdfbfb01f8fefffd040301000105f1fa040007f80202f104fc02edfcfdfdff00f8f702ff03fc09f5fe01fffe0201fcff00f9ff00f7fefbfdfbfafc00fd020201f7f90004fdfffb02faf9fd02fbfd01fcf9ff03010507fc00000500fd00fffc05fefcfef9fd00ff0303f900020407f7f9ff0004e4fd08f5f5ff00060c03f701fcfafe01f9040afef5f1fcfffaf7020afbfe0aeefdfef60004f9040103020df9ff0801fd000201f7f804fd0402eaf4f2f501fef9fefdfee6f804f8fafffa040bfcf6f50a01f00f00fdfbf803f8fef7ffddf7fefdd303f205f9ecfff7f6ef03f5fe06fef4f4f5ed0ccdfffafdfe01d1e402b8daefefd301b9e8f6ddd0e3d909e3f9e4d50605eccacc0bf0f0bbf3beb2e0c7b5e1e5d105b0afd4d2f4c2e6dbdad4b1b9e9f1bf1ad306d9bab0ecc8f7f710f2f50e17fcf4fb0ef4f9fcf2ea04f70f1512fdcff0fa0dfdf62608e9ece204f9380bf6f913110e09ed1df116020309ee15f6f413cff81d14001ffeff080bfd030000fb01fe00ff00fe000100fffc00fe0000fefb01fe02fe00020000010202fdfe04fffffe0003fffffdfefefffefd01ff00fc0003fe0000ff0302ff010101030102020000000003fe0100ff0200fd0002fe000000fb010001fe0201010101fe03030203ff02ff00010302ff0102feff00fffe02fffe01fdff02fe0002fefe00fe01ff0202fffe00ffff02ff00fefefe00fdfefe0000000100020101ff0101ff000102fe000001fdfffafe01020000fd01fffe00fffe0001feff0200010102ffff01fbff01ff00fd0200fffefeffff00fcffff01000001ff02ff00ff01fe01ff01fffd02ff00fefd0001fefffefd010001000000fdfe0000fcfefd00ff01d6e5f5edb3f8e0df04def0ebe8d9e9ebed11fe0a19fbfcf9f6e809e4fccbf5f30bfad7e0e7fde2fde5e7fb06f1e7e0e9e00ce7fbf506da01d7faecedf6e7ddefedfff9e9f5fcf402030cf316eef0ed05fff816fa0104ed0cfaeae11906f6f1ed07ef0718f5f425060c0c0906fc0bfa02e7ea0310e709eff60b0df9fc1605eb10fdfcfcfdf8ee040003fdfb01f7f6fdfa05fc00f90101fff9f2f906f600fd01fdf20205f8f6f30002030308f809fc0200fe09ff00f7fcf407fdff0600f506ff03fbf3fff30ffff1030207fe06fffc030df3eaf0ff0805f8f8040ae60a0805ef04f4010100fbfb01fdfef6060103fb040004fcfafdf60402f501fc0dfbfdfcf7fa05fcfb0103fc020004000105ff0000ff010001fe06060106ff0100f700fffcfefc0505f9010203fffd0300030004ff0206fb03fd08000104020002fefd01ff02fdfcfcfffdfe01ff00fcff01ff01fcfffd01f302fefffe04fe0102fefdffff01030301fdfdfefbfcf6fffffdfd01fffdfffe010103fb0003fffcfffe0103fcfeeefb11e0170fe5e621fd3502030bff10492a0214f7280e0211d21f020cf9fce629f2d1ec2d0cfe02e2f41620e0f0eddd171fdff5ea000e340a15fcf9ebfed307e8e3faf0f30d1dedfe0efcead9ed01f84b264deed51209f229f0f93dfef1f0dd08fa0f05e2142f01303ff3e9f00dfd2408e007fdf6f7dae8ff36211ddff4443101010001ff03feff01fffdfe00fffefcffff000203ff0100ff00ff020000010000fd00020102000000fffcfffc010101ff010002000003fd010100ff0203010204000206fd0103fd01fb0400fffe01feff0300fe01ff06fb00000701fe0106fe0201010200020000fd03fffefefd01ff000006ff0000fafe0003fc01fb010101f7fe08f506000802fa020608fdff0f171d060116f5fafdfe08010dfdf8fb07f5fef3edf2ffeff703fb12090e190907f80bf6f1e40003f501f80d05fafb10f6dcea01fbfaf1eafefa011804e9ec00efe90dfe12f6f400010104fafb0909f9f6f3070026fbf1fc0513110cf1fff913fd0ff4fcfdfefcebfcfe1217e5fe00fe0a05fffc02fefffefe00020003fffefe03020506ff050300fe0000ff03ff00fb01fdfffffe000102ff00f90008fcfb0000fe0004fd0100ff020602fd0202ff040001fe0600fb0102fdfd0003fd00fffeff000101fffe0000fe0002feff020101fdff05000400fc00040402000004fd00fefefffe0001fb0100ff0103fdff02fffd01fb0400fdfcfffc00fdff05fdfefe000201fe00fefcfbfffdfdfffc02fefffe0100fbfe0103fd000001fc00fefffc00ff02fefefffbff0201ff01fd040000fe05fffdfbff0201ff0501fffeff01fe0402010101fd02fefdfc0103fcfc0202ff00fb00ff04fe00feff00f8040101fc00fcfdfefefdfe0301fdfeff0203000100f7fc0000010104fcff01fdfdfc0403fe00fc0001fbfefc0100040001030201020205fffe0403fdfdff03fcfcfafdff0301ff03fffffc0102fc0100010303fa00fdfffdff00ffff00fd00ff01fefd00fffefdfefd01ff0000ff01fffffbfefd02ffff01fffffcff00fffd0000fdfe02feff0201010100fffe03fefbfc01000101ff00ff000000000000ff000000000000000000000001ff000100000000000000000000000000010000ff00ff0100010000ff0000010000000001ff0000000100ff00010000ff0101ff00ff01ffff000100010102ffff00010000ff0000ffff00ff02010000010100020002ff01ffff02010000010000ffffffff01ff00ff01010009f8fdfa0cf7f9fd05f90317fdf5fb08f907030305090100fafbeffefbeaf7eef20503e4fd000503ee03ee07fe0bf8fc03f403040f02020803f3fc04f10af9fbf6fffbf6f1e3fcf601f7f2fff5f3faf2f1f6f8f9fdf707effcf9fef201fef6fce5060602f9fcf501f90109fdf1fdf9eb01f9f50701fff605fa0ee600f7fff7f7fdfa08fd0301fcf901f9fbfc02fd04fefc0401f705fd0205fe02fdf9fcfbf8fdfcfcfc0506fefcf9f9f8f8f8f304fdfb04fd00010406faf4f700f7f902fbfef001fb01f9f807fbfa02fcfd0afbfdeeffff0400f9fefefdfbfef8ff00fafffdf8ff01fdf9fbfbfff4fcfef4faf100ffff00f9000701faf50008fffd01fffbfa00faf4f5f3f6f8e4ff05e5eff0f3f6fbfcf5f3f8f200e9f6f704f9f8f3fcebfffc09fef20001f6f7f9f4eff8f1f9eef8eeec02faf3fefd03f1fbf7ee04f9f2f3f0f7f4fefaeceff8eafbf5fcdce8e8f7f207f1efebf2f2f9c5f3eafcf9f4f0faeff6f300fef5fdda03ecd8f5ffeef4e8e9ebe9eee8ebedd7e7f3fce805ebfe00fbfe020ff5fcfcfb0cf9040ffffaf10d121809fe0710fb04fbfdf8fa060cf6fff5fdf7fdfbf704f501eb01211a0dfffcfcf301f5faff01071af70f0b04f60ffd05f9fefc00f700fdf8fffaf9f7f6fafd03050f0af9f90703fd04fb02040105fbf9ff020bf5030205000b03f702f5f9fbfe0ef6fdfefffdf5f9f6050602fcfe01090000fe00ffff0201ff01000000000100fe0101ffff0101ff01010000ff01fe0101020100fffe01000202ff0102fe010000010100ffffff000100000201ff0100fcfefefb04fffe030002fe0101010101fffefa02fe00fc03fe02fefd02fff801fc00feff02fefffefffd01000201fefd00fffd01fe0003fffffd03ff0100f800f1fc0cd2e1fc02f3d1d52614dbe122172fcefe1528db08d6bcd316bfddf7160dd4f7ddb5e607d813f7e6fb2042e8bcf1e3d8e6cfe907c5159d302213adf3e5fcdd00f4e6fdfef8effb16e0dedcdbf3f80200260be9faf4fc09d4d524e7d8f2e304ef4903f1fb38f721fc00020c34f417ebdef2f8e4f3ddfa10081316fde3ff08e5f00bf7f3f5c0efdde2fceef11507f910e009f5f2c7eae80701eee905f5e40916d7e50dfd10c9ee10e4ec0a07d8deec0208f6f3fc05eb11de0fcd04fddff9fadd0204f1010fefe90111f3f2e1f6f1f3f4021defeaf2f4f807e7e10408f8f0ebf6f509fc00f71ff00c05fb06f91ffe12e3e309f5ecfee8ee08051ffdf6f7faf807f2f5f50afaf9fcfb03f20cee03fb0300fdfd010706010206f7f4f00df902f9fefa03e60007f803edfd06ff0800f2f804fefcf101fefdf7120909fbf3f8efecf7fbfcf5ebfeeef500fe0003f3f8e8f8f90ddcee0205f9180d03fafdedf800eff90307f9fef7fefff107fff0fb030d0306f9df08fef5fffffefccb0bfe04f8f20003fffffef9fe0101020302ffff00ff0403ff03fdfafefffffe02f9feff0301fffefffe00fe00fefb03fdf90300fffdfa05fefdfcff020205fc0305020505fffe0900fe05080101000402fe01fe010105fdfcfb0700fbfa0403fe060a04fe0207000306fd06fc05040102090001fffefefffafff40afdfff801ff02fbfef6fe),
    .CHANNEL_BETAS(1024'h7513768271b1772974557773761174b577d1768173a276b877c1777b74ee769d75ce75b4759574c5754b732d77737876760d77507667785f7494779c7796760975f5772074ab78c276bf6b23775c7580757577997779752a755e7760775b758f75e276a677c776fb760c72f177db772a7680781e757376f976857641767c75d1),
    .CHANNEL_THRESHOLDS(1024'h0204021001f9021902100220021f02060204020d020302170207020f020c02140221020802140212020201fb02070207020e02090211020d0210020e02160214020f0217021602140208021a020d020b02160209020b0206020a0212020702000212020302090215020d020d01ff02110217020d021a02060214021002100209),
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
    .KERNEL_WEIGHTS(16384'h242a220418e1f71df8f8f9061516f2eaf4cf202a0e0105e7c1cb7fc7388de7eadad3f2f6ee1b09f1e1ffefdcf68bef1607c1f9dc1edf1503fbfdcd5cfee0060ee80cf8100a0513f806fcef08fa03fe0306e8ff0008f2fa05041af90f0d291e100a18010407fe04dcf4080816fa1403fc03f3f40f06fef8ff0408f9f709fb021bfef6f20ffcf8140ce803f0fbf8ff120d28d63248f0ecfc1a29e4e01ae94c0b15120cf1fb1015fa1c15ffc900ef1a0b08f8c8e01b1a04ecebf2f1255f0cf7f515e2e2eefe94cbdaeabf020f8006e3eeebe6f6f5dfd71db5e303c2e60009d9e0d9d2f4f9fae80700b1d6f991090a9e15e3a1ee02cde53324fef3f7cd1080a9f5071f1dd7fe3215100e15f4eee8f50f120f2719d6f224011e131de52dfb1bd8e703e70df9fdf7251d31300a27faf8fdfc1c081ef3e5ec121908fd1018ce3f1e0eb7ef00e9fc0b0e2a001103e82bee151d241cdc050a00f504060b052808183a0f0a090f06fd0a0c0a2c03081e08e90c05f01bf4070c05f6260800020afa2efef607f0efe40ee8a9150202eaf6040207e9d212e03329dce4b9d4e706b013d8f5f2f8d1e206fdf71f058fed00b5e9efe7f3fad5bedfe6dcefcdeb08fae835eb9beaefdb02a8c09780e70796f4ce80f30e80e295b2db8980daa398b28080ffcfb9b4d7c709f5ecef80f2daf50780b5f180b2f480b2f2b4d7e88a0508f0d7d38080f59ff9f0be252d2a30ec1b01f2ebdf21261815d0f711f00505251b1ed60c1528f214e31e0dfdfa2f172236102004e029f3000cd3f617f624fe050c0808e24f4217fd0a030917f5fbf4ece602dd0c00fbef07fbad2d51cfec04f500ffe401c949eb0b090d07ed210f12bffbe5d01bc0ee0e0bf2ffdc3d0cfbe1fcf3fce42edadcfaf64916e2f30b306f14110118fbfa1b26214dcfbaa6261223df37cad0433cf50c20be0706cfcf08d11d44cb17f60812edfcffc30c0219d5cb06f3ff6e056149cae4530ffeed0a03f2d8c61409f6f4cc1323160d240e14ede6fac8ddd8fb1000dcedda08e3f6d112f7ea1001ec19f01b12e6f1fa04f01304e50b0bf1e31bfc05f510111cf3073a3135ef02f3dff3deef0f1efbfeecf4020afc2b13e81629093ff017102d0902242210233dfdfe2f1e00d00a0d35f31c0bfc4d0604fd2b96f9e80c0513092ebcdc80f421af0e24aaebfcf30df4fa03ffdbd8b3d6d6fbf1f6ccbad5fecae3fa0301f8f8ecd01a93c2e580f521b8ece6fe0330d7fd0a03ec3d8bd807eb331925d3fbe9932cf0ecf9d807e3de05ef420e3f32e6dae38de9e3edd316ccfd0ee9fc07211810d3d1041a1cf7b5151dfd350bfb3aeb0b1616febad5b1c92d2308ca3ab3c1edd82ad2f04ba7e2def10b10ebd1cffa12f1e2cce8d7c1ffb8daef07fef601f9d2e1c601ffcad70fb8f416c328e4da0616bb04de01d40e99dee6d4b1f11602f131f43ef2e4d72027ebdb0cd502e92cf6f4d307bcf8502d0d3817104d02200e38d415cad92df8130313d8241a3bf311fbc840fed0edf9169b9ffc067f2702ce15bdc9b9e1f10ef5e01cf0cf082b22fe010fffe3b7e4c4d4138dd00adde60af1da07fadef3f3ef2ce4cf0fa0dfe1e0c61912e41311faff21920cf326e6ee06cc808016e28ef3f480efc794f4cef20bf00be9a8c5f680cdd4d5b2a5f700f8d7fdf6a9fea59d0a80bfc880d30b87e1daabdde5d7fdf5f2c8fb8080f8b7172104dfec95f30db60415e3e1ecfd03f61ef407eafd9af7eefdb2f107e9eddac9f4ebf10d0aeab4f00c8e8df5801403f8c6e4fbf82aabfbf506f15780a8ed970114e4d9b7c0c9fad60dfabefaf7fddee9d9decefafbd1f8e9c5b9f11ae4dffee3f4e6f8f7b3fbbafaf0abe6e5d603d9c7dbeddc0afce408fd04f2eed6a9f3e5280822cde3bfeff8cb0c3ca6f5bff104df0fbed1dc1be205d9c2caed1ed6d811b200f4fbeedbecf5fbd285e81080e313d906cfd3eafb88fd03fec2fc8080d9d312df2eacd289cc24cc1139e7f8e9cbc0c7ddeaf30d10a8f6d8f7df0604dfe0f7d8ed0d010d04fdb3e6ffaf80c791da35c4e7cdd0df15b30bf304bf298080fe8e7ff4d5d9ead9e8c5e20bf9ccebece9f3fe4f17f9010cd903df14d4eeee83f806a6f9f4fedd12fcb3cc00201b00a706b9eafdfdebde1bfb030c0fdaea80a9e7f8f84601d50ec0fe0d3b19e9edfa112b1be8e9d2e8d2ddedec1cd050d1eabbe41cd3edf2ede11f142e101e123401d6e1fe161a0fdcec217f07051406b71b00f0b0290d0cfd0efddf06d5f9edf7f1ac1000e43cc6801803b71ae5cd0ee006d0ed180e0e210ad00c0dd510f5f42909ffee0d2763facf14ed3af3290afa9b00b028120e031d09e01505011307141c090fde120ac5445b1ad81af3f6f9e32fdc2f321a021a28f2fb3222f1f116e8ffe7ebd222ecf2063afb0080f8ecffef24ef2c080a12f6f9eefdf2fdec0903f6fff1fd03fa06ff14faf30904ebf61de5fef4edf7faef01f1ff06fce9040bfa05f6ec0214ef0ff7fbe701f1fefd0af9e40e080ff605fd02f7f6f607fdef1409070cf208fffa0ff71c0702f61f11020e090ff0180a0202140104fefe07fffdf4fb140f1905def3fc0e060c07edfc07010708160dff1bc2311527a980f9239d05198010e9a5f7acdd00fdf805b7c98080fdf5ded280f9140414f6f709faf3ce2880990780d54aa113e7defa17d1eff8f2c022808007c1d0fa80bfcb8080e39df8e88002d980e2a5fad3cc80b0a7c4a1808bfe80b086dfb20bfd07edbafcc2eeeb80980180cfe180c6f0bff9f0ba09ff03b8a38080e7aa3c061fdb06c2d6edd5151480ef01e310e94dcaabe919f3e3dbbed2000cebbadfd8fdf9f3f5e6f8ade5dacd2a188beeacf109f7f6032cedfe14fdf6fc80a80100),
    .CHANNEL_BETAS(512'h7826778777a978cb780777de78ad7ae177e277ad78dc7794782477e77879780b7861781f79ba785e788f783f7893763e772078bc78107707781f79a97add789f),
    .CHANNEL_THRESHOLDS(512'h01f80209020c01fa020b0210022302200224020401f801fd020101f001f601e601ea01fa020f01fe021401ec01ec0217020701f701fa0210021101ed022401ee),
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
    .KERNEL_WEIGHTS(46080'h0b0e093d51461629032b1a2e313325021d23e40503282a17202611502a4a595e59353a2af7e422240f010c170ceff6fe1528130014122d3c155448303713f9ea2218191918f9fe1f53273f634b5e7f7f7f8080808080809d8cbf8080808080808082808080bc8088a98094b6ba95895c50467f7f75efe7e82304f542111e7f7f7f7f7f7f7f7f7f35647fec3f73bae44599a880f8dc9bf8e38a484a744d31597f5d7f8080808080808080807f7f7f676e5f74767b808080808080808080e7daeefafcf71afdf880808080808080808080808080808080808074454b4224493a342f9e83afc4b2e318130480f30c80cbfe808095d1e1e8ff0af1e109e8808080808080808080808080808080808080201c223648294d2443c4afbef3dbe71f2510808080808080808080808080809a8080808099808dba809fd0a4cc1c2659595d5d7f7f7f01fa0ef6f2fa132752f8364084d3048092cf809aad8081a780868c808080808080808080ecf616dede05bcbfd5e9f013d7e7f9ccc2d1d5f502cfd7f2b2bfcfe7ec03cde000b9badceff909d9ddffcdb8c9d2e205d3e3fbb7b4d5e3f207e1dd03bdc9dfc8d205c9c3e9b6adbb80808080808080808066466a5a364e6c476709f01108fb12080010accff1c0bfc5959eb88080808080808080807646734f245262434dd4e9dd060e01ece1e76b777d53677f4a425bf9e0dcf6f3f602fc02fed9f8f4e6e7fedaf9bbcccbe0e1cabebfb8ebe8f7f3e2f1f5e5df63434b4b3246784c63d7c9cce1ecebd6cfcd250424292027291d2afefcfe1f380e1122ff48345d3829514f384f808080828980808c805c7f7f59687f525365122722201c2e010b045659745f686f454b429eacadbebcc8b9c5a4a8bba0d5d7ceabbcae808080808080808080808080809080808080e5f3e0fc00f6fb00f40efb05feff09150907e4f206f50b08d6eff57f7f7f72597f7f627f281915192d271c140f466d7f566e7f56597ae5fcf907121ce201058080c88080808080808080808080808080808080b5808080808080808020808080808080808083808080808080808080808080808080808083808080808080808080808080808080809580bdfac3b4bed6d3b0ade39a9fc5ac81f8ebbb1d09d5d0cdd98080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7fa58abb93b7f3808087e9d00bd1f31180a2fc7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f5d6a7f36103fd2b17f7f7f7f7f7f7f7f7f808091808082808080808080808080808080b1a3d2c1bbcccfc0ac8080808080808080809d89c48280b08080838080808080808080807f7f7f7f7f7f7f7f7fbdf07f80807f80802680923c80ab058080c1808080808080808080210c1912e502dbbbca7f7f7f7f7f7f7f7f7f0cee37f3051a18dc1e746974677f753b33497f7470471e34dfcacb80809b8080808080808080808080808080806335364f687f4d4d7cdaf1fcd3d3cd8e9e88e7e4ece6ebe8f0ebf0d7dfe1ded9dde8e3e2e2dce0e2d9e1e7e5e6ede5eae7e9e7f1e6f0d7d3dadfccdcdecddfdedbe3e2d5e8d8d2dee8daecede9eae4e7e4d9d4e2d7dbeededfe5dde2dce9dae5dfdfe2e7ebeff2eef4eef5ebf3ecebf4f3f3f6f7f0dad1d2dbd0d3dbd1d2dbd0d2d6ddd3e4e6e0dfdcd8dee2e5e2efecf7eefbfceefdf0fbf1cdc6dad4c3d7cdcdd5808080808080808080f2f5effaf2f0f8f9f7808080808080808087ebf0eeecf8f3fafcf6bdc2bebdcbc9c6d0d4c3c7d3c9cfd2d7d4e00f0600070a08070bfee0dde5e3e7e3e7dadcf4fa03f6fc03fb0101ece9efedf0f4f8f6f5f1edf1eee5f0e8eeeaf3ebe9f6f2eff7f2f7d1c7cbcac8cbd1cfd5bdb7c3c0c3c4babbc0f5eeeff3f0f8fbedf0f7f1eaf2eef3f8f5f2afaec1aeacc0b1bacbb6b2afb3a5a7b6b7b2e0dae2f1e0eae9ece7d0c8ccd6d8d1dbd6e4a8a2a0aaa8b0aaa6a8e0d4dee3d5e3dad7dfe7dee6ecdce7e7daebfbf7faf3f7f8f1f1f780808080808080808080808080808080808095bcd5ccb2e3b7d5fd808080808084808090808080808080808080808080808080808080808080808080808080808080808080808080808080808080ae808023433a8283c7808080fec2d8d9d2d0f3d4e9b2a34b808034808041808080808080808080808080808080808080f6ae8037dc8d7f683a8780b380a3ead7e0f48080808080808080807f3934230cf20de3b37f7f7f7f657f7f4a7d7f7f7f7f7f7f7f7f7f8080808080808080808b808080808091808e6c7f7f5f4c7f1f4663514e7b3e456c4f28708080808080808080807f7f7f7f7f7f7f7f7f808080808080808080b881abc7bac2fb05237f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f671f3614df1c15ec097f7f7f7f7f7f7f7f7f96bfc090a7baa8ba9e7f7f7f7f7f7f7f7f7f584c524f7565613e537f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f808080808080808080657f7f5b7f7f7f7f7f7f7f7f7f7f7f7f7f7f1b09191a1a2025121f080a111e1f171d1f1d04f8091003031b050a05ff061c0f181d110c121320221b282721270d0602160810170f0f090c0a261717241a1d28192245363e4031411b3b4d0d1c2dff041c7f727f7f7f7f7f7f7ff7050cd9e5f6b1b5d01d140b34261133221fe5f9f4e7f5fbc9dce0c1cfd2d0e0dac2d1c5a9a7a6babcb4b7bcb60dfb080a0304f5e4e5b9c8c4c2d9cdaac7be736156604f44674d49c8d4c8dae8d6c4cbcd040001101afd15190ad9eae1dee8ead3d8d7edf907f3f201b8cce27f7f7f7f7f7f7f7f7f7f77777f7f7f7f7f7f22110c25120c2d130ffceef700f7f7f4f2f8eef2f504fcf706f9f8f1f2e8fffdf1160a02d2c5cbe3d9e3e5e0dfe6dde9f2eef4f6faf01113161e1c233a2d201e131730282c2d2d30cfe7dfd0eff1bfdad7e5ebedf1f5f8eaeef106020309000619060fdbece5e2e8eedde9f0b8c6d1cbccd5bdc9d22319101e1b180e1110e7deeee9dee0d0cacd26131e2f2c2b4b3f3cd9d9e3e9e7e2eae4edcfdcdadadcdcdde9e5dcdbdae8e4e3eaeeecdbe0e1e7e9e4e8efe6dde0e6e0edeae7ede6dae0dfdddee2ece7e2d2dddad8dfdadde6ded5dfe3e4dde5e5ecedeef8fdf7f4f9fbfffde2e0dfe7e3dadcded6fcf4fbf9f4f7f2f7f29bb0b898c2cea1c6cff5f2f7faf0f5eeedf2ece6eee9e7ece7eaebed010ff4fc07f4f705cfeaf7b7d2d3a5bbc20b07060b08050dff0af7fafafcf7f5f6f6f2030005f8faf9f9fcfbe8dee7e4deebe0e2dffef703fbf1fbf6f1f5ecf8fce5f1f7e5e7f4eff4eff9f6f6f6efeaececf1f7f7f7f0f1eed7dedce3e0dee3dfd6eeebf4e9ecf2eaf1f0808080808080808085b8c6cdb9ced3c6cfd9adc2e0a2b3cfa2b3c9adcbe1b6cddbb0c9d7b8cbdfbed0d4b6c7d9d7dfe3e1e5e4d7dce90d0b0f0a0a0a050908f9fdf7f8f4fdf9f6faecedeaedeaeff3f2eafef8fcf9f9f8faf6f2151b1f10101f080d11848fa18893a88e9aa19db1c48aa2ac8692a4a3a6b6acbdbea1b9be000300fe0102010201000202ff0303000402000102fc0001fd0105fdfe01000003ff0300030304020204040205fc00fffd00fdfffdfffe0100fdff01010100030404030606020407030304030504040303eeefeee7e8e6e5e5e50706040606030905050407060106060403070a0b090a06090808070504040201010201fefbfcf9fffdf9fefdfbfe02010102ff03ffff0f0e0f0a0b0c0c0a0cfafafbf7f9fdf5f6fa010202000303040303050304ff020300ff0305020100ff00040200fdf9f7fff7f9fefdfbe5e5e5e6e9e6e7e6e6f9fbfaf7f8f9f7f8fbfcfefbf8fbfaf9fcfbf9fbfffafc01f9fd0002ffff0101ff00ffff01fe0002ff0001ff01fdff03fd0102fefe01fdfaf9fefefafbfefbfefcfdfffdfb00fefe0101ff0102fd0002fdfffcfafffcfc01fbfafdfcfc00fdfdfdfffdfbfafbf8fbfbf8f7f7f9fcfcfaf9fdf7fafbfdfcfdfdfcfbfafdff040102020203040302fdfdfcfeffff010200fbfcfafbfcfdfffcfb7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7d7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f44554b616d638080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807a7f5c7f723e5e7f358080808080809680808080808080808080808080818089808080808080809d8a80a8c6b680808080948ec5e1d780908080978080a69d7f7f7f7f7f7f7f7f7f8080808080808080807f577f6a1e337f717fdcfce2c3f6dee3f4d6f1c69a969a808580807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7ff3807ffa807f76d27fb9c37c959b7f3c2e7f7f7f7f7f7f7f7f7f7f7f7f7f7f6f7f7f657f7f7f7f7f7f7f7f7ff8dddbebe1f013f11a8080808080808080807f7f047f7f527f7f7f8080808080808080807f7f7f7f7f7f7f7f7f7f1e807f7f807f7f037f7f7f7f7f4e7f7f7ffcf5f50cff0f120b01f5faf30e07130d10120af5f9261a1819212006f1f7170e16270e20f2f0ee140410020408ebdbd811080619050302edf60f0d0515090ff9f0ef1710020a100db9bbcdc0ccd6d5eef2e9f9faeff1fcf0eef9f4f6f5f3f7fbfcf40280808080959580808911030b09fcfe0afbf801ebfbfaf5f2f6eefa808e8f808b99809d9c8080808080808080803122291d231f2c2925dde8e9efedfe0501050504fb02edf503eff7b1b2bb9c9aa89a9092090306f9f504f4faf680979e8282808a8080b9c9b8c3d1c1bbb4b7b3b0bbd1c5c6cfd3c9d0d4e7e1e0e7e3ebe4b8b8b3aab1a6a2a99c8080808080808080808080808080808080809fd0e1b1d3c09fcbc480808f8087a38080808080808080808080808089958080808080800c1015fe050af1fc09fdf9f6f6fdfaf6ebedf1edef01f2f9fdf30303090aedf5f9e6ebfa1c11151e19130f0f138080808080808080808080808080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f80808080808080808080808080808080808099f4c3a8a9898080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080808087808a98808080807f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f8080808080808080807f7f7f7f7f7f7f7f7f8080808080808080808080808080808080800e09f9c2e9dc9edfcd808080808080808080477f732e4461425170808080808080808080808e808080808080887f705747f1fe04f5ce0a0f00c50dd59bcacb7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f3374600b3b2e01341406260eb6d3bca7a397ffd0eae2adaff6dc9280808080808080808080808080808080808080a08a8080808080807f7f347f7f417f7f746e610e44631a7f7f477f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7ffaedfff2cbf5f6d9ebf1dbf3ecdaf3fbc7e5e8dbe8eec9dffce3e6fcecf6e5d2eef1daeaf7eae8eadbe701f4fcebf6ffe5eaf107fd080be400fcd6ecf4ece3edd1eedfbbc7d9c4e6808080b2b2b6b5b09ad3f3e9d7f3fab7ccca8080808080808080808080a58f809ab2adbb7f7f7f7f7f7f7f7f7f2b3028431915452d393829134834122808ed11fb1605091efdf50fbcc7ccb7b6b2e7ccc8afc0ccd9f907d5e9f4fad9e7fae7f416f61c03d9ef1b05050dfb107f7f7f12fc2a111b40e9bcd603dff6f6c9d27f7f7f7f7f796a767f19e3f81afdfb01ebfc2226381c243313112f121b1a2a2204190d140eedf014f4fd0ff5f3ab8d96e5d5e0e8c9c9b6b1a7aeb6add0d5cc16f8191a040506eb03d8e6e2fee1f5e4d7e079494152252f51343e294d7ff51c6122547f7f7f7f7f7f7f7f7f7f2d312070766e424b45e5e5d601f0ed10edf5bec0d0c3e1eabbebe6ebdbe8e2daf6f2f0f82308f91df0f518f5f84353563b31402e3341838080808080808080808095808080808080bdb1c38f9fa3928080808e9b80808a80808080808080808080808080958680808e808080a282868080808080808080808080808080807f7f7f7f7f7f7f7f7f7f7f7f7d2d373b200e7f7f7f7f7f7f7f7f7f9796929698978080808080808080808080807f7630503febf0ac807f7f7f7f7f7f7f7f7fd8b8bcf4d4cdd4ccdcebc3990ac7b6da87807f7f7f7f7f7f7f7f7f0a4b7d042961c3e0317f7f7f7f7f7f7f7f7f8080808080808080807f7f7f64734c7f6f7f4d473a7f78495f47435711162f2a294d2811164265f7eb26fbf1447f6e447978537f6b578080808080808080806a53674a525f5046738098998098aa808080effefbe5f905fcee13fecbcfecb0df13f3dc8c8080b8c998c4969f808080808080808080d5eac86f50252329fc7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f120462e2e535ef021b8780a293aa8095808080848080ab818f8480808080808080808080fcfdfbf9fafcf8fffef9fefbfffbfbf9fbf900fdfefcfffb0202fcfefbfdfbfafdfefefd01fdfe000201000202fe00030403fd00fffffdfef8f9fcfbfefafcfa00fffefafefffd01f7f6f9f5f8fbf6fbfbf2f7f2f9fbfaf8fffaf7faf5faf9f4f9f9f5f8fafcf9f5fbf5f8f6fafcfc00fefb01fc01e3e7dfe3e5e5e4e8e2030504040501080506fbfa01fbfb01fcfe00bac5c8c3c9cdced5d2fcfe01020101fe0202faf6f7f5fbfaf8faf7040306040507040308f7fdfafafbfefafaf9fef9fbfafbfdfffdfefbfcfdfdfffdf9fdfbfcf7fafbf8f6f7f6f7fbfaf7fcf8f8fcf9fbfd0302fefd03fd00feff0201ff0203ffff01f7fcfef7f9f9fdfdfe040604070806040603fffeff01fefc02fdfdfdfaf9fcfcf8f9fbfe0101fe0302fc0100ffff02ff040003030402f9f9f8f8fbf8fcf8fdf6f6f5f2f6f6f6f3f4ff0401ffff04fe010201ff0304fe03fd0003fbfcf9fdf9fff9f9fc01ff0202fb010201fd0300000003040303015e685e7a6460362c404e4f6367725b3a384552675f5e6469404d474b545d5a4d55331d3f7f7f7c7f7f7f7d7c66636c5c68777f5f4251694c606e625e3d335b787f7c7f7d7f6a6f62cbbbb312e6061a0f0f7f7f7f7f7f7f7f7f7f08f81729001a17033414fd2612fb0a05ec1d2efe202804193e1b507f7f7f7f5d7f7f7f7fe6f523211f511e2a4a7f7f7978567a6d666a5c35537f477f7f7f7f4f454c503c414e43616637596246777f4c69cdaec2d0c7bfdc9cc92d29461c0a052c0b1a8080808080808080809887a88d8ea2a6808180808080808080808030205420ef34fef328dae5f0e2f90bbad0f665527f7f767f63747f80808080808b8080987f7f7f7f7f7f7f7f7f80808080808080808080808080808080808005ccce1a00082108e17f7f7f7f7f7f7f7f7fa484978380888080808080a68f80a4808093e4ed24f40c0feee90f7f7f7f7f7f7f7f7f7f21060618faf91ffffb4a507f46657f5e7a7fc0d0dfd1d5e688a8bf7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f2b696f9998d280809b80808080808080d7a19180838080808080807f7f7f7f7f7f7f7f7f808080808080808080808080808080808080517f7fe83c7e80edfd9b80b8808080808085808080808080808080808080808080808080808080808080808080808080808080808080808080808080808080de5e7f91e15880dd1b8080808080808080807f7f7f7f7f7f7f7f7f7f3f337f7f7b7f7f7fb180938080a0809ab57f2c62671b2f781c4f1e0c39e4e9fd16e2e817beba26acb356d2c8b18381808080b78dae7f7f7f7f7f7f7f7f7f808080808080808080809880808081808080808080808080808080808080808080808080b5c912c1091c17054a808080808080808080333923311d307a727f7f7d7d2a0a100ee5d026d4ff09e9b51a0212),
    .CHANNEL_BETAS(256'h4a175272525779953265670d723d751a42a86e3f2a4b6082469c78f44c512c4d),
    .CHANNEL_THRESHOLDS(256'h020f022701c2022a020202a5015001ff024e012c01fe01df02330242020e0259),
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
    .CLASS_COUNT(11),
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .PREDICTION_BINS(10),
    .READOUT_WEIGHTS(1408'hf0ffea070af3ebf3f6e30211ee09f70a08fc0007ff06f6e809aefdfd0504f6fdf4f5f9f60ff4f0f903ea08fc0604f70805fef60ffafdeefd09f8000df201080a0ff6f1fd0dfbeaef01e6f6f30ffdfdf90a14fcfd000100f2ee17f0f90ceb11f30201f6f509f4f0010cfb0c02f8100805f7f3e0f305fbd9f004800ff6f001f80cf4fceff0f200ebf308adfd000101f40bf8f4fc060a00f5f706020110f70b03f6fbed14f707ee030601150a1af5f60de6)
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
