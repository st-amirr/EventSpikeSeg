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
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer CURRENT_WIDTH = 32,
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
  localparam logic signed [CURRENT_WIDTH-1:0] MAX_CURRENT =
    {1'b0, {(CURRENT_WIDTH-1){1'b1}}};
  localparam logic signed [CURRENT_WIDTH-1:0] MIN_CURRENT =
    {1'b1, {(CURRENT_WIDTH-1){1'b0}}};
  initial begin
    if (INPUT_CHANNELS % GROUPS != 0 || OUTPUT_CHANNELS % GROUPS != 0)
      $error("resident convolution channel counts must be divisible by GROUPS");
  end

  // Build a fixed 32-bit addition chain for every destination. Keeping every
  // spike and weight index constant avoids the large dynamic-select network
  // that Yosys otherwise creates while deriving a parameterized actor.
  generate
    for (genvar destination = 0; destination < DEST_COUNT; destination = destination+1) begin : currents
      localparam integer OUTPUT_CHANNEL = destination/OUTPUT_SPATIAL_COUNT;
      localparam integer OUTPUT_X = (destination%OUTPUT_SPATIAL_COUNT)%OUTPUT_TILE_WIDTH;
      localparam integer OUTPUT_Y = (destination%OUTPUT_SPATIAL_COUNT)/OUTPUT_TILE_WIDTH;
      localparam integer TERM_COUNT = INPUTS_PER_GROUP*TAP_COUNT;
      logic signed [(TERM_COUNT+1)*32-1:0] partial_sum;
      integer signed sum_value;

      assign partial_sum[0 +: 32] = 32'sd0;
      for (genvar term = 0; term < TERM_COUNT; term = term+1) begin : terms
        localparam integer LOCAL_INPUT_CHANNEL = term/TAP_COUNT;
        localparam integer TAP = term%TAP_COUNT;
        localparam integer KERNEL_X = TAP%KERNEL_WIDTH;
        localparam integer KERNEL_Y = TAP/KERNEL_WIDTH;
        localparam integer INPUT_CHANNEL =
          (OUTPUT_CHANNEL/OUTPUTS_PER_GROUP)*INPUTS_PER_GROUP+LOCAL_INPUT_CHANNEL;
        localparam integer INPUT_X =
          (OUTPUT_TILE_X+OUTPUT_X)*STRIDE_X-PAD_X+
          KERNEL_X*DILATION_X-INPUT_TILE_X;
        localparam integer INPUT_Y =
          (OUTPUT_TILE_Y+OUTPUT_Y)*STRIDE_Y-PAD_Y+
          KERNEL_Y*DILATION_Y-INPUT_TILE_Y;
        localparam integer WEIGHT_INDEX =
          (OUTPUT_CHANNEL*INPUTS_PER_GROUP+LOCAL_INPUT_CHANNEL)*TAP_COUNT+TAP;
        if (INPUT_X >= 0 && INPUT_X < INPUT_WIDTH &&
            INPUT_Y >= 0 && INPUT_Y < INPUT_HEIGHT) begin : connected
          localparam integer INPUT_INDEX =
            INPUT_CHANNEL*INPUT_SPATIAL_COUNT+INPUT_Y*INPUT_WIDTH+INPUT_X;
          assign partial_sum[(term+1)*32 +: 32] =
            $signed(partial_sum[term*32 +: 32]) +
            (spike_vector_i[INPUT_INDEX] ?
             $signed(KERNEL_WEIGHTS[WEIGHT_INDEX*WEIGHT_WIDTH +: WEIGHT_WIDTH]) : 0);
        end else begin : outside_halo
          assign partial_sum[(term+1)*32 +: 32] =
            partial_sum[term*32 +: 32];
        end
      end

      always_comb begin
        // The original procedural integer accumulated with signed 32-bit wrap.
        sum_value = $signed(partial_sum[TERM_COUNT*32 +: 32]);
        if (sum_value > MAX_CURRENT) sum_value = MAX_CURRENT;
        else if (sum_value < MIN_CURRENT) sum_value = MIN_CURRENT;
        current_delta_o[destination*CURRENT_WIDTH +: CURRENT_WIDTH] =
          sum_value[CURRENT_WIDTH-1:0];
      end
    end
  endgenerate
endmodule
