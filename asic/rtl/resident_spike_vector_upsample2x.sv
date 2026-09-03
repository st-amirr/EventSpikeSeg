`timescale 1ns/1ps
// Stateless nearest-neighbor 2x expansion of a channel-major spike vector.
module resident_spike_vector_upsample2x #(
  parameter integer CHANNELS = 2,
  parameter integer INPUT_WIDTH = 2,
  parameter integer INPUT_HEIGHT = 2,
  parameter integer OUTPUT_WIDTH = 2*INPUT_WIDTH,
  parameter integer OUTPUT_HEIGHT = 2*INPUT_HEIGHT,
  parameter integer TAG_WIDTH = 24,
  parameter integer INPUT_COUNT = CHANNELS*INPUT_WIDTH*INPUT_HEIGHT,
  parameter integer OUTPUT_COUNT = CHANNELS*OUTPUT_WIDTH*OUTPUT_HEIGHT
) (
  input logic in_valid_i, output logic in_ready_o,
  input logic [INPUT_COUNT-1:0] in_vector_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [OUTPUT_COUNT-1:0] out_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o
);
  integer channel;
  integer input_x;
  integer input_y;
  integer dx;
  integer dy;
  integer input_index;
  integer output_index;
  assign in_ready_o = out_ready_i;
  assign out_valid_o = in_valid_i;
  assign out_completion_o = in_completion_i;
  assign out_tag_o = in_tag_i;

  always_comb begin
    out_vector_o = '0;
    input_index = 0;
    output_index = 0;
    for (channel = 0; channel < CHANNELS; channel = channel+1)
      for (input_y = 0; input_y < INPUT_HEIGHT; input_y = input_y+1)
        for (input_x = 0; input_x < INPUT_WIDTH; input_x = input_x+1) begin
          input_index = channel*INPUT_WIDTH*INPUT_HEIGHT+
                        input_y*INPUT_WIDTH+input_x;
          for (dy = 0; dy < 2; dy = dy+1)
            for (dx = 0; dx < 2; dx = dx+1) begin
              output_index = channel*OUTPUT_WIDTH*OUTPUT_HEIGHT+
                (2*input_y+dy)*OUTPUT_WIDTH+2*input_x+dx;
              out_vector_o[output_index] = in_vector_i[input_index];
            end
        end
  end
endmodule
