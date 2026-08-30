`timescale 1ns/1ps
// SRAM-transactional PLIF actor for populations without retinotopic mechanisms.
// One packed state word is owned by each logical neuron. A second narrow SRAM
// records first-touch order, so epoch commit never scans the dense population.
module asynchronous_plif_actor_sram #(
  parameter integer ADDRESS_WIDTH = 8,
  parameter integer DEST_COUNT = 16,
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer COUNT_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT + 1),
  parameter integer QUEUE_ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer CHANNEL_COUNT = 1,
  parameter integer SPATIAL_DEST_COUNT = DEST_COUNT,
  parameter integer USE_CHANNEL_PARAMETERS = 0,
  parameter integer USE_SRAM_MACRO = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0
) (
  input logic clk,
  input logic reset,
  input logic contribution_valid,
  output logic contribution_ready,
  input logic [ADDRESS_WIDTH-1:0] destination_i,
  input logic signed [WEIGHT_WIDTH-1:0] weight_i,
  input logic epoch_end_valid,
  output logic epoch_end_ready,
  input logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  input logic [BETA_WIDTH-1:0] beta_i,
  input logic signed [MEM_WIDTH-1:0] threshold_i,
  output logic spike_valid,
  input logic spike_ready,
  output logic [ADDRESS_WIDTH-1:0] spike_destination_o,
  output logic epoch_done_valid,
  input logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic address_error_o
);
  localparam integer CURRENT_LSB = 0;
  localparam integer MEMBRANE_LSB = CURRENT_LSB + CURRENT_WIDTH;
  localparam integer TAG_LSB = MEMBRANE_LSB + MEM_WIDTH;
  localparam integer LIVE_BIT = TAG_LSB + EPOCH_TAG_WIDTH;
  localparam integer TOUCHED_BIT = LIVE_BIT + 1;
  localparam integer STATE_WIDTH = TOUCHED_BIT + 1;
  localparam signed [CURRENT_WIDTH:0] MAX_CURRENT =
    (1 <<< (CURRENT_WIDTH - 1)) - 1;
  localparam signed [CURRENT_WIDTH:0] MIN_CURRENT =
    -(1 <<< (CURRENT_WIDTH - 1));
  localparam [3:0] SCRUB = 4'd0, COLLECT = 4'd1,
    CONTRIBUTION_WAIT = 4'd2, QUEUE_READ = 4'd3,
    QUEUE_CAPTURE = 4'd4, STATE_READ = 4'd5, STATE_CAPTURE = 4'd6,
    PLIF_ISSUE = 4'd7, PLIF_WAIT = 4'd8, HOLD_SPIKE = 4'd9,
    HOLD_EPOCH_DONE = 4'd10;

  logic [3:0] state_reg;
  logic [ADDRESS_WIDTH-1:0] scrub_address_reg;
  logic [ADDRESS_WIDTH-1:0] destination_reg;
  logic signed [WEIGHT_WIDTH-1:0] contribution_weight_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic [EPOCH_TAG_WIDTH-1:0] elapsed_reg;
  logic signed [MEM_WIDTH-1:0] plif_membrane_in;
  logic signed [CURRENT_WIDTH-1:0] plif_current_in;
  logic address_error_reg;

  logic state_read_enable;
  logic [ADDRESS_WIDTH-1:0] state_read_address;
  logic state_read_valid;
  logic [STATE_WIDTH-1:0] state_read_data;
  logic state_write_enable;
  logic [ADDRESS_WIDTH-1:0] state_write_address;
  logic [STATE_WIDTH-1:0] state_write_data;
  logic queue_read_enable;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_read_address;
  logic queue_read_valid;
  logic [ADDRESS_WIDTH-1:0] queue_read_data;
  logic queue_write_enable;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_write_address;
  logic [ADDRESS_WIDTH-1:0] queue_write_data;

  logic plif_in_valid;
  logic plif_in_ready;
  logic plif_out_valid;
  logic plif_out_ready;
  logic signed [MEM_WIDTH-1:0] plif_candidate;
  logic signed [MEM_WIDTH-1:0] plif_membrane;
  logic plif_spike;
  logic [BETA_WIDTH-1:0] selected_beta;
  logic signed [MEM_WIDTH-1:0] selected_threshold;
  logic signed [CURRENT_WIDTH:0] contribution_sum;
  logic signed [CURRENT_WIDTH-1:0] saturated_contribution_sum;
  integer parameter_channel;

  assign contribution_ready = state_reg == COLLECT && !epoch_end_valid;
  assign epoch_end_ready = state_reg == COLLECT;
  assign spike_valid = state_reg == HOLD_SPIKE;
  assign epoch_done_valid = state_reg == HOLD_EPOCH_DONE;
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg;
  assign plif_in_valid = state_reg == PLIF_ISSUE;
  assign plif_out_ready = state_reg == PLIF_WAIT;

  initial begin
    if (USE_CHANNEL_PARAMETERS && DEST_COUNT != CHANNEL_COUNT * SPATIAL_DEST_COUNT)
      $error("channelized destination geometry does not match DEST_COUNT");
  end

  always_comb begin
    parameter_channel = $unsigned(destination_reg) / SPATIAL_DEST_COUNT;
    if (USE_CHANNEL_PARAMETERS) begin
      selected_beta = CHANNEL_BETAS[parameter_channel*BETA_WIDTH +: BETA_WIDTH];
      selected_threshold =
        CHANNEL_THRESHOLDS[parameter_channel*MEM_WIDTH +: MEM_WIDTH];
    end else begin
      selected_beta = beta_i;
      selected_threshold = threshold_i;
    end

    contribution_sum =
      $signed(state_read_data[CURRENT_LSB +: CURRENT_WIDTH]) +
      $signed(contribution_weight_reg);
    if (contribution_sum > MAX_CURRENT)
      saturated_contribution_sum = MAX_CURRENT[CURRENT_WIDTH-1:0];
    else if (contribution_sum < MIN_CURRENT)
      saturated_contribution_sum = MIN_CURRENT[CURRENT_WIDTH-1:0];
    else
      saturated_contribution_sum = contribution_sum[CURRENT_WIDTH-1:0];

    state_read_enable = 1'b0;
    state_read_address = destination_reg;
    if (state_reg == COLLECT && contribution_valid && contribution_ready &&
        $unsigned(destination_i) < DEST_COUNT) begin
      state_read_enable = 1'b1;
      state_read_address = destination_i;
    end else if (state_reg == STATE_READ) begin
      state_read_enable = 1'b1;
    end

    state_write_enable = 1'b0;
    state_write_address = destination_reg;
    state_write_data = state_read_data;
    if (state_reg == SCRUB) begin
      state_write_enable = 1'b1;
      state_write_address = scrub_address_reg;
      state_write_data = '0;
    end else if (state_reg == CONTRIBUTION_WAIT && state_read_valid) begin
      state_write_enable = 1'b1;
      state_write_data[CURRENT_LSB +: CURRENT_WIDTH] = saturated_contribution_sum;
      state_write_data[TOUCHED_BIT] = 1'b1;
    end else if (state_reg == PLIF_WAIT && plif_out_valid) begin
      state_write_enable = 1'b1;
      state_write_data = '0;
      state_write_data[MEMBRANE_LSB +: MEM_WIDTH] = plif_membrane;
      state_write_data[TAG_LSB +: EPOCH_TAG_WIDTH] = epoch_tag_reg;
      state_write_data[LIVE_BIT] = plif_membrane != 0;
    end

    queue_write_enable = state_reg == CONTRIBUTION_WAIT && state_read_valid &&
                         !state_read_data[TOUCHED_BIT];
    queue_write_address = touched_count_reg[QUEUE_ADDRESS_WIDTH-1:0];
    queue_write_data = destination_reg;
    queue_read_enable = state_reg == QUEUE_READ;
    queue_read_address = commit_index_reg[QUEUE_ADDRESS_WIDTH-1:0];
  end

  actor_local_state_sram #(
    .DATA_WIDTH(STATE_WIDTH), .DEPTH(DEST_COUNT), .ADDRESS_WIDTH(ADDRESS_WIDTH),
    .USE_MACRO(USE_SRAM_MACRO)
  ) state_bank (
    .clk, .read_enable_i(state_read_enable), .read_address_i(state_read_address),
    .read_valid_o(state_read_valid), .read_data_o(state_read_data),
    .write_enable_i(state_write_enable), .write_address_i(state_write_address),
    .write_data_i(state_write_data)
  );

  actor_local_state_sram #(
    .DATA_WIDTH(ADDRESS_WIDTH), .DEPTH(DEST_COUNT),
    .ADDRESS_WIDTH(QUEUE_ADDRESS_WIDTH), .USE_MACRO(USE_SRAM_MACRO)
  ) touched_queue (
    .clk, .read_enable_i(queue_read_enable), .read_address_i(queue_read_address),
    .read_valid_o(queue_read_valid), .read_data_o(queue_read_data),
    .write_enable_i(queue_write_enable), .write_address_i(queue_write_address),
    .write_data_i(queue_write_data)
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
      state_reg <= SCRUB;
      scrub_address_reg <= '0;
      destination_reg <= '0;
      contribution_weight_reg <= '0;
      commit_index_reg <= '0;
      touched_count_reg <= '0;
      epoch_tag_reg <= '0;
      elapsed_reg <= '0;
      plif_membrane_in <= '0;
      plif_current_in <= '0;
      address_error_reg <= 1'b0;
      spike_destination_o <= '0;
    end else begin
      case (state_reg)
        SCRUB: begin
          if (scrub_address_reg + 1'b1 >= DEST_COUNT) begin
            scrub_address_reg <= '0;
            state_reg <= COLLECT;
          end else scrub_address_reg <= scrub_address_reg + 1'b1;
        end
        COLLECT: begin
          if (epoch_end_valid) begin
            epoch_tag_reg <= epoch_tag_i;
            commit_index_reg <= '0;
            state_reg <= touched_count_reg == 0 ? HOLD_EPOCH_DONE : QUEUE_READ;
          end else if (contribution_valid) begin
            if ($unsigned(destination_i) < DEST_COUNT) begin
              destination_reg <= destination_i;
              contribution_weight_reg <= weight_i;
              state_reg <= CONTRIBUTION_WAIT;
            end else address_error_reg <= 1'b1;
          end
        end
        CONTRIBUTION_WAIT: if (state_read_valid) begin
          if (!state_read_data[TOUCHED_BIT])
            touched_count_reg <= touched_count_reg + 1'b1;
          state_reg <= COLLECT;
        end
        QUEUE_READ: state_reg <= QUEUE_CAPTURE;
        QUEUE_CAPTURE: if (queue_read_valid) begin
          destination_reg <= queue_read_data;
          state_reg <= STATE_READ;
        end
        STATE_READ: state_reg <= STATE_CAPTURE;
        STATE_CAPTURE: if (state_read_valid) begin
          plif_current_in <= state_read_data[CURRENT_LSB +: CURRENT_WIDTH];
          if (state_read_data[LIVE_BIT]) begin
            plif_membrane_in <= state_read_data[MEMBRANE_LSB +: MEM_WIDTH];
            elapsed_reg <= epoch_tag_reg -
                           state_read_data[TAG_LSB +: EPOCH_TAG_WIDTH];
          end else begin
            plif_membrane_in <= '0;
            elapsed_reg <= {{(EPOCH_TAG_WIDTH-1){1'b0}}, 1'b1};
          end
          state_reg <= PLIF_ISSUE;
        end
        PLIF_ISSUE: if (plif_in_ready) state_reg <= PLIF_WAIT;
        PLIF_WAIT: if (plif_out_valid) begin
          if (plif_spike) begin
            spike_destination_o <= destination_reg;
            state_reg <= HOLD_SPIKE;
          end else if (commit_index_reg + 1'b1 >= touched_count_reg)
            state_reg <= HOLD_EPOCH_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_READ;
          end
        end
        HOLD_SPIKE: if (spike_ready) begin
          if (commit_index_reg + 1'b1 >= touched_count_reg)
            state_reg <= HOLD_EPOCH_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_READ;
          end
        end
        HOLD_EPOCH_DONE: if (epoch_done_ready) begin
          touched_count_reg <= '0;
          address_error_reg <= 1'b0;
          state_reg <= COLLECT;
        end
        default: state_reg <= SCRUB;
      endcase
    end
  end
endmodule
