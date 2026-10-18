`timescale 1ns/1ps
// Event-address fanout for an analog synapse array.
//
// This block performs only categorical work: it maps one presynaptic event to
// the legal output-neuron coordinates and emits the address of each trained
// analog weight. It never stores, quantizes, compares, or outputs a weight value.
// The downstream analog pulse/charge circuit reads the weight at weight_address_o
// and applies the original floating-point coefficient's calibrated analog value.
module gf180_analog_weight_event_scatter #(
  parameter integer COORD_WIDTH = 10,
  parameter integer CHANNEL_WIDTH = 8,
  parameter integer WEIGHT_ADDR_WIDTH = 20,
  parameter integer BIN_WIDTH = 24,
  parameter integer INPUT_CHANNELS = 2,
  parameter integer OUTPUT_CHANNELS = 2,
  parameter integer GROUPS = 1,
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
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS / GROUPS,
  parameter integer OUTPUTS_PER_GROUP = OUTPUT_CHANNELS / GROUPS,
  parameter integer TAP_COUNT = KERNEL_WIDTH * KERNEL_HEIGHT,
  // A presynaptic input channel can connect only to output channels in its
  // group. Enumerate that group alone instead of scanning and discarding the
  // other groups (especially important for depthwise convolution).
  parameter integer PROJECTION_COUNT = OUTPUTS_PER_GROUP * TAP_COUNT,
  parameter integer WEIGHT_COUNT =
    OUTPUT_CHANNELS * INPUTS_PER_GROUP * TAP_COUNT,
  parameter integer PROJECTION_WIDTH = (PROJECTION_COUNT <= 1) ? 1 : $clog2(PROJECTION_COUNT),
  parameter integer WEIGHT_COUNT_WIDTH = (WEIGHT_COUNT <= 1) ? 1 : $clog2(WEIGHT_COUNT)
) (
  input  logic clk,
  input  logic reset,

  input  logic event_valid_i,
  output logic event_ready_o,
  input  logic [CHANNEL_WIDTH-1:0] input_channel_i,
  input  logic [COORD_WIDTH-1:0] input_x_i,
  input  logic [COORD_WIDTH-1:0] input_y_i,
  input  logic [1:0] multiplicity_i,
  input  logic [BIN_WIDTH-1:0] bin_tag_i,

  output logic contribution_valid_o,
  input  logic contribution_ready_i,
  output logic [WEIGHT_ADDR_WIDTH-1:0] weight_address_o,
  output logic [CHANNEL_WIDTH-1:0] output_channel_o,
  output logic [COORD_WIDTH-1:0] output_x_o,
  output logic [COORD_WIDTH-1:0] output_y_o,
  output logic [1:0] multiplicity_o,
  output logic [BIN_WIDTH-1:0] bin_tag_o,
  output logic address_overflow_o,
  output logic channel_error_o
);
  logic active_reg;
  logic [CHANNEL_WIDTH-1:0] input_channel_reg;
  logic [COORD_WIDTH-1:0] input_x_reg, input_y_reg;
  logic [1:0] multiplicity_reg;
  logic [BIN_WIDTH-1:0] bin_tag_reg;
  logic [PROJECTION_WIDTH-1:0] projection_reg;

  integer output_channel;
  integer local_output_channel;
  integer kernel_x;
  integer kernel_y;
  integer tap_index;
  integer local_input_channel;
  integer input_group;
  integer output_group;
  integer numerator_x;
  integer numerator_y;
  integer destination_x;
  integer destination_y;
  integer weight_index;
  logic candidate_legal;
  logic [WEIGHT_COUNT_WIDTH-1:0] candidate_weight_index;

  always_comb begin
    local_output_channel = $unsigned(projection_reg) / TAP_COUNT;
    input_group = $unsigned(input_channel_reg) / INPUTS_PER_GROUP;
    output_channel = input_group * OUTPUTS_PER_GROUP + local_output_channel;
    tap_index = $unsigned(projection_reg) % TAP_COUNT;
    kernel_y = tap_index / KERNEL_WIDTH;
    kernel_x = tap_index % KERNEL_WIDTH;
    local_input_channel = $unsigned(input_channel_reg) % INPUTS_PER_GROUP;
    output_group = output_channel / OUTPUTS_PER_GROUP;

    numerator_x = $unsigned(input_x_reg) + PAD_X - kernel_x * DILATION_X;
    numerator_y = $unsigned(input_y_reg) + PAD_Y - kernel_y * DILATION_Y;
    destination_x = 0;
    destination_y = 0;
    weight_index =
      (output_channel * INPUTS_PER_GROUP + local_input_channel) * TAP_COUNT +
      tap_index;
    candidate_weight_index = weight_index[WEIGHT_COUNT_WIDTH-1:0];

    candidate_legal = active_reg &&
      ($unsigned(input_channel_reg) < INPUT_CHANNELS) &&
      (output_channel < OUTPUT_CHANNELS) &&
      (input_group == output_group) &&
      (numerator_x >= 0) && (numerator_y >= 0) &&
      ((numerator_x % STRIDE_X) == 0) &&
      ((numerator_y % STRIDE_Y) == 0);
    if (candidate_legal) begin
      destination_x = numerator_x / STRIDE_X;
      destination_y = numerator_y / STRIDE_Y;
      candidate_legal = (destination_x < OUTPUT_WIDTH) &&
                        (destination_y < OUTPUT_HEIGHT);
    end

    event_ready_o = !active_reg;
    contribution_valid_o = candidate_legal;
    weight_address_o = candidate_weight_index;
    output_channel_o = output_channel[CHANNEL_WIDTH-1:0];
    output_x_o = destination_x[COORD_WIDTH-1:0];
    output_y_o = destination_y[COORD_WIDTH-1:0];
    multiplicity_o = multiplicity_reg;
    bin_tag_o = bin_tag_reg;
    address_overflow_o = candidate_legal &&
      ((weight_index < 0) || (weight_index >= WEIGHT_COUNT) ||
       (weight_index >= (1 << WEIGHT_ADDR_WIDTH)));
    channel_error_o = event_valid_i &&
      ($unsigned(input_channel_i) >= INPUT_CHANNELS);
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      active_reg <= 1'b0;
      input_channel_reg <= '0;
      input_x_reg <= '0;
      input_y_reg <= '0;
      multiplicity_reg <= '0;
      bin_tag_reg <= '0;
      projection_reg <= '0;
    end else begin
      if (event_valid_i && event_ready_o) begin
        input_channel_reg <= input_channel_i;
        input_x_reg <= input_x_i;
        input_y_reg <= input_y_i;
        multiplicity_reg <= multiplicity_i;
        bin_tag_reg <= bin_tag_i;
        projection_reg <= '0;
        active_reg <= (multiplicity_i != 0) &&
                      (input_channel_i < INPUT_CHANNELS);
      end else if (active_reg) begin
        if (!candidate_legal || contribution_ready_i) begin
          if (projection_reg == PROJECTION_COUNT - 1)
            active_reg <= 1'b0;
          else
            projection_reg <= projection_reg + 1'b1;
        end
      end
    end
  end

  initial begin
    if (GROUPS <= 0 || INPUT_CHANNELS % GROUPS != 0 ||
        OUTPUT_CHANNELS % GROUPS != 0)
      $error("channel counts must be divisible by positive GROUPS");
    if (STRIDE_X <= 0 || STRIDE_Y <= 0 || DILATION_X <= 0 || DILATION_Y <= 0)
      $error("stride and dilation values must be positive");
    if (WEIGHT_COUNT > (1 << WEIGHT_ADDR_WIDTH))
      $error("WEIGHT_ADDR_WIDTH cannot address the analog weight array");
    if (INPUTS_PER_GROUP <= 0 || OUTPUTS_PER_GROUP <= 0)
      $error("grouped convolution dimensions are invalid");
  end
endmodule
