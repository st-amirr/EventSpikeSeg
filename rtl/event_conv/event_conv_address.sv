`timescale 1ns/1ps

module event_conv_address #(
    parameter integer COORD_WIDTH = 10,
    parameter integer STRIDE_X = 2,
    parameter integer STRIDE_Y = 2,
    parameter integer PAD_X = 1,
    parameter integer PAD_Y = 1,
    parameter integer OUTPUT_WIDTH = 120,
    parameter integer OUTPUT_HEIGHT = 90
) (
    input  logic [COORD_WIDTH-1:0] input_x,
    input  logic [COORD_WIDTH-1:0] input_y,
    input  logic [COORD_WIDTH-1:0] kernel_x,
    input  logic [COORD_WIDTH-1:0] kernel_y,
    output logic valid,
    output logic [COORD_WIDTH-1:0] output_x,
    output logic [COORD_WIDTH-1:0] output_y
);
    integer numerator_x;
    integer numerator_y;
    integer quotient_x;
    integer quotient_y;

    always_comb begin
        numerator_x = input_x + PAD_X - kernel_x;
        numerator_y = input_y + PAD_Y - kernel_y;
        quotient_x = numerator_x / STRIDE_X;
        quotient_y = numerator_y / STRIDE_Y;
        valid = numerator_x >= 0 && numerator_y >= 0
            && numerator_x % STRIDE_X == 0 && numerator_y % STRIDE_Y == 0
            && quotient_x < OUTPUT_WIDTH && quotient_y < OUTPUT_HEIGHT;
        output_x = valid ? quotient_x[COORD_WIDTH-1:0] : '0;
        output_y = valid ? quotient_y[COORD_WIDTH-1:0] : '0;
    end
endmodule
