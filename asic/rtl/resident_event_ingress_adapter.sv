`timescale 1ns/1ps
// Converts each timestamp-ordered raw event packet into a one-hot input pulse
// for a resident actor. Events are not binned or deduplicated: repeated events
// produce repeated transactions and therefore repeated synaptic additions.
module resident_event_ingress_adapter #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer X_LSB = 0,
  parameter integer X_WIDTH = 10,
  parameter integer Y_LSB = 10,
  parameter integer Y_WIDTH = 9,
  parameter integer CHANNEL_LSB = 19,
  parameter integer CHANNEL_WIDTH = 7,
  parameter integer INPUT_CHANNELS = 2,
  parameter integer INPUT_WIDTH = 640,
  parameter integer INPUT_HEIGHT = 440,
  parameter integer INPUT_COUNT = INPUT_CHANNELS*INPUT_WIDTH*INPUT_HEIGHT
) (
  input logic in_valid_i, output logic in_ready_o,
  input logic [PAYLOAD_WIDTH-1:0] in_payload_i,
  input logic in_completion_i,
  input logic [TAG_WIDTH-1:0] in_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [INPUT_COUNT-1:0] out_spike_vector_o,
  output logic out_completion_o,
  output logic [TAG_WIDTH-1:0] out_tag_o,
  output logic coordinate_error_o
);
  integer event_x;
  integer event_y;
  integer event_channel;
  integer event_index;

  assign in_ready_o = out_ready_i;
  assign out_valid_o = in_valid_i;
  assign out_completion_o = in_completion_i;
  assign out_tag_o = in_tag_i;

  always_comb begin
    out_spike_vector_o = '0;
    event_x = $unsigned(in_payload_i[X_LSB +: X_WIDTH]);
    event_y = $unsigned(in_payload_i[Y_LSB +: Y_WIDTH]);
    event_channel = $unsigned(in_payload_i[CHANNEL_LSB +: CHANNEL_WIDTH]);
    event_index = 0;
    coordinate_error_o = in_valid_i && !in_completion_i &&
      (event_x >= INPUT_WIDTH || event_y >= INPUT_HEIGHT ||
       event_channel >= INPUT_CHANNELS);
    if (in_valid_i && !in_completion_i && !coordinate_error_o) begin
      event_index = event_channel*INPUT_WIDTH*INPUT_HEIGHT+
                    event_y*INPUT_WIDTH+event_x;
      out_spike_vector_o[event_index] = 1'b1;
    end
  end
endmodule
