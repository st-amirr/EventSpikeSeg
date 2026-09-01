`timescale 1ns/1ps
module presynaptic_tap_array #(
  parameter integer COORD_WIDTH   = 10,
  parameter integer WEIGHT_WIDTH  = 8,
  parameter integer KERNEL_WIDTH  = 3,
  parameter integer KERNEL_HEIGHT = 3,
  parameter integer STRIDE_X      = 1,
  parameter integer STRIDE_Y      = 1,
  parameter integer DILATION_X    = 1,
  parameter integer DILATION_Y    = 1,
  parameter integer PAD_X         = 1,
  parameter integer PAD_Y         = 1,
  parameter integer OUTPUT_WIDTH  = 16,
  parameter integer OUTPUT_HEIGHT = 16,
  parameter integer TAP_COUNT     = KERNEL_WIDTH * KERNEL_HEIGHT
) (
  input  logic input_valid,
  input  logic [COORD_WIDTH-1:0] input_x,
  input  logic [COORD_WIDTH-1:0] input_y,
  input  logic signed [TAP_COUNT*WEIGHT_WIDTH-1:0] weights_i,
  output logic [TAP_COUNT-1:0] tap_valid_o,
  output logic [TAP_COUNT*COORD_WIDTH-1:0] tap_x_o,
  output logic [TAP_COUNT*COORD_WIDTH-1:0] tap_y_o,
  output logic [TAP_COUNT*WEIGHT_WIDTH-1:0] tap_weight_o
);
  integer kernel_x;
  integer kernel_y;
  integer tap_index;
  integer numerator_x;
  integer numerator_y;
  integer destination_x;
  integer destination_y;
  logic signed [WEIGHT_WIDTH-1:0] tap_weight;

  always_comb begin
    tap_valid_o = '0;
    tap_x_o = '0;
    tap_y_o = '0;
    tap_weight_o = weights_i;
    destination_x = 0;
    destination_y = 0;

    for (kernel_y = 0; kernel_y < KERNEL_HEIGHT; kernel_y = kernel_y + 1) begin
      for (kernel_x = 0; kernel_x < KERNEL_WIDTH; kernel_x = kernel_x + 1) begin
        tap_index = kernel_y * KERNEL_WIDTH + kernel_x;
        tap_weight = weights_i[tap_index*WEIGHT_WIDTH +: WEIGHT_WIDTH];
        numerator_x = $unsigned(input_x) + PAD_X - kernel_x * DILATION_X;
        numerator_y = $unsigned(input_y) + PAD_Y - kernel_y * DILATION_Y;
        if (input_valid && tap_weight != 0 && numerator_x >= 0 && numerator_y >= 0) begin
          destination_x = numerator_x / STRIDE_X;
          destination_y = numerator_y / STRIDE_Y;
          if ((numerator_x % STRIDE_X) == 0 && (numerator_y % STRIDE_Y) == 0 &&
              destination_x < OUTPUT_WIDTH && destination_y < OUTPUT_HEIGHT) begin
            tap_valid_o[tap_index] = 1'b1;
            tap_x_o[tap_index*COORD_WIDTH +: COORD_WIDTH] = destination_x[COORD_WIDTH-1:0];
            tap_y_o[tap_index*COORD_WIDTH +: COORD_WIDTH] = destination_y[COORD_WIDTH-1:0];
          end
        end
      end
    end
  end
endmodule
