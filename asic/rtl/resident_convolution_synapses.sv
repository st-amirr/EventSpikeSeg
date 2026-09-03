`timescale 1ns/1ps
// Compile-time convolutional synapse fabric for resident PLIF populations.
// A presynaptic spike bitmap gates fixed int8 weights; all postsynaptic current
// deltas are formed in parallel with no weight or membrane memory transaction.
// Flattening matches PyTorch Conv2d: [out][in/groups][ky][kx].
module resident_convolution_synapses #(
  parameter integer INPUT_CHANNELS = 1,
  parameter integer INPUT_WIDTH = 4,
  parameter integer INPUT_HEIGHT = 4,
  parameter integer INPUT_TILE_X = 0,
  parameter integer INPUT_TILE_Y = 0,
  parameter integer OUTPUT_CHANNELS = 1,
  parameter integer OUTPUT_WIDTH = 4,
  parameter integer OUTPUT_HEIGHT = 4,
  parameter integer OUTPUT_TILE_X = 0,
  parameter integer OUTPUT_TILE_Y = 0,
  parameter integer OUTPUT_TILE_WIDTH = OUTPUT_WIDTH,
  parameter integer OUTPUT_TILE_HEIGHT = OUTPUT_HEIGHT,
  parameter integer GROUPS = 1,
  parameter integer KERNEL_WIDTH = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X = 1,
  parameter integer STRIDE_Y = 1,
  parameter integer DILATION_X = 1,
  parameter integer DILATION_Y = 1,
  parameter integer PAD_X = 1,
  parameter integer PAD_Y = 1,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer INPUT_SPATIAL_COUNT = INPUT_WIDTH*INPUT_HEIGHT,
  parameter integer OUTPUT_SPATIAL_COUNT = OUTPUT_TILE_WIDTH*OUTPUT_TILE_HEIGHT,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*INPUT_SPATIAL_COUNT,
  parameter integer DEST_COUNT = OUTPUT_CHANNELS*OUTPUT_SPATIAL_COUNT,
  parameter integer TAP_COUNT = KERNEL_WIDTH*KERNEL_HEIGHT,
  parameter integer INPUTS_PER_GROUP = INPUT_CHANNELS/GROUPS,
  parameter integer OUTPUTS_PER_GROUP = OUTPUT_CHANNELS/GROUPS,
  parameter integer WEIGHT_COUNT = OUTPUT_CHANNELS*INPUTS_PER_GROUP*TAP_COUNT,
  parameter logic signed [WEIGHT_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0
) (
  input logic [INPUT_COUNT-1:0] spike_vector_i,
  output logic signed [DEST_COUNT*CURRENT_WIDTH-1:0] current_delta_o
);
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH-1))-1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH-1));
  integer output_channel;
  integer output_x;
  integer output_y;
  integer output_spatial;
  integer destination;
  integer input_channel;
  integer local_input_channel;
  integer kernel_x;
  integer kernel_y;
  integer tap;
  integer input_x;
  integer input_y;
  integer input_spatial;
  integer input_index;
  integer weight_index;
  integer signed sum_value;

  initial begin
    if (INPUT_CHANNELS % GROUPS != 0 || OUTPUT_CHANNELS % GROUPS != 0)
      $error("resident convolution channel counts must be divisible by GROUPS");
  end

  always_comb begin
    current_delta_o = '0;
    input_channel = 0;
    input_x = 0;
    input_y = 0;
    input_spatial = 0;
    input_index = 0;
    weight_index = 0;
    tap = 0;
    output_spatial = 0;
    destination = 0;
    sum_value = 0;
    for (output_channel = 0; output_channel < OUTPUT_CHANNELS;
         output_channel = output_channel+1)
      for (output_y = 0; output_y < OUTPUT_TILE_HEIGHT; output_y = output_y+1)
        for (output_x = 0; output_x < OUTPUT_TILE_WIDTH; output_x = output_x+1) begin
          sum_value = 0;
          for (local_input_channel = 0;
               local_input_channel < INPUTS_PER_GROUP;
               local_input_channel = local_input_channel+1) begin
            input_channel = (output_channel/OUTPUTS_PER_GROUP)*INPUTS_PER_GROUP+
                            local_input_channel;
            for (kernel_y = 0; kernel_y < KERNEL_HEIGHT; kernel_y = kernel_y+1)
              for (kernel_x = 0; kernel_x < KERNEL_WIDTH; kernel_x = kernel_x+1) begin
                // Convert the checkpoint's global convolution coordinate into
                // this physical tile's local receptive-halo coordinate.
                input_x = (OUTPUT_TILE_X+output_x)*STRIDE_X-PAD_X+
                          kernel_x*DILATION_X-INPUT_TILE_X;
                input_y = (OUTPUT_TILE_Y+output_y)*STRIDE_Y-PAD_Y+
                          kernel_y*DILATION_Y-INPUT_TILE_Y;
                if (input_x >= 0 && input_x < INPUT_WIDTH &&
                    input_y >= 0 && input_y < INPUT_HEIGHT) begin
                  input_spatial = input_y*INPUT_WIDTH+input_x;
                  input_index = input_channel*INPUT_SPATIAL_COUNT+input_spatial;
                  tap = kernel_y*KERNEL_WIDTH+kernel_x;
                  weight_index = (output_channel*INPUTS_PER_GROUP+
                                  local_input_channel)*TAP_COUNT+tap;
                  if (spike_vector_i[input_index])
                    sum_value = sum_value + $signed(KERNEL_WEIGHTS[
                      weight_index*WEIGHT_WIDTH +: WEIGHT_WIDTH]);
                end
              end
          end
          if (sum_value > MAX_CURRENT) sum_value = MAX_CURRENT;
          else if (sum_value < MIN_CURRENT) sum_value = MIN_CURRENT;
          output_spatial = output_y*OUTPUT_TILE_WIDTH+output_x;
          destination = output_channel*OUTPUT_SPATIAL_COUNT+output_spatial;
          current_delta_o[destination*CURRENT_WIDTH +: CURRENT_WIDTH] =
            sum_value[CURRENT_WIDTH-1:0];
        end
  end
endmodule
