`timescale 1ns/1ps
// Group-parallel event addressing for analog convolution weights.
// One input event selects one spatial kernel tap per cycle, while every output
// channel in the input's convolution group receives its own analog weight
// address concurrently. Numerical weights are never represented digitally.
module gf180_analog_weight_event_scatter_parallel #(
  parameter integer COORD_WIDTH = 10,
  parameter integer CHANNEL_WIDTH = 8,
  parameter integer WEIGHT_ADDR_WIDTH = 20,
  parameter integer BIN_WIDTH = 24,
  parameter integer INPUT_CHANNELS = 128,
  parameter integer OUTPUT_CHANNELS = 128,
  parameter integer GROUPS = 1,
  parameter integer KERNEL_WIDTH = 1,
  parameter integer KERNEL_HEIGHT = 1,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 0,
  parameter integer PAD_Y = 0,
  parameter integer OUTPUT_WIDTH = 80,
  parameter integer OUTPUT_HEIGHT = 55,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS / GROUPS,
  parameter integer OUTPUTS_PER_GROUP = OUTPUT_CHANNELS / GROUPS,
  parameter integer TAP_COUNT = KERNEL_WIDTH * KERNEL_HEIGHT,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS * INPUTS_PER_GROUP * TAP_COUNT,
  parameter integer NUM_LANES = OUTPUTS_PER_GROUP,
  parameter integer TAP_WIDTH = (TAP_COUNT <= 1) ? 1 : $clog2(TAP_COUNT)
) (
  input logic clk,
  input logic reset,
  input logic event_valid_i,
  output logic event_ready_o,
  input logic [CHANNEL_WIDTH-1:0] input_channel_i,
  input logic [COORD_WIDTH-1:0] input_x_i,
  input logic [COORD_WIDTH-1:0] input_y_i,
  input logic [1:0] multiplicity_i,
  input logic [BIN_WIDTH-1:0] bin_tag_i,
  output logic contribution_valid_o,
  input logic contribution_ready_i,
  output logic [CHANNEL_WIDTH-1:0] output_channel_base_o,
  output logic [CHANNEL_WIDTH-1:0] input_channel_local_o,
  output logic [TAP_WIDTH-1:0] tap_index_o,
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
  logic [TAP_WIDTH-1:0] tap_reg;
  integer input_group;
  integer local_input_channel;
  integer kernel_x, kernel_y;
  integer numerator_x, numerator_y;
  integer destination_x, destination_y;
  integer output_channel, weight_index;
  integer lane;
  logic spatial_candidate_legal;

  always_comb begin
    input_group = $unsigned(input_channel_reg) / INPUTS_PER_GROUP;
    local_input_channel = $unsigned(input_channel_reg) % INPUTS_PER_GROUP;
    kernel_y = $unsigned(tap_reg) / KERNEL_WIDTH;
    kernel_x = $unsigned(tap_reg) % KERNEL_WIDTH;
    numerator_x = $unsigned(input_x_reg) + PAD_X - kernel_x * DILATION_X;
    numerator_y = $unsigned(input_y_reg) + PAD_Y - kernel_y * DILATION_Y;
    destination_x = 0;
    destination_y = 0;
    spatial_candidate_legal = active_reg &&
      ($unsigned(input_channel_reg) < INPUT_CHANNELS) &&
      numerator_x >= 0 && numerator_y >= 0 &&
      (numerator_x % STRIDE_X) == 0 &&
      (numerator_y % STRIDE_Y) == 0;
    if (spatial_candidate_legal) begin
      destination_x = numerator_x / STRIDE_X;
      destination_y = numerator_y / STRIDE_Y;
      spatial_candidate_legal = (destination_x < OUTPUT_WIDTH) &&
                                (destination_y < OUTPUT_HEIGHT);
    end

    event_ready_o = !active_reg;
    contribution_valid_o = spatial_candidate_legal;
    output_channel_base_o = input_group * OUTPUTS_PER_GROUP;
    output_x_o = destination_x[COORD_WIDTH-1:0];
    output_y_o = destination_y[COORD_WIDTH-1:0];
    multiplicity_o = multiplicity_reg;
    bin_tag_o = bin_tag_reg;
    input_channel_local_o = local_input_channel[CHANNEL_WIDTH-1:0];
    tap_index_o = tap_reg;
    address_overflow_o = 1'b0;
    for (lane = 0; lane < NUM_LANES; lane = lane + 1) begin
      output_channel = input_group * OUTPUTS_PER_GROUP + lane;
      weight_index = (output_channel * INPUTS_PER_GROUP +
                      local_input_channel) * TAP_COUNT + $unsigned(tap_reg);
      if (spatial_candidate_legal) begin
        if (weight_index < 0 || weight_index >= WEIGHT_COUNT ||
            weight_index >= (1 << WEIGHT_ADDR_WIDTH))
          address_overflow_o = 1'b1;
      end
    end
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
      tap_reg <= '0;
    end else begin
      if (event_valid_i && event_ready_o) begin
        input_channel_reg <= input_channel_i;
        input_x_reg <= input_x_i;
        input_y_reg <= input_y_i;
        multiplicity_reg <= multiplicity_i;
        bin_tag_reg <= bin_tag_i;
        tap_reg <= '0;
        active_reg <= (multiplicity_i != 0) &&
                      (input_channel_i < INPUT_CHANNELS);
      end else if (active_reg &&
                   (!spatial_candidate_legal || contribution_ready_i)) begin
        if (tap_reg == TAP_COUNT - 1)
          active_reg <= 1'b0;
        else
          tap_reg <= tap_reg + 1'b1;
      end
    end
  end

  initial begin
    if (GROUPS <= 0 || INPUT_CHANNELS % GROUPS != 0 ||
        OUTPUT_CHANNELS % GROUPS != 0)
      $error("channel counts must be divisible by positive GROUPS");
    if (STRIDE_X <= 0 || STRIDE_Y <= 0 || DILATION_X <= 0 || DILATION_Y <= 0)
      $error("stride and dilation values must be positive");
    if (NUM_LANES != OUTPUTS_PER_GROUP)
      $error("NUM_LANES must cover every output channel in one group");
    if (WEIGHT_COUNT > (1 << WEIGHT_ADDR_WIDTH))
      $error("WEIGHT_ADDR_WIDTH cannot address the analog weight array");
    if (INPUTS_PER_GROUP <= 0 || OUTPUTS_PER_GROUP <= 0)
      $error("grouped convolution dimensions are invalid");
  end
endmodule
