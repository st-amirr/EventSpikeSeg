`timescale 1ns/1ps
// Mechanism-enabled actor with direct-indexed actor-local SRAM state.
// Contributions update one channel destination at a time; completion loads and
// commits every channel at each queued retinotopic location as one atomic group.
module retinotopic_asynchronous_plif_actor #(
  parameter integer ADDRESS_WIDTH = 8,
  parameter integer CHANNEL_COUNT = 4,
  parameter integer SPATIAL_DEST_COUNT = 16,
  parameter integer DEST_COUNT = CHANNEL_COUNT * SPATIAL_DEST_COUNT,
  parameter integer SPATIAL_WIDTH =
    (SPATIAL_DEST_COUNT <= 1) ? 1 : $clog2(SPATIAL_DEST_COUNT),
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 16,
  parameter integer COUNT_WIDTH = $clog2(SPATIAL_DEST_COUNT + 1),
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer USE_STATE_MACRO = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [AGE_WIDTH-1:0] ADAPTATION_DURATION = '0
) (
  input logic clk, input logic reset,
  input logic contribution_valid, output logic contribution_ready,
  input logic [ADDRESS_WIDTH-1:0] destination_i,
  input logic signed [WEIGHT_WIDTH-1:0] weight_i,
  input logic epoch_end_valid, output logic epoch_end_ready,
  input logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_i,
  output logic spike_valid, input logic spike_ready,
  output logic [ADDRESS_WIDTH-1:0] spike_destination_o,
  output logic epoch_done_valid, input logic epoch_done_ready,
  output logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_o,
  output logic address_error_o,
  output logic initialization_done_o
);
  localparam [3:0] COLLECT = 4'd0, CONTRIBUTION_STATE_WAIT = 4'd1,
                   CONTRIBUTION_STATE_WRITE = 4'd2,
                   CONTRIBUTION_SPATIAL_ISSUE = 4'd3,
                   CONTRIBUTION_SPATIAL_WAIT = 4'd4,
                   CONTRIBUTION_SPATIAL_WRITE = 4'd5,
                   GROUP_READ_ISSUE = 4'd6, GROUP_READ_WAIT = 4'd7,
                   LEAK_ISSUE = 4'd8, LEAK_WAIT = 4'd9,
                   GROUP_WRITE = 4'd10, SPATIAL_CLEAR = 4'd11,
                   EMIT_SPIKES = 4'd12, HOLD_DONE = 4'd13,
                   QUEUE_WAIT = 4'd14;
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH-1)) - 1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH-1));
  localparam [AGE_WIDTH-1:0] INACTIVE_AGE = {AGE_WIDTH{1'b1}};
  localparam integer CURRENT_LSB = 0;
  localparam integer MEMBRANE_LSB = CURRENT_WIDTH;
  localparam integer TAG_LSB = MEMBRANE_LSB + MEM_WIDTH;
  localparam integer AGE_STORAGE_WIDTH = ENABLE_ADAPTATION ? AGE_WIDTH : 1;
  localparam integer AMPLITUDE_STORAGE_WIDTH = ENABLE_ADAPTATION ? MEM_WIDTH : 1;
  localparam integer AGE_LSB = TAG_LSB + EPOCH_TAG_WIDTH;
  localparam integer AMPLITUDE_LSB = AGE_LSB + AGE_STORAGE_WIDTH;
  localparam integer LIVE_BIT = AMPLITUDE_LSB + AMPLITUDE_STORAGE_WIDTH;
  localparam integer TOUCHED_BIT = LIVE_BIT + 1;
  localparam integer STATE_WIDTH = TOUCHED_BIT + 1;
  localparam integer CHANNEL_INDEX_WIDTH =
    (CHANNEL_COUNT <= 1) ? 1 : $clog2(CHANNEL_COUNT);

  logic [3:0] state_reg;
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [CHANNEL_INDEX_WIDTH-1:0] group_channel_reg;
  logic [ADDRESS_WIDTH-1:0] destination_reg;
  logic [SPATIAL_WIDTH-1:0] spatial_reg;
  logic signed [WEIGHT_WIDTH-1:0] contribution_weight_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic address_error_reg;

  logic state_initialization_done;
  logic state_read_valid, state_read_ready, state_read_response_valid;
  logic [ADDRESS_WIDTH-1:0] state_read_address;
  logic [STATE_WIDTH-1:0] state_read_data;
  logic state_write_valid, state_write_ready;
  logic [ADDRESS_WIDTH-1:0] state_write_address;
  logic [STATE_WIDTH-1:0] state_write_data;
  logic [STATE_WIDTH-1:0] contribution_write_data_reg;
  logic state_request_conflict;

  logic spatial_initialization_done;
  logic spatial_read_valid, spatial_read_ready, spatial_read_response_valid;
  logic [SPATIAL_WIDTH-1:0] spatial_read_address;
  logic [0:0] spatial_read_data;
  logic spatial_write_valid, spatial_write_ready;
  logic [0:0] spatial_write_data;
  logic spatial_request_conflict;
  logic queue_initialization_done;
  logic queue_read_enable, queue_read_ready, queue_read_valid, queue_write_enable;
  logic queue_write_ready, queue_request_conflict;
  logic [SPATIAL_WIDTH-1:0] queue_read_address, queue_read_data;

  logic [CHANNEL_COUNT-1:0] update_mask_reg;
  logic [CHANNEL_COUNT-1:0] loaded_live_reg;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] loaded_membranes_reg;
  logic [CHANNEL_COUNT*EPOCH_TAG_WIDTH-1:0] loaded_tags_reg;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] loaded_ages_reg;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] loaded_amplitudes_reg;
  logic signed [CHANNEL_COUNT*CURRENT_WIDTH-1:0] leak_currents_reg;
  logic [CHANNEL_COUNT*EPOCH_TAG_WIDTH-1:0] elapsed_bins_reg;
  logic [CHANNEL_COUNT-1:0] leak_in_ready;
  logic [CHANNEL_COUNT-1:0] leak_out_valid;
  logic [CHANNEL_COUNT-1:0] leak_out_ready;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] candidates;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] result_membranes_reg;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] result_ages_reg;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] result_amplitudes_reg;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_membranes;
  logic [CHANNEL_COUNT-1:0] mechanism_spikes;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] mechanism_ages;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_amplitudes;
  logic [CHANNEL_COUNT-1:0] spike_pending_reg;

  integer selected_channel;
  integer destination_index;
  integer spatial_index;
  integer channel;
  integer signed sum_value;
  logic selected_live;
  logic signed [MEM_WIDTH-1:0] selected_membrane;
  logic [EPOCH_TAG_WIDTH-1:0] selected_tag;
  logic [AGE_WIDTH-1:0] selected_age;
  logic [MEM_WIDTH-1:0] selected_amplitude;
  logic [AGE_STORAGE_WIDTH-1:0] stored_age;
  logic [AMPLITUDE_STORAGE_WIDTH-1:0] stored_amplitude;

  assign contribution_ready = state_initialization_done && spatial_initialization_done &&
                              queue_initialization_done &&
                              (state_reg == COLLECT) && !epoch_end_valid;
  assign epoch_end_ready = state_initialization_done && spatial_initialization_done &&
                           queue_initialization_done &&
                           (state_reg == COLLECT);
  assign spike_valid = (state_reg == EMIT_SPIKES) && (spike_pending_reg != 0);
  assign epoch_done_valid = (state_reg == HOLD_DONE);
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg || state_request_conflict ||
                           spatial_request_conflict || queue_request_conflict;
  assign initialization_done_o = state_initialization_done &&
                                 spatial_initialization_done &&
                                 queue_initialization_done;
  assign leak_out_ready = {CHANNEL_COUNT{state_reg == LEAK_WAIT && &leak_out_valid}};

  assign state_read_valid =
    ((state_reg == COLLECT) && contribution_valid && contribution_ready &&
     ($unsigned(destination_i) < DEST_COUNT)) ||
    (state_reg == GROUP_READ_ISSUE);
  assign state_read_address = (state_reg == GROUP_READ_ISSUE) ?
    (group_channel_reg*SPATIAL_DEST_COUNT + spatial_reg) : destination_i;
  assign state_write_valid = (state_reg == CONTRIBUTION_STATE_WRITE) ||
                             (state_reg == GROUP_WRITE);
  assign state_write_address = (state_reg == GROUP_WRITE) ?
    (group_channel_reg*SPATIAL_DEST_COUNT + spatial_reg) : destination_reg;

  assign spatial_read_valid = (state_reg == CONTRIBUTION_SPATIAL_ISSUE);
  assign spatial_read_address = spatial_reg;
  assign spatial_write_valid = (state_reg == CONTRIBUTION_SPATIAL_WRITE) ||
                               (state_reg == SPATIAL_CLEAR);
  assign spatial_write_data = (state_reg == CONTRIBUTION_SPATIAL_WRITE) ? 1'b1 : 1'b0;
  assign queue_write_enable = (state_reg == CONTRIBUTION_SPATIAL_WAIT) &&
                              spatial_read_response_valid && !spatial_read_data[0];
  assign queue_read_enable =
    ((state_reg == COLLECT) && epoch_end_valid && epoch_end_ready &&
     (touched_count_reg != 0)) ||
    ((state_reg == SPATIAL_CLEAR) && spatial_write_ready &&
     (spike_pending_reg == 0) &&
     ((commit_index_reg + 1'b1) < touched_count_reg)) ||
    ((state_reg == EMIT_SPIKES) && spike_valid && spike_ready &&
     ((spike_pending_reg & ~(1'b1 << selected_channel)) == 0) &&
     ((commit_index_reg + 1'b1) < touched_count_reg));
  assign queue_read_address = (state_reg == COLLECT) ? '0 :
                              (commit_index_reg + 1'b1);

  always_comb begin
    selected_channel = 0;
    for (channel = CHANNEL_COUNT-1; channel >= 0; channel = channel-1)
      if (spike_pending_reg[channel]) selected_channel = channel;
    spike_destination_o =
      selected_channel*SPATIAL_DEST_COUNT + $unsigned(spatial_reg);

    selected_membrane =
      loaded_membranes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH];
    selected_tag = loaded_tags_reg[group_channel_reg*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH];
    selected_age = loaded_ages_reg[group_channel_reg*AGE_WIDTH +: AGE_WIDTH];
    selected_amplitude =
      loaded_amplitudes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH];
    if (update_mask_reg[group_channel_reg]) begin
      selected_membrane =
        result_membranes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH];
      selected_tag = epoch_tag_reg;
      selected_age = result_ages_reg[group_channel_reg*AGE_WIDTH +: AGE_WIDTH];
      selected_amplitude =
        result_amplitudes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH];
    end
    selected_live = (selected_membrane != 0) ||
                    (selected_age != INACTIVE_AGE) || (selected_amplitude != 0);
    stored_age = (ENABLE_ADAPTATION != 0) ?
                 selected_age[AGE_STORAGE_WIDTH-1:0] : '0;
    stored_amplitude = (ENABLE_ADAPTATION != 0) ?
                       selected_amplitude[AMPLITUDE_STORAGE_WIDTH-1:0] : '0;
    state_write_data = (state_reg == CONTRIBUTION_STATE_WRITE) ?
      contribution_write_data_reg :
      {1'b0, selected_live, stored_amplitude, stored_age, selected_tag,
       selected_membrane, {CURRENT_WIDTH{1'b0}}};
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
    .write_address_i(state_write_address), .write_data_i(state_write_data),
    .request_conflict_o(state_request_conflict)
  );

  initialized_actor_state_bank #(
    .DATA_WIDTH(1), .DEPTH(SPATIAL_DEST_COUNT),
    .ADDRESS_WIDTH(SPATIAL_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) touched_spatial_bank (
    .clk, .reset, .initialization_done_o(spatial_initialization_done),
    .read_valid_i(spatial_read_valid), .read_ready_o(spatial_read_ready),
    .read_address_i(spatial_read_address),
    .read_response_valid_o(spatial_read_response_valid), .read_data_o(spatial_read_data),
    .write_valid_i(spatial_write_valid), .write_ready_o(spatial_write_ready),
    .write_address_i(spatial_reg), .write_data_i(spatial_write_data),
    .request_conflict_o(spatial_request_conflict)
  );

  initialized_actor_state_bank #(
    .DATA_WIDTH(SPATIAL_WIDTH), .DEPTH(SPATIAL_DEST_COUNT),
    .ADDRESS_WIDTH(SPATIAL_WIDTH), .USE_MACRO(USE_STATE_MACRO)
  ) touched_queue_bank (
    .clk, .reset, .initialization_done_o(queue_initialization_done),
    .read_valid_i(queue_read_enable), .read_ready_o(queue_read_ready),
    .read_address_i(queue_read_address),
    .read_response_valid_o(queue_read_valid), .read_data_o(queue_read_data),
    .write_valid_i(queue_write_enable), .write_ready_o(queue_write_ready),
    .write_address_i(touched_count_reg[SPATIAL_WIDTH-1:0]),
    .write_data_i(spatial_reg), .request_conflict_o(queue_request_conflict)
  );

  genvar generated_channel;
  generate for (generated_channel = 0; generated_channel < CHANNEL_COUNT;
                generated_channel = generated_channel + 1) begin : leak_lanes
    plif_leak_charge #(
      .MEM_WIDTH(MEM_WIDTH), .CURRENT_WIDTH(CURRENT_WIDTH),
      .BETA_WIDTH(BETA_WIDTH), .BETA_FRAC_BITS(BETA_FRAC_BITS),
      .DELTA_WIDTH(EPOCH_TAG_WIDTH)
    ) leak (
      .clk, .reset, .in_valid(state_reg == LEAK_ISSUE),
      .in_ready(leak_in_ready[generated_channel]),
      .membrane_i(loaded_membranes_reg[generated_channel*MEM_WIDTH +: MEM_WIDTH]),
      .current_i(leak_currents_reg[generated_channel*CURRENT_WIDTH +: CURRENT_WIDTH]),
      .beta_i(CHANNEL_BETAS[generated_channel*BETA_WIDTH +: BETA_WIDTH]),
      .elapsed_bins_i(elapsed_bins_reg[
        generated_channel*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH]),
      .out_valid(leak_out_valid[generated_channel]),
      .out_ready(leak_out_ready[generated_channel]),
      .candidate_o(candidates[generated_channel*MEM_WIDTH +: MEM_WIDTH])
    );
  end endgenerate

  retinotopic_mechanism_update #(
    .CHANNELS(CHANNEL_COUNT), .MEM_WIDTH(MEM_WIDTH), .AGE_WIDTH(AGE_WIDTH),
    .ELAPSED_WIDTH(EPOCH_TAG_WIDTH)
  ) mechanisms (
    .candidates_i(candidates), .base_thresholds_i(CHANNEL_THRESHOLDS),
    .update_mask_i(update_mask_reg), .ages_i(loaded_ages_reg),
    .amplitudes_i(loaded_amplitudes_reg), .elapsed_bins_i(elapsed_bins_reg),
    .inhibition_enabled_i(ENABLE_INHIBITION != 0),
    .adaptation_enabled_i(ENABLE_ADAPTATION != 0),
    .inhibition_strength_i(INHIBITION_STRENGTH),
    .adaptation_strength_i(ADAPTATION_STRENGTH),
    .adaptation_duration_i(ADAPTATION_DURATION),
    .membranes_o(mechanism_membranes), .spikes_o(mechanism_spikes),
    .ages_o(mechanism_ages), .amplitudes_o(mechanism_amplitudes),
    .shared_penalty_o(), .membrane_energy_o()
  );

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= COLLECT;
      touched_count_reg <= '0;
      commit_index_reg <= '0;
      group_channel_reg <= '0;
      destination_reg <= '0;
      spatial_reg <= '0;
      contribution_weight_reg <= '0;
      epoch_tag_reg <= '0;
      address_error_reg <= 1'b0;
      contribution_write_data_reg <= '0;
      update_mask_reg <= '0;
      loaded_live_reg <= '0;
      loaded_membranes_reg <= '0;
      loaded_tags_reg <= '0;
      loaded_ages_reg <= {CHANNEL_COUNT{INACTIVE_AGE}};
      loaded_amplitudes_reg <= '0;
      leak_currents_reg <= '0;
      elapsed_bins_reg <= '0;
      result_membranes_reg <= '0;
      result_ages_reg <= {CHANNEL_COUNT{INACTIVE_AGE}};
      result_amplitudes_reg <= '0;
      spike_pending_reg <= '0;
    end else case (state_reg)
      COLLECT: begin
        if (epoch_end_valid && epoch_end_ready) begin
          epoch_tag_reg <= epoch_tag_i;
          commit_index_reg <= '0;
          group_channel_reg <= '0;
          update_mask_reg <= '0;
          if (touched_count_reg == 0)
            state_reg <= HOLD_DONE;
          else state_reg <= QUEUE_WAIT;
        end else if (contribution_valid && contribution_ready) begin
          destination_index = $unsigned(destination_i);
          if (destination_index < DEST_COUNT) begin
            destination_reg <= destination_i;
            spatial_index = destination_index % SPATIAL_DEST_COUNT;
            spatial_reg <= spatial_index[SPATIAL_WIDTH-1:0];
            contribution_weight_reg <= weight_i;
            if (state_read_ready) state_reg <= CONTRIBUTION_STATE_WAIT;
          end else address_error_reg <= 1'b1;
        end
      end
      CONTRIBUTION_STATE_WAIT: if (state_read_response_valid) begin
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
        state_reg <= CONTRIBUTION_STATE_WRITE;
      end
      CONTRIBUTION_STATE_WRITE: if (state_write_ready)
        state_reg <= CONTRIBUTION_SPATIAL_ISSUE;
      CONTRIBUTION_SPATIAL_ISSUE: if (spatial_read_ready)
        state_reg <= CONTRIBUTION_SPATIAL_WAIT;
      CONTRIBUTION_SPATIAL_WAIT: if (spatial_read_response_valid) begin
        if (!spatial_read_data[0]) begin
          touched_count_reg <= touched_count_reg + 1'b1;
          state_reg <= CONTRIBUTION_SPATIAL_WRITE;
        end else state_reg <= COLLECT;
      end
      CONTRIBUTION_SPATIAL_WRITE: if (spatial_write_ready) state_reg <= COLLECT;
      QUEUE_WAIT: if (queue_read_valid) begin
        spatial_reg <= queue_read_data;
        group_channel_reg <= '0;
        update_mask_reg <= '0;
        state_reg <= GROUP_READ_ISSUE;
      end
      GROUP_READ_ISSUE: if (state_read_ready) state_reg <= GROUP_READ_WAIT;
      GROUP_READ_WAIT: if (state_read_response_valid) begin
        loaded_live_reg[group_channel_reg] <= state_read_data[LIVE_BIT];
        loaded_membranes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH] <=
          state_read_data[LIVE_BIT] ?
            state_read_data[MEMBRANE_LSB +: MEM_WIDTH] : '0;
        loaded_tags_reg[group_channel_reg*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] <=
          state_read_data[TAG_LSB +: EPOCH_TAG_WIDTH];
        loaded_ages_reg[group_channel_reg*AGE_WIDTH +: AGE_WIDTH] <=
          (ENABLE_ADAPTATION != 0) && state_read_data[LIVE_BIT] ?
            {{(AGE_WIDTH-AGE_STORAGE_WIDTH){1'b0}},
             state_read_data[AGE_LSB +: AGE_STORAGE_WIDTH]} : INACTIVE_AGE;
        loaded_amplitudes_reg[group_channel_reg*MEM_WIDTH +: MEM_WIDTH] <=
          (ENABLE_ADAPTATION != 0) && state_read_data[LIVE_BIT] ?
            {{(MEM_WIDTH-AMPLITUDE_STORAGE_WIDTH){1'b0}},
             state_read_data[AMPLITUDE_LSB +: AMPLITUDE_STORAGE_WIDTH]} : '0;
        update_mask_reg[group_channel_reg] <=
          (ENABLE_INHIBITION != 0) || state_read_data[TOUCHED_BIT];
        leak_currents_reg[group_channel_reg*CURRENT_WIDTH +: CURRENT_WIDTH] <=
          ((ENABLE_INHIBITION != 0) || state_read_data[TOUCHED_BIT]) ?
            state_read_data[CURRENT_LSB +: CURRENT_WIDTH] : '0;
        elapsed_bins_reg[group_channel_reg*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] <=
          ((ENABLE_INHIBITION != 0) || state_read_data[TOUCHED_BIT]) ?
            (state_read_data[LIVE_BIT] ?
              epoch_tag_reg-state_read_data[TAG_LSB +: EPOCH_TAG_WIDTH] :
              {{(EPOCH_TAG_WIDTH-1){1'b0}}, 1'b1}) : '0;
        if (group_channel_reg + 1 >= CHANNEL_COUNT) begin
          group_channel_reg <= '0;
          state_reg <= LEAK_ISSUE;
        end else begin
          group_channel_reg <= group_channel_reg + 1'b1;
          state_reg <= GROUP_READ_ISSUE;
        end
      end
      LEAK_ISSUE: if (&leak_in_ready) state_reg <= LEAK_WAIT;
      LEAK_WAIT: if (&leak_out_valid) begin
        result_membranes_reg <= mechanism_membranes;
        result_ages_reg <= mechanism_ages;
        result_amplitudes_reg <= mechanism_amplitudes;
        spike_pending_reg <= mechanism_spikes;
        group_channel_reg <= '0;
        state_reg <= GROUP_WRITE;
      end
      GROUP_WRITE: if (state_write_ready) begin
        if (group_channel_reg + 1 >= CHANNEL_COUNT) begin
          group_channel_reg <= '0;
          state_reg <= SPATIAL_CLEAR;
        end else group_channel_reg <= group_channel_reg + 1'b1;
      end
      SPATIAL_CLEAR: if (spatial_write_ready) begin
        if (spike_pending_reg != 0) state_reg <= EMIT_SPIKES;
        else if (commit_index_reg + 1 >= touched_count_reg) state_reg <= HOLD_DONE;
        else begin
          commit_index_reg <= commit_index_reg + 1'b1;
          state_reg <= QUEUE_WAIT;
        end
      end
      EMIT_SPIKES: if (spike_valid && spike_ready) begin
        spike_pending_reg[selected_channel] <= 1'b0;
        if ((spike_pending_reg & ~(1'b1 << selected_channel)) == 0) begin
          if (commit_index_reg + 1 >= touched_count_reg) state_reg <= HOLD_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_WAIT;
          end
        end
      end
      HOLD_DONE: if (epoch_done_ready) begin
        touched_count_reg <= '0;
        address_error_reg <= 1'b0;
        state_reg <= COLLECT;
      end
      default: state_reg <= COLLECT;
    endcase
  end
endmodule
