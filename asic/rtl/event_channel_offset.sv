`timescale 1ns/1ps
// Fixed channel-ID remap used by compile-time concatenation routes.
// Payload convention defaults to x[9:0], y[18:10], channel[25:19].
module event_channel_offset #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer CHANNEL_LSB = 19,
  parameter integer CHANNEL_WIDTH = 7,
  parameter integer CHANNEL_OFFSET = 0
) (
  input  logic in_valid,
  output logic in_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in_payload,
  input  logic in_completion,
  input  logic [TAG_WIDTH-1:0] in_bin_tag,

  output logic out_valid,
  input  logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic channel_overflow_o
);
  localparam integer MAX_CHANNEL = (1 << CHANNEL_WIDTH) - 1;
  integer mapped_channel;

  always_comb begin
    in_ready = out_ready;
    out_valid = in_valid;
    out_payload = in_payload;
    out_completion = in_completion;
    out_bin_tag = in_bin_tag;
    mapped_channel = $unsigned(
      in_payload[CHANNEL_LSB +: CHANNEL_WIDTH]
    ) + CHANNEL_OFFSET;
    channel_overflow_o = in_valid && !in_completion && mapped_channel > MAX_CHANNEL;
    if (!in_completion)
      out_payload[CHANNEL_LSB +: CHANNEL_WIDTH] =
        mapped_channel[CHANNEL_WIDTH-1:0];
  end
endmodule
