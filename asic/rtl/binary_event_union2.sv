`timescale 1ns/1ps
// Exact binary OR/union for two sparse spike streams. Unique events are held
// in one local SRAM. Deduplication uses a sequential exact search, avoiding a
// destination-scale combinational CAM while preserving lossless semantics.
module binary_event_union2 #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer MAX_EVENTS = 64,
  parameter integer COUNT_WIDTH = $clog2(MAX_EVENTS + 1),
  parameter integer MEMORY_ADDRESS_WIDTH =
    (MAX_EVENTS <= 1) ? 1 : $clog2(MAX_EVENTS),
  parameter integer USE_STATE_MACRO = 0
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
  localparam [3:0] COLLECT = 4'd0, SEARCH_ISSUE = 4'd1,
                   SEARCH_WAIT = 4'd2, APPEND_WRITE = 4'd3,
                   DRAIN_ISSUE = 4'd4, DRAIN_WAIT = 4'd5,
                   DRAIN_HOLD = 4'd6, EMIT_DONE = 4'd7;
  logic [3:0] state_reg;
  logic [COUNT_WIDTH-1:0] event_count_reg;
  logic [COUNT_WIDTH-1:0] search_index_reg;
  logic [COUNT_WIDTH-1:0] drain_index_reg;
  logic completion0_seen_reg;
  logic completion1_seen_reg;
  logic [TAG_WIDTH-1:0] completion0_tag_reg;
  logic [TAG_WIDTH-1:0] completion1_tag_reg;
  logic [PAYLOAD_WIDTH-1:0] selected_payload_reg;
  logic [PAYLOAD_WIDTH-1:0] drain_payload_reg;
  logic select0, select1, selected_completion;
  logic [PAYLOAD_WIDTH-1:0] selected_payload;
  logic [TAG_WIDTH-1:0] selected_tag;

  logic memory_read_enable;
  logic [MEMORY_ADDRESS_WIDTH-1:0] memory_read_address;
  logic memory_read_valid;
  logic [PAYLOAD_WIDTH-1:0] memory_read_data;
  logic memory_write_enable;
  logic [MEMORY_ADDRESS_WIDTH-1:0] memory_write_address;

  always_comb begin
    in0_ready = 1'b0;
    in1_ready = 1'b0;
    select0 = 1'b0;
    select1 = 1'b0;
    selected_completion = 1'b0;
    selected_payload = '0;
    selected_tag = '0;
    if (state_reg == COLLECT) begin
      if (!completion0_seen_reg && in0_valid) begin
        select0 = 1'b1;
        in0_ready = 1'b1;
        selected_completion = in0_completion;
        selected_payload = in0_payload;
        selected_tag = in0_bin_tag;
      end else if (!completion1_seen_reg && in1_valid) begin
        select1 = 1'b1;
        in1_ready = 1'b1;
        selected_completion = in1_completion;
        selected_payload = in1_payload;
        selected_tag = in1_bin_tag;
      end
    end
  end

  assign out_valid = (state_reg == DRAIN_HOLD) || (state_reg == EMIT_DONE);
  assign out_payload = (state_reg == DRAIN_HOLD) ? drain_payload_reg : '0;
  assign out_completion = (state_reg == EMIT_DONE);
  assign out_bin_tag = completion0_tag_reg;
  assign memory_read_enable = (state_reg == SEARCH_ISSUE) ||
                              (state_reg == DRAIN_ISSUE);
  assign memory_read_address = (state_reg == SEARCH_ISSUE) ?
                               search_index_reg[MEMORY_ADDRESS_WIDTH-1:0] :
                               drain_index_reg[MEMORY_ADDRESS_WIDTH-1:0];
  assign memory_write_enable = (state_reg == APPEND_WRITE);
  assign memory_write_address = event_count_reg[MEMORY_ADDRESS_WIDTH-1:0];

  actor_local_state_sram #(
    .DATA_WIDTH(PAYLOAD_WIDTH), .DEPTH(MAX_EVENTS),
    .ADDRESS_WIDTH(MEMORY_ADDRESS_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) event_bank (
    .clk, .read_enable_i(memory_read_enable),
    .read_address_i(memory_read_address), .read_valid_o(memory_read_valid),
    .read_data_o(memory_read_data), .write_enable_i(memory_write_enable),
    .write_address_i(memory_write_address), .write_data_i(selected_payload_reg)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      event_count_reg <= '0;
      search_index_reg <= '0;
      drain_index_reg <= '0;
      completion0_seen_reg <= 1'b0;
      completion1_seen_reg <= 1'b0;
      completion0_tag_reg <= '0;
      completion1_tag_reg <= '0;
      selected_payload_reg <= '0;
      drain_payload_reg <= '0;
      overflow_o <= 1'b0;
      tag_mismatch_o <= 1'b0;
    end else begin
      case (state_reg)
        COLLECT: begin
          if (completion0_seen_reg && completion1_seen_reg) begin
            if (overflow_o) begin
              // Fail closed: a partial residual union must never produce a
              // downstream completion token or corrupted prediction.
              state_reg <= COLLECT;
            end else if (completion0_tag_reg != completion1_tag_reg)
              tag_mismatch_o <= 1'b1;
            else begin
              drain_index_reg <= '0;
              state_reg <= (event_count_reg == 0) ? EMIT_DONE : DRAIN_ISSUE;
            end
          end else if ((select0 || select1) &&
                       ((select0 && in0_valid && in0_ready) ||
                        (select1 && in1_valid && in1_ready))) begin
            if (selected_completion) begin
              if (select0) begin
                completion0_seen_reg <= 1'b1;
                completion0_tag_reg <= selected_tag;
                if (completion1_seen_reg && completion1_tag_reg != selected_tag)
                  tag_mismatch_o <= 1'b1;
              end else begin
                completion1_seen_reg <= 1'b1;
                completion1_tag_reg <= selected_tag;
                if (completion0_seen_reg && completion0_tag_reg != selected_tag)
                  tag_mismatch_o <= 1'b1;
              end
            end else begin
              selected_payload_reg <= selected_payload;
              search_index_reg <= '0;
              if (event_count_reg == 0) begin
                if (MAX_EVENTS > 0) state_reg <= APPEND_WRITE;
                else overflow_o <= 1'b1;
              end else state_reg <= SEARCH_ISSUE;
            end
          end
        end
        SEARCH_ISSUE: state_reg <= SEARCH_WAIT;
        SEARCH_WAIT: if (memory_read_valid) begin
          if (memory_read_data == selected_payload_reg)
            state_reg <= COLLECT;
          else if (search_index_reg + 1'b1 >= event_count_reg) begin
            if (event_count_reg < MAX_EVENTS)
              state_reg <= APPEND_WRITE;
            else begin
              overflow_o <= 1'b1;
              state_reg <= COLLECT;
            end
          end else begin
            search_index_reg <= search_index_reg + 1'b1;
            state_reg <= SEARCH_ISSUE;
          end
        end
        APPEND_WRITE: begin
          event_count_reg <= event_count_reg + 1'b1;
          state_reg <= COLLECT;
        end
        DRAIN_ISSUE: state_reg <= DRAIN_WAIT;
        DRAIN_WAIT: if (memory_read_valid) begin
          drain_payload_reg <= memory_read_data;
          state_reg <= DRAIN_HOLD;
        end
        DRAIN_HOLD: if (out_ready) begin
          if (drain_index_reg + 1'b1 >= event_count_reg)
            state_reg <= EMIT_DONE;
          else begin
            drain_index_reg <= drain_index_reg + 1'b1;
            state_reg <= DRAIN_ISSUE;
          end
        end
        EMIT_DONE: if (out_ready) begin
          state_reg <= COLLECT;
          event_count_reg <= '0;
          search_index_reg <= '0;
          drain_index_reg <= '0;
          completion0_seen_reg <= 1'b0;
          completion1_seen_reg <= 1'b0;
        end
        default: state_reg <= COLLECT;
      endcase
    end
  end
endmodule
