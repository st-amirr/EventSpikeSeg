`timescale 1ns/1ps
module plif_update #(
  parameter integer MEM_WIDTH      = 16,
  parameter integer CURRENT_WIDTH  = 24,
  parameter integer BETA_WIDTH     = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer DELTA_WIDTH    = 24
) (
  input  logic clk,
  input  logic reset,
  input  logic in_valid,
  output logic in_ready,
  input  logic signed [MEM_WIDTH-1:0] membrane_i,
  input  logic signed [CURRENT_WIDTH-1:0] current_i,
  input  logic [BETA_WIDTH-1:0] beta_i,
  input  logic signed [MEM_WIDTH-1:0] threshold_i,
  input  logic [DELTA_WIDTH-1:0] elapsed_bins_i,
  output logic out_valid,
  input  logic out_ready,
  output logic signed [MEM_WIDTH-1:0] candidate_o,
  output logic signed [MEM_WIDTH-1:0] membrane_o,
  output logic spike_o
);
  localparam [1:0] IDLE = 2'd0, LEAK = 2'd1, CHARGE = 2'd2, HOLD_RESULT = 2'd3;
  localparam integer MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH - 1));

  logic [1:0] state_reg;
  logic signed [MEM_WIDTH-1:0] work_mem_reg;
  logic signed [CURRENT_WIDTH-1:0] current_reg;
  logic [BETA_WIDTH-1:0] beta_reg;
  logic signed [MEM_WIDTH-1:0] threshold_reg;
  logic [DELTA_WIDTH-1:0] remaining_reg;

  integer signed product_value;
  integer signed leaked_value;
  integer signed candidate_value;
  integer signed membrane_value;

  function automatic integer signed round_ties_away(input integer signed value);
    integer signed magnitude;
    begin
      if (value >= 0)
        round_ties_away = (value + (1 << (BETA_FRAC_BITS - 1))) >>> BETA_FRAC_BITS;
      else begin
        magnitude = -value;
        round_ties_away = -((magnitude + (1 << (BETA_FRAC_BITS - 1))) >>> BETA_FRAC_BITS);
      end
    end
  endfunction

  function automatic integer signed saturate_mem(input integer signed value);
    begin
      if (value > MAX_MEM)
        saturate_mem = MAX_MEM;
      else if (value < MIN_MEM)
        saturate_mem = MIN_MEM;
      else
        saturate_mem = value;
    end
  endfunction

  assign in_ready = (state_reg == IDLE);
  assign out_valid = (state_reg == HOLD_RESULT);

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= IDLE;
      work_mem_reg <= '0;
      current_reg <= '0;
      beta_reg <= '0;
      threshold_reg <= '0;
      remaining_reg <= '0;
      candidate_o <= '0;
      membrane_o <= '0;
      spike_o <= 1'b0;
    end else begin
      case (state_reg)
        IDLE: begin
          spike_o <= 1'b0;
          if (in_valid) begin
            work_mem_reg <= membrane_i;
            current_reg <= current_i;
            beta_reg <= beta_i;
            threshold_reg <= threshold_i;
            remaining_reg <= elapsed_bins_i;
            state_reg <= (elapsed_bins_i == 0) ? CHARGE : LEAK;
          end
        end
        LEAK: begin
          product_value = $signed(work_mem_reg) * $signed({1'b0, beta_reg});
          leaked_value = saturate_mem(round_ties_away(product_value));
          work_mem_reg <= leaked_value[MEM_WIDTH-1:0];
          if (remaining_reg <= 1) begin
            remaining_reg <= '0;
            state_reg <= CHARGE;
          end else begin
            remaining_reg <= remaining_reg - 1'b1;
          end
        end
        CHARGE: begin
          candidate_value = saturate_mem($signed(work_mem_reg) + $signed(current_reg));
          candidate_o <= candidate_value[MEM_WIDTH-1:0];
          if (candidate_value >= $signed(threshold_reg)) begin
            membrane_value = saturate_mem(candidate_value - $signed(threshold_reg));
            membrane_o <= membrane_value[MEM_WIDTH-1:0];
            spike_o <= 1'b1;
          end else begin
            membrane_o <= candidate_value[MEM_WIDTH-1:0];
            spike_o <= 1'b0;
          end
          state_reg <= HOLD_RESULT;
        end
        HOLD_RESULT: if (out_ready) state_reg <= IDLE;
        default: state_reg <= IDLE;
      endcase
    end
  end
endmodule
