`timescale 1ns/1ps
// Autonomous actor-local state engine for mechanism-enabled PLIF populations.
// Contributions accumulate per (channel,spatial) destination; completion commits
// all channels at each touched retinotopic location as one atomic group.
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
  localparam [2:0] COLLECT = 3'd0, LEAK_ISSUE = 3'd1, LEAK_WAIT = 3'd2,
                   EMIT_SPIKES = 3'd3, HOLD_DONE = 3'd4;
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH-1)) - 1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH-1));
  localparam [AGE_WIDTH-1:0] INACTIVE_AGE = {AGE_WIDTH{1'b1}};
  logic [2:0] state_reg;
  logic signed [CURRENT_WIDTH-1:0] current_mem [0:DEST_COUNT-1];
  logic signed [MEM_WIDTH-1:0] membrane_mem [0:DEST_COUNT-1];
  logic [EPOCH_TAG_WIDTH-1:0] last_tag_mem [0:DEST_COUNT-1];
  logic [AGE_WIDTH-1:0] age_mem [0:DEST_COUNT-1];
  logic [MEM_WIDTH-1:0] amplitude_mem [0:DEST_COUNT-1];
  logic [DEST_COUNT-1:0] touched_channel_mem;
  logic [SPATIAL_DEST_COUNT-1:0] touched_spatial_mem;
  logic [SPATIAL_WIDTH-1:0] touched_spatial_queue [0:SPATIAL_DEST_COUNT-1];
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [SPATIAL_WIDTH-1:0] spatial_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic address_error_reg;
  logic [CHANNEL_COUNT-1:0] update_mask;
  logic [CHANNEL_COUNT-1:0] leak_in_ready;
  logic [CHANNEL_COUNT-1:0] leak_out_valid;
  logic [CHANNEL_COUNT-1:0] leak_out_ready;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] leak_membranes;
  logic signed [CHANNEL_COUNT*CURRENT_WIDTH-1:0] leak_currents;
  logic [CHANNEL_COUNT*EPOCH_TAG_WIDTH-1:0] elapsed_bins;
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] candidates;
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] mechanism_ages_in;
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_amplitudes_in;
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
  integer i;

  assign contribution_ready = (state_reg == COLLECT) && !epoch_end_valid;
  assign epoch_end_ready = (state_reg == COLLECT);
  assign spike_valid = (state_reg == EMIT_SPIKES) && (spike_pending_reg != 0);
  assign epoch_done_valid = (state_reg == HOLD_DONE);
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg;
  assign leak_out_ready = {CHANNEL_COUNT{state_reg == LEAK_WAIT && &leak_out_valid}};

  always_comb begin
    update_mask = '0;
    leak_membranes = '0;
    leak_currents = '0;
    elapsed_bins = '0;
    mechanism_ages_in = '0;
    mechanism_amplitudes_in = '0;
    for (channel = 0; channel < CHANNEL_COUNT; channel = channel + 1) begin
      destination_index = channel*SPATIAL_DEST_COUNT + $unsigned(spatial_reg);
      update_mask[channel] = ENABLE_INHIBITION ? 1'b1 :
                             touched_channel_mem[destination_index];
      leak_membranes[channel*MEM_WIDTH +: MEM_WIDTH] = membrane_mem[destination_index];
      leak_currents[channel*CURRENT_WIDTH +: CURRENT_WIDTH] =
        update_mask[channel] ? current_mem[destination_index] : '0;
      elapsed_bins[channel*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH] =
        update_mask[channel] ? epoch_tag_reg-last_tag_mem[destination_index] : '0;
      mechanism_ages_in[channel*AGE_WIDTH +: AGE_WIDTH] = age_mem[destination_index];
      mechanism_amplitudes_in[channel*MEM_WIDTH +: MEM_WIDTH] =
        amplitude_mem[destination_index];
    end
    selected_channel = 0;
    for (channel = CHANNEL_COUNT-1; channel >= 0; channel = channel-1)
      if (spike_pending_reg[channel]) selected_channel = channel;
    spike_destination_o =
      (selected_channel*SPATIAL_DEST_COUNT + $unsigned(spatial_reg));
  end

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
      .membrane_i(leak_membranes[generated_channel*MEM_WIDTH +: MEM_WIDTH]),
      .current_i(leak_currents[generated_channel*CURRENT_WIDTH +: CURRENT_WIDTH]),
      .beta_i(CHANNEL_BETAS[generated_channel*BETA_WIDTH +: BETA_WIDTH]),
      .elapsed_bins_i(elapsed_bins[generated_channel*EPOCH_TAG_WIDTH +: EPOCH_TAG_WIDTH]),
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
    .update_mask_i(update_mask), .ages_i(mechanism_ages_in),
    .amplitudes_i(mechanism_amplitudes_in), .elapsed_bins_i(elapsed_bins),
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
      touched_channel_mem <= '0;
      touched_spatial_mem <= '0;
      touched_count_reg <= '0;
      commit_index_reg <= '0;
      spatial_reg <= '0;
      epoch_tag_reg <= '0;
      address_error_reg <= 1'b0;
      spike_pending_reg <= '0;
      for (i = 0; i < DEST_COUNT; i = i+1) begin
        current_mem[i] = '0;
        membrane_mem[i] = '0;
        last_tag_mem[i] = '0;
        age_mem[i] = INACTIVE_AGE;
        amplitude_mem[i] = '0;
      end
      for (i = 0; i < SPATIAL_DEST_COUNT; i = i+1)
        touched_spatial_queue[i] = '0;
    end else case (state_reg)
      COLLECT: begin
        if (epoch_end_valid) begin
          epoch_tag_reg <= epoch_tag_i;
          commit_index_reg <= '0;
          if (touched_count_reg == 0) state_reg <= HOLD_DONE;
          else begin
            spatial_reg <= touched_spatial_queue[0];
            state_reg <= LEAK_ISSUE;
          end
        end else if (contribution_valid) begin
          destination_index = $unsigned(destination_i);
          if (destination_index < DEST_COUNT) begin
            sum_value = $signed(current_mem[destination_index]) + $signed(weight_i);
            if (sum_value > MAX_CURRENT) sum_value = MAX_CURRENT;
            if (sum_value < MIN_CURRENT) sum_value = MIN_CURRENT;
            current_mem[destination_index] <= sum_value[CURRENT_WIDTH-1:0];
            touched_channel_mem[destination_index] <= 1'b1;
            spatial_index = destination_index % SPATIAL_DEST_COUNT;
            if (!touched_spatial_mem[spatial_index]) begin
              touched_spatial_mem[spatial_index] <= 1'b1;
              touched_spatial_queue[touched_count_reg] <= spatial_index[SPATIAL_WIDTH-1:0];
              touched_count_reg <= touched_count_reg + 1'b1;
            end
          end else address_error_reg <= 1'b1;
        end
      end
      LEAK_ISSUE: if (&leak_in_ready) state_reg <= LEAK_WAIT;
      LEAK_WAIT: if (&leak_out_valid) begin
        for (channel = 0; channel < CHANNEL_COUNT; channel = channel+1) begin
          destination_index = channel*SPATIAL_DEST_COUNT + $unsigned(spatial_reg);
          if (update_mask[channel]) begin
            membrane_mem[destination_index] =
              mechanism_membranes[channel*MEM_WIDTH +: MEM_WIDTH];
            last_tag_mem[destination_index] = epoch_tag_reg;
            age_mem[destination_index] = mechanism_ages[channel*AGE_WIDTH +: AGE_WIDTH];
            amplitude_mem[destination_index] =
              mechanism_amplitudes[channel*MEM_WIDTH +: MEM_WIDTH];
          end
          current_mem[destination_index] = '0;
          touched_channel_mem[destination_index] <= 1'b0;
        end
        touched_spatial_mem[spatial_reg] <= 1'b0;
        spike_pending_reg <= mechanism_spikes;
        if (mechanism_spikes != 0) state_reg <= EMIT_SPIKES;
        else if (commit_index_reg + 1 >= touched_count_reg) state_reg <= HOLD_DONE;
        else begin
          commit_index_reg <= commit_index_reg + 1'b1;
          spatial_reg <= touched_spatial_queue[commit_index_reg + 1'b1];
          state_reg <= LEAK_ISSUE;
        end
      end
      EMIT_SPIKES: if (spike_valid && spike_ready) begin
        spike_pending_reg[selected_channel] <= 1'b0;
        if ((spike_pending_reg & ~(1'b1 << selected_channel)) == 0) begin
          if (commit_index_reg + 1 >= touched_count_reg) state_reg <= HOLD_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            spatial_reg <= touched_spatial_queue[commit_index_reg + 1'b1];
            state_reg <= LEAK_ISSUE;
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
