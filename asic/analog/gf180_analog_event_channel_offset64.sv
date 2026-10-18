`timescale 1ns/1ps
// Registered GF180 channel-ID remap for the 64..127 decoder concat input.
// The one-entry output stage sustains one packet per cycle and holds both data
// and completion packets under backpressure.
module gf180_analog_event_channel_offset64 (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [31:0] in_payload_i, input logic in_completion_i,
  input logic [23:0] in_bin_tag_i,
  output logic out_valid_o, input logic out_ready_i,
  output logic [31:0] out_payload_o, output logic out_completion_o,
  output logic [23:0] out_bin_tag_o,
  output logic channel_overflow_o
);
  logic mapped_valid, mapped_ready;
  logic [31:0] mapped_payload;
  logic mapped_completion;
  logic [23:0] mapped_tag;
  logic mapped_overflow;
  logic output_valid_reg;
  logic [31:0] output_payload_reg;
  logic output_completion_reg;
  logic [23:0] output_tag_reg;
  logic output_slot_ready;

  assign output_slot_ready = !output_valid_reg || out_ready_i;
  assign mapped_ready = output_slot_ready && !channel_overflow_o;
  assign in_ready_o = mapped_ready;
  assign out_valid_o = output_valid_reg && !channel_overflow_o;
  assign out_payload_o = output_payload_reg;
  assign out_completion_o = output_completion_reg;
  assign out_bin_tag_o = output_tag_reg;

  event_channel_offset #(
    .PAYLOAD_WIDTH(32), .TAG_WIDTH(24), .CHANNEL_LSB(19),
    .CHANNEL_WIDTH(7), .CHANNEL_OFFSET(64)
  ) offset_cell (
    .in_valid(in_valid_i && !channel_overflow_o), .in_ready(),
    .in_payload(in_payload_i), .in_completion(in_completion_i),
    .in_bin_tag(in_bin_tag_i),
    .out_valid(mapped_valid), .out_ready(mapped_ready),
    .out_payload(mapped_payload), .out_completion(mapped_completion),
    .out_bin_tag(mapped_tag), .channel_overflow_o(mapped_overflow)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      output_valid_reg <= 1'b0;
      output_payload_reg <= '0;
      output_completion_reg <= 1'b0;
      output_tag_reg <= '0;
      channel_overflow_o <= 1'b0;
    end else begin
      if (in_valid_i && in_ready_o && mapped_overflow)
        channel_overflow_o <= 1'b1;
      if (output_slot_ready && !channel_overflow_o) begin
        output_valid_reg <= mapped_valid && !mapped_overflow;
        if (mapped_valid && !mapped_overflow) begin
          output_payload_reg <= mapped_payload;
          output_completion_reg <= mapped_completion;
          output_tag_reg <= mapped_tag;
        end
      end
    end
  end
endmodule
