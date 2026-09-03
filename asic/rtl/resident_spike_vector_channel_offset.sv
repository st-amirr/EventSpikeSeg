`timescale 1ns/1ps
// Combinational channel remap for a channel-major spike vector. Used by fixed
// concatenation joins; spatial locations are unchanged and no data is stored.
module resident_spike_vector_channel_offset #(
  parameter integer INPUT_CHANNELS = 2,
  parameter integer OUTPUT_CHANNELS = 4,
  parameter integer SPATIAL_COUNT = 4,
  parameter integer CHANNEL_OFFSET = 0,
  parameter integer TAG_WIDTH = 24,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*SPATIAL_COUNT,
  parameter integer OUTPUT_COUNT = OUTPUT_CHANNELS*SPATIAL_COUNT
) (
  input logic in_valid_i, output logic in_ready_o,
  input logic [INPUT_COUNT-1:0] in_vector_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [OUTPUT_COUNT-1:0] out_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o,
  output logic configuration_error_o
);
  integer channel;
  integer spatial;
  assign in_ready_o = out_ready_i;
  assign out_valid_o = in_valid_i;
  assign out_completion_o = in_completion_i;
  assign out_tag_o = in_tag_i;
  assign configuration_error_o = CHANNEL_OFFSET+INPUT_CHANNELS > OUTPUT_CHANNELS;

  always_comb begin
    out_vector_o = '0;
    for (channel = 0; channel < INPUT_CHANNELS; channel = channel+1)
      for (spatial = 0; spatial < SPATIAL_COUNT; spatial = spatial+1)
        if (!configuration_error_o)
          out_vector_o[(channel+CHANNEL_OFFSET)*SPATIAL_COUNT+spatial] =
            in_vector_i[channel*SPATIAL_COUNT+spatial];
  end
endmodule
