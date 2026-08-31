`timescale 1ns/1ps
module asynchronous_plif_actor #(
  parameter integer ADDRESS_WIDTH   = 8,
  parameter integer DEST_COUNT      = 16,
  parameter integer MEM_WIDTH       = 16,
  parameter integer CURRENT_WIDTH   = 24,
  parameter integer WEIGHT_WIDTH    = 8,
  parameter integer BETA_WIDTH      = 16,
  parameter integer BETA_FRAC_BITS  = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer COUNT_WIDTH     = $clog2(DEST_COUNT + 1),
  parameter integer CHANNEL_COUNT   = 1,
  parameter integer SPATIAL_DEST_COUNT = DEST_COUNT,
  parameter integer USE_CHANNEL_PARAMETERS = 0,
  parameter integer USE_STATE_MACRO = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic contribution_valid,
  output logic contribution_ready,
  input  logic [ADDRESS_WIDTH-1:0] destination_i,
  input  logic signed [WEIGHT_WIDTH-1:0] weight_i,
  input  logic epoch_end_valid,
  output logic epoch_end_ready,
  input  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  input  logic [BETA_WIDTH-1:0] beta_i,
  input  logic signed [MEM_WIDTH-1:0] threshold_i,
  output logic spike_valid,
  input  logic spike_ready,
  output logic [ADDRESS_WIDTH-1:0] spike_destination_o,
  output logic epoch_done_valid,
  input  logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic address_error_o,
  output logic initialization_done_o
);
  localparam [3:0] COLLECT = 4'd0, CONTRIBUTION_WAIT = 4'd1,
                   CONTRIBUTION_WRITE = 4'd2, LOAD_TOUCHED_ISSUE = 4'd3,
                   LOAD_TOUCHED_WAIT = 4'd4, PLIF_ISSUE = 4'd5,
                   PLIF_WAIT = 4'd6, COMMIT_WRITE = 4'd7,
                   HOLD_SPIKE = 4'd8, HOLD_EPOCH_DONE = 4'd9,
                   QUEUE_WAIT = 4'd10;
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH - 1)) - 1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH - 1));
  localparam integer CURRENT_LSB = 0;
  localparam integer MEMBRANE_LSB = CURRENT_WIDTH;
  localparam integer TAG_LSB = MEMBRANE_LSB + MEM_WIDTH;
  localparam integer LIVE_BIT = TAG_LSB + EPOCH_TAG_WIDTH;
  localparam integer TOUCHED_BIT = LIVE_BIT + 1;
  localparam integer STATE_WIDTH = TOUCHED_BIT + 1;
  localparam integer QUEUE_ADDRESS_WIDTH =
    (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT);

  logic [3:0] state_reg;
  logic [ADDRESS_WIDTH-1:0] destination_reg;
  logic signed [WEIGHT_WIDTH-1:0] contribution_weight_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic [EPOCH_TAG_WIDTH-1:0] elapsed_reg;
  logic signed [MEM_WIDTH-1:0] plif_membrane_in;
  logic signed [CURRENT_WIDTH-1:0] plif_current_in;
  logic signed [MEM_WIDTH-1:0] result_membrane_reg;
  logic result_spike_reg;
  logic address_error_reg;

  logic state_initialization_done;
  logic state_read_valid;
  logic state_read_ready;
  logic [ADDRESS_WIDTH-1:0] state_read_address;
  logic state_read_response_valid;
  logic [STATE_WIDTH-1:0] state_read_data;
  logic state_write_valid;
  logic state_write_ready;
  logic [STATE_WIDTH-1:0] state_write_data;
  logic [STATE_WIDTH-1:0] contribution_write_data_reg;
  logic state_request_conflict;
  logic queue_initialization_done;
  logic queue_read_enable;
  logic queue_read_ready;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_read_address;
  logic queue_read_valid;
  logic [ADDRESS_WIDTH-1:0] queue_read_data;
  logic queue_write_enable;
  logic queue_write_ready;
  logic queue_request_conflict;

  logic plif_in_valid;
  logic plif_in_ready;
  logic plif_out_valid;
  logic plif_out_ready;
  logic signed [MEM_WIDTH-1:0] plif_candidate;
  logic signed [MEM_WIDTH-1:0] plif_membrane;
  logic plif_spike;
  logic [BETA_WIDTH-1:0] selected_beta;
  logic signed [MEM_WIDTH-1:0] selected_threshold;
  integer destination_index;
  integer parameter_channel;
  integer signed sum_value;

  assign contribution_ready = state_initialization_done && queue_initialization_done &&
                              (state_reg == COLLECT) && !epoch_end_valid;
  assign epoch_end_ready = state_initialization_done && queue_initialization_done &&
                           (state_reg == COLLECT);
  assign spike_valid = (state_reg == HOLD_SPIKE);
  assign epoch_done_valid = (state_reg == HOLD_EPOCH_DONE);
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg || state_request_conflict ||
                           queue_request_conflict;
  assign initialization_done_o = state_initialization_done &&
                                 queue_initialization_done;
  assign plif_in_valid = (state_reg == PLIF_ISSUE);
  assign plif_out_ready = (state_reg == PLIF_WAIT);

  assign state_read_valid =
    ((state_reg == COLLECT) && contribution_valid && contribution_ready &&
     ($unsigned(destination_i) < DEST_COUNT)) ||
    (state_reg == LOAD_TOUCHED_ISSUE);
  assign state_read_address = (state_reg == LOAD_TOUCHED_ISSUE) ?
                              destination_reg : destination_i;
  assign state_write_valid = (state_reg == CONTRIBUTION_WRITE) ||
                             (state_reg == COMMIT_WRITE);
  assign state_write_data = (state_reg == CONTRIBUTION_WRITE) ?
                            contribution_write_data_reg :
                            {1'b0, (result_membrane_reg != 0), epoch_tag_reg,
                             result_membrane_reg, {CURRENT_WIDTH{1'b0}}};
  assign queue_write_enable = (state_reg == CONTRIBUTION_WAIT) &&
                              state_read_response_valid &&
                              !state_read_data[TOUCHED_BIT];
  assign queue_read_enable =
    ((state_reg == COLLECT) && epoch_end_valid && epoch_end_ready &&
     (touched_count_reg != 0)) ||
    ((state_reg == COMMIT_WRITE) && state_write_ready && !result_spike_reg &&
     ((commit_index_reg + 1'b1) < touched_count_reg)) ||
    ((state_reg == HOLD_SPIKE) && spike_ready &&
     ((commit_index_reg + 1'b1) < touched_count_reg));
  assign queue_read_address = (state_reg == COLLECT) ? '0 :
                              (commit_index_reg + 1'b1);

  initial begin
    if (USE_CHANNEL_PARAMETERS && DEST_COUNT != CHANNEL_COUNT * SPATIAL_DEST_COUNT)
      $error("channelized destination geometry does not match DEST_COUNT");
  end

  always_comb begin
    parameter_channel = $unsigned(destination_reg) / SPATIAL_DEST_COUNT;
    if (USE_CHANNEL_PARAMETERS) begin
      selected_beta = CHANNEL_BETAS[parameter_channel*BETA_WIDTH +: BETA_WIDTH];
      selected_threshold = CHANNEL_THRESHOLDS[
        parameter_channel*MEM_WIDTH +: MEM_WIDTH
      ];
    end else begin
      selected_beta = beta_i;
      selected_threshold = threshold_i;
    end
  end

  initialized_actor_state_bank #(
    .DATA_WIDTH(STATE_WIDTH), .DEPTH(DEST_COUNT),
    .ADDRESS_WIDTH(ADDRESS_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) state_bank (
    .clk, .reset, .initialization_done_o(state_initialization_done),
    .read_valid_i(state_read_valid), .read_ready_o(state_read_ready),
    .read_address_i(state_read_address),
    .read_response_valid_o(state_read_response_valid), .read_data_o(state_read_data),
    .write_valid_i(state_write_valid), .write_ready_o(state_write_ready),
    .write_address_i(destination_reg), .write_data_i(state_write_data),
    .request_conflict_o(state_request_conflict)
  );

  initialized_actor_state_bank #(
    .DATA_WIDTH(ADDRESS_WIDTH), .DEPTH(DEST_COUNT),
    .ADDRESS_WIDTH(QUEUE_ADDRESS_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) touched_queue_bank (
    .clk, .reset, .initialization_done_o(queue_initialization_done),
    .read_valid_i(queue_read_enable), .read_ready_o(queue_read_ready),
    .read_address_i(queue_read_address),
    .read_response_valid_o(queue_read_valid), .read_data_o(queue_read_data),
    .write_valid_i(queue_write_enable), .write_ready_o(queue_write_ready),
    .write_address_i(touched_count_reg[QUEUE_ADDRESS_WIDTH-1:0]),
    .write_data_i(destination_reg), .request_conflict_o(queue_request_conflict)
  );

  plif_update #(
    .MEM_WIDTH(MEM_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH), .BETA_WIDTH(BETA_WIDTH),
    .BETA_FRAC_BITS(BETA_FRAC_BITS), .DELTA_WIDTH(EPOCH_TAG_WIDTH)
  ) updater (
    .clk, .reset, .in_valid(plif_in_valid), .in_ready(plif_in_ready),
    .membrane_i(plif_membrane_in), .current_i(plif_current_in),
    .beta_i(selected_beta), .threshold_i(selected_threshold),
    .elapsed_bins_i(elapsed_reg), .out_valid(plif_out_valid),
    .out_ready(plif_out_ready), .candidate_o(plif_candidate),
    .membrane_o(plif_membrane), .spike_o(plif_spike)
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      destination_reg <= '0;
      contribution_weight_reg <= '0;
      commit_index_reg <= '0;
      touched_count_reg <= '0;
      epoch_tag_reg <= '0;
      elapsed_reg <= '0;
      plif_membrane_in <= '0;
      plif_current_in <= '0;
      result_membrane_reg <= '0;
      result_spike_reg <= 1'b0;
      contribution_write_data_reg <= '0;
      address_error_reg <= 1'b0;
      spike_destination_o <= '0;
    end else begin
      case (state_reg)
        COLLECT: begin
          if (epoch_end_valid && epoch_end_ready) begin
            epoch_tag_reg <= epoch_tag_i;
            commit_index_reg <= '0;
            if (touched_count_reg == 0)
              state_reg <= HOLD_EPOCH_DONE;
            else state_reg <= QUEUE_WAIT;
          end else if (contribution_valid && contribution_ready) begin
            destination_index = $unsigned(destination_i);
            if (destination_index < DEST_COUNT) begin
              destination_reg <= destination_i;
              contribution_weight_reg <= weight_i;
              if (state_read_ready)
                state_reg <= CONTRIBUTION_WAIT;
            end else begin
              address_error_reg <= 1'b1;
            end
          end
        end
        CONTRIBUTION_WAIT: if (state_read_response_valid) begin
          sum_value = $signed(state_read_data[CURRENT_LSB +: CURRENT_WIDTH]) +
                      $signed(contribution_weight_reg);
          contribution_write_data_reg <= state_read_data;
          if (sum_value > MAX_CURRENT)
            contribution_write_data_reg[CURRENT_LSB +: CURRENT_WIDTH] <= MAX_CURRENT;
          else if (sum_value < MIN_CURRENT)
            contribution_write_data_reg[CURRENT_LSB +: CURRENT_WIDTH] <= MIN_CURRENT;
          else
            contribution_write_data_reg[CURRENT_LSB +: CURRENT_WIDTH] <=
              sum_value[CURRENT_WIDTH-1:0];
          contribution_write_data_reg[TOUCHED_BIT] <= 1'b1;
          if (!state_read_data[TOUCHED_BIT])
            touched_count_reg <= touched_count_reg + 1'b1;
          state_reg <= CONTRIBUTION_WRITE;
        end
        CONTRIBUTION_WRITE: if (state_write_ready) state_reg <= COLLECT;
        QUEUE_WAIT: if (queue_read_valid) begin
          destination_reg <= queue_read_data;
          state_reg <= LOAD_TOUCHED_ISSUE;
        end
        LOAD_TOUCHED_ISSUE: if (state_read_ready) state_reg <= LOAD_TOUCHED_WAIT;
        LOAD_TOUCHED_WAIT: if (state_read_response_valid) begin
          plif_current_in <= state_read_data[CURRENT_LSB +: CURRENT_WIDTH];
          if (state_read_data[LIVE_BIT]) begin
            plif_membrane_in <= state_read_data[MEMBRANE_LSB +: MEM_WIDTH];
            elapsed_reg <= epoch_tag_reg - state_read_data[TAG_LSB +: EPOCH_TAG_WIDTH];
          end else begin
            plif_membrane_in <= '0;
            elapsed_reg <= {{(EPOCH_TAG_WIDTH-1){1'b0}}, 1'b1};
          end
          state_reg <= PLIF_ISSUE;
        end
        PLIF_ISSUE: if (plif_in_ready) state_reg <= PLIF_WAIT;
        PLIF_WAIT: if (plif_out_valid) begin
          result_membrane_reg <= plif_membrane;
          result_spike_reg <= plif_spike;
          state_reg <= COMMIT_WRITE;
        end
        COMMIT_WRITE: if (state_write_ready) begin
          if (result_spike_reg) begin
            spike_destination_o <= destination_reg;
            state_reg <= HOLD_SPIKE;
          end else if ((commit_index_reg + 1'b1) >= touched_count_reg) begin
            state_reg <= HOLD_EPOCH_DONE;
          end else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_WAIT;
          end
        end
        HOLD_SPIKE: if (spike_ready) begin
          if ((commit_index_reg + 1'b1) >= touched_count_reg)
            state_reg <= HOLD_EPOCH_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_WAIT;
          end
        end
        HOLD_EPOCH_DONE: if (epoch_done_ready) begin
          touched_count_reg <= '0;
          address_error_reg <= 1'b0;
          state_reg <= COLLECT;
        end
        default: state_reg <= COLLECT;
      endcase
    end
  end
endmodule
