`timescale 1ns/1ps
// Channel-aware sparse convolution projection front end. One presynaptic spike
// is expanded only to legal output-channel/kernel-tap destinations. Static
// weights use PyTorch Conv2d flattening: [out][in/groups][ky][kx].
module channelized_convolution_scatter #(
  parameter integer COORD_WIDTH = 10,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer INPUT_CHANNELS = 2,
  parameter integer OUTPUT_CHANNELS = 2,
  parameter integer GROUPS = 1,
  parameter integer INPUT_CHANNEL_WIDTH =
    (INPUT_CHANNELS <= 1) ? 1 : $clog2(INPUT_CHANNELS),
  parameter integer OUTPUT_CHANNEL_WIDTH =
    (OUTPUT_CHANNELS <= 1) ? 1 : $clog2(OUTPUT_CHANNELS),
  parameter integer KERNEL_WIDTH = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 1,
  parameter integer PAD_Y = 1,
  parameter integer OUTPUT_WIDTH = 16,
  parameter integer OUTPUT_HEIGHT = 16,
  parameter integer TAP_COUNT = KERNEL_WIDTH * KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS / GROUPS,
  parameter integer OUTPUTS_PER_GROUP = OUTPUT_CHANNELS / GROUPS,
  parameter integer PROJECTION_COUNT = OUTPUT_CHANNELS * TAP_COUNT,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS * INPUTS_PER_GROUP * TAP_COUNT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic spike_valid,
  output logic spike_ready,
  input  logic [INPUT_CHANNEL_WIDTH-1:0] spike_channel_i,
  input  logic [COORD_WIDTH-1:0] spike_x_i,
  input  logic [COORD_WIDTH-1:0] spike_y_i,

  output logic contribution_valid,
  input  logic contribution_ready,
  output logic [OUTPUT_CHANNEL_WIDTH-1:0] destination_channel_o,
  output logic [COORD_WIDTH-1:0] destination_x_o,
  output logic [COORD_WIDTH-1:0] destination_y_o,
  output logic signed [WEIGHT_WIDTH-1:0] weight_o,
  output logic channel_error_o
);
  logic [PROJECTION_COUNT-1:0] scatter_valid;
  logic [PROJECTION_COUNT*COORD_WIDTH-1:0] scatter_x;
  logic [PROJECTION_COUNT*COORD_WIDTH-1:0] scatter_y;
  logic [PROJECTION_COUNT*WEIGHT_WIDTH-1:0] scatter_weight;
  logic [PROJECTION_COUNT-1:0] pending_valid_reg;
  logic [PROJECTION_COUNT*COORD_WIDTH-1:0] pending_x_reg;
  logic [PROJECTION_COUNT*COORD_WIDTH-1:0] pending_y_reg;
  logic [PROJECTION_COUNT*WEIGHT_WIDTH-1:0] pending_weight_reg;
  integer output_channel;
  integer kernel_x;
  integer kernel_y;
  integer tap_index;
  integer projection_index;
  integer local_input_channel;
  integer input_group;
  integer output_group;
  integer weight_index;
  integer numerator_x;
  integer numerator_y;
  integer destination_x;
  integer destination_y;
  integer selected_projection;
  logic signed [WEIGHT_WIDTH-1:0] selected_weight;

  initial begin
    if (INPUT_CHANNELS % GROUPS != 0 || OUTPUT_CHANNELS % GROUPS != 0)
      $error("channel counts must be divisible by GROUPS");
  end

  always_comb begin
    scatter_valid = '0;
    scatter_x = '0;
    scatter_y = '0;
    scatter_weight = '0;
    destination_x = 0;
    destination_y = 0;
    local_input_channel = $unsigned(spike_channel_i) % INPUTS_PER_GROUP;
    input_group = $unsigned(spike_channel_i) / INPUTS_PER_GROUP;

    for (output_channel = 0; output_channel < OUTPUT_CHANNELS;
         output_channel = output_channel + 1) begin
      output_group = output_channel / OUTPUTS_PER_GROUP;
      for (kernel_y = 0; kernel_y < KERNEL_HEIGHT; kernel_y = kernel_y + 1) begin
        for (kernel_x = 0; kernel_x < KERNEL_WIDTH; kernel_x = kernel_x + 1) begin
          tap_index = kernel_y * KERNEL_WIDTH + kernel_x;
          projection_index = output_channel * TAP_COUNT + tap_index;
          weight_index = (output_channel * INPUTS_PER_GROUP + local_input_channel) *
                         TAP_COUNT + tap_index;
          selected_weight = KERNEL_WEIGHTS[
            weight_index*WEIGHT_WIDTH +: WEIGHT_WIDTH
          ];
          scatter_weight[projection_index*WEIGHT_WIDTH +: WEIGHT_WIDTH] =
            selected_weight;
          numerator_x = $unsigned(spike_x_i) + PAD_X - kernel_x * DILATION_X;
          numerator_y = $unsigned(spike_y_i) + PAD_Y - kernel_y * DILATION_Y;
          if (spike_valid && $unsigned(spike_channel_i) < INPUT_CHANNELS &&
              output_group == input_group && selected_weight != 0 &&
              numerator_x >= 0 && numerator_y >= 0) begin
            destination_x = numerator_x / STRIDE_X;
            destination_y = numerator_y / STRIDE_Y;
            if ((numerator_x % STRIDE_X) == 0 &&
                (numerator_y % STRIDE_Y) == 0 &&
                destination_x < OUTPUT_WIDTH && destination_y < OUTPUT_HEIGHT) begin
              scatter_valid[projection_index] = 1'b1;
              scatter_x[projection_index*COORD_WIDTH +: COORD_WIDTH] =
                destination_x[COORD_WIDTH-1:0];
              scatter_y[projection_index*COORD_WIDTH +: COORD_WIDTH] =
                destination_y[COORD_WIDTH-1:0];
            end
          end
        end
      end
    end
  end

  always_comb begin
    selected_projection = 0;
    for (projection_index = PROJECTION_COUNT - 1; projection_index >= 0;
         projection_index = projection_index - 1)
      if (pending_valid_reg[projection_index])
        selected_projection = projection_index;
    destination_channel_o = selected_projection / TAP_COUNT;
    destination_x_o = pending_x_reg[
      selected_projection*COORD_WIDTH +: COORD_WIDTH
    ];
    destination_y_o = pending_y_reg[
      selected_projection*COORD_WIDTH +: COORD_WIDTH
    ];
    weight_o = pending_weight_reg[
      selected_projection*WEIGHT_WIDTH +: WEIGHT_WIDTH
    ];
  end

  assign spike_ready = (pending_valid_reg == 0);
  assign contribution_valid = (pending_valid_reg != 0);
  assign channel_error_o = spike_valid &&
                           ($unsigned(spike_channel_i) >= INPUT_CHANNELS);

  always_ff @(posedge clk) begin
    if (reset) begin
      pending_valid_reg <= '0;
      pending_x_reg <= '0;
      pending_y_reg <= '0;
      pending_weight_reg <= '0;
    end else if (spike_valid && spike_ready) begin
      pending_valid_reg <= scatter_valid;
      pending_x_reg <= scatter_x;
      pending_y_reg <= scatter_y;
      pending_weight_reg <= scatter_weight;
    end else if (contribution_valid && contribution_ready) begin
      pending_valid_reg[selected_projection] <= 1'b0;
    end
  end
endmodule
