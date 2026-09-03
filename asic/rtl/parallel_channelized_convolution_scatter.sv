`timescale 1ns/1ps
// One presynaptic spike expands into up to one contribution per independent
// channel-by-spatial destination bank on each clock. Projection order within
// a bank matches channelized_convolution_scatter.
module parallel_channelized_convolution_scatter #(
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
  parameter integer CHANNEL_LANE_COUNT = 1,
  parameter integer SPATIAL_LANE_COUNT = 4,
  parameter integer LANE_COUNT = CHANNEL_LANE_COUNT*SPATIAL_LANE_COUNT,
  parameter integer TAP_COUNT = KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer OUTPUTS_PER_GROUP = OUTPUT_CHANNELS/GROUPS,
  parameter integer PROJECTION_COUNT = OUTPUT_CHANNELS*TAP_COUNT,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*TAP_COUNT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0
) (
  input logic clk,
  input logic reset,
  input logic spike_valid,
  output logic spike_ready,
  output logic idle_o,
  input logic [INPUT_CHANNEL_WIDTH-1:0] spike_channel_i,
  input logic [COORD_WIDTH-1:0] spike_x_i,
  input logic [COORD_WIDTH-1:0] spike_y_i,
  output logic [LANE_COUNT-1:0] contribution_valid,
  input logic [LANE_COUNT-1:0] contribution_ready,
  output logic [LANE_COUNT*OUTPUT_CHANNEL_WIDTH-1:0] destination_channel_o,
  output logic [LANE_COUNT*COORD_WIDTH-1:0] destination_x_o,
  output logic [LANE_COUNT*COORD_WIDTH-1:0] destination_y_o,
  output logic signed [LANE_COUNT*WEIGHT_WIDTH-1:0] weight_o,
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
  integer selected_projection [0:LANE_COUNT-1];
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
  integer candidate_channel;
  integer candidate_x;
  integer candidate_y;
  integer candidate_spatial;
  integer candidate_lane;
  integer lane_index;
  logic [LANE_COUNT-1:0] lane_has_pending;
  logic [PROJECTION_COUNT-1:0] accepted_projection;
  logic pending_drains;
  logic signed [WEIGHT_WIDTH-1:0] selected_weight;

  initial begin
    if (INPUT_CHANNELS % GROUPS != 0 || OUTPUT_CHANNELS % GROUPS != 0)
      $error("channel counts must be divisible by GROUPS");
    if (CHANNEL_LANE_COUNT > OUTPUT_CHANNELS ||
        SPATIAL_LANE_COUNT > OUTPUT_WIDTH*OUTPUT_HEIGHT)
      $error("parallel scatter lane geometry exceeds its destination population");
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
         output_channel = output_channel+1) begin
      output_group = output_channel / OUTPUTS_PER_GROUP;
      for (kernel_y = 0; kernel_y < KERNEL_HEIGHT; kernel_y = kernel_y+1)
        for (kernel_x = 0; kernel_x < KERNEL_WIDTH; kernel_x = kernel_x+1) begin
          tap_index = kernel_y*KERNEL_WIDTH+kernel_x;
          projection_index = output_channel*TAP_COUNT+tap_index;
          weight_index = (output_channel*INPUTS_PER_GROUP+local_input_channel)*
                         TAP_COUNT+tap_index;
          selected_weight = KERNEL_WEIGHTS[
            weight_index*WEIGHT_WIDTH +: WEIGHT_WIDTH];
          scatter_weight[projection_index*WEIGHT_WIDTH +: WEIGHT_WIDTH] =
            selected_weight;
          numerator_x = $unsigned(spike_x_i)+PAD_X-kernel_x*DILATION_X;
          numerator_y = $unsigned(spike_y_i)+PAD_Y-kernel_y*DILATION_Y;
          if (spike_valid && $unsigned(spike_channel_i) < INPUT_CHANNELS &&
              output_group == input_group && selected_weight != 0 &&
              numerator_x >= 0 && numerator_y >= 0) begin
            destination_x = numerator_x/STRIDE_X;
            destination_y = numerator_y/STRIDE_Y;
            if ((numerator_x % STRIDE_X) == 0 &&
                (numerator_y % STRIDE_Y) == 0 &&
                destination_x < OUTPUT_WIDTH && destination_y < OUTPUT_HEIGHT) begin
              scatter_valid[projection_index] = 1'b1;
              scatter_x[projection_index*COORD_WIDTH +: COORD_WIDTH] = destination_x;
              scatter_y[projection_index*COORD_WIDTH +: COORD_WIDTH] = destination_y;
            end
          end
        end
    end
  end

  always_comb begin
    contribution_valid = '0;
    destination_channel_o = '0;
    destination_x_o = '0;
    destination_y_o = '0;
    weight_o = '0;
    lane_has_pending = '0;
    accepted_projection = '0;
    for (lane_index = 0; lane_index < LANE_COUNT; lane_index = lane_index+1)
      selected_projection[lane_index] = 0;
    for (projection_index = PROJECTION_COUNT-1; projection_index >= 0;
         projection_index = projection_index-1) begin
      candidate_channel = projection_index/TAP_COUNT;
      candidate_x = $unsigned(pending_x_reg[
        projection_index*COORD_WIDTH +: COORD_WIDTH]);
      candidate_y = $unsigned(pending_y_reg[
        projection_index*COORD_WIDTH +: COORD_WIDTH]);
      candidate_spatial = candidate_y*OUTPUT_WIDTH+candidate_x;
      candidate_lane = (candidate_channel % CHANNEL_LANE_COUNT)*
                       SPATIAL_LANE_COUNT+
                       (candidate_spatial % SPATIAL_LANE_COUNT);
      if (pending_valid_reg[projection_index]) begin
        selected_projection[candidate_lane] = projection_index;
        lane_has_pending[candidate_lane] = 1'b1;
      end
    end
    for (lane_index = 0; lane_index < LANE_COUNT; lane_index = lane_index+1) begin
      projection_index = selected_projection[lane_index];
      contribution_valid[lane_index] = lane_has_pending[lane_index];
      destination_channel_o[
        lane_index*OUTPUT_CHANNEL_WIDTH +: OUTPUT_CHANNEL_WIDTH] =
        projection_index/TAP_COUNT;
      destination_x_o[lane_index*COORD_WIDTH +: COORD_WIDTH] =
        pending_x_reg[projection_index*COORD_WIDTH +: COORD_WIDTH];
      destination_y_o[lane_index*COORD_WIDTH +: COORD_WIDTH] =
        pending_y_reg[projection_index*COORD_WIDTH +: COORD_WIDTH];
      weight_o[lane_index*WEIGHT_WIDTH +: WEIGHT_WIDTH] =
        pending_weight_reg[projection_index*WEIGHT_WIDTH +: WEIGHT_WIDTH];
      if (lane_has_pending[lane_index] && contribution_ready[lane_index])
        accepted_projection[projection_index] = 1'b1;
    end
    pending_drains = pending_valid_reg != 0 &&
                     (pending_valid_reg & ~accepted_projection) == 0;
  end

  // Replace a fully accepted projection set in the same clock. This removes
  // the empty cycle between presynaptic events when all selected banks accept.
  assign spike_ready = (pending_valid_reg == 0) || pending_drains;
  assign idle_o = (pending_valid_reg == 0);
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
    end else begin
      for (lane_index = 0; lane_index < LANE_COUNT; lane_index = lane_index+1)
        if (contribution_valid[lane_index] && contribution_ready[lane_index])
          pending_valid_reg[selected_projection[lane_index]] <= 1'b0;
    end
  end
endmodule
