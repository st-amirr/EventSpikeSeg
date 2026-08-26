`timescale 1ns/1ps
// Learned-beta lazy leak and current integration without threshold/reset. This
// is the first phase of a retinotopic multi-channel mechanism commit.
module plif_leak_charge #(
  parameter integer MEM_WIDTH = 16,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer DELTA_WIDTH = 24
) (
  input logic clk, input logic reset,
  input logic in_valid, output logic in_ready,
  input logic signed [MEM_WIDTH-1:0] membrane_i,
  input logic signed [CURRENT_WIDTH-1:0] current_i,
  input logic [BETA_WIDTH-1:0] beta_i,
  input logic [DELTA_WIDTH-1:0] elapsed_bins_i,
  output logic out_valid, input logic out_ready,
  output logic signed [MEM_WIDTH-1:0] candidate_o
);
  localparam [1:0] IDLE = 2'd0, LEAK = 2'd1, CHARGE = 2'd2, HOLD = 2'd3;
  localparam integer MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH - 1));
  logic [1:0] state_reg;
  logic signed [MEM_WIDTH-1:0] work_mem_reg;
  logic signed [CURRENT_WIDTH-1:0] current_reg;
  logic [BETA_WIDTH-1:0] beta_reg;
  logic [DELTA_WIDTH-1:0] remaining_reg;
  integer signed product_value;
  integer signed magnitude;
  integer signed rounded_value;
  integer signed candidate_value;

  assign in_ready = (state_reg == IDLE);
  assign out_valid = (state_reg == HOLD);

  always_ff @(posedge clk) begin
    if (reset) begin
      state_reg <= IDLE;
      work_mem_reg <= '0;
      current_reg <= '0;
      beta_reg <= '0;
      remaining_reg <= '0;
      candidate_o <= '0;
    end else case (state_reg)
      IDLE: if (in_valid) begin
        work_mem_reg <= membrane_i;
        current_reg <= current_i;
        beta_reg <= beta_i;
        remaining_reg <= elapsed_bins_i;
        state_reg <= (elapsed_bins_i == 0) ? CHARGE : LEAK;
      end
      LEAK: begin
        product_value = $signed(work_mem_reg) * $signed({1'b0, beta_reg});
        if (product_value >= 0)
          rounded_value = (product_value + (1 << (BETA_FRAC_BITS-1))) >>>
                          BETA_FRAC_BITS;
        else begin
          magnitude = -product_value;
          rounded_value = -((magnitude + (1 << (BETA_FRAC_BITS-1))) >>>
                            BETA_FRAC_BITS);
        end
        if (rounded_value > MAX_MEM) rounded_value = MAX_MEM;
        if (rounded_value < MIN_MEM) rounded_value = MIN_MEM;
        work_mem_reg <= rounded_value[MEM_WIDTH-1:0];
        if (remaining_reg <= 1) begin
          remaining_reg <= '0;
          state_reg <= CHARGE;
        end else remaining_reg <= remaining_reg - 1'b1;
      end
      CHARGE: begin
        candidate_value = $signed(work_mem_reg) + $signed(current_reg);
        if (candidate_value > MAX_MEM) candidate_value = MAX_MEM;
        if (candidate_value < MIN_MEM) candidate_value = MIN_MEM;
        candidate_o <= candidate_value[MEM_WIDTH-1:0];
        state_reg <= HOLD;
      end
      HOLD: if (out_ready) state_reg <= IDLE;
      default: state_reg <= IDLE;
    endcase
  end
endmodule
