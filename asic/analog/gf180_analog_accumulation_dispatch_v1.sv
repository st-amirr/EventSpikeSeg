`timescale 1ns/1ps
// Categorical destination selection only. Membrane and contribution stay analog.
// A service request means restore -> signed charge injection -> capture/commit.
// service_done_i must acknowledge the real completed analog operation; it must
// not be generated merely from accepting an address or issuing a pulse.
module gf180_analog_accumulation_dispatch_v1 #(
  parameter integer CHANNELS=8, HEIGHT=440, WIDTH=640,
  parameter integer GAPPED_LOCAL_BANKS=0,
  parameter integer BANKS_X=(WIDTH+7)/8, BANKS_Y=(HEIGHT+7)/8
) (
  input wire clk, reset,
  input wire group_valid_i,
  output wire group_ready_o,
  input wire [7:0] channel_base_i, lane_count_i,
  input wire [9:0] x_i, y_i,
  input wire [23:0] bin_tag_i,
  output wire group_settled_done_o,
  output wire service_valid_o,
  input wire service_ready_i, service_done_i,
  output wire [6:0] channel_o,
  output wire [9:0] x_o,
  output wire [8:0] y_o,
  output wire [7:0] contribution_lane_o,
  output wire [23:0] service_bin_tag_o,
  output wire [19:0] linear_bank_o,
  output wire [1:0] service_kind_o,
  output wire [21:0] forest_address_o,
  output wire [6:0] local_page_address_o,
  output wire local_bank_select_o,
  output wire [2:0] local_row_o,
  output wire [7:0] column_select_o,
  output reg fault_o,
  output wire busy_o
);
  localparam [2:0] IDLE=0, MAP=1, REQUEST=2, WAIT_SERVICE=3, COMPLETE=4;
  reg [2:0] state;
  reg [7:0] channel, remaining, lane;
  reg [9:0] x, y;
  reg [23:0] tag;
  reg [19:0] bank;
  reg ack_armed;
  wire [8:0] end_channel={1'b0,channel_base_i}+{1'b0,lane_count_i};
  wire invalid=(lane_count_i==0 || channel_base_i>=CHANNELS || end_channel>CHANNELS ||
                x_i>=WIDTH || y_i>=HEIGHT);
  wire [19:0] mapped_bank=channel*(BANKS_X*BANKS_Y)+(y>>3)*BANKS_X+(x>>3);
  integer local_index;
  always @* begin
    if(!GAPPED_LOCAL_BANKS) local_index=(bank<19)?bank:-1;
    else if(bank<9) local_index=bank;
    else if(bank>=10 && bank<20) local_index=bank-1;
    else local_index=-1;
  end
  wire [19:0] forest_rank=(GAPPED_LOCAL_BANKS && bank==9)?20'd0:bank-20'd19;
  assign group_ready_o=(state==IDLE) && !fault_o;
  assign group_settled_done_o=(state==COMPLETE) && !fault_o;
  assign service_valid_o=(state==REQUEST) && !fault_o;
  assign busy_o=(state!=IDLE) && !fault_o;
  assign channel_o=channel[6:0];
  assign x_o=x; assign y_o=y[8:0];
  assign contribution_lane_o=lane;
  assign service_bin_tag_o=tag;
  assign linear_bank_o=bank;
  assign service_kind_o=(local_index==0)?2'd0:
                        (local_index>0 && local_index<3)?2'd1:
                        (local_index>=3)?2'd2:2'd3;
  assign forest_address_o=(local_index<0)?{forest_rank[18:0],y[2:0]}:22'd0;
  assign local_page_address_o=(local_index>=3)?((local_index-3)*8+y[2:0]):7'd0;
  assign local_bank_select_o=(local_index==2);
  assign local_row_o=y[2:0];
  assign column_select_o=8'b1<<x[2:0];
  always @(posedge clk) begin
    if(reset) begin
      state<=IDLE;channel<=0;remaining<=0;lane<=0;x<=0;y<=0;tag<=0;
      bank<=0;ack_armed<=0;fault_o<=0;
    end else if(!fault_o) case(state)
      IDLE: if(group_valid_i) begin
        if(invalid) fault_o<=1;
        else begin
          channel<=channel_base_i;remaining<=lane_count_i;lane<=0;
          x<=x_i;y<=y_i;tag<=bin_tag_i;state<=MAP;
        end
      end
      MAP: begin bank<=mapped_bank;state<=REQUEST;end
      REQUEST: if(service_ready_i) begin
        ack_armed<=!service_done_i;state<=WAIT_SERVICE;
      end
      WAIT_SERVICE: begin
        if(!service_done_i) ack_armed<=1;
        if(service_done_i && ack_armed) begin
          ack_armed<=0;
          if(remaining==1) state<=COMPLETE;
          else begin
            remaining<=remaining-1'b1;channel<=channel+1'b1;lane<=lane+1'b1;
            bank<=bank+BANKS_X*BANKS_Y;state<=REQUEST;
          end
        end
      end
      COMPLETE: state<=IDLE;
      default: fault_o<=1;
    endcase
  end
  initial begin
    if(CHANNELS<1 || CHANNELS>128 || HEIGHT<1 || HEIGHT>512 || WIDTH<1 || WIDTH>1024 ||
       CHANNELS*BANKS_X*BANKS_Y>(1<<19) || (GAPPED_LOCAL_BANKS!=0 && GAPPED_LOCAL_BANKS!=1))
      $error("Unsupported canonical membrane destination dimensions");
  end
endmodule
