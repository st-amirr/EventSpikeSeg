`timescale 1ns/1ps
// Correctness-reference binary OR/union for two sparse spike streams.
// Equal packed spike addresses are emitted once per 5 ms bin.  The block waits
// for completion from both inputs, then drains the unique set followed by one
// completion token.  MAX_EVENTS is deliberately small for component/equivalence
// testing; full-chip residual paths require a banked sparse dedup implementation.
module binary_event_union2 #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer MAX_EVENTS = 64,
  parameter integer COUNT_WIDTH = $clog2(MAX_EVENTS + 1)
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
  output logic overflow_o,
  output logic tag_mismatch_o
);
  localparam [1:0] COLLECT = 2'd0, DRAIN = 2'd1, EMIT_DONE = 2'd2;
  logic [1:0] state_reg;
  logic [PAYLOAD_WIDTH-1:0] events_mem [0:MAX_EVENTS-1];
  logic [COUNT_WIDTH-1:0] event_count_reg;
  logic [COUNT_WIDTH-1:0] drain_index_reg;
  logic completion0_seen_reg;
  logic completion1_seen_reg;
  logic [TAG_WIDTH-1:0] completion0_tag_reg;
  logic [TAG_WIDTH-1:0] completion1_tag_reg;
  logic select0;
  logic select1;
  logic selected_completion;
  logic [PAYLOAD_WIDTH-1:0] selected_payload;
  logic [TAG_WIDTH-1:0] selected_tag;
  logic duplicate;
  integer i;

  always_comb begin
    in0_ready = 1'b0;
    in1_ready = 1'b0;
    out_valid = 1'b0;
    out_payload = '0;
    out_completion = 1'b0;
    out_bin_tag = completion0_tag_reg;
    select0 = 1'b0;
    select1 = 1'b0;
    selected_completion = 1'b0;
    selected_payload = '0;
    selected_tag = '0;
    duplicate = 1'b0;

    if (state_reg == COLLECT) begin
      if (!completion0_seen_reg && in0_valid) begin
        select0 = 1'b1;
        selected_completion = in0_completion;
        selected_payload = in0_payload;
        selected_tag = in0_bin_tag;
        in0_ready = 1'b1;
      end else if (!completion1_seen_reg && in1_valid) begin
        select1 = 1'b1;
        selected_completion = in1_completion;
        selected_payload = in1_payload;
        selected_tag = in1_bin_tag;
        in1_ready = 1'b1;
      end
      if ((select0 || select1) && !selected_completion) begin
        for (i = 0; i < MAX_EVENTS; i = i + 1)
          if (i < event_count_reg && events_mem[i] == selected_payload)
            duplicate = 1'b1;
      end
    end else if (state_reg == DRAIN) begin
      out_valid = (drain_index_reg < event_count_reg);
      out_payload = events_mem[drain_index_reg];
      out_completion = 1'b0;
      out_bin_tag = completion0_tag_reg;
    end else if (state_reg == EMIT_DONE) begin
      out_valid = 1'b1;
      out_completion = 1'b1;
      out_bin_tag = completion0_tag_reg;
    end
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      event_count_reg <= '0;
      drain_index_reg <= '0;
      completion0_seen_reg <= 1'b0;
      completion1_seen_reg <= 1'b0;
      completion0_tag_reg <= '0;
      completion1_tag_reg <= '0;
      overflow_o <= 1'b0;
      tag_mismatch_o <= 1'b0;
    end else begin
      case (state_reg)
        COLLECT: begin
          if (select0 && in0_valid && in0_ready) begin
            if (in0_completion) begin
              completion0_seen_reg <= 1'b1;
              completion0_tag_reg <= in0_bin_tag;
              if (completion1_seen_reg && completion1_tag_reg != in0_bin_tag)
                tag_mismatch_o <= 1'b1;
            end else if (!duplicate) begin
              if (event_count_reg < MAX_EVENTS) begin
                events_mem[event_count_reg] <= in0_payload;
                event_count_reg <= event_count_reg + 1'b1;
              end else begin
                overflow_o <= 1'b1;
              end
            end
          end else if (select1 && in1_valid && in1_ready) begin
            if (in1_completion) begin
              completion1_seen_reg <= 1'b1;
              completion1_tag_reg <= in1_bin_tag;
              if (completion0_seen_reg && completion0_tag_reg != in1_bin_tag)
                tag_mismatch_o <= 1'b1;
            end else if (!duplicate) begin
              if (event_count_reg < MAX_EVENTS) begin
                events_mem[event_count_reg] <= in1_payload;
                event_count_reg <= event_count_reg + 1'b1;
              end else begin
                overflow_o <= 1'b1;
              end
            end
          end

          // Transition one cycle after both completion flags are visible.
          if (completion0_seen_reg && completion1_seen_reg) begin
            if (completion0_tag_reg != completion1_tag_reg) begin
              tag_mismatch_o <= 1'b1;
            end else begin
              drain_index_reg <= '0;
              state_reg <= (event_count_reg == 0) ? EMIT_DONE : DRAIN;
            end
          end
        end

        DRAIN: begin
          if (out_valid && out_ready) begin
            if (drain_index_reg + 1'b1 >= event_count_reg)
              state_reg <= EMIT_DONE;
            else
              drain_index_reg <= drain_index_reg + 1'b1;
          end
        end

        EMIT_DONE: begin
          if (out_valid && out_ready) begin
            state_reg <= COLLECT;
            event_count_reg <= '0;
            drain_index_reg <= '0;
            completion0_seen_reg <= 1'b0;
            completion1_seen_reg <= 1'b0;
          end
        end

        default: state_reg <= COLLECT;
      endcase
    end
  end
endmodule
