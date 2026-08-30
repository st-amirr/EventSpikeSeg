`timescale 1ns/1ps
// SRAM-transactional residual OR. A direct-address one-bit seen map replaces
// the O(MAX_EVENTS) associative scan, while a second SRAM stores unique packed
// events for ordered drain. Both banks can bind to compiler macros.
module binary_event_union2_sram #(
  parameter integer PAYLOAD_WIDTH = 32,
  parameter integer TAG_WIDTH = 24,
  parameter integer X_LSB = 0,
  parameter integer X_WIDTH = 10,
  parameter integer Y_LSB = 10,
  parameter integer Y_WIDTH = 9,
  parameter integer CHANNEL_LSB = 19,
  parameter integer CHANNEL_WIDTH = 7,
  parameter integer OUTPUT_WIDTH = 16,
  parameter integer OUTPUT_HEIGHT = 16,
  parameter integer CHANNEL_COUNT = 8,
  parameter integer SPATIAL_COUNT = OUTPUT_WIDTH * OUTPUT_HEIGHT,
  parameter integer ADDRESS_COUNT = CHANNEL_COUNT * SPATIAL_COUNT,
  parameter integer ADDRESS_WIDTH = (ADDRESS_COUNT <= 1) ? 1 : $clog2(ADDRESS_COUNT),
  parameter integer MAX_EVENTS = 64,
  parameter integer COUNT_WIDTH = (MAX_EVENTS <= 1) ? 1 : $clog2(MAX_EVENTS + 1),
  parameter integer QUEUE_ADDRESS_WIDTH = (MAX_EVENTS <= 1) ? 1 : $clog2(MAX_EVENTS),
  parameter integer USE_SRAM_MACRO = 0
) (
  input logic clk,
  input logic reset,
  input logic in0_valid,
  output logic in0_ready,
  input logic [PAYLOAD_WIDTH-1:0] in0_payload,
  input logic in0_completion,
  input logic [TAG_WIDTH-1:0] in0_bin_tag,
  input logic in1_valid,
  output logic in1_ready,
  input logic [PAYLOAD_WIDTH-1:0] in1_payload,
  input logic in1_completion,
  input logic [TAG_WIDTH-1:0] in1_bin_tag,
  output logic out_valid,
  input logic out_ready,
  output logic [PAYLOAD_WIDTH-1:0] out_payload,
  output logic out_completion,
  output logic [TAG_WIDTH-1:0] out_bin_tag,
  output logic overflow_o,
  output logic tag_mismatch_o
);
  localparam [2:0] SCRUB = 3'd0, COLLECT = 3'd1, LOOKUP = 3'd2,
    DRAIN_READ = 3'd3, DRAIN_CAPTURE = 3'd4, DRAIN_OUTPUT = 3'd5,
    EMIT_DONE = 3'd6;

  logic [2:0] state_reg;
  logic [ADDRESS_WIDTH-1:0] scrub_address_reg;
  logic [COUNT_WIDTH-1:0] event_count_reg;
  logic [COUNT_WIDTH-1:0] drain_index_reg;
  logic completion0_seen_reg;
  logic completion1_seen_reg;
  logic [TAG_WIDTH-1:0] completion0_tag_reg;
  logic [TAG_WIDTH-1:0] completion1_tag_reg;
  logic [ADDRESS_WIDTH-1:0] lookup_address_reg;
  logic [ADDRESS_WIDTH-1:0] drain_address_reg;
  logic select0;
  logic select1;
  logic selected_completion;
  logic [PAYLOAD_WIDTH-1:0] selected_payload;
  logic [TAG_WIDTH-1:0] selected_tag;
  integer selected_x;
  integer selected_y;
  integer selected_channel;
  integer selected_linear_address;
  logic selected_address_valid;
  integer drain_x;
  integer drain_y;
  integer drain_channel;
  integer drain_spatial_address;

  logic seen_read_enable;
  logic [ADDRESS_WIDTH-1:0] seen_read_address;
  logic seen_read_valid;
  logic seen_read_data;
  logic seen_write_enable;
  logic [ADDRESS_WIDTH-1:0] seen_write_address;
  logic seen_write_data;
  logic queue_read_enable;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_read_address;
  logic queue_read_valid;
  logic [ADDRESS_WIDTH-1:0] queue_read_data;
  logic queue_write_enable;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_write_address;
  logic [ADDRESS_WIDTH-1:0] queue_write_data;

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

    selected_x = $unsigned(selected_payload[X_LSB +: X_WIDTH]);
    selected_y = $unsigned(selected_payload[Y_LSB +: Y_WIDTH]);
    selected_channel = $unsigned(selected_payload[CHANNEL_LSB +: CHANNEL_WIDTH]);
    selected_linear_address = selected_channel * SPATIAL_COUNT +
                              selected_y * OUTPUT_WIDTH + selected_x;
    selected_address_valid = selected_x < OUTPUT_WIDTH &&
                             selected_y < OUTPUT_HEIGHT &&
                             selected_channel < CHANNEL_COUNT;

    drain_channel = $unsigned(drain_address_reg) / SPATIAL_COUNT;
    drain_spatial_address = $unsigned(drain_address_reg) % SPATIAL_COUNT;
    drain_y = drain_spatial_address / OUTPUT_WIDTH;
    drain_x = drain_spatial_address % OUTPUT_WIDTH;

    seen_read_enable = state_reg == COLLECT && (select0 || select1) &&
                       !selected_completion && selected_address_valid &&
                       event_count_reg < MAX_EVENTS;
    seen_read_address = selected_linear_address[ADDRESS_WIDTH-1:0];
    seen_write_enable = 1'b0;
    seen_write_address = '0;
    seen_write_data = 1'b0;
    if (state_reg == SCRUB) begin
      seen_write_enable = 1'b1;
      seen_write_address = scrub_address_reg;
    end else if (state_reg == LOOKUP && seen_read_valid && !seen_read_data) begin
      seen_write_enable = 1'b1;
      seen_write_address = lookup_address_reg;
      seen_write_data = 1'b1;
    end else if (state_reg == DRAIN_OUTPUT && out_ready) begin
      seen_write_enable = 1'b1;
      seen_write_address = drain_address_reg;
    end

    queue_write_enable = state_reg == LOOKUP && seen_read_valid && !seen_read_data;
    queue_write_address = event_count_reg[QUEUE_ADDRESS_WIDTH-1:0];
    queue_write_data = lookup_address_reg;
    queue_read_enable = state_reg == DRAIN_READ;
    queue_read_address = drain_index_reg[QUEUE_ADDRESS_WIDTH-1:0];

    out_valid = state_reg == DRAIN_OUTPUT || state_reg == EMIT_DONE;
    out_payload = '0;
    out_payload[X_LSB +: X_WIDTH] = drain_x[X_WIDTH-1:0];
    out_payload[Y_LSB +: Y_WIDTH] = drain_y[Y_WIDTH-1:0];
    out_payload[CHANNEL_LSB +: CHANNEL_WIDTH] =
      drain_channel[CHANNEL_WIDTH-1:0];
    out_completion = state_reg == EMIT_DONE;
    out_bin_tag = completion0_tag_reg;
  end

  actor_local_state_sram #(
    .DATA_WIDTH(1), .DEPTH(ADDRESS_COUNT), .ADDRESS_WIDTH(ADDRESS_WIDTH),
    .USE_MACRO(USE_SRAM_MACRO)
  ) seen_bank (
    .clk, .read_enable_i(seen_read_enable),
    .read_address_i(seen_read_address), .read_valid_o(seen_read_valid),
    .read_data_o(seen_read_data), .write_enable_i(seen_write_enable),
    .write_address_i(seen_write_address), .write_data_i(seen_write_data)
  );

  actor_local_state_sram #(
    .DATA_WIDTH(ADDRESS_WIDTH), .DEPTH(MAX_EVENTS),
    .ADDRESS_WIDTH(QUEUE_ADDRESS_WIDTH), .USE_MACRO(USE_SRAM_MACRO)
  ) event_queue (
    .clk, .read_enable_i(queue_read_enable),
    .read_address_i(queue_read_address), .read_valid_o(queue_read_valid),
    .read_data_o(queue_read_data), .write_enable_i(queue_write_enable),
    .write_address_i(queue_write_address), .write_data_i(queue_write_data)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= SCRUB;
      scrub_address_reg <= '0;
      event_count_reg <= '0;
      drain_index_reg <= '0;
      completion0_seen_reg <= 1'b0;
      completion1_seen_reg <= 1'b0;
      completion0_tag_reg <= '0;
      completion1_tag_reg <= '0;
      lookup_address_reg <= '0;
      drain_address_reg <= '0;
      overflow_o <= 1'b0;
      tag_mismatch_o <= 1'b0;
    end else begin
      case (state_reg)
        SCRUB: begin
          if (scrub_address_reg + 1'b1 >= ADDRESS_COUNT) begin
            scrub_address_reg <= '0;
            state_reg <= COLLECT;
          end else begin
            scrub_address_reg <= scrub_address_reg + 1'b1;
          end
        end
        COLLECT: begin
          if ((select0 || select1) && (in0_ready || in1_ready)) begin
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
            end else if (!selected_address_valid || event_count_reg >= MAX_EVENTS) begin
              overflow_o <= 1'b1;
            end else begin
              lookup_address_reg <= selected_linear_address[ADDRESS_WIDTH-1:0];
              state_reg <= LOOKUP;
            end
          end
          if (completion0_seen_reg && completion1_seen_reg) begin
            if (completion0_tag_reg != completion1_tag_reg)
              tag_mismatch_o <= 1'b1;
            else begin
              drain_index_reg <= '0;
              state_reg <= event_count_reg == 0 ? EMIT_DONE : DRAIN_READ;
            end
          end
        end
        LOOKUP: if (seen_read_valid) begin
          if (!seen_read_data)
            event_count_reg <= event_count_reg + 1'b1;
          state_reg <= COLLECT;
        end
        DRAIN_READ: state_reg <= DRAIN_CAPTURE;
        DRAIN_CAPTURE: if (queue_read_valid) begin
          drain_address_reg <= queue_read_data;
          state_reg <= DRAIN_OUTPUT;
        end
        DRAIN_OUTPUT: if (out_valid && out_ready) begin
          if (drain_index_reg + 1'b1 >= event_count_reg)
            state_reg <= EMIT_DONE;
          else begin
            drain_index_reg <= drain_index_reg + 1'b1;
            state_reg <= DRAIN_READ;
          end
        end
        EMIT_DONE: if (out_valid && out_ready) begin
          state_reg <= COLLECT;
          event_count_reg <= '0;
          drain_index_reg <= '0;
          completion0_seen_reg <= 1'b0;
          completion1_seen_reg <= 1'b0;
        end
        default: state_reg <= SCRUB;
      endcase
    end
  end
endmodule
