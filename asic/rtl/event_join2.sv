`timescale 1ns/1ps
// Two-input lossless event merge with ordered 5 ms completion-token rendezvous.
// Data events from both inputs are forwarded without deduplication.  Completion
// tokens are consumed locally and exactly one downstream completion is emitted
// only after BOTH inputs have closed the same bin.  This matches concat and the
// multiplicity-preserving decoder skip; residual binary-OR needs an additional
// address-dedup stage and is intentionally not hidden in this primitive.
module event_join2 #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24
) (
  input  logic clk,
  input  logic reset,

  input  logic in0_valid,
  output logic in0_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in0_payload,
  input  logic in0_completion,
  input  logic [TAG_WIDTH-1:0] in0_bin_tag,

  input  logic in1_valid,
  output logic in1_ready,
  input  logic [PAYLOAD_WIDTH-1:0] in1_payload,
  input  logic in1_completion,
  input  logic [TAG_WIDTH-1:0] in1_bin_tag,

  output logic out_valid,
  input  logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic tag_mismatch_o
);
  logic completion0_seen_reg;
  logic completion1_seen_reg;
  logic [TAG_WIDTH-1:0] completion0_tag_reg;
  logic [TAG_WIDTH-1:0] completion1_tag_reg;
  logic completion_pending;
  logic select0;
  logic select1;

  // A mismatched rendezvous is fatal for this stream: report it and fail
  // closed. Forwarding either tag would let downstream PLIFs commit an
  // incomplete/corrupted epoch.
  assign completion_pending = completion0_seen_reg && completion1_seen_reg &&
                              (completion0_tag_reg == completion1_tag_reg);

  always_comb begin
    in0_ready = 1'b0;
    in1_ready = 1'b0;
    out_valid = 1'b0;
    out_payload = '0;
    out_completion = 1'b0;
    out_bin_tag = completion0_tag_reg;
    select0 = 1'b0;
    select1 = 1'b0;

    if (completion_pending) begin
      out_valid = 1'b1;
      out_completion = 1'b1;
      out_bin_tag = completion0_tag_reg;
    end else if (!completion0_seen_reg && in0_valid) begin
      // Fixed priority is sufficient for the correctness reference.  A later
      // physical router may use round-robin arbitration without changing semantics.
      select0 = 1'b1;
      if (in0_completion) begin
        in0_ready = 1'b1;
      end else begin
        out_valid = 1'b1;
        out_payload = in0_payload;
        out_completion = 1'b0;
        out_bin_tag = in0_bin_tag;
        in0_ready = out_ready;
      end
    end else if (!completion1_seen_reg && in1_valid) begin
      select1 = 1'b1;
      if (in1_completion) begin
        in1_ready = 1'b1;
      end else begin
        out_valid = 1'b1;
        out_payload = in1_payload;
        out_completion = 1'b0;
        out_bin_tag = in1_bin_tag;
        in1_ready = out_ready;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      completion0_seen_reg <= 1'b0;
      completion1_seen_reg <= 1'b0;
      completion0_tag_reg <= '0;
      completion1_tag_reg <= '0;
      tag_mismatch_o <= 1'b0;
    end else begin
      if (select0 && in0_valid && in0_ready && in0_completion) begin
        completion0_seen_reg <= 1'b1;
        completion0_tag_reg <= in0_bin_tag;
        if (completion1_seen_reg && completion1_tag_reg != in0_bin_tag)
          tag_mismatch_o <= 1'b1;
      end
      if (select1 && in1_valid && in1_ready && in1_completion) begin
        completion1_seen_reg <= 1'b1;
        completion1_tag_reg <= in1_bin_tag;
        if (completion0_seen_reg && completion0_tag_reg != in1_bin_tag)
          tag_mismatch_o <= 1'b1;
      end

      if (completion_pending && out_valid && out_ready) begin
        if (completion0_tag_reg != completion1_tag_reg)
          tag_mismatch_o <= 1'b1;
        completion0_seen_reg <= 1'b0;
        completion1_seen_reg <= 1'b0;
      end
    end
  end
endmodule
