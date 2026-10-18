`timescale 1ns/1ps
// One packet is one presynaptic event. Repeated addresses are NOT collapsed:
// raw-event counts and project2+x1 multiplicity arrive as repeated packets.
// Only categorical addresses are generated. A group request requires every
// connected output channel's signed analog contribution before settled-done.
module gf180_analog_actor_ingress_v1 #(
  parameter integer INPUT_CHANNELS=2, OUTPUT_CHANNELS=4, GROUPS=1,
  parameter integer INPUT_WIDTH=4, INPUT_HEIGHT=4,
  parameter integer OUTPUT_WIDTH=4, OUTPUT_HEIGHT=4,
  parameter integer KERNEL_WIDTH=3, KERNEL_HEIGHT=3,
  parameter integer STRIDE_X=1, STRIDE_Y=1, DILATION_X=1, DILATION_Y=1,
  parameter integer PAD_X=1, PAD_Y=1,
  parameter integer INPUTS_PER_GROUP=INPUT_CHANNELS/GROUPS,
  parameter integer OUTPUTS_PER_GROUP=OUTPUT_CHANNELS/GROUPS,
  parameter integer TAP_COUNT=KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer TAP_WIDTH=(TAP_COUNT<=1)?1:$clog2(TAP_COUNT)
) (
  input wire clk, reset, accumulate_enable_i,
  input wire graph_valid_i,
  output wire graph_ready_o,
  input wire [31:0] graph_payload_i,
  input wire graph_completion_i,
  input wire [23:0] graph_bin_tag_i,
  output wire group_valid_o,
  input wire group_ready_i,
  input wire group_settled_done_i,
  output wire [19:0] weight_address_base_o,
  output wire [19:0] weight_lane_stride_o,
  output wire [7:0] output_channel_base_o,
  output wire [7:0] output_lane_count_o,
  output wire [9:0] output_x_o, output_y_o,
  output wire [23:0] contribution_bin_tag_o,
  output wire bin_complete_valid_o,
  input wire bin_complete_ready_i,
  output wire [23:0] bin_complete_tag_o,
  output wire busy_o,
  output reg tag_error_o, input_error_o
);
  reg inflight, ack_armed, pending_completion, tag_seen;
  reg [23:0] tag;
  wire scatter_ready, contribution_valid, overflow, channel_error;
  wire [7:0] local_input_channel;
  wire [TAP_WIDTH-1:0] tap;
  wire [1:0] unused_multiplicity;
  wire fault=tag_error_o||input_error_o;
  wire tag_bad=tag_seen && (graph_bin_tag_i!=tag);
  wire range_bad=!graph_completion_i &&
      (graph_payload_i[25:19]>=INPUT_CHANNELS || graph_payload_i[9:0]>=INPUT_WIDTH || graph_payload_i[18:10]>=INPUT_HEIGHT);
  assign graph_ready_o=accumulate_enable_i && !fault && !pending_completion && !inflight && scatter_ready;
  wire event_valid=graph_valid_i && graph_ready_o && !graph_completion_i && !tag_bad && !range_bad;
  assign group_valid_o=contribution_valid && !inflight && !fault && accumulate_enable_i;
  assign weight_address_base_o=(output_channel_base_o*INPUTS_PER_GROUP+local_input_channel)*TAP_COUNT+tap;
  assign weight_lane_stride_o=INPUTS_PER_GROUP*TAP_COUNT;
  assign output_lane_count_o=OUTPUTS_PER_GROUP;
  assign bin_complete_valid_o=pending_completion && !fault;
  assign bin_complete_tag_o=tag;
  assign busy_o=tag_seen || inflight || !scatter_ready || pending_completion;
  gf180_analog_weight_event_scatter_parallel #(
    .INPUT_CHANNELS(INPUT_CHANNELS),.OUTPUT_CHANNELS(OUTPUT_CHANNELS),.GROUPS(GROUPS),
    .KERNEL_WIDTH(KERNEL_WIDTH),.KERNEL_HEIGHT(KERNEL_HEIGHT),
    .STRIDE_X(STRIDE_X),.STRIDE_Y(STRIDE_Y),.DILATION_X(DILATION_X),.DILATION_Y(DILATION_Y),
    .PAD_X(PAD_X),.PAD_Y(PAD_Y),.OUTPUT_WIDTH(OUTPUT_WIDTH),.OUTPUT_HEIGHT(OUTPUT_HEIGHT)
  ) scatter (
    .clk(clk),.reset(reset),.event_valid_i(event_valid),.event_ready_o(scatter_ready),
    .input_channel_i({1'b0,graph_payload_i[25:19]}),.input_x_i(graph_payload_i[9:0]),
    .input_y_i({1'b0,graph_payload_i[18:10]}),.multiplicity_i(2'd1),.bin_tag_i(graph_bin_tag_i),
    .contribution_valid_o(contribution_valid),.contribution_ready_i(group_ready_i && !inflight && !fault && accumulate_enable_i),
    .output_channel_base_o(output_channel_base_o),.input_channel_local_o(local_input_channel),
    .tap_index_o(tap),.output_x_o(output_x_o),.output_y_o(output_y_o),
    .multiplicity_o(unused_multiplicity),.bin_tag_o(contribution_bin_tag_o),
    .address_overflow_o(overflow),.channel_error_o(channel_error)
  );
  always @(posedge clk) begin
    if(reset) begin
      inflight<=0;ack_armed<=0;pending_completion<=0;tag_seen<=0;tag<=0;
      tag_error_o<=0;input_error_o<=0;
    end else begin
      if(graph_valid_i && graph_ready_o) begin
        if(tag_bad) tag_error_o<=1;
        if(range_bad) input_error_o<=1;
        if(!tag_bad && !range_bad) begin
          tag_seen<=1;tag<=graph_bin_tag_i;
          if(graph_completion_i) pending_completion<=1;
        end
      end
      if(overflow || channel_error) input_error_o<=1;
      if(group_valid_o && group_ready_i) begin
        inflight<=1;ack_armed<=!group_settled_done_i;
      end else if(inflight) begin
        if(!group_settled_done_i) ack_armed<=1;
        if(group_settled_done_i && ack_armed) begin inflight<=0;ack_armed<=0;end
      end
      if(bin_complete_valid_o && bin_complete_ready_i) begin pending_completion<=0;tag_seen<=0;end
    end
  end
endmodule
