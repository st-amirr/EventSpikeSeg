`timescale 1ns/1ps
// SRAM-transactional mechanism actor. Each channel owns a local state lane
// addressed by spatial position, allowing an atomic all-channel retinotopic
// read/commit without fetching membrane state from another actor.
module retinotopic_asynchronous_plif_actor_sram #(
  parameter integer ADDRESS_WIDTH = 8,
  parameter integer CHANNEL_COUNT = 4,
  parameter integer SPATIAL_DEST_COUNT = 16,
  parameter integer DEST_COUNT = CHANNEL_COUNT * SPATIAL_DEST_COUNT,
  parameter integer SPATIAL_WIDTH =
    (SPATIAL_DEST_COUNT <= 1) ? 1 : $clog2(SPATIAL_DEST_COUNT),
  parameter integer CHANNEL_WIDTH = (CHANNEL_COUNT <= 1) ? 1 : $clog2(CHANNEL_COUNT),
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer EPOCH_TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 16,
  parameter integer COUNT_WIDTH =
    (SPATIAL_DEST_COUNT <= 1) ? 1 : $clog2(SPATIAL_DEST_COUNT + 1),
  parameter integer QUEUE_ADDRESS_WIDTH =
    (SPATIAL_DEST_COUNT <= 1) ? 1 : $clog2(SPATIAL_DEST_COUNT),
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter integer USE_SRAM_MACRO = 0,
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
  output logic address_error_o
);
  localparam integer CURRENT_LSB = 0;
  localparam integer MEMBRANE_LSB = CURRENT_LSB + CURRENT_WIDTH;
  localparam integer TAG_LSB = MEMBRANE_LSB + MEM_WIDTH;
  localparam integer TOUCHED_BIT = TAG_LSB + EPOCH_TAG_WIDTH;
  localparam integer STATE_WIDTH = TOUCHED_BIT + 1;
  localparam integer ADAPT_AGE_LSB = 0;
  localparam integer ADAPT_AMPLITUDE_LSB = AGE_WIDTH;
  localparam integer ADAPT_STATE_WIDTH = AGE_WIDTH + MEM_WIDTH;
  localparam [AGE_WIDTH-1:0] INACTIVE_AGE = {AGE_WIDTH{1'b1}};
  localparam signed [CURRENT_WIDTH:0] MAX_CURRENT =
    (1 <<< (CURRENT_WIDTH - 1)) - 1;
  localparam signed [CURRENT_WIDTH:0] MIN_CURRENT =
    -(1 <<< (CURRENT_WIDTH - 1));
  localparam [3:0] SCRUB = 4'd0, COLLECT = 4'd1,
    CONTRIBUTION_WAIT = 4'd2, QUEUE_READ = 4'd3,
    QUEUE_CAPTURE = 4'd4, STATE_READ = 4'd5, STATE_CAPTURE = 4'd6,
    LEAK_ISSUE = 4'd7, LEAK_WAIT = 4'd8, EMIT_SPIKES = 4'd9,
    HOLD_DONE = 4'd10;

  logic [3:0] state_reg;
  logic [SPATIAL_WIDTH-1:0] scrub_spatial_reg;
  logic [SPATIAL_WIDTH-1:0] spatial_reg;
  logic [CHANNEL_WIDTH-1:0] contribution_channel_reg;
  logic signed [WEIGHT_WIDTH-1:0] contribution_weight_reg;
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic address_error_reg;
  logic [CHANNEL_COUNT-1:0] spike_pending_reg;

  logic [CHANNEL_COUNT-1:0] lane_read_enable;
  logic [CHANNEL_COUNT-1:0] lane_read_valid;
  logic [CHANNEL_COUNT*STATE_WIDTH-1:0] lane_read_data;
  logic [CHANNEL_COUNT-1:0] lane_write_enable;
  logic [CHANNEL_COUNT*STATE_WIDTH-1:0] lane_write_data;
  logic [CHANNEL_COUNT*STATE_WIDTH-1:0] captured_state_reg;
  logic [SPATIAL_WIDTH-1:0] lane_read_address;
  logic [SPATIAL_WIDTH-1:0] lane_write_address;
  logic [CHANNEL_COUNT-1:0] adapt_read_enable;
  logic [CHANNEL_COUNT-1:0] adapt_read_valid;
  logic [CHANNEL_COUNT*ADAPT_STATE_WIDTH-1:0] adapt_read_data;
  logic [CHANNEL_COUNT-1:0] adapt_write_enable;
  logic [CHANNEL_COUNT*ADAPT_STATE_WIDTH-1:0] adapt_write_data;
  logic [CHANNEL_COUNT*ADAPT_STATE_WIDTH-1:0] captured_adapt_state_reg;
  logic adapt_read_complete;

  logic seen_read_enable, seen_read_valid, seen_read_data;
  logic seen_write_enable, seen_write_data;
  logic [SPATIAL_WIDTH-1:0] seen_read_address, seen_write_address;
  logic queue_read_enable, queue_read_valid, queue_write_enable;
  logic [QUEUE_ADDRESS_WIDTH-1:0] queue_read_address, queue_write_address;
  logic [SPATIAL_WIDTH-1:0] queue_read_data, queue_write_data;

  logic [CHANNEL_COUNT-1:0] update_mask_reg;
  logic [CHANNEL_COUNT-1:0] leak_in_ready;
  logic [CHANNEL_COUNT-1:0] leak_out_valid;
  logic [CHANNEL_COUNT-1:0] leak_out_ready;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] leak_membranes_reg;
  logic signed [CHANNEL_COUNT*CURRENT_WIDTH-1:0] leak_currents_reg;
  logic [CHANNEL_COUNT*EPOCH_TAG_WIDTH-1:0] elapsed_bins_reg;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] candidates;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] mechanism_ages_in_reg;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_amplitudes_in_reg;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_membranes;
  logic [CHANNEL_COUNT-1:0] mechanism_spikes;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] mechanism_ages;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_amplitudes;
  logic [STATE_WIDTH-1:0] selected_state;
  logic signed [CURRENT_WIDTH:0] contribution_sum;
  logic signed [CURRENT_WIDTH-1:0] saturated_contribution_sum;
  integer selected_channel;
  integer destination_value;
  integer contribution_channel_value;
  integer contribution_spatial_value;
  integer channel;

  assign contribution_ready = state_reg == COLLECT && !epoch_end_valid;
  assign epoch_end_ready = state_reg == COLLECT;
  assign spike_valid = state_reg == EMIT_SPIKES && spike_pending_reg != 0;
  assign epoch_done_valid = state_reg == HOLD_DONE;
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg;
  assign leak_out_ready = {CHANNEL_COUNT{state_reg == LEAK_WAIT && &leak_out_valid}};

  initial begin
    if (MEM_WIDTH != 16 || CURRENT_WIDTH != 24 || BETA_WIDTH != 16 ||
        BETA_FRAC_BITS != 15 || EPOCH_TAG_WIDTH != 24)
      $error("mechanism SRAM actor widths must match fixed plif_leak_charge contract");
  end

  always_comb begin
    destination_value = $unsigned(destination_i);
    contribution_channel_value = destination_value / SPATIAL_DEST_COUNT;
    contribution_spatial_value = destination_value % SPATIAL_DEST_COUNT;
    selected_state = lane_read_data[contribution_channel_reg*STATE_WIDTH +: STATE_WIDTH];
    contribution_sum =
      $signed(selected_state[CURRENT_LSB +: CURRENT_WIDTH]) +
      $signed(contribution_weight_reg);
    if (contribution_sum > MAX_CURRENT)
      saturated_contribution_sum = MAX_CURRENT[CURRENT_WIDTH-1:0];
    else if (contribution_sum < MIN_CURRENT)
      saturated_contribution_sum = MIN_CURRENT[CURRENT_WIDTH-1:0];
    else
      saturated_contribution_sum = contribution_sum[CURRENT_WIDTH-1:0];

    lane_read_enable = '0;
    lane_read_address = spatial_reg;
    if (state_reg == COLLECT && contribution_valid && contribution_ready &&
        destination_value < DEST_COUNT) begin
      lane_read_enable[contribution_channel_value] = 1'b1;
      lane_read_address = contribution_spatial_value[SPATIAL_WIDTH-1:0];
    end else if (state_reg == STATE_READ)
      lane_read_enable = {CHANNEL_COUNT{1'b1}};

    lane_write_enable = '0;
    lane_write_address = spatial_reg;
    lane_write_data = captured_state_reg;
    if (state_reg == SCRUB) begin
      lane_write_enable = {CHANNEL_COUNT{1'b1}};
      lane_write_address = scrub_spatial_reg;
      lane_write_data = '0;
    end else if (state_reg == CONTRIBUTION_WAIT &&
                 lane_read_valid[contribution_channel_reg] && seen_read_valid) begin
      lane_write_enable[contribution_channel_reg] = 1'b1;
      lane_write_data[contribution_channel_reg*STATE_WIDTH +: STATE_WIDTH] = selected_state;
      lane_write_data[contribution_channel_reg*STATE_WIDTH + CURRENT_LSB +: CURRENT_WIDTH] =
        saturated_contribution_sum;
      lane_write_data[contribution_channel_reg*STATE_WIDTH + TOUCHED_BIT] = 1'b1;
    end else if (state_reg == LEAK_WAIT && &leak_out_valid) begin
      lane_write_enable = {CHANNEL_COUNT{1'b1}};
      for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1) begin
        lane_write_data[channel*STATE_WIDTH + CURRENT_LSB +: CURRENT_WIDTH] = '0;
        lane_write_data[channel*STATE_WIDTH + TOUCHED_BIT] = 1'b0;
        if (update_mask_reg[channel]) begin
          lane_write_data[channel*STATE_WIDTH + MEMBRANE_LSB +: MEM_WIDTH] =
            mechanism_membranes[channel*MEM_WIDTH +: MEM_WIDTH];
          lane_write_data[channel*STATE_WIDTH + TAG_LSB +: EPOCH_TAG_WIDTH] = epoch_tag_reg;
        end
      end
    end

    adapt_read_enable = '0;
    if (state_reg == STATE_READ && ENABLE_ADAPTATION != 0)
      adapt_read_enable = {CHANNEL_COUNT{1'b1}};
    adapt_read_complete = ENABLE_ADAPTATION == 0 || &adapt_read_valid;
    adapt_write_enable = '0;
    adapt_write_data = captured_adapt_state_reg;
    if (state_reg == SCRUB && ENABLE_ADAPTATION != 0) begin
      adapt_write_enable = {CHANNEL_COUNT{1'b1}};
      adapt_write_data = '0;
      for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1)
        adapt_write_data[channel*ADAPT_STATE_WIDTH + ADAPT_AGE_LSB +: AGE_WIDTH] =
          INACTIVE_AGE;
    end else if (state_reg == LEAK_WAIT && &leak_out_valid &&
                 ENABLE_ADAPTATION != 0) begin
      adapt_write_enable = {CHANNEL_COUNT{1'b1}};
      for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1)
        if (update_mask_reg[channel]) begin
          adapt_write_data[
            channel*ADAPT_STATE_WIDTH + ADAPT_AGE_LSB +: AGE_WIDTH] =
            mechanism_ages[channel*AGE_WIDTH +: AGE_WIDTH];
          adapt_write_data[
            channel*ADAPT_STATE_WIDTH + ADAPT_AMPLITUDE_LSB +: MEM_WIDTH] =
            mechanism_amplitudes[channel*MEM_WIDTH +: MEM_WIDTH];
        end
    end

    seen_read_enable = state_reg == COLLECT && contribution_valid &&
                       contribution_ready && destination_value < DEST_COUNT;
    seen_read_address = contribution_spatial_value[SPATIAL_WIDTH-1:0];
    seen_write_enable = 1'b0;
    seen_write_address = spatial_reg;
    seen_write_data = 1'b0;
    if (state_reg == SCRUB) begin
      seen_write_enable = 1'b1;
      seen_write_address = scrub_spatial_reg;
    end else if (state_reg == CONTRIBUTION_WAIT && seen_read_valid &&
                 lane_read_valid[contribution_channel_reg] && !seen_read_data) begin
      seen_write_enable = 1'b1;
      seen_write_data = 1'b1;
    end else if (state_reg == LEAK_WAIT && &leak_out_valid)
      seen_write_enable = 1'b1;

    queue_write_enable = state_reg == CONTRIBUTION_WAIT && seen_read_valid &&
                         lane_read_valid[contribution_channel_reg] && !seen_read_data;
    queue_write_address = touched_count_reg[QUEUE_ADDRESS_WIDTH-1:0];
    queue_write_data = spatial_reg;
    queue_read_enable = state_reg == QUEUE_READ;
    queue_read_address = commit_index_reg[QUEUE_ADDRESS_WIDTH-1:0];

    selected_channel = 0;
    for (channel = CHANNEL_COUNT-1; channel >= 0; channel = channel-1)
      if (spike_pending_reg[channel]) selected_channel = channel;
    spike_destination_o =
      selected_channel*SPATIAL_DEST_COUNT + $unsigned(spatial_reg);
  end

  genvar generated_channel;
  generate for (generated_channel = 0; generated_channel < CHANNEL_COUNT;
                generated_channel = generated_channel + 1) begin : state_lanes
    actor_local_state_sram #(
      .DATA_WIDTH(STATE_WIDTH), .DEPTH(SPATIAL_DEST_COUNT),
      .ADDRESS_WIDTH(SPATIAL_WIDTH), .USE_MACRO(USE_SRAM_MACRO)
    ) state_bank (
      .clk, .read_enable_i(lane_read_enable[generated_channel]),
      .read_address_i(lane_read_address),
      .read_valid_o(lane_read_valid[generated_channel]),
      .read_data_o(lane_read_data[generated_channel*STATE_WIDTH +: STATE_WIDTH]),
      .write_enable_i(lane_write_enable[generated_channel]),
      .write_address_i(lane_write_address),
      .write_data_i(lane_write_data[generated_channel*STATE_WIDTH +: STATE_WIDTH])
    );
    if (ENABLE_ADAPTATION != 0) begin : adaptation_state
      actor_local_state_sram #(
        .DATA_WIDTH(ADAPT_STATE_WIDTH), .DEPTH(SPATIAL_DEST_COUNT),
        .ADDRESS_WIDTH(SPATIAL_WIDTH), .USE_MACRO(USE_SRAM_MACRO)
      ) adaptation_bank (
        .clk, .read_enable_i(adapt_read_enable[generated_channel]),
        .read_address_i(lane_read_address),
        .read_valid_o(adapt_read_valid[generated_channel]),
        .read_data_o(adapt_read_data[
          generated_channel*ADAPT_STATE_WIDTH +: ADAPT_STATE_WIDTH]),
        .write_enable_i(adapt_write_enable[generated_channel]),
        .write_address_i(lane_write_address),
        .write_data_i(adapt_write_data[
          generated_channel*ADAPT_STATE_WIDTH +: ADAPT_STATE_WIDTH])
      );
    end else begin : no_adaptation_state
      assign adapt_read_valid[generated_channel] = 1'b1;
      assign adapt_read_data[
        generated_channel*ADAPT_STATE_WIDTH +: ADAPT_STATE_WIDTH] = '0;
    end
    // EventSpikeSeg fixes these widths to the plif_leak_charge defaults. Avoid
    // redundant overrides: Yosys 0.23 crashes when deriving the same overridden
    // module more than once inside a generate loop.
    plif_leak_charge leak (
      .clk, .reset, .in_valid(state_reg == LEAK_ISSUE),
      .in_ready(leak_in_ready[generated_channel]),
      .membrane_i(leak_membranes_reg[generated_channel*MEM_WIDTH +: MEM_WIDTH]),
      .current_i(leak_currents_reg[generated_channel*CURRENT_WIDTH +: CURRENT_WIDTH]),
      .beta_i(CHANNEL_BETAS[generated_channel*BETA_WIDTH +: BETA_WIDTH]),
      .elapsed_bins_i(elapsed_bins_reg[
        generated_channel*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH]),
      .out_valid(leak_out_valid[generated_channel]),
      .out_ready(leak_out_ready[generated_channel]),
      .candidate_o(candidates[generated_channel*MEM_WIDTH +: MEM_WIDTH])
    );
  end endgenerate

  actor_local_state_sram #(
    .DATA_WIDTH(1), .DEPTH(SPATIAL_DEST_COUNT), .ADDRESS_WIDTH(SPATIAL_WIDTH),
    .USE_MACRO(USE_SRAM_MACRO)
  ) spatial_seen_bank (
    .clk, .read_enable_i(seen_read_enable), .read_address_i(seen_read_address),
    .read_valid_o(seen_read_valid), .read_data_o(seen_read_data),
    .write_enable_i(seen_write_enable), .write_address_i(seen_write_address),
    .write_data_i(seen_write_data)
  );

  actor_local_state_sram #(
    .DATA_WIDTH(SPATIAL_WIDTH), .DEPTH(SPATIAL_DEST_COUNT),
    .ADDRESS_WIDTH(QUEUE_ADDRESS_WIDTH), .USE_MACRO(USE_SRAM_MACRO)
  ) touched_spatial_queue (
    .clk, .read_enable_i(queue_read_enable), .read_address_i(queue_read_address),
    .read_valid_o(queue_read_valid), .read_data_o(queue_read_data),
    .write_enable_i(queue_write_enable), .write_address_i(queue_write_address),
    .write_data_i(queue_write_data)
  );

  retinotopic_mechanism_update #(
    .CHANNELS(CHANNEL_COUNT), .MEM_WIDTH(MEM_WIDTH), .AGE_WIDTH(AGE_WIDTH),
    .ELAPSED_WIDTH(EPOCH_TAG_WIDTH)
  ) mechanisms (
    .candidates_i(candidates), .base_thresholds_i(CHANNEL_THRESHOLDS),
    .update_mask_i(update_mask_reg), .ages_i(mechanism_ages_in_reg),
    .amplitudes_i(mechanism_amplitudes_in_reg), .elapsed_bins_i(elapsed_bins_reg),
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
      state_reg <= SCRUB;
      scrub_spatial_reg <= '0;
      spatial_reg <= '0;
      contribution_channel_reg <= '0;
      contribution_weight_reg <= '0;
      touched_count_reg <= '0;
      commit_index_reg <= '0;
      epoch_tag_reg <= '0;
      address_error_reg <= 1'b0;
      spike_pending_reg <= '0;
      captured_state_reg <= '0;
      captured_adapt_state_reg <= '0;
      update_mask_reg <= '0;
      leak_membranes_reg <= '0;
      leak_currents_reg <= '0;
      elapsed_bins_reg <= '0;
      mechanism_ages_in_reg <= '0;
      mechanism_amplitudes_in_reg <= '0;
    end else case (state_reg)
      SCRUB: begin
        if (scrub_spatial_reg + 1'b1 >= SPATIAL_DEST_COUNT) begin
          scrub_spatial_reg <= '0;
          state_reg <= COLLECT;
        end else scrub_spatial_reg <= scrub_spatial_reg + 1'b1;
      end
      COLLECT: begin
        if (epoch_end_valid) begin
          epoch_tag_reg <= epoch_tag_i;
          commit_index_reg <= '0;
          state_reg <= touched_count_reg == 0 ? HOLD_DONE : QUEUE_READ;
        end else if (contribution_valid) begin
          if (destination_value < DEST_COUNT) begin
            contribution_channel_reg <= contribution_channel_value[CHANNEL_WIDTH-1:0];
            spatial_reg <= contribution_spatial_value[SPATIAL_WIDTH-1:0];
            contribution_weight_reg <= weight_i;
            state_reg <= CONTRIBUTION_WAIT;
          end else address_error_reg <= 1'b1;
        end
      end
      CONTRIBUTION_WAIT: if (seen_read_valid &&
                            lane_read_valid[contribution_channel_reg]) begin
        if (!seen_read_data) touched_count_reg <= touched_count_reg + 1'b1;
        state_reg <= COLLECT;
      end
      QUEUE_READ: state_reg <= QUEUE_CAPTURE;
      QUEUE_CAPTURE: if (queue_read_valid) begin
        spatial_reg <= queue_read_data;
        state_reg <= STATE_READ;
      end
      STATE_READ: state_reg <= STATE_CAPTURE;
      STATE_CAPTURE: if (&lane_read_valid && adapt_read_complete) begin
        captured_state_reg <= lane_read_data;
        captured_adapt_state_reg <= adapt_read_data;
        for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1) begin
          update_mask_reg[channel] <= ENABLE_INHIBITION != 0 ? 1'b1 :
            lane_read_data[channel*STATE_WIDTH + TOUCHED_BIT];
          leak_membranes_reg[channel*MEM_WIDTH +: MEM_WIDTH] <=
            lane_read_data[channel*STATE_WIDTH + MEMBRANE_LSB +: MEM_WIDTH];
          leak_currents_reg[channel*CURRENT_WIDTH +: CURRENT_WIDTH] <=
            (ENABLE_INHIBITION != 0 ||
             lane_read_data[channel*STATE_WIDTH + TOUCHED_BIT]) ?
            lane_read_data[channel*STATE_WIDTH + CURRENT_LSB +: CURRENT_WIDTH] : '0;
          elapsed_bins_reg[channel*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] <=
            (ENABLE_INHIBITION != 0 ||
             lane_read_data[channel*STATE_WIDTH + TOUCHED_BIT]) ?
            epoch_tag_reg - lane_read_data[
              channel*STATE_WIDTH + TAG_LSB +: EPOCH_TAG_WIDTH] : '0;
          mechanism_ages_in_reg[channel*AGE_WIDTH +: AGE_WIDTH] <=
            ENABLE_ADAPTATION != 0 ? adapt_read_data[
              channel*ADAPT_STATE_WIDTH + ADAPT_AGE_LSB +: AGE_WIDTH] : INACTIVE_AGE;
          mechanism_amplitudes_in_reg[channel*MEM_WIDTH +: MEM_WIDTH] <=
            ENABLE_ADAPTATION != 0 ? adapt_read_data[
              channel*ADAPT_STATE_WIDTH + ADAPT_AMPLITUDE_LSB +: MEM_WIDTH] : '0;
        end
        state_reg <= LEAK_ISSUE;
      end
      LEAK_ISSUE: if (&leak_in_ready) state_reg <= LEAK_WAIT;
      LEAK_WAIT: if (&leak_out_valid) begin
        spike_pending_reg <= mechanism_spikes;
        if (mechanism_spikes != 0) state_reg <= EMIT_SPIKES;
        else if (commit_index_reg + 1'b1 >= touched_count_reg) state_reg <= HOLD_DONE;
        else begin
          commit_index_reg <= commit_index_reg + 1'b1;
          state_reg <= QUEUE_READ;
        end
      end
      EMIT_SPIKES: if (spike_valid && spike_ready) begin
        spike_pending_reg[selected_channel] <= 1'b0;
        if ((spike_pending_reg & ~(1'b1 << selected_channel)) == 0) begin
          if (commit_index_reg + 1'b1 >= touched_count_reg) state_reg <= HOLD_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            state_reg <= QUEUE_READ;
          end
        end
      end
      HOLD_DONE: if (epoch_done_ready) begin
        touched_count_reg <= '0;
        address_error_reg <= 1'b0;
        state_reg <= COLLECT;
      end
      default: state_reg <= SCRUB;
    endcase
  end
endmodule
