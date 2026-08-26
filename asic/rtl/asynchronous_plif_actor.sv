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
  output logic address_error_o
);
  localparam [2:0] COLLECT = 3'd0, LOAD_TOUCHED = 3'd1, PLIF_ISSUE = 3'd2,
                   PLIF_WAIT = 3'd3, HOLD_SPIKE = 3'd4, HOLD_EPOCH_DONE = 3'd5;
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH - 1)) - 1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH - 1));

  logic [2:0] state_reg;
  logic signed [CURRENT_WIDTH-1:0] current_mem [0:DEST_COUNT-1];
  logic signed [MEM_WIDTH-1:0] membrane_mem [0:DEST_COUNT-1];
  logic [EPOCH_TAG_WIDTH-1:0] last_tag_mem [0:DEST_COUNT-1];
  logic [DEST_COUNT-1:0] touched_mem;
  logic [DEST_COUNT-1:0] state_live_mem;
  logic [ADDRESS_WIDTH-1:0] touched_queue [0:DEST_COUNT-1];

  logic [ADDRESS_WIDTH-1:0] destination_reg;
  logic [COUNT_WIDTH-1:0] commit_index_reg;
  logic [COUNT_WIDTH-1:0] touched_count_reg;
  logic [EPOCH_TAG_WIDTH-1:0] epoch_tag_reg;
  logic [EPOCH_TAG_WIDTH-1:0] elapsed_reg;
  logic signed [MEM_WIDTH-1:0] plif_membrane_in;
  logic signed [CURRENT_WIDTH-1:0] plif_current_in;
  logic address_error_reg;

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
  integer i;

  assign contribution_ready = (state_reg == COLLECT) && !epoch_end_valid;
  assign epoch_end_ready = (state_reg == COLLECT);
  assign spike_valid = (state_reg == HOLD_SPIKE);
  assign epoch_done_valid = (state_reg == HOLD_EPOCH_DONE);
  assign epoch_tag_o = epoch_tag_reg;
  assign address_error_o = address_error_reg;
  assign plif_in_valid = (state_reg == PLIF_ISSUE);
  assign plif_out_ready = (state_reg == PLIF_WAIT);

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
      touched_mem <= '0;
      state_live_mem <= '0;
      destination_reg <= '0;
      commit_index_reg <= '0;
      touched_count_reg <= '0;
      epoch_tag_reg <= '0;
      address_error_reg <= 1'b0;
      spike_destination_o <= '0;
      for (i = 0; i < DEST_COUNT; i = i + 1) begin
        current_mem[i] <= '0;
        membrane_mem[i] <= '0;
        last_tag_mem[i] <= '0;
        touched_queue[i] <= '0;
      end
    end else begin
      case (state_reg)
        COLLECT: begin
          if (epoch_end_valid) begin
            epoch_tag_reg <= epoch_tag_i;
            commit_index_reg <= '0;
            if (touched_count_reg == 0)
              state_reg <= HOLD_EPOCH_DONE;
            else begin
              destination_reg <= touched_queue[0];
              state_reg <= LOAD_TOUCHED;
            end
          end else if (contribution_valid) begin
            destination_index = $unsigned(destination_i);
            if (destination_index < DEST_COUNT) begin
              sum_value = $signed(current_mem[destination_index]) + $signed(weight_i);
              if (sum_value > MAX_CURRENT)
                current_mem[destination_index] <= MAX_CURRENT;
              else if (sum_value < MIN_CURRENT)
                current_mem[destination_index] <= MIN_CURRENT;
              else
                current_mem[destination_index] <= sum_value[CURRENT_WIDTH-1:0];
              if (!touched_mem[destination_index]) begin
                touched_queue[touched_count_reg] <= destination_i;
                touched_count_reg <= touched_count_reg + 1'b1;
                touched_mem[destination_index] <= 1'b1;
              end
            end else begin
              address_error_reg <= 1'b1;
            end
          end
        end
        LOAD_TOUCHED: begin
          plif_current_in <= current_mem[destination_reg];
          if (state_live_mem[destination_reg]) begin
            plif_membrane_in <= membrane_mem[destination_reg];
            elapsed_reg <= epoch_tag_reg - last_tag_mem[destination_reg];
          end else begin
            plif_membrane_in <= '0;
            elapsed_reg <= {{(EPOCH_TAG_WIDTH-1){1'b0}}, 1'b1};
          end
          state_reg <= PLIF_ISSUE;
        end
        PLIF_ISSUE: if (plif_in_ready) state_reg <= PLIF_WAIT;
        PLIF_WAIT: if (plif_out_valid) begin
          membrane_mem[destination_reg] <= plif_membrane;
          last_tag_mem[destination_reg] <= epoch_tag_reg;
          state_live_mem[destination_reg] <= (plif_membrane != 0);
          current_mem[destination_reg] <= '0;
          touched_mem[destination_reg] <= 1'b0;
          if (plif_spike) begin
            spike_destination_o <= destination_reg;
            state_reg <= HOLD_SPIKE;
          end else if ((commit_index_reg + 1'b1) >= touched_count_reg) begin
            state_reg <= HOLD_EPOCH_DONE;
          end else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            destination_reg <= touched_queue[commit_index_reg + 1'b1];
            state_reg <= LOAD_TOUCHED;
          end
        end
        HOLD_SPIKE: if (spike_ready) begin
          if ((commit_index_reg + 1'b1) >= touched_count_reg)
            state_reg <= HOLD_EPOCH_DONE;
          else begin
            commit_index_reg <= commit_index_reg + 1'b1;
            destination_reg <= touched_queue[commit_index_reg + 1'b1];
            state_reg <= LOAD_TOUCHED;
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
