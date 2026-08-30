`timescale 1ns/1ps
// Generated file: do not hand edit. Source is model_spec.yaml graph + ROM images.
module eventspikeseg140k_dag_top #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer RESIDUAL_MAX_EVENTS = 0,
  parameter integer USE_SCORE_SRAM_MACRO = 0,
  parameter integer USE_RESIDUAL_SRAM_MACRO = 0,
  parameter integer USE_ACTOR_STATE_SRAM_MACRO = 0
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
  output logic [24:0] actor_trace_valid_o,
  output logic [24:0] actor_trace_ready_o,
  output logic [24:0] actor_trace_completion_o,
  output logic [25*PAYLOAD_WIDTH-1:0] actor_trace_payload_o,
  output logic [25*TAG_WIDTH-1:0] actor_trace_bin_tag_o,
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/00_detail_stem.mem"),
    .CHANNEL_BETAS(128'h796a752d71fe7a7670e2773a767c712e),
    .CHANNEL_THRESHOLDS(128'h0165015b0196018f01a2016c029c0173),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/01_detail1_standard.mem"),
    .CHANNEL_BETAS(128'h79df7a067a7d776c767779cf75fa7aa3),
    .CHANNEL_THRESHOLDS(128'h0187016e017501a601c501a301c30172),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/02_stem.mem"),
    .CHANNEL_BETAS(512'h76b1795c78c173cd7a9f77cc76d47705726b7578785b6c85736e797070d171ec755478db745b763c78997a316b52777a79137849787679d17a157976750473f4),
    .CHANNEL_THRESHOLDS(512'h020b016e0206020f01d60310020c02db02620237014d02ab025c014202220230024b015c023101ba01e3022b02b001790156026901de02430177025c01df020f),
    .ENABLE_INHIBITION(1),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/03_enc1_standard.mem"),
    .CHANNEL_BETAS(512'h757e7950780c784974a3780576da7b5872aa6b9675c6702473b0770b72bf6591747979b4750f6fb376e376586d37741d785c77e674b073c079456d5167e671bb),
    .CHANNEL_THRESHOLDS(512'h01a6019302a9021d01d3027b01ed01d801e00231016102aa01f9018201e1020601e7018602ae01c4021501b502420195018e01bf018f023a017001f601e501c3),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/04_enc1_extra_depthwise.mem"),
    .CHANNEL_BETAS(512'h78af789e777b794078fe790d764f7a11789579d877fc7af3768f796a781f798e796577cd7a55793078ac77fd77d47a047aa67998788c77927bd979de79977a6f),
    .CHANNEL_THRESHOLDS(512'h022101bc024601f701a3029102410284022f025101de0265020f0204019a01f7023101e5026a022502320224026201a901e6028e020502230235027601ce01e3),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/05_enc1_extra_pointwise.mem"),
    .CHANNEL_BETAS(512'h77f176a7761d7596767675c375db77e07211728475ca7560756877b1736b6dc976d177be76a47045768472607549758276a3750b786576e2756f77796bd36bc8),
    .CHANNEL_THRESHOLDS(512'h01ad01b301f801ee01ea0211020401f70252021301b90242022301cc0207023a01f401c0027a01e201ee01ca022001c801a901f201e3023201ad01e30244022b),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/06_down2_standard.mem"),
    .CHANNEL_BETAS(1024'h774376cb794676dc765577ad78f176cd78ed76277699740977d87701763277c6776d714a780579746f7878d46f88761775d37789770d74b678d876d874a276f377c476da7599796477ec77d477267795771076d37803774677947831784374577473779b7698780f76ad76de785c753877fd78e67886799c742775ea77a37781),
    .CHANNEL_THRESHOLDS(1024'h023c01df02370246022b022a0216022c01ec027f0211023901ed0223025201f20266024701e3021c0247023002490210021f0229020b027d01cb01eb0244024401e0022302090227022201b5020b01ce0203020f023802420254022b01af01ea0219020201d20242020b021202240230020a0202022601d1021901f401e901e8),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/07_enc2_depthwise.mem"),
    .CHANNEL_BETAS(1024'h7932793e780478c9790d786578837827781e78a67801777578327878785e77e877c87869793b788577af785b78b277e3790c78267838799e785278e679d678c177f978cc78077817781177f17783789f7816781a787377f378b078c7780b79f079b1787277f7790679fb77c6780b78c377eb7835780f786d780279257847780a),
    .CHANNEL_THRESHOLDS(1024'h020f0240020201f301e201f0022501e5022a020b0239020f02160219021801e90210021701e30204021b0200023a01f4020701f401f60265022801e7020b01fd0219022a022401e601d601e201f601ed020c01f3020f021101f9020201f6023e020e021a01f902130231021b01e801f401f101ea020e0209020a01e9020701fd),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/08_enc2_pointwise.mem"),
    .CHANNEL_BETAS(1024'h77c076b279d577e67792796978ca76d178f677e578d4778a774879ce797976f2788378ea7794799f788479347690778376e7780677c7793577c577797758781076ab78c77851796d786a788978997986788d77667870790477f278e076c1797077eb78b278137951773a7780792e78867838787077f3787276da781e77ba7834),
    .CHANNEL_THRESHOLDS(1024'h021d020d0239022a0244020c021d024501e7024c0237023c0204021d0235021b0246024c020a02230249022c024b0241021d023301fe025101db021b024a02340206023c021a021f01e601fb021701dc01fd0214023c023c0228022401e401f40236022001f9022d020f0228024d020c0228020e026401e2022d021b020001db),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/09_enc2_extra_depthwise.mem"),
    .CHANNEL_BETAS(1024'h78a876fe7834786e785978d5794378fc781b7951788e77ce78ca78d6788478ce77937843789e7806791e77f6790e79f3781477e07877781077cc78d5777a78a679a07870778e77e778b97882780c776477be781978ab780b79bf789f78607aac78bf771b7870791a78eb7873780b792578707837785377fb785579d3789d78ce),
    .CHANNEL_THRESHOLDS(1024'h0216023a0201022101f902060249020201e802390216027401fa023a022f01f401e9021301ea0208020a020a022d020101fe01cf01d101e1021301ea0214021e01d602180220021e01e401fa022f0213021402200226022a0206021a0216025a01f201ea01f10248022d021601dd01fb020d021702240203021c01f6020401f7),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/10_enc2_extra_pointwise.mem"),
    .CHANNEL_BETAS(1024'h784275c778fd78187752798177e1774777c476cf78c477c97827798178c477ca7850784977c4772d77b778fa77a8777b77e2784d78a47995789377c578217853786b79027908798b785b77c278d778ad783177f376c577f2775a787a77a9776b7879796478387814785d77c678f8781c7819789b767378d6775a778e786d77d4),
    .CHANNEL_THRESHOLDS(1024'h020901fe024802270215020a01f8021301e8024a0225021701e7020e02470202022f024b020401fa023f0210023e01e9022a020301e9024d01e502270238022301f1024802160219021a01fe021b01d601f602190224021f020d0239020901ee0229021601f502200205021c024d020f02020206023401f50228021501e301fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/11_down3_depthwise.mem"),
    .CHANNEL_BETAS(1024'h7826776f77f677f377cf77f87924786f776378ca77f9792477fe780b77be770e77a8777d775777cc789277c9787f7862779878327780788577a177d37813788577c7778d786f7804785377e077cf77bd7824781479127790778a795f777a781d797e77e0788e788277f97801781877d377637825771c7774789476ab77f07885),
    .CHANNEL_THRESHOLDS(1024'h0238021801f7021d01ec01ff022001f301fd01f901fa01fa020101f9023e01f10217022601f802020222020802170212020d02270217020c020a020a020e020f01fd01dc021b020101ec01ee021702010203020201fb022801f4020901ed020c021001f201f401fa020a01ea01e201ff01e701eb022801f1020001f401fd01e5),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/12_down3_pointwise.mem"),
    .CHANNEL_BETAS(2048'h77a9787c77c678297833785d781f77ce789b789d782b781a782877b077fd78a678747848778477c1785577bc778278247775785c7860785777ca784c7796781977f177b0787f784778dd7862787977be76f3786a777077b477dc770577a2781b77d477d877f5784e785b78a978147819783b77ff782c779e785a786077ed780e777d774177d877a978a5785177f4785c7862785477c477dd77d7781776c0785a782e78e87811784f77b977c37842780977c8785e785a777a788778a777fe781577c6789277ee785f77eb77e277e5785c786a77f778317835787177ff783b7830784b771d78bf77b8781b777e77de78b37843783f7817784f786177e877e577c7),
    .CHANNEL_THRESHOLDS(2048'h020701f2022d0206022101f302270231022c0205020d021301ff0213020a0216020102040206020f01fe020301ff022401fa0212020101fb02060234021b02170217022801fe01f601f2020a01fb021f020a02090214020f02230202020e02210212020801fc021d020102160206021a0229022501ec020b021b01fb0206022e020501f4020f0206020f02200214020801fe0217021c022a01ff021b01fb020c0201020101de01fe022d02120209021e01fc01f8020d0204022001ee01ef020a020f01fe02230207021b0215021a01f801fb01f101fe0203020f0223021701f80211020b020c020502240213021b0208021a02260202021d0216020401fd0220),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/13_enc3_depthwise.mem"),
    .CHANNEL_BETAS(2048'h7939785677fa78dc77d377e478697809783f782a77a9782e780977fe780b7813787b781d789277fa77f078ab77e977e777c277fb77db780677f877f477a7782677e277fc78317794781277fa780d789677b7783a7773778377f4782178a2780477fd77c277d87804782e7802782e781c77f577f077ba781c780b77ec7837784577f7772c77d877fe7828781d7818780077f8784c780e77fb7854781b787877ff7805783977d2782177ef7814781d78017850780a77e9787077f6789d780377da780477df77ed77e378537781780678307827787e77e6788277d0781c782477b877ee77f9780e77dc77fe77d877dd77da788877dc779b784977e777df76a97816),
    .CHANNEL_THRESHOLDS(2048'h0203022601f101ce01ef01e801fb021601ec01d60203020201f201f101d001f701ee01f30212021901ef01d801f7020b01ed01e201ec0202020301fa01f301f001ff01f4020f01fe0201020701e801fb020b020b0202020101f701e201da0203022001ee020e01e6020e020b0200020c020f01e402010209020a01f401ff01e201fb01eb01f50223020a0212020401f10201020a020a021501e801f901e001f102020215020c01f0021f0204020402180203021201f601f2020201f701ff01ee01e901fc01f4021a020e0229020b01fa01f501d601f301f001ec01f201e201ed020101f101ea01e801e201e101f3020d01dc01ef01ed01fe01f5020f01f4020a),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/14_enc3_pointwise.mem"),
    .CHANNEL_BETAS(2048'h77aa78967802785478107651780f783478f77862780277cd784d7783775d7851779478cf77e9779c77e2780a7852786977ee77be77ea77b177e3787f776977dd78cb778678537781784b7746781577e37849773977b8784d77a977d677fb77c0777477cc783d781d7891780c772e77e277ef785a77bf7749785c785e77cf77d5788d78f577d7770f78787857776c7781772d77ad77fb7829784d784177dc77ce7846781277e877d777fd783877d077f0779e777a7828783c780f78f7774d78097778785b77a8788477e2783b77c0788b77f67744783f77ab78a577ed77eb78907824779a786b76da785e77c278347842780877ff783f77a07857775077f27803),
    .CHANNEL_THRESHOLDS(2048'h01ff01e80215020a022001f702230211021a02080220021001fa0216020902210219020801f9021b021401ef01fb022c01fc021b01f8020802030215021b022502260224020c01fd0205020f0205021c020902160212020b02190205020d02220210021001ea021601fc0216020a022a0227021401e60215021801f602050236020001f801fb0210021602210212020b01f80214021a021f01fa021b01f602100206020d01e8020c02250207020c0220021601f3020c01f7021b01da01f7020b021e0203022701fb02150220021e01f6020401ff020902110217022702150201020d0201020d0207022602140219020502150210020d022102130205020e0210),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/15_enc3_extra_depthwise.mem"),
    .CHANNEL_BETAS(2048'h789877ba77cc77cf77b4775c7808780178267815784c786c7816780f780a786677ec783378b5782377c9786277c5780277eb77c87825782377ab781f781d77f577b077ea782f789377f978397821783278be786a7836781178007840788f77c7788177ff78a8781f7829780e77f77815782877f977da781c780c78a2780f7818784976d278b777f978117828780377ce781d7818780d782077ff781277b577df782077f4785a78a7783d7831785a7843780e7840785777be7815786b77da77c378007849783177f377eb77bd7807785277fc7845780e77f577bd781b783b77db782d77a2786378097817786a7858780d77cd785978f47812780077ba77827841),
    .CHANNEL_THRESHOLDS(2048'h01de020801fe01ec01e901f1020701e701fd0206020201eb01ec01fa01dd020e022301e501e601e5020301e501fa01f101f101f201e501ee01f2020601e901f801f1021101e901f801ec01fa01ef022b01e301ed01e5020901fd01e00208020b022d01f10206022101f601f1022a01ee01f2021a01eb01e9020401cd01f3020c01e601f701f2021001dd01ed01fc01e301cf021101fa01df020401f401fa01e701f001eb020801df0219020d021b020d01d601ec021301ee0226021201f1021501f601ec022b01e801fc01ed01eb020701f301e501e801fb01ea022501e801ea01f101ec020501ed01df01f8022301f501e801ec01f901e701fa01f201f10203),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/16_enc3_extra_pointwise.mem"),
    .CHANNEL_BETAS(2048'h785d78e2782a779c77bb784077a6789878a377c477b977a87813773976fa7888776e791b789c774877b3785678907816783577b57872778277b977e17800778378aa778b78987872783677a877fd777e790d78c077c377d1774078c677c178397769771c789f77d3782977cb771a77d3781578347802777f782a78d777fc77fb794f78c1780377aa78497800778678bd784f776c77c577fd785977ef7817779677f77846771d784977a077b1777d77ad773078a8785278ac782a7860784278c2772e789e7769778b774577d577e4781f77ff77f677ff77a8783577dd781177da782a789977fe766d77d9781d786a788877e27833780d77e9784e7774785e77c9),
    .CHANNEL_THRESHOLDS(2048'h020a01e4021d020c021f01f602210214021f0210021c020f01fa020c02090207020f020301fa021d021401f201f8022001f4021b01f30205020e0219020b02190226021c020801ef0205020c0206021601ff0204020c020b021602040213021f020c020801f2021701f9021b020b021b0228021501f10210021701fa0201021801f9020701f2020a02160221020d020c01ff020e0214021f01fe021801f5020e0206020401e001fc0227021002100217020b01fb020801f9021b01d101f30202021401ff022301fb02190218020c01f6020801ed020f020e02170218021301fc020f02010218020502200207020c0201020f021e02090223021401f1020a020c),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/17_context1_depthwise.mem"),
    .CHANNEL_BETAS(2048'h77bf777c780178ba77d976e8782877b677c4789778fc784c7877785877dc78ed789d784b781c783a788e779b786277f277d8783f7802791b786b7792782a78207827783977fe786b780e784e78a677dc78aa785078c178057840787478b7780d781477e178e178217899783e784c77ff78a477ef77897815783d77e77869780e78a177cc790b782c783b7809782976f377c6781377e07830781477c7763d7875787d781e77cb781577ea78c2789878cd780c77dc77e6787278d77831780178ff77fd784278697774783177d27872777b784777af77e378067844789b782f7813781b781b783e7802782778897837777478a278b87820783e77b77884780b77e9),
    .CHANNEL_THRESHOLDS(2048'h01ff020201fd0217020601ef020c01ff01fd01f601f3020001f401fa01e6021501bf01f301f001c901fa01f301fa020201f4023301f401ef01f0021801f702350221022901f1020d01ef020b0205020901f501ec0202020001fd01fa020b020c02070214021d021701fb0203021d021501f20206020e01f901fe0213020d01e801dc01fb01fb0201020401da024301f701ec01fe02010203020201f10200021202000200022d01fa021d021901f501e9020301f6021101f001f1020102040212023801ff01dd02090208022c022b01fd020b01df01f70225020b01e4020201f101fc01f80203020d020601f7020201f302070207021b0233020301e801fc021d),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/18_context1_pointwise.mem"),
    .CHANNEL_BETAS(2048'h78cf76db785e7868772777a4782178987948781b77d5777278df76d6777d7817773276c077ac76f277867726794c7815791e77b7782d77da785078fe777677f078eb7726781f77fc784e780477db76e27751780877f077f076b977b1777477bc7743773f78a577bd76fb78d07685780f782777a878bc77ce77cd77f67877774c768b7869775a7845781877b7776c78167845771d783f7865786d77cb77e37741781477dc76e57891778e7740778077c176f4776577cc77367831799d7740784777377776771d7742768b7786780f7899784d77e177e877a4781c776b77ed77fb789e77d87813779777a3778177c57841785e7824788577a7775c7718776377dc),
    .CHANNEL_THRESHOLDS(2048'h020d01f102230202021701fb0208021c0201021202150201020702030201021d020c020d02030203020e01fc02010224020f020002010208020a01f6020502080220020f020c01fb0208020a020002150201020301fb0200020502070209020c020301fb01ee021c020c021d01f802070220021001f2020e021201ed0205021b02020203020401ec0221020f01f60218020302060206020701ed020401f702140205021601e10200021f02080207021901f001fc022201f8020c01c901f601f001f00208020e01fd020d0214020401f1020102020204020f020502140205020c021a01fb021201f6021302040214020701f7021902160212021101f401f501fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/19_context2_depthwise.mem"),
    .CHANNEL_BETAS(2048'h777a776e782f78ff77f5770c791c7834790e77f5793c77f0789c783679e0795f7875779677e078d8782a779977bb7820775877f7793177c278a17983771f77cc79227812784977dc77f5781979187870762577e7789f77ec7850774e78d678c778be77f778db797c76f8784d784d783677fc78087708790078087766780677f5764b77fe78d078a177f27817782878067758782e78bc791f773e782576bf7872780077e2789d787977b2787c77e779047804774c785d769d7752783976a776f277fb78867813775977c278af783b78aa784477f4772d78fd770378147803780c77e6772f771379e9785277fc78ee76ec76ee788677cc781778ae78a877a17825),
    .CHANNEL_THRESHOLDS(2048'h01fc0204020601e7020801f0020d0209020201fe01ff02020203023101f501f901f7020801f7021401f60211020401f801f8020101ef01e901fd01d202000206020502220204020e021801ea01ef01e20217021001ea01f701f20208020201ef01fa020701f8020a021001f10212020701c4020f01db01c101d0020b01fb01f2021001f701fb01de01e101e001b1020b0211021601f801f4020901f401f1020001ed021201fc01e401f10221021401e901f701f801ed020d022201ca020701f501f70206020801f90209020301e201ef020a01e50205020b01fb01f902100201021d01f70215021301f00203020501df0224020e01f30215020201bf02000215),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/20_context2_pointwise.mem"),
    .CHANNEL_BETAS(2048'h78ea7980789a780177ec78e177da78e078be7785777a76fe78b578db776e789d77ad78e878a67687779c7908787677d37969790f78e87a58790d783c7719794e7906771b78ac7959796e780578837756799578e577b5785a765779f177e977f176bc771678407819787d7826775e77c6784f77e978d9777677e57916781d76b97908781b7928785378ad77a278cd7954798976fe780f77c1789c780b78ca76b878e9788278c4784d77b4771977ee7926785f785c788778cc782178c1789e77db77e5798178537962773c76f2784b78da77c17925789d77ee783b7766780e7904797379dd79da77d977e177ef779579bb786478a978e47840781078a377a877ab),
    .CHANNEL_THRESHOLDS(2048'h020501f7021101f6020201f30210021c020c021001f8020d01f201ea01f1021c01ff01fd01f201ff01f901ee01f5020f021401f501fd021201f40211020901f5021b0209020501f0020302050208020201ff01fe01fb01fe020c01fa0204020601e201ee01ec021001fc021001e601fd020a01fc01f40204020c01e601fa021901fa01fe01f701ef020b020901f1020d0204020b01f8020a01f001ff01f60208020a020801c30203021601fc01ff021001e601f6020d01f4020201fa01f001f501fb01f8020701fe020001fc01fe01fe01f901fc020802140202020e021d01f302170203020501e5020202020212020d01ee020302070203020201ee01e401f8),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(1),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/21_project3.mem"),
    .CHANNEL_BETAS(1024'h782b78a5790b79eb7968777278b5756077ec79d8798f78507645798778d3785478d87933773f76ef799a7732792b76ba765b76c376cc786978587779782c7968783478d678b4767c792378b677b376c7771e78e5770978bc7859791f797476df77cd787c785c797f796d77d077887701770578337725769977cf776374dd78ff),
    .CHANNEL_THRESHOLDS(1024'h0218021e021c021001f301fa0207020a01eb021001f801fc0208020901fd021201fd01ed01f5020e01f501fe0216020702080209020a020e020801f201fe01f601f5020b02160210020c021102080206020e0212020301fe01f501f9020e020f0201021301f501dd021101f7020101fd01fa020e0207020b020001f801f70202),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/22_decoder2_fuse.mem"),
    .CHANNEL_BETAS(1024'h77a374f17414733176dd78d475eb75f7758b75e474ae76067369736275bc74a27493760b748b74837599765177776f5b769a763b767775496a207849774b74e5750776bb750b74cf76b07513739d77f16c6c76266bd375156eb4721d773d764477c176106e8b773e76ff7567739075087229775f770474d476dd75c17781751e),
    .CHANNEL_THRESHOLDS(1024'h020f020a020b01fe0207020a02160210020e0206020201fb0212020e0204020302110214020302070206020e0213021501fb02140201020e02150209020e020c020c0204020d02110208020e02120212020102110203021202130207020b020b01f90213020e020e020d021301fd020b02140211021202080215020701f401fa),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/23_project2.mem"),
    .CHANNEL_BETAS(512'h77757c8077ef7727787077887c5076987bd77c057c8275097c247bf07bcf7a7b77527cc276eb7bd376bd775d7a2e7b617cb577647692772e7cc5768779917af2),
    .CHANNEL_THRESHOLDS(512'h020c021f020b022101e40204021b02050220021c021f01f40222021b0224021d01f902210216020b01e80200021e020c02230208021202080220020d01f70212),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
    .PACKED_WEIGHT_COUNT(1),
    .KERNEL_WEIGHT_FILE("weights/24_final_fuse_standard.mem"),
    .CHANNEL_BETAS(256'h2bf52e5c70b46f6057d43909620134dd72aa7a8557f7294f59d471266f5a3f9a),
    .CHANNEL_THRESHOLDS(256'h0240023a01e701ef01ed0220015b021b0240023301f1025b020e0125012801f6),
    .ENABLE_INHIBITION(0),
    .ENABLE_ADAPTATION(0),
    .USE_STATE_SRAM_MACRO(USE_ACTOR_STATE_SRAM_MACRO),
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
  assign actor_trace_valid_o[0] = n_detail_stem_valid;
  assign actor_trace_ready_o[0] = n_detail_stem_ready;
  assign actor_trace_completion_o[0] = n_detail_stem_completion;
  assign actor_trace_payload_o[0*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_detail_stem_payload;
  assign actor_trace_bin_tag_o[0*TAG_WIDTH +: TAG_WIDTH] = n_detail_stem_bin_tag;
  assign actor_trace_valid_o[1] = n_detail1_standard_valid;
  assign actor_trace_ready_o[1] = n_detail1_standard_ready;
  assign actor_trace_completion_o[1] = n_detail1_standard_completion;
  assign actor_trace_payload_o[1*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_detail1_standard_payload;
  assign actor_trace_bin_tag_o[1*TAG_WIDTH +: TAG_WIDTH] = n_detail1_standard_bin_tag;
  assign actor_trace_valid_o[2] = n_stem_valid;
  assign actor_trace_ready_o[2] = n_stem_ready;
  assign actor_trace_completion_o[2] = n_stem_completion;
  assign actor_trace_payload_o[2*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_stem_payload;
  assign actor_trace_bin_tag_o[2*TAG_WIDTH +: TAG_WIDTH] = n_stem_bin_tag;
  assign actor_trace_valid_o[3] = n_enc1_standard_valid;
  assign actor_trace_ready_o[3] = n_enc1_standard_ready;
  assign actor_trace_completion_o[3] = n_enc1_standard_completion;
  assign actor_trace_payload_o[3*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc1_standard_payload;
  assign actor_trace_bin_tag_o[3*TAG_WIDTH +: TAG_WIDTH] = n_enc1_standard_bin_tag;
  assign actor_trace_valid_o[4] = n_enc1_extra_depthwise_valid;
  assign actor_trace_ready_o[4] = n_enc1_extra_depthwise_ready;
  assign actor_trace_completion_o[4] = n_enc1_extra_depthwise_completion;
  assign actor_trace_payload_o[4*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc1_extra_depthwise_payload;
  assign actor_trace_bin_tag_o[4*TAG_WIDTH +: TAG_WIDTH] = n_enc1_extra_depthwise_bin_tag;
  assign actor_trace_valid_o[5] = n_enc1_extra_pointwise_valid;
  assign actor_trace_ready_o[5] = n_enc1_extra_pointwise_ready;
  assign actor_trace_completion_o[5] = n_enc1_extra_pointwise_completion;
  assign actor_trace_payload_o[5*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc1_extra_pointwise_payload;
  assign actor_trace_bin_tag_o[5*TAG_WIDTH +: TAG_WIDTH] = n_enc1_extra_pointwise_bin_tag;
  assign actor_trace_valid_o[6] = n_down2_standard_valid;
  assign actor_trace_ready_o[6] = n_down2_standard_ready;
  assign actor_trace_completion_o[6] = n_down2_standard_completion;
  assign actor_trace_payload_o[6*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_down2_standard_payload;
  assign actor_trace_bin_tag_o[6*TAG_WIDTH +: TAG_WIDTH] = n_down2_standard_bin_tag;
  assign actor_trace_valid_o[7] = n_enc2_depthwise_valid;
  assign actor_trace_ready_o[7] = n_enc2_depthwise_ready;
  assign actor_trace_completion_o[7] = n_enc2_depthwise_completion;
  assign actor_trace_payload_o[7*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc2_depthwise_payload;
  assign actor_trace_bin_tag_o[7*TAG_WIDTH +: TAG_WIDTH] = n_enc2_depthwise_bin_tag;
  assign actor_trace_valid_o[8] = n_enc2_pointwise_valid;
  assign actor_trace_ready_o[8] = n_enc2_pointwise_ready;
  assign actor_trace_completion_o[8] = n_enc2_pointwise_completion;
  assign actor_trace_payload_o[8*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc2_pointwise_payload;
  assign actor_trace_bin_tag_o[8*TAG_WIDTH +: TAG_WIDTH] = n_enc2_pointwise_bin_tag;
  assign actor_trace_valid_o[9] = n_enc2_extra_depthwise_valid;
  assign actor_trace_ready_o[9] = n_enc2_extra_depthwise_ready;
  assign actor_trace_completion_o[9] = n_enc2_extra_depthwise_completion;
  assign actor_trace_payload_o[9*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc2_extra_depthwise_payload;
  assign actor_trace_bin_tag_o[9*TAG_WIDTH +: TAG_WIDTH] = n_enc2_extra_depthwise_bin_tag;
  assign actor_trace_valid_o[10] = n_enc2_extra_pointwise_valid;
  assign actor_trace_ready_o[10] = n_enc2_extra_pointwise_ready;
  assign actor_trace_completion_o[10] = n_enc2_extra_pointwise_completion;
  assign actor_trace_payload_o[10*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc2_extra_pointwise_payload;
  assign actor_trace_bin_tag_o[10*TAG_WIDTH +: TAG_WIDTH] = n_enc2_extra_pointwise_bin_tag;
  assign actor_trace_valid_o[11] = n_down3_depthwise_valid;
  assign actor_trace_ready_o[11] = n_down3_depthwise_ready;
  assign actor_trace_completion_o[11] = n_down3_depthwise_completion;
  assign actor_trace_payload_o[11*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_down3_depthwise_payload;
  assign actor_trace_bin_tag_o[11*TAG_WIDTH +: TAG_WIDTH] = n_down3_depthwise_bin_tag;
  assign actor_trace_valid_o[12] = n_down3_pointwise_valid;
  assign actor_trace_ready_o[12] = n_down3_pointwise_ready;
  assign actor_trace_completion_o[12] = n_down3_pointwise_completion;
  assign actor_trace_payload_o[12*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_down3_pointwise_payload;
  assign actor_trace_bin_tag_o[12*TAG_WIDTH +: TAG_WIDTH] = n_down3_pointwise_bin_tag;
  assign actor_trace_valid_o[13] = n_enc3_depthwise_valid;
  assign actor_trace_ready_o[13] = n_enc3_depthwise_ready;
  assign actor_trace_completion_o[13] = n_enc3_depthwise_completion;
  assign actor_trace_payload_o[13*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc3_depthwise_payload;
  assign actor_trace_bin_tag_o[13*TAG_WIDTH +: TAG_WIDTH] = n_enc3_depthwise_bin_tag;
  assign actor_trace_valid_o[14] = n_enc3_pointwise_valid;
  assign actor_trace_ready_o[14] = n_enc3_pointwise_ready;
  assign actor_trace_completion_o[14] = n_enc3_pointwise_completion;
  assign actor_trace_payload_o[14*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc3_pointwise_payload;
  assign actor_trace_bin_tag_o[14*TAG_WIDTH +: TAG_WIDTH] = n_enc3_pointwise_bin_tag;
  assign actor_trace_valid_o[15] = n_enc3_extra_depthwise_valid;
  assign actor_trace_ready_o[15] = n_enc3_extra_depthwise_ready;
  assign actor_trace_completion_o[15] = n_enc3_extra_depthwise_completion;
  assign actor_trace_payload_o[15*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc3_extra_depthwise_payload;
  assign actor_trace_bin_tag_o[15*TAG_WIDTH +: TAG_WIDTH] = n_enc3_extra_depthwise_bin_tag;
  assign actor_trace_valid_o[16] = n_enc3_extra_pointwise_valid;
  assign actor_trace_ready_o[16] = n_enc3_extra_pointwise_ready;
  assign actor_trace_completion_o[16] = n_enc3_extra_pointwise_completion;
  assign actor_trace_payload_o[16*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_enc3_extra_pointwise_payload;
  assign actor_trace_bin_tag_o[16*TAG_WIDTH +: TAG_WIDTH] = n_enc3_extra_pointwise_bin_tag;
  assign actor_trace_valid_o[17] = n_context1_depthwise_valid;
  assign actor_trace_ready_o[17] = n_context1_depthwise_ready;
  assign actor_trace_completion_o[17] = n_context1_depthwise_completion;
  assign actor_trace_payload_o[17*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_context1_depthwise_payload;
  assign actor_trace_bin_tag_o[17*TAG_WIDTH +: TAG_WIDTH] = n_context1_depthwise_bin_tag;
  assign actor_trace_valid_o[18] = n_context1_pointwise_valid;
  assign actor_trace_ready_o[18] = n_context1_pointwise_ready;
  assign actor_trace_completion_o[18] = n_context1_pointwise_completion;
  assign actor_trace_payload_o[18*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_context1_pointwise_payload;
  assign actor_trace_bin_tag_o[18*TAG_WIDTH +: TAG_WIDTH] = n_context1_pointwise_bin_tag;
  assign actor_trace_valid_o[19] = n_context2_depthwise_valid;
  assign actor_trace_ready_o[19] = n_context2_depthwise_ready;
  assign actor_trace_completion_o[19] = n_context2_depthwise_completion;
  assign actor_trace_payload_o[19*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_context2_depthwise_payload;
  assign actor_trace_bin_tag_o[19*TAG_WIDTH +: TAG_WIDTH] = n_context2_depthwise_bin_tag;
  assign actor_trace_valid_o[20] = n_context2_pointwise_valid;
  assign actor_trace_ready_o[20] = n_context2_pointwise_ready;
  assign actor_trace_completion_o[20] = n_context2_pointwise_completion;
  assign actor_trace_payload_o[20*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_context2_pointwise_payload;
  assign actor_trace_bin_tag_o[20*TAG_WIDTH +: TAG_WIDTH] = n_context2_pointwise_bin_tag;
  assign actor_trace_valid_o[21] = n_project3_valid;
  assign actor_trace_ready_o[21] = n_project3_ready;
  assign actor_trace_completion_o[21] = n_project3_completion;
  assign actor_trace_payload_o[21*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_project3_payload;
  assign actor_trace_bin_tag_o[21*TAG_WIDTH +: TAG_WIDTH] = n_project3_bin_tag;
  assign actor_trace_valid_o[22] = n_decoder2_fuse_valid;
  assign actor_trace_ready_o[22] = n_decoder2_fuse_ready;
  assign actor_trace_completion_o[22] = n_decoder2_fuse_completion;
  assign actor_trace_payload_o[22*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_decoder2_fuse_payload;
  assign actor_trace_bin_tag_o[22*TAG_WIDTH +: TAG_WIDTH] = n_decoder2_fuse_bin_tag;
  assign actor_trace_valid_o[23] = n_project2_valid;
  assign actor_trace_ready_o[23] = n_project2_ready;
  assign actor_trace_completion_o[23] = n_project2_completion;
  assign actor_trace_payload_o[23*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_project2_payload;
  assign actor_trace_bin_tag_o[23*TAG_WIDTH +: TAG_WIDTH] = n_project2_bin_tag;
  assign actor_trace_valid_o[24] = n_final_fuse_standard_valid;
  assign actor_trace_ready_o[24] = n_final_fuse_standard_ready;
  assign actor_trace_completion_o[24] = n_final_fuse_standard_completion;
  assign actor_trace_payload_o[24*PAYLOAD_WIDTH +: PAYLOAD_WIDTH] = n_final_fuse_standard_payload;
  assign actor_trace_bin_tag_o[24*TAG_WIDTH +: TAG_WIDTH] = n_final_fuse_standard_bin_tag;
  logic error_tag_detail1_residual_or;
  logic error_union_detail1_residual_or;
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 2252800 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(640), .OUTPUT_HEIGHT(440), .CHANNEL_COUNT(8), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_detail1_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 2252800 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(320), .OUTPUT_HEIGHT(220), .CHANNEL_COUNT(32), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc1_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 2252800 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(320), .OUTPUT_HEIGHT(220), .CHANNEL_COUNT(32), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc1_extra_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 1126400 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(160), .OUTPUT_HEIGHT(110), .CHANNEL_COUNT(64), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc2_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 1126400 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(160), .OUTPUT_HEIGHT(110), .CHANNEL_COUNT(64), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc2_extra_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 563200 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(80), .OUTPUT_HEIGHT(55), .CHANNEL_COUNT(128), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc3_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 563200 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(80), .OUTPUT_HEIGHT(55), .CHANNEL_COUNT(128), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_enc3_extra_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 563200 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(80), .OUTPUT_HEIGHT(55), .CHANNEL_COUNT(128), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_context1_residual_or (
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
  binary_event_union2_sram #(.MAX_EVENTS((RESIDUAL_MAX_EVENTS == 0) ? 563200 : RESIDUAL_MAX_EVENTS), .OUTPUT_WIDTH(80), .OUTPUT_HEIGHT(55), .CHANNEL_COUNT(128), .USE_SRAM_MACRO(USE_RESIDUAL_SRAM_MACRO)) union_context2_residual_or (
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
  temporal_class_readout_sram #(
    .INPUT_CHANNELS(16),
    .CLASS_COUNT(6),
    .OUTPUT_WIDTH(640),
    .OUTPUT_HEIGHT(440),
    .PREDICTION_BINS(10),
    .USE_SCORE_SRAM_MACRO(USE_SCORE_SRAM_MACRO),
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
