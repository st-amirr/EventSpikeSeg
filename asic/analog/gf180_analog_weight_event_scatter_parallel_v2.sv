`timescale 1ns/1ps
// Bounded fixed-kernel address generator. No runtime kernel division, no
// replicated per-output arithmetic: all connected output channels share a tap.
module gf180_analog_weight_event_scatter_parallel_v2 #(
  parameter integer COORD_WIDTH=10, CHANNEL_WIDTH=8, WEIGHT_ADDR_WIDTH=20, BIN_WIDTH=24,
  parameter integer INPUT_CHANNELS=128, OUTPUT_CHANNELS=128, GROUPS=1,
  parameter integer KERNEL_WIDTH=1, KERNEL_HEIGHT=1,
  parameter integer STRIDE_X=1, STRIDE_Y=1, DILATION_X=1, DILATION_Y=1,
  parameter integer PAD_X=0, PAD_Y=0, OUTPUT_WIDTH=80, OUTPUT_HEIGHT=55,
  parameter integer INPUTS_PER_GROUP=INPUT_CHANNELS/GROUPS,
  parameter integer OUTPUTS_PER_GROUP=OUTPUT_CHANNELS/GROUPS,
  parameter integer TAP_COUNT=KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer NUM_LANES=OUTPUTS_PER_GROUP,
  parameter integer TAP_WIDTH=(TAP_COUNT<=1)?1:$clog2(TAP_COUNT)
) (
  input wire clk,reset,event_valid_i,
  output wire event_ready_o,
  input wire [CHANNEL_WIDTH-1:0] input_channel_i,
  input wire [COORD_WIDTH-1:0] input_x_i,input_y_i,
  input wire [1:0] multiplicity_i,
  input wire [BIN_WIDTH-1:0] bin_tag_i,
  output wire contribution_valid_o,
  input wire contribution_ready_i,
  output wire [CHANNEL_WIDTH-1:0] output_channel_base_o,input_channel_local_o,
  output wire [TAP_WIDTH-1:0] tap_index_o,
  output reg [COORD_WIDTH-1:0] output_x_o,output_y_o,
  output wire [1:0] multiplicity_o,
  output wire [BIN_WIDTH-1:0] bin_tag_o,
  output wire address_overflow_o,channel_error_o
);
  reg active;
  reg [CHANNEL_WIDTH-1:0] channel;
  reg [COORD_WIDTH-1:0] x,y;
  reg [1:0] multiplicity;
  reg [BIN_WIDTH-1:0] tag;
  reg [TAP_WIDTH-1:0] tap;
  wire [TAP_COUNT-1:0] legal;
  wire [COORD_WIDTH-1:0] tap_x [0:TAP_COUNT-1];
  wire [COORD_WIDTH-1:0] tap_y [0:TAP_COUNT-1];
  genvar t;
  generate for(t=0;t<TAP_COUNT;t=t+1) begin: fixed_tap
    // Twelve bits cover actual 10-bit coordinates and fixed 1/3/5 kernels.
    wire signed [11:0] nx=$signed({2'b0,x})+PAD_X-(t%KERNEL_WIDTH)*DILATION_X;
    wire signed [11:0] ny=$signed({2'b0,y})+PAD_Y-(t/KERNEL_WIDTH)*DILATION_Y;
    wire signed [11:0] dx=nx >>> $clog2(STRIDE_X);
    wire signed [11:0] dy=ny >>> $clog2(STRIDE_Y);
    assign legal[t]=nx>=0 && ny>=0 &&
       ((nx & (STRIDE_X-1))==0) && ((ny & (STRIDE_Y-1))==0) &&
       dx<OUTPUT_WIDTH && dy<OUTPUT_HEIGHT;
    assign tap_x[t]=dx[COORD_WIDTH-1:0];
    assign tap_y[t]=dy[COORD_WIDTH-1:0];
  end endgenerate
  integer k;
  reg selected_legal;
  always @* begin
    selected_legal=0;output_x_o=0;output_y_o=0;
    for(k=0;k<TAP_COUNT;k=k+1) if(tap==k) begin
      selected_legal=legal[k];
      if(legal[k]) begin output_x_o=tap_x[k];output_y_o=tap_y[k];end
    end
  end
  generate if(GROUPS==1) begin
    assign output_channel_base_o=0;
    assign input_channel_local_o=channel;
  end else if(GROUPS==INPUT_CHANNELS) begin
    assign output_channel_base_o=channel*OUTPUTS_PER_GROUP;
    assign input_channel_local_o=0;
  end else begin
    assign output_channel_base_o=(channel/INPUTS_PER_GROUP)*OUTPUTS_PER_GROUP;
    assign input_channel_local_o=channel%INPUTS_PER_GROUP;
  end endgenerate
  assign event_ready_o=!active;
  assign contribution_valid_o=active && selected_legal;
  assign tap_index_o=tap;
  assign multiplicity_o=multiplicity;
  assign bin_tag_o=tag;
  // For valid channels/taps every OIHW lane is in the statically checked array.
  assign address_overflow_o=0;
  assign channel_error_o=event_valid_i && input_channel_i>=INPUT_CHANNELS;
  always @(posedge clk) begin
    if(reset) begin active<=0;channel<=0;x<=0;y<=0;multiplicity<=0;tag<=0;tap<=0;end
    else if(event_valid_i && event_ready_o) begin
      channel<=input_channel_i;x<=input_x_i;y<=input_y_i;
      multiplicity<=multiplicity_i;tag<=bin_tag_i;tap<=0;
      active<=multiplicity_i!=0 && input_channel_i<INPUT_CHANNELS;
    end else if(active && (!selected_legal || contribution_ready_i)) begin
      if(tap==TAP_COUNT-1) active<=0;
      else tap<=tap+1'b1;
    end
  end
  initial begin
    if(COORD_WIDTH!=10 || (STRIDE_X!=1 && STRIDE_X!=2) || (STRIDE_Y!=1 && STRIDE_Y!=2))
      $error("fixed-kernel generator requires 10-bit coordinates and stride1/2");
    if(GROUPS<=0 || INPUT_CHANNELS%GROUPS!=0 || OUTPUT_CHANNELS%GROUPS!=0 || NUM_LANES!=OUTPUTS_PER_GROUP)
      $error("invalid convolution groups");
    if(OUTPUT_CHANNELS*INPUTS_PER_GROUP*TAP_COUNT>(1<<WEIGHT_ADDR_WIDTH))
      $error("weight address width too small");
    if(PAD_X>16 || PAD_Y>16 || KERNEL_WIDTH*DILATION_X>32 || KERNEL_HEIGHT*DILATION_Y>32)
      $error("fixed kernel exceeds bounded coordinate arithmetic");
  end
endmodule
